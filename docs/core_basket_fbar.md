# Core Basket and Non-Core Grocery Spending by Income Group

Used in: N.Y.C. Groceries price cut (Δp_j = 0.30 × κ × p_j), Affordability Payment estimate, ΔCS sanity check · Last updated: 2026-09-30

## Files

**Code**
- [`code/build_fbar_core_basket.py`](../code/build_fbar_core_basket.py): builds everything on this page.
- [`code/parse_bls_ces_xlsx.py`](../code/parse_bls_ces_xlsx.py): parses the CES tables and builds f̄ and M. It is the source of the bracket mapping (`ACS_TO_CES`), the income groups (`MODEL_GROUPS`) and the NYC scale factor.
- [`code/build_kappa.py`](../code/build_kappa.py): the source of the Core Basket category tags (`CATEGORIES`) and the partial weight (`PARTIAL_WEIGHT`). Its own output is the older national κ.

**Inputs**
- [`data/bls/cu-region-by-income-northeast-2023-2024.xlsx`](../data/bls/cu-region-by-income-northeast-2023-2024.xlsx): BLS CES Table 3104, Northeast region by income before taxes, 2023-24.
- [`data/bls/cu-msa-northeast-2-year-average-2023-2024.xlsx`](../data/bls/cu-msa-northeast-2-year-average-2023-2024.xlsx): BLS CES Table 3004, Northeastern metro areas (incl. New York), 2023-24.
- [`data/acs/cd2_B19001_2024.csv`](../data/acs/cd2_B19001_2024.csv) (also 2020-2023): ACS household income brackets for the 16 Bronx CD2 tracts.

**Outputs**
- [`data/bls/fbar_core_noncore_by_income_group_northeast.csv`](../data/bls/fbar_core_noncore_by_income_group_northeast.csv): the full results. There is one row per ACS year (2020-2024), κ version (low, base, high) and group (Low, Mid, High, CD2 overall).
- [`data/bls/kappa_core_basket_share_northeast_cd2weighted.csv`](../data/bls/kappa_core_basket_share_northeast_cd2weighted.csv): just κ, by year and group.
- Related f̄ and M files (from `parse_bls_ces_xlsx.py`):
  - [`ces_fbar_by_income_group_northeast_cd2weighted.csv`](../data/bls/ces_fbar_by_income_group_northeast_cd2weighted.csv)
  - [`cd2_market_size_M_northeast_cd2weighted.csv`](../data/bls/cd2_market_size_M_northeast_cd2weighted.csv)

**Related docs**
- [`fbar_M_update_log.md`](fbar_M_update_log.md): change log for the f̄, M and κ updates.
- [`kappa_core_basket.md`](kappa_core_basket.md): the original national κ and the Core Basket definition.
- [`nyc_groceries_store.md`](nyc_groceries_store.md): N.Y.C. Groceries store inputs.

## How to rerun

Close any of the output CSVs that are open in Excel first, because Excel locks them. Then run:

```
python code/parse_bls_ces_xlsx.py
python code/build_fbar_core_basket.py
```

The first script builds f̄ and M; the second builds the Core Basket split and checks that it adds back up to the first script's f̄ and M.

## Result (ACS 2024)

Base κ for Bronx CD2 is **0.615**: about 61% of a household's grocery spending goes to Core Basket items. Under base κ, households spend about **$51 a week (Low), $59 (Mid) and $89 (High)** on Core Basket items.

All values are per household, NYC-scaled. "f̄ total" is all grocery (food-at-home) spending.

**κ low**: only categories fully in the Core Basket

| Income group | Households | f̄ total | Core | Non-core | κ |
|---|---|---|---|---|---|
| Low (under $25K) | 7,683 | $81.64/wk ($4,245/yr) | $32.87/wk ($1,709/yr) | $48.77/wk ($2,536/yr) | 0.403 |
| Middle ($25K-50K) | 4,795 | $94.17/wk ($4,897/yr) | $37.26/wk ($1,938/yr) | $56.91/wk ($2,959/yr) | 0.396 |
| High (over $50K) | 7,444 | $146.94/wk ($7,641/yr) | $54.08/wk ($2,812/yr) | $92.86/wk ($4,829/yr) | 0.368 |
| CD2 overall | 19,922 | $109.06/wk ($5,671/yr) | $41.85/wk ($2,176/yr) | $67.20/wk ($3,495/yr) | 0.384 |

**κ base**: fully-in categories plus half of partly-in

| Income group | Households | f̄ total | Core | Non-core | κ |
|---|---|---|---|---|---|
| Low (under $25K) | 7,683 | $81.64/wk ($4,245/yr) | **$51.00/wk** ($2,652/yr) | $30.64/wk ($1,593/yr) | **0.625** |
| Middle ($25K-50K) | 4,795 | $94.17/wk ($4,897/yr) | **$58.56/wk** ($3,045/yr) | $35.61/wk ($1,852/yr) | **0.622** |
| High (over $50K) | 7,444 | $146.94/wk ($7,641/yr) | **$89.03/wk** ($4,630/yr) | $57.91/wk ($3,011/yr) | **0.606** |
| CD2 overall | 19,922 | $109.06/wk ($5,671/yr) | **$67.03/wk** ($3,486/yr) | $42.03/wk ($2,185/yr) | **0.615** |

**κ high**: fully-in plus all of partly-in categories

| Income group | Households | f̄ total | Core | Non-core | κ |
|---|---|---|---|---|---|
| Low (under $25K) | 7,683 | $81.64/wk ($4,245/yr) | $69.13/wk ($3,595/yr) | $12.51/wk ($650/yr) | 0.847 |
| Middle ($25K-50K) | 4,795 | $94.17/wk ($4,897/yr) | $79.85/wk ($4,152/yr) | $14.32/wk ($744/yr) | 0.848 |
| High (over $50K) | 7,444 | $146.94/wk ($7,641/yr) | $123.98/wk ($6,447/yr) | $22.96/wk ($1,194/yr) | 0.844 |
| CD2 overall | 19,922 | $109.06/wk ($5,671/yr) | $92.21/wk ($4,795/yr) | $16.85/wk ($876/yr) | 0.845 |

Across all of CD2 under base κ, households spend **$69.4M a year on Core Basket items** and $43.5M on everything else, $113.0M in total (the market size M).

## What core and non-core f̄ mean

- **f̄** is how much a household spends on groceries per week, at all stores combined.
- **Core f̄** is the part of that spending on items in the N.Y.C. Groceries Core Basket (produce, fresh meat and seafood, and staples like milk, eggs, bread, rice and beans). Only these items get the 30% discount.
- **Non-core f̄** is everything else: snacks, sweets, drinks, and the non-staple parts of mixed categories.
- **κ** is just core ÷ total.

**Example.** A Low-income household spends $51.00 a week on Core Basket items under base κ. If it bought all of them at N.Y.C. Groceries at 30% off, it would save 0.30 × $51.00 = **$15.30 a week**, about $796 a year. Its other $30.64 of weekly grocery spending gets no discount.

## How it was calculated

1. **Tag the categories.** BLS splits grocery spending into 18 categories. Each is tagged "in", "partly in" or "out" of the Core Basket, exactly as in [`kappa_core_basket.md`](kappa_core_basket.md). For example, fresh fruit is in, bakery products are partly in (sandwich bread only), and sugar and sweets are out.
2. **Three versions of κ.** For each of BLS's nine Northeast income brackets:
   - Core spending = "in" + w × "partly in", where w = 0 (low), 0.5 (base) or 1 (high).
   - Non-core spending = total grocery spending − core. Taking it as the remainder also absorbs a $1-2 rounding gap in the BLS table.
3. **Match BLS brackets to CD2 households.** Each of the 16 ACS income brackets for CD2 is matched to its BLS bracket. The ACS $60-75K bracket crosses the BLS $70K line, so 2/3 of it goes to BLS $50-70K and 1/3 to BLS $70-100K.
4. **Weight by CD2 households.** Each income group's value is the average over its brackets, weighted by how many CD2 households are in each. For example, the High group is dominated by households earning $50-100K, because that's who lives in CD2.
5. **Scale to NYC.** BLS doesn't publish NYC spending by income. So the Northeast figures are multiplied by NYC ÷ Northeast total grocery spending (7,033 ÷ 7,029 = 1.0006), which makes almost no difference.
6. **Check.** The script confirms that core + non-core equals the f̄ from `parse_bls_ces_xlsx.py`, and that core M + non-core M equals the total M, for every year and κ version.

The Low, Middle and High groups are the same as everywhere else in the model: ACS household income under $25K, $25-50K, and over $50K.

## How to use it in the model

For N.Y.C. Groceries, pass-through θ = 1: the 30% discount is written into the operator contract, so all of it reaches shelf prices.

- **Price cut in the choice model.** The basket price at N.Y.C. Groceries falls by 0.30 × κ:
  - 18.8% for Low, 18.7% for Middle and 18.2% for High (base κ).
  - These are close enough that one κ works fine (see next section).
- **Savings in dollars.** Maximum weekly savings per household, if it buys its whole Core Basket at the store, are 0.30 × core f̄:
  - Low: $15.30 ($796/yr)
  - Middle: $17.57 ($914/yr)
  - High: $26.71 ($1,389/yr)
- **Check the model's ΔCS.** Multiply each group's savings by how many households are in the group and by the share of their shopping the store gets ($P_{g,NYCG}$):

  $$
  \Delta CS \approx \sum_g n_g \cdot P_{g,NYCG} \cdot 0.30 \cdot \bar f^{core}_g \cdot 52
  $$

  If the logit model's ΔCS is far from this, check the units. The logsum gives dollars per trip, not per year; see issue 4 in [`ISSUES_AND_GAPS.md`](ISSUES_AND_GAPS.md).
- **Estimate the Affordability Payment.** The city pays the operator to cover the discount.
  - The current formula, 0.30 × κ × Revenue_j, needs store revenue. The planned Spofford Ave store doesn't have a revenue figure yet.
  - Instead, build it from demand:

    $$
    \text{AP} = 0.30 \sum_g n_g \cdot P_{g,NYCG} \cdot \bar f^{core}_g \cdot 52
    $$

  - This also shows how much of the payment benefits low-income households.
- **Non-core spending.** The base model assumes a household buys its whole basket at one store. If households instead buy Core Basket items at N.Y.C. Groceries and everything else at their usual store, non-core f̄ is the spending the usual stores keep. This matters for existing stores' revenue and for any future split-basket version of the model, but it isn't needed in the base run.
- **Remember.** f̄ is spending at *all* stores. The new store only gets its choice share of it, so always multiply by $P_{g,j}$ before calling anything "store revenue" or "savings at the store".

## Differences from the earlier national κ

| | Earlier ([`kappa_core_basket.md`](kappa_core_basket.md)) | Now |
|---|---|---|
| Spending data | National, 2024 (Table 1203) | Northeast, 2023-24 (Table 3104), scaled to NYC |
| Weighting across brackets | U.S. spending weights | Bronx CD2 household counts |
| κ base, overall | 0.602 | 0.615 |
| κ base by group (Low / Mid / High) | 0.603 / 0.601 / 0.602 | 0.625 / 0.622 / 0.606 |

The Northeast κ is slightly higher, and it falls a little as income rises. Lower-income households spend a bigger share on produce, meat, eggs and staples.

## One κ vs κ per income group

There are two separate changes here: moving to the regional estimate, and using a different κ for each income group.

**How κ enters the model today.** A single number for everyone:

$$
\Delta p_j = 0.30 \cdot \kappa \cdot p_j, \qquad \Delta U_{ij} = -\beta_{p,i} \cdot \Delta p_j
$$

Every income group sees the same percentage price cut at N.Y.C. Groceries (about 18%). Only price sensitivity $\beta_{p,i}$ differs by group.

**Change 1: the regional estimate.** κ goes from 0.602 to 0.615, so the price cut goes from 18.1% to 18.5% for everyone. The price change is about 2% bigger, so ΔCS rises by roughly 2%. Same model, better data.

**Change 2: κ per income group.** Give each group its own κ:

$$
\Delta p_{j,i} = 0.30 \cdot \kappa_i \cdot p_j
$$

This gives price cuts of 18.8% (Low), 18.7% (Middle) and 18.2% (High) instead of 18.5% for all. Compared with one κ:

- The Low group's price cut is about 1.6% larger, so its ΔCS rises by about 1-2%.
- The High group's price cut is about 1.5% smaller, so its ΔCS falls by about the same.
- The CD2 total barely changes.

The result is that a little more of the benefit goes to low-income households. In code, κ becomes a vector indexed by income group instead of a single number, used wherever the price cut is computed. Nothing else changes.

**Where group values matter more: dollar calculations.** In the choice model, κ only sets a percentage cut on one basket price that everyone shares. But in dollar calculations κ multiplies each group's own spending, and κ_g × f̄_g is exactly core f̄_g:

| Weekly savings (whole Core Basket at the store) | One κ (0.615 × f̄_g) | κ per group (core f̄_g) |
|---|---|---|
| Low | 0.30 × 0.615 × $81.64 = $15.06 | 0.30 × $51.00 = $15.30 |
| Middle | 0.30 × 0.615 × $94.17 = $17.37 | 0.30 × $58.56 = $17.57 |
| High | 0.30 × 0.615 × $146.94 = $27.11 | 0.30 × $89.03 = $26.71 |

The Affordability Payment works the same way:
- With one κ, it's 0.30 × κ × Revenue_j, which has no revenue figure for the new store.
- With group values, it's built from demand as 0.30 × Σ households × choice share × core f̄ × 52, and it can be split by group.

Either way, the big differences between groups come from how much they spend ($82 vs $147 a week), not from κ.

**Recommendation**
- **Choice model:** use the regional CD2-overall κ, **0.615**, with 0.384 and 0.845 as the low/high sweep. Running κ per group is an optional sensitivity check. It costs nothing to implement, but don't expect it to change conclusions.
- **Dollar outputs** (household savings, Affordability Payment, the ΔCS check): use the group core f̄ values in the tables above.

## Caveats

1. **The "half" in κ base is a judgment call.** BLS categories aren't detailed enough to know exactly how much of, say, "miscellaneous foods" is soup vs chips. κ low and κ high bracket the uncertainty; run both as a sweep.
2. **The Core Basket list is preliminary.** NYCEDC will refine it with the operator, so κ could move.
3. **Northeast profile, not NYC.** BLS publishes NYC spending only for all households combined, so the Northeast income profile is assumed to hold in NYC. NYC households earn more than Northeast households on average but spend about the same on groceries. So within each income bracket, NYC spending may be slightly lower than shown.
4. **Two-year average.** The BLS figures pool 2023 and 2024.
5. **The $60-75K split is an assumption.** It assumes incomes are spread evenly within that ACS bracket.
6. **Earlier years use 2023-24 spending.** Rows for ACS 2020-2023 in the CSVs apply 2023-24 dollars without inflation adjustment. Use ACS 2024.
7. **Non-core is a remainder.** It includes the small rounding gap between BLS category totals and the published grocery total.

## Sources

| What | Source |
|---|---|
| Grocery spending by category and income, Northeast | BLS Consumer Expenditure Surveys, Table 3104, 2023-2024 ([CE tables](https://www.bls.gov/cex/tables.htm)) |
| NYC vs Northeast grocery spending | BLS Consumer Expenditure Surveys, Table 3004, 2023-2024 ([geographic tables](https://www.bls.gov/cex/tables/geographic/mean.htm)) |
| CD2 households by income | U.S. Census Bureau, ACS 5-year, table B19001, 16 Bronx CD2 tracts |
| Core Basket list and 30% discount | See Sources in [`kappa_core_basket.md`](kappa_core_basket.md) (RFP Appendix C, Mayor's Office press release, RFP Round 1 Q&A) |
| Pass-through θ = 1 | NYCEDC RFP Round 1 Q&A, Q1 (see [`nyc_groceries_store.md`](nyc_groceries_store.md)) |
