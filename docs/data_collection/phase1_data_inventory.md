# Phase 1: Data Inventory — Bronx CD2 (Lead = S)

**Study area:** Bronx Community District 2 (BoroCD = 202; Hunts Point / Longwood)  
**Years of interest:** 2020–2025  
**Source of requirements:** Appendix F in `LEVEL_1_NYC_Grocery_Subsidy_Model_Specification_v3_drive.docx`  
**Scope rule:** Collect only rows with Lead **S**. For **R+S** (`Q_j`), collect ACS B11001 × BLS CES spending inputs only (no ReferenceUSA).  
**Deferred to Phase 3:** `Tax_j` (NYCDB / DOF), `Rent_j` (ACRIS).

---

## Summary of Lead = S / R+S items

| Symbol | Term | Lead | Public? | Phase 2 automated? |
|--------|------|------|---------|--------------------|
| `d_ij` | Distance inputs (store coords + tract centroids) | S | Yes | Yes (coords/centroids; matrix later) |
| `n_i` | Households by income group | S | Yes | Yes (Census API) |
| `N_HH` | Total CD2 households | S | Yes | Yes (Census API) |
| `Q_j` | Annual volume (cross-check only) | R+S | Partial | Yes (spending side only) |
| `M` | Total CD2 grocery market ($) | S | Yes | Yes (ACS × CES) |
| `f̄` | Avg weekly food-at-home spend | S | Yes | Yes (BLS CES) |
| `Tax_j` | Annual property/business tax | S | Yes (complex) | **No — Phase 3** |
| `Rent_j` | Annual rent | S | Yes (complex) | **No — Phase 3** |
| `B` | Program budget constraint | S | Partial | Research only (no download) |

**Additional store inventories (user request, all three):** NYS Ag & Markets, USDA SNAP, NYC Open Data food/retail establishments.

---

## 1. Geography (supports `d_ij`, tract filters)

### 1.1 NYC Community Districts

| Field | Detail |
|-------|--------|
| **What** | Polygon for BoroCD = 202 (Bronx CD2) |
| **Source** | NYC Department of City Planning — Bytes of the Big Apple |
| **Access** | Public download (shapefile / GeoJSON) |
| **Auth** | None |
| **Working links** | Portal: https://www.nyc.gov/site/planning/data-maps/open-data.page · Community Districts (NYC Open Data): https://data.cityofnewyork.us/City-Government/Community-Districts/5crt-au7u · GeoJSON API: https://data.cityofnewyork.us/resource/5crt-au7u.geojson |
| **Phase 2** | Download and filter `boro_cd` / `BoroCD` == 202 |

### 1.2 Census tracts + centroids

| Field | Detail |
|-------|--------|
| **What** | Tract polygons intersecting CD2; centroid lon/lat |
| **Source** | U.S. Census Bureau TIGER/Line or cartographic boundary files; ACS geography |
| **Access** | Public |
| **Auth** | None for TIGER downloads |
| **Working links** | TIGER tracts (example pattern): https://www2.census.gov/geo/tiger/TIGER2024/TRACT/ · Census geocoder / geography docs: https://www.census.gov/programs-surveys/geography.html · NYC Planning Census Tracts (alternate): https://data.cityofnewyork.us/City-Government/2020-Census-Tracts-Tabulation-Water-Included-/63ge-mke6 |
| **Phase 2** | Spatial intersect with CD2; write centroids CSV/GeoJSON |

---

## 2. Households and income groups (`n_i`, `N_HH`)

### 2.1 ACS Table B19001 — household income (for `n_i`)

| Field | Detail |
|-------|--------|
| **What** | Counts of households by income bracket; aggregate to Low (&lt;$25k), Mid ($25–50k), High (&gt;$50k) |
| **Source** | U.S. Census Bureau ACS 5-Year Estimates |
| **Access** | Public via **Census Reporter API** (no key) or Census API with free `CENSUS_API_KEY` |
| **Auth** | Census API requires a key as of 2025+; Census Reporter needs a project-specific User-Agent |
| **Geography** | State 36, County 005 (Bronx), tract level → filter to CD2 tracts |
| **Working links** | Census Reporter API: https://api.censusreporter.org/ · Example: https://api.censusreporter.org/1.0/data/show/acs2024_5yr?table_ids=B19001&geo_ids=140%7C05000US36005 · Census API: https://api.census.gov/data.html · data.census.gov B19001: https://data.census.gov/table/ACSDT5Y2023.B19001 |
| **2020–2025 note** | ACS 2024 5-year covers years **2020–2024**. Separate end-year vintages 2020–2023 require `CENSUS_API_KEY`. Calendar 2025 ACS 5-year not yet available. |

### 2.2 ACS Table B11001 — household type / total households (for `N_HH`)

| Field | Detail |
|-------|--------|
| **What** | Total households per tract (`B11001_001E`) |
| **Source** | ACS 5-Year |
| **Access** | Same Census API |
| **Working links** | https://data.census.gov/table/ACSDT5Y2023.B11001 · API base: https://api.census.gov/data/{year}/acs/acs5 |
| **Phase 2** | Yes |

---

## 3. Spending and market size (`M`, `f̄`, `Q_j` cross-check)

### 3.1 BLS Consumer Expenditure Survey (CES) — Table 4700 / food-at-home

| Field | Detail |
|-------|--------|
| **What** | Average food-at-home spending by income quintile / group (`f̄`); combine with `N_HH` for `M` |
| **Source** | U.S. Bureau of Labor Statistics |
| **Access** | Public tables / downloads |
| **Auth** | None |
| **Working links** | CES home: https://www.bls.gov/cex/ · Tables (XLSX): https://www.bls.gov/cex/tables.htm · Income tables (recent): https://www.bls.gov/cex/tables/calendar-year/mean/cu-income-before-taxes-2023.xlsx (pattern varies by year; Phase 2 resolves current URLs) · Series / API: https://www.bls.gov/developers/ |
| **Caveat** | National or MSA-level CES may be used if NYC-metro food-at-home by income is not published at the needed grain; document which geography is used. |
| **Phase 2** | Download available CES income × food-at-home tables for years overlapping 2020–2025 |

### 3.2 `Q_j` (R+S) — spending-side only

| Field | Detail |
|-------|--------|
| **What** | Cross-check volume: conceptually `Q_j ≈ S_j · M / p_j` (market-share path). Phase 2 delivers `M` and `f̄` / income spending, not store-level ReferenceUSA revenue. |
| **Skipped** | ReferenceUSA establishment revenue (private / library) |
| **Working links** | Same ACS + BLS links above |

---

## 4. Store inventories (three sources)

### 4.1 NYS Agriculture & Markets — Retail Food Stores

| Field | Detail |
|-------|--------|
| **What** | Licensed retail food stores (name, address, license, square footage when present, coords if present) |
| **Source** | NYS Department of Agriculture and Markets via Open NY |
| **Access** | **Public** Socrata API / CSV |
| **Auth** | None (app token optional) |
| **Working links** | Dataset: https://data.ny.gov/Economic-Development/Retail-Food-Stores/9a8c-vfzj · JSON: https://data.ny.gov/resource/9a8c-vfzj.json · CSV: https://data.ny.gov/resource/9a8c-vfzj.csv |
| **Phase 2** | Filter to Bronx / CD2; retain coordinates or geocode flags |

### 4.2 USDA SNAP Retailer Locator

| Field | Detail |
|-------|--------|
| **What** | SNAP-authorized retailers with name, type, address, lat/lon |
| **Source** | USDA Food and Nutrition Service |
| **Access** | **Public** CSV / ZIP download |
| **Auth** | None |
| **Working links** | Locator overview: https://www.fns.usda.gov/snap/retailer-locator · Retailer data: https://www.fns.usda.gov/snap/retailer/data · Historical data: https://www.fns.usda.gov/snap/retailer-locator/data · Alternate historical ZIP page: https://www.fns.usda.gov/snap/retailer/historicaldata |
| **Phase 2** | Download CSV/ZIP; filter New York + CD2 by coordinates |

### 4.3 NYC Open Data — food / retail establishments

| Field | Detail |
|-------|--------|
| **What** | NYC food establishments with addresses and coordinates (model doc cites DOHMH) |
| **Primary dataset chosen** | **DOHMH New York City Restaurant Inspection Results** (`43nn-pn8j`) — includes grocery / deli-grocery cuisine types; dedupe by CAMIS |
| **Access** | **Public** Socrata |
| **Auth** | None (app token optional) |
| **Working links** | Dataset: https://data.cityofnewyork.us/Health/DOHMH-New-York-City-Restaurant-Inspection-Results/43nn-pn8j · JSON: https://data.cityofnewyork.us/resource/43nn-pn8j.json |
| **Supplemental (not a store list)** | FRESH zoning: https://data.cityofnewyork.us/City-Government/FRESH-Food-Stores-Zoning-Boundaries/cgn7-aehz |
| **Phase 2** | Filter Bronx, grocery-like cuisine / keywords, clip to CD2, latest inspection per CAMIS |

---

## 5. Budget constraint `B` (research — not a downloadable dataset)

No published **Bronx CD2–only annual operating subsidy** amount was found for use as model parameter `B`. Public materials describe **capital** funding for the citywide N.Y.C. Groceries program and a Hunts Point (Peninsula) site.

| Finding | Detail | Working link |
|---------|--------|--------------|
| Citywide capital | **$70 million** capital allocated to develop **five** municipal grocery stores (one per borough) | https://edc.nyc/program/nyc-groceries |
| Bronx / CD2 site | **The Peninsula** (former Spofford site), Hunts Point; ~**20,000 sq ft**; anticipated open **2027** | https://www.nyc.gov/mayors-office/news/2026/05/mayor-mamdani-announces-the-peninsula-in-the-bronx-as-the-second |
| Same announcement (local coverage) | Confirms Peninsula site and $70M capital framing | https://www.bxtimes.com/mamdani-city-owned-grocery-store-hunts-point-2027/ |
| Operating “Affordability Payments” | RFP Q&A: payments sized for ~**30% Core Basket** discount; **annual limit TBD**; funding **separate from capital** and subject to **additional budget approvals** | https://edc.nyc/sites/default/files/2026-08/26.08.14_Round%201%20Q%26A%20vF.pdf |
| La Marqueta capital (context) | Program page cites **$30M** for ground-up construction at La Marqueta (East Harlem) — not CD2 | https://edc.nyc/program/nyc-groceries |

**Implication for the model:** Treat `B` as a **policy scenario parameter**. Sensible documented anchors: (a) share of $70M capital across five stores ≈ **$14M capital/site** (not annual operating); (b) leave annual Affordability Payment / operating `B` as **unknown pending EDC negotiation**. Do not invent a CD2 operating budget.

---

## 6. Explicitly out of Phase 2

| Symbol / source | Why |
|-----------------|-----|
| ReferenceUSA | Private / library; excluded for `Q_j` per Lead R+S rule |
| `Tax_j` / NYCDB | Public but needs BBL matching — **Phase 3** |
| `Rent_j` / ACRIS | Public but lease matching is heavy — **Phase 3** |
| Lead **R** / **C** parameters | Literature or other leads (e.g. SNAP-only `J` as R is superseded by collecting all three store lists) |

### Phase 3 backlog (from this inventory)

1. Match Phase 2 store addresses to BBLs.  
2. Pull `Tax_j` from NYCDB / NYC DOF: https://nycdb.info/ · DOF open data as available.  
3. Pull `Rent_j` from ACRIS: https://a836-acris.nyc.gov/ · document lease availability gaps.

---

## 7. Phase 2 implementation checklist

- [x] CD2 boundary + tract centroids → `data/geography/`
- [x] ACS B11001 & B19001 (ACS 2024 5-year via Census Reporter) → `data/acs/`
- [x] BLS CES food-at-home published series + `M` estimates → `data/bls/`
- [x] Ag & Markets stores in CD2 → `data/stores/`
- [x] SNAP retailers in CD2 → `data/stores/`
- [x] NYC DOHMH grocery-like establishments in CD2 → `data/stores/`
- [x] Phase 2 issues + citations report → `docs/data_collection/phase2_download_report.md`
