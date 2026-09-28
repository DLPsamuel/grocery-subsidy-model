# Lead = C parameters: source inventory and library requests

**Owner:** Chris · **Scope:** Appendix F rows with Lead = C (β_p_i, β_d_i, θ), plus trips per year
(ISSUES_AND_GAPS #4) · **Last verified:** 2026-09-27

Every figure quoted below was checked against the paper itself. Page and table references are to
the PDFs in `docs/research_papers/`, except Hillier et al., which was checked against the PMC full
text (the PDF still needs to be added).

This complements `docs/ISSUES_AND_GAPS.md` and `docs/SIMPLIFIED_PLAN_AND_SOURCES.md` and follows the
θ plan in the latter.

---

## 1. Summary

| Symbol | Spec value | Status | Recommended handling |
|---|---|---|---|
| β_p_i | Low 0.55 · Mid 0.30 · High 0.15 | **Citation does not support it** | Derive from β_d and USDOT value of time: Low 0.43 · Mid 0.14 · High 0.06 (see §3); α_j calibrated to shares given β_p |
| β_d_i | Low 0.40 · Mid 0.25 · High 0.15 | **Level sourced, gradient not** | Hillier level (per mile → convert to d_ij units); gradient pending Taylor & Villas-Boas |
| θ | 0.65 (0.40–0.85) | **0.65 unsourced** | θ = 1 for N.Y.C. Groceries (contracted); θ ∈ {0, 0.25, 0.5, 1} for FRESH-type breaks |
| trips/yr | not in spec | **Borrowed (Dannefer 2016); unit choice open** | ~40 supermarket visits/yr, or 52·f̄/p_j ≈ 128/158/255 basket-equivalents. Team must pick the unit (ISSUES #4) |

---

## 2. Papers in `docs/research_papers/`

| File | Citation | Serves | What it actually says (verified) |
|---|---|---|---|
| `hillier_etal_2017_foodaps_discrete_choice.pdf` | Hillier, Smith, Whiteman & Chrisinger (2017). *IJERPH* 14(10):1133. Open access: PMC5664634 | β_d | Conditional logit on FoodAPS store trips. Table 2: **DIST −0.3736** (z −8.67), **DIST-URBAN −0.1745** (z −7.49), DIST-SNAP −0.0043 (p 0.836), DIST-RACE 0.0631 (p 0.06), DIST-CAR is internally inconsistent in the published table (coef −0.0043, z +1.96; the text says car owners travel further), so don't use it. SQFT 0.0170 (z 6.64), SQFT-URBAN −0.0072 (z −4.96): used for γ_sq. **Distance in miles.** No income interaction. |
| `cao_etal_2026_cowles_d2508_willingness_to_travel.pdf` | Cao, Chevalier, Handbury, Parsley & Williams (2026). Cowles Foundation Discussion Paper 2508 | β_d | Instruments for endogenous store location. Treating distance as exogenous **understates distance coefficients by 37% (income Q1) and 43% (Q4)** (p. 7). Setting is general-merchandise chains, not grocery. |
| `marshall_pires_2017_travel_costs_grocery.pdf` | Marshall & Pires (2018). "Measuring the Impact of Travel Costs on Grocery Shopping." *Economic Journal* 128(614):2538–2557. File is the May 2017 working paper | β_d : β_p ratio | Store convenience (travel cost), not prices or variety, drives grocery store choice. Sanity check: if our calibration lets price dominate distance, we are out of line with this. |
| `dube_gupta_2008_crossbrand_passthrough.pdf` | Dubé & Gupta (2008). *Marketing Science* 27(3):324–333 | θ | Cross-brand pass-through **elasticities** across 11 categories. No 0.65. |
| `besanko_dube_gupta_2005_own_crossbrand_passthrough.pdf` | Besanko, Dubé & Gupta (2005). *Marketing Science* 24(1):123–137 | θ | The spec's primary θ citation. Abstract: own-brand pass-through rates "on average, more than 60% for 9 of 11 categories." This is per-unit wholesale-cost pass-through, not a share of a fixed-cost subsidy. |
| `allcott_etal_2017_nber_w24094_fooddeserts.pdf` | Allcott, Diamond, Dubé, Handbury, Rahkovsky & Schnell. NBER WP 24094 (published *QJE* 134(4), 2019) | context, α_j | Table 4 = "Preferences for Nutrients by Household Income", in Healthy Eating Index units. **No store-choice price coefficient.** |

---

## 3. Parameter detail

### θ (pass-through)

- **0.65 has no traceable source.** It is not in Besanko et al. (2005) or Dubé & Gupta (2008). The
  closest figure is Besanko's ">60% on average", which measures a different thing.
- **Different object:** the literature reports elasticities or rates for per-unit wholesale cost
  changes. Our θ is the fraction of subsidy dollars that reaches shoppers via Δp_j = θ·s/Q_j.
- **Different mechanism:** tax and rent relief cut *fixed* costs. Standard theory says a
  profit-maximiser's price does not respond (θ ≈ 0; Weyl & Fabinger 2013).
- **Handling:** as in `SIMPLIFIED_PLAN_AND_SOURCES.md`: **θ = 1 for N.Y.C. Groceries**, because the 30%
  core-basket discount is written into the operator contract and covered by Affordability Payments
  (RFP Round 1 Q&A). **θ ∈ {0, 0.25, 0.5, 1} for FRESH-type breaks.** Report whether the lever
  ranking changes across that range.

### β_p_i (price sensitivity)

- The spec cites Allcott et al. (2019) Table IV. That table reports nutrient-characteristic
  preferences by income quartile (HEI units, e.g. cups of produce). The paper's Cobb-Douglas form
  "typically restricts product group price elasticities to one", though it lets them vary through
  unobserved characteristics. There is **no store-choice price coefficient** to borrow.
- With β_p = 0.55 per basket dollar, a $6 price gap outweighs the +1.5 supermarket α_j, which gives
  supermarkets roughly 0% share (ISSUES #5).
- **Correction (9/28):** observed store shares can pin down α_j given β_p, but not β_p as well. β_p
  has to come from outside the share data.
- **Handling (adopted in `docs/MODEL_PLAN_AND_ASSIGNMENTS.md`):** β_p,i = −β_d / value of a minute for
  group i. USDOT travel-time guidance: local personal travel at 50% of the hourly wage, walking time at
  100%. Hourly income = group median (from B19001 brackets: $13.3K / $39.8K / $92.5K) ÷ 2,080. With
  β_d = −0.0227/min this gives **Low 0.43 · Mid 0.14 · High 0.06** per basket dollar (100% values:
  0.21 / 0.07 / 0.03). Status DERIVED. Taylor & Villas-Boas would give an estimated willingness to
  travel to check it against.
- **Elasticity check:** the logit own-price elasticity β_p·p·(1−S) at p ≈ $29 is about 12 / 4 / 2,
  above food category elasticities (0.27–0.81, Andreyeva et al. 2010). Run 2 sweeps β_p to test this.

### β_d_i (distance sensitivity)

- **Level:** Hillier DIST + DIST-URBAN ≈ **−0.55 per mile** for a >90%-urban county (CD2 qualifies).
- **Units:** the spec measures d_ij in minutes (15 min/km). At 15 min/km, 1 mile ≈ 24.1 min, so
  about −0.023 per minute. Whichever unit the model uses, convert once and document it.
- **Gradient:** Hillier has no income interaction, and DIST-SNAP is insignificant. The spec's
  Low/Mid/High split (0.40/0.25/0.15) is unsourced.
- **Bias direction:** Cao et al. imply naive (exogenous-distance) estimates like Hillier's are too
  small in magnitude, by roughly 37–43% in their setting. Use this as an upper sensitivity bound.
- **Sign convention (proposed for `params.py`):** raw coefficients, so β_d is negative and distance
  enters utility with a plus. Published values then drop in without re-signing.
- **Vehicle access:** the spec suggests scaling by ACS B08201 (households without a vehicle). CD2
  B08201 data **has not been downloaded yet**; an earlier draft quoted "71.9% car-free" without a
  data file behind it. Do not cite that figure until the summary exists in `data/acs/`.

### Trips per year (new; needed for ISSUES #4)

- logsum/β_p gives dollars per shopping trip. ΔCS per year needs trips/yr.
- **Source read (2026-09-28):** Dannefer, Adjoian, Brathwaite & Walsh (2016), "Food shopping
  behaviors of residents in two Bronx neighborhoods," *AIMS Public Health* 3(1):1–12,
  doi:10.3934/publichealth.2016.1.1 (online Dec 2015; PMC5690258). Street-intercept survey,
  April 2012, West Farms (10460) and Fordham (10458), n = 505, 40% response rate.
  - Table 2, supermarkets: ever shops at a neighbourhood supermarket 96.8%; **once per week or more
    60.1%**; less than once per week 36.7%; never 3.2%. Usual supermarket inside the neighbourhood
    83.8%, outside 16.2%.
  - Table 2, bodegas: ever 94.6%; **once per day or more 65.5%**.
  - Table 3: 83% walk to their usual supermarket, mean 9.1 min (7 min if it's in the neighbourhood,
    19 min if outside).
  - No income, SNAP or car-ownership breakdown, so any trips/yr from this source is the same for
    every income group.
- **Caveats:** these are neighbouring areas, not CD2 (Hunts Point / Longwood is 10459/10474/10455);
  the data are from 2012; "once per week or more" is top-coded, so the weekly rate is a floor.
- **Physical visits (supermarket):** 0.601 × 52 + 0.367 × 24 ≈ **40/yr**, assuming less-than-weekly
  shoppers go twice a month; **36–49** if that group goes 1–4 times a month. Round scenario: 52.
  BORROWED + assumption.
- **Units decide which number is right.** β_p is per *basket* dollar and the spec defines
  Q_j = Revenue_j / p_j in basket-trips, so a "trip" in the model is one p_j basket, not one visit.
  In those units, trips/yr = 52 · f̄_i / p_j. With mean p_j = $29.10 (6 CD2 stores), that is
  **Low ≈ 128 · Mid ≈ 158 · High ≈ 255** basket-equivalents per year (f̄ caveats apply: US
  averages). The visit counts above are 3–6× smaller. The team has to pick one definition and use
  it for both Q_j and ΔCS annualisation (ISSUES #4).
- **Bodegas:** 65.5% shop at a bodega daily. If J includes bodegas (the 137-store option), bodega
  visits are small top-up trips, not full baskets. That is one more reason to count trips in
  basket units rather than visits.
- **Also relevant to β_d:** 83% walk, whereas 84.7% of Hillier's FoodAPS sample had a car and
  Hillier measures *driving* miles. Hillier's per-mile coefficient probably understates distance
  sensitivity for CD2's mostly walking shoppers. This supports using the Cao et al. +37–43% as the
  upper sensitivity bound.
- **Capture share c_i (simplified plan):** Dannefer isn't a capture-share estimate. It shows strong
  loyalty to nearby stores: 84% use an in-neighbourhood supermarket, and 16% shop outside, which
  gives an outside-option share. Keep c_i ∈ {10, 25, 40%} as scenarios, anchored on the
  low-adoption evidence (Dubowitz 2015; Cummins 2014).

---

## 4. Library requests (priority order)

1. **Taylor, R. & Villas-Boas, S. B. (2016).** "Food Store Choices of Poor Households: A Discrete
   Choice Analysis of the National Household Food Acquisition and Purchase Survey (FoodAPS)."
   *American Journal of Agricultural Economics* 98(2):513–532. Mixed logit on FoodAPS by store type,
   with heterogeneity by income/SNAP. The best candidate for a β_d income gradient and for
   willingness to travel. Marshall & Pires cite it (p. 4).
2. **Kim, S. & Kim, D. (2025).** "The role of geographic market definition in the analysis of grocery
   retailing." *AJAE* 107(1):208–230. Store choice with both distance and basket prices.
3. **Nakamura, E. & Zerom, D. (2010).** "Accounting for Incomplete Pass-Through." *Review of Economic
   Studies* 77(3):1192–1230. The spec's second θ citation (coffee industry).
4. **Ben-Akiva, M. & Lerman, S. R. (1985).** *Discrete Choice Analysis.* MIT Press. The spec cites Ch. 5
   for β_d; check whether it contains empirical values or only theory.
5. **Dannefer et al. (2015)** full text for trips per year. Open access, so no library request needed.

No longer needed from the library: Besanko et al. (2005), which is free from the author and now in
the repo. Same trip, not a Lead = C item: ReferenceUSA / Data Axle for `Revenue_j` (Rahul).

---

## 5. Open dependencies on other leads

- **Store set J** (S): β_p/α_j calibration depends on which stores are in the choice set.
- **Basket definition** (R/S): β_p is per basket dollar.
- **Vehicle access B08201** (S): needed before any car-free scaling of β_d.
