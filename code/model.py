"""Store-choice logit for Bronx CD2: utility -> shares -> logsum -> Delta CS, and the levers.

Follows MAIN_NYC_Grocery_Subsidy_Model_Specification_v2.md §1, with the changes the team
agreed on 2026-10-02:
  - store-type constants alpha (supermarket / small independent), calibrated to revenue;
  - an outside option ("other stores"), V_i0 = 0;
  - T = 52 trips/yr, with price entering per trip: k_g * (p_j - p_bar).

Utility for group i = (tract t, income g) at store j:
    V_ij = alpha_type(j) + GAMMA_SQ * sqft_j/1000 - beta_p,g * k_g * (p_j - p_bar) + BETA_D * d_tj
Annual welfare change (Small & Rosen 1981):
    Delta CS = sum_i n_i * T / beta_p,g * (logsum_i_post - logsum_i_pre)
"""
from __future__ import annotations

from dataclasses import dataclass, field, replace

import numpy as np
import pandas as pd

import params as P
from data_paths import ACS_DIR, BLS_DIR, DESC_STATS_V2_DIR, DISTANCE_DIR, PRICES_DIR  # noqa: F401

GROUPS = ("Low", "Mid", "High")
NEW_STORE = "N.Y.C. GROCERIES (PLANNED)"


@dataclass
class Params:
    gamma_sq: float = P.GAMMA_SQ
    beta_d: float = P.BETA_D
    beta_p: dict = field(default_factory=lambda: dict(P.BETA_P))
    beta_p_scale: float = 1.0  # level calibrated by calibrate_beta_p_scale(); gradient from beta_p
    trips: float = P.T_TRIPS
    high_income_distance_scale: float = 1.0
    kappa_version: str = P.KAPPA_VERSION

    def with_(self, **kw) -> "Params":
        return replace(self, **kw)

    def bp(self) -> dict:
        """Price sensitivity used in the model: derived gradient x calibrated level."""
        return {g: v * self.beta_p_scale for g, v in self.beta_p.items()}


@dataclass
class Market:
    groups: pd.DataFrame  # one row per consumer group: tract_id, group, n
    stores: pd.DataFrame  # one row per store (9 existing + planned), indexed 0..J-1
    dist: np.ndarray  # G x J Manhattan miles, tract centroid -> store
    fbar: dict  # weekly food-at-home $ by income group
    kappa: pd.DataFrame  # kappa_low/base/high by income group
    p_bar: float  # mean basket price of the 9 existing stores

    @property
    def existing(self) -> np.ndarray:
        return (self.stores["status"] == "existing").to_numpy()


def load_market() -> Market:
    """Read the v2 inputs. 13 tracts with households x 3 income groups = 39 groups."""
    hh = pd.read_csv(DESC_STATS_V2_DIR / "hh_by_tract_income_group_v2.csv")
    hh = hh[hh["active_tract"]]
    groups = pd.concat(
        [pd.DataFrame({"tract_id": hh["tract_id"], "group": g, "n": hh[f"n_{g.lower()}"]}) for g in GROUPS],
        ignore_index=True,
    )
    groups = groups[groups["n"] > 0].reset_index(drop=True)

    s = pd.read_csv(DESC_STATS_V2_DIR / "store_summary_stats_v2.csv")
    s = s[s["row_type"] == "store"].copy()
    prices = pd.read_csv(PRICES_DIR / "p_j_cd2_candidate_stores.csv").set_index("store")["p_j_current"]
    s["p"] = s["store"].map(prices).fillna(s["p_j"])  # planned store keeps its all-Bronx price
    stores = pd.DataFrame({
        "store": s["store"],
        "short": s["store_short"],
        "status": s["store_status"],
        "type": np.where(s["store"].isin(P.SMALL_STORES), "small", "supermarket"),
        "sqft": s["agm_sqft"],
        "p": s["p"],
        "R": s["R_j_v2"],
        "R_low": s["R_j_v2_low"],
        "R_high": s["R_j_v2_high"],
        "rent": s["Rent_j"],
        "tax": s["Tax_j"],
        "tax_high": s["Tax_j_high"],
    }).reset_index(drop=True)

    d = pd.read_csv(DISTANCE_DIR / "d_tract_store_miles.csv")
    dmat = d.pivot(index="tract_id", columns="store", values="miles")
    dist = dmat.loc[groups["tract_id"], stores["store"]].to_numpy()

    f = pd.read_csv(BLS_DIR / "ces_fbar_by_income_group_northeast_cd2weighted.csv")
    f = f[f["acs_year"] == 2024]
    fbar = {g: float(f.loc[f["group"].str.startswith(g), "f_bar_weekly_usd_nyc"].iloc[0]) for g in GROUPS}

    k = pd.read_csv(BLS_DIR / "kappa_core_basket_share_northeast_cd2weighted.csv")
    k = k[k["acs_year"] == 2024]
    kappa = pd.DataFrame({g: k[k["group"].str.startswith(g)].iloc[0] for g in GROUPS}).T

    p_bar = float(stores.loc[stores["status"] == "existing", "p"].mean())
    return Market(groups, stores, dist, fbar, kappa, p_bar)


# --- Core logit ------------------------------------------------------------------------------

def _per_group(mkt: Market, values: dict) -> np.ndarray:
    """Column vector (G x 1) of a per-income-group value."""
    return mkt.groups["group"].map(values).to_numpy(dtype=float)[:, None]


def baskets_per_trip(mkt: Market, prm: Params) -> np.ndarray:
    """k_g = annual food-at-home spending / (trips x mean basket price); weekly trips -> f_bar / p_bar."""
    return _per_group(mkt, {g: 52 * mkt.fbar[g] / (prm.trips * mkt.p_bar) for g in GROUPS})


def kappa_g(mkt: Market, prm: Params) -> np.ndarray:
    """Core basket share by income group; "whole_basket" applies the discount to every item."""
    if prm.kappa_version == "whole_basket":
        return _per_group(mkt, {g: 1.0 for g in GROUPS})
    return _per_group(mkt, mkt.kappa[prm.kappa_version].astype(float).to_dict())


def utility(mkt: Market, prm: Params, alpha: dict, price: np.ndarray, cols: np.ndarray) -> np.ndarray:
    """V_ij for the stores in `cols` (bool mask over mkt.stores). price is G x J."""
    st = mkt.stores
    a = st["type"].map(alpha).to_numpy(dtype=float)
    bd = prm.beta_d * _per_group(mkt, {"Low": 1.0, "Mid": 1.0, "High": prm.high_income_distance_scale})
    V = (a + prm.gamma_sq * st["sqft"].to_numpy() / 1000
         - _per_group(mkt, prm.bp()) * baskets_per_trip(mkt, prm) * (price - mkt.p_bar)
         + bd * mkt.dist)
    return np.where(cols, V, -np.inf)


def shares(V: np.ndarray) -> np.ndarray:
    """Choice probabilities over stores; the outside option (V = 0) takes the rest."""
    e = np.exp(V)
    return e / (1.0 + e.sum(axis=1, keepdims=True))


def logsum(V: np.ndarray) -> np.ndarray:
    return np.log1p(np.exp(V).sum(axis=1))


def sales(mkt: Market, prm: Params, s: np.ndarray, price: np.ndarray) -> np.ndarray:
    """Annual sales per store from CD2 households: sum_i n_i * T * s_ij * k_g * price_ij."""
    n = mkt.groups["n"].to_numpy()[:, None]
    return (n * prm.trips * s * baskets_per_trip(mkt, prm) * price).sum(axis=0)


def delta_cs_i(mkt: Market, prm: Params, V_pre: np.ndarray, V_post: np.ndarray) -> np.ndarray:
    """Annual Delta CS ($) for each consumer group i (tract x income), all its households."""
    n = mkt.groups["n"].to_numpy()
    bp = _per_group(mkt, prm.bp())[:, 0]
    return n * prm.trips / bp * (logsum(V_post) - logsum(V_pre))


def summarize_dcs(mkt: Market, by_i: np.ndarray) -> pd.Series:
    out = pd.Series(by_i).groupby(mkt.groups["group"].to_numpy()).sum().reindex(GROUPS)
    out["Total"] = out.sum()
    return out


def delta_cs(mkt: Market, prm: Params, V_pre: np.ndarray, V_post: np.ndarray) -> pd.Series:
    """Annual Delta CS ($) by income group and in total."""
    by_i = delta_cs_i(mkt, prm, V_pre, V_post)
    out = pd.Series(by_i).groupby(mkt.groups["group"].to_numpy()).sum().reindex(GROUPS)
    out["Total"] = out.sum()
    return out


def with_stores(mkt: Market, **cols) -> Market:
    """Copy of the market with store columns replaced, e.g. with_stores(mkt, R=mkt.stores.R_low)."""
    return replace(mkt, stores=mkt.stores.assign(**cols))


def base_price(mkt: Market) -> np.ndarray:
    return np.broadcast_to(mkt.stores["p"].to_numpy(dtype=float), mkt.dist.shape).copy()


# --- Calibration (run 0) -------------------------------------------------------------------

def calibrate(mkt: Market, prm: Params, tol: float = 1e-10, max_iter: int = 5000) -> dict:
    """alpha by store type so predicted sales by type equal R_j summed by type.

    Contraction alpha_t <- alpha_t + ln(R_t / R_hat_t) (Berry 1994). Must be re-run for every
    parameter set, since alpha absorbs whatever the betas leave unexplained.
    """
    ex = mkt.existing
    types = mkt.stores["type"].to_numpy()
    price = base_price(mkt)
    target = {t: mkt.stores.loc[ex & (types == t), "R"].sum() for t in ("supermarket", "small")}
    alpha = {"supermarket": 0.0, "small": 0.0}
    for _ in range(max_iter):
        R_hat = sales(mkt, prm, shares(utility(mkt, prm, alpha, price, ex)), price)
        step = {t: np.log(target[t] / R_hat[ex & (types == t)].sum()) for t in alpha}
        alpha = {t: alpha[t] + step[t] for t in alpha}
        if max(abs(v) for v in step.values()) < tol:
            return alpha
    raise RuntimeError("calibration did not converge")


def calibrate_beta_p_scale(mkt: Market, prm: Params, lo: float = 0.01, hi: float = 1.0,
                           tol: float = 1e-4, capacity_mult: float = 1.0) -> float:
    """Level of beta_p such that N.Y.C. Groceries at the 30% discount sells its capacity.

    Capacity = 15,000 sq ft x Bronx $801/sq ft = R_j of the planned store (MAIN spec v2
    Part 2). At the derived (USDOT value-of-time) level the store would sell ~$56M/yr, 4.7x
    that, because store-level price elasticity is ~19. The income gradient of beta_p is kept;
    only its level is scaled. alpha is recalibrated at every trial value. Bisection on log scale.
    """
    j = int(np.flatnonzero(mkt.stores["store"] == NEW_STORE)[0])
    target = mkt.stores.at[j, "R"] * capacity_mult

    def excess(scale: float) -> float:
        p = prm.with_(beta_p_scale=scale)
        return lever_contract(mkt, p, calibrate(mkt, p), j, P.DISCOUNT).extra["predicted_sales"] - target

    if excess(lo) > 0 or excess(hi) < 0:
        raise RuntimeError("capacity target not bracketed")
    while np.log(hi / lo) > tol:
        mid = np.sqrt(lo * hi)
        lo, hi = (lo, mid) if excess(mid) > 0 else (mid, hi)
    return float(np.sqrt(lo * hi))


# --- Levers ------------------------------------------------------------------------------------

@dataclass
class LeverResult:
    cost: float  # annual public cost ($)
    dcs: pd.Series  # Delta CS by group + Total
    extra: dict = field(default_factory=dict)
    by_i: np.ndarray | None = None  # Delta CS per consumer group (tract x income)


def lever_cost_cut(mkt: Market, prm: Params, alpha: dict, j: int, s: float, theta: float) -> LeverResult:
    """FRESH tax break or rent subsidy s at existing store j: Delta p_j = theta * s / Q_j (§1.3.1).

    Q_j is the model's predicted annual baskets at j, so that at theta = 1 the price cut hands
    back about s to shoppers whatever the store's calibration fit. The spec's Q_j = R_j / p_j
    (observed revenue) is reported alongside as dcs_total_observed_Q; with it, stores the model
    under-predicts look worse for reasons unrelated to the policy.
    """
    ex = mkt.existing
    p0 = base_price(mkt)
    V0 = utility(mkt, prm, alpha, p0, ex)
    st = mkt.stores.iloc[j]
    q_model = sales(mkt, prm, shares(V0), p0)[j] / st["p"]
    q_obs = st["R"] / st["p"]

    def dcs_for(q: float) -> pd.Series:
        p1 = p0.copy()
        p1[:, j] -= theta * s / q
        return delta_cs(mkt, prm, V0, utility(mkt, prm, alpha, p1, ex))

    return LeverResult(s, dcs_for(q_model), {
        "dp_per_basket": theta * s / q_model,
        "dcs_total_observed_Q": dcs_for(q_obs)["Total"],
    })


def lever_contract(mkt: Market, prm: Params, alpha: dict, j: int, depth: float = P.DISCOUNT,
                   tax_col: str = "tax") -> LeverResult:
    """N.Y.C. Groceries contract at store j: depth% off the core basket (§1.3.2, §1.5).

    If j is the planned store it is added to the choice set (baseline = 9 existing stores).
    Its Delta CS then counts only the gain from the discount: Delta CS(depth) - Delta CS(0).
    A plain logit credits any added store with welfare (a copy of Key Food adds ~$0.9M/yr at
    the derived beta_p), so the gain from the store existing is not identified; it is reported
    as `entry_gain_not_identified` and left out of the comparison.
    Public cost = Rent + Tax + Affordability Payment = max(Rent + Tax, discount cost).
    Discount cost uses the model's post-policy demand at store j; the spec's version
    (depth * kappa_j * R_j, R_j fixed) is reported alongside.
    """
    ex = mkt.existing
    post_cols = ex.copy()
    post_cols[j] = True
    p0 = base_price(mkt)
    kap = kappa_g(mkt, prm)
    p1 = p0.copy()
    p1[:, j] = p0[:, j] * (1 - depth * kap[:, 0])
    V_pre = utility(mkt, prm, alpha, p0, ex)
    V_post = utility(mkt, prm, alpha, p1, post_cols)
    s_post = shares(V_post)

    st = mkt.stores.iloc[j]
    n = mkt.groups["n"].to_numpy()[:, None]
    core_sales = (n * prm.trips * s_post * baskets_per_trip(mkt, prm) * kap * p0)[:, j].sum()
    sales_post = sales(mkt, prm, s_post, p0)[j]  # at pre-discount shelf prices
    kappa_j = core_sales / sales_post
    fixed = st["rent"] + st[tax_col]
    cost_model = max(fixed, depth * core_sales)
    cost_spec = max(fixed, depth * kappa_j * st["R"])
    by_i = delta_cs_i(mkt, prm, V_pre, V_post)
    entry = 0.0
    if not ex[j]:
        entry_i = delta_cs_i(mkt, prm, V_pre, utility(mkt, prm, alpha, p0, post_cols))
        by_i, entry = by_i - entry_i, float(entry_i.sum())
    return LeverResult(cost_model, summarize_dcs(mkt, by_i), by_i=by_i, extra={
        "entry_gain_not_identified": entry,
        "cost_spec": cost_spec,
        "rent_plus_tax": fixed,
        "affordability_payment": cost_model - fixed,
        "kappa_j": kappa_j,
        "predicted_sales": sales_post,
        "R_j": st["R"],
        "share_of_cd2_spending": sales_post / total_spending(mkt, prm),
    })


def total_spending(mkt: Market, prm: Params) -> float:
    """Annual CD2 food-at-home spending implied by the model: sum_i n_i * T * k_g * p_bar."""
    n = mkt.groups["n"].to_numpy()[:, None]
    return float((n * prm.trips * baskets_per_trip(mkt, prm) * mkt.p_bar).sum())
