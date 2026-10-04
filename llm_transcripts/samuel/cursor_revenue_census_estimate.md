# Revenue census estimate
_Exported on 10/4/2026 at 10:41:31 EDT from Cursor (3.17.8)_

---

**User**

Review the file "LEVEL_1_... .docx" and the files in \docs. I would like to make some changes, but first I have some questions

The revenue we find from reference USA seems really off. How can I get an estimate for revenue per square foot for grocery stores in the bronx? Is there a way I can use corporate information from Key foods or C-town (chains) to get an estimate?

---

**Cursor**

I'll start by finding the LEVEL_1 document and looking through `docs`.

The `.docx` can't be opened directly and the shell is unavailable, so I'll work from the markdown docs, which probably mirror the spec. Starting with the revenue notes.

The revenue notes explain the problem well. Next I'll check the untracked research PDFs and any text export of the spec for revenue or sales-per-square-foot figures.

The Forbes article only gives margins (1–3%), not sales per square foot. Next I'll check the team plan, the revenue script, and the city RFP documents for any sales benchmarks.

The team already flagged the 2022 Economic Census as the preferred Bronx source. Next I'll skim the city RFP Q&A and Vision Plan for projected store sales.

I couldn't find a Bronx sales-per-square-foot figure anywhere in the repo, and Key Food or C-Town corporate data won't give you one directly. Neither chain publishes store-level financials. The best public route is to divide Bronx supermarket sales from the Census Bureau's 2022 Economic Census by the total square footage of licensed Bronx food stores in the NY State Department of Agriculture and Markets (Ag & Markets) list. Chain-level figures are useful as an upper-bound check.

I couldn't open the `.docx`, but `docs/revenue_j_estimates.md`, `ISSUES_AND_GAPS.md` and `SOURCE_LIST_RAHUL.md` describe how it handles revenue, so the answer below is based on those.

## Why the ReferenceUSA numbers look wrong

Your own notes explain it. Data Axle (the company behind ReferenceUSA) estimates sales from headcount and carries the same number forward for years:

```77:77:c:\Users\samia\Code_Projects\grocery_subsidy_analysis\docs\revenue_j_estimates.md
1. **ReferenceUSA doesn't know real sales.** Data Axle estimates sales from the number of workers, and carries estimates forward: most stores show the exact same number for 2020–2023. Treat these as rough size estimates, not accounting data.
```

Here is what the 2024 figures imply per square foot per year:

| Store | $/sq ft/yr |
|---|---|
| Food Fair | $618 |
| Key Food | $535 |
| C-Town (809) | $412 |
| C-Town (564) | $360 |
| Antillana | $275 |
| Sagal | $120 |
| Fine Fare | $62 |

The median, $360 per year (about $6.90 per week), is roughly a third of the national rate from FMI (the Food Industry Association): $19.59 per week, or about $1,019 per year. The tenfold spread between stores shows the numbers are artifacts of headcount estimates, not real differences in sales.

## Using Key Food or C-Town corporate information

**What's available:** Both are banners of independently owned stores, not corporate chains. Key Food is a retailer-owned cooperative, and C-Town stores are independents supplied by a wholesaler. Neither files public financial reports. The closest you'll get:
- Trade-press rankings such as Supermarket News' Top 75 and Progressive Grocer's PG 100, or the Chain Store Guide directory. These list estimated total annual sales and store counts for the co-op or wholesaler.
- Store counts, and sometimes store sizes, from the banner websites' store locators.

**How you'd use it:**

\[
\text{sales per sq ft} \approx \frac{\text{banner-wide retail sales}}{\text{number of stores} \times \text{average store size}}
\]

If the ranking reports wholesale sales (what the co-op sells to its members) rather than retail sales, gross it up:

\[
\text{retail sales} \approx \frac{\text{wholesale sales}}{1 - \text{gross margin}}
\]

Typical supermarket gross margins are roughly 25–30%.

**Limitations:**
- The trade-press sales figures are themselves estimates.
- A banner-wide average mixes in larger stores in Queens, Long Island and New Jersey, so it will likely overstate sales for a 7,500 sq ft Hunts Point store.
- You'd have to guess the average store size.

So I'd treat it as an upper-bound check, not the main estimate. Separately, `revenue_j_estimates.md` notes that ReferenceUSA lists Food Fair and Food Universe as Key Food co-op members. If you use a Key Food rate, it would arguably apply to those two stores as well.

## Better ways to get a Bronx number

**1. Economic Census 2022, Bronx County (main recommendation).** `SOURCE_LIST_RAHUL.md` already names this as the replacement for the FMI rate; the earlier attempt through the Census data API returned nothing.
- Download the geographic area table (EC2244BASIC) for NAICS 445110 (supermarkets and grocery stores) for Bronx County from data.census.gov. It gives total sales, number of establishments and paid employees.
- Sum the square footage of Bronx stores in the Ag & Markets license file. You already use it for CD2, and it covers the whole state.
- Divide total sales by total square footage to get a Bronx-wide rate. Adjust 2022 dollars to 2024 with the BLS index you already use in `build_p_j.py`.
- Watch-outs:
  - Filter the Ag & Markets list the same way Census defines the industry. Drop warehouses, wholesalers, pharmacies and gas stations; ISSUES #10 already found these in the CD2 list.
  - Decide whether bodegas coded as convenience retailers (NAICS 445131) belong in the comparison.
  - Impute square footage for stores that have none.
  - The result is an average across all Bronx grocery formats, so full supermarkets probably sit above it and small shops below.

**2. Sales per employee (cross-check).** The same Census table gives Bronx sales per employee. Multiply it by each store's staff count to get a second estimate. The weak point is headcount, since ReferenceUSA's counts are estimates too. Counting checkout lanes or calling the stores would firm it up.

**3. Benchmarks for independent grocers.** The National Grocers Association and FMI publish financial surveys of independent grocers that report sales per square foot for smaller stores. That fits your 7,500–15,000 sq ft stores better than FMI's 42,000 sq ft median store.

**4. Store-level data if your school has access.**
- Advan (formerly SafeGraph) foot-traffic and spend data through Dewey: visits per store times average ticket ($49.06 per transaction from FMI, already in your source list) gives a revenue estimate for each store.
- NielsenIQ scanner data via Kilts, which your proposal mentions: it gives store-level sales for Bronx County (FIPS 36005). But it only covers participating retailers and barcoded items (no loose produce or meat), and store names are masked.

**Sources that won't help:**
- The city's RFP Q&A says NYCEDC's sales forecasts use proprietary data it won't share (Q23).
- The Forbes article only gives margins of 1–3%.

## Suggested approach

Build a range instead of picking one number:
- **Low:** ReferenceUSA (about $360 per sq ft per year).
- **Central:** Economic Census Bronx sales divided by Ag & Markets square footage.
- **High:** a banner-wide Key Food or C-Town average, or FMI's national rate.

Then run the model at each value. It matters because the price cut per basket, Δp_j = θ·s/Q_j, scales inversely with revenue: underestimating sales makes the subsidy look stronger than it is.

Check each value against the market size: the nine stores' total should be a plausible share of CD2's $113M in yearly grocery spending. At FMI's rate they'd capture about 60%; at the ReferenceUSA rate, about 24%.

When you switch to Agent mode, I can add the Economic Census rate and the low, central and high scenarios to `build_revenue_j.py`.

---

**User**

Create a plan for the central approach. create new code file, and save data in data/revenue_census_estimate

---

**Cursor**

I'll check which Ag & Markets and Census files are already in the repo, and how the earlier Census pull failed, before drafting the plan.

The Bronx Ag & Markets file and the 2023/2024 archives are already in the repo. Next I'll check how much square-footage coverage the Bronx rows have, since that determines the denominator.

Grep's counts cap at 100, so I'll leave the exact square-footage coverage to the script. Last, I'll check how `build_p_j.py` inflates prices, so the new script can reuse the same deflator.

---

**User**

Implement the plan as specified, it is attached for your reference. Do NOT edit the plan file itself.

To-do's from the plan have already been created. Do not create them again. Mark them as in_progress as you work, starting with the first one. Don't stop until you have completed all the to-dos.

---

**Cursor**

Starting with the Census pull. First I'll look up the todo tool and confirm the shell works in Agent mode.

The Census API works: in 2022 the Bronx had 1,125 supermarkets and grocery stores (NAICS 445110) with $3.43B in sales. Next I'll query convenience retailers (445131) and the combined 4451 total.

I have everything needed from the existing files. One last check: whether Nonemployer Statistics and the Economic Census publish 445110 and specialty food (4452) separately for the Bronx.

The new script, `code/build_revenue_census.py`, runs end to end and puts Bronx grocery sales at about **$829 per sq ft per year ($15.93 per week) in 2024 dollars**. That is 2.3 times ReferenceUSA's $360 and a bit below FMI's national $19.59 per week. Applied to the nine CD2 stores, it gives **$56.8M a year, about 50% of CD2's $113M grocery market**. The current ReferenceUSA numbers give 24% and FMI gives 62%.

**How the rate is built.** Bronx grocery and convenience sales from the 2022 Economic Census ($3.75B, including owner-run stores) are divided by 4.75M sq ft across 2,043 matched Bronx Ag & Markets stores in the 2023 list. The result is inflated from 2022 to 2024 with the New York food-at-home price index (×1.049). The Census API worked directly, so no manual download was needed.

**Range across variants (2024 dollars per sq ft per year):**

| Variant | Rate |
|---|---|
| Central | $829 |
| Paid-employee stores only | $804 |
| Supermarkets and grocers only, no bodegas (NAICS 445110) | $1,092 |
| Adding meat, fish and produce markets (NAICS 4452) | $844 |
| Current Ag & Markets list instead of 2023 | $858 |
| Stores with recorded square footage only | $719 |

**What changes per store (central estimate):**
- Key Food: $12.4M, up from $8.0M.
- Food Fair: $10.8M.
- **Fine Fare: $8.3M, up from $0.6M.** That resolves the "too low" caveat in `revenue_j_estimates.md`.
- Both C-Towns: about $6.2–6.6M, up from about $3M.
- Baskets sold per year (`Q_j_census`) rise by the same proportion, so price cuts per basket from a given subsidy get smaller.

**Changes from the plan:**
- **Owner-run stores added to the numerator.** The Economic Census counts only businesses with paid employees, but Ag & Markets lists owner-run bodegas too. The Census publishes those separately (1,788 Bronx stores, $110M in sales), so I added them. The paid-employees-only version is kept as a variant.
- **Convenience retailers (445131) are published as 0 for the Bronx**, which is suppression, not real zeros. The broad scope therefore uses the grocery-plus-convenience total (4451), which includes them.
- **Added the specialty-food variant**, because three of the nine stores are meat or produce markets.
- **Name filter tuned after an audit.**
  - Names like "DELI & SMOKE SHOP" or "GROCERY & 99 CENTS" are kept as bodegas.
  - Discount, variety and gas-station names are excluded.
  - Supermarket names cut short in the data ("SUPERMKT", "FOOD TOWN") are still recognised.
  - Every excluded row has an `exclude_reason` so you can check it.
- **Store inputs come from the existing revenue output**, which already holds square footage, basket price, ReferenceUSA and FMI. The output also has low and high revenue columns (the lowest and highest variants) and a sales-per-employee cross-check.

**Caveats:**
- About 26% of the matched stores have no recorded square footage and use the median for their category. They make up 15% of the total square footage.
- Ag & Markets square footage covers the whole licensed location, not just the selling floor. That's consistent on both sides of the ratio, but it's not the same basis as FMI's figure.
- The Bronx rate is an average across all store formats, so it likely understates sales for the full supermarkets and overstates them for the small meat and produce shops.

`build_revenue_j.py` and its outputs are unchanged. Whether to switch the model's main revenue figure to this estimate is still a team decision.

Files are in `data/revenue_census_estimate/`:
- `revenue_j_census_cd2_candidate_stores.csv`
- `bronx_sales_per_sqft_census.csv`
- `bronx_agmarkets_stores_filtered.csv`
- `revenue_census_meta.json`
- `raw/ecn_2022_bronx_4451.csv`

---

**User**

<timestamp>Wednesday, Sep 30, 2026, 10:19 AM (UTC-4)</timestamp>
<system_notification>
The following task has finished. If you were already aware, ignore this notification and do not restate prior responses.

<task>
kind: shell
status: success
task_id: 459238
title: Check Python env and .env presence
tool_call_id: toolu_01QwJsdBxvUqrqmNL1sYmLRt
output_path: C:\Users\samia\.cursor\projects\c-Users-samia-Code-Projects-grocery-subsidy-analysis\terminals\459238.txt
</task>
</system_notification>
<user_query>Briefly inform the user about the task result and perform any follow-up actions (if needed).</user_query>

---

**Cursor**

That notification is from the environment check I ran at the start (Python 3.13 with pandas 3.0.3, and a `.env` file present). It has now finished and needs no follow-up, since the Census revenue script and its outputs were completed after it.

---

**User**

Create a markdown file in docs/ that describes all the steps, assumptions, and files made (and where they live) and your findings.

---

**Cursor**

I'll pull the exact counts from the metadata file, then write the doc.

I've written `docs/revenue_census_estimate.md`, laid out like the existing `revenue_j_estimates.md`. It covers:

- **Files and locations:** the script, the five outputs in `data/revenue_census_estimate/` with what each holds, the input files used (none modified), and how to run the script.
- **Why:** the problems with ReferenceUSA's sales, and why Key Food and C-Town corporate data can't give store-level figures.
- **Method:** the formula, then four steps.
  1. The Census figures used, including the owner-run stores and the suppressed convenience-store data.
  2. The Ag & Markets filtering: license codes, name exclusions with counts, the bodega exception, store categories and square-footage imputation.
  3. The 2022 to 2024 price adjustment (×1.0493).
  4. Applying the rate to the nine stores.
- **Results:** the table of rate variants, the nine-store revenue table (central, low and high next to ReferenceUSA and FMI), and the check against CD2's $113M market size.
- **Findings:** the main one is about $829 per sq ft per year in the Bronx (range $719–$1,092 across variants), 2.3 times ReferenceUSA. The doc also explains that the "Fine Fare looks too low" caveat is resolved at about $8.3M, and why the larger baskets-per-year figures mean smaller price cuts per basket.
- **Assumptions and caveats:** eight items, including one rate for all store formats, whole-location square footage, the name-based filter, and imputed square footage.
- **Next steps:** team decisions on adopting the estimate as the main revenue figure, and updating the Level 1 spec's revenue row.

I checked the figures in the doc against the generated CSV and metadata files.

---

**User**

When calculating the $/sq ft /year, when the numerator was changed (class of store), was the denominator changed as well (selected stores for square footage)? There are other ways to filter. For example, SNAP license, if matched to a store, has more detailed information on store type. Second, the column “estab_type” has a code system and may help distinguish. Would you need the data dictionary to do this?
It is not exactly clear where each variant comes from. CAn you add a section in the .md that describes specifically how each variant is created (numerator and denominator)?

---

**Cursor**

I'll check how the variants are wired in the code and what SNAP data is available Bronx-wide.

To answer directly: **the denominator changed in some variants but not all, and one variant is mismatched in a way that pushes its rate up.** Both of your filtering ideas are workable. I already have the establishment-code dictionary and used it. The SNAP match is the more useful of the two.

## Did the denominator change with the numerator?

Each scope in `build_revenue_census.py` pairs a set of Census industry codes with a set of Ag & Markets store categories:

```111:119:c:\Users\samia\Code_Projects\grocery_subsidy_analysis\code\build_revenue_census.py
SCOPES = {
    "A": (["supermarket", "convenience or deli", "other grocery"],
          [("ecnbasic", "4451"), ("nonemp", "4451")]),
    "A_employer": (["supermarket", "convenience or deli", "other grocery"],
                   [("ecnbasic", "4451")]),
    "B": (["supermarket", "other grocery"], [("ecnbasic", "445110")]),
    "C": (["supermarket", "convenience or deli", "other grocery", "specialty"],
          [("ecnbasic", "4451"), ("nonemp", "4451"), ("ecnbasic", "4452"), ("nonemp", "4452")]),
}
```

How well each variant matches:

- **With specialty (4452):** Specialty shops are added to both sides. This one matches.
- **Employer only:** The numerator drops owner-run stores, but the denominator doesn't. Ag & Markets can't tell which stores have paid employees. So owner-run bodegas stay in the square footage without their sales, and the rate ($804) is biased low.
- **Grocery only (445110):** The denominator drops everything named "deli" or "grocery". But the Census classes most Bronx bodegas as 445110, not as convenience stores. The evidence: 1,125 Census 445110 businesses against only 750 Ag & Markets stores in that denominator, and only 285 convenience-type businesses in total. So bodega sales stay in the numerator while their square footage leaves, and **$1,092 is biased high**. The current doc presents it as the supermarket rate, which overstates what it shows.
- **Known square footage only:** Both sides change. But it assumes stores without recorded square footage have average sales, and they're probably smaller, so it's biased low.

## Filtering by SNAP store type

This would help most. The repo already has a Bronx-wide SNAP file, `data/stores/snap_bronx_county.csv`: about 9,800 historical records with authorization and end dates. Keeping stores active in 2022 gives a 2022 snapshot. USDA's store types map well onto Census industries:

| SNAP store type | Census industry |
|---|---|
| Supermarket, Super Store, Large / Medium / Small Grocery | 445110 |
| Convenience Store | 445131 |
| Meat/Poultry, Seafood, Fruits/Veg, Bakery Specialty | 4452 |
| Combination Grocery/Other (pharmacies, dollar stores) | exclude |

The address and distance matching in `link_agmarkets_snap.py` already works for CD2 and could run Bronx-wide. Two limits:
- Stores without SNAP authorization wouldn't match, so they'd fall back to the name categories.
- USDA assigns store types by stocking and sales, which is close to, but not the same as, the Census definitions.

This would fix the grocery-only variant and replace most of the name-keyword guessing.

## The `estab_type` codes

I don't need anything more; I already downloaded and used the code sheet (`NYSDAM_RetailFoodStoresEstablishmentTypeCodes.pdf` on data.ny.gov). The codes are: A store, B bakery, C food manufacturer, D food warehouse, E beverage plant, H wholesale manufacturer, I and L refrigerated warehouses, J multiple operations, K vehicle. The script keeps A and drops D, E, H, I and L.

The codes are limited for telling store types apart, because they describe licensed activities, not formats. Almost every store is AC (store with in-store food preparation such as slicing deli meat). The bakery flag B is the one useful signal. In the 2023 archive:
- JAC: 1,991 stores, median 1,000 sq ft.
- A: 528 stores, median 900 sq ft.
- JABC: 45 stores, median 7,000 sq ft.

So B helps identify supermarkets as a supporting signal, but it can't separate bodegas from grocers.

I saved the PDF to a temp folder, not the repo. It would be worth adding it to `data/stores/`.

## Section to add to the doc

I'm in Ask mode, so I can't edit the file. Here is a section you can paste into `docs/revenue_census_estimate.md` after "Step 4". If you switch to Agent mode, I can add it and implement the SNAP-based filter.

```markdown
### How each variant is built

Every variant divides a Census sales total (numerator) by the square footage of a set of Bronx Ag & Markets stores (denominator). Defined in `SCOPES` and `VARIANTS` in `code/build_revenue_census.py`.

| Variant | Numerator (Census, 2022) | Denominator (Ag & Markets) | Stores / sq ft | Rate 2024 |
|---|---|---|---|---|
| Central | 4451 employer ($3,639M) + 4451 nonemployer ($110M) = $3,749M | 2023 archive; categories supermarket, convenience or deli, other grocery; missing sq ft imputed | 2,043 / 4.75M | $829 |
| Employer only | 4451 employer = $3,639M | Same as central (unchanged) | 2,043 / 4.75M | $804 |
| Grocery only (445110) | 445110 employer = $3,425M | 2023 archive; supermarket + other grocery only (convenience or deli dropped); imputed | 750 / 3.29M | $1,092 |
| With specialty (4452) | 4451 + 4452, employer + nonemployer = $4,082M | Central denominator + specialty category | 2,275 / 5.08M | $844 |
| Current list | Same as central | Current Ag & Markets list, same rules and categories | 1,798 / 4.58M | $858 |
| Known sq ft only | Central × 1,509 / 2,043 = $2,769M | Central stores, recorded sq ft only | 1,509 / 4.04M | $719 |

**Matching caveats**
- **Employer only:** the denominator is not reduced, because Ag & Markets does not show which stores have paid employees. Owner-run stores stay in the denominator without their sales, so the rate is biased low.
- **Grocery only (445110):** mismatched. The Census counts most Bronx bodegas as 445110 (1,125 establishments, against 750 stores in this denominator), but their square footage was removed with the "convenience or deli" name category. The rate is biased high and should not be read as a supermarket-only rate.
- **Known sq ft only:** assumes stores without recorded sq ft have average sales. They are probably smaller, so the rate is biased low.
- **Categories** come from store names (see `category_patterns` in `revenue_census_meta.json`). A planned improvement is to assign categories from matched USDA SNAP store types instead (supermarket and grocery types = 445110, convenience store = 445131, specialty types = 4452).
```

---

**User**

Create a second .md file (v2) that creates a new code file (v2). Try the filtering by snap and estab codes. be sure to match numerator with denominator.

---

**Cursor**

I'll read the rest of the existing SNAP linking script to see what can be reused Bronx-wide.

---

**User**

Implement the plan as specified, it is attached for your reference. Do NOT edit the plan file itself.

To-do's from the plan have already been created. Do not create them again. Mark them as in_progress as you work, starting with the first one. Don't stop until you have completed all the to-dos.

---

**Cursor**

Writing the v2 script.

The Census API returned a temporary 503 error. I'll add a short retry to the v2 loader and run again.

Everything ran up to the metadata step, which failed on tuple keys in one dictionary. Fixing that.

One cell in the variant table is garbled. I'll pull the exact counts of stores with recorded square footage from the CSV and fix it.

v2 is done and runs end to end. With every numerator matched to the same class of stores, the recommended Bronx rate is **$801 per sq ft per year ($15.41 per week)**. The range is **$698–$845**, and the nine stores total **$55.0M, 49% of CD2's grocery market**. v1 gave $829 and $56.8M, so the central estimate barely moves. The range narrows because v1's $1,092 top end came from its mismatched variant.

**How the classes are built**
- **Establishment codes** decide which licenses count as stores (code A kept; warehouse, plant and wholesale codes dropped).
- **SNAP store type** sets the Census class for the 78% of kept stores that match a SNAP retailer active in 2022.
- **Store names** are the fallback for the other 22%.
- **Owner-run stores:** the Census publishes nonemployer figures for convenience stores, so every class's numerator includes owner-run stores. The Census reports those figures separately, and Ag & Markets lists those stores too.

**Main finding: a separate supermarket rate can't be matched from these sources.**
- SNAP and the Census draw the line between grocery and convenience in different places. Among Ag & Markets stores, 46% fall in the grocery class, against 85% of Census establishments. SNAP calls most bodegas "Convenience Store", while the Census counts them as grocery stores.
- Because of that, the grocery-only rate ($1,044) is too high and the convenience rate ($179) too low. The specialty-food rate ($2,206) is distorted as well.
- The script runs this split check and falls back to the pooled grocery-plus-convenience rate, which doesn't depend on where the line is drawn.

**Establishment codes on their own can't separate bodegas from grocers**, because almost every store has the same code (store plus in-store food preparation). The in-store bakery flag does mark full supermarkets (median 7,000 sq ft), so I used it in the square-footage imputation groups.

**Changes from the plan**
- **Spatial matching now requires a shared name word.** A sample audit showed the "within 15 m, no name check" rule mostly matched neighbouring shops (a smoke shop matched to an ALDI, a vape shop to a seafood store).
- **Added two pooled variants** (current list, and recorded square footage only) so the low/high range comes from the recommended family of variants.
- **Added a retry** for a temporary Census API outage (503 error).

**Files**
- Code: `code/build_revenue_census_v2.py`
- Doc: `docs/revenue_census_estimate_v2.md`. It has the "How each variant is built" table, with the numerator and denominator for every variant, plus the classification results, split check, code breakdown and a v1 comparison.
- Outputs in `data/revenue_census_estimate/v2/`:
  - `raw/ecn_2022_bronx_v2.csv`
  - `bronx_agmarkets_snap_linked_v2.csv`
  - `bronx_class_counts_v2.csv`
  - `bronx_sales_per_sqft_census_v2.csv`
  - `revenue_j_census_v2_cd2_candidate_stores.csv`
  - `revenue_census_v2_meta.json`
- Code sheet saved to `data/stores/NYSDAM_RetailFoodStoresEstablishmentTypeCodes.pdf`.

The v1 script, outputs and doc are unchanged.

