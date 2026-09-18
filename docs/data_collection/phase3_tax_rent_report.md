# Phase 3: Tax_j and Rent_j Matching Report

**Study area:** Bronx Community District 2  
**Code:** [`code/phase3_tax_rent.py`](../../code/phase3_tax_rent.py)  
**Outputs:** [`data/phase3/`](../../data/phase3/)  
**Inputs:** Phase 2 CD2 store lists (Ag & Markets, SNAP, DOHMH)

---

## Goal

For each of the three Phase 2 store inventories, match store addresses to:

1. **BBL** (Borough–Block–Lot)
2. **`Tax_j`** — annual property tax proxy for the tax-break instrument
3. **`Rent_j`** — annual rent for the rent-subsidy instrument  
   - **Path A:** ACRIS lease-related documents  
   - **Path B:** `square_footage ×` market rate ($20 / $27.50 / $35 per sq-ft / year)

Document every data source attempted and per-list **success rates**.

---

## Pipeline summary

```text
Store CSV → normalize address → NYC GeoSearch (BBL)
                              → PLUTO fallback if needed
         → PLUTO assessed values
         → DOF Property Charges Balance → Tax_j
         → DOF Assessment Data (attempted)
         → ACRIS Legals + Master → lease docs / Rent_j_acris
         → sq-ft × market rate → Rent_j_low/mid/high
```

---

## Attempts (what was tried)

### 1. Address → BBL — SUCCESS (primary)

| Item | Detail |
|------|--------|
| **Source** | NYC GeoSearch (Planning Labs / PAD) |
| **URL** | https://geosearch.planninglabs.nyc/docs/ |
| **Endpoint** | https://geosearch.planninglabs.nyc/v2/search?text={address} |
| **Field used** | `features[0].properties.addendum.pad.bbl` |
| **Auth** | None |
| **Result** | Primary matcher for all three lists |

### 2. Address → BBL fallback — PLUTO — USED when GeoSearch misses

| Item | Detail |
|------|--------|
| **Source** | Primary Land Use Tax Lot Output (PLUTO) |
| **Dataset** | `64uk-42ks` |
| **URL** | https://data.cityofnewyork.us/City-Government/Primary-Land-Use-Tax-Lot-Output-PLUTO-/64uk-42ks |
| **API** | https://data.cityofnewyork.us/resource/64uk-42ks.json |
| **Method** | `$where` Bronx address prefix match |
| **Result** | Occasional rescue when GeoSearch returns no BBL |

### 3. Tax context — PLUTO assessed values — SUCCESS

| Item | Detail |
|------|--------|
| **Fields** | `assesstot`, `assessland`, `exempttot`, `ownername`, `bldgclass`, `lotarea`, `bldgarea` |
| **Role** | Assessed-value context (not the annual tax bill) |
| **Result** | Near-complete for stores with BBL |

### 4. Tax_j — DOF Property Charges Balance — SUCCESS (primary Tax_j)

| Item | Detail |
|------|--------|
| **Source** | DOF: Property Charges Balance |
| **Dataset** | `scjx-j6np` |
| **URL** | https://data.cityofnewyork.us/City-Government/DOF-Property-Charges-Balance/scjx-j6np |
| **API** | https://data.cityofnewyork.us/resource/scjx-j6np.json?parid={BBL}&code=CHG |
| **Method** | Sum `sum_liab` for latest `taxyear`; if &lt;4 quarters present, annualize × (4/n) |
| **Result** | Primary `Tax_j` column |
| **Caveat** | **Lot-level** tax, not store-only. Mixed-use BBLs can look very large relative to a single retail tenant. Validate before using as instrument upper bound. |

### 5. Tax — DOF Assessment Data — ATTEMPTED, sparse

| Item | Detail |
|------|--------|
| **Dataset** | `xw8u-vy7p` |
| **URL** | https://data.cityofnewyork.us/City-Government/Assessment-Data/xw8u-vy7p |
| **API** | https://data.cityofnewyork.us/resource/xw8u-vy7p.json?parid={BBL} |
| **Result** | Often empty for queried BBLs; recorded as `assessment_ok` false when no rows |
| **Status** | Attempted; not used as primary `Tax_j` |

### 6. Tax — NYCDB / taxbills.nyc — DEFERRED

| Item | Detail |
|------|--------|
| **NYCDB** | https://nycdb.info/ — requires Postgres + ETL; not installed this phase |
| **taxbills.nyc** | Historical 2015 bill scrape (stale); not used |
| **Status** | Documented only; deferred |

### 7. Rent path A — ACRIS — PARTIAL SUCCESS

| Item | Detail |
|------|--------|
| **Legals** | `8h5j-fqxa` — https://data.cityofnewyork.us/City-Government/ACRIS-Real-Property-Legals/8h5j-fqxa |
| **Master** | `bnx9-e6tj` — https://data.cityofnewyork.us/City-Government/ACRIS-Real-Property-Master/bnx9-e6tj |
| **Doc codes** | `7isb-wh4c` — https://data.cityofnewyork.us/City-Government/ACRIS-Document-Control-Codes/7isb-wh4c |
| **Method** | Parse BBL → borough/block/lot → Legals `document_id` → Master; keep lease-related types: `LEAS`, `MLEA`, `ASSTO`, `TERL`, `SUBL` |
| **Portal** | https://a836-acris.nyc.gov/ |
| **Result** | ~11% of Ag & Markets / SNAP BBLs have a lease-related document; **dollar amounts rarely usable as annual rent** (`document_amt` often 0 or not annual) |
| **Caveat** | ACRIS rarely yields a clean annual `Rent_j`. Market-rate fallback is the operational bound for most stores. |

### 8. Rent path B — sq-ft × market rate — SUCCESS where sq-ft exists

| Item | Detail |
|------|--------|
| **Sq-ft source** | Ag & Markets `square_footage` only (SNAP/DOHMH lack sq-ft) |
| **Rates** | $20 / $27.50 / $35 per sq-ft / year (Appendix F Hunts Point range) |
| **Columns** | `Rent_j_low`, `Rent_j_mid`, `Rent_j_high`; preferred `Rent_j` = mid when ACRIS amount missing |
| **Result** | 69.3% of Ag & Markets stores |

---

## Success rates (by store list)

Machine-readable copy: [`data/phase3/phase3_success_rates.json`](../../data/phase3/phase3_success_rates.json)

### Ag & Markets (`tax_rent_agmarkets_cd2.csv`) — n = 137

| Metric | Count | Rate |
|--------|------:|-----:|
| BBL matched | 136 | **99.3%** |
| `Tax_j` (DOF) | 125 | **91.2%** |
| PLUTO assessed fields | 136 | **99.3%** |
| ACRIS lease-related doc | 16 | **11.7%** |
| ACRIS dollar amount | 5 | **3.6%** |
| Market-rate rent (has sq-ft) | 95 | **69.3%** |
| Any rent signal (A or B) | 98 | **71.5%** |

Rent method mix: ACRIS amount 5 · market-rate 91 · none 39

### USDA SNAP (`tax_rent_snap_cd2.csv`) — n = 553

| Metric | Count | Rate |
|--------|------:|-----:|
| BBL matched | 552 | **99.8%** |
| `Tax_j` (DOF) | 508 | **91.9%** |
| PLUTO assessed fields | 552 | **99.8%** |
| ACRIS lease-related doc | 62 | **11.2%** |
| ACRIS dollar amount | 15 | **2.7%** |
| Market-rate rent | 0 | **0.0%** (no sq-ft in SNAP) |
| Any rent signal | 62 | **11.2%** |

Rent method mix: ACRIS amount 15 · market-rate 0 · none 491

### NYC DOHMH (`tax_rent_dohmh_cd2.csv`) — n = 9

| Metric | Count | Rate |
|--------|------:|-----:|
| BBL matched | 9 | **100%** |
| `Tax_j` (DOF) | 7 | **77.8%** |
| PLUTO assessed fields | 9 | **100%** |
| ACRIS lease-related doc | 0 | **0%** |
| Market-rate rent | 0 | **0%** (no sq-ft) |
| Any rent signal | 0 | **0%** |

---

## Failure modes observed

| Failure | Cause | Mitigation |
|---------|-------|------------|
| No BBL | Bad/incomplete address; GeoSearch + PLUTO both miss | Manual BBL / PAD lookup |
| No `Tax_j` | DOF charges empty for BBL (exempt, timing, condo unit quirks) | Use PLUTO assessed as soft proxy; NYCDB later |
| No ACRIS lease | Owner-occupied or lease not recorded / not coded as LEAS/MLEA/… | Market-rate path B |
| ACRIS amount unusable | `document_amt` = 0 or not annual rent | Prefer path B |
| No market rent | Missing `square_footage` (SNAP, DOHMH) | Join Ag & Markets sq-ft by address/BBL later |
| Inflated `Tax_j` | Whole-lot tax on mixed-use BBL | Scale by retail share / use as upper bound only |
| Assessment API empty | No row for `parid` in `xw8u-vy7p` | Rely on DOF charges + PLUTO |

---

## Output files

| File | Description |
|------|-------------|
| [`data/phase3/tax_rent_agmarkets_cd2.csv`](../../data/phase3/tax_rent_agmarkets_cd2.csv) | Ag & Markets + BBL + tax + rent |
| [`data/phase3/tax_rent_snap_cd2.csv`](../../data/phase3/tax_rent_snap_cd2.csv) | SNAP + BBL + tax + rent |
| [`data/phase3/tax_rent_dohmh_cd2.csv`](../../data/phase3/tax_rent_dohmh_cd2.csv) | DOHMH + BBL + tax + rent |
| `bbl_cache.json` / `tax_cache.json` / `acris_cache.json` | API response caches |
| `phase3_success_rates.json` | Rates above |
| `phase3_attempts_log.json` | Run log |

### Key columns

- `bbl`, `bbl_method`, `Tax_j`, `dof_taxyear`, `pluto_assesstot`
- `acris_lease_hit`, `Rent_j_acris`
- `rent_sqft`, `Rent_j_low`, `Rent_j_mid`, `Rent_j_high`
- `Rent_j` (preferred), `rent_method` ∈ {`acris`, `market_rate_sqft`, `acris_lease_no_amount`, `none`}

---

## Working citation links

1. NYC GeoSearch docs — https://geosearch.planninglabs.nyc/docs/  
2. NYC GeoSearch API — https://geosearch.planninglabs.nyc/v2/search  
3. PLUTO — https://data.cityofnewyork.us/City-Government/Primary-Land-Use-Tax-Lot-Output-PLUTO-/64uk-42ks  
4. PLUTO API — https://data.cityofnewyork.us/resource/64uk-42ks.json  
5. DOF Property Charges Balance — https://data.cityofnewyork.us/City-Government/DOF-Property-Charges-Balance/scjx-j6np  
6. DOF Charges API — https://data.cityofnewyork.us/resource/scjx-j6np.json  
7. DOF Assessment Data — https://data.cityofnewyork.us/City-Government/Assessment-Data/xw8u-vy7p  
8. ACRIS Real Property Legals — https://data.cityofnewyork.us/City-Government/ACRIS-Real-Property-Legals/8h5j-fqxa  
9. ACRIS Real Property Master — https://data.cityofnewyork.us/City-Government/ACRIS-Real-Property-Master/bnx9-e6tj  
10. ACRIS Document Control Codes — https://data.cityofnewyork.us/City-Government/ACRIS-Document-Control-Codes/7isb-wh4c  
11. ACRIS portal — https://a836-acris.nyc.gov/  
12. NYCDB (deferred) — https://nycdb.info/  
13. NYS Ag & Markets stores (sq-ft) — https://data.ny.gov/Economic-Development/Retail-Food-Stores/9a8c-vfzj  

---

## How to re-run

```bash
python code/phase3_tax_rent.py
```

Caches under `data/phase3/` make re-runs much faster.

---

## Bottom line for the model

- **`Tax_j`:** Usable for ~**91–92%** of Ag & Markets and SNAP stores via DOF charges (lot-level; treat carefully).  
- **`Rent_j`:** ACRIS almost never gives a clean annual rent (~3% with amounts). For Ag & Markets, **market-rate × sq-ft covers ~69%** and is the practical instrument bound. SNAP/DOHMH need sq-ft joins or surveys before path B works.  
- **Best modeling inventory for instruments:** Ag & Markets CD2 file (`tax_rent_agmarkets_cd2.csv`).

## Next steps (optional)

1. Crosswalk SNAP/DOHMH → Ag & Markets on BBL/address to inherit sq-ft.  
2. Validate outlier `Tax_j` values; optionally scale by PLUTO `retailarea / bldgarea`.  
3. Install NYCDB if bill-level annual tax is required beyond DOF charges.
