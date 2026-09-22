"""Parse manually downloaded CES income/quintile XLSX into clean food-at-home tables."""
from __future__ import annotations

import json
import warnings
from pathlib import Path

import pandas as pd

warnings.filterwarnings("ignore", category=UserWarning)

BLS_DIR = Path(__file__).resolve().parents[1] / "data" / "bls"
ACS_DIR = Path(__file__).resolve().parents[1] / "data" / "acs"

INCOME_COLS = [
    "all_consumer_units",
    "lt_15k",
    "15_to_29k",
    "30_to_39k",
    "40_to_49k",
    "50_to_69k",
    "70_to_99k",
    "100_to_149k",
    "150_to_199k",
    "200k_plus",
]

QUINTILE_COLS = [
    "all_consumer_units",
    "lowest_20",
    "second_20",
    "third_20",
    "fourth_20",
    "highest_20",
]


def _find_mean_row(df: pd.DataFrame, label: str) -> pd.Series | None:
    for i, v in df[0].items():
        if isinstance(v, str) and v.strip().lower() == label.lower():
            # next non-empty "Mean" row
            for j in range(i + 1, min(i + 6, len(df))):
                lab = df.iloc[j, 0]
                if isinstance(lab, str) and lab.strip().lower() == "mean":
                    return df.iloc[j]
            return None
    return None


def parse_income_file(path: Path, year: int) -> dict | None:
    df = pd.read_excel(path, header=None)
    row = _find_mean_row(df, "Food at home")
    if row is None:
        return None
    vals = [pd.to_numeric(row.iloc[k], errors="coerce") for k in range(1, 11)]
    out = {"year": year, "table": "income_before_taxes", "item": "food_at_home_annual_usd"}
    for name, val in zip(INCOME_COLS, vals):
        out[name] = float(val) if pd.notna(val) else None
    # Model income groups: Low <$25k ~ lt_15k + 15_to_29k avg; Mid $25-50k; High >$50k
    low = [out["lt_15k"], out["15_to_29k"]]
    mid = [out["30_to_39k"], out["40_to_49k"]]
    high = [
        out["50_to_69k"],
        out["70_to_99k"],
        out["100_to_149k"],
        out["150_to_199k"],
        out["200k_plus"],
    ]
    out["model_low_lt25k_approx"] = round(sum(x for x in low if x) / len([x for x in low if x]), 2)
    out["model_mid_25_50k_approx"] = round(sum(x for x in mid if x) / len([x for x in mid if x]), 2)
    out["model_high_gt50k_approx"] = round(sum(x for x in high if x) / len([x for x in high if x]), 2)
    out["f_bar_weekly_all"] = round(out["all_consumer_units"] / 52, 2) if out["all_consumer_units"] else None
    out["source_file"] = path.name
    return out


def parse_quintile_file(path: Path, year: int) -> dict | None:
    df = pd.read_excel(path, header=None)
    row = _find_mean_row(df, "Food at home")
    if row is None:
        return None
    vals = [pd.to_numeric(row.iloc[k], errors="coerce") for k in range(1, 7)]
    out = {"year": year, "table": "income_quintiles", "item": "food_at_home_annual_usd"}
    for name, val in zip(QUINTILE_COLS, vals):
        out[name] = float(val) if pd.notna(val) else None
    out["f_bar_weekly_all"] = round(out["all_consumer_units"] / 52, 2) if out["all_consumer_units"] else None
    out["source_file"] = path.name
    return out


def main() -> None:
    income_rows = []
    quintile_rows = []
    missing = []

    for year in range(2020, 2025):
        inc = BLS_DIR / f"cu-income-before-taxes-{year}.xlsx"
        q = BLS_DIR / f"cu-income-quintiles-before-taxes-{year}.xlsx"
        if inc.exists():
            parsed = parse_income_file(inc, year)
            if parsed:
                income_rows.append(parsed)
                print(f"income {year}: all-CU food-at-home ${parsed['all_consumer_units']:,.0f}")
            else:
                missing.append(f"{inc.name}: no Food at home Mean row")
        else:
            missing.append(str(inc.name))

        if q.exists():
            parsed = parse_quintile_file(q, year)
            if parsed:
                quintile_rows.append(parsed)
                print(
                    f"quintiles {year}: all-CU ${parsed['all_consumer_units']:,.0f}; "
                    f"Q1 ${parsed['lowest_20']:,.0f} … Q5 ${parsed['highest_20']:,.0f}"
                )
            else:
                missing.append(f"{q.name}: no Food at home Mean row")
        else:
            missing.append(str(q.name))

    inc_df = pd.DataFrame(income_rows)
    q_df = pd.DataFrame(quintile_rows)
    inc_df.to_csv(BLS_DIR / "ces_food_at_home_by_income_bracket.csv", index=False)
    q_df.to_csv(BLS_DIR / "ces_food_at_home_by_income_quintile.csv", index=False)

    # Weekly f_bar by model groups from latest income table
    if not inc_df.empty:
        latest = inc_df.sort_values("year").iloc[-1]
        fbar = pd.DataFrame(
            [
                {
                    "group": "Low (<$25K)",
                    "f_bar_weekly_usd": round(latest["model_low_lt25k_approx"] / 52, 2),
                    "f_bar_annual_usd": latest["model_low_lt25k_approx"],
                    "ces_year": int(latest["year"]),
                    "method": "avg of CES brackets <$15k and $15–30k",
                    "source_file": latest["source_file"],
                },
                {
                    "group": "Mid ($25-50K)",
                    "f_bar_weekly_usd": round(latest["model_mid_25_50k_approx"] / 52, 2),
                    "f_bar_annual_usd": latest["model_mid_25_50k_approx"],
                    "ces_year": int(latest["year"]),
                    "method": "avg of CES brackets $30–40k and $40–50k",
                    "source_file": latest["source_file"],
                },
                {
                    "group": "High (>$50K)",
                    "f_bar_weekly_usd": round(latest["model_high_gt50k_approx"] / 52, 2),
                    "f_bar_annual_usd": latest["model_high_gt50k_approx"],
                    "ces_year": int(latest["year"]),
                    "method": "avg of CES brackets $50k+",
                    "source_file": latest["source_file"],
                },
                {
                    "group": "All consumer units",
                    "f_bar_weekly_usd": latest["f_bar_weekly_all"],
                    "f_bar_annual_usd": latest["all_consumer_units"],
                    "ces_year": int(latest["year"]),
                    "method": "CES all consumer units",
                    "source_file": latest["source_file"],
                },
            ]
        )
        fbar.to_csv(BLS_DIR / "ces_fbar_by_income_group_from_xlsx.csv", index=False)

        # Update M estimates with ACS CD2 counts
        summary_path = ACS_DIR / "cd2_household_income_summary.csv"
        market_rows = []
        if summary_path.exists():
            acs = pd.read_csv(summary_path)
            for _, acs_row in acs.iterrows():
                acs_year = int(acs_row["year"])
                # nearest CES year
                ces = inc_df.iloc[(inc_df["year"] - acs_year).abs().argsort()[:1]].iloc[0]
                n_hh = float(acs_row["N_HH"])
                m_all = n_hh * float(ces["all_consumer_units"])
                m_w = (
                    float(acs_row["n_low"]) * float(ces["model_low_lt25k_approx"])
                    + float(acs_row["n_mid"]) * float(ces["model_mid_25_50k_approx"])
                    + float(acs_row["n_high"]) * float(ces["model_high_gt50k_approx"])
                )
                market_rows.append(
                    {
                        "acs_year": acs_year,
                        "ces_year": int(ces["year"]),
                        "N_HH": n_hh,
                        "M_usd_all_cu_mean": round(m_all, 2),
                        "M_usd_income_weighted": round(m_w, 2),
                        "f_bar_weekly_all": ces["f_bar_weekly_all"],
                        "food_at_home_annual_all_cu": ces["all_consumer_units"],
                        "source_file": ces["source_file"],
                    }
                )
            pd.DataFrame(market_rows).to_csv(
                BLS_DIR / "cd2_market_size_M_from_xlsx.csv", index=False
            )
            print(pd.DataFrame(market_rows).to_string(index=False))

    meta = {
        "income_years": [r["year"] for r in income_rows],
        "quintile_years": [r["year"] for r in quintile_rows],
        "missing_or_failed": missing,
        "outputs": [
            "ces_food_at_home_by_income_bracket.csv",
            "ces_food_at_home_by_income_quintile.csv",
            "ces_fbar_by_income_group_from_xlsx.csv",
            "cd2_market_size_M_from_xlsx.csv",
        ],
    }
    (BLS_DIR / "ces_xlsx_parse_meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    print("Missing:", missing)
    print("Done.")


if __name__ == "__main__":
    main()
