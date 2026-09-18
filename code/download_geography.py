"""Download Bronx CD2 boundary, intersecting census tracts, and centroids."""
from __future__ import annotations

import sys
from pathlib import Path

import geopandas as gpd
import pandas as pd
from shapely.geometry import shape

sys.path.insert(0, str(Path(__file__).resolve().parent))
from data_paths import GEO_DIR, SESSION, download_file, load_cd2_boundary  # noqa: E402


TRACT_GEOJSON = "https://data.cityofnewyork.us/resource/63ge-mke6.geojson"
TIGER_NY = "https://www2.census.gov/geo/tiger/TIGER2023/TRACT/tl_2023_36_tract.zip"


def fetch_bronx_tracts() -> gpd.GeoDataFrame:
    """Paginate NYC Open Data 2020 tracts for the Bronx."""
    features = []
    offset = 0
    limit = 50000
    while True:
        params = {"$limit": limit, "$offset": offset, "$where": "boroname='Bronx'"}
        print(f"Fetching Bronx tracts offset={offset}")
        r = SESSION.get(TRACT_GEOJSON, params=params, timeout=180)
        r.raise_for_status()
        data = r.json()
        batch = data.get("features", [])
        features.extend(batch)
        if len(batch) < limit:
            break
        offset += limit

    if not features:
        raise RuntimeError("No Bronx tracts returned from NYC Open Data")

    recs = []
    for f in features:
        props = dict(f.get("properties") or {})
        geom = shape(f["geometry"]) if f.get("geometry") else None
        props["geometry"] = geom
        recs.append(props)
    return gpd.GeoDataFrame(recs, crs="EPSG:4326")


def fetch_tracts_tiger_fallback() -> gpd.GeoDataFrame:
    tiger = GEO_DIR / "tl_2023_36_tract.zip"
    if not tiger.exists():
        download_file(TIGER_NY, tiger)
    gdf = gpd.read_file(f"zip://{tiger}")
    gdf = gdf.to_crs(epsg=4326)
    return gdf[gdf["COUNTYFP"] == "005"].copy()


def main() -> None:
    print("=== Geography: Bronx CD2 + tract centroids ===")
    cd2 = load_cd2_boundary()
    print(f"CD2 features: {len(cd2)}")
    cd2_path = GEO_DIR / "bronx_cd2_boundary.geojson"
    if not cd2_path.exists():
        cd2.to_file(cd2_path, driver="GeoJSON")

    try:
        tracts = fetch_bronx_tracts()
    except Exception as e:
        print(f"NYC tracts failed ({e}); using TIGER fallback")
        tracts = fetch_tracts_tiger_fallback()

    print(f"Tract features loaded: {len(tracts)}; cols={list(tracts.columns)[:12]}...")

    cd2_union = cd2.geometry.union_all()
    tracts_cd2 = tracts[tracts.intersects(cd2_union)].copy()

    tracts_proj = tracts_cd2.to_crs(epsg=2263)
    centroids_proj = tracts_proj.copy()
    centroids_proj["geometry"] = centroids_proj.geometry.centroid
    centroids_wgs = centroids_proj.to_crs(epsg=4326)

    inside = centroids_wgs[centroids_wgs.within(cd2_union)].copy()
    if len(inside) >= 5:
        use = tracts_cd2.loc[inside.index]
        use_c = inside
        print(f"Using centroid-within filter: {len(use)} tracts")
    else:
        use = tracts_cd2
        use_c = centroids_wgs
        print(f"Fallback intersects filter: {len(use)} tracts")

    out_tracts = GEO_DIR / "bronx_cd2_tracts.geojson"
    use.to_file(out_tracts, driver="GeoJSON")

    rows = []
    for idx, row in use_c.iterrows():
        geoid = None
        for key in ("geoid", "GEOID", "boroct2020", "BoroCT2020", "ct2020", "CT2020"):
            if key in use_c.columns and pd.notna(row.get(key)):
                geoid = str(row[key])
                break
        rows.append(
            {
                "tract_id": geoid or str(idx),
                "lon": row.geometry.x,
                "lat": row.geometry.y,
            }
        )
    cent_df = pd.DataFrame(rows)
    cent_csv = GEO_DIR / "bronx_cd2_tract_centroids.csv"
    cent_df.to_csv(cent_csv, index=False)

    cent_gdf = gpd.GeoDataFrame(
        cent_df,
        geometry=gpd.points_from_xy(cent_df.lon, cent_df.lat),
        crs="EPSG:4326",
    )
    cent_gdf.to_file(GEO_DIR / "bronx_cd2_tract_centroids.geojson", driver="GeoJSON")

    cd2_proj = cd2.to_crs(epsg=2263)
    c = cd2_proj.geometry.centroid.to_crs(epsg=4326).iloc[0]
    pd.DataFrame([{"name": "bronx_cd2", "lon": c.x, "lat": c.y}]).to_csv(
        GEO_DIR / "bronx_cd2_centroid.csv", index=False
    )

    print(f"Wrote {out_tracts} ({len(use)} tracts)")
    print(f"Wrote {cent_csv} ({len(cent_df)} centroids)")
    print("Done.")


if __name__ == "__main__":
    main()
