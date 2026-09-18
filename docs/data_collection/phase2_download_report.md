# Phase 2: Download Report — Bronx CD2 (Lead = S)

**Run date:** 2026-09-17 (local)  
**Study area:** Bronx Community District 2 (BoroCD = 202)  
**Scripts:** [`code/`](../../code/) · **Outputs:** [`data/`](../../data/)  
**Inventory:** [`phase1_data_inventory.md`](phase1_data_inventory.md)

---

## Executive summary

Public downloads for geography, ACS households/income, CES spending inputs, and **three** store lists completed with usable CD2 extracts. Two access friction points were documented and worked around: (1) Census API now requires a key — used Census Reporter instead; (2) bls.gov XLSX downloads return HTTP 403 here — transcribed published CES food-at-home figures with citations. `Tax_j` / `Rent_j` deferred to Phase 3. No Bronx-CD2-only annual operating budget `B` was published; capital and program citations are below.

---

## File inventory (CD2-focused)

### Geography (`data/geography/`)

| File | Description | Count |
|------|-------------|------:|
| `bronx_cd2_boundary.geojson` | CD2 polygon | 1 |
| `bronx_cd2_centroid.csv` | CD2 centroid lon/lat | 1 |
| `bronx_cd2_tracts.geojson` | Tracts with centroid inside CD2 | 16 |
| `bronx_cd2_tract_centroids.csv` / `.geojson` | Tract centroids for `d_ij` | 16 |

### ACS (`data/acs/`)

| File | Description |
|------|-------------|
| `cd2_B11001_2024.csv` | Total households by CD2 tract |
| `cd2_B19001_2024.csv` | Income brackets + `n_low` / `n_mid` / `n_high` |
| `cd2_household_income_summary.csv` | CD2 aggregates |
| `bronx_B11001_*.csv`, `bronx_B19001_*.csv` | Full Bronx County tract pulls |
| `acs_download_meta.json` | Provenance |

**CD2 aggregate (ACS 2024 5-year, covers 2020–2024):**

| Year | N_HH | n_low (&lt;$25k) | n_mid ($25–50k) | n_high (&gt;$50k) | Tracts |
|------|------:|------:|------:|------:|------:|
| 2024 | 19,922 | 7,683 | 4,795 | 7,444 | 16 |

### BLS / market size (`data/bls/`)

| File | Description |
|------|-------------|
| `ces_food_at_home_annual_published.csv` | US mean food-at-home 2019–2024 |
| `ces_fbar_by_income_group_approx.csv` | Approx weekly `f̄` by income group |
| `cd2_market_size_M_estimates.csv` | Two `M` estimates for CD2 |
| `bls_download_meta.json` | XLSX 403 failures + notes |

**Illustrative `M`:** ≈ **$124.0M**/yr using `N_HH × $6,224` (2024 CES all-CU food-at-home); ≈ **$109.1M** using income-group weekly ranges × 52.

### Stores (`data/stores/`)

| Source | CD2 file | CD2 rows | Coords? |
|--------|----------|--------:|---------|
| NYS Ag & Markets | `agmarkets_bronx_cd2.csv` (+ GeoJSON) | **137** | Yes |
| USDA SNAP | `snap_bronx_cd2.csv` (+ GeoJSON) | **553** | Yes |
| NYC DOHMH (grocery-like) | `nyc_dohmh_bronx_cd2_grocery.csv` (+ GeoJSON) | **9** | Yes |

---

## Per-source results and issues

### 1. Community Districts + tracts — SUCCESS

- **CD boundary:** NYC Open Data Community Districts `5crt-au7u` (older ID `yfnk-k7r4` 404’d).  
  https://data.cityofnewyork.us/City-Government/Community-Districts/5crt-au7u  
  https://data.cityofnewyork.us/resource/5crt-au7u.geojson
- **Tracts:** NYC 2020 Census Tracts `63ge-mke6`, Bronx paginated, centroid-within CD2 → **16 tracts**.  
  https://data.cityofnewyork.us/City-Government/2020-Census-Tracts-Tabulation-Water-Included-/63ge-mke6  
- **Issue fixed:** Initial `gpd.read_file` without `$where`/`$limit` returned a truncated citywide page and under-counted tracts.

### 2. ACS B11001 / B19001 — SUCCESS (partial years)

- **Worked:** Census Reporter `acs2024_5yr` for all Bronx tracts, filtered to CD2 GEOIDs.  
  https://api.censusreporter.org/1.0/data/show/acs2024_5yr?table_ids=B11001,B19001&geo_ids=140%7C05000US36005
- **Issue:** `api.census.gov` returns HTML “Missing Key” without `CENSUS_API_KEY` — cannot automate separate end-years 2020–2023/2025 without a key.
- **Year coverage:** ACS 2024 5-year spans **2020–2024**. No ACS 2025 5-year release yet.
- **Action if multi-year needed:** Set `CENSUS_API_KEY` and re-run `code/download_acs.py`.

### 3. BLS CES (`M`, `f̄`, `Q_j` spending side) — PARTIAL

- **Failed:** Direct downloads of CES income XLSX from bls.gov → **HTTP 403** (also via curl).  
  Example blocked URL: https://www.bls.gov/cex/tables/calendar-year/mean/cu-income-before-taxes-2023.xlsx  
  Portal: https://www.bls.gov/cex/tables.htm · https://www.bls.gov/cex/
- **Workaround:** Transcribed published all-CU **food-at-home** annual means from BLS reports/news releases into `ces_food_at_home_annual_published.csv`.
- **Caveat:** US all-CU means, not NYC-metro or full income-quintile Table 4700 detail. Income-group weekly rates are approximate pending XLSX access (manual download in a browser should work).

### 4. NYS Ag & Markets Retail Food Stores — SUCCESS

- Dataset: https://data.ny.gov/Economic-Development/Retail-Food-Stores/9a8c-vfzj  
  API: https://data.ny.gov/resource/9a8c-vfzj.json  
- Parsed `georeference` Point coordinates; spatial clip to CD2 → **137** stores.
- Includes square footage when present (useful later for store-type / α_j).

### 5. USDA SNAP Retailer Locator — SUCCESS

- Historical ZIP: https://www.fns.usda.gov/sites/default/files/resource-files/snap-retailer-locator-data2005-2025.zip  
- Portal: https://www.fns.usda.gov/snap/retailer-locator  
- Data pages: https://www.fns.usda.gov/snap/retailer/data · https://www.fns.usda.gov/snap/retailer/historicaldata  
- CD2 spatial filter → **553** authorized retailers (includes many store types beyond full-line grocery).
- **Note:** Candidate hardcoded ZIP URLs 404’d first; scraper found the working resource-files link.

### 6. NYC Open Data DOHMH — SUCCESS (narrow)

- Dataset: https://data.cityofnewyork.us/Health/DOHMH-New-York-City-Restaurant-Inspection-Results/43nn-pn8j  
  API: https://data.cityofnewyork.us/resource/43nn-pn8j.json  
- Filtered Bronx + grocery/deli/market keywords; deduped by CAMIS → 138 Bronx; CD2 → **9**.
- **Issue:** DOHMH is restaurant-inspection oriented; many Ag & Markets / SNAP grocery retailers are absent. Treat as a **supplement**, not the primary inventory.

### Store-list overlap (counts only)

| List | CD2 n |
|------|------:|
| Ag & Markets | 137 |
| SNAP | 553 |
| DOHMH grocery-like | 9 |

Full fuzzy name/address matching across lists is **not** done in Phase 2 (deferred). Expect SNAP ⊃ many convenience retailers; Ag & Markets is the cleaner licensed retail-food universe for CD2; DOHMH is sparse.

---

## Budget parameter `B` (research)

No published **Bronx CD2–specific annual operating subsidy** was found for direct use as model `B`.

| Finding | Value | Link |
|---------|-------|------|
| Citywide capital for 5 N.Y.C. Groceries stores | **$70M** | https://edc.nyc/program/nyc-groceries |
| Bronx site | The Peninsula, Hunts Point; ~20,000 sq ft; open ~**2027** | https://www.nyc.gov/mayors-office/news/2026/05/mayor-mamdani-announces-the-peninsula-in-the-bronx-as-the-second |
| Local coverage (same announcement) | Confirms site + $70M framing | https://www.bxtimes.com/mamdani-city-owned-grocery-store-hunts-point-2027/ |
| Operating Affordability Payments | Sized for ~30% Core Basket discount; **annual amount TBD**; separate from capital; needs further budget approval | https://edc.nyc/sites/default/files/2026-08/26.08.14_Round%201%20Q%26A%20vF.pdf |
| La Marqueta capital (not CD2) | **$30M** construction (context) | https://edc.nyc/program/nyc-groceries |

**Model implication:** Scenario-test `B` (e.g. share of capital ≈ $14M/site is **not** annual operating). Leave operating `B` as a policy slider until EDC publishes Affordability Payment caps.

---

## Working-link citation list (all Phase 2 sources)

1. NYC Community Districts — https://data.cityofnewyork.us/City-Government/Community-Districts/5crt-au7u  
2. NYC Community Districts GeoJSON — https://data.cityofnewyork.us/resource/5crt-au7u.geojson  
3. NYC Planning open data portal — https://www.nyc.gov/site/planning/data-maps/open-data.page  
4. NYC 2020 Census Tracts — https://data.cityofnewyork.us/City-Government/2020-Census-Tracts-Tabulation-Water-Included-/63ge-mke6  
5. Census Reporter ACS API — https://api.censusreporter.org/  
6. ACS 2024 5-year Bronx tracts (B11001, B19001) — https://api.censusreporter.org/1.0/data/show/acs2024_5yr?table_ids=B11001,B19001&geo_ids=140%7C05000US36005  
7. U.S. Census API docs — https://api.census.gov/data.html  
8. data.census.gov B11001 — https://data.census.gov/table/ACSDT5Y2023.B11001  
9. data.census.gov B19001 — https://data.census.gov/table/ACSDT5Y2023.B19001  
10. BLS CES home — https://www.bls.gov/cex/  
11. BLS CES tables — https://www.bls.gov/cex/tables.htm  
12. BLS Consumer Expenditures in 2023 report — https://www.bls.gov/opub/reports/consumer-expenditures/2023/  
13. BLS CE 2023 news release — https://www.bls.gov/news.release/cesan.nr0.htm  
14. BLS CE 2024 news release — https://www.bls.gov/news.release/cesan.htm  
15. NYS Retail Food Stores — https://data.ny.gov/Economic-Development/Retail-Food-Stores/9a8c-vfzj  
16. NYS Retail Food Stores API — https://data.ny.gov/resource/9a8c-vfzj.json  
17. USDA SNAP Retailer Locator — https://www.fns.usda.gov/snap/retailer-locator  
18. USDA SNAP retailer data — https://www.fns.usda.gov/snap/retailer/data  
19. USDA SNAP historical data page — https://www.fns.usda.gov/snap/retailer/historicaldata  
20. SNAP retailer ZIP (downloaded) — https://www.fns.usda.gov/sites/default/files/resource-files/snap-retailer-locator-data2005-2025.zip  
21. DOHMH Restaurant Inspection Results — https://data.cityofnewyork.us/Health/DOHMH-New-York-City-Restaurant-Inspection-Results/43nn-pn8j  
22. DOHMH API — https://data.cityofnewyork.us/resource/43nn-pn8j.json  
23. NYCEDC N.Y.C. Groceries — https://edc.nyc/program/nyc-groceries  
24. Mayor’s Office Peninsula / Hunts Point announcement — https://www.nyc.gov/mayors-office/news/2026/05/mayor-mamdani-announces-the-peninsula-in-the-bronx-as-the-second  
25. Bronx Times coverage — https://www.bxtimes.com/mamdani-city-owned-grocery-store-hunts-point-2027/  
26. EDC Round 1 Q&A (Affordability Payments) — https://edc.nyc/sites/default/files/2026-08/26.08.14_Round%201%20Q%26A%20vF.pdf  

---

## How to re-run

```bash
pip install -r requirements-data.txt
python code/run_all_downloads.py
# or individually:
python code/download_geography.py
python code/download_acs.py
python code/download_bls_ces.py
python code/download_stores_agmarkets.py
python code/download_stores_snap.py
python code/download_stores_nyc_opendata.py
```

Optional: `set CENSUS_API_KEY=...` before `download_acs.py` for official multi-year ACS end-years.

---

## Phase 3 backlog

1. **`Tax_j`:** Match store addresses → BBL → NYCDB / DOF tax bills (https://nycdb.info/).  
2. **`Rent_j`:** Match to ACRIS leases (https://a836-acris.nyc.gov/).  
3. Crosswalk Ag & Markets ↔ SNAP ↔ DOHMH for a cleaned candidate set `J`.  
4. Manual CES income XLSX (Table / income-before-taxes) for income-specific `f̄`.  
5. Optional multi-year ACS 2020–2023 with Census API key.  
6. Finalize policy `B` when Affordability Payment caps are published.
