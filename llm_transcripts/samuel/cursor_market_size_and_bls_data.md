# Market size and BLS data
_Exported on 10/4/2026 at 10:40:34 EDT from Cursor (3.17.8)_

---

**User**

Review the file "LEVEL_1_... .docx" and the files in \docs. I would like to make some changes, but first I have some questions

1. How was the market size and f_bar calculated? (data\cd2_market_size_M_from_xlsx.csv, data\ces_fbar_by_income_group_from_xlsx.csv) I would like to use the weighted average using the number of units in each income group. It was likely created in code\parse_bls_ces_xlsx.py.
2. Is there the same consumption BLS CES data for the NYC region (with the categories "food-at-home"? Is it broken down by income group? Where can I find this data?

---

**Cursor**

I'll look at the Level 1 doc, the docs folder, and the parsing script to answer both questions.

The doc points to CES "Table 4700" for the NYC metro area. I'll check what the docs folder already says about regional CES data.

Right now \(\bar f\) for each income group is a **simple (unweighted) average** of the national CES brackets it covers, not weighted by consumer units. For question 2: CES food-at-home data exists for the New York metro area, but BLS doesn't publish it broken down by income. Income breakdowns are only published nationally and for the Northeast region.

## 1. How \(M\) and \(\bar f\) are calculated now

You were right that both files come from `code/parse_bls_ces_xlsx.py` (the outputs are in `data/bls/`). It reads the "Food at home → Mean" row from each national CES Table 1203 (`cu-income-before-taxes-{year}.xlsx`). It then collapses the nine CES income brackets into the model's three groups by simple averaging:

```59:71:code/parse_bls_ces_xlsx.py
    # Model income groups: Low <$25k ~ lt_15k + 15_to_29k avg; Mid $25-50k; High >$50k
    low = [out["lt_15k"], out["15_to_29k"]]
    mid = [out["30_to_39k"], out["40_to_49k"]]
    high = [
        out["50_to_69k"],
        out["70_to_99k"],
        out["100_to_149k"],
        out["150_to_199k"],
        out["200k_plus"],
    ]
    out["model_low_lt25k_approx"] = round(sum(x for x in low if x) / len([x for x in low if x]), 2)
    out["model_mid_25_50k_approx"] = round(sum(x for x in mid if x) / len([x for x in mid if x]), 2)
    out["model_high_gt50k_approx"] = round(sum(x for x in high if x) / len([x for x in high if x]), 2)
```

- **`ces_fbar_by_income_group_from_xlsx.csv`** uses only the latest year (2024). Each group's weekly \(\bar f\) is its annual average divided by 52. The "All consumer units" row is the national all-households mean divided by 52. It isn't weighted to Bronx CD2's income mix.
- **`cd2_market_size_M_from_xlsx.csv`** has one row per ACS year, matched to the CES release of the same year. It holds two versions of \(M\):
  - `M_usd_all_cu_mean` = \(N_{HH} \times\) the national all-households annual food-at-home mean.
  - `M_usd_income_weighted` = \(\sum_g n_g \times \bar f_g^{annual}\), where the household counts \(n_g\) come from ACS table B19001 (`data/acs/cd2_household_income_summary.csv`).

**What changes with consumer-unit weighting.** Each CES file has a "Number of consumer units (in thousands)" row, so the weighted version is \(\bar f_g = \sum_{b \in g} N_b f_b \,/\, \sum_{b \in g} N_b\). I ran it read-only on the 2024 file:

| Group | Current, simple average | Weighted by consumer units |
|---|---|---|
| Low | \$3,737 (\$71.87/wk) | \$3,773 (\$72.55/wk) |
| Mid | \$4,603 (\$88.52/wk) | \$4,603 (\$88.52/wk) |
| High | \$7,421 (\$142.71/wk) | \$7,314 (\$140.66/wk) |
| \(M\) (2024) | \$106.02M | \$105.51M |

The biggest change is in the High group. The \$200k+ bracket has the highest spending but fewer households than the \$100–150k bracket, so a simple average overweights it. Over 2020–2024 the weighted \(M\) comes out about 0.5–3% lower. The Mid group is unchanged in 2024 because both of its brackets happen to be \$4,603 in the source file; I checked this against the spreadsheet and it isn't a parsing error.

**Other issues worth fixing while you're in this code:**
- **The income brackets don't line up.** The Low group is labelled "<\$25K", but it uses the CES "\$15,000–\$29,999" bracket, so on the CES side it really means under \$30K. On the ACS side, `download_acs.py` counts Low as B19001_002–005 (under \$25K) and Mid as 006–010 (\$25K–\$50K). So households earning \$25–30K are counted as Mid but get spending values from the Low brackets. One fix is to split the \$15–30K bracket, or relabel the groups.
- **"All consumer units" in `ces_fbar_by_income_group_from_xlsx.csv` is the national average.** An \(\bar f\) weighted to CD2's income mix would be \(M_{weighted} / N_{HH} / 52\), which is about \$102/week for 2024, not \$119.69.
- **The doc and the code cite different tables.** The Level 1 doc cites "Table 4700 (food-at-home by income quintile)", but the code uses Table 1203 (income before taxes). The doc also says "NYC metro", while all of these numbers are national.

## 2. BLS CES data for the NYC region

These are the published options, from most local to least:

- **NYC metro area (the New York–Newark–Jersey City MSA).**
  - **Where:** the BLS page [CE geographic tables](https://www.bls.gov/cex/tables/geographic/mean.htm), in the metropolitan-area tables. The files are grouped by region, so New York is in the Northeast file.
  - **Food at home:** yes, with sub-items such as cereals, meats, dairy, and fruits/vegetables.
  - **By income:** no. These tables cover all households only.
  - **Caveats:** figures are published as two-year averages (e.g. 2023–24) and have large standard errors.
  - **Also useful:** BLS's regional office publishes a narrative release, "Consumer Expenditures for the New York Area," comparing NYC spending shares with the U.S. It's also not broken down by income.

- **Northeast region.**
  - **Where:** the same geographic tables page, plus the cross-tabulated tables (region by income before taxes, and region by income quintile).
  - **Food at home:** yes.
  - **By income:** yes. This is the most local published income breakdown.

- **Microdata (CE Public-Use Microdata, PUMD).**
  - **Where:** [bls.gov/cex/pumd.htm](https://www.bls.gov/cex/pumd.htm).
  - **What it gives you:** you'd build your own table. The household interview file has food-at-home spending variables (e.g. `FDHOMEPQ`/`FDHOMECQ`), household income, survey weights, and a sampling-area (PSU) code that identifies a few of the largest metros, including New York.
  - **Caveat:** the NYC sample split by income group will be thin, so check the standard errors.

A common approach is to keep the income *profile* from the Northeast (or national) table and rescale it to the NYC metro level:

\[
\bar f_g^{NYC} = \bar f_g^{Northeast} \times \frac{\bar f_{all}^{NYC\,MSA}}{\bar f_{all}^{Northeast}}
\]

One practical note: `data/bls/bls_download_meta.json` records that automated downloads from bls.gov returned HTTP 403 errors. You'll probably need to download these files by hand in a browser, like the existing ones in `data/bls/`.

I'm in Ask mode, so I haven't changed any files. Switch to Agent mode if you'd like me to add the consumer-unit weighting, fix the bracket mismatch, or add a parser for the NYC metro and Northeast tables.

---

**User**

I downloaded data/bls/cu-region... and cu-msa... files. Review these files and outline your approach to updating f_bar, and updating M

---

**Cursor**

I'll look at the new region and MSA files you downloaded, then outline the approach.

**Weighting choice for f_bar and M**

> **When collapsing the Northeast CES brackets into Low/Mid/High, whose household counts should weight each bracket? (2023-24 Northeast data, ACS 2024)

A) CD2's own ACS B19001 counts: Low $81.60/wk, Mid $94.12/wk, High $146.86/wk, M = $112.9M. Matches Hunts Point's income mix; High is lower because most CD2 households in that group earn $50-100k.

B) Northeast CES consumer-unit counts (what you described): Low $82.06/wk, Mid $94.69/wk, High $161.01/wk, M = about $118.7M. The Northeast's High group is skewed toward $100k+.**
> - A) Weight by CD2 ACS household counts per bracket (Recommended) ✔
> - B) Weight by Northeast CES consumer-unit counts
> - Compute both; use A as primary and report B as a sensitivity

> **What should this change cover?**
> - Update the parser and output CSVs only
> - Update the parser and CSVs, and also revise the M and f_bar text/table rows in the LEVEL_1 docx
>
> Answer: Update the parser, and create new CSV files. Create a .md file that will log all changes and new files. This .md file will be used to create a new document

---

**User**

Implement the plan as specified, it is attached for your reference. Do NOT edit the plan file itself.

To-do's from the plan have already been created. Do not create them again. Mark them as in_progress as you work, starting with the first one. Don't stop until you have completed all the to-dos.

---

**Cursor**

I've updated \(\bar f\) and \(M\) using the Northeast and NYC-metro CES data, weighted by Bronx CD2's own household income counts from the ACS. For ACS 2024, \(M\) is now about **\$113.0M**, up from \$106.0M (+6.6%). The CD2-wide \(\bar f\) is **\$109.06/week**. All the consistency checks pass. One step is blocked: the full script run fails because `data/bls/cd2_market_size_M_from_xlsx.csv` is open in Excel.

| Group | Before (national, simple average) | Now (Northeast, CD2-weighted, NYC-scaled) |
|---|---|---|
| Low (<\$25K) | \$71.87/wk | \$81.64/wk |
| Mid (\$25–50K) | \$88.52/wk | \$94.17/wk |
| High (>\$50K) | \$142.71/wk | \$146.94/wk |
| CD2 overall | \$119.69/wk (national mean) | \$109.06/wk |

**Why the numbers moved:**
- **Low and Mid rise** because low-income households in the Northeast spend more on groceries than the national figures showed.
- **High rises only a little.** Most CD2 High-group households earn \$50–100K, so the \$150K+ brackets now count for little.
- **The NYC scaling barely matters.** It multiplies by 1.0006, because New York metro food-at-home spending (\$7,033) is almost identical to the Northeast's (\$7,029).

**What changed in `code/parse_bls_ces_xlsx.py`:**
- New readers for the Northeast-by-income table (3104) and the Northeast metro-area table (3004). These tables put values on the item row itself rather than a separate "Mean" row, and footnote codes become blanks.
- A mapping from ACS income brackets to CES brackets. The ACS \$60–75K bracket crosses the CES \$70K line, so it's split 2/3 below and 1/3 above.
- A new function that computes \(\bar f\) and \(M\) for each ACS year from 2020 to 2024. It stops with an error if the bracket counts don't add up to the total households.
- `main()` runs this new step after the existing national one, whose outputs are unchanged and kept for comparison.

**New files:**
- `data/bls/ces_food_at_home_northeast_by_income_2023_2024.csv`
- `data/bls/ces_food_at_home_northeast_msa_2023_2024.csv`
- `data/bls/ces_fbar_by_income_group_northeast_cd2weighted.csv`
- `data/bls/cd2_market_size_M_northeast_cd2weighted.csv`
- `docs/fbar_M_update_log.md`, the change log. It covers the summary, sources, method and formulas, before-and-after tables, code changes, new files, verification, caveats, and a list of text to revise elsewhere. That includes the "Table 4700" citation and "\$75–140/week" range in the LEVEL_1 doc, and the "\$106–124M" figure in `docs/revenue_j_estimates.md`.

**Checks:**
- ACS 2024 unscaled \(M\) = \$112,912,893, which matches my earlier independent calculation.
- Adding up households × \(\bar f\) across the three groups gives \(M\) in every year, apart from cent-level rounding.
- The bracket counts add up to the total households every year (19,922 in 2024).

**Blocked step:** because of the Excel lock, I generated the four new CSVs by calling the new functions directly. They're the same functions `main()` uses, so the files are what a full run would produce. What hasn't been refreshed yet is `data/bls/ces_xlsx_parse_meta.json`. Close that CSV in Excel and run `python code/parse_bls_ces_xlsx.py` to update it. Git shows the existing national outputs rewrote identically.

**Caveat on 2020–2023:** those years reuse the 2023–24 regional spending with no inflation adjustment, so their \(M\) is overstated (up to +23% for 2020). Treat ACS 2024 as the main estimate.

---

**User**

I closed all the excel files.

---

**Cursor**

With Excel closed, I'll rerun the full parser so every output, including the metadata file, comes from one clean run.

With Excel closed, `python code/parse_bls_ces_xlsx.py` ran cleanly from start to finish with no errors and nothing reported missing. The plan is now fully implemented.

- **Numbers unchanged:** the full run gave the same values as my earlier direct run. For ACS 2024, \(M\) is \$112.98M, and \(\bar f\) is \$81.64/week (Low), \$94.17/week (Mid), \$146.94/week (High) and \$109.06/week for CD2 overall.
- **Metadata refreshed:** `data/bls/ces_xlsx_parse_meta.json` now records the 2023-2024 regional data period and lists all eight output files.
- **Old files untouched:** git shows no changes to the original national outputs. The only modified file is the metadata JSON; the four new CSVs and `docs/fbar_M_update_log.md` are new files.

Nothing is committed yet. The code change, the new CSVs, the log and the two BLS spreadsheets you downloaded are all uncommitted in your working tree.

---

**User**

Lastly, there is a difference between the amount spent on "Core basket" items and non "core basket" items (see docs/kappa_core_basket.md). Can I find an f_bar per income group on core basket items and non core basket items according to the definition in the document? create three tables, one for each kappa (low, base, high).

Will this be useful in our model when pass through is 1 for the 30% core basket price reduction?

---

**Cursor**

I'll check whether the Northeast income table has the same 18 spending categories used to define κ, which would keep the core/non-core split consistent with the new \(\bar f\).

All 18 categories are in the Northeast table. I'll preview the core and non-core \(\bar f\) values for ACS 2024 (a read-only calculation) so the plan can include expected numbers.

The preview has an off-by-one column error: it included the "Total Northeast" column as the first income bracket. I'll rerun with the correct columns.

The corrected preview is consistent with the new \(\bar f\) (Low \$81.64/week, and so on). Next I'll check how κ and \(\bar f\) are used in the model, to answer the pass-through question.

**Core / non-core f_bar tables**

> **Core spending needs a κ for each income bracket. Which spending data should define it?

A) Recompute κ from the Northeast Table 3104 categories, the same data as the new f_bar. All 18 categories are there. Base κ: Low 0.625, Mid 0.622, High 0.606, CD2 overall 0.615.

B) Keep the current national κ from kappa_core_basket_share.csv (Low 0.603, Mid 0.601, High 0.602) and apply it to the new Northeast f_bar.**
> - A) Recompute κ from Northeast data by bracket, CD2-weighted (Recommended) ✔
> - B) Apply the existing national κ to the new f_bar

---

**User**

create a .md file to explain the work you do, where files are, etc. afterwards.

---

**Cursor**

I've added the explainer document to the plan. It will be written last, as `docs/core_basket_fbar.md`, once the script has run and the numbers are verified. It follows the style of `docs/kappa_core_basket.md` and covers:
- every code, input and output file, with links
- how to rerun both scripts
- the three tables, one per κ version
- a worked savings example
- the method
- how to use the numbers in the model
- how the result differs from the earlier national κ
- caveats and sources

**Can you get core and non-core \(\bar f\) per income group?** Yes. The Northeast table has all 18 spending categories used to define κ, so the split uses the same data and weighting as the new \(\bar f\). Here are the preview values for ACS 2024, per household per week, scaled to NYC:

| κ version | Group | \(\bar f\) | Core | Non-core | κ |
|---|---|---|---|---|---|
| Low | Low / Mid / High | \$81.64 / \$94.17 / \$146.94 | \$32.87 / \$37.26 / \$54.08 | \$48.77 / \$56.91 / \$92.86 | 0.403 / 0.396 / 0.368 |
| Base | Low / Mid / High | same | \$51.00 / \$58.56 / \$89.03 | \$30.64 / \$35.61 / \$57.91 | 0.625 / 0.622 / 0.606 |
| High | Low / Mid / High | same | \$69.13 / \$79.85 / \$123.98 | \$12.51 / \$14.32 / \$22.96 | 0.847 / 0.848 / 0.844 |

**Is it useful with pass-through of 1 and the 30% core discount?** Yes, but mainly for dollar amounts rather than the choice model itself:
- **The price cut barely varies by income group.** Under base κ, the effective cut is about 18–19% of the basket price for all three groups, so one κ is still fine inside the logit model.
- **Household savings in dollars are direct.** A Low household that buys all its core items at the store saves 0.30 × \$51.00 = **\$15.30 a week** (about \$796 a year). Weighted by the store's choice share for each group, this gives a check on the model's consumer-welfare result.
- **The Affordability Payment has an input it currently lacks.** The planned Spofford Ave store has no ReferenceUSA revenue, so the current formula (0.30 × κ × revenue) can't be filled in. The payment can instead be built from demand as 0.30 × the sum over groups of households × choice share × core \(\bar f\) × 52. This also shows how much of it goes to low-income households.
- **Non-core \(\bar f\) is secondary.** It matters only if households split their shopping, buying core items at N.Y.C. Groceries and the rest elsewhere. In that case it's the spending that existing stores keep.

The plan is ready. Tell me when you want me to start implementing it.

---

**User**

How does the different kappa per income group change our current version of the model? is it just updating with the regional estimate? how would a kappa per income group be used versus one kappa overall

---

**Cursor**

I'll check how κ and the price cut are used in the current model code before answering.

There are two separate changes here, and both are small. Moving to the regional estimate shifts κ up for everyone (0.602 → 0.615 base). Using a κ per income group adds a slight gradient: low-income households get a marginally larger effective discount. In the choice model itself, neither changes results by more than a few percent. Where group κ matters more is in the dollar calculations, such as household savings and the Affordability Payment.

**How κ enters the model now.** No model code uses κ yet. The specification (`docs/nyc_groceries_store.md`, `docs/kappa_core_basket.md`) uses a single scalar:

\[
\Delta p_j = 0.30 \cdot \kappa \cdot p_j, \qquad \Delta U_{ij} = -\beta_{p,i}\,\Delta p_j
\]

Every income group sees the same price cut at N.Y.C. Groceries, about 18% of the basket price, and only \(\beta_{p,i}\) differs by group.

**Change 1: the regional level.** Switching κ from 0.602 (national) to 0.615 (Northeast, CD2-weighted) raises the effective cut from 18.1% to 18.5% for all groups. The price change is about 2% larger, so ΔCS rises by roughly 2% across the board. It's the same kind of update as the new \(\bar f\): better data, same structure.

**Change 2: κ per income group.** Index κ by group:

\[
\Delta p_{j,i} = 0.30 \cdot \kappa_i \cdot p_j
\]

With base κ, the effective cut is 18.8% for Low, 18.7% for Mid and 18.2% for High, compared with 18.5% for everyone under one κ. Relative to the single value, Low households' price cut is about 1.6% larger and High households' about 1.5% smaller. So ΔCS for the Low group rises about 1–2%, High falls about the same, and the CD2 total barely moves. It shifts a little of the benefit toward low-income households, which is the direction you'd expect because they spend a larger share on produce, meat and staples.

In the code, κ just becomes a vector indexed by income group instead of a single number, used wherever the price cut is computed. Nothing else in the logit changes.

**Where group κ matters more: dollar amounts.** In the logit, κ only scales a percentage cut on one representative basket price \(p_j\), which is the same for every group. But when you compute dollars, κ multiplies each group's own spending, and \(\kappa_g \times \bar f_g = \bar f^{core}_g\) is exactly the core \(\bar f\) from the plan:

| | One κ | κ per group (the core \(\bar f\) values) |
|---|---|---|
| Weekly savings if a household buys all core items at the store | 0.30 × 0.615 × \(\bar f_g\) | 0.30 × \(\bar f^{core}_g\): Low \$15.30, Mid \$17.57, High \$26.71 |
| Affordability Payment | 0.30 × κ × Revenue\(_j\) (no revenue figure exists for the new store) | 0.30 × \(\sum_g n_g P_{g,j}\,\bar f^{core}_g\) × 52, which also shows each group's share of the payment |

Here the differences come mostly from spending levels (\$82 vs \$147/week), not from κ. That's why the core \(\bar f\) tables are more useful than the κ gradient alone.

**Recommendation:**
- **Choice model:** use the regional CD2-overall κ (0.615 base) as the default, with 0.384 and 0.845 as the sensitivity sweep. Run group κ as a sensitivity or just adopt it; it costs nothing to implement, but don't expect it to change conclusions.
- **Dollar outputs** (savings per household, Affordability Payment, the check on ΔCS): use the group core \(\bar f\) values. That's where the per-group split actually adds information.

If you want, I can add this recommendation to the plan so the explainer doc (`docs/core_basket_fbar.md`) includes a "one κ vs κ per group" section.

---

**User**

Add to the explainer doc

---

**Cursor**

I've added a "One κ vs κ per income group" section to the outline for the explainer document, `docs/core_basket_fbar.md`, and updated that to-do to match. It will cover:

- **How κ enters the model today:** a single κ in \(\Delta p_j = 0.30\,\kappa\,p_j\), so every income group gets the same cut of about 18%.
- **Moving to the regional estimate:** κ goes from 0.602 to 0.615, which lifts the cut to 18.5% for everyone and raises ΔCS by roughly 2%.
- **Using κ per group:** cuts of 18.8% for Low, 18.7% for Mid and 18.2% for High. This shifts a little of the benefit toward low-income households but barely changes the CD2 total. In the code, κ just becomes a list with one value per income group.
- **Where per-group values matter more:** household savings and the Affordability Payment, where \(\kappa_g \bar f_g = \bar f^{core}_g\). The differences there come mainly from spending levels, not from κ.
- **Recommendation:** use the regional CD2-overall κ (0.615, with 0.384 and 0.845 as the sweep) in the choice model, keep group κ as an optional sensitivity, and use the group core \(\bar f\) values for dollar outputs.

Tell me when you want me to start implementing the plan.

---

**User**

Implement the plan as specified, it is attached for your reference. Do NOT edit the plan file itself.

To-do's from the plan have already been created. Do not create them again. Mark them as in_progress as you work, starting with the first one. Don't stop until you have completed all the to-dos.

---

**Cursor**

The script ran and passed its consistency checks. Every value matches the preview. Next I'll pull the annual figures for the doc tables.

The earlier parts of the change log write math as `$...$`, but my new sections use `\(...\)`. I'll convert the new sections to `$...$` so both files are consistent.

The first conversion attempt matched nothing because of a backslash-escaping problem in PowerShell. I'll rerun it with the correct escaping.

The inline math converted correctly, but PowerShell swallowed the `$$` delimiters on the display equations in the explainer, leaving those lines blank. I'll restore them by hand.

I've split each income group's grocery spending into Core Basket and non-core amounts for all three κ versions. The results match the preview, and the script's built-in checks pass: core plus non-core reproduces the new \(\bar f\) and \(M\) for every year, group and κ version.

Base κ results for ACS 2024, per household per week:

| Group | \(\bar f\) total | Core | Non-core | κ |
|---|---|---|---|---|
| Low (<\$25K) | \$81.64 | \$51.00 | \$30.64 | 0.625 |
| Mid (\$25–50K) | \$94.17 | \$58.56 | \$35.61 | 0.622 |
| High (>\$50K) | \$146.94 | \$89.03 | \$57.91 | 0.606 |
| CD2 overall | \$109.06 | \$67.03 | \$42.03 | 0.615 |

With the full 30% discount passed through, a Low household that buys all its Core Basket items at N.Y.C. Groceries saves 0.30 × \$51.00 = **\$15.30 a week**, about \$796 a year. Across CD2, the \$113.0M market splits into \$69.4M core and \$43.5M non-core.

**What was created or changed:**
- **`code/build_fbar_core_basket.py`**: the new script.
  - It reuses the Core Basket category tags from `build_kappa.py`, and the income-bracket mapping, income groups and NYC scaling from `parse_bls_ces_xlsx.py`.
  - It stops with an error if the totals don't reconcile.
- **`data/bls/fbar_core_noncore_by_income_group_northeast.csv`**: the full results, 60 rows covering ACS years 2020–2024 × three κ versions × four groups.
- **`data/bls/kappa_core_basket_share_northeast_cd2weighted.csv`**: κ low, base and high by year and group.
- **`docs/core_basket_fbar.md`**: the explainer you asked for. It covers:
  - where every code, input and output file lives, and how to rerun both scripts
  - the three κ tables, a worked savings example, and the method
  - how to use the numbers in the model when pass-through is 1
  - differences from the earlier national κ
  - the "one κ vs κ per income group" section with the recommendation
  - caveats and sources
- **`docs/fbar_M_update_log.md`**: a new section 10 logging this work, with the three tables, method, new files, verification, caveats and follow-ups.

`docs/kappa_core_basket.md`, `docs/nyc_groceries_store.md` and `data/bls/kappa_core_basket_share.csv` still use the national κ of 0.60. I left them unchanged, and section 10 of the log flags them as candidates to update to 0.615.

