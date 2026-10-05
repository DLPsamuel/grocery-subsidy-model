"""
Generate figures/cd2_store_map_v3.png
CD2 boundary + census tracts + 9 existing stores + NYC Groceries (planned).

v3 changes from generate_cd2_store_map_v2.py (presentation version):
  - Store-name labels and the planned-store label are removed (markers kept).
  - Zero-household tract text labels are removed (hatching and centroids kept).
  - Title, latitude/longitude axis labels, ticks and frame are removed.
  - Legend is enlarged and placed outside the map on the right.
  - Map markers are slightly larger.
"""

import os
import sys

import geopandas as gpd
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.lines import Line2D

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_d_ij import PLANNED_STORES  # noqa: E402

# ── paths ──────────────────────────────────────────────────────────────────────
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GEO   = os.path.join(ROOT, "data", "geography")
STORES_CSV = os.path.join(ROOT, "data", "stores", "large_grocery_stores_cd2.csv")
INCOME_CSV = os.path.join(ROOT, "data", "acs", "cd2_B19001_2024.csv")
OUT_DIR    = os.path.join(ROOT, "figures")
OUT_PNG    = os.path.join(OUT_DIR, "cd2_store_map_v3.png")

os.makedirs(OUT_DIR, exist_ok=True)

# ── load geographic layers ─────────────────────────────────────────────────────
cd2_boundary = gpd.read_file(os.path.join(GEO, "bronx_cd2_boundary.geojson"))
tracts       = gpd.read_file(os.path.join(GEO, "bronx_cd2_tracts.geojson"))

income = pd.read_csv(INCOME_CSV, dtype={"GEOID": str})
zero_ids = set(income.loc[income["B19001_001E"] == 0, "GEOID"])
tracts["zero_hh"] = tracts["geoid"].isin(zero_ids)
active_tracts = tracts[~tracts["zero_hh"]]
zero_tracts   = tracts[tracts["zero_hh"]]

# ── load stores ────────────────────────────────────────────────────────────────
stores_df = pd.read_csv(STORES_CSV)
stores_gdf = gpd.GeoDataFrame(
    stores_df,
    geometry=gpd.points_from_xy(stores_df["longitude"], stores_df["latitude"]),
    crs="EPSG:4326",
)

NYCG_LAT = float(PLANNED_STORES.loc[0, "latitude"])
NYCG_LON = float(PLANNED_STORES.loc[0, "longitude"])
nyc_groceries = gpd.GeoDataFrame(
    [{"name": "N.Y.C. Groceries\n(Planned)"}],
    geometry=gpd.points_from_xy([NYCG_LON], [NYCG_LAT]),
    crs="EPSG:4326",
)

# ── plot ───────────────────────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(13, 8), dpi=150)

# active tracts — light fill, grey border
active_tracts.plot(ax=ax, facecolor="#f0f4f8", edgecolor="#9dafc0", linewidth=0.8, zorder=1)

# zero-household tracts — no fill, light hatch, same border
zero_tracts.plot(ax=ax, facecolor="white", edgecolor="#9dafc0", linewidth=0.8,
                 hatch="///", zorder=1)
# hatch colour follows edgecolor; redraw a plain border on top
zero_tracts.boundary.plot(ax=ax, color="#9dafc0", linewidth=0.8, zorder=1.5)

# CD2 boundary — thicker outline
cd2_boundary.plot(ax=ax, facecolor="none", edgecolor="#1a3a5c", linewidth=2.2, zorder=2)

# tract centroids — filled for active tracts, hollow for zero-household tracts
centroids_csv = os.path.join(GEO, "bronx_cd2_tract_centroids.csv")
centroids_df  = pd.read_csv(centroids_csv, dtype={"tract_id": str})
centroids_df["zero_hh"] = centroids_df["tract_id"].isin(zero_ids)
centroids_gdf = gpd.GeoDataFrame(
    centroids_df,
    geometry=gpd.points_from_xy(centroids_df["lon"], centroids_df["lat"]),
    crs="EPSG:4326",
)
centroids_gdf[~centroids_gdf["zero_hh"]].plot(
    ax=ax, color="#6b7c93", markersize=24, marker="o", zorder=3, alpha=0.65)
centroids_gdf[centroids_gdf["zero_hh"]].plot(
    ax=ax, facecolor="white", edgecolor="#6b7c93", markersize=30, marker="o",
    linewidth=1.0, zorder=3)

ctlabels = dict(zip(tracts["geoid"], tracts["ctlabel"]))

# existing stores — blue circles with white edge
stores_gdf.plot(
    ax=ax,
    color="#1565c0",
    markersize=120,
    marker="o",
    edgecolor="white",
    linewidth=1.0,
    zorder=4,
)

# planned store — orange star
nyc_groceries.plot(
    ax=ax,
    color="#e65100",
    markersize=260,
    marker="*",
    edgecolor="white",
    linewidth=0.8,
    zorder=6,
)

# ── legend ─────────────────────────────────────────────────────────────────────
legend_elements = [
    mpatches.Patch(facecolor="#f0f4f8", edgecolor="#9dafc0", linewidth=0.8,
                   label=f"Census tract with households (n={len(active_tracts)})"),
    mpatches.Patch(facecolor="white", edgecolor="#9dafc0", linewidth=0.8, hatch="///",
                   label=f"Tract with 0 households, omitted (n={len(zero_tracts)})"),
    mpatches.Patch(facecolor="none",   edgecolor="#1a3a5c", linewidth=2.2,
                   label="CD2 boundary"),
    Line2D([0], [0], marker="o", color="w", markerfacecolor="#6b7c93",
           markersize=12, label="Tract centroid"),
    Line2D([0], [0], marker="o", color="w", markerfacecolor="white",
           markeredgecolor="#6b7c93", markersize=12, label="Centroid of omitted tract"),
    Line2D([0], [0], marker="o", color="w", markerfacecolor="#1565c0",
           markeredgecolor="white", markersize=15, label="Existing grocery store (n=9)"),
    Line2D([0], [0], marker="*", color="w", markerfacecolor="#e65100",
           markeredgecolor="white", markersize=20, label="N.Y.C. Groceries (Planned)"),
]
ax.legend(handles=legend_elements, loc="center left", bbox_to_anchor=(1.0, 0.5),
          fontsize=13, handlelength=2.2, handleheight=1.4, labelspacing=0.8,
          borderpad=0.8, framealpha=0.92, edgecolor="#ccc")

ax.set_axis_off()

# tighten extent slightly around CD2
bounds = cd2_boundary.total_bounds  # [minx, miny, maxx, maxy]
pad_x = (bounds[2] - bounds[0]) * 0.08
pad_y = (bounds[3] - bounds[1]) * 0.08
ax.set_xlim(bounds[0] - pad_x, bounds[2] + pad_x)
ax.set_ylim(bounds[1] - pad_y, bounds[3] + pad_y)

plt.tight_layout()
plt.savefig(OUT_PNG, dpi=150, bbox_inches="tight")
print(f"Saved: {OUT_PNG}")
print(f"Zero-household tracts: {sorted(ctlabels[g] for g in zero_ids)}")
