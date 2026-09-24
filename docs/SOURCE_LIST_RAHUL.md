# Source List — annotated

**Project:** Policy Levers for Grocery Access in Bronx Community District 2 (94-867)
**Compiled by:** Rahul Tejannavar · **Date:** 2026-09-21 · **Updated:** 2026-09-24
**Model:** LEVEL 1 NYC Grocery Subsidy Model Specification (v3), Appendix F

Sources for my Appendix F rows (Lead = R) and supporting context, what each one actually contains, and which parameter it feeds. Sources are grouped by how far verification actually got, because that determines what we can safely cite in Appendix F.

- **Tier A** — the document was opened and read; figures below are quoted from the source itself.
- **Tier B** — identified, but only ever seen as a search-result snippet. Titles and URLs are confirmed real; the numbers are not yet verified in situ.
- **Tier C** — identified but not retrieved at all.

Each **Feeds** line is tagged by how the source is used:

- **[input]** — a number from the source goes directly into a model calculation. Remove the source and a model value changes.
- **[context]** — the source supports, explains or sanity-checks a value, but no number from it is plugged in.

---

# Status of my Appendix F rows (v3 spec, Lead = R), as of 2026-09-24

The v3 spec's Appendix F has six rows with R in the Lead column. This table maps each one to the data we now have.

Status: ✅ have it · 🟡 have a first estimate, can be improved · ⚠️ assumption, no source

| Symbol | What it is | Status | Data we have | Still open |
|---|---|---|---|---|
| J | Number of candidate stores | ✅ | **6 stores:** SNAP-eligible CD2 stores with at least 6,000 sq ft (the FRESH minimum). Key Food 1050 Westchester Ave (15,000), Food Fair Fresh Market 1065 E 163rd St (13,000), Fine Fare 950 Westchester Ave (10,000), Food Universe 724 Hunts Point Ave (8,000), C-Town 564 Southern Blvd (8,000), C Town 809 Southern Blvd (7,500). Source: `data/stores/agmarkets_bronx_cd2_snap_eligibility.csv` (Samuel's Ag & Markets–SNAP linkage). CD2 has 97 active SNAP retailers in total. | Team to confirm the 6,000 sq ft cut-off |
| e_j | Store eligibility (1/0) | ✅ | SNAP-authorized with no end date, located in CD2, and at least 6,000 sq ft of grocery space (FRESH threshold, NYC Comptroller 2024) | Same decision as J |
| α_j | Store quality score by type | ✅ type / ⚠️ values | Store type for every store from the SNAP `Store Type` column (3 Supermarket, 3 Super Store among the 6) | The +1.5 / 0 / −1.5 values come from the spec and have **no citation**. Label them as assumptions and test them in sensitivity analysis. |
| p_j | Price of the 10-item basket at each store | 🟡 | Built in `data/prices/p_j_cd2_candidate_stores.csv` (script `code/build_p_j.py`). Aug 2026 prices: Key Food $27.76, Food Fair $28.95, Fine Fare $30.32, Food Universe $29.93, both C-Towns $28.82. Method: 2019 DOHMH survey (Crossa et al.), adjusted by BLS CPI food at home for NY metro (series CUURS12ASAF11), factor 1.31 from Mar–Aug 2019 to Aug 2026. | Only Key Food is a direct match. The others use same-chain Bronx averages; Food Fair uses the all-Bronx average. An Instacart or in-store check of the 6 stores would replace these proxies. |
| Revenue_j | Annual sales of each store | 🟡 | Square footage for each store (above) × sales per sq ft. The only rate so far is FMI's national **$19.59/sq ft/week (≈$1,019/yr)**. | Compute the first estimate. Replace the national rate with a Bronx one from the 2022 Economic Census (NAICS 445110, Bronx County) if time allows. The FMI rate likely overstates sales for stores this small. |
| Q_j (shared with S) | Baskets sold per year | 🟡 derived | Q_j = Revenue_j ÷ p_j, so nothing new is needed | Available once Revenue_j is computed. Cross-check against Samuel's market size M. |

**Bottom line:** every R row now has a data source. What remains is computing Revenue_j and Q_j, not finding new data.

---

# Tier A — documents that were opened and read

## 1. NYC DOHMH, Epi Data Brief No. 158 — *The Food Retail Environment in the South Bronx, 2019 to 2025* (Apr 2026)

[PDF](https://www.nyc.gov/assets/doh/downloads/pdf/epi/databrief158-south-bronx-food-environment.pdf) · fetched, text extracted from the PDF

**Store counts** (Shop Healthy NYC assessments, 1,102 establishments, 2019–2024):

| Type | N | Share |
|---|---|---|
| Bodegas | 384 | 35% |
| Fast food / limited service | 255 | 23% |
| Supermarkets | 64 | 6% |
| Fresh produce stores | 29 | 3% |

Ratio: **1 supermarket : 6 bodegas : 4 fast food**. The 2012 Crotona–Tremont study had 1:10, so the gap has narrowed.

**Availability:** 68% of bodegas sell fresh produce; 32% lack fresh vegetables (excluding onions and potatoes), 13% lack fruit. Supermarkets: 98% fruit, 100% vegetables. Of stores with delis (168 bodegas, 20 supermarkets), only 3% and 5% respectively list a healthy option.

**Prices, 2025** (N=113 stores): the standard basket cost **$37.40–$43.00 across 10 South Bronx ZIP codes**. In 6 of the 10 ZIPs, fewer than 80% of basket items were available. Item-level: eggs avg **$7.75/dozen**, deli beef avg **$12.90/lb**, lettuce **$1–$4.99/head**, avocados **$1–$5 each**, tomatoes **$0.79–$4.99/lb**. Some items cost more than 4× the lowest price found.

**Feeds:** **[context]** p_j (price context for the South Bronx). The brief states that "the cost of food in supermarkets and bodegas was similar," which matters for how much price differences can drive store choice in the model.

**Two precision points when citing it:**

- The **$37.40–$43.00 is a range across ZIP codes**, not a supermarket-vs-bodega split, so it can't be used as a price by store type. The store-type claim is qualitative in the source, with no numbers attached.
- The text says 10 ZIP codes; the footnote lists **eleven** (10451–10460 plus 10474). Hunts Point 10474 is in the footnote, so CD2 coverage holds either way, but cite it carefully.

Also note a conflicting popular claim surfaced in the same search: a CBS / Measure of America comparison put bodega prices ~16% above supermarkets on a 5-item basket. Different basket, different method, no peer review — but if we assert "prices are similar," expect someone to raise it.

## 2. NYC Comptroller — *Good Jobs and the New York City FRESH Program* (Oct 2024)

[Report](https://comptroller.nyc.gov/reports/good-jobs-and-the-new-york-city-fresh-program-evaluation-and-recommendations/) · fetched

**Scale:** 53 FRESH stores opened or under development since 2009; **27 received tax subsidies** as of FY2023. 11 of the 27 (40%) sit within a half-mile of another recipient.

**What the subsidy actually is:**

- Land taxes partially or fully abated up to **25 years**; building taxes stabilized at pre-improvement levels up to 25 years
- Land abatement = **$500 × each FTE** (outside Empire/Empowerment Zones)
- Sales tax waived on construction/renovation materials
- **Mortgage recording tax 2.8% → 0.3%**
- Zoning: extra residential FAR in mixed-use buildings, reduced parking minimums, saturation cap of 40,000 sq ft of FRESH grocery space per half-mile

**Cost:** **$29.2M total through FY2023**, of which $25.3M (87%) is property tax. Peak **$4.0M in FY2021**; recent years $3–4M/yr. Dividing gives roughly **$110–150K per store per year** ($3–4M ÷ 27). That is **our own arithmetic**, not a number the Comptroller prints, so label it as derived. It is a useful baseline for the starting subsidy s.

**Eligibility thresholds:** min 6,000 sq ft of general grocery, ≥50% of selling area for general food, ≥30% perishables, 500 sq ft fresh meat/produce.

**Geography:** clusters in Central Brooklyn, Northern Manhattan and the Bronx; 23 of 59 community districts eligible for zoning benefits.

**Labor findings currently unused:** 1,869 FTE jobs at FRESH stores in FY2023 (63% at unionized ShopRite/Food Bazaar, 13% Western Beef non-union, 24% mixed/unknown). NYC grocery floor workers' median wage **$15.25/hr**, supervisors **$22.73/hr**. Only **46%** of full-time grocery workers get employer health insurance vs. 74% citywide. This is a whole equity dimension sitting unused — and it is the report's actual thesis, since the title is "Good Jobs."

**Feeds:**

- **[input]** s — the ~$110–150K per store per year baseline sets the starting range for the subsidy grid search
- **[input]** e_j and J — the 6,000 sq ft minimum is the cut-off used to pick the candidate stores
- **[context]** θ — the report gives no evidence that FRESH lowered shelf prices

## 3. NYCEDC — N.Y.C. Groceries RFP, Round 1 Q&A #1 (Aug 14, 2026)

[PDF](https://edc.nyc/sites/default/files/2026-08/26.08.14_Round%201%20Q%26A%20vF.pdf) · WebFetch returned raw binary; the downloaded PDF was read directly

Sections: Core Basket Items and Pricing, Labor, Proposal Requirements, Site Selection, Store Operations, supplier sourcing. Authored by Leyla Arcasoy, created Aug 13, 2026.

- **Q1** — the 30% discount on the core basket, with an **Affordability Payment** sized to offset it. Core items often carry markups below 30%, so they would be sold below cost. Relevant to θ: under N.Y.C. Groceries the discount is written into the contract, so pass-through is effectively 1, compared with the spec's base case of 0.65.
- **Q5** — an annual cap agreed with the operator, funded separately from capital / rent / tax relief, requiring budget approval. The cap itself is not published, which is relevant to budget B.
- **Q21** — La Marqueta area foot traffic ~**4,300/week**.
- **Q25, Q37** — operator earns a "modest margin" (not quantified).

**Feeds:** **[context]** θ and B. No number from it is plugged into the model.

## 4. FMI — Food Industry Facts (2025)

[Page](https://www.fmi.org/our-research/food-industry-facts) · fetched. FMI's underlying sources: *The Food Retailing Industry Speaks* and NielsenIQ TDLinx.

| Metric | Value |
|---|---|
| Weekly sales per sq ft | **$19.59** (≈$1,019/yr) |
| Avg weekly sales per supermarket | $668,377 |
| Median store size | 42,272 sq ft |
| Net profit after taxes | **2.1%** (2025); 1.7% (2024, per [Grocery Dive](https://www.grocerydive.com/news/grocery-industry-profit-margins-fall-to-pre-pandemic-levels-fmi/720517/)) |
| Sales per in-store transaction | $49.06 |
| Items carried | 33,248 |
| US supermarkets | 45,575 (2024) |

**Feeds:** **[input]** Revenue_j = sales per sq ft × store square footage.

**Caveat for the limitations section:** these are national medians for a **42,272 sq ft** store, while the CD2 candidate stores are **7,500–15,000 sq ft** (18–36% of median size). Sales per sq ft does not hold constant across formats; smaller stores generally turn less per sq ft, so this rate likely overstates Revenue_j.

## 5. Crossa, Cooperman, James, Ma & Baquero 2023 — *Data in Brief*

[Paper](https://pmc.ncbi.nlm.nih.gov/articles/PMC10293947/) · fetched (after a 301 redirect) · [data](https://github.com/nychealth/food-pricing-survey-nyc-2019/) · DOI 10.5281/zenodo.7896745

**The 10-item basket:** beef (1 lb, 90% lean), eggs (12 large brown), milk (½ gal 1%), navel oranges, vine tomatoes (1 lb), Russet potatoes (1 lb), bananas (1 lb), sliced whole wheat bread, strawberries (1 lb), romaine lettuce (1 head).

**163 supermarkets** across **71 of NYC's 181 neighborhoods**, priced **March–August 2019**. Mean **$22.81**, range **$16.20–$35.11**.

**Feeds:** **[input]** p_j (the 2019 basket prices, adjusted to 2026). This is the **only store-level price microdata in the entire source set**, and it is downloadable.

**Caveats:** 2019 prices (needs CPI food-at-home adjustment to 2025–26), **supermarkets only** — no bodegas, so it cannot speak to the store-type comparison.

**Checked in the dataset (2026-09-24):** 30 distinct Bronx supermarkets are included (31 survey rows; one store was recorded twice). **One is in CD2: Key Food, 1050 Westchester Ave, $21.21 in 2019**, with all 10 items found. The Bronx average is $22.12. This is now the basis for p_j (see the status table at the top).

## 6. Allcott, Diamond, Dubé, Handbury, Rahkovsky & Schnell 2019 — *QJE*

[NBER w24094](https://www.nber.org/papers/w24094) · the Oxford page was blocked, so this came from NBER

> "Exposing low-income households to the same products and prices available to high-income households reduces nutritional inequality by only **nine percent**, while the remaining **91 percent** is driven by differences in demand."

Second finding, currently unused: means-tested healthy-food subsidies could in principle eliminate nutritional inequality at roughly **15% of the annual SNAP budget**.

**Feeds:**

- **[input]** β_p_i (Lead C) — Appendix F cites Table IV of this paper for the price-sensitivity values. I have not checked that Table IV gives 0.55 / 0.30 / 0.15; Chris should confirm.
- **[context]** the discussion and limitations sections. The second finding favours demand-side price subsidies over store-siting, which is relevant to the FRESH vs. N.Y.C. Groceries comparison in the proposal.

## 7. Dannefer, Adjoian, Brathwaite & Walsh 2015 — *AIMS Public Health*

[Paper](https://pmc.ncbi.nlm.nih.gov/articles/PMC5690258/) · fetched · published Dec 24, 2015, data collected **Spring 2012**, **n=505**, in **West Farms and Fordham**

- **97%** shopped at supermarkets in their own neighborhood; **95%** at neighborhood bodegas; only **16%** usually shopped at supermarkets outside the neighborhood
- Frequency: supermarkets **60%** once a week or more; bodegas **65%** once a day or more
- Travel: **83%** walked to their usual supermarket, mean **9.1 min**. In-neighborhood shoppers: 94% walked, 7.3 min. Out-of-neighborhood: 43% drove, 26% bus, 23% walked, 18.6 min
- **76%** bought most fresh produce at supermarkets

**Feeds:** **[context]** β_d_i and d_ij (Lead C and S): most Bronx shoppers walk to their supermarket, in about 7–9 minutes.

**Caveat:** it measures *whether* people shop somewhere, not *what share of their spending* lands there. It is also 2012 data from two Bronx neighborhoods that are not CD2.

## 8. N.Y.C. Groceries Vision Plan (Jul 27, 2026)

In this repo at `docs/research_papers/NYC-Groceries-Vision-Plan_07-27-2026.pdf` · [program page](https://edc.nyc/program/nyc-groceries)

Peninsula store **15,000 sq ft**, opening late 2027 (p.10 — this is what contradicts the Phase 1 report's 20,000). City covers **rent and property taxes** and funds the initial buildout (p.9). NYC households spend ~**6%** of income on groceries, low-income up to **25%** (citing BLS CE). **$70M is for buildout of 5 stores** (~$14M/site), a one-time capital cost. It does **not** cover rent or property taxes; the city pays those separately, and that amount is not published.

**Feeds:** **[context]** s and B — shows the scale of city spending on the N.Y.C. Groceries program. No number from it is plugged into the model.

---

# Tier B — identified but never actually opened

These appeared only as search-result snippets. The titles, authors, journals and URLs are real and confirmed, but the **numbers attributed to them came from search summaries, not from the papers**. Each should be opened before it is cited.

| Source | What we claim it says | Risk |
|---|---|---|
| [Andreyeva, Long & Brownell 2010, AJPH](https://ajph.aphapublications.org/doi/full/10.2105/AJPH.2008.151415) | Elasticities **0.27–0.81** by category | Possible check on β_p_i. A precise range taken from a snippet; verify before citing. |
| [Dubowitz et al. 2015, Health Affairs](https://www.healthaffairs.org/doi/10.1377/hlthaff.2015.0667) | Low adoption of a new supermarket (Pittsburgh Hill District) | We assert "few made it their main store" with no figure |
| [Cummins et al. 2014](https://pubmed.ncbi.nlm.nih.gov/24493772/) | Same, Philadelphia | Same |
| [Elbel et al. 2015, Public Health Nutrition](https://www.cambridge.org/core/journals/public-health-nutrition/article/assessment-of-a-governmentsubsidized-supermarket-in-a-highneed-area-on-household-food-availability-and-childrens-dietary-intakes/C998CF42FACEDADAE59D906CE63D04B7) | Bronx subsidized supermarket → no diet change | Discussion section; verify before citing |
| [Butters, Sacks & Seo 2022, AER](https://www.aeaweb.org/articles?id=10.1257%2Faer.20201524) | Local per-unit cost shocks pass through to prices | Theory anchor for θ |
| [Weyl & Fabinger 2013, JPE](https://doi.org/10.1086/670401) | Fixed costs don't move prices | Theory anchor for θ≈0 |
| [Kaufman et al. 1997, USDA ERS](https://ers.usda.gov/sites/default/files/_laserfiche/publications/40816/32372_aer759.pdf) | Supermarkets usually cheapest | Background for α_j only, and 29 years old |

**Also snippet-only:** **$7,033 per household per year** on food at home (relevant to f̄ and M, Lead S) came from a search snippet of the BLS release, not the release itself. The snippet reads: NY-area households spent $7,033 (60.0%) of their food dollars on food at home and $4,679 (40.0%) away from home, 2023–24, New York–Newark–Jersey City NY-NJ-PA. Plausible and probably right, but not verified until someone loads [the page](https://www.bls.gov/regions/northeast/news-release/consumerexpenditures_newyork.htm).

---

# Tier C — identified but not retrieved

- **[2022 Economic Census](https://www.census.gov/data/tables/2022/econ/economic-census/naics-sector-44-45.html)**, NAICS 445110 / 445131, Bronx County — would give a Bronx sales rate for Revenue_j. An API query was attempted and returned nothing; needs an API key or a manual pull from data.census.gov
- **[BLS CE geographic tables](https://www.bls.gov/cex/tables/geographic/mean.htm#msa)** and **[CE tables](https://www.bls.gov/cex/tables.htm)** (food spending by income, for f̄) — both return HTTP 403 to scripts, browser download only. **Update 2026-09-24:** Samuel has since added the CE income and income-quintile tables for 2020–2024 to `data/bls/`.
- **Rent, $20–35/sq ft/yr** (Rent_j, Lead S) — the spec gives no citation. Samuel is working on rent and square footage.

