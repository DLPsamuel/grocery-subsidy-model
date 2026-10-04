# Bronx CD2 boundary file source
_Exported on 10/4/2026 at 10:39:09 EDT from Cursor (3.17.8)_

---

**User**

@data/geography/bronx_cd2_boundary.geojson:1-9 where did this file come from? how was it downloaded?

---

**Cursor**

I'll trace where `bronx_cd2_boundary.geojson` is referenced and how the download scripts produce it.

`data/geography/bronx_cd2_boundary.geojson` is a one-feature extract of Bronx Community District 2 (BoroCD `202`). It was not downloaded as its own file. It was cut from the citywide NYC Community Districts layer and written locally.

**Source.** NYC Department of City Planning, published on NYC Open Data as [Community Districts](https://data.cityofnewyork.us/City-Government/Community-Districts/5crt-au7u) (dataset `5crt-au7u`). The properties on the feature match that layer: `boro_cd` = `"202"`, plus `shape_leng` and `shape_area`. The geometry is a MultiPolygon in WGS84.

**How it was written.** [`load_cd2_boundary()`](code/data_paths.py) in `code/data_paths.py` does the fetch and filter. If the local file is missing, it loads the full citywide GeoJSON with GeoPandas, keeps the row whose BoroCD is `202`, and saves that feature:

```49:81:code/data_paths.py
def load_cd2_boundary() -> gpd.GeoDataFrame:
    """Load Bronx CD2 (BoroCD 202) from saved GeoJSON, or fetch from NYC Open Data."""
    path = GEO_DIR / "bronx_cd2_boundary.geojson"
    if path.exists():
        gdf = gpd.read_file(path)
        return gdf.to_crs(epsg=4326)

    # Current NYC Open Data Community Districts dataset
    url = "https://data.cityofnewyork.us/resource/5crt-au7u.geojson"
    # Fetch all CDs then filter (dataset is small)
    try:
        gdf = gpd.read_file(url)
    except Exception:
        # Fallback: geospatial export endpoint
        url = "https://data.cityofnewyork.us/api/geospatial/5crt-au7u?method=export&format=GeoJSON"
        gdf = gpd.read_file(url)
    ...
    cd2.to_file(path, driver="GeoJSON")
```

Primary URL: `https://data.cityofnewyork.us/resource/5crt-au7u.geojson`. If that fails, the fallback is the Socrata geospatial export (`/api/geospatial/5crt-au7u?method=export&format=GeoJSON`). No API key is required.

**What triggered it.** The Phase 2 geography run calls that helper from [`code/download_geography.py`](code/download_geography.py) (`python code/download_geography.py`). The same helper also runs from the store scripts if the file is not already on disk. After the first successful fetch, later runs only read the saved GeoJSON. The Phase 2 report records that boundary as present (one polygon) as of 2026-09-18.

---

**User**

@data/geography/bronx_cd2_tracts.geojson:6 What does nta2020 tell us? is 0202 CD2?

---

**Cursor**

The tract feature uses `nta2020` of `BX0202`. I’ll check how that code is defined in the project data and NYC geography docs.

`nta2020` is the 2020 Neighborhood Tabulation Area code. On this tract it is `BX0202`, which is Longwood, not Community District 2 itself.

NYC Department of City Planning builds that six-character code as borough + community district + neighborhood:

| Part | Value | Meaning |
|------|--------|---------|
| Borough | `BX` | Bronx |
| Community district | `02` | Bronx CD 2 |
| Neighborhood | `02` | The second NTA inside that district |

So the middle `02` is CD 2. The last `02` is only the neighborhood number inside that district. `BX0202` as a whole is one neighborhood: Longwood (`ntaname`).

The field that stands for CD 2 is `cdta2020` = `BX02`. Its name on this feature is `BX02 Longwood-Hunts Point (CD 2 Approximation)`. A CDTA is the census-tract approximation of a community district, not the legal CD boundary in `bronx_cd2_boundary.geojson` (BoroCD `202`).

In this file, that CD 2 approximation contains two NTAs:

- `BX0201` — Hunts Point
- `BX0202` — Longwood

---

**User**

@code/download_acs.py:207-211 what does this section of code do?

---

**Cursor**

I’ll read the surrounding ACS download logic so I can explain what those four lines filter and write.

Those lines keep only Bronx Community District 2 tracts from a borough-wide ACS pull and save that subset.

Just above them, Census Reporter has already returned every Bronx census tract for one release. `hh` is table B11001 (households by type, including total households). `inc` is table B19001 (income brackets, plus the `n_low`, `n_mid`, and `n_high` sums). Those full-Bronx frames are written as `bronx_B11001_*.csv` and `bronx_B19001_*.csv`.

`cd2_geoids` was loaded earlier from `data/geography/bronx_cd2_tracts.geojson` — the 16 tracts whose centroids fall inside CD2. Lines 208–209 keep rows whose `GEOID` is in that set. If the GeoJSON is missing and the set is empty, the `else` branch keeps every Bronx tract instead of writing an empty file.

Lines 210–211 write the filtered tables to `data/acs/cd2_B11001_{year}.csv` and `data/acs/cd2_B19001_{year}.csv`. The next lines sum those CD2 rows into the household and income totals. The same filter is repeated at lines 248–251 for the official Census API years.

---

**User**

Was assigning the 16 tract GeoID part of this code or does NY data already do this?

---

**Cursor**

The 16-tract set is **not** assigned in `download_acs.py`. That script only **reads** GEOIDs already saved in `bronx_cd2_tracts.geojson` and filters ACS rows to match.

Two separate things:

**1. GEOID values themselves — from NYC / Census data**  
Each tract feature already has a Census GEOID (e.g. `36005008700`). NYC’s 2020 tracts layer includes that as `geoid`. ACS uses the same IDs. Nothing in this project invents them.

**2. Which tracts count as “CD2” — decided by this project**  
[`download_geography.py`](code/download_geography.py) builds the list by geometry:
- load Bronx CD2 boundary (`BoroCD` 202)
- load Bronx tracts from NYC Open Data
- keep tracts whose **centroid falls inside** that CD2 polygon

That filtered set is written to `bronx_cd2_tracts.geojson` (16 tracts). ACS later uses those GEOIDs.

NYC does attach related labels on tracts (`cdta2020` = `BX02`, names like “CD 2 Approximation”), but the pipeline does **not** use those fields to pick the 16 tracts. It uses the spatial centroid-within-CD2 rule against the official CD boundary.

---

**User**

Did I get the data from census reporter or census API?

---

**Cursor**

Checking the ACS download metadata and summary files to see which source was actually used.

Both ran, but the CD2 numbers you rely on are from the **Census API**.

`acs_download_meta.json` shows `api_key_used: true`, and the combined summary marks every year as `censusapi`:

| Year | Source in summary |
|------|-------------------|
| 2020–2024 | `censusapi:2020` … `censusapi:2024` |
| 2025 | missing (not released) |

What happened in the run:
1. **Census Reporter** pulled ACS 2024 5-year (and `latest`, same release) and wrote borough files like `bronx_B11001_2024_acs2024_5yr.csv`.
2. **Census API** then pulled 2020–2024 with your key and **overwrote** the per-year CD2 files (`cd2_B11001_*.csv`, `cd2_B19001_*.csv`) and the summaries.

The script prefers Census API over Census Reporter when both exist for the same year, so treat the official multi-year CD2 series as Census API.

---

**User**

where were the census tract shape files downloaded from?

---

**Cursor**

Checking the geography download script and what's on disk for tract sources.

They weren’t downloaded as Census shapefiles. The CD2 tracts came from **NYC Open Data as GeoJSON**.

**Primary source used** (in [`download_geography.py`](code/download_geography.py)):

- Dataset: [2020 Census Tracts (Tabulation Water Included)](https://data.cityofnewyork.us/City-Government/2020-Census-Tracts-Tabulation-Water-Included-/63ge-mke6)
- API: `https://data.cityofnewyork.us/resource/63ge-mke6.geojson`
- Filter: `boroname='Bronx'`, then centroid-within CD2 → `bronx_cd2_tracts.geojson`

That matches the attributes on disk (`ntaname`, `cdta2020`, `nta2020`, etc.), which are NYC Planning fields, not TIGER.

**Fallback (not used here):** U.S. Census TIGER/Line shapefile zip  
`https://www2.census.gov/geo/tiger/TIGER2023/TRACT/tl_2023_36_tract.zip`  
There is no `tl_2023_36_tract.zip` under `data/geography/`, so the NYC GeoJSON path succeeded and TIGER was never needed.

---

**User**

What is the difference between the files data\acs\bronx_B11001_2024_acs2024_5yr.csv and data\acs\bronx_B11001_2024_latest.csv

---

**Cursor**

Comparing those two files and how the download script produces them.

They are the **same ACS data**, pulled twice from Census Reporter under different release aliases.

`download_acs.py` tries both:

```15:18:code/download_acs.py
RELEASES = [
    ("acs2024_5yr", 2024),
    ("latest", None),  # resolve year from response metadata if needed
]
```

| File | Census Reporter release | `source` column |
|------|-------------------------|-----------------|
| `bronx_B11001_2024_acs2024_5yr.csv` | `acs2024_5yr` | `censusreporter:acs2024_5yr` |
| `bronx_B11001_2024_latest.csv` | `latest` | `censusreporter:latest` |

At the time of the download, `latest` pointed at ACS 2024 5-year, so you got 361 Bronx tracts with identical GEOIDs, names, household counts, and year. The only difference is the `source` label.

`latest` is a moving alias; later it could resolve to a newer release. `acs2024_5yr` is pinned to that specific release.

---

**User**

Create a table describing what each type of .csv file is in data/acs

---

**Cursor**

I'll inventory the ACS CSV naming patterns and summarize what each type contains.

| File pattern | Geography | Table / content | Source | Rows (typical) | Role |
|---|---|---|---|---:|---|
| `bronx_B11001_{year}_{release}.csv` | All Bronx tracts | B11001 total households (`B11001_001E`) | Census Reporter (`acs2024_5yr` or `latest`) | 361 | Full-borough raw pull |
| `bronx_B19001_{year}_{release}.csv` | All Bronx tracts | B19001 income brackets + `n_low` / `n_mid` / `n_high` | Census Reporter | 361 | Full-borough raw pull |
| `bronx_B11001_censusapi_{year}.csv` | All Bronx tracts | B11001 total households | Official Census API | 361 | Full-borough raw pull (preferred multi-year) |
| `bronx_B19001_censusapi_{year}.csv` | All Bronx tracts | B19001 income brackets + income groups | Official Census API | 361 | Full-borough raw pull (preferred multi-year) |
| `cd2_B11001_{year}.csv` | CD2 tracts only | B11001 total households | Filtered from borough pull (Census API overwrote these) | 16 | Study-area household counts by tract |
| `cd2_B19001_{year}.csv` | CD2 tracts only | B19001 brackets + `n_low` / `n_mid` / `n_high` | Same filter / overwrite | 16 | Study-area income groups by tract |
| `cd2_household_income_summary_{year}.csv` | CD2 aggregate | One row: `N_HH`, `n_low`, `n_mid`, `n_high`, tract count, source | Sum of CD2 tract rows | 1 | Per-year district totals |
| `cd2_household_income_summary.csv` | CD2 aggregate | Same columns for all years | Merged yearly summaries; prefers `censusapi` over Reporter | 5 (2020–2024) | Canonical multi-year CD2 summary |

**Quick reading guide**

- `bronx_*` = all ~361 Bronx tracts; `cd2_*` = the 16 CD2 tracts.
- `B11001` = household totals; `B19001` = household income bands.
- `censusapi` / no release tag on `cd2_*` = what the project actually uses for 2020–2024.
- `*_acs2024_5yr` and `*_latest` = duplicate Census Reporter snapshots of the same 2024 5-year release.

---

**User**

What is the difference between B11001 and B19001

---

**Cursor**

They are two different ACS tables that answer different questions about households.

| | **B11001** | **B19001** |
|---|---|---|
| **Name** | Household Type | Household Income in the Past 12 Months |
| **What it counts** | Households by living arrangement (family vs nonfamily, married, etc.) | Households by income bracket |
| **Main variable used here** | `B11001_001E` = **total households** | `B19001_001E` = total households (should match), plus brackets `002`–`017` |
| **Role in this project** | District / tract size `N_HH` | Split households into `n_low`, `n_mid`, `n_high` |

In this repo:

- **B11001** → how many households are in each tract (`N_HH`).
- **B19001** → how those households fall across income bands, then grouped as:
  - low: &lt;$25k (`002`–`005`)
  - mid: $25k–$49,999 (`006`–`010`)
  - high: ≥$50k (`011`–`017`)

Same universe (households), different cross-tabs: type vs income.

---

**User**

why is both 5 yr and individual year donwloaded?

---

**Cursor**

Checking which ACS product (1-year vs 5-year) each download path actually requests.

They are **not** 5-year vs 1-year downloads. Almost everything here is ACS **5-year**. What looks like “individual years” are different **end-year vintages** of that same 5-year product.

**What the files actually are**

| What you see | What it really is |
|---|---|
| `*_acs2024_5yr` / `*_latest` | One ACS **5-year** release (2020–2024 pooled), via Census Reporter |
| `*_censusapi_2020` … `2024` | ACS **5-year** for each end-year, via `api.census.gov/.../acs/acs5` |

The Census API URL is explicitly 5-year:

```139:139:code/download_acs.py
    base = f"https://api.census.gov/data/{year}/acs/acs5"
```

So `censusapi_2022` means “ACS 5-year **ending** 2022” (roughly 2018–2022 pooled), not ACS 1-year 2022.

**Why both paths exist**

1. **Census Reporter** — works without a key; good for the latest 5-year release only. That’s why you get `acs2024_5yr` and `latest`.
2. **Census API** — needs a key; can pull **each end-year** 2020–2024 so you can track change over time for the model.

When both succeed for the same end-year, the script prefers Census API for the `cd2_*` files and the combined summary.

**Why multiple end-years at all**

Tract-level ACS for small areas like CD2 is published mainly as 5-year estimates. Pulling 2020–2024 end-years gives a short time series of overlapping 5-year windows, not five separate annual surveys.

There is no ACS 1-year tract download in this pipeline.

---

**User**

I deleted those files. It looks like only 1 family type was downloaded. Is B11001 just for a total number?

---

**Cursor**

Yes. In this project, **B11001 is only used for the total household count**.

The download requests a single estimate:

```140:140:code/download_acs.py
    vars_hh = ["NAME", "B11001_001E"]
```

`B11001_001E` is “Total households.” The full ACS table also breaks that into family / nonfamily subtypes (married-couple, male householder, living alone, etc.), but those variables are **not** downloaded here.

So:
- **B11001 in this repo** → one number per tract: total households (`N_HH`)
- **B19001** → income brackets (and the low/mid/high splits)

If you need household *composition* by type, you’d have to pull more B11001 columns; right now the pipeline only needs the total.

---

**User**

DId I end up downloading CES data from script or manually?

---

**Cursor**

Checking the BLS download scripts and Phase 2 notes for how the CES files were obtained.

**Manually (browser), not via successful script HTTP download** — for the CES workbooks themselves.

Phase 2 records that `bls.gov` returned **HTTP 403** to automated clients, so the 10 XLSX files were saved into `data/bls/` from a browser, then processed by script:

- Income before taxes: `cu-income-before-taxes-2020.xlsx` … `2024.xlsx`
- Quintiles: `cu-income-quintiles-before-taxes-2020.xlsx` … `2024.xlsx`

**What the scripts did**

| Step | How |
|------|-----|
| Get the `.xlsx` files | Browser (manual) |
| Try automated download | `download_bls_ces_xlsx.py` — often 403; skips files already on disk |
| Extract food-at-home / build `M` | Scripts (`parse_bls_ces_xlsx.py`, related CES parsers) |

`bls_xlsx_download_meta.json` lists most files under `"downloaded"`, but that also includes **“already present”** (browser saves). It still records an explicit **HTTP 403** for `cu-income-quintiles-before-taxes-2024.xlsx` on at least one run.

So: **raw CES tables = manual; parsing and derived CSVs = script.**

---

**User**

Describe to me where Cu-income-before-taxes and cu-income-quintile-before-taxes came from (website) and what they are

---

**Cursor**

They come from the **U.S. Bureau of Labor Statistics (BLS) Consumer Expenditure Survey (CES)** — calendar-year detailed spending tables.

### Website

- Portal: [BLS CES tables](https://www.bls.gov/cex/tables.htm) · [CES home](https://www.bls.gov/cex/)
- Folder used here:  
  `https://www.bls.gov/cex/tables/calendar-year/mean-item-share-average-standard-error/`
- Example files:  
  - [cu-income-before-taxes-2024.xlsx](https://www.bls.gov/cex/tables/calendar-year/mean-item-share-average-standard-error/cu-income-before-taxes-2024.xlsx)  
  - [cu-income-quintiles-before-taxes-2024.xlsx](https://www.bls.gov/cex/tables/calendar-year/mean-item-share-average-standard-error/cu-income-quintiles-before-taxes-2024.xlsx)

“CU” = **consumer unit** (CES household-like spending unit). These workbooks report **mean**, **share**, and **standard error** of expenditures by income group for a calendar year (national all-CU geography, not NYC-specific).

### What each table is

| File | What it is | Columns / groups |
|------|------------|------------------|
| `cu-income-before-taxes-{year}.xlsx` | Average spending by **pretax income brackets** | e.g. all CUs, &lt;$15k, $15–29k, …, $200k+ |
| `cu-income-quintiles-before-taxes-{year}.xlsx` | Same spending items by **income quintiles** | all CUs, lowest 20%, …, highest 20% |

Both include many expenditure lines (food, housing, etc.). This project pulls the **“Food at home” → Mean** row to get annual food-at-home spending (`f̄`) by income group, then combines that with ACS household counts for market-size `M`.

**In short:** official BLS CES national spending tables, split two ways — income **brackets** vs income **quintiles** — both before taxes.

---

**User**

is ces_food_at_home calculated by adding food at home and Other food at home?

---

**Cursor**

Checking how the parser extracts the food-at-home values from the CES workbooks.

No. The values are taken from the single **“Food at home”** Mean row — they are **not** Food at home + Other food at home.

```50:54:code/parse_bls_ces_xlsx.py
def parse_income_file(path: Path, year: int) -> dict | None:
    df = pd.read_excel(path, header=None)
    row = _find_mean_row(df, "Food at home")
    if row is None:
        return None
```

Same for quintiles: exact match on `"Food at home"`, then the next **Mean** row’s dollar amounts by income group.

In CES, **Other food at home** is a **subcategory** under Food at home (along with cereals, meats, dairy, fruits/vegetables, etc.). Adding it would double-count. The scanner CSVs (`ces_food_*rows*`) list both labels because they match any row containing “food at home,” but the clean outputs (`ces_food_at_home_by_income_*.csv`) use only the parent Food at home total.

---

**User**

what is f_bar_weekly_all

---

**Cursor**

`f_bar_weekly_all` is **mean weekly food-at-home spending for all consumer units**, in dollars.

It is the CES annual “Food at home” mean for all CUs, divided by 52:

```72:72:code/parse_bls_ces_xlsx.py
    out["f_bar_weekly_all"] = round(out["all_consumer_units"] / 52, 2) if out["all_consumer_units"] else None
```

Example from 2024: annual `$6,224` → weekly `$119.69`.

That is the project’s `f̄` (f-bar) for the average household, used when building market size `M` (e.g. households × annual food-at-home spending). It is national CES, not Bronx-specific.

---

**User**

where does cd2_market_size come from?

---

**Cursor**

It is **not downloaded**. It is **computed** in [`parse_bls_ces_xlsx.py`](code/parse_bls_ces_xlsx.py) from two local inputs:

1. **ACS CD2 household counts** — `data/acs/cd2_household_income_summary.csv` (`N_HH`, `n_low`, `n_mid`, `n_high` by year)
2. **CES food-at-home means** — parsed from `cu-income-before-taxes-{year}.xlsx` (annual $ by income bracket)

For each ACS year, the script matches the nearest CES year and writes `cd2_market_size_M_from_xlsx.csv`:

| Column | Formula |
|--------|---------|
| `M_usd_all_cu_mean` | `N_HH ×` CES all-CU annual food-at-home |
| `M_usd_income_weighted` | `n_low × f̄_low + n_mid × f̄_mid + n_high × f̄_high` (annual) |

Example 2024: `19,922 × $6,224 ≈ $124M` all-CU mean; income-weighted ≈ `$106M`.

There is also an older/alternate file, `cd2_market_size_M_estimates.csv`, from [`download_bls_ces.py`](code/download_bls_ces.py) (published CES series + ACS). The XLSX-based file is the one Phase 2 treats as the main `M` estimate.

---

**User**

what website is ag& markets data from

---

**Cursor**

**New York State Open Data** — Retail Food Stores (NYS Department of Agriculture and Markets).

- Portal: https://data.ny.gov/Economic-Development/Retail-Food-Stores/9a8c-vfzj  
- API used by the script: https://data.ny.gov/resource/9a8c-vfzj.json  

[`download_stores_agmarkets.py`](code/download_stores_agmarkets.py) pulls that JSON, then keeps stores inside Bronx CD2.

---

**User**

what are the files "FC_SHD_bbl_analysis" and "neighborhood_indicators_..." files?

---

**Cursor**

Both are **NYU Furman Center** downloads (dated **2026-05-05**). They are **not** from your Phase 2 Ag & Markets / ACS / CES scripts, and the project notes them as **unused** for the grocery model so far ([`docs/ISSUES_AND_GAPS.md`](docs/ISSUES_AND_GAPS.md)).

### `FC_SHD_bbl_analysis_*`
**Furman Center Subsidized Housing Database (SHD), lot/BBL view.**

- Files: `data/FC_SHD_bbl_analysis_2026-05-05.csv` + matching data dictionary
- Unit of analysis: **BBL** (Borough–Block–Lot)
- Content: property attributes (address, CD, tract, units, year built, assessed value, owner, violations, flood flags, etc.) for lots tied to subsidized housing
- About: **housing** subsidies / properties, not grocery stores

There is a related sister file, `FC_SHD_subsidy_analysis_*`, which is the **subsidy/program** view (agency, program name like LIHTC, start/end dates, units) rather than the lot attributes view.

### `Neighorhood_Indicators_CoreDataDownload_*`
**Furman Center CoreData.nyc neighborhood indicators** (filename has the typo “Neighorhood”).

- File: `data/Neighorhood_Indicators_CoreDataDownload_2026-05-05.xlsx`
- Source branding: CoreData.nyc / NYU Furman Center 2026  
  Methods: https://furmancenter.org/coredata/userguide/methodology
- Content: annual indicators by region (city, borough, neighborhood, etc.): income, rent burden, crime, demographics, housing, subsidized housing counts (`shd_*`), etc.

**Bottom line:** SHD = subsidized **housing** at the BBL/program level; CoreData = neighborhood **socioeconomic/housing** indicators. Neither is a grocery or Ag & Markets dataset.

---

**User**

how do i know if a store closed in ag & markets database?

---

**Cursor**

You generally **can’t**, from a single Ag & Markets download.

The NYS Retail Food Stores file (`9a8c-vfzj`) is a **snapshot of currently licensed stores**. Your columns are things like `license_number`, `operation_type`, `estab_type`, name, address, `square_footage`, `georeference` — there is **no** `status`, `closed`, `active`, or license-expiration field in `agmarkets_retail_food_stores_raw.csv` / `agmarkets_bronx_cd2.csv`.

In your pull, `operation_type` is essentially all `"Store"`; that is not open vs closed.

**Practical implications**

| Approach | What it tells you |
|----------|-------------------|
| One Ag & Markets extract | Treat rows as licensed/open at download time |
| Compare two downloads over time | Store missing later ≈ likely closed / license dropped |
| SNAP list | Has open/closed (your docs note many SNAP rows are closed) — different dataset |

So: Ag & Markets ≈ “on the licensed list now.” Closure is inferred by **disappearing from a later refresh**, not by a flag in this file.

---

**User**

how was the list of ag and market stores filtered for cd2?

---

**Cursor**

Filtered in two steps in [`download_stores_agmarkets.py`](code/download_stores_agmarkets.py):

1. **County** — keep rows where `county == "BRONX"` → `agmarkets_bronx_county.csv`
2. **CD2 geometry** — parse lon/lat from `georeference`, then keep points **inside** the Bronx CD2 polygon from `load_cd2_boundary()` via `points_in_cd2(..., predicate="within")` → `agmarkets_bronx_cd2.csv` (137 stores)

Fallback (only if coords are missing): ZIP codes `10454`, `10455`, `10459`, `10474`. Your run used the **spatial** path, not ZIP.

So CD2 membership is **point-in-polygon** against the official CD2 boundary, not NTA/`cdta2020` labels.

---

**User**

Describe to me what phase 3 found, where it got each data file, how each one was filtered, and what they represent

---

**Cursor**

I'll read the Phase 3 report, script, and outputs to summarize findings, sources, filters, and what each file means.

## What Phase 3 was for

Attach **property tax (`Tax_j`)** and **rent (`Rent_j`)** to each Phase 2 CD2 store so the model can treat tax breaks and rent subsidies as instruments. It does **not** re-filter geography: it starts from the Phase 2 CD2 lists and enriches them.

Pipeline: address → **BBL** → tax + rent lookups → three enriched CSVs under `data/phase3/`.

---

## What it found (bottom line)

| Inventory | n | BBL | Tax_j | Usable Rent_j |
|-----------|--:|----:|------:|--------------:|
| Ag & Markets | 137 | 99% | 91% | ~72% (mostly sq-ft × market rate) |
| SNAP | 553 | ~100% | 92% | ~11% (ACRIS only; no sq-ft) |
| DOHMH | 9 | 100% | 78% | 0% |

- **`Tax_j` works** for most Ag & Markets / SNAP stores (DOF lot charges). Caveat: tax is for the **whole lot**, not just the store.
- **`Rent_j` from ACRIS almost never works** as annual rent (~3% with dollar amounts).
- **Practical rent** = Ag & Markets **sq-ft × $20 / $27.50 / $35** (Hunts Point range). Best modeling file: `tax_rent_agmarkets_cd2.csv`.

---

## Input store lists (already CD2-filtered in Phase 2)

| File | Source website | How filtered to CD2 | What it is |
|------|----------------|---------------------|------------|
| `agmarkets_bronx_cd2.csv` | [NYS Open Data Retail Food Stores](https://data.ny.gov/Economic-Development/Retail-Food-Stores/9a8c-vfzj) | Bronx county → point-in-polygon vs CD2 boundary | Licensed retail food stores (+ sq-ft) |
| `snap_bronx_cd2.csv` | USDA SNAP Retailer Locator ZIP | Bronx/coords → point-in-CD2 | SNAP-authorized retailers (many closed in raw SNAP) |
| `nyc_dohmh_bronx_cd2_grocery.csv` | [DOHMH Restaurant Inspection Results](https://data.cityofnewyork.us/Health/DOHMH-New-York-City-Restaurant-Inspection-Results/43nn-pn8j) | Bronx + grocery-like keywords → CD2 | Sparse grocery-like establishments |

Phase 3 does **not** re-apply the CD2 spatial filter; it uses these CSVs as-is.

---

## External data Phase 3 called (per store / BBL)

| Purpose | Source | URL / dataset | Filter / method | What it represents |
|---------|--------|---------------|-----------------|-------------------|
| Address → BBL (primary) | NYC GeoSearch | [geosearch.planninglabs.nyc](https://geosearch.planninglabs.nyc/v2/search) | Query normalized street address; take PAD `bbl` | City lot ID for the address |
| Address → BBL (fallback) | PLUTO | Open Data `64uk-42ks` | Bronx address prefix match when GeoSearch fails | Same lot ID from tax-lot table |
| Assessed value context | PLUTO | same | Lookup by BBL | `assesstot`, land, exemptions, owner, building class — **not** the tax bill |
| **`Tax_j` (primary)** | DOF Property Charges Balance | `scjx-j6np` | `parid={BBL}`, `code=CHG`; sum latest tax year; annualize if &lt;4 quarters | Annual **property tax charges** on the lot |
| Tax (attempted, sparse) | DOF Assessment Data | `xw8u-vy7p` | by BBL | Often empty; not used as primary `Tax_j` |
| Rent path A | ACRIS Legals + Master | `8h5j-fqxa`, `bnx9-e6tj` | Borough/block/lot → docs typed `LEAS`, `MLEA`, `ASSTO`, `TERL`, `SUBL` | Recorded lease-related filings; amounts rarely usable as annual rent |
| Rent path B | Ag & Markets `square_footage` × rates | rates from Appendix F | Only where sq-ft present | Estimated annual rent: low/mid/high ($20 / $27.50 / $35 per sq-ft) |

Deferred / unused: NYCDB, taxbills.nyc.

---

## Output files and what they represent

| File | What it is |
|------|------------|
| `tax_rent_agmarkets_cd2.csv` | 137 Ag & Markets stores + BBL, `Tax_j`, rent columns — **main instrument file** |
| `tax_rent_snap_cd2.csv` | 553 SNAP stores + same enrichment (rent weak) |
| `tax_rent_dohmh_cd2.csv` | 9 DOHMH stores + enrichment (no rent) |
| `bbl_cache.json` / `tax_cache.json` / `acris_cache.json` | Cached API responses for re-runs |
| `phase3_success_rates.json` | Match-rate summary |
| `phase3_attempts_log.json` | Run log of attempts |

**Key columns:** `bbl`, `Tax_j`, `Rent_j` (preferred), `Rent_j_low/mid/high`, `Rent_j_acris`, `rent_method` ∈ {`acris`, `market_rate_sqft`, `acris_lease_no_amount`, `none`}.

---

## Takeaway

Phase 3 **matched almost all CD2 stores to lots and tax**, but **rent only works well for Ag & Markets with square footage**. SNAP/DOHMH need a sq-ft join (or survey) before rent instruments are usable at scale. Full write-up: [`docs/data_collection/phase3_tax_rent_report.md`](docs/data_collection/phase3_tax_rent_report.md).

---

**User**

@code/phase3_tax_rent.py:48 Add comments to each function describing what it does

---

**Cursor**

I'm in Ask mode, so I can't edit the file. Switch to Agent mode if you want me to add the comments directly.

Here's what each function does (for docstrings you can paste in):

Suggested one-liners / short docstrings:

| Function | Description |
|----------|-------------|
| `log_attempt` | Append one API/step attempt record to the in-memory run log. |
| `load_json` | Load a JSON file as a dict, or return `{}` if missing. |
| `save_json` | Write JSON atomically (temp file then replace) to avoid partial writes. |
| `clean_bbl` | Normalize a BBL to a 10-digit digit string, or `None` if invalid. |
| `parse_bbl` | Split a 10-digit BBL into borough, block, and lot for ACRIS queries. |
| `normalize_street` | Uppercase and abbreviate street tokens (AVE, ST, E/W, etc.). |
| `build_address` | Build a GeoSearch query string from house number, street, and ZIP. |
| `load_store_frames` | Load Phase 2 Ag & Markets, SNAP, and DOHMH CD2 store CSVs. |
| `geosearch_bbl` | Look up BBL via NYC GeoSearch (cached); return match fields. |
| `pluto_fallback_bbl` | If GeoSearch fails, try PLUTO address match for a Bronx BBL. |
| `fetch_pluto` | Fetch PLUTO assessed-value / lot attributes for a BBL. |
| `_num` | Coerce a value to float, or `None` if missing/invalid. |
| `fetch_dof_tax` | Compute annual `Tax_j` from DOF Property Charges Balance for a BBL. |
| `fetch_assessment` | Attempt DOF Assessment Data lookup (often empty). |
| `fetch_acris_lease` | Find lease-related ACRIS docs for a BBL and any `document_amt`. |
| `apply_market_rent` | Compute low/mid/high rent from sq-ft × $20 / $27.50 / $35. |
| `enrich_frame` | For one store list: match BBL, attach tax/rent columns, choose `Rent_j`. |
| `success_rates` | Summarize BBL / Tax_j / Rent_j match rates for a finished frame. |
| `main` | Run Phase 3 end-to-end: load stores, enrich all lists, write CSVs and meta. |

Example style at line 48:

```python
def log_attempt(name: str, **kwargs: Any) -> None:
    """Append one API/step attempt record to the in-memory run log."""
```

Switch to **Agent mode** and ask again if you want these applied across the file.

---

**User**

Go ahead and now add them in the file

---

**Cursor**

Adding concise docstrings to every function.

Docstrings are on all 19 functions in `code/phase3_tax_rent.py`.

---

**User**

what website is tax and rent information from?

---

**Cursor**

**Tax (`Tax_j`)** and **rent** come from different NYC sources:

### Tax
| Role | Website / dataset |
|------|-------------------|
| Primary `Tax_j` | [DOF Property Charges Balance](https://data.cityofnewyork.us/City-Government/DOF-Property-Charges-Balance/scjx-j6np) (`scjx-j6np`) |
| Context (assessed value) | [PLUTO](https://data.cityofnewyork.us/City-Government/Primary-Land-Use-Tax-Lot-Output-PLUTO-/64uk-42ks) (`64uk-42ks`) |
| Attempted, rarely used | [DOF Assessment Data](https://data.cityofnewyork.us/City-Government/Assessment-Data/xw8u-vy7p) (`xw8u-vy7p`) |

BBL matching (needed before tax lookup): [NYC GeoSearch](https://geosearch.planninglabs.nyc/docs/), with PLUTO as address fallback.

### Rent
| Role | Website / source |
|------|------------------|
| Path A (lease docs) | [ACRIS Real Property Legals](https://data.cityofnewyork.us/City-Government/ACRIS-Real-Property-Legals/8h5j-fqxa) + [Master](https://data.cityofnewyork.us/City-Government/ACRIS-Real-Property-Master/bnx9-e6tj); portal [a836-acris.nyc.gov](https://a836-acris.nyc.gov/) |
| Path B (most usable) | Ag & Markets `square_footage` × $20 / $27.50 / $35 (Appendix F rates) — **not** a rent website |

So: tax ≈ **NYC DOF Open Data**; recorded lease rent ≈ **ACRIS**; practical rent for most stores ≈ **sq-ft estimate**, not an official rent feed.

---

**User**

where did you get the $20, $27.5, $35 numbers from?

---

**Cursor**

They are **not from a rent website or broker report**. They come from the **model spec / Appendix F** as an assumed Hunts Point commercial range of **~$20–$35 per sq-ft per year**.

In code:

```35:38:code/phase3_tax_rent.py
# Appendix F Hunts Point market rent range ($/sq-ft/year)
RENT_PSF_LOW = 20.0
RENT_PSF_MID = 27.5
RENT_PSF_HIGH = 35.0
```

- **$20** and **$35** = the low and high ends of that stated range  
- **$27.50** = the midpoint used as the preferred `Rent_j` when ACRIS has no usable amount  

Your own source notes flag this as **unsourced**:

- [`docs/SIMPLIFIED_PLAN_AND_SOURCES.md`](docs/SIMPLIFIED_PLAN_AND_SOURCES.md): “from the spec, **no source given**”
- [`docs/SOURCE_LIST_RAHUL.md`](docs/SOURCE_LIST_RAHUL.md): “still unsourced… Inherited from the v3 spec with no citation”

So Phase 3 uses them as a **placeholder market-rate band**, not as measured Hunts Point listing data.

---

**User**

How is the DOF file showing taxes? it shows outstanding payments?

---

**Cursor**

It’s **billed property-tax charges (liabilities)**, not a curated “outstanding unpaid taxes only” field — though the same DOF table also has balance columns.

### What Phase 3 uses
Dataset: [DOF Property Charges Balance](https://data.cityofnewyork.us/City-Government/DOF-Property-Charges-Balance/scjx-j6np) (`scjx-j6np`).

For each BBL it pulls rows with `code=CHG`, takes the latest `taxyear`, and sums **`sum_liab`** across quarters (`cycle` like `1Q`…`4Q`). If fewer than 4 quarters exist, it annualizes: × `(4 / n_quarters)`.

```310:317:code/phase3_tax_rent.py
        liab = sum(_num(x.get("sum_liab")) or 0.0 for x in year_rows)
        ...
        if n_q and n_q < 4 and liab > 0:
            annual = liab * (4.0 / n_q)
```

### What the DOF fields mean (from API rows)
| Field | Meaning |
|-------|---------|
| `sum_liab` | Charge / liability for that period (**what Phase 3 uses**) |
| `sum_coll` | Collections / payments |
| `sum_bal` | Remaining balance |
| `sum_int` | Interest |
| `sum_dsc` | Discounts |

So **`Tax_j` ≈ annual charged tax liability**, not “how much is past due.”

### Why it can look like outstanding balances
On many rows (especially **future** quarters), `sum_coll` is `0` and `sum_bal == sum_liab`, so charge and unpaid balance match until payment posts. The code still intentionally uses **`sum_liab`**, not `sum_bal`.

Also: this is **lot-level** tax for the whole BBL, not the store’s share of a mixed-use building — which is why some Ag & Markets `Tax_j` values look huge.

---

**User**

what does code=CHG mean

---

**Cursor**

In the DOF Property Charges Balance dataset, **`code=CHG` means Charge** — a property-tax **charge/liability** row for that lot and quarter.

Phase 3 filters to `CHG` so it only sums billed tax charges (`sum_liab`), not other transaction types in the same table. For the sample BBL, the other code present was `SAC` (a different charge category), so without `code=CHG` you’d mix unlike records.

So: **`CHG` = tax charge**, not “closed,” “change,” or “outstanding balance.” Balance/payment status is in fields like `sum_bal` and `sum_coll`.

---

**User**

<timestamp>Tuesday, Sep 22, 2026, 4:51 PM (UTC-4)</timestamp>
<system_notification>
The following task has finished. If you were already aware, ignore this notification and do not restate prior responses.

<task>
kind: shell
status: error
task_id: 430237
title: List distinct DOF code values and counts
tool_call_id: call-c2ce5280-92de-4395-8740-7520db8dda13-86
fc_d549959a-f67d-9fb5-af38-75135e7ea508_0
detail: exit_code=1
output_path: C:\Users\samia\.cursor\projects\c-Users-samia-Code-Projects-grocery-subsidy-analysis\terminals\430237.txt
</task>
</system_notification>
<user_query>Briefly inform the user about the task result and perform any follow-up actions (if needed). If there's no follow-ups needed, don't explicitly say that.</user_query>

---

**Cursor**

The bulk query of all DOF `code` values timed out and failed. A single-BBL sample was enough instead: that lot showed `CHG` (charges) and `SAC` (another charge type), which is what the earlier answer used.

---

**User**

is BLS CPI and BLS CES food-at-home spending the same data?

---

**Cursor**

No. They are different BLS products.

| | **BLS CPI** | **BLS CES (CE)** |
|---|---|---|
| Full name | Consumer Price Index | Consumer Expenditure Survey |
| What it measures | **Price** change for a basket of goods over time (inflation index) | How much households **actually spend** on categories |
| Food-at-home role | Index of grocery **prices** | Average **dollars spent** on food at home |
| Units | Index (e.g. 1982–84 = 100), or % change | Dollars per consumer unit / year |
| In this project | Mentioned to **inflate old basket prices** (e.g. 2019 → today) | Used for **`f̄` and market size `M`** from the XLSX tables |

Your `data/bls/cu-income-*.xlsx` files are **CES**, not CPI. Same agency (BLS), different surveys: CPI tracks prices; CES tracks spending.

---

**User**

whats the smallest geography for CPI data

---

**Cursor**

**Smallest published CPI geography: selected metro / urban areas** (about **23** local indexes), not city neighborhoods, CDs, tracts, or ZIPs.

For your study, that means something like **New York–Newark–Jersey City, NY-NJ-PA** — not Bronx CD2.

BLS also publishes broader levels: U.S. city average, 4 regions, 9 divisions, and city-size classes. Prices are collected in ~75 urban areas, but indexes are only published for those coarser geographies. CPI also measures **price change over time**, not price *levels* across places.

---

**User**

Did i try matching SNAP database with AG and markets to see which ones accept snap?

---

**Cursor**

No. The three lists were downloaded and filtered to CD2 separately. There is **no** Ag & Markets ↔ SNAP crosswalk in the repo.

Phase 2 explicitly deferred it (“full fuzzy cross-list matching”). Phase 3 and `ISSUES_AND_GAPS.md` still list matching on **BBL/address** as a next step — mainly to flag SNAP-accepting licensed stores and to copy sq-ft from Ag & Markets onto SNAP.

So you do **not** yet have a field for “this Ag & Markets store accepts SNAP.” That would require joining the lists (and preferably keeping only **active** SNAP rows first, since ~456 of 553 CD2 SNAP records look closed).

---

**User**

how do I detemine if a row in snap is active?

---

**Cursor**

Use the **`End Date`** column in the SNAP file.

| `End Date` | Meaning |
|------------|---------|
| Blank / empty | Still authorized → treat as **active** |
| A real date | Authorization ended that day → **closed / inactive** |

In your CD2 extract (`snap_bronx_cd2.csv`):

- **97** rows with blank `End Date` → active  
- **456** rows with an end date → closed  

Example filter:

```python
active = df["End Date"].astype(str).str.strip().isin(["", "nan", "None"])
# or: active = pd.to_datetime(df["End Date"], errors="coerce").isna()
```

`Authorization Date` is when they were approved; it does **not** tell you if they’re still open. Your download script currently keeps all rows and does **not** filter on `End Date`.

