"""Download ACS B11001 and B19001 for Bronx tracts via Census Reporter; filter to CD2."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd
import requests

sys.path.insert(0, str(Path(__file__).resolve().parent))
from data_paths import ACS_DIR, GEO_DIR, SESSION, census_api_key  # noqa: E402

# Census Reporter release names that work without a Census API key
RELEASES = [
    ("acs2024_5yr", 2024),
    ("latest", None),  # resolve year from response metadata if needed
]

UA = "grocery-subsidy-analysis/0.1 (research; Bronx CD2 ACS pull)"

# Census Reporter uses concatenated codes without underscore: B19001002 etc.
B19001_LOW = [f"B19001{i:03d}" for i in range(2, 6)]
B19001_MID = [f"B19001{i:03d}" for i in range(6, 11)]
B19001_HIGH = [f"B19001{i:03d}" for i in range(11, 18)]


def load_cd2_tract_geoids() -> set[str]:
    path = GEO_DIR / "bronx_cd2_tracts.geojson"
    if not path.exists():
        return set()
    import geopandas as gpd

    gdf = gpd.read_file(path)
    out = set()
    for col in ("geoid", "GEOID"):
        if col in gdf.columns:
            out |= set(gdf[col].astype(str))
    # boroct2020 → GEOID
    if "boroct2020" in gdf.columns:
        for v in gdf["boroct2020"].astype(str):
            v = v.zfill(7)
            out.add(f"36005{v[-6:]}")
    return out


def fetch_census_reporter(release: str) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    url = f"https://api.censusreporter.org/1.0/data/show/{release}"
    params = {"table_ids": "B11001,B19001", "geo_ids": "140|05000US36005"}
    headers = {"User-Agent": UA}
    r = SESSION.get(url, params=params, headers=headers, timeout=180)
    r.raise_for_status()
    payload = r.json()
    if "error" in payload and "data" not in payload:
        raise RuntimeError(payload["error"])

    hh_rows = []
    inc_rows = []
    for geo_id, tables in payload.get("data", {}).items():
        # geo_id like 14000US36005008700
        geoid = geo_id.replace("14000US", "")
        name = payload.get("geography", {}).get(geo_id, {}).get("name", geo_id)

        b11 = tables.get("B11001", {}).get("estimate", {})
        hh_rows.append(
            {
                "GEOID": geoid,
                "NAME": name,
                "B11001_001E": b11.get("B11001001"),
                "source": f"censusreporter:{release}",
            }
        )

        b19 = tables.get("B19001", {}).get("estimate", {})
        row = {
            "GEOID": geoid,
            "NAME": name,
            "source": f"censusreporter:{release}",
        }
        for i in range(1, 18):
            code = f"B19001{i:03d}"
            row[f"B19001_{i:03d}E"] = b19.get(code)
        # income groups
        def _sum(codes):
            return sum(float(b19.get(c) or 0) for c in codes)

        row["n_low"] = _sum(B19001_LOW)
        row["n_mid"] = _sum(B19001_MID)
        row["n_high"] = _sum(B19001_HIGH)
        row["n_i_sum"] = row["n_low"] + row["n_mid"] + row["n_high"]
        inc_rows.append(row)

    meta = {
        "release": release,
        "release_info": payload.get("release", {}),
        "n_geographies": len(payload.get("data", {})),
        "url": r.url,
    }
    return pd.DataFrame(hh_rows), pd.DataFrame(inc_rows), meta


def try_census_api(year: int) -> tuple[pd.DataFrame, pd.DataFrame] | None:
    """Optional path if CENSUS_API_KEY is set."""
    key = census_api_key()
    if not key:
        return None
    base = f"https://api.census.gov/data/{year}/acs/acs5"
    vars_hh = ["NAME", "B11001_001E"]
    vars_inc = ["NAME"] + [f"B19001_{i:03d}E" for i in range(1, 18)]

    def _one(variables):
        params = {
            "get": ",".join(variables),
            "for": "tract:*",
            "in": "state:36 county:005",
            "key": key,
        }
        r = SESSION.get(base, params=params, timeout=120)
        r.raise_for_status()
        data = r.json()
        df = pd.DataFrame(data[1:], columns=data[0])
        df["GEOID"] = df["state"] + df["county"] + df["tract"]
        df["year"] = year
        return df

    try:
        return _one(vars_hh), _one(vars_inc)
    except Exception as e:
        msg = str(e).replace(key, "***")
        print(f"  Census API {year} failed: {msg}")
        return None


def main() -> None:
    print("=== ACS B11001 / B19001 (Bronx tracts -> CD2) ===")
    cd2_geoids = load_cd2_tract_geoids()
    print(f"CD2 tract GEOIDs loaded: {len(cd2_geoids)}")

    meta: dict = {
        "api_key_used": bool(census_api_key()),
        "sources": [],
        "years_ok": [],
        "years_missing": [],
        "notes": [],
    }

    # Prefer Census Reporter (no key). Pull available releases.
    releases_tried = []
    for release, year_hint in RELEASES:
        if release in releases_tried:
            continue
        releases_tried.append(release)
        try:
            print(f"Fetching Census Reporter release={release}...")
            hh, inc, rel_meta = fetch_census_reporter(release)
        except Exception as e:
            print(f"  Failed: {e}")
            meta["notes"].append(f"{release}: {e}")
            continue

        year = year_hint
        if year is None:
            name = str(rel_meta.get("release_info", {}).get("id") or release)
            year = 2024 if "2024" in name else 2023 if "2023" in name else None
            if year is None:
                year = 2024
        out_tag = f"{year}_{release}"
        hh["year"] = year
        inc["year"] = year
        hh.to_csv(ACS_DIR / f"bronx_B11001_{out_tag}.csv", index=False)
        inc.to_csv(ACS_DIR / f"bronx_B19001_{out_tag}.csv", index=False)
        meta["sources"].append(rel_meta)
        meta["years_ok"].append(year)

        hh_cd2 = hh[hh["GEOID"].isin(cd2_geoids)].copy() if cd2_geoids else hh.copy()
        inc_cd2 = inc[inc["GEOID"].isin(cd2_geoids)].copy() if cd2_geoids else inc.copy()
        hh_cd2.to_csv(ACS_DIR / f"cd2_B11001_{year}.csv", index=False)
        inc_cd2.to_csv(ACS_DIR / f"cd2_B19001_{year}.csv", index=False)

        agg = {
            "year": year,
            "N_HH": hh_cd2["B11001_001E"].sum(),
            "n_low": inc_cd2["n_low"].sum(),
            "n_mid": inc_cd2["n_mid"].sum(),
            "n_high": inc_cd2["n_high"].sum(),
            "n_i_sum": inc_cd2["n_i_sum"].sum(),
            "tracts": hh_cd2["GEOID"].nunique(),
            "source": f"censusreporter:{release}",
        }
        pd.DataFrame([agg]).to_csv(
            ACS_DIR / f"cd2_household_income_summary_{year}.csv", index=False
        )
        print(agg)

    # Official Census API for 2020-2025 if key present
    if census_api_key():
        summary_rows = []
        for year in range(2020, 2026):
            print(f"Fetching Census API ACS {year}...")
            got = try_census_api(year)
            if not got:
                meta["years_missing"].append(year)
                continue
            hh, inc = got
            for v in [c for c in inc.columns if c.startswith("B19001_")]:
                inc[v] = pd.to_numeric(inc[v], errors="coerce")
            hh["B11001_001E"] = pd.to_numeric(hh["B11001_001E"], errors="coerce")
            inc["n_low"] = inc[[f"B19001_{i:03d}E" for i in range(2, 6)]].sum(axis=1)
            inc["n_mid"] = inc[[f"B19001_{i:03d}E" for i in range(6, 11)]].sum(axis=1)
            inc["n_high"] = inc[[f"B19001_{i:03d}E" for i in range(11, 18)]].sum(axis=1)
            inc["n_i_sum"] = inc["n_low"] + inc["n_mid"] + inc["n_high"]
            hh.to_csv(ACS_DIR / f"bronx_B11001_censusapi_{year}.csv", index=False)
            inc.to_csv(ACS_DIR / f"bronx_B19001_censusapi_{year}.csv", index=False)

            hh_cd2 = hh[hh["GEOID"].isin(cd2_geoids)].copy() if cd2_geoids else hh.copy()
            inc_cd2 = inc[inc["GEOID"].isin(cd2_geoids)].copy() if cd2_geoids else inc.copy()
            hh_cd2.to_csv(ACS_DIR / f"cd2_B11001_{year}.csv", index=False)
            inc_cd2.to_csv(ACS_DIR / f"cd2_B19001_{year}.csv", index=False)

            agg = {
                "year": year,
                "N_HH": float(hh_cd2["B11001_001E"].sum()),
                "n_low": float(inc_cd2["n_low"].sum()),
                "n_mid": float(inc_cd2["n_mid"].sum()),
                "n_high": float(inc_cd2["n_high"].sum()),
                "n_i_sum": float(inc_cd2["n_i_sum"].sum()),
                "tracts": int(hh_cd2["GEOID"].nunique()),
                "source": f"censusapi:{year}",
            }
            summary_rows.append(agg)
            pd.DataFrame([agg]).to_csv(
                ACS_DIR / f"cd2_household_income_summary_{year}.csv", index=False
            )
            meta["years_ok"].append(year)
            print(agg)
    else:
        meta["notes"].append(
            "CENSUS_API_KEY not set; multi-year ACS via api.census.gov skipped "
            "(API now requires a key). Used Census Reporter for latest 5-year."
        )
        meta["years_missing"].extend([2020, 2021, 2022, 2023, 2025])

    # Combined summary from any cd2_household_income_summary_*.csv
    summaries = list(ACS_DIR.glob("cd2_household_income_summary_*.csv"))
    if summaries:
        all_sum = pd.concat([pd.read_csv(p) for p in summaries], ignore_index=True)
        # Prefer censusapi rows over censusreporter for the same year
        all_sum["_rank"] = all_sum["source"].astype(str).str.startswith("censusapi").astype(int)
        all_sum = (
            all_sum.sort_values(["year", "_rank"])
            .drop_duplicates(subset=["year"], keep="last")
            .drop(columns=["_rank"])
            .sort_values("year")
        )
        all_sum.to_csv(ACS_DIR / "cd2_household_income_summary.csv", index=False)
        print(all_sum.to_string(index=False))

    with open(ACS_DIR / "acs_download_meta.json", "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2, default=str)
    print("Done.")

if __name__ == "__main__":
    main()
