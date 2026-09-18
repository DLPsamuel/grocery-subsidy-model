# Simplified Plan and Appendix F Sources

**Project:** Policy Levers for Grocery Access in Bronx Community District 2 (94-867)
**Drafted:** 2026-09-18 · **Status:** proposal for team discussion
**Companion doc:** [ISSUES_AND_GAPS.md](ISSUES_AND_GAPS.md)

---

## 1. Why simplify

The v3 spec is a store-by-store logit demand model. It needs price, volume, quality and distance data for every store, plus preference parameters we can't estimate well. With 7 weeks and no store-level price or sales data, that is too much, and it still wouldn't answer the proposal's main question: **FRESH vs. N.Y.C. Groceries**.

Sources we found this week also weaken the logit model's central mechanism: **"a subsidy lowers prices, so people switch stores"**.
- **Prices:** in the South Bronx in 2025, a standard food basket cost about the same at supermarkets and bodegas: $37.40–$43.00 across 10 ZIP codes (DOHMH Epi Data Brief 158).
- **Adoption:** new supermarkets in low-access neighborhoods are adopted as a household's main store at low rates (Dubowitz et al. 2015; Cummins et al. 2014). A subsidized supermarket in the Bronx did not change children's diets or home food availability (Elbel et al. 2015).
- **Supply vs. demand:** differences in what stores offer explain only about 9% of the nutrition gap between rich and poor households (Allcott et al. 2019).
- **FRESH prices:** there's no evidence that FRESH tax breaks lowered shelf prices. The Comptroller's 2024 evaluation reports none.
- **Contracted discount:** N.Y.C. Groceries doesn't rely on stores choosing to pass savings on. It *contracts* a 30% discount on a core basket and pays an "Affordability Payment" to cover it (NYCEDC RFP Q&A #1, Aug 2026).

**Takeaway:** the policy question is mostly an **accounting and store-economics** question, not a demand-estimation one. That is simpler to model and a better match for the real policies.

---

## 2. The simplified model

It keeps the same three decision questions from the proposal.

### Building block 1: Who shops at the store, and how much

| Symbol | Meaning |
|---|---|
| N_i | Households in CD2 by income group (Low / Mid / High), from ACS. **Already in the repo.** |
| F_i | Yearly food-at-home spending per household, from BLS CE (NY metro, by income quintile) |
| c_i | **Capture share:** fraction of that spending that goes to the policy store (a scenario input, 10–40%) |
| κ | Share of spending that falls in the "core basket" (produce, meat, fish, some dairy/pantry), from BLS CE category shares |

Core-basket spending at the store, at market prices:
**V = κ · Σ_i N_i · c_i · F_i**

### Building block 2: Store economics (one year)

**π₀ = GM · R − (labor + rent + property tax + other costs)**
- R = sales = sales per sq ft × sq ft
- GM = gross margin
- π₀ = profit before any subsidy

Industry benchmarks (FMI, company 10-K filings) replace store-level data we don't have.

### Building block 3: The two policies

**A. N.Y.C. Groceries (city-owned store, contracted discount d = 30%)**
- Consumer savings: **S_B = d · V**
- Public cost (rent and tax relief + Affordability Payment): **C_B = d · V − π₀ + fee**
  - "fee" is the operator's "modest margin" (RFP Q&A #25).
- Public $ per consumer $ saved: **C_B / S_B = 1 + (fee − π₀) / (d · V)**

**B. FRESH-style tax break s to a private store**
- Consumer savings: **S_A = θ · s + 1[subsidy is what makes the store viable] × access gain**
  - θ = pass-through. Tax and rent relief lowers a *fixed* cost, and standard theory says fixed costs don't move prices. So θ is uncertain and possibly near 0 unless competition forces it. Run it as scenarios: θ ∈ {0, 0.25, 0.5, 1}.
  - Access gain = the benefit of having a store at all (shorter trips, better selection), counted only when the subsidy is what makes the store viable.
- Public cost: C_A = s. For scale: FRESH cost about $3–4M a year across 27 stores, roughly **$110–150K per store per year** (NYC Comptroller 2024).

### How each decision question gets answered

| Proposal question | Model output |
|---|---|
| Q1. How does the subsidy amount relate to money consumers save? | A **savings vs. subsidy curve** for each policy. Savings are zero until the store is viable (it breaks even), then rise in a straight line with slope 1 (N.Y.C. Groceries) or θ (FRESH). |
| Q2. What is the ideal subsidy for a given level of welfare? | Work backwards from a target, e.g. "$X per low-income household per year": d* = target / V, and the cost follows from C_B. |
| Q3. How does the required subsidy change across store types? | Repeat for store formats (bodega, medium grocery, supermarket, N.Y.C. Groceries format) using each format's sales and margin. The cost of a d% price cut is s_k = d · V_k / θ_k, so it grows with store size and falls with pass-through. |
| Fairness | The share of savings going to low-income households: d · κ · N_low · c_low · F_low / S |

### What we drop, keep and add

| Drop | Keep (reuse Samuel's work) | Add |
|---|---|---|
| Store-by-store logit, logsum formula, distance matrix | ACS households by income | BLS CE NY spending by income (manual download) |
| α_j, β_p, β_d, V_ij, s_ij for each store | CD2 boundary and tracts (maps) | DOHMH 2025 South Bronx prices |
| ReferenceUSA, NielsenIQ | Store lists (count store types, map them) | FMI and 10-K store economics |
| Matching tax and rent for every store | Phase 3 tax and rent (to size FRESH-type relief by store type) | EDC RFP terms (discount, Affordability Payments) |

### Optional extensions, only if time allows

1. **Store portfolio in Gurobi (keeps the proposal's promised solver phase):** choose from a menu of interventions: N.Y.C. Groceries with d ∈ {10, 20, 30%}, a FRESH-type break by store format, a discount program at existing stores. Maximize savings for low-income households subject to budget B and each store breaking even. It's a small integer program (a knapsack) and takes about a day to build.
2. **Capture share from a simple logit:** set c_i as a function of the discount, using the food price elasticities in Andreyeva et al. (2010), instead of fixed scenarios.

---

## 3. Seven-week plan

| Week | Deliverable | Lead |
|---|---|---|
| 1 | Team agrees on this plan and updates the proposal wording (the model changes; the decision question doesn't) | All |
| 2 | Parameter sheet filled in from Section 4, with a range for every value | R (store), C (behavior/policy), S (demographics/spending) |
| 3 | Python calculator: `savings(policy, params)`, `cost(policy, params)`, base case | R + S |
| 4 | Q1–Q3 outputs, savings-vs-subsidy curves, fairness breakdown | All |
| 5 | Sensitivity analysis (capture share, θ, margin, sales per sq ft, discount depth, budget); optional Gurobi portfolio | C + R |
| 6 | Charts, maps, policy memo draft | S + All |
| 7 | Final report and presentation; chat-history archive | All |

---

## 4. Appendix F sources for the simplified model

Status: ✅ verified and ready · 🟡 source found, needs a manual download or extraction · ⚠️ weak or unsourced, replace or treat as a scenario.

### Demand side

| Parameter | Value / range | Source | Status | Lead |
|---|---|---|---|---|
| N_i, households by income (2024) | Low 7,683 · Mid 4,795 · High 7,444 · total 19,922 | ACS 2024 5-year, B19001/B11001, in repo `data/acs/` | ✅ | S |
| F, food-at-home spending | **$7,033 per household per year** (NY metro, 2023–24, all households) | [BLS: Consumer Expenditures in the NY Metro Area 2023–24](https://www.bls.gov/regions/northeast/news-release/consumerexpenditures_newyork.htm) | ✅ | S |
| F_i by income | Income-quintile table for New York | [BLS CE geographic tables](https://www.bls.gov/cex/tables/geographic/mean.htm#msa) (the same source NYCEDC's vision plan cites). Use a browser; scripts get HTTP 403. | 🟡 | S |
| κ, core-basket share of spending | Fruit/vegetables + meat/poultry/fish/eggs + part of dairy | [BLS CE tables](https://www.bls.gov/cex/tables.htm) (food-at-home category detail) | 🟡 | R |
| c_i, capture share | Scenarios 10 / 25 / 40% | Low adoption of new stores: [Dubowitz et al. 2015, *Health Affairs*](https://www.healthaffairs.org/doi/10.1377/hlthaff.2015.0667); [Cummins et al. 2014, *Health Affairs*](https://pubmed.ncbi.nlm.nih.gov/24493772/). In two Bronx neighborhoods, 97% shop at neighborhood supermarkets, 60% weekly, 83% walk (mean 9.1 min): [Dannefer et al. 2015, *AIMS Public Health*](https://pmc.ncbi.nlm.nih.gov/articles/PMC5690258/). La Marqueta area foot traffic about 4,300 per week: NYCEDC RFP Q&A #1, Q21. | ✅ as a scenario range | C |
| Price elasticity (extension only) | 0.27–0.81 (absolute value) by food category | [Andreyeva, Long & Brownell 2010, *AJPH*](https://ajph.aphapublications.org/doi/full/10.2105/AJPH.2008.151415) | ✅ | C |

### Prices and stores

| Parameter | Value / range | Source | Status | Lead |
|---|---|---|---|---|
| Basket price by store type, South Bronx | $37.40–$43.00 per standard basket (2025, 10 ZIP codes including 10474 Hunts Point). **Supermarket ≈ bodega.** 1 supermarket per 6 bodegas. | [NYC DOHMH Epi Data Brief 158, Apr 2026](https://www.nyc.gov/assets/doh/downloads/pdf/epi/databrief158-south-bronx-food-environment.pdf) | ✅ | R |
| NYC supermarket basket prices, store level | 10-item basket, mean $22.81 (range $16.20–$35.11), 163 stores, 2019 | [Crossa et al. 2023, *Data in Brief*](https://pmc.ncbi.nlm.nih.gov/articles/PMC10293947/); data on [GitHub](https://github.com/nychealth/food-pricing-survey-nyc-2019/) | ✅ (2019, adjust with CPI) | R |
| Price differences by store format (national) | Supermarkets usually cheapest | [Kaufman et al. 1997, USDA ERS AER-759](https://ers.usda.gov/sites/default/files/_laserfiche/publications/40816/32372_aer759.pdf) | ✅ (old, background only) | R |
| Discount d | 30% on core basket (all produce, meat and seafood, plus some dairy, shelf-stable and frozen) | [N.Y.C. Groceries Vision Plan, Summer 2026](https://edc.nyc/program/nyc-groceries) (in repo `docs/`) | ✅ | — |
| Peninsula store size | **15,000 sq ft**, opening late 2027 (Phase 1 report says 20,000; the vision plan is newer) | Vision Plan p.10 | ✅ | S |
| Store types in CD2 | About 97 active SNAP retailers, including 5 supermarkets, 3 super stores, 2 large grocery | Repo `snap_bronx_cd2.csv`, filtered to rows with no `End Date` | 🟡 re-run the filter | S |

### Store economics

| Parameter | Value / range | Source | Status | Lead |
|---|---|---|---|---|
| Sales per sq ft | **$19.59 per sq ft per week** (about $1,019 per year) | [FMI Food Industry Facts (2025)](https://www.fmi.org/our-research/food-industry-facts) | ✅ | R |
| Supermarket size and sales | Median 42,272 sq ft; $668,377 per week; $49.06 per transaction | FMI (2025) | ✅ | R |
| Net profit margin | 2.1% (2025); 1.7% (2024) | FMI; [Grocery Dive](https://www.grocerydive.com/news/grocery-industry-profit-margins-fall-to-pre-pandemic-levels-fmi/720517/) | ✅ | R |
| Gross margin | About 22% (Kroger FY2024, as reported); add Albertsons for a range | Kroger and Albertsons 10-K filings (SEC EDGAR) | 🟡 confirm in the 10-Ks | R |
| Bronx grocery sales per store | Sales and establishment counts, NAICS 445110 and 445131, Bronx County | [2022 Economic Census, table EC2244BASIC](https://www.census.gov/data/tables/2022/econ/economic-census/naics-sector-44-45.html) via data.census.gov (the API needs a key) | 🟡 | R |
| Rent | $20–35 per sq ft per year (from the spec, **no source given**) | Replace with Hunts Point retail listings or a broker report; or use Phase 3 square-footage rents as a check | ⚠️ | R + S |
| Property tax | Lot-level DOF charges; median about $336K (whole building) | Repo `data/phase3/` (scale by retail share of floor area) | 🟡 | S |
| Operator fee | "Modest margin"; use 1–2% of sales | NYCEDC RFP Q&A #1, Q25 and Q37 | ✅ as a range | R |

### Policy parameters

| Parameter | Value / range | Source | Status | Lead |
|---|---|---|---|---|
| Affordability Payment structure | Sized to offset the 30% discount; annual cap agreed with the operator; funded separately from capital, rent and tax relief; needs budget approval. Core items often have markups under 30%, so they are sold below cost. | [NYCEDC RFP Q&A #1 (Aug 14, 2026)](https://edc.nyc/sites/default/files/2026-08/26.08.14_Round%201%20Q%26A%20vF.pdf) | ✅ | C |
| City's in-kind support | City covers rent and property taxes and funds the initial buildout | Vision Plan p.9 | ✅ | C |
| Capital budget | $70M for 5 stores (about $14M per site; capital, not yearly) | [NYCEDC N.Y.C. Groceries](https://edc.nyc/program/nyc-groceries) | ✅ | All |
| FRESH benefits and cost | Property tax abatement up to 25 years; mortgage recording tax cut from 2.8% to 0.3%; $29.2M total through FY2023; $3–4M per year; 27 stores; **no evidence on prices** | [NYC Comptroller 2024 FRESH evaluation](https://comptroller.nyc.gov/reports/good-jobs-and-the-new-york-city-fresh-program-evaluation-and-recommendations/) | ✅ | C |
| θ for Affordability Payments | 1, by contract | RFP Q&A #1 | ✅ | C |
| θ for a FRESH-type fixed-cost break | Scenarios {0, 0.25, 0.5, 1}. Theory: fixed costs don't move prices ([Weyl & Fabinger 2013, *JPE*](https://doi.org/10.1086/670401)). Local *per-unit* cost changes, such as taxes, are passed through to prices ([Butters, Sacks & Seo 2022, *AER*](https://www.aeaweb.org/articles?id=10.1257%2Faer.20201524)). | 🟡 scenario | C |
| Budget B | Scenario range; the yearly Affordability Payment cap hasn't been published | RFP Q&A #1, Q5 | ✅ as a scenario | All |

### Context and framing (for the report introduction and limitations)

- **Nutrition gap:** stores explain only about 9% of it ([Allcott et al. 2019, *QJE*](https://academic.oup.com/qje/article/134/4/1793/5492274); [NBER w24094](https://www.nber.org/papers/w24094)).
- **Bronx FRESH supermarket:** no measurable change in children's diets ([Elbel et al. 2015, *Public Health Nutrition*](https://www.cambridge.org/core/journals/public-health-nutrition/article/assessment-of-a-governmentsubsidized-supermarket-in-a-highneed-area-on-household-food-availability-and-childrens-dietary-intakes/C998CF42FACEDADAE59D906CE63D04B7)).
- **Grocery burden:** NYC households spend about 6% of income on groceries, and low-income households up to 25% (Vision Plan, citing BLS CE).
- **Food insecurity:** about 15% of New Yorkers ([NYC Food by the Numbers, Jan 2025](https://www.nyc.gov/assets/foodpolicy/downloads/pdf/NYC-Food-by-the-Numbers-2024.pdf)).
- **Neighborhood profile:** NYC DOHMH Community Health Profile, *Hunts Point and Longwood (BX 202)*, at nyc.gov/health/profiles.

---

## 5. Decisions the team needs to make

1. Do we adopt this simplified model as the core, with the logit as an optional extension?
2. Which welfare target do we use for Q2 (for example, $ per low-income household per year)?
3. Is the Gurobi portfolio in scope (it keeps the proposal's promise), or is it optional?
4. Do we tell the instructor that the model changed? The decision question stays the same.
