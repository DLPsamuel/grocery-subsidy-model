"""Download NYS Ag & Markets Retail Food Stores; filter to Bronx CD2."""
from __future__ import annotations

import ast
import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from data_paths import STORES_DIR, SESSION, load_cd2_boundary, points_in_cd2  # noqa: E402

DATASET = "9a8c-vfzj"
BASE = f"https://data.ny.gov/resource/{DATASET}.json"

CD2_ZIPS = {"10454", "10455", "10459", "10474"}


def fetch_all(limit: int = 50000) -> pd.DataFrame:
    rows = []
    offset = 0
    while True:
        params = {"$limit": limit, "$offset": offset}
        print(f"  offset={offset}")
        r = SESSION.get(BASE, params=params, timeout=180)
        r.raise_for_status()
        batch = r.json()
        if not batch:
            break
        rows.extend(batch)
        if len(batch) < limit:
            break
        offset += limit
    return pd.DataFrame(rows)


def parse_georeference(val):
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return None, None
    if isinstance(val, dict):
        coords = val.get("coordinates")
        if coords and len(coords) >= 2:
            return float(coords[0]), float(coords[1])
        return None, None
    if isinstance(val, str):
        try:
            obj = ast.literal_eval(val)
            return parse_georeference(obj)
        except Exception:
            try:
                obj = json.loads(val)
                return parse_georeference(obj)
            except Exception:
                return None, None
    return None, None


def main() -> None:
    print("=== NYS Ag & Markets Retail Food Stores ===")
    df = fetch_all()
    raw_path = STORES_DIR / "agmarkets_retail_food_stores_raw.csv"
    df.to_csv(raw_path, index=False)
    print(f"Raw rows: {len(df)}; cols={list(df.columns)}")

    if "georeference" in df.columns:
        parsed = df["georeference"].apply(parse_georeference)
        df["longitude"] = [p[0] for p in parsed]
        df["latitude"] = [p[1] for p in parsed]

    bronx = df[df["county"].astype(str).str.upper().eq("BRONX")].copy()
    bronx.to_csv(STORES_DIR / "agmarkets_bronx_county.csv", index=False)
    print(f"Bronx county rows: {len(bronx)}")

    meta = {
        "dataset": DATASET,
        "url": f"https://data.ny.gov/Economic-Development/Retail-Food-Stores/{DATASET}",
        "api": BASE,
        "raw_rows": len(df),
        "bronx_rows": len(bronx),
        "with_coords": int(bronx[["longitude", "latitude"]].notna().all(axis=1).sum())
        if "longitude" in bronx.columns
        else 0,
    }

    cd2 = load_cd2_boundary()
    if "longitude" in bronx.columns and bronx[["longitude", "latitude"]].notna().any().any():
        spatial_src = bronx.dropna(subset=["longitude", "latitude"])
        cd2_gdf = points_in_cd2(spatial_src, "longitude", "latitude", cd2=cd2)
        csv_df = pd.DataFrame(cd2_gdf.drop(columns=["geometry"], errors="ignore"))
        csv_df.to_csv(STORES_DIR / "agmarkets_bronx_cd2.csv", index=False)
        cd2_gdf.to_file(STORES_DIR / "agmarkets_bronx_cd2.geojson", driver="GeoJSON")
        meta["cd2_rows"] = len(cd2_gdf)
        print(f"CD2 spatial filter rows: {len(cd2_gdf)}")
    else:
        z = bronx["zip_code"].astype(str).str[:5]
        zip_df = bronx[z.isin(CD2_ZIPS)].copy()
        zip_df.to_csv(STORES_DIR / "agmarkets_bronx_cd2_FALLBACK_zip.csv", index=False)
        meta["cd2_rows"] = len(zip_df)
        meta["note"] = "ZIP fallback used"
        print(f"ZIP fallback rows: {len(zip_df)}")

    with open(STORES_DIR / "agmarkets_download_meta.json", "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)
    print("Done.")


if __name__ == "__main__":
    main()
