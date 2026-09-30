"""Central Revenue_j: Bronx grocery sales per sq ft from the 2022 Economic Census
(Appendix F, Lead R).

  rate_2024 = Census Bronx grocery sales (2022) / sq ft of matched Bronx Ag & Markets stores
              x CPI(2024) / CPI(2022)
  Revenue_j = store sq ft x rate_2024;  Q_j = Revenue_j / p_j

Sources:
  - Numerator: 2022 Economic Census, Geographic Area Statistics (api.census.gov/data/2022/ecnbasic,
    table EC2244BASIC), Bronx County (state 36, county 005). Employer establishments only, so
    Nonemployer Statistics 2022 (api.census.gov/data/2022/nonemp) are added for owner-run stores.
    Convenience retailers (445131) are published as 0 for the Bronx (suppressed), so the broad
    scope uses the 4451 total. Nonemployer data has no 445110 split at county level.
  - Denominator: NYS Ag & Markets Retail Food Stores (data.ny.gov 9a8c-vfzj). 2023 archive is the
    primary vintage (closest to 2022); the current list is a sensitivity. square_footage is the
    whole licensed location; 0 means not recorded.
  - Inflation: BLS CPI food at home, New York area (CUURS12ASAF11), annual average 2024 / 2022.

Decision: central rate = scope A (NAICS 4451, employer + nonemployer) over Ag & Markets grocery
stores (non-grocery retail, warehouses and specialty food shops removed), 2023 vintage, missing
sq ft imputed. Other variants are written alongside it as a range.

If the Census API is unavailable, the script reads a cached raw/ecn_2022_bronx_4451.csv (same
columns as it writes; can be rebuilt by hand from EC2244BASIC and the Nonemployer table for the
Bronx on data.census.gov).
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_p_j import CPI_SERIES, cpi_year  # noqa: E402
from data_paths import SESSION, census_api_key  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "data" / "revenue_census_estimate"
RAW_DIR = OUT_DIR / "raw"
RAW_DIR.mkdir(parents=True, exist_ok=True)

RAW_CENSUS_CSV = RAW_DIR / "ecn_2022_bronx_4451.csv"
STORES_OUT_CSV = OUT_DIR / "bronx_agmarkets_stores_filtered.csv"
RATES_OUT_CSV = OUT_DIR / "bronx_sales_per_sqft_census.csv"
REVENUE_OUT_CSV = OUT_DIR / "revenue_j_census_cd2_candidate_stores.csv"
META_JSON = OUT_DIR / "revenue_census_meta.json"

AGM_2023_CSV = ROOT / "data" / "stores" / "agmarkets_retail_food_stores_archive_2023.csv"
AGM_CURRENT_CSV = ROOT / "data" / "stores" / "agmarkets_bronx_county.csv"
REVENUE_J_CSV = ROOT / "data" / "revenue" / "revenue_j_cd2_candidate_stores.csv"
MARKET_M_CSV = ROOT / "data" / "bls" / "cd2_market_size_M_northeast_cd2weighted.csv"

CENSUS_YEAR = 2022
TARGET_YEAR = 2024
API_BASE = f"https://api.census.gov/data/{CENSUS_YEAR}"
GEO = {"for": "county:005", "in": "state:36"}
CENSUS_QUERIES = [  # (dataset, NAICS 2022 code)
    ("ecnbasic", "4451"), ("ecnbasic", "445110"), ("ecnbasic", "445131"), ("ecnbasic", "4452"),
    ("nonemp", "4451"), ("nonemp", "4452"),
]

MIN_SQFT = 100          # smaller recorded values are treated as missing
MAX_SQFT = 100_000      # larger locations are warehouses, not single stores

# Ag & Markets establishment codes: A store, B bakery, C food manufacturer, D food warehouse,
# E beverage plant, H wholesale manufacturer, I refrigerated warehouse, J multiple operations,
# K vehicle, L produce refrigerated warehouse (NYSDAM_RetailFoodStoresEstablishmentTypeCodes.pdf).
WAREHOUSE_CODES = set("DEHIL")

EXCLUDE_PATTERNS = {  # exclude_reason -> name pattern; checked in this order
    "pharmacy": r"WALGREENS?|RITE ?AID|CVS|DUANE ?READE|PHARMACY|FARMACIA|CHEMISTS?|DRUGS?",
    "general merchandise or dollar store": (
        r"DOLLAR|99 ?CENTS?|99 ?C|TARGET|WAL ?MART|BJ ?S|COSTCO|FIVE BELOW|BIG LOTS|BURLINGTON|"
        r"MARSHALLS|T ?J ?MAXX|HOME DEPOT|BOB ?S DISCOUNT|DISCOUNT FURNITUR\w*|BED BATH|"
        r"ROSS DRESS|OLD NAVY|KMART|SEARS|MACY ?S|STAPLES|PARTY CITY|SUPER ?DISCOUNT|DISCOUNT|"
        r"BARGAINS?|VALUE STORES?|PRICE BUSTERS|VARIETY"),
    "gas station": (r"BP|MOBIL|MOBIL MART|SHELL|SUNOCO|CITGO|EXXON|GULF|SPEEDWAY|HESS|GETTY|"
                    r"LUKOIL|VALERO|GAS|FUEL|SERVICE STATION|PETROLEUM|AM ?PM"),
    "online, wholesale or warehouse": (
        r"GO ?PUFF|FRESH ?DIRECT|PRIME NOW|AMAZON|INSTACART|GETIR|GORILLAS|JOKR|FRIDGE NO MORE|"
        r"WAREHOUSE|WHOLESALE|DISTRIBUT\w*|JETRO|RESTAURANT DEPOT|IMPORT\w*|EXPORT\w*|DEPOT"),
    "food service or non-food retail": (
        r"GNC|GENERAL NUTRITION|VITAMIN SHOPPE|SMOKE|VAPE|TOBACCO|NEWS ?STAND|HUDSON NEWS|PETCO|PETSMART|"
        r"PET SUPPL\w*|EDIBLE ARRANGEMENTS|DUNKIN|STARBUCKS|MCDONALD ?S|RESTAURANT|PIZZA|"
        r"LIQUORS?|WINES?|SPIRITS|BREWERY|BREWING|CATERERS?|CATERING"),
}
# Names like "DELI & SMOKE SHOP" or "GROCERY & 99 CENTS" are bodegas, so these reasons are
# overridden when the name also says grocery, deli, food or supermarket.
OVERRIDABLE_REASONS = {"general merchandise or dollar store", "food service or non-food retail"}
GROCERY_OVERRIDE = r"DELI|GROCERY|GRO|GRCY|GROCERIA|FOODS?|SUPER ?MARKET|SUPERMKT"

CATEGORY_PATTERNS = {  # first match wins; anything else is "other grocery"
    "supermarket": (
        r"SUPER ?MARKETS?|SUPERMKTS?|SUPERMARKE?|SUPERMERCADO|KEY ?FOODS?|C ?TOWN|FINE FARE|"
        r"FOOD UNIVERSE|BRAVO|ASSOCIATED|PIONEER|FOOD ?TOWN|MET ?FOOD|MET ?FRESH|FOOD BAZAAR|"
        r"STOP ?& ?SHOP|SHOP ?RITE|WESTERN BEEF|ALDI|LIDL|FOOD ?D[YI]NASTY|SHOP FAIR|"
        r"COMPARE FOODS?|TRADER JOE ?S|WHOLE FOODS|FOOD ?FAIR|MORTON WILLIAMS|FAIRWAY|GRISTEDES|"
        r"SUPER ?FOODS?|FRESH MARKET|SAVE A LOT|PATHMARK|NETCOST|GOLDEN MANGO|"
        r"MARKET ?PLA\w*|FOOD PLAZA|JUMBO"),
    "convenience or deli": (r"DELI|GROCERY|GROCERIA|MINI ?MART|MINI ?MARKET|CONVENIENCE|BODEGA|"
                            r"7 ?ELEVEN|ELEVEN|FOOD MART|CANDY"),
    "specialty": (r"MEATS?|CARNICERIA|BUTCHER|POULTRY|FISH|SEAFOODS?|MARISCOS|BAKERY|BAKERS|"
                  r"PANADERIA|PASTRY|PASTELERIA|CAKES?|CHEESECAKE|FRUITS?|PRODUCE|VEGETABLES?|"
                  r"NUTS|SPICES?|CHEESE|CHOCOLATES?"),
}

# Scope -> (Ag & Markets categories in the denominator, Census numerator parts)
SCOPES = {
    "A": (["supermarket", "convenience or deli", "other grocery"],
          [("ecnbasic", "4451"), ("nonemp", "4451")]),
    "A_employer": (["supermarket", "convenience or deli", "other grocery"],
                   [("ecnbasic", "4451")]),
    "B": (["supermarket", "other grocery"], [("ecnbasic", "445110")]),
    "C": (["supermarket", "convenience or deli", "other grocery", "specialty"],
          [("ecnbasic", "4451"), ("nonemp", "4451"), ("ecnbasic", "4452"), ("nonemp", "4452")]),
}
SCOPE_LABELS = {
    "A": "NAICS 4451 grocery + convenience, employer + nonemployer",
    "A_employer": "NAICS 4451 grocery + convenience, employer only",
    "B": "NAICS 445110 grocery (no convenience), employer only",
    "C": "NAICS 4451 + 4452 grocery + specialty food, employer + nonemployer",
}
# (variant, scope, Ag & Markets vintage, sq ft treatment); the first row is the central estimate
VARIANTS = [
    ("central", "A", "2023", "impute"),
    ("employer_only", "A_employer", "2023", "impute"),
    ("grocery_445110_only", "B", "2023", "impute"),
    ("with_specialty_4452", "C", "2023", "impute"),
    ("current_agmarkets_list", "A", "current", "impute"),
    ("known_sqft_only", "A", "2023", "known_only"),
]


def _compile(pattern: str) -> re.Pattern:
    return re.compile(rf"\b(?:{pattern})\b")


EXCLUDE_RE = {k: _compile(v) for k, v in EXCLUDE_PATTERNS.items()}
OVERRIDE_RE = _compile(GROCERY_OVERRIDE)
CATEGORY_RE = {k: _compile(v) for k, v in CATEGORY_PATTERNS.items()}


def census_request(dataset: str, naics: str, key: str | None) -> dict:
    fields = "ESTAB,RCPTOT,EMP,PAYANN" if dataset == "ecnbasic" else "NESTAB,NRCPTOT"
    params = {"get": f"NAICS2022_LABEL,{fields}", "NAICS2022": naics, **GEO}
    if key:
        params["key"] = key
    r = SESSION.get(f"{API_BASE}/{dataset}", params=params, timeout=180)
    r.raise_for_status()
    header, row = r.json()[:2]
    rec = dict(zip(header, row))
    employer = dataset == "ecnbasic"
    return {
        "dataset": dataset,
        "source": "employer (Economic Census)" if employer else "nonemployer (NES)",
        "naics2022": naics,
        "label": rec["NAICS2022_LABEL"],
        "establishments": int(rec["ESTAB" if employer else "NESTAB"]),
        "sales_usd": int(rec["RCPTOT" if employer else "NRCPTOT"]) * 1000,
        "employees": int(rec["EMP"]) if employer else None,
        "payroll_usd": int(rec["PAYANN"]) * 1000 if employer else None,
        "year": CENSUS_YEAR,
        "geography": "Bronx County, NY (36005)",
        "api_url": f"{API_BASE}/{dataset}",
    }


def load_census() -> tuple[pd.DataFrame, str]:
    key = census_api_key()
    try:
        census = pd.DataFrame([census_request(d, n, key) for d, n in CENSUS_QUERIES])
        census.to_csv(RAW_CENSUS_CSV, index=False)
        return census, "api"
    except Exception as exc:  # noqa: BLE001
        if RAW_CENSUS_CSV.exists():
            print(f"Census API failed ({exc}); using cached {RAW_CENSUS_CSV.relative_to(ROOT)}")
            return pd.read_csv(RAW_CENSUS_CSV, dtype={"naics2022": str}), "cached file"
        sys.exit(
            f"Census API failed ({exc}) and no cached file. Download from data.census.gov:\n"
            "  - EC2244BASIC, Bronx County NY: NAICS 4451, 445110, 445131, 4452 "
            "(establishments, sales, employees, payroll)\n"
            "  - Nonemployer Statistics 2022, Bronx County NY: NAICS 4451, 4452\n"
            f"and save them to {RAW_CENSUS_CSV} with columns: dataset (ecnbasic/nonemp), "
            "naics2022, establishments, sales_usd (dollars), employees, payroll_usd.")


def census_value(census: pd.DataFrame, parts: list[tuple[str, str]], col: str) -> float:
    idx = census.set_index(["dataset", "naics2022"])
    return float(sum(idx.loc[p, col] for p in parts))


def normalize_name(s: pd.Series) -> pd.Series:
    return (s.fillna("").str.upper().str.replace(r"[^A-Z0-9&]+", " ", regex=True)
            .str.replace(r"\s+", " ", regex=True).str.strip())


def classify(name: str, codes: str, sqft: float) -> tuple[str, str]:
    """(exclude_reason, category) for one Ag & Markets row."""
    if "A" not in codes:
        return "not a store license", ""
    if WAREHOUSE_CODES & set(codes):
        return "warehouse, wholesale or plant license", ""
    for reason, rx in EXCLUDE_RE.items():
        if rx.search(name) and not (reason in OVERRIDABLE_REASONS and OVERRIDE_RE.search(name)):
            return reason, ""
    if pd.notna(sqft) and sqft > MAX_SQFT:
        return f"over {MAX_SQFT:,} sq ft", ""
    for cat, rx in CATEGORY_RE.items():
        if rx.search(name):
            return "", cat
    return "", "other grocery"


def load_agmarkets(vintage: str) -> pd.DataFrame:
    if vintage == "2023":
        df = pd.read_csv(AGM_2023_CSV, dtype=str)
        df = df[df["county"].str.upper() == "BRONX"].copy()
        df["codes"] = df["estab_type"].fillna("").str.replace(r"^J", "", regex=True)
    else:
        df = pd.read_csv(AGM_CURRENT_CSV, dtype=str)
        df["codes"] = df["estab_type"].fillna("")
    df["vintage"] = vintage
    df["name"] = normalize_name(df["dba_name"].fillna(df["entity_name"]))
    sq = pd.to_numeric(df["square_footage"], errors="coerce")
    df["sqft_recorded"] = sq.where(sq >= MIN_SQFT)

    labels = [classify(n, c, s) for n, c, s in zip(df["name"], df["codes"], df["sqft_recorded"])]
    df["exclude_reason"] = [r for r, _ in labels]
    df["category"] = [c for _, c in labels]
    df["keep"] = df["exclude_reason"].eq("").astype(int)

    kept = df["keep"] == 1
    medians = df[kept].groupby("category")["sqft_recorded"].median()
    df["sqft_imputed"] = (kept & df["sqft_recorded"].isna()).astype(int)
    df["sqft"] = df["sqft_recorded"].fillna(df["category"].map(medians)).where(kept)
    cols = ["vintage", "license_number", "estab_type", "dba_name", "entity_name", "street_number",
            "street_name", "zip_code", "square_footage", "sqft_recorded", "sqft_imputed", "sqft",
            "category", "keep", "exclude_reason"]
    return df[cols]


def rate_row(variant: str, scope: str, vintage: str, sqft_mode: str, stores: pd.DataFrame,
             census: pd.DataFrame, cpi_factor: float) -> dict:
    categories, parts = SCOPES[scope]
    members = stores[(stores["vintage"] == vintage) & (stores["keep"] == 1)
                     & stores["category"].isin(categories)]
    sales = census_value(census, parts, "sales_usd")
    n_members = len(members)
    n_known = int(members["sqft_recorded"].notna().sum())
    if sqft_mode == "impute":
        sqft_total = members["sqft"].sum()
        numerator = sales
    else:
        sqft_total = members["sqft_recorded"].sum()
        numerator = sales * n_known / n_members
    employer_parts = [p for p in parts if p[0] == "ecnbasic"]
    employer_sales = census_value(census, employer_parts, "sales_usd")
    employees = census_value(census, employer_parts, "employees")
    nonemp_parts = [p for p in parts if p[0] == "nonemp"]
    rate_2022 = numerator / sqft_total
    return {
        "variant": variant,
        "scope": SCOPE_LABELS[scope],
        "agmarkets_vintage": vintage,
        "sqft_treatment": sqft_mode,
        "census_sales_usd": round(sales),
        "numerator_usd": round(numerator),
        "census_employer_establishments": int(census_value(census, employer_parts, "establishments")),
        "census_nonemployer_establishments": (
            int(census_value(census, nonemp_parts, "establishments")) if nonemp_parts else 0),
        "agmarkets_stores": n_members,
        "agmarkets_stores_known_sqft": n_known,
        "share_stores_imputed": round(1 - n_known / n_members, 3),
        "share_sqft_imputed": (round(members.loc[members["sqft_imputed"] == 1, "sqft"].sum()
                                     / members["sqft"].sum(), 3) if sqft_mode == "impute" else 0.0),
        "sqft_total": round(sqft_total),
        "sales_per_sqft_2022": round(rate_2022, 2),
        "sales_per_sqft_2024": round(rate_2022 * cpi_factor, 2),
        "sales_per_sqft_week_2024": round(rate_2022 * cpi_factor / 52, 2),
        "sales_per_employee_2024": round(employer_sales / employees * cpi_factor),
    }


def cpi_ratio() -> tuple[float, float, float]:
    base = cpi_year(CENSUS_YEAR)["value"].mean()
    target = cpi_year(TARGET_YEAR)["value"].mean()
    return target / base, base, target


def main() -> None:
    census, census_source = load_census()
    print(census[["source", "naics2022", "label", "establishments", "sales_usd", "employees"]]
          .to_string(index=False))

    cpi_factor, cpi_base, cpi_target = cpi_ratio()
    print(f"\nCPI food at home NY ({CPI_SERIES}): {CENSUS_YEAR} {cpi_base:.3f} -> "
          f"{TARGET_YEAR} {cpi_target:.3f}, factor {cpi_factor:.4f}")

    stores = pd.concat([load_agmarkets("2023"), load_agmarkets("current")], ignore_index=True)
    stores.to_csv(STORES_OUT_CSV, index=False)

    rates = pd.DataFrame([rate_row(v, s, vin, m, stores, census, cpi_factor)
                          for v, s, vin, m in VARIANTS])
    rates.to_csv(RATES_OUT_CSV, index=False)
    central = rates.iloc[0]
    rate = central["sales_per_sqft_2024"]
    per_employee = central["sales_per_employee_2024"]

    rev = pd.read_csv(REVENUE_J_CSV, dtype={"license_number": str})
    out = rev[["store", "address", "license_number", "square_footage", "employees_2024", "p_j"]].copy()
    out["sales_per_sqft_2024"] = rate
    out["revenue_census_central"] = (out["square_footage"] * rate).round(-3)
    out["revenue_census_low"] = (out["square_footage"] * rates["sales_per_sqft_2024"].min()).round(-3)
    out["revenue_census_high"] = (out["square_footage"] * rates["sales_per_sqft_2024"].max()).round(-3)
    out["Q_j_census"] = (out["revenue_census_central"] / out["p_j"]).round()
    out["revenue_census_per_employee"] = (out["employees_2024"] * per_employee).round(-3)
    out["revenue_rusa_2024"] = rev["revenue_rusa_2024"]
    out["revenue_fmi"] = rev["revenue_size_based"]
    out["Revenue_j_current"] = rev["Revenue_j"]
    out = out.sort_values("revenue_census_central", ascending=False)
    out.to_csv(REVENUE_OUT_CSV, index=False)

    m_row = pd.read_csv(MARKET_M_CSV).set_index("acs_year").loc[TARGET_YEAR]
    market_m = float(m_row["M_usd_nyc_scaled"])
    totals = {
        "census_central": out["revenue_census_central"].sum(),
        "census_low": out["revenue_census_low"].sum(),
        "census_high": out["revenue_census_high"].sum(),
        "referenceusa_current_Revenue_j": out["Revenue_j_current"].sum(),
        "fmi_national": out["revenue_fmi"].sum(),
    }

    matched = stores[stores["keep"] == 1]
    meta = {
        "census_source": census_source,
        "census_year": CENSUS_YEAR,
        "census_queries": [f"{API_BASE}/{d}?NAICS2022={n}&for=county:005&in=state:36"
                           for d, n in CENSUS_QUERIES],
        "census_note": ("445131 convenience retailers are published as 0 for the Bronx "
                        "(suppressed); the 4451 total includes them. Nonemployer Statistics "
                        "have no 445110 row at county level."),
        "cpi_series": CPI_SERIES,
        "cpi_annual_avg": {str(CENSUS_YEAR): round(cpi_base, 3), str(TARGET_YEAR): round(cpi_target, 3)},
        "cpi_factor": round(cpi_factor, 4),
        "agmarkets_files": {"2023": str(AGM_2023_CSV.relative_to(ROOT)),
                            "current": str(AGM_CURRENT_CSV.relative_to(ROOT))},
        "filter_rules": {
            "keep": "operation_type Store with establishment code A (store)",
            "exclude_codes": sorted(WAREHOUSE_CODES),
            "exclude_name_patterns": EXCLUDE_PATTERNS,
            "grocery_override": {"reasons": sorted(OVERRIDABLE_REASONS), "pattern": GROCERY_OVERRIDE},
            "category_patterns": CATEGORY_PATTERNS,
            "sqft_missing_below": MIN_SQFT,
            "sqft_excluded_above": MAX_SQFT,
            "imputation": "median recorded sq ft of kept stores in the same category and vintage",
        },
        "excluded_counts": {v: stores[stores["vintage"] == v]["exclude_reason"]
                            .replace("", "kept").value_counts().to_dict() for v in ("2023", "current")},
        "kept_by_category": {v: matched[matched["vintage"] == v]["category"].value_counts().to_dict()
                             for v in ("2023", "current")},
        "central_variant": central.to_dict(),
        "market_size_M_2024_nyc_scaled": market_m,
        "nine_store_totals": {k: round(v) for k, v in totals.items()},
        "nine_store_share_of_M": {k: round(v / market_m, 3) for k, v in totals.items()},
    }
    META_JSON.write_text(json.dumps(meta, indent=2, default=str), encoding="utf-8")

    pd.set_option("display.width", 220)
    print("\nAg & Markets Bronx rows by outcome (2023 archive):")
    print(meta["excluded_counts"]["2023"])
    print("\nSales per sq ft variants:")
    print(rates[["variant", "agmarkets_stores", "census_employer_establishments",
                 "census_nonemployer_establishments", "share_stores_imputed", "sqft_total",
                 "sales_per_sqft_2022", "sales_per_sqft_2024", "sales_per_sqft_week_2024"]]
          .to_string(index=False))
    print(f"\nCentral rate: ${rate:,.0f}/sq ft/yr (${rate / 52:,.2f}/wk), {TARGET_YEAR} dollars")
    print(out.drop(columns=["address", "license_number", "sales_per_sqft_2024"]).to_string(index=False))
    print(f"\nMarket size M ({TARGET_YEAR}, NYC-scaled): ${market_m:,.0f}")
    for k, v in totals.items():
        print(f"  9-store total, {k}: ${v:,.0f} ({v / market_m:.0%} of M)")
    print(f"\nSaved outputs to {OUT_DIR.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
