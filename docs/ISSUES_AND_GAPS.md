# Issues and Gaps: Bronx CD2 Grocery Subsidy Project

**Reviewed:** 2026-09-18 · **Reviewer:** Rahul (with Claude Code)
**Scope:** `Proposal .pdf`, `LEVEL_1_NYC_Grocery_Subsidy_Model_Specification_v3_drive` (the "spec"), and the team repo `grocery-subsidy-model/` at commit `50b8fdd`.

Leads follow Appendix F: **R** = Rahul, **C** = Chris, **S** = Samuel, **All** = team decision.

Severity:
- 🔴 **Critical:** changes results or fails the proposal's promise.
- 🟠 **Major:** makes results wrong or misleading if left as is.
- 🟡 **Minor:** clean-up, clarity or housekeeping.

---

## Summary

| # | Issue | Severity | Lead |
|---|---|---|---|
| 1 | Spec no longer compares FRESH with N.Y.C. Groceries | 🔴 | All |
| 2 | Firm profit function missing from the spec | 🟠 | R + C |
| 3 | Other differences from the proposal (solver, utility, data sources) | 🟡 | All |
| 4 | Welfare is per shopping trip but labelled per year (about 50× too low) | 🔴 | C |
| 5 | Price sensitivity outweighs store type, so supermarkets get about 0% share | 🔴 | C + R |
| 6 | Example numbers in the spec are placeholders and contradict each other | 🟠 | All |
| 7 | Welfare threshold defined three different ways | 🟠 | All |
| 8 | Smaller spec issues (bodega price, IIA, distance, code bug) | 🟡 | All |
| 9 | 553 SNAP stores in CD2 include about 456 closed retailers | 🔴 | S |
| 10 | State store list includes warehouses and wholesalers | 🟠 | S + R |
| 11 | `Tax_j` is tax on the whole building, not the store | 🟠 | S |
| 12 | Rent only available for State-listed stores with square footage | 🟠 | S |
| 13 | Spending inputs are US averages, not NYC or income-specific | 🟠 | S |
| 14 | Budget `B` is unknown | 🟠 | All |
| 15 | Phase 2 report out of date on census data | 🟡 | S |
| 16 | No model code exists yet | 🔴 | All |
| 17 | Rahul's and Chris's inputs not collected yet | 🟠 | R, C |
| 18 | Data in the repo that nothing uses | 🟡 | S |
| 19 | Git LFS setup (large files arrive as pointers) | 🟡 | All |
| 20 | Repo housekeeping (old website, hardcoded paths, stray files) | 🟡 | S |

---

## A. Proposal vs. spec (scope drift)

### 1. 🔴 The two-policy comparison is gone
The proposal says we will "compare the efficacy of the two policies": **FRESH** (zoning and tax incentives since 2009) and **N.Y.C. Groceries** (a city-owned site with a core basket about 30% below market). The v3 spec models only one generic subsidy to an existing store, and treats a tax break and a rent subsidy as identical. There is no N.Y.C. Groceries scenario and no FRESH-specific scenario.
- **Why it matters:** comparing the two policies is the main promise of the proposal.
- **Fix:** add N.Y.C. Groceries as its own case: a new store in the choice set, with price = 0.7 × market basket price for the core basket, funded by capital plus "Affordability Payments". Model FRESH as a cost reduction to an operator with θ < 1. The v1 website already has a "city sets price" option that can be reused.

### 2. 🟠 The firm side is missing
The proposal defines firm profit (π = Margin × Quantity − Fixed cost). The spec has no firm model: pass-through θ is simply assumed, and there's no check on whether a store stays profitable or would enter the market.
- **Fix:** at minimum, check that each store is still viable after the subsidy. Better, derive θ or prices from the firm's markup, using the Lerner equation already on the v1 website.

### 3. 🟡 Other differences from the proposal
- **Solver:** the proposal promises "Phase 2: Gurobi MIP". The spec picks one store (K = 1) by simple ranking, and uses Gurobi only if K > 1. Either do K > 1 with Gurobi, or update the proposal.
- **Utility:** the proposal's utility has Quality + Variety. The spec folds both into one store-type bonus α_j.
- **Data sources:** these are in the proposal but not used: NielsenIQ via Kilts, SNAP enrollment by CD, the USDA Food Access Research Atlas, and the FRESH zoning map. The spec relies on ReferenceUSA, which the repo leaves out because access is private.

---

## B. Model and math problems (spec v3)

### 4. 🔴 Welfare is per trip, not per year
The logsum divided by β_p gives **dollars per shopping trip**. The spec calls it "$ per household per year" and never multiplies by the number of trips per year.
- **Effect:** the benefit is understated by roughly 50×, assuming about 52 trips per year.
- **Worked example (Appendix A):** the exact gain is **$0.066 per trip** (the spec shows $0.036 because of rounding), or about **$3.41 per household per year** at 52 trips.
- **Fix:** ΔCS = Σ_i n_i × trips_i × Δlogsum_i / β_p,i.

### 5. 🔴 Price sensitivity outweighs everything else
With β_p = 0.55 per dollar of basket price, a $6 price gap is worth 3.3 utility points, compared with a supermarket bonus of 1.5. In the worked example this gives the low-income group market shares of **7.6% / 92.3% / 0.2%**, so **almost nobody shops at the supermarket**, which isn't realistic.
- **Fix:** tune the store-type bonuses α_j (and possibly scale β_p) so that predicted shares match observed shares, from revenue or square footage. Check where the β values come from: the spec cites Allcott et al. (2019) Table IV.

### 6. 🟠 The spec's example numbers are placeholders and contradict each other
- **Goal 2 example table:** the code gives each store the full budget ($1.5M), which means a price cut of about **$10.78** at Store 1. The table shows **$0.72**, which is the $100K result.
- **Appendix B:** the text says the required subsidy drops "about 35%" as θ goes from 0.40 to 0.85. The table itself shows **52%** ($2.3M → $1.1M). Since price cut = θ·s/Q, the formula predicts 53%.
- **Appendix A:** it says exp(−25.50) = 7.87e−12. The correct value is 8.38e−12.
- **Placeholder households:** 5,900 households versus the **19,922** actual count (2024 census data, now in the repo).
- **Rule:** don't cite any of the spec's example outputs in the report.

### 7. 🟠 The minimum-welfare threshold is defined two ways
Section 1.4.1 recommends "$100 × low-income households", which is **$768,300** with 7,683 households. Its own table and Goal 1 code use **$50,000**. Appendix E then defines s* as the "elbow" of the curve, which is a third definition.
- **Fix:** pick one definition and use it everywhere.

### 8. 🟡 Smaller spec issues
- **Bodega basket price:** bodegas get the cheapest basket ($30). In practice bodegas usually charge more per item. Check against real data.
- **IIA not acknowledged:** when one store gets cheaper, the logit model draws customers proportionally from every other store (independence of irrelevant alternatives). This isn't in Appendix D's assumptions. A nested logit (grouping by store type) would fix it.
- **Distance:** the example code places every income group at the district centroid, so distance never differs between groups. The repo has 16 tract centroids that could be used instead, weighted by where each income group lives.
- **Code bug:** Goal 1's `print(f"... {s_star:,.0f}")` crashes when no subsidy meets the thresholds (`s_star = None`).
- **Outside shopping:** Appendix D assumes residents shop only inside CD2, and says this overstates the benefit. It could be large in practice, so plan to test it.

---

## C. Data problems (repo `grocery-subsidy-model/`)

### 9. 🔴 Most of the SNAP store list is closed stores
`download_stores_snap.py` uses USDA's **historical 2005–2025** file and never filters on `End Date`. Of the **553** CD2 retailers, **456 have an end date**, leaving about **97 active**: 37 convenience stores, 28 small grocery, 10 medium grocery, 6 combination, 5 supermarkets, 3 super stores, 2 large grocery and a few specialty stores. Phase 3 then matched tax and rent for all 553.
- **Fix:** keep only rows with no `End Date` (or a future one), then re-run Phase 3 for the SNAP list.

### 10. 🟠 The State (Ag & Markets) store list includes non-stores
The largest entry is **PRIME NOW LLC at 180,000 sq ft**, which looks like an Amazon fulfilment warehouse. Other names, such as a cold-brew producer and an artisan bakery, look like wholesalers or manufacturers from the Hunts Point food market. Only **5 of 137** entries are 10,000 sq ft or larger, and **42** have no square footage.
- **Fix:** build a cleaned candidate list by matching the SNAP (active), State and health-inspection lists on BBL (the city's property ID) or address. This is already listed as Samuel's next step. Drop warehouses and wholesalers.

### 11. 🟠 `Tax_j` is tax for the whole building
The DOF (NYC Department of Finance) charges are per tax lot, so buildings with homes above a shop count the whole building's tax. The median `Tax_j` for State-listed stores is **about $336K a year**, which is too high for a small shop's share.
- **Fix:** scale by the retail share of the building (PLUTO's `retailarea / bldgarea`), or treat the value only as an upper bound.

### 12. 🟠 Rent is only available for part of the list
City lease records (ACRIS) give a usable dollar figure for only about 3% of stores. The fallback, square feet × $20–35, works for **69%** of State-listed stores and **0%** of SNAP or health-inspection stores, because those lists have no square footage.
- **Fix:** give matched SNAP stores the square footage from the State list, and use survey or estimate values for the rest.

### 13. 🟠 Spending inputs aren't local
The BLS income tables were blocked (HTTP 403 errors), so the market size M (about $109–124M a year) uses the **US average** food-at-home spending. The per-group weekly spending figures (**$75 / $100 / $140**) are simply the spec's own ranges, not data.
- **Fix:** download the BLS income-level spending tables by hand in a browser, ideally for the NYC metro area.

### 14. 🟠 The budget `B` is unknown
No yearly operating budget has been published for CD2. What is public: **$70M** in construction money for 5 city-owned stores (not yearly), the CD2 site ("The Peninsula", Hunts Point, about 20,000 sq ft, opening 2027), and yearly "Affordability Payments" whose amount is **still to be decided**.
- **Fix:** treat B as a range of scenarios, and say so clearly in the report.

### 15. 🟡 Phase 2 report is out of date
It says the 2020–2023 census data couldn't be downloaded without an API key. The files exist, and `acs_download_meta.json` shows a key was used.

---

## D. Missing work

### 16. 🔴 No model code yet
The repo only covers data collection and documentation. Nothing computes:
- choice probabilities or market shares,
- ΔCS,
- the Goal 1 subsidy search,
- the Goal 2 store ranking,
- the benefit breakdown by income group,
- the sensitivity runs.

### 17. 🟠 Inputs not collected yet
- **Rahul (R):** store prices p_j, store type α_j, revenue or volume Q_j, eligibility e_j, candidate count J.
- **Chris (C):** price sensitivity β_p, distance sensitivity β_d, pass-through θ (with sources), trips per year (see issue 4).

### 18. 🟡 Data in the repo that nothing uses
Furman Center CoreData neighborhood indicators and the Subsidized Housing Database (`data/FC_SHD_*`). The housing database covers housing subsidies, not grocery, so decide whether it's needed.

---

## E. Repo and setup housekeeping

### 19. 🟡 Git LFS
The three large SNAP raw files are stored with Git LFS. If LFS isn't installed, they arrive as **133-byte pointer files**, and re-running `download_stores_snap.py` or reading those files will fail. Follow `docs/git_lfs_team_guide.md`. The small CD2 files don't need LFS.

### 20. 🟡 Other clean-up
- **Old website:** it still shows the **v1** model (mixed logit, quality/variety, firm costs, a third "spillover" goal), not v3. Update it once the model is final.
- **Hardcoded paths:** `generate_model_doc*.py` save to `C:\Users\samia\...`, which breaks the LFS guide's own no-personal-paths rule and fails on other machines.
- **Cache folder committed:** `code/__pycache__/` is in the repo. Add `__pycache__/` to `.gitignore`.
- **Empty or placeholder files:** `appendix_f_full.txt` and `code/_hello_world.py`.
- **Loose working files at the root:** `edited_doc_content.txt`, `v2_drive_content.txt`, `appendix_f_extract.txt`, `test_eq.png`, and six spec `.docx` versions. Move them into `docs/spec/` or delete them.
