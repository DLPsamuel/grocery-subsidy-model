"""
Convert MAIN_NYC_Grocery_Subsidy_Model_Specification.md to .docx

Strategy:
- Display equations $$...$$  → rendered PNG via matplotlib mathtext, embedded centered
- Inline math $...$          → converted to Unicode/plain notation
- Markdown tables            → python-docx Table objects
- Headings #/##/###/####    → python-docx Heading styles 1-4
- Horizontal rules ---       → thin border paragraph
- Images ![alt](path)        → embedded image
- Mermaid code blocks        → plain italic note
- **bold**, *italic*         → python-docx run formatting
"""

import os
import re
import io
import sys
import textwrap
import tempfile
import hashlib

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MD_PATH  = os.path.join(ROOT, "MAIN_NYC_Grocery_Subsidy_Model_Specification.md")
OUT_PATH = os.path.join(ROOT, "MAIN_NYC_Grocery_Subsidy_Model_Specification.docx")
FIG_DIR  = os.path.join(ROOT, "figures")
EQ_CACHE = os.path.join(ROOT, "figures", "_eq_cache")
os.makedirs(EQ_CACHE, exist_ok=True)

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from docx import Document
from docx.shared import Inches, Pt, RGBColor, Emu
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
import copy

# ── equation rendering ─────────────────────────────────────────────────────────

def preprocess_latex(src: str) -> str:
    """Simplify LaTeX for matplotlib mathtext (subset of full LaTeX)."""
    s = src.strip()
    # Remove unsupported layout commands
    s = re.sub(r'\\displaystyle\b', '', s)
    s = re.sub(r'\\textstyle\b', '', s)
    s = re.sub(r'\\scriptstyle\b', '', s)
    s = re.sub(r'\\boldsymbol\{([^}]+)\}', r'\1', s)
    # Replace \dfrac with \frac
    s = re.sub(r'\\dfrac', r'\\frac', s)
    # Replace \text{...} with \mathrm{...}
    s = re.sub(r'\\text\{([^}]+)\}', r'\\mathrm{\1}', s)
    # Replace \left( \right) with ( )
    s = re.sub(r'\\left\(', r'(', s)
    s = re.sub(r'\\right\)', r')', s)
    s = re.sub(r'\\left\[', r'[', s)
    s = re.sub(r'\\right\]', r']', s)
    s = re.sub(r'\\left\\', r'', s)
    s = re.sub(r'\\right\\', r'', s)
    s = re.sub(r'\\left\.', r'', s)
    s = re.sub(r'\\right\.', r'', s)
    # Replace \bigl( \bigr) etc.
    s = re.sub(r'\\big[lr]?\(', r'(', s)
    s = re.sub(r'\\big[lr]?\)', r')', s)
    s = re.sub(r'\\Big[lr]?\(', r'(', s)
    s = re.sub(r'\\Big[lr]?\)', r')', s)
    s = re.sub(r'\\bigl\[', r'[', s)
    s = re.sub(r'\\bigr\]', r']', s)
    # Replace \quad, \qquad with spaces
    s = re.sub(r'\\qquad', r'\\;\\;', s)
    s = re.sub(r'\\quad', r'\\;', s)
    # Replace \! (negative thin space) with nothing
    s = re.sub(r'\\!', r'', s)
    # Replace \; \: \, with spaces (matplotlib handles some)
    # keep them — matplotlib supports \;
    # Replace specific macros
    s = re.sub(r'\\mathrm\{HH\}', r'\\mathrm{HH}', s)
    s = re.sub(r'\\approx', r'\\approx', s)
    # Remove \! from \ln\!
    s = re.sub(r'(\\[a-z]+)\\!', r'\1', s)
    # Remove \noindent etc.
    s = re.sub(r'\\noindent\b', '', s)
    # Simplify alignment: replace \qquad (used for spacing equations)
    # Split multi-part equations at \qquad → just use spaces
    return s


def render_equation(latex_src: str) -> str:
    """Render a LaTeX display equation to PNG; return path."""
    key = hashlib.md5(latex_src.encode()).hexdigest()[:12]
    path = os.path.join(EQ_CACHE, f"eq_{key}.png")
    if os.path.exists(path):
        return path

    # wrap in $...$ for matplotlib mathtext
    expr = preprocess_latex(latex_src)
    if not expr.startswith("$"):
        expr = f"${expr}$"

    fig = plt.figure(figsize=(0.01, 0.01))
    try:
        t = fig.text(0, 0, expr, fontsize=13)
        # measure bounding box
        fig.canvas.draw()
        bbox = t.get_window_extent(renderer=fig.canvas.get_renderer())
        w_in = max(bbox.width / 150 + 0.3, 1.0)
        h_in = max(bbox.height / 150 + 0.2, 0.4)
    except Exception:
        w_in, h_in = 5.0, 0.6
    plt.close(fig)

    fig = plt.figure(figsize=(w_in, h_in))
    fig.patch.set_alpha(0)
    try:
        fig.text(0.5, 0.5, expr, fontsize=13, ha="center", va="center")
    except Exception as e:
        # fallback: render as plain text if LaTeX fails
        clean = re.sub(r'\\[a-zA-Z]+', '', latex_src).replace('{','').replace('}','').replace('\\','')
        fig.text(0.5, 0.5, clean, fontsize=11, ha="center", va="center", color="#333")
    fig.savefig(path, dpi=150, bbox_inches="tight", transparent=True)
    plt.close(fig)
    return path


# ── inline math simplification ─────────────────────────────────────────────────
# Convert $...$ to a readable plain-text approximation

_SUBS = [
    (r"\\beta_\{\\text\{sqft\}\}", "β_sqft"),
    (r"\\beta_\{p,i\}", "β_p,i"),
    (r"\\beta_\{d,i\}", "β_d,i"),
    (r"\\text\{sqft\}_j", "sqft_j"),
    (r"\\text\{sqft\}", "sqft"),
    (r"\\bar\{f\}_g", "f̄_g"),
    (r"\\bar\{f\}", "f̄"),
    (r"\\kappa_g", "κ_g"),
    (r"\\kappa_j", "κ_j"),
    (r"\\kappa_\{\\text\{low\}\}", "κ_low"),
    (r"\\kappa_\{\\text\{base\}\}", "κ_base"),
    (r"\\kappa_\{\\text\{high\}\}", "κ_high"),
    (r"\\kappa", "κ"),
    (r"\\theta", "θ"),
    (r"\\Delta p_\{j,g\}", "Δp_j,g"),
    (r"\\Delta p_j", "Δp_j"),
    (r"\\Delta CS", "ΔCS"),
    (r"\\Delta", "Δ"),
    (r"\\beta", "β"),
    (r"\\alpha", "α"),
    (r"\\sigma", "σ"),
    (r"\\tau", "τ"),
    (r"\\lambda", "λ"),
    (r"\\gamma", "γ"),
    (r"\\sum_\{[^}]*\}", "Σ"),
    (r"\\sum", "Σ"),
    (r"\\ln", "ln"),
    (r"\\max", "max"),
    (r"\\min", "min"),
    (r"\\exp", "exp"),
    (r"\\frac\{([^}]*)\}\{([^}]*)\}", r"\1/\2"),
    (r"\{", ""), (r"\}", ""),
    (r"\\", ""),
    (r"_", "_"), (r"\^", "^"),
]

def inline_math_to_text(m):
    """Convert inline $...$ to readable plain text."""
    src = m.group(1)
    result = src
    for pat, rep in _SUBS:
        result = re.sub(pat, rep, result)
    return result


def process_inline(text: str) -> str:
    """Replace $...$ with plain text approximation."""
    return re.sub(r'\$([^$\n]+?)\$', inline_math_to_text, text)


def strip_md_formatting(text: str) -> str:
    """Remove markdown formatting markers, leaving plain text."""
    text = process_inline(text)
    text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
    text = re.sub(r'\*(.+?)\*', r'\1', text)
    text = re.sub(r'`([^`]+)`', r'\1', text)
    return text


# ── docx helpers ───────────────────────────────────────────────────────────────

def add_heading(doc, text, level):
    text = strip_md_formatting(text)
    doc.add_heading(text, level=level)


def add_equation_image(doc, latex_src):
    """Render equation and add as a centered paragraph with image."""
    path = render_equation(latex_src)
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run()
    # scale: max width 5.5 inches
    run.add_picture(path, width=Inches(min(5.5, 5.5)))
    p.paragraph_format.space_before = Pt(4)
    p.paragraph_format.space_after  = Pt(4)


def add_formatted_paragraph(doc, text, style=None):
    """Add a paragraph, applying **bold** and `code` runs, inline math as plain."""
    text = process_inline(text)
    if style:
        p = doc.add_paragraph(style=style)
    else:
        p = doc.add_paragraph()

    # Split on **bold** and `code`
    pattern = re.compile(r'(\*\*[^*]+\*\*|`[^`]+`|\*[^*]+\*)')
    parts = pattern.split(text)
    for part in parts:
        if part.startswith('**') and part.endswith('**'):
            run = p.add_run(part[2:-2])
            run.bold = True
        elif part.startswith('`') and part.endswith('`'):
            run = p.add_run(part[1:-1])
            run.font.name = 'Courier New'
            run.font.size = Pt(9)
        elif part.startswith('*') and part.endswith('*'):
            run = p.add_run(part[1:-1])
            run.italic = True
        else:
            p.add_run(part)
    return p


def parse_md_table(lines):
    """Parse markdown table lines into (headers, rows)."""
    headers = []
    rows = []
    for i, line in enumerate(lines):
        line = line.strip()
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if i == 0:
            headers = cells
        elif re.match(r'^[\s|:-]+$', line):
            continue  # separator row
        else:
            rows.append(cells)
    return headers, rows


def add_md_table(doc, headers, rows):
    """Add a formatted table to the docx."""
    n_cols = max(len(headers), max((len(r) for r in rows), default=0))
    if n_cols == 0:
        return
    # normalize column count
    headers = (headers + [""] * n_cols)[:n_cols]
    rows = [(r + [""] * n_cols)[:n_cols] for r in rows]

    table = doc.add_table(rows=1 + len(rows), cols=n_cols)
    table.style = "Table Grid"

    # header row
    hdr_cells = table.rows[0].cells
    for j, hdr in enumerate(headers):
        hdr_cells[j].text = strip_md_formatting(hdr)
        for run in hdr_cells[j].paragraphs[0].runs:
            run.bold = True
        # shade header
        tc = hdr_cells[j]._tc
        tcPr = tc.get_or_add_tcPr()
        shd = OxmlElement('w:shd')
        shd.set(qn('w:val'), 'clear')
        shd.set(qn('w:color'), 'auto')
        shd.set(qn('w:fill'), 'D9E1F2')
        tcPr.append(shd)

    # data rows
    for i, row in enumerate(rows):
        row_cells = table.rows[i + 1].cells
        for j, cell in enumerate(row):
            row_cells[j].text = strip_md_formatting(cell)

    doc.add_paragraph()  # spacing after table


def add_hr(doc):
    """Add a thin horizontal rule paragraph."""
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(2)
    p.paragraph_format.space_after  = Pt(2)
    pPr = p._p.get_or_add_pPr()
    pBdr = OxmlElement('w:pBdr')
    bottom = OxmlElement('w:bottom')
    bottom.set(qn('w:val'), 'single')
    bottom.set(qn('w:sz'),  '6')
    bottom.set(qn('w:space'), '1')
    bottom.set(qn('w:color'), '999999')
    pBdr.append(bottom)
    pPr.append(pBdr)


# ── main parser / converter ────────────────────────────────────────────────────

def convert(md_path, out_path):
    with open(md_path, encoding="utf-8") as f:
        content = f.read()

    doc = Document()

    # set normal font
    style = doc.styles["Normal"]
    style.font.name = "Calibri"
    style.font.size = Pt(11)

    # narrow margins
    from docx.shared import Inches
    for section in doc.sections:
        section.top_margin    = Inches(1.0)
        section.bottom_margin = Inches(1.0)
        section.left_margin   = Inches(1.2)
        section.right_margin  = Inches(1.2)

    lines = content.splitlines()
    i = 0
    total = len(lines)

    while i < total:
        line = lines[i]

        # ── Heading ────────────────────────────────────────────────────────────
        hm = re.match(r'^(#{1,4})\s+(.*)', line)
        if hm:
            level = len(hm.group(1))
            text  = hm.group(2)
            add_heading(doc, text, level)
            i += 1
            continue

        # ── Horizontal rule ────────────────────────────────────────────────────
        if re.match(r'^-{3,}\s*$', line):
            add_hr(doc)
            i += 1
            continue

        # ── Display math $$...$$ (possibly multiline) ──────────────────────────
        if line.strip().startswith("$$"):
            eq_lines = []
            # same-line closing $$
            rest = line.strip()[2:]
            if rest.endswith("$$") and len(rest) > 2:
                add_equation_image(doc, rest[:-2].strip())
                i += 1
                continue
            # else gather lines until closing $$
            i += 1
            while i < total:
                if lines[i].strip() == "$$":
                    i += 1
                    break
                eq_lines.append(lines[i])
                i += 1
            latex = "\n".join(eq_lines).strip()
            add_equation_image(doc, latex)
            continue

        # ── Mermaid / code block ───────────────────────────────────────────────
        if line.strip().startswith("```"):
            lang = line.strip()[3:].strip()
            block_lines = []
            i += 1
            while i < total and not lines[i].strip().startswith("```"):
                block_lines.append(lines[i])
                i += 1
            i += 1  # skip closing ```
            if lang == "mermaid":
                p = doc.add_paragraph()
                run = p.add_run("[Causal Chain Diagram]")
                run.italic = True
                run.font.color.rgb = RGBColor(0x55, 0x55, 0x55)
            else:
                for bl in block_lines:
                    p = doc.add_paragraph(style="No Spacing")
                    run = p.add_run(bl)
                    run.font.name = "Courier New"
                    run.font.size = Pt(9)
            continue

        # ── Markdown table ─────────────────────────────────────────────────────
        if line.strip().startswith("|"):
            table_lines = []
            while i < total and lines[i].strip().startswith("|"):
                table_lines.append(lines[i])
                i += 1
            headers, rows = parse_md_table(table_lines)
            if headers or rows:
                add_md_table(doc, headers, rows)
            continue

        # ── Image ──────────────────────────────────────────────────────────────
        img_m = re.match(r'!\[([^\]]*)\]\(([^)]+)\)', line.strip())
        if img_m:
            alt  = img_m.group(1)
            path = img_m.group(2)
            abs_path = os.path.join(ROOT, path.replace("/", os.sep))
            if os.path.exists(abs_path):
                p = doc.add_paragraph()
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                run = p.add_run()
                run.add_picture(abs_path, width=Inches(5.5))
                cap = doc.add_paragraph(alt)
                cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
                cap.runs[0].italic = True
                cap.runs[0].font.size = Pt(9)
            else:
                p = doc.add_paragraph(f"[Image: {alt}]")
                p.runs[0].italic = True
            i += 1
            continue

        # ── Blockquote ─────────────────────────────────────────────────────────
        if line.strip().startswith(">"):
            text = line.strip().lstrip(">").strip()
            p = add_formatted_paragraph(doc, text)
            p.paragraph_format.left_indent = Inches(0.4)
            pPr = p._p.get_or_add_pPr()
            pBdr = OxmlElement('w:pBdr')
            left = OxmlElement('w:left')
            left.set(qn('w:val'), 'single')
            left.set(qn('w:sz'), '6')
            left.set(qn('w:space'), '20')
            left.set(qn('w:color'), '4472C4')
            pBdr.append(left)
            pPr.append(pBdr)
            i += 1
            continue

        # ── Bullet list ────────────────────────────────────────────────────────
        if re.match(r'^[-*]\s+', line):
            text = re.sub(r'^[-*]\s+', '', line)
            p = add_formatted_paragraph(doc, text, style="List Bullet")
            i += 1
            continue

        # ── Numbered list ──────────────────────────────────────────────────────
        if re.match(r'^\d+\.\s+', line):
            text = re.sub(r'^\d+\.\s+', '', line)
            p = add_formatted_paragraph(doc, text, style="List Number")
            i += 1
            continue

        # ── Blank line ─────────────────────────────────────────────────────────
        if not line.strip():
            i += 1
            continue

        # ── Regular paragraph ──────────────────────────────────────────────────
        add_formatted_paragraph(doc, line)
        i += 1

    doc.save(out_path)
    print(f"Saved: {out_path}")


if __name__ == "__main__":
    print("Rendering equations and building docx...")
    convert(MD_PATH, OUT_PATH)
