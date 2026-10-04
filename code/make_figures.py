"""Figures for the presentation, from the outputs of code/run_model.py.

    python code/make_figures.py

  results/chris_run1_base/fig_subsidy_vs_cs.png  Delta CS against annual subsidy, one line per lever
  results/chris_run1_base/fig_who_gains_map.png  Delta CS per household by tract: N.Y.C. Groceries
                                           vs the same 30% contract at Key Food
Colors: categorical slots 1-4 of the dataviz reference palette (validated; aqua and yellow
sit below 3:1 on the surface, so every line is direct-labelled and the CSVs are the table view).
"""
from __future__ import annotations

import geopandas as gpd
import matplotlib

matplotlib.use("Agg")
matplotlib.rcParams["text.parse_math"] = False  # "$" is currency here, not math mode
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib import patheffects  # noqa: E402
from matplotlib.colors import LinearSegmentedColormap  # noqa: E402
from matplotlib.ticker import FuncFormatter  # noqa: E402

import params as P  # noqa: E402
from data_paths import GEO_DIR, RESULTS_DIR, STORES_DIR  # noqa: E402

SURFACE, INK, INK2, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#e4e3df"
SERIES = {  # fixed order: slot 1..4
    "N.Y.C. Groceries (new store)": "#2a78d6",
    "30% contract at existing store": "#eb6834",
    "Rent subsidy": "#1baf7a",
    "FRESH tax break": "#eda100",
}
BLUES = ["#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95", "#0d366b"]


def _money(x, _=None):
    return f"${x / 1e6:.1f}M" if x >= 1e6 else f"${x / 1e3:.0f}K"


def _style(ax):
    ax.set_facecolor(SURFACE)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(GRID)
    ax.tick_params(colors=INK2, labelsize=9)
    ax.grid(True, color=GRID, linewidth=0.6)
    ax.set_axisbelow(True)


def subsidy_vs_cs() -> None:
    c = pd.read_csv(RESULTS_DIR / "chris_run1_base" / "lever_curves.csv")
    c = c[c["theta"].isin([P.THETA_BASE, P.THETA_CONTRACT])]
    fig, ax = plt.subplots(figsize=(9, 5.4), facecolor=SURFACE)
    _style(ax)
    lim = (5e3, 9e6)
    ax.plot(lim, lim, color=INK2, linewidth=1, linestyle=(0, (4, 3)))
    ax.text(1.1e4, 1.45e4, "$1 of benefit per $1", color=INK2, fontsize=8.5, ha="left", rotation=33)
    for lever, color in SERIES.items():
        lc = c[c["lever"] == lever]
        store = lc.groupby("store")["dcs_total"].max().idxmax()  # store with the largest reach
        s = lc[(lc["store"] == store) & (lc["dcs_total"] > 0)].sort_values("cost")
        ax.plot(s["cost"], s["dcs_total"], color=color, linewidth=2, solid_capstyle="round")
        end = s.iloc[-1]
        ax.scatter([end["cost"]], [end["dcs_total"]], s=46, color=color, edgecolor=SURFACE, linewidth=2, zorder=3)
        label = {
            "N.Y.C. Groceries (new store)": "N.Y.C. Groceries, 30% off\n(new store, discount gain only)",
            "30% contract at existing store": f"30% contract at an existing store\n({store})",
            "Rent subsidy": f"Rent subsidy, θ = {P.THETA_BASE}\n({store}; cap = all its rent)",
            "FRESH tax break": f"FRESH tax break, θ = {P.THETA_BASE}\n({store}; cap = all its property tax)",
        }[lever]
        offset, ha, va = {
            "N.Y.C. Groceries (new store)": ((10, -6), "left", "top"),
            "30% contract at existing store": ((-10, 10), "right", "bottom"),
            "Rent subsidy": ((-10, 10), "right", "bottom"),
            "FRESH tax break": ((10, -6), "left", "top"),
        }[lever]
        ax.annotate(label, (end["cost"], end["dcs_total"]), xytext=offset, textcoords="offset points",
                    fontsize=8.5, color=INK, ha=ha, va=va)
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlim(*lim)
    ax.set_ylim(2e3, 9e6)
    ax.xaxis.set_major_formatter(FuncFormatter(_money))
    ax.yaxis.set_major_formatter(FuncFormatter(_money))
    ax.set_xlabel("Annual public cost (subsidy, $/yr, log scale)", color=INK2, fontsize=9.5)
    ax.set_ylabel("Consumer surplus gain, all CD2 ($/yr, log scale)", color=INK2, fontsize=9.5)
    ax.set_title("Tax and rent breaks run out before they reach large gains;\n"
                 "contracted discounts keep going at about $0.81 per $1",
                 loc="left", color=INK, fontsize=12, fontweight="bold")
    fig.text(0.01, 0.01, "Each line: the store where the lever reaches furthest. N.Y.C. Groceries counts the discount's gain only. "
             "Source: Chris run 1 (code/run_model.py).", color=INK2, fontsize=7.5)
    fig.tight_layout(rect=(0, 0.03, 1, 1))
    fig.savefig(RESULTS_DIR / "chris_run1_base" / "fig_subsidy_vs_cs.png", dpi=200, facecolor=SURFACE)
    plt.close(fig)


def who_gains_map() -> None:
    t = pd.read_csv(RESULTS_DIR / "chris_run1_base" / "dcs_by_tract.csv")
    tr = t.groupby("tract_id")[["n", "dcs_nycg", "dcs_keyfood"]].sum()
    tr["nycg"] = tr["dcs_nycg"] / tr["n"]
    tr["keyfood"] = tr["dcs_keyfood"] / tr["n"]
    geo = gpd.read_file(GEO_DIR / "bronx_cd2_tracts.geojson")
    geo["tract_id"] = geo["geoid"].astype("int64")
    geo = geo.merge(tr, left_on="tract_id", right_index=True, how="left")
    stores = pd.read_csv(STORES_DIR / "large_grocery_stores_cd2.csv", encoding="utf-8-sig")
    kf = stores[stores["dba_name"] == "KEY FOOD"].iloc[0]
    sites = {"nycg": (-73.88995, 40.81459, "N.Y.C. Groceries\n(1215 Spofford Ave)"),
             "keyfood": (kf["longitude"], kf["latitude"], "Key Food\n(1050 Westchester Ave)")}
    vmax = float(tr[["nycg", "keyfood"]].max().max())
    cmap = LinearSegmentedColormap.from_list("blues", BLUES)
    fig, axes = plt.subplots(1, 2, figsize=(11, 6), facecolor=SURFACE)
    for ax, (col, title) in zip(axes, (("nycg", "30% off at the new N.Y.C. Groceries store"),
                                       ("keyfood", "Same 30% contract at Key Food"))):
        ax.set_facecolor(SURFACE)
        geo[geo[col].isna()].plot(ax=ax, color=SURFACE, edgecolor=GRID, hatch="///", linewidth=0.6)
        geo[geo[col].notna()].plot(ax=ax, column=col, cmap=cmap, vmin=0, vmax=vmax, edgecolor=SURFACE, linewidth=1.2)
        x, y, label = sites[col]
        ax.scatter([x], [y], marker="*", s=260, color=INK, edgecolor=SURFACE, linewidth=1.5, zorder=3)
        ax.annotate(label, (x, y), xytext=(8, 8), textcoords="offset points", fontsize=8.5, color=INK,
                    path_effects=[patheffects.withStroke(linewidth=3, foreground=SURFACE)])
        tot = tr[f"dcs_{col}"].sum()
        ax.set_title(f"{title}\nTotal {_money(tot)}/yr · mean ${tot / tr['n'].sum():,.0f} per household",
                     loc="left", fontsize=10.5, color=INK)
        ax.set_axis_off()
    sm = plt.cm.ScalarMappable(cmap=cmap, norm=plt.Normalize(0, vmax))
    cb = fig.colorbar(sm, ax=axes, orientation="horizontal", fraction=0.04, pad=0.02, shrink=0.5)
    cb.ax.xaxis.set_major_formatter(FuncFormatter(lambda x, _: f"${x:.0f}"))
    cb.set_label("Consumer surplus gain per household ($/yr)", color=INK2, fontsize=9)
    cb.outline.set_visible(False)
    cb.ax.tick_params(colors=INK2, labelsize=8.5)
    fig.suptitle("Where the discount sits decides who gains", x=0.02, ha="left",
                 fontsize=13, fontweight="bold", color=INK)
    fig.text(0.02, 0.015, "Hatched: tracts with 0 households (omitted). N.Y.C. Groceries counts the discount's gain only. "
             "Source: Chris run 1, results/chris_run1_base/dcs_by_tract.csv.", color=INK2, fontsize=7.5)
    fig.savefig(RESULTS_DIR / "chris_run1_base" / "fig_who_gains_map.png", dpi=200, facecolor=SURFACE, bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    subsidy_vs_cs()
    who_gains_map()
    print("Saved figures to results/chris_run1_base/")
