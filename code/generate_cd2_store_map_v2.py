"""
Generate figures/cd2_store_map_v2.png
CD2 boundary + census tracts + 9 existing stores + NYC Groceries (planned).

v2 changes from generate_cd2_store_map.py:
  - Tracts with 0 households in ACS 2024 (B19001) are left unshaded (hatched) and
    labelled as omitted; their boundaries and centroids are still drawn.
  - The planned store uses the PLUTO point from build_d_ij.py (same point as the
    distances), not the RFP point.
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
OUT_PNG    = os.path.join(OUT_DIR, "cd2_store_map_v2.png")

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
fig, ax = plt.subplots(figsize=(8, 8), dpi=150)

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
    ax=ax, color="#6b7c93", markersize=18, marker="o", zorder=3, alpha=0.65)
centroids_gdf[centroids_gdf["zero_hh"]].plot(
    ax=ax, facecolor="white", edgecolor="#6b7c93", markersize=22, marker="o",
    linewidth=1.0, zorder=3)

# zero-household tract labels (lon_delta, lat_delta from the centroid)
zero_label_offsets = {
    "36005001904": (0.009, 0.0005),
    "36005009302": (0.001, -0.0035),
    "36005011702": (-0.001, -0.004),
}
ctlabels = dict(zip(tracts["geoid"], tracts["ctlabel"]))
for _, row in centroids_gdf[centroids_gdf["zero_hh"]].iterrows():
    dx, dy = zero_label_offsets.get(row["tract_id"], (0.003, -0.003))
    ax.annotate(
        f"Tract {ctlabels[row['tract_id']]}\n0 households (omitted)",
        xy=(row.geometry.x, row.geometry.y),
        xytext=(row.geometry.x + dx, row.geometry.y + dy),
        fontsize=6.3,
        color="#6b7c93",
        fontstyle="italic",
        ha="left" if dx > 0.002 else "center",
        va="center",
        arrowprops=dict(arrowstyle="-", color="#6b7c93", lw=0.5),
        bbox=dict(boxstyle="round,pad=0.2", facecolor="white", edgecolor="none", alpha=0.85),
        zorder=5,
    )

# existing stores — blue circles with white edge
stores_gdf.plot(
    ax=ax,
    color="#1565c0",
    markersize=80,
    marker="o",
    edgecolor="white",
    linewidth=1.0,
    zorder=4,
)

# store labels (abbreviated)
abbrev = {
    "ANTILLANA FRESH MEAT MARKET": "Antillana",
    "SAGAL MEAT MARKET": "Sagal",
    "FOOD FAIR FRESH MARKET": "Food Fair",
    "KEY FOOD": "Key Food",
    "C-TOWN SUPERMARKET": "C-Town\n(564)",
    "JJ SOUTHERN FARM FRUIT": "JJ Southern",
    "FINE FARE SUPERMARKET": "Fine Fare",
    "C TOWN SUPERMARKET": "C-Town\n(809)",
    "FOOD UNIVERSE": "Food\nUniverse",
}

# label offsets (lon_delta, lat_delta) to avoid overlap
offsets = {
    "ANTILLANA FRESH MEAT MARKET": (0.003, 0.002),
    "SAGAL MEAT MARKET":           (-0.012, 0.002),
    "FOOD FAIR FRESH MARKET":      (0.003, -0.004),
    "KEY FOOD":                    (0.003, 0.003),
    "C-TOWN SUPERMARKET":          (-0.014, -0.003),
    "JJ SOUTHERN FARM FRUIT":      (0.003, -0.004),
    "FINE FARE SUPERMARKET":       (-0.014, 0.002),
    "C TOWN SUPERMARKET":          (0.003, 0.001),
    "FOOD UNIVERSE":               (0.003, -0.003),
}

for _, row in stores_gdf.iterrows():
    name = row["dba_name"]
    label = abbrev.get(name, name)
    dx, dy = offsets.get(name, (0.003, 0.002))
    ax.annotate(
        label,
        xy=(row.geometry.x, row.geometry.y),
        xytext=(row.geometry.x + dx, row.geometry.y + dy),
        fontsize=6.5,
        color="#1565c0",
        fontweight="bold",
        ha="left",
        va="center",
        arrowprops=dict(arrowstyle="-", color="#1565c0", lw=0.6),
        zorder=5,
    )

# planned store — orange star
nyc_groceries.plot(
    ax=ax,
    color="#e65100",
    markersize=160,
    marker="*",
    edgecolor="white",
    linewidth=0.8,
    zorder=6,
)
ax.annotate(
    "N.Y.C. Groceries\n(Planned)",
    xy=(NYCG_LON, NYCG_LAT),
    xytext=(NYCG_LON - 0.0075, NYCG_LAT - 0.0025),
    fontsize=7,
    color="#e65100",
    fontweight="bold",
    ha="left",
    va="top",
    arrowprops=dict(arrowstyle="-", color="#e65100", lw=0.6),
    zorder=7,
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
           markersize=7, label="Tract centroid"),
    Line2D([0], [0], marker="o", color="w", markerfacecolor="white",
           markeredgecolor="#6b7c93", markersize=7, label="Centroid of omitted tract"),
    Line2D([0], [0], marker="o", color="w", markerfacecolor="#1565c0",
           markeredgecolor="white", markersize=9, label="Existing grocery store (n=9)"),
    Line2D([0], [0], marker="*", color="w", markerfacecolor="#e65100",
           markeredgecolor="white", markersize=12, label="N.Y.C. Groceries (Planned)"),
]
ax.legend(handles=legend_elements, loc="lower left", fontsize=7,
          framealpha=0.92, edgecolor="#ccc")

# ── labels / title ─────────────────────────────────────────────────────────────
ax.set_title(
    "Bronx Community District 2 — Hunts Point / Longwood\nGrocery Stores and Census Tracts",
    fontsize=11, fontweight="bold", pad=10,
)
ax.set_xlabel("Longitude", fontsize=8)
ax.set_ylabel("Latitude",  fontsize=8)
ax.tick_params(labelsize=7)

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
