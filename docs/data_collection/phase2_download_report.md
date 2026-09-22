# Phase 2: Download Report — Bronx CD2 (Lead = S)

**Last updated:** 2026-09-18  
**Study area:** Bronx Community District 2 (BoroCD = 202)  
**Scripts:** [`code/`](../../code/) · **Outputs:** [`data/`](../../data/)  
**Inventory:** [`phase1_data_inventory.md`](phase1_data_inventory.md)

---

## Executive summary

Phase 2 public data collection for Bronx CD2 is **substantially complete** for all Lead=S targets that do not require Phase 3 tax/rent matching:

| Target | Status |
|--------|--------|
| Geography (CD2 + tract centroids) | **SUCCESS** |
| ACS `n_i` / `N_HH` (B11001, B19001) | **SUCCESS** — Census API key enabled **2020–2024** end-years |
| BLS CES `M` / `f̄` (income + quintile XLSX) | **SUCCESS** — all **2020–2024** workbooks on disk and parsed |
| Stores: Ag & Markets, SNAP, DOHMH | **SUCCESS** (three CD2 extracts with coordinates) |
| Budget `B` | **RESEARCH ONLY** — no CD2-only annual operating figure published |
| ACS calendar **2025** | **Not released** yet (expected) |
| `Tax_j` / `Rent_j` | Moved to [Phase 3](phase3_tax_rent_report.md) |

Automated `api.census.gov` pulls work with `CENSUS_API_KEY` in `.env`. Automated bls.gov XLSX downloads return **HTTP 403** from this environment; files were obtained via browser and saved under `data/bls/`, then parsed by [`code/parse_bls_ces_xlsx.py`](../../code/parse_bls_ces_xlsx.py).

---

## Success checklist (Phase 2 targets)

- [x] CD2 boundary + **16** census tract centroids  
- [x] ACS B11001 / B19001 for CD2 tracts, years **2020–2024** (Census API)  
- [x] BLS CES Income before taxes XLSX **2020–2024**  
- [x] BLS CES Quintiles of income before taxes XLSX **2020–2024**  
- [x] Parsed food-at-home → `f̄` by income group + CD2 `M` estimates  
- [x] NYS Ag & Markets stores in CD2 (**137**) with coordinates  
- [x] USDA SNAP retailers in CD2 (**553**) with coordinates  
- [x] NYC DOHMH grocery-like establishments in CD2 (**9**) with coordinates  
- [x] Documented budget `B` research (capital / Affordability Payments TBD)  
- [ ] ACS 2025 5-year (not published)  
- [ ] `Tax_j` / `Rent_j` (Phase 3)

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
| `cd2_B11001_{2020–2024}.csv` | Total households by CD2 tract |
| `cd2_B19001_{2020–2024}.csv` | Income brackets + `n_low` / `n_mid` / `n_high` |
| `cd2_household_income_summary.csv` | CD2 aggregates by year (Census API) |
| `bronx_B11001_censusapi_*.csv`, `bronx_B19001_censusapi_*.csv` | Full Bronx County pulls |
| `acs_download_meta.json` | Provenance (`api_key_used: true`) |

**CD2 household / income aggregates (ACS 5-year end-years via Census API):**

| Year | N_HH | n_low (&lt;$25k) | n_mid ($25–50k) | n_high (&gt;$50k) | Tracts | Source |
|------|------:|------:|------:|------:|------:|--------|
| 2020 | 18,582 | 8,331 | 4,379 | 5,872 | 16 | `censusapi:2020` |
| 2021 | 19,149 | 7,822 | 4,756 | 6,571 | 16 | `censusapi:2021` |
| 2022 | 19,620 | 7,375 | 4,551 | 7,694 | 16 | `censusapi:2022` |
| 2023 | 19,721 | 7,339 | 4,656 | 7,726 | 16 | `censusapi:2023` |
| 2024 | 19,922 | 7,683 | 4,795 | 7,444 | 16 | `censusapi:2024` |

### BLS / market size (`data/bls/`)

| File | Description |
|------|-------------|
| `cu-income-before-taxes-2020.xlsx` … `2024.xlsx` | CES Income before taxes (browser download) |
| `cu-income-quintiles-before-taxes-2020.xlsx` … `2024.xlsx` | CES income quintiles (browser download) |
| `ces_food_at_home_by_income_bracket.csv` | Parsed Food at home by income bracket |
| `ces_food_at_home_by_income_quintile.csv` | Parsed Food at home by quintile |
| `ces_fbar_by_income_group_from_xlsx.csv` | Model Low/Mid/High weekly `f̄` (from 2024 brackets) |
| `cd2_market_size_M_from_xlsx.csv` | CD2 `M` by ACS year × matching CES year |
| `ces_xlsx_download_urls.txt` | Canonical download URL list |
| `ces_xlsx_parse_meta.json` | Parse status (no missing files) |

**2024 weekly food-at-home `f̄` (from Income before taxes XLSX):**

| Group | Annual | Weekly |
|-------|--------:|-------:|
| Low (&lt;$25K) | $3,737 | $71.87 |
| Mid ($25–50K) | $4,603 | $88.52 |
| High (&gt;$50K) | $7,421 | $142.71 |
| All consumer units | $6,224 | $119.69 |

**CD2 market size `M` (income-weighted preferred):**

| ACS year | CES year | N_HH | M (all-CU mean) | M (income-weighted) |
|----------|----------|------:|----------------:|--------------------:|
| 2020 | 2020 | 18,582 | $91.8M | **$80.8M** |
| 2021 | 2021 | 19,149 | $100.7M | **$91.6M** |
| 2022 | 2022 | 19,620 | $111.9M | **$101.3M** |
| 2023 | 2023 | 19,721 | $119.4M | **$106.7M** |
| 2024 | 2024 | 19,922 | $124.0M | **$106.0M** |

**2024 quintiles (Food at home, annual):** Q1 $3,843 · Q2 $4,952 · Q3 $5,820 · Q4 $7,162 · Q5 $9,336 (all-CU $6,224).

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

### 2. ACS B11001 / B19001 — SUCCESS (2020–2024)

- **Primary path (current):** U.S. Census API with `CENSUS_API_KEY` from gitignored [`.env`](../../.env) (see [`.env.example`](../../.env.example)).  
  Script: [`code/download_acs.py`](../../code/download_acs.py)  
  Docs: https://api.census.gov/data.html  
- **Also available:** Census Reporter `acs2024_5yr` (no key) as backup.  
  https://api.censusreporter.org/1.0/data/show/acs2024_5yr?table_ids=B11001,B19001&geo_ids=140%7C05000US36005
- **Year coverage:** End-years **2020–2024** downloaded and filtered to CD2. **2025** ACS 5-year not released (404).
- **Earlier issue (resolved):** Without a key, `api.census.gov` returned “Missing Key”; that blocked multi-year pulls until the key was added.

### 3. BLS CES (`M`, `f̄`, `Q_j` spending side) — SUCCESS

- **Tables used (Calendar year → Mean → item share / SE series):**  
  - **Income before taxes:** `cu-income-before-taxes-{YYYY}.xlsx`  
  - **Quintiles of income before taxes:** `cu-income-quintiles-before-taxes-{YYYY}.xlsx`  
  Path pattern:  
  `https://www.bls.gov/cex/tables/calendar-year/mean-item-share-average-standard-error/`
- **2024 examples:**  
  - https://www.bls.gov/cex/tables/calendar-year/mean-item-share-average-standard-error/cu-income-before-taxes-2024.xlsx  
  - https://www.bls.gov/cex/tables/calendar-year/mean-item-share-average-standard-error/cu-income-quintiles-before-taxes-2024.xlsx  
- **Portal:** https://www.bls.gov/cex/tables.htm · https://www.bls.gov/cex/
- **Automation:** Direct HTTP from this environment still returns **403**; files were downloaded in a browser into `data/bls/` (all 10 files for 2020–2024).  
- **Parsing:** [`code/parse_bls_ces_xlsx.py`](../../code/parse_bls_ces_xlsx.py) extracts **Food at home** Mean rows → bracket / quintile CSVs and CD2 `M`.  
- **Geography caveat:** National CES consumer-unit means (not NYC-metro-specific). Acceptable for Level-1 market-size construction; document when upgrading to MSA tables if available.

### 4. NYS Ag & Markets Retail Food Stores — SUCCESS

- Dataset: https://data.ny.gov/Economic-Development/Retail-Food-Stores/9a8c-vfzj  
  API: https://data.ny.gov/resource/9a8c-vfzj.json  
- Parsed `georeference` Point coordinates; spatial clip to CD2 → **137** stores.
- Includes square footage when present (used in Phase 3 rent path B).

### 5. USDA SNAP Retailer Locator — SUCCESS

- Historical ZIP: https://www.fns.usda.gov/sites/default/files/resource-files/snap-retailer-locator-data2005-2025.zip  
- Portal: https://www.fns.usda.gov/snap/retailer-locator  
- Data pages: https://www.fns.usda.gov/snap/retailer/data · https://www.fns.usda.gov/snap/retailer/historicaldata  
- CD2 spatial filter → **553** authorized retailers (includes many store types beyond full-line grocery).

### 6. NYC Open Data DOHMH — SUCCESS (narrow coverage)

- Dataset: https://data.cityofnewyork.us/Health/DOHMH-New-York-City-Restaurant-Inspection-Results/43nn-pn8j  
  API: https://data.cityofnewyork.us/resource/43nn-pn8j.json  
- Filtered Bronx + grocery/deli/market keywords; deduped by CAMIS → CD2 → **9**.
- **Limitation:** Restaurant-inspection oriented; sparse vs Ag & Markets / SNAP. Treat as a **supplement**.

### Store-list overlap (counts only)

| List | CD2 n |
|------|------:|
| Ag & Markets | 137 |
| SNAP | 553 |
| DOHMH grocery-like | 9 |

Full fuzzy cross-list matching is deferred (Phase 3+ / model prep). Ag & Markets remains the cleanest licensed retail-food universe for CD2.

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

**Model implication:** Scenario-test `B`. Capital share ≈ $14M/site is **not** annual operating. Leave operating `B` as a policy slider until EDC publishes Affordability Payment caps.

---

## Working-link citation list

1. NYC Community Districts — https://data.cityofnewyork.us/City-Government/Community-Districts/5crt-au7u  
2. NYC Community Districts GeoJSON — https://data.cityofnewyork.us/resource/5crt-au7u.geojson  
3. NYC Planning open data portal — https://www.nyc.gov/site/planning/data-maps/open-data.page  
4. NYC 2020 Census Tracts — https://data.cityofnewyork.us/City-Government/2020-Census-Tracts-Tabulation-Water-Included-/63ge-mke6  
5. U.S. Census API — https://api.census.gov/data.html  
6. Census API key signup — https://api.census.gov/data/key_signup.html  
7. Census Reporter ACS API — https://api.censusreporter.org/  
8. data.census.gov B11001 — https://data.census.gov/table/ACSDT5Y2023.B11001  
9. data.census.gov B19001 — https://data.census.gov/table/ACSDT5Y2023.B19001  
10. BLS CES home — https://www.bls.gov/cex/  
11. BLS CES tables — https://www.bls.gov/cex/tables.htm  
12. CES Income before taxes 2024 — https://www.bls.gov/cex/tables/calendar-year/mean-item-share-average-standard-error/cu-income-before-taxes-2024.xlsx  
13. CES Quintiles of income before taxes 2024 — https://www.bls.gov/cex/tables/calendar-year/mean-item-share-average-standard-error/cu-income-quintiles-before-taxes-2024.xlsx  
14. NYS Retail Food Stores — https://data.ny.gov/Economic-Development/Retail-Food-Stores/9a8c-vfzj  
15. NYS Retail Food Stores API — https://data.ny.gov/resource/9a8c-vfzj.json  
16. USDA SNAP Retailer Locator — https://www.fns.usda.gov/snap/retailer-locator  
17. USDA SNAP retailer data — https://www.fns.usda.gov/snap/retailer/data  
18. SNAP retailer ZIP — https://www.fns.usda.gov/sites/default/files/resource-files/snap-retailer-locator-data2005-2025.zip  
19. DOHMH Restaurant Inspection Results — https://data.cityofnewyork.us/Health/DOHMH-New-York-City-Restaurant-Inspection-Results/43nn-pn8j  
20. DOHMH API — https://data.cityofnewyork.us/resource/43nn-pn8j.json  
21. NYCEDC N.Y.C. Groceries — https://edc.nyc/program/nyc-groceries  
22. Mayor’s Office Peninsula / Hunts Point announcement — https://www.nyc.gov/mayors-office/news/2026/05/mayor-mamdani-announces-the-peninsula-in-the-bronx-as-the-second  
23. Bronx Times coverage — https://www.bxtimes.com/mamdani-city-owned-grocery-store-hunts-point-2027/  
24. EDC Round 1 Q&A (Affordability Payments) — https://edc.nyc/sites/default/files/2026-08/26.08.14_Round%201%20Q%26A%20vF.pdf  

---

## How to re-run

```bash
pip install -r requirements-data.txt
# Census key in .env: CENSUS_API_KEY=...
python code/download_geography.py
python code/download_acs.py
python code/download_bls_ces_xlsx.py   # tries HTTP; skips files already in data/bls/
python code/parse_bls_ces_xlsx.py      # parse Food at home from XLSX
python code/download_stores_agmarkets.py
python code/download_stores_snap.py
python code/download_stores_nyc_opendata.py
# or: python code/run_all_downloads.py
```

---

## Remaining gaps (not Phase 2 blockers)

1. ACS **2025** 5-year release when Census publishes it.  
2. Optional NYC-metro CES tables if finer geography than US all-CU is required.  
3. Store-list crosswalk / candidate set `J` cleaning.  
4. Policy `B` when Affordability Payment caps are published.  
5. `Tax_j` / `Rent_j` — see [phase3_tax_rent_report.md](phase3_tax_rent_report.md).
