"""Estimate Revenue_j (annual sales) and Q_j (baskets sold per year) for the CD2 stores
(Appendix F, Lead R).

Team decision: use 2024 figures, to match the other 2024 inputs (ACS households, BLS spending).

  - Main source: ReferenceUSA / Data Axle U.S. Historical Businesses, 2024 version,
    "Location Sales Volume Actual" (pulled 2026-09-29). Records are picked by IUSA number
    (see IUSA_TO_LICENSE). Food Universe and JJ Southern Farm have no historical record.
  - Fallback for the two stores with no 2024 record: square footage x the median 2024
    ReferenceUSA sales per sq ft of the other 7 stores, so all 9 are on the same scale.
  - Check only: square footage x FMI national sales per sq ft ($19.59/week, Food Industry
    Facts 2025). Runs much higher than ReferenceUSA, so it is not mixed in.

Q_j = Revenue_j / p_j, with p_j from data/prices/p_j_cd2_candidate_stores.csv.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
REVENUE_DIR = ROOT / "data" / "revenue"
RUSA_DIR = ROOT / "data" / "archive" / "referenceusa"
HISTORICAL_CSV = RUSA_DIR / "referenceusa_historical_2020_2024.csv"
STORES_CSV = ROOT / "data" / "stores" / "large_grocery_stores_cd2.csv"
PRICES_CSV = ROOT / "data" / "prices" / "p_j_cd2_candidate_stores.csv"
OUT_CSV = REVENUE_DIR / "revenue_j_cd2_candidate_stores.csv"
HISTORY_OUT_CSV = RUSA_DIR / "referenceusa_sales_by_year.csv"

YEAR = "2024"
FMI_SALES_PER_SQFT_WEEK = 19.59
WEEKS_PER_YEAR = 52

# ReferenceUSA record (IUSA number) -> our store (Ag & Markets license number).
# Checked by address, phone and Verified status; see docs/revenue_j_estimates.md.
IUSA_TO_LICENSE = {
    "71-512-7646": "601435",  # Key Food, 1050 Westchester Ave
    "22-473-1729": "603652",  # Food Fair, 1065 E 163rd St
    "72-380-0203": "704892",  # Fine Fare (listed as Fair Farm Food), 950 Westchester Ave
    "11-396-5248": "600246",  # C-Town, 564 Southern Blvd
    "11-399-7589": "609927",  # C-Town, 809 Southern Blvd
    "72-125-4832": "725894",  # Antillana (A & J Super Food), 1025 Westchester Ave
    "71-786-6922": "723677",  # Sagal (Southern Blvd Meat Market), 1087-1093 Southern Blvd
}


def load_history() -> pd.DataFrame:
    """One row per store and year, for our stores only."""
    h = pd.read_csv(HISTORICAL_CSV, dtype=str)
    h = h[h["IUSA Number"].isin(IUSA_TO_LICENSE)].copy()
    h["license_number"] = h["IUSA Number"].map(IUSA_TO_LICENSE)
    h["sales"] = h["Location Sales Volume Actual"].str.replace(r"[$,]", "", regex=True).astype(float)
    h["employees"] = h["Location Employee Size Actual"].astype(int)
    return h[["license_number", "IUSA Number", "Version Year", "sales", "employees"]]


def main() -> None:
    stores = pd.read_csv(STORES_CSV, encoding="utf-8-sig", dtype={"license_number": str})
    stores = stores[stores["keep"] == 1].copy()
    stores["address"] = (stores["street_number"].astype(str) + " "
                         + stores["street_name"].str.replace("#", "").str.strip())

    history = load_history()
    by_year = history.pivot(index="license_number", columns="Version Year", values="sales")
    wide = stores[["license_number", "dba_name", "address"]].merge(
        by_year, left_on="license_number", right_index=True, how="left")
    wide.to_csv(HISTORY_OUT_CSV, index=False)

    latest = history[history["Version Year"] == YEAR].set_index("license_number")
    prices = pd.read_csv(PRICES_CSV)
    prices["address"] = prices["address"].str.replace("#", "").str.strip()

    df = stores.merge(latest[["IUSA Number", "sales", "employees"]],
                      left_on="license_number", right_index=True, how="left")
    df = df.merge(prices[["address", "p_j_current"]], on="address", how="left")

    df["revenue_rusa_2024"] = df["sales"]
    df["revenue_size_based"] = (df["square_footage"] * FMI_SALES_PER_SQFT_WEEK
                                * WEEKS_PER_YEAR).round(-3)
    rusa_per_sqft = (df["revenue_rusa_2024"] / df["square_footage"]).median()
    df["revenue_rusa_rate"] = (df["square_footage"] * rusa_per_sqft).round(-3)
    df["Revenue_j"] = df["revenue_rusa_2024"].fillna(df["revenue_rusa_rate"])
    df["revenue_source"] = df["revenue_rusa_2024"].notna().map(
        {True: "ReferenceUSA 2024", False: "sq ft x median ReferenceUSA 2024 $/sq ft"})
    df["Q_j"] = (df["Revenue_j"] / df["p_j_current"]).round()

    out = df.rename(columns={"dba_name": "store", "IUSA Number": "iusa_number",
                             "employees": "employees_2024", "p_j_current": "p_j"})
    out = out[["store", "address", "license_number", "iusa_number", "square_footage",
               "employees_2024", "revenue_rusa_2024", "revenue_size_based", "Revenue_j",
               "revenue_source", "p_j", "Q_j"]]
    out = out.sort_values("Revenue_j", ascending=False)
    out.to_csv(OUT_CSV, index=False)

    pd.set_option("display.width", 200)
    print(out.drop(columns=["address", "license_number", "iusa_number"]).to_string(index=False))
    print(f"\nMedian ReferenceUSA 2024 sales per sq ft: ${rusa_per_sqft:,.0f}")
    print(f"Total Revenue_j (9 stores): ${out['Revenue_j'].sum():,.0f}")
    print(f"\nSaved {OUT_CSV.relative_to(ROOT)} and {HISTORY_OUT_CSV.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
