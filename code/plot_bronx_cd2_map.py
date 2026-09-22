"""Plot Bronx CD2 census tracts over a basemap, with CD2 boundary overlay."""
from __future__ import annotations

import sys
from pathlib import Path

import contextily as cx
import geopandas as gpd
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
from data_paths import GEO_DIR  # noqa: E402

TRACTS_PATH = GEO_DIR / "bronx_cd2_tracts.geojson"
CD2_PATH = GEO_DIR / "bronx_cd2_boundary.geojson"
OUT_PNG = GEO_DIR / "bronx_cd2_tracts_map.png"
OUT_PDF = GEO_DIR / "bronx_cd2_tracts_map.pdf"


def _label_col(gdf: gpd.GeoDataFrame) -> str:
    for c in ("ctlabel", "ct2020", "geoid"):
        if c in gdf.columns:
            return c
    raise KeyError(f"No tract id column in {list(gdf.columns)}")


def main() -> None:
    if not TRACTS_PATH.exists():
        raise FileNotFoundError(TRACTS_PATH)
    if not CD2_PATH.exists():
        raise FileNotFoundError(CD2_PATH)

    tracts = gpd.read_file(TRACTS_PATH).to_crs(epsg=3857)
    cd2 = gpd.read_file(CD2_PATH).to_crs(epsg=3857)
    label_col = _label_col(tracts)

    fig, ax = plt.subplots(1, 1, figsize=(10, 12))
    tracts.plot(
        ax=ax,
        facecolor="#2E86AB",
        edgecolor="white",
        linewidth=1.0,
        alpha=0.45,
        zorder=2,
    )
    cd2.boundary.plot(ax=ax, color="#C0392B", linewidth=2.5, zorder=3)

    # Tract labels at polygon centroids
    cents = tracts.copy()
    cents["geometry"] = cents.geometry.representative_point()
    for _, row in cents.iterrows():
        ax.annotate(
            str(row[label_col]).lstrip("0") if str(row[label_col]).isdigit() else str(row[label_col]),
            xy=(row.geometry.x, row.geometry.y),
            ha="center",
            va="center",
            fontsize=7,
            color="#1a1a1a",
            fontweight="bold",
            zorder=4,
        )

    # Slight pad around bounds for basemap context
    minx, miny, maxx, maxy = tracts.total_bounds
    pad_x = (maxx - minx) * 0.08
    pad_y = (maxy - miny) * 0.08
    ax.set_xlim(minx - pad_x, maxx + pad_x)
    ax.set_ylim(miny - pad_y, maxy + pad_y)

    # Esri World Street Map (OSM tiles block non-browser User-Agents from this env)
    cx.add_basemap(
        ax,
        source=cx.providers.Esri.WorldStreetMap,
        attribution_size=6,
        zorder=1,
    )

    ax.set_axis_off()
    ax.set_title(
        "Bronx Community District 2 — Census Tracts (2020)",
        fontsize=13,
        fontweight="bold",
        pad=12,
    )
    ax.legend(
        handles=[
            Patch(facecolor="#2E86AB", edgecolor="white", alpha=0.45, label="Census tracts"),
            Patch(facecolor="none", edgecolor="#C0392B", linewidth=2.5, label="CD2 boundary"),
        ],
        loc="lower left",
        framealpha=0.9,
    )

    fig.tight_layout()
    fig.savefig(OUT_PNG, dpi=200, bbox_inches="tight")
    fig.savefig(OUT_PDF, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved {OUT_PNG}")
    print(f"Saved {OUT_PDF}")


if __name__ == "__main__":
    main()
