"""Estimate p_j, the 10-item basket price at each candidate CD2 store (Appendix F, Lead R).

Sources:
  - Crossa et al. 2023 (NYC DOHMH 2019 food pricing survey): 10-item basket priced at
    163 NYC supermarkets, Mar-Aug 2019. github.com/nychealth/food-pricing-survey-nyc-2019
  - BLS CPI food at home, New York-Newark-Jersey City (series CUURS12ASAF11), used to
    move 2019 prices to the latest month available.

Method:
  - Store surveyed directly (same address) -> use its own 2019 price.
  - Otherwise -> average of the same chain's Bronx stores in the survey.
  - Chain not surveyed -> average of all Bronx stores.
  - Multiply by CPI(latest month) / CPI(average Mar-Aug 2019).
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[1]
STORES_DIR = ROOT / "data" / "stores"
PRICES_DIR = ROOT / "data" / "prices"
PRICES_DIR.mkdir(parents=True, exist_ok=True)

CROSSA_URL = (
    "https://raw.githubusercontent.com/nychealth/food-pricing-survey-nyc-2019/"
    "main/Cleaned_Pricing_data_imputed_final.csv"
)
CPI_SERIES = "CUURS12ASAF11"
CPI_URL = "https://api.bls.gov/publicAPI/v2/timeseries/data/"
SURVEY_MONTHS = ["M03", "M04", "M05", "M06", "M07", "M08"]  # Mar-Aug 2019

OUT_CSV = PRICES_DIR / "p_j_cd2_candidate_stores.csv"
CROSSA_BRONX_CSV = PRICES_DIR / "crossa_2019_bronx_basket_prices.csv"

# Candidate stores: SNAP-eligible CD2 stores with >= 6,000 sq ft (FRESH minimum),
# from agmarkets_bronx_cd2_snap_eligibility.csv
MIN_SQFT = 6000


def chain_of(name: str) -> str:
    """Normalize store names to a chain label."""
    n = str(name).upper().replace("-", " ")
    for chain in ["KEY FOOD", "FINE FARE", "FOOD UNIVERSE", "C TOWN", "FOOD FAIR"]:
        if chain in n:
            return chain
    return n.strip()


ABBREV = {"AVENUE": "AVE", "STREET": "ST", "ROAD": "RD", "BOULEVARD": "BLVD",
          "EAST": "E", "WEST": "W", "POINT": "PT"}


def street_key(number: object, street: object) -> str:
    """Address key: house number + street name with common abbreviations."""
    words = [ABBREV.get(w, w) for w in str(street).upper().replace(".", "").split()]
    return f"{str(number).split('.')[0].strip()} {' '.join(words)}"


def load_candidates() -> pd.DataFrame:
    ag = pd.read_csv(STORES_DIR / "agmarkets_bronx_cd2_snap_eligibility.csv")
    ag = ag[(ag["snap_eligible"] == 1) & (ag["square_footage"] >= MIN_SQFT)].copy()
    ag["chain"] = ag["dba_name"].map(chain_of)
    ag["addr_key"] = [street_key(n, s) for n, s in zip(ag["street_number"], ag["street_name"])]
    return ag


def load_crossa_bronx() -> pd.DataFrame:
    df = pd.read_csv(CROSSA_URL)
    bx = df[df["BoroName"] == "BRONX"].copy()
    bx["chain"] = bx["StoreName"].map(chain_of)
    parts = bx["StoreAddress"].str.split(n=1)
    bx["addr_key"] = [street_key(p[0], p[1]) for p in parts]
    bx["n_items_imputed"] = bx["missingvalues"]
    # Two survey rows at the same address (e.g. Key Food, 760 Melrose) -> average them
    bx = (
        bx.groupby(["chain", "addr_key"], as_index=False)
        .agg(
            store_name=("StoreName", "first"),
            address=("StoreAddress", "first"),
            cd_code=("CD.Code", "first"),
            basket_2019=("SFB_imp", "mean"),
            n_items_imputed=("n_items_imputed", "max"),
        )
    )
    bx.to_csv(CROSSA_BRONX_CSV, index=False)
    return bx


def cpi_year(year: int) -> pd.DataFrame:
    """Monthly CPI values for one year (v2 API; no key needed for small requests)."""
    body = {"seriesid": [CPI_SERIES], "startyear": str(year), "endyear": str(year)}
    r = requests.post(CPI_URL, json=body, timeout=60)
    r.raise_for_status()
    cpi = pd.DataFrame(r.json()["Results"]["series"][0]["data"])
    # Keep monthly rows with a value (drops annual M13 and months missing in 2025 shutdown)
    cpi = cpi[cpi["period"].str.match(r"M(0[1-9]|1[0-2])") & (cpi["value"] != "-")]
    cpi["value"] = cpi["value"].astype(float)
    return cpi


def cpi_factor() -> tuple[float, str]:
    base = cpi_year(2019)
    base = base[base["period"].isin(SURVEY_MONTHS)]["value"].mean()
    recent = cpi_year(pd.Timestamp.today().year)
    latest = recent.sort_values("period").iloc[-1]
    label = f"{latest['periodName']} {latest['year']}"
    return latest["value"] / base, label


def main() -> None:
    stores = load_candidates()
    crossa = load_crossa_bronx()
    factor, cpi_label = cpi_factor()
    bronx_avg = crossa["basket_2019"].mean()

    out = []
    for _, s in stores.iterrows():
        direct = crossa[(crossa["chain"] == s["chain"]) & (crossa["addr_key"] == s["addr_key"])]
        same_chain = crossa[crossa["chain"] == s["chain"]]
        if not direct.empty:
            p2019, method, n = direct["basket_2019"].iloc[0], "direct match (same store)", 1
        elif not same_chain.empty:
            p2019, method, n = same_chain["basket_2019"].mean(), "same-chain Bronx average", len(same_chain)
        else:
            p2019, method, n = bronx_avg, "all-Bronx average (chain not surveyed)", len(crossa)
        out.append(
            {
                "store": s["dba_name"],
                "address": f"{int(s['street_number'])} {s['street_name']}",
                "snap_store_type": s["snap_store_type"],
                "square_footage": int(s["square_footage"]),
                "method": method,
                "n_survey_stores_used": n,
                "p_j_2019": round(p2019, 2),
                "cpi_factor": round(factor, 4),
                "p_j_current": round(p2019 * factor, 2),
                "price_month": cpi_label,
            }
        )

    result = pd.DataFrame(out).sort_values("square_footage", ascending=False)
    result.to_csv(OUT_CSV, index=False)
    print(f"CPI factor (avg Mar-Aug 2019 -> {cpi_label}): {factor:.4f}")
    print(f"Bronx survey average 2019: ${bronx_avg:.2f} ({len(crossa)} stores)")
    print(result[["store", "method", "n_survey_stores_used", "p_j_2019", "p_j_current"]].to_string(index=False))
    print(f"\nSaved {OUT_CSV.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
