"""
Render every displayed equation in MAIN_NYC_Grocery_Subsidy_Model_Specification_v2.md as a slide
"equation card": equation name, section reference, the equation, and a description of each symbol.

Output: figures/equations/eq_NN_<name>.png (transparent, high resolution) and .svg.
"""

import os
import re

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT    = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(ROOT, "figures", "equations")
os.makedirs(OUT_DIR, exist_ok=True)

matplotlib.rcParams["mathtext.fontset"] = "cm"   # Computer Modern, matches LaTeX
matplotlib.rcParams["font.family"] = "DejaVu Sans"

DPI         = 400
TITLE_SIZE  = 26
REF_SIZE    = 15
EQ_SIZE     = 34
SYM_SIZE    = 21
DESC_SIZE   = 17
WRAP_CHARS  = 72
TITLE_COLOR = "#1a3a5c"
TEXT_COLOR  = "#222222"
REF_COLOR   = "#777777"

# Symbols shared by several equations: key -> (mathtext, description).
SYM = {
    "U_ij":    (r"$U_{ij}$", "Total utility consumer group $i$ gets from shopping at store $j$ (not computed)"),
    "V_ij":    (r"$V_{ij}$", "Systematic utility: the part of $U_{ij}$ the model computes"),
    "V_ik":    (r"$V_{ik}$", "Systematic utility group $i$ gets from store $k$"),
    "V_pre":   (r"$V_{ij}^{\mathrm{pre}}$", "Systematic utility of store $j$ for group $i$ before the subsidy"),
    "V_post":  (r"$V_{ij}^{\mathrm{post}}$", "Systematic utility of store $j$ for group $i$ after the subsidy"),
    "Vk_pre":  (r"$V_{ik}^{\mathrm{pre}}$", "Systematic utility of store $k$ for group $i$ before the subsidy"),
    "Vk_post": (r"$V_{ik}^{\mathrm{post}}$", "Systematic utility of store $k$ for group $i$ after the subsidy"),
    "eps":     (r"$\varepsilon_{ij}$",
                "Unobserved taste shock (habit, brand loyalty, route to work); independent and "
                "identically distributed across groups and stores. Notation only, not modeled"),
    "b_sqft":  (r"$\beta_{\mathrm{sqft}}$", "Utility per square foot of store floor area; same for all groups"),
    "sqft":    (r"$\mathrm{sqft}_j$", "Floor area of store $j$ (sq ft, NYS Ag & Markets license)"),
    "b_p":     (r"$\beta_{p,i}$", "Disutility per dollar of basket price; varies by income group"),
    "b_p_cs":  (r"$\beta_{p,i}$", "Disutility per dollar of basket price; dividing by it converts utils to dollars"),
    "p_j":     (r"$p_j$", r"Price of the 10-item basket at store $j$ (\$/basket, Aug 2026 dollars)"),
    "b_d":     (r"$\beta_{d,i}$", "Disutility per mile of travel; varies by income group"),
    "d_tj":    (r"$d_{tj}$", "Manhattan distance (miles) from the centroid of group $i$'s tract $t$ to store $j$"),
    "n_i":     (r"$n_i$", "Number of households in consumer group $i$"),
    "N_HH":    (r"$N_{\mathrm{HH}}$", "Total households in Bronx CD2: 19,922 (ACS 2024)"),
    "s_ij":    (r"$s_{ij}$", "Probability that a household in group $i$ chooses store $j$"),
    "J":       (r"$J$", "Number of stores in the choice set: 9 existing, 10 with N.Y.C. Groceries"),
    "k":       (r"$k$", "Index over all stores in the choice set"),
    "T":       (r"$T$", "Shopping trips per year: 52 (weekly)"),
    "R_j":     (r"$R_j$", r"Annual revenue of store $j$ (\$)"),
    "Q_j":     (r"$Q_j$", "Baskets store $j$ sells per year (44,283 to 432,925)"),
    "pct30":   (r"$0.30$", "The 30% discount on core-basket items required by the N.Y.C. Groceries contract"),
    "kappa_g": (r"$\kappa_g$",
                "Share of income group $g$'s grocery basket that is core items: "
                "Low 0.6247 · Mid 0.6218 · High 0.6059"),
    "kappa_j": (r"$\kappa_j$", "Core-basket share of store $j$'s sales, weighted by who shops there"),
    "Rent":    (r"$\mathrm{Rent}_j$", "Annual rent of store $j$, paid by NYCEDC (FY2025)"),
    "Tax":     (r"$\mathrm{Tax}_j$", "Annual property tax on store $j$'s share of the lot, paid by NYCEDC (FY2025)"),
    "AP_j":    (r"$\mathrm{AP}_j$", r"Affordability Payment: NYCEDC's payment beyond rent and tax (\$/yr)"),
    "gdc":     (r"$0.30 \cdot \kappa_j \cdot R_j$", r"Gross discount cost: revenue store $j$ gives up through the discount (\$/yr)"),
    "s_star":  (r"$s_j^*$", r"Total annual cost to NYCEDC of subsidizing store $j$ (\$)"),
    "dCS":     (r"$\Delta CS$", r"Annual change in consumer surplus summed over all 39 groups (\$)"),
    "theta":   (r"$\theta$", "Pass-through rate: share of the subsidy that lowers shelf prices (0.40, 0.65, 0.85)"),
}

UTILITY_SYMS = ["b_sqft", "sqft", "b_p", "p_j", "b_d", "d_tj"]

# (file stem, equation name, section, equation mathtext, symbols: SYM keys or (tex, description))
CARDS = [
    ("random_utility", "Random Utility", "§1.1.1",
     r"$U_{ij} = V_{ij} + \varepsilon_{ij}, \qquad \varepsilon_{ij} \overset{\mathrm{i.i.d.}}{\sim} \mathrm{Gumbel}(0, 1)$",
     ["U_ij", "V_ij", "eps",
      (r"$\mathrm{Gumbel}(0, 1)$",
       "Type I extreme value distribution with location 0 and scale 1; it gives the closed-form logit")]),

    ("systematic_utility", "Systematic Utility", "§1.1.1",
     r"$V_{ij} = \beta_{\mathrm{sqft}} \cdot \mathrm{sqft}_j \;-\; \beta_{p,i} \cdot p_j \;-\; \beta_{d,i} \cdot d_{tj}$",
     ["V_ij"] + UTILITY_SYMS),

    ("manhattan_distance", "Manhattan Distance", "§1.1.1",
     r"$d_{tj} = 69.17\,\left|\mathrm{lat}_t - \mathrm{lat}_j\right| \;+\; "
     r"69.17\cos\!\left(\overline{\mathrm{lat}}_{tj}\right)\,\left|\mathrm{lon}_t - \mathrm{lon}_j\right|"
     r" \quad \mathrm{(miles)}$",
     [(r"$d_{tj}$", "Distance from the centroid of tract $t$ to store $j$: north-south gap plus east-west gap"),
      (r"$\mathrm{lat}_t,\ \mathrm{lon}_t$", "Latitude and longitude of tract $t$'s centroid (degrees)"),
      (r"$\mathrm{lat}_j,\ \mathrm{lon}_j$", "Latitude and longitude of store $j$ (degrees)"),
      (r"$\overline{\mathrm{lat}}_{tj}$", "Mean latitude of the tract and the store"),
      (r"$69.17$", "Miles per degree of latitude"),
      (r"$69.17\cos(\overline{\mathrm{lat}}_{tj})$", "Miles per degree of longitude at that latitude (about 52.4 in the Bronx)")]),

    ("consumer_groups", "Consumer Group Definition", "§1.1.2",
     r"$i \;\equiv\; (t,\, g), \qquad n_i \equiv n_{t,g}$",
     [(r"$i$", "Consumer group: one census tract crossed with one income group (13 × 3 = 39 groups)"),
      (r"$t$", "Census tract (13 CD2 tracts with households)"),
      (r"$g$", r"Income group: Low (under \$25K), Mid (\$25K to \$50K), High (over \$50K)"),
      (r"$n_i,\ n_{t,g}$", "Number of households in group $i$, i.e. in tract $t$ and income group $g$")]),

    ("total_households", "Total Households", "§1.1.2",
     r"$\sum_i n_i = N_{\mathrm{HH}} = 19{,}922$",
     [(r"$\sum_i$", "Sum over all 39 consumer groups"),
      "n_i",
      (r"$N_{\mathrm{HH}}$", "Total households in Bronx CD2 (ACS 2024): Low 7,683 · Mid 4,795 · High 7,444")]),

    ("choice_probability", "Logit Choice Probability", "§1.1.3",
     r"$s_{ij} = \Pr\!\left(U_{ij} \geq U_{ik}\ \ \forall k\right) = \frac{\exp(V_{ij})}{\sum_{k=1}^{J}\; \exp(V_{ik})}$",
     ["s_ij",
      (r"$U_{ij},\ U_{ik}$", "Total utility of store $j$ and of any other store $k$"),
      (r"$V_{ij},\ V_{ik}$", "Systematic utility of store $j$ and of store $k$"),
      "k", "J"]),

    ("market_share", "Aggregate Market Share", "§1.1.4",
     r"$S_j = \frac{1}{N_{\mathrm{HH}}} \sum_{i}\; n_i \cdot s_{ij}$",
     [(r"$S_j$", "Share of all CD2 households that shop at store $j$"),
      "N_HH", "n_i", "s_ij"]),

    ("expected_max_utility", "Expected Maximum Utility (Logsum)", "§1.1.5",
     r"$E\!\left[\max_k U_{ik}\right] = \ln\!\left[\sum_{k=1}^{J}\; \exp(V_{ik})\right] + \gamma$",
     [(r"$E\!\left[\max_k U_{ik}\right]$", "Expected utility of group $i$'s best store, averaged over taste shocks"),
      "V_ik", "k", "J",
      (r"$\gamma$", r"Euler's constant, about 0.5772 (mean of the Gumbel error); it cancels in $\Delta CS$")]),

    ("annual_welfare", "Annual Consumer Welfare", "§1.1.5",
     r"$W_i = \frac{T}{\beta_{p,i}} \ln\!\left[\sum_{k=1}^{J}\; \exp(V_{ik})\right]$",
     [(r"$W_i$", "Annual welfare of a household in group $i$, in dollars"),
      "T", "b_p_cs",
      (r"$\ln \sum_k \exp(V_{ik})$", "Logsum: expected utility of the best store on one trip"),
      "V_ik", "J"]),

    ("delta_cs", "Annual Change in Consumer Surplus", "§1.1.5",
     r"$\Delta CS = \sum_{i}\; \frac{n_i \cdot T}{\beta_{p,i}} \left[\ln\sum_{k}\; \exp\!\left(V_{ik}^{\mathrm{post}}\right)"
     r" \;-\; \ln\sum_{k}\; \exp\!\left(V_{ik}^{\mathrm{pre}}\right)\right]$",
     ["dCS", "n_i", "T", "b_p_cs", "Vk_post", "Vk_pre"]),

    ("store_revenue", "Store Revenue", "§1.2.1",
     r"$R_j = \mathrm{sqft}_j \times r, \qquad r = \$801.18/\mathrm{sq\ ft/yr\ (2024\ \$)}$",
     ["R_j", "sqft",
      (r"$r$", r"Bronx grocery sales per sq ft per year: \$801.18 (range \$697.95 to \$845.08), "
               "Census 2022, CPI-adjusted to 2024")]),

    ("basket_volume", "Annual Basket Volume", "§1.2.1",
     r"$Q_j = \frac{R_j}{p_j}$",
     ["Q_j", "R_j", "p_j"]),

    ("market_size", "CD2 Grocery Market Size", "§1.2.1",
     r"$M = \sum_{g}\; N_{g} \cdot \bar{f}_g \cdot 52 \;\approx\; \$112.98\mathrm{M/yr\ (2024)}$",
     [(r"$M$", "Annual grocery (food-at-home) spending by all CD2 households"),
      (r"$g$", "Income group: Low, Mid, High"),
      (r"$N_g$", "Households in income group $g$: Low 7,683 · Mid 4,795 · High 7,444"),
      (r"$\bar{f}_g$", "Average weekly food-at-home spending per household: "
                       r"Low \$81.64 · Mid \$94.17 · High \$146.94"),
      (r"$52$", "Weeks per year")]),

    ("price_cut_v1", "Price Cut from a Lump-Sum Subsidy (v1)", "§1.3.1",
     r"$\Delta p_j = \theta \cdot \frac{s}{Q_j}$",
     [(r"$\Delta p_j$", r"Reduction in the basket price at store $j$ (\$/basket)"),
      "theta",
      (r"$s$", r"Annual lump-sum subsidy to the store (\$), e.g. a tax break or rent subsidy"),
      "Q_j"]),

    ("post_utility_v1", "Post-Subsidy Utility (v1)", "§1.3.1",
     r"$V_{ij}^{\mathrm{post}} = V_{ij}^{\mathrm{pre}} + \beta_{p,i} \cdot \Delta p_j$",
     ["V_post", "V_pre", "b_p",
      (r"$\Delta p_j$", r"Reduction in the basket price at store $j$ (\$/basket)")]),

    ("price_cut_v2", "Price Cut from the 30% Core-Basket Discount (v2)", "§1.3.2",
     r"$\Delta p_{j,g} = 0.30 \cdot \kappa_g \cdot p_j$",
     [(r"$\Delta p_{j,g}$", r"Reduction in the basket price at store $j$ for income group $g$ (\$/basket)"),
      "pct30", "kappa_g", "p_j"]),

    ("post_utility_v2", "Post-Discount Utility (v2)", "§1.3.2",
     r"$V_{ij}^{\mathrm{post}} = V_{ij}^{\mathrm{pre}} + \beta_{p,i} \cdot 0.30 \cdot \kappa_g \cdot p_j$",
     ["V_post", "V_pre", "b_p", "pct30", "kappa_g", "p_j"]),

    ("store_core_share", "Store-Level Core-Basket Share", "§1.3.2",
     r"$\kappa_j = \frac{\sum_{i}\; s_{ij} \cdot n_i \cdot \kappa_g}{\sum_{i}\; s_{ij} \cdot n_i}$",
     ["kappa_j", "s_ij", "n_i",
      (r"$\kappa_g$", "Core-basket share of the income group $g$ that group $i$ belongs to")]),

    ("gross_discount_cost", "Gross Discount Cost", "§1.3.2",
     r"$\mathrm{Gross\ discount\ cost} = 0.30 \cdot \kappa_j \cdot R_j$",
     [(r"$\mathrm{Gross\ discount\ cost}$", r"Revenue store $j$ gives up each year by offering the discount (\$)"),
      "pct30", "kappa_j", "R_j"]),

    ("affordability_payment", "Affordability Payment", "§1.3.2",
     r"$\mathrm{AP}_j = \max\left(0,\; 0.30 \cdot \kappa_j \cdot R_j \;-\; \mathrm{Rent}_j \;-\; \mathrm{Tax}_j\right)$",
     ["AP_j", "gdc", "Rent", "Tax",
      (r"$\max(0,\ \cdot)$", "The payment is zero when rent and tax relief already cover the discount")]),

    ("total_subsidy_cost", "Total Annual Subsidy Cost", "§1.3.2",
     r"$s_j^* = \mathrm{Rent}_j + \mathrm{Tax}_j + \mathrm{AP}_j = "
     r"\max\left(\mathrm{Rent}_j + \mathrm{Tax}_j,\; 0.30 \cdot \kappa_j \cdot R_j\right)$",
     ["s_star", "Rent", "Tax", "AP_j", "gdc"]),

    ("step_a_pre_utility", "Step A: Pre-Subsidy Utility", "§1.4",
     r"$V_{ij}^{\mathrm{pre}} = \beta_{\mathrm{sqft}} \cdot \mathrm{sqft}_j - \beta_{p,i} \cdot p_j - \beta_{d,i} \cdot d_{tj}$",
     ["V_pre"] + UTILITY_SYMS),

    ("step_b_post_utility", "Step B: Post-Subsidy Utility", "§1.4",
     r"$V_{ij}^{\mathrm{post}} = V_{ij}^{\mathrm{pre}} + \beta_{p,i} \cdot \Delta p_{j,g}$",
     ["V_post", "V_pre", "b_p",
      (r"$\Delta p_{j,g}$", "Price cut at store $j$ for income group $g$, from v1 (§1.3.1) or v2 (§1.3.2)")]),

    ("step_c_logsum", "Step C: Logsum Welfare by Group", "§1.4",
     r"$L_i^{\mathrm{pre}} = \ln\!\sum_{k=1}^{J}\; \exp\!\left(V_{ik}^{\mathrm{pre}}\right), \qquad "
     r"L_i^{\mathrm{post}} = \ln\!\sum_{k=1}^{J}\; \exp\!\left(V_{ik}^{\mathrm{post}}\right)$",
     [(r"$L_i^{\mathrm{pre}},\ L_i^{\mathrm{post}}$",
       "Logsum for group $i$ (expected utility of the best store on one trip), before and after the subsidy"),
      "Vk_pre", "Vk_post", "k", "J"]),

    ("step_d_delta_cs", "Step D: Annual Change in Consumer Surplus", "§1.4",
     r"$\Delta CS = \sum_{i=1}^{39}\; \frac{n_i \cdot T}{\beta_{p,i}} \left(L_i^{\mathrm{post}} - L_i^{\mathrm{pre}}\right)$",
     ["dCS",
      (r"$\sum_{i=1}^{39}$", "Sum over the 39 consumer groups"),
      "n_i", "T", "b_p_cs",
      (r"$L_i^{\mathrm{post}} - L_i^{\mathrm{pre}}$", "Change in group $i$'s logsum from Step C (utils per trip)")]),

    ("subsidy_efficiency", "Subsidy Efficiency (Store Ranking)", "§1.5",
     r"$\mathrm{efficiency}_j = \frac{\Delta CS_j}{s_j^*}$",
     [(r"$\mathrm{efficiency}_j$", "Consumer surplus gained per dollar of subsidy at store $j$; stores are ranked by it"),
      (r"$\Delta CS_j$", r"Annual consumer surplus gain from subsidizing store $j$ (\$)"),
      "s_star"]),

    ("post_discount_price", "Post-Discount Basket Price", "§1.5",
     r"$p_j^{\mathrm{post}} = p_j \cdot \left(1 - 0.30 \cdot \kappa_g\right)$",
     [(r"$p_j^{\mathrm{post}}$", "Basket price for income group $g$ after the discount "
                                 r"(N.Y.C. Groceries: Low \$23.52 · Mid \$23.55 · High \$23.69)"),
      (r"$p_j$", r"Basket price before the discount (\$28.95 at N.Y.C. Groceries)"),
      "pct30", "kappa_g"]),

    ("min_subsidy_v1", "Minimum Subsidy for a Target Consumer Surplus Gain (v1)", "§1.5",
     r"$s_j^* = \min_{s\,\geq\,0}\ s \quad \mathrm{subject\ to} \quad \Delta CS_j(s) \;\geq\; \Delta CS_{\min}$",
     [(r"$s_j^*$", r"Smallest annual subsidy to store $j$ that reaches the target gain (\$)"),
      (r"$s$", r"Annual lump-sum subsidy to store $j$ (\$); the choice variable, searched over a grid"),
      (r"$\Delta CS_j(s)$",
       r"Annual consumer surplus gain when store $j$ gets subsidy $s$, passed to shoppers as the price "
       r"cut $\Delta p_j=\theta\,s/Q_j$ (\$)"),
      (r"$\Delta CS_{\min}$", r"Target annual consumer surplus gain set by the policy maker (\$)")]),
]

# Inline $...$ segments (ignoring escaped \$) are kept whole when wrapping descriptions.
TOKEN = re.compile(r"(?<!\\)\$.*?(?<!\\)\$\S*|\S+")


def wrap(text, width=WRAP_CHARS):
    lines, line = [], ""
    for tok in TOKEN.findall(text):
        if line and len(line) + 1 + len(tok) > width:
            lines.append(line)
            line = tok
        else:
            line = f"{line} {tok}" if line else tok
    lines.append(line)
    return "\n".join(lines)


def render_card(num, stem, name, section, tex, symbols):
    size = 20
    fig = plt.figure(figsize=(size, size))
    renderer = fig.canvas.get_renderer()

    def put(x, y, s, **kw):
        t = fig.text(x / size, y / size, s, va="top", **kw)
        bb = t.get_window_extent(renderer)
        return bb.width / fig.dpi, bb.height / fig.dpi

    y = size - 0.5
    _, h = put(0, y, name, fontsize=TITLE_SIZE, fontweight="bold", color=TITLE_COLOR)
    y -= h + 0.12
    _, h = put(0, y, f"MAIN model specification v2, {section}", fontsize=REF_SIZE, color=REF_COLOR)
    y -= h + 0.45
    _, h = put(0.3, y, tex, fontsize=EQ_SIZE, color=TEXT_COLOR)
    y -= h + 0.5
    _, h = put(0, y, "where", fontsize=DESC_SIZE, style="italic", color=REF_COLOR)
    y -= h + 0.2

    rows = [SYM[s] if isinstance(s, str) else s for s in symbols]
    probe = [fig.text(0, 0, sym, fontsize=SYM_SIZE) for sym, _ in rows]
    sym_w = max(t.get_window_extent(renderer).width for t in probe) / fig.dpi
    for t in probe:
        t.remove()

    desc_x = 0.3 + sym_w + 0.4
    for sym, desc in rows:
        _, hs = put(0.3, y, sym, fontsize=SYM_SIZE, color=TEXT_COLOR)
        _, hd = put(desc_x, y - 0.03, wrap(desc), fontsize=DESC_SIZE, color=TEXT_COLOR,
                    linespacing=1.35)
        y -= max(hs, hd) + 0.22

    for ext in ("png", "svg"):
        out = os.path.join(OUT_DIR, f"eq_{num:02d}_{stem}.{ext}")
        fig.savefig(out, dpi=DPI, transparent=True, bbox_inches="tight", pad_inches=0.15)
    print(f"Saved: eq_{num:02d}_{stem}.png/.svg")
    plt.close(fig)


if __name__ == "__main__":
    for num, card in enumerate(CARDS, start=1):
        render_card(num, *card)
