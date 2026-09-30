# Tax_j: property tax for the 9 CD2 candidate stores, fiscal year 2025

Built by `code/build_tax_j.py`. Fiscal year 2025 = July 1, 2024 to June 30, 2025, to match the team's 2024 base year.

Run order: `python code/build_tax_j.py`, then `python code/build_rent_nopv.py`, then `python code/build_tax_j.py` again (the second run fills the check against the Notices of Property Value).

## Files

| File | Contents |
|---|---|
| `candidate_store_lots.csv` | Store, license number, Ag & Markets sq ft, tax lot (BBL), lot type, and the lot PLUTO describes |
| `raw/dof_charges_{bbl}.json` | Every property tax charge row (`code = CHG`) DOF publishes for the lot, unchanged |
| `pluto_candidate_lots.csv` | PLUTO floor areas (building, commercial, retail, residential), buildings, class, assessed value |
| `tax_j_cd2_candidate_stores.csv` | Lot tax, store share, `Tax_j`, notice check and flags, one row per store |
| `tax_j_meta.json` | Sources, fiscal year, duplicate-handling and store-share rules |

## Sources

- Tax bills: DOF Property Charges Balance, NYC Open Data `scjx-j6np`, property tax charges only (`code = CHG`).
- Floor area: MapPLUTO, NYC Open Data `64uk-42ks` (`bldgarea`).
- Store sq ft: NYS Ag & Markets retail food store licenses (`data/stores/large_grocery_stores_cd2.csv`).
- Check: estimated property tax printed on each lot's 2024-25 Notice of Property Value (`data/rent/nopv_income_fy2025.csv`).

## Method

1. **Lot tax.** DOF repeats each installment in every monthly extract and adds a row when a payment posts; its `taxyear` field can also hold the prior year's installments. The script keeps installments whose billing period falls inside the fiscal year, takes the latest extract, counts each billing period once (largest liability) and sums. Quarterly and semiannual payers both come to 12 months, so nothing is annualized. This fixes the Phase 3 values in `data/phase3/`, which were about 4 times too high (Key Food about 8 times).
2. **Store share** = store sq ft / PLUTO building area, capped at 1. The tax covers the whole lot, including upper floors and apartments, so total building area is the denominator.
3. **Tax_j** = lot tax x store share.

## Things to know

- **Fine Fare** is a condo unit. The building's billing lot (2027037501) has no tax bill; the store's own unit lot (2027031001, the parcel number in ReferenceUSA) does, so its share is 1.
- **Key Food**: its 15,000 sq ft (Ag & Markets) is more than the building's commercial area (12,810 sq ft), and the building has 63 apartments above the store. The floor-area split is rough.
- **Food Fair** (5 buildings, 17 storefronts) and **Antillana** (4 buildings) share their lots with other tenants.
- **Notice check:** 7 lots are within 1.6% of their notice (the notice used the 2023-24 rate, 10.592%). JJ Southern Farm (-26%) and Sagal (-21%) were billed less because DOF reduced installments during the year, typically a Tax Commission reduction or abatement. The final billed amount is used.
- Whether the store actually pays this tax depends on its lease (net vs gross). Owner-occupied stores pay it directly.
