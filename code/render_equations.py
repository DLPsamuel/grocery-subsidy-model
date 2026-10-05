"""
Render model equations as high-resolution images for slides (figures/eq_*.png / .svg).

PNGs have a transparent background, so they sit on any slide colour; SVGs scale without loss.
"""

import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT    = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(ROOT, "figures")
os.makedirs(OUT_DIR, exist_ok=True)

matplotlib.rcParams["mathtext.fontset"] = "cm"   # Computer Modern, matches LaTeX

EQUATIONS = {
    "eq_utility_V_ij": r"$V_{ij} = \alpha_j + \gamma_{sq} \left( sq_j/1000 \right)"
                       r" - \beta_{p,i} b_i p_j - \beta_d d_{ij}$",
}


def render(name, tex, fontsize=40, dpi=600):
    fig = plt.figure(figsize=(0.01, 0.01))
    fig.text(0, 0, tex, fontsize=fontsize, color="black")
    for ext in ("png", "svg"):
        out = os.path.join(OUT_DIR, f"{name}.{ext}")
        fig.savefig(out, dpi=dpi, transparent=True, bbox_inches="tight", pad_inches=0.08)
        print(f"Saved: {out}")
    plt.close(fig)


if __name__ == "__main__":
    for name, tex in EQUATIONS.items():
        render(name, tex)
