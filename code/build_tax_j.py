"""Estimate Tax_j (annual property tax borne by each store) for the 9 CD2 candidate stores
(Appendix F, Lead S).

Team decision: use fiscal year 2025 (July 1, 2024 - June 30, 2025), to match the other 2024
inputs (ACS households, BLS spending, ReferenceUSA 2024 revenue).

Method
  1. Store -> tax lot (BBL). Lots come from the Phase 3 geocoding
     (data/phase3/tax_rent_agmarkets_cd2.csv). Fine Fare sits in a condo building whose billing
     lot (2027037501) carries no tax bill; its own condo unit lot (2027031001, the parcel number
     in ReferenceUSA) is used instead.
  2. Lot tax = DOF Property Charges Balance (NYC Open Data scjx-j6np), property tax charge
     rows only (code = CHG). The dataset repeats each installment across monthly extracts and
     adds a row when a payment posts, and its "taxyear" field can include the prior fiscal
     year's installments. So: keep installments whose billing period falls inside the fiscal
     year, keep the latest extract, count each billing period once (largest liability), and
     sum. Quarterly and semiannual payers both end up with 12 months; nothing is annualized.
  3. Store share = store sq ft (Ag & Markets) / building gross floor area (PLUTO bldgarea),
     capped at 1. The condo unit bill is already the store's own, so its share is 1.
  4. Tax_j = lot tax x store share.
  5. Check: lot tax vs the "Estimated Property Tax" printed on the 2024-25 Notice of Property
     Value (read by build_rent_nopv.py). The notice uses the prior year's tax rate and leaves
     out abatements, so small differences are expected (about +1.6% from the rate change).
     Larger shortfalls mean DOF reduced installments during the year; the latest extract
     carries the reduced, final liability.

Run order: build_tax_j.py, build_rent_nopv.py, then build_tax_j.py again to fill the check.
"""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[1]
TAX_DIR = ROOT / "data" / "tax"
RAW_DIR = TAX_DIR / "raw"
STORES_CSV = ROOT / "data" / "stores" / "large_grocery_stores_cd2.csv"
PHASE3_CSV = ROOT / "data" / "phase3" / "tax_rent_agmarkets_cd2.csv"
NOPV_CSV = ROOT / "data" / "rent" / "nopv_income_fy2025.csv"

LOTS_CSV = TAX_DIR / "candidate_store_lots.csv"
PLUTO_CSV = TAX_DIR / "pluto_candidate_lots.csv"
OUT_CSV = TAX_DIR / "tax_j_cd2_candidate_stores.csv"
META_JSON = TAX_DIR / "tax_j_meta.json"

DOF_CHARGES = "https://data.cityofnewyork.us/resource/scjx-j6np.json"
PLUTO = "https://data.cityofnewyork.us/resource/64uk-42ks.json"

FISCAL_YEAR = 2025
FY_START = date(FISCAL_YEAR - 1, 7, 1)
FY_END = date(FISCAL_YEAR, 6, 30)
NOPV_TOLERANCE = 0.05

# Condo buildings: store license -> (unit lot that carries the bill, billing lot used by PLUTO)
CONDO_UNIT_LOTS = {"704892": ("2027031001", "2027037501")}  # Fine Fare, 950 Westchester Ave

PLUTO_FIELDS = ["bbl", "address", "ownername", "bldgclass", "landuse", "numbldgs", "numfloors",
                "lotarea", "bldgarea", "comarea", "retailarea", "resarea", "officearea",
                "unitsres", "unitstotal", "assessland", "assesstot", "exempttot", "yearbuilt"]

SESSION = requests.Session()
SESSION.headers.update({"User-Agent": "grocery-subsidy-analysis/0.1 (Bronx CD2 research; academic)"})


def bbl_str(v) -> str | None:
    """Normalize a BBL (float, int or string) to a 10-digit string."""
    if pd.isna(v):
        return None
    return str(int(float(v))).zfill(10)


def build_lots() -> pd.DataFrame:
    """One row per candidate store with its tax lot."""
    stores = pd.read_csv(STORES_CSV, encoding="utf-8-sig", dtype={"license_number": str})
    stores = stores[stores["keep"] == 1]
    phase3 = pd.read_csv(PHASE3_CSV, dtype={"store_id": str})
    phase3["bbl"] = phase3["bbl"].map(bbl_str)
    lots = stores.merge(phase3[["store_id", "bbl"]], left_on="license_number",
                        right_on="store_id", how="left")
    lots["street"] = lots["street_name"].str.replace("#", "").str.strip()
    lots["address"] = lots["street_number"].astype(str) + " " + lots["street"]
    lots["lot_type"] = "whole_lot"
    lots["pluto_bbl"] = lots["bbl"]
    for lic, (unit_bbl, billing_bbl) in CONDO_UNIT_LOTS.items():
        m = lots["license_number"] == lic
        lots.loc[m, ["bbl", "pluto_bbl", "lot_type"]] = [unit_bbl, billing_bbl, "condo_unit"]
    lots = lots.rename(columns={"dba_name": "store", "square_footage": "store_sqft"})
    lots = lots[["license_number", "store", "address", "store_sqft", "bbl", "lot_type", "pluto_bbl"]]
    lots.to_csv(LOTS_CSV, index=False)
    return lots


def fetch_charges(bbl: str) -> list[dict]:
    """All property tax charge rows for a lot, saved unchanged to data/tax/raw/."""
    r = SESSION.get(DOF_CHARGES, params={"parid": bbl, "code": "CHG", "$limit": "5000"}, timeout=120)
    r.raise_for_status()
    rows = r.json()
    (RAW_DIR / f"dof_charges_{bbl}.json").write_text(json.dumps(rows, indent=1), encoding="utf-8")
    return rows


def fiscal_year_tax(rows: list[dict]) -> dict:
    """Annual tax for FISCAL_YEAR: one liability per billing period from the latest extract."""
    if not rows:
        return {"lot_tax": None, "n_periods": 0, "months_covered": 0.0, "cycles": None,
                "extract_date": None, "full_year": False}
    df = pd.DataFrame(rows)
    df["begin"] = pd.to_datetime(df["dt_pd_begin"]).dt.date
    df["end"] = pd.to_datetime(df["dt_pd_end"]).dt.date
    df["sum_liab"] = df["sum_liab"].astype(float)
    df = df[(df["begin"] >= FY_START) & (df["end"] <= FY_END)]
    if df.empty:
        return {"lot_tax": None, "n_periods": 0, "months_covered": 0.0, "cycles": None,
                "extract_date": None, "full_year": False}
    latest = df["extractdt"].max()
    df = df[df["extractdt"] == latest]
    periods = df.groupby(["begin", "end"], as_index=False).agg(
        liab=("sum_liab", "max"), cycle=("cycle", "first"))
    days = sum((e - b).days + 1 for b, e in zip(periods["begin"], periods["end"]))
    months = round(days / 30.4375, 1)
    return {
        "lot_tax": round(periods["liab"].sum(), 2),
        "n_periods": len(periods),
        "months_covered": months,
        "cycles": ",".join(sorted(periods["cycle"])),
        "extract_date": latest[:10],
        "full_year": abs(months - 12) < 0.5,
    }


def fetch_pluto(bbl: str) -> dict:
    r = SESSION.get(PLUTO, params={"bbl": bbl, "$select": ",".join(PLUTO_FIELDS)}, timeout=120)
    r.raise_for_status()
    rows = r.json()
    return rows[0] if rows else {"bbl": bbl}


def main() -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    lots = build_lots()

    tax_rows = []
    for bbl in lots["bbl"]:
        tax_rows.append({"bbl": bbl, **fiscal_year_tax(fetch_charges(bbl))})
    tax = pd.DataFrame(tax_rows)

    pluto = pd.DataFrame([fetch_pluto(b) for b in lots["pluto_bbl"].unique()])
    pluto["bbl"] = pluto["bbl"].map(bbl_str)
    num_cols = [c for c in PLUTO_FIELDS if c not in ("bbl", "address", "ownername", "bldgclass", "landuse")]
    pluto[num_cols] = pluto[num_cols].apply(pd.to_numeric, errors="coerce")
    pluto.to_csv(PLUTO_CSV, index=False)

    df = lots.merge(tax, on="bbl", how="left")
    df = df.merge(pluto.add_prefix("pluto_"), on="pluto_bbl", how="left")

    whole = df["lot_type"] == "whole_lot"
    df["store_share"] = 1.0
    df.loc[whole, "store_share"] = (df.loc[whole, "store_sqft"] / df.loc[whole, "pluto_bldgarea"]).clip(upper=1)
    df["store_share"] = df["store_share"].round(4)
    df["Tax_j"] = (df["lot_tax"] * df["store_share"]).round(2)

    flags = []
    for _, r in df.iterrows():
        f = []
        if not r["full_year"]:
            f.append("billing periods do not cover 12 months")
        if r["lot_type"] == "whole_lot" and r["store_sqft"] > r["pluto_comarea"]:
            f.append("store sq ft exceeds PLUTO commercial area")
        if r["lot_type"] == "whole_lot" and r["pluto_numbldgs"] > 1:
            f.append(f"lot has {int(r['pluto_numbldgs'])} buildings")
        if r["lot_type"] == "whole_lot" and r["pluto_resarea"] > 0:
            f.append("mixed-use lot with residential floor area")
        if r["lot_type"] == "condo_unit":
            f.append("condo unit bill (store's own)")
        flags.append("; ".join(f))
    df["flags"] = flags

    if NOPV_CSV.exists():
        nopv = pd.read_csv(NOPV_CSV, dtype={"bbl": str})[["bbl", "nopv_est_property_tax"]]
        df = df.merge(nopv.drop_duplicates("bbl"), on="bbl", how="left")
        df["nopv_diff_pct"] = ((df["lot_tax"] / df["nopv_est_property_tax"] - 1) * 100).round(1)
        tol = NOPV_TOLERANCE * 100
        df["nopv_check"] = "ok"
        df.loc[df["nopv_diff_pct"] < -tol, "nopv_check"] = (
            "bill below notice estimate: installments were reduced during the year "
            "(Tax Commission reduction or abatement); final billed amount used")
        df.loc[df["nopv_diff_pct"] > tol, "nopv_check"] = "bill above notice estimate: check raw charges"
        df.loc[df["nopv_est_property_tax"].isna(), "nopv_check"] = "no notice"
    else:
        df["nopv_est_property_tax"] = None
        df["nopv_diff_pct"] = None
        df["nopv_check"] = "notice data not built yet (run build_rent_nopv.py, then rerun)"

    out = df[["store", "address", "license_number", "store_sqft", "bbl", "lot_type", "pluto_bbl",
              "pluto_bldgclass", "pluto_numbldgs", "pluto_bldgarea", "pluto_comarea",
              "pluto_retailarea", "pluto_resarea", "cycles", "n_periods", "months_covered",
              "extract_date", "lot_tax", "store_share", "Tax_j", "nopv_est_property_tax",
              "nopv_diff_pct", "nopv_check", "flags"]]
    out = out.rename(columns={"lot_tax": f"lot_tax_fy{FISCAL_YEAR}"})
    out = out.sort_values("Tax_j", ascending=False)
    out.to_csv(OUT_CSV, index=False)

    meta = {
        "fiscal_year": FISCAL_YEAR,
        "fiscal_year_period": [FY_START.isoformat(), FY_END.isoformat()],
        "sources": {
            "tax_bills": "DOF Property Charges Balance, NYC Open Data scjx-j6np (code = CHG)",
            "floor_area": "MapPLUTO, NYC Open Data 64uk-42ks (bldgarea)",
            "store_sqft": "NYS Ag & Markets retail food store licenses (data/stores/large_grocery_stores_cd2.csv)",
            "tax_lots": "Phase 3 geocoding (data/phase3/tax_rent_agmarkets_cd2.csv); Fine Fare condo unit from ReferenceUSA parcel number",
            "check": "DOF Notice of Property Value 2024-25, estimated property tax (data/rent/nopv_income_fy2025.csv)",
        },
        "dedup_rule": "Keep CHG rows whose billing period lies inside the fiscal year; keep the latest extractdt; "
                      "one liability per billing period (max sum_liab); sum periods. No annualizing.",
        "store_share_rule": "min(store_sqft / PLUTO bldgarea, 1); condo unit = 1",
        "condo_unit_lots": {k: {"unit_bbl": v[0], "billing_bbl": v[1]} for k, v in CONDO_UNIT_LOTS.items()},
        "outputs": [p.relative_to(ROOT).as_posix() for p in (LOTS_CSV, PLUTO_CSV, OUT_CSV)],
    }
    META_JSON.write_text(json.dumps(meta, indent=2), encoding="utf-8")

    pd.set_option("display.width", 220)
    print(out[["store", "bbl", "cycles", "months_covered", f"lot_tax_fy{FISCAL_YEAR}", "store_share",
               "Tax_j", "nopv_diff_pct", "flags"]].to_string(index=False))
    print(f"\nTotal Tax_j (9 stores, FY{FISCAL_YEAR}): ${out['Tax_j'].sum():,.0f}")
    print(f"Saved {OUT_CSV.relative_to(ROOT)}, {LOTS_CSV.relative_to(ROOT)}, {PLUTO_CSV.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
