# Property Tax (Tax_j) and Rent (Rent_j), Fiscal Year 2025, v2

Appendix F rows: Tax_j, Rent_j · Stores: the final 9 CD2 candidate stores · Last updated: 2026-09-30

This updates [rent_and_tax_fy2025.md](rent_and_tax_fy2025.md) (v1) using a site check of every store's tax lot in ZoLa and Google Earth. v1 files are left unchanged. All v2 outputs are in `data/tax/v2/` and `data/rent/v2/`.

Fiscal year 2025 = July 1, 2024 to June 30, 2025.

## Summary

- **Tax_j v2 totals \$351,085**, down from \$690,411 in v1. If Food Fair's tax is split by floor area instead of income, the total is \$651,715 (the high end).
- **Rent_j v2 totals \$1,403,475** (range \$1.29M to \$1.59M), up from \$1,335,208.
- **What changed:** each store's share of its lot now comes from how much of the building it actually occupies, based on the site check. v1 divided the Ag & Markets license sq ft by the building's floor area. The same occupied area now feeds both tax and rent.
- **Food Fair** is the biggest change: \$58,408 instead of \$409,408. Its lot has 17 storefronts, and v2 splits the lot's tax by each tenant's share of the lot's income rather than floor area. This is our modeling choice, not a DOF rule (see below).
- **All 9 tax lots were confirmed** in ZoLa, so the lot tax figures are unchanged from v1.
- **Revenue_j is unchanged.** Ag & Markets sq ft stays the store size for revenue. The measurements are saved as extra store attributes.

## Site check (ZoLa and Google Earth, 2026-09-30)

Recorded in [`data/stores/store_site_observations.csv`](../data/stores/store_site_observations.csv).

| Store | Tax lot (BBL) | What the site check found | Measured (Google Earth) |
|---|---|---|---|
| Food Fair (1065 E 163rd St) | 2027420003 | Lot confirmed. Store is the southeast corner of the lot; about 4 other buildings share it. No second floor. | Store's building 11,400 sq ft |
| Key Food (1050 Westchester Ave) | 2027430025 | Full first floor, 5 stories of apartments above. | First floor 15,300; apartment floors 9,200 each |
| Fine Fare (950 Westchester Ave) | 2027031001 (condo unit) | Northeast part of a group of buildings. 3 condo stories sit above the 10,000 sq ft store only. An adjacent 2-story strip mall (12,200 sq ft) is partly under a 12-story apartment building (17,500 sq ft footprint, 7,200 sq ft of it over the strip mall). | Store 10,000 |
| Food Universe (724 Hunts Pt Ave) | 2027630256 | Occupies the whole lot and building. | 10,300 |
| C-Town (564 Southern Blvd) | 2026030011 | Full first floor. The second floor extends across the strip mall and is likely not theirs. | Building 13,000 |
| C-Town (809 Southern Blvd) | 2027210024 | Lot confirmed (PLUTO lists it as 823 Southern Blvd). No second floor. A shop on either side. | Building 12,600; store about 9,200 |
| JJ Southern Farm (1046 Southern Blvd) | 2027430015 | Building on the front half of the lot; the back half is trees. The second floor looks uninhabitable (former bank). | Building 6,700 |
| Antillana (1025 Westchester Ave) | 2027260070 | About half the building. No second story. | Store 6,000 |
| Sagal (1091 Southern Blvd) | 2027270045 | Half the lot is green space. The second floor extends across the whole strip mall. | Store 2,500 |

## What each square footage source measures

| Source | What it measures | Reference |
|---|---|---|
| **DOF / PLUTO building area** (`bldgarea`) | Total gross floor area of all structures on the lot, all floors, measured from the outside walls, including halls, stairwells and elevator shafts. Not tied to any occupant. Commercial and retail area are the parts of that total used for those purposes. Condo units are net sq ft from the condo declaration. | [PLUTO data dictionary](https://www.nyc.gov/assets/planning/download/pdf/data-maps/open-data/pluto_datadictionary.pdf) |
| **Ag & Markets** (`square_footage`) | "The square footage of the entire physical location of the licensed entity." Reported by the store on its license. | [NY Open Data 9a8c-vfzj](https://data.ny.gov/Economic-Development/Retail-Food-Stores/9a8c-vfzj); data dictionary saved at [`data/stores/NYSDAM_RetailFoodStores_DataDictionary.pdf`](../data/stores/NYSDAM_RetailFoodStores_DataDictionary.pdf) |
| **Google Earth** (site check) | Roof outline traced on satellite imagery. Includes walls and overhangs; can't see interior walls or count floors. | Team measurements |

### How close the measurements are

Where a Google Earth measurement and DOF describe the same space:

| Store | Google Earth | DOF | Difference |
|---|---|---|---|
| Food Universe (whole building) | 10,300 | 9,800 | +5% |
| C-Town 564 (ground floor) | 13,000 | 10,000 per floor | +30% (also larger than the 12,500 sq ft lot) |
| JJ Southern Farm (building) | 6,700 | 8,251 | −19% |
| C-Town 809 (building) | 12,600 | 16,500 | −24% |
| Key Food (first floor) | 15,300 | 12,810 commercial; lot is 14,271 | +19% vs commercial area; +7% larger than the lot |
| Key Food (whole building) | 15,300 + 5 × 9,200 = 61,300 | 67,339 | −9% |

Google Earth comes within 5–30% of DOF in both directions. Ag & Markets compared with DOF ranges from −81% (JJ Southern Farm, 1,600 vs an 8,251 sq ft building) to +17% (Key Food, 15,000 vs 12,810 commercial).

### Which one v2 uses

The tax share divides the store's area by DOF's building area, so the store's area should be measured the same way where possible:

- **Store fills a space DOF defines** (whole building, ground floor, condo unit): use DOF's figure.
- **Store shares a floor with other tenants:** use the site-check measurement or observed fraction.
- **JJ Southern Farm and Sagal:** use Ag & Markets sq ft, as decided in review. Sagal's measurement matches Ag & Markets exactly.

Revenue stays on Ag & Markets sq ft, since the revenue method was built on it.

## Occupied area and share per store

Rule: `store_share_area = min(occupied sq ft / building sq ft, 1)`, where building sq ft is PLUTO `bldgarea`, or the condo unit's own area for Fine Fare. Rent = rent per sq ft × occupied sq ft.

| Store | Basis | Occupied sq ft | Building sq ft | Share v1 | Share v2 (floor area) |
|---|---|---|---|---|---|
| Key Food | DOF commercial area (full first floor) | 12,810 | 67,339 | 0.223 | 0.190 |
| Food Fair | measured (store's building) | 11,400 | 22,000 | 0.591 | 0.518 (income share 0.084 used) |
| Fine Fare | 10,000 of the retail condo unit | 10,000 | 19,300 | 1.000 | 0.518 |
| Food Universe | whole building | 9,800 | 9,800 | 0.816 | 1.000 |
| C-Town (564 Southern Blvd) | DOF retail area (ground floor) | 10,000 | 20,000 | 0.400 | 0.500 |
| C-Town (809 Southern Blvd) | measured (shops on either side) | 9,200 | 16,500 | 0.455 | 0.558 |
| JJ Southern Farm | Ag & Markets | 1,600 | 8,251 | 0.194 | 0.194 |
| Antillana | half the building | 4,635 | 9,270 | 0.324 | 0.500 |
| Sagal | Ag & Markets (confirmed) | 2,500 | 17,600 | 0.142 | 0.142 |

Notes:

- **Key Food:** a share computed only from your measurements would be 0.25 (15,300 ÷ 61,300). DOF's commercial area gives 0.190. A store sq ft is usually worth more than an apartment sq ft, so 0.19 is probably a lower bound.
- **Fine Fare:** v1 gave it the whole condo unit's bill (share 1). The retail condo unit is 19,300 sq ft and the store is 10,000 of it. The unit's bill is small (\$15,711) because of a 421-a exemption (new construction, built 2006), which cuts its taxable value from \$2.76M to \$146K. That exemption may end, depending on its benefit schedule.

## Food Fair: splitting the tax by income

**What DOF does.** DOF values stores and other commercial (class 4) property from income. From DOF's [Determining your market value](https://www.nyc.gov/site/finance/property/property-determining-your-market-value.page): "Most other real property, such as office buildings, factories, stores, hotels, and lofts. The Department of Finance uses your property's income earning potential and expenses. Estimated annual income is based in part on information you provide on the annual Real Property Income and Expense (RPIE) Filing." Food Fair's own notice ([`data/rent/nopv/2027420003_2024-25.txt`](../data/rent/nopv/2027420003_2024-25.txt)) says: "We estimate your property's market value using the income approach. Market value is determined by dividing the net operating income by the overall capitalization rate." The tax is then a percentage of that value.

**What DOF does not do.** DOF bills the whole lot and does not split the tax among tenants. How tenants share it is set by each lease, and commercial leases usually use each tenant's share of floor area. **Splitting by income is our modeling choice.**

**Why income for Food Fair.** The tax follows the lot's value, and the value follows its income, so each tenant's share of the income is a fair measure of how much of the tax it causes. DOF estimates the lot's income at \$2,492,183 on 22,000 sq ft (\$113 per sq ft), across 17 storefronts. If Food Fair uses 11,400 sq ft at a supermarket rent (\$18.43 per sq ft, about \$210K), the other 16 shops would bring in about \$2.28M on about 10,600 sq ft. A floor-area split would charge Food Fair 52% of a tax driven mostly by the small shops' rents.

**Where the lot's income comes from.** It's the "Estimated Gross Income" on the 2024-25 notice, stored in [`data/rent/nopv_income_fy2025.csv`](../data/rent/nopv_income_fy2025.csv) (column `nopv_gross_income`) and read from `data/rent/nopv/2027420003_2024-25.pdf`.

**Calculation.** Income share = Food Fair Rent_j v2 ÷ lot income = \$210,102 ÷ \$2,492,183 = 0.0843. Tax_j = \$692,855 × 0.0843 = **\$58,408**. The floor-area split (\$359,038) is reported as `Tax_j_high`. Food Fair's rent is itself an estimate (the median DOF rent for supermarket-sized buildings), so the income share inherits that uncertainty.

The income share is calculated for every store, for comparison. For stores whose rent comes from their own lot's notice, it equals the floor-area share, because their rent per sq ft is the lot average. It differs only for Food Fair and Key Food. Key Food's is 0.118, but its lot income includes 63 apartments, so v2 keeps the floor-area share for Key Food.

## Results

### Tax_j (fiscal year 2025)

| Store | Lot tax | Share v1 | Tax_j v1 | Share v2 | Tax_j v2 | Method |
|---|---|---|---|---|---|---|
| Key Food | \$472,669 | 0.223 | \$105,311 | 0.190 | \$89,902 | floor area |
| Food Universe | \$60,962 | 0.816 | \$49,764 | 1.000 | \$60,962 | floor area |
| Food Fair | \$692,855 | 0.591 | \$409,408 | 0.084 | \$58,408 (high \$359,038) | income |
| C-Town (809 Southern Blvd) | \$104,002 | 0.455 | \$47,269 | 0.558 | \$57,991 | floor area |
| C-Town (564 Southern Blvd) | \$61,728 | 0.400 | \$24,691 | 0.500 | \$30,864 | floor area |
| Antillana | \$37,193 | 0.324 | \$12,036 | 0.500 | \$18,597 | floor area |
| JJ Southern Farm | \$88,474 | 0.194 | \$17,155 | 0.194 | \$17,155 | floor area |
| Sagal | \$63,849 | 0.142 | \$9,067 | 0.142 | \$9,067 | floor area |
| Fine Fare | \$15,711 | 1.000 | \$15,711 | 0.518 | \$8,140 | floor area |
| **Total** | | | **\$690,411** | | **\$351,085** (high \$651,715) | |

The lot tax checks against the notices are unchanged from v1: 7 lots are within 1.6%, and JJ Southern Farm and Sagal were billed less because DOF reduced their installments during the year.

### Rent_j

Same rule as v1: the store's own DOF notice rent per sq ft where usable, otherwise the median of usable supermarket-sized lots (\$18.43). The difference is that rent now uses occupied sq ft. Listings are still too few to use (5 usable).

| Store | Ag & Markets sq ft | Occupied sq ft | Rent / sq ft | Rent_j v1 | Rent_j v2 | Low | High |
|---|---|---|---|---|---|---|---|
| Key Food | 15,000 | 12,810 | \$18.43 (median) | \$276,450 | \$236,088 | \$221,869 | \$245,311 |
| Food Fair | 13,000 | 11,400 | \$18.43 (median) | \$239,590 | \$210,102 | \$197,448 | \$218,310 |
| Food Universe | 8,000 | 9,800 | \$19.15 (own lot) | \$153,200 | \$187,670 | \$169,736 | \$187,670 |
| Fine Fare | 10,000 | 10,000 | \$18.43 (median) | \$184,300 | \$184,300 | \$173,200 | \$191,500 |
| C-Town (564 Southern Blvd) | 8,000 | 10,000 | \$18.43 (own lot) | \$147,440 | \$184,300 | \$173,200 | \$191,500 |
| C-Town (809 Southern Blvd) | 7,500 | 9,200 | \$17.32 (own lot) | \$129,900 | \$159,344 | \$159,344 | \$176,180 |
| Antillana | 3,000 | 4,635 | \$22.84 (own lot) | \$68,520 | \$105,863 | \$105,863 | \$199,908 |
| JJ Southern Farm | 1,600 | 1,600 | \$43.13 (own lot) | \$69,008 | \$69,008 | \$36,544 | \$69,008 |
| Sagal | 2,500 | 2,500 | \$26.72 (own lot) | \$66,800 | \$66,800 | \$57,100 | \$107,825 |
| **Total** | | | | **\$1,335,208** | **\$1,403,475** | **\$1,294,304** | **\$1,587,212** |

The median for supermarket-sized buildings stays at \$18.43, because JJ Southern Farm and Antillana are still under 5,000 occupied sq ft.

### Revenue_j

Unchanged. Revenue for Food Universe and JJ Southern Farm was estimated as Ag & Markets sq ft × \$360 per sq ft, and that stays as it is: the measured and DOF areas include back rooms and space outside the sales operation, so they aren't comparable with the sq ft the \$360 rate was built on. The measurements are kept as store attributes in `data/stores/store_site_observations.csv`.

## Caveats

- Google Earth measurements are within about 5–30% of DOF figures. Shares based on them (Food Fair, C-Town 809) carry that uncertainty.
- Food Fair's income split depends on its estimated rent. If its actual rent is higher, its share and tax rise in proportion.
- Whether a store pays property tax directly depends on its lease (net vs gross). If a lease is gross, the tax is already inside the rent, so the model shouldn't count both.
- Fine Fare's 421-a exemption keeps its tax low; the full tax would be much higher if the exemption ends.

## Lot map

[`data/tax/v2/lot_check_map_v2.html`](../data/tax/v2/lot_check_map_v2.html) shows each tax lot outlined on satellite imagery with a pin at the store's Ag & Markets address. Each lot is labeled with the share used. Clicking a lot or a store in the sidebar shows occupied sq ft, both shares, lot tax, Tax_j, Rent_j, the site-check note, and links to Google Maps and ZoLa. Open the file in a web browser (it loads Leaflet and the imagery from the internet). Fine Fare's outline is the whole condo building (billing lot 2027037501), since MapPLUTO draws condos that way.

## Files

### Code (new)

| File | What it does |
|---|---|
| [`code/build_store_occupancy.py`](../code/build_store_occupancy.py) | Combines the site check, PLUTO areas and Fine Fare's condo unit area into one occupied area and floor-area share per store, with the sq ft source comparison |
| [`code/build_rent_j_v2.py`](../code/build_rent_j_v2.py) | Rent_j with occupied sq ft (reuses the helpers in `build_rent_j.py`) |
| [`code/build_tax_j_v2.py`](../code/build_tax_j_v2.py) | Tax_j with the floor-area share, the income share, and the Food Fair income split |
| [`code/build_lot_map.py`](../code/build_lot_map.py) | Downloads lot outlines from MapPLUTO and builds the lot map (`--skip-download` reuses the saved outlines) |

### Data (new)

| File | Contents |
|---|---|
| [`data/stores/store_site_observations.csv`](../data/stores/store_site_observations.csv) | Site check per store: lot confirmed, occupancy note, second floor, Google Earth measurements, occupancy basis |
| [`data/tax/v2/store_occupancy_v2.csv`](../data/tax/v2/store_occupancy_v2.csv) | Ag & Markets, Google Earth and DOF areas side by side; occupied sq ft; floor-area share; percent differences |
| [`data/rent/v2/rent_j_cd2_candidate_stores_v2.csv`](../data/rent/v2/rent_j_cd2_candidate_stores_v2.csv) | **Final Rent_j v2**, with v1 and the old \$27.50 estimate for comparison |
| [`data/tax/v2/tax_j_cd2_candidate_stores_v2.csv`](../data/tax/v2/tax_j_cd2_candidate_stores_v2.csv) | **Final Tax_j v2**: both shares, share method, Tax_j, Tax_j_high, v1 values, notice check and flags |
| [`data/tax/v2/tax_j_v2_meta.json`](../data/tax/v2/tax_j_v2_meta.json) | Sources, share rules, income-split rationale, references and totals |
| [`data/tax/v2/lot_polygons_v2.geojson`](../data/tax/v2/lot_polygons_v2.geojson) | Lot outlines from MapPLUTO with store fields |
| [`data/tax/v2/lot_check_map_v2.html`](../data/tax/v2/lot_check_map_v2.html) | Lot map |

v1 inputs read, not changed: `data/tax/candidate_store_lots.csv`, `data/tax/pluto_candidate_lots.csv`, `data/tax/tax_j_cd2_candidate_stores.csv`, `data/rent/nopv_income_fy2025.csv`, `data/rent/nopv/2027031001_2024-25.txt`, `data/rent/rent_j_cd2_candidate_stores.csv`, `data/rent/listings/bronx_retail_listings.csv`, `data/referenceusa/referenceusa_cd2_grocery_download_edited.csv`, `data/stores/large_grocery_stores_cd2.csv`.

## How to rerun

```
python code/build_store_occupancy.py
python code/build_rent_j_v2.py
python code/build_tax_j_v2.py
python code/build_lot_map.py
```

To change a store's occupancy, edit its row in `data/stores/store_site_observations.csv` (`occupancy_basis` and `occupancy_value`) and rerun all four. To use a floor-area split for Food Fair instead, remove its license from `INCOME_SPLIT_LICENSES` in `build_tax_j_v2.py`.
