"""
Phase 3: Match CD2 store addresses to BBL, Tax_j, and Rent_j.

Inputs: Phase 2 store CSVs (Ag & Markets, SNAP, DOHMH)
Outputs: data/phase3/tax_rent_*.csv, caches, success rates JSON
"""
from __future__ import annotations

import json
import re
import sys
import time
from pathlib import Path
from typing import Any

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from data_paths import DATA, SESSION, STORES_DIR  # noqa: E402

PHASE3_DIR = DATA / "phase3"
PHASE3_DIR.mkdir(parents=True, exist_ok=True)

GEOSEARCH = "https://geosearch.planninglabs.nyc/v2/search"
PLUTO = "https://data.cityofnewyork.us/resource/64uk-42ks.json"
DOF_CHARGES = "https://data.cityofnewyork.us/resource/scjx-j6np.json"
ASSESSMENT = "https://data.cityofnewyork.us/resource/xw8u-vy7p.json"
ACRIS_LEGALS = "https://data.cityofnewyork.us/resource/8h5j-fqxa.json"
ACRIS_MASTER = "https://data.cityofnewyork.us/resource/bnx9-e6tj.json"
ACRIS_DOC_CODES = "https://data.cityofnewyork.us/resource/7isb-wh4c.json"

# Lease-related ACRIS document types (not AL&R mortgage collateral)
LEASE_DOC_TYPES = {"LEAS", "MLEA", "ASSTO", "TERL", "SUBL"}

# Appendix F Hunts Point market rent range ($/sq-ft/year)
RENT_PSF_LOW = 20.0
RENT_PSF_MID = 27.5
RENT_PSF_HIGH = 35.0

SLEEP = 0.12  # ~8 req/s polite rate limit
BBL_CACHE_PATH = PHASE3_DIR / "bbl_cache.json"
TAX_CACHE_PATH = PHASE3_DIR / "tax_cache.json"
ACRIS_CACHE_PATH = PHASE3_DIR / "acris_cache.json"

ATTEMPTS_LOG: list[dict[str, Any]] = []


def log_attempt(name: str, **kwargs: Any) -> None:
    """Append one API/step attempt record to the in-memory run log."""
    ATTEMPTS_LOG.append({"attempt": name, **kwargs})


def load_json(path: Path) -> dict:
    """Load a JSON file as a dict, or return {} if the file is missing."""
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return {}


def save_json(path: Path, obj: object) -> None:
    """Write JSON atomically (temp file then replace) to avoid partial writes."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    data = json.dumps(obj, indent=2, default=str)
    tmp.write_text(data, encoding="utf-8")
    for _ in range(5):
        try:
            tmp.replace(path)
            return
        except OSError:
            time.sleep(0.2)
    # Last resort: write directly
    path.write_text(data, encoding="utf-8")
    tmp.unlink(missing_ok=True)


def clean_bbl(val: Any) -> str | None:
    """Normalize a BBL to a 10-digit digit string, or None if invalid."""
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return None
    s = str(val).strip()
    if "." in s:
        s = s.split(".", 1)[0]
    s = re.sub(r"\D", "", s)
    if len(s) == 10:
        return s
    return None


def parse_bbl(bbl: str) -> tuple[str, str, str]:
    """Split a 10-digit BBL into borough, block, and lot for ACRIS queries."""
    boro = bbl[0]
    block = str(int(bbl[1:6]))
    lot = str(int(bbl[6:10]))
    return boro, block, lot


def normalize_street(s: str) -> str:
    """Uppercase and abbreviate street tokens (AVE, ST, E/W, etc.)."""
    s = str(s or "").upper().strip()
    s = re.sub(r"\s+", " ", s)
    reps = [
        (r"\bAVENUE\b", "AVE"),
        (r"\bSTREET\b", "ST"),
        (r"\bROAD\b", "RD"),
        (r"\bBOULEVARD\b", "BLVD"),
        (r"\bPLACE\b", "PL"),
        (r"\bDRIVE\b", "DR"),
        (r"\bEAST\b", "E"),
        (r"\bWEST\b", "W"),
        (r"\bNORTH\b", "N"),
        (r"\bSOUTH\b", "S"),
    ]
    for pat, rep in reps:
        s = re.sub(pat, rep, s)
    return s


def build_address(number: Any, street: Any, zipcode: Any = None) -> str:
    """Build a GeoSearch query string from house number, street, and ZIP."""
    num = str(number or "").strip()
    st = normalize_street(street)
    z = str(zipcode or "").strip()[:5]
    parts = [p for p in (num, st) if p and p.lower() != "nan"]
    base = " ".join(parts)
    if not base:
        return ""
    if z and z.lower() != "nan":
        return f"{base}, Bronx, NY {z}"
    return f"{base}, Bronx, NY"


def load_store_frames() -> dict[str, pd.DataFrame]:
    """Load Phase 2 Ag & Markets, SNAP, and DOHMH CD2 store CSVs."""
    frames = {}

    ag = pd.read_csv(STORES_DIR / "agmarkets_bronx_cd2.csv")
    ag["source"] = "agmarkets"
    ag["store_id"] = ag["license_number"].astype(str)
    ag["store_name"] = ag["dba_name"].fillna(ag["entity_name"])
    ag["addr_number"] = ag["street_number"]
    ag["addr_street"] = ag["street_name"]
    ag["addr_zip"] = ag["zip_code"]
    ag["sqft"] = pd.to_numeric(ag.get("square_footage"), errors="coerce")
    frames["agmarkets"] = ag

    snap = pd.read_csv(STORES_DIR / "snap_bronx_cd2.csv")
    snap["source"] = "snap"
    snap["store_id"] = snap["Record ID"].astype(str)
    snap["store_name"] = snap["store_name"]
    snap["addr_number"] = snap["Street Number"]
    snap["addr_street"] = snap["Street Name"]
    snap["addr_zip"] = snap["Zip Code"]
    snap["sqft"] = pd.NA
    frames["snap"] = snap

    dohmh = pd.read_csv(STORES_DIR / "nyc_dohmh_bronx_cd2_grocery.csv")
    dohmh["source"] = "dohmh"
    dohmh["store_id"] = dohmh["camis"].astype(str)
    dohmh["store_name"] = dohmh["dba"]
    dohmh["addr_number"] = dohmh["building"]
    dohmh["addr_street"] = dohmh["street"]
    dohmh["addr_zip"] = dohmh["zipcode"]
    dohmh["sqft"] = pd.NA
    frames["dohmh"] = dohmh

    return frames


def geosearch_bbl(address: str, cache: dict) -> dict:
    """Look up BBL via NYC GeoSearch (cached); return match fields."""
    if not address:
        return {"bbl": None, "method": "empty_address", "label": None, "bin": None}
    if address in cache:
        return cache[address]
    time.sleep(SLEEP)
    try:
        r = SESSION.get(GEOSEARCH, params={"text": address}, timeout=30)
        r.raise_for_status()
        feats = r.json().get("features") or []
        if not feats:
            out = {"bbl": None, "method": "geosearch_no_hit", "label": None, "bin": None}
            cache[address] = out
            return out
        props = feats[0].get("properties") or {}
        pad = (props.get("addendum") or {}).get("pad") or {}
        bbl = clean_bbl(pad.get("bbl"))
        out = {
            "bbl": bbl,
            "method": "geosearch" if bbl else "geosearch_no_bbl",
            "label": props.get("label") or props.get("name"),
            "bin": pad.get("bin"),
            "confidence": props.get("confidence"),
        }
        cache[address] = out
        return out
    except Exception as e:
        out = {"bbl": None, "method": f"geosearch_error:{e}", "label": None, "bin": None}
        cache[address] = out
        return out


def pluto_fallback_bbl(number: Any, street: Any, cache_key: str, cache: dict) -> dict:
    """If GeoSearch fails, try PLUTO address match for a Bronx BBL."""
    if cache_key in cache and cache[cache_key].get("bbl"):
        return cache[cache_key]
    num = str(number or "").strip()
    st = normalize_street(street)
    if not num or not st:
        return {"bbl": None, "method": "pluto_skip", "label": None, "bin": None}
    # PLUTO address often like "770 HUNTS POINT AVENUE"
    time.sleep(SLEEP)
    try:
        where = (
            f"borough='BX' AND address like '{num} %' "
            f"AND upper(address) like '%{st.split()[0]}%'"
        )
        r = SESSION.get(
            PLUTO,
            params={"$where": where, "$limit": "5", "$select": "bbl,address,borough"},
            timeout=60,
        )
        r.raise_for_status()
        rows = r.json() or []
        if not rows:
            out = {"bbl": None, "method": "pluto_no_hit", "label": None, "bin": None}
            cache[cache_key] = out
            return out
        # Prefer exact house number prefix
        pick = rows[0]
        for row in rows:
            addr = str(row.get("address") or "").upper()
            if addr.startswith(num + " "):
                pick = row
                break
        bbl = clean_bbl(pick.get("bbl"))
        out = {
            "bbl": bbl,
            "method": "pluto_fallback" if bbl else "pluto_no_bbl",
            "label": pick.get("address"),
            "bin": None,
        }
        cache[cache_key] = out
        return out
    except Exception as e:
        out = {"bbl": None, "method": f"pluto_error:{e}", "label": None, "bin": None}
        cache[cache_key] = out
        return out


def fetch_pluto(bbl: str) -> dict:
    """Fetch PLUTO assessed-value and lot attributes for a BBL."""
    time.sleep(SLEEP)
    try:
        r = SESSION.get(PLUTO, params={"bbl": bbl, "$limit": "1"}, timeout=60)
        r.raise_for_status()
        rows = r.json() or []
        if not rows:
            return {"pluto_ok": False}
        row = rows[0]
        return {
            "pluto_ok": True,
            "pluto_address": row.get("address"),
            "pluto_ownername": row.get("ownername"),
            "pluto_bldgclass": row.get("bldgclass"),
            "pluto_lotarea": _num(row.get("lotarea")),
            "pluto_bldgarea": _num(row.get("bldgarea")),
            "pluto_assessland": _num(row.get("assessland")),
            "pluto_assesstot": _num(row.get("assesstot")),
            "pluto_exempttot": _num(row.get("exempttot")),
            "pluto_yearbuilt": row.get("yearbuilt"),
            "pluto_zipcode": row.get("zipcode"),
        }
    except Exception as e:
        return {"pluto_ok": False, "pluto_error": str(e)}


def _num(v: Any) -> float | None:
    """Coerce a value to float, or None if missing/invalid."""
    try:
        if v is None or (isinstance(v, float) and pd.isna(v)):
            return None
        return float(v)
    except Exception:
        return None


def fetch_dof_tax(bbl: str) -> dict:
    """Compute annual Tax_j from DOF Property Charges Balance for a BBL."""
    time.sleep(SLEEP)
    try:
        r = SESSION.get(
            DOF_CHARGES,
            params={
                "parid": bbl,
                "code": "CHG",
                "$limit": "50",
                "$order": "taxyear DESC",
            },
            timeout=60,
        )
        r.raise_for_status()
        rows = r.json() or []
        if not rows:
            return {"dof_ok": False, "Tax_j": None}
        # Latest tax year with data
        years = sorted({str(x.get("taxyear")) for x in rows if x.get("taxyear")}, reverse=True)
        taxyear = years[0]
        year_rows = [x for x in rows if str(x.get("taxyear")) == taxyear]
        liab = sum(_num(x.get("sum_liab")) or 0.0 for x in year_rows)
        # If only one quarter present, annualize
        n_q = len({x.get("cycle") for x in year_rows if x.get("cycle")})
        annual = liab
        annualized = False
        if n_q and n_q < 4 and liab > 0:
            annual = liab * (4.0 / n_q)
            annualized = True
        return {
            "dof_ok": True,
            "Tax_j": round(annual, 2),
            "dof_taxyear": taxyear,
            "dof_quarters": n_q,
            "dof_annualized": annualized,
            "dof_sum_liab_raw": round(liab, 2),
            "dof_n_rows": len(year_rows),
        }
    except Exception as e:
        return {"dof_ok": False, "Tax_j": None, "dof_error": str(e)}


def fetch_assessment(bbl: str) -> dict:
    """Attempt DOF Assessment Data lookup for a BBL (often empty)."""
    time.sleep(SLEEP)
    try:
        r = SESSION.get(
            ASSESSMENT,
            params={"parid": bbl, "$limit": "3", "$order": "year DESC"},
            timeout=60,
        )
        r.raise_for_status()
        rows = r.json() or []
        if not rows:
            return {"assessment_ok": False}
        row = rows[0]
        return {
            "assessment_ok": True,
            "assessment_year": row.get("year"),
            "assessment_curmkttot": _num(row.get("curmkttot") or row.get("pymkttot")),
            "assessment_curacttot": _num(row.get("curacttot") or row.get("pyacttot")),
            "assessment_taxclass": row.get("taxclass") or row.get("valclass"),
        }
    except Exception as e:
        return {"assessment_ok": False, "assessment_error": str(e)}


def fetch_acris_lease(bbl: str) -> dict:
    """Find lease-related ACRIS documents for a BBL and any document_amt."""
    boro, block, lot = parse_bbl(bbl)
    time.sleep(SLEEP)
    try:
        r = SESSION.get(
            ACRIS_LEGALS,
            params={
                "borough": boro,
                "block": block,
                "lot": lot,
                "$limit": "100",
                "$order": "good_through_date DESC",
            },
            timeout=60,
        )
        r.raise_for_status()
        legals = r.json() or []
        if not legals:
            return {
                "acris_ok": False,
                "acris_lease_hit": False,
                "Rent_j_acris": None,
                "acris_n_docs": 0,
            }
        doc_ids = list(dict.fromkeys(x["document_id"] for x in legals if x.get("document_id")))
        # Batch master in chunks of 20
        masters = []
        for i in range(0, min(len(doc_ids), 60), 20):
            chunk = doc_ids[i : i + 20]
            where = "document_id in (" + ",".join(f"'{d}'" for d in chunk) + ")"
            time.sleep(SLEEP)
            r2 = SESSION.get(
                ACRIS_MASTER,
                params={"$where": where, "$limit": "50", "$order": "document_date DESC"},
                timeout=60,
            )
            r2.raise_for_status()
            masters.extend(r2.json() or [])

        lease_docs = [m for m in masters if str(m.get("doc_type") or "").upper() in LEASE_DOC_TYPES]
        rent_amt = None
        best = None
        for m in lease_docs:
            amt = _num(m.get("document_amt"))
            if amt and amt > 0:
                if rent_amt is None or amt > rent_amt:
                    rent_amt = amt
                    best = m
        if best is None and lease_docs:
            best = lease_docs[0]

        return {
            "acris_ok": True,
            "acris_lease_hit": bool(lease_docs),
            "acris_n_docs": len(masters),
            "acris_n_lease_docs": len(lease_docs),
            "acris_lease_doc_type": (best or {}).get("doc_type"),
            "acris_lease_doc_date": (best or {}).get("document_date"),
            "acris_lease_doc_id": (best or {}).get("document_id"),
            "Rent_j_acris": rent_amt,  # often null / not annual rent
        }
    except Exception as e:
        return {
            "acris_ok": False,
            "acris_lease_hit": False,
            "Rent_j_acris": None,
            "acris_error": str(e),
        }


def apply_market_rent(sqft: Any) -> dict:
    """Compute low/mid/high annual rent from sq-ft × $20 / $27.50 / $35."""
    s = _num(sqft)
    if s is None or s <= 0:
        return {
            "rent_sqft": None,
            "Rent_j_low": None,
            "Rent_j_mid": None,
            "Rent_j_high": None,
            "rent_market_ok": False,
        }
    return {
        "rent_sqft": s,
        "Rent_j_low": round(s * RENT_PSF_LOW, 2),
        "Rent_j_mid": round(s * RENT_PSF_MID, 2),
        "Rent_j_high": round(s * RENT_PSF_HIGH, 2),
        "rent_market_ok": True,
    }


def enrich_frame(df: pd.DataFrame, source: str, bbl_cache: dict, tax_cache: dict, acris_cache: dict) -> pd.DataFrame:
    """Match BBL and attach tax/rent columns for one store list; choose Rent_j."""
    print(f"\n=== Enriching {source} ({len(df)} rows) ===")
    rows_out = []
    for i, row in df.iterrows():
        address = build_address(row["addr_number"], row["addr_street"], row["addr_zip"])
        geo = geosearch_bbl(address, bbl_cache)
        bbl = geo.get("bbl")
        if not bbl:
            geo2 = pluto_fallback_bbl(row["addr_number"], row["addr_street"], address + "|pluto", bbl_cache)
            if geo2.get("bbl"):
                geo = geo2
                bbl = geo2["bbl"]

        tax = {}
        acris = {}
        if bbl:
            if bbl not in tax_cache:
                pluto = fetch_pluto(bbl)
                dof = fetch_dof_tax(bbl)
                assess = fetch_assessment(bbl)
                tax_cache[bbl] = {**pluto, **dof, **assess}
            tax = tax_cache[bbl]

            if bbl not in acris_cache:
                acris_cache[bbl] = fetch_acris_lease(bbl)
            acris = acris_cache[bbl]

        market = apply_market_rent(row.get("sqft"))

        # Choose rent_method
        if acris.get("Rent_j_acris"):
            rent_method = "acris"
            Rent_j = acris["Rent_j_acris"]
        elif market.get("rent_market_ok"):
            rent_method = "market_rate_sqft"
            Rent_j = market["Rent_j_mid"]
        elif acris.get("acris_lease_hit"):
            rent_method = "acris_lease_no_amount"
            Rent_j = None
        else:
            rent_method = "none"
            Rent_j = None

        out = {
            "source": source,
            "store_id": row["store_id"],
            "store_name": row["store_name"],
            "address_query": address,
            "addr_number": row["addr_number"],
            "addr_street": row["addr_street"],
            "addr_zip": row["addr_zip"],
            "latitude": row.get("latitude"),
            "longitude": row.get("longitude"),
            "bbl": bbl,
            "bbl_method": geo.get("method"),
            "bbl_label": geo.get("label"),
            "bin": geo.get("bin"),
            "Tax_j": tax.get("Tax_j"),
            "dof_taxyear": tax.get("dof_taxyear"),
            "dof_annualized": tax.get("dof_annualized"),
            "pluto_assesstot": tax.get("pluto_assesstot"),
            "pluto_assessland": tax.get("pluto_assessland"),
            "pluto_ownername": tax.get("pluto_ownername"),
            "pluto_bldgclass": tax.get("pluto_bldgclass"),
            "pluto_ok": tax.get("pluto_ok"),
            "dof_ok": tax.get("dof_ok"),
            "assessment_ok": tax.get("assessment_ok"),
            "assessment_year": tax.get("assessment_year"),
            "acris_lease_hit": acris.get("acris_lease_hit"),
            "acris_n_lease_docs": acris.get("acris_n_lease_docs"),
            "acris_lease_doc_type": acris.get("acris_lease_doc_type"),
            "Rent_j_acris": acris.get("Rent_j_acris"),
            "rent_sqft": market.get("rent_sqft"),
            "Rent_j_low": market.get("Rent_j_low"),
            "Rent_j_mid": market.get("Rent_j_mid"),
            "Rent_j_high": market.get("Rent_j_high"),
            "Rent_j": Rent_j,
            "rent_method": rent_method,
        }
        rows_out.append(out)
        if (len(rows_out) % 25) == 0:
            print(f"  {source}: {len(rows_out)}/{len(df)} ...")
            save_json(BBL_CACHE_PATH, bbl_cache)
            save_json(TAX_CACHE_PATH, tax_cache)
            save_json(ACRIS_CACHE_PATH, acris_cache)

    save_json(BBL_CACHE_PATH, bbl_cache)
    save_json(TAX_CACHE_PATH, tax_cache)
    save_json(ACRIS_CACHE_PATH, acris_cache)
    return pd.DataFrame(rows_out)


def success_rates(df: pd.DataFrame, source: str) -> dict:
    """Summarize BBL / Tax_j / Rent_j match rates for a finished frame."""
    n = len(df)
    if n == 0:
        return {"source": source, "n": 0}

    def pct(mask) -> float:
        return round(100.0 * float(mask.sum()) / n, 1)

    has_bbl = df["bbl"].notna()
    has_tax = df["Tax_j"].notna()
    has_pluto = df["pluto_assesstot"].notna()
    has_acris_lease = df["acris_lease_hit"].fillna(False).astype(bool)
    has_market = df["Rent_j_mid"].notna()
    has_any_rent = df["Rent_j"].notna() | has_acris_lease | has_market

    return {
        "source": source,
        "n": n,
        "n_with_bbl": int(has_bbl.sum()),
        "pct_with_bbl": pct(has_bbl),
        "n_with_Tax_j": int(has_tax.sum()),
        "pct_with_Tax_j": pct(has_tax),
        "n_with_pluto_assessed": int(has_pluto.sum()),
        "pct_with_pluto_assessed": pct(has_pluto),
        "n_with_acris_lease": int(has_acris_lease.sum()),
        "pct_with_acris_lease": pct(has_acris_lease),
        "n_with_Rent_j_acris_amount": int(df["Rent_j_acris"].notna().sum()),
        "pct_with_Rent_j_acris_amount": pct(df["Rent_j_acris"].notna()),
        "n_with_market_rent": int(has_market.sum()),
        "pct_with_market_rent": pct(has_market),
        "n_with_any_Rent_j": int(has_any_rent.sum()),
        "pct_with_any_Rent_j": pct(has_any_rent),
        "n_rent_method_acris": int((df["rent_method"] == "acris").sum()),
        "n_rent_method_market": int((df["rent_method"] == "market_rate_sqft").sum()),
        "n_rent_method_none": int((df["rent_method"] == "none").sum()),
    }


def main() -> None:
    """Run Phase 3 end-to-end: load stores, enrich all lists, write CSVs and meta."""
    print("=== Phase 3: Tax_j / Rent_j ===")
    log_attempt(
        "sources_declared",
        geosearch=GEOSEARCH,
        pluto=PLUTO,
        dof_charges=DOF_CHARGES,
        assessment=ASSESSMENT,
        acris_legals=ACRIS_LEGALS,
        acris_master=ACRIS_MASTER,
        acris_doc_codes=ACRIS_DOC_CODES,
        nycdb="deferred (requires Postgres install)",
        taxbills_nyc="deferred (stale 2015 scrape; not used)",
    )

    bbl_cache = load_json(BBL_CACHE_PATH)
    tax_cache = load_json(TAX_CACHE_PATH)
    acris_cache = load_json(ACRIS_CACHE_PATH)

    frames = load_store_frames()
    rates = {}
    for source, df in frames.items():
        enriched = enrich_frame(df, source, bbl_cache, tax_cache, acris_cache)
        out_path = PHASE3_DIR / f"tax_rent_{source}_cd2.csv"
        enriched.to_csv(out_path, index=False)
        rates[source] = success_rates(enriched, source)
        print(json.dumps(rates[source], indent=2))
        payload = dict(rates[source])
        payload["path"] = str(out_path)
        log_attempt("dataset_written", **payload)

    save_json(PHASE3_DIR / "phase3_success_rates.json", rates)
    save_json(PHASE3_DIR / "phase3_attempts_log.json", ATTEMPTS_LOG)
    print("\nAll Phase 3 datasets written to", PHASE3_DIR)


if __name__ == "__main__":
    main()
