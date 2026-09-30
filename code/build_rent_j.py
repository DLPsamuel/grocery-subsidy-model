"""Combine the rent estimates for the 9 CD2 candidate stores into Rent_j (Appendix F, Lead S).

Inputs
  - Option 1, DOF estimated gross income per sq ft from each lot's 2024-25 Notice of Property
    Value (data/rent/nopv_income_fy2025.csv, from build_rent_nopv.py).
  - Option 2, asking rents from Bronx retail listings
    (data/rent/listings/bronx_retail_listings.csv, collected from Crexi and by hand).
  - ReferenceUSA "Rent Expenses" ranges (Data Axle's modeled estimate), for comparison.
  - The old placeholder, store sq ft x $27.50 (midpoint of the unsourced $20-35 range).

Rent_j rule, in order:
  1. DOF notice for the store's own lot, where usable (single-use store buildings, or small
     shops on multi-storefront lots).
  2. Otherwise, median listing rent for the store's size group x store sq ft, using listings in
     the CD2-area ZIP codes if there are at least MIN_COMPS, else all Bronx listings.
  3. Otherwise, median DOF notice rent of the usable lots in the same size group x store sq ft.
Rent_j_low / Rent_j_high: listing p25-p75 when there are enough listings, otherwise the
min-max of the usable DOF notice lots in the same size group.

Listing rents are 2026 asking rents; the notices describe fiscal year 2025. Asking rents are
usually above the rents tenants actually pay after concessions.
"""
from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RENT_DIR = ROOT / "data" / "rent"
LOTS_CSV = ROOT / "data" / "tax" / "candidate_store_lots.csv"
NOPV_CSV = RENT_DIR / "nopv_income_fy2025.csv"
LISTINGS_CSV = RENT_DIR / "listings" / "bronx_retail_listings.csv"
RUSA_CSV = ROOT / "data" / "referenceusa" / "referenceusa_cd2_grocery_download_edited.csv"
COMPS_OUT = RENT_DIR / "rent_comps_summary.csv"
OUT_CSV = RENT_DIR / "rent_j_cd2_candidate_stores.csv"

LARGE_STORE_SQFT = 5000
CD2_AREA_ZIPS = {"10459", "10474", "10455", "10451", "10456", "10460"}
MIN_COMPS = 5
OLD_RENT_PSF = 27.50


def size_group(sqft: float) -> str:
    return "large (5,000+ sq ft)" if sqft >= LARGE_STORE_SQFT else "small (under 5,000 sq ft)"


def load_listings() -> pd.DataFrame:
    """Listings converted to annual rent per sq ft; rows noted 'exclude' are dropped."""
    df = pd.read_csv(LISTINGS_CSV, dtype={"zip": str})
    if df.empty:
        return df
    df["sqft"] = pd.to_numeric(df["sqft"], errors="coerce")
    rent = pd.to_numeric(df["asking_rent_psf_yr"], errors="coerce")
    basis = df["rent_basis"].fillna("psf_yr").str.strip()
    factor = basis.map({"psf_yr": 1.0, "psf_mo": 12.0}).fillna(1.0)
    df["rent_psf_yr"] = rent * factor
    total_mo = basis == "monthly_total"
    df.loc[total_mo, "rent_psf_yr"] = rent[total_mo] * 12 / df.loc[total_mo, "sqft"]
    total_yr = basis == "annual_total"
    df.loc[total_yr, "rent_psf_yr"] = rent[total_yr] / df.loc[total_yr, "sqft"]
    keep = df["rent_psf_yr"].notna() & df["sqft"].gt(0)
    keep &= ~df["notes"].fillna("").str.contains("exclude", case=False)
    df = df[keep].copy()
    df["size_group"] = df["sqft"].map(size_group)
    df["area"] = df["zip"].str[:5].isin(CD2_AREA_ZIPS).map({True: "CD2-area ZIPs", False: "rest of Bronx"})
    return df


def summarize_comps(listings: pd.DataFrame) -> pd.DataFrame:
    rows = []
    if listings.empty:
        return pd.DataFrame(columns=["area", "size_group", "n", "p25", "median", "p75", "min", "max"])
    for area, sub_a in [("CD2-area ZIPs", listings[listings["area"] == "CD2-area ZIPs"]), ("all Bronx", listings)]:
        for grp, sub in [("all sizes", sub_a)] + list(sub_a.groupby("size_group")):
            r = sub["rent_psf_yr"]
            rows.append({"area": area, "size_group": grp, "n": len(r),
                         "p25": r.quantile(0.25), "median": r.median(), "p75": r.quantile(0.75),
                         "min": r.min(), "max": r.max()})
    out = pd.DataFrame(rows)
    out[["p25", "median", "p75", "min", "max"]] = out[["p25", "median", "p75", "min", "max"]].round(2)
    return out


def comps_for(summary: pd.DataFrame, grp: str) -> tuple[pd.Series | None, bool]:
    """Listing stats for a size group (CD2-area ZIPs first, then all Bronx) and whether n >= MIN_COMPS."""
    best = None
    for area in ("CD2-area ZIPs", "all Bronx"):
        m = summary[(summary["area"] == area) & (summary["size_group"] == grp)]
        if m.empty:
            continue
        if m.iloc[0]["n"] >= MIN_COMPS:
            return m.iloc[0], True
        if best is None or m.iloc[0]["n"] > best["n"]:
            best = m.iloc[0]
    return best, False


def parse_rusa_range(s) -> tuple[float | None, float | None]:
    """'$10,000 to $25,000' -> (10000, 25000); 'Less than $10,000' -> (0, 10000)."""
    if not isinstance(s, str):
        return None, None
    nums = [float(x.replace(",", "")) for x in re.findall(r"\$([\d,]+)", s)]
    if s.lower().startswith("less than") and nums:
        return 0.0, nums[0]
    if len(nums) >= 2:
        return nums[0], nums[1]
    return None, None


def main() -> None:
    lots = pd.read_csv(LOTS_CSV, dtype={"license_number": str, "bbl": str})
    nopv = pd.read_csv(NOPV_CSV, dtype={"license_number": str, "bbl": str})
    listings = load_listings()
    summary = summarize_comps(listings)
    summary.to_csv(COMPS_OUT, index=False)

    df = lots.merge(nopv[["license_number", "nopv_bldg_class", "nopv_gross_sqft", "nopv_gross_income",
                          "rent_psf_nopv", "rent_nopv", "nopv_usable"]], on="license_number", how="left")
    df["size_group"] = df["store_sqft"].map(size_group)

    usable = df[df["nopv_usable"] == "usable"]
    peer = usable.groupby("size_group")["rent_psf_nopv"].agg(["median", "min", "max"])

    rusa = pd.read_csv(RUSA_CSV, dtype={"license_number": str}, low_memory=False)
    rusa["license_number"] = rusa["license_number"].str.replace(r"\.0$", "", regex=True)
    rusa = rusa.dropna(subset=["license_number"]).drop_duplicates("license_number")
    rusa = rusa[["license_number", "Rent Expenses"]].copy()
    rng = rusa["Rent Expenses"].map(parse_rusa_range)
    rusa["rent_rusa_low"] = [a for a, _ in rng]
    rusa["rent_rusa_high"] = [b for _, b in rng]
    df = df.merge(rusa[["license_number", "Rent Expenses", "rent_rusa_low", "rent_rusa_high"]],
                  on="license_number", how="left").rename(columns={"Rent Expenses": "rent_rusa_range"})

    df["rent_old_27_50"] = df["store_sqft"] * OLD_RENT_PSF

    cols = {k: [] for k in ("comps_basis", "rent_psf_comps_p25", "rent_psf_comps_median", "rent_psf_comps_p75",
                            "rent_psf_nopv_peer_median", "Rent_j", "Rent_j_low", "Rent_j_high",
                            "rent_psf_used", "rent_source")}
    for _, r in df.iterrows():
        stats, enough = comps_for(summary, r["size_group"])
        comps = stats if enough else None
        if stats is None:
            cols["comps_basis"].append("no listings")
        else:
            cols["comps_basis"].append(f"{stats['area']}, n={int(stats['n'])}"
                                       + ("" if enough else f" (fewer than {MIN_COMPS}; not used)"))
        cols["rent_psf_comps_p25"].append(stats["p25"] if stats is not None else None)
        cols["rent_psf_comps_median"].append(stats["median"] if stats is not None else None)
        cols["rent_psf_comps_p75"].append(stats["p75"] if stats is not None else None)
        pr = peer.loc[r["size_group"]] if r["size_group"] in peer.index else None
        cols["rent_psf_nopv_peer_median"].append(pr["median"] if pr is not None else None)

        sq = r["store_sqft"]
        if r["nopv_usable"] == "usable":
            psf, lo, hi = r["rent_psf_nopv"], None, None
            if comps is not None:
                lo, hi = comps["p25"], comps["p75"]
            elif pr is not None:
                lo, hi = pr["min"], pr["max"]
            src = "DOF notice 2024-25, own lot"
        elif comps is not None:
            psf, lo, hi = comps["median"], comps["p25"], comps["p75"]
            src = f"listing median ({comps['area']}, {r['size_group']}); own-lot notice {r['nopv_usable'].split(':')[0]}"
        elif pr is not None:
            psf, lo, hi = pr["median"], pr["min"], pr["max"]
            src = f"DOF notice median of usable {r['size_group']} lots; own-lot notice {r['nopv_usable'].split(':')[0]}"
        else:
            psf, lo, hi, src = None, None, None, "no estimate"
        cols["rent_psf_used"].append(round(psf, 2) if psf is not None else None)
        cols["Rent_j"].append(round(psf * sq) if psf is not None else None)
        cols["Rent_j_low"].append(round(min(lo, psf) * sq) if lo is not None and psf is not None else None)
        cols["Rent_j_high"].append(round(max(hi, psf) * sq) if hi is not None and psf is not None else None)
        cols["rent_source"].append(src)
    for k, v in cols.items():
        df[k] = v

    out = df[["store", "address", "license_number", "bbl", "store_sqft", "size_group",
              "nopv_bldg_class", "nopv_gross_sqft", "nopv_gross_income", "rent_psf_nopv", "rent_nopv", "nopv_usable",
              "rent_psf_nopv_peer_median", "comps_basis", "rent_psf_comps_p25", "rent_psf_comps_median",
              "rent_psf_comps_p75", "rent_rusa_range", "rent_rusa_low", "rent_rusa_high", "rent_old_27_50",
              "rent_psf_used", "Rent_j", "Rent_j_low", "Rent_j_high", "rent_source"]]
    out = out.sort_values("Rent_j", ascending=False)
    out.to_csv(OUT_CSV, index=False)

    pd.set_option("display.width", 250)
    pd.set_option("display.max_colwidth", 70)
    print("Listing comps (annual $/sq ft):")
    print(summary.to_string(index=False) if not summary.empty else "  none yet")
    print()
    print(out[["store", "store_sqft", "rent_psf_nopv", "rent_psf_comps_median", "rent_rusa_range",
               "rent_old_27_50", "rent_psf_used", "Rent_j", "Rent_j_low", "Rent_j_high", "rent_source"]].to_string(index=False))
    print(f"\nTotal Rent_j (9 stores): ${out['Rent_j'].sum():,.0f}")
    print(f"Saved {OUT_CSV.relative_to(ROOT)} and {COMPS_OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
