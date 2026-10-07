"""
Equation cards for the model as run (code/model.py, code/run_model.py), for ONLY the MAIN spec v2
equations whose form changed. File numbers match figures/equations/ (MAIN v2 cards).

Output: figures/equations_v3/eq_NN_<name>.png (transparent) and .svg.
Values in descriptions are from results/chris_run0_calibration/ (base run).
Why each equation changed: docs/equations_v3_changes.md.
"""

import os

from render_main_equations import ROOT, render_card

OUT_DIR = os.path.join(ROOT, "figures", "equations_v3")
os.makedirs(OUT_DIR, exist_ok=True)

SOURCE = "Model as run (code/model.py), updates MAIN v2"

UTILITY_RHS = (r"\alpha_j + \gamma_{sq} \left( sq_j/1000 \right)"
               r" - \beta_{p,i}\, b_i \left( p_j - \bar{p} \right) - \beta_d\, d_{ij}$")
# Large \right) after a \sum renders as "!" in mathtext's cm font, so brackets are used here.
LOGSUM_1 = r"\ln\left[1 + \sum_{k=1}^{J}\; \exp(V_{ik}^{\mathrm{%s}})\right]"

SYM = {
    "V_ij":    (r"$V_{ij}$", r"Systematic utility of store $j$ for consumer group $i$ (tract × income group)"),
    "V_ijk":   (r"$V_{ij},\ V_{ik}$", r"Systematic utility of store $j$ and of store $k$"),
    "V_ik":    (r"$V_{ik}$", r"Systematic utility group $i$ gets from store $k$"),
    "V_pre":   (r"$V_{ij}^{\mathrm{pre}}$", r"Systematic utility of store $j$ for group $i$ before the policy"),
    "V_post":  (r"$V_{ij}^{\mathrm{post}}$", r"Systematic utility of store $j$ for group $i$ after the policy"),
    "Vk_pre":  (r"$V_{ik}^{\mathrm{pre}}$", r"Systematic utility of store $k$ for group $i$ before the policy"),
    "Vk_post": (r"$V_{ik}^{\mathrm{post}}$", r"Systematic utility of store $k$ for group $i$ after the policy"),
    "alpha":   (r"$\alpha_j$",
                r"Constant for store $j$'s type, calibrated so predicted sales by type match revenue: "
                r"supermarket −1.71 · small independent −3.10"),
    "gamma":   (r"$\gamma_{sq}$", r"Utility per 1,000 sq ft of floor area: 0.0098 (Hillier et al. 2017)"),
    "sq":      (r"$sq_j$", r"Floor area of store $j$ (sq ft, NYS Ag & Markets license)"),
    "b_p":     (r"$\beta_{p,i}$",
                r"Disutility per dollar of trip spending, by income group (calibrated): "
                r"Low 0.0583 · Mid 0.0195 · High 0.0084"),
    "b_p_cs":  (r"$\beta_{p,i}$",
                r"Disutility per dollar of trip spending (Low 0.0583 · Mid 0.0195 · High 0.0084); "
                r"dividing by it converts utils to dollars"),
    "b_i":     (r"$b_i$",
                r"Baskets bought per trip, $52\,\bar{f}_g/(T \cdot \bar{p})$: Low 2.83 · Mid 3.27 · High 5.10"),
    "p_j":     (r"$p_j$", r"Price of the 10-item basket at store $j$ (\$/basket, Aug 2026 dollars)"),
    "p_bar":   (r"$\bar{p}$", r"Mean basket price of the 9 existing stores, \$28.83; also the outside option's price"),
    "b_d":     (r"$\beta_d$", r"Disutility per mile of travel, same for all groups: 0.548 (Hillier et al. 2017)"),
    "d_ij":    (r"$d_{ij}$", r"Manhattan distance (miles) from the centroid of group $i$'s tract to store $j$"),
    "one":     (r"$1$",
                r"The outside option, other stores (bodegas and stores outside CD2): "
                r"$V_{i0}=0$, so $e^{V_{i0}}=1$"),
    "s_ij":    (r"$s_{ij}$", r"Probability that a household in group $i$ chooses store $j$; the rest choose other stores"),
    "s_post":  (r"$s_{ij}^{\mathrm{post}}$", r"Probability that group $i$ chooses store $j$ after the policy"),
    "k":       (r"$k$", r"Index over the modeled stores"),
    "J":       (r"$J$", r"Number of modeled stores: 9 existing, 10 with N.Y.C. Groceries"),
    "T":       (r"$T$", r"Shopping trips per year: 52 (weekly)"),
    "n_i":     (r"$n_i$", r"Number of households in consumer group $i$"),
    "R_hat":   (r"$\hat{R}_j$", r"Model-predicted annual sales at store $j$ to CD2 households, before the policy (\$)"),
    "R_post":  (r"$\hat{R}_j^{\mathrm{post}}$",
                r"Model-predicted annual sales at store $j$ after the discount, at pre-discount prices (\$)"),
    "Q_hat":   (r"$\hat{Q}_j$", r"Model-predicted baskets sold per year at store $j$, before the policy"),
    "theta":   (r"$\theta$", r"Pass-through rate: share of the subsidy that lowers shelf prices (0.25, 0.50 base, 0.75)"),
    "s":       (r"$s$", r"Annual subsidy to store $j$ (\$): a FRESH tax break or a rent subsidy"),
    "dp":      (r"$\Delta p_j$", r"Reduction in the basket price at store $j$ (\$/basket)"),
    "dp_g":    (r"$\Delta p_{j,g}$",
                r"Price cut at store $j$ for income group $g$: $\theta\,s/\hat{Q}_j$ (v1) or $0.30\,\kappa_g\,p_j$ (v2)"),
    "pct30":   (r"$0.30$", r"The 30% discount on core-basket items required by the N.Y.C. Groceries contract"),
    "kappa_g": (r"$\kappa_g$",
                r"Share of income group $g$'s grocery basket that is core items: "
                r"Low 0.6247 · Mid 0.6218 · High 0.6059"),
    "kappa_j": (r"$\kappa_j$", r"Core-basket share of store $j$'s predicted sales after the discount"),
    "Rent":    (r"$\mathrm{Rent}_j$", r"Annual rent of store $j$, paid by NYCEDC (FY2025)"),
    "Tax":     (r"$\mathrm{Tax}_j$", r"Annual property tax on store $j$'s share of the lot, paid by NYCEDC (FY2025)"),
    "AP_j":    (r"$\mathrm{AP}_j$", r"Affordability Payment: NYCEDC's payment beyond rent and tax (\$/yr)"),
    "gdc":     (r"$0.30 \cdot \kappa_j \cdot \hat{R}_j^{\mathrm{post}}$",
                r"Gross discount cost: revenue store $j$ gives up on the core items its shoppers buy (\$/yr)"),
    "s_star":  (r"$s_j^*$", r"Total annual cost to NYCEDC of the contract at store $j$ (\$)"),
    "dCS":     (r"$\Delta CS$", r"Annual change in consumer surplus summed over all 39 groups (\$)"),
}

# (v2 card number, file stem, equation name, MAIN v2 section, mathtext, symbols)
CARDS_V3 = [
    (2, "systematic_utility", "Systematic Utility", "§1.1.1",
     r"$V_{ij} = " + UTILITY_RHS,
     ["V_ij", "alpha", "gamma", "sq", "b_p", "b_i", "p_j", "p_bar", "b_d", "d_ij"]),

    (6, "choice_probability", "Logit Choice Probability", "§1.1.3",
     r"$s_{ij} = \frac{\exp(V_{ij})}{1 + \sum_{k=1}^{J}\; \exp(V_{ik})}$",
     ["s_ij", "V_ijk", "one", "k", "J"]),

    (8, "expected_max_utility", "Expected Maximum Utility (Logsum)", "§1.1.5",
     r"$E\left[\,\max_k\; U_{ik}\,\right] = \ln\left[1 + \sum_{k=1}^{J}\; \exp(V_{ik})\right] + \gamma$",
     [(r"$E\left[\,\max_k\; U_{ik}\,\right]$",
       r"Expected utility of group $i$'s best option (a modeled store or other stores), averaged over taste shocks"),
      "one", "V_ik", "J",
      (r"$\gamma$", r"Euler's constant, about 0.5772 (mean of the Gumbel error); it cancels in $\Delta CS$")]),

    (9, "annual_welfare", "Annual Consumer Welfare", "§1.1.5",
     r"$W_i = \frac{T}{\beta_{p,i}} \ln\left[1 + \sum_{k=1}^{J}\; \exp(V_{ik})\right]$",
     [(r"$W_i$", r"Annual welfare of a household in group $i$, in dollars"),
      "T", "b_p_cs", "one", "V_ik", "J"]),

    (10, "delta_cs", "Annual Change in Consumer Surplus", "§1.1.5",
     r"$\Delta CS = \sum_{i}\; \frac{n_i \cdot T}{\beta_{p,i}} \left\{" + LOGSUM_1 % "post"
     + r" \;-\; " + LOGSUM_1 % "pre" + r"\right\}$",
     ["dCS", "n_i", "T", "b_p_cs", "one", "Vk_post", "Vk_pre"]),

    (12, "basket_volume", "Annual Basket Volume (Model-Predicted)", "§1.2.1",
     r"$\hat{Q}_j = \frac{\hat{R}_j}{p_j}, \qquad \hat{R}_j = \sum_{i}\; n_i \cdot T \cdot s_{ij} \cdot b_i \cdot p_j$",
     ["Q_hat", "R_hat", "p_j", "n_i", "T", "s_ij", "b_i"]),

    (14, "price_cut_v1", "Price Cut from a Lump-Sum Subsidy (v1)", "§1.3.1",
     r"$\Delta p_j = \theta \cdot \frac{s}{\hat{Q}_j}$",
     ["dp", "theta", "s", "Q_hat"]),

    (15, "post_utility_v1", "Post-Subsidy Utility (v1)", "§1.3.1",
     r"$V_{ij}^{\mathrm{post}} = V_{ij}^{\mathrm{pre}} + \beta_{p,i}\, b_i\, \Delta p_j$",
     ["V_post", "V_pre", "b_p", "b_i", "dp"]),

    (17, "post_utility_v2", "Post-Discount Utility (v2)", "§1.3.2",
     r"$V_{ij}^{\mathrm{post}} = V_{ij}^{\mathrm{pre}} + \beta_{p,i}\, b_i \cdot 0.30 \cdot \kappa_g \cdot p_j$",
     ["V_post", "V_pre", "b_p", "b_i", "pct30", "kappa_g", "p_j"]),

    (18, "store_core_share", "Store-Level Core-Basket Share", "§1.3.2",
     r"$\kappa_j = \frac{\sum_{i}\; n_i \cdot s_{ij}^{\mathrm{post}} \cdot b_i \cdot \kappa_g}"
     r"{\sum_{i}\; n_i \cdot s_{ij}^{\mathrm{post}} \cdot b_i}$",
     ["kappa_j", "n_i", "s_post", "b_i",
      (r"$\kappa_g$", r"Core-basket share of the income group $g$ that group $i$ belongs to")]),

    (19, "gross_discount_cost", "Gross Discount Cost", "§1.3.2",
     r"$\mathrm{Gross\ discount\ cost} = 0.30 \cdot \kappa_j \cdot \hat{R}_j^{\mathrm{post}}$",
     [(r"$\mathrm{Gross\ discount\ cost}$", r"Revenue store $j$ gives up each year by offering the discount (\$)"),
      "pct30", "kappa_j", "R_post"]),

    (20, "affordability_payment", "Affordability Payment", "§1.3.2",
     r"$\mathrm{AP}_j = \max\left(0,\; 0.30 \cdot \kappa_j \cdot \hat{R}_j^{\mathrm{post}}"
     r" \;-\; \mathrm{Rent}_j \;-\; \mathrm{Tax}_j\right)$",
     ["AP_j", "gdc", "Rent", "Tax",
      (r"$\max(0,\ \cdot)$", r"The payment is zero when rent and tax relief already cover the discount")]),

    (21, "total_subsidy_cost", "Total Annual Subsidy Cost", "§1.3.2",
     r"$s_j^* = \mathrm{Rent}_j + \mathrm{Tax}_j + \mathrm{AP}_j = "
     r"\max\left(\mathrm{Rent}_j + \mathrm{Tax}_j,\; 0.30 \cdot \kappa_j \cdot \hat{R}_j^{\mathrm{post}}\right)$",
     ["s_star", "Rent", "Tax", "AP_j", "gdc"]),

    (22, "step_a_pre_utility", "Step A: Pre-Subsidy Utility", "§1.4",
     r"$V_{ij}^{\mathrm{pre}} = " + UTILITY_RHS,
     ["V_pre", "alpha", "gamma", "sq", "b_p", "b_i", "p_j", "p_bar", "b_d", "d_ij"]),

    (23, "step_b_post_utility", "Step B: Post-Subsidy Utility", "§1.4",
     r"$V_{ij}^{\mathrm{post}} = V_{ij}^{\mathrm{pre}} + \beta_{p,i}\, b_i\, \Delta p_{j,g}$",
     ["V_post", "V_pre", "b_p", "b_i", "dp_g"]),

    (24, "step_c_logsum", "Step C: Logsum Welfare by Group", "§1.4",
     r"$L_i^{\mathrm{pre}} = " + LOGSUM_1 % "pre" + r", \qquad L_i^{\mathrm{post}} = " + LOGSUM_1 % "post" + "$",
     [(r"$L_i^{\mathrm{pre}},\ L_i^{\mathrm{post}}$",
       r"Logsum for group $i$ (expected utility of the best option on one trip), before and after the policy"),
      "one", "Vk_pre", "Vk_post", "k", "J"]),

    (28, "min_subsidy", "Minimum Subsidy for a Target Consumer Surplus Gain", "§1.5",
     r"$s_j^* = \min\ \left\{\, s \in [0,\ \bar{s}_j] \;:\; \Delta CS_j(s) \;\geq\; \Delta CS_{\min} \,\right\}$",
     [(r"$s_j^*$", r"Smallest annual public cost at store $j$ that reaches the target gain (\$)"),
      (r"$s$", r"Annual public cost of the lever (\$), searched on a 21-point grid with linear interpolation"),
      (r"$\bar{s}_j$",
       r"Lever cap at store $j$: $\mathrm{Tax}_j$ (FRESH tax break), $\mathrm{Rent}_j$ (rent subsidy), "
       r"or the cost of the full 30% discount (contract)"),
      (r"$\Delta CS_j(s)$", r"Annual consumer surplus gain when the lever at store $j$ costs $s$ (\$)"),
      (r"$\Delta CS_{\min}$", r"Target annual gain: \$50K, \$100K, \$250K, \$500K or \$1M")]),
]


if __name__ == "__main__":
    for num, *card in CARDS_V3:
        render_card(num, *card, out_dir=OUT_DIR, source=SOURCE, sym_table=SYM)
