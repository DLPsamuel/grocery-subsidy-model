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

REGION_INCOME_FILE = BLS_DIR / "cu-region-by-income-northeast-2023-2024.xlsx"
MSA_FILE = BLS_DIR / "cu-msa-northeast-2-year-average-2023-2024.xlsx"
REGIONAL_CES_PERIOD = "2023-2024"

FOOD_AT_HOME_ITEMS = {
    "food_at_home": "Food at home",
    "cereals_bakery": "Cereals and bakery products",
    "meats_poultry_fish_eggs": "Meats, poultry, fish, and eggs",
    "dairy": "Dairy products",
    "fruits_vegetables": "Fruits and vegetables",
    "other_food_at_home": "Other food at home",
}

MSA_COLS = ["northeast", "new_york", "philadelphia", "boston"]

# ACS B19001 bracket -> [(CES Table 3104 bracket, share of households)].
# B19001_012 ($60-75k) straddles the CES $70k cut; split assuming a uniform
# income distribution within the bracket.
ACS_TO_CES = {
    2: [("lt_15k", 1.0)],
    3: [("lt_15k", 1.0)],
    4: [("15_to_29k", 1.0)],
    5: [("15_to_29k", 1.0)],
    6: [("15_to_29k", 1.0)],
    7: [("30_to_39k", 1.0)],
    8: [("30_to_39k", 1.0)],
    9: [("40_to_49k", 1.0)],
    10: [("40_to_49k", 1.0)],
    11: [("50_to_69k", 1.0)],
    12: [("50_to_69k", 2 / 3), ("70_to_99k", 1 / 3)],
    13: [("70_to_99k", 1.0)],
    14: [("100_to_149k", 1.0)],
    15: [("100_to_149k", 1.0)],
    16: [("150_to_199k", 1.0)],
    17: [("200k_plus", 1.0)],
}

# Model income groups, defined on ACS B19001 brackets (same as download_acs.py).
MODEL_GROUPS = {
    "Low (<$25K)": range(2, 6),
    "Mid ($25-50K)": range(6, 11),
    "High (>$50K)": range(11, 18),
}


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


def _find_item_row(df: pd.DataFrame, label: str, n_cols: int) -> list[float | None]:
    """Values on the first row labelled `label` (regional/MSA tables have no Mean row).

    Footnote markers such as "b/" or "c/" become None.
    """
    target = label.strip().lower()
    for i, v in df[0].items():
        if isinstance(v, str) and v.strip().lower().startswith(target):
            vals = [pd.to_numeric(df.iloc[i, k], errors="coerce") for k in range(1, n_cols + 1)]
            return [float(x) if pd.notna(x) else None for x in vals]
    raise ValueError(f"row '{label}' not found")


def parse_region_income_file(path: Path) -> pd.DataFrame:
    """Table 3104: Northeast region by income before taxes, one row per CES bracket."""
    df = pd.read_excel(path, header=None)
    n = len(INCOME_COLS)
    cols = {
        "consumer_units_thousands": _find_item_row(df, "Number of consumer units", n),
        "income_before_taxes": _find_item_row(df, "Income before taxes", n),
    }
    for key, label in FOOD_AT_HOME_ITEMS.items():
        cols[f"{key}_annual_usd"] = _find_item_row(df, label, n)
    out = pd.DataFrame(cols)
    out.insert(0, "ces_bracket", ["total_northeast"] + INCOME_COLS[1:])
    out.insert(1, "ces_period", REGIONAL_CES_PERIOD)
    out["source_file"] = path.name
    return out


def parse_msa_file(path: Path) -> pd.DataFrame:
    """Table 3004: selected Northeastern MSAs (all consumer units only)."""
    df = pd.read_excel(path, header=None)
    n = len(MSA_COLS)
    cols = {
        "consumer_units_thousands": _find_item_row(df, "Number of consumer units", n),
        "income_before_taxes": _find_item_row(df, "Income before taxes", n),
    }
    for key, label in FOOD_AT_HOME_ITEMS.items():
        cols[f"{key}_annual_usd"] = _find_item_row(df, label, n)
    out = pd.DataFrame(cols)
    out.insert(0, "area", MSA_COLS)
    out.insert(1, "ces_period", REGIONAL_CES_PERIOD)
    ne_fah = out.loc[out["area"] == "northeast", "food_at_home_annual_usd"].iloc[0]
    out["food_at_home_ratio_to_northeast"] = (out["food_at_home_annual_usd"] / ne_fah).round(6)
    out["source_file"] = path.name
    return out


def build_cd2_weighted_outputs(
    region_df: pd.DataFrame, msa_df: pd.DataFrame, prev_market_path: Path
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """f_bar by model group and M, weighting Northeast CES brackets by CD2 ACS B19001 counts."""
    f_b = region_df.set_index("ces_bracket")["food_at_home_annual_usd"].to_dict()
    nyc_scale = float(
        msa_df.loc[msa_df["area"] == "new_york", "food_at_home_ratio_to_northeast"].iloc[0]
    )
    f_acs = {code: sum(f_b[b] * w for b, w in parts) for code, parts in ACS_TO_CES.items()}

    prev = pd.read_csv(prev_market_path).set_index("acs_year") if prev_market_path.exists() else None
    sources = f"{REGION_INCOME_FILE.name}; {MSA_FILE.name}"

    fbar_rows, market_rows = [], []
    for acs_path in sorted(ACS_DIR.glob("cd2_B19001_*.csv")):
        acs = pd.read_csv(acs_path)
        acs_year = int(acs["year"].iloc[0])
        n = {code: float(acs[f"B19001_{code:03d}E"].sum()) for code in ACS_TO_CES}
        n_hh = float(acs["B19001_001E"].sum())
        n_sum = sum(n.values())
        if abs(n_sum - n_hh) > 0.5:
            raise ValueError(f"ACS {acs_year}: bracket sum {n_sum} != B19001_001E {n_hh}")

        m = sum(n[c] * f_acs[c] for c in ACS_TO_CES)
        method = "CD2 ACS B19001 household-weighted Northeast CES brackets"
        for group, codes in MODEL_GROUPS.items():
            n_g = sum(n[c] for c in codes)
            f_g = sum(n[c] * f_acs[c] for c in codes) / n_g
            fbar_rows.append(
                {
                    "acs_year": acs_year,
                    "group": group,
                    "n_hh": n_g,
                    "f_bar_annual_usd": round(f_g, 2),
                    "f_bar_weekly_usd": round(f_g / 52, 2),
                    "f_bar_annual_usd_nyc": round(f_g * nyc_scale, 2),
                    "f_bar_weekly_usd_nyc": round(f_g * nyc_scale / 52, 2),
                    "nyc_scale": nyc_scale,
                    "ces_period": REGIONAL_CES_PERIOD,
                    "method": method,
                    "source_file": sources,
                }
            )
        fbar_rows.append(
            {
                "acs_year": acs_year,
                "group": "CD2 overall",
                "n_hh": n_hh,
                "f_bar_annual_usd": round(m / n_hh, 2),
                "f_bar_weekly_usd": round(m / n_hh / 52, 2),
                "f_bar_annual_usd_nyc": round(m * nyc_scale / n_hh, 2),
                "f_bar_weekly_usd_nyc": round(m * nyc_scale / n_hh / 52, 2),
                "nyc_scale": nyc_scale,
                "ces_period": REGIONAL_CES_PERIOD,
                "method": method,
                "source_file": sources,
            }
        )

        prev_m = float(prev.loc[acs_year, "M_usd_income_weighted"]) if prev is not None and acs_year in prev.index else None
        market_rows.append(
            {
                "acs_year": acs_year,
                "ces_period": REGIONAL_CES_PERIOD,
                "N_HH": n_hh,
                "M_usd_northeast": round(m, 2),
                "M_usd_nyc_scaled": round(m * nyc_scale, 2),
                "f_bar_weekly_cd2": round(m / n_hh / 52, 2),
                "f_bar_weekly_cd2_nyc": round(m * nyc_scale / n_hh / 52, 2),
                "nyc_scale": nyc_scale,
                "M_usd_prev_national_simple_avg": prev_m,
                "pct_change_vs_prev": round(100 * (m * nyc_scale / prev_m - 1), 2) if prev_m else None,
                "source_file": f"{sources}; {acs_path.name}",
            }
        )
    return pd.DataFrame(fbar_rows), pd.DataFrame(market_rows)


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

    outputs = [
        "ces_food_at_home_by_income_bracket.csv",
        "ces_food_at_home_by_income_quintile.csv",
        "ces_fbar_by_income_group_from_xlsx.csv",
        "cd2_market_size_M_from_xlsx.csv",
    ]

    if REGION_INCOME_FILE.exists() and MSA_FILE.exists():
        region_df = parse_region_income_file(REGION_INCOME_FILE)
        msa_df = parse_msa_file(MSA_FILE)
        fbar_ne, market_ne = build_cd2_weighted_outputs(
            region_df, msa_df, BLS_DIR / "cd2_market_size_M_from_xlsx.csv"
        )
        regional_outputs = {
            "ces_food_at_home_northeast_by_income_2023_2024.csv": region_df,
            "ces_food_at_home_northeast_msa_2023_2024.csv": msa_df,
            "ces_fbar_by_income_group_northeast_cd2weighted.csv": fbar_ne,
            "cd2_market_size_M_northeast_cd2weighted.csv": market_ne,
        }
        for name, frame in regional_outputs.items():
            frame.to_csv(BLS_DIR / name, index=False)
        outputs += list(regional_outputs)
        print(fbar_ne[fbar_ne["acs_year"] == fbar_ne["acs_year"].max()].to_string(index=False))
        print(market_ne.to_string(index=False))
    else:
        missing += [p.name for p in (REGION_INCOME_FILE, MSA_FILE) if not p.exists()]

    meta = {
        "income_years": [r["year"] for r in income_rows],
        "quintile_years": [r["year"] for r in quintile_rows],
        "regional_ces_period": REGIONAL_CES_PERIOD,
        "missing_or_failed": missing,
        "outputs": outputs,
    }
    (BLS_DIR / "ces_xlsx_parse_meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    print("Missing:", missing)
    print("Done.")


if __name__ == "__main__":
    main()
