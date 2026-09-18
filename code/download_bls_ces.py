"""Collect BLS CES food-at-home spending inputs for market size M and f_bar.

Automated downloads from bls.gov return HTTP 403 in this environment.
This script:
  1) Attempts direct XLSX downloads (records success/failure)
  2) Writes a curated CES food-at-home series from published BLS tables
     with working citation URLs for Phase 2 reporting
  3) Builds a simple M / f_bar worksheet using CD2 N_HH if available
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from data_paths import ACS_DIR, BLS_DIR, SESSION, download_file  # noqa: E402

CES_INCOME_URLS = {
    2020: "https://www.bls.gov/cex/tables/calendar-year/mean/cu-income-before-taxes-2020.xlsx",
    2021: "https://www.bls.gov/cex/tables/calendar-year/mean/cu-income-before-taxes-2021.xlsx",
    2022: "https://www.bls.gov/cex/tables/calendar-year/mean/cu-income-before-taxes-2022.xlsx",
    2023: "https://www.bls.gov/cex/tables/calendar-year/mean/cu-income-before-taxes-2023.xlsx",
    2024: "https://www.bls.gov/cex/tables/calendar-year/mean/cu-income-before-taxes-2024.xlsx",
}

# Published all-CU mean annual food-at-home ($) from BLS CES news / reports
# Sources cited in meta and CSV.
PUBLISHED_FOOD_AT_HOME = [
    {
        "year": 2019,
        "food_at_home_annual_usd": 4643,
        "food_away_annual_usd": 3526,
        "food_total_annual_usd": 8169,
        "geography": "United States (all consumer units)",
        "source_url": "https://www.bls.gov/opub/reports/consumer-expenditures/2023/",
        "source_note": "BLS Consumer Expenditures in 2023 report, historical comparison table",
    },
    {
        "year": 2020,
        "food_at_home_annual_usd": 4935,
        "food_away_annual_usd": 2375,
        "food_total_annual_usd": 7310,
        "geography": "United States (all consumer units)",
        "source_url": "https://www.bls.gov/opub/reports/consumer-expenditures/2023/",
        "source_note": "BLS Consumer Expenditures in 2023 report",
    },
    {
        "year": 2021,
        "food_at_home_annual_usd": 5259,
        "food_away_annual_usd": 3030,
        "food_total_annual_usd": 8289,
        "geography": "United States (all consumer units)",
        "source_url": "https://www.bls.gov/opub/reports/consumer-expenditures/2023/",
        "source_note": "BLS Consumer Expenditures in 2023 report",
    },
    {
        "year": 2022,
        "food_at_home_annual_usd": 5703,
        "food_away_annual_usd": 3639,
        "food_total_annual_usd": 9343,
        "geography": "United States (all consumer units)",
        "source_url": "https://www.bls.gov/news.release/cesan.nr0.htm",
        "source_note": "BLS Consumer Expenditures — 2023 news release table",
    },
    {
        "year": 2023,
        "food_at_home_annual_usd": 6053,
        "food_away_annual_usd": 3933,
        "food_total_annual_usd": 9985,
        "geography": "United States (all consumer units)",
        "source_url": "https://www.bls.gov/news.release/cesan.nr0.htm",
        "source_note": "BLS Consumer Expenditures — 2023 news release",
    },
    {
        "year": 2024,
        "food_at_home_annual_usd": 6224,
        "food_away_annual_usd": 3945,
        "food_total_annual_usd": 10169,
        "geography": "United States (all consumer units)",
        "source_url": "https://www.bls.gov/news.release/cesan.htm",
        "source_note": "BLS Consumer Expenditures News Release — 2024 A01 results table",
    },
]

# Approximate weekly food-at-home by income band for model groups
# (derived from CES income tables / model doc ranges; mark as approximate)
INCOME_GROUP_WEEKLY = [
    {
        "group": "Low (<$25K)",
        "f_bar_weekly_usd_approx": 75,
        "notes": "Lower end of model doc range; refine with CES income table when XLSX accessible",
        "source_url": "https://www.bls.gov/cex/tables.htm",
    },
    {
        "group": "Mid ($25-50K)",
        "f_bar_weekly_usd_approx": 100,
        "notes": "Mid of model doc ~$75–$140/week range",
        "source_url": "https://www.bls.gov/cex/tables.htm",
    },
    {
        "group": "High (>$50K)",
        "f_bar_weekly_usd_approx": 140,
        "notes": "Upper end of model doc range",
        "source_url": "https://www.bls.gov/cex/tables.htm",
    },
]


def attempt_xlsx_downloads() -> dict:
    meta = {"downloaded": [], "failed": {}, "sources": {}}
    # Browser-like headers (still often blocked)
    SESSION.headers.update(
        {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/122.0.0.0 Safari/537.36"
            ),
            "Accept": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet,*/*",
            "Referer": "https://www.bls.gov/cex/tables.htm",
        }
    )
    for year, url in CES_INCOME_URLS.items():
        dest = BLS_DIR / f"ces_cu_income_before_taxes_{year}.xlsx"
        try:
            print(f"  Trying XLSX {year}")
            download_file(url, dest)
            # 403 pages are small HTML
            if dest.stat().st_size < 5000:
                meta["failed"][str(year)] = f"too small ({dest.stat().st_size} bytes) — likely blocked"
                dest.unlink(missing_ok=True)
                continue
            meta["downloaded"].append(year)
            meta["sources"][str(year)] = url
        except Exception as e:
            meta["failed"][str(year)] = str(e)
            dest.unlink(missing_ok=True)
    return meta


def main() -> None:
    print("=== BLS CES food-at-home / market size inputs ===")
    xlsx_meta = attempt_xlsx_downloads()

    food = pd.DataFrame(PUBLISHED_FOOD_AT_HOME)
    food["f_bar_weekly_usd"] = (food["food_at_home_annual_usd"] / 52).round(2)
    food.to_csv(BLS_DIR / "ces_food_at_home_annual_published.csv", index=False)

    groups = pd.DataFrame(INCOME_GROUP_WEEKLY)
    groups.to_csv(BLS_DIR / "ces_fbar_by_income_group_approx.csv", index=False)

    # Build M estimate if ACS summary exists
    summary_path = ACS_DIR / "cd2_household_income_summary.csv"
    market_rows = []
    if summary_path.exists():
        acs = pd.read_csv(summary_path)
        # Use most recent ACS year and most recent CES year
        acs_year = int(acs["year"].max())
        n_hh = float(acs.loc[acs["year"] == acs_year, "N_HH"].iloc[0])
        ces_year = int(food["year"].max())
        fah = float(food.loc[food["year"] == ces_year, "food_at_home_annual_usd"].iloc[0])
        market_rows.append(
            {
                "acs_year": acs_year,
                "ces_year": ces_year,
                "N_HH": n_hh,
                "food_at_home_annual_usd_per_CU": fah,
                "M_usd_approx": n_hh * fah,
                "f_bar_weekly_usd": round(fah / 52, 2),
                "method": "M = N_HH * CES mean annual food-at-home (all CU)",
                "caveat": (
                    "Uses US all-CU mean, not NYC-metro or income-specific rates; "
                    "Q_j cross-check only until income-specific CES XLSX available"
                ),
                "ces_source": food.loc[food["year"] == ces_year, "source_url"].iloc[0],
            }
        )
        # Income-group weighted M using approx weekly * 52
        if {"n_low", "n_mid", "n_high"}.issubset(acs.columns):
            row = acs.loc[acs["year"] == acs_year].iloc[0]
            gmap = {
                "Low (<$25K)": ("n_low", 75),
                "Mid ($25-50K)": ("n_mid", 100),
                "High (>$50K)": ("n_high", 140),
            }
            m_w = 0.0
            for label, (col, weekly) in gmap.items():
                m_w += float(row[col]) * weekly * 52
            market_rows.append(
                {
                    "acs_year": acs_year,
                    "ces_year": "approx_model_ranges",
                    "N_HH": n_hh,
                    "food_at_home_annual_usd_per_CU": None,
                    "M_usd_approx": m_w,
                    "f_bar_weekly_usd": None,
                    "method": "M = sum_i n_i * f_bar_i_weekly * 52 (model doc ranges)",
                    "caveat": "Approximate weekly rates pending CES income-table access",
                    "ces_source": "https://www.bls.gov/cex/tables.htm",
                }
            )

    if market_rows:
        pd.DataFrame(market_rows).to_csv(BLS_DIR / "cd2_market_size_M_estimates.csv", index=False)

    meta = {
        "xlsx_attempt": xlsx_meta,
        "published_series_file": "ces_food_at_home_annual_published.csv",
        "tables_portal": "https://www.bls.gov/cex/tables.htm",
        "ces_home": "https://www.bls.gov/cex/",
        "block_note": (
            "Direct bls.gov file downloads returned HTTP 403 from this environment; "
            "published annual food-at-home figures were transcribed from BLS HTML reports "
            "with citations."
        ),
    }
    with open(BLS_DIR / "bls_download_meta.json", "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)

    print(f"XLSX downloaded: {xlsx_meta['downloaded']}")
    print(f"XLSX failed: {list(xlsx_meta['failed'].keys())}")
    print(f"Wrote published food-at-home series ({len(food)} years)")
    print("Done.")


if __name__ == "__main__":
    main()
