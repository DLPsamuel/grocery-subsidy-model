"""Rent_j v2 for the 9 CD2 candidate stores: same rule as build_rent_j.py, applied to the
occupied floor area from build_store_occupancy.py instead of Ag & Markets sq ft.

Rent_j rule, in order:
  1. DOF notice rent per sq ft for the store's own lot, where usable, x occupied sq ft.
  2. Otherwise, median listing rent for the store's size group x occupied sq ft, if there are at
     least MIN_COMPS listings.
  3. Otherwise, median DOF notice rent of usable lots in the same size group x occupied sq ft.
Size groups use occupied sq ft. The old placeholder ($27.50 x Ag & Markets sq ft) and the v1
Rent_j are kept for comparison.

Reads existing v1 outputs only; writes data/rent/v2/rent_j_cd2_candidate_stores_v2.csv.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

from build_rent_j import (MIN_COMPS, NOPV_CSV, OLD_RENT_PSF, OUT_CSV as RENT_V1_CSV, RUSA_CSV,
                          comps_for, load_listings, parse_rusa_range, size_group, summarize_comps)

ROOT = Path(__file__).resolve().parents[1]
OCC_CSV = ROOT / "data" / "tax" / "v2" / "store_occupancy_v2.csv"
OUT_DIR = ROOT / "data" / "rent" / "v2"
OUT_CSV = OUT_DIR / "rent_j_cd2_candidate_stores_v2.csv"


def main() -> None:
    occ = pd.read_csv(OCC_CSV, dtype={"license_number": str, "bbl": str})
    nopv = pd.read_csv(NOPV_CSV, dtype={"license_number": str, "bbl": str})
    v1 = pd.read_csv(RENT_V1_CSV, dtype={"license_number": str})
    summary = summarize_comps(load_listings())

    df = occ[["license_number", "store", "address", "bbl", "agm_sqft", "occupancy_basis", "occupied_sqft"]].merge(
        nopv[["license_number", "nopv_bldg_class", "nopv_gross_sqft", "nopv_gross_income",
              "rent_psf_nopv", "nopv_usable"]], on="license_number", how="left")
    df["size_group"] = df["occupied_sqft"].map(size_group)

    usable = df[df["nopv_usable"] == "usable"]
    peer = usable.groupby("size_group")["rent_psf_nopv"].agg(["median", "min", "max"])

    rusa = pd.read_csv(RUSA_CSV, dtype={"license_number": str}, low_memory=False)
    rusa["license_number"] = rusa["license_number"].str.replace(r"\.0$", "", regex=True)
    rusa = rusa.dropna(subset=["license_number"]).drop_duplicates("license_number")
    rusa = rusa[["license_number", "Rent Expenses"]].copy()
    rng = rusa["Rent Expenses"].map(parse_rusa_range)
    rusa["rent_rusa_low"] = [a for a, _ in rng]
    rusa["rent_rusa_high"] = [b for _, b in rng]
    df = df.merge(rusa, on="license_number", how="left").rename(columns={"Rent Expenses": "rent_rusa_range"})

    df["rent_old_27_50"] = df["agm_sqft"] * OLD_RENT_PSF
    df = df.merge(v1[["license_number", "Rent_j"]].rename(columns={"Rent_j": "Rent_j_v1"}),
                  on="license_number", how="left")

    cols = {k: [] for k in ("comps_basis", "rent_psf_nopv_peer_median", "rent_psf_used",
                            "Rent_j", "Rent_j_low", "Rent_j_high", "rent_source")}
    for _, r in df.iterrows():
        stats, enough = comps_for(summary, r["size_group"])
        comps = stats if enough else None
        if stats is None:
            cols["comps_basis"].append("no listings")
        else:
            cols["comps_basis"].append(f"{stats['area']}, n={int(stats['n'])}"
                                       + ("" if enough else f" (fewer than {MIN_COMPS}; not used)"))
        pr = peer.loc[r["size_group"]] if r["size_group"] in peer.index else None
        cols["rent_psf_nopv_peer_median"].append(pr["median"] if pr is not None else None)

        sq = r["occupied_sqft"]
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
    df["Rent_j_change_vs_v1"] = df["Rent_j"] - df["Rent_j_v1"]

    out = df[["store", "address", "license_number", "bbl", "agm_sqft", "occupancy_basis", "occupied_sqft",
              "size_group", "nopv_bldg_class", "nopv_gross_sqft", "nopv_gross_income", "rent_psf_nopv", "nopv_usable",
              "rent_psf_nopv_peer_median", "comps_basis", "rent_rusa_range", "rent_rusa_low", "rent_rusa_high",
              "rent_old_27_50", "Rent_j_v1", "rent_psf_used", "Rent_j", "Rent_j_low", "Rent_j_high",
              "Rent_j_change_vs_v1", "rent_source"]]
    out = out.sort_values("Rent_j", ascending=False)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out.to_csv(OUT_CSV, index=False)

    pd.set_option("display.width", 250)
    pd.set_option("display.max_colwidth", 60)
    print(out[["store", "agm_sqft", "occupied_sqft", "size_group", "rent_psf_used", "Rent_j_v1", "Rent_j",
               "Rent_j_low", "Rent_j_high", "rent_source"]].to_string(index=False))
    print(f"\nTotal Rent_j v2: ${out['Rent_j'].sum():,.0f} (v1 ${out['Rent_j_v1'].sum():,.0f}); "
          f"range ${out['Rent_j_low'].sum():,.0f} to ${out['Rent_j_high'].sum():,.0f}")
    print(f"Saved {OUT_CSV.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
