"""Shared paths and helpers for Bronx CD2 data collection."""
from __future__ import annotations

import os
from pathlib import Path

import geopandas as gpd
import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
GEO_DIR = DATA / "geography"
ACS_DIR = DATA / "acs"
BLS_DIR = DATA / "bls"
STORES_DIR = DATA / "stores"

for _d in (GEO_DIR, ACS_DIR, BLS_DIR, STORES_DIR):
    _d.mkdir(parents=True, exist_ok=True)

SESSION = requests.Session()
SESSION.headers.update(
    {"User-Agent": "grocery-subsidy-analysis/0.1 (Bronx CD2 research; academic)"}
)


def get_json(url: str, params: dict | None = None, timeout: int = 120) -> object:
    r = SESSION.get(url, params=params, timeout=timeout)
    r.raise_for_status()
    return r.json()


def download_file(url: str, dest: Path, timeout: int = 300) -> Path:
    dest.parent.mkdir(parents=True, exist_ok=True)
    with SESSION.get(url, stream=True, timeout=timeout) as r:
        r.raise_for_status()
        with open(dest, "wb") as f:
            for chunk in r.iter_content(chunk_size=1 << 16):
                if chunk:
                    f.write(chunk)
    return dest


def load_cd2_boundary() -> gpd.GeoDataFrame:
    """Load Bronx CD2 (BoroCD 202) from saved GeoJSON, or fetch from NYC Open Data."""
    path = GEO_DIR / "bronx_cd2_boundary.geojson"
    if path.exists():
        gdf = gpd.read_file(path)
        return gdf.to_crs(epsg=4326)

    # Current NYC Open Data Community Districts dataset
    url = "https://data.cityofnewyork.us/resource/5crt-au7u.geojson"
    # Fetch all CDs then filter (dataset is small)
    try:
        gdf = gpd.read_file(url)
    except Exception:
        # Fallback: geospatial export endpoint
        url = "https://data.cityofnewyork.us/api/geospatial/5crt-au7u?method=export&format=GeoJSON"
        gdf = gpd.read_file(url)
    gdf = gdf.to_crs(epsg=4326)
    # Column names vary: boro_cd / BoroCD
    col = None
    for c in gdf.columns:
        if c.lower().replace("_", "") in ("borocd",):
            col = c
            break
    if col is None:
        raise KeyError(f"No BoroCD column in Community Districts: {list(gdf.columns)}")
    gdf[col] = gdf[col].astype(str).str.zfill(3)
    cd2 = gdf[gdf[col] == "202"].copy()
    if cd2.empty:
        # try int compare
        cd2 = gdf[pd.to_numeric(gdf[col], errors="coerce") == 202].copy()
    if cd2.empty:
        raise ValueError("Bronx CD2 (202) not found in Community Districts layer")
    cd2.to_file(path, driver="GeoJSON")
    return cd2


def points_in_cd2(
    df: pd.DataFrame,
    lon_col: str,
    lat_col: str,
    cd2: gpd.GeoDataFrame | None = None,
) -> gpd.GeoDataFrame:
    """Filter a DataFrame with lon/lat columns to points inside CD2."""
    if cd2 is None:
        cd2 = load_cd2_boundary()
    work = df.copy()
    work[lon_col] = pd.to_numeric(work[lon_col], errors="coerce")
    work[lat_col] = pd.to_numeric(work[lat_col], errors="coerce")
    work = work.dropna(subset=[lon_col, lat_col])
    gdf = gpd.GeoDataFrame(
        work,
        geometry=gpd.points_from_xy(work[lon_col], work[lat_col]),
        crs="EPSG:4326",
    )
    joined = gpd.sjoin(gdf, cd2[["geometry"]], how="inner", predicate="within")
    if "index_right" in joined.columns:
        joined = joined.drop(columns=["index_right"])
    return joined


def _load_dotenv() -> None:
    """Load KEY=VALUE pairs from repo-root .env into os.environ (no extra dependency)."""
    env_path = ROOT / ".env"
    if not env_path.exists():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        key, val = key.strip(), val.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = val


def census_api_key() -> str | None:
    _load_dotenv()
    key = (os.environ.get("CENSUS_API_KEY") or "").strip()
    return key or None
