"""Samuel run: the CD2 model with beta_p not calibrated to N.Y.C. Groceries capacity.

Reuses code/run_model.py and code/model.py unchanged. Two settings, applied at runtime only
(params.py is not edited):

  option1_derived_beta      beta_p at its derived level (USDOT value of time; scale 1.0) in every
                            run (0, 1, 1b, 2, 3, 4). alpha is still calibrated to revenue.
  option2_fixed_beta_sweep  run 2 sweep with beta_p fixed at the base-case calibrated scale; only
                            alpha is refit in each case.

Both are compared with Chris's saved results (results/chris_*) in results/samuel_run/comparison/.
In both settings the two "N.Y.C. Groceries capacity" sweep cases equal the base case, because
capacity only enters the beta_p calibration.

    python code/samuel_run.py            # both options, then the comparison tables
    python code/samuel_run.py compare    # comparison tables only, from saved outputs
"""
from __future__ import annotations

import sys

import pandas as pd

import model as m
import params as P
import run_model as rm
from data_paths import RESULTS_DIR

OUT = RESULTS_DIR / "samuel_run"
OPT1 = "option1_derived_beta"
OPT2 = "option2_fixed_beta_sweep"
SETTINGS = {"chris": None, "option1": OPT1, "option2": OPT2}


def redirect(option: str) -> None:
    """Send run_model outputs to results/samuel_run/<option>/<run> instead of results/chris_<run>."""
    def _out(run: str):
        d = OUT / option / run.replace("chris_", "")
        d.mkdir(parents=True, exist_ok=True)
        return d
    rm._out = _out


def result_path(setting: str, run: str, file: str):
    if setting == "chris":
        return RESULTS_DIR / f"chris_{run}" / file
    return OUT / SETTINGS[setting] / run / file


def read(setting: str, run: str, file: str) -> pd.DataFrame | None:
    p = result_path(setting, run, file)
    return pd.read_csv(p) if p.exists() else None


# --- Runs ---------------------------------------------------------------------------------------

def run_options() -> None:
    calibrate_flag = P.CALIBRATE_BETA_P_LEVEL
    try:
        mkt = m.load_market()
        P.CALIBRATE_BETA_P_LEVEL = True
        base_prm, _ = rm.fit(mkt, m.Params())
        print(f"Base-case calibrated beta_p scale: {base_prm.beta_p_scale:.4f}")

        P.CALIBRATE_BETA_P_LEVEL = False
        print(f"\n=== Option 2: run 2 sweep with beta_p fixed at scale {base_prm.beta_p_scale:.4f} ===")
        redirect(OPT2)
        res = rm.run2(mkt, base_prm)
        print(res.drop_duplicates("case")[["case", "beta_p_scale", "lever_ranking_per_dollar"]].to_string(index=False))

        print("\n=== Option 1: every run with beta_p at the derived level (scale 1.0) ===")
        redirect(OPT1)
        rm.main("all")
    finally:
        P.CALIBRATE_BETA_P_LEVEL = calibrate_flag


# --- Comparison ---------------------------------------------------------------------------------

def calibration_compare(out) -> None:
    cols = ["store", "type", "alpha", "R_j_observed", "R_j_predicted", "ratio_predicted_to_observed",
            "own_price_elasticity"]
    a = read("chris", "run0_calibration", "calibration_by_store.csv")[cols]
    b = read("option1", "run0_calibration", "calibration_by_store.csv")[cols]
    a.merge(b.drop(columns=["type", "R_j_observed"]), on="store", suffixes=("_chris", "_option1")).to_csv(
        out / "calibration_compare.csv", index=False)

    a = read("chris", "run0_calibration", "calibration_summary.csv").rename(columns={"value": "chris"})
    b = read("option1", "run0_calibration", "calibration_summary.csv").rename(columns={"value": "option1"})
    s = a.merge(b, on="item")
    s["item"] = s["item"].str.replace(" (calibrated to N.Y.C. Groceries capacity)", "", regex=False)
    s.to_csv(out / "calibration_summary_compare.csv", index=False)

    a = read("chris", "run0_calibration", "calibration_by_income_group.csv")
    b = read("option1", "run0_calibration", "calibration_by_income_group.csv")
    a.merge(b.drop(columns=["households"]), on="group", suffixes=("_chris", "_option1")).to_csv(
        out / "calibration_by_group_compare.csv", index=False)


def summarize_full(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["sales_vs_capacity"] = df["predicted_sales"] / df["R_j"]
    return (df.groupby(["lever", "theta"], sort=False, dropna=False)
            .agg(stores=("store", "size"), cost_median=("cost", "median"), dcs_total_median=("dcs_total", "median"),
                 dcs_per_dollar_median=("dcs_per_dollar", "median"), dcs_per_dollar_min=("dcs_per_dollar", "min"),
                 dcs_per_dollar_max=("dcs_per_dollar", "max"), low_income_share_median=("low_income_share", "median"),
                 sales_vs_capacity_max=("sales_vs_capacity", "max"))
            .round(3).reset_index())


def full_lever_compare(out) -> None:
    a = summarize_full(read("chris", "run1b_per_store", "per_store_full_lever.csv"))
    b = summarize_full(read("option1", "run1b_per_store", "per_store_full_lever.csv"))
    c = a.merge(b.drop(columns=["stores"]), on=["lever", "theta"], suffixes=("_chris", "_option1"))
    c["dcs_per_dollar_change"] = (c["dcs_per_dollar_median_option1"] - c["dcs_per_dollar_median_chris"]).round(3)
    c.to_csv(out / "full_lever_compare.csv", index=False)


def sweep_compare(out) -> None:
    keep = ["case", "lever", "beta_p_scale", "dcs_per_dollar_median", "low_income_share_median",
            "max_dcs_any_store", "lever_ranking_per_dollar"]
    frames = []
    for setting in SETTINGS:
        d = read(setting, "run2_sweep", "sweep_by_lever.csv")[keep]
        frames.append(d.set_index(["case", "lever"]).add_suffix(f"_{setting}"))
    c = pd.concat(frames, axis=1).reset_index()
    for s in ("option1", "option2"):
        c[f"ranking_same_as_chris_{s}"] = c[f"lever_ranking_per_dollar_{s}"] == c["lever_ranking_per_dollar_chris"]
    c.to_csv(out / "sweep_compare.csv", index=False)


def kappa_compare(out) -> None:
    rows = []
    for setting in ("chris", "option1"):
        d = read(setting, "run3_pass_through", "effective_discount_summary.csv")
        for _, r in d.iterrows():
            rows.append({"setting": setting, "source": "run 3 (beta_p not refit)", "case": r["discount"],
                         "lever": r["lever"], "dcs_total_median": r["dcs_total_median"],
                         "dcs_per_dollar_median": r["dcs_per_dollar_median"],
                         "low_income_share_median": r["low_income_share_median"],
                         "sales_vs_capacity_max": r["sales_vs_capacity_max"]})
    cases = ("Base", "Core basket share low", "Core basket share high")
    levers = ("30% contract at existing store", "N.Y.C. Groceries (new store)")
    for setting in SETTINGS:
        d = read(setting, "run2_sweep", "sweep_by_lever.csv")
        d = d[d["case"].isin(cases) & d["lever"].isin(levers)]
        for _, r in d.iterrows():
            rows.append({"setting": setting, "source": "run 2 sweep", "case": r["case"], "lever": r["lever"],
                         "beta_p_scale": r["beta_p_scale"], "max_dcs_any_store": r["max_dcs_any_store"],
                         "dcs_per_dollar_median": r["dcs_per_dollar_median"],
                         "low_income_share_median": r["low_income_share_median"]})
    pd.DataFrame(rows).to_csv(out / "kappa_compare.csv", index=False)


def capital_compare(out) -> None:
    a = read("chris", "run4_capital_cost", "capital_cost_summary.csv")
    b = read("option1", "run4_capital_cost", "capital_cost_summary.csv")
    if a is None or b is None:
        return
    a.drop(columns=["run"]).merge(b.drop(columns=["run", "stores", "annual_capital"]), on=["lever", "capital_case"],
                                  suffixes=("_chris", "_option1")).to_csv(out / "capital_cost_compare.csv", index=False)


def compare() -> None:
    out = OUT / "comparison"
    out.mkdir(parents=True, exist_ok=True)
    calibration_compare(out)
    full_lever_compare(out)
    sweep_compare(out)
    kappa_compare(out)
    capital_compare(out)
    print(f"\nComparison tables saved to {out.relative_to(RESULTS_DIR.parent)}/")


if __name__ == "__main__":
    if "compare" not in sys.argv[1:]:
        run_options()
    compare()
