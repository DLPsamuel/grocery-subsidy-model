"""Build d_ij, the travel distance (miles) from each income group to each CD2 store
(Appendix F, Lead S).

Method (Datasets sheet, row 18 note):
  - Manhattan distance (east-west + north-south, like walking the blocks) from each of the
    16 CD2 census tract centroids to each store.
  - For each income group, average over tracts, weighted by how many households of that
    group live in each tract (ACS B19001, 2024). Tracts with no households get no weight.
  - Kept in miles (team decision), to match the units of the distance papers (Hillier et
    al. 2017). The Level 1 spec uses minutes; 1 mile = about 24 min at its 15 min/km.

Store locations come from Samuel's final list. Food Universe uses the old 724 Hunts Point
Ave location for now (team still deciding on 1334 Louis Nine Blvd).
"""
from __future__ import annotations

from math import cos, radians
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
CENTROIDS_CSV = DATA / "geography" / "bronx_cd2_tract_centroids.csv"
INCOME_CSV = DATA / "acs" / "cd2_B19001_2024.csv"
STORES_CSV = DATA / "stores" / "large_grocery_stores_cd2.csv"
OUT_DIR = DATA / "distance"
OUT_DIR.mkdir(parents=True, exist_ok=True)
OUT_CSV = OUT_DIR / "d_ij_cd2.csv"
TRACT_CSV = OUT_DIR / "d_tract_store_miles.csv"

MILES_PER_DEG_LAT = 69.17
GROUPS = {"low": "n_low", "mid": "n_mid", "high": "n_high"}


def manhattan_miles(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """North-south plus east-west distance in miles (flat-earth, fine at this scale)."""
    mid_lat = radians((lat1 + lat2) / 2)
    dy = abs(lat1 - lat2) * MILES_PER_DEG_LAT
    dx = abs(lon1 - lon2) * MILES_PER_DEG_LAT * cos(mid_lat)
    return dx + dy


def main() -> None:
    tracts = pd.read_csv(CENTROIDS_CSV, dtype={"tract_id": str})
    income = pd.read_csv(INCOME_CSV, dtype={"GEOID": str})
    tracts = tracts.merge(income[["GEOID", *GROUPS.values()]],
                          left_on="tract_id", right_on="GEOID")

    stores = pd.read_csv(STORES_CSV, encoding="utf-8-sig")
    stores = stores[stores["keep"] == 1].copy()
    stores["address"] = (stores["street_number"].astype(str) + " "
                         + stores["street_name"].str.replace("#", "").str.strip())

    # Distance from every tract to every store
    rows = []
    for _, t in tracts.iterrows():
        for _, s in stores.iterrows():
            rows.append({
                "tract_id": t["tract_id"],
                "store": s["dba_name"],
                "address": s["address"],
                "miles": manhattan_miles(t["lat"], t["lon"], s["latitude"], s["longitude"]),
                **{col: t[col] for col in GROUPS.values()},
            })
    pairs = pd.DataFrame(rows)
    pairs.drop(columns=list(GROUPS.values())).round({"miles": 3}).to_csv(TRACT_CSV, index=False)

    # Household-weighted average for each income group
    out = []
    for group, col in GROUPS.items():
        for (store, address), g in pairs.groupby(["store", "address"], sort=False):
            miles = (g["miles"] * g[col]).sum() / g[col].sum()
            out.append({"income_group": group, "store": store, "address": address,
                        "d_ij_miles": round(miles, 3)})
    result = pd.DataFrame(out)
    result.to_csv(OUT_CSV, index=False)

    wide = result.pivot(index="store", columns="income_group", values="d_ij_miles")
    wide = wide[["low", "mid", "high"]].sort_values("low")
    print("d_ij (miles, Manhattan distance)")
    print(wide.to_string())
    print(f"\nSaved {OUT_CSV.relative_to(ROOT)} and {TRACT_CSV.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
