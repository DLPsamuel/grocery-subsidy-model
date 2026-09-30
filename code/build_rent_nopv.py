"""Rent option 1: DOF's estimated gross income for each candidate store's tax lot, from the
2024-25 Notice of Property Value (NOPV), to match fiscal year 2025 (Appendix F, Rent_j).

DOF values income-producing property (tax classes 2 and 4) with the income approach, using
the income and expense statements (RPIE) owners must file each year. For those lots the NOPV
prints the building's estimated gross square footage, estimated gross income, estimated
expenses, net operating income and capitalization rate. Gross income per sq ft is DOF's
estimate of what space in that building rents for.

  rent_psf_nopv  = estimated gross income / estimated building gross sq ft
  rent_nopv      = rent_psf_nopv x store sq ft (Ag & Markets)

Special cases (flagged, not used directly for Rent_j):
  - Key Food: class 2 apartment building, so gross income includes 63 apartments' rents.
  - Fine Fare: condo unit; condo NOPVs print a market value only, with no income factors.
  - Food Fair: 13,000 sq ft supermarket on a lot with 17 storefronts; the lot average
    ($113/sq ft) reflects small-shop rents.

Usage:
  python code/build_rent_nopv.py                  # find, download and parse the notices
  python code/build_rent_nopv.py --skip-download  # parse PDFs already saved in data/rent/nopv/

Manual download (if the portal blocks the script): see data/rent/README.md.
"""
from __future__ import annotations

import argparse
import io
import re
from pathlib import Path

import pandas as pd
import pypdf
import requests

ROOT = Path(__file__).resolve().parents[1]
RENT_DIR = ROOT / "data" / "rent"
NOPV_DIR = RENT_DIR / "nopv"
LOTS_CSV = ROOT / "data" / "tax" / "candidate_store_lots.csv"
OUT_CSV = RENT_DIR / "nopv_income_fy2025.csv"
LINKS_CSV = NOPV_DIR / "nopv_links.csv"

TAX_YEAR_LABEL = "2024 - 2025"
TAX_YEAR_TAG = "2024-25"

# Large floorplates rent for less per sq ft than small storefronts, so a supermarket on a lot
# with many storefronts is not priced by the lot average.
LARGE_STORE_SQFT = 5000
MULTI_TENANT_UNITS = 5

PTS_SEARCH = "https://a836-pts-access.nyc.gov/care/search/commonsearch.aspx?mode=persprop"
PTS_NOPV = ("https://a836-pts-access.nyc.gov/care/datalets/datalet.aspx?mode=nopv&UseSearch=no"
            "&pin={bbl}&jur=65&taxyr=2025&LMparent=20")

SESSION = requests.Session()
SESSION.headers.update({"User-Agent": "Mozilla/5.0 (grocery-subsidy-analysis; Bronx CD2 research; academic)"})

MONEY = r"\$\s*([\d,]+(?:\.\d+)?)"
FIELDS = {
    "nopv_market_value": r"Market\s*Value:\s*" + MONEY,
    "nopv_assessed_value": r"Assessed\s*Value:\s*" + MONEY,
    "nopv_taxable_value": r"EstimatedPropertyTax\s*\d{4}-\d{2}\s*" + MONEY,
    "nopv_tax_rate": r"x\s*([\d.]+)\s*=",
    "nopv_est_property_tax": r"x\s*[\d.]+\s*=\s*" + MONEY,
    "nopv_tax_class": r"Tax\s*Class:\s*(\w+)",
    "nopv_bldg_class": r"Building\s*Class:\s*(\w+)",
    "nopv_gross_sqft": r"Estimated\s*Building\s*Gross\s*Square\s*Footage:\s*([\d,]+)",
    "nopv_gross_income": r"Estimated\s*Gross\s*Income:\s*" + MONEY,
    "nopv_expenses": r"Estimated\s*Expenses:\s*" + MONEY,
    "nopv_noi": r"net\s*operating\s*income\s*of\s*" + MONEY,
    "nopv_base_cap_rate_pct": r"capitalization\s*rate\s*of\s*([\d.]+)%",
    "nopv_effective_tax_rate_pct": r"effective\s*tax\s*rate\s*of\s*([\d.]+)%",
    "nopv_overall_cap_rate_pct": r"overall\s*capitalization\s*rate\s*is\s*([\d.]+)%",
    "nopv_exemptions": r"property\s*tax\s*exemptions:\s*(.+?)See\s*below",
}
UNITS = r"Units:\s*(?:(\d+)\s*Residential)?\s*-?\s*(?:(\d+)\s*Non-Residential)?"
NUMERIC = [k for k in FIELDS if k not in ("nopv_tax_class", "nopv_bldg_class", "nopv_exemptions")]


def pdf_path(bbl: str) -> Path:
    return NOPV_DIR / f"{bbl}_{TAX_YEAR_TAG}.pdf"


def find_notice_url(bbl: str) -> str | None:
    """Link to the 2024-25 notice on the lot's 'Notices of Property Value' portal page."""
    html = SESSION.get(PTS_NOPV.format(bbl=bbl), timeout=60).text
    for label, url in re.findall(r">(\d{4} - \d{4})</td><td[^>]*><a HREF=([^ >]+)", html):
        if label == TAX_YEAR_LABEL:
            return url
    return None


def download_notices(bbls: list[str]) -> None:
    NOPV_DIR.mkdir(parents=True, exist_ok=True)
    SESSION.get(PTS_SEARCH, timeout=60)
    links = []
    for bbl in bbls:
        url = find_notice_url(bbl)
        status = "no 2024-25 notice listed"
        if url:
            r = SESSION.get(url, timeout=120)
            if r.ok and r.content[:4] == b"%PDF":
                pdf_path(bbl).write_bytes(r.content)
                status = "downloaded"
            else:
                status = f"download failed ({r.status_code}, {r.headers.get('content-type')})"
        links.append({"bbl": bbl, "tax_year": TAX_YEAR_LABEL, "url": url, "status": status})
        print(f"  {bbl}: {status}")
    pd.DataFrame(links).to_csv(LINKS_CSV, index=False)


def parse_notice(path: Path) -> dict:
    text = " ".join(p.extract_text() or "" for p in pypdf.PdfReader(io.BytesIO(path.read_bytes())).pages)
    path.with_suffix(".txt").write_text(text, encoding="utf-8")
    out = {}
    for key, pat in FIELDS.items():
        m = re.search(pat, text, flags=re.I | re.S)
        out[key] = m.group(1).strip() if m else None
    for key in NUMERIC:
        if out[key] is not None:
            out[key] = float(out[key].replace(",", ""))
    m = re.search(UNITS, text)
    out["nopv_units_res"] = int(m.group(1)) if m and m.group(1) else 0
    out["nopv_units_nonres"] = int(m.group(2)) if m and m.group(2) else 0
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--skip-download", action="store_true", help="parse PDFs already in data/rent/nopv/")
    args = ap.parse_args()

    lots = pd.read_csv(LOTS_CSV, dtype={"bbl": str, "pluto_bbl": str, "license_number": str})
    if not args.skip_download:
        print(f"Downloading {TAX_YEAR_LABEL} notices of property value ...")
        download_notices(lots["bbl"].tolist())

    rows = []
    for _, lot in lots.iterrows():
        path = pdf_path(lot["bbl"])
        rec = {"license_number": lot["license_number"], "store": lot["store"], "bbl": lot["bbl"],
               "lot_type": lot["lot_type"], "store_sqft": lot["store_sqft"],
               "nopv_file": path.relative_to(ROOT).as_posix() if path.exists() else None}
        if path.exists():
            rec.update(parse_notice(path))
        rows.append(rec)
    df = pd.DataFrame(rows)

    df["rent_psf_nopv"] = (df["nopv_gross_income"] / df["nopv_gross_sqft"]).round(2)
    df["expense_ratio_nopv"] = (df["nopv_expenses"] / df["nopv_gross_income"]).round(3)
    df["rent_nopv"] = (df["rent_psf_nopv"] * df["store_sqft"]).round(0)

    def usability(r) -> str:
        if pd.isna(r.get("nopv_file")):
            return "no notice"
        if pd.isna(r["nopv_gross_income"]):
            return "no income factors on notice (condo unit valued by market value only)"
        if r["nopv_tax_class"] == "2" or r["nopv_units_res"] > 0:
            return f"residential mixed ({r['nopv_units_res']} apartments): income includes apartment rents, not usable directly"
        if r["store_sqft"] >= LARGE_STORE_SQFT and r["nopv_units_nonres"] >= MULTI_TENANT_UNITS:
            return (f"multi-tenant lot ({r['nopv_units_nonres']} storefronts): average reflects small-shop rents, "
                    "not usable directly for a supermarket")
        return "usable"

    df["nopv_usable"] = df.apply(usability, axis=1)
    df["nopv_note"] = ""
    df.loc[df["lot_type"] == "condo_unit", "nopv_note"] = "condo unit notice; income approach not shown"

    df = df.sort_values("rent_psf_nopv", ascending=False)
    df.to_csv(OUT_CSV, index=False)

    pd.set_option("display.width", 220)
    print(df[["store", "bbl", "nopv_tax_class", "nopv_bldg_class", "nopv_gross_sqft", "nopv_gross_income",
              "rent_psf_nopv", "store_sqft", "rent_nopv", "nopv_est_property_tax", "nopv_usable"]].to_string(index=False))
    print(f"\nSaved {OUT_CSV.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
