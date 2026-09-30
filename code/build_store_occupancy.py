"""Occupied floor area and floor-area share of the tax lot for the 9 CD2 candidate stores (v2).

Replaces the v1 rule (Ag & Markets sq ft / PLUTO building area) with one occupied area per
store, set from the team's ZoLa and Google Earth site checks
(data/stores/store_site_observations.csv). The same occupied area feeds the tax share
(build_tax_j_v2.py) and rent (build_rent_j_v2.py). Revenue keeps Ag & Markets sq ft.

occupancy_basis -> occupied_sqft
  whole_building        DOF building area (store is the only occupant)
  dof_commercial_area   PLUTO comarea (store fills the commercial floor of a mixed-use building)
  dof_retail_area       PLUTO retailarea (store fills the ground-floor retail space)
  condo_unit_part       occupancy_value sq ft of the condo unit
  fraction_of_building  occupancy_value x DOF building area
  measured              occupancy_value sq ft (Google Earth; store shares a floor with others)
  agmarkets             Ag & Markets square_footage

Denominator: PLUTO bldgarea (gross, exterior dimensions, all structures on the lot), except
condo units, where it is the unit's own area from its Notice of Property Value.
store_share_area = min(occupied_sqft / denominator, 1).

Reads existing v1 outputs only; writes data/tax/v2/store_occupancy_v2.csv.
"""
from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OBS_CSV = ROOT / "data" / "stores" / "store_site_observations.csv"
LOTS_CSV = ROOT / "data" / "tax" / "candidate_store_lots.csv"
PLUTO_CSV = ROOT / "data" / "tax" / "pluto_candidate_lots.csv"
NOPV_TXT_DIR = ROOT / "data" / "rent" / "nopv"
OUT_DIR = ROOT / "data" / "tax" / "v2"
OUT_CSV = OUT_DIR / "store_occupancy_v2.csv"

CONDO_SQFT_RE = re.compile(r"GrossSquareFootageoftheSuffix:\s*([\d,]+)")
DOF_BASES = {"whole_building", "dof_commercial_area", "dof_retail_area"}


def condo_unit_sqft(bbl: str) -> float | None:
    """Condo unit gross sq ft from the saved 2024-25 notice text."""
    path = NOPV_TXT_DIR / f"{bbl}_2024-25.txt"
    if not path.exists():
        return None
    m = CONDO_SQFT_RE.search(path.read_text(encoding="utf-8"))
    return float(m.group(1).replace(",", "")) if m else None


def pct(a, b):
    if pd.isna(a) or pd.isna(b) or not b:
        return None
    return round((a / b - 1) * 100, 1)


def occupied_area(r: pd.Series) -> float:
    basis, val = r["occupancy_basis"], r["occupancy_value"]
    if basis == "whole_building":
        return r["denominator_sqft"]
    if basis == "dof_commercial_area":
        return r["pluto_comarea"]
    if basis == "dof_retail_area":
        return r["pluto_retailarea"]
    if basis == "fraction_of_building":
        return float(val) * r["denominator_sqft"]
    if basis in ("condo_unit_part", "measured"):
        return float(val)
    if basis == "agmarkets":
        return r["agm_sqft"]
    raise ValueError(f"unknown occupancy_basis {basis!r} for {r['store']}")


def main() -> None:
    obs = pd.read_csv(OBS_CSV, dtype={"license_number": str, "bbl": str})
    lots = pd.read_csv(LOTS_CSV, dtype={"license_number": str, "bbl": str, "pluto_bbl": str})
    pluto = pd.read_csv(PLUTO_CSV, dtype={"bbl": str})
    pluto = pluto[["bbl", "numbldgs", "numfloors", "lotarea", "bldgarea", "comarea", "retailarea", "resarea"]]
    pluto = pluto.add_prefix("pluto_")

    df = lots.rename(columns={"store_sqft": "agm_sqft"}).merge(pluto, on="pluto_bbl", how="left")
    df = df.merge(obs.drop(columns=["store", "bbl"]), on="license_number", how="left")
    missing = df[df["occupancy_basis"].isna()]
    if not missing.empty:
        raise SystemExit(f"No site observation for: {', '.join(missing['store'])}")

    df["condo_unit_sqft"] = [condo_unit_sqft(b) if t == "condo_unit" else None
                             for b, t in zip(df["bbl"], df["lot_type"])]
    condo = df["lot_type"] == "condo_unit"
    df["denominator_sqft"] = df["pluto_bldgarea"].astype(float)
    df.loc[condo, "denominator_sqft"] = df.loc[condo, "condo_unit_sqft"]
    df["denominator_source"] = "PLUTO bldgarea (all floors, all buildings on the lot)"
    df.loc[condo, "denominator_source"] = "condo unit gross sq ft (2024-25 notice)"

    df["occupied_sqft"] = df.apply(occupied_area, axis=1).round(0)
    df["store_share_area"] = (df["occupied_sqft"] / df["denominator_sqft"]).clip(upper=1).round(4)

    df["dof_bldgarea_per_floor"] = (df["pluto_bldgarea"] / df["pluto_numfloors"].clip(lower=1)).round(0)
    df["ge_building_vs_dof_pct"] = [pct(a, b) for a, b in zip(df["ge_building_sqft"], df["dof_bldgarea_per_floor"])]
    df["ge_store_vs_dof_pct"] = [pct(a, b) if basis in DOF_BASES else None
                                 for a, b, basis in zip(df["ge_store_sqft"], df["occupied_sqft"], df["occupancy_basis"])]
    df["agm_vs_occupied_pct"] = [pct(a, b) for a, b in zip(df["agm_sqft"], df["occupied_sqft"])]

    out = df[["license_number", "store", "address", "bbl", "lot_type", "pluto_bbl",
              "agm_sqft", "ge_store_sqft", "ge_building_sqft", "ge_upper_floor_sqft",
              "pluto_numbldgs", "pluto_numfloors", "pluto_lotarea", "pluto_bldgarea", "pluto_comarea",
              "pluto_retailarea", "pluto_resarea", "condo_unit_sqft", "dof_bldgarea_per_floor",
              "occupancy_basis", "occupancy_value", "occupied_sqft", "denominator_sqft", "denominator_source",
              "store_share_area", "ge_building_vs_dof_pct", "ge_store_vs_dof_pct", "agm_vs_occupied_pct",
              "second_floor_used", "occupancy_note"]]
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out.to_csv(OUT_CSV, index=False)

    pd.set_option("display.width", 250)
    print(out[["store", "agm_sqft", "ge_store_sqft", "occupancy_basis", "occupied_sqft", "denominator_sqft",
               "store_share_area", "ge_building_vs_dof_pct", "ge_store_vs_dof_pct", "agm_vs_occupied_pct"]].to_string(index=False))
    print(f"\nSaved {OUT_CSV.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
