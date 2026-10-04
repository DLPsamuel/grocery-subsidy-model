"""Behavioural and policy parameters for the CD2 store-choice model (Lead C).

Sign convention: raw coefficients. BETA_D is negative and distance enters utility with a
plus. BETA_P is a positive number and price enters with a minus, as in MAIN spec v2 §1.1.1.

Tags: SOURCED (taken from a primary source), BORROWED (estimate from another study/setting),
DERIVED (computed from other values here), CALIBRATED (fitted to our data in code/model.py),
SCENARIO (assumed; varied in sensitivity runs).

Sources: docs/phase4_consumer_policy_params_inventory.md and docs/MODEL_PLAN_AND_ASSIGNMENTS.md §4.
Team decisions of 2026-10-02 (group chat): 2 store types, outside option, FRESH theta set,
T = 52 trips with price per trip.
"""
from __future__ import annotations

# --- Utility: store size and distance --------------------------------------------------

# Store size, utility per 1,000 sq ft. Hillier et al. (2017) Table 2: SQFT 0.0170 +
# SQFT-URBAN -0.0072 (CD2 is a >90% urban county). Units of SQFT are not stated in the paper;
# per 1,000 sq ft is the only reading that gives sensible utilities.        BORROWED
GAMMA_SQ = 0.0170 - 0.0072  # = 0.0098

# Distance, utility per mile (raw, negative). Hillier et al. (2017) Table 2: DIST -0.3736 +
# DIST-URBAN -0.1745. Per trip. Distances are Manhattan miles (code/build_d_ij.py). BORROWED
BETA_D = -0.3736 - 0.1745  # = -0.5481

# --- Utility: price ------------------------------------------------------------------------

# beta_p,g = -BETA_D / (dollar value of one mile of travel for group g).        DERIVED
# Value of time: USDOT Revised Departmental Guidance on Valuation of Travel Time (2016):
# local personal travel at 50% of the hourly wage.                              SOURCED
VOT_SHARE_OF_WAGE = 0.50
HOURS_PER_YEAR = 2080  # full-time hours, converts annual income to an hourly wage   SOURCED
# Walking pace 15 min/km (MAIN spec v3 distance convention) -> minutes per mile.  SCENARIO
MIN_PER_MILE = 15 * 1.609344  # = 24.14
# Group median household income from ACS B19001 brackets, 2024 (plan §3).          DERIVED
# These values come from data/acs/cd2_B19001_2024.csv
MEDIAN_INCOME = {"Low": 13_300, "Mid": 39_800, "High": 92_500}


def dollars_per_mile(group: str, vot_share: float = VOT_SHARE_OF_WAGE) -> float:
    """Value of one mile of travel time for a household in `group` ($/mile)."""
    per_minute = MEDIAN_INCOME[group] / HOURS_PER_YEAR / 60 * vot_share
    return per_minute * MIN_PER_MILE


def beta_p(beta_d: float = BETA_D, vot_share: float = VOT_SHARE_OF_WAGE) -> dict[str, float]:
    """Price sensitivity per dollar of trip spending, by income group.          DERIVED"""
    return {g: -beta_d / dollars_per_mile(g, vot_share) for g in MEDIAN_INCOME}


BETA_P = beta_p()  # ~ Low 0.43 · Mid 0.14 · High 0.06 (gradient across groups)

# Level of beta_p. At the derived level, store-level own-price elasticity is ~19 and
# N.Y.C. Groceries at 30% off would sell ~$56M/yr (half of CD2 spending, 4.7x its capacity).
# So the level is scaled so that store sells its capacity, 15,000 sq ft x $801/sq ft = $12.0M
# (MAIN spec v2 Part 2); the gradient above is kept. Fitted in
# code/model.py:calibrate_beta_p_scale (team decision 2026-10-03).                CALIBRATED
CALIBRATE_BETA_P_LEVEL = True

# --- Trips and price per trip ----------------------------------------------------------

# Shopping trips per year, same for every income group (MAIN spec v2 §1.1.5; team chat
# 10/2). Base: weekly shopping.                                                       SCENARIO
T_TRIPS = 52
# Sensitivity: Dannefer, Adjoian, Brathwaite & Walsh, "Food shopping behaviors of residents
# in two Bronx neighborhoods", AIMS Public Health 3(1):1-12, 2016 (published online Dec
# 2015). Table 2, neighborhood supermarket: 60.1% shop once a week or more, 36.7% less than
# once a week. Assuming the less-than-weekly group shops twice a month:
# 0.601 x 52 + 0.367 x 24 = 40.1 visits/yr (36-49 if that group shops 1-4 times a month).
# "Once a week or more" is top-coded, so this is a floor.          BORROWED + assumption
T_TRIPS_ALT = 40

# Baskets per trip k_g = weekly food-at-home spending f_bar_g / mean basket price.
# Computed in code/model.py from data/bls/ces_fbar_by_income_group_northeast_cd2weighted.csv
# (BLS CES Northeast, NYC-scaled, CD2-weighted).                                    DERIVED
# Price enters utility per trip: -beta_p,g * k_g * (p_j - p_bar).

# Outside option ("other stores": bodegas and stores outside CD2), V_i0 = 0, priced at the
# mean basket price p_bar. South Bronx supermarket and bodega baskets cost about the same
# (NYC DOHMH Epi Data Brief 158, 2026).                                             SCENARIO
OUTSIDE_PRICE = "mean"

# --- Store constants -------------------------------------------------------------------

# Two store types (team chat 10/2). alpha by type is fitted so predicted sales by type
# match R_j (v2 Census revenue) in code/model.py.                                 CALIBRATED
SMALL_STORES = ("ANTILLANA FRESH MEAT MARKET", "SAGAL MEAT MARKET", "JJ SOUTHERN FARM FRUIT")

# --- Policy levers ---------------------------------------------------------------------

# N.Y.C. Groceries: 30% off the core basket, by contract (NYCEDC RFP; Round 1 Q&A #1,
# Aug 2026). Price cut per group = DISCOUNT * kappa_g * p_j (MAIN spec v2 §1.3.2). SOURCED
DISCOUNT = 0.30
THETA_CONTRACT = 1.0  # contracted, covered by Affordability Payments (RFP Q&A #1)  SOURCED

# FRESH-type tax break and rent subsidy: pass-through of a fixed-cost subsidy. No source
# (fixed costs need not move prices; Weyl & Fabinger 2013). Team set, chat 10/2.    SCENARIO
THETA_FRESH = (0.25, 0.50, 0.75)
THETA_BASE = 0.50

# Core basket share kappa_g: base version (low/high are sensitivity), from
# data/bls/kappa_core_basket_share_northeast_cd2weighted.csv.                     SOURCED
KAPPA_VERSION = "kappa_base"

# Capital cost of building N.Y.C. Groceries (Chris run 4). NYCEDC program page
# (edc.nyc/program/nyc-groceries): $70M of capital for 5 city-owned stores, one per borough,
# i.e. ~$14M per site. The $30M on the same page is La Marqueta (East Harlem), not CD2.
# The CD2 site's own capital budget is not published.                               SOURCED
CAPITAL_TOTAL = 70_000_000
CAPITAL_STORES = 5
# Spread over the store's life as an annual payment (annuity). Rate and life are assumed:
# (3%, 30 yr) low, (4%, 20 yr) high.                                                SCENARIO
CAPITAL_AMORTIZATION = {"low (3%, 30 yr)": (0.03, 30), "high (4%, 20 yr)": (0.04, 20)}

# --- Run 2 sweep ranges (MODEL_PLAN §4) ---------------------------------------------------

GAMMA_SQ_HIGH = 0.0170  # SQFT main effect only (Hillier)                           BORROWED
BETA_D_SCALE_HIGH = 1.40  # naive distance estimates too small by 37-43% (Cao et al. 2026) BORROWED
VOT_SHARE_WALK = 1.00  # USDOT: walking time valued at 100% of the wage              SOURCED
HIGH_INCOME_DISTANCE_SCALE = 0.75  # High-income distance effect 25% weaker         SCENARIO

# --- Outputs -----------------------------------------------------------------------------

# Consumer-surplus targets for the subsidy-needed table ($/yr, all CD2; MODEL_PLAN §5).
CS_TARGETS = (50_000, 100_000, 250_000, 500_000, 1_000_000)
