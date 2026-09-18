"""Download NYC DOHMH food establishments (grocery-like); filter to Bronx CD2."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from data_paths import STORES_DIR, SESSION, load_cd2_boundary, points_in_cd2  # noqa: E402

DATASET = "43nn-pn8j"
BASE = f"https://data.cityofnewyork.us/resource/{DATASET}.json"

# Cuisine / keyword filters aligned with grocery retail
GROCERY_CUISINES = [
    "Grocery",
    "Delicatessen",
    "Donuts",  # often convenience; keep optional — we'll use broader keyword set
]
# Prefer explicit grocery-like cuisine descriptions
CUISINE_WHERE = (
    "upper(cuisine_description) like '%GROCERY%' OR "
    "upper(cuisine_description) like '%DELICATESSEN%' OR "
    "upper(cuisine_description) like '%DELICATESSEN%' OR "
    "upper(cuisine_description) like '%SANDWICH%' OR "
    "upper(dba) like '%GROCERY%' OR "
    "upper(dba) like '%SUPERMARKET%' OR "
    "upper(dba) like '%FOOD%' OR "
    "upper(dba) like '%BODEGA%' OR "
    "upper(dba) like '%MARKET%'"
)


def fetch_bronx_grocery(limit: int = 50000) -> pd.DataFrame:
    rows = []
    offset = 0
    where = f"boro='Bronx' AND ({CUISINE_WHERE})"
    while True:
        params = {
            "$limit": limit,
            "$offset": offset,
            "$where": where,
            "$select": (
                "camis,dba,boro,building,street,zipcode,cuisine_description,"
                "latitude,longitude,inspection_date,grade,score"
            ),
            "$order": "camis,inspection_date DESC",
        }
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
        if offset > 200000:
            break
    return pd.DataFrame(rows)


def main() -> None:
    print("=== NYC Open Data DOHMH food establishments (grocery-like) ===")
    df = fetch_bronx_grocery()
    raw = STORES_DIR / "nyc_dohmh_bronx_grocery_inspections_raw.csv"
    df.to_csv(raw, index=False)
    print(f"Inspection rows: {len(df)}")

    # Dedupe to latest inspection per CAMIS
    if "camis" in df.columns:
        df["inspection_date"] = pd.to_datetime(df.get("inspection_date"), errors="coerce")
        stores = (
            df.sort_values("inspection_date", ascending=False)
            .drop_duplicates(subset=["camis"], keep="first")
            .copy()
        )
    else:
        stores = df.drop_duplicates().copy()

    stores.to_csv(STORES_DIR / "nyc_dohmh_bronx_grocery_stores.csv", index=False)
    print(f"Unique establishments: {len(stores)}")

    meta = {
        "dataset": DATASET,
        "url": (
            "https://data.cityofnewyork.us/Health/"
            "DOHMH-New-York-City-Restaurant-Inspection-Results/43nn-pn8j"
        ),
        "api": BASE,
        "inspection_rows": len(df),
        "unique_stores_bronx": len(stores),
    }

    cd2 = load_cd2_boundary()
    if "longitude" in stores.columns and "latitude" in stores.columns:
        gdf = points_in_cd2(stores, "longitude", "latitude", cd2=cd2)
        pd.DataFrame(gdf.drop(columns=["geometry"], errors="ignore")).to_csv(
            STORES_DIR / "nyc_dohmh_bronx_cd2_grocery.csv", index=False
        )
        gdf.to_file(STORES_DIR / "nyc_dohmh_bronx_cd2_grocery.geojson", driver="GeoJSON")
        meta["cd2_rows"] = len(gdf)
        print(f"CD2 rows: {len(gdf)}")
    else:
        meta["cd2_rows"] = None
        print("No coordinates")

    with open(STORES_DIR / "nyc_dohmh_download_meta.json", "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)
    print("Done.")


if __name__ == "__main__":
    main()
