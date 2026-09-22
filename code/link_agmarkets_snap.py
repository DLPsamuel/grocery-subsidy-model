"""Link Bronx CD2 Ag & Markets stores to USDA SNAP retailers for eligibility flags."""
from __future__ import annotations

import re
import sys
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
from geopy.distance import geodesic

sys.path.insert(0, str(Path(__file__).resolve().parent))
from data_paths import STORES_DIR  # noqa: E402

AG_PATH = STORES_DIR / "agmarkets_bronx_cd2.csv"
SNAP_PATH = STORES_DIR / "snap_bronx_cd2.csv"
OUT_CSV = STORES_DIR / "agmarkets_bronx_cd2_snap_eligibility.csv"
OUT_GEOJSON = STORES_DIR / "agmarkets_bronx_cd2_snap_eligibility.geojson"

SPATIAL_MAX_M = 75.0

STREET_REPLACEMENTS = [
    (r"\bAVENUE\b", "AVE"),
    (r"\bSTREET\b", "ST"),
    (r"\bROAD\b", "RD"),
    (r"\bBOULEVARD\b", "BLVD"),
    (r"\bPLACE\b", "PL"),
    (r"\bDRIVE\b", "DR"),
    (r"\bCOURT\b", "CT"),
    (r"\bLANE\b", "LN"),
    (r"\bEAST\b", "E"),
    (r"\bWEST\b", "W"),
    (r"\bNORTH\b", "N"),
    (r"\bSOUTH\b", "S"),
]


def normalize_street(s: object) -> str:
    text = str(s or "").upper().strip()
    text = re.sub(r"[^\w\s]", " ", text)
    text = re.sub(r"\s+", " ", text)
    for pat, rep in STREET_REPLACEMENTS:
        text = re.sub(pat, rep, text)
    return text.strip()


def normalize_number(s: object) -> str:
    text = str(s or "").strip().upper()
    # Keep leading house number digits (drop unit suffixes like 1A -> 1)
    m = re.match(r"(\d+)", text)
    return m.group(1) if m else text


def normalize_zip(s: object) -> str:
    text = re.sub(r"\D", "", str(s or ""))
    return text[:5]


def is_current_snap(end_date: object) -> bool:
    text = str(end_date or "").strip()
    return text == "" or text.lower() in {"nan", "none", "nat"}


def street_similarity(a: str, b: str) -> float:
    if not a or not b:
        return 0.0
    if a == b:
        return 1.0
    ta, tb = set(a.split()), set(b.split())
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / len(ta | tb)


def prepare_snap(snap: pd.DataFrame) -> pd.DataFrame:
    df = snap.copy()
    df["snap_record_id"] = df["Record ID"]
    df["snap_store_name"] = df["store_name"].astype(str).str.strip()
    df["snap_store_type"] = df.get("Store Type")
    df["snap_auth_date"] = df.get("Authorization Date")
    df["snap_end_date"] = df.get("End Date")
    df["num"] = df["Street Number"].map(normalize_number)
    df["street"] = df["Street Name"].map(normalize_street)
    df["zip5"] = df["Zip Code"].map(normalize_zip)
    df["lat"] = pd.to_numeric(df["latitude"], errors="coerce")
    df["lon"] = pd.to_numeric(df["longitude"], errors="coerce")
    df["snap_current"] = df["snap_end_date"].map(is_current_snap)

    # Prefer current authorizations, then latest auth date
    df["_auth_ts"] = pd.to_datetime(df["snap_auth_date"], errors="coerce")
    df = df.sort_values(
        ["snap_current", "_auth_ts"],
        ascending=[False, False],
        na_position="last",
    )
    dedupe_keys = ["snap_store_name", "num", "street", "zip5"]
    df = df.drop_duplicates(subset=dedupe_keys, keep="first").reset_index(drop=True)
    return df


def match_address(ag_row: pd.Series, snap: pd.DataFrame) -> tuple[pd.Series | None, str]:
    cand = snap[
        (snap["zip5"] == ag_row["zip5"]) & (snap["num"] == ag_row["num"]) & (snap["num"] != "")
    ]
    if cand.empty:
        return None, "none"
    scores = cand["street"].map(lambda s: street_similarity(ag_row["street"], s))
    best_idx = scores.idxmax()
    if scores.loc[best_idx] < 0.4:
        return None, "none"
    return cand.loc[best_idx], "address"


def match_spatial(ag_row: pd.Series, snap: pd.DataFrame) -> tuple[pd.Series | None, float]:
    if pd.isna(ag_row["lat"]) or pd.isna(ag_row["lon"]):
        return None, np.nan
    valid = snap.dropna(subset=["lat", "lon"])
    if valid.empty:
        return None, np.nan

    # Prefer current SNAP points first
    for subset in (valid[valid["snap_current"]], valid):
        if subset.empty:
            continue
        dists = subset.apply(
            lambda r: geodesic((ag_row["lat"], ag_row["lon"]), (r["lat"], r["lon"])).meters,
            axis=1,
        )
        best_idx = dists.idxmin()
        best_d = float(dists.loc[best_idx])
        if best_d <= SPATIAL_MAX_M:
            return subset.loc[best_idx], best_d
    return None, np.nan


def link_one(ag_row: pd.Series, snap: pd.DataFrame) -> dict:
    hit, method = match_address(ag_row, snap)
    dist_m = 0.0 if method == "address" else np.nan
    if hit is None:
        hit, dist_m = match_spatial(ag_row, snap)
        method = "spatial" if hit is not None else "none"

    if hit is None:
        return {
            "snap_eligible": 0,
            "snap_ever_authorized": 0,
            "snap_match_method": "none",
            "snap_record_id": None,
            "snap_store_name": None,
            "snap_store_type": None,
            "snap_auth_date": None,
            "snap_end_date": None,
            "snap_match_distance_m": None,
        }

    current = bool(hit["snap_current"])
    return {
        "snap_eligible": 1 if current else 0,
        "snap_ever_authorized": 1,
        "snap_match_method": method,
        "snap_record_id": hit["snap_record_id"],
        "snap_store_name": hit["snap_store_name"],
        "snap_store_type": hit["snap_store_type"],
        "snap_auth_date": hit["snap_auth_date"],
        "snap_end_date": hit["snap_end_date"] if not current else None,
        "snap_match_distance_m": None if pd.isna(dist_m) else round(float(dist_m), 1),
    }


def main() -> None:
    print("=== Link Ag & Markets <-> SNAP eligibility ===")
    ag = pd.read_csv(AG_PATH)
    snap_raw = pd.read_csv(SNAP_PATH)
    snap = prepare_snap(snap_raw)
    print(f"Ag & Markets rows: {len(ag)}")
    print(f"SNAP rows (raw / deduped): {len(snap_raw)} / {len(snap)}")
    print(f"SNAP currently authorized (deduped): {int(snap['snap_current'].sum())}")

    ag = ag.copy()
    ag["num"] = ag["street_number"].map(normalize_number)
    ag["street"] = ag["street_name"].map(normalize_street)
    ag["zip5"] = ag["zip_code"].map(normalize_zip)
    ag["lat"] = pd.to_numeric(ag["latitude"], errors="coerce")
    ag["lon"] = pd.to_numeric(ag["longitude"], errors="coerce")

    link_rows = [link_one(row, snap) for _, row in ag.iterrows()]
    linked = pd.concat([ag.reset_index(drop=True), pd.DataFrame(link_rows)], axis=1)
    linked = linked.drop(columns=["num", "street", "zip5", "lat", "lon"], errors="ignore")

    linked.to_csv(OUT_CSV, index=False)

    gdf = gpd.GeoDataFrame(
        linked,
        geometry=gpd.points_from_xy(
            pd.to_numeric(linked["longitude"], errors="coerce"),
            pd.to_numeric(linked["latitude"], errors="coerce"),
        ),
        crs="EPSG:4326",
    )
    gdf = gdf.dropna(subset=["geometry"])
    # GeoJSON can't store some awkward column names from Socrata
    gdf = gdf.rename(columns={c: c.replace(":", "_") for c in gdf.columns if isinstance(c, str)})
    gdf.to_file(OUT_GEOJSON, driver="GeoJSON")

    n = len(linked)
    n_elig = int(linked["snap_eligible"].sum())
    n_ever = int(linked["snap_ever_authorized"].sum())
    methods = linked["snap_match_method"].value_counts().to_dict()
    print("\nMatch summary")
    print(f"  snap_eligible (current): {n_elig}/{n} ({100 * n_elig / n:.1f}%)")
    print(f"  snap_ever_authorized:    {n_ever}/{n} ({100 * n_ever / n:.1f}%)")
    print(f"  methods: {methods}")
    print(f"Wrote {OUT_CSV}")
    print(f"Wrote {OUT_GEOJSON}")


if __name__ == "__main__":
    main()
