"""
Generate NYC_Grocery_Subsidy_Model_Specification.docx
"""

from docx import Document
from docx.shared import Pt, Inches, RGBColor, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
import os

OUT_PATH = r"C:\Users\samia\Code_Projects\grocery_subsidy_analysis\NYC_Grocery_Subsidy_Model_Specification.docx"

# ── helpers ──────────────────────────────────────────────────────────────────

def set_cell_bg(cell, hex_color):
    """Set table cell background color."""
    tc = cell._tc
    tcPr = tc.get_or_add_tcPr()
    shd = OxmlElement('w:shd')
    shd.set(qn('w:val'), 'clear')
    shd.set(qn('w:color'), 'auto')
    shd.set(qn('w:fill'), hex_color)
    tcPr.append(shd)

def set_col_width(table, col_idx, width_inches):
    for row in table.rows:
        row.cells[col_idx].width = Inches(width_inches)

def add_heading(doc, text, level):
    h = doc.add_heading(text, level=level)
    h.paragraph_format.space_before = Pt(14 if level <= 2 else 8)
    h.paragraph_format.space_after = Pt(4)
    return h

def add_para(doc, text, bold=False, italic=False, size=11, color=None, indent=0):
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(6)
    if indent:
        p.paragraph_format.left_indent = Inches(indent)
    run = p.add_run(text)
    run.bold = bold
    run.italic = italic
    run.font.size = Pt(size)
    if color:
        run.font.color.rgb = RGBColor(*color)
    return p

def add_equation_block(doc, label, equation, note=None):
    """Render an equation label + monospace block + optional note."""
    # Label
    lbl = doc.add_paragraph()
    lbl.paragraph_format.space_after = Pt(2)
    lbl.paragraph_format.space_before = Pt(6)
    r = lbl.add_run(label)
    r.bold = True
    r.font.size = Pt(10)
    r.font.color.rgb = RGBColor(0x44, 0x44, 0x44)

    # Equation box — shaded paragraph
    eq_para = doc.add_paragraph()
    eq_para.paragraph_format.left_indent = Inches(0.2)
    eq_para.paragraph_format.right_indent = Inches(0.2)
    eq_para.paragraph_format.space_after = Pt(2)
    eq_run = eq_para.add_run(equation)
    eq_run.font.name = "Courier New"
    eq_run.font.size = Pt(9.5)
    # Light grey shading on paragraph
    pPr = eq_para._p.get_or_add_pPr()
    shd = OxmlElement('w:shd')
    shd.set(qn('w:val'), 'clear')
    shd.set(qn('w:color'), 'auto')
    shd.set(qn('w:fill'), 'F2F2F2')
    pPr.append(shd)

    if note:
        n = doc.add_paragraph()
        n.paragraph_format.left_indent = Inches(0.2)
        n.paragraph_format.space_after = Pt(8)
        nr = n.add_run(note)
        nr.italic = True
        nr.font.size = Pt(9)
        nr.font.color.rgb = RGBColor(0x55, 0x55, 0x55)

def add_term_table(doc, rows):
    """
    rows: list of (term, symbol, type_, description, data_source)
    """
    headers = ["Term", "Symbol", "Type", "Description", "Data Source / Estimation"]
    col_widths = [1.05, 0.85, 0.85, 2.2, 2.3]
    table = doc.add_table(rows=1, cols=5)
    table.style = "Table Grid"
    table.alignment = WD_TABLE_ALIGNMENT.LEFT

    # Header row
    hdr = table.rows[0].cells
    for i, (h, w) in enumerate(zip(headers, col_widths)):
        hdr[i].width = Inches(w)
        hdr[i].text = h
        hdr[i].paragraphs[0].runs[0].bold = True
        hdr[i].paragraphs[0].runs[0].font.size = Pt(9)
        set_cell_bg(hdr[i], "1F4E79")
        hdr[i].paragraphs[0].runs[0].font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)

    for idx, row_data in enumerate(rows):
        row = table.add_row().cells
        bg = "EBF3FA" if idx % 2 == 0 else "FFFFFF"
        for i, (val, w) in enumerate(zip(row_data, col_widths)):
            row[i].width = Inches(w)
            row[i].text = val
            row[i].paragraphs[0].runs[0].font.size = Pt(9)
            set_cell_bg(row[i], bg)
            if i == 2:  # Type column
                t = val.lower()
                if "parameter" in t:
                    row[i].paragraphs[0].runs[0].font.color.rgb = RGBColor(0x17, 0x6B, 0x24)
                    row[i].paragraphs[0].runs[0].bold = True
                elif "dataset" in t or "data" in t:
                    row[i].paragraphs[0].runs[0].font.color.rgb = RGBColor(0x7B, 0x36, 0x00)
                    row[i].paragraphs[0].runs[0].bold = True
    doc.add_paragraph()

def add_source_box(doc, sources):
    """Render a list of literature sources."""
    p = doc.add_paragraph()
    r = p.add_run("Literature Sources")
    r.bold = True
    r.font.size = Pt(10)
    r.font.color.rgb = RGBColor(0x1F, 0x4E, 0x79)
    p.paragraph_format.space_after = Pt(3)

    for src in sources:
        sp = doc.add_paragraph(style="List Bullet")
        sp.paragraph_format.left_indent = Inches(0.25)
        sp.paragraph_format.space_after = Pt(3)
        run = sp.add_run(src["citation"])
        run.font.size = Pt(9)
        if "doi" in src:
            sp.add_run("  ")
            link_run = sp.add_run(f"DOI: {src['doi']}")
            link_run.font.size = Pt(9)
            link_run.font.color.rgb = RGBColor(0x00, 0x56, 0xB3)
            link_run.italic = True
        if "url" in src:
            sp.add_run("  ")
            url_run = sp.add_run(src["url"])
            url_run.font.size = Pt(9)
            url_run.font.color.rgb = RGBColor(0x00, 0x56, 0xB3)
            url_run.italic = True
    doc.add_paragraph()

def add_code_block(doc, code_text, caption=None):
    """Render a code block."""
    if caption:
        cp = doc.add_paragraph()
        cp.paragraph_format.space_after = Pt(2)
        cr = cp.add_run(caption)
        cr.bold = True
        cr.font.size = Pt(10)
        cr.font.color.rgb = RGBColor(0x33, 0x33, 0x33)

    for line in code_text.split("\n"):
        lp = doc.add_paragraph()
        lp.paragraph_format.space_before = Pt(0)
        lp.paragraph_format.space_after = Pt(0)
        lp.paragraph_format.left_indent = Inches(0.2)
        lr = lp.add_run(line if line else " ")
        lr.font.name = "Courier New"
        lr.font.size = Pt(8.5)
        pPr = lp._p.get_or_add_pPr()
        shd = OxmlElement('w:shd')
        shd.set(qn('w:val'), 'clear')
        shd.set(qn('w:color'), 'auto')
        shd.set(qn('w:fill'), 'F7F7F7')
        pPr.append(shd)
    doc.add_paragraph()

def add_callout(doc, title, text, color_hex="D9EDF7"):
    """Render a callout / note box."""
    tbl = doc.add_table(rows=1, cols=1)
    tbl.style = "Table Grid"
    cell = tbl.cell(0, 0)
    set_cell_bg(cell, color_hex)
    p1 = cell.paragraphs[0]
    r1 = p1.add_run(title + "  ")
    r1.bold = True
    r1.font.size = Pt(9.5)
    r2 = p1.add_run(text)
    r2.font.size = Pt(9.5)
    doc.add_paragraph()

def add_numbered_step(doc, n, title, detail):
    p = doc.add_paragraph()
    p.paragraph_format.left_indent = Inches(0.2)
    p.paragraph_format.space_after = Pt(4)
    r1 = p.add_run(f"Step {n}: {title}\n")
    r1.bold = True
    r1.font.size = Pt(10)
    r2 = p.add_run(detail)
    r2.font.size = Pt(10)

# ── document ──────────────────────────────────────────────────────────────────

doc = Document()

# Page margins
for section in doc.sections:
    section.top_margin = Inches(1)
    section.bottom_margin = Inches(1)
    section.left_margin = Inches(1.1)
    section.right_margin = Inches(1.1)

# Default paragraph font
doc.styles["Normal"].font.name = "Calibri"
doc.styles["Normal"].font.size = Pt(11)

# ══════════════════════════════════════════════════════════════════════════════
# TITLE PAGE
# ══════════════════════════════════════════════════════════════════════════════
doc.add_paragraph()
title_p = doc.add_paragraph()
title_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
tr = title_p.add_run("NYC Municipal Grocery Subsidy\nModel Specification and Implementation Guide")
tr.bold = True
tr.font.size = Pt(20)
tr.font.color.rgb = RGBColor(0x1F, 0x4E, 0x79)

sub_p = doc.add_paragraph()
sub_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
sr = sub_p.add_run(
    "Optimization Framework for Allocating a City Subsidy Across Candidate\n"
    "Retail Food Stores in a Defined NYC Region\n\n"
    "Decision-Maker: NYCEDC / Mayor's Office\n"
    "Model Type: Static Single-Period | Choice Model: Multinomial Logit (Mixed Logit)\n"
    "Instruments: Tax Break · Rent Subsidy · Direct Operation"
)
sr.font.size = Pt(11)
sr.font.color.rgb = RGBColor(0x44, 0x44, 0x44)
sub_p.paragraph_format.space_before = Pt(12)

doc.add_paragraph()
add_callout(doc,
    "Causal Chain:",
    "Subsidy (s)  →  Cost Reduction (ΔFC or ΔVC)  →  Price Change (Δp_j, via pass-through θ_j)  →  "
    "Utility Shift (ΔV_ij)  →  Share Reallocation (Δs_ij)  →  Welfare Gain (ΔCS) and Spillovers (ΔQ_k)",
    color_hex="EBF3FA"
)

doc.add_page_break()

# ══════════════════════════════════════════════════════════════════════════════
# TABLE OF CONTENTS (manual)
# ══════════════════════════════════════════════════════════════════════════════
add_heading(doc, "Table of Contents", 1)
toc_items = [
    "Part 1: Model Equations",
    "    1.1  Consumer Demand (Mixed Logit)",
    "    1.2  Store Cost and Pricing",
    "    1.3  Subsidy Pass-Through",
    "    1.4  Optimization Problems",
    "Part 2: Data Loading, Model Setup, and Solution",
    "    2.0  Phase 0 — Data Pipeline",
    "    2.1  Goal 1 — Single-Store Subsidy Effect",
    "    2.2  Goal 2 — Optimal Store Selection (Gurobi / scipy)",
    "    2.3  Goal 3 — Cross-Store Spillovers",
    "Appendix A: Worked Numerical Example",
    "Appendix B: Sensitivity Analysis Framework",
    "Appendix C: Model Validation Checklist",
    "Appendix D: Assumptions, Limitations, and Caveats",
    "Appendix E: Output Interpretation and Plain-Language Template",
]
for item in toc_items:
    p = doc.add_paragraph(item)
    p.paragraph_format.space_after = Pt(2)
    if not item.startswith("    "):
        p.runs[0].bold = True

doc.add_page_break()

# ══════════════════════════════════════════════════════════════════════════════
# PART 1: MODEL EQUATIONS
# ══════════════════════════════════════════════════════════════════════════════
add_heading(doc, "Part 1: Model Equations", 1)
add_para(doc,
    "This section documents every equation used in the model, defines each term, classifies it as a "
    "parameter (estimated from data) or a dataset (directly observed/acquired), and provides the "
    "original literature source with citation and DOI."
)

# ── 1.1 Consumer Demand ──────────────────────────────────────────────────────
add_heading(doc, "1.1  Consumer Demand (Mixed Logit)", 2)
add_para(doc,
    "Consumers are discrete agents, each choosing exactly one grocery store per shopping period. "
    "The multinomial logit (MNL) framework assumes that utility has an observable systematic component "
    "V_ij and an unobservable idiosyncratic component ε_ij. The Mixed Logit extends this by allowing "
    "preference weights to vary across the population, capturing income-driven heterogeneity in "
    "price sensitivity — which is central to evaluating equity impacts of the subsidy."
)

add_heading(doc, "1.1.1  Indirect Utility Function", 3)
add_equation_block(doc,
    "Equation",
    "U_ij = β_q_i · q_j  +  β_v_i · v_j  −  β_p_i · p_j  −  β_d_i · d_ij  +  ε_ij\n"
    "\n"
    "ε_ij ~ Gumbel(0, 1)   i.i.d. extreme value (Type I)"
)
add_term_table(doc, [
    ("Utility of consumer i at store j", "U_ij", "Derived", "Total utility (systematic + random)", "Computed from model; not observed"),
    ("Quality index of store j", "q_j", "Dataset", "Proxy: store type, sq footage, health scores", "NYC DOHMH food retail data; store classification"),
    ("Variety index of store j", "v_j", "Dataset", "Proxy: store type, product SKU count estimate", "NYC DOHMH; IBISWorld average SKU by store type"),
    ("Price level at store j", "p_j", "Dataset / Parameter", "Baseline: back-calculated from revenue/volume; post-subsidy: model output", "ReferenceUSA revenue estimates ÷ quantity; BLS CPI regional food index"),
    ("Travel cost from consumer i to store j", "d_ij", "Dataset", "Walking/transit time in minutes or miles", "Census TIGER centroids + OSMnx or Google Maps API"),
    ("Quality preference weight for consumer i", "β_q_i", "Parameter", "Drawn from MVN(μ_β, Σ_β); mean from literature", "Literature prior: Handbury (2021); scaled by income quintile"),
    ("Variety preference weight for consumer i", "β_v_i", "Parameter", "Drawn from MVN; mean from literature", "Literature prior: Allcott et al. (2019)"),
    ("Price sensitivity for consumer i", "β_p_i", "Parameter", "Higher for lower-income consumers; calibrated to CES food budget shares", "ACS income distribution + BLS Consumer Expenditure Survey"),
    ("Distance sensitivity for consumer i", "β_d_i", "Parameter", "Higher for households without vehicle access", "ACS vehicle access variable (B08201)"),
    ("Idiosyncratic error", "ε_ij", "Distributional assumption", "Unobserved taste; Gumbel distribution gives closed-form logit probabilities", "Assumption (McFadden 1974)"),
])
add_source_box(doc, [
    {"citation": "McFadden, D. (1974). Conditional logit analysis of qualitative choice behavior. In P. Zarembka (Ed.), Frontiers in Econometrics (pp. 105–142). Academic Press.", "url": "https://eml.berkeley.edu/~mcfadden/"},
    {"citation": "Train, K.E. (2009). Discrete Choice Methods with Simulation (2nd ed.). Cambridge University Press.", "url": "https://eml.berkeley.edu/books/train1201.pdf"},
    {"citation": "Allcott, H., Diamond, R., Dubé, J.P., Handbury, J., Rahkovsky, I., & Schnell, M. (2019). Food deserts and the causes of nutritional inequality. Quarterly Journal of Economics, 134(4), 1793–1844.", "doi": "10.1093/qje/qjz015"},
])

add_heading(doc, "1.1.2  Preference Heterogeneity (Random Coefficients)", 3)
add_equation_block(doc,
    "Equation",
    "β_i = (β_q_i, β_v_i, β_p_i, β_d_i)  ~  MVN(μ_β, Σ_β)\n"
    "\n"
    "μ_β = mean preference vector (from literature + ACS calibration)\n"
    "Σ_β = covariance matrix (captures correlated preferences)"
)
add_term_table(doc, [
    ("Vector of preference weights for consumer i", "β_i", "Parameter", "4-dimensional vector drawn from a multivariate normal distribution", "Simulated from MVN(μ_β, Σ_β) estimated from literature + ACS"),
    ("Mean preference vector", "μ_β", "Parameter", "Population-average preference weights; anchored to published grocery demand estimates", "Allcott et al. (2019); Handbury (2021); BLS CES food budget shares"),
    ("Preference covariance matrix", "Σ_β", "Parameter", "Correlation between price and distance sensitivity (e.g., low-income = high on both)", "Calibrated from ACS income and vehicle access; literature"),
])
add_source_box(doc, [
    {"citation": "Train, K.E. (2009). Discrete Choice Methods with Simulation. Cambridge University Press — Chapter 6: Mixed Logit.", "url": "https://eml.berkeley.edu/books/train1201.pdf"},
    {"citation": "Handbury, J. (2021). Are poor cities cheap for everyone? Non-homotheticity and the cost of living across U.S. cities. Econometrica, 89(6), 2679–2715.", "doi": "10.3982/ECTA11738"},
])

add_heading(doc, "1.1.3  Individual Choice Probability", 3)
add_equation_block(doc,
    "Equation (conditional on β_i)",
    "s_ij | β_i  =  exp(V_ij)  /  Σ_k  exp(V_ik)\n"
    "\n"
    "V_ij = β_q_i · q_j  +  β_v_i · v_j  −  β_p_i · p_j  −  β_d_i · d_ij   (systematic utility)"
)
add_term_table(doc, [
    ("Choice probability of consumer i selecting store j", "s_ij", "Derived", "Logistic function of systematic utilities across all stores", "Computed from equation; denominator sums over all J stores"),
    ("Systematic utility of store j for consumer i", "V_ij", "Derived", "Deterministic part of utility, excluding ε_ij", "Computed from β_i and store attributes"),
    ("Index over all stores in the choice set", "k", "Dataset", "Set of J candidate stores in the study area", "USDA SNAP Retailer Locator + NYC DOHMH"),
])
add_source_box(doc, [
    {"citation": "McFadden, D. (1974). Conditional logit analysis of qualitative choice behavior.", "url": "https://eml.berkeley.edu/~mcfadden/"},
    {"citation": "Ben-Akiva, M., & Lerman, S.R. (1985). Discrete Choice Analysis: Theory and Application to Travel Demand. MIT Press. ISBN: 9780262022170"},
])

add_heading(doc, "1.1.4  Aggregate Market Share", 3)
add_equation_block(doc,
    "Equation",
    "S_j  =  (1/N) · Σ_i  s_ij   ≈   ∫ s_ij(β) · f(β) dβ\n"
    "\n"
    "Mixed logit simulation: S_j ≈ (1/R) · Σ_r  s_ij(β^r)  where β^r ~ MVN(μ_β, Σ_β)"
)
add_term_table(doc, [
    ("Aggregate market share of store j", "S_j", "Derived", "Fraction of all consumers who choose store j", "Computed; should sum to 1 across all stores"),
    ("Number of consumers (households) in study area", "N", "Dataset", "Total households in study area", "ACS Table B11001: Household count by census tract"),
    ("Number of simulation draws", "R", "Parameter", "Typically R = 1,000–2,000 for stable estimates", "Researcher choice; higher R = more accurate"),
    ("Draw r from preference distribution", "β^r", "Parameter", "Simulated preference vector from MVN(μ_β, Σ_β)", "Simulated using numpy.random.multivariate_normal"),
])
add_source_box(doc, [
    {"citation": "Train, K.E. (2009). Discrete Choice Methods with Simulation — Chapter 9: Simulation-Assisted Estimation.", "url": "https://eml.berkeley.edu/books/train1201.pdf"},
])

add_heading(doc, "1.1.5  Consumer Welfare (Williams-Daly-Zachary Logsum)", 3)
add_equation_block(doc,
    "Equations",
    "W_i  =  (1/β_p_i) · ln[ Σ_k  exp(V_ik) ]          (expected maximum utility, in dollars)\n"
    "\n"
    "ΔW_i  =  (1/β_p_i) · [ ln Σ_k exp(V_ik_post)  −  ln Σ_k exp(V_ik_pre) ]\n"
    "\n"
    "ΔCS   =  Σ_i  ΔW_i · income_weight_i               (aggregate consumer surplus change)",
    note=(
        "The logsum (log of the denominator) is the log-sum-of-exponentials over all stores. "
        "Dividing by β_p_i (marginal utility of income) converts utils to dollars — "
        "this is the 'rule-of-half' generalization for logit models. "
        "income_weight_i = 1 for unweighted welfare; > 1 for low-income households under equity-weighted objective."
    )
)
add_term_table(doc, [
    ("Consumer welfare in dollars for consumer i", "W_i", "Derived", "Expected utility of best available option, monetized", "Computed from logsum formula"),
    ("Consumer welfare change (post vs. pre subsidy)", "ΔW_i", "Derived", "Dollar-equivalent welfare gain from price reduction", "Computed"),
    ("Aggregate consumer surplus change", "ΔCS", "Derived — primary outcome", "Sum of individual welfare gains; main policy metric", "Computed"),
    ("Pre-subsidy systematic utility", "V_ik_pre", "Derived", "V_ik evaluated at baseline prices", "Computed"),
    ("Post-subsidy systematic utility", "V_ik_post", "Derived", "V_ik_pre + β_p_i · |Δp_j| for subsidized store j", "Computed after applying subsidy"),
    ("Income weight for consumer i", "income_weight_i", "Parameter", "= 1 for standard welfare; scaled by inverse income for equity weighting", "ACS income by tract; researcher policy choice"),
])
add_source_box(doc, [
    {"citation": "Small, K.A., & Rosen, H.S. (1981). Applied welfare economics with discrete choice models. Econometrica, 49(1), 105–130.", "doi": "10.2307/1911129"},
    {"citation": "Williams, H.C.W.L. (1977). On the formation of travel demand models and economic evaluation measures of user benefit. Environment and Planning A, 9(3), 285–344.", "doi": "10.1068/a090285"},
    {"citation": "Train, K.E. (2009). Discrete Choice Methods with Simulation — Chapter 3: Welfare.", "url": "https://eml.berkeley.edu/books/train1201.pdf"},
])

# ── 1.2 Store Cost and Pricing ───────────────────────────────────────────────
add_heading(doc, "1.2  Store Cost and Pricing", 2)
add_para(doc,
    "Each store's cost structure is calibrated from industry benchmarks and chain-specific financial data. "
    "Pricing follows a cost-plus markup rule, with markups calibrated by store type. "
    "The own-price elasticity formula from the MNL model connects the demand side to the pricing side."
)

add_heading(doc, "1.2.1  Total Cost Function", 3)
add_equation_block(doc,
    "Equation",
    "TC_j(Q_j)  =  FC_j  +  VC_j · Q_j\n"
    "\n"
    "FC_j  =  Rent_j  +  Labor_fixed_j  +  Other_fixed_j\n"
    "VC_j  =  COGS_per_unit_j  +  Labor_variable_per_unit_j"
)
add_term_table(doc, [
    ("Total cost of store j", "TC_j", "Derived", "Sum of fixed and variable costs", "Computed from FC_j and VC_j"),
    ("Quantity sold (units or revenue-equivalent)", "Q_j", "Dataset / Derived", "From ReferenceUSA revenue ÷ price; or S_j × M", "ReferenceUSA / Dun & Bradstreet establishment revenue"),
    ("Fixed costs of store j (annual)", "FC_j", "Parameter", "Rent + fixed labor + overhead; does not vary with output", "NYC ACRIS rent data + IBISWorld labor benchmarks"),
    ("Annual rent for store j", "Rent_j", "Dataset", "From property lease records or sq-ft × market rate", "NYC ACRIS (a836-acris.nyc.gov); NYC DOF property records"),
    ("Fixed labor cost", "Labor_fixed_j", "Parameter", "Manager and administrative staff salaries", "IBISWorld Supermarkets & Grocery Stores industry report"),
    ("Variable cost per unit for store j", "VC_j", "Parameter", "COGS + variable labor per unit sold", "IBISWorld gross margin benchmarks: VC ≈ 70–80% of revenue for grocery"),
    ("Cost of goods sold per unit", "COGS_per_unit_j", "Parameter", "Wholesale price of products; varies by store type and chain", "SEC 10-K filings (COGS/Revenue ratio by chain); IBISWorld"),
])
add_source_box(doc, [
    {"citation": "IBISWorld (2024). Supermarkets & Grocery Stores in the US — Industry Report 44511. IBISWorld.", "url": "https://www.ibisworld.com"},
    {"citation": "Supermarket News (annual). Top 75 Retailers & Wholesalers. Penton Media.", "url": "https://www.supermarketnews.com"},
    {"citation": "Walmart Inc. (2024). Annual Report on Form 10-K. SEC EDGAR.", "url": "https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=wmt"},
])

add_heading(doc, "1.2.2  Profit Function", 3)
add_equation_block(doc,
    "Equation",
    "π_j  =  (p_j  −  VC_j) · Q_j  −  FC_j\n"
    "     =  margin_j · Q_j  −  FC_j"
)
add_term_table(doc, [
    ("Profit of store j", "π_j", "Derived", "Revenue minus total costs; key for Goal 3 spillover analysis", "Computed"),
    ("Price level at store j", "p_j", "Dataset / Parameter", "Baseline from ReferenceUSA; post-subsidy from pricing model", "ReferenceUSA; BLS regional CPI food index for calibration"),
    ("Gross margin per unit", "margin_j = p_j − VC_j", "Derived", "Revenue per unit minus variable cost", "Computed; benchmarked against IBISWorld gross margins"),
])

add_heading(doc, "1.2.3  Baseline Pricing Rule (Cost-Plus Markup)", 3)
add_equation_block(doc,
    "Equation",
    "p_j  =  (1 + μ_j) · VC_j\n"
    "\n"
    "Calibrated markup rates by store type:\n"
    "  Large chain (Walmart, Costco, Target):     μ ≈ 0.20 – 0.25\n"
    "  Mid-size regional (Key Food, C-Town):      μ ≈ 0.30 – 0.40\n"
    "  Small independent grocery:                 μ ≈ 0.40 – 0.60\n"
    "\n"
    "Alternative (Lerner condition from MNL elasticity):\n"
    "  p_j  =  VC_j  /  (1 − 1/|ε_jj|)",
    note="Use cost-plus as the base model. Switch to the Lerner condition for robustness check once ε_jj is estimated from the demand side."
)
add_term_table(doc, [
    ("Markup rate for store j", "μ_j", "Parameter", "Calibrated by store type from industry data; not directly observed at store level", "IBISWorld gross margin by store type; SEC 10-K filings"),
    ("Own-price elasticity of demand", "ε_jj", "Derived", "From MNL formula (see 1.2.4); feeds back into Lerner pricing", "Computed from demand model"),
])
add_source_box(doc, [
    {"citation": "Nevo, A. (2001). Measuring market power in the ready-to-eat cereal industry. Econometrica, 69(2), 307–342.", "doi": "10.1111/1468-0262.00194"},
    {"citation": "Berry, S., Levinsohn, J., & Pakes, A. (1995). Automobile prices in market equilibrium. Econometrica, 63(4), 841–890.", "doi": "10.2307/2171802"},
])

add_heading(doc, "1.2.4  Own-Price Elasticity from MNL", 3)
add_equation_block(doc,
    "Equation",
    "Standard MNL:\n"
    "  ε_jj  =  −β_p · p_j · (1 − S_j)\n"
    "\n"
    "Mixed Logit:\n"
    "  ε_jj  =  −p_j · (1/N) · Σ_i [ β_p_i · s_ij · (1 − s_ij) ]",
    note="Expected range for grocery: ε_jj ∈ [−2, −5]. Values outside this range suggest miscalibration of β_p."
)
add_term_table(doc, [
    ("Own-price elasticity of store j", "ε_jj", "Derived", "% change in store j's demand given a 1% price increase at store j", "Computed from demand model"),
    ("Population-average price sensitivity", "β_p", "Parameter", "Mean of β_p_i across consumers (standard MNL only)", "Calibrated from CES + literature"),
    ("Individual choice probability (store j, consumer i)", "s_ij", "Derived", "From MNL formula", "Computed"),
    ("Market share of store j", "S_j", "Derived", "Average of s_ij across consumers", "Computed"),
])
add_source_box(doc, [
    {"citation": "Train, K.E. (2009). Discrete Choice Methods with Simulation — Appendix: Elasticities.", "url": "https://eml.berkeley.edu/books/train1201.pdf"},
    {"citation": "Davis, P. (2006). Spatial competition in retail markets: Movie theaters. RAND Journal of Economics, 37(4), 964–982.", "doi": "10.1111/j.1756-2171.2006.tb00066.x"},
])

add_heading(doc, "1.2.5  Store Volume (Quantity Demanded)", 3)
add_equation_block(doc,
    "Equation",
    "Q_j  =  S_j · M\n"
    "\n"
    "M  =  total market size (dollars per period)\n"
    "    =  N_households · avg_weekly_food_spend · 52\n"
    "\n"
    "Calibration check: Q_j · p_j  ≈  Revenue_j  (from ReferenceUSA)"
)
add_term_table(doc, [
    ("Quantity demanded at store j (units/year)", "Q_j", "Derived", "Market share times total market size", "Computed; verified against ReferenceUSA revenue estimates"),
    ("Total market size ($)", "M", "Parameter", "Total annual food-at-home spending in study area", "ACS households × BLS CES food-at-home expenditure by income quintile"),
    ("Number of households in study area", "N_households", "Dataset", "Household count by census tract", "ACS 5-Year Table B11001"),
    ("Average annual food-at-home spend per household", "avg_food_spend", "Dataset", "Varies by income quintile; ~$3,500–$8,000/year", "BLS Consumer Expenditure Survey (bls.gov/cex)"),
])

# ── 1.3 Subsidy Pass-Through ─────────────────────────────────────────────────
add_heading(doc, "1.3  Subsidy Pass-Through", 2)
add_para(doc,
    "The pass-through equation is the critical behavioral link in the model: it translates a city expenditure "
    "into a consumer price reduction. The pass-through rate θ_j is an empirical parameter calibrated from "
    "the literature. It varies by instrument type and competitive context."
)

add_heading(doc, "1.3.1  General Pass-Through Equation", 3)
add_equation_block(doc,
    "Equation",
    "Δp_j  =  −θ_j · g_j(s)\n"
    "\n"
    "θ_j  ∈  [0, 1]   = pass-through rate\n"
    "g_j(s)           = per-unit price savings generated by subsidy s",
    note="θ_j = 1 means the store passes the entire subsidy to consumers as lower prices. θ_j = 0 means the store keeps all savings as profit. Grocery literature: θ ≈ 0.50–0.85."
)
add_term_table(doc, [
    ("Price change at store j from subsidy", "Δp_j", "Derived", "Reduction in consumer-facing price; feeds into utility update", "Computed from pass-through equation"),
    ("Pass-through rate", "θ_j", "Parameter", "Fraction of subsidy cost reduction passed to consumers; calibrated from literature", "Besanko et al. (2005); Nakamura & Zerom (2010); vary in sensitivity analysis"),
    ("Per-unit price savings from subsidy s", "g_j(s)", "Derived", "Depends on instrument type (see 1.3.2–1.3.4)", "Computed from instrument-specific formula"),
    ("Total subsidy amount (dollars/year)", "s", "Decision variable", "Set by the city; the lever in the optimization", "City policy decision; constrained by budget B"),
])
add_source_box(doc, [
    {"citation": "Besanko, D., Dubé, J.P., & Gupta, S. (2005). Own-brand and cross-brand retail pass-through. Marketing Science, 24(1), 123–137.", "doi": "10.1287/mksc.1040.0107"},
    {"citation": "Nakamura, E., & Zerom, D. (2010). Accounting for incomplete pass-through. Review of Economic Studies, 77(3), 1192–1230.", "doi": "10.1111/j.1467-937X.2009.00597.x"},
    {"citation": "Weyl, E.G., & Fabinger, M. (2013). Pass-through as an economic tool: Principles of incidence under imperfect competition. Journal of Political Economy, 121(3), 528–583.", "doi": "10.1086/670401"},
])

add_heading(doc, "1.3.2  Instrument 1: Tax Break", 3)
add_equation_block(doc,
    "Equations",
    "Effective tax reduction:  ΔTax_j  =  −τ · Tax_j\n"
    "\n"
    "Per-unit saving:          g_j(s)  =  τ · Tax_j / Q_j\n"
    "\n"
    "Price effect:             Δp_j    =  −θ_j · τ · Tax_j / Q_j\n"
    "\n"
    "Total subsidy cost:       s  =  τ · Tax_j"
)
add_term_table(doc, [
    ("Fraction of tax liability forgiven", "τ", "Decision variable", "The policy lever for this instrument; τ = 1 = full exemption", "City policy decision"),
    ("Current annual property/business tax for store j", "Tax_j", "Dataset", "Assessed annual tax bill", "NYC Property Tax Data (NYCDB); NYC Dept. of Finance"),
    ("Volume at store j", "Q_j", "Derived", "See Section 1.2.5", "Computed"),
])

add_heading(doc, "1.3.3  Instrument 2: Rent Subsidy", 3)
add_equation_block(doc,
    "Equations",
    "Fixed cost reduction:     ΔFC_j   =  −σ_rent\n"
    "\n"
    "Per-unit saving:          g_j(s)  =  σ_rent / Q_j\n"
    "\n"
    "Price effect:             Δp_j    =  −θ_j · σ_rent / Q_j\n"
    "\n"
    "Total subsidy cost:       s  =  σ_rent  (annual dollar amount)"
)
add_term_table(doc, [
    ("Annual rent subsidy amount", "σ_rent", "Decision variable", "The policy lever for this instrument; city pays σ_rent of store's annual rent", "City policy decision; upper bound = full rent Rent_j"),
    ("Current annual rent for store j", "Rent_j", "Dataset", "From property lease records", "NYC ACRIS lease filings; NYC DOF assessed values; market rate × sq footage"),
])

add_heading(doc, "1.3.4  Instrument 3: Direct Operation (State-Run)", 3)
add_equation_block(doc,
    "Equations",
    "Option A — Zero-markup pricing:\n"
    "  p_j_post  =  VC_j   (city absorbs all fixed cost losses)\n"
    "\n"
    "Option B — Per-unit subsidy:\n"
    "  p_j_post  =  p_j_pre  −  s_unit\n"
    "  s_unit    =  subsidy per unit sold\n"
    "  Total cost = s_unit · Q_j\n"
    "\n"
    "Equivalent pass-through: θ_j = 1 (full pass-through by design)\n"
    "\n"
    "City operating loss: Loss = FC_j  −  (p_j_post − VC_j) · Q_j",
    note="Direct operation is the strongest instrument but requires the city to cover operating losses. The binding constraint is the budget B covering FC_j plus any per-unit subsidy."
)
add_term_table(doc, [
    ("Post-subsidy price under direct operation", "p_j_post", "Decision variable", "City sets price directly; either = VC_j or = p_j − s_unit", "Policy decision"),
    ("Per-unit subsidy amount", "s_unit", "Decision variable", "City pays s_unit per unit sold to cover below-cost pricing", "Policy decision"),
    ("City operating loss", "Loss", "Derived", "Net cost to city of operating the store below cost-plus pricing", "Computed; must satisfy Loss ≤ B"),
])

add_heading(doc, "1.3.5  Post-Subsidy Utility and Share Update", 3)
add_equation_block(doc,
    "Core update equations (used in all three Goals)",
    "V_ij*_post  =  V_ij*_pre  +  β_p_i · |Δp_j*|         (subsidized store j*)\n"
    "V_ik_post   =  V_ik_pre                                (all other stores k ≠ j*)\n"
    "\n"
    "s_ij_post   =  exp(V_ij_post)  /  Σ_l exp(V_il_post)  (updated choice probability)\n"
    "\n"
    "ΔCS         =  Σ_i (1/β_p_i) · [ln Σ_l exp(V_il_post)  −  ln Σ_l exp(V_il_pre)]",
    note="This is the complete pipeline: subsidy → price drop → utility shift → share reallocation → welfare gain."
)

# ── 1.4 Optimization Problems ────────────────────────────────────────────────
add_heading(doc, "1.4  Optimization Problems", 2)

add_heading(doc, "1.4.1  Goal 1: Minimum Effective Subsidy (Single Store)", 3)
add_equation_block(doc,
    "Problem statement",
    "min   s\n"
    "s.t.  Δp_j(s)  ≥  Δp_min          (price must fall by at least Δp_min, e.g. 5%)\n"
    "      ΔCS_j(s) ≥  ΔCS_min         (minimum welfare gain threshold)\n"
    "      s        ≤  B                (total budget)\n"
    "      s        ≥  0\n"
    "\n"
    "Solution: invert  Δp_j(s) = −θ_j · g_j(s)  to get  s*(Δp_min)\n"
    "Then check:        ΔCS_j(s*) ≥ ΔCS_min",
    note="This is a single-variable inversion, not a hard optimization. Evaluate ΔCS over a grid of s values to trace the cost-effectiveness curve."
)
add_term_table(doc, [
    ("Minimum required price reduction", "Δp_min", "Parameter", "Policy threshold, e.g. 5% of baseline price p_j", "Researcher/policy choice"),
    ("Minimum welfare gain threshold", "ΔCS_min", "Parameter", "Policy threshold, e.g. $X per household per year", "Researcher/policy choice"),
    ("Total budget", "B", "Parameter / constraint", "City's annual budget for the subsidy program", "City budget allocation (exogenous input)"),
    ("Minimum effective subsidy", "s*", "Derived — primary output", "Smallest subsidy achieving both Δp_min and ΔCS_min", "Computed"),
])

add_heading(doc, "1.4.2  Goal 2: Optimal Store Selection", 3)
add_equation_block(doc,
    "Binary selection (K stores from J candidates)",
    "max_{x_j ∈ {0,1}}    Σ_j  x_j · ΔCS_j(s_j)\n"
    "\n"
    "s.t.   Σ_j  x_j · s_j  ≤  B          (total budget)\n"
    "       Σ_j  x_j         ≤  K          (at most K stores selected)\n"
    "       x_j              ≤  e_j  ∀j    (eligibility: e_j ∈ {0,1})\n"
    "       s_j              ≥  s_j_min    (minimum effective subsidy per store)\n"
    "       x_j              ∈  {0, 1}"
)
add_equation_block(doc,
    "Continuous allocation (split budget across stores)",
    "max_{s_j ≥ 0}    Σ_j  ΔCS_j(s_j)\n"
    "\n"
    "s.t.   Σ_j  s_j  ≤  B\n"
    "       s_j = 0  if  e_j = 0   (ineligible stores receive no subsidy)\n"
    "\n"
    "KKT optimality condition (if ΔCS_j concave):  dΔCS_j/ds_j = λ  for all active stores\n"
    "(equalize marginal welfare gain per dollar across selected stores)"
)
add_term_table(doc, [
    ("Binary store selection variable", "x_j", "Decision variable", "1 if store j is selected; 0 otherwise", "Optimization output"),
    ("Subsidy allocated to store j", "s_j", "Decision variable", "Dollar amount of subsidy; may be fixed or also optimized", "Optimization output"),
    ("Welfare gain if store j receives subsidy s_j", "ΔCS_j(s_j)", "Derived", "From Goal 1 computation applied to store j", "Computed for each candidate store"),
    ("Maximum number of stores to subsidize", "K", "Parameter", "Policy constraint (usually K = 1 or K = 2)", "City policy decision"),
    ("Eligibility indicator for store j", "e_j", "Dataset", "1 if store passes all eligibility criteria; 0 otherwise", "SNAP authorization status + location zone + size + ownership type"),
    ("Minimum subsidy threshold for store j", "s_j_min", "Derived", "Smallest s achieving meaningful ΔCS at store j (from Goal 1)", "Computed in Goal 1 phase"),
    ("Shadow price on budget constraint", "λ", "Derived", "Marginal welfare gain per dollar of budget; equalized at optimum", "KKT condition output"),
])
add_source_box(doc, [
    {"citation": "Wolsey, L.A. (1998). Integer Programming. Wiley. ISBN: 9780471283669"},
    {"citation": "Gurobi Optimization (2024). Gurobi Optimizer Reference Manual. Gurobi LLC.", "url": "https://www.gurobi.com/documentation/"},
])

add_heading(doc, "1.4.3  Goal 3: Cross-Store Spillovers (Comparative Statics)", 3)
add_equation_block(doc,
    "Shock propagation (not an optimization)",
    "Given: optimal subsidy s* at store j*  →  price change Δp_j*\n"
    "\n"
    "For all rival stores k ≠ j*  (prices held fixed — no rival response):\n"
    "\n"
    "  ΔS_k      =  S_k_post  −  S_k_pre\n"
    "             =  (1/N) · Σ_i [ s_ik_post  −  s_ik_pre ]\n"
    "\n"
    "  ΔQ_k      =  M · ΔS_k\n"
    "\n"
    "  Δπ_k      =  (p_k  −  VC_k) · ΔQ_k          (variable profit change only; FC_k unchanged)\n"
    "\n"
    "  ΔW_total  =  ΔCS  +  Δπ_j*  +  Σ_{k≠j*} Δπ_k   (net social surplus change)"
)
add_term_table(doc, [
    ("Change in market share of rival store k", "ΔS_k", "Derived", "Negative (store k loses customers to subsidized j*)", "Computed from updated logit denominator"),
    ("Change in quantity at rival store k", "ΔQ_k", "Derived", "ΔQ_k = M · ΔS_k; measured in sales volume or revenue", "Computed"),
    ("Change in variable profit of rival store k", "Δπ_k", "Derived", "Profit loss from reduced traffic; FC unchanged in short run", "Computed"),
    ("Net social surplus change", "ΔW_total", "Derived — key output of Goal 3", "Consumer gain plus all profit changes (positive if ΔCS dominates losses)", "Computed"),
    ("Profit change at subsidized store j*", "Δπ_j*", "Derived", "May increase (if volume gain > subsidy cost) or decrease (if price cut too large)", "Computed"),
])

doc.add_page_break()

# ══════════════════════════════════════════════════════════════════════════════
# PART 2: IMPLEMENTATION
# ══════════════════════════════════════════════════════════════════════════════
add_heading(doc, "Part 2: Data Loading, Model Setup, and Solution", 1)
add_para(doc,
    "This section provides step-by-step instructions for each phase of the implementation. "
    "Phase 0 covers data acquisition and cleaning. Phases 1–3 correspond to Goals 1–3. "
    "Code examples use Python with Gurobi (gurobipy) for Goal 2 optimization and scipy for Goals 1 and 3."
)
add_callout(doc, "Software stack:",
    "Python 3.10+ | pandas, geopandas, numpy, scipy | gurobipy (Gurobi 11) | "
    "xlogit or pylogit (demand estimation) | osmnx (distance matrix) | folium (maps)",
    color_hex="EBF3FA"
)

# ── Phase 0 ──────────────────────────────────────────────────────────────────
add_heading(doc, "2.0  Phase 0 — Data Pipeline", 2)
add_para(doc, "Output: clean dataset with store attributes, consumer demographics, and distance matrix.")

steps_p0 = [
    (1, "Define geographic scope",
     "Select 1–3 contiguous NYC community districts or ~10–20 census tracts containing food deserts. "
     "Use NYC Community Health Profiles or USDA Food Access Research Atlas to identify low-access areas."),
    (2, "Download ACS data",
     "Pull ACS 5-year tract-level estimates: households (B11001), income distribution (B19001), "
     "vehicle access (B08201), household size (B25010). Use the Census API or censusdataapi Python package."),
    (3, "Build candidate store list",
     "Download USDA SNAP Retailer Locator CSV. Filter to study area bounding box. "
     "Cross-reference with NYC DOHMH food establishment data. Geocode addresses. "
     "Classify stores by type: supermarket, discount, independent bodega."),
    (4, "Compute distance matrix d_ij",
     "Compute tract centroids from TIGER shapefiles (geopandas). "
     "Use osmnx to build a street network graph. Calculate walking or transit time "
     "from each tract centroid to each store. Output: N_tracts × J_stores matrix."),
    (5, "Assign store attributes q_j and v_j",
     "Score quality (q_j): supermarket = 3, discount/dollar store = 2, bodega/convenience = 1. "
     "Score variety (v_j): use IBISWorld average SKU count by store type (normalized 0–1). "
     "If available, supplement with NYC DOHMH inspection scores."),
    (6, "Calibrate cost structure (FC_j, VC_j)",
     "For each store: estimate Rent_j from NYC ACRIS × sq footage × $/sq-ft market rate. "
     "Estimate Labor_fixed from employee count (ReferenceUSA) × average grocery manager wage (BLS OES). "
     "Set VC_j = COGS benchmark from IBISWorld (e.g., VC ≈ 72% of revenue for conventional grocery). "
     "Get Revenue_j from ReferenceUSA; back out Q_j = Revenue_j / p_j."),
    (7, "Set preference parameters (β)",
     "Set mean preferences μ_β from literature. Scale β_p_i by income: "
     "for each tract, use ACS median income to compute a scaling factor "
     "(e.g., β_p_i = β_p_base × (median_income_region / median_income_i)^0.5). "
     "Set Σ_β diagonal entries from literature standard deviations."),
]
for n, title, detail in steps_p0:
    add_numbered_step(doc, n, title, detail)

add_code_block(doc, """# Phase 0 — Data Loading Example (Python)
import pandas as pd
import geopandas as gpd
import numpy as np
from censusdataapi import CensusData   # pip install censusdataapi

# ── 1. ACS data ──────────────────────────────────────────────────────────────
census = CensusData('YOUR_API_KEY')
acs = census.acs5(
    variables=['B11001_001E',  # total households
               'B19001_001E',  # household income distribution
               'B08201_001E',  # vehicle access
               'B19013_001E'], # median household income
    for_='tract:*',
    in_='state:36 county:005,047,061,081,085'  # NYC counties
)
acs.to_csv('data/acs_tracts.csv', index=False)

# ── 2. SNAP stores ───────────────────────────────────────────────────────────
snap = pd.read_csv('data/snap_retailer_locator.csv')
snap = snap[(snap['State'] == 'NY') &
            (snap['City'].str.upper().isin(['NEW YORK', 'BRONX', 'BROOKLYN', ...]))]
# Geocode using geopy or pre-geocoded addresses
snap_gdf = gpd.GeoDataFrame(snap, geometry=gpd.points_from_xy(snap.Longitude, snap.Latitude))

# ── 3. Distance matrix ───────────────────────────────────────────────────────
import osmnx as ox
# Download walking network for study area
G = ox.graph_from_place('Bronx, New York, USA', network_type='walk')
# Compute nearest node for each tract centroid and store
# ... (loop over tracts and stores, use ox.distance.nearest_nodes)
# Store result: d_ij matrix (N_tracts × J_stores)
""", caption="Phase 0: Data Loading")

# ── Phase 1 ──────────────────────────────────────────────────────────────────
add_heading(doc, "2.1  Goal 1 — Single-Store Subsidy Effect", 2)
add_para(doc, "Output: cost-effectiveness curve ΔCS(s) and minimum effective subsidy s* for one store.")

steps_g1 = [
    (1, "Select representative store j*",
     "Choose a mid-size independent in a food desert tract. All other store prices stay at baseline."),
    (2, "Build price-as-function-of-subsidy",
     "For each instrument, compute g_j(s) and Δp_j(s) = −θ_j · g_j(s). "
     "Create a subsidy grid: s_grid = np.linspace(0, B_max, 500)."),
    (3, "Compute baseline systematic utilities V_ij_pre",
     "V_ij = β_q_i·q_j + β_v_i·v_j − β_p_i·p_j − β_d_i·d_ij for all (i, j). "
     "Store as matrix V_pre of shape (N_consumers, J_stores)."),
    (4, "For each s in grid, compute ΔCS(s)",
     "Update V_ij*_post = V_ij*_pre + β_p_i · |Δp_j*(s)|. "
     "Compute logsum_pre = log(sum(exp(V_ij_pre), axis=1)) for each consumer. "
     "Compute logsum_post = log(sum(exp(V_ij_post), axis=1)). "
     "ΔW_i = (1/β_p_i) · (logsum_post − logsum_pre). ΔCS = sum(ΔW_i)."),
    (5, "Find minimum effective subsidy s*",
     "s* = min{s : ΔCS(s) ≥ ΔCS_min AND Δp_j(s) ≥ Δp_min}."),
    (6, "Sensitivity on θ and β_p",
     "Repeat steps 2–5 for θ ∈ {0.4, 0.6, 0.8} and β_p scale ∈ {0.8, 1.0, 1.2}. "
     "Plot 3×3 grid of ΔCS(s) curves."),
    (7, "Compare instruments",
     "At fixed s* (from rent subsidy baseline), compare ΔCS across all three instruments."),
]
for n, title, detail in steps_g1:
    add_numbered_step(doc, n, title, detail)

add_code_block(doc, """# Goal 1 — Single-Store Subsidy Effect (Python / scipy)
import numpy as np
import pandas as pd
from scipy.special import logsumexp

# ── Parameters ────────────────────────────────────────────────────────────────
# Stores: J=8, Consumers (tract-level): N=15 tracts
# β_p_i: price sensitivity per consumer tract (higher for lower income)
# V_pre: (N, J) matrix of pre-subsidy systematic utilities
# j_star: index of subsidized store

def compute_DCS(s, j_star, theta, FC_j, Q_j, V_pre, beta_p_i, instrument='rent'):
    \"\"\"
    Compute aggregate consumer surplus change for subsidy level s at store j*.
    instrument: 'rent', 'tax', or 'direct'
    \"\"\"
    # Step 1: price change from subsidy
    if instrument == 'rent':
        g = s / Q_j[j_star]                    # per-unit saving
    elif instrument == 'tax':
        tau = s / FC_j['tax'][j_star]           # fraction of tax forgiven
        g = s / Q_j[j_star]
    elif instrument == 'direct':
        g = s / Q_j[j_star]                    # theta = 1

    delta_p = theta * g                        # price reduction (positive value)

    # Step 2: update utility matrix
    V_post = V_pre.copy()
    V_post[:, j_star] += beta_p_i * delta_p   # consumer i gains beta_p_i * delta_p

    # Step 3: logsum welfare
    logsum_pre  = logsumexp(V_pre,  axis=1)    # shape (N,)
    logsum_post = logsumexp(V_post, axis=1)    # shape (N,)

    # Step 4: welfare change per consumer (dollars = utils / beta_p)
    delta_W_i = (1.0 / beta_p_i) * (logsum_post - logsum_pre)

    # Step 5: aggregate (weight by household count)
    DCS = np.sum(delta_W_i * household_count)  # household_count: (N,) array
    return DCS, delta_p

# ── Grid search ───────────────────────────────────────────────────────────────
s_grid   = np.linspace(0, 2_000_000, 500)  # $0 to $2M annual subsidy
theta    = 0.65                            # base pass-through rate
DCS_vals = []
dp_vals  = []

for s in s_grid:
    dcs, dp = compute_DCS(s, j_star=2, theta=theta,
                          FC_j=FC_j, Q_j=Q_j,
                          V_pre=V_pre, beta_p_i=beta_p_i)
    DCS_vals.append(dcs)
    dp_vals.append(dp)

DCS_vals = np.array(DCS_vals)
dp_vals  = np.array(dp_vals)

# ── Find s* ───────────────────────────────────────────────────────────────────
DCS_min = 50_000     # $50K aggregate welfare gain threshold
dp_min  = p_j[2] * 0.05   # 5% price reduction

mask = (DCS_vals >= DCS_min) & (dp_vals >= dp_min)
s_star = s_grid[mask][0] if mask.any() else None
print(f"Minimum effective subsidy: ${s_star:,.0f}")
""", caption="Goal 1: Python Implementation")

# ── Phase 2 ──────────────────────────────────────────────────────────────────
add_heading(doc, "2.2  Goal 2 — Optimal Store Selection (Gurobi)", 2)
add_para(doc, "Output: optimal store selection and subsidy allocation that maximizes ΔCS subject to budget B.")

steps_g2 = [
    (1, "Run Goal 1 for every candidate store",
     "Call compute_DCS(B, j, theta, ...) for each store j. "
     "Store results as DCS_j = np.array([ΔCS_1, ΔCS_2, ..., ΔCS_J]) evaluated at budget B."),
    (2, "Apply eligibility filters",
     "Set e_j = 0 for stores that are not SNAP-authorized, outside the target zone, "
     "above the size threshold, or fail other policy criteria."),
    (3, "Binary selection (K=1): enumerate",
     "If selecting only one store, compute argmax_j {DCS_j · e_j}. No solver needed."),
    (4, "Binary selection (K>1): Gurobi ILP",
     "Set up integer linear program: x_j ∈ {0,1}, maximize Σ DCS_j·x_j, "
     "subject to Σ s_j·x_j ≤ B, Σ x_j ≤ K, x_j ≤ e_j."),
    (5, "Continuous allocation: Gurobi QP or scipy SLSQP",
     "If ΔCS_j(s_j) is approximated as piecewise-linear or quadratic in s_j, "
     "set up a continuous nonlinear program maximizing Σ ΔCS_j(s_j) s.t. Σ s_j ≤ B."),
    (6, "Distributional analysis",
     "Decompose ΔCS by income quintile: ΔCS_q = Σ_{i in quintile q} ΔW_i. "
     "Compare equity profile across store selections."),
    (7, "Instrument comparison",
     "For the optimal store j*, re-run Goal 1 under all three instruments at equal cost s*. "
     "Report ΔCS and Δp_j per instrument."),
]
for n, title, detail in steps_g2:
    add_numbered_step(doc, n, title, detail)

add_code_block(doc, """# Goal 2 — Optimal Store Selection using Gurobi (gurobipy)
import gurobipy as gp
from gurobipy import GRB
import numpy as np

# ── Inputs ────────────────────────────────────────────────────────────────────
# DCS_j : np.array of shape (J,) — welfare gain if store j receives budget B
# s_j   : np.array of shape (J,) — minimum effective subsidy per store
#          (from Goal 1; or set = B for equal treatment)
# e_j   : np.array of shape (J,), binary eligibility
# B     : total budget (scalar)
# K     : max stores to select (scalar, e.g. K=1 or K=2)

J     = len(DCS_j)
B     = 1_500_000    # $1.5M annual budget
K     = 2            # select up to 2 stores

# ── Build Gurobi model ────────────────────────────────────────────────────────
m = gp.Model("store_selection")
m.setParam('OutputFlag', 0)  # suppress solver output

# Decision variables: x_j ∈ {0,1}
x = m.addVars(J, vtype=GRB.BINARY, name="x")

# Objective: maximize total welfare gain
m.setObjective(gp.quicksum(DCS_j[j] * x[j] for j in range(J)), GRB.MAXIMIZE)

# Constraint 1: total subsidy cost ≤ budget
m.addConstr(gp.quicksum(s_j[j] * x[j] for j in range(J)) <= B, "budget")

# Constraint 2: at most K stores selected
m.addConstr(gp.quicksum(x[j] for j in range(J)) <= K, "max_stores")

# Constraint 3: eligibility
for j in range(J):
    m.addConstr(x[j] <= e_j[j], f"eligibility_{j}")

# ── Solve ─────────────────────────────────────────────────────────────────────
m.optimize()

if m.status == GRB.OPTIMAL:
    selected = [j for j in range(J) if x[j].X > 0.5]
    print(f"Optimal stores: {selected}")
    print(f"Total ΔCS:      ${m.ObjVal:,.0f}")
    print(f"Total cost:     ${sum(s_j[j] for j in selected):,.0f}")
else:
    print("No feasible solution found.")

# ── Continuous allocation variant (scipy SLSQP) ───────────────────────────────
from scipy.optimize import minimize

def neg_total_DCS(s_vec):
    \"\"\"Negative total welfare (for minimization).\"\"\"
    return -sum(compute_DCS(s_vec[j], j, theta, ...)[0]
                for j in range(J) if e_j[j] == 1)

s0      = np.ones(J) * B / J    # equal split as starting point
bounds  = [(0, B) for _ in range(J)]
constr  = {'type': 'ineq', 'fun': lambda s: B - np.sum(s)}  # budget constraint

result = minimize(neg_total_DCS, s0, method='SLSQP',
                  bounds=bounds, constraints=constr,
                  options={'ftol': 1e-9, 'maxiter': 1000})

s_opt = result.x
print("Optimal continuous allocation:", dict(enumerate(s_opt.round(0))))
""", caption="Goal 2: Gurobi + scipy Implementation")

# ── Phase 3 ──────────────────────────────────────────────────────────────────
add_heading(doc, "2.3  Goal 3 — Cross-Store Spillovers", 2)
add_para(doc, "Output: ΔQ_k, ΔRev_k, and Δπ_k for all rival stores; net social welfare ΔW_total.")

steps_g3 = [
    (1, "Start from Phase 2 optimal",
     "Use the optimal store j* and subsidy s* from Goal 2. "
     "V_ij*_post is already computed from Goal 1/2 run."),
    (2, "Recompute all market shares",
     "Hold all store prices fixed except j*. Recompute s_ik_post for all k using updated logit denominator."),
    (3, "Compute quantity and revenue changes",
     "ΔS_k = S_k_post − S_k_pre. ΔQ_k = M · ΔS_k. ΔRev_k = p_k · ΔQ_k."),
    (4, "Compute profit changes",
     "Δπ_k = (p_k − VC_k) · ΔQ_k. Negative for rivals losing traffic."),
    (5, "Identify at-risk stores",
     "Flag stores where π_k_post = π_k_pre + Δπ_k < 0 (subsidy makes rival unprofitable)."),
    (6, "Compute net social welfare",
     "ΔW_total = ΔCS + Δπ_j* + Σ_{k≠j*} Δπ_k."),
    (7, "Sensitivity and geographic map",
     "Re-run for second- and third-best store selections. Map ΔQ_k as choropleth."),
]
for n, title, detail in steps_g3:
    add_numbered_step(doc, n, title, detail)

add_code_block(doc, """# Goal 3 — Cross-Store Spillovers (Python)
import numpy as np
from scipy.special import softmax

def compute_spillovers(j_star, delta_p, V_pre, M, p_j, VC_j, beta_p_i, household_count):
    \"\"\"
    Compute market share, revenue, and profit changes for all rival stores.

    Parameters
    ----------
    j_star    : index of subsidized store
    delta_p   : price reduction at store j* (scalar, positive)
    V_pre     : (N, J) matrix of pre-subsidy systematic utilities
    M         : total market size in dollars
    p_j       : (J,) baseline prices
    VC_j      : (J,) variable costs
    beta_p_i  : (N,) price sensitivity per consumer group
    household_count : (N,) number of households per tract

    Returns
    -------
    dict with keys: delta_S, delta_Q, delta_Rev, delta_pi, pi_pre, pi_post
    \"\"\"
    N, J = V_pre.shape

    # Pre-subsidy shares
    S_pre = np.zeros(J)
    for i in range(N):
        s_i = softmax(V_pre[i])
        S_pre += s_i * household_count[i]
    S_pre /= household_count.sum()

    # Post-subsidy utility (only j* changes)
    V_post = V_pre.copy()
    V_post[:, j_star] += beta_p_i * delta_p

    # Post-subsidy shares
    S_post = np.zeros(J)
    for i in range(N):
        s_i = softmax(V_post[i])
        S_post += s_i * household_count[i]
    S_post /= household_count.sum()

    # Market share and quantity changes
    delta_S   = S_post - S_pre                    # (J,)
    delta_Q   = delta_S * M                       # (J,) — positive for j*, negative for rivals

    # Revenue and profit changes
    delta_Rev = p_j * delta_Q                     # (J,)
    delta_pi  = (p_j - VC_j) * delta_Q           # (J,) — variable profit change

    # Baseline and post-subsidy profits (use known Q_j from data)
    pi_pre  = (p_j - VC_j) * Q_j - FC_j
    pi_post = pi_pre + delta_pi
    pi_post[j_star] -= s  # cost of subsidy borne by city (store profit neutral if θ=1)

    return {
        'delta_S':   delta_S,
        'delta_Q':   delta_Q,
        'delta_Rev': delta_Rev,
        'delta_pi':  delta_pi,
        'pi_pre':    pi_pre,
        'pi_post':   pi_post,
        'at_risk':   [k for k in range(J) if k != j_star and pi_post[k] < 0]
    }

# Run
results = compute_spillovers(j_star=2, delta_p=dp_star,
                             V_pre=V_pre, M=M,
                             p_j=p_j, VC_j=VC_j,
                             beta_p_i=beta_p_i,
                             household_count=household_count)

print("At-risk stores:", results['at_risk'])
print("Net social welfare change: $", (DCS + results['delta_pi'].sum()).round(0))
""", caption="Goal 3: Spillover Computation")

doc.add_page_break()

# ══════════════════════════════════════════════════════════════════════════════
# APPENDIX A: WORKED NUMERICAL EXAMPLE
# ══════════════════════════════════════════════════════════════════════════════
add_heading(doc, "Appendix A: Worked Numerical Example", 1)
add_para(doc,
    "This example walks through the model end-to-end with illustrative (hypothetical) numbers "
    "for a single mid-size independent grocery store in a food desert census tract in the South Bronx. "
    "All figures are plausible but not real."
)

add_heading(doc, "A.1  Setup", 2)
add_para(doc, "Study area: 1 census tract. Stores: J = 3 (one mid-size independent, one discount, one chain). "
              "Consumers: N = 800 households. Market size M = 800 × $5,200 = $4,160,000/year.")

add_heading(doc, "A.2  Store Attributes", 2)
tbl = doc.add_table(rows=1, cols=7)
tbl.style = "Table Grid"
hdrs = ["Store", "Type", "q_j", "v_j", "p_j (index)", "FC_j ($K/yr)", "VC_j (% of p)"]
for i, h in enumerate(hdrs):
    c = tbl.rows[0].cells[i]
    c.text = h
    c.paragraphs[0].runs[0].bold = True
    c.paragraphs[0].runs[0].font.size = Pt(9)
    set_cell_bg(c, "1F4E79")
    c.paragraphs[0].runs[0].font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)

rows_a = [
    ["Store 1 (Independent)", "Independent", "2", "2", "1.00 (base)", "$320K", "72%"],
    ["Store 2 (Discount)", "Discount", "1", "1", "0.88", "$180K", "78%"],
    ["Store 3 (Chain)", "Supermarket", "3", "3", "1.10", "$680K", "68%"],
]
for row_data in rows_a:
    row = tbl.add_row().cells
    for i, val in enumerate(row_data):
        row[i].text = val
        row[i].paragraphs[0].runs[0].font.size = Pt(9)
doc.add_paragraph()

add_heading(doc, "A.3  Subsidy Calculation (Rent Subsidy at Store 1)", 2)
add_equation_block(doc,
    "Given values",
    "FC_j = $320,000/year   Rent_j = $180,000/year\n"
    "Q_j = 95,000 units/year   θ_j = 0.65\n"
    "s = $100,000 rent subsidy\n"
    "\n"
    "Per-unit saving:   g_j = $100,000 / 95,000 = $1.053/unit\n"
    "Price reduction:   Δp_j = −0.65 × $1.053 = −$0.684/unit  (≈ 6.8% of baseline)\n"
)

add_heading(doc, "A.4  Welfare Calculation (3 Consumer Groups)", 2)
add_para(doc, "Three income groups: Low ($25K), Mid ($55K), High ($90K). "
              "β_p scaled inversely with income.")
tbl2 = doc.add_table(rows=1, cols=6)
tbl2.style = "Table Grid"
h2 = ["Consumer Group", "Households", "β_p_i", "ΔV_i (at store 1)", "ΔW_i ($/HH)", "Total ΔW_i"]
for i, h in enumerate(h2):
    c = tbl2.rows[0].cells[i]
    c.text = h
    c.paragraphs[0].runs[0].bold = True
    c.paragraphs[0].runs[0].font.size = Pt(9)
    set_cell_bg(c, "1F4E79")
    c.paragraphs[0].runs[0].font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
r2 = [
    ["Low income ($25K)", "320", "0.45", "+0.308", "$0.685/yr", "$219"],
    ["Mid income ($55K)", "360", "0.30", "+0.205", "$0.683/yr", "$246"],
    ["High income ($90K)", "120", "0.18", "+0.123", "$0.683/yr", "$82"],
    ["Total", "800", "—", "—", "—", "$547/yr"],
]
for d in r2:
    row = tbl2.add_row().cells
    for i, val in enumerate(d):
        row[i].text = val
        row[i].paragraphs[0].runs[0].font.size = Pt(9)
doc.add_paragraph()

add_callout(doc, "Interpretation:",
    "A $100K annual rent subsidy at Store 1 yields ~$547/year in aggregate consumer welfare gain. "
    "Cost-effectiveness ratio: $547 / $100,000 = $0.0055 per dollar spent. "
    "To reach $10,000 in welfare gains would require approximately $1.83M in annual rent subsidy.",
    color_hex="E8F5E9"
)

doc.add_page_break()

# ══════════════════════════════════════════════════════════════════════════════
# APPENDIX B: SENSITIVITY ANALYSIS
# ══════════════════════════════════════════════════════════════════════════════
add_heading(doc, "Appendix B: Sensitivity Analysis Framework", 1)
add_para(doc,
    "The model's key output — the minimum effective subsidy s* — depends on two poorly-observed parameters: "
    "the pass-through rate θ and the price sensitivity β_p. The table below shows how s* varies "
    "across a plausible range of these parameters for a representative store."
)
add_para(doc, "Illustrative sensitivity: s* required to achieve ΔCS ≥ $50,000/year at Store 1 (rent subsidy instrument).",
         italic=True)

sens_tbl = doc.add_table(rows=1, cols=5)
sens_tbl.style = "Table Grid"
sh = ["β_p scale \\ θ", "θ = 0.40", "θ = 0.55", "θ = 0.65 (base)", "θ = 0.80"]
for i, h in enumerate(sh):
    c = sens_tbl.rows[0].cells[i]
    c.text = h
    c.paragraphs[0].runs[0].bold = True
    c.paragraphs[0].runs[0].font.size = Pt(9)
    set_cell_bg(c, "1F4E79")
    c.paragraphs[0].runs[0].font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)

sens_data = [
    ["β_p × 0.8 (less sensitive)", "$3.2M", "$2.3M", "$1.9M", "$1.6M"],
    ["β_p × 1.0 (base)",           "$2.3M", "$1.7M", "$1.4M", "$1.1M"],
    ["β_p × 1.2 (more sensitive)", "$1.9M", "$1.4M", "$1.2M", "$0.9M"],
]
for d in sens_data:
    row = sens_tbl.add_row().cells
    for i, val in enumerate(d):
        row[i].text = val
        row[i].paragraphs[0].runs[0].font.size = Pt(9)
        if i == 3:
            set_cell_bg(row[i], "FFF9C4")
doc.add_paragraph()

add_para(doc,
    "Key insight: when the pass-through rate doubles (from 0.40 to 0.80), the required subsidy halves. "
    "Getting a good empirical estimate of θ is therefore the highest-priority calibration task. "
    "Run the model first at θ = 0.65 (literature midpoint) and present results with the full range as a band."
)

doc.add_page_break()

# ══════════════════════════════════════════════════════════════════════════════
# APPENDIX C: MODEL VALIDATION CHECKLIST
# ══════════════════════════════════════════════════════════════════════════════
add_heading(doc, "Appendix C: Model Validation Checklist", 1)
add_para(doc,
    "Run these checks after calibration and before interpreting results. "
    "A failure indicates miscalibration — not a bug in the code."
)

checks = [
    ("Demand-side", "Market shares sum to 1", "Σ_j S_j = 1.0 (±0.001)", "Verify: assert abs(S_j.sum() - 1) < 1e-3"),
    ("Demand-side", "All choice probabilities in (0,1)", "0 < s_ij < 1 for all i, j", "Check: assert (S > 0).all() and (S < 1).all()"),
    ("Demand-side", "Predicted store volumes near observed", "Q_j · p_j ≈ Revenue_j (ReferenceUSA) within 20%", "Compare: predicted vs. observed revenue by store"),
    ("Demand-side", "Own-price elasticities in expected range", "ε_jj ∈ [−2, −5] for grocery", "Print elasticity matrix; flag outliers"),
    ("Demand-side", "Welfare formula sign", "ΔCS > 0 when Δp_j < 0 (price falls → welfare rises)", "Unit test: compute_DCS(s=100k, ...) > 0"),
    ("Supply-side", "Markup calibration", "p_j ≈ (1 + μ_j) · VC_j within 5%", "Compare implied vs. observed price levels"),
    ("Supply-side", "Store profitability at baseline", "π_j > 0 for all incumbent stores pre-subsidy", "assert (pi_pre > 0).all()"),
    ("Pass-through", "θ produces realistic price reductions", "1% subsidy/revenue → 0.5%–0.8% price reduction", "Check Δp_j / p_j for s = 1% of Revenue_j"),
    ("Optimization", "Optimal solution feasible", "Σ s_j ≤ B and all eligibility constraints satisfied", "Verify after Gurobi solve: check constraint violations"),
    ("Optimization", "Welfare strictly positive at optimum", "ΔCS* > ΔCS_min", "Assert at end of solve"),
]

check_tbl = doc.add_table(rows=1, cols=4)
check_tbl.style = "Table Grid"
ch_hdrs = ["Category", "Check", "Criterion", "How to Verify"]
for i, h in enumerate(ch_hdrs):
    c = check_tbl.rows[0].cells[i]
    c.text = h
    c.paragraphs[0].runs[0].bold = True
    c.paragraphs[0].runs[0].font.size = Pt(9)
    set_cell_bg(c, "1F4E79")
    c.paragraphs[0].runs[0].font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)

for idx, row_data in enumerate(checks):
    row = check_tbl.add_row().cells
    bg = "EBF3FA" if idx % 2 == 0 else "FFFFFF"
    for i, val in enumerate(row_data):
        row[i].text = val
        row[i].paragraphs[0].runs[0].font.size = Pt(9)
        set_cell_bg(row[i], bg)
doc.add_paragraph()

doc.add_page_break()

# ══════════════════════════════════════════════════════════════════════════════
# APPENDIX D: ASSUMPTIONS AND LIMITATIONS
# ══════════════════════════════════════════════════════════════════════════════
add_heading(doc, "Appendix D: Assumptions, Limitations, and Caveats", 1)
add_para(doc,
    "Every model rests on assumptions. The table below lists each assumption, the condition "
    "required for it to hold, and the consequence if it is violated. "
    "This section should be included in any policy brief or report."
)

assump_tbl = doc.add_table(rows=1, cols=4)
assump_tbl.style = "Table Grid"
a_hdrs = ["Assumption", "Required for it to hold", "If violated…", "Sensitivity / Extension"]
for i, h in enumerate(a_hdrs):
    c = assump_tbl.rows[0].cells[i]
    c.text = h
    c.paragraphs[0].runs[0].bold = True
    c.paragraphs[0].runs[0].font.size = Pt(9)
    set_cell_bg(c, "1F4E79")
    c.paragraphs[0].runs[0].font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)

assumptions = [
    ("Static single-period model", "Short-run analysis; no store entry or exit induced by subsidy", "Underestimates long-run access benefits if subsidy prevents closure; overestimates if it attracts new entrants", "Extend to dynamic model if multi-year program"),
    ("Fixed store attributes (q_j, v_j)", "Subsidy does not enable store to improve quality or expand variety", "Welfare gains are underestimated if store reinvests subsidy savings in upgrades", "Sensitivity run: shift q_j or v_j by 0.5–1 unit"),
    ("No rival store response", "Rivals do not react to competitor's price cut (no Nash equilibrium)", "If rivals cut prices in response, consumer welfare gains are larger; rival losses smaller", "Optional extension: Bertrand best-response loop"),
    ("IIA (standard MNL)", "Consumer substitution patterns are proportional across all stores", "Underestimates share capture from similar stores (e.g., two discount stores)", "Upgrade to nested logit (store types as nests) or mixed logit"),
    ("Pass-through rate θ is constant", "Store's pricing behavior is linear in subsidy amount", "If store pockets more at large subsidies (θ decreases with s), cost-effectiveness overstated at high s", "Model θ as decreasing function of s; run sensitivity"),
    ("No online grocery / out-of-area shopping", "Consumers in study area shop exclusively at local stores in choice set", "If consumers can easily shop online or travel far, market shares and welfare gains are overstated", "Add 'outside option' store j=0 with fixed utility"),
    ("Income is fixed; no labor market effects", "Subsidy does not affect household income or employment", "If store hires more workers from local community, secondary welfare gains are missed", "Beyond model scope; note as limitation"),
    ("Logit errors are i.i.d. Gumbel", "True unobserved tastes are uncorrelated across stores and consumers", "If consumers have strong brand loyalty, logit underestimates stickiness", "Mixed logit partially addresses this via random coefficients"),
]
for idx, row_data in enumerate(assumptions):
    row = assump_tbl.add_row().cells
    bg = "EBF3FA" if idx % 2 == 0 else "FFFFFF"
    for i, val in enumerate(row_data):
        row[i].text = val
        row[i].paragraphs[0].runs[0].font.size = Pt(9)
        set_cell_bg(row[i], bg)
doc.add_paragraph()

doc.add_page_break()

# ══════════════════════════════════════════════════════════════════════════════
# APPENDIX E: OUTPUT INTERPRETATION GUIDE
# ══════════════════════════════════════════════════════════════════════════════
add_heading(doc, "Appendix E: Output Interpretation and Plain-Language Template", 1)

add_heading(doc, "E.1  Key Outputs by Goal", 2)
out_tbl = doc.add_table(rows=1, cols=4)
out_tbl.style = "Table Grid"
o_hdrs = ["Goal", "Primary Output", "Chart / Table", "How to Read It"]
for i, h in enumerate(o_hdrs):
    c = out_tbl.rows[0].cells[i]
    c.text = h
    c.paragraphs[0].runs[0].bold = True
    c.paragraphs[0].runs[0].font.size = Pt(9)
    set_cell_bg(c, "1F4E79")
    c.paragraphs[0].runs[0].font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)

outputs = [
    ("Goal 1", "Cost-effectiveness frontier: ΔCS(s)", "Line chart: x = annual subsidy $, y = ΔCS $", "Find the 'elbow' where marginal welfare gain per additional dollar drops sharply — that is s*"),
    ("Goal 1", "Instrument comparison table", "Bar chart or table: ΔCS per dollar for tax break, rent subsidy, direct operation", "The instrument with highest ΔCS/dollar is most efficient; direct operation is strongest but most costly to administer"),
    ("Goal 2", "Store ranking by welfare return", "Table: stores sorted by ΔCS_j(B), with eligibility flags", "Top-ranked eligible store = recommended selection under K=1"),
    ("Goal 2", "Distributional breakdown of ΔCS", "Stacked bar: ΔCS by income quintile per store", "Prefer stores where a larger share of ΔCS goes to lowest-income quintile"),
    ("Goal 3", "Rival impact table", "Table: ΔQ_k, Δπ_k for each rival store k", "Flag stores with Δπ_k < 0 and |Δπ_k| > 10% of baseline π_k as 'at risk'"),
    ("Goal 3", "Net social welfare", "Single number: ΔW_total = ΔCS + Σ Δπ_k", "If ΔW_total > 0, subsidy improves total welfare. If ΔW_total < 0, consumer gains are outweighed by industry losses"),
    ("Goal 3", "Geographic spillover map", "Choropleth: color stores by ΔQ_k intensity", "Stores closest to j* and serving overlapping census tracts will show largest spillovers"),
]
for idx, row_data in enumerate(outputs):
    row = out_tbl.add_row().cells
    bg = "EBF3FA" if idx % 2 == 0 else "FFFFFF"
    for i, val in enumerate(row_data):
        row[i].text = val
        row[i].paragraphs[0].runs[0].font.size = Pt(9)
        set_cell_bg(row[i], bg)
doc.add_paragraph()

add_heading(doc, "E.2  Plain-Language Summary Template", 2)
add_para(doc,
    "Use this template when presenting results to non-technical audiences (NYCEDC staff, elected officials, community boards):"
)
add_callout(doc, "Summary Template:",
    '"Subsidizing [STORE NAME], a [store type] located at [address] in [neighborhood], '
    'with a [rent subsidy / tax break / direct operation] of $[AMOUNT] per year is projected to '
    'reduce consumer prices by approximately [X]%, generating an estimated aggregate welfare gain of '
    '$[ΔCS] per year for the [N] households in the [neighborhood] area. '
    'Low-income households (earning below $35,000/year) capture approximately [Y]% of this benefit. '
    'Under this scenario, nearby stores including [Store A] and [Store B] are estimated to see '
    'foot traffic reductions of [Z1]% and [Z2]% respectively. '
    'The net change in total social welfare — consumer gains plus changes in store profits — '
    'is estimated at $[ΔW_total], indicating that the program [improves / reduces] overall '
    'economic efficiency in the study area."',
    color_hex="F3E5F5"
)

doc.add_paragraph()
add_heading(doc, "E.3  Decision Flowchart for Instrument Selection", 2)
add_para(doc, "Use the following logic to select the appropriate instrument before running the model:")

flow_steps = [
    "Is the store's lease structure compatible with a direct rent subsidy?\n"
    "   YES → Use Instrument 2 (Rent Subsidy). Data needed: NYC ACRIS lease amount.\n"
    "   NO  → Continue to next question.",
    "Does the store own its property and pay significant property tax?\n"
    "   YES → Use Instrument 1 (Tax Break). Data needed: NYC NYCDB tax bill.\n"
    "   NO  → Continue to next question.",
    "Is the city willing and legally able to operate or co-operate the store directly?\n"
    "   YES → Use Instrument 3 (Direct Operation). Data needed: VC_j, FC_j, unit volume.\n"
    "   NO  → Reconsider store eligibility or design a hybrid instrument.",
]
for i, step in enumerate(flow_steps, 1):
    p = doc.add_paragraph()
    p.paragraph_format.left_indent = Inches(0.3)
    p.paragraph_format.space_after = Pt(6)
    r = p.add_run(f"{i}.  {step}")
    r.font.size = Pt(10)

# ── Save ──────────────────────────────────────────────────────────────────────
doc.save(OUT_PATH)
print(f"Saved: {OUT_PATH}")
