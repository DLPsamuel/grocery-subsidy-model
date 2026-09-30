# Store Sales (Revenue_j): Central Estimate from the Economic Census, v2

Owner: Rahul · Appendix F rows: Revenue_j, Q_j (Lead R) · Last updated: 2026-09-30

v2 of the Census-based Revenue_j. [v1](revenue_census_estimate.md) sorted Bronx stores into classes by name only, and two of its variants divided one set of stores' sales by a different set of stores' square footage. v2 classifies each store using its **USDA SNAP store type** and its **Ag & Markets establishment codes**, and every rate divides a class's Census sales by the square footage of the stores in **that same class**.

**Recommended rate: $801 per sq ft per year ($15.41 per week), 2024 dollars**, range $698–$845. The 9 CD2 stores total **$55.0M, 49% of CD2 grocery spending**. v1 gave $829 and $56.8M.

## Files

- Code: [`code/build_revenue_census_v2.py`](../code/build_revenue_census_v2.py). Run `python code/build_revenue_census_v2.py` (needs `CENSUS_API_KEY` in `.env`; about 20 seconds).
- Output folder: [`data/revenue_census_estimate/v2/`](../data/revenue_census_estimate/v2/)

| File | Content |
|---|---|
| `raw/ecn_2022_bronx_v2.csv` | Every Census row queried: establishments, sales, employees, payroll |
| `bronx_agmarkets_snap_linked_v2.csv` | One row per Bronx Ag & Markets store (2023 archive and current list): establishment codes, bakery flag, SNAP match (method, distance, SNAP name, SNAP type), name category, Census class, class source, exclude reason, recorded / imputed sq ft |
| `bronx_class_counts_v2.csv` | Per class and vintage: Ag & Markets stores and sq ft against Census establishments and sales, and each side's class split |
| `bronx_sales_per_sqft_census_v2.csv` | One row per variant, with `numerator_definition` and `denominator_definition` written out, the dollar amounts, store counts and rates |
| `revenue_j_census_v2_cd2_candidate_stores.csv` | The 9 CD2 stores: recommended Revenue_j, low / high, class-rate and pooled versions, Q_j, share of M, and v1 / ReferenceUSA / FMI for comparison |
| `revenue_census_v2_meta.json` | API calls, CPI values, SNAP type map, match rules, exclusion and class-source counts, sq ft by establishment code, split check, totals |

New reference file: [`data/stores/NYSDAM_RetailFoodStoresEstablishmentTypeCodes.pdf`](../data/stores/NYSDAM_RetailFoodStoresEstablishmentTypeCodes.pdf), the Ag & Markets establishment-code sheet, from data.ny.gov.

**Inputs used (not modified):**
- Ag & Markets 2023 archive and current Bronx list (`data/stores/agmarkets_retail_food_stores_archive_2023.csv`, `data/stores/agmarkets_bronx_county.csv`)
- USDA SNAP retailers, Bronx, 2005–2025 (`data/stores/snap_bronx_county.csv`)
- The CD2 stores' SNAP types (`data/stores/agmarkets_bronx_cd2_snap_eligibility.csv`)
- Store sq ft, basket price, ReferenceUSA and FMI (`data/revenue/revenue_j_cd2_candidate_stores.csv`)
- v1 output (`data/revenue_census_estimate/revenue_j_census_cd2_candidate_stores.csv`)
- Market size M (`data/bls/cd2_market_size_M_northeast_cd2weighted.csv`)

**Reused code:** from v1, `census_request`, `classify` and `normalize_name`; from `link_agmarkets_snap.py`, the address normalizers and `street_similarity`; from `build_p_j.py`, `cpi_year`.

## What changed from v1

| | v1 | v2 | Why |
|---|---|---|---|
| Store class | Store name only | SNAP store type; name only when a store has no SNAP match | SNAP types are assigned by USDA from each store's stock and sales |
| Establishment codes | Gate only (A kept; D, E, H, I, L dropped) | Same gate, plus the bakery flag (B) as an imputation group and a reported diagnostic | The codes describe licensed activities, not store formats |
| Convenience numerator | Suppressed (445131 = 0); only the 4451 total was usable | 44513 employer ($214M) and nonemployer ($20.9M) are both published | Allows a separate convenience class |
| Nonemployer sales | Added to 4451 and 4452 only | Split by class: NES 445110 = NES 4451 − NES 44513 | Every class numerator is employer + nonemployer, matching Ag & Markets, which lists both |
| Employer-only variant | Numerator without owner-run stores, denominator with them | **Dropped** | Ag & Markets can't identify owner-run stores, so it can't be matched |
| 445110-only variant | Census 445110 (includes bodegas) over stores minus deli/grocery names | 445110 sales over 445110-class stores | v1's version removed bodega sq ft but kept bodega sales (biased high) |
| Imputation groups | Name category | Class × SNAP type (or name category) × bakery flag | Finer groups |

## Method

$$
r_{c,2024} = \frac{\text{Census Bronx sales}_{c,2022}\ (\text{employer + nonemployer})}{\sum \text{sq ft of Ag \& Markets stores in class } c} \times \frac{\text{CPI}_{2024}}{\text{CPI}_{2022}}
$$

### Step 1: Census numerators by class

| Class (NAICS 2022) | Employer sales | Nonemployer sales | **Total** | Employer est. | Nonemployer est. |
|---|---|---|---|---|---|
| 445110 Supermarkets and other grocery | $3,425.2M | $89.4M | **$3,514.6M** | 1,125 | 1,579 |
| 44513 Convenience retailers | $213.9M | $20.9M | **$234.8M** | 285 | 209 |
| 4452 Specialty food | $295.6M | $37.4M | **$333.0M** | 219 | 706 |
| 4451 total (445110 + 44513) | $3,639.0M | $110.3M | $3,749.4M | 1,410 | 1,788 |

Sources are `api.census.gov/data/2022/ecnbasic` (Economic Census, businesses with paid employees) and `api.census.gov/data/2022/nonemp` (Nonemployer Statistics, owner-run businesses). Nonemployer 445110 isn't published for the county, so it is NES 4451 minus NES 44513. The 44513 employer total includes vending-machine operators (445132), which are published as 0 for the Bronx.

### Step 2: Establishment-code gate

From the code sheet, the codes are A store, B bakery, C food manufacturer, D food warehouse, E beverage plant, H wholesale manufacturer, I refrigerated warehouse, J multiple operations, K vehicle, and L produce refrigerated warehouse.

- Keep stores with code A. Drop any store with D, E, H, I or L.
- The J prefix in the 2023 archive is stripped first.
- v1's name exclusions still apply to every store, whatever its SNAP type: pharmacies, dollar and general-merchandise stores, gas stations, online/warehouse operations, and food service or non-food retail. Gas-station mini-marts, for example, are "Convenience Store" in SNAP but a different industry in the Census (457110). Names that also say deli, grocery, food or supermarket are kept.
- Locations over 100,000 sq ft are dropped as warehouses.

2023 archive outcomes: 2,275 kept; 168 general merchandise or dollar stores; 75 pharmacies; 36 gas stations; 35 warehouse or wholesale codes; 23 food service or non-food; 5 online or warehouse.

### Step 3: Link to SNAP

- **SNAP snapshot:** Bronx SNAP retailers active at any point in 2022 (authorized on or before 2022-12-31, and no end date or an end date on or after 2022-01-01). That's 2,287 records. Duplicates of the same name and address are dropped, keeping the latest authorization. For the current-list variant, currently authorized retailers are used instead.
- **Match 1, address:** same house number and ZIP, street-name similarity at least 0.4. This is the rule from `link_agmarkets_snap.py`, vectorized.
- **Match 2, spatial:** the nearest SNAP retailer within 50 m of the Ag & Markets point that **shares a non-generic name word**. Common words such as deli, grocery, food, market, inc and corp are ignored. The Ag & Markets DBA name and legal entity name are both compared to the SNAP name.
- **Change from the plan:** the plan also accepted any SNAP retailer within 15 m without a name check. A sample audit found those matches were mostly wrong neighbours: a smoke shop matched to an ALDI, a vape shop to a seafood store, a deli to a Dollar Tree. Bronx storefronts are adjacent, so that rule was removed.

2023 results: 1,869 address matches, 97 spatial matches, 651 unmatched (all rows, before the gate).

### Step 4: Assign a Census class

| Rule | Class |
|---|---|
| SNAP Supermarket, Super Store, Large / Medium / Small Grocery Store | 445110 |
| SNAP Convenience Store | 44513 |
| SNAP Combination Grocery/Other (non-grocery names already excluded in step 2) | 44513 |
| SNAP Meat/Poultry, Seafood, Fruits/Veg, Bakery Specialty | 4452 |
| SNAP Farmers' Market, Food Buying Co-op, Military Commissary | excluded |
| No SNAP match: v1 name category supermarket or other grocery | 445110 |
| No SNAP match: v1 name category convenience or deli | 44513 |
| No SNAP match: v1 name category specialty | 4452 |

Kept stores, 2023 archive:

| Class | From SNAP type | From name | Total |
|---|---|---|---|
| 445110 | 828 | 172 | 1,000 |
| 44513 | 867 | 305 | 1,172 |
| 4452 | 69 | 34 | 103 |
| **All** | **1,764 (78%)** | **511 (22%)** | **2,275** |

### Step 5: Square footage

- Values under 100 sq ft count as missing.
- Missing sq ft = median recorded sq ft among kept stores in the same class × SNAP type (or name category) × bakery flag.
- If a group has fewer than 5 recorded values, the group widens to class × bakery flag, then to class alone.
- The group used is recorded in `impute_group`.

### Step 6: Inflation

BLS CPI food at home, New York area (`CUURS12ASAF11`), annual averages: 2022 = 303.153, 2024 = 318.094, factor **1.0493**.

### Step 7: Class split check

If the Ag & Markets class split is close to the Census split, the per-class rates can be trusted. If it isn't, only pooled classes are matched. The script compares 445110's share of grocery + convenience stores on each side, with a tolerance of 15 percentage points.

| Class | Ag & Markets stores (2023) | Census establishments | Ag & Markets share of 4451 | Census share of 4451 |
|---|---|---|---|---|
| 445110 | 1,000 | 2,704 | **46%** | **85%** |
| 44513 | 1,172 | 494 | 54% | 15% |
| 4452 | 103 | 925 | – | – |

**The split check fails (a gap of 39 points), so the pooled 4451 rate is recommended.**

- **Grocery vs convenience:** SNAP calls most Bronx bodegas "Convenience Store". The Census defines convenience retailers narrowly (chain-style convenience stores) and counts independent bodegas as grocery stores (445110). The pooled rate doesn't depend on where that line is drawn, because both sides include all grocery and convenience stores.
- **Specialty:** the Census counts 925 specialty-food businesses (706 of them owner-run: market stalls, home-based businesses), but only 103 Ag & Markets stores are typed specialty. SNAP types many meat and produce markets as groceries; Antillana and Sagal, for example, are "Large Grocery Store". The specialty rate ($2,206) is not usable either.

### Step 8: Apply to the 9 stores

- Each store's class comes from its own SNAP type. Key Food, Food Fair and C-Town (564) are Super Store; Fine Fare, Food Universe, C-Town (809) and JJ Southern Farm are Supermarket; Antillana and Sagal are Large Grocery Store. So all 9 are class 445110.
- Revenue_j = sq ft × the recommended rate (pooled 4451 for 445110 and 44513 stores). Q_j = Revenue_j ÷ p_j.
- Low and high come from the pooled family of variants: pooled, all-food, pooled current list, and pooled known-sq-ft-only.

## How each variant is built

Every variant uses the same Census classes in the numerator as store classes in the denominator. Dollar amounts are 2022; rates are shown in 2024 dollars.

| Variant | Numerator (Census 2022, employer + nonemployer) | Denominator (Ag & Markets stores in the same classes) | Stores / sq ft | $/sq ft/yr (2024) | $/sq ft/wk |
|---|---|---|---|---|---|
| **pooled_4451 (recommended)** | 445110 + 44513 = $3,749.4M | 2023 archive; classes 445110 + 44513; recorded + imputed sq ft | 2,172 / 4.91M | **$801** | **$15.41** |
| central (class 445110) | 445110 = $3,514.6M | 2023 archive; class 445110 only; recorded + imputed | 1,000 / 3.53M | $1,044 | $20.08 |
| all_food_445 | 445110 + 44513 + 4452 = $4,082.4M | 2023 archive; all three classes; recorded + imputed | 2,275 / 5.07M | $845 | $16.25 |
| convenience_44513 | 44513 = $234.8M | 2023 archive; class 44513; recorded + imputed | 1,172 / 1.38M | $179 | $3.44 |
| specialty_4452 | 4452 = $333.0M | 2023 archive; class 4452; recorded + imputed | 103 / 0.16M | $2,206 | $42.43 |
| current_list | 445110 = $3,514.6M | Current Ag & Markets list with currently authorized SNAP; class 445110 | 844 / 3.44M | $1,073 | $20.63 |
| known_sqft_only | 445110 × 787 / 1,000 (share of class stores with recorded sq ft) = $2,766.0M | 2023 archive; class 445110; recorded sq ft only | 787 / 3.15M | $923 | $17.75 |
| pooled_current_list | 445110 + 44513 = $3,749.4M | Current list with currently authorized SNAP; classes 445110 + 44513 | 1,892 / 4.74M | $831 | $15.98 |
| pooled_known_sqft_only | (445110 + 44513) × 1,608 / 2,172 = $2,775.8M | 2023 archive; classes 445110 + 44513; recorded sq ft only | 1,608 / 4.17M | $698 | $13.42 |

**Reading the table**
- The per-class variants (central, convenience_44513, specialty_4452, current_list, known_sqft_only) are matched by definition, but they are **distorted by the class split** described in step 7. Central is too high and convenience too low, because bodega sales sit in the Census grocery numerator while many bodega square feet sit in the convenience denominator.
- The pooled variants (pooled_4451, all_food_445, pooled_current_list, pooled_known_sqft_only) are robust to that split, and they set the recommended rate and its range: **$698–$845**.
- The known-sq-ft-only variants assume stores with no recorded sq ft have average sales. They are probably smaller, so these rates are biased low; they are the bottom of the range.

## Establishment codes as a signal

Kept stores in the 2023 archive, by code (groups with at least 5 stores):

| Codes | Stores | Median recorded sq ft | Share in class 445110 |
|---|---|---|---|
| A (store only) | 277 | 800 | 33% |
| AC (store + food preparation) | 1,936 | 1,200 | 45% |
| ABC (+ in-store bakery) | 44 | 7,000 | 73% |
| ABCK (+ vehicle) | 6 | 7,500 | 67% |
| ACK | 8 | 1,100 | 88% |

Almost every store is AC, so the codes can't separate bodegas from grocers. The bakery flag (B) is a strong sign of a full supermarket: a median of 7,000 sq ft, and 73% are SNAP grocery types. It's used as an imputation group. The gate (A only; no warehouse, plant or wholesale codes) remains the main use of the codes.

## Results

### Revenue_j for the 9 CD2 stores (2024 dollars)

| Store | Sq ft | **v2 (pooled $801)** | Low ($698) | High ($845) | Class rate ($1,044) | Q_j (v2) | v1 ($829) | ReferenceUSA 2024 |
|---|---|---|---|---|---|---|---|---|
| Key Food | 15,000 | **$12.02M** | $10.47M | $12.68M | $15.66M | 432,925 | $12.43M | $8.03M |
| Food Fair Fresh Market | 13,000 | **$10.42M** | $9.07M | $10.99M | $13.58M | 359,758 | $10.77M | $8.03M |
| Fine Fare Supermarket | 10,000 | **$8.01M** | $6.98M | $8.45M | $10.44M | 264,248 | $8.29M | $0.62M |
| Food Universe | 8,000 | **$6.41M** | $5.58M | $6.76M | $8.35M | 214,133 | $6.63M | – |
| C-Town (564 Southern Blvd) | 8,000 | **$6.41M** | $5.58M | $6.76M | $8.35M | 222,380 | $6.63M | $2.88M |
| C-Town (809 Southern Blvd) | 7,500 | **$6.01M** | $5.24M | $6.34M | $7.83M | 208,501 | $6.22M | $3.09M |
| Antillana Fresh Meat Market | 3,000 | **$2.40M** | $2.09M | $2.54M | $3.13M | 83,040 | $2.49M | $0.82M |
| Sagal Meat Market | 2,500 | **$2.00M** | $1.75M | $2.11M | $2.61M | 69,188 | $2.07M | $0.30M |
| JJ Southern Farm Fruit | 1,600 | **$1.28M** | $1.12M | $1.35M | $1.67M | 44,283 | $1.33M | – |
| **Total** | | **$54.96M** | $47.88M | $57.97M | $71.64M | | $56.84M | $23.78M* |

\* 7 stores with a 2024 ReferenceUSA record.

### Check against market size

CD2 households spend **$113.0M** a year on groceries (M, ACS 2024, NYC-scaled).

| Estimate | 9-store total | Share of M |
|---|---|---|
| ReferenceUSA (7 stores) | $23.8M | 21% |
| v2 low | $47.9M | 42% |
| **v2 recommended (pooled)** | **$55.0M** | **49%** |
| v1 central | $56.8M | 50% |
| v2 high | $58.0M | 51% |
| FMI national | $69.9M | 62% |
| v2 class rate (not recommended) | $71.6M | 63% |

## Findings

1. **Once numerators and denominators are matched, the Bronx rate is about $801 per sq ft per year**, close to v1's $829. v1's central estimate was already roughly matched (its numerator and denominator both covered grocery + convenience). The small drop comes from SNAP moving some stores between classes and from the finer imputation groups.
2. **The range narrows** from v1's $719–$1,092 to **$698–$845**. v1's top end ($1,092) came from the mismatched 445110 variant.
3. **A separate supermarket rate can't be matched from these sources.** SNAP and the Census draw the grocery/convenience line in different places: 46% vs 85% of stores are grocery. Rates for the grocery class ($1,044) and convenience class ($179) are therefore distorted in opposite directions. The same goes for specialty food.
4. **The bakery code (B) marks full supermarkets** (median 7,000 sq ft). It's useful for imputation, but too rare (50 stores) to define a class.
5. **For the model:** v2 lowers the 9-store total by 3% relative to v1 ($55.0M vs $56.8M). It stays about 2.3× ReferenceUSA, so the conclusions from v1 hold: Fine Fare is about $8M, not $0.6M, and Q_j is 1.3–2.3× higher than under ReferenceUSA for most supermarkets.

## Assumptions and caveats

1. **SNAP types are not Census industries.** USDA classifies by stock and sales for SNAP rules; the Census classifies by primary activity. The mapping is only reliable at the pooled 4451 level (step 7).
2. **Combination Grocery/Other** stores that survive the name exclusions are treated as bodegas (44513). Only the pooled rate is used, so this choice doesn't affect the recommended rate.
3. **Nonemployer split.** NES 445110 is derived as NES 4451 − NES 44513. Nonemployers are 3% of 4451 sales.
4. **Spatial matching** requires a shared name word within 50 m. Genuine matches where the store's DBA and legal names share no word with the SNAP name are missed; those stores fall back to name rules.
5. **22% of kept stores are classified by name** because they have no SNAP match. In the pooled rate this only matters for deciding whether a store is grocery/convenience or specialty.
6. **One rate for all formats.** The pooled rate averages supermarkets and bodegas. Supermarkets probably sell more per sq ft, so it likely understates Key Food and Food Fair. The matched class rate that could fix this isn't reliable (finding 3).
7. **Whole-location sq ft, imputation, vintage and inflation caveats are the same as v1.** Ag & Markets sq ft covers the whole licensed location. The 2022 Census is paired with the 2023 Ag & Markets archive. The CPI adjusts prices only.

## Next steps

- Team decision: use v2's pooled rate ($801/sq ft/yr) as the main Revenue_j, with $698–$845 as the sensitivity range and ReferenceUSA as an outside low case.
- A supermarket-specific rate would need data that splits sales by store size in the Bronx, for example the Economic Census tables of establishments by sales size class (state level only) or store-level data (Advan/SafeGraph, NielsenIQ).
