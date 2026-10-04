"""Chris's runs 0, 1, 1b, 2 and 3 of the CD2 model (docs/MODEL_PLAN_AND_ASSIGNMENTS.md §2).

Run 3 is Samuel's in the plan; this is Chris's own version, kept under chris_run3_* so the
two are not confused.

    python code/run_model.py            # all runs
    python code/run_model.py run0       # calibration check only (also: run1, run2, run3)

Outputs go to results/<run_name>/.
  chris_run0_calibration: predicted vs observed sales by store, store constants, price elasticities
  chris_run1_base:        Delta CS against subsidy for every lever and store (the budget sweep),
                    and the minimum subsidy that reaches each consumer-surplus target
  chris_run1b_per_store:  one row per store and lever at the full lever (Tax_j, Rent_j, 30%)
  chris_run2_sweep:       robustness: every lever re-run with alpha and the beta_p level recalibrated
                    for each alternative parameter or data case
  chris_run3_pass_through: FRESH / rent at theta 0.25, 0.5, 0.75 (+ 1.0 best case), and the
                    30% discount on the core basket (~18% of the bill) vs on the whole basket
"""
from __future__ import annotations

import sys

import numpy as np
import pandas as pd

import model as m
import params as P
from data_paths import RESULTS_DIR

GRID = np.linspace(0, 1, 21)  # fraction of the lever's maximum (Tax_j, Rent_j, 30% discount)


def _out(run: str):
    d = RESULTS_DIR / run
    d.mkdir(parents=True, exist_ok=True)
    return d


def run0(mkt: m.Market, prm: m.Params, alpha: dict) -> pd.DataFrame:
    ex = mkt.existing
    p0 = m.base_price(mkt)
    s = m.shares(m.utility(mkt, prm, alpha, p0, ex))
    R_hat = m.sales(mkt, prm, s, p0)
    st = mkt.stores[ex]
    cal = pd.DataFrame({
        "store": st["short"], "type": st["type"], "alpha": st["type"].map(alpha),
        "R_j_observed": st["R"], "R_j_predicted": R_hat[ex].round(),
        "ratio_predicted_to_observed": (R_hat[ex] / st["R"]).round(3),
    })
    # Own-price elasticity of store demand, logit: beta_p,g * k_g * p_j * (1 - s_ij), sales-weighted
    n = mkt.groups["n"].to_numpy()[:, None]
    bp = mkt.groups["group"].map(prm.bp()).to_numpy()[:, None]
    el = bp * m.baskets_per_trip(mkt, prm) * p0 * (1 - s)
    w = n * s
    cal["own_price_elasticity"] = ((el * w)[:, ex].sum(0) / w[:, ex].sum(0)).round(2)

    grp = []
    for g in m.GROUPS:
        rows = (mkt.groups["group"] == g).to_numpy()
        ng = n[rows]
        grp.append({
            "group": g, "households": int(ng.sum()), "beta_p": round(prm.bp()[g], 4),
            "baskets_per_trip": round(52 * mkt.fbar[g] / (prm.trips * mkt.p_bar), 3),
            "share_of_trips_to_9_stores": round(float((ng * s[rows][:, ex]).sum() / ng.sum()), 3),
            "own_price_elasticity": round(float((el * w)[rows][:, ex].sum() / w[rows][:, ex].sum()), 2),
        })
    out = _out("chris_run0_calibration")
    cal.to_csv(out / "calibration_by_store.csv", index=False)
    pd.DataFrame(grp).to_csv(out / "calibration_by_income_group.csv", index=False)
    spend = m.total_spending(mkt, prm)
    pd.DataFrame([
        {"item": "9-store predicted sales / CD2 spending", "value": round(R_hat[ex].sum() / spend, 4)},
        {"item": "9-store observed revenue / M", "value": round(st["R"].sum() / spend, 4)},
        {"item": "model CD2 spending ($/yr)", "value": round(spend)},
        {"item": "p_bar ($/basket)", "value": round(mkt.p_bar, 4)},
        {"item": "beta_p level scale (calibrated to N.Y.C. Groceries capacity)", "value": round(prm.beta_p_scale, 4)},
        {"item": "store constant alpha, supermarket", "value": round(float(alpha["supermarket"]), 4)},
        {"item": "store constant alpha, small independent", "value": round(float(alpha["small"]), 4)},
    ]).to_csv(out / "calibration_summary.csv", index=False)
    return cal


def _row(lever, store, theta, x, res: m.LeverResult) -> dict:
    d = res.dcs
    return {
        "lever": lever, "store": store, "theta": theta, "lever_fraction": round(x, 3),
        "cost": round(res.cost), "dcs_total": round(d["Total"]),
        "dcs_low": round(d["Low"]), "dcs_mid": round(d["Mid"]), "dcs_high": round(d["High"]),
        "low_income_share": round(d["Low"] / d["Total"], 3) if d["Total"] > 0 else np.nan,
        **{k: (round(v, 4) if isinstance(v, float) else v) for k, v in res.extra.items()},
    }


def lever_curves(mkt: m.Market, prm: m.Params, alpha: dict) -> pd.DataFrame:
    rows = []
    st = mkt.stores
    for j in np.flatnonzero(mkt.existing):
        name = st.at[j, "short"]
        for theta in P.THETA_FRESH:
            for x in GRID:
                rows.append(_row("FRESH tax break", name, theta, x,
                                 m.lever_cost_cut(mkt, prm, alpha, j, x * st.at[j, "tax"], theta)))
                rows.append(_row("Rent subsidy", name, theta, x,
                                 m.lever_cost_cut(mkt, prm, alpha, j, x * st.at[j, "rent"], theta)))
        for x in GRID:
            rows.append(_row("30% contract at existing store", name, P.THETA_CONTRACT, x,
                             m.lever_contract(mkt, prm, alpha, j, x * P.DISCOUNT)))
    j_new = int(np.flatnonzero(st["store"] == m.NEW_STORE)[0])
    for x in GRID:
        rows.append(_row("N.Y.C. Groceries (new store)", st.at[j_new, "short"], P.THETA_CONTRACT, x,
                         m.lever_contract(mkt, prm, alpha, j_new, x * P.DISCOUNT)))
    return pd.DataFrame(rows)


def subsidy_for_targets(curves: pd.DataFrame) -> pd.DataFrame:
    """Invert each Delta CS(s) curve: the minimum subsidy that reaches each target."""
    rows = []
    for (lever, store, theta), c in curves.groupby(["lever", "store", "theta"], sort=False):
        c = c.sort_values("lever_fraction")
        cost, dcs, low = c["cost"].to_numpy(float), c["dcs_total"].to_numpy(float), c["low_income_share"].to_numpy(float)
        for target in P.CS_TARGETS:
            hit = np.flatnonzero(dcs >= target)
            if hit.size == 0:
                s_star, ok, share = np.nan, False, np.nan
            else:
                i = hit[0]
                if i == 0 or dcs[i] == dcs[i - 1]:
                    s_star = cost[i]
                else:  # linear interpolation between grid points
                    s_star = cost[i - 1] + (target - dcs[i - 1]) * (cost[i] - cost[i - 1]) / (dcs[i] - dcs[i - 1])
                ok, share = True, low[i]
            rows.append({
                "cs_target": target, "lever": lever, "store": store, "theta": theta,
                "min_subsidy": round(s_star) if ok else np.nan,
                "subsidy_per_dollar_cs": round(s_star / target, 3) if ok else np.nan,
                "low_income_share": share,
                "max_dcs_within_lever": round(dcs.max()),
                "reachable": "yes" if ok else "not reachable",
            })
    return pd.DataFrame(rows)


def full_lever(mkt: m.Market, prm: m.Params, alpha: dict, thetas=P.THETA_FRESH) -> pd.DataFrame:
    """One row per lever and store at the full lever (Tax_j, Rent_j, 30% discount)."""
    st = mkt.stores
    rows = []
    for j in np.flatnonzero(mkt.existing):
        name = st.at[j, "short"]
        for theta in thetas:
            rows.append(_row("FRESH tax break", name, theta, 1.0, m.lever_cost_cut(mkt, prm, alpha, j, st.at[j, "tax"], theta)))
            rows.append(_row("Rent subsidy", name, theta, 1.0, m.lever_cost_cut(mkt, prm, alpha, j, st.at[j, "rent"], theta)))
        rows.append(_row("30% contract at existing store", name, P.THETA_CONTRACT, 1.0,
                         m.lever_contract(mkt, prm, alpha, j, P.DISCOUNT)))
    j_new = int(np.flatnonzero(st["store"] == m.NEW_STORE)[0])
    rows.append(_row("N.Y.C. Groceries (new store)", st.at[j_new, "short"], P.THETA_CONTRACT, 1.0,
                     m.lever_contract(mkt, prm, alpha, j_new, P.DISCOUNT)))
    full = pd.DataFrame(rows)
    full["dcs_per_dollar"] = (full["dcs_total"] / full["cost"]).round(3)
    return full


def run1(mkt: m.Market, prm: m.Params, alpha: dict) -> tuple[pd.DataFrame, pd.DataFrame]:
    curves = lever_curves(mkt, prm, alpha)
    targets = subsidy_for_targets(curves)
    out = _out("chris_run1_base")
    curves.to_csv(out / "lever_curves.csv", index=False)
    targets.to_csv(out / "subsidy_by_cs_target.csv", index=False)

    full = curves[curves["lever_fraction"] == 1.0].copy()
    full["dcs_per_dollar"] = (full["dcs_total"] / full["cost"]).round(3)
    # N.Y.C. Groceries with Tax_j = 0 (city-owned lot; MAIN spec v2 Part 2 note)
    st = mkt.stores
    j_new = int(np.flatnonzero(st["store"] == m.NEW_STORE)[0])
    r = m.lever_contract(m.with_stores(mkt, tax_zero=0.0), prm, alpha, j_new, P.DISCOUNT, tax_col="tax_zero")
    extra = _row("N.Y.C. Groceries (new store), Tax_j = 0", st.at[j_new, "short"], P.THETA_CONTRACT, 1.0, r)
    extra["dcs_per_dollar"] = round(extra["dcs_total"] / extra["cost"], 3)
    full = pd.concat([full, pd.DataFrame([extra])], ignore_index=True)
    full.sort_values(["lever", "theta", "dcs_per_dollar"], ascending=[True, True, False]).to_csv(
        _out("chris_run1b_per_store") / "per_store_full_lever.csv", index=False)
    who_gains(mkt, prm, alpha).to_csv(out / "dcs_by_tract.csv", index=False)
    return curves, targets


def pass_through_table(full: pd.DataFrame) -> pd.DataFrame:
    """Median Delta CS per $ by lever and theta, and the theta at which FRESH/rent would match
    the contract per dollar (Delta CS per $ is proportional to theta for these levers)."""
    full = full[~full["lever"].str.contains("Tax_j = 0")]
    t = (full.groupby(["lever", "theta"])
         .agg(stores=("store", "size"), dcs_per_dollar_median=("dcs_per_dollar", "median"),
              dcs_per_dollar_min=("dcs_per_dollar", "min"), dcs_per_dollar_max=("dcs_per_dollar", "max"),
              max_dcs_any_store=("dcs_total", "max"), low_income_share_median=("low_income_share", "median"))
         .reset_index())
    contract = t.loc[t["lever"] == "30% contract at existing store", "dcs_per_dollar_median"].iloc[0]
    cut = t["lever"].isin(["FRESH tax break", "Rent subsidy"])
    t.loc[cut, "theta_to_match_contract"] = (t.loc[cut, "theta"] * contract / t.loc[cut, "dcs_per_dollar_median"]).round(2)
    return t


def who_gains(mkt: m.Market, prm: m.Params, alpha: dict) -> pd.DataFrame:
    """Delta CS per household by tract and income group: N.Y.C. Groceries (discount only) vs the
    same 30% contract at Key Food, the largest existing store."""
    st = mkt.stores
    j_new = int(np.flatnonzero(st["store"] == m.NEW_STORE)[0])
    j_kf = int(np.flatnonzero(st["short"] == "Key Food")[0])
    g = mkt.groups.copy()
    for label, j in (("nycg", j_new), ("keyfood", j_kf)):
        r = m.lever_contract(mkt, prm, alpha, j, P.DISCOUNT)
        g[f"dcs_{label}"] = r.by_i.round()
        g[f"dcs_per_hh_{label}"] = (r.by_i / g["n"]).round(2)
        g[f"miles_to_{label}"] = mkt.dist[:, j].round(3)
    return g


# --- Chris run 2: robustness sweep --------------------------------------------------------------------

def fit(mkt: m.Market, prm: m.Params, capacity_mult: float = 1.0) -> tuple[m.Params, dict]:
    """Calibrate the beta_p level and the store constants for this parameter set."""
    if P.CALIBRATE_BETA_P_LEVEL:
        prm = prm.with_(beta_p_scale=m.calibrate_beta_p_scale(mkt, prm, capacity_mult=capacity_mult))
    return prm, m.calibrate(mkt, prm)


def sweep_cases(mkt: m.Market, prm: m.Params) -> list[tuple[str, m.Market, m.Params, float]]:
    s = mkt.stores
    return [
        ("Base", mkt, prm, 1.0),
        ("Distance effect +40% (Cao et al. 2026)", mkt, prm.with_(beta_d=P.BETA_D * P.BETA_D_SCALE_HIGH), 1.0),
        ("Store size term high (SQFT main effect, Hillier)", mkt, prm.with_(gamma_sq=P.GAMMA_SQ_HIGH), 1.0),
        ("High-income distance effect 25% weaker", mkt, prm.with_(high_income_distance_scale=P.HIGH_INCOME_DISTANCE_SCALE), 1.0),
        ("40 trips/yr (Dannefer et al. 2016)", mkt, prm.with_(trips=P.T_TRIPS_ALT), 1.0),
        ("Core basket share low", mkt, prm.with_(kappa_version="kappa_low"), 1.0),
        ("Core basket share high", mkt, prm.with_(kappa_version="kappa_high"), 1.0),
        ("Revenue low ($698/sq ft)", m.with_stores(mkt, R=s["R_low"]), prm, 1.0),
        ("Revenue high ($845/sq ft)", m.with_stores(mkt, R=s["R_high"]), prm, 1.0),
        ("N.Y.C. Groceries capacity -25%", mkt, prm, 0.75),
        ("N.Y.C. Groceries capacity +25%", mkt, prm, 1.25),
        ("Food Fair tax, floor-area split", m.with_stores(mkt, tax=s["tax_high"].fillna(s["tax"])), prm, 1.0),
    ]


def run2(mkt: m.Market, prm: m.Params) -> pd.DataFrame:
    rows = []
    for name, mk, pr, cap in sweep_cases(mkt, prm):
        pr, alpha = fit(mk, pr, cap)
        full = full_lever(mk, pr, alpha, thetas=(P.THETA_BASE,))
        for lever, f in full.groupby("lever", sort=False):
            rows.append({
                "case": name, "beta_p_scale": round(pr.beta_p_scale, 4),
                "alpha_supermarket": round(float(alpha["supermarket"]), 3), "alpha_small": round(float(alpha["small"]), 3),
                "lever": lever, "max_dcs_any_store": f["dcs_total"].max(),
                "dcs_per_dollar_median": f["dcs_per_dollar"].median(),
                "dcs_per_dollar_min": f["dcs_per_dollar"].min(), "dcs_per_dollar_max": f["dcs_per_dollar"].max(),
                "low_income_share_median": f["low_income_share"].median(),
                "reaches_50k": bool(f["dcs_total"].max() >= 50_000),
                "reaches_250k": bool(f["dcs_total"].max() >= 250_000),
            })
        print(f"  Chris run 2: {name} done (beta_p scale {pr.beta_p_scale:.3f})")
    res = pd.DataFrame(rows)
    rank = (res.sort_values(["case", "dcs_per_dollar_median"], ascending=[True, False])
            .groupby("case", sort=False)["lever"].apply(lambda x: " > ".join(x)))
    res["lever_ranking_per_dollar"] = res["case"].map(rank)
    out = _out("chris_run2_sweep")
    res.to_csv(out / "sweep_by_lever.csv", index=False)
    return res


# --- Chris run 3: pass-through and effective discount ------------------------------------------

THETA_RUN3 = P.THETA_FRESH + (1.0,)  # team set + full pass-through as FRESH's best case


def run3(mkt: m.Market, prm: m.Params, alpha: dict) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Chris's version of run 3 (Samuel's in the plan).

    (a) FRESH tax break and rent subsidy at each theta: Delta CS per $, and the largest gain
        any store can reach (the lever is capped by the tax / rent the store owes).
    (b) N.Y.C. Groceries and the contract at each existing store: 30% off the core basket
        (kappa_g ~ 0.61, so ~18% off the bill; the RFP design) vs 30% off the whole basket.
    """
    full = full_lever(mkt, prm, alpha, thetas=THETA_RUN3)
    pt = pass_through_table(full)
    pt.insert(0, "run", "Chris run 3")
    rows = []
    st = mkt.stores
    p0 = m.base_price(mkt)
    base_sales = m.sales(mkt, prm, m.shares(m.utility(mkt, prm, alpha, p0, mkt.existing)), p0)
    for label, kv in (("30% off core basket (~18% of bill)", prm.kappa_version), ("30% off whole basket", "whole_basket")):
        pk = prm.with_(kappa_version=kv)
        for j in range(len(st)):
            r = m.lever_contract(mkt, pk, alpha, j, P.DISCOUNT)
            rows.append({
                "run": "Chris run 3", "discount": label, "store": st.at[j, "short"],
                "lever": "N.Y.C. Groceries (new store)" if st.at[j, "status"] != "existing" else "30% contract at existing store",
                "cost": round(r.cost), "dcs_total": round(r.dcs["Total"]),
                "dcs_per_dollar": round(r.dcs["Total"] / r.cost, 3),
                "low_income_share": round(r.dcs["Low"] / r.dcs["Total"], 3),
                "predicted_sales": round(r.extra["predicted_sales"]),
                "sales_vs_capacity_R_j": round(r.extra["predicted_sales"] / st.at[j, "R"], 2),
                # existing stores: growth over the model's own baseline (the planned store has none)
                "sales_vs_predicted_baseline": (round(r.extra["predicted_sales"] / base_sales[j], 2)
                                                if st.at[j, "status"] == "existing" else np.nan),
            })
    cut = pd.DataFrame(rows)
    out = _out("chris_run3_pass_through")
    full.insert(0, "run", "Chris run 3")
    full.to_csv(out / "per_store_by_theta.csv", index=False)
    pt.to_csv(out / "pass_through_summary.csv", index=False)
    cut.to_csv(out / "effective_discount_core_vs_whole.csv", index=False)
    summ = (cut.groupby(["discount", "lever"])
            .agg(stores=("store", "size"), dcs_total_median=("dcs_total", "median"), cost_median=("cost", "median"),
                 dcs_per_dollar_median=("dcs_per_dollar", "median"), low_income_share_median=("low_income_share", "median"),
                 sales_vs_capacity_max=("sales_vs_capacity_R_j", "max"),
                 sales_growth_vs_baseline_median=("sales_vs_predicted_baseline", "median"))
            .reset_index())
    summ.insert(0, "run", "Chris run 3")
    summ.to_csv(out / "effective_discount_summary.csv", index=False)
    return pt, summ


def main(which: str = "all") -> None:
    mkt = m.load_market()
    prm, alpha = fit(mkt, m.Params())
    cal = run0(mkt, prm, alpha)
    print(f"Chris run 0: beta_p level scale {prm.beta_p_scale:.4f} ->",
          {g: round(v, 4) for g, v in prm.bp().items()})
    print("Store constants", {k: round(float(v), 3) for k, v in alpha.items()})
    print(cal.to_string(index=False))
    if which in ("all", "run1"):
        run1(mkt, prm, alpha)
        print("\nChris run 1 / 1b: saved")
    if which in ("all", "run3"):
        pt, cut = run3(mkt, prm, alpha)
        print("\nChris run 3: pass-through (FRESH / rent) and effective discount (contracts)")
        print(pt.to_string(index=False))
        print(cut.to_string(index=False))
    if which in ("all", "run2"):
        res = run2(mkt, m.Params())
        print("\nChris run 2: lever ranking by Delta CS per $ (FRESH/rent at theta = 0.5)")
        print(res.drop_duplicates("case")[["case", "beta_p_scale", "lever_ranking_per_dollar"]].to_string(index=False))
    print(f"\nSaved to {RESULTS_DIR.relative_to(RESULTS_DIR.parent)}/")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "all")
