"""Delta CS against annual subsidy s at one store, with the CS targets marked. Chris's model and results only.

    python code/plot_cs_vs_subsidy.py   ->  figures/cs_vs_subsidy_targets.png

Curves for FRESH (theta = 0.5), rent (theta = 0.5, 0.75) and the 30% contract come from
results/chris_run1_base/lever_curves.csv. Run 1 does not trace rent at theta = 1 (run 3 has only its
end point), so that curve is computed with Chris's base calibration and the same m.lever_cost_cut call
run_model.lever_curves uses. Minimum subsidies per target use run_model.subsidy_for_targets.
"""
from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.patches import Rectangle
from matplotlib.ticker import FuncFormatter

import model as m
import params as P
import run_model as rm
from data_paths import RESULTS_DIR, ROOT
from make_figures import INK, INK2, SERIES, SURFACE, _money, _style

STORE = "Key Food"
CONTRACT = "30% contract at existing store"
RENT_THETAS = (0.5, 0.75, 1.0)
LINES = (  # (lever, theta, color, label)
    ("FRESH tax break", 0.5, SERIES["FRESH tax break"], "FRESH tax break, θ = 0.5"),
    ("Rent subsidy", 0.5, "#7fd4b0", "Rent subsidy, θ = 0.5"),
    ("Rent subsidy", 0.75, SERIES["Rent subsidy"], "Rent subsidy, θ = 0.75"),
    ("Rent subsidy", 1.0, "#0b5e40", "Rent subsidy, θ = 1 (full pass-through)"),
    (CONTRACT, 1.0, SERIES[CONTRACT], "30% contract, θ = 1"),
)
ZOOM = (600_000, 300_000)
OUT = ROOT / "figures" / "cs_vs_subsidy_targets.png"


def _k(x, _=None):
    return "$0" if x == 0 else _money(x)


def rent_curve_full_pass_through() -> pd.DataFrame:
    mkt = m.load_market()
    prm, alpha = rm.fit(mkt, m.Params())
    st = mkt.stores
    j = int(np.flatnonzero(st["short"] == STORE)[0])
    return pd.DataFrame([rm._row("Rent subsidy", STORE, 1.0, x,
                                 m.lever_cost_cut(mkt, prm, alpha, j, x * st.at[j, "rent"], 1.0)) for x in rm.GRID])


def load() -> tuple[pd.DataFrame, pd.DataFrame]:
    c = pd.read_csv(RESULTS_DIR / "chris_run1_base" / "lever_curves.csv")
    c = c[c["store"] == STORE]
    keep = [(lv, th) for lv, th, *_ in LINES]
    c = c[[(lv, th) in keep for lv, th in zip(c["lever"], c["theta"])]]
    c = pd.concat([c, rent_curve_full_pass_through()], ignore_index=True)
    return c, rm.subsidy_for_targets(c)


def draw(ax, curves, targets, zoom: bool) -> None:
    _style(ax)
    xmax, ymax = ZOOM if zoom else (2.7e6, 2.25e6)
    label_min = 0 if zoom else ZOOM[1]
    for T in P.CS_TARGETS:
        if T < ymax:
            ax.axhline(T, color=INK2, linewidth=0.8, linestyle=(0, (3, 3)), zorder=1)
            if T >= label_min:
                ax.text(xmax * 0.995, T, f"target {_money(T)}", color=INK2, fontsize=8, ha="right", va="bottom")

    for lever, theta, color, label in LINES:
        s = curves[(curves["lever"] == lever) & (curves["theta"] == theta)].sort_values("lever_fraction")
        ax.plot(s["cost"], s["dcs_total"], color=color, linewidth=2.2, label=label, zorder=3)
        hit = targets[(targets["lever"] == lever) & (targets["theta"] == theta) & (targets["reachable"] == "yes")]
        hit = hit[hit["cs_target"] < ymax]
        ax.scatter(hit["min_subsidy"], hit["cs_target"], s=40, color=color, edgecolor=INK, linewidth=0.7, zorder=5)
        if lever == CONTRACT:
            for _, r in hit[hit["cs_target"] >= label_min].iterrows():
                ax.annotate(f"s = {_money(r['min_subsidy'])}", (r["min_subsidy"], r["cs_target"]), xytext=(6, 5),
                            textcoords="offset points", fontsize=7.5, color=INK, fontweight="bold")
        elif zoom:
            end = s.iloc[-1]
            ax.scatter([end["cost"]], [end["dcs_total"]], s=22, color=color, zorder=4)
            below = lever == "FRESH tax break"
            ax.annotate(f"{'FRESH ' if below else ''}θ = {theta:g}: max {_money(end['dcs_total'])}",
                        (end["cost"], end["dcs_total"]), xytext=(4, -9) if below else (6, 0),
                        textcoords="offset points", fontsize=7.5, color=color, va="top" if below else "center",
                        fontweight="bold")

    ax.set_xlim(0, xmax)
    ax.set_ylim(0, ymax)
    ax.xaxis.set_major_formatter(FuncFormatter(_k))
    ax.yaxis.set_major_formatter(FuncFormatter(_k))
    ax.set_xlabel("Annual subsidy s ($/yr)", color=INK2, fontsize=9.5)
    ax.set_ylabel("Change in consumer surplus, all CD2 ($/yr)", color=INK2, fontsize=9.5)
    if not zoom:
        ax.add_patch(Rectangle((0, 0), *ZOOM, fill=False, edgecolor=INK2, linewidth=1, zorder=6))
        ax.text(ZOOM[0], ZOOM[1], " zoom →", color=INK2, fontsize=8, va="bottom")


def table(ax, targets) -> None:
    ax.axis("off")
    cells, colors = [], []
    for lever, theta, color, label in LINES:
        t = targets[(targets["lever"] == lever) & (targets["theta"] == theta)].set_index("cs_target")
        cells.append([label] + [_money(t.at[T, "min_subsidy"]) if t.at[T, "reachable"] == "yes" else "not reachable"
                                for T in P.CS_TARGETS])
        colors.append(color)
    tb = ax.table(cellText=cells, colLabels=["Minimum annual subsidy s to reach ΔCS target"] +
                  [_money(T) for T in P.CS_TARGETS], loc="center", cellLoc="center", colLoc="center",
                  colWidths=[0.3] + [0.1] * len(P.CS_TARGETS))
    tb.auto_set_font_size(False)
    tb.set_fontsize(8.5)
    tb.scale(1, 1.35)
    for (r, c), cell in tb.get_celld().items():
        cell.set_edgecolor("#e4e3df")
        cell.set_facecolor(SURFACE)
        if r == 0:
            cell.set_text_props(color=INK, fontweight="bold")
        else:
            cell.set_text_props(color=colors[r - 1] if c == 0 else
                                (INK2 if cell.get_text().get_text() == "not reachable" else INK),
                                fontweight="bold" if c == 0 else "normal")
        if c == 0:
            cell.set_text_props(ha="left")
            cell.PAD = 0.03


def main() -> None:
    curves, targets = load()
    fig = plt.figure(figsize=(14, 8.6), facecolor=SURFACE)
    gs = fig.add_gridspec(2, 2, height_ratios=(3.2, 1.1), hspace=0.22)
    ax_full, ax_zoom, ax_tab = fig.add_subplot(gs[0, 0]), fig.add_subplot(gs[0, 1]), fig.add_subplot(gs[1, :])
    draw(ax_full, curves, targets, zoom=False)
    draw(ax_zoom, curves, targets, zoom=True)
    table(ax_tab, targets)
    ax_full.set_title("Full range", loc="left", color=INK, fontsize=10.5)
    ax_zoom.set_title(f"Zoom: s up to {_money(ZOOM[0])}", loc="left", color=INK, fontsize=10.5)
    handles, labels = ax_full.get_legend_handles_labels()
    fig.legend(handles, labels, loc="upper left", bbox_to_anchor=(0.01, 0.925), ncol=5, frameon=False, fontsize=8.5,
               labelcolor=INK)
    fig.suptitle(f"Change in consumer surplus against subsidy s at {STORE}\n"
                 "Even at full pass-through the rent subsidy tops out near $243K; the 30% contract reaches every target",
                 x=0.01, ha="left", fontsize=12.5, fontweight="bold", color=INK)
    fig.text(0.01, 0.012, "Dots: minimum annual subsidy that reaches each CS target. The contract pays at least the "
             "store's rent + tax ($326K), so its curve starts with a vertical segment.\nRent θ = 1 is computed with "
             "Chris's base calibration (run 1 does not trace it). Source: Chris run 1 (results/chris_run1_base/).",
             color=INK2, fontsize=7.5)
    fig.subplots_adjust(left=0.06, right=0.985, top=0.86, bottom=0.04, wspace=0.18)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT, dpi=200, facecolor=SURFACE)
    plt.close(fig)
    print(f"Saved {OUT.relative_to(ROOT)}")
    print(targets[targets["reachable"] == "yes"][["lever", "theta", "cs_target", "min_subsidy"]].to_string(index=False))


if __name__ == "__main__":
    main()
