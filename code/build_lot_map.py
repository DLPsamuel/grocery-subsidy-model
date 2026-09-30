"""Map of the tax lots matched to the 9 CD2 candidate stores, for checking against Google Maps.

Lot outlines come from City Planning's MapPLUTO ArcGIS service (condo stores use the building's
billing lot, which is how MapPLUTO draws condos). Store pins use the Ag & Markets license
coordinates. Each lot is labeled with the store's v2 share, and the popup shows occupied sq ft,
floor-area and income shares, lot tax, Tax_j and Rent_j, with Google Maps and ZoLa links.

The page is plain Leaflet (loaded from unpkg) on Esri satellite imagery; no Python mapping
packages are needed.

  python code/build_lot_map.py                  # download outlines, build the map
  python code/build_lot_map.py --skip-download  # reuse data/tax/v2/lot_polygons_v2.geojson

Writes data/tax/v2/lot_polygons_v2.geojson and data/tax/v2/lot_check_map_v2.html.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[1]
STORES_CSV = ROOT / "data" / "stores" / "large_grocery_stores_cd2.csv"
OCC_CSV = ROOT / "data" / "tax" / "v2" / "store_occupancy_v2.csv"
TAX_V2_CSV = ROOT / "data" / "tax" / "v2" / "tax_j_cd2_candidate_stores_v2.csv"
OUT_DIR = ROOT / "data" / "tax" / "v2"
GEOJSON_OUT = OUT_DIR / "lot_polygons_v2.geojson"
HTML_OUT = OUT_DIR / "lot_check_map_v2.html"

MAPPLUTO_QUERY = ("https://services5.arcgis.com/GfwWNkhOj9bNBqoJ/arcgis/rest/services/"
                  "MAPPLUTO/FeatureServer/0/query")


def fetch_polygons(bbls: list[str]) -> dict:
    params = {"where": f"BBL IN ({','.join(bbls)})", "outFields": "BBL,Address,LotArea,BldgArea",
              "outSR": 4326, "f": "geojson"}
    r = requests.get(MAPPLUTO_QUERY, params=params, timeout=60)
    r.raise_for_status()
    gj = r.json()
    if "features" not in gj:
        raise RuntimeError(f"MapPLUTO query failed: {str(gj)[:300]}")
    return gj


def zola_url(bbl: str) -> str:
    return f"https://zola.planning.nyc.gov/l/lot/{bbl[0]}/{int(bbl[1:6])}/{int(bbl[6:])}"


def store_records() -> list[dict]:
    stores = pd.read_csv(STORES_CSV, dtype={"license_number": str})[["license_number", "latitude", "longitude"]]
    occ = pd.read_csv(OCC_CSV, dtype={"license_number": str, "pluto_bbl": str})[
        ["license_number", "pluto_bbl", "occupancy_note"]]
    tax = pd.read_csv(TAX_V2_CSV, dtype={"license_number": str, "bbl": str})
    df = tax.merge(occ, on="license_number", how="left").merge(stores, on="license_number", how="left")
    recs = []
    for _, r in df.iterrows():
        recs.append({
            "license_number": r["license_number"], "store": r["store"].title(), "address": r["address"].title(),
            "bbl": r["bbl"], "pluto_bbl": r["pluto_bbl"], "lot_type": r["lot_type"],
            "lat": r["latitude"], "lon": r["longitude"],
            "agm_sqft": r["agm_sqft"], "occupied_sqft": r["occupied_sqft"], "denominator_sqft": r["denominator_sqft"],
            "occupancy_basis": r["occupancy_basis"], "occupancy_note": r["occupancy_note"],
            "store_share_v1": r["store_share_v1"], "store_share_area": r["store_share_area"],
            "store_share_income": None if pd.isna(r["store_share_income"]) else r["store_share_income"],
            "share_method": r["share_method"], "store_share": r["store_share"],
            "lot_tax": r["lot_tax_fy2025"], "Tax_j": r["Tax_j"], "Tax_j_high": r["Tax_j_high"],
            "Tax_j_v1": r["Tax_j_v1"], "Rent_j": r["Rent_j_v2"],
            "google_maps": f"https://www.google.com/maps/search/?api=1&query={r['latitude']},{r['longitude']}",
            "zola": zola_url(r["pluto_bbl"]),
        })
    return recs


HTML_TEMPLATE = """<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>CD2 candidate stores: tax lots and store shares (v2, FY2025)</title>
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css">
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<style>
  body { margin: 0; font-family: Arial, sans-serif; display: flex; height: 100vh; }
  #side { width: 340px; overflow-y: auto; padding: 10px; box-sizing: border-box; font-size: 13px; }
  #map { flex: 1; }
  .store { border-bottom: 1px solid #ddd; padding: 6px 0; cursor: pointer; }
  .store:hover { background: #f3f3f3; }
  .share { font-weight: bold; }
  .lbl { background: rgba(255,255,255,0.85); border: 1px solid #333; font-size: 11px; font-weight: bold; }
  table.pop td { padding: 1px 6px 1px 0; vertical-align: top; }
</style>
</head>
<body>
<div id="side">
  <h3 style="margin:4px 0">Tax lots and store shares</h3>
  <div>Fiscal year 2025, v2. Yellow outline = tax lot (MapPLUTO); pin = store address (Ag &amp; Markets).
  Click a store to zoom. Totals: Tax_j __TAX_TOTAL__ (high __TAX_HIGH__), Rent_j __RENT_TOTAL__.</div>
  <div id="list"></div>
</div>
<div id="map"></div>
<script>
const STORES = __STORES__;
const LOTS = __LOTS__;
const fmt = v => v == null ? "n/a" : "$" + Math.round(v).toLocaleString();
const sq = v => v == null ? "n/a" : Math.round(v).toLocaleString() + " sq ft";
const sh = v => v == null ? "n/a" : Number(v).toFixed(3);

const imagery = L.tileLayer("https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
  {maxZoom: 21, maxNativeZoom: 19, attribution: "Imagery: Esri, Maxar, Earthstar Geographics"});
const labels = L.tileLayer("https://server.arcgisonline.com/ArcGIS/rest/services/Reference/World_Boundaries_and_Places/MapServer/tile/{z}/{y}/{x}",
  {maxZoom: 21, maxNativeZoom: 19});
const streets = L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
  {maxZoom: 21, maxNativeZoom: 19, attribution: "&copy; OpenStreetMap contributors"});
const map = L.map("map", {layers: [imagery, labels]}).setView([STORES[0].lat, STORES[0].lon], 16);
L.control.layers({"Satellite": imagery, "Streets": streets}, {"Place labels": labels}).addTo(map);

function popup(s) {
  return `<b>${s.store}</b><br>${s.address}<table class="pop">
  <tr><td>Tax lot (BBL)</td><td>${s.bbl}${s.lot_type === "condo_unit" ? " (condo unit; outline is billing lot " + s.pluto_bbl + ")" : ""}</td></tr>
  <tr><td>Occupied area</td><td>${sq(s.occupied_sqft)} (${s.occupancy_basis})</td></tr>
  <tr><td>Building area</td><td>${sq(s.denominator_sqft)}</td></tr>
  <tr><td>Ag &amp; Markets sq ft</td><td>${sq(s.agm_sqft)}</td></tr>
  <tr><td>Share, floor area</td><td>${sh(s.store_share_area)}</td></tr>
  <tr><td>Share, income</td><td>${sh(s.store_share_income)}</td></tr>
  <tr><td><b>Share used</b></td><td><b>${sh(s.store_share)}</b> (${s.share_method}); v1 ${sh(s.store_share_v1)}</td></tr>
  <tr><td>Lot tax FY2025</td><td>${fmt(s.lot_tax)}</td></tr>
  <tr><td><b>Tax_j</b></td><td><b>${fmt(s.Tax_j)}</b>${s.Tax_j_high !== s.Tax_j ? " (high " + fmt(s.Tax_j_high) + ")" : ""}; v1 ${fmt(s.Tax_j_v1)}</td></tr>
  <tr><td><b>Rent_j</b></td><td><b>${fmt(s.Rent_j)}</b></td></tr>
  <tr><td>Site check</td><td>${s.occupancy_note || ""}</td></tr>
  </table><a href="${s.google_maps}" target="_blank">Google Maps</a> | <a href="${s.zola}" target="_blank">ZoLa</a>`;
}

const byLot = {};
STORES.forEach(s => { byLot[s.pluto_bbl] = s; });
const lotLayers = {};
const lotLayer = L.geoJSON(LOTS, {
  style: {color: "#ffd400", weight: 3, fillOpacity: 0.15},
  onEachFeature: (f, layer) => {
    const s = byLot[String(f.properties.BBL)];
    if (!s) return;
    lotLayers[s.license_number] = layer;
    layer.bindPopup(popup(s), {maxWidth: 380});
    layer.bindTooltip(`${s.store}: share ${sh(s.store_share)}`, {permanent: true, direction: "center", className: "lbl"});
  }
}).addTo(map);

const list = document.getElementById("list");
STORES.forEach(s => {
  const m = L.circleMarker([s.lat, s.lon], {radius: 6, color: "#fff", weight: 2, fillColor: "#e4002b", fillOpacity: 1})
    .addTo(map).bindPopup(popup(s), {maxWidth: 380});
  const d = document.createElement("div");
  d.className = "store";
  d.innerHTML = `<b>${s.store}</b><br>${s.address} &middot; BBL ${s.bbl}<br>
    Share <span class="share">${sh(s.store_share)}</span> (${s.share_method.split(" (")[0]}) &middot; Tax_j ${fmt(s.Tax_j)} &middot; Rent_j ${fmt(s.Rent_j)}`;
  d.onclick = () => {
    const lyr = lotLayers[s.license_number];
    if (lyr) { map.fitBounds(lyr.getBounds(), {maxZoom: 20, padding: [40, 40]}); lyr.openPopup(); }
    else { map.setView([s.lat, s.lon], 19); m.openPopup(); }
  };
  list.appendChild(d);
});
map.fitBounds(lotLayer.getBounds(), {padding: [30, 30]});
</script>
</body>
</html>
"""


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--skip-download", action="store_true", help="reuse the saved lot outlines")
    args = ap.parse_args()

    recs = store_records()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    if args.skip_download:
        lots = json.loads(GEOJSON_OUT.read_text(encoding="utf-8"))
    else:
        lots = fetch_polygons(sorted({r["pluto_bbl"] for r in recs}))
        by_bbl = {r["pluto_bbl"]: r for r in recs}
        for f in lots["features"]:
            r = by_bbl.get(str(f["properties"]["BBL"]), {})
            f["properties"].update({k: r.get(k) for k in ("store", "license_number", "bbl", "occupied_sqft",
                                                          "store_share", "share_method", "Tax_j", "Rent_j")})
        GEOJSON_OUT.write_text(json.dumps(lots), encoding="utf-8")
    found = {str(f["properties"]["BBL"]) for f in lots["features"]}
    missing = [r["store"] for r in recs if r["pluto_bbl"] not in found]
    if missing:
        print(f"No lot outline for: {', '.join(missing)}")

    html = (HTML_TEMPLATE
            .replace("__STORES__", json.dumps(recs))
            .replace("__LOTS__", json.dumps(lots))
            .replace("__TAX_TOTAL__", f"${sum(r['Tax_j'] for r in recs):,.0f}")
            .replace("__TAX_HIGH__", f"${sum(r['Tax_j_high'] for r in recs):,.0f}")
            .replace("__RENT_TOTAL__", f"${sum(r['Rent_j'] for r in recs):,.0f}"))
    HTML_OUT.write_text(html, encoding="utf-8")
    print(f"{len(found)} lot outlines for {len(recs)} stores")
    print(f"Saved {GEOJSON_OUT.relative_to(ROOT)} and {HTML_OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
