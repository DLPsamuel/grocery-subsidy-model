# Bronx CD2 data collection
_Exported on 10/4/2026 at 10:39:32 EDT from Cursor (3.17.8)_

---

**User**

In the document LEVEL_1_... .docx, It explains a model i am trying to create. Your task is to go to the table in "Appendix F" and write python code (saved in code directory) to access and save data (saved in the data directory). You are to only try to access data from the rows that have "S" in the Lead column. The row that has R+S, just look at ACS B11001 x BLS CES, spending data, not Reference USA. This also includes a list of stores from NY Ag & Markets Food retailers (or whichever database is specified) for Bronx CD2 and ideally their location (coordinates) as well as the centroids of the census tracts in Bronx CD2. Documents should be saved in directory docs/data_collection

Here are your phases. The region of focus is Bronx Community District 2 for years 2020-2025. 

Phase 1: figure out what specific data set is needed, how to access it, and if it's public or private. detail all of this in a markdown document.

Phase 2: Create code for the public data that's accessible for now. Download what is possible, then create a report on any issues and save in markdown document

In this plan, go ahead and execute phase 1 and phase 2. you can ask for user input after phase 1 if necessary.

Review the referenced document LEVEL_1... .docx. What questions do you have?

---

**Cursor**

I'll review Appendix F in the LEVEL_1 document and the repo layout so I can ask focused questions before drafting the phase 1–2 plan.

Encoding tripped up the extract; I'll pull Appendix F with UTF-8 and dig into any existing data-collection notes.

Checking Phase 0 in the LEVEL_1 doc for store-source guidance and whether Ag & Markets is specified.

Reviewed Appendix F in `LEVEL_1_...v3_drive.docx`. Lead **S** (and **R+S** per your rule) maps to:

| Symbol | Data | Source in doc |
|--------|------|---------------|
| `d_ij` | Distances / store geocodes / group centroids | SNAP geocodes + ACS tract centroids |
| `n_i` | Households by income group | ACS B19001 |
| `N_HH` | Total households | ACS B11001 |
| `Q_j` (R+S) | Volume cross-check only | ACS B11001 × BLS CES (skip ReferenceUSA) |
| `M` | Total grocery market $ | ACS × BLS CES Table 4700 |
| `f̄` | Weekly food spending | BLS CES Table 4700 |
| `Tax_j` | Property/business tax | NYCDB / NYC DOF |
| `Rent_j` | Annual rent | NYC ACRIS |
| `B` | Program budget | City policy input |

You also want **NY Ag & Markets food retailers** for Bronx CD2 (with coords) and **census tract centroids**. Phase 0 in the doc still points to USDA SNAP + DOHMH for the store list, and marks `J` as Lead **R**.

Two decisions that change the Phase 1–2 plan:

**1. Store list source for Phase 2**  
Appendix F marks store inventory `J` as Lead **R** (USDA SNAP). You asked for **NY Ag & Markets Food Retailers** (public on data.ny.gov). Which should Phase 2 download and geocode for Bronx CD2?

- **A)** NY Ag & Markets only (your override)  
- **B)** Both Ag & Markets and USDA SNAP (if SNAP CSV is still publicly downloadable)  
- **C)** Ag & Markets + NYC Open Data retail/food establishments as the spatial/filter layer  

**2. Scope of Lead=S rows `Tax_j`, `Rent_j`, and `B` in Phase 2**  
- `B` is a city budget input (not a downloadable dataset) — document only, skip code?  
- `Tax_j` (NYCDB / DOF) and `Rent_j` (ACRIS) are public but need store→BBL/lease matching and are heavier — attempt automated pulls in Phase 2, or document as “public but deferred” and focus Phase 2 on ACS, BLS CES, geography, and the store list?

Once you answer those, I’ll write the Phase 1–2 plan (docs in `docs/data_collection/`, scripts in `code/`, outputs in `data/`) and execute after you approve.

---

**User**

1. Could you try all three: Ag & Markets, USDA SNAP, and NYC Open Data retail/food establishments?
2. see if you can find in the web what the city budget for NYC grocery stores is, or what they are planning to spendon the bronx CD2 store. Cite all sources in your report (that includes for all data sets, working link must be added)
3. Defer Tax_j and Rent_j for phase 3, trying to match using the information we got from stores.

---

**Cursor**

Updating the plan with your decisions and checking public sources for the three store datasets and any Bronx CD2 / 

grocery subsidy budget figures.

I have enough to lock decisions into a concrete Phase 1–2 plan.

---

**User**

Implement the plan as specified, it is attached for your reference. Do NOT edit the plan file itself.

To-do's from the plan have already been created. Do not create them again. Mark them as in_progress as you work, starting with the first one. Don't stop until you have completed all the to-dos.

---

**Cursor**

Implementing Phase 1–2 now: starting the data inventory, then setting up directories and download scripts.

Phase 1 inventory is done. Setting up dependencies and download scripts next.

Community Districts URL returned 404 — looking up the correct NYC Open Data endpoint.

Only 5 tracts came back — likely a Socrata pagination limit. Fixing the tract fetch to pull all Bronx tracts.

Geography succeeded (16 tracts). Fixing ACS API handling and BLS 403 blocks next.

Census API now requires a key, and BLS is blocking automated downloads. Switching to alternate public sources.

ACS and BLS are in place. Running all three store downloads next.

Ag & Markets has a `georeference` field — I'll parse coordinates from it and re-filter to CD2.

Store downloads succeeded. Gathering file counts and writing the Phase 2 report.

Phase 1–2 are done. Deliverables:

**Docs**
- [`docs/data_collection/phase1_data_inventory.md`](docs/data_collection/phase1_data_inventory.md) — Lead=S inventory, access methods, public/private, URLs, budget research
- [`docs/data_collection/phase2_download_report.md`](docs/data_collection/phase2_download_report.md) — download results, issues, full working-link citations

**Code** (`code/`) — modular downloaders + `run_all_downloads.py`  
**Data** under `data/geography|acs|bls|stores/`

**What landed for Bronx CD2**
| Dataset | Result |
|---------|--------|
| Geography | CD2 boundary + **16** tract centroids |
| ACS (`n_i`, `N_HH`) | ACS 2024 5-yr: **19,922** HH (7,683 / 4,795 / 7,444) |
| CES (`M`, `f̄`) | Published food-at-home series; `M` ≈ **$124M** (US all-CU) |
| Ag & Markets | **137** stores w/ coords |
| USDA SNAP | **553** retailers w/ coords |
| NYC DOHMH grocery-like | **9** (sparse vs the other two) |

**Issues worth knowing**
1. Census API now needs `CENSUS_API_KEY` — used Census Reporter for 2020–2024 coverage; set a key to pull separate end-years.
2. bls.gov XLSX returns **403** here — transcribed published CES figures; download income tables manually for finer `f̄`.
3. No CD2-only annual operating `B` published — citywide **$70M capital** / Peninsula site / Affordability Payments TBD (cited in both docs).
4. `Tax_j` / `Rent_j` remain Phase 3.

---

**User**

<timestamp>Thursday, Sep 17, 2026, 9:01 PM (UTC-4)</timestamp>
<system_notification>
The following task has finished. If you were already aware, ignore this notification and do not restate prior responses.

<task>
kind: shell
status: success
task_id: 601201
title: Run all three store download scripts
tool_call_id: call-6304df3c-8545-4d3c-b18d-c1eb12ece67e-70
fc_f3ae977b-f909-9fdc-be7e-1198fd422033_1
output_path: C:\Users\samia\.cursor\projects\c-Users-samia-Code-Projects-grocery-subsidy-analysis\terminals\601201.txt
</task>
</system_notification>
<user_query>Briefly inform the user about the task result and perform any follow-up actions (if needed). If there's no follow-ups needed, don't explicitly say that.</user_query>

---

**Cursor**

The store download job finished successfully. CD2 extracts are in `data/stores/`:

- **Ag & Markets:** 137 stores (with coordinates after georeference parsing)
- **USDA SNAP:** 553 retailers  
- **NYC DOHMH grocery-like:** 9 establishments

Full details and citations are in [`docs/data_collection/phase2_download_report.md`](docs/data_collection/phase2_download_report.md).

---

**User**

where can I paste the Census API key? (i want it in git ignore

---

**Cursor**

I'll set up a gitignored `.env` for the Census API key and wire the download scripts to read it.

Paste it in **`.env`** at the repo root:

```env
CENSUS_API_KEY=your_actual_key_here
```

That file is in [`.gitignore`](.gitignore). Use [`.env.example`](.env.example) as a template (safe to commit).

Get a free key at https://api.census.gov/data/key_signup.html — then re-run `python code/download_acs.py` for multi-year ACS pulls.

---

**User**

I added it - try it now

---

**Cursor**

Re-running the ACS download with your Census API key.

Key loaded. Fixing a console encoding issue, then re-running.

Key works. Redacting it from error logs (it appeared in a 404 URL) and confirming multi-year CD2 outputs.

Key worked for 2020–2024. Updating the script to write CD2 summaries for those years and redact the key from error messages.

Your key works. Pulled ACS 5-year for **2020–2024** via the Census API into `data/acs/` (CD2 summaries in `cd2_household_income_summary.csv`):

| Year | N_HH | Low | Mid | High |
|------|------|-----|-----|------|
| 2020 | 18,582 | 8,331 | 4,379 | 5,872 |
| 2021 | 19,149 | 7,822 | 4,756 | 6,571 |
| 2022 | 19,620 | 7,375 | 4,551 | 7,694 |
| 2023 | 19,721 | 7,339 | 4,656 | 7,726 |
| 2024 | 19,922 | 7,683 | 4,795 | 7,444 |

**2025** is not published yet (404). Error logs now redact the key.

---

**User**

<timestamp>Thursday, Sep 17, 2026, 9:36 PM (UTC-4)</timestamp>
<system_notification>
The following task has finished. If you were already aware, ignore this notification and do not restate prior responses.

<task>
kind: shell
status: success
task_id: 311972
title: Re-run ACS with CD2 multi-year summaries
tool_call_id: call-e30daa47-9a92-4cd6-a34e-2b0939d3f922-97
fc_d1c609f9-2abf-9020-ac72-e4f75cd9e117_1
output_path: C:\Users\samia\.cursor\projects\c-Users-samia-Code-Projects-grocery-subsidy-analysis\terminals\311972.txt
</task>
</system_notification>
<user_query>Briefly inform the user about the task result and perform any follow-up actions (if needed). If there's no follow-ups needed, don't explicitly say that.</user_query>

---

**Cursor**

ACS re-run finished successfully. Multi-year CD2 household/income summaries for **2020–2024** are in `data/acs/cd2_household_income_summary.csv`; **2025** is not available yet.

---

**User**

Now that you have the store data - try to find tax and rent information. Document all the different things you try in a document for "Phase 3" and save code in a phase 3 file. Any quesitons?

---

**Cursor**

Checking what store fields we have for matching, then I'll ask the critical questions.

Two decisions that change the Phase 3 plan:

**1. Which store list should we match tax/rent against?**  
Ag & Markets is the cleanest licensed retail-food list (**137** in CD2 with addresses + coords). SNAP has **553** (many convenience). Matching all three is a lot of address→BBL work.

Recommend: **Ag & Markets as primary**, keep SNAP/DOHMH for later crosswalk only. OK?

**2. For `Rent_j`, what counts as success?**  
ACRIS often has no usable lease for a given store (owner-occupied, missing docs). Appendix F also allows **sq-ft × market rate** (~$20–$35/sq-ft/yr in Hunts Point) when lease data is missing.

Should Phase 3:  
- **A)** Attempt ACRIS + document gaps only, or  
- **B)** ACRIS where possible, plus sq-ft × market-rate fallback using Ag & Markets `square_footage`?

---

**User**

1. Create 3 data sets, try to match all three. Also document success rate in the markdown file.
2. Try both A and B

---

**Cursor**

Locking those choices in and checking public NYC tax/rent/BBL access paths so the Phase 3 plan is concrete.

---

**User**

Implement the plan as specified, it is attached for your reference. Do NOT edit the plan file itself.

To-do's from the plan have already been created. Do not create them again. Mark them as in_progress as you work, starting with the first one. Don't stop until you have completed all the to-dos.

---

**Cursor**

Implementing Phase 3: starting with the tax/rent pipeline and probing the NYC API schemas.

Schemas look good. Probing BBL lookups next, then implementing the full pipeline.

Implementing the full Phase 3 pipeline now.

Fixing cache writes (Windows file lock) and reducing how often we flush to disk.

Ag & Markets finished. Fixing the logging bug and continuing with SNAP and DOHMH.

Pipeline finished. Writing the Phase 3 report and cleaning up probe scripts.

Phase 3 is done. Summary:

**Code:** [`code/phase3_tax_rent.py`](code/phase3_tax_rent.py)  
**Report:** [`docs/data_collection/phase3_tax_rent_report.md`](docs/data_collection/phase3_tax_rent_report.md)  
**Data:** `data/phase3/tax_rent_{agmarkets,snap,dohmh}_cd2.csv`

| List | BBL | Tax_j | ACRIS lease | Market rent | Any rent |
|------|-----|-------|-------------|-------------|----------|
| Ag & Markets (137) | 99.3% | 91.2% | 11.7% | **69.3%** | **71.5%** |
| SNAP (553) | 99.8% | 91.9% | 11.2% | 0% (no sq-ft) | 11.2% |
| DOHMH (9) | 100% | 77.8% | 0% | 0% | 0% |

**Takeaways:** DOF charges work well for lot-level `Tax_j`. ACRIS almost never gives usable annual rent; Ag & Markets market-rate × sq-ft is the practical `Rent_j` path. SNAP/DOHMH need sq-ft joins for path B.

Checking whether Phase 3 deliverables are already complete from the prior run.

Phase 3 is already complete from the earlier run. All todos are done.

**Deliverables**
- Code: [`code/phase3_tax_rent.py`](code/phase3_tax_rent.py)
- Report: [`docs/data_collection/phase3_tax_rent_report.md`](docs/data_collection/phase3_tax_rent_report.md)
- Datasets: `data/phase3/tax_rent_{agmarkets,snap,dohmh}_cd2.csv`

| List | BBL | Tax_j | Any rent |
|------|-----|-------|----------|
| Ag & Markets | 99.3% | 91.2% | 71.5% (mostly market-rate × sq-ft) |
| SNAP | 99.8% | 91.9% | 11.2% (ACRIS only; no sq-ft) |
| DOHMH | 100% | 77.8% | 0% |

Re-run with `python code/phase3_tax_rent.py` if you want a fresh pull (caches in `data/phase3/` speed it up).

---

**User**

<timestamp>Friday, Sep 18, 2026, 6:10 AM (UTC-4)</timestamp>
<system_notification>
The following task has finished. If you were already aware, ignore this notification and do not restate prior responses.

<task>
kind: shell
status: success
task_id: 834999
title: Probe API schemas via Python script
tool_call_id: call-665e7645-83d3-450b-ac71-b00f67b48a80-111
fc_a4491083-d100-9e8e-a541-b833227e91ec_0
output_path: C:\Users\samia\.cursor\projects\c-Users-samia-Code-Projects-grocery-subsidy-analysis\terminals\834999.txt
</task>
</system_notification>
<user_query>Briefly inform the user about the task result and perform any follow-up actions (if needed). If there's no follow-ups needed, don't explicitly say that.</user_query>

---

**Cursor**

The API probe finished successfully — GeoSearch, PLUTO, DOF charges, and ACRIS schemas all responded as expected. Those endpoints are what the Phase 3 tax/rent pipeline used.

---

**User**

For phase 2 markdown document #3, what is the table I should look for on https://www.bls.gov/cex/tables.htm to download?

---

**Cursor**

For Phase 2 item **#3 (BLS CES)**, on https://www.bls.gov/cex/tables.htm download:

**Calendar year → Mean expenditures → “Income before taxes”**

On the site that’s the Excel file named like:

`cu-income-before-taxes-YYYY.xlsx`  
example: https://www.bls.gov/cex/tables/calendar-year/mean/cu-income-before-taxes-2023.xlsx

That’s what Phase 2 tried (and failed with HTTP 403 from the automated downloader). Inside the workbook, use the **Food at home** row across the income columns for `f̄` / `M`.

**Also useful (closer to Appendix F “by income quintile”):**  
**“Quintiles of income before taxes”** (same Calendar year / Mean section). That splits spending by income quintile, which maps better to Low/Mid/High than the all-consumer-unit average alone.

**Note:** Older model text says “Table 4700.” On the current BLS tables page that label isn’t always shown; **Income before taxes** / **Quintiles of income before taxes** are the current equivalents.

---

**User**

Here is the link for Income before taxes 2024: https://www.bls.gov/cex/tables/calendar-year/mean-item-share-average-standard-error/cu-income-before-taxes-2024.xlsx

Here is the link for Quintile of income before taxes 2024: https://www.bls.gov/cex/tables/calendar-year/mean-item-share-average-standard-error/cu-income-quintiles-before-taxes-2024.xlsx

Can you use these links to download these files, plus through 2020?

---

**Cursor**

Downloading the 2020–2024 CES income and quintile workbooks using that URL pattern.

Automated downloads are still blocked by BLS (403). Trying the browser/fetch path next.

BLS is blocking this environment. Checking archive mirrors, then updating the download script with your URL pattern.

BLS returns HTTP 403 from this environment. Updating the download script with your URL pattern and adding a URL checklist you can open in a browser.

**Couldn't download them from here** — bls.gov returns **HTTP 403** to this environment (same as Phase 2). Your URL pattern is correct, though.

I added [`code/download_bls_ces_xlsx.py`](code/download_bls_ces_xlsx.py) and a checklist at [`data/bls/ces_xlsx_download_urls.txt`](data/bls/ces_xlsx_download_urls.txt) with all 10 files (income + quintiles, **2020–2024**).

**What to do:** In your browser, download each file and save into `data/bls/` with the same filenames, then tell me (or run `python code/download_bls_ces_xlsx.py`) — it will pick up existing files and extract the food-at-home rows.

---

**User**

I entered the data in the data/bls/ directory

---

**Cursor**

Checking the files you added and extracting the food-at-home spending data.

Found 9 of 10 files (2024 quintiles still missing). Parsing them into clean food-at-home series and updating market-size estimates.

Parsed your files. **9 of 10** are in place; only `cu-income-quintiles-before-taxes-2024.xlsx` is still missing.

**Outputs in `data/bls/`:**
- `ces_food_at_home_by_income_bracket.csv` — 2020–2024
- `ces_food_at_home_by_income_quintile.csv` — 2020–2023
- `ces_fbar_by_income_group_from_xlsx.csv` — model Low/Mid/High weekly spend
- `cd2_market_size_M_from_xlsx.csv` — CD2 market size `M`

**2024 food-at-home (annual → weekly `f̄`):**
| Group | Annual | Weekly |
|-------|--------|--------|
| Low (&lt;$25K) | $3,737 | **$71.87** |
| Mid ($25–50K) | $4,603 | **$88.52** |
| High (&gt;$50K) | $7,421 | **$142.71** |
| All CU | $6,224 | **$119.69** |

**CD2 `M` (2024):** ≈ **$124.0M** (all-CU mean) · ≈ **$106.0M** (income-weighted)

If you drop in the 2024 quintiles file, say the word and I’ll parse it too.

---

**User**

I added 2024 quintiles. Go ahead and parse that as well.

Also, Can you update phase 2 markdown with the ACS data updates (now that I used the Census_API_KEY) and downloaded BLS data (and other changes)? Phase 2 should accurately reflect how successfully I have downloaded all the target data.

---

**Cursor**

Parsing the 2024 quintiles file and updating the Phase 2 report to match the current ACS and BLS results.

2024 quintiles are parsed. Food at home: Q1 **$3,843** … Q5 **$9,336** (all-CU **$6,224**). All 10 XLSX files are complete; `ces_food_at_home_by_income_quintile.csv` now covers **2020–2024**.

[`docs/data_collection/phase2_download_report.md`](docs/data_collection/phase2_download_report.md) is updated to reflect:

- ACS **2020–2024** via Census API key (full household/income table)
- BLS income + quintile XLSX **2020–2024** on disk and parsed (`f̄`, income-weighted `M`)
- Store extracts unchanged (137 / 553 / 9)
- Clear success checklist; remaining gaps only ACS 2025, policy `B`, and Phase 3 tax/rent

---

**User**

Can you create python code to create and save a plot of the census tracts in bronx_cd2_tracts.geojson overlapped with a map of that section of the bronx? 

Do i have the geofile of CD2? if so, can it be overlayed?

---

**Cursor**

Checking which geography files you already have for CD2 and the tracts.

Yes — you already have the CD2 boundary at [`data/geography/bronx_cd2_boundary.geojson`](data/geography/bronx_cd2_boundary.geojson). It can be overlaid with the tracts.

---

**User**

Implement the plan as specified, it is attached for your reference. Do NOT edit the plan file itself.

To-do's from the plan have already been created. Do not create them again. Mark them as in_progress as you work, starting with the first one. Don't stop until you have completed all the to-dos.

---

**Cursor**

CartoDB tiles now need an API key, so the basemap may be blank. Switching to OpenStreetMap and regenerating.

OSM blocked the tile requests. Switching to Esri World Street Map and regenerating.

Done. Tracts + CD2 boundary are plotted on a street basemap.

**Outputs**
- [`data/geography/bronx_cd2_tracts_map.png`](data/geography/bronx_cd2_tracts_map.png)
- [`data/geography/bronx_cd2_tracts_map.pdf`](data/geography/bronx_cd2_tracts_map.pdf)

**Script:** [`code/plot_bronx_cd2_map.py`](code/plot_bronx_cd2_map.py)  
Uses your existing [`bronx_cd2_tracts.geojson`](data/geography/bronx_cd2_tracts.geojson) and overlays [`bronx_cd2_boundary.geojson`](data/geography/bronx_cd2_boundary.geojson) in red. Basemap is Esri World Street Map (OSM/Carto blocked automated tile access from this environment).

Re-run: `python code/plot_bronx_cd2_map.py`

---

**User**

<timestamp>Tuesday, Sep 22, 2026, 3:07 PM (UTC-4)</timestamp>
<system_notification>
The following task has finished. If you were already aware, ignore this notification and do not restate prior responses.

<task>
kind: shell
status: success
task_id: 979946
title: Install contextily and generate CD2 tract map
tool_call_id: call-7fe7f6c4-e1cc-4d1a-b372-77f33ab7c156-169
fc_f37218a6-69fa-9ffa-8f87-98b65133b10a_1
output_path: C:\Users\samia\.cursor\projects\c-Users-samia-Code-Projects-grocery-subsidy-analysis\terminals\979946.txt
</task>
</system_notification>
<user_query>Briefly inform the user about the task result and perform any follow-up actions (if needed). If there's no follow-ups needed, don't explicitly say that.</user_query>

---

**Cursor**

The map generation finished successfully. The figure is at `data/geography/bronx_cd2_tracts_map.png` (and `.pdf`), with census tracts and the CD2 boundary over an Esri street basemap.

---

**User**

which is the recommended data base for stores: NY ag and markets, SNAP, or NYC open data?

---

**Cursor**

**Recommended primary list: NYS Ag & Markets** (`data/stores/agmarkets_bronx_cd2.csv`, 137 stores in CD2).

Why:
- It’s the licensed retail food store universe (what you asked for originally).
- Best coverage of useful fields (including **square footage** for rent path B).
- Strong Phase 3 match rates (BBL ~99%, Tax_j ~91%, any rent ~72%).
- Cleaner for a grocery/bodega candidate set than SNAP’s much larger mix.

**SNAP** (553): good for SNAP-authorization / eligibility (`e_j`), but includes many non–full-line retailers. Use as a **cross-check / eligibility filter**, not the main inventory.

**NYC DOHMH Open Data** (9): too sparse (restaurant-inspection oriented). Keep as a **supplement only**.

Practical approach: build the model’s store set `J` from **Ag & Markets**, then flag which are also in SNAP.

---

**User**

Write a script that determines if an agmarkets store has SNAP eligibility by linking the data. Save in a new dataset agmarkets_bronx_cd2_snap_eligibility.csv and a .geojson

---

**Cursor**

Checking Ag & Markets and SNAP field structures so we can plan a solid link.

---

**User**

Implement the plan as specified, it is attached for your reference. Do NOT edit the plan file itself.

To-do's from the plan have already been created. Do not create them again. Mark them as in_progress as you work, starting with the first one. Don't stop until you have completed all the to-dos.

---

**Cursor**

Ag & Markets stores are linked to SNAP eligibility.

**Outputs**
- `data/stores/agmarkets_bronx_cd2_snap_eligibility.csv`
- `data/stores/agmarkets_bronx_cd2_snap_eligibility.geojson`

**Match rates (137 Ag & Markets stores)**
- Currently SNAP eligible: **86/137 (62.8%)**
- Ever SNAP authorized: **123/137 (89.8%)**
- Methods: 112 address, 11 spatial (≤75 m), 14 none

Run again with: `python code/link_agmarkets_snap.py`

---

**User**

when I do git add, git commit, git push, do I have to do something weearate for the lfs data?

---

**Cursor**

Checking how this repo handles Git LFS so I can give a precise answer.

No separate LFS commit/push for day-to-day work. Once `git lfs install` has been run once on the machine, normal `git add` / `git commit` / `git push` handles LFS automatically for paths already listed in `.gitattributes`.

In this repo that means only:
- `data/stores/snap_retailers_us_raw.csv`
- `data/stores/snap_retailers_raw_sample_cols.csv`
- `data/stores/**/*.zip`

Everything else under `data/` (CD2 CSVs, GeoJSON, the SNAP eligibility outputs, etc.) is normal git.

You only need extra LFS steps when:
1. **Adding a new large file type** — run `git lfs track "path/or/pattern"` and commit the updated `.gitattributes` with (or before) the file.
2. **After clone/pull** — if a big file looks like a tiny pointer stub, run `git lfs pull`.

So for your usual Phase outputs: just add/commit/push as usual.

