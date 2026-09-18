"""
NYC_Grocery_Subsidy_Model_Specification_v2.docx
Study area: Bronx Community District 2 — Hunts Point / Longwood
"""

import io, os, sys, tempfile
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from docx import Document
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

OUT_PATH = r"C:\Users\samia\Code_Projects\grocery_subsidy_analysis\NYC_Grocery_Subsidy_Model_Specification_v2.docx"

# ─────────────────────────────────────────────────────────────────────────────
# EQUATION RENDERING  (matplotlib mathtext → PNG → BytesIO)
# ─────────────────────────────────────────────────────────────────────────────
def sanitize_latex(s):
    """Remove/replace LaTeX commands not supported by matplotlib mathtext."""
    import re
    s = s.replace(r"\displaystyle", "")
    s = s.replace(r"\textstyle", "")
    s = s.replace(r"\scriptstyle", "")
    s = s.replace(r"\mid", r"\,|\,")
    s = s.replace(r"\Longrightarrow", r"\Rightarrow")
    s = s.replace(r"\;", r"\,")
    # \text{...} is supported in matplotlib; leave it
    return s

def render_equation(latex_str, fontsize=12, fig_width=6.4, fig_height=0.65):
    latex_str = sanitize_latex(latex_str)
    fig = plt.figure(figsize=(fig_width, fig_height))
    fig.patch.set_facecolor("white")
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_axis_off()
    ax.set_xlim(0, 1); ax.set_ylim(0, 1)
    try:
        ax.text(0.02, 0.5, f"${latex_str}$",
                fontsize=fontsize, va="center", ha="left",
                transform=ax.transAxes, color="black")
        # test render by drawing
        fig.canvas.draw()
    except Exception as e:
        plt.close(fig)
        # fallback: plain monospace text
        fig = plt.figure(figsize=(fig_width, fig_height))
        fig.patch.set_facecolor("white")
        ax = fig.add_axes([0, 0, 1, 1])
        ax.set_axis_off()
        plain = latex_str.replace("$", "").replace("\\", "").replace("{", "").replace("}", "")
        ax.text(0.02, 0.5, plain,
                fontsize=fontsize - 1, va="center", ha="left",
                transform=ax.transAxes, color="black", family="monospace")
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150, bbox_inches="tight",
                facecolor="white", edgecolor="none", pad_inches=0.06)
    plt.close(fig)
    buf.seek(0)
    return buf

def add_latex_eq(doc, latex_str, fontsize=12, fig_width=6.4, fig_height=0.65, label=None):
    if label:
        lp = doc.add_paragraph()
        lp.paragraph_format.space_after = Pt(1)
        lr = lp.add_run(label)
        lr.italic = True; lr.font.size = Pt(9)
        lr.font.color.rgb = RGBColor(0x55, 0x55, 0x55)
    buf = render_equation(latex_str, fontsize, fig_width, fig_height)
    p = doc.add_paragraph()
    p.paragraph_format.left_indent = Inches(0.25)
    p.paragraph_format.space_after = Pt(6)
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    run = p.add_run()
    run.add_picture(buf, width=Inches(min(fig_width * 0.85, 5.8)))

# ─────────────────────────────────────────────────────────────────────────────
# DOC HELPERS
# ─────────────────────────────────────────────────────────────────────────────
def set_cell_bg(cell, hex_color):
    tc = cell._tc
    tcPr = tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear"); shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), hex_color)
    tcPr.append(shd)

def add_heading(doc, text, level):
    h = doc.add_heading(text, level=level)
    h.paragraph_format.space_before = Pt(14 if level <= 2 else 9)
    h.paragraph_format.space_after  = Pt(4)
    return h

def add_para(doc, text, bold=False, italic=False, size=11, indent=0, space_after=6):
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(space_after)
    if indent: p.paragraph_format.left_indent = Inches(indent)
    run = p.add_run(text)
    run.bold = bold; run.italic = italic; run.font.size = Pt(size)
    return p

def add_callout(doc, title, text, bg_hex="D9EDF7", title_color=None):
    tbl = doc.add_table(rows=1, cols=1)
    tbl.style = "Table Grid"
    cell = tbl.cell(0, 0)
    set_cell_bg(cell, bg_hex)
    p = cell.paragraphs[0]
    p.paragraph_format.space_after = Pt(0)
    r1 = p.add_run(title + "  ")
    r1.bold = True; r1.font.size = Pt(9.5)
    if title_color:
        r1.font.color.rgb = RGBColor(*title_color)
    r2 = p.add_run(text)
    r2.font.size = Pt(9.5)
    doc.add_paragraph().paragraph_format.space_after = Pt(4)

def add_plain_english(doc, text):
    """Green callout — plain-language explanation for intro-micro audience."""
    add_callout(doc, "In plain English:", text, bg_hex="E8F5E9",
                title_color=(0x1B, 0x5E, 0x20))

def add_answer_callout(doc, q_label, text):
    """Blue callout answering a conceptual question."""
    add_callout(doc, f"Conceptual note — {q_label}:", text, bg_hex="E3F2FD",
                title_color=(0x0D, 0x47, 0xA1))

def add_simplification_note(doc, text):
    """Orange callout for simplification options."""
    add_callout(doc, "Simplification option:", text, bg_hex="FFF8E1",
                title_color=(0xE6, 0x5C, 0x00))

def add_equation_block(doc, label, equation, note=None):
    lbl = doc.add_paragraph()
    lbl.paragraph_format.space_after = Pt(1)
    lbl.paragraph_format.space_before = Pt(4)
    r = lbl.add_run(label); r.bold = True; r.font.size = Pt(10)
    r.font.color.rgb = RGBColor(0x33, 0x33, 0x33)
    eq_p = doc.add_paragraph()
    eq_p.paragraph_format.left_indent  = Inches(0.2)
    eq_p.paragraph_format.right_indent = Inches(0.2)
    eq_p.paragraph_format.space_after  = Pt(2)
    er = eq_p.add_run(equation)
    er.font.name = "Courier New"; er.font.size = Pt(9.5)
    pPr = eq_p._p.get_or_add_pPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear"); shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), "F4F4F4"); pPr.append(shd)
    if note:
        n = doc.add_paragraph()
        n.paragraph_format.left_indent = Inches(0.2)
        n.paragraph_format.space_after = Pt(8)
        nr = n.add_run(note); nr.italic = True
        nr.font.size = Pt(9); nr.font.color.rgb = RGBColor(0x55, 0x55, 0x55)

def add_term_table(doc, rows, extra_note=None):
    headers = ["Term", "Symbol", "Type", "Description", "Data Source / Estimation"]
    col_w   = [1.0, 0.85, 0.85, 2.2, 2.35]
    tbl = doc.add_table(rows=1, cols=5)
    tbl.style = "Table Grid"
    hdr = tbl.rows[0].cells
    for i, (h, w) in enumerate(zip(headers, col_w)):
        hdr[i].width = Inches(w); hdr[i].text = h
        hdr[i].paragraphs[0].runs[0].bold = True
        hdr[i].paragraphs[0].runs[0].font.size = Pt(9)
        set_cell_bg(hdr[i], "1F4E79")
        hdr[i].paragraphs[0].runs[0].font.color.rgb = RGBColor(255,255,255)
    for idx, row_data in enumerate(rows):
        row = tbl.add_row().cells
        bg = "EBF3FA" if idx % 2 == 0 else "FFFFFF"
        for i, (val, w) in enumerate(zip(row_data, col_w)):
            row[i].width = Inches(w)
            row[i].text = val
            row[i].paragraphs[0].runs[0].font.size = Pt(9)
            set_cell_bg(row[i], bg)
            if i == 2:
                t = val.lower()
                if "parameter" in t:
                    row[i].paragraphs[0].runs[0].font.color.rgb = RGBColor(0x17,0x6B,0x24)
                    row[i].paragraphs[0].runs[0].bold = True
                elif "dataset" in t:
                    row[i].paragraphs[0].runs[0].font.color.rgb = RGBColor(0x7B,0x36,0x00)
                    row[i].paragraphs[0].runs[0].bold = True
                elif "decision" in t:
                    row[i].paragraphs[0].runs[0].font.color.rgb = RGBColor(0x50,0x00,0x7B)
                    row[i].paragraphs[0].runs[0].bold = True
    if extra_note:
        n = doc.add_paragraph()
        n.paragraph_format.space_after = Pt(4)
        nr = n.add_run(extra_note); nr.italic = True; nr.font.size = Pt(9)
    doc.add_paragraph()

def add_source_box(doc, sources):
    p = doc.add_paragraph()
    r = p.add_run("Literature Sources")
    r.bold = True; r.font.size = Pt(10)
    r.font.color.rgb = RGBColor(0x1F, 0x4E, 0x79)
    p.paragraph_format.space_after = Pt(3)
    for src in sources:
        sp = doc.add_paragraph(style="List Bullet")
        sp.paragraph_format.left_indent = Inches(0.25)
        sp.paragraph_format.space_after = Pt(3)
        run = sp.add_run(src["citation"]); run.font.size = Pt(9)
        for key in ("doi", "url"):
            if key in src:
                sp.add_run("  ")
                lr = sp.add_run(src[key])
                lr.font.size = Pt(9)
                lr.font.color.rgb = RGBColor(0x00, 0x56, 0xB3)
                lr.italic = True
    doc.add_paragraph()

def add_code_block(doc, code_text, caption=None):
    if caption:
        cp = doc.add_paragraph()
        cp.paragraph_format.space_after = Pt(2)
        cr = cp.add_run(caption); cr.bold = True; cr.font.size = Pt(10)
    for line in code_text.split("\n"):
        lp = doc.add_paragraph()
        lp.paragraph_format.space_before = Pt(0)
        lp.paragraph_format.space_after  = Pt(0)
        lp.paragraph_format.left_indent  = Inches(0.2)
        lr = lp.add_run(line if line else " ")
        lr.font.name = "Courier New"; lr.font.size = Pt(8.5)
        pPr = lp._p.get_or_add_pPr()
        shd = OxmlElement("w:shd")
        shd.set(qn("w:val"), "clear"); shd.set(qn("w:color"), "auto")
        shd.set(qn("w:fill"), "F7F7F7"); pPr.append(shd)
    doc.add_paragraph()

def add_step(doc, n, title, detail):
    p = doc.add_paragraph()
    p.paragraph_format.left_indent = Inches(0.2)
    p.paragraph_format.space_after = Pt(5)
    r1 = p.add_run(f"Step {n}: {title}\n")
    r1.bold = True; r1.font.size = Pt(10)
    r2 = p.add_run(detail); r2.font.size = Pt(10)

# ═════════════════════════════════════════════════════════════════════════════
# BUILD DOCUMENT
# ═════════════════════════════════════════════════════════════════════════════
doc = Document()
for sec in doc.sections:
    sec.top_margin = sec.bottom_margin = Inches(1)
    sec.left_margin = sec.right_margin = Inches(1.1)
doc.styles["Normal"].font.name = "Calibri"
doc.styles["Normal"].font.size = Pt(11)

# ── TITLE ─────────────────────────────────────────────────────────────────────
doc.add_paragraph()
tp = doc.add_paragraph()
tp.alignment = WD_ALIGN_PARAGRAPH.CENTER
tr = tp.add_run("NYC Municipal Grocery Subsidy\nModel Specification and Implementation Guide")
tr.bold = True; tr.font.size = Pt(20)
tr.font.color.rgb = RGBColor(0x1F, 0x4E, 0x79)

sp = doc.add_paragraph(); sp.alignment = WD_ALIGN_PARAGRAPH.CENTER
sr = sp.add_run(
    "Optimization Framework for Allocating a City Subsidy Across Candidate\n"
    "Retail Food Stores in Bronx Community District 2 (Hunts Point / Longwood)\n\n"
    "Decision-Maker: NYCEDC / Mayor's Office\n"
    "Study Area: Bronx CD2 — Hunts Point and Longwood neighborhoods\n"
    "Model Type: Static Single-Period  |  Choice Model: Multinomial Logit\n"
    "Instruments: Tax Break  ·  Rent Subsidy  (unified as cost subsidy s)"
)
sr.font.size = Pt(11); sr.font.color.rgb = RGBColor(0x33, 0x33, 0x33)
sp.paragraph_format.space_before = Pt(12)

doc.add_paragraph()
add_callout(doc,
    "Causal chain (read left to right):",
    "City pays subsidy s  →  Store's fixed cost falls by s  →  Store reduces price by "
    "Δp_j = θ · s / Q_j  →  Utility of shopping at that store rises (V_ij increases)  →  "
    "More consumers choose that store (market share shifts)  →  "
    "Consumer welfare improves (ΔCS = measured dollar value of that improvement)",
    bg_hex="EBF3FA"
)

add_callout(doc,
    "Study area note — Bronx CD2 (Hunts Point / Longwood):",
    "Hunts Point and Longwood are among the highest food-insecurity neighborhoods in NYC. "
    "Median household income is approximately $22,000–$28,000 (ACS 2022). "
    "The area is predominantly Puerto Rican and Dominican, with very few full-service supermarkets "
    "relative to fast food outlets and bodegas. "
    "Census tracts in Bronx CD2 fall in Bronx County (FIPS state=36, county=005). "
    "The ACS and SNAP data are filtered to these tracts using a spatial join with the "
    "NYC Community Districts shapefile (nyc.gov/planning).",
    bg_hex="FFF9C4"
)

doc.add_page_break()

# ── TOC ───────────────────────────────────────────────────────────────────────
add_heading(doc, "Table of Contents", 1)
for item in [
    "Part 1: Model Equations",
    "    1.1  Consumer Demand (Multinomial Logit)",
    "    1.2  Store Cost and Pricing",
    "    1.3  Subsidy Pass-Through (Unified: Tax Break or Rent Subsidy)",
    "    1.4  Optimization Problems (Goal 1 and Goal 2)",
    "Simplification Options for First Implementation",
    "Part 2: Data Loading, Model Setup, and Solution",
    "    2.0  Phase 0 — Data Pipeline (Bronx CD2)",
    "    2.1  Goal 1 — Single-Store Subsidy Effect",
    "    2.2  Goal 2 — Optimal Store Selection (Gurobi / scipy)",
    "Appendix A: Worked Numerical Example",
    "Appendix B: Sensitivity Analysis Framework",
    "Appendix C: Model Validation Checklist",
    "Appendix D: Assumptions, Limitations, and Caveats",
    "Appendix E: Output Interpretation and Plain-Language Template",
    "Appendix F: Complete Data and Parameter Reference Table",
]:
    p = doc.add_paragraph(item)
    p.paragraph_format.space_after = Pt(2)
    if not item.startswith("    "):
        p.runs[0].bold = True
doc.add_page_break()

# ═════════════════════════════════════════════════════════════════════════════
# PART 1
# ═════════════════════════════════════════════════════════════════════════════
add_heading(doc, "Part 1: Model Equations", 1)
add_para(doc,
    "This section documents every equation used in the model. For each equation you will find: "
    "(1) a rendered LaTeX-style equation, (2) a plain-English explanation of what the equation is capturing, "
    "(3) a term definition table classifying each symbol as a parameter, dataset, or decision variable, "
    "and (4) literature citations. Green boxes give plain-English explanations. Blue boxes answer "
    "conceptual questions. Orange boxes describe simplifications you can make.")

# ── 1.1 ──────────────────────────────────────────────────────────────────────
add_heading(doc, "1.1  Consumer Demand (Multinomial Logit)", 2)
add_para(doc,
    "The multinomial logit (MNL) model describes how consumers choose which grocery store to visit. "
    "Each consumer assigns a 'satisfaction score' (utility) to each store, then probabilistically "
    "chooses the store with the highest score. The probability of choosing store j increases as "
    "its price falls, its quality rises, or its distance shrinks.")

# 1.1.1
add_heading(doc, "1.1.1  Indirect Utility Function", 3)
add_plain_english(doc,
    "Think of U_ij as a 'satisfaction score' that consumer i gets from shopping at store j. "
    "It goes up when the store has better quality (q_j) or variety (v_j), and down when the "
    "price (p_j) or distance (d_ij) is higher. The ε_ij term captures everything we can't observe — "
    "personal loyalty, a one-time convenience — modeled as random noise.")

add_latex_eq(doc,
    r"U_{ij} = \beta_{q,i} \cdot q_j + \beta_{v,i} \cdot v_j "
    r"- \beta_{p,i} \cdot p_j - \beta_{d,i} \cdot d_{ij} + \varepsilon_{ij}",
    fig_height=0.7, label="Equation 1.1.1a — Utility of consumer i at store j")
add_latex_eq(doc,
    r"\varepsilon_{ij} \sim \text{Gumbel}(0,\,1) \quad \text{(i.i.d. random noise)}",
    fig_height=0.6, label="Equation 1.1.1b — Distributional assumption on error")

add_equation_block(doc, "Notation (ASCII reference)",
    "U_ij = β_q_i·q_j  +  β_v_i·v_j  −  β_p_i·p_j  −  β_d_i·d_ij  +  ε_ij\n"
    "ε_ij ~ Gumbel(0,1)  [i.i.d. extreme value — see Q4 note below]")

add_answer_callout(doc, "Q2 — How are consumers represented in the data?",
    "You do NOT need a dataset of individual people. Each census tract is treated as "
    "one 'consumer type' (i). A tract has many households, but they all share the same "
    "tract centroid (→ distance to stores), median income (→ price sensitivity β_p_i), "
    "and household count (→ how much weight that tract gets in total welfare). "
    "With ~15–20 tracts in Bronx CD2, N = 15–20. This is very manageable. "
    "ACS Table B19013 gives median income per tract; ACS B11001 gives household count.")

add_term_table(doc, [
    ("Total utility of consumer (tract) i at store j", "U_ij", "Derived", "Satisfaction score; not directly observed; computed from equation", "Computed from β_i and store attributes"),
    ("Quality index of store j", "q_j", "Dataset", "Ordinal: supermarket=3, discount=2, bodega=1", "NYC DOHMH food retail classification; store type from SNAP locator"),
    ("Variety index of store j", "v_j", "Dataset", "Proxy: same ordinal as quality, or IBISWorld avg SKU by store type", "NYC DOHMH; IBISWorld Supermarkets report (normalized 0–1)"),
    ("Price level at store j (see Q1 note)", "p_j", "Dataset (baseline) / Derived (post-subsidy)", "Single representative price per store — see Section 1.2.5 and Q1 note", "ReferenceUSA revenue ÷ estimated volume; BLS CPI food index"),
    ("Travel time/distance from tract i to store j", "d_ij", "Dataset", "Walking or transit minutes from tract centroid to store address", "Census TIGER tract centroids + OSMnx walking network (Bronx)"),
    ("Price sensitivity of consumer i", "β_p_i", "Parameter", "Higher for lower-income tracts; scaled from literature by ACS income", "Allcott et al. (2019) Table IV as base; scaled by tract income (see Q3 note)"),
    ("Quality preference weight for consumer i", "β_q_i", "Parameter", "Fixed at 1.0 for simplified model (see simplification table)", "Handbury (2021); can fix = 1 initially"),
    ("Variety preference weight for consumer i", "β_v_i", "Parameter", "Fixed at 1.0 for simplified model", "Handbury (2021); can fix = 1 initially"),
    ("Distance sensitivity for consumer i", "β_d_i", "Parameter", "Higher for households without vehicle access (high in Hunts Point)", "Ben-Akiva & Lerman (1985) Table 5.3; scaled by ACS vehicle access B08201"),
    ("Unobserved idiosyncratic preference", "ε_ij", "Distributional assumption", "Random noise; Gumbel distribution gives closed-form logit formula", "Statistical assumption — McFadden (1974); not observed"),
])
add_source_box(doc, [
    {"citation": "McFadden, D. (1974). Conditional logit analysis of qualitative choice behavior. In Zarembka (Ed.), Frontiers in Econometrics, pp. 105–142. Academic Press.",
     "url": "https://escholarship.org/uc/item/61s3q2xr"},
    {"citation": "Train, K.E. (2009). Discrete Choice Methods with Simulation (2nd ed.). Cambridge University Press. [Ch. 2, pp. 11–33 for MNL]",
     "url": "https://eml.berkeley.edu/books/train1201.pdf"},
    {"citation": "Allcott, H., Diamond, R., Dubé, J.P., Handbury, J., Rahkovsky, I., & Schnell, M. (2019). Food deserts and the causes of nutritional inequality. Quarterly Journal of Economics, 134(4), 1793–1844.",
     "doi": "DOI: 10.1093/qje/qjz015", "url": "https://academic.oup.com/qje/article-abstract/134/4/1793/5492274"},
])

# 1.1.2
add_heading(doc, "1.1.2  Preference Heterogeneity (Random Coefficients)", 3)
add_plain_english(doc,
    "Different people care about price, quality, variety, and distance differently. "
    "A low-income household cares a lot about price; someone without a car cares a lot about distance. "
    "The MVN distribution is just a statistical way of saying: each consumer's preferences are "
    "a random draw from a population distribution that we characterize by its average (μ_β) "
    "and how spread out it is (Σ_β). "
    "For the simplified model, you can skip the random-draws step entirely and just assign "
    "fixed β values to each income group (see simplification table).")

add_answer_callout(doc, "Q4 — What is MVN and why is the mean a vector?",
    "MVN stands for Multivariate Normal Distribution — the multi-dimensional version of a "
    "normal bell curve. It is a vector because there are 4 preference weights "
    "(for quality, variety, price, and distance), so the 'average consumer' is described by "
    "4 numbers, not 1. The covariance matrix Σ_β captures whether these preferences move together — "
    "for example, price-sensitive and distance-sensitive tend to go together (both reflect "
    "low-income / limited-mobility constraints). "
    "Source: Train (2009), Chapter 6 — Mixed Logit, pp. 135–177.")

add_latex_eq(doc,
    r"\beta_i = (\beta_{q,i},\,\beta_{v,i},\,\beta_{p,i},\,\beta_{d,i}) "
    r"\sim \text{MVN}(\mu_\beta,\, \Sigma_\beta)",
    fig_height=0.65, label="Equation 1.1.2 — Consumer preference vector drawn from population distribution")
add_equation_block(doc, "Notation (ASCII reference)",
    "β_i = (β_q_i, β_v_i, β_p_i, β_d_i)  ~  MVN(μ_β, Σ_β)\n"
    "μ_β = (μ_q, μ_v, μ_p, μ_d)  = mean preference vector (4 numbers)\n"
    "Σ_β = 4×4 covariance matrix  = how correlated the preferences are")

add_answer_callout(doc, "Q3 — How to calibrate μ_β from ACS and literature?",
    "Step-by-step calibration:\n"
    "1. μ_p (price sensitivity mean): Use Allcott et al. (2019) Table IV, which reports "
    "price sensitivity by income quintile for US grocery shoppers. Compute a weighted "
    "average using ACS income distribution in Bronx CD2.\n"
    "2. μ_d (distance sensitivity mean): Use Davis (2006) grocery distance coefficient, "
    "or Ben-Akiva & Lerman (1985) Table 5.3. For Hunts Point, scale upward because "
    "ACS Table B08201 shows very low vehicle ownership (<15% of households).\n"
    "3. μ_q, μ_v (quality and variety): Use Handbury (2021). For a simplified model, "
    "set both to 1.0 as equal-weight scaling factors — no calibration needed.\n"
    "4. Σ_β: Set off-diagonal entries to zero (simpler) or use literature covariances. "
    "Diagonal entries (variances) reflect how spread out preferences are in the population.")

add_simplification_note(doc,
    "Skip the full MVN distribution entirely. Instead, assign fixed β values to 3 income groups: "
    "Low (<$25K/yr): β_p = 0.55, β_d = 0.40. Mid ($25K–$50K): β_p = 0.30, β_d = 0.25. "
    "High (>$50K): β_p = 0.15, β_d = 0.15. ACS gives household counts per group per tract. "
    "This eliminates Monte Carlo simulation entirely and makes the model run in seconds.")

add_term_table(doc, [
    ("Preference weight vector for consumer i", "β_i", "Parameter", "4-dim vector: (β_q, β_v, β_p, β_d); calibrated then varied in sensitivity", "Literature starting point + ACS income distribution calibration"),
    ("Mean preference vector (population average)", "μ_β", "Parameter", "4 numbers: average quality, variety, price, distance weights across all consumers", "Allcott et al. (2019); Handbury (2021); Davis (2006); Ben-Akiva & Lerman (1985)"),
    ("Preference covariance matrix", "Σ_β", "Parameter", "4×4 matrix capturing correlated preferences. Set diagonal only for simplicity.", "Literature; set to zero off-diagonals for simplified model"),
])
add_source_box(doc, [
    {"citation": "Train, K.E. (2009). Discrete Choice Methods with Simulation — Chapter 6: Mixed Logit, pp. 135–177.",
     "url": "https://eml.berkeley.edu/books/train1201.pdf"},
    {"citation": "Handbury, J. (2021). Are poor cities cheap for everyone? Non-homotheticity and the cost of living across U.S. cities. Econometrica, 89(6), 2679–2715.",
     "doi": "DOI: 10.3982/ECTA11738", "url": "https://onlinelibrary.wiley.com/doi/abs/10.3982/ECTA11738"},
])

# 1.1.3
add_heading(doc, "1.1.3  Individual Choice Probability", 3)
add_plain_english(doc,
    "This is the core logit formula. The probability that consumer i chooses store j equals "
    "the 'attractiveness' of store j (exp(V_ij)) divided by the total attractiveness of ALL stores. "
    "If store j lowers its price, exp(V_ij) rises, so its share of the denominator rises — "
    "more consumers choose it. V_ij is the systematic (predictable) part of utility — "
    "the same as U_ij but without the random ε_ij term.")

add_latex_eq(doc,
    r"s_{ij}\mid\beta_i \;=\; \frac{\exp(V_{ij})}{\displaystyle\sum_{k=1}^{J}\exp(V_{ik})}",
    fig_height=0.8, label="Equation 1.1.3a — Probability consumer i chooses store j")
add_latex_eq(doc,
    r"V_{ij} = \beta_{q,i}\cdot q_j + \beta_{v,i}\cdot v_j "
    r"- \beta_{p,i}\cdot p_j - \beta_{d,i}\cdot d_{ij}",
    fig_height=0.65, label="Equation 1.1.3b — Systematic utility V_ij (defined here; used in all subsequent equations)")
add_equation_block(doc, "Notation (ASCII reference)",
    "s_ij = exp(V_ij)  /  Σ_k exp(V_ik)     [V_ij defined above — used in 1.1.4, 1.1.5, and 1.3.3]",
    note="V_ij appears in all subsequent equations. It is always the systematic (no ε) part of utility as defined here.")

add_term_table(doc, [
    ("Choice probability: consumer i picks store j", "s_ij", "Derived", "Probability between 0 and 1; all J probabilities sum to 1 for each consumer", "Computed from V_ij values"),
    ("Systematic utility of store j for consumer i", "V_ij", "Derived — defined here, used throughout", "Deterministic part of utility; computed from β_i and store attributes q_j, v_j, p_j, d_ij", "Computed; referenced in 1.1.4, 1.1.5, 1.3.3"),
    ("Number of stores in the choice set", "J", "Dataset", "Candidate stores in Bronx CD2 (target 5–12 SNAP-authorized stores)", "USDA SNAP Retailer Locator + NYC DOHMH food retail data"),
    ("Index over all stores", "k", "Index", "Sums over all J stores in denominator", "—"),
])
add_source_box(doc, [
    {"citation": "McFadden, D. (1974). Conditional logit analysis. pp. 105–142.",
     "url": "https://escholarship.org/uc/item/61s3q2xr"},
    {"citation": "Ben-Akiva, M., & Lerman, S.R. (1985). Discrete Choice Analysis. MIT Press. ISBN: 9780262022170",
     "url": "Available online through CMU library"},
])

# 1.1.4
add_heading(doc, "1.1.4  Aggregate Market Share", 3)

add_answer_callout(doc, "Q6 — What is the 'simulation' in this section?",
    "When consumers have different β values (from MVN), we cannot compute the average market "
    "share analytically (the integral has no closed form). Instead, we use Monte Carlo simulation: "
    "(1) Draw R = 1,000 random preference vectors β^r from MVN(μ_β, Σ_β). "
    "(2) For each draw r, compute the logit choice probability s_ij(β^r) using equation 1.1.3. "
    "(3) Average across all R draws: S_j ≈ (1/R)·Σ_r s_ij(β^r). "
    "This average estimates 'what fraction of the population chooses store j, "
    "given the full distribution of preferences.' "
    "SIMPLIFIED MODEL: If you use 3 fixed income groups instead of MVN, "
    "you compute S_j as a household-count-weighted average of 3 group probabilities — "
    "no simulation needed.")

add_answer_callout(doc, "Q7 — How is β^r different from β_i?",
    "β^r is NOT a separate β for each real consumer. It is one sample ('draw') from the "
    "population distribution MVN(μ_β, Σ_β). Each draw r = a hypothetical consumer type with "
    "that particular combination of preferences (e.g., r=1: very price-sensitive, low distance "
    "sensitivity; r=500: moderate price sensitivity, high distance sensitivity). "
    "Together, the R draws approximate the full range of consumer types in Bronx CD2. "
    "Averaging s_ij(β^r) over R draws is equivalent to asking: 'Across all possible consumer "
    "types in this population, what is the average probability of choosing store j?'")

add_latex_eq(doc,
    r"S_j = \frac{1}{N}\sum_{i=1}^{N} s_{ij} "
    r"\;\approx\; \frac{1}{R}\sum_{r=1}^{R} s_{ij}(\beta^r), "
    r"\quad \beta^r \sim \text{MVN}(\mu_\beta, \Sigma_\beta)",
    fig_height=0.7, fig_width=7.0, label="Equation 1.1.4 — Aggregate market share of store j")
add_equation_block(doc, "Notation (ASCII reference)",
    "S_j = (1/N) · Σ_i s_ij           [exact, if β is fixed per income group — RECOMMENDED]\n"
    "S_j ≈ (1/R) · Σ_r s_ij(β^r)      [simulation approximation, if using full MVN]")

add_term_table(doc, [
    ("Aggregate market share of store j", "S_j", "Derived", "Fraction of consumers who choose store j; must sum to 1 across all stores", "Computed; cross-check: Σ_j S_j = 1"),
    ("Number of consumer groups (tracts or income groups)", "N", "Dataset", "Number of census tracts in Bronx CD2 (~15–20) OR number of income groups (3–5)", "ACS tract boundaries + NYC CD2 shapefile"),
    ("Number of simulation draws", "R", "Parameter", "R = 1,000 for stable results in mixed logit; R = 0 if using simplified income-group model", "Researcher choice; not needed for simplified model"),
    ("Draw r from preference distribution", "β^r", "Parameter (simulated)", "One sample of (β_q, β_v, β_p, β_d) from MVN; represents one 'consumer type'", "Simulated: numpy.random.multivariate_normal(μ_β, Σ_β)"),
])
add_source_box(doc, [
    {"citation": "Train, K.E. (2009). Discrete Choice Methods with Simulation — Chapter 9: Simulation Methods, pp. 195–222.",
     "url": "https://eml.berkeley.edu/books/train1201.pdf"},
])

# 1.1.5
add_heading(doc, "1.1.5  Consumer Welfare (Logsum Formula)", 3)
add_plain_english(doc,
    "In intro micro, consumer surplus = the area above the price line and below the demand curve. "
    "For logit models, the exact equivalent is the 'logsum' — the log of the denominator from "
    "equation 1.1.3. Dividing by β_p_i converts it from 'utils' into dollars "
    "(because β_p_i is the marginal utility of income — how much utility you get per dollar).")

add_answer_callout(doc, "Q8 — Why this equation? What is the rule-of-half and income weighting?",
    "The RULE-OF-HALF is the standard consumer surplus approximation from intro micro: "
    "ΔCS ≈ ½ · ΔQ · Δp. This is a linear approximation that works for small price changes. "
    "The LOGSUM FORMULA is the exact version for logit models — it accounts for the fact "
    "that consumers also switch between stores (not just buy more/less at one store). "
    "It is always preferred over the rule-of-half when you have a logit demand model. "
    "Source: Small & Rosen (1981), pp. 105–130.\n\n"
    "INCOME WEIGHTING (w_i): Setting w_i = 1 for all consumers treats everyone equally "
    "— a $1 welfare gain counts the same whether it goes to a rich or poor household. "
    "Setting w_i > 1 for low-income households means the policy objective explicitly "
    "weights their welfare more heavily. This is a policy choice by NYCEDC, not a "
    "mathematical requirement. For Bronx CD2, using w_i = 1 is the neutral baseline; "
    "equity-weighting can be explored as a sensitivity run.")

add_latex_eq(doc,
    r"W_i = \frac{1}{\beta_{p,i}} \ln\!\left[\sum_{k=1}^{J} \exp(V_{ik})\right]",
    fig_height=0.75, label="Equation 1.1.5a — Welfare level for consumer i (in dollars)")
add_latex_eq(doc,
    r"\Delta W_i = \frac{1}{\beta_{p,i}} \!\left[\ln\sum_k \exp\!\left(V_{ik}^{\text{post}}\right) "
    r"- \ln\sum_k \exp\!\left(V_{ik}^{\text{pre}}\right)\right]",
    fig_height=0.8, fig_width=7.0, label="Equation 1.1.5b — Welfare gain for consumer i from a subsidy")
add_latex_eq(doc,
    r"\Delta CS = \sum_{i=1}^{N} \Delta W_i \cdot w_i",
    fig_height=0.6, label="Equation 1.1.5c — Aggregate consumer surplus change (primary policy metric)")
add_equation_block(doc, "Notation (ASCII reference)",
    "W_i   = (1/β_p_i) · ln[ Σ_k exp(V_ik) ]\n"
    "ΔW_i  = (1/β_p_i) · [ ln Σ_k exp(V_ik_post)  −  ln Σ_k exp(V_ik_pre) ]\n"
    "ΔCS   = Σ_i  ΔW_i · w_i      (w_i = 1 for equal weighting; > 1 for equity weighting)",
    note="V_ik is the systematic utility defined in Section 1.1.3. 'pre' = before subsidy, 'post' = after.")

add_term_table(doc, [
    ("Consumer welfare level (in dollars)", "W_i", "Derived", "Dollar value of best available option for consumer i; increases when prices fall or options improve", "Computed from logsum formula using V_ij values"),
    ("Welfare change for consumer i", "ΔW_i", "Derived", "Dollar gain from the subsidy; positive when store j* lowers its price", "Computed: (1/β_p_i) × Δ logsum"),
    ("Aggregate consumer surplus change", "ΔCS", "Derived — PRIMARY OUTCOME", "Sum of all consumer welfare gains; the main number the city cares about", "Computed; weighted by household count"),
    ("Income weight for consumer i", "w_i", "Parameter", "= 1 (equal weighting) or > 1 for low-income tracts (equity weighting)", "Policy choice; recommend starting with w_i = 1"),
])
add_source_box(doc, [
    {"citation": "Small, K.A., & Rosen, H.S. (1981). Applied welfare economics with discrete choice models. Econometrica, 49(1), 105–130.",
     "doi": "DOI: 10.2307/1911129"},
    {"citation": "Williams, H.C.W.L. (1977). On the formation of travel demand models and economic evaluation measures of user benefit. Environment and Planning A, 9(3), 285–344.",
     "doi": "DOI: 10.1068/a090285"},
    {"citation": "Train, K.E. (2009). Discrete Choice Methods with Simulation — Chapter 3: Welfare, pp. 55–79.",
     "url": "https://eml.berkeley.edu/books/train1201.pdf"},
])

# ── 1.2 ──────────────────────────────────────────────────────────────────────
add_heading(doc, "1.2  Store Cost and Pricing", 2)
add_para(doc,
    "Each store's cost structure is calibrated from industry benchmarks and chain-specific data. "
    "There is one representative 'price level' per store (not a price per product) — "
    "think of it as the average cost of a standard grocery basket.")

# 1.2.1
add_heading(doc, "1.2.1  Total Cost Function", 3)
add_latex_eq(doc,
    r"TC_j(Q_j) = FC_j + VC_j \cdot Q_j",
    fig_height=0.6, label="Equation 1.2.1a — Total annual cost of store j")
add_latex_eq(doc,
    r"FC_j = \text{Rent}_j + \text{Labor}_{j}^{\text{fixed}} + \text{Other}_j",
    fig_height=0.65, label="Equation 1.2.1b — Fixed cost components")
add_latex_eq(doc,
    r"VC_j = \text{COGS per unit}_j + \text{Labor per unit}_j",
    fig_height=0.65, label="Equation 1.2.1c — Variable cost per unit")
add_equation_block(doc, "Notation (ASCII reference)",
    "TC_j = FC_j  +  VC_j · Q_j\n"
    "FC_j = Rent_j + Labor_fixed_j + Other_fixed_j\n"
    "VC_j = COGS_per_unit_j  +  Labor_variable_per_unit_j")
add_term_table(doc, [
    ("Total annual cost of store j", "TC_j", "Derived", "Sum of all costs; not used directly but defines profitability", "Computed from FC_j and VC_j"),
    ("Annual quantity sold at store j", "Q_j", "Dataset / Derived", "Annual transactions or basket-equivalents — see Section 1.2.5", "ReferenceUSA revenue ÷ p_j; or S_j × M"),
    ("Fixed costs of store j (annual $)", "FC_j", "Parameter", "Costs that don't change with sales volume: rent, salaried staff, utilities", "NYC ACRIS (rent) + IBISWorld labor benchmarks"),
    ("Annual rent for store j", "Rent_j", "Dataset", "From property lease records; basis for rent subsidy instrument", "NYC ACRIS lease filings; NYC DOF assessed values × market $/sq-ft"),
    ("Variable cost per unit", "VC_j", "Parameter", "Wholesale cost + variable labor per basket; ≈ 70–80% of revenue for grocery", "IBISWorld gross margin benchmarks: COGS/Revenue ratio by store type"),
])
add_source_box(doc, [
    {"citation": "IBISWorld (2024). Supermarkets & Grocery Stores in the US — Industry Report 44511.",
     "url": "https://www.ibisworld.com"},
    {"citation": "Supermarket News (annual). Top 75 Retailers & Wholesalers. Penton Media.",
     "url": "https://www.supermarketnews.com"},
    {"citation": "Walmart Inc. (2024). Annual Report on Form 10-K. SEC EDGAR.",
     "url": "https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=wmt"},
])

# 1.2.2
add_heading(doc, "1.2.2  Profit Function", 3)
add_latex_eq(doc,
    r"\pi_j = (p_j - VC_j) \cdot Q_j - FC_j",
    fig_height=0.65, label="Equation 1.2.2 — Annual profit of store j")
add_equation_block(doc, "Notation (ASCII reference)",
    "π_j = (p_j − VC_j) · Q_j  −  FC_j\n"
    "     = margin_j · Q_j  −  FC_j\n\n"
    "Note: VC_j and FC_j are defined in Section 1.2.1.\n"
    "      Q_j is defined in Section 1.2.5.\n"
    "      p_j is the baseline price level defined in Section 1.2.3 (and Q1 note below).")

add_answer_callout(doc, "Q1 — What does 'price back-calculated from revenue/volume' mean?",
    "p_j is a single number representing the average cost of a standard grocery basket at store j "
    "(e.g., $45 per shopping trip). It is NOT a price vector over many products. "
    "It is estimated as: p_j = Revenue_j / Q_j, where Revenue_j comes from ReferenceUSA "
    "(establishment-level annual revenue estimate) and Q_j is the estimated annual trip count "
    "(estimated from employee count × industry average transactions per employee). "
    "This gives one price index per store. For Bronx CD2, the BLS regional CPI food index "
    "can be used to cross-check that the p_j values are reasonable relative to area prices.")

add_term_table(doc, [
    ("Annual profit of store j", "π_j", "Derived", "Revenue minus costs; must be > 0 for store to remain open (validation check)", "Computed; check π_j > 0 for all stores before running model"),
    ("Price level at store j", "p_j", "Dataset (baseline)", "Avg basket price = Revenue_j / Q_j; see Q1 note above and Section 1.2.3", "ReferenceUSA revenue ÷ estimated volume; see Section 1.2.5"),
    ("Variable cost per unit (cross-ref)", "VC_j", "Parameter — defined in Section 1.2.1", "See Section 1.2.1 for definition and data source", "IBISWorld COGS benchmarks"),
    ("Quantity (cross-ref)", "Q_j", "Dataset / Derived — defined in Section 1.2.5", "See Section 1.2.5 for definition and data source", "ReferenceUSA; S_j × M"),
    ("Fixed cost (cross-ref)", "FC_j", "Parameter — defined in Section 1.2.1", "See Section 1.2.1 for definition and data source", "NYC ACRIS; IBISWorld"),
    ("Gross margin per unit", "margin_j = p_j − VC_j", "Derived", "Revenue per unit above variable cost; benchmark: 20–32% for grocery", "Computed; verify against IBISWorld gross margin by store type"),
])

# 1.2.3
add_heading(doc, "1.2.3  Baseline Pricing Rule (Cost-Plus Markup)", 3)
add_plain_english(doc,
    "Stores set their price as variable cost times (1 + markup). "
    "A 30% markup on a $3.00 variable cost gives a $3.90 price. "
    "Larger chains have more buying power and run on lower markups. "
    "Small independent stores in Hunts Point typically run higher markups.")
add_latex_eq(doc,
    r"p_j = (1 + \mu_j) \cdot VC_j",
    fig_height=0.6, label="Equation 1.2.3 — Baseline pricing rule (cost-plus markup)")
add_equation_block(doc, "Markup benchmarks by store type",
    "Large chain (Key Food, CTown):   μ ≈ 0.25 – 0.35\n"
    "Mid-size independent:            μ ≈ 0.35 – 0.45\n"
    "Small bodega / convenience:      μ ≈ 0.45 – 0.65\n"
    "(Source: IBISWorld grocery industry gross margin data)")
add_term_table(doc, [
    ("Markup rate for store j", "μ_j", "Parameter", "Calibrated by store type from IBISWorld; not directly observed at store level", "IBISWorld Supermarkets report; cross-check with 10-K filings for chains"),
])
add_source_box(doc, [
    {"citation": "Nevo, A. (2001). Measuring market power in the ready-to-eat cereal industry. Econometrica, 69(2), 307–342.", "doi": "DOI: 10.1111/1468-0262.00194"},
    {"citation": "Berry, S., Levinsohn, J., & Pakes, A. (1995). Automobile prices in market equilibrium. Econometrica, 63(4), 841–890.", "doi": "DOI: 10.2307/2171802"},
])

# 1.2.4
add_heading(doc, "1.2.4  Own-Price Elasticity from MNL", 3)
add_plain_english(doc,
    "Price elasticity measures how responsive consumers are to a price change at store j. "
    "An elasticity of −3 means: if store j raises prices by 1%, it loses 3% of its customers. "
    "For grocery stores, this typically falls between −2 and −5. "
    "You use this mainly as a validation check — if your estimated elasticity is far outside "
    "this range, your β_p calibration needs adjustment.")
add_latex_eq(doc,
    r"\varepsilon_{jj} = -\beta_p \cdot p_j \cdot (1 - S_j)",
    fig_height=0.65, label="Equation 1.2.4 — Own-price elasticity (standard MNL formula)")
add_equation_block(doc, "Notation (ASCII reference)",
    "ε_jj  =  −β_p · p_j · (1 − S_j)    [standard MNL]\n"
    "Expected grocery range: ε_jj ∈ [−2, −5].  If outside range, recalibrate β_p.")
add_term_table(doc, [
    ("Own-price elasticity of store j", "ε_jj", "Derived (validation check)", "% demand change per 1% price increase; expected range: −2 to −5 for grocery", "Computed from demand model; compare to literature"),
    ("Price sensitivity (population avg)", "β_p", "Parameter", "Mean of β_p_i across all income groups", "Weighted avg of group β_p values"),
])
add_source_box(doc, [
    {"citation": "Train, K.E. (2009). Discrete Choice Methods with Simulation — Appendix: Elasticities, pp. 301–310.", "url": "https://eml.berkeley.edu/books/train1201.pdf"},
    {"citation": "Davis, P. (2006). Spatial competition in retail markets: Movie theaters. RAND Journal of Economics, 37(4), 964–982.", "doi": "DOI: 10.1111/j.1756-2171.2006.tb00066.x"},
])

# 1.2.5
add_heading(doc, "1.2.5  Store Volume (Quantity Demanded)", 3)
add_latex_eq(doc,
    r"Q_j = S_j \cdot M, \qquad M = N_{\text{HH}} \cdot \bar{f} \cdot 52",
    fig_height=0.65, label="Equation 1.2.5 — Annual volume at store j and total market size M")
add_equation_block(doc, "Notation (ASCII reference)",
    "Q_j = S_j · M\n"
    "M   = N_households · avg_weekly_food_spend · 52  [annual food-at-home market, in $]\n\n"
    "Calibration check:  Q_j · p_j  ≈  Revenue_j  (from ReferenceUSA)")
add_term_table(doc, [
    ("Annual quantity (basket-trips) at store j", "Q_j", "Derived (calibration check)", "Market share times total market; verify against ReferenceUSA revenue within 20%", "Computed; cross-check: Q_j × p_j ≈ Revenue_j"),
    ("Total annual food-at-home market ($)", "M", "Parameter", "Total annual grocery spending by all households in Bronx CD2", "ACS B11001 household count × BLS CES food-at-home spend by income quintile"),
    ("Number of households in Bronx CD2", "N_HH", "Dataset", "Sum of household counts across all tracts in CD2", "ACS 5-Year Table B11001, Bronx County, CD2 tracts"),
    ("Average weekly food-at-home spending", "f̄", "Parameter", "Varies by income; ~$75–$140/week; from BLS CES by income quintile", "BLS Consumer Expenditure Survey (bls.gov/cex); Table 4700"),
])

# ── 1.3 UNIFIED ───────────────────────────────────────────────────────────────
add_heading(doc, "1.3  Subsidy Pass-Through", 2)
add_para(doc,
    "This section answers how a dollar of city subsidy translates into a lower price for consumers. "
    "There is one key insight: tax break and rent subsidy work identically in this model. "
    "Both reduce the store's fixed costs by s dollars per year. The math is the same.")
add_callout(doc,
    "Instrument unification:",
    "Tax break: city forgives s dollars of the store's annual property/business tax. ΔTax_j = −s.\n"
    "Rent subsidy: city pays s dollars of the store's annual rent. ΔRent_j = −s.\n"
    "In both cases, fixed costs fall by s:  ΔFC_j = −s.\n"
    "Price effect in both cases:  Δp_j = −θ_j · s / Q_j.\n"
    "The model treats them identically. The choice of instrument is a practical/legal decision "
    "(which cost item can the city reduce?), not a modeling decision.",
    bg_hex="FFF3E0"
)

# 1.3.1
add_heading(doc, "1.3.1  General Pass-Through Equation", 3)
add_plain_english(doc,
    "The pass-through rate θ_j answers: 'For every dollar the city gives the store, "
    "how much of that reaches the consumer as a lower price?' "
    "If θ = 0.65, a $100,000 annual subsidy at a store with 95,000 annual transactions "
    "lowers the per-basket price by: 0.65 × $100,000 / 95,000 = $0.68 per basket.")

add_answer_callout(doc, "Q10 — Is Δp_j a vector of prices or a single number?",
    "Δp_j is a SINGLE SCALAR (one number) per store — the change in the store's representative "
    "price level (average basket price). It is NOT a vector over individual products. "
    "This is consistent with using one price index per store throughout the model. "
    "Example: if baseline basket price is $42.00 and the subsidy generates Δp = −$0.68, "
    "then post-subsidy price = $41.32. Every consumer who shops at store j now pays $0.68 less.")

add_latex_eq(doc,
    r"\Delta p_j = -\theta_j \cdot g_j(s)",
    fig_height=0.6, label="Equation 1.3.1 — General pass-through equation")
add_equation_block(doc, "Notation (ASCII reference)",
    "Δp_j  = −θ_j · g_j(s)         [price reduction at store j from subsidy s]\n"
    "θ_j   ∈ [0, 1]                 [pass-through rate: fraction of savings passed to consumers]\n"
    "g_j(s) = per-unit price saving  [depends on instrument — see 1.3.2]",
    note="θ_j = 1: store passes 100% to consumers. θ_j = 0: store keeps all savings as profit. "
         "Literature: grocery markets θ ≈ 0.50–0.85. Use 0.65 as baseline; vary in sensitivity analysis.")
add_term_table(doc, [
    ("Price reduction at store j (scalar)", "Δp_j", "Derived", "Single number: drop in average basket price from subsidy; negative value = price falls", "Computed: −θ_j × g_j(s)"),
    ("Pass-through rate", "θ_j", "Parameter", "Fraction of subsidy that reaches consumers as lower prices; calibrated from literature", "Besanko et al. (2005); Nakamura & Zerom (2010); base = 0.65"),
    ("Per-unit price saving from subsidy s", "g_j(s)", "Derived", "How much s reduces the cost per unit sold; depends on instrument", "Computed from instrument formula in Section 1.3.2"),
    ("Annual subsidy amount", "s", "Decision variable", "Total dollars/year the city commits to store j; the policy lever", "City budget decision; constrained by total budget B"),
])
add_source_box(doc, [
    {"citation": "Besanko, D., Dubé, J.P., & Gupta, S. (2005). Own-brand and cross-brand retail pass-through. Marketing Science, 24(1), 123–137.", "doi": "DOI: 10.1287/mksc.1040.0107"},
    {"citation": "Nakamura, E., & Zerom, D. (2010). Accounting for incomplete pass-through. Review of Economic Studies, 77(3), 1192–1230.", "doi": "DOI: 10.1111/j.1467-937X.2009.00597.x"},
    {"citation": "Weyl, E.G., & Fabinger, M. (2013). Pass-through as an economic tool. Journal of Political Economy, 121(3), 528–583.", "doi": "DOI: 10.1086/670401"},
])

# 1.3.2
add_heading(doc, "1.3.2  Unified Cost Subsidy (Tax Break or Rent Subsidy)", 3)
add_plain_english(doc,
    "Whether the city forgives taxes or pays rent, the effect is the same: "
    "the store's fixed annual costs fall by s dollars. The store then saves s/Q_j per basket sold, "
    "and passes fraction θ of that saving to consumers as a lower price.")
add_latex_eq(doc,
    r"\Delta FC_j = -s \qquad \Longrightarrow \qquad g_j(s) = \frac{s}{Q_j}",
    fig_height=0.7, label="Equation 1.3.2a — Fixed cost reduction and per-unit saving")
add_latex_eq(doc,
    r"\Delta p_j(s) = -\theta_j \cdot \frac{s}{Q_j}",
    fig_height=0.65, label="Equation 1.3.2b — Price reduction as continuous function of subsidy s")
add_equation_block(doc, "Notation (ASCII reference)",
    "Tax break:     s = τ · Tax_j    (city forgives fraction τ of annual tax bill Tax_j)\n"
    "Rent subsidy:  s = σ_rent       (city pays σ_rent of annual rent directly)\n"
    "Both:          Δp_j(s) = −θ_j · s / Q_j    ← SAME FORMULA for both\n\n"
    "ΔCS(s) curve:  compute ΔCS for s = $0, $50K, $100K, ..., up to B (budget cap)\n"
    "               Plot s on x-axis, ΔCS on y-axis → cost-effectiveness frontier")
add_term_table(doc, [
    ("Fixed cost reduction", "ΔFC_j = −s", "Derived", "Fixed costs fall by exactly s dollars/year", "Computed"),
    ("Tax break: fraction of tax forgiven", "τ", "Decision variable", "τ ∈ [0,1]; total cost s = τ · Tax_j; data: NYC NYCDB annual tax bill", "NYC Property Tax Data: nycdb.info or data.cityofnewyork.us"),
    ("Annual tax liability of store j", "Tax_j", "Dataset", "Annual property/business tax bill for store j's parcel", "NYC NYCDB; NYC Dept. of Finance property tax portal"),
    ("Rent subsidy amount", "σ_rent", "Decision variable", "Total annual rent the city covers; total cost s = σ_rent; max = Rent_j", "City decision; upper bound = Rent_j from NYC ACRIS"),
    ("Annual rent for store j", "Rent_j", "Dataset", "From lease records or estimated from sq-ft × market rental rate", "NYC ACRIS (a836-acris.nyc.gov); NYC DOF; LoopNet commercial rate data"),
])

# 1.3.3
add_heading(doc, "1.3.3  Post-Subsidy Utility and Share Update", 3)
add_plain_english(doc,
    "This is the 'pipeline' that converts a price drop into a welfare number. "
    "There are four steps, each corresponding to one of the equations below.")

add_answer_callout(doc, "Q on 1.3.3 — What is each equation doing?",
    "Step-by-step explanation of the four equations:\n\n"
    "EQUATION A: V_ij*_post = V_ij*_pre + β_p_i · |Δp_j*|\n"
    "  → The subsidized store's utility score INCREASES because its price fell. "
    "  The improvement β_p_i · |Δp_j*| is bigger for consumers who are more price-sensitive "
    "  (higher β_p_i). Other stores' utility scores are UNCHANGED (no spillover in Goals 1 & 2).\n\n"
    "EQUATION B: V_ik_post = V_ik_pre  (for all k ≠ j*)\n"
    "  → All other stores keep their original utility scores — we are not modeling rival responses.\n\n"
    "EQUATION C: s_ij_post = exp(V_ij_post) / Σ_l exp(V_il_post)\n"
    "  → Recompute choice probabilities using the updated utility matrix. "
    "  Store j*'s share rises; all other stores' shares fall proportionally.\n\n"
    "EQUATION D: ΔCS = Σ_i (1/β_p_i) · Δln[Σ_k exp(V_ik)]\n"
    "  → The logsum (log of the denominator) rose because V_ij* rose. "
    "  The welfare gain is this logsum change divided by β_p_i (converting utils to dollars), "
    "  summed across all consumers. This is the number the city maximizes.")

add_latex_eq(doc,
    r"V_{ij^*}^{\text{post}} = V_{ij^*}^{\text{pre}} + \beta_{p,i}\cdot|\Delta p_{j^*}|",
    fig_height=0.7, label="Equation 1.3.3a — Update utility of subsidized store j* (Step 1: utility rises)")
add_latex_eq(doc,
    r"V_{ik}^{\text{post}} = V_{ik}^{\text{pre}} \quad \forall\, k \neq j^*",
    fig_height=0.65, label="Equation 1.3.3b — Rival store utilities unchanged (Step 2: no rival response)")
add_latex_eq(doc,
    r"s_{ij}^{\text{post}} = \frac{\exp\!\left(V_{ij}^{\text{post}}\right)}{\displaystyle\sum_k \exp\!\left(V_{ik}^{\text{post}}\right)}",
    fig_height=0.8, label="Equation 1.3.3c — Recompute choice probabilities with updated utilities (Step 3)")
add_latex_eq(doc,
    r"\Delta CS = \sum_{i}\frac{1}{\beta_{p,i}}\left[\ln\!\sum_k e^{V_{ik}^{\text{post}}} - \ln\!\sum_k e^{V_{ik}^{\text{pre}}}\right]",
    fig_height=0.75, fig_width=7.0, label="Equation 1.3.3d — Aggregate welfare gain (Step 4: the outcome)")
add_equation_block(doc, "Notation (ASCII reference)",
    "A: V_ij*_post = V_ij*_pre  +  β_p_i · |Δp_j*|  [j* = subsidized store]\n"
    "B: V_ik_post  = V_ik_pre                         [all other stores k]\n"
    "C: s_ij_post  = exp(V_ij_post) / Σ_l exp(V_il_post)\n"
    "D: ΔCS        = Σ_i (1/β_p_i) · Δlogsum_i",
    note="V_ij is the systematic utility from Section 1.1.3. "
         "Δlogsum_i = change in log-denominator from equations A and B. "
         "ΔCS is the number we maximize in Goal 2.")

# ── 1.4 ──────────────────────────────────────────────────────────────────────
add_heading(doc, "1.4  Optimization Problems", 2)

add_heading(doc, "1.4.1  Goal 1: Minimum Effective Subsidy (Single Store)", 3)
add_plain_english(doc,
    "Goal 1 asks: for a chosen store, how much must the city spend (s) to achieve a "
    "meaningful price reduction (say 5%) and a meaningful welfare gain (say $50K/year)? "
    "This is not a hard optimization — just trace the curve ΔCS(s) from s = 0 upward.")
add_latex_eq(doc,
    r"\min_{s \geq 0}\; s \quad\text{s.t.}\quad "
    r"\Delta p_j(s) \geq \Delta p_{\min},\;\; \Delta CS_j(s) \geq \Delta CS_{\min},\;\; s \leq B",
    fig_height=0.75, fig_width=7.0, label="Equation 1.4.1 — Goal 1: minimum subsidy meeting both thresholds")
add_equation_block(doc, "Notation (ASCII reference)",
    "min s\n"
    "s.t.  Δp_j(s)  ≥  Δp_min       [price must fall by at least Δp_min, e.g. 5% of p_j]\n"
    "      ΔCS_j(s) ≥  ΔCS_min      [welfare gain threshold, e.g. $50,000/year]\n"
    "      s        ≤  B             [total annual budget]\n\n"
    "Solution approach: grid search — compute ΔCS(s) for s = $0 to B in $10K steps;\n"
    "find first s where both constraints are satisfied.",
    note="ΔCS_min and Δp_min are set by the policymaker, not by the model. A reasonable starting point: "
         "Δp_min = 5% of baseline price; ΔCS_min = $100 per low-income household per year.")
add_term_table(doc, [
    ("Minimum required price reduction", "Δp_min", "Parameter (policy threshold)", "City's threshold: how much must prices fall to count as meaningful?", "Policy choice; e.g., 5% of baseline basket price"),
    ("Minimum welfare gain threshold", "ΔCS_min", "Parameter (policy threshold)", "City's threshold: minimum aggregate consumer surplus gain", "Policy choice; e.g., $50,000/year for CD2"),
    ("Total annual budget", "B", "Parameter (constraint)", "City's maximum annual commitment to the subsidy program", "City budget allocation — exogenous input"),
    ("Minimum effective subsidy", "s*", "Derived — OUTPUT of Goal 1", "Smallest s meeting both thresholds; the answer to Goal 1", "Computed from grid search over ΔCS(s)"),
])

add_heading(doc, "1.4.2  Goal 2: Optimal Store Selection", 3)
add_plain_english(doc,
    "Goal 2 asks: given a fixed budget B and multiple candidate stores, which store(s) "
    "should the city subsidize to maximize total consumer welfare? "
    "With 5–12 candidate stores and K = 1 (pick one store), "
    "the answer is simply: pick the store with the highest ΔCS_j(B).")
add_latex_eq(doc,
    r"\max_{\,x_j \in \{0,1\}}\;\sum_{j} x_j \cdot \Delta CS_j(s_j)",
    fig_height=0.65, label="Equation 1.4.2a — Goal 2 objective: maximize total welfare")
add_latex_eq(doc,
    r"\text{s.t.}\quad \sum_j x_j \cdot s_j \leq B,\quad "
    r"\sum_j x_j \leq K,\quad x_j \leq e_j",
    fig_height=0.65, fig_width=7.0, label="Equation 1.4.2b — Constraints: budget, store count, eligibility")
add_equation_block(doc, "Notation (ASCII reference)",
    "max_{x_j ∈ {0,1}}  Σ_j  x_j · ΔCS_j(s_j)\n"
    "s.t.  Σ_j x_j · s_j  ≤  B       [total subsidy cost ≤ budget]\n"
    "      Σ_j x_j         ≤  K       [at most K stores selected; K = 1 for simplest case]\n"
    "      x_j              ≤  e_j    [eligibility: e_j=0 eliminates ineligible stores]\n"
    "      s_j              ≥  s_j*   [minimum effective subsidy from Goal 1]",
    note="With K=1 and 5–12 stores: solve by enumeration (no optimization software needed). "
         "With K>1: use Gurobi ILP or scipy.optimize.milp.")
add_term_table(doc, [
    ("Binary store selection (1 = selected)", "x_j", "Decision variable", "1 if store j receives subsidy; 0 otherwise", "Optimization output"),
    ("Subsidy to store j", "s_j", "Decision variable", "Amount of annual subsidy; can be fixed at B (all budget to one store) or optimized", "Optimization output"),
    ("Welfare gain if store j receives s_j", "ΔCS_j(s_j)", "Derived", "From Goal 1 computation applied to each candidate store", "Computed for each store; input to Goal 2"),
    ("Max stores to select", "K", "Parameter (policy)", "Usually K = 1 for first analysis", "Policy decision"),
    ("Eligibility indicator", "e_j", "Dataset", "1 if store is SNAP-authorized, in CD2, meets size threshold", "USDA SNAP locator + city eligibility criteria"),
    ("Minimum effective subsidy at store j", "s_j*", "Derived (from Goal 1)", "Smallest s achieving meaningful ΔCS at store j", "Output of Goal 1 run per store"),
])
add_source_box(doc, [
    {"citation": "Wolsey, L.A. (1998). Integer Programming. Wiley. ISBN: 9780471283669"},
    {"citation": "Gurobi Optimization (2024). Gurobi Optimizer Reference Manual.", "url": "https://www.gurobi.com/documentation/"},
])

doc.add_page_break()

# ─────────────────────────────────────────────────────────────────────────────
# SIMPLIFICATION OPTIONS
# ─────────────────────────────────────────────────────────────────────────────
add_heading(doc, "Simplification Options for First Implementation", 1)
add_para(doc,
    "The table below lists modeling assumptions you can make to simplify the first version. "
    "Column 1 = the assumption. Column 2 = what math it simplifies. Column 3 = what you lose. "
    "Recommendation: start with the simplified model, verify results make sense, then relax "
    "assumptions one at a time.")

simp_tbl = doc.add_table(rows=1, cols=4)
simp_tbl.style = "Table Grid"
s_hdrs = ["Assumption", "What equation it simplifies", "What you lose", "When to relax"]
for i, h in enumerate(s_hdrs):
    c = simp_tbl.rows[0].cells[i]
    c.text = h; c.paragraphs[0].runs[0].bold = True
    c.paragraphs[0].runs[0].font.size = Pt(9)
    set_cell_bg(c, "1F4E79")
    c.paragraphs[0].runs[0].font.color.rgb = RGBColor(255,255,255)
simp_data = [
    ("Use standard MNL with 3 fixed income groups instead of Mixed Logit / MVN",
     "Section 1.1.2 and 1.1.4: eliminates Monte Carlo simulation entirely. "
     "Market shares have a closed-form formula.",
     "Within-group preference heterogeneity. "
     "All low-income consumers behave identically.",
     "If you suspect strong within-group heterogeneity or have time for calibration."),
    ("Fix β_q = β_v = 1.0 (equal quality and variety weights)",
     "Section 1.1.1: reduces calibration to just β_p and β_d.",
     "Cannot rank stores by quality vs. variety tradeoff.",
     "When quality or variety clearly matters more than price for a specific store."),
    ("Use a single pass-through rate θ = 0.65 for all stores",
     "Section 1.3.1 and 1.3.2: no store-specific θ calibration needed.",
     "Cannot distinguish how efficiently different store types pass subsidies.",
     "After first model runs; vary θ ∈ {0.4, 0.65, 0.85} as sensitivity parameter."),
    ("Ignore the outside option (all consumers shop at one of the J stores)",
     "Section 1.1.3: denominator sums only over in-area stores, not an outside option.",
     "Slightly overstates market size and welfare gains if some consumers shop elsewhere.",
     "If evidence of significant out-of-area or online shopping in CD2."),
    ("Use K=1 (subsidize one store only)",
     "Section 1.4.2: reduces optimization to argmax (no solver needed); compare ΔCS_j for each store.",
     "Cannot evaluate multi-store portfolio strategies.",
     "After Goal 1 is validated and budget allows multiple subsidies."),
]
for idx, row_data in enumerate(simp_data):
    row = simp_tbl.add_row().cells
    bg = "EBF3FA" if idx % 2 == 0 else "FFFFFF"
    for i, val in enumerate(row_data):
        row[i].text = val; row[i].paragraphs[0].runs[0].font.size = Pt(9)
        set_cell_bg(row[i], bg)
doc.add_paragraph()
doc.add_page_break()

# ─────────────────────────────────────────────────────────────────────────────
# PART 2
# ─────────────────────────────────────────────────────────────────────────────
add_heading(doc, "Part 2: Data Loading, Model Setup, and Solution", 1)
add_para(doc,
    "This section provides step-by-step instructions. Phase 0 assembles the data for "
    "Bronx CD2 (Hunts Point / Longwood). "
    "Phase 1 solves Goal 1 (minimum effective subsidy at one store). "
    "Phase 2 solves Goal 2 (optimal store selection).")
add_callout(doc, "Software stack:",
    "Python 3.10+ | pandas, geopandas, numpy, scipy | gurobipy (Gurobi 11) | "
    "osmnx (distance matrix) | folium (maps) | censusdataapi (ACS data)",
    bg_hex="EBF3FA")

# Phase 0
add_heading(doc, "2.0  Phase 0 — Data Pipeline (Bronx CD2)", 2)
add_para(doc, "Output: clean dataset with store attributes, consumer tracts, and distance matrix.")
add_callout(doc, "Bronx CD2 geography:",
    "Bronx Community District 2 covers Hunts Point and Longwood. "
    "FIPS: state=36, county=005. "
    "The NYC Community Districts shapefile (available at nyc.gov/planning → MapPLUTO / "
    "Community Districts) defines the exact tract boundaries. "
    "Filter ACS data using a spatial join: keep only census tracts whose centroid "
    "falls within CD2's polygon. Expected result: approximately 15–20 tracts.",
    bg_hex="FFF9C4")

p0_steps = [
    (1, "Download NYC CD2 boundary",
     "Download NYC Community Districts shapefile from NYC Planning (nyc.gov/planning → "
     "Bytes of the Big Apple → Community Districts). Load into geopandas as a GeoDataFrame. "
     "Filter to BoroCD = 202 (Bronx CD2)."),
    (2, "Download ACS data for Bronx CD2 tracts",
     "Pull ACS 5-year estimates for all Bronx tracts: B11001 (households), "
     "B19013 (median income), B19001 (income distribution brackets), "
     "B08201 (vehicle access). Spatial join with CD2 boundary to keep only CD2 tracts."),
    (3, "Assign income groups to tracts",
     "For simplified model: classify each tract into Low (<$25K), Mid ($25K–$50K), "
     "High (>$50K) based on B19001 bracket distribution. "
     "Compute household count per group per tract."),
    (4, "Build candidate store list",
     "Download USDA SNAP Retailer Locator CSV (snap-retailer-locator.fns.usda.gov). "
     "Filter to Bronx (state=NY, county=Bronx). Geocode. Spatial join to CD2 boundary. "
     "Cross-reference with NYC DOHMH food establishment data "
     "(data.cityofnewyork.us dataset: DOHMH New York City Restaurant Inspection Results). "
     "Target: 5–12 SNAP-authorized stores."),
    (5, "Classify stores and assign q_j, v_j",
     "Supermarket → q_j = 3, v_j = 3. Discount/dollar store → q_j = 2, v_j = 2. "
     "Bodega/convenience → q_j = 1, v_j = 1. "
     "Use sq footage from property records (ACRIS) to distinguish within types."),
    (6, "Compute distance matrix d_ij",
     "Compute tract centroids (geopandas centroid). Geocode store addresses. "
     "Use osmnx: ox.graph_from_place('Hunts Point, Bronx, NY', network_type='walk') "
     "then ox.distance.nearest_nodes for each centroid/store. "
     "Compute shortest walking path time (minutes). Store as N×J matrix."),
    (7, "Calibrate cost structure (FC_j, VC_j) per store",
     "FC_j: Rent_j from ACRIS (sq ft × $/sq-ft market rate for Hunts Point, ~$20–$35/sq-ft/yr) "
     "+ Labor_fixed from employee count (ReferenceUSA) × avg grocery manager wage (BLS OES 41-1011). "
     "VC_j: IBISWorld COGS benchmark for store type (conventional grocery: ~72% of revenue; "
     "discount: ~78%; bodega: ~75%). "
     "Q_j: Revenue_j (ReferenceUSA) ÷ p_j."),
    (8, "Set preference parameters β per income group",
     "Low income (<$25K): β_p = 0.55, β_d = 0.40. "
     "Mid income ($25K–$50K): β_p = 0.30, β_d = 0.25. "
     "High income (>$50K): β_p = 0.15, β_d = 0.15. "
     "β_q = β_v = 1.0 for all groups. "
     "These starting values come from Allcott et al. (2019) Table IV. "
     "Treat as sensitivity parameters."),
]
for n, title, detail in p0_steps:
    add_step(doc, n, title, detail)

add_code_block(doc, """# Phase 0 — Bronx CD2 Data Pipeline (Python)
import pandas as pd
import geopandas as gpd
import numpy as np
import osmnx as ox
from censusdataapi import CensusData   # pip install censusdataapi

# ── 1. NYC CD2 boundary ──────────────────────────────────────────────────────
cd_url = "https://data.cityofnewyork.us/api/geospatial/jp9i-3b7y?method=export&type=Shapefile"
cd = gpd.read_file(cd_url).to_crs(epsg=4326)
cd2 = cd[cd["BoroCD"] == 202]   # Bronx CD 2

# ── 2. ACS data ──────────────────────────────────────────────────────────────
c = CensusData("YOUR_API_KEY")
acs = c.acs5(
    variables=["B11001_001E",  # households
               "B19013_001E",  # median income
               "B08201_001E",  # vehicle access
               "B19001_001E"], # income brackets
    for_="tract:*",
    in_="state:36 county:005"  # NY, Bronx County
)
tracts_gdf = gpd.GeoDataFrame(acs, geometry=gpd.points_from_xy(
    acs["lon"], acs["lat"])).set_crs(epsg=4326)
cd2_tracts = tracts_gdf.sjoin(cd2[["geometry"]], how="inner", predicate="within")
print(f"CD2 tracts: {len(cd2_tracts)}")

# ── 3. SNAP stores ───────────────────────────────────────────────────────────
snap = pd.read_csv("data/snap_retailer_locator.csv")
snap_bronx = snap[snap["State"] == "NY"]
snap_gdf = gpd.GeoDataFrame(snap_bronx,
    geometry=gpd.points_from_xy(snap_bronx.Longitude, snap_bronx.Latitude)).set_crs(epsg=4326)
stores_cd2 = snap_gdf.sjoin(cd2[["geometry"]], how="inner", predicate="within")
print(f"SNAP stores in CD2: {len(stores_cd2)}")

# ── 4. Walking distance matrix ───────────────────────────────────────────────
G = ox.graph_from_place("Hunts Point, Bronx, New York, USA", network_type="walk")
tract_centroids = cd2_tracts.geometry.centroid
store_coords    = [(r.geometry.y, r.geometry.x) for _, r in stores_cd2.iterrows()]

d_ij = np.zeros((len(cd2_tracts), len(stores_cd2)))
for i, centroid in enumerate(tract_centroids):
    n_src = ox.distance.nearest_nodes(G, centroid.x, centroid.y)
    for j, (sy, sx) in enumerate(store_coords):
        n_dst = ox.distance.nearest_nodes(G, sx, sy)
        try:
            t = nx.shortest_path_length(G, n_src, n_dst, weight="travel_time")
        except Exception:
            t = 999  # unreachable
        d_ij[i, j] = t / 60  # convert seconds to minutes
print("Distance matrix shape:", d_ij.shape)
""", caption="Phase 0: Bronx CD2 Data Pipeline")

# Phase 1
add_heading(doc, "2.1  Goal 1 — Single-Store Subsidy Effect", 2)
add_para(doc, "Output: ΔCS(s) curve for one store — shows welfare gain at every subsidy level from $0 to B.")

g1_steps = [
    (1, "Select representative store j*",
     "Choose a store in a food-desert tract (e.g., lowest-income tract in CD2). "
     "All other store prices remain at baseline. Fix θ = 0.65."),
    (2, "Build Δp_j(s) function",
     "Δp_j(s) = θ_j · s / Q_j. Build a grid: s_grid = np.linspace(0, B_max, 500)."),
    (3, "Compute V_ij matrix (pre-subsidy)",
     "For each income group i and store j: V_ij = β_q_i·q_j + β_v_i·v_j − β_p_i·p_j − β_d_i·d_ij. "
     "Store as matrix V_pre of shape (N_groups, J)."),
    (4, "For each s in grid, compute ΔCS(s)",
     "Update V_ij*_post = V_ij*_pre + β_p_i·|Δp_j*(s)|. "
     "Compute logsum_pre = log(Σ_k exp(V_ik_pre)) per group. "
     "Compute logsum_post = log(Σ_k exp(V_ik_post)) per group. "
     "ΔW_i = (1/β_p_i)·(logsum_post − logsum_pre). "
     "ΔCS = Σ_i ΔW_i · household_count_i."),
    (5, "Find threshold s*",
     "s* = min{s : ΔCS(s) ≥ ΔCS_min AND Δp_j(s)/p_j ≥ 5%}."),
    (6, "Sensitivity on θ and β_p",
     "Repeat for θ ∈ {0.40, 0.65, 0.85} and β_p scale ∈ {0.8, 1.0, 1.2}. "
     "Plot ΔCS(s) curves with confidence band."),
    (7, "Compare tax break vs. rent subsidy",
     "Both use the same formula Δp_j = θ·s/Q_j, so the ΔCS(s) curve is identical. "
     "The difference is practical: which cost item (tax or rent) can the city actually reduce "
     "for this store? Report both instrument labels at the same s* value."),
]
for n, title, detail in g1_steps:
    add_step(doc, n, title, detail)

add_code_block(doc, """# Goal 1 — Single-Store Subsidy Effect (Python)
import numpy as np
from scipy.special import logsumexp

# ── Inputs (from Phase 0) ─────────────────────────────────────────────────────
# q_j, v_j : (J,) store quality and variety scores
# p_j      : (J,) baseline price levels
# d_ij     : (N, J) distance matrix
# beta_p_i : (N,) price sensitivity per income group
# beta_d_i : (N,) distance sensitivity per income group
# beta_q, beta_v : scalars (= 1.0 for simplified model)
# household_count : (N,) households per income group in CD2
# Q_j      : (J,) annual volumes
# theta    : pass-through rate (scalar, start with 0.65)
# j_star   : index of subsidized store
# B_max    : max annual subsidy to consider

# ── Pre-subsidy utility matrix V_pre ─────────────────────────────────────────
N, J = len(beta_p_i), len(q_j)
V_pre = np.zeros((N, J))
for i in range(N):
    V_pre[i] = (beta_q * q_j + beta_v * v_j
                - beta_p_i[i] * p_j
                - beta_d_i[i] * d_ij[i])

# ── Grid search over subsidy levels ──────────────────────────────────────────
s_grid   = np.linspace(0, B_max, 500)
DCS_vals = np.zeros_like(s_grid)
dp_vals  = np.zeros_like(s_grid)

for idx, s in enumerate(s_grid):
    delta_p = theta * s / Q_j[j_star]          # price reduction ($/basket)
    V_post  = V_pre.copy()
    V_post[:, j_star] += beta_p_i * delta_p    # utility of j* rises

    logsum_pre  = logsumexp(V_pre,  axis=1)     # (N,)
    logsum_post = logsumexp(V_post, axis=1)     # (N,)

    delta_W     = (1.0 / beta_p_i) * (logsum_post - logsum_pre)  # (N,) in $
    DCS_vals[idx] = np.sum(delta_W * household_count)
    dp_vals[idx]  = delta_p

# ── Find minimum effective subsidy ───────────────────────────────────────────
DCS_min = 50_000           # $50K aggregate welfare threshold
dp_min  = p_j[j_star] * 0.05   # 5% price reduction

mask   = (DCS_vals >= DCS_min) & (dp_vals >= dp_min)
s_star = s_grid[mask][0] if mask.any() else None
print(f"Min effective subsidy: ${s_star:,.0f}  |  "
      f"Price drop: {dp_vals[mask][0]:.2f}  |  "
      f"ΔCS: ${DCS_vals[mask][0]:,.0f}")

# ── Plot ΔCS(s) curve ─────────────────────────────────────────────────────────
import matplotlib.pyplot as plt
fig, ax = plt.subplots(figsize=(7, 4))
ax.plot(s_grid / 1000, DCS_vals / 1000, color="steelblue", lw=2, label="ΔCS(s), θ=0.65")
ax.axhline(DCS_min / 1000, color="red", ls="--", label=f"ΔCS_min = ${DCS_min/1000:.0f}K")
if s_star: ax.axvline(s_star / 1000, color="green", ls=":", label=f"s* = ${s_star/1000:.0f}K")
ax.set_xlabel("Annual subsidy s ($ thousands)")
ax.set_ylabel("Aggregate welfare gain ΔCS ($ thousands/year)")
ax.set_title("Goal 1: Cost-Effectiveness Frontier — Store j* in Bronx CD2")
ax.legend(); ax.grid(alpha=0.3)
fig.savefig("goal1_curve.png", dpi=150, bbox_inches="tight")
plt.show()
""", caption="Goal 1: Python Implementation")

# Phase 2
add_heading(doc, "2.2  Goal 2 — Optimal Store Selection (Gurobi)", 2)
add_para(doc, "Output: which store maximizes ΔCS subject to budget B.")

g2_steps = [
    (1, "Run Goal 1 for every candidate store",
     "Call the Goal 1 function for each store j at the full budget B. "
     "Record DCS_j = ΔCS_j(B) and s_j_star = minimum effective subsidy per store."),
    (2, "Apply eligibility filters",
     "Set e_j = 0 for: stores not SNAP-authorized, stores outside CD2, "
     "stores owned by a chain if policy targets independents."),
    (3, "K=1 enumeration (recommended first step)",
     "Sort eligible stores by DCS_j descending. "
     "Top store is optimal under K=1. No solver needed."),
    (4, "K>1 integer program via Gurobi",
     "Use gurobipy to set up and solve the ILP from equation 1.4.2."),
    (5, "Continuous budget allocation (scipy SLSQP)",
     "Optimize s_j across stores simultaneously using scipy.optimize.minimize."),
    (6, "Distributional analysis",
     "Break ΔCS_j down by income group. "
     "Does the best store disproportionately benefit the lowest-income tracts in CD2?"),
    (7, "Instrument comparison",
     "For the optimal store, report: same ΔCS applies to both tax break and rent subsidy. "
     "Flag which instrument is available based on store lease/ownership structure."),
]
for n, title, detail in g2_steps:
    add_step(doc, n, title, detail)

add_code_block(doc, """# Goal 2 — Optimal Store Selection using Gurobi (gurobipy)
import gurobipy as gp
from gurobipy import GRB
import numpy as np

# ── Inputs: DCS_j[j] = welfare gain if store j gets full budget B ────────────
# s_j_star[j] = minimum effective subsidy for store j (from Goal 1)
# e_j[j]      = 1 if store j is eligible; 0 otherwise
# B           = total annual budget
# K           = max stores to subsidize

J = len(DCS_j)
B = 1_500_000    # $1.5M annual budget (adjust to Bronx CD2 policy context)
K = 1            # start with K=1 (single store selection)

# ── K=1 solution by enumeration (simplest approach) ──────────────────────────
eligible_welfare = [(DCS_j[j], j) for j in range(J) if e_j[j] == 1]
best_store = max(eligible_welfare, key=lambda x: x[0])
print(f"K=1 optimal store: {best_store[1]}  ΔCS = ${best_store[0]:,.0f}")

# ── K>1 solution via Gurobi ILP ───────────────────────────────────────────────
m = gp.Model("store_selection")
m.setParam("OutputFlag", 0)

x = m.addVars(J, vtype=GRB.BINARY, name="x")
m.setObjective(gp.quicksum(DCS_j[j] * x[j] for j in range(J)), GRB.MAXIMIZE)

m.addConstr(gp.quicksum(s_j_star[j] * x[j] for j in range(J)) <= B, "budget")
m.addConstr(gp.quicksum(x[j]           for j in range(J)) <= K,    "max_stores")
for j in range(J):
    m.addConstr(x[j] <= e_j[j], f"elig_{j}")

m.optimize()

if m.status == GRB.OPTIMAL:
    selected = [j for j in range(J) if x[j].X > 0.5]
    print(f"Gurobi optimal (K={K}): stores {selected}, ΔCS = ${m.ObjVal:,.0f}")

# ── Continuous allocation: scipy SLSQP ───────────────────────────────────────
from scipy.optimize import minimize

def neg_DCS_total(s_vec):
    total = 0
    for j in range(J):
        if e_j[j] == 1:
            delta_p = theta * s_vec[j] / Q_j[j]
            V_post  = V_pre.copy()
            V_post[:, j] += beta_p_i * delta_p
            dW = (1.0 / beta_p_i) * (logsumexp(V_post, axis=1) - logsumexp(V_pre, axis=1))
            total += np.sum(dW * household_count)
    return -total

s0     = np.ones(J) * B / J
bounds = [(0, B) for _ in range(J)]
constr = {"type": "ineq", "fun": lambda s: B - np.sum(s)}
res = minimize(neg_DCS_total, s0, method="SLSQP",
               bounds=bounds, constraints=constr,
               options={"ftol": 1e-9, "maxiter": 500})
print("Continuous optimal allocation ($/store):", res.x.round(0).astype(int))
""", caption="Goal 2: Gurobi + scipy Implementation")

doc.add_page_break()

# ─────────────────────────────────────────────────────────────────────────────
# APPENDIX A
# ─────────────────────────────────────────────────────────────────────────────
add_heading(doc, "Appendix A: Worked Numerical Example", 1)
add_para(doc,
    "A complete end-to-end numerical example for Bronx CD2 with hypothetical but "
    "realistic values. All arithmetic is shown so you can verify the model by hand.")
add_heading(doc, "A.1  Setup", 2)
add_para(doc,
    "Study area: 1 census tract (Hunts Point, Bronx). Stores: J = 3. "
    "Consumer income groups: N = 3 (Low <$25K, Mid $25K–$50K, High >$50K). "
    "Market size: M = 1,200 households × $5,000/yr = $6,000,000/yr.")

add_heading(doc, "A.2  Store Attributes", 2)
tbl = doc.add_table(rows=1, cols=7); tbl.style = "Table Grid"
for i, h in enumerate(["Store", "Type", "q_j", "v_j", "p_j ($/basket)", "FC_j ($K/yr)", "VC_j ($/basket)"]):
    c = tbl.rows[0].cells[i]
    c.text = h; c.paragraphs[0].runs[0].bold = True
    c.paragraphs[0].runs[0].font.size = Pt(9)
    set_cell_bg(c, "1F4E79")
    c.paragraphs[0].runs[0].font.color.rgb = RGBColor(255,255,255)
for d in [
    ["Store 1 (Independent)", "Independent", "2", "2", "$42.00", "$310K", "$31.50"],
    ["Store 2 (Discount)",    "Discount",    "1", "1", "$36.00", "$175K", "$28.80"],
    ["Store 3 (Chain Key Food)", "Supermarket", "3", "3", "$48.00", "$620K", "$34.56"],
]:
    row = tbl.add_row().cells
    for i, v in enumerate(d):
        row[i].text = v; row[i].paragraphs[0].runs[0].font.size = Pt(9)
doc.add_paragraph()

add_heading(doc, "A.3  Consumer Groups", 2)
tbl2 = doc.add_table(rows=1, cols=5); tbl2.style = "Table Grid"
for i, h in enumerate(["Group", "HH Count", "β_p_i", "β_d_i", "Avg distance to Store 1 (min)"]):
    c = tbl2.rows[0].cells[i]
    c.text = h; c.paragraphs[0].runs[0].bold = True
    c.paragraphs[0].runs[0].font.size = Pt(9)
    set_cell_bg(c, "1F4E79")
    c.paragraphs[0].runs[0].font.color.rgb = RGBColor(255,255,255)
for d in [
    ["Low (<$25K)",       "720",  "0.55", "0.40", "6 min"],
    ["Mid ($25–$50K)",    "360",  "0.30", "0.25", "9 min"],
    ["High (>$50K)",      "120",  "0.15", "0.15", "12 min"],
]:
    row = tbl2.add_row().cells
    for i, v in enumerate(d):
        row[i].text = v; row[i].paragraphs[0].runs[0].font.size = Pt(9)
doc.add_paragraph()

add_heading(doc, "A.4  Rent Subsidy Calculation at Store 1 (s = $100,000)", 2)
add_equation_block(doc, "Step-by-step arithmetic",
    "Given:  FC_j = $310,000/yr,  Rent_j = $175,000/yr,  Q_j = 90,000 baskets/yr\n"
    "        θ = 0.65,  s = $100,000 annual rent subsidy\n\n"
    "Per-unit saving:  g_j = $100,000 / 90,000 = $1.111 per basket\n"
    "Price reduction:  Δp_j = 0.65 × $1.111 = $0.722 per basket  (≈ 1.7% of $42.00)\n\n"
    "Utility update for Low-income group:\n"
    "  V_11_pre  = 1.0·2 + 1.0·2 − 0.55·42 − 0.40·6  = 4.0 − 23.1 − 2.4 = −21.5\n"
    "  ΔV_11     = β_p_1 · Δp_j = 0.55 × 0.722 = +0.397\n"
    "  V_11_post = −21.5 + 0.397 = −21.103\n\n"
    "Logsum for Low-income group (all 3 stores, approximate):\n"
    "  logsum_pre  ≈ ln(e^{-21.5} + e^{-23.4} + e^{-19.8}) ≈ −19.78\n"
    "  logsum_post ≈ ln(e^{-21.1} + e^{-23.4} + e^{-19.8}) ≈ −19.77\n"
    "  ΔW_low = (1/0.55) × (−19.77 − (−19.78)) = 1.818 × 0.010 = $0.018 per HH\n"
    "  ΔCS_low group = $0.018 × 720 HH = $13.0/year")

add_callout(doc, "Interpretation of worked example:",
    "A $100,000 annual rent subsidy at Store 1 yields approximately $13–$50 in aggregate "
    "welfare gain per year (scaling up from the low-income group example to all 3 groups). "
    "This illustrates that a small pass-through and modest scale lead to modest welfare gains. "
    "The key sensitivity is: at what θ and Q_j does the welfare gain per dollar become policy-relevant? "
    "Use the Goal 1 grid search to find the answer.",
    bg_hex="E8F5E9")

doc.add_page_break()

# APPENDIX B
add_heading(doc, "Appendix B: Sensitivity Analysis Framework", 1)
add_para(doc,
    "The minimum effective subsidy s* is most sensitive to two parameters: θ (pass-through rate) "
    "and β_p (price sensitivity). The table shows illustrative s* values for different combinations.")
add_para(doc, "Sensitivity: s* to achieve ΔCS ≥ $50,000/year at Store 1 (Bronx CD2, rent subsidy).",
         italic=True)

sens_tbl = doc.add_table(rows=1, cols=5); sens_tbl.style = "Table Grid"
for i, h in enumerate(["β_p scale  \\  θ", "θ = 0.40", "θ = 0.55", "θ = 0.65 (base)", "θ = 0.85"]):
    c = sens_tbl.rows[0].cells[i]
    c.text = h; c.paragraphs[0].runs[0].bold = True
    c.paragraphs[0].runs[0].font.size = Pt(9)
    set_cell_bg(c, "1F4E79")
    c.paragraphs[0].runs[0].font.color.rgb = RGBColor(255,255,255)
for d in [
    ["β_p × 0.8 (less sensitive)", "$3.2M", "$2.3M", "$1.9M", "$1.5M"],
    ["β_p × 1.0 (base)",           "$2.3M", "$1.7M", "$1.4M", "$1.1M"],
    ["β_p × 1.2 (more sensitive)", "$1.9M", "$1.4M", "$1.2M", "$0.9M"],
]:
    row = sens_tbl.add_row().cells
    for i, v in enumerate(d):
        row[i].text = v; row[i].paragraphs[0].runs[0].font.size = Pt(9)
        if i == 3: set_cell_bg(row[i], "FFF9C4")
doc.add_paragraph()
add_para(doc, "Key insight: when θ doubles (0.40 → 0.85), required subsidy drops by ~35%. "
              "The most important calibration task is getting a good estimate of θ from the literature.")

doc.add_page_break()

# APPENDIX C
add_heading(doc, "Appendix C: Model Validation Checklist", 1)
add_para(doc,
    "Run these checks after Phase 0 data assembly and before computing welfare results. "
    "A failure means a calibration problem, not a code bug.")
chk_tbl = doc.add_table(rows=1, cols=4); chk_tbl.style = "Table Grid"
for i, h in enumerate(["Category", "Check", "Criterion", "How to Verify"]):
    c = chk_tbl.rows[0].cells[i]
    c.text = h; c.paragraphs[0].runs[0].bold = True
    c.paragraphs[0].runs[0].font.size = Pt(9)
    set_cell_bg(c, "1F4E79")
    c.paragraphs[0].runs[0].font.color.rgb = RGBColor(255,255,255)
for idx, d in enumerate([
    ("Demand", "Market shares sum to 1", "sum(S_j) = 1.0 ± 0.001", "assert abs(S_j.sum()-1)<1e-3"),
    ("Demand", "All probabilities in (0,1)", "0 < s_ij < 1 for all i,j", "assert (s>0).all() and (s<1).all()"),
    ("Demand", "Predicted volumes near observed", "Q_j·p_j within 20% of Revenue_j", "Compare to ReferenceUSA revenue"),
    ("Demand", "Own-price elasticities in range", "ε_jj ∈ [−2, −5] for grocery", "Compute and print ε_jj for all stores"),
    ("Demand", "Welfare sign is correct", "ΔCS > 0 when price falls", "Unit test: compute_DCS(s=100K) > 0"),
    ("Supply", "All stores profitable at baseline", "π_j > 0 for all j", "assert (pi_pre > 0).all()"),
    ("Supply", "Markup calibration check", "p_j ≈ (1+μ_j)·VC_j within 5%", "Compare implied vs. observed prices"),
    ("Pass-through", "θ produces realistic Δp", "1% subsidy → 0.5–0.8% price drop", "Check Δp/p for s = 1% of Revenue_j"),
    ("Optimization", "Gurobi solution feasible", "Σ s_j ≤ B and e_j constraints satisfied", "Check Gurobi constraint violations"),
]):
    row = chk_tbl.add_row().cells
    bg = "EBF3FA" if idx % 2 == 0 else "FFFFFF"
    for i, v in enumerate(d):
        row[i].text = v; row[i].paragraphs[0].runs[0].font.size = Pt(9)
        set_cell_bg(row[i], bg)
doc.add_paragraph()

doc.add_page_break()

# APPENDIX D
add_heading(doc, "Appendix D: Assumptions, Limitations, and Caveats", 1)
add_para(doc,
    "Every model rests on assumptions. The table lists each assumption, "
    "what must be true for it to hold, and what happens if it is violated.")
a_tbl = doc.add_table(rows=1, cols=4); a_tbl.style = "Table Grid"
for i, h in enumerate(["Assumption", "Required condition", "If violated…", "Sensitivity / Extension"]):
    c = a_tbl.rows[0].cells[i]
    c.text = h; c.paragraphs[0].runs[0].bold = True
    c.paragraphs[0].runs[0].font.size = Pt(9)
    set_cell_bg(c, "1F4E79")
    c.paragraphs[0].runs[0].font.color.rgb = RGBColor(255,255,255)
for idx, d in enumerate([
    ("Static single-period model", "Short-run; no store entry or exit", "Underestimates long-run access benefits if subsidy prevents closure", "Extend to dynamic if multi-year program"),
    ("Fixed store attributes (q_j, v_j)", "Subsidy doesn't enable quality/variety upgrades", "Welfare gains underestimated if store reinvests subsidy in upgrades", "Sensitivity run: shift q_j or v_j by +1"),
    ("No rival response", "Competing stores don't react to subsidized store's lower price", "If rivals cut prices too, consumer gains are larger; rival losses smaller", "Optional extension: Bertrand loop"),
    ("Single representative price per store", "Consumers can be characterized by one avg basket price", "Ignores within-store price variation across products", "Use product-level data if available"),
    ("Pass-through θ is constant", "Store's pricing is linear in subsidy amount", "If store pockets more at larger subsidies, cost-effectiveness is overstated", "Model θ as decreasing in s; run sensitivity"),
    ("No outside option / online grocery", "Consumers shop only at the J local stores", "If consumers shop at Walmart in co-op city or online, welfare gains overstated", "Add j=0 outside option with fixed utility"),
    ("Census tract = homogeneous consumer unit", "All households in a tract have the same preferences", "Ignores within-tract income heterogeneity", "Split tracts into income groups (3-group model)"),
]):
    row = a_tbl.add_row().cells
    bg = "EBF3FA" if idx % 2 == 0 else "FFFFFF"
    for i, v in enumerate(d):
        row[i].text = v; row[i].paragraphs[0].runs[0].font.size = Pt(9)
        set_cell_bg(row[i], bg)
doc.add_paragraph()

doc.add_page_break()

# APPENDIX E
add_heading(doc, "Appendix E: Output Interpretation and Plain-Language Template", 1)
add_heading(doc, "E.1  Key Outputs by Goal", 2)
out_tbl = doc.add_table(rows=1, cols=4); out_tbl.style = "Table Grid"
for i, h in enumerate(["Goal", "Primary output", "Chart / table", "How to read it"]):
    c = out_tbl.rows[0].cells[i]
    c.text = h; c.paragraphs[0].runs[0].bold = True
    c.paragraphs[0].runs[0].font.size = Pt(9)
    set_cell_bg(c, "1F4E79")
    c.paragraphs[0].runs[0].font.color.rgb = RGBColor(255,255,255)
for idx, d in enumerate([
    ("Goal 1", "Cost-effectiveness frontier ΔCS(s)", "Line chart: x = annual subsidy $, y = ΔCS $/yr", "Find the 'elbow' where each extra dollar gives rapidly diminishing welfare return — that is s*"),
    ("Goal 1", "Instrument comparison", "Side-by-side table: tax break vs. rent subsidy at equal cost s*", "Both instruments produce same ΔCS; difference is which cost item the city reduces"),
    ("Goal 2", "Store ranking table", "Table: stores sorted by ΔCS_j(B), with eligibility column", "Top-ranked eligible store = recommended selection under K=1 and budget B"),
    ("Goal 2", "Distributional breakdown", "Bar chart: ΔCS by income group for each candidate store", "Prefer stores where a larger share of ΔCS goes to Low-income households in Hunts Point"),
]):
    row = out_tbl.add_row().cells
    bg = "EBF3FA" if idx % 2 == 0 else "FFFFFF"
    for i, v in enumerate(d):
        row[i].text = v; row[i].paragraphs[0].runs[0].font.size = Pt(9)
        set_cell_bg(row[i], bg)
doc.add_paragraph()

add_heading(doc, "E.2  Plain-Language Summary Template", 2)
add_para(doc, "Use this template for NYCEDC staff, elected officials, and community boards:")
add_callout(doc, "Summary Template:",
    '"Subsidizing [STORE NAME], a [store type] at [address] in Hunts Point, '
    'with a [rent subsidy / tax break] of $[AMOUNT] per year is projected to reduce '
    'consumer prices by approximately [X]%, generating an estimated welfare gain of '
    '$[ΔCS] per year for the [N] households in Bronx Community District 2. '
    'Low-income households (earning below $25,000/year) capture approximately [Y]% of this benefit. '
    'The most cost-effective store — generating $[ΔCS*] in welfare per dollar spent — '
    'is [STORE NAME], which is estimated to benefit [Z] low-income households directly."',
    bg_hex="F3E5F5"
)

add_heading(doc, "E.3  Instrument Selection Flowchart", 2)
add_para(doc, "Use this to decide which subsidy instrument to apply before running the model:")
for n, step in enumerate([
    "Does the store lease (not own) its space?\n"
    "   YES → Use Rent Subsidy (Instrument 2). Data needed: NYC ACRIS lease amount (Rent_j).\n"
    "   NO  → Continue.",
    "Does the store own its property and pay significant property tax?\n"
    "   YES → Use Tax Break (Instrument 1). Data needed: NYC NYCDB annual tax bill (Tax_j).\n"
    "   NO  → Explore hybrid instruments or reconsider eligibility.",
    "Note: both instruments use the same model equation: Δp_j = −θ_j · s / Q_j.\n"
    "The only difference is which data you use to set the maximum value of s.",
], start=1):
    p = doc.add_paragraph()
    p.paragraph_format.left_indent = Inches(0.3)
    p.paragraph_format.space_after = Pt(6)
    p.add_run(f"{n}.  {step}").font.size = Pt(10)

doc.add_page_break()

# APPENDIX F — MASTER REFERENCE TABLE
add_heading(doc, "Appendix F: Complete Data and Parameter Reference Table", 1)
add_para(doc,
    "Every symbol used in the model is listed below with its type, the equation section where "
    "it first appears, and the specific dataset or estimation method needed to obtain it. "
    "Green = parameter (estimated from data). Orange = dataset (directly observed). "
    "Purple = decision variable (set by city).")

ref_tbl = doc.add_table(rows=1, cols=6)
ref_tbl.style = "Table Grid"
for i, h in enumerate(["Symbol", "Term", "Section", "Type", "Specific data needed", "Source"]):
    c = ref_tbl.rows[0].cells[i]
    c.text = h; c.paragraphs[0].runs[0].bold = True
    c.paragraphs[0].runs[0].font.size = Pt(8.5)
    set_cell_bg(c, "1F4E79")
    c.paragraphs[0].runs[0].font.color.rgb = RGBColor(255,255,255)

ref_rows = [
    ("q_j",        "Quality index",              "1.1.1", "Dataset",   "Store type classification; sq footage", "NYC DOHMH + SNAP locator"),
    ("v_j",        "Variety index",              "1.1.1", "Dataset",   "Store type; IBISWorld avg SKU by type", "NYC DOHMH; IBISWorld"),
    ("p_j",        "Baseline price level",       "1.1.1 / 1.2.3", "Dataset", "Revenue_j / Q_j (see 1.2.5)", "ReferenceUSA + BLS CPI"),
    ("d_ij",       "Distance (min)",             "1.1.1", "Dataset",   "Walking minutes from tract centroid to store", "OSMnx + Census TIGER"),
    ("β_p_i",      "Price sensitivity",          "1.1.1", "Parameter", "Allcott et al. Table IV; scaled by ACS income", "Allcott et al. (2019)"),
    ("β_d_i",      "Distance sensitivity",       "1.1.1", "Parameter", "Literature; scaled by ACS vehicle access (B08201)", "Ben-Akiva & Lerman (1985)"),
    ("β_q_i",      "Quality weight",             "1.1.1", "Parameter", "Set = 1.0 for simplified model", "Handbury (2021)"),
    ("β_v_i",      "Variety weight",             "1.1.1", "Parameter", "Set = 1.0 for simplified model", "Handbury (2021)"),
    ("μ_β",        "Mean preference vector",     "1.1.2", "Parameter", "Weighted avg of group β values from literature", "Allcott et al. (2019); Davis (2006)"),
    ("Σ_β",        "Preference covariance",      "1.1.2", "Parameter", "Set to diagonal for simplified model", "Train (2009) Ch. 6"),
    ("V_ij",       "Systematic utility",         "1.1.3", "Derived",   "Computed from β_i and store attributes", "Equation 1.1.3b"),
    ("S_j",        "Market share",               "1.1.4", "Derived",   "Weighted avg of choice probs across income groups", "Equation 1.1.4"),
    ("N_HH",       "Household count in CD2",     "1.1.4 / 1.2.5", "Dataset", "Sum of households across CD2 tracts", "ACS Table B11001, Bronx CD2 tracts"),
    ("W_i / ΔW_i", "Welfare / welfare change",   "1.1.5", "Derived",   "Logsum formula; computed from V_ij", "Equation 1.1.5"),
    ("ΔCS",        "Aggregate welfare change",   "1.1.5", "Derived — PRIMARY OUTPUT", "Σ_i ΔW_i · household_count_i", "Equation 1.1.5c"),
    ("w_i",        "Income weight",              "1.1.5", "Parameter", "= 1 for neutral weighting; > 1 for equity", "Policy choice"),
    ("FC_j",       "Fixed costs ($/yr)",         "1.2.1", "Parameter", "Rent_j (ACRIS) + salaried labor (BLS OES) + other", "NYC ACRIS; BLS OES 41-1011"),
    ("VC_j",       "Variable cost per unit",     "1.2.1", "Parameter", "COGS = 1 − gross margin; IBISWorld by store type", "IBISWorld Report 44511"),
    ("Rent_j",     "Annual rent",                "1.2.1", "Dataset",   "Lease amount from ACRIS; or sq-ft × market rate", "NYC ACRIS; a836-acris.nyc.gov"),
    ("π_j",        "Annual profit",              "1.2.2", "Derived",   "Validation check: must be > 0 at baseline", "Equation 1.2.2"),
    ("μ_j",        "Markup rate",                "1.2.3", "Parameter", "IBISWorld gross margin by store type", "IBISWorld; 10-K filings"),
    ("Q_j",        "Annual volume (baskets)",    "1.2.5", "Dataset/Derived", "Revenue_j / p_j; cross-check with S_j × M", "ReferenceUSA; BLS CES"),
    ("M",          "Total market size ($)",      "1.2.5", "Parameter", "N_HH × avg annual food spend × income share", "ACS B11001 × BLS CES Table 4700"),
    ("θ_j",        "Pass-through rate",          "1.3.1", "Parameter", "Literature: 0.50–0.85; base = 0.65", "Besanko et al. (2005)"),
    ("s",          "Subsidy amount ($/yr)",      "1.3.2", "Decision variable", "Annual $ the city commits; constrained by B", "City budget"),
    ("Tax_j",      "Annual tax liability",       "1.3.2", "Dataset",   "Annual property/business tax bill for store j", "NYC NYCDB; nycdb.info"),
    ("Δp_j",       "Price reduction ($/basket)", "1.3.1 / 1.3.3", "Derived", "= θ_j · s / Q_j; single scalar per store", "Equation 1.3.2b"),
    ("B",          "Total budget ($/yr)",        "1.4.1", "Parameter (constraint)", "City's max annual commitment", "City budget allocation"),
    ("s*",         "Min effective subsidy",      "1.4.1", "Derived — Goal 1 output", "Smallest s meeting Δp_min and ΔCS_min", "Grid search over ΔCS(s)"),
    ("x_j",        "Store selection binary",     "1.4.2", "Decision variable", "1 if store selected; 0 otherwise", "Gurobi / enumeration output"),
    ("e_j",        "Eligibility indicator",      "1.4.2", "Dataset",   "1 = SNAP-authorized + in CD2 + meets criteria", "USDA SNAP locator + city criteria"),
]
for idx, d in enumerate(ref_rows):
    row = ref_tbl.add_row().cells
    bg = "EBF3FA" if idx % 2 == 0 else "FFFFFF"
    for i, v in enumerate(d):
        row[i].text = v; row[i].paragraphs[0].runs[0].font.size = Pt(8.5)
        set_cell_bg(row[i], bg)
        if i == 3:
            t = v.lower()
            if "parameter" in t:
                row[i].paragraphs[0].runs[0].font.color.rgb = RGBColor(0x17,0x6B,0x24)
                row[i].paragraphs[0].runs[0].bold = True
            elif "dataset" in t:
                row[i].paragraphs[0].runs[0].font.color.rgb = RGBColor(0x7B,0x36,0x00)
                row[i].paragraphs[0].runs[0].bold = True
            elif "decision" in t:
                row[i].paragraphs[0].runs[0].font.color.rgb = RGBColor(0x50,0x00,0x7B)
                row[i].paragraphs[0].runs[0].bold = True
doc.add_paragraph()

# ── SAVE ──────────────────────────────────────────────────────────────────────
doc.save(OUT_PATH)
print(f"Saved: {OUT_PATH}")
