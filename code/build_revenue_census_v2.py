"""Central Revenue_j v2: Bronx sales per sq ft with SNAP- and code-based store classes
(Appendix F, Lead R). v1 is code/build_revenue_census.py; this version matches every numerator
to a denominator of the same store class.

  rate_c,2024 = Census Bronx sales of class c (2022, employer + nonemployer)
                / sq ft of Bronx Ag & Markets stores assigned to class c
                x CPI(2024) / CPI(2022)

Classes (NAICS 2022): 445110 supermarkets and grocery; 44513 convenience; 4452 specialty food.

Store classification, in order:
  1. Ag & Markets establishment codes: keep A (store); drop D, E, H, I, L (warehouses, plants,
     wholesale). Code sheet: data/stores/NYSDAM_RetailFoodStoresEstablishmentTypeCodes.pdf.
  2. v1 name exclusions (pharmacy, dollar store, gas station, online/warehouse, non-food retail),
     applied to every store whatever its SNAP type.
  3. USDA SNAP store type of the matched SNAP retailer (active in 2022 for the 2023 archive;
     currently authorized for the current list). Matched by address, then by the nearest SNAP
     point within 50 m that shares a name word.
  4. Stores with no SNAP match: v1 name categories.

Sources: 2022 Economic Census (api.census.gov/data/2022/ecnbasic) and Nonemployer Statistics
(api.census.gov/data/2022/nonemp), Bronx County; NYS Ag & Markets Retail Food Stores
(data.ny.gov 9a8c-vfzj); USDA SNAP retailer historical file (data/stores/snap_bronx_county.csv);
BLS CPI food at home, New York area (CUURS12ASAF11).
"""
from __future__ import annotations

import json
import re
import sys
import time
from pathlib import Path

import geopandas as gpd
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_p_j import CPI_SERIES, cpi_year  # noqa: E402
from build_revenue_census import (  # noqa: E402
    API_BASE, CENSUS_YEAR, MAX_SQFT, MIN_SQFT, TARGET_YEAR, WAREHOUSE_CODES, census_request,
    classify, normalize_name,
)
from data_paths import census_api_key  # noqa: E402
from link_agmarkets_snap import (  # noqa: E402
    normalize_number, normalize_street, normalize_zip, street_similarity,
)

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "data" / "revenue_census_estimate" / "v2"
RAW_DIR = OUT_DIR / "raw"
RAW_DIR.mkdir(parents=True, exist_ok=True)

RAW_CENSUS_CSV = RAW_DIR / "ecn_2022_bronx_v2.csv"
LINKED_OUT_CSV = OUT_DIR / "bronx_agmarkets_snap_linked_v2.csv"
CLASS_COUNTS_CSV = OUT_DIR / "bronx_class_counts_v2.csv"
RATES_OUT_CSV = OUT_DIR / "bronx_sales_per_sqft_census_v2.csv"
REVENUE_OUT_CSV = OUT_DIR / "revenue_j_census_v2_cd2_candidate_stores.csv"
META_JSON = OUT_DIR / "revenue_census_v2_meta.json"

AGM_2023_CSV = ROOT / "data" / "stores" / "agmarkets_retail_food_stores_archive_2023.csv"
AGM_CURRENT_CSV = ROOT / "data" / "stores" / "agmarkets_bronx_county.csv"
SNAP_CSV = ROOT / "data" / "stores" / "snap_bronx_county.csv"
CD2_SNAP_CSV = ROOT / "data" / "stores" / "agmarkets_bronx_cd2_snap_eligibility.csv"
REVENUE_J_CSV = ROOT / "data" / "revenue" / "revenue_j_cd2_candidate_stores.csv"
V1_REVENUE_CSV = ROOT / "data" / "revenue_census_estimate" / "revenue_j_census_cd2_candidate_stores.csv"
MARKET_M_CSV = ROOT / "data" / "bls" / "cd2_market_size_M_northeast_cd2weighted.csv"

CENSUS_QUERIES = [
    ("ecnbasic", "4451"), ("ecnbasic", "445110"), ("ecnbasic", "44513"), ("ecnbasic", "4452"),
    ("nonemp", "4451"), ("nonemp", "44513"), ("nonemp", "4452"),
]
SNAP_ACTIVE_WINDOW = ("2022-01-01", "2022-12-31")  # active at any point in the Census year

SPATIAL_MAX_M = 50.0
FT_PER_M = 3.28084
# Words too common in store names to count as a name match
GENERIC_WORDS = {
    "INC", "CORP", "CORPORATION", "LLC", "CO", "LTD", "THE", "OF", "AND", "&", "NY", "NYC", "BRONX",
    "DELI", "GROCERY", "GROCERIA", "FOOD", "FOODS", "MARKET", "MARKETS", "SUPERMARKET", "MINI",
    "MART", "STORE", "STORES", "CANDY", "CONVENIENCE", "FRESH", "SUPER", "NEW", "BEST", "FAMILY",
    "GOURMET", "MEAT", "MEATS", "FRUIT", "FRUITS", "PRODUCE", "BAKERY", "SHOP", "ST", "AVE", "E", "W",
    "1", "2", "3", "I", "II", "III",
}

SNAP_TYPE_CLASS = {
    "Supermarket": "445110", "Super Store": "445110", "Large Grocery Store": "445110",
    "Medium Grocery Store": "445110", "Small Grocery Store": "445110",
    "Convenience Store": "44513",
    "Meat/Poultry Specialty": "4452", "Seafood Specialty": "4452",
    "Fruits/Veg Specialty": "4452", "Bakery Specialty": "4452",
    "Combination Grocery/Other": "44513",  # non-grocery names are already excluded by step 2
}
SNAP_TYPES_EXCLUDED = {"Farmers' Market", "Food Buying Co-op", "Military Commissary"}
NAME_CATEGORY_CLASS = {"supermarket": "445110", "other grocery": "445110",
                       "convenience or deli": "44513", "specialty": "4452"}

CLASSES = ["445110", "44513", "4452"]
CLASS_LABELS = {"445110": "Supermarkets and other grocery", "44513": "Convenience retailers",
                "4452": "Specialty food"}
# variant -> (Census classes in numerator = store classes in denominator, vintage, sq ft mode)
VARIANTS = {
    "central": (["445110"], "2023", "impute"),
    "pooled_4451": (["445110", "44513"], "2023", "impute"),
    "all_food_445": (["445110", "44513", "4452"], "2023", "impute"),
    "convenience_44513": (["44513"], "2023", "impute"),
    "specialty_4452": (["4452"], "2023", "impute"),
    "current_list": (["445110"], "current", "impute"),
    "known_sqft_only": (["445110"], "2023", "known_only"),
    "pooled_current_list": (["445110", "44513"], "current", "impute"),
    "pooled_known_sqft_only": (["445110", "44513"], "2023", "known_only"),
}
# Low/high range for a 445110 store, taken from the recommended family of variants
RANGE_VARIANTS = {
    "central": ["central", "current_list", "known_sqft_only"],
    "pooled_4451": ["pooled_4451", "all_food_445", "pooled_current_list", "pooled_known_sqft_only"],
}
SPLIT_TOLERANCE = 0.15  # max gap between Ag & Markets and Census 445110 share of 4451 stores


# ---------------------------------------------------------------- Census numerator

def request_with_retry(dataset: str, naics: str, key: str | None, tries: int = 4) -> dict:
    for attempt in range(tries):
        try:
            return census_request(dataset, naics, key)
        except Exception:  # noqa: BLE001
            if attempt == tries - 1:
                raise
            time.sleep(5 * (attempt + 1))
    raise RuntimeError("unreachable")


def load_census() -> tuple[pd.DataFrame, str]:
    key = census_api_key()
    try:
        census = pd.DataFrame([request_with_retry(d, n, key) for d, n in CENSUS_QUERIES])
        census.to_csv(RAW_CENSUS_CSV, index=False)
        return census, "api"
    except Exception as exc:  # noqa: BLE001
        if RAW_CENSUS_CSV.exists():
            print(f"Census API failed ({exc}); using cached {RAW_CENSUS_CSV.relative_to(ROOT)}")
            return pd.read_csv(RAW_CENSUS_CSV, dtype={"naics2022": str}), "cached file"
        sys.exit(f"Census API failed ({exc}) and no cached {RAW_CENSUS_CSV}. See v1 for the "
                 "manual-download instructions; add ecnbasic 44513 and nonemp 44513 rows.")


def class_numerators(census: pd.DataFrame) -> tuple[pd.DataFrame, str]:
    """Employer + nonemployer sales and establishments per class."""
    idx = census.set_index(["dataset", "naics2022"])

    def get(ds: str, n: str, col: str) -> float | None:
        return float(idx.loc[(ds, n), col]) if (ds, n) in idx.index else None

    rows = {}
    for col in ("sales_usd", "establishments"):
        ne_4451, ne_44513 = get("nonemp", "4451", col), get("nonemp", "44513", col)
        if ne_44513 is not None:
            split = "NES 445110 = NES 4451 - NES 44513"
            ne = {"445110": ne_4451 - ne_44513, "44513": ne_44513}
        else:
            split = "NES 4451 split by employer establishment shares (NES 44513 not published)"
            w = get("ecnbasic", "44513", "establishments") / get("ecnbasic", "4451", "establishments")
            ne = {"445110": ne_4451 * (1 - w), "44513": ne_4451 * w}
        ne["4452"] = get("nonemp", "4452", col)
        for c in CLASSES:
            rows.setdefault(c, {})[f"employer_{col}"] = get("ecnbasic", c, col)
            rows[c][f"nonemployer_{col}"] = ne[c]
    num = pd.DataFrame(rows).T
    num["sales_usd"] = num["employer_sales_usd"] + num["nonemployer_sales_usd"]
    num["establishments"] = num["employer_establishments"] + num["nonemployer_establishments"]
    num.index.name = "naics_class"
    return num, split


# ---------------------------------------------------------------- Ag & Markets and SNAP

def parse_point(val: object) -> tuple[float | None, float | None]:
    m = re.search(r"(-?\d+\.\d+)[ ,]+(-?\d+\.\d+)", str(val))
    return (float(m.group(1)), float(m.group(2))) if m else (None, None)


def load_agmarkets(vintage: str) -> pd.DataFrame:
    if vintage == "2023":
        df = pd.read_csv(AGM_2023_CSV, dtype=str)
        df = df[df["county"].str.upper() == "BRONX"].copy()
        df["codes"] = df["estab_type"].fillna("").str.replace(r"^J", "", regex=True)
        pts = df["georeference"].map(parse_point)
        df["lon"] = [p[0] for p in pts]
        df["lat"] = [p[1] for p in pts]
    else:
        df = pd.read_csv(AGM_CURRENT_CSV, dtype=str)
        df["codes"] = df["estab_type"].fillna("")
        df["lon"] = pd.to_numeric(df["longitude"], errors="coerce")
        df["lat"] = pd.to_numeric(df["latitude"], errors="coerce")
    df = df.reset_index(drop=True)
    df["vintage"] = vintage
    df["name"] = normalize_name(df["dba_name"].fillna(df["entity_name"]))
    df["entity"] = normalize_name(df["entity_name"])
    sq = pd.to_numeric(df["square_footage"], errors="coerce")
    df["sqft_recorded"] = sq.where(sq >= MIN_SQFT)
    df["bakery_flag"] = df["codes"].str.contains("B").astype(int)
    df["num"] = df["street_number"].map(normalize_number)
    df["street"] = df["street_name"].map(normalize_street)
    df["zip5"] = df["zip_code"].map(normalize_zip)
    return df


def load_snap(vintage: str) -> pd.DataFrame:
    s = pd.read_csv(SNAP_CSV, dtype=str)
    auth = pd.to_datetime(s["Authorization Date"], errors="coerce")
    end = pd.to_datetime(s["End Date"].str.strip().replace("", None), errors="coerce")
    if vintage == "2023":
        start, stop = SNAP_ACTIVE_WINDOW
        active = (auth <= stop) & (end.isna() | (end >= start))
    else:
        active = end.isna()
    s = s[active].copy()
    s["auth_ts"] = auth[active]
    s["snap_record_id"] = s["Record ID"]
    s["snap_store_name"] = s["store_name"].str.strip()
    s["snap_store_type"] = s["Store Type"]
    s["snap_name_norm"] = normalize_name(s["snap_store_name"])
    s["num"] = s["Street Number"].map(normalize_number)
    s["street"] = s["Street Name"].map(normalize_street)
    s["zip5"] = s["Zip Code"].map(normalize_zip)
    s["lat"] = pd.to_numeric(s["latitude"], errors="coerce")
    s["lon"] = pd.to_numeric(s["longitude"], errors="coerce")
    s = s.sort_values("auth_ts", ascending=False)
    s = s.drop_duplicates(["snap_name_norm", "num", "street", "zip5"]).reset_index(drop=True)
    return s[["snap_record_id", "snap_store_name", "snap_store_type", "snap_name_norm", "num",
              "street", "zip5", "lat", "lon", "auth_ts"]]


def name_words(s: str) -> set[str]:
    return {w for w in str(s).split() if w not in GENERIC_WORDS and not w.isdigit()}


def link_snap(ag: pd.DataFrame, snap: pd.DataFrame) -> pd.DataFrame:
    """One SNAP match (or none) per Ag & Markets row: address first, then spatial."""
    cols = ["snap_record_id", "snap_store_name", "snap_store_type"]

    cand = ag[["num", "zip5", "street"]].reset_index().merge(
        snap, on=["num", "zip5"], suffixes=("", "_snap"))
    cand = cand[cand["num"] != ""]
    cand["street_sim"] = [street_similarity(a, b) for a, b in zip(cand["street"], cand["street_snap"])]
    cand = cand[cand["street_sim"] >= 0.4].sort_values(["street_sim", "auth_ts"], ascending=False)
    addr = cand.drop_duplicates("index").set_index("index")[cols]
    addr["snap_match_method"] = "address"
    addr["snap_match_distance_m"] = 0.0

    rest = ag.loc[~ag.index.isin(addr.index) & ag["lat"].notna()]
    ag_pts = gpd.GeoDataFrame(rest[["name", "entity"]], crs="EPSG:4326",
                              geometry=gpd.points_from_xy(rest["lon"], rest["lat"])).to_crs(2263)
    sn = snap.dropna(subset=["lat", "lon"])
    sn_pts = gpd.GeoDataFrame(sn[cols + ["snap_name_norm"]], crs="EPSG:4326",
                              geometry=gpd.points_from_xy(sn["lon"], sn["lat"])).to_crs(2263)
    buf = ag_pts.copy()
    buf["geometry"] = ag_pts.buffer(SPATIAL_MAX_M * FT_PER_M)
    pairs = gpd.sjoin(buf, sn_pts, predicate="intersects").reset_index(names="ag_idx")
    pairs["dist_m"] = [ag_pts.geometry.loc[i].distance(sn_pts.geometry.loc[j]) / FT_PER_M
                       for i, j in zip(pairs["ag_idx"], pairs["index_right"])]
    pairs["name_match"] = [bool((name_words(a) | name_words(e)) & name_words(s))
                           for a, e, s in zip(pairs["name"], pairs["entity"], pairs["snap_name_norm"])]
    # Storefronts are adjacent in the Bronx, so distance alone picks up neighbours
    pairs = pairs[pairs["name_match"]].sort_values(["ag_idx", "dist_m"])
    spat = pairs.drop_duplicates("ag_idx").set_index("ag_idx")
    spat["snap_match_method"] = "spatial, name match"
    spat["snap_match_distance_m"] = spat["dist_m"].round(1)
    spat = spat[cols + ["snap_match_method", "snap_match_distance_m"]]

    links = pd.concat([addr, spat])
    out = ag.join(links)
    out["snap_match_method"] = out["snap_match_method"].fillna("none")
    return out


def assign_class(df: pd.DataFrame) -> pd.DataFrame:
    reasons, classes, sources, name_cats = [], [], [], []
    for name, codes, sqft, snap_type in zip(df["name"], df["codes"], df["sqft_recorded"],
                                            df["snap_store_type"]):
        reason, cat = classify(name, codes, sqft)  # v1: code gate, name exclusions, >100k sq ft
        name_cats.append(cat)
        if reason:
            reasons.append(reason); classes.append(""); sources.append("excluded by codes or name")
        elif pd.notna(snap_type) and snap_type in SNAP_TYPE_CLASS:
            reasons.append(""); classes.append(SNAP_TYPE_CLASS[snap_type]); sources.append("SNAP type")
        elif pd.notna(snap_type) and snap_type in SNAP_TYPES_EXCLUDED:
            reasons.append(f"SNAP type {snap_type}"); classes.append(""); sources.append("SNAP type")
        else:
            reasons.append(""); classes.append(NAME_CATEGORY_CLASS[cat]); sources.append("name fallback")
    df["name_category"] = name_cats
    df["naics_class"] = classes
    df["class_source"] = sources
    df["exclude_reason"] = reasons
    df["keep"] = df["naics_class"].ne("").astype(int)
    return df


def impute_sqft(df: pd.DataFrame) -> pd.DataFrame:
    """Median recorded sq ft by (class, SNAP type or name category, bakery flag), coarsening
    to (class, bakery flag) and then class when a group has fewer than 5 recorded values."""
    kept = df["keep"] == 1
    df["type_group"] = df["snap_store_type"].where(df["class_source"] == "SNAP type",
                                                   "name: " + df["name_category"])
    df["sqft"] = df["sqft_recorded"].where(kept)
    df["sqft_imputed"] = (kept & df["sqft_recorded"].isna()).astype(int)
    df["impute_group"] = ""
    for keys in (["naics_class", "type_group", "bakery_flag"], ["naics_class", "bakery_flag"],
                 ["naics_class"]):
        g = df[kept].groupby(keys)["sqft_recorded"].agg(["median", "count"])
        g = g[g["count"] >= 5]["median"]
        need = kept & df["sqft"].isna()
        if not need.any():
            break
        med = df.loc[need, keys].apply(lambda r: g.get(tuple(r) if len(keys) > 1 else r.iloc[0]), axis=1)
        fill = need.copy()
        fill.loc[need] = med.notna().values
        df.loc[fill, "sqft"] = med[med.notna()]
        df.loc[fill, "impute_group"] = " x ".join(keys)
    return df


def build_stores(vintage: str) -> pd.DataFrame:
    ag = load_agmarkets(vintage)
    linked = link_snap(ag, load_snap(vintage))
    return impute_sqft(assign_class(linked))


# ---------------------------------------------------------------- rates

def rate_row(variant: str, stores: pd.DataFrame, num: pd.DataFrame, cpi_factor: float) -> dict:
    classes, vintage, mode = VARIANTS[variant]
    members = stores[(stores["vintage"] == vintage) & (stores["keep"] == 1)
                     & stores["naics_class"].isin(classes)]
    sales = num.loc[classes, "sales_usd"].sum()
    n, n_known = len(members), int(members["sqft_recorded"].notna().sum())
    if mode == "impute":
        sqft_total, numerator = members["sqft"].sum(), sales
    else:
        sqft_total, numerator = members["sqft_recorded"].sum(), sales * n_known / n
    rate_2022 = numerator / sqft_total
    codes = " + ".join(classes)
    return {
        "variant": variant,
        "numerator_definition": (f"Census 2022 NAICS {codes}, employer + nonemployer"
                                 + (f", x {n_known}/{n} stores with recorded sq ft"
                                    if mode == "known_only" else "")),
        "denominator_definition": (f"Ag & Markets {vintage} stores in class {codes}; "
                                   + ("recorded + imputed sq ft" if mode == "impute"
                                      else "recorded sq ft only")),
        "classes": codes,
        "agmarkets_vintage": vintage,
        "sqft_treatment": mode,
        "census_employer_sales_usd": round(num.loc[classes, "employer_sales_usd"].sum()),
        "census_nonemployer_sales_usd": round(num.loc[classes, "nonemployer_sales_usd"].sum()),
        "numerator_usd": round(numerator),
        "census_establishments": round(num.loc[classes, "establishments"].sum()),
        "agmarkets_stores": n,
        "agmarkets_stores_known_sqft": n_known,
        "share_stores_snap_typed": round((members["class_source"] == "SNAP type").mean(), 3),
        "share_sqft_imputed": round(members.loc[members["sqft_imputed"] == 1, "sqft"].sum()
                                    / members["sqft"].sum(), 3) if mode == "impute" else 0.0,
        "sqft_total": round(sqft_total),
        "sales_per_sqft_2022": round(rate_2022, 2),
        "sales_per_sqft_2024": round(rate_2022 * cpi_factor, 2),
        "sales_per_sqft_week_2024": round(rate_2022 * cpi_factor / 52, 2),
    }


def class_counts(stores: pd.DataFrame, num: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for vintage in ("2023", "current"):
        kept = stores[(stores["vintage"] == vintage) & (stores["keep"] == 1)]
        n_4451 = kept["naics_class"].isin(["445110", "44513"]).sum()
        census_4451 = num.loc[["445110", "44513"], "establishments"].sum()
        for c in CLASSES:
            k = kept[kept["naics_class"] == c]
            rows.append({
                "agmarkets_vintage": vintage, "naics_class": c, "label": CLASS_LABELS[c],
                "agmarkets_stores": len(k),
                "agmarkets_stores_snap_typed": int((k["class_source"] == "SNAP type").sum()),
                "agmarkets_stores_name_fallback": int((k["class_source"] == "name fallback").sum()),
                "agmarkets_sqft": round(k["sqft"].sum()),
                "census_employer_establishments": round(num.loc[c, "employer_establishments"]),
                "census_nonemployer_establishments": round(num.loc[c, "nonemployer_establishments"]),
                "census_establishments": round(num.loc[c, "establishments"]),
                "census_sales_usd": round(num.loc[c, "sales_usd"]),
                "agmarkets_share_of_4451_stores": (round(len(k) / n_4451, 3) if c != "4452" else None),
                "census_share_of_4451_establishments": (
                    round(num.loc[c, "establishments"] / census_4451, 3) if c != "4452" else None),
            })
    return pd.DataFrame(rows)


def cpi_ratio() -> tuple[float, float, float]:
    base = cpi_year(CENSUS_YEAR)["value"].mean()
    target = cpi_year(TARGET_YEAR)["value"].mean()
    return target / base, base, target


# ---------------------------------------------------------------- main

def main() -> None:
    census, census_source = load_census()
    num, nes_split = class_numerators(census)
    print(num.round(0).to_string())

    cpi_factor, cpi_base, cpi_target = cpi_ratio()
    print(f"\nCPI {CPI_SERIES}: {CENSUS_YEAR} {cpi_base:.3f} -> {TARGET_YEAR} {cpi_target:.3f}, "
          f"factor {cpi_factor:.4f}")

    stores = pd.concat([build_stores("2023"), build_stores("current")], ignore_index=True)
    out_cols = ["vintage", "license_number", "estab_type", "codes", "bakery_flag", "dba_name",
                "entity_name", "street_number", "street_name", "zip_code", "lat", "lon",
                "snap_match_method", "snap_match_distance_m", "snap_record_id", "snap_store_name",
                "snap_store_type", "name_category", "class_source", "naics_class", "keep",
                "exclude_reason", "square_footage", "sqft_recorded", "sqft_imputed", "impute_group",
                "sqft"]
    stores[out_cols].to_csv(LINKED_OUT_CSV, index=False)

    counts = class_counts(stores, num)
    counts.to_csv(CLASS_COUNTS_CSV, index=False)

    rates = pd.DataFrame([rate_row(v, stores, num, cpi_factor) for v in VARIANTS])
    rates.to_csv(RATES_OUT_CSV, index=False)
    r = rates.set_index("variant")["sales_per_sqft_2024"]

    c23 = counts[(counts["agmarkets_vintage"] == "2023") & (counts["naics_class"] == "445110")].iloc[0]
    split_gap = abs(c23["agmarkets_share_of_4451_stores"] - c23["census_share_of_4451_establishments"])
    recommended = "central" if split_gap <= SPLIT_TOLERANCE else "pooled_4451"
    class_rate = {"445110": r["central"], "44513": r["convenience_44513"], "4452": r["specialty_4452"]}
    pooled_rate = {"445110": r["pooled_4451"], "44513": r["pooled_4451"], "4452": r["specialty_4452"]}
    applied = class_rate if recommended == "central" else pooled_rate

    rev = pd.read_csv(REVENUE_J_CSV, dtype={"license_number": str})
    cd2 = pd.read_csv(CD2_SNAP_CSV, dtype={"license_number": str})[["license_number", "snap_store_type"]]
    v1 = pd.read_csv(V1_REVENUE_CSV, dtype={"license_number": str})[
        ["license_number", "revenue_census_central"]]
    out = rev[["store", "address", "license_number", "square_footage", "p_j"]].merge(
        cd2, on="license_number", how="left")
    out["naics_class"] = out["snap_store_type"].map(SNAP_TYPE_CLASS)
    out["rate_applied_2024"] = out["naics_class"].map(applied)
    out["revenue_census_v2"] = (out["square_footage"] * out["rate_applied_2024"]).round(-3)
    out["revenue_class_rate"] = (out["square_footage"] * out["naics_class"].map(class_rate)).round(-3)
    out["revenue_pooled_4451"] = (out["square_footage"] * out["naics_class"].map(pooled_rate)).round(-3)
    range_rates = r[RANGE_VARIANTS[recommended]]
    out["revenue_census_v2_low"] = (out["square_footage"] * range_rates.min()).round(-3)
    out["revenue_census_v2_high"] = (out["square_footage"] * range_rates.max()).round(-3)
    out["Q_j_census_v2"] = (out["revenue_census_v2"] / out["p_j"]).round()

    market_m = float(pd.read_csv(MARKET_M_CSV).set_index("acs_year").loc[TARGET_YEAR, "M_usd_nyc_scaled"])
    out["share_of_M"] = (out["revenue_census_v2"] / market_m).round(4)
    out = out.merge(v1.rename(columns={"revenue_census_central": "revenue_census_v1"}),
                    on="license_number", how="left")
    out["revenue_rusa_2024"] = rev["revenue_rusa_2024"].values
    out["revenue_fmi"] = rev["revenue_size_based"].values
    out = out.sort_values("revenue_census_v2", ascending=False)
    out.to_csv(REVENUE_OUT_CSV, index=False)

    totals = {k: out[k].sum() for k in ["revenue_census_v2", "revenue_class_rate", "revenue_pooled_4451",
                                        "revenue_census_v2_low", "revenue_census_v2_high",
                                        "revenue_census_v1", "revenue_rusa_2024", "revenue_fmi"]}

    s23 = stores[stores["vintage"] == "2023"]
    kept23 = s23[s23["keep"] == 1]
    code_groups = kept23.assign(code_group=kept23["codes"].str.replace("J", "")).groupby("code_group")
    meta = {
        "census_source": census_source,
        "census_queries": [f"{API_BASE}/{d}?NAICS2022={n}&for=county:005&in=state:36"
                           for d, n in CENSUS_QUERIES],
        "nonemployer_split": nes_split,
        "class_numerators": num.round(0).to_dict(orient="index"),
        "cpi_series": CPI_SERIES,
        "cpi_annual_avg": {str(CENSUS_YEAR): round(cpi_base, 3), str(TARGET_YEAR): round(cpi_target, 3)},
        "cpi_factor": round(cpi_factor, 4),
        "snap_file": str(SNAP_CSV.relative_to(ROOT)),
        "snap_active_window_for_2023_archive": SNAP_ACTIVE_WINDOW,
        "snap_type_class": SNAP_TYPE_CLASS,
        "snap_types_excluded": sorted(SNAP_TYPES_EXCLUDED),
        "name_category_class": NAME_CATEGORY_CLASS,
        "spatial_match": {"max_m": SPATIAL_MAX_M, "requires_shared_name_word": True,
                          "generic_words_ignored": sorted(GENERIC_WORDS)},
        "estab_code_gate": {"keep": "A", "exclude": sorted(WAREHOUSE_CODES),
                            "code_sheet": "data/stores/NYSDAM_RetailFoodStoresEstablishmentTypeCodes.pdf"},
        "sqft_missing_below": MIN_SQFT, "sqft_excluded_above": MAX_SQFT,
        "snap_match_methods": {v: stores[stores["vintage"] == v]["snap_match_method"].value_counts().to_dict()
                               for v in ("2023", "current")},
        "class_source_counts_kept": {
            v: {f"{c} / {src}": int(n) for (c, src), n in
                stores[(stores["vintage"] == v) & (stores["keep"] == 1)]
                .groupby(["naics_class", "class_source"]).size().items()}
            for v in ("2023", "current")},
        "exclude_reasons": {v: stores[stores["vintage"] == v]["exclude_reason"].replace("", "kept")
                            .value_counts().to_dict() for v in ("2023", "current")},
        "sqft_by_estab_code_2023_kept": {k: {"stores": int(len(g)),
                                             "median_recorded_sqft": g["sqft_recorded"].median(),
                                             "share_445110": round((g["naics_class"] == "445110").mean(), 3)}
                                         for k, g in code_groups if len(g) >= 5},
        "split_check": {"agmarkets_445110_share_of_4451_stores": c23["agmarkets_share_of_4451_stores"],
                        "census_445110_share_of_4451_establishments": c23["census_share_of_4451_establishments"],
                        "gap": round(split_gap, 3), "tolerance": SPLIT_TOLERANCE,
                        "recommended_variant": recommended,
                        "range_variants": RANGE_VARIANTS[recommended]},
        "market_size_M_2024_nyc_scaled": market_m,
        "nine_store_totals": {k: round(v) for k, v in totals.items()},
        "nine_store_share_of_M": {k: round(v / market_m, 3) for k, v in totals.items()},
    }
    META_JSON.write_text(json.dumps(meta, indent=2, default=str), encoding="utf-8")

    pd.set_option("display.width", 240)
    print("\nSNAP match methods (2023):", meta["snap_match_methods"]["2023"])
    print("Class sources (2023, kept):", meta["class_source_counts_kept"]["2023"])
    print("\nClass counts:")
    print(counts.drop(columns=["label"]).to_string(index=False))
    print("\nVariants:")
    print(rates[["variant", "classes", "agmarkets_vintage", "sqft_treatment", "numerator_usd",
                 "census_establishments", "agmarkets_stores", "sqft_total", "sales_per_sqft_2022",
                 "sales_per_sqft_2024", "sales_per_sqft_week_2024"]].to_string(index=False))
    print(f"\nSplit check: Ag & Markets 445110 share {c23['agmarkets_share_of_4451_stores']:.2f} vs "
          f"Census {c23['census_share_of_4451_establishments']:.2f} (gap {split_gap:.2f}); "
          f"recommended: {recommended}")
    print(out.drop(columns=["address", "license_number"]).to_string(index=False))
    print(f"\nMarket size M ({TARGET_YEAR}): ${market_m:,.0f}")
    for k, v in totals.items():
        print(f"  9-store total, {k}: ${v:,.0f} ({v / market_m:.0%} of M)")
    print(f"\nSaved outputs to {OUT_DIR.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
