"""Download USDA SNAP retailer data; filter to Bronx CD2."""
from __future__ import annotations

import io
import json
import sys
import zipfile
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from data_paths import STORES_DIR, SESSION, download_file, load_cd2_boundary, points_in_cd2  # noqa: E402

# Candidate download URLs (USDA pages change; try several)
CANDIDATE_URLS = [
    # Historical data landing often links a zip; try known CDN / fns paths
    "https://www.fns.usda.gov/sites/default/files/media/file/SNAP_Retailer_Location_data.zip",
    "https://www.fns.usda.gov/sites/default/files/resource-files/SNAP_Store_Locations.zip",
    "https://www.fns.usda.gov/sites/default/files/media/file/SNAP_Store_Locations-2.zip",
]


def find_csv_in_zip(zip_path: Path) -> pd.DataFrame:
    with zipfile.ZipFile(zip_path, "r") as zf:
        names = [n for n in zf.namelist() if n.lower().endswith(".csv")]
        if not names:
            raise FileNotFoundError(f"No CSV in {zip_path}: {zf.namelist()[:20]}")
        # Prefer largest csv
        names.sort(key=lambda n: zf.getinfo(n).file_size, reverse=True)
        with zf.open(names[0]) as f:
            return pd.read_csv(f, low_memory=False)


def try_download() -> tuple[Path, str]:
    raw_dir = STORES_DIR / "snap_raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    errors = []
    for url in CANDIDATE_URLS:
        dest = raw_dir / Path(url).name
        try:
            print(f"Trying {url}")
            download_file(url, dest)
            if dest.stat().st_size < 1000:
                errors.append(f"{url}: too small")
                continue
            return dest, url
        except Exception as e:
            errors.append(f"{url}: {e}")
    # Scrape historical data page for .zip links
    for page in (
        "https://www.fns.usda.gov/snap/retailer/historicaldata",
        "https://www.fns.usda.gov/snap/retailer-locator/data",
        "https://www.fns.usda.gov/snap/retailer/data",
    ):
        try:
            print(f"Scraping {page}")
            html = SESSION.get(page, timeout=60).text
            import re

            for m in re.finditer(r'href="([^"]+\.zip)"', html, re.I):
                href = m.group(1)
                if href.startswith("/"):
                    href = "https://www.fns.usda.gov" + href
                elif not href.startswith("http"):
                    continue
                dest = raw_dir / Path(href.split("?")[0]).name
                try:
                    download_file(href, dest)
                    if dest.stat().st_size > 1000:
                        return dest, href
                except Exception as e:
                    errors.append(f"{href}: {e}")
        except Exception as e:
            errors.append(f"page {page}: {e}")

    raise RuntimeError("Could not download SNAP retailer ZIP. Errors:\n" + "\n".join(errors))


def normalize_cols(df: pd.DataFrame) -> pd.DataFrame:
    rename = {}
    lower = {c.lower().strip(): c for c in df.columns}
    mapping = {
        "store_name": ["store_name", "store name", "storename", "name"],
        "latitude": ["latitude", "lat", "y"],
        "longitude": ["longitude", "long", "lon", "lng", "x"],
        "address": ["street_address", "address", "store_street_address", "address1"],
        "city": ["city", "store_city"],
        "state": ["state", "store_state"],
        "zip": ["zip5", "zip", "zipcode", "zip_code"],
        "store_type": ["store_type", "storetype", "type"],
    }
    for std, aliases in mapping.items():
        for a in aliases:
            if a in lower:
                rename[lower[a]] = std
                break
    return df.rename(columns=rename)


def main() -> None:
    print("=== USDA SNAP Retailer Locator ===")
    meta: dict = {"errors": []}
    try:
        path, url = try_download()
        meta["download_url"] = url
        meta["local_file"] = str(path)
    except Exception as e:
        meta["fatal"] = str(e)
        with open(STORES_DIR / "snap_download_meta.json", "w", encoding="utf-8") as f:
            json.dump(meta, f, indent=2)
        print(f"FATAL: {e}")
        raise SystemExit(1)

    if path.suffix.lower() == ".zip":
        df = find_csv_in_zip(path)
    else:
        df = pd.read_csv(path, low_memory=False)

    df = normalize_cols(df)
    df.to_csv(STORES_DIR / "snap_retailers_raw_sample_cols.csv", index=False)
    # Keep full raw too (may be large)
    raw_full = STORES_DIR / "snap_retailers_us_raw.csv"
    df.to_csv(raw_full, index=False)
    print(f"US rows: {len(df)}; cols={list(df.columns)[:15]}")

    # Filter NY
    if "state" in df.columns:
        ny = df[df["state"].astype(str).str.upper().isin(["NY", "NEW YORK"])].copy()
    else:
        ny = df.copy()
    # Bronx by city or zip
    bronx_zips = {
        "10451", "10454", "10455", "10459", "10460", "10474", "10456", "10457",
        "10458", "10461", "10462", "10463", "10464", "10465", "10466", "10467",
        "10468", "10469", "10470", "10471", "10472", "10473", "10475",
    }
    mask = pd.Series(False, index=ny.index)
    if "city" in ny.columns:
        mask = mask | ny["city"].astype(str).str.contains("bronx", case=False, na=False)
    if "zip" in ny.columns:
        z = ny["zip"].astype(str).str[:5]
        mask = mask | z.isin(bronx_zips)
    bronx = ny[mask].copy() if mask.any() else ny.copy()
    bronx.to_csv(STORES_DIR / "snap_bronx_county.csv", index=False)
    print(f"Bronx filter rows: {len(bronx)}")

    cd2 = load_cd2_boundary()
    if "longitude" in bronx.columns and "latitude" in bronx.columns:
        cd2_gdf = points_in_cd2(bronx, "longitude", "latitude", cd2=cd2)
        csv_df = pd.DataFrame(cd2_gdf.drop(columns=["geometry"], errors="ignore"))
        csv_df.to_csv(STORES_DIR / "snap_bronx_cd2.csv", index=False)
        cd2_gdf.to_file(STORES_DIR / "snap_bronx_cd2.geojson", driver="GeoJSON")
        meta["cd2_rows"] = len(cd2_gdf)
        print(f"CD2 rows: {len(cd2_gdf)}")
    else:
        meta["cd2_rows"] = None
        meta["note"] = "Missing lat/lon after normalize"
        bronx.to_csv(STORES_DIR / "snap_bronx_cd2_FALLBACK.csv", index=False)

    meta["us_rows"] = len(df)
    meta["bronx_rows"] = len(bronx)
    meta["portal"] = "https://www.fns.usda.gov/snap/retailer-locator"
    with open(STORES_DIR / "snap_download_meta.json", "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)
    print("Done.")


if __name__ == "__main__":
    main()
