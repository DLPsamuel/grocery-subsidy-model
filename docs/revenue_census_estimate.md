# Store Sales (Revenue_j): Central Estimate from the Economic Census

Owner: Rahul · Appendix F rows: Revenue_j, Q_j (Lead R) · Last updated: 2026-09-30

This is the **central** Revenue_j estimate. It replaces ReferenceUSA's modelled sales with a Bronx-wide sales-per-sq-ft rate built from public Census data. The ReferenceUSA estimate in [`revenue_j_estimates.md`](revenue_j_estimates.md) is unchanged and kept as the low end.

**Files**
- Code: [`code/build_revenue_census.py`](../code/build_revenue_census.py)
- Output folder: [`data/revenue_census_estimate/`](../data/revenue_census_estimate/)

| File | Content |
|---|---|
| `raw/ecn_2022_bronx_4451.csv` | Census numerator: Bronx establishments, sales, employees, payroll for each NAICS code queried (employer and nonemployer) |
| `bronx_agmarkets_stores_filtered.csv` | Every Bronx Ag & Markets store (2023 archive and current list): recorded and imputed sq ft, category, keep flag, exclude reason |
| `bronx_sales_per_sqft_census.csv` | One row per variant: sales, total sq ft, store counts on both sides, rate in 2022 and 2024 dollars, sales per employee |
| `revenue_j_census_cd2_candidate_stores.csv` | The 9 CD2 stores: central, low and high Revenue_j, Q_j, per-employee cross-check, and ReferenceUSA / FMI for comparison |
| `revenue_census_meta.json` | API calls, CPI values, all filter rules and patterns, exclusion counts, 9-store totals and share of M |

**Inputs used (not modified)**
- Ag & Markets 2023 archive: [`data/stores/agmarkets_retail_food_stores_archive_2023.csv`](../data/stores/agmarkets_retail_food_stores_archive_2023.csv)
- Ag & Markets current Bronx list: [`data/stores/agmarkets_bronx_county.csv`](../data/stores/agmarkets_bronx_county.csv)
- Store sq ft, basket price, ReferenceUSA and FMI revenue: [`data/revenue/revenue_j_cd2_candidate_stores.csv`](../data/revenue/revenue_j_cd2_candidate_stores.csv)
- Market size M: [`data/bls/cd2_market_size_M_northeast_cd2weighted.csv`](../data/bls/cd2_market_size_M_northeast_cd2weighted.csv)
- CPI helper `cpi_year()` imported from [`code/build_p_j.py`](../code/build_p_j.py)

Run with `python code/build_revenue_census.py` (needs `CENSUS_API_KEY` in `.env`; takes about 20 seconds).

## Why

ReferenceUSA's sales are estimated by Data Axle from headcount, not reported. Implied sales per sq ft for our 7 matched stores range from $62 to $618 a year (median $360), a 10× spread that reflects headcount guesses rather than real differences. Fine Fare (10,000 sq ft, $618K) was the clearest problem. We needed a local, public benchmark.

Key Food and C-Town are banners of independently owned stores and publish no store-level financials, so corporate data can only give a banner-wide average (an upper-bound check at best).

## Method

\[
r_{2024} = \frac{\text{Census Bronx grocery sales}_{2022}}{\sum \text{sq ft of matched Bronx Ag \& Markets stores}} \times \frac{\text{CPI}_{2024}}{\text{CPI}_{2022}}
\qquad
\text{Revenue}_j = \text{sq ft}_j \times r_{2024}
\qquad
Q_j = \text{Revenue}_j / p_j
\]

### Step 1: Census numerator

Pulled from the Census API for Bronx County (state 36, county 005):

| Source | NAICS 2022 | Establishments | Sales (2022) | Employees |
|---|---|---|---|---|
| Economic Census (employer) | 4451 Grocery and convenience retailers | 1,410 | $3,639M | 11,903 |
| Economic Census (employer) | 445110 Supermarkets and other grocery | 1,125 | $3,425M | 11,108 |
| Economic Census (employer) | 445131 Convenience retailers | 0 (suppressed) | 0 | 0 |
| Economic Census (employer) | 4452 Specialty food | 219 | $296M | 892 |
| Nonemployer Statistics | 4451 | 1,788 | $110M | – |
| Nonemployer Statistics | 4452 | 706 | $37M | – |

API endpoints: `api.census.gov/data/2022/ecnbasic` (table EC2244BASIC) and `api.census.gov/data/2022/nonemp`. The earlier failed attempt noted in `SOURCE_LIST_RAHUL.md` now works with the API key.

- The Economic Census only counts businesses **with paid employees**. Ag & Markets also licenses owner-run bodegas, so Nonemployer Statistics are added. They add many establishments but little money ($110M vs $3.64B).
- 445131 is published as 0 for the Bronx, which is suppression, not real zeros. The central scope therefore uses the **4451 total**, which includes convenience retailers.
- Nonemployer Statistics have no 445110 row at county level, so the 445110 variant is employer-only.

### Step 2: Ag & Markets denominator

- **Vintage:** the 2023 archive (2,617 Bronx stores) is primary, as the closest to the 2022 Census. The current list (2,235) is a sensitivity.
- **Missing sq ft:** the archive records unknown sq ft as 0. Values under 100 sq ft are treated as missing.
- **License codes** (from the NYSDAM establishment-type code sheet): keep stores with code A (store). Drop codes D, E, H, I, L (food warehouse, beverage plant, wholesale manufacturer, refrigerated warehouses). The archive prefixes multi-operation licenses with J; it is stripped before checking.
- **Name filter:** drop businesses outside NAICS 4451 by name keyword. Every dropped row keeps its `exclude_reason`. Results for the 2023 archive:

| Outcome | Stores |
|---|---|
| Kept | 2,275 |
| General merchandise or dollar store (Family Dollar, 99-cent, discount, variety, Target, BJ's) | 168 |
| Pharmacy (Walgreens, Rite Aid, CVS) | 75 |
| Gas station (BP, Mobil, Shell, AM/PM, "gas", "petroleum") | 36 |
| Warehouse, wholesale or plant license code | 35 |
| Food service or non-food retail (smoke shops, GNC, pizza, Edible Arrangements) | 23 |
| Online or warehouse (GoPuff, FreshDirect, Amazon Fresh) | 5 |

- **Bodega override:** names such as "DELI & SMOKE SHOP" or "GROCERY & 99 CENTS" are kept, because they are bodegas. The general-merchandise and non-food reasons are overridden when the name also contains deli, grocery, food or supermarket.
- **Outliers:** locations over 100,000 sq ft are dropped as warehouses (2 in the current list, including Prime Now; none in the 2023 archive).
- **Categories** (by name): supermarket (195 stores, median 8,000 sq ft), convenience or deli (1,293, median 1,000), specialty meat/fish/produce/bakery (232), other grocery (555). Truncated names are handled ("SUPERMKT", "FOOD TOWN", "KEY FOODS").
- **Imputation:** missing sq ft = median recorded sq ft of kept stores in the same category and vintage. In the central variant, 26% of stores and 15% of total sq ft are imputed.

The central scope (4451) excludes the specialty category from the denominator, since specialty shops are NAICS 4452. That leaves **2,043 stores and 4.75M sq ft**.

**Count check:** 2,043 Ag & Markets stores sit between the Census's 1,410 employer establishments and the 3,198 employer + nonemployer total. Many nonemployer businesses have no storefront, so this is consistent.

### Step 3: Inflation

BLS CPI food at home, New York area (`CUURS12ASAF11`), annual average: 2022 = 303.153, 2024 = 318.094, factor **1.0493**. 2024 matches the year of the other model inputs (ACS households, BLS spending).

### Step 4: Apply to the 9 stores

Revenue_j = store sq ft (Ag & Markets) × rate. Q_j = Revenue_j ÷ p_j (basket price from `build_p_j.py`). Low and high columns use the lowest and highest variant rates. A cross-check multiplies Census sales per employee ($320,791, 2024 dollars) by each store's ReferenceUSA 2024 headcount.

## Results

### Sales per sq ft (Bronx)

| Variant | Scope | Ag & Markets stores | $/sq ft/yr (2022) | **$/sq ft/yr (2024)** | $/sq ft/wk (2024) |
|---|---|---|---|---|---|
| **Central** | 4451, employer + nonemployer, 2023 list, imputed | 2,043 | $790 | **$829** | $15.93 |
| Employer only | 4451, employer only | 2,043 | $766 | $804 | $15.47 |
| Grocery only | 445110, employer only, no bodegas in denominator | 750 | $1,040 | $1,092 | $20.99 |
| With specialty | 4451 + 4452, specialty shops in denominator | 2,275 | $804 | $844 | $16.22 |
| Current list | Central scope, current Ag & Markets list | 1,798 | $818 | $858 | $16.50 |
| Known sq ft only | Drop stores with no sq ft; numerator scaled by covered share | 2,043 (1,509 used) | $686 | $719 | $13.83 |

For comparison: ReferenceUSA median $360/yr ($6.92/wk); FMI national $1,019/yr ($19.59/wk, for a 42,000 sq ft median store).

### Revenue_j for the 9 CD2 stores (2024 dollars)

| Store | Sq ft | Central | Low ($719) | High ($1,092) | Q_j (central) | ReferenceUSA 2024 | FMI |
|---|---|---|---|---|---|---|---|
| Key Food | 15,000 | $12.43M | $10.79M | $16.37M | 447,731 | $8.03M | $15.28M |
| Food Fair Fresh Market | 13,000 | $10.77M | $9.35M | $14.19M | 372,090 | $8.03M | $13.24M |
| Fine Fare Supermarket | 10,000 | $8.29M | $7.19M | $10.92M | 273,285 | $0.62M | $10.19M |
| Food Universe | 8,000 | $6.63M | $5.76M | $8.73M | 221,483 | – | $8.15M |
| C-Town (564 Southern Blvd) | 8,000 | $6.63M | $5.76M | $8.73M | 230,014 | $2.88M | $8.15M |
| C-Town (809 Southern Blvd) | 7,500 | $6.22M | $5.40M | $8.19M | 215,649 | $3.09M | $7.64M |
| Antillana Fresh Meat Market | 3,000 | $2.49M | $2.16M | $3.28M | 85,872 | $0.82M | $3.06M |
| Sagal Meat Market | 2,500 | $2.07M | $1.80M | $2.73M | 71,572 | $0.30M | $2.55M |
| JJ Southern Farm Fruit | 1,600 | $1.33M | $1.15M | $1.75M | 45,803 | – | $1.63M |
| **Total** | | **$56.8M** | $49.3M | $74.9M | | $27.2M* | $69.9M |

\* Current Revenue_j, which fills Food Universe and JJ Southern Farm with size × $360.

### Check against market size

CD2 households spend **$113.0M** a year on groceries (M, ACS 2024, NYC-scaled).

| Estimate | 9-store total | Share of M |
|---|---|---|
| ReferenceUSA (current Revenue_j) | $27.2M | 24% |
| **Census central** | **$56.8M** | **50%** |
| Census low | $49.3M | 44% |
| FMI national | $69.9M | 62% |
| Census high | $74.9M | 66% |

## Findings

1. **Bronx grocery stores sell about $829 per sq ft a year**, 2.3× ReferenceUSA's median and about 80% of FMI's national rate. Across all variants the range is $719–$1,092.
2. **ReferenceUSA understates sales for every store**, most of all for Fine Fare (13× lower) and the two meat markets (3–7× lower). The "Fine Fare looks too low" caveat in `revenue_j_estimates.md` is resolved: at Bronx rates it sells about $8.3M, not $0.6M.
3. **The 9 stores capture about half of CD2 grocery spending** under the central estimate. That leaves the other half for bodegas, small grocers and stores outside CD2, which is more plausible than ReferenceUSA's 24%.
4. **Removing bodegas raises the rate** (the grocery-only variant is $1,092). Supermarkets sell more per sq ft than the Bronx average, so the central rate likely understates the larger stores.
5. **The per-employee cross-check is lower** (Key Food $7.7M, Fine Fare $1.0M) because it relies on ReferenceUSA headcounts, which are themselves estimates.
6. **Model impact:** Q_j rises 1.3–2.3× for most supermarkets, and far more for Fine Fare and the meat markets. Since Δp_j = θ · s / Q_j, a given subsidy produces a smaller price cut per basket than under ReferenceUSA.

## Assumptions and caveats

1. **One rate for all formats.** The Bronx rate averages supermarkets, bodegas and grocers. It probably understates full supermarkets (Key Food, Food Fair) and overstates small specialty shops (Antillana, Sagal, JJ Southern Farm).
2. **Whole-location sq ft.** Ag & Markets records the whole licensed location, not selling area. The rate is consistent because the same measure is used for the Bronx denominator and the stores, but it is not directly comparable to FMI's figure.
3. **Name-based filter.** Matching Census industries to Ag & Markets stores by name is imperfect. Every decision is recorded in `bronx_agmarkets_stores_filtered.csv` for audit.
4. **Imputed sq ft.** 26% of stores (15% of sq ft) use category medians.
5. **Vintage gap.** Census sales are for 2022; the Ag & Markets list is the 2023 archive. The current list gives a similar rate ($858).
6. **Suppressed data.** Convenience retailers (445131) are suppressed for the Bronx; the 4451 total is used instead. Nonemployer data has no 445110 split.
7. **Inflation only.** 2022 → 2024 adjusts for food prices, not for any change in volume.
8. **Specialty stores in the central rate.** Three of the 9 stores are meat or produce markets (NAICS 4452) but get the 4451 grocery rate. The specialty variant ($844) is close, so this has little effect.

## Next steps

- Team decision: adopt the central estimate as the main Revenue_j in the model, with ReferenceUSA as the low case and the grocery-only rate or FMI as the high case.
- If a format-specific rate is wanted, scale the rate by store size (e.g. use the grocery-only rate for the 6 stores of 6,000+ sq ft).
- Update the Level 1 spec's Revenue_j row to cite the Economic Census and Ag & Markets instead of ReferenceUSA.
