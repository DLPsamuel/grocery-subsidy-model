# Food price elasticities of demand: what the literature says

**Scope:** price elasticity of demand for food bought at supermarkets (food at home), with attention
to low-income households · **Serves:** θ intuition (pass-through slides), sanity check on β_p_i ·
**Last verified:** 2026-10-04

Every figure below was checked against the PDFs in `docs/research_papers/` unless marked
*not verified*. Elasticities are reported as absolute values unless a sign is shown.

---

## 1. Summary

- **Market-level food demand is inelastic.** Category elasticities cluster between about 0.3 and
  0.8. A 10% price cut raises the quantity bought by roughly 3–8%, depending on the food.
- **Food at home overall is about 0.6.** Andreyeva et al. (2010) report 0.59 for food at home, but
  from only 7 studies. Okrent & Alston (2012) find group elasticities from 0.05 (dairy) to 0.98
  ("other food at home").
- **Low-income households are not clearly more price-sensitive.** In the only broad comparisons,
  low-income and all households are nearly identical (0.62 vs 0.64). Dong & Lin (2009) find
  low-income households slightly more responsive for vegetables and less for fruit.
- **Narrow products are more elastic than broad groups.** For example, white bread is 1.54, pork
  1.26 and cakes/cookies 1.20, while broad groups stay below 1. Shoppers substitute between
  products more easily than they cut back on food as a whole.
- **No source estimates Bronx or NYC elasticities.** None of the Bronx papers in the folder
  (Dannefer 2016, Epi Data Brief 158, Crossa 2023) measures how quantity responds to price.
- **The elasticity a single store faces is a different number.** It also includes shoppers
  switching stores, so it is larger than any category elasticity here. See section 4.

---

## 2. Papers added to `docs/research_papers/`

| File | Citation | Data | Main result |
|---|---|---|---|
| `andreyeva_long_brownell_2010_food_price_elasticity_review.pdf` | Andreyeva, Long & Brownell (2010). *Am J Public Health* 100(2):216–222. Open access: PMC2804646 | Review of 160 U.S. studies, 1938–2007 | Mean elasticities for 16 categories, 0.27–0.81 (Table 1, p. 219) |
| `okrent_alston_2012_ers_err139_food_demand_elasticities.pdf` | Okrent & Alston (2012). *The Demand for Disaggregated Food-Away-From-Home and Food-at-Home Products in the United States.* USDA ERS Economic Research Report 139 | BLS Consumer Expenditure Survey diary, 1998–2010; 43-product demand system | Food-group elasticities (Table 4, p. 16) and 38 food-at-home products (Table 6, p. 20) |
| `dong_lin_2009_ers_err70_fruit_veg_low_income_elasticities.pdf` | Dong & Lin (2009). *Fruit and Vegetable Consumption by Low-Income Americans: Would a Price Reduction Make a Difference?* USDA ERS Economic Research Report 70 | Nielsen Homescan 2004; low-income = below 130% of poverty | Low-income elasticities: fruit −0.52, vegetables −0.69 (p. 7) |

---

## 3. Findings by paper

### 3.1 Andreyeva, Long & Brownell (2010): review of 160 studies

Mean absolute price elasticity by category (Table 1, p. 219):

| Category | Mean (95% CI) | Range | No. of estimates |
|---|---|---|---|
| Food away from home | 0.81 (0.56, 1.07) | 0.23–1.76 | 13 |
| Soft drinks | 0.79 (0.33, 1.24) | 0.13–3.18 | 14 |
| Juice | 0.76 (0.55, 0.98) | 0.33–1.77 | 14 |
| Beef | 0.75 (0.67, 0.83) | 0.29–1.42 | 51 |
| Pork | 0.72 (0.66, 0.78) | 0.17–1.23 | 49 |
| Fruit | 0.70 (0.41, 0.98) | 0.16–3.02 | 20 |
| Poultry | 0.68 (0.44, 0.92) | 0.16–2.72 | 23 |
| Dairy | 0.65 (0.46, 0.84) | 0.19–1.16 | 13 |
| Cereals | 0.60 (0.43, 0.77) | 0.07–1.67 | 24 |
| Milk | 0.59 (0.40, 0.79) | 0.02–1.68 | 26 |
| Vegetables | 0.58 (0.44, 0.71) | 0.21–1.11 | 20 |
| Fish | 0.50 (0.30, 0.69) | 0.05–1.41 | 18 |
| Fats/oils | 0.48 (0.29, 0.66) | 0.14–1.00 | 13 |
| Cheese | 0.44 (0.25, 0.63) | 0.01–1.95 | 20 |
| Sweets/sugars | 0.34 (0.14, 0.53) | 0.05–1.00 | 13 |
| Eggs | 0.27 (0.08, 0.45) | 0.06–1.28 | 14 |

Other verified points:
- **Food at home overall: 0.59**, more inelastic than food away from home (0.81). The authors flag
  that 0.59 is based on only 7 studies (p. 219).
- **Income:** only 9 of the 160 studies estimate elasticities for low-income groups. The 3 broad
  studies report 0.62 for low-income households vs 0.64 for all consumers. Single-product studies
  found bigger gaps: milk 1.2 vs 0.66, fast food 2.09 vs 0.51 (p. 219).
- **What is measured:** category (primary) demand, which is what tax and subsidy analysis needs.
  The 12 brand-level studies were excluded (p. 218).
- **Worked example:** with fruit at 0.70 and vegetables at 0.58, a 10% price cut raises purchases
  by 7.0% and 5.8% (p. 221).
- **Method caveat:** the pooled figures are simple means, not a meta-analysis, because most studies
  don't report standard errors (p. 221).

### 3.2 Okrent & Alston (2012): USDA ERS report ERR-139

First-stage own-price elasticities for food groups, uncompensated (Table 4, p. 16):

| Group | Own-price elasticity |
|---|---|
| Cereals and bakery | −0.58 |
| Meat and eggs | −0.31 |
| Dairy | −0.05 (not significant) |
| Fruits and vegetables | −0.79 |
| Nonalcoholic beverages | −0.65 |
| Other food at home | −0.98 |
| Food away from home and alcohol | −0.71 |

Selected unconditional product elasticities, which account for substitution across all goods
(Table 6, p. 20):

| Product | Own-price | Product | Own-price |
|---|---|---|---|
| Eggs | −0.24 | Milk | −0.10 (n.s.) |
| Beef | −0.70 | Cheese | −0.70 |
| Poultry | −0.81 | Potatoes | −0.42 |
| Fish | −0.84 | Tomatoes | −0.58 |
| Pork | −1.26 | Lettuce | −0.84 |
| Nonwhite bread | −0.59 | Bananas | −1.01 |
| White bread | −1.54 | Processed fruits and vegetables | −0.77 |
| Cakes and cookies | −1.20 | Breakfast cereals | −1.05 |

Points relevant to us:
- Foods usually called "healthy" (fruits and vegetables, nonwhite bread, fish) tend to be less
  price-elastic than "unhealthy" ones (white bread, cakes and cookies, cheese) (Summary, p. iv).
- Cross-price effects are large. Forecasts that ignore substitution between food groups can even
  get the sign of a quantity change wrong (Summary, p. iv).
- Their group elasticities are smaller than the average of earlier studies. For example, fruits
  and vegetables average −0.91 across 4 earlier studies, and dairy −0.85 across 8 (Table 5, p. 18).

### 3.3 Dong & Lin (2009): USDA ERS report ERR-70, low-income households

- **Own estimates** (Nielsen Homescan 2004, households below 130% of poverty): fruit **−0.52**,
  vegetables **−0.69** (p. 7). For higher-income households: fruit −0.58, vegetables −0.57
  (Table 2, p. 7).
- **Literature range for low-income households:** Park et al. (1996) fruit −0.34, vegetables
  −0.32; Huang & Lin (2000) fruit −0.65, vegetables −0.70 (Table 2, p. 7). The report uses these
  as the small and large cases.
- **Policy simulation:** a 10% retail price discount for low-income households raises total
  consumption of fruit by 2.1–5.2% and vegetables by 2.1–4.9%. Most households still don't meet
  dietary guidelines (Summary, p. iii).
- **Income pattern is mixed:** earlier studies suggest low-income households respond *less* to
  fruit and vegetable prices. Dong & Lin find them more responsive for vegetables and less for
  fruit (p. 8).
- **Supply assumption (relevant to θ):** the authors note there is "no empirical estimate of retail
  supply elasticities for fruits and vegetables". They assume perfectly elastic supply, which means
  the whole discount reaches consumers, and say this may overstate the consumption response
  (p. 10).

---

## 4. Store-level elasticities (not downloaded; paywalled)

These measure how demand at *one store* responds to that store's prices, including customers who
switch to competitors. That makes them the right comparison for our logit store-choice model.
*Not verified against the full text*; the descriptions are from abstracts.

- **Hoch, Kim, Montgomery & Rossi (1995).** "Determinants of Store-Level Price Elasticity."
  *Journal of Marketing Research* 32(1):17–29. Store-specific elasticities for 18 categories
  across 83 supermarkets in one chain. Trading-area demographics and competition explain on
  average 67% of the variation in price response, and demographics matter more than competition.
- **Smith (2004).** "Supermarket Choice and Supermarket Competition in Market Equilibrium."
  *Review of Economic Studies* 71(1):235–263. A UK store-choice model. The elasticity of how much
  shoppers buy once they've chosen a store is set to about −0.7; store-level demand is more
  elastic once switching is included.

---

## 5. Implications for the project

**θ and the pass-through slides (`figures/slides/cs_4_*`, `cs_5_*`).** In the simple competitive
diagram, θ = demand steepness / (demand steepness + supply steepness). Market-level food demand is
inelastic (about 0.6 for food at home), which supports presenting the θ-high case, where steep
demand dominates. Two caveats:
- No source estimates retail *supply* elasticity for food (Dong & Lin, p. 10), so the slope of the
  supply curve is an assumption.
- With imperfect competition, pass-through also depends on demand curvature, not just elasticity
  (Weyl & Fabinger, already in the folder). The diagram is intuition, not a calibrated θ.

**β_p_i in the store-choice model.** The logit own-price elasticity β_p·p·(1−S) is about 12 / 4 /
2 for Low / Mid / High income at p ≈ $29 (`docs/MODEL_PLAN_AND_ASSIGNMENTS.md`). These numbers
should be compared with store-level elasticities (section 4), not with the category elasticities
above:
- Category elasticities (about 0.6) are a **floor**: a single store's demand must respond more
  than total food demand does.
- An elasticity of 12 means a 1% price cut raises a store's trips by 12%. That's high next to
  everything here, especially as low-income households are no more price-sensitive than average
  in the broad studies. This supports testing lower β_p values in run 2.

**The core basket.** The N.Y.C. Groceries discount covers produce, dairy, bread, meat and seafood.
At the category level these sit between about 0.3 (eggs) and 0.8 (fruit, meats). A 30% discount
would raise quantities in those categories by roughly 10–25% if the discount applied market-wide.
The store-level response is larger because shoppers switch stores.

---

## 6. Corrections to existing docs

- `docs/SIMPLIFIED_PLAN_AND_SOURCES.md` and `docs/MODEL_PLAN_AND_ASSIGNMENTS.md` describe 0.27–0.81
  as the range for *food categories*. That's correct, but the top of the range (0.81) is food
  *away from home*. For supermarket food the relevant figure is 0.59 (food at home), or 0.27–0.79
  across at-home categories.
- `docs/SOURCE_LIST_RAHUL.md` flags the Andreyeva range as "taken from a snippet; verify before
  citing". It is now verified against the PDF (Table 1, p. 219).
