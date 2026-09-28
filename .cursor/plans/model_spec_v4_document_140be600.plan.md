---
name: Model Spec v4 Document
overview: Answer all seven technical questions, list the design decisions that require approval, then produce LEVEL_1_NYC_Grocery_Subsidy_Model_Specification_v4.docx and a companion v3→v4 changes document.
todos:
  - id: design-decisions
    content: Receive user approval on the 7 design decisions listed in the plan before drafting v4
    status: pending
  - id: draft-v4-docx
    content: Produce LEVEL_1_NYC_Grocery_Subsidy_Model_Specification_v4.docx in docs/ with all structural changes applied
    status: pending
  - id: draft-changes-doc
    content: Produce LEVEL_1_NYC_Grocery_Subsidy_Model_v3_to_v4_changes.docx explaining every change from v3 in plain English
    status: pending
isProject: false
---

# Grocery Subsidy Model Spec v4 — Plan

## Answers to your seven questions

### Q1 — SNAP eligibility and consumer utility

SNAP acceptance should enter utility as a **benefit term** for low- and mid-income groups, not as an eligibility filter alone. The mechanism: a low-income consumer who can pay with SNAP benefits receives real additional value from a SNAP-authorized store (no cash needed, purchasing power expanded). The standard approach in the food-retail discrete choice literature (Hillier et al. 2017 — already in `docs/literature/`) is to add an indicator term:

```
V_ij = α_j − β_p_i · p_j − β_d_i · d_ij + δ_SNAP_i · snap_j
```

where `snap_j = 1` if store j is SNAP-authorized and `δ_SNAP_i ≥ 0` for low/mid income groups, `= 0` for high income. This means:
- **e_j (eligibility)** stays as a hard filter for subsidy candidates — the city can only subsidize SNAP stores.
- **snap_j in V_ij** adds a soft utility bonus — consumers benefit from SNAP stores regardless of the subsidy.

The value of δ is a **design decision** (see below). Hillier et al. (2017) estimate a SNAP × store-type interaction coefficient in their conditional logit, which is the best available source.

---

### Q2 — BLP-style β construction

**What BLP actually is in this context:** Berry, Levinsohn, and Pakes (1995) introduced a random coefficients logit for differentiated products. Your model is in the same family: consumers have heterogeneous preferences (β_i) over store characteristics. The "BLP approach" your colleague is describing is making β_i a deterministic function of observable demographics plus an unobserved residual.

**Simple structural form for β_d_i (distance sensitivity):**

```
β_d_i = α_car · car_free_share_i + α_inc · income_index_i + [α_age · avg_age_i]
```

All three variables are available per (tract, income group) from ACS B08201 and B01002. `α_car` is the largest driver — CD2 has 71.9% car-free households overall, but this varies by tract and income group. `α_car` and `α_inc` are borrowed from the grocery-choice literature (Taylor & Villas-Boas 2016 — Chris's Tier 2 #1; Marshall & Pires 2017 — already in the library).

**Simple structural form for β_p_i (price sensitivity):**

Chris's params doc gives the right answer here: **anchor β_d first from demographics, then derive β_p from the ratio** WTP_distance = β_d / β_p, where the ratio is calibrated from literature (Taylor & Villas-Boas 2016 report willingness to pay in distance per dollar, by income group). This avoids assuming both parameters independently — which is the inconsistency the spec currently has.

```
β_p_i = β_d_i / WTP_i    (WTP_i from Taylor & Villas-Boas 2016)
```

**The "simultaneous equation" your colleague mentioned** is the BLP contraction mapping (Berry 1994): finding the vector of mean utilities δ such that predicted market shares exactly match observed shares. It is solved iteratively: `δ_j^(new) = δ_j^(old) + log(s_j_observed) − log(S_j_predicted)`. **You cannot run this without observed market shares.** Since we don't have transaction data, we skip the contraction mapping and instead do a softer calibration check: confirm that predicted shares are qualitatively consistent with the known fact that CD2 has mostly bodegas and one supermarket (Issue #5 from ISSUES_AND_GAPS.md).

**β_p/β_d ratio approach — what is gained/lost:**
- Gained: the ratio is more robustly estimated in the literature than individual levels; the two parameters are internally consistent; reduces the number of free parameters from 6 (two per group) to 3.
- Lost: you can no longer independently vary price and distance sensitivity; sensitivity analysis on one implicitly moves the other.

**Benefits of BLP-style vs. ad-hoc values:**
- Interpretable: you can say "β_d is higher in this tract because 80% of households have no car."
- Credible: rooted in observable data, not just assumed.
- Easy to update: when new ACS data arrives, β values update automatically.

**Issues:**
- Without estimation, α values are still borrowed; the structural form is a framework, not an estimate.
- Requires a term table entry per demographic variable used.
- α_car and α_inc may be correlated across tracts (car-free is correlated with low income), creating multicollinearity that makes separate identification hard.

---

### Q3 — Pass-through θ as economic incidence / elasticities

Chris's Tier 3 analysis is exactly right. The pass-through literature (Besanko et al. 2005, Nakamura & Zerom 2010) reports log-log elasticities from per-unit wholesale cost shocks on branded packaged goods. Our subsidy instruments are **fixed-cost reductions** (rent, property tax). Standard theory (Weyl & Fabinger 2013) says fixed-cost changes do not move a profit-maximising firm's prices, implying θ = 0 for FRESH-type instruments.

**For the NYC Groceries contracted model:** θ = 1 by contract (Affordability Payments guarantee the 30% discount). This is already documented.

**Elasticity-based derivation for per-unit instruments (reference only):**
For a linear demand/supply system: `θ = ε_supply / (|ε_demand| + ε_supply)`. For a competitive market (ε_supply → ∞): θ = 1. For a monopolist: θ = 1/(2) in a linear model. Andreyeva et al. (2010, AJPH) gives grocery food price elasticities by category (0.27–0.81 absolute value) — available and relevant.

**Recommendation for v4:** Treat θ as explicitly unidentified for FRESH-type subsidies. Report three scenarios (θ = 0, 0.40, 0.85) in a dedicated sensitivity table. Cite Weyl & Fabinger (2013) and Butters, Sacks & Seo (2022, AER) to explain why θ ≠ 1 is expected for fixed-cost instruments. For NYC Groceries, set θ = 1 and cite the RFP contract.

---

### Q4 — Estimating Q_j from market size and square footage

The approach you describe (sq-ft × sales-per-sqft by store level) is already the preferred method in `docs/SIMPLIFIED_PLAN_AND_SOURCES.md` using FMI benchmarks. The formula:

```
Revenue_j = sq_ft_j × sales_per_sqft_j
Q_j = Revenue_j / p_j
```

where `sales_per_sqft_j` varies by store type:
- Supermarket / national chain: ~$1,019/sqft/year (FMI 2025)
- Mid-size independent: scale down ~20–30%
- Small grocery/bodega: scale down ~40–50%

The 1–2% profit margin from FMI can be used as a cross-check: `profit_j = margin × Revenue_j`. Square footage is available for 69% of Ag & Markets stores (from `data/phase3/tax_rent_agmarkets_cd2.csv`). This approach avoids needing ReferenceUSA entirely.

---

### Q5 — Core basket structure in pass-through

The RFP contract adds explicit structure. Replace the scalar θ in Eq 1.3.1 with:

```
Δp_j = 0.30 × κ × p_j
```

where `κ` is the **core basket share** — the fraction of total food-at-home spending that falls on RFP core basket categories (all produce, all meat/seafood, selected dairy, selected shelf-stable from RFP Appendix C). This is a new parameter in v4.

The required subsidy to fund this price reduction:
```
s_required = 0.30 × κ × Revenue_j_core − Rent_j − Tax_j
```
where `Revenue_j_core = κ × Revenue_j`.

For FRESH-type analysis: `Δp_j = θ × s / Q_j` is retained (with θ as a scenario), because there is no contractual specification of which items are discounted.

---

### Q6 — How is p_j estimated?

Current approach in [`code/build_p_j.py`](code/build_p_j.py): a 10-item basket from Crossa et al. 2023 (NYC DOHMH 2019 food pricing survey, 163 NYC supermarkets, Bronx average), CPI-adjusted to the current month using BLS series CUURS12ASAF11.

The Crossa 10-item basket includes: bread, milk, eggs, cheese, sugar, orange juice, coffee, canned corn, macaroni, and one fresh item — which overlaps substantially with the RFP core basket. So `p_j` from build_p_j.py **approximates the core basket price**, not the full-store average.

**Recommendation for v4:** Keep `p_j` as the overall basket price for the utility function (consumers respond to overall store price level), and add notation `p_core_j ≈ p_j` (noting that the Crossa basket is a close proxy for the RFP core basket). Document the approximation explicitly. The price reduction entering utility is:
```
Δp_j = 0.30 × κ × p_j    (in V_ij)
```

---

### Q7 — How is the BLS CES data constructed?

From [`code/parse_bls_ces_xlsx.py`](code/parse_bls_ces_xlsx.py):

- **`ces_food_at_home_by_income_bracket.csv`**: Annual food-at-home spending per consumer unit by CES income bracket (10 brackets). Source: **national** BLS Consumer Expenditure Survey, income-before-taxes tables, 2020–2024. Model groups are constructed as a **simple unweighted average** of adjacent brackets:
  - Low (<$25K): mean of `lt_15k` and `15_to_29k` brackets
  - Mid ($25–50K): mean of `30_to_39k` and `40_to_49k` brackets
  - High (>$50K): unweighted mean of the 5 brackets above $50K

- **`ces_fbar_by_income_group_from_xlsx.csv`**: Weekly f_bar = annual_usd / 52 for the most recent CES year (2024), one row per model group.

**What value is represented:** Annual food-at-home expenditure per consumer unit (≈ household), in current dollars. This is **not NYC-specific** — it is the US national average. Issue #13 in ISSUES_AND_GAPS.md flags this: NYC food spending is higher; the NYC metro BLS figure is $7,033/year for all households vs. $6,224 national. The income-group averaging is also unweighted within brackets, not population-weighted.

---

## Design decisions requiring your approval before drafting v4

These are listed in order of importance to the model structure.

1. **SNAP utility bonus δ_SNAP_i**: Add SNAP term to V_ij for low/mid income groups? If yes, source δ from Hillier et al. (2017) coefficient (requires reading that paper's table), or set as a scenario value (e.g., equivalent to a $2–3 price advantage)?

2. **β_d_i structural formula**: Use `β_d_i = α_car × car_free_share_i + α_inc × income_index_i`? Which demographic variables to include? Whether to cap the number of terms at 2 for simplicity?

3. **β_p_i derivation**: Derive from β_d_i / WTP_ratio (Chris's recommended approach)? Or keep as a separate parameter per income group?

4. **θ for FRESH-type subsidies**: Scenarios only (0, 0.40, 0.85), or include an elasticity-based derivation section showing the formula θ = f(ε_demand)?

5. **Core basket share κ**: Estimate from BLS CE food category shares (cereals + meat/poultry/eggs + dairy + fruits/vegetables), or map RFP Appendix C list directly to BLS CE categories? (The two approaches give slightly different values.)

6. **Trips per year T**: Fix Issue #4 (welfare currently per trip, not per year) by multiplying ΔCS by T = 52. Use a single T for all groups, or differentiate by income group (low-income households may shop more frequently at neighborhood stores)?

7. **Fix placeholder numbers in v3**: The worked example uses 5,900 households (actual = 19,922) and contains arithmetic errors (Issues #4, #5, #6). Replace with correct values in v4, or note as illustrative only?

---

## Document changes for v4

The two files to produce:

**File 1:** `docs/LEVEL_1_NYC_Grocery_Subsidy_Model_Specification_v4.docx`

Changes from v3:

- **Sec 1.1.1**: Add `δ_SNAP_i · snap_j` term to V_ij; update term table.
- **Sec 1.1.2**: Replace 3-group fixed-β table with 48-consumer-type (16 tracts × 3 income groups) specification. Add structural formula for β_d_i and β_p_i derivation from WTP ratio. Update term table with new symbols.
- **Sec 1.1.4 / 1.1.5**: Add trips-per-year multiplier T to ΔCS (fix Issue #4). Correct welfare per trip → per year.
- **Sec 1.2.1**: Add square-footage-based Q_j estimation method (FMI benchmarks). Add store type sales_per_sqft table. Clarify that p_j is the overall basket approximated by the Crossa 10-item basket.
- **Sec 1.3.1 (new split)**: Separate into two sub-sections:
  - 1.3.1a — NYC Groceries (contracted): `Δp_j = 0.30 × κ × p_j`, θ = 1, s is solved backwards.
  - 1.3.1b — FRESH-type (market): `Δp_j = θ × s / Q_j`, θ = scenarios {0, 0.40, 0.85}.
- **New Sec 1.3.0**: Define `κ` (core basket share), source from BLS CE categories cross-referenced with RFP Appendix C.
- **Sec 1.4 / Goal 1**: Update the causal direction for NYC Groceries: Δp is fixed → solve for s.
- **Sec 2.0 Phase 0**: Update store universe to Ag & Markets filtered + SNAP active as e_j. Remove references to DOHMH as primary source.
- **Appendix A**: Replace placeholder household counts (5,900 → 19,922 actual), fix arithmetic errors.
- **Appendix D**: Add acknowledgement of IIA limitation and BLP calibration assumption.
- **Appendix F (param table)**: Add δ_SNAP_i, κ, T (trips/year), sales_per_sqft_j; update β_d_i and β_p_i rows with structural formula source.

**File 2:** `docs/LEVEL_1_NYC_Grocery_Subsidy_Model_v3_to_v4_changes.docx`

A companion document explaining each change in plain English for someone familiar with v3 only, organized as: (a) what the equation was, (b) what it is now, (c) why it changed.

---

## Key files referenced

- [`LEVEL_1_NYC_Grocery_Subsidy_Model_Specification_v3_drive.docx`](LEVEL_1_NYC_Grocery_Subsidy_Model_Specification_v3_drive.docx) — source doc
- [`docs/chris_params_inventory.md.docx`](docs/chris_params_inventory.md.docx) — β and θ sourcing
- [`code/build_p_j.py`](code/build_p_j.py) — p_j estimation (Crossa 2023 + CPI)
- [`code/parse_bls_ces_xlsx.py`](code/parse_bls_ces_xlsx.py) — f_bar construction
- [`data/bls/ces_fbar_by_income_group_from_xlsx.csv`](data/bls/ces_fbar_by_income_group_from_xlsx.csv) — f_bar values (national CES, simple avg)
- [`docs/ISSUES_AND_GAPS.md`](docs/ISSUES_AND_GAPS.md) — Issues #4 (trips), #5 (β calibration), #9 (SNAP filter)
- [`docs/SIMPLIFIED_PLAN_AND_SOURCES.md`](docs/SIMPLIFIED_PLAN_AND_SOURCES.md) — κ, FMI benchmarks, θ scenarios
- RFP PDFs in `docs/research_papers/` — core basket definition, contract structure
