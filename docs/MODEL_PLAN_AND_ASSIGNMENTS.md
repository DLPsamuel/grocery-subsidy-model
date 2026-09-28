# Model Plan and Assignments

**Updated:** 2026-09-28 · **Author:** Chris · **Deadlines:** presentation Oct 5 / 7, final report Oct 9

This is the working plan for the model phase: who runs what, how code moves through the repo, the
parameters for the utility function, and what the runs produce.

---

## 1. Workflow

1. **Samuel** finalizes the model equations and functions (utility → choice shares → logsum → ΔCS)
   and pushes them to `code/`.
2. **Chris** pulls once Samuel says they're final, adds `code/params.py` and the run configs, runs
   his models, and pushes the outputs to `results/`.
3. **Samuel** pulls those results, reuses them, and iterates on his own runs.
4. **Rahul** reviews the code, the results and the report.

Rules for all of us:
- `git pull --rebase origin main` before every commit.
- Model code goes in `code/`, outputs go in `results/<run_name>/`, and nothing goes in `src/`
  (that's the website; a broken build fails the deploy).
- Use relative paths via `code/data_paths.py`.
- Don't edit someone else's functions to make a run work. Tell the owner instead.

## 2. Assignments

| Run | What varies | Who |
|---|---|---|
| 0. Calibration check | Predicted vs observed store shares | Chris |
| 1. Base case (foundation) | All three levers at base parameters | Chris |
| 1b. Base case per store | Run 1, one row per candidate store (which store to subsidize) | Chris |
| 2. β sweep | β_p, β_d and γ_sq ranges (§4); trips counted as baskets vs visits | Chris |
| 3. Pass-through sweep | FRESH θ ∈ {0, 0.25, 0.5, 1}; N.Y.C. Groceries effective cut 18% vs 30% | Samuel |
| Review | Code, results, report | Rahul |

- **Budget is swept inside every run.** The subsidy amount s is the x-axis of each result, so there
  is no separate budget run. Every run reports where the budget binds. If it never binds, the
  city-run store wins by default, and we have to say so rather than report a ranking.
- **Dropped:** the store-universe comparison and the revenue range.

## 3. Consumer groups: 39

The model uses tract × income groups: **16 tracts × 3 income groups = 48 cells, of which 39 have
households.** Tracts 19.04, 93.02 and 117.02 have 0 households in ACS 2024, so the model runs
**13 tracts × 3 income groups = 39 groups** (19,922 households). Drop the empty tracts before
taking logs.

| Group | Household income | Households | Median income (from B19001 brackets) |
|---|---|---|---|
| Low | under $25,000 | 7,683 | ≈ $13,300 |
| Mid | $25,000–49,999 | 4,795 | ≈ $39,800 |
| High | $50,000 and over | 7,444 | ≈ $92,500 |

Sources: `data/acs/cd2_B19001_2024.csv` (households per tract and group) and
`data/geography/bronx_cd2_tract_centroids.csv` (distance origins).

## 4. Indirect utility function (Chris's runs)

**V_ij = α_type(j) + γ_sq · (sqft_j / 1,000) − β_p,i · p_j + β_d · d_ij**

i = consumer group (tract × income), j = store. β_d is a raw coefficient (negative), so distance
enters with a plus. β_p is written as a positive number with a minus sign in front, as in the spec.
Outside option (shopping outside CD2): V_i0 = 0.

| Parameter | Base value | Sweep | Source | Status |
|---|---|---|---|---|
| **γ_sq**, store quality from size (new) | **+0.0098 per 1,000 sq ft** (SQFT 0.0170 + SQFT-URBAN −0.0072) | 0.0098 – 0.0170 | Hillier et al. 2017, Table 2 | BORROWED |
| **β_d**, distance | **−0.548 per mile = −0.0227 per walking minute** (DIST −0.3736 + DIST-URBAN −0.1745; 15 min/km) | base, and 40% larger in magnitude | Hillier Table 2; Cao et al. 2026 (naive estimates too small by 37–43%) | BORROWED |
| **β_p,i**, price (per basket $) | **Low 0.43 · Mid 0.14 · High 0.06** | value of time at 100%: 0.21 / 0.07 / 0.03 | β_p,i = −β_d / value of a minute for group i (below) | DERIVED |
| **α_type**, store-type constant | calibrated | — | Chosen so predicted shares match observed shares (revenue or sq ft ÷ M, M = $106M) | CALIBRATED |
| **trips/yr** | **basket units: 52 · f̄_i / p_j ≈ 128 / 158 / 255** | ~40 supermarket visits/yr | Dannefer et al. 2016, Table 2; BLS CES f̄ | BORROWED |
| **θ**, pass-through | 1 (N.Y.C. Groceries) | FRESH {0, .25, .5, 1} (Samuel's run 3) | NYCEDC RFP Q&A #1; scenario | SOURCED / SCENARIO |

**How β_p is derived.** A shopper trades price against travel time at their value of time.
USDOT's travel-time guidance values local personal travel at 50% of the hourly wage and walking
time at 100%. With hourly income = group median ÷ 2,080 hours, a minute is worth $0.053 (Low),
$0.160 (Mid) and $0.371 (High) at 50%. Dividing −β_d by those values gives the base β_p. The
walking-time (100%) values are the low end of the sweep. This gives β_p a source, and it makes
low-income households the most price-sensitive, which is the direction the spec intended.

**Notes on these values:**
- **γ_sq units are an assumption.** Hillier doesn't state the units of SQFT. Per 1,000 sq ft is the
  only reading that gives sensible utilities (per single sq ft, a 44,000 sq ft store would get +748).
  For scale: a 1,300 sq ft bodega gets +0.013, the 15,000 sq ft N.Y.C. Groceries store on the
  Peninsula +0.147, and a 42,000 sq ft supermarket +0.41.
- **α is set by store type, not per store.** A separate α for every store would absorb the sq ft
  term. With α by type, sq ft separates stores within a type, and it's how the model values a new
  store that has no sales history (the N.Y.C. Groceries site).
- **Store list: J = 9** (Samuel, `data/stores/large_grocery_stores_cd2.csv`, 9/28): 2 large grocery
  stores, 3 super stores and 4 supermarkets, 1,600–15,000 sq ft, all SNAP-eligible. Square footage is
  known for all 9, so there are three α values to calibrate (one per SNAP store type).
- **Hillier's sample drives; CD2 walks.** 85% of Hillier's sample had a car; 83% of Bronx shoppers
  walk (Dannefer). β_d is probably too small in magnitude here, which is why run 2 includes +40%.
- **Check the price elasticity.** The logit own-price elasticity is β_p · p_j · (1 − S_j). At the
  base values and p ≈ $29 it is about 12 (Low), 4 (Mid) and 2 (High). Those are high for low-income
  shoppers, and food category elasticities are 0.27–0.81 (Andreyeva et al. 2010). Store switching
  should respond more than category demand does, but run 2 has to show whether results depend on it.
- **A trip means one basket.** β_p is per basket dollar and Q_j = Revenue_j / p_j, so trips are
  counted in basket units everywhere, including the per-year ΔCS (ISSUES #4).

## 5. Output: subsidy needed for each consumer-surplus target

Each run sweeps the subsidy s over a grid (the budget) and records ΔCS(s) for each lever and
store. We then invert that curve: for each consumer-surplus target, the minimum subsidy that reaches
it.

| ΔCS target ($/yr, all CD2) | Lever | Store | Minimum subsidy s* ($/yr) | $ subsidy per $ of ΔCS | Share of ΔCS to low-income | Reachable within the grid? |
|---|---|---|---|---|---|---|
| 50K / 100K / 250K / 500K / 1M | FRESH · rent · N.Y.C. Groceries | each candidate | … | … | … | yes / no |

- Written to `results/<run_name>/subsidy_by_cs_target.csv`, with a chart of s* against the ΔCS target.
- The same table for every run lets us compare base, β sweep and θ sweep directly.
- A target that can't be reached within the grid is reported as "not reachable", not left blank.

## 6. What each run needs, and from whom

| Input | Who | Needed by |
|---|---|---|
| Final equations and functions in `code/` | Samuel | 10/1 |
| Final store list J ✅ (9 stores, pushed 9/28); p_j for all 9 (6 are in `data/prices/`) | Samuel / Rahul | 10/1 |
| Distance matrix d_ij (tract centroid → store, minutes) | Samuel | 10/1 |
| Store revenue for observed shares. The fallback is sq ft × sales per sq ft by store type (FMI $1,019/sq ft/yr, scaled down for smaller formats, as in the v4 plan Q4) | Rahul | 10/1 |
| Lever costs: Tax_j, Rent_j, Affordability Payment | Rahul / Samuel | 10/1 |

**Target:** runs 0 and 1 working by 10/2, runs 1b, 2 and 3 by 10/3, slides on 10/4.

## 7. Differences from the spec v4 plan to settle

Samuel's v4 plan (`.cursor/plans/model_spec_v4_document_140be600.plan.md`) was drafted from Chris's
9/22 inventory. That inventory has since been corrected, so these points should be agreed before v4 is
written:

| v4 plan says | Proposed here | Why |
|---|---|---|
| β_d built from a car-free share (CD2 "71.9% car-free") | Same β_d for every group, from Hillier; +40% in the sweep | No data file backs 71.9% (B08201 was never downloaded). Download it first if we keep the car-free term. |
| β_p = β_d / WTP, WTP from Taylor & Villas-Boas | Same identity, with WTP from USDOT value of time (§4) | T&VB needs a library request that may not arrive before 10/5. The USDOT route works now; T&VB can replace it later. |
| SNAP utility bonus δ_SNAP · snap_j, sourced from Hillier | Leave it out | All 9 stores are SNAP-eligible, so the term is the same for every store and doesn't change shares. Hillier's SNAP interactions are insignificant (DIST-SNAP p = 0.84, SUPMKT-SNAP p = 0.48), and there's no SNAP main effect because every store in his sample accepted SNAP. |
| Skip the share calibration (no observed shares) | Calibrate α by store type to shares from sq ft × sales per sq ft | The v4 plan's own Q4 method gives the revenue, so shares exist. Without calibration we can't check ISSUES #5. |
| FRESH θ ∈ {0, 0.40, 0.85} | θ ∈ {0, 0.25, 0.5, 1} (team plan) | The 0.40–0.85 range came from the unsourced 0.65. Including 1 shows the best case for FRESH. Samuel's run 3, so his call. |
| T = 52 trips/yr | Basket units, 52 · f̄_i / p_j | β_p is per basket dollar, so trips must be counted in baskets. Run 2 compares the two. |
| N.Y.C. Groceries Δp = 0.30 · κ · p_j | Same | Agreed. It matches the "effective cut" in run 3. |

Chris's 9/22 inventory (`chris_temp.txt`, `docs/chris_params_inventory.md.docx`) was removed on 9/28.
The current version is `docs/phase4_consumer_policy_params_inventory.md`.

Parameter sources in detail: `docs/phase4_consumer_policy_params_inventory.md`.
