# Samuel run: what changes when beta_p is not calibrated

Script: `code/samuel_run.py` (reuses `run_model.py` / `model.py` unchanged; the calibration switch
is turned off in memory only). Chris's results in `results/chris_*` were not modified (all 16 files
hash-identical before and after).

| Setting | beta_p level | alpha | Runs |
|---|---|---|---|
| Chris (baseline) | recalibrated in every case so N.Y.C. Groceries at 30% off sells its $12.0M capacity (base scale 0.1368) | refit | 0-4 |
| Option 1 `option1_derived_beta/` | derived level (USDOT value of time), scale 1.0 everywhere | refit | 0-4 |
| Option 2 `option2_fixed_beta_sweep/` | fixed at the base calibrated scale 0.1368 in every sweep case | refit | 2 |

Comparison tables are in `comparison/`.

## Bottom line

1. **Option 2 shows that the beta_p recalibration was not washing out most sweep results.** With
   beta_p held fixed, the lever ranking is identical to Chris's in 11 of 12 cases, and ΔCS per $
   moves by 0.01 or less in the distance, store-size, high-income-distance, revenue and Food Fair tax
   cases. The exceptions are the cases that change the size of the per-trip price cut:
   - **Core basket share (κ) now matters.** Contract ΔCS/$ is 0.872 at κ low and 0.749 at κ high,
     against 0.808 in the base case. Chris's numbers were 0.800 / 0.811. His recalibration offset
     κ by moving the beta_p scale from 0.22 down to 0.10, so the ±0.06 swing was hidden.
   - **40 trips/yr:** contract 0.757 and N.Y.C. Groceries 0.759 (Chris: 0.808 / 0.809).
   - **The N.Y.C. Groceries capacity ±25% cases become identical to Base.** Capacity only enters
     through the beta_p calibration. This is the one case where the ranking changes, because Chris's
     −25% case had the contract ahead of N.Y.C. Groceries.
2. **Option 1 (derived beta_p) is a stress test, not a credible alternative.** At scale 1.0, store
   demand is about 7 times more price-sensitive: own-price elasticity is 14 to 19, against about 2.5.
   Under a 30% contract, the model predicts sales that are physically implausible:
   - N.Y.C. Groceries sells $56.3M, which is 4.7 times its $12.0M capacity and half of all CD2
     grocery spending.
   - Key Food sells $62.0M, 5.2 times its revenue.
   - JJ Southern Farm's core-basket sales reach 30 times its revenue.
3. **Under option 1, contract ΔCS per $ falls from about 0.81 to about 0.52, and the ranking flips
   to Rent > N.Y.C. Groceries > 30% contract > FRESH.** The flip is mostly mechanical; see the
   mechanism section. N.Y.C. Groceries still edges out the existing-store contract in every setting
   (0.809 vs 0.808 for Chris, 0.530 vs 0.523 for option 1).
4. **Under option 1, the low-income share of gains rises sharply for the contract-type levers:**
   - 30% contract: 0.37 to 0.59.
   - N.Y.C. Groceries: 0.35 to 0.58.
   - FRESH: 0.29 to 0.25 (slight fall).
   - Rent: 0.30 to 0.28 (slight fall).

   Low-income households have the largest derived beta_p (0.43, elasticity 29), so they switch
   stores the most.

## Option 1: derived beta_p (scale 1.0)

### Calibration (run 0)
- The 9-store total still matches (predicted / CD2 spending = 0.4865), because alpha absorbs it.
- The store constants hardly move: supermarket −1.87 vs −1.71, small −3.03 vs −3.10.
- The per-store fit is about as good overall (mean absolute error about 22% vs about 20%), but the
  pattern differs:
  - Fine Fare is badly under-predicted (0.46 of observed, vs 1.01).
  - Key Food is over-predicted (1.16, vs 0.75).
  - C-Town (809) improves (1.19, vs 1.41).
  - The small stores are unchanged.
- Own-price elasticity by income group:
  - Low: 29.4 (Chris 4.4).
  - Mid: 12.3 (Chris 1.7).
  - High: 8.3 (Chris 1.1).

  The revenue fit alone cannot tell the two beta_p levels apart. Only the N.Y.C. Groceries capacity
  anchor does that.

### Full levers (runs 1 / 1b)

| Lever | ΔCS/$ Chris | ΔCS/$ option 1 | median cost Chris | median cost option 1 | max sales / capacity option 1 |
|---|---|---|---|---|---|
| 30% contract at existing store | 0.808 | 0.523 (0.41-0.66) | $2.13M | $10.10M | 30.3 |
| N.Y.C. Groceries | 0.809 | 0.530 | $2.22M | $10.46M | 4.7 |
| Rent subsidy, θ = 0.5 | 0.507 | 0.566 | $0.18M | $0.18M | n/a |
| FRESH tax break, θ = 0.5 | 0.502 | 0.514 | $0.03M | $0.03M | n/a |

- **Absolute ΔCS roughly triples:** the contract median goes from $1.72M to $5.35M, and N.Y.C.
  Groceries from $1.80M to $5.54M.
- **Cost rises about 5 times,** because contract cost is 30% of the much larger post-policy sales.
- **The per-store spread widens.** Under the contract, ΔCS/$ runs from 0.41 at the small stores to
  0.66 at Key Food, against 0.79-0.81 for Chris.

### Pass-through and effective discount (run 3)
- **FRESH and rent at full pass-through (θ = 1) exceed $1 of ΔCS per $:** FRESH 1.06, rent 1.30
  (Antillana 1.70). Chris's values are 1.01 and 1.03. See the mechanism section; this is a modeling
  artifact, not a real gain.
- **The θ needed to match the contract drops:**
  - FRESH: 0.49-0.52 (Chris 0.80).
  - Rent: 0.40-0.49 (Chris 0.79-0.80).
- **Whole-basket discount:** contract ΔCS/$ is 0.556 vs 0.523 on the core basket. That is the
  opposite direction from Chris's results (0.712 vs 0.808). Sales-to-capacity reaches 44 times.

### Capital cost (run 4)
- N.Y.C. Groceries with its share of the $70M build-out gives ΔCS/$ of 0.496 (low case) and 0.482
  (high case), against Chris's 0.612 / 0.553.
- Capital shifts the result less in option 1 because the operating cost is 5 times larger.

### Sweep (run 2)
- **Every case ranks Rent > N.Y.C. Groceries > contract > FRESH,** except Core basket low and
  Revenue low. Those two rank Rent > FRESH > N.Y.C. Groceries > contract.
- **κ moves the result in the opposite direction from option 2:** contract ΔCS/$ is 0.488 at κ low
  and 0.548 at κ high. This is a symptom of saturation (see the mechanism section).

## Why the results move this way (mechanism)

- **Contract-type levers (contract, N.Y.C. Groceries):** cost is 30% of core sales *after* the
  policy, Δp × Q1. ΔCS is about Δp × ½(Q0 + Q1). So ΔCS/$ ≈ ½(1 + Q0/Q1), which falls toward 0.5
  as switching grows. Chris's calibration fixes Q1/Q0 for N.Y.C. Groceries at a modest level, which
  gives about 0.81. At the derived beta_p, median store sales grow about 9 times, which gives about
  0.52.
- **Fixed-budget levers (FRESH, rent):** cost is a fixed dollar amount, but the price cut θ·s/Q0 is
  computed on *baseline* baskets. So ΔCS/$ ≈ θ × ½(1 + Q1/Q0), which *rises* with elasticity. At
  θ = 1 it goes above 1. The store is then implicitly funding the price cut on all the extra baskets
  it attracts. That is why rent overtakes the contract in option 1: the ranking depends on the
  assumed θ = 0.5 and on this cost convention, not on rent being a better policy.
- **Saturation:** at the derived beta_p, a single discounted store captures about half of all CD2
  spending. Once most of the households who would switch have switched, a deeper discount goes
  mostly to existing customers. In that regime a larger κ (or the whole basket) *raises* ΔCS/$,
  which reverses the sign seen in Chris's results and in option 2. The rule-of-half intuition no
  longer applies.

## What this says about recalibration
- **The capacity anchor is what pins the beta_p level.** Revenue data alone fit both levels about
  equally well. Without the anchor, the derived beta_p predicts that discounted stores would sell 5 to
  30 times their revenue. So some anchor of this kind is needed. The open question is whether
  capacity, or an external elasticity estimate, is the better anchor.
- **Re-fitting beta_p within each sweep case mostly did not change conclusions,** since option 2
  matches Chris on rankings. It did hide the sensitivity to κ and to trips per year. For those cases,
  option 2's numbers are the more informative robustness check: 0.75-0.87 rather than 0.80-0.81.
- **The N.Y.C. Groceries vs existing-store contract comparison is robust** to every beta_p setting
  tested. The position of rent and FRESH relative to those two is not.

## Caveats
- **Inherited labels in option 1's run 0:** `calibration_summary.csv` labels the scale row
  "calibrated to N.Y.C. Groceries capacity", and the "run" columns say "Chris run N". Both come from
  `run_model.py`. In option 1 the scale is simply 1.0.
  `comparison/calibration_summary_compare.csv` strips the label.
- **Capacity ±25% cases equal Base** in both options, by construction.
- **Option 2 covers run 2 only.** Its base case reproduces Chris's base exactly.
- **Figures were not regenerated:** `make_figures.py` writes into `chris_run1_base/`, so it was not
  run.
- **Sales-to-capacity comes from the per-store tables.** The sweep output does not report it, so
  option 2's capacity overshoot in the κ-high and 40-trips cases is not measured here.
