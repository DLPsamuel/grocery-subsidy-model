"""Estimate kappa, the core basket share: the fraction of food-at-home spending that falls on
N.Y.C. Groceries Core Basket items (used in Delta p_j = 0.30 * kappa * p_j).

Core Basket (RFP Appendix C, preliminary): all produce, all fresh meat and seafood,
refrigerated staples (cows' milk, eggs, butter, tofu, yogurt, non-specialty cheese, deli
meats) and shelf-stable staples (pasta, sandwich bread, ready-to-eat cereal, tuna, pasta
sauce, soup, cooking oil, nuts, raw rice, non-dairy milks, flour and meal, beans), plus
specialty cheese and prepared salads. Snacks and desserts are excluded.

Spending shares: BLS Consumer Expenditure Survey 2024, Table 1203 (income before taxes).
Each BLS food-at-home category is tagged:
  - "in":      the whole category is in the Core Basket
  - "partial": only some items in the category are in the Core Basket
  - "out":     nothing (or almost nothing) in the category is in the Core Basket
kappa_low counts only "in", kappa_high counts "in" + all of "partial", and kappa_base
counts "in" + half of "partial".
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
BLS_XLSX = ROOT / "data" / "bls" / "cu-income-before-taxes-2024.xlsx"
OUT_CSV = ROOT / "data" / "bls" / "kappa_core_basket_share.csv"

PARTIAL_WEIGHT = 0.5

CATEGORIES = {
    "Fresh fruits": "in",
    "Fresh vegetables": "in",
    "Beef": "in",
    "Pork": "in",
    "Other meats": "in",               # includes deli and lunch meats
    "Poultry": "in",
    "Fish and seafood": "in",
    "Eggs": "in",
    "Fresh milk and cream": "in",
    "Cereals and cereal products": "partial",   # flour, rice, pasta, cereal
    "Bakery products": "partial",               # sandwich bread only; no cakes or cookies
    "Other dairy products": "partial",          # butter, cheese, yogurt; no ice cream
    "Processed fruits and vegetables": "partial",  # beans, canned vegetables; no juice
    "Fats and oils": "partial",                 # cooking oil
    "Miscellaneous foods": "partial",           # soup, pasta sauce, nuts, prepared salads; no snacks
    "Sugar and other sweets": "out",
    "Nonalcoholic beverages": "out",
    "Food prepared by consumer unit on out of town trips": "out",
}

# BLS income brackets (column order in Table 1203) -> our three income groups.
# The $15,000-$29,999 bracket straddles the $25K line, so it counts toward Low.
BRACKETS = {
    1: ("all", None), 2: ("<15K", "low"), 3: ("15-30K", "low"), 4: ("30-40K", "mid"),
    5: ("40-50K", "mid"), 6: ("50-70K", "high"), 7: ("70-100K", "high"),
    8: ("100-150K", "high"), 9: ("150-200K", "high"), 10: (">=200K", "high"),
}


def mean_row(table: pd.DataFrame, label: str) -> pd.Series:
    """The 'Mean' row directly under a category label."""
    idx = table.index[table[0].astype(str).str.strip() == label][0]
    return table.loc[idx + 1, list(BRACKETS)].astype(float)


def main() -> None:
    table = pd.read_excel(BLS_XLSX, header=None)
    units = table.loc[3, list(BRACKETS)].astype(float)  # consumer units, thousands
    food_at_home = mean_row(table, "Food at home")

    spend = pd.DataFrame({c: mean_row(table, c) for c in CATEGORIES}).T
    tag = pd.Series(CATEGORIES)
    in_sum = spend[tag == "in"].sum()
    partial_sum = spend[tag == "partial"].sum()

    shares = pd.DataFrame({
        "food_at_home": food_at_home,
        "kappa_low": in_sum / food_at_home,
        "kappa_base": (in_sum + PARTIAL_WEIGHT * partial_sum) / food_at_home,
        "kappa_high": (in_sum + partial_sum) / food_at_home,
        "units": units,
    })
    shares["bracket"] = [BRACKETS[c][0] for c in shares.index]
    shares["group"] = [BRACKETS[c][1] for c in shares.index]

    rows = [{"group": "all", "kappa_low": shares.loc[1, "kappa_low"],
             "kappa_base": shares.loc[1, "kappa_base"], "kappa_high": shares.loc[1, "kappa_high"]}]
    for group in ["low", "mid", "high"]:
        g = shares[shares["group"] == group]
        w = g["units"] * g["food_at_home"]  # spending-weighted across brackets
        rows.append({"group": group,
                     **{k: (g[k] * w).sum() / w.sum() for k in ["kappa_low", "kappa_base", "kappa_high"]}})
    out = pd.DataFrame(rows).round(3)
    out.to_csv(OUT_CSV, index=False)

    print("Category spending, all consumer units, 2024 ($/yr):")
    print(pd.DataFrame({"tag": tag, "spend": spend[1]}).to_string())
    print(f"\nFood at home: ${food_at_home[1]:,.0f}")
    print(out.to_string(index=False))
    print(f"\nSaved {OUT_CSV.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
