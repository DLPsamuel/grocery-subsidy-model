# Rent_j: rent for the 9 CD2 candidate stores

Replaces the unsourced $20-35 per sq ft placeholder. Two data-backed estimates, combined by `code/build_rent_j.py`.

Run order: `python code/build_tax_j.py` (creates the store-to-lot table), `python code/build_rent_nopv.py`, then `python code/build_rent_j.py`.

## Files

| File | Contents |
|---|---|
| `nopv/{bbl}_2024-25.pdf` | DOF Notice of Property Value, tax year 2024-25 (dated January 2024), one per lot |
| `nopv/{bbl}_2024-25.txt` | Text extracted from each notice |
| `nopv/nopv_links.csv` | Notice URL and download status per lot |
| `nopv_income_fy2025.csv` | Parsed notice fields, rent per sq ft, usability flag |
| `listings/bronx_retail_listings.csv` | Asking rents from retail listings (Crexi so far; add more by hand) |
| `rent_comps_summary.csv` | Listing rent per sq ft by area and size group |
| `rent_j_cd2_candidate_stores.csv` | All estimates side by side, proposed `Rent_j` with low/high and source |

## Option 1: DOF estimated gross income (main source)

DOF values commercial buildings (tax class 4) from the rent they earn, using the income and expense statements (RPIE) owners must file each year. Each notice prints the building's estimated gross square footage and estimated gross income.

- `rent_psf_nopv` = estimated gross income / estimated gross sq ft
- `rent_nopv` = `rent_psf_nopv` x store sq ft (Ag & Markets)

Usable for 6 stores. Not usable directly for 3:

- **Key Food**: apartment building (class 2), so income includes 63 apartments' rents.
- **Food Fair**: a 13,000 sq ft supermarket on a lot with 17 storefronts; the lot average ($113/sq ft) reflects small-shop rents.
- **Fine Fare**: condo unit; condo notices show a market value only, no income figures.

For those three, `Rent_j` uses the median notice rent of the usable large lots ($18.43/sq ft) unless there are at least 5 listing comps for their size group.

### Manual download (if the portal blocks the script)

1. Go to https://a836-pts-access.nyc.gov/care/search/commonsearch.aspx?mode=persprop and accept the disclaimer.
2. Search by borough (2 = Bronx), block and lot. Example: 2027630256 is block 2763, lot 256.
3. Open the "Notices of Property Value" tab and click the date on the **2024 - 2025** row (January 2024).
4. Save the PDF as `data/rent/nopv/{BBL}_2024-25.pdf`.
5. Lots: 2027430015, 2027260070, 2027270045, 2027031001, 2027210024, 2027630256, 2027420003, 2027430025, 2026030011.
6. Run `python code/build_rent_nopv.py --skip-download`.

## Option 2: asking rents from listings

- **LoopNet** blocks automated access ("Access Denied"), including the built-in browser.
- **Crexi** loads in a browser. Its Bronx retail lease search listed 428 properties; most say "Undisclosed rate". The 5 South Bronx listings with a disclosed rate were recorded on 2026-09-30 (3 have sq ft). The browser connection dropped before listing pages could be opened, so the file needs more rows before the listing median is used (at least 5 per size group).

### Adding listings by hand

Columns: `source, url, address, zip, sqft, asking_rent_psf_yr, rent_basis, lease_type, floor, date_seen, notes`.

- `rent_basis`: `psf_yr` (default), `psf_mo` ($/sq ft per month), `monthly_total` or `annual_total` (whole-space rent; needs `sqft`).
- Put `exclude` in `notes` to leave a row out (for example offices, medical space, ground leases).
- Ground-floor retail only. Aim for 15 to 30 listings, at least 5 of 5,000 sq ft or more.
- Where to look:
  - **Crexi:** Lease, Retail, "Bronx, NY". Open "Undisclosed rate" listings in ZIP codes 10459, 10474, 10455, 10451, 10456 and 10460; some show rates per space.
  - **LoopNet** in a normal browser.
  - **Broker reports:** Ripco or Cushman & Wakefield Bronx retail reports (use `source = broker_report`).
  - **CoStar:** through a university library, if available.

Then rerun `python code/build_rent_j.py`.

## Caveats

- Notice figures are DOF estimates for fiscal year 2025; listings are 2026 asking rents, usually above rents paid after concessions.
- A long-standing supermarket lease can be well below either figure.
- ReferenceUSA's `Rent Expenses` ranges are Data Axle's modeled estimates, shown for comparison only.
- Whether property tax is included in rent depends on the lease (net vs gross).
