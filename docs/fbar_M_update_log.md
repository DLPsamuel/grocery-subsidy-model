# Change log: f̄ and M updated with Northeast and NYC-metro CES data

Date: 2026-09-30

## 1. Summary

Average weekly food-at-home spending (f̄) and total CD2 annual grocery market size (M) were recomputed using regional instead of national BLS Consumer Expenditure Survey (CES) data:

- **Source changed from national to regional.** Spending by income bracket now comes from CES Table 3104 (Northeast region by income before taxes, 2023-24). CES Table 3004 (Northeastern metropolitan areas, 2023-24) is used to scale the Northeast values to the New York metro area.
- **Weighting changed from simple average to CD2 household-weighted.** Previously each model income group's f̄ was an unweighted average of the national CES brackets in that group. Now each CES bracket is weighted by the number of Bronx CD2 households in it (ACS B19001), so f̄ and M reflect Hunts Point's own income distribution.
- **Bracket mismatch fixed.** Previously the model's Low group (<$25K) used CES spending for households up to $30K, while the ACS counted <$25K. Now every ACS bracket is mapped to its own CES bracket, so each household gets the spending of its actual income bracket.

The previous national outputs are unchanged and kept for comparison.

For ACS 2024, M rises from $106.0M to $113.0M (+6.6%). The CD2-wide f̄ is $109.06/week.

## 2. Data sources

| Table | Content | Period | File | 
|---|---|---|---|
| CES Table 3104 | Northeast region by income before taxes: consumer units, income, food at home and sub-items for 9 income brackets | 2023-2024 (two-year average) | `data/bls/cu-region-by-income-northeast-2023-2024.xlsx` |
| CES Table 3004 | Selected Northeastern MSAs (Northeast total, New York, Philadelphia, Boston), all consumer units only | 2023-2024 (two-year average) | `data/bls/cu-msa-northeast-2-year-average-2023-2024.xlsx` |
| ACS B19001 | Household income in the past 12 months, 16 brackets, by census tract (16 CD2 tracts) | ACS 5-year, 2020-2024 releases | `data/acs/cd2_B19001_{2020..2024}.csv` |

BLS CES tables portal: https://www.bls.gov/cex/tables.htm (geographic tables: https://www.bls.gov/cex/tables/geographic/mean.htm). Both BLS files were downloaded manually because automated downloads from bls.gov return HTTP 403.

Key values from the source tables (annual food at home, 2023-24):

- Northeast, all consumer units: $7,029
- New York MSA, all consumer units: $7,033
- Northeast by income bracket: <$15k $4,193; $15-30k $4,315; $30-40k $4,574; $40-50k $5,323; $50-70k $6,078; $70-100k $7,305; $100-150k $8,149; $150-200k $9,390; $200k+ $10,338

## 3. Method

### 3.1 Mapping ACS brackets to CES brackets

| ACS B19001 variable | ACS income range | CES bracket (Table 3104) | Model group |
|---|---|---|---|
| 002-003 | < $15,000 | Less than $15,000 | Low |
| 004-005 | $15,000-24,999 | $15,000-29,999 | Low |
| 006 | $25,000-29,999 | $15,000-29,999 | Mid |
| 007-008 | $30,000-39,999 | $30,000-39,999 | Mid |
| 009-010 | $40,000-49,999 | $40,000-49,999 | Mid |
| 011 | $50,000-59,999 | $50,000-69,999 | High |
| 012 | $60,000-74,999 | 2/3 to $50,000-69,999, 1/3 to $70,000-99,999 | High |
| 013 | $75,000-99,999 | $70,000-99,999 | High |
| 014-015 | $100,000-149,999 | $100,000-149,999 | High |
| 016 | $150,000-199,999 | $150,000-199,999 | High |
| 017 | $200,000+ | $200,000 and more | High |

ACS bracket 012 ($60-75k) straddles the CES $70k boundary. It is split assuming incomes are spread evenly within the bracket: $10k of its $15k width falls below $70k (2/3) and $5k above (1/3). The model groups keep their existing ACS definitions from `code/download_acs.py` (Low = 002-005, Mid = 006-010, High = 011-017).

### 3.2 Formulas

Notation: $f_b$ = Northeast annual food-at-home spending for ACS bracket $b$ (from the mapping above); $n_b$ = CD2 households in bracket $b$ (summed over the 16 tracts); $s$ = NYC scale factor.

NYC scale factor:

$$
s = \frac{f^{\text{NYC MSA}}_{\text{all}}}{f^{\text{Northeast}}_{\text{all}}} = \frac{7033}{7029} = 1.000569
$$

Market size:

$$
M = s \sum_b n_b f_b
$$

Group $\bar f$ (annual):

$$
\bar f_g = s \, \frac{\sum_{b \in g} n_b f_b}{\sum_{b \in g} n_b}
$$

- Weekly $\bar f$ = annual / 52
- CD2-wide $\bar f$ (weekly) = $M / N_{HH} / 52$

By construction $M = \sum_g n_g \bar f_g$, so group-level $\bar f$ values and M are always consistent.

The Table 3004 MSA data has no income breakdown, so the Northeast income profile is used and rescaled by $s$. Because $s$ is so close to 1, the NYC adjustment changes results by only 0.06%. Both unscaled (Northeast) and NYC-scaled values are reported.

## 4. Results (ACS 2024)

### 4.1 f̄ by income group

| Group | Households (ACS 2024) | Previous f̄ (national, simple average) | New f̄ (Northeast, CD2-weighted) | New f̄ (NYC-scaled) |
|---|---|---|---|---|
| Low (<$25K) | 7,683 | $71.87/wk ($3,737/yr) | $81.60/wk ($4,243/yr) | $81.64/wk ($4,245/yr) |
| Mid ($25-50K) | 4,795 | $88.52/wk ($4,603/yr) | $94.12/wk ($4,894/yr) | $94.17/wk ($4,897/yr) |
| High (>$50K) | 7,444 | $142.71/wk ($7,421/yr) | $146.86/wk ($7,637/yr) | $146.94/wk ($7,641/yr) |
| CD2 overall | 19,922 | $119.69/wk (national all-CU mean, not CD2-weighted) | $109.00/wk ($5,668/yr) | $109.06/wk ($5,671/yr) |

### 4.2 Market size M

| ACS year | N_HH | Previous M (national, simple average, income-weighted) | New M (Northeast) | New M (NYC-scaled) | Change |
|---|---|---|---|---|---|
| 2020 | 18,582 | $80.79M | $99.36M | $99.42M | +23.1% |
| 2021 | 19,149 | $91.59M | $104.84M | $104.90M | +14.5% |
| 2022 | 19,620 | $101.26M | $111.34M | $111.41M | +10.0% |
| 2023 | 19,721 | $106.69M | $112.57M | $112.64M | +5.6% |
| **2024** | **19,922** | **$106.02M** | **$112.91M** | **$112.98M** | **+6.6%** |

The previous "all consumer units" version of M (N_HH × national all-CU mean) was $123.99M for 2024. The new estimate lies between the two previous versions.

The larger changes in earlier years are mostly because the 2023-24 Northeast spending profile is applied to every ACS year without inflation adjustment, while the previous series used same-year national CES. **ACS 2024 is the primary estimate.**

### 4.3 Why the values changed

- **Low and Mid rise.** Northeast low-income households spend more on food at home than national ones ($4,193 vs. $3,577 for <$15k in 2024 national data).
- **High rises less.** Most CD2 High-group households earn $50-100k, so the $150k+ brackets carry little weight under CD2 weighting. The previous simple average gave each of the five national $50k+ brackets equal weight.
- **CD2 overall is below the regional mean** ($109/wk vs. $135/wk for the Northeast). About 39% of CD2 households earn under $25K.

## 5. Code changes: `code/parse_bls_ces_xlsx.py`

New constants:

- `REGION_INCOME_FILE`, `MSA_FILE`, `REGIONAL_CES_PERIOD`: paths and period of the two regional files.
- `FOOD_AT_HOME_ITEMS`: food at home and its five sub-items (cereals and bakery; meats, poultry, fish and eggs; dairy; fruits and vegetables; other food at home).
- `MSA_COLS`: Northeast, New York, Philadelphia, Boston.
- `ACS_TO_CES`: ACS B19001 bracket to CES bracket mapping with shares (section 3.1).
- `MODEL_GROUPS`: Low/Mid/High as ranges of ACS B19001 brackets.

New functions:

- `_find_item_row(df, label, n_cols)`: finds values on the item row itself. Regional and MSA tables have no separate "Mean" row, unlike national Table 1203. Footnote markers (`b/`, `c/`, `d/`) become missing.
- `parse_region_income_file(path)`: parses Table 3104 into one row per CES bracket (plus the Northeast total), with consumer units, income, food at home and sub-items.
- `parse_msa_file(path)`: parses Table 3004 into one row per area and computes each area's food-at-home ratio to the Northeast.
- `build_cd2_weighted_outputs(region_df, msa_df, prev_market_path)`: for each `data/acs/cd2_B19001_{year}.csv`, sums brackets across tracts. It checks that bracket counts add up to B19001_001E, then computes group f̄, CD2 f̄ and M (unscaled and NYC-scaled), and attaches the previous M for comparison.

`main()`:

- Runs the regional step after the existing national outputs, only if both regional files exist. Otherwise it records them as missing.
- Writes the four new CSVs.
- Adds `regional_ces_period` and the new outputs to `data/bls/ces_xlsx_parse_meta.json`.

The existing national parsing and outputs are unchanged.

## 6. New files

| File | Content |
|---|---|
| `data/bls/ces_food_at_home_northeast_by_income_2023_2024.csv` | Parsed Table 3104: consumer units, income, food at home and 5 sub-items for the Northeast total and 9 income brackets |
| `data/bls/ces_food_at_home_northeast_msa_2023_2024.csv` | Parsed Table 3004: same fields for Northeast, New York, Philadelphia, Boston, plus ratio to Northeast (the NYC scale factor) |
| `data/bls/ces_fbar_by_income_group_northeast_cd2weighted.csv` | One row per ACS year (2020-2024) and group (Low, Mid, High, CD2 overall): households, f̄ annual/weekly unscaled and NYC-scaled, scale factor, CES period, method, sources |
| `data/bls/cd2_market_size_M_northeast_cd2weighted.csv` | One row per ACS year: N_HH, M unscaled and NYC-scaled, CD2 weekly f̄, scale factor, previous M and % change |
| `docs/fbar_M_update_log.md` | This log |

Unchanged files kept for comparison: `data/bls/ces_fbar_by_income_group_from_xlsx.csv`, `data/bls/cd2_market_size_M_from_xlsx.csv`, `data/bls/ces_food_at_home_by_income_bracket.csv`, `data/bls/ces_food_at_home_by_income_quintile.csv`.

## 7. Verification

- ACS 2024 unscaled M = $112,912,893, matching an independent hand calculation.
- $\sum_g n_g \bar f_g$ equals M in every year, apart from cent-level rounding of f̄.
- Tract-summed ACS bracket counts equal N_HH (B19001_001E) in every year, e.g. 19,922 for 2024.
- Parsed Table 3104 and 3004 values match the source spreadsheets (section 2).

## 8. Caveats

- **Two-year averages.** CES regional and MSA tables are pooled 2023-2024 estimates, not single-year values.
- **No NYC income breakdown.** BLS does not publish metro-area spending by income. The Northeast income profile is assumed to apply to NYC and is rescaled by the all-household NYC/Northeast ratio. NYC households have higher average income than the Northeast ($122,952 vs. $116,310) but similar food-at-home spending, which suggests NYC spending within each bracket may be slightly below the Northeast. The simple ratio does not capture this.
- **$60-75k split.** The 2/3 : 1/3 split of ACS bracket 012 assumes incomes are evenly spread within it.
- **Dollar-year mismatch.** ACS 5-year income brackets are in the release year's dollars, while CES spending is 2023-24 dollars. Applying the 2023-24 profile to ACS 2020-2023 overstates M for those years.
- **Sampling error.** Regional bracket estimates have relative standard errors of several percent. MSA estimates are less precise still.
- **Consumer units vs. households.** CES consumer units and ACS households are similar but not identical concepts.

## 9. Downstream text to revise

- **LEVEL_1 model specification (`LEVEL_1_NYC_Grocery_Subsidy_Model_Specification_v3_drive.docx`):**
  - The M and f̄ rows cite "BLS CES Table 4700 (food-at-home by income quintile)". Replace with CES Table 3104 (Northeast by income before taxes, 2023-24) and Table 3004 (Northeastern MSAs, 2023-24), weighted by ACS B19001 CD2 household counts.
  - The f̄ range "approx $75-$140/week in NYC" should become roughly $82-$147/week (Low to High), with a CD2-wide f̄ of about $109/week.
  - Option B in Equation 1.2.1b uses "$100/week"; update it to about $109/week.
  - M is described as "N_HH × average annual food-at-home spending per household". Update it to the income-weighted formula in section 3.2.
- **`docs/revenue_j_estimates.md`, line 54:** "about $106-124M a year" should become about $113M a year (ACS 2024), citing `data/bls/cd2_market_size_M_northeast_cd2weighted.csv`.
- **Revenue and Q_j cross-checks:** any cross-check using $Q_j = S_j \cdot M / p_j$ should use the new M.

---

## 10. Addendum (2026-09-30): Core Basket and non-core f̄ by income group

### 10.1 What changed

- **New split of f̄.** f̄ for each income group is now split into spending on N.Y.C. Groceries Core Basket items and spending on everything else, for each of the three κ versions (low, base, high).
- **κ recomputed on the regional basis.** κ now uses the same Northeast Table 3104 data, CD2 household weighting and NYC scaling as the new f̄. It replaces the national 2024 Table 1203 basis used in `code/build_kappa.py`.
- **Existing national κ unchanged.** `data/bls/kappa_core_basket_share.csv` is left as it was.

Full explanation, file locations and model guidance: [`core_basket_fbar.md`](core_basket_fbar.md).

### 10.2 Method

- **Category tags.** The 18 food-at-home categories in Table 3104 are tagged "in", "partly in" or "out" of the Core Basket exactly as in `code/build_kappa.py` (`CATEGORIES`).
- **Core and non-core spending per CES bracket.** With partial weight $w$ = 0 (κ low), 0.5 (κ base) or 1 (κ high):
  - $\text{core}_b = \text{in}_b + w \cdot \text{partial}_b$
  - $\text{noncore}_b = \text{FoodAtHome}_b - \text{core}_b$. Taking non-core as the remainder absorbs the \$1-2 rounding gap between the category sum and the published total.
- **Aggregation to model groups.** Brackets are aggregated as in section 3: `ACS_TO_CES` mapping, CD2 ACS B19001 weights, NYC scale $s$ = 1.000569.
  - $\bar f^{core}_g = s \sum_{b \in g} n_b\,\text{core}_b / \sum_{b \in g} n_b$
  - $\bar f^{noncore}_g = \bar f_g - \bar f^{core}_g$
  - $\kappa_g = \bar f^{core}_g / \bar f_g$
  - $M^{core} = \sum_g n_g \bar f^{core}_g$

### 10.3 Results (ACS 2024, NYC-scaled)

**κ low** ("in" categories only)

| Group | Households | f̄ total | Core f̄ | Non-core f̄ | κ |
|---|---|---|---|---|---|
| Low (<$25K) | 7,683 | $81.64/wk ($4,245/yr) | $32.87/wk ($1,709/yr) | $48.77/wk ($2,536/yr) | 0.403 |
| Mid ($25-50K) | 4,795 | $94.17/wk ($4,897/yr) | $37.26/wk ($1,938/yr) | $56.91/wk ($2,959/yr) | 0.396 |
| High (>$50K) | 7,444 | $146.94/wk ($7,641/yr) | $54.08/wk ($2,812/yr) | $92.86/wk ($4,829/yr) | 0.368 |
| CD2 overall | 19,922 | $109.06/wk ($5,671/yr) | $41.85/wk ($2,176/yr) | $67.20/wk ($3,495/yr) | 0.384 |

**κ base** ("in" + half of "partly in")

| Group | Households | f̄ total | Core f̄ | Non-core f̄ | κ |
|---|---|---|---|---|---|
| Low (<$25K) | 7,683 | $81.64/wk ($4,245/yr) | $51.00/wk ($2,652/yr) | $30.64/wk ($1,593/yr) | 0.625 |
| Mid ($25-50K) | 4,795 | $94.17/wk ($4,897/yr) | $58.56/wk ($3,045/yr) | $35.61/wk ($1,852/yr) | 0.622 |
| High (>$50K) | 7,444 | $146.94/wk ($7,641/yr) | $89.03/wk ($4,630/yr) | $57.91/wk ($3,011/yr) | 0.606 |
| CD2 overall | 19,922 | $109.06/wk ($5,671/yr) | $67.03/wk ($3,486/yr) | $42.03/wk ($2,185/yr) | 0.615 |

**κ high** ("in" + all of "partly in")

| Group | Households | f̄ total | Core f̄ | Non-core f̄ | κ |
|---|---|---|---|---|---|
| Low (<$25K) | 7,683 | $81.64/wk ($4,245/yr) | $69.13/wk ($3,595/yr) | $12.51/wk ($650/yr) | 0.847 |
| Mid ($25-50K) | 4,795 | $94.17/wk ($4,897/yr) | $79.85/wk ($4,152/yr) | $14.32/wk ($744/yr) | 0.848 |
| High (>$50K) | 7,444 | $146.94/wk ($7,641/yr) | $123.98/wk ($6,447/yr) | $22.96/wk ($1,194/yr) | 0.844 |
| CD2 overall | 19,922 | $109.06/wk ($5,671/yr) | $92.21/wk ($4,795/yr) | $16.85/wk ($876/yr) | 0.845 |

CD2 market split (κ base): $69.4M core + $43.5M non-core = $113.0M.

Compared with the national κ in `kappa_core_basket.md` (base 0.602, flat across groups), the Northeast base κ is slightly higher (0.615) and falls a little with income (0.625 Low to 0.606 High).

### 10.4 Use in the N.Y.C. Groceries scenario (θ = 1, 30% Core Basket discount)

- **Price index in the logit.** With θ = 1, $\Delta p_j / p_j = 0.30\,\kappa$.
  - Group cuts under base κ: 18.8% (Low), 18.7% (Mid), 18.2% (High).
  - A single κ (0.615, i.e. an 18.5% cut) remains adequate in the utility function.
- **Dollar savings.** A household buying its whole Core Basket at the store saves $0.30\,\bar f^{core}_g$ under base κ. These are upper bounds.
  - Low: $15.30/wk ($796/yr)
  - Mid: $17.57/wk ($914/yr)
  - High: $26.71/wk ($1,389/yr)
- **First-order check on ΔCS:** $\Delta CS \approx \sum_g n_g P_{g,NYCG} \cdot 0.30\,\bar f^{core}_g \cdot 52$.
- **Affordability Payment from demand.** The planned store has no revenue figure, so the payment can be built from demand instead: $\text{AP} = 0.30 \sum_g n_g P_{g,NYCG}\,\bar f^{core}_g \cdot 52$.
- **Non-core f̄.** This is the spending incumbent stores would keep if households split their shopping. It is relevant for incumbents' Q_j and for a split-basket extension, not the base run.

### 10.5 New files

| File | Content |
|---|---|
| `code/build_fbar_core_basket.py` | Builds core and non-core f̄ and κ by group. It imports category tags from `build_kappa.py` and bracket mapping, groups and file paths from `parse_bls_ces_xlsx.py`. |
| `data/bls/kappa_core_basket_share_northeast_cd2weighted.csv` | κ low, base and high by ACS year and group |
| `data/bls/fbar_core_noncore_by_income_group_northeast.csv` | One row per ACS year × κ version × group. Columns: households, κ, f̄ total, core and non-core (annual unscaled; annual and weekly NYC-scaled), M core and non-core. |
| `docs/core_basket_fbar.md` | Standalone explainer for this work |

### 10.6 Verification

- Core + non-core f̄ reproduces `f_bar_annual_usd_nyc` in `ces_fbar_by_income_group_northeast_cd2weighted.csv` for every year, group and κ version. The script checks this and fails if not.
- $M^{core} + M^{noncore}$, summed over Low/Mid/High, equals `M_usd_nyc_scaled` in `cd2_market_size_M_northeast_cd2weighted.csv` for every year and κ version. The script also checks this.

### 10.7 Caveats

- **Partial weight is a judgment call.** The partial weight (0.5 in κ base) is still a judgment call; κ low and κ high bound it.
- **Core Basket list is preliminary.** NYCEDC will refine it with the operator.
- **Non-core is a remainder.** It includes the small rounding gap between the category sum and the published total.
- **Same caveats as section 8.** Two-year averages, the Northeast income profile applied to NYC, and the $60-75k split all apply here too.

### 10.8 Downstream text to revise

- `docs/kappa_core_basket.md` and `docs/nyc_groceries_store.md` cite κ = 0.60 (national). They could be updated to 0.615 (Northeast, CD2-weighted); both files were left unchanged.
