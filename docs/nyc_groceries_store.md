# N.Y.C. Groceries Store (Hunts Point): Inputs for the Model

Owner: Rahul · Last updated: 2026-09-29

This collects everything we know about the planned city grocery store in CD2, and what the model uses for it.

**Related files**
- Distances: [`d_ij_distances.md`](d_ij_distances.md) and [`data/distance/d_ij_cd2.csv`](../data/distance/d_ij_cd2.csv) (row "N.Y.C. GROCERIES (PLANNED)")
- Core basket share κ: [`kappa_core_basket.md`](kappa_core_basket.md) and [`data/bls/kappa_core_basket_share.csv`](../data/bls/kappa_core_basket_share.csv)
- Code: [`code/build_d_ij.py`](../code/build_d_ij.py), [`code/build_kappa.py`](../code/build_kappa.py)

## The store

| Item | Value | Source |
|---|---|---|
| Site | **Peninsula 1A, 1215 Spofford Ave, Unit 8, Bronx 10474** | RFP site listing (via [Obedio summary](https://hs.getobedio.com/blog/n.y.c.-groceries-operator-rfp-who-qualifies-what-the-city-pays-and-when-the-stores-have-to-open)) |
| Map location used | 40.81459, −73.88995 (the city-owned 1225 Spofford Ave lot, BBL 2027387502) | NYC PLUTO |
| Size | about **15,000 sq ft**, including mezzanine | RFP site listing |
| Opening | target **second half of 2027** | RFP site listing |
| Discount | **30% off Core Basket items** | [NYC Mayor's Office press release](https://www.nyc.gov/mayors-office/news/2026/07/mayor-mamdani-unveils-30--discount---including-all-produce--all-) |
| Operator | Private operator, chosen through NYCEDC RFP #11639 | RFP |

The site is inside CD2, in the Peninsula development on the old Spofford juvenile center campus.

## Model inputs

| Input | Value | Notes |
|---|---|---|
| **Distance (d_ij), miles** | Low 0.75 · Middle 0.64 · High 0.65 | About 15–18 minutes' walk. Closer than Food Universe and the 564 Southern Blvd C-Town, farther than the Westchester Ave stores. |
| **Size (for γ_sq)** | 15,000 sq ft | Same size as Key Food, our biggest existing store. |
| **Core basket share (κ)** | **0.60** (range 0.37–0.83) | Share of grocery spending on discounted items. |
| **Price cut** | Δp = 0.30 × κ × p_j ≈ **18%** of the basket price | Matches the "effective cut 18%" in Chris's plan. |
| **Pass-through (θ)** | 1 | The discount is written into the operator contract (RFP Round 1 Q&A, Q1). |
| **Affordability Payment** | **No published number** | See below. |

## Affordability Payment

The city pays the operator an **Affordability Payment** to cover the 30% discount. What we found:

- The RFP gives **no dollar amount or percentage**. It says the amount will be set in negotiations with the operator.
- The [Round 1 Q&A](https://edc.nyc/sites/default/files/2026-08/26.08.14_Round%201%20Q&A%20vF.pdf) says it will be **sized to cover the 30% Core Basket discount** (Q1), and it has an **annual cap** agreed with the operator that isn't published (Q5).
- It's funded separately from capital, rent and tax relief (Q5).

**So we have to estimate it.** The simplest estimate is the cost of the discount itself:

> Affordability Payment ≈ 0.30 × κ × Revenue_j

For example, if the store sold as much as Key Food ($8.03M in 2024), that would be 0.30 × 0.60 × $8.03M ≈ **$1.45M a year**. This is only an illustration; the store has no sales history yet.

## Caveats

1. **Site details come from a secondary summary** of the RFP, because the NYCEDC website blocked automated access. They should be checked against the RFP PDF itself.
2. **The map point is approximate.** There's no city lot numbered 1215 Spofford Ave; the Peninsula is listed as 1201–1225, so we use the 1225 lot. Any error is well under a block.
3. **The store isn't open.** It has no sales, rent or tax history, so its sales for the model must come from its size (for example, 15,000 sq ft × the $360/sq ft rate used for the other stores ≈ $5.4M) or from a team assumption.
4. **The Core Basket list is preliminary** and will be refined with the operator, so κ may change.
