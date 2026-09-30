"""Split f_bar (food-at-home spending per household) by income group into Core Basket and
non-core spending, using the Northeast CES by-income table weighted by Bronx CD2 households.

Core Basket tags and the partial weight come from build_kappa.py; bracket mapping, model
groups and the NYC scale factor come from parse_bls_ces_xlsx.py.

For each CES bracket b and kappa version (partial weight w = 0 low, 0.5 base, 1 high):
  core_b    = in_b + w * partial_b
  noncore_b = food_at_home_b - core_b   (absorbs rounding between categories and the total)
Group values weight brackets by CD2 ACS B19001 household counts and scale to the NYC MSA:
  f_core_g = s * sum(n_b * core_b) / sum(n_b),  kappa_g = f_core_g / f_bar_g
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

from build_kappa import CATEGORIES, PARTIAL_WEIGHT
from parse_bls_ces_xlsx import (
    ACS_DIR,
    ACS_TO_CES,
    BLS_DIR,
    INCOME_COLS,
    MODEL_GROUPS,
    MSA_FILE,
    REGION_INCOME_FILE,
    REGIONAL_CES_PERIOD,
    _find_item_row,
    parse_msa_file,
)

KAPPA_OUT = BLS_DIR / "kappa_core_basket_share_northeast_cd2weighted.csv"
FBAR_OUT = BLS_DIR / "fbar_core_noncore_by_income_group_northeast.csv"
MARKET_CSV = BLS_DIR / "cd2_market_size_M_northeast_cd2weighted.csv"
FBAR_CSV = BLS_DIR / "ces_fbar_by_income_group_northeast_cd2weighted.csv"

KAPPA_VERSIONS = {"low": 0.0, "base": PARTIAL_WEIGHT, "high": 1.0}
BRACKETS = INCOME_COLS[1:]
ALL_GROUPS = {**MODEL_GROUPS, "CD2 overall": range(2, 18)}


def bracket_spending() -> pd.DataFrame:
    """Food at home, 'in' and 'partial' spending per CES bracket (Total Northeast column dropped)."""
    table = pd.read_excel(REGION_INCOME_FILE, header=None)
    n = len(INCOME_COLS)

    def row(label: str) -> pd.Series:
        return pd.Series(_find_item_row(table, label, n)[1:], index=BRACKETS)

    tag = pd.Series(CATEGORIES)
    return pd.DataFrame({
        "food_at_home": row("Food at home"),
        "in": sum(row(c) for c in tag[tag == "in"].index),
        "partial": sum(row(c) for c in tag[tag == "partial"].index),
        "out": sum(row(c) for c in tag[tag == "out"].index),
    })


def per_acs_bracket(values: pd.Series) -> dict[int, float]:
    """CES bracket values -> ACS B19001 bracket values (splitting bracket 012)."""
    return {code: sum(values[b] * w for b, w in parts) for code, parts in ACS_TO_CES.items()}


def main() -> None:
    spend = bracket_spending()
    msa = parse_msa_file(MSA_FILE)
    s = float(msa.loc[msa["area"] == "new_york", "food_at_home_ratio_to_northeast"].iloc[0])
    f_acs = per_acs_bracket(spend["food_at_home"])
    core_acs = {
        version: per_acs_bracket(spend["in"] + w * spend["partial"])
        for version, w in KAPPA_VERSIONS.items()
    }
    sources = f"{REGION_INCOME_FILE.name}; {MSA_FILE.name}"

    rows = []
    for acs_path in sorted(ACS_DIR.glob("cd2_B19001_*.csv")):
        acs = pd.read_csv(acs_path)
        acs_year = int(acs["year"].iloc[0])
        n = {code: float(acs[f"B19001_{code:03d}E"].sum()) for code in ACS_TO_CES}
        for version, core in core_acs.items():
            for group, codes in ALL_GROUPS.items():
                n_g = sum(n[c] for c in codes)
                f_g = sum(n[c] * f_acs[c] for c in codes) / n_g
                c_g = sum(n[c] * core[c] for c in codes) / n_g
                rows.append({
                    "acs_year": acs_year,
                    "kappa_version": version,
                    "group": group,
                    "n_hh": n_g,
                    "kappa": round(c_g / f_g, 4),
                    "f_bar_annual_usd": round(f_g, 2),
                    "f_core_annual_usd": round(c_g, 2),
                    "f_noncore_annual_usd": round(f_g - c_g, 2),
                    "f_bar_annual_usd_nyc": round(f_g * s, 2),
                    "f_core_annual_usd_nyc": round(c_g * s, 2),
                    "f_noncore_annual_usd_nyc": round((f_g - c_g) * s, 2),
                    "f_bar_weekly_usd_nyc": round(f_g * s / 52, 2),
                    "f_core_weekly_usd_nyc": round(c_g * s / 52, 2),
                    "f_noncore_weekly_usd_nyc": round((f_g - c_g) * s / 52, 2),
                    "M_core_usd_nyc": round(n_g * c_g * s, 2),
                    "M_noncore_usd_nyc": round(n_g * (f_g - c_g) * s, 2),
                    "nyc_scale": s,
                    "ces_period": REGIONAL_CES_PERIOD,
                    "source_file": f"{sources}; {acs_path.name}",
                })
    out = pd.DataFrame(rows)

    check_against_fbar_outputs(out)

    kappa = (
        out.pivot_table(index=["acs_year", "group"], columns="kappa_version", values="kappa", sort=False)
        .reindex(columns=list(KAPPA_VERSIONS))
        .add_prefix("kappa_")
        .reset_index()
    )
    kappa.columns.name = None
    kappa.to_csv(KAPPA_OUT, index=False)
    out.to_csv(FBAR_OUT, index=False)

    latest = out[out["acs_year"] == out["acs_year"].max()]
    cols = ["kappa_version", "group", "n_hh", "kappa", "f_bar_weekly_usd_nyc",
            "f_core_weekly_usd_nyc", "f_noncore_weekly_usd_nyc", "M_core_usd_nyc", "M_noncore_usd_nyc"]
    print(latest[cols].to_string(index=False))
    print(f"\nSaved {KAPPA_OUT.name}, {FBAR_OUT.name}")


def check_against_fbar_outputs(out: pd.DataFrame) -> None:
    """Core + non-core must reproduce the f_bar and M written by parse_bls_ces_xlsx.py."""
    fbar = pd.read_csv(FBAR_CSV).set_index(["acs_year", "group"])["f_bar_annual_usd_nyc"]
    market = pd.read_csv(MARKET_CSV).set_index("acs_year")["M_usd_nyc_scaled"]
    for _, r in out.iterrows():
        expected = fbar.loc[(r["acs_year"], r["group"])]
        total = r["f_core_annual_usd_nyc"] + r["f_noncore_annual_usd_nyc"]
        if abs(total - expected) > 0.05:
            raise ValueError(f"{r['acs_year']} {r['kappa_version']} {r['group']}: {total} != {expected}")
    groups = out[out["group"] != "CD2 overall"]
    m = groups.groupby(["acs_year", "kappa_version"])[["M_core_usd_nyc", "M_noncore_usd_nyc"]].sum().sum(axis=1)
    for (acs_year, version), total in m.items():
        if abs(total - market.loc[acs_year]) > 5:
            raise ValueError(f"{acs_year} {version}: M_core + M_noncore {total} != M {market.loc[acs_year]}")


if __name__ == "__main__":
    main()
