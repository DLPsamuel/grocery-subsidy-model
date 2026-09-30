"""Tax_j v2 for the 9 CD2 candidate stores, fiscal year 2025.

The lot tax is unchanged from v1 (build_tax_j.py: DOF Property Charges Balance, fiscal year
2025, duplicates removed). What changes is the store's share of it:

  store_share_area    occupied sq ft / DOF building area (build_store_occupancy.py), from the
                      team's ZoLa and Google Earth site checks.
  store_share_income  store Rent_j (v2) / DOF estimated gross income of the lot (2024-25 Notice
                      of Property Value). Computed wherever both exist, for comparison.

Tax_j uses the floor-area share, except for stores in INCOME_SPLIT_LICENSES. For those,
Tax_j uses the income share and Tax_j_high keeps the floor-area share.

Why an income split for Food Fair: DOF values class 4 property from its income
(https://www.nyc.gov/site/finance/property/property-determining-your-market-value.page;
the lot's notice: "Market value is determined by dividing the net operating income by the
overall capitalization rate"), so the lot's tax follows its income. The lot has 17 storefronts
and DOF's income estimate ($2.49M on 22,000 sq ft) reflects small-shop rents far above a
supermarket's. DOF itself does not split tax among tenants; this split is a modeling choice.

Reads existing v1 outputs only; writes data/tax/v2/tax_j_cd2_candidate_stores_v2.csv and
data/tax/v2/tax_j_v2_meta.json.
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
TAX_V1_CSV = ROOT / "data" / "tax" / "tax_j_cd2_candidate_stores.csv"
NOPV_CSV = ROOT / "data" / "rent" / "nopv_income_fy2025.csv"
OCC_CSV = ROOT / "data" / "tax" / "v2" / "store_occupancy_v2.csv"
RENT_V2_CSV = ROOT / "data" / "rent" / "v2" / "rent_j_cd2_candidate_stores_v2.csv"
OUT_DIR = ROOT / "data" / "tax" / "v2"
OUT_CSV = OUT_DIR / "tax_j_cd2_candidate_stores_v2.csv"
META_JSON = OUT_DIR / "tax_j_v2_meta.json"

FISCAL_YEAR = 2025
INCOME_SPLIT_LICENSES = {"603652"}  # Food Fair Fresh Market, 940 Southern Blvd lot (17 storefronts)


def main() -> None:
    v1 = pd.read_csv(TAX_V1_CSV, dtype={"license_number": str, "bbl": str, "pluto_bbl": str})
    occ = pd.read_csv(OCC_CSV, dtype={"license_number": str})
    rent = pd.read_csv(RENT_V2_CSV, dtype={"license_number": str})
    nopv = pd.read_csv(NOPV_CSV, dtype={"license_number": str})
    lot_tax_col = f"lot_tax_fy{FISCAL_YEAR}"

    df = v1[["store", "address", "license_number", "bbl", "lot_type", "pluto_bbl", "store_sqft", lot_tax_col,
             "store_share", "Tax_j", "nopv_est_property_tax", "nopv_diff_pct", "nopv_check", "flags"]].rename(
        columns={"store_sqft": "agm_sqft", "store_share": "store_share_v1", "Tax_j": "Tax_j_v1", lot_tax_col: "lot_tax"})
    df = df.merge(occ[["license_number", "occupancy_basis", "occupied_sqft", "denominator_sqft",
                       "denominator_source", "store_share_area"]], on="license_number", how="left")
    df = df.merge(rent[["license_number", "Rent_j"]], on="license_number", how="left")
    df = df.merge(nopv[["license_number", "nopv_gross_income"]], on="license_number", how="left")

    df["store_share_income"] = (df["Rent_j"] / df["nopv_gross_income"]).clip(upper=1).round(4)
    df["Tax_j_area"] = (df["lot_tax"] * df["store_share_area"]).round(2)
    df["Tax_j_income"] = (df["lot_tax"] * df["store_share_income"]).round(2)

    income = df["license_number"].isin(INCOME_SPLIT_LICENSES)
    df["share_method"] = "floor area"
    df.loc[income, "share_method"] = "income (floor-area share kept as Tax_j_high)"
    df["store_share"] = df["store_share_area"]
    df.loc[income, "store_share"] = df.loc[income, "store_share_income"]
    df["Tax_j"] = df["Tax_j_area"]
    df.loc[income, "Tax_j"] = df.loc[income, "Tax_j_income"]
    df["Tax_j_high"] = df["Tax_j_area"]
    df["Tax_j_change_vs_v1"] = (df["Tax_j"] - df["Tax_j_v1"]).round(2)

    df["flags"] = df["flags"].fillna("").str.replace(
        "store sq ft exceeds PLUTO commercial area",
        "Ag & Markets sq ft exceeds PLUTO commercial area (occupied area set to commercial area)", regex=False)
    df.loc[income, "flags"] = df.loc[income, "flags"].str.cat(
        ["multi-tenant lot: tax split by share of DOF estimated income"] * income.sum(), sep="; ").str.strip("; ")
    df.loc[df["lot_type"] == "condo_unit", "flags"] = "condo unit bill; store is part of the retail unit"

    out = df[["store", "address", "license_number", "bbl", "lot_type", "agm_sqft", "occupancy_basis",
              "occupied_sqft", "denominator_sqft", "denominator_source", "lot_tax", "nopv_gross_income",
              "Rent_j", "store_share_v1", "store_share_area", "store_share_income", "share_method",
              "store_share", "Tax_j_v1", "Tax_j_area", "Tax_j_income", "Tax_j", "Tax_j_high",
              "Tax_j_change_vs_v1", "nopv_est_property_tax", "nopv_diff_pct", "nopv_check", "flags"]]
    out = out.rename(columns={"lot_tax": lot_tax_col, "Rent_j": "Rent_j_v2"}).sort_values("Tax_j", ascending=False)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out.to_csv(OUT_CSV, index=False)

    meta = {
        "fiscal_year": FISCAL_YEAR,
        "fiscal_year_dates": f"{FISCAL_YEAR - 1}-07-01 to {FISCAL_YEAR}-06-30",
        "lot_tax": f"unchanged from v1 ({TAX_V1_CSV.relative_to(ROOT).as_posix()})",
        "sources": {
            "lot_tax": "DOF Property Charges Balance, NYC Open Data scjx-j6np (code = CHG), via build_tax_j.py",
            "building_area": "MapPLUTO, NYC Open Data 64uk-42ks (bldgarea, comarea, retailarea); condo unit area from its 2024-25 Notice of Property Value",
            "occupied_area": "data/stores/store_site_observations.csv (team ZoLa and Google Earth site check, 2026-09-30) via build_store_occupancy.py",
            "lot_income": "Estimated Gross Income, 2024-25 Notice of Property Value (data/rent/nopv_income_fy2025.csv)",
            "store_rent": f"{RENT_V2_CSV.relative_to(ROOT).as_posix()} (build_rent_j_v2.py)",
        },
        "store_share_area_rule": "min(occupied_sqft / denominator_sqft, 1); denominator = PLUTO bldgarea, or the condo unit's own area",
        "store_share_income_rule": "min(Rent_j v2 / lot estimated gross income, 1)",
        "income_split_licenses": sorted(INCOME_SPLIT_LICENSES),
        "income_split_rationale": (
            "DOF values class 4 property from its income (NOPV: market value = net operating income / overall cap rate), "
            "so a lot's tax follows its income. Food Fair's lot has 17 storefronts whose small-shop rents dominate DOF's "
            "income estimate. DOF does not split tax among tenants; this is a modeling choice. Tax_j_high keeps the floor-area split."),
        "references": [
            "https://www.nyc.gov/site/finance/property/property-determining-your-market-value.page",
            "https://www.nyc.gov/assets/planning/download/pdf/data-maps/open-data/pluto_datadictionary.pdf",
            "https://data.ny.gov/Economic-Development/Retail-Food-Stores/9a8c-vfzj",
        ],
        "totals": {
            "Tax_j_v1": round(float(out["Tax_j_v1"].sum()), 2),
            "Tax_j_v2": round(float(out["Tax_j"].sum()), 2),
            "Tax_j_v2_high": round(float(out["Tax_j_high"].sum()), 2),
        },
    }
    META_JSON.write_text(json.dumps(meta, indent=2), encoding="utf-8")

    pd.set_option("display.width", 250)
    print(out[["store", "occupied_sqft", "store_share_v1", "store_share_area", "store_share_income", "share_method",
               "Tax_j_v1", "Tax_j", "Tax_j_high"]].to_string(index=False))
    t = meta["totals"]
    print(f"\nTotal Tax_j v2: ${t['Tax_j_v2']:,.0f} (high ${t['Tax_j_v2_high']:,.0f}; v1 ${t['Tax_j_v1']:,.0f})")
    print(f"Saved {OUT_CSV.relative_to(ROOT)} and {META_JSON.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
