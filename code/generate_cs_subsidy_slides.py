"""
Generate the consumer-surplus / pass-through slide figures in figures/slides/

Stylized supply-and-demand slides showing how a per-unit producer subsidy shifts
supply down, lowers the price and raises consumer surplus, and how the price
change is split between consumers and producers (pass-through, theta).

  cs_1_baseline.png        demand, Supply 1, equilibrium (Q*, P*), original CS shaded
  cs_2_subsidy.png         slide 1 plus Supply 2, the subsidy shift, (Q**, P**) and
                           the CS gain shaded in a second colour
  cs_3_pass_through.png    slide 2 plus the subsidy wedge at Q**, P_S, and brackets
                           splitting the subsidy into consumer and producer shares
  cs_4_theta_high_*.png    theta high (~0.8): most of the subsidy lowers the price
  cs_5_theta_low_*.png     theta low (~0.2): barely any of the subsidy lowers the price
                           (* = demand | supply | both: which curve's slope changes)

All images share the same canvas, axis limits and margins (no bbox_inches="tight")
so flipping between the slides reads as an animation.
"""

import os
from dataclasses import dataclass

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon

# ── paths ──────────────────────────────────────────────────────────────────────
ROOT    = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(ROOT, "figures", "slides")
os.makedirs(OUT_DIR, exist_ok=True)

# ── market parameters (linear: P = intercept + slope * Q) ─────────────────────
Q_STAR, P_STAR = 4.0, 7.0     # pre-subsidy equilibrium, shared by every scenario
SUBSIDY        = 3.0          # per-unit subsidy; Supply 2 = Supply 1 shifted down

Q_MAX, P_MAX = 10.0, 12.0     # axis extent


@dataclass(frozen=True)
class Market:
    d_int: float
    d_slope: float
    s_int: float
    s_slope: float
    subsidy: float = SUBSIDY

    @classmethod
    def through_star(cls, d_slope, s_slope):
        """Curves with the given slopes that cross at (Q_STAR, P_STAR)."""
        return cls(P_STAR - d_slope * Q_STAR, d_slope,
                   P_STAR - s_slope * Q_STAR, s_slope)

    def _equilibrium(self, s_int):
        q = (self.d_int - s_int) / (self.s_slope - self.d_slope)
        return q, self.d_int + self.d_slope * q

    @property
    def eq1(self):
        return self._equilibrium(self.s_int)

    @property
    def eq2(self):
        return self._equilibrium(self.s_int - self.subsidy)

    @property
    def p_s(self):
        """Price producers receive after the subsidy (consumer price + subsidy)."""
        return self.eq2[1] + self.subsidy

    @property
    def theta(self):
        """Share of the subsidy that lowers the consumer price."""
        return (self.eq1[1] - self.eq2[1]) / self.subsidy


BASE = Market.through_star(d_slope=-1.0, s_slope=1.0)

# ── style ──────────────────────────────────────────────────────────────────────
FIGSIZE = (40 / 3, 7.5)       # 16:9
DPI     = 300
MARGINS = dict(left=0.27, right=0.86, bottom=0.13, top=0.94)

FONT_AXIS  = 26
FONT_LABEL = 22
FONT_TICK  = 22
FONT_NOTE  = 20
LW_CURVE   = 3.5
LW_GUIDE   = 1.8

C_DEMAND   = "#1a3a5c"
C_SUPPLY1  = "#555555"
C_SUPPLY2  = "#e65100"
C_CS       = "#bcd4ee"
C_CS_TEXT  = "#1a3a5c"
C_GAIN     = "#fdd3b0"
C_GAIN_TXT = "#b23c00"
C_GUIDE    = "#333333"
C_WEDGE    = "#1565c0"

P_LABEL_GAP = 0.8             # min vertical gap between P tick labels (data units)
Q_LABEL_GAP = 1.0             # below this Q*/Q** labels are pushed apart

# curve-end labels: (which end of the clipped line, text alignment)
DEFAULT_LABELS = {"demand": ("end", "left"), "supply1": ("end", "left"),
                  "supply2": ("end", "left")}


def line_points(intercept, slope, q_lo=0.0, q_hi=Q_MAX):
    """Endpoints of a line clipped to the plotting box [0, Q_MAX] x [0, P_MAX]."""
    qs = []
    for q in (q_lo, q_hi):
        p = intercept + slope * q
        if p > P_MAX:
            q = (P_MAX - intercept) / slope
        elif p < 0:
            q = -intercept / slope
        qs.append(q)
    return qs, [intercept + slope * q for q in qs]


def draw_axes(ax):
    ax.set_xlim(0, Q_MAX)
    ax.set_ylim(0, P_MAX)
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.set_xticks([])
    ax.set_yticks([])
    arrow = dict(arrowstyle="-|>", color="black", lw=2.2, mutation_scale=28)
    ax.annotate("", xy=(Q_MAX, 0), xytext=(0, 0), arrowprops=arrow,
                annotation_clip=False, zorder=6)
    ax.annotate("", xy=(0, P_MAX), xytext=(0, 0), arrowprops=arrow,
                annotation_clip=False, zorder=6)
    ax.text(Q_MAX, -0.55, "Q", fontsize=FONT_AXIS, ha="center", va="top")
    ax.text(-0.25, P_MAX, "P", fontsize=FONT_AXIS, ha="right", va="center")


def draw_guides(ax, q, p, color):
    ax.plot([q, q], [0, p], ls="--", color=C_GUIDE, lw=LW_GUIDE, zorder=2)
    ax.plot([0, q], [p, p], ls="--", color=C_GUIDE, lw=LW_GUIDE, zorder=2)
    ax.plot(q, p, "o", color=color, markersize=13, markeredgecolor="white",
            markeredgewidth=1.5, zorder=5)


def p_tick(ax, y, label):
    ax.text(-0.15, y, label, fontsize=FONT_TICK, ha="right", va="center")


def q_tick(ax, x, label, ha="center"):
    ax.text(x, -0.3, label, fontsize=FONT_TICK, ha=ha, va="top")


def draw_curve(ax, intercept, slope, color, label, spec):
    anchor, ha = spec
    qs, ps = line_points(intercept, slope)
    ax.plot(qs, ps, color=color, lw=LW_CURVE, solid_capstyle="round", zorder=3)
    i = 1 if anchor == "end" else 0
    dx = 0.15 if ha == "left" else -0.15
    ax.text(qs[i] + dx, ps[i], label, fontsize=FONT_LABEL, color=color,
            fontweight="bold", ha=ha, va="center")


def draw_bracket(ax, p_lo, p_hi, text, color):
    """Square bracket left of the P axis spanning [p_lo, p_hi], label to its left."""
    x, tick, inset = -1.25, 0.2, 0.06
    lo, hi = p_lo + inset, p_hi - inset
    ax.plot([x + tick, x, x, x + tick], [hi, hi, lo, lo], color=color, lw=2.4,
            solid_joinstyle="miter", clip_on=False, zorder=5)
    ax.text(x - 0.2, (p_lo + p_hi) / 2, text, fontsize=FONT_NOTE, color=color,
            fontweight="bold", ha="right", va="center", linespacing=1.1)


def draw_theta_note(ax, mkt, level):
    body = {
        "high": "most of the subsidy\nlowers the price\nconsumers pay",
        "low":  "barely any of the\nsubsidy lowers the\nprice consumers pay",
    }[level]
    x, y = -4.4, 12.6
    ax.text(x, y, f"θ {level} (≈ {mkt.theta:.1f})", fontsize=FONT_LABEL,
            color=C_DEMAND, fontweight="bold", ha="left", va="top")
    ax.text(x, y - 0.85, body, fontsize=FONT_NOTE, color=C_DEMAND,
            ha="left", va="top", linespacing=1.15)


def draw(ax, mkt, show_cs, show_subsidy, show_split, theta_text=None,
         show_shift=True, labels=None):
    labels = {**DEFAULT_LABELS, **(labels or {})}
    q1, p1 = mkt.eq1
    q2, p2 = mkt.eq2
    draw_axes(ax)

    if show_cs:
        # original consumer surplus: area under demand, above P*
        ax.add_patch(Polygon([(0, mkt.d_int), (0, p1), (q1, p1)], closed=True,
                             facecolor=C_CS, edgecolor="none", zorder=1))
        ax.text(0.22 * q1, p1 + 0.65 * (mkt.d_int - p1), "CS", fontsize=FONT_LABEL,
                color=C_CS_TEXT, fontweight="bold", ha="center", va="center",
                zorder=5)

    draw_curve(ax, mkt.d_int, mkt.d_slope, C_DEMAND, "Demand", labels["demand"])
    draw_curve(ax, mkt.s_int, mkt.s_slope, C_SUPPLY1, "Supply 1", labels["supply1"])
    draw_guides(ax, q1, p1, C_SUPPLY1)

    if not show_subsidy:
        p_tick(ax, p1, "$P^{*}$")
        q_tick(ax, q1, "$Q^{*}$")
        return

    # consumer surplus gain: strip under demand between P* and P**
    ax.add_patch(Polygon([(0, p1), (q1, p1), (q2, p2), (0, p2)], closed=True,
                         facecolor=C_GAIN, edgecolor="none", zorder=1))
    if show_cs:
        ax.text(q1 / 3, (p1 + p2) / 2, "Gain in CS", fontsize=FONT_LABEL,
                color=C_GAIN_TXT, fontweight="bold", ha="center", va="center",
                zorder=5)

    draw_curve(ax, mkt.s_int - mkt.subsidy, mkt.s_slope, C_SUPPLY2, "Supply 2",
               labels["supply2"])

    if show_shift:
        # subsidy shift: vertical arrow from Supply 1 down to Supply 2
        q_arrow = 7.0
        p_top = mkt.s_int + mkt.s_slope * q_arrow
        p_bot = p_top - mkt.subsidy
        ax.annotate("", xy=(q_arrow, p_bot + 0.15), xytext=(q_arrow, p_top - 0.15),
                    arrowprops=dict(arrowstyle="-|>", color=C_SUPPLY2, lw=2.8,
                                    mutation_scale=30),
                    zorder=4)
        ax.text(q_arrow + 0.2, p_top - 0.7, "Subsidy", fontsize=FONT_LABEL,
                color=C_SUPPLY2, fontweight="bold", ha="left", va="center")

    draw_guides(ax, q2, p2, C_SUPPLY2)

    # tick labels, nudged apart when equilibria are close
    p_tick(ax, p1, "$P^{*}$")
    p_tick(ax, min(p2, p1 - P_LABEL_GAP), "$P^{**}$")
    if q2 - q1 < Q_LABEL_GAP:
        q_tick(ax, q1 + 0.05, "$Q^{*}$", ha="right")
        q_tick(ax, q2 - 0.05, "$Q^{**}$", ha="left")
    else:
        q_tick(ax, q1, "$Q^{*}$")
        q_tick(ax, q2, "$Q^{**}$")

    if show_split:
        p_s = mkt.p_s
        ax.plot([0, q2], [p_s, p_s], ls="--", color=C_GUIDE, lw=LW_GUIDE, zorder=2)
        ax.plot([q2, q2], [p2, p_s], color=C_WEDGE, lw=4.0,
                solid_capstyle="butt", zorder=4)
        ax.plot(q2, p_s, "o", color=C_SUPPLY1, markersize=10,
                markeredgecolor="white", markeredgewidth=1.5, zorder=5)
        p_tick(ax, max(p_s, p1 + P_LABEL_GAP), "$P_S$")
        draw_bracket(ax, p1, p_s, "Producers\nreceive more", C_SUPPLY1)
        draw_bracket(ax, p2, p1, "Consumers\npay less", C_GAIN_TXT)

    if theta_text:
        draw_theta_note(ax, mkt, theta_text)


def render(filename, mkt=BASE, **kwargs):
    fig, ax = plt.subplots(figsize=FIGSIZE, dpi=DPI)
    fig.subplots_adjust(**MARGINS)
    draw(ax, mkt, **kwargs)
    out = os.path.join(OUT_DIR, filename)
    fig.savefig(out, dpi=DPI, facecolor="white")
    plt.close(fig)
    print(f"Saved: {out}")


# theta scenarios: (version, level) -> market and curve-label placement.
# theta = |d_slope| / (|d_slope| + s_slope); every pair keeps (Q*, P*) fixed.
THETA_SCENARIOS = {
    ("demand", "high"): (Market.through_star(-4.0, 1.0),
                         {"demand": ("start", "left")}),
    ("demand", "low"):  (Market.through_star(-0.25, 1.0), {}),
    ("supply", "high"): (Market.through_star(-1.0, 0.25), {}),
    ("supply", "low"):  (Market.through_star(-1.0, 4.0),
                         {"supply1": ("end", "right")}),
    ("both", "high"):   (Market.through_star(-2.0, 0.5),
                         {"demand": ("start", "left")}),
    ("both", "low"):    (Market.through_star(-0.5, 2.0),
                         {"supply1": ("end", "right")}),
}


if __name__ == "__main__":
    q1, p1 = BASE.eq1
    q2, p2 = BASE.eq2
    print(f"Base: Q* = {q1:g}, P* = {p1:g};  Q** = {q2:g}, P** = {p2:g};  "
          f"P_S = {BASE.p_s:g};  theta = {BASE.theta:.2f}")
    render("cs_1_baseline.png",     show_cs=True, show_subsidy=False, show_split=False)
    render("cs_2_subsidy.png",      show_cs=True, show_subsidy=True,  show_split=False)
    render("cs_3_pass_through.png", show_cs=True, show_subsidy=True,  show_split=True)

    for (version, level), (mkt, labels) in THETA_SCENARIOS.items():
        slide = 4 if level == "high" else 5
        print(f"{version:>6} / {level:<4}: theta = {mkt.theta:.2f}")
        render(f"cs_{slide}_theta_{level}_{version}.png", mkt=mkt,
               show_cs=False, show_subsidy=True, show_split=True,
               theta_text=level, show_shift=False, labels=labels)
