# Store Sales (Revenue_j), Baskets Sold (Q_j) and Rent (Rent_j)

Owner: Rahul · Appendix F rows: Revenue_j, Q_j (Lead R); Rent_j (second source) · Last updated: 2026-09-29

**Files**
- Code: [`code/build_revenue_j.py`](../code/build_revenue_j.py)
- Output: [`data/revenue/revenue_j_cd2_candidate_stores.csv`](../data/revenue/revenue_j_cd2_candidate_stores.csv) (Revenue_j and Q_j, one row per store)
- Sales by year, 2020–2024: [`data/revenue/referenceusa_sales_by_year.csv`](../data/revenue/referenceusa_sales_by_year.csv)
- Raw ReferenceUSA historical download: [`data/revenue/referenceusa_historical_2020_2024.csv`](../data/revenue/referenceusa_historical_2020_2024.csv)
- Samuel's detailed ReferenceUSA download (current listing; used for matching and rent): [`data/referenceusa/referenceusa_cd2_grocery_download.csv`](../data/referenceusa/referenceusa_cd2_grocery_download.csv)
- Basket prices used for Q_j: [`data/prices/p_j_cd2_candidate_stores.csv`](../data/prices/p_j_cd2_candidate_stores.csv), built by [`code/build_p_j.py`](../code/build_p_j.py)
- Store list: [`data/stores/large_grocery_stores_cd2.csv`](../data/stores/large_grocery_stores_cd2.csv) (Samuel's final 9 stores)
- Current rent estimates (size × market rate): [`data/phase3/tax_rent_agmarkets_cd2.csv`](../data/phase3/tax_rent_agmarkets_cd2.csv)

## Decision

**Use 2024 sales**, so every input comes from the same year: the household counts (ACS 2024) and grocery spending (BLS 2024) are 2024 too.

- **Main source:** ReferenceUSA (Data Axle) **U.S. Historical Businesses, 2024 version**, "Location Sales Volume Actual". This is the source named in the Level 1 spec.
- **Two stores have no historical record** (Food Universe, JJ Southern Farm). For those: store size × **$360 per sq ft**, the median 2024 ReferenceUSA sales per sq ft of the other 7 stores. That keeps all 9 stores on the same scale.
- **Baskets sold per year (Q_j)** = yearly sales ÷ basket price (p_j).

## Results

| Store | Size (sq ft) | Workers (2024) | Revenue_j (2024) | Source | Basket price | Q_j (baskets/yr) | Baskets/day |
|---|---|---|---|---|---|---|---|
| Key Food | 15,000 | 24 | $8,032,000 | ReferenceUSA 2024 | $27.76 | 289,337 | ~790 |
| Food Fair Fresh Market | 13,000 | 20 | $8,032,000 | ReferenceUSA 2024 | $28.95 | 277,444 | ~760 |
| C-Town (809 Southern Blvd) | 7,500 | 15 | $3,090,000 | ReferenceUSA 2024 | $28.82 | 107,217 | ~290 |
| C-Town (564 Southern Blvd) | 8,000 | 14 | $2,884,000 | ReferenceUSA 2024 | $28.82 | 100,069 | ~270 |
| Food Universe | 8,000 | – | $2,884,000 | size × $360 | $29.93 | 96,358 | ~260 |
| Antillana Fresh Meat Market | 3,000 | 4 | $824,000 | ReferenceUSA 2024 | $28.95 | 28,463 | ~80 |
| Fine Fare Supermarket | 10,000 | 3 | $618,000 | ReferenceUSA 2024 | $30.32 | 20,383 | ~56 |
| JJ Southern Farm Fruit | 1,600 | – | $577,000 | size × $360 | $28.95 | 19,931 | ~55 |
| Sagal Meat Market | 2,500 | 2 | $299,000 | ReferenceUSA 2024 | $28.95 | 10,328 | ~28 |
| **Total** | | | **$27,240,000** | | | | |

## Sales by year (ReferenceUSA, $ millions)

| Store | 2020 | 2021 | 2022 | 2023 | 2024 |
|---|---|---|---|---|---|
| Key Food | 5.77 | 5.77 | 5.77 | 5.77 | 8.03 |
| Food Fair | 5.77 | 5.77 | 5.77 | 5.77 | 8.03 |
| C-Town (809) | 3.09 | 3.09 | 3.09 | 3.09 | 3.09 |
| C-Town (564) | 2.88 | 2.88 | 2.88 | 2.88 | 2.88 |
| Antillana | 0.62 | 0.62 | 0.62 | 0.62 | 0.82 |
| Fine Fare | 0.62 | 0.62 | 0.62 | 0.62 | 0.62 |
| Sagal | 0.45 | 0.45 | 0.45 | 0.45 | 0.30 |
| Food Universe | – | – | – | – | – |
| JJ Southern Farm | – | – | – | – | – |

## Neighborhood spending check

All CD2 households together spend about **$106–124M a year** on groceries (market size M, 2024: ACS households × BLS food-at-home spending, in `data/bls/cd2_market_size_M_from_xlsx.csv`).

Our 9 stores total **$27.2M, about 22–26%** of that. The rest goes to bodegas, small grocers and stores outside CD2. That's plausible for an area where most people walk and bodegas are everywhere, though it may be on the low side (see caveat 3).

For comparison, the FMI national rate (store size × $19.59/sq ft/week, *Food Industry Facts* 2025) would give $69.9M, about 60%. It's kept as a check column in the output file but not used, because it's a national average driven by large suburban supermarkets.

## Matching ReferenceUSA records to our stores

Samuel matched stores by license number. Three stores had more than one ReferenceUSA record. We kept one per store:

| Store | Record kept (IUSA no.) | Dropped | Why |
|---|---|---|---|
| Food Fair (1065 E 163rd St) | "Food Fair" (22-473-1729) | F T Meat Corp, Fine Fare Supermarkets, FT Meat Corp (Samuel's rows 9, 10, 12) | The kept record is Verified, has the store's name and 20–28 workers. Row 9 has the same phone number (company-name record of the same store). Row 10 is an unverified old listing; row 12 has a scrambled address and $0 sales. |
| Fine Fare (950 Westchester Ave) | "Fair Farm Food" (72-380-0203), Samuel's row 19 | "950 Fair Food Corp", row 1 | Row 19 is Verified, filed as a grocery, has a phone. Row 1 is unverified, filed as a food manufacturer at a Kelly St mailing address: a paperwork record. |
| Antillana (1025 Westchester Ave) | "A & J Super Food Inc" (72-125-4832), row 3 | Same name at 1019 Westchester, row 2 | Row 3 is at our address and Verified; row 2 is unverified at the same map point. |

The IUSA numbers used are listed in `IUSA_TO_LICENSE` in the code.

**Location check:** every kept record is within about 100 ft of our state-license location, except Fine Fare (about 240 ft, a building or two over). That doesn't change distances in any meaningful way.

## Caveats

1. **ReferenceUSA doesn't know real sales.** Data Axle estimates sales from the number of workers, and carries estimates forward: most stores show the exact same number for 2020–2023. Treat these as rough size estimates, not accounting data.
2. **Today's ReferenceUSA listing is much lower than the 2024 version** for the two biggest stores. Key Food: $1.24M and 7 workers today vs $8.03M and 24 workers in 2024. Food Fair: $1–2.5M today vs $8.03M in 2024. A 15,000 sq ft supermarket with 24 staff is far more believable, so the 2024 version is the better record anyway.
3. **Fine Fare still looks too low.** 10,000 sq ft but 3 workers and $618K every year: about 56 baskets a day. If it's undercounted, a subsidy there will look more powerful than it really is, because Δp_j = θ · s / Q_j. Worth a closer look before results are presented.
4. **Two stores use an estimate, not a record.** Food Universe and JJ Southern Farm have no historical record, so they use size × $360/sq ft. Food Universe's size is from its old 724 Hunts Point Ave location (the team is still deciding between that and 1334 Louis Nine Blvd). Today's listing for 724 Hunts Point Ave calls it a restaurant with $186K in sales, which hints that store may have closed.
5. **Stores in ReferenceUSA that are not on our list.** Samuel's download has a "Key Food" at **862 Hunts Point Ave** ($9.9M, 48 workers). We checked Google Maps (Street View and satellite): **it's an apartment building**, and ReferenceUSA itself marks the record "Closed/Out of Business". It stays off the list. A C-Town at 736 Hunts Point Ave ($0.6M, 3 workers) is also in the download but not on our list.

## Rent (Rent_j): second source from ReferenceUSA

Samuel's detailed ReferenceUSA download has a **"Rent Expenses"** column, which estimates how much each store pays in rent per year. That gives us a second source to check our current rent numbers. Our current numbers are store size × $27.50 per sq ft per year, the middle of the $20–35 range in the Level 1 spec.

| Store | Current Rent_j (size × $27.50) | ReferenceUSA rent | Own or lease (RUSA) | RUSA row |
|---|---|---|---|---|
| Key Food | $412,500 | $100K–250K | Unknown | 13 |
| Food Fair Fresh Market | $357,500 | $10K–25K | Own | 9 |
| Fine Fare Supermarket | $275,000 | $10K–25K | Unknown | 19 |
| C-Town (564 Southern Blvd) | $220,000 | $50K–100K | Unknown | 6 |
| Food Universe (724 Hunts Point Ave) | $220,000 | under $10K | Own | 8 |
| C-Town (809 Southern Blvd) | $206,250 | $50K–100K | Lease | 7 |
| Antillana Fresh Meat Market | $82,500 | $10K–25K | Lease | 3 |
| Sagal Meat Market | $68,750 | under $10K | Lease | 17 |
| JJ Southern Farm Fruit | $44,000 | no data | Own | 18 |

For reference, ReferenceUSA lists Food Universe's other address (1334 Louis Nine Blvd, row 11) at $100K–250K. Food Fair's rent comes from row 9, the company-name record of the same store (the kept "Food Fair" record isn't in Samuel's file).

**What this shows:** ReferenceUSA's rent is lower than our size-based numbers for every store, by anywhere from **about 1.5× (Key Food) to over 30× (Food Fair)**.

**Rent caveats**
1. **ReferenceUSA rent is an estimate too, not a real lease.** Data Axle models expenses from its own store size and worker counts, and those come from today's listing, which is lower than the 2024 version for the big stores (see caveat 2 above).
2. **"Own" stores may pay no rent at all.** ReferenceUSA says Food Fair, Food Universe and JJ Southern Farm own their space. If that's true, a rent subsidy can't help them, and the rent lever only applies to stores that lease. This should be checked before the rent lever is run.
3. **Our size-based rent may be high.** The $20–35 per sq ft range is a general Hunts Point estimate from the Level 1 spec, not a figure for these buildings. Only 5 stores in the area had an actual lease amount in city records (ACRIS).
4. **Suggestion:** keep the size-based rent as the main number and use ReferenceUSA as the low end of a range. The rent lever can then be run at both ends.

## Basket prices (p_j) used above

Built by [`code/build_p_j.py`](../code/build_p_j.py) from the NYC Health Department's 2019 food price survey (Crossa et al. 2023). It priced the same 10 items at 163 NYC supermarkets. Prices are brought up to August 2026 with the BLS food-at-home price index for the New York area (× 1.31).

| How the price was set | Stores |
|---|---|
| The store's own survey price | Key Food |
| Average of the same chain's Bronx stores | Fine Fare, Food Universe, both C-Towns |
| Average of all Bronx stores | Food Fair, Antillana, Sagal, JJ Southern Farm |

We rechecked all 163 surveyed stores by name and address: **Key Food (1050 Westchester Ave) is the only one in CD2.**

**Price caveats**
- The survey only covered supermarkets. The three small shops all get the same Bronx average ($28.95), so the model can't tell them apart on price. Only store type and distance separate them.
- ReferenceUSA lists Food Fair and Food Universe as members of the Key Food co-op. They could use the Key Food Bronx average (about $27.94 today; $21.35 in 2019 across 8 stores) instead of their current prices ($28.95 and $29.93). Open for the team to decide.
