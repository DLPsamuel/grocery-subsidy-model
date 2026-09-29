# Core Basket Share (κ)

Owner: Rahul · Used in: N.Y.C. Groceries price cut, Δp_j = 0.30 × κ × p_j · Last updated: 2026-09-29

**Files**
- Code: [`code/build_kappa.py`](../code/build_kappa.py)
- Output: [`data/bls/kappa_core_basket_share.csv`](../data/bls/kappa_core_basket_share.csv)
- Input: [`data/bls/cu-income-before-taxes-2024.xlsx`](../data/bls/cu-income-before-taxes-2024.xlsx) (BLS Consumer Expenditure Survey 2024, Table 1203)

## Result

**κ = 0.60** (range 0.37 to 0.83). About 60% of a family's grocery bill is on Core Basket items.

So the N.Y.C. Groceries 30% discount cuts the whole basket price by about **0.30 × 0.60 = 18%**. That matches the "effective cut 18% vs 30%" already in Chris's run 3.

| Income group | κ low | **κ base** | κ high |
|---|---|---|---|
| All households | 0.370 | **0.602** | 0.833 |
| Low (under $25K) | 0.376 | **0.603** | 0.830 |
| Middle ($25K–50K) | 0.372 | **0.601** | 0.830 |
| High (over $50K) | 0.369 | **0.602** | 0.834 |

κ is almost the same for every income group, so **one value (0.60) is enough** for the model.

## What κ means

The 30% discount at N.Y.C. Groceries stores only applies to Core Basket items, not everything in the store. κ is the share of grocery spending that goes to those items. If κ were 1, the whole bill would be 30% cheaper. With κ = 0.60, the bill is 18% cheaper.

## How it was calculated

1. **What's in the Core Basket.** The preliminary list in RFP Appendix C: all produce, all fresh meat and seafood, refrigerated staples (cows' milk, eggs, butter, tofu, yogurt, non-specialty cheese, deli meats) and shelf-stable staples (pasta, sandwich bread, ready-to-eat cereal, tuna, pasta sauce, soup, cooking oil, nuts, raw rice, non-dairy milks, flour and meal, beans), plus specialty cheese and prepared salads. Snacks and desserts were removed.
2. **How families spend.** BLS splits grocery spending into 18 categories. In 2024 the average household spent $6,224 a year on groceries.
3. **Tag each category** as fully in, partly in, or out:

| Tag | BLS categories | $ per year (all households) | Share |
|---|---|---|---|
| **In** (whole category counts) | Fresh fruits, fresh vegetables, beef, pork, other meats (incl. deli), poultry, fish and seafood, eggs, fresh milk and cream | $2,304 | 37% |
| **Partly in** (only some items count) | Cereals (flour, rice, pasta, cereal: in); bakery (sandwich bread only); other dairy (butter, cheese, yogurt; no ice cream); processed fruits and vegetables (beans, canned veg; no juice); fats and oils (cooking oil); miscellaneous foods (soup, pasta sauce, nuts, prepared salads; no snacks or frozen meals) | $2,881 | 46% |
| **Out** | Sugar and sweets, non-alcoholic drinks, food bought on trips | $1,038 | 17% |

4. **Three versions of κ:**
   - **Low** = "in" only → 0.37
   - **High** = "in" + all of "partly in" → 0.83
   - **Base** = "in" + half of "partly in" → 0.60

Income groups: BLS brackets are grouped into ours (under $30K counts as Low, $30K–50K as Middle, $50K+ as High) and averaged by how much each bracket spends.

## Sources

| What | Source |
|---|---|
| Core Basket list (RFP Appendix C) | NYCEDC, *N.Y.C. Groceries Operator(s) RFP*, Project #11639, Appendix C. The list above is quoted from a summary of the RFP ([Obedio](https://hs.getobedio.com/blog/n.y.c.-groceries-operator-rfp-who-qualifies-what-the-city-pays-and-when-the-stores-have-to-open)) because the NYCEDC page blocked automated access. |
| Core Basket headline | [NYC Mayor's Office press release](https://www.nyc.gov/mayors-office/news/2026/07/mayor-mamdani-unveils-30--discount---including-all-produce--all-): "all fresh produce, meat and seafood, along with roughly 20 additional categories of pantry staples, dairy and refrigerated goods" |
| Core Basket still being refined | [NYCEDC RFP Round 1 Q&A](https://edc.nyc/sites/default/files/2026-08/26.08.14_Round%201%20Q&A%20vF.pdf): the list will be finalized with the operator during contract talks |
| Spending by category | BLS Consumer Expenditure Survey 2024, Table 1203 (income before taxes) |

## Caveats

1. **The "half" in κ base is a judgment call.** BLS doesn't split categories finely enough to know exactly how much of, say, "miscellaneous foods" is soup vs chips. That's why we give a low and high version. Run the model at 0.37 and 0.83 as a sweep.
2. **The Core Basket list is preliminary.** NYCEDC says it'll be refined with the operator, so κ could move.
3. **The list is quoted from a secondary summary.** It should be checked against the RFP PDF itself (Appendix C) when someone can open the NYCEDC site.
4. **National spending, not Bronx spending.** BLS doesn't publish category splits for CD2. Low-income households spend a slightly bigger share on meat, eggs and produce, but κ barely changes across income groups here, so this likely doesn't matter much.

## Other N.Y.C. Groceries facts found while doing this

See [`nyc_groceries_store.md`](nyc_groceries_store.md) for the full store inputs.

- **Bronx store site:** Peninsula 1A, **1215 Spofford Ave, Unit 8, Bronx 10474**, about 15,000 sq ft (including mezzanine), target opening second half of 2027 (same Obedio RFP summary). This is the location needed to add the new store to the distance table.
- **Affordability Payment:** the RFP gives **no dollar amount or cap**. It says the amount will be set in negotiations with the operator. The Round 1 Q&A (Q1, Q5) adds that it will be sized to cover the 30% Core Basket discount and has an annual cap that isn't published. So the model has to estimate it rather than look it up, for example as the cost of the discount: 0.30 × κ × Revenue_j.
