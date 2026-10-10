# Property Tax (Tax_j) and Rent (Rent_j), Fiscal Year 2025

Appendix F rows: Tax_j, Rent_j · Stores: the final 9 CD2 candidate stores · Last updated: 2026-09-30

Fiscal year 2025 = July 1, 2024 to June 30, 2025, to match the team's 2024 base year.

## Summary

- **Tax_j totals $690,411** across the 9 stores. It comes from DOF's actual property tax bills, split by the store's share of building floor area. It is checked against the tax estimate on each lot's Notice of Property Value: 7 lots are within 1.6%, and the other 2 are explained by reductions DOF made during the year.
- **Rent_j totals $1,335,208** (range $1.23M to $1.48M). The main source is DOF's estimated gross income for each building, from its 2024-25 Notice of Property Value. The old placeholder (store sq ft × $27.50) gave $1,886,500.
- Supermarket buildings in CD2 earn about **$17 to $19 per sq ft** according to DOF, well below the $27.50 placeholder. Smaller meat and produce stores are higher ($23 to $43).
- Listing asking rents (option 2) were only partly collected. LoopNet blocks automated access, and the browser connection dropped partway through Crexi. Only 5 usable listings are recorded. That is too few to set Rent_j, so they are shown for comparison only.
- The Phase 3 tax figures in `data/phase3/` were about 4 times too high (Key Food about 8 times). They counted duplicate bill rows and annualized partial years. Use the new figures instead.

## How to rerun

```
python code/build_tax_j.py        # store-to-lot table, tax bills, PLUTO, Tax_j
python code/build_rent_nopv.py    # download and read the 2024-25 notices
python code/build_tax_j.py        # second run fills in the notice check
python code/build_rent_j.py       # combine rent sources into Rent_j
```

`build_rent_nopv.py --skip-download` rereads PDFs already saved in `data/rent/nopv/` without downloading them again.

## Part A: Property tax (Tax_j)

### What was done

1. **Matched each store to its tax lot (BBL).** The lots come from the Phase 3 table. There is one override: Fine Fare is a condo unit. The building's billing lot (2027037501) has no tax bill, so the store's own unit lot (2027031001) is used. That is also the parcel number in ReferenceUSA.
2. **Downloaded every property tax charge** (`code = CHG`) for each lot from DOF Property Charges Balance (NYC Open Data `scjx-j6np`). The rows are saved unchanged.
3. **Calculated the fiscal year 2025 lot tax:**
   - keep installments whose billing period falls between 2024-07-01 and 2025-06-30
   - use the latest data extract
   - count each billing period once (DOF repeats rows in every monthly extract and adds a row when a payment posts)
   - add up the periods

   All 9 lots come to exactly 12 months, so nothing is annualized.
4. **Pulled floor areas from PLUTO** (`64uk-42ks`): building, commercial, retail and residential area, and number of buildings.
5. **Split the lot tax to the store:** `store_share = min(store_sqft / building_area, 1)` and `Tax_j = lot_tax × store_share`. Store sq ft is from the Ag & Markets license. Fine Fare's share is 1 because its condo bill is already the store's own.
6. **Checked against the notices:** compared each lot tax with the "Estimated Property Tax" on its 2024-25 Notice of Property Value. Differences over 5% are flagged.

### Results

| Store | Store sq ft | Lot tax FY2025 | Building sq ft | Store share | Tax_j | Notice check |
|---|---|---|---|---|---|---|
| Food Fair Fresh Market | 13,000 | $692,855 | 22,000 | 0.591 | $409,408 | ok (+0.3%) |
| Key Food | 15,000 | $472,669 | 67,339 | 0.223 | $105,311 | ok (0.0%) |
| Food Universe | 8,000 | $60,962 | 9,800 | 0.816 | $49,764 | ok (+1.6%) |
| C-Town (809 Southern Blvd) | 7,500 | $104,002 | 16,500 | 0.455 | $47,269 | ok (+1.6%) |
| C-Town (564 Southern Blvd) | 8,000 | $61,728 | 20,000 | 0.400 | $24,691 | ok (+1.6%) |
| JJ Southern Farm | 1,600 | $88,474 | 8,251 | 0.194 | $17,155 | −26.1%, reduced during year |
| Fine Fare Supermarket | 10,000 | $15,711 | condo unit | 1.000 | $15,711 | ok (+1.6%) |
| Antillana Fresh Meat Market | 3,000 | $37,193 | 9,270 | 0.324 | $12,036 | ok (+1.6%) |
| Sagal Meat Market | 2,500 | $63,849 | 17,600 | 0.142 | $9,067 | −21.4%, reduced during year |
| **Total** | | | | | **$690,411** | |

### Findings and caveats

- **The notice check confirms the method.** The +1.6% gap on most lots is the tax rate change: the notice uses the 2023-24 rate. JJ Southern Farm and Sagal were billed less than their notices because DOF cut their installments during the year, typically from a Tax Commission reduction or an abatement. The final billed amount is used.
- **Key Food:** the store's 15,000 sq ft is more than the building's commercial area (12,810 sq ft), and there are 63 apartments above it. The floor-area split is rough.
- **Food Fair** (5 buildings, 17 storefronts) and **Antillana** (4 buildings) share their lots with other tenants. The floor-area split assumes tax is spread evenly by floor area.
- Whether the store pays this tax depends on its lease: tenants pay it under a net lease, while under a gross lease it is built into the rent. Owner-occupied stores pay it directly.

## Part B: Rent (Rent_j)

### Option 1: DOF estimated gross income (main source)

DOF values commercial buildings (tax class 4) using the income approach, based on the income and expense statements (RPIE) that owners must file each year. Each Notice of Property Value prints the building's estimated gross square footage and estimated gross income.

**What was done**

1. For each lot, the script opened the Notices of Property Value page on the DOF property portal. It found the 2024-25 notice (dated January 2024) and downloaded the PDF. The portal did not block the script, and all 9 notices downloaded automatically.
2. It read the PDF text for tax class, building class, units, market and assessed value, gross sq ft, gross income, expenses, net operating income, cap rates and estimated property tax.
3. Rent per sq ft = estimated gross income ÷ estimated gross sq ft. Store rent = rent per sq ft × store sq ft.
4. It flagged lots where the building-wide figure doesn't represent a supermarket's rent.

**Rent per sq ft from the notices**

| Store | Building class | Rent / sq ft | Usable? |
|---|---|---|---|
| JJ Southern Farm | K1 | $43.13 | yes |
| Sagal Meat Market | K4 | $26.72 | yes |
| Antillana Fresh Meat Market | K1 | $22.84 | yes |
| Food Universe | K1 | $19.15 | yes |
| C-Town (564 Southern Blvd) | K2 | $18.43 | yes |
| C-Town (809 Southern Blvd) | K1 | $17.32 | yes |
| Food Fair Fresh Market | K1 | $113.28 | no: 17 storefronts on the lot, so the figure reflects small-shop rents |
| Key Food | D9 | $29.72 | no: apartment building, so income includes 63 apartments' rents |
| Fine Fare Supermarket | RK | none | no: condo notices show market value only ($6,168,720), no income |

### Option 2: asking rents from Bronx retail listings (partial)

**What was done**

- **LoopNet** returned "Access Denied" (Akamai bot protection), including in Cursor's built-in browser. Per the plan, no attempt was made to get around it.
- **Crexi** loaded in the built-in browser. Its Bronx retail lease search listed 428 properties, and 382 were collected by scrolling each results page. Most show "Undisclosed rate". The browser connection dropped before the individual listing pages could be opened.
- Six South Bronx listings with a disclosed rate were recorded, and one (a former medical office) is marked `exclude`. Of the 5 usable listings, 3 have sq ft. Asking rents are $22 to $65 per sq ft per year, and $35 to $65 for listings on busy corridors.

**Why listings don't set Rent_j yet:** the rule requires at least 5 listings in a store's size group (5,000 sq ft and up, or under 5,000). There is 1 large listing and 2 small ones in the CD2-area ZIP codes. To use listings, add rows by hand to `data/rent/listings/bronx_retail_listings.csv` and rerun `build_rent_j.py`. Step-by-step instructions are in `data/rent/README.md`.

### How Rent_j is chosen

1. Use the store's own notice figure if it is usable.
2. Otherwise, use the listing median × store sq ft if there are at least 5 listings in its size group.
3. Otherwise, use the median notice rent of usable lots in its size group × store sq ft. That is $18.43 for large stores.

Low and high values are the 25th to 75th percentile of listings when there are enough of them, otherwise the lowest and highest rent among the usable notice lots in the size group.

### Results

| Store | Store sq ft | Rent / sq ft used | Rent_j | Low | High | Source | Old (× $27.50) | ReferenceUSA range |
|---|---|---|---|---|---|---|---|---|
| Key Food | 15,000 | $18.43 | $276,450 | $259,800 | $287,250 | large-lot notice median | $412,500 | $100K to $250K |
| Food Fair Fresh Market | 13,000 | $18.43 | $239,590 | $225,160 | $248,950 | large-lot notice median | $357,500 | $100K to $250K |
| Fine Fare Supermarket | 10,000 | $18.43 | $184,300 | $173,200 | $191,500 | large-lot notice median | $275,000 | $10K to $25K |
| Food Universe | 8,000 | $19.15 | $153,200 | $138,560 | $153,200 | own notice | $220,000 | under $10K |
| C-Town (564 Southern Blvd) | 8,000 | $18.43 | $147,440 | $138,560 | $153,200 | own notice | $220,000 | $50K to $100K |
| C-Town (809 Southern Blvd) | 7,500 | $17.32 | $129,900 | $129,900 | $143,625 | own notice | $206,250 | $50K to $100K |
| JJ Southern Farm | 1,600 | $43.13 | $69,008 | $36,544 | $69,008 | own notice | $44,000 | none |
| Antillana Fresh Meat Market | 3,000 | $22.84 | $68,520 | $68,520 | $129,390 | own notice | $82,500 | $10K to $25K |
| Sagal Meat Market | 2,500 | $26.72 | $66,800 | $57,100 | $107,825 | own notice | $68,750 | under $10K |
| **Total** | | | **$1,335,208** | **$1,227,344** | **$1,483,948** | | **$1,886,500** | |

### Findings and caveats

- DOF's figures show supermarket-sized buildings in CD2 earning $17 to $19 per sq ft, about a third below the $27.50 placeholder. Rent_j is 29% lower in total than the old estimate.
- The three large stores without a usable notice of their own (Key Food, Food Fair, Fine Fare) use the median of the three usable large lots. These are the least certain figures and account for over half of total Rent_j.
- The notice figures are DOF estimates for fiscal year 2025 based on owner filings. Listings are 2026 asking rents, which usually run above rents paid after concessions. A long-standing supermarket lease can be below either figure.
- ReferenceUSA's "Rent Expenses" ranges are Data Axle's modeled estimates, and several look implausibly low (for example, under $10K for an 8,000 sq ft supermarket). They are shown for comparison only.
- Whether property tax is included in rent depends on the lease (net vs gross). Check that Tax_j and Rent_j aren't double-counted in the model.

## Files created

### Code

| File | What it does |
|---|---|
| [`code/build_tax_j.py`](../code/build_tax_j.py) | Builds the store-to-lot table, downloads DOF tax bills and PLUTO, and computes the fiscal year 2025 lot tax, store share, Tax_j and the notice check |
| [`code/build_rent_nopv.py`](../code/build_rent_nopv.py) | Finds and downloads each lot's 2024-25 Notice of Property Value and reads its income, sq ft and tax fields (`--skip-download` to reuse saved PDFs) |
| [`code/build_rent_j.py`](../code/build_rent_j.py) | Summarizes listings by area and size group, combines notice, listing, ReferenceUSA and old estimates, and picks Rent_j |

### Tax data (`data/tax/`)

| File | Contents |
|---|---|
| [`data/tax/candidate_store_lots.csv`](../data/tax/candidate_store_lots.csv) | Store, license number, Ag & Markets sq ft, tax lot, lot type (whole lot or condo unit) |
| `data/tax/raw/dof_charges_{bbl}.json` | Every property tax charge row DOF publishes for each lot, unchanged (9 files) |
| [`data/tax/pluto_candidate_lots.csv`](../data/tax/pluto_candidate_lots.csv) | PLUTO floor areas, number of buildings, building class, assessed value |
| [`data/tax/tax_j_cd2_candidate_stores.csv`](../data/tax/tax_j_cd2_candidate_stores.csv) | **Final Tax_j**: lot tax, store share, Tax_j, notice check and flags, one row per store |
| [`data/tax/tax_j_meta.json`](../data/tax/tax_j_meta.json) | Sources, fiscal year, duplicate-handling and store-share rules |
| [`data/tax/README.md`](../data/tax/README.md) | Notes on sources, method and caveats |

### Rent data (`data/rent/`)

| File | Contents |
|---|---|
| `data/rent/nopv/{bbl}_2024-25.pdf` | DOF Notice of Property Value, tax year 2024-25, one per lot (9 files) |
| `data/rent/nopv/{bbl}_2024-25.txt` | Text extracted from each notice |
| [`data/rent/nopv/nopv_links.csv`](../data/rent/nopv/nopv_links.csv) | Notice URL and download status per lot |
| [`data/rent/nopv_income_fy2025.csv`](../data/rent/nopv_income_fy2025.csv) | Parsed notice fields, rent per sq ft, usability flag |
| [`data/rent/listings/bronx_retail_listings.csv`](../data/rent/listings/bronx_retail_listings.csv) | Listing asking rents (Crexi so far; add more by hand) |
| [`data/rent/rent_comps_summary.csv`](../data/rent/rent_comps_summary.csv) | Listing rent per sq ft by area and size group |
| [`data/rent/rent_j_cd2_candidate_stores.csv`](../data/rent/rent_j_cd2_candidate_stores.csv) | **Final Rent_j**: all estimates side by side, Rent_j with low/high and source |
| [`data/rent/README.md`](../data/rent/README.md) | Notes on sources, manual notice download and manual listing steps |

## Sources

- DOF Property Charges Balance, NYC Open Data [`scjx-j6np`](https://data.cityofnewyork.us/City-Government/Property-Charges-Balance/scjx-j6np)
- MapPLUTO, NYC Open Data [`64uk-42ks`](https://data.cityofnewyork.us/City-Government/Primary-Land-Use-Tax-Lot-Output-PLUTO-/64uk-42ks)
- DOF Notices of Property Value, tax year 2024-25, from the [DOF property portal](https://a836-pts-access.nyc.gov/care/search/commonsearch.aspx?mode=persprop)
- Crexi Bronx retail lease listings, seen 2026-09-30
- NYS Ag & Markets retail food store licenses (store sq ft), via `data/stores/large_grocery_stores_cd2.csv`
- ReferenceUSA (Data Axle) "Rent Expenses", via `data/archive/referenceusa/referenceusa_cd2_grocery_download_edited.csv`

## Next steps

- Add listings by hand (Crexi listing pages, LoopNet in a normal browser, broker reports), aiming for at least 5 of 5,000 sq ft or more, then rerun `build_rent_j.py`.
- Decide whether the model treats rent as net or gross of property tax, so Tax_j isn't counted twice.
