# Source List — annotated

**Project:** Policy Levers for Grocery Access in Bronx Community District 2 (94-867)
**Compiled by:** Rahul Tejannavar · **Date:** 2026-09-21
**Companion docs:** [SIMPLIFIED_PLAN_AND_SOURCES.md](SIMPLIFIED_PLAN_AND_SOURCES.md) · [ISSUES_AND_GAPS.md](ISSUES_AND_GAPS.md)

Every source behind the simplified model, what it actually contains, and what it feeds. Sources are grouped by how far verification actually got, because that determines what we can safely cite in Appendix F.

- **Tier A** — the document was opened and read; figures below are quoted from the source itself.
- **Tier B** — cited in the plan, but only ever seen as a search-result snippet. Titles and URLs are confirmed real; the numbers are not yet verified in situ.
- **Tier C** — identified but not retrieved at all.

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

**Feeds:** price parameters, and the central argument for simplifying — the brief states plainly that "the cost of food in supermarkets and bodegas was similar."

**Two precision problems to fix before this goes into Appendix F:**

- The **$37.40–$43.00 is a range across ZIP codes**, not a supermarket-vs-bodega split. The plan's table row reads "Basket price **by store type** … $37.40–$43.00," which conflates two separate findings. The store-type claim is qualitative in the source, with no numbers attached.
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

**Cost:** **$29.2M total through FY2023**, of which $25.3M (87%) is property tax. Peak **$4.0M in FY2021**; recent years $3–4M/yr. The $110–150K per store per year figure used in the plan is **our own arithmetic** ($3–4M ÷ 27), not a number the Comptroller prints — label it as derived.

**Eligibility thresholds:** min 6,000 sq ft of general grocery, ≥50% of selling area for general food, ≥30% perishables, 500 sq ft fresh meat/produce.

**Geography:** clusters in Central Brooklyn, Northern Manhattan and the Bronx; 23 of 59 community districts eligible for zoning benefits.

**Labor findings currently unused:** 1,869 FTE jobs at FRESH stores in FY2023 (63% at unionized ShopRite/Food Bazaar, 13% Western Beef non-union, 24% mixed/unknown). NYC grocery floor workers' median wage **$15.25/hr**, supervisors **$22.73/hr**. Only **46%** of full-time grocery workers get employer health insurance vs. 74% citywide. This is a whole equity dimension sitting unused — and it is the report's actual thesis, since the title is "Good Jobs."

**Feeds:** s, C_A, store-format eligibility, and the θ≈0 argument.

## 3. NYCEDC — N.Y.C. Groceries RFP, Round 1 Q&A #1 (Aug 14, 2026)

[PDF](https://edc.nyc/sites/default/files/2026-08/26.08.14_Round%201%20Q%26A%20vF.pdf) · WebFetch returned raw binary; the downloaded PDF was read directly

Sections: Core Basket Items and Pricing, Labor, Proposal Requirements, Site Selection, Store Operations, supplier sourcing. Authored by Leyla Arcasoy, created Aug 13, 2026.

- **Q1** — the 30% discount on the core basket, with an **Affordability Payment** sized to offset it. Core items often carry markups below 30%, so they would be sold below cost. This is the single most important source in the set: it establishes **θ = 1 by contract**, which is what makes the accounting model legitimate.
- **Q5** — an annual cap agreed with the operator, funded separately from capital / rent / tax relief, requiring budget approval. The cap itself is not published → budget B stays a scenario.
- **Q21** — La Marqueta area foot traffic ~**4,300/week**.
- **Q25, Q37** — operator earns a "modest margin" (unquantified; we use 1–2% of sales).

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

**Feeds:** R = sales/sq ft × sq ft, and π₀.

**Caveat for the limitations section:** these are national medians for a **42,272 sq ft** store, applied to a **15,000 sq ft** Hunts Point store — under 36% of median size. Sales per sq ft does not hold constant across formats; smaller stores generally turn less per sq ft. FMI also gives no gross margin, which is why GM remains open pending the Kroger / Albertsons 10-Ks.

## 5. Crossa, Cooperman, James, Ma & Baquero 2023 — *Data in Brief*

[Paper](https://pmc.ncbi.nlm.nih.gov/articles/PMC10293947/) · fetched (after a 301 redirect) · [data](https://github.com/nychealth/food-pricing-survey-nyc-2019/) · DOI 10.5281/zenodo.7896745

**The 10-item basket:** beef (1 lb, 90% lean), eggs (12 large brown), milk (½ gal 1%), navel oranges, vine tomatoes (1 lb), Russet potatoes (1 lb), bananas (1 lb), sliced whole wheat bread, strawberries (1 lb), romaine lettuce (1 head).

**163 supermarkets** across **71 of NYC's 181 neighborhoods**, priced **March–August 2019**. Mean **$22.81**, range **$16.20–$35.11**.

**Feeds:** store-level price dispersion. This is the **only store-level price microdata in the entire source set**, and it is downloadable. Worth prioritising: pulling it and filtering to Bronx ZIPs would let us say something concrete about CD2 instead of borrowing a South Bronx average.

**Caveats:** 2019 prices (needs CPI food-at-home adjustment to 2025–26), **supermarkets only** — no bodegas, so it cannot speak to the store-type comparison. The paper does not state whether Bronx or Hunts Point stores are included; that has to be checked in the dataset itself.

## 6. Allcott, Diamond, Dubé, Handbury, Rahkovsky & Schnell 2019 — *QJE*

[NBER w24094](https://www.nber.org/papers/w24094) · the Oxford page was blocked, so this came from NBER

> "Exposing low-income households to the same products and prices available to high-income households reduces nutritional inequality by only **nine percent**, while the remaining **91 percent** is driven by differences in demand."

Second finding, currently unused: means-tested healthy-food subsidies could in principle eliminate nutritional inequality at roughly **15% of the annual SNAP budget**.

**Feeds:** the limitations section. Note that the second finding cuts in our favour — it favours demand-side price subsidies over store-siting, which is exactly the N.Y.C. Groceries design and exactly not FRESH.

## 7. Dannefer, Adjoian, Brathwaite & Walsh 2015 — *AIMS Public Health*

[Paper](https://pmc.ncbi.nlm.nih.gov/articles/PMC5690258/) · fetched · published Dec 24, 2015, data collected **Spring 2012**, **n=505**, in **West Farms and Fordham**

- **97%** shopped at supermarkets in their own neighborhood; **95%** at neighborhood bodegas; only **16%** usually shopped at supermarkets outside the neighborhood
- Frequency: supermarkets **60%** once a week or more; bodegas **65%** once a day or more
- Travel: **83%** walked to their usual supermarket, mean **9.1 min**. In-neighborhood shoppers: 94% walked, 7.3 min. Out-of-neighborhood: 43% drove, 26% bus, 23% walked, 18.6 min
- **76%** bought most fresh produce at supermarkets

**Feeds:** the c_i capture-share range.

**Caveat:** it measures *whether* people shop somewhere, not *what share of their dollars* lands there. c_i is a dollar share, so this is an indirect anchor at best. It is also 2012 data from two Bronx neighborhoods that are not CD2.

## 8. N.Y.C. Groceries Vision Plan (Jul 27, 2026)

In this repo at `docs/NYC-Groceries-Vision-Plan_07-27-2026.pdf` · [program page](https://edc.nyc/program/nyc-groceries)

Peninsula store **15,000 sq ft**, opening late 2027 (p.10 — this is what contradicts the Phase 1 report's 20,000). City covers **rent and property taxes** and funds the initial buildout (p.9). NYC households spend ~**6%** of income on groceries, low-income up to **25%** (citing BLS CE). **$70M capital for 5 stores**, ~$14M/site — capital, not annual.

---

# Tier B — cited in the plan but never actually opened

These appeared only as search-result snippets. The titles, authors, journals and URLs are real and confirmed, but the **numbers attributed to them came from search summaries, not from the papers**. Each should be opened before Appendix F is finalised.

| Source | What we claim it says | Risk |
|---|---|---|
| [Andreyeva, Long & Brownell 2010, AJPH](https://ajph.aphapublications.org/doi/full/10.2105/AJPH.2008.151415) | Elasticities **0.27–0.81** by category | We quote a precise range from a snippet. Highest priority to verify — the only place we cite specific numbers never seen in situ. |
| [Dubowitz et al. 2015, Health Affairs](https://www.healthaffairs.org/doi/10.1377/hlthaff.2015.0667) | Low adoption of a new supermarket (Pittsburgh Hill District) | We assert "few made it their main store" with no figure |
| [Cummins et al. 2014](https://pubmed.ncbi.nlm.nih.gov/24493772/) | Same, Philadelphia | Same |
| [Elbel et al. 2015, Public Health Nutrition](https://www.cambridge.org/core/journals/public-health-nutrition/article/assessment-of-a-governmentsubsidized-supermarket-in-a-highneed-area-on-household-food-availability-and-childrens-dietary-intakes/C998CF42FACEDADAE59D906CE63D04B7) | Bronx subsidized supermarket → no diet change | A load-bearing claim for the whole argument |
| [Butters, Sacks & Seo 2022, AER](https://www.aeaweb.org/articles?id=10.1257%2Faer.20201524) | Local per-unit cost shocks pass through to prices | Theory anchor for θ |
| [Weyl & Fabinger 2013, JPE](https://doi.org/10.1086/670401) | Fixed costs don't move prices | Theory anchor for θ≈0 |
| [Kaufman et al. 1997, USDA ERS](https://ers.usda.gov/sites/default/files/_laserfiche/publications/40816/32372_aer759.pdf) | Supermarkets usually cheapest | Background only, and 29 years old |

**Also mis-statused in the plan:** **F = $7,033/HH/yr** is marked ✅, but it came from a search snippet of the BLS release, not the release itself. The snippet reads: NY-area households spent $7,033 (60.0%) of their food dollars on food at home and $4,679 (40.0%) away from home, 2023–24, New York–Newark–Jersey City NY-NJ-PA. Plausible and probably right, but it should be downgraded until someone loads [the page](https://www.bls.gov/regions/northeast/news-release/consumerexpenditures_newyork.htm).

---

# Tier C — identified but not retrieved

- **[2022 Economic Census](https://www.census.gov/data/tables/2022/econ/economic-census/naics-sector-44-45.html)**, NAICS 445110 / 445131, Bronx County — an API query was attempted and returned nothing; needs an API key or a manual pull from data.census.gov
- **[BLS CE geographic tables](https://www.bls.gov/cex/tables/geographic/mean.htm#msa)** (F_i by income quintile) and **[CE tables](https://www.bls.gov/cex/tables.htm)** (κ) — both return HTTP 403 to scripts, browser download only
- **Rent, $20–35/sq ft/yr** — still unsourced. Inherited from the v3 spec with no citation attached. Nothing found so far supports it.
- **Kroger / Albertsons 10-Ks** for gross margin — the ~22% figure has never been confirmed in a filing

---

# Corrections to make in SIMPLIFIED_PLAN_AND_SOURCES.md

1. The price row conflates a ZIP-code range with a store-type comparison — split them.
2. F = $7,033 is marked verified but was never confirmed at source.
3. $110–150K per FRESH store per year is our arithmetic, not a quoted figure — mark it derived.
