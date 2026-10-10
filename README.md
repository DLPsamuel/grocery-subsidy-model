# Policy Levers for Grocery Access in Bronx Community District 2

**94-867 From Data to Action, Carnegie Mellon University, Fall 2026**
Samuel De La Paz · Chris Oueis · Rahul Tejannavar

**Decision question:** Which grocery subsidy gives Bronx CD2 families the most benefit per dollar, and at which store?

New York City has two ways to make groceries cheaper in Hunts Point and Longwood. FRESH gives a supermarket tax breaks and hopes the owner passes the savings on. N.Y.C. Groceries pays a store's rent and property tax in exchange for selling a core basket of staples 30% below market. We built a store-choice (multinomial logit) model of the district's 9 grocery stores and 39 household groups (13 census tracts × 3 income levels). For each policy, the model finds how much families gain each year (the change in consumer surplus) and what it costs the City.

**Main result:** a 30% core-basket contract returns about $0.81 of family benefit per subsidy dollar, against about $0.50 for tax or rent breaks, and it stays ahead in 11 of 12 stress tests.

## Repository map

| Folder | What's in it |
|---|---|
| `code/` | The model (`model.py`, `params.py`, `run_model.py`) and the scripts that built its inputs |
| `data/` | All model inputs (already built) and the raw data behind them |
| `results/` | Output of every model run, as CSV files |
| `figures/` | Figures used in the presentation and report |
| `docs/` | Method notes for each input, the source list, and the research papers we borrowed parameters from |
| `report/` | Report drafts |
| `llm_transcripts/` | Each team member's LLM transcripts (report appendix) |

---

## How to run the code

This section explains how to reproduce every number, table and figure in the final report.

Repository: https://github.com/DLPsamuel/grocery-subsidy-model

### Quick start (about 1 minute)

All model inputs are already committed in `data/`, so the model runs without downloads or API keys.

```bash
git clone https://github.com/DLPsamuel/grocery-subsidy-model.git
cd grocery-subsidy-model
pip install -r requirements.txt   # Python 3.10+
python code/run_model.py        # runs 0-4, about 35 seconds; writes results/chris_run*/
python code/make_figures.py     # optional: subsidy curve and who-gains map
python code/samuel_run.py       # optional: Samuel's comparison with beta_p not calibrated
```

Run the commands from the repository root. Every path is relative and goes through `code/data_paths.py`, so nothing depends on a local folder. Re-running `run_model.py` reproduces the committed files in `results/` exactly.

One run can be run on its own: `python code/run_model.py run0` (also `run1`, `run2`, `run3`, `run4`).

### What to run, in order

| Step | Command | What it does | Output |
|---|---|---|---|
| 1 | `python code/run_model.py` | Calibrates the model, then runs all policy experiments | `results/chris_run0_calibration/` to `results/chris_run4_capital_cost/` |
| 2 | `python code/make_figures.py` | Draws the subsidy curve and the who-gains map from step 1 | `results/chris_run1_base/*.png` |
| 3 (optional) | `python code/samuel_run.py` | Re-runs with price sensitivity not calibrated to the new store, and compares | `results/samuel_run/` |

### Model code (`code/`)

| File | Role |
|---|---|
| `params.py` | Every behavioural and policy parameter, with its source and a tag (SOURCED, BORROWED, DERIVED, CALIBRATED or SCENARIO) |
| `model.py` | The multinomial logit store-choice model: utility, choice shares, sales, consumer surplus (logsum), calibration and the policy levers |
| `run_model.py` | Runs 0–4 (table below) |
| `make_figures.py` | Figures from the run outputs |
| `samuel_run.py` | Samuel's alternative calibration runs; reuses `model.py` and `run_model.py` |
| `data_paths.py` | Shared relative paths to `data/` and `results/` |

### Runs and where they appear in the report

| Run | Folder | Contents | Report |
|---|---|---|---|
| 0 | `results/chris_run0_calibration/` | Predicted vs. estimated sales by store, store-type constants, price-sensitivity scale, elasticities | Model Calibration; model check |
| 1 | `results/chris_run1_base/` | Family benefit (ΔCS) against subsidy for every lever and store; smallest subsidy for each benefit target; gain by tract | Result 1, Table 2, Figure 3 |
| 1b | `results/chris_run1b_per_store/` | Each lever at its maximum at every store | Result 1 (Figure 1), Result 2 (Figure 2, Table 3) |
| 2 | `results/chris_run2_sweep/` | 11 alternative parameter and data cases, model recalibrated in each | Sensitivity 2 (Table 5, Figure 5) |
| 3 | `results/chris_run3_pass_through/` | Pass-through θ = 0.25–1.0; core basket vs. whole store | Sensitivity 1 and 3 (Tables 4 and 6, Figure 4) |
| 4 | `results/chris_run4_capital_cost/` | New store with its share of the $70M build-out | Result 2 (Figure 2) |

### Model inputs (`data/`, already built)

| File | What it holds | Built by |
|---|---|---|
| `data/descriptive_stats_v2/hh_by_tract_income_group_v2.csv` | Households by tract and income group (ACS 2020–2024, B19001) | `build_cd2_descriptive_stats_v2.py` |
| `data/descriptive_stats_v2/store_summary_stats_v2.csv` | Store size, type, revenue, rent and property tax | `build_cd2_descriptive_stats_v2.py`, from `build_revenue_census_v2.py`, `build_rent_j_v2.py`, `build_tax_j_v2.py` |
| `data/prices/p_j_cd2_candidate_stores.csv` | Basket price at each store (2019 NYC survey, CPI-adjusted) | `build_p_j.py` |
| `data/distance/d_tract_store_miles.csv` | Street-grid distance from each tract to each store | `build_d_ij.py` |
| `data/bls/ces_fbar_by_income_group_northeast_cd2weighted.csv` | Weekly food-at-home spending by income group | `build_fbar_core_basket.py` |
| `data/bls/kappa_core_basket_share_northeast_cd2weighted.csv` | Core-basket share of spending (κ) | `build_kappa.py`, `build_fbar_core_basket.py` |

Rebuilding the inputs from the raw sources is optional and needs internet access and a few extra packages (`pip install -r requirements-data.txt`). `python code/run_all_downloads.py` fetches the public data (geography, ACS, BLS CES, store lists). The Census API steps need a free key in a `.env` file (see `.env.example`). Then run the `build_*.py` scripts listed above. Each script's docstring and the matching file in `docs/` explain its method and sources:

- `docs/revenue_census_estimate_v2.md`
- `docs/rent_and_tax_fy2025_v2.md`
- `docs/kappa_core_basket.md`
- `docs/core_basket_fbar.md`

### Model specification

[`docs/archive/MAIN_NYC_Grocery_Subsidy_Model_Specification_v2.md`](docs/archive/MAIN_NYC_Grocery_Subsidy_Model_Specification_v2.md) is the model specification the code implements. Earlier spec versions and the scripts used to draft them are in the same folder.
