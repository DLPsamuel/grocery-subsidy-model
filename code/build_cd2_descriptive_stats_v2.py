"""Descriptive statistics for Bronx CD2, v2 (companion to MAIN spec v2).

Answers "are the Low / Mid / High income groups balanced across tracts?" and collects the
other summary numbers the model uses (f_bar, kappa, market size M, store inputs, distances).

Inputs (read only):
  data/acs/cd2_B19001_2024.csv, data/acs/cd2_household_income_summary.csv
  data/geography/bronx_cd2_tracts.geojson
  data/bls/ces_fbar_by_income_group_northeast_cd2weighted.csv
  data/bls/fbar_core_noncore_by_income_group_northeast.csv
  data/bls/kappa_core_basket_share_northeast_cd2weighted.csv
  data/bls/cd2_market_size_M_northeast_cd2weighted.csv
  data/prices/p_j_cd2_candidate_stores.csv
  data/revenue_census_estimate/v2/revenue_j_census_v2_cd2_candidate_stores.csv
  data/revenue_census_estimate/v2/bronx_sales_per_sqft_census_v2.csv
  data/rent/v2/rent_j_cd2_candidate_stores_v2.csv
  data/tax/v2/tax_j_cd2_candidate_stores_v2.csv
  data/distance/d_tract_store_miles.csv, data/distance/d_ij_cd2.csv

Outputs:
  data/descriptive_stats_v2/*.csv
  figures/descriptive_v2/*.png

N.Y.C. Groceries v2 inputs (planned store, 15,000 sq ft):
  Revenue = sq ft x pooled 4451 rate (low / high = min / max of the pooled variants)
  Rent    = sq ft x median DOF rent per sq ft of large (5,000+ sq ft) lots
  Tax     = sq ft x median (Tax_j v2 / occupied sq ft) over the large existing stores
"""
from __future__ import annotations

from pathlib import Path

import geopandas as gpd
import matplotlib
import numpy as np
import pandas as pd
from scipy import stats

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
OUT_DIR = DATA / "descriptive_stats_v2"
FIG_DIR = ROOT / "figures" / "descriptive_v2"
OUT_DIR.mkdir(parents=True, exist_ok=True)
FIG_DIR.mkdir(parents=True, exist_ok=True)

INCOME_CSV = DATA / "acs" / "cd2_B19001_2024.csv"
TREND_CSV = DATA / "acs" / "cd2_household_income_summary.csv"
TRACTS_GEOJSON = DATA / "geography" / "bronx_cd2_tracts.geojson"
CD2_GEOJSON = DATA / "geography" / "bronx_cd2_boundary.geojson"
FBAR_CSV = DATA / "bls" / "ces_fbar_by_income_group_northeast_cd2weighted.csv"
FBAR_CORE_CSV = DATA / "bls" / "fbar_core_noncore_by_income_group_northeast.csv"
KAPPA_CSV = DATA / "bls" / "kappa_core_basket_share_northeast_cd2weighted.csv"
M_CSV = DATA / "bls" / "cd2_market_size_M_northeast_cd2weighted.csv"
PRICE_CSV = DATA / "prices" / "p_j_cd2_candidate_stores.csv"
REV_CSV = DATA / "revenue_census_estimate" / "v2" / "revenue_j_census_v2_cd2_candidate_stores.csv"
RATE_CSV = DATA / "revenue_census_estimate" / "v2" / "bronx_sales_per_sqft_census_v2.csv"
RENT_CSV = DATA / "rent" / "v2" / "rent_j_cd2_candidate_stores_v2.csv"
TAX_CSV = DATA / "tax" / "v2" / "tax_j_cd2_candidate_stores_v2.csv"
DIST_TRACT_CSV = DATA / "distance" / "d_tract_store_miles.csv"
DIST_GROUP_CSV = DATA / "distance" / "d_ij_cd2.csv"

ACS_YEAR = 2024
SQFT_PER_SQMI = 5280 ** 2
GROUPS = [("low", "n_low", "Low (<$25K)"),
          ("mid", "n_mid", "Mid ($25-50K)"),
          ("high", "n_high", "High (>$50K)")]
GROUP_COLORS = {"low": "#d95f02", "mid": "#7570b3", "high": "#1b9e77"}
POOLED_VARIANTS = ["pooled_4451", "all_food_445", "pooled_current_list", "pooled_known_sqft_only"]
LARGE_STORE_SQFT = 5000

NYCG = {"store": "N.Y.C. GROCERIES (PLANNED)", "address": "1215 SPOFFORD AVE",
        "sqft": 15000, "p_j": 28.95, "snap_store_type": "(planned)"}

SHORT = {
    "KEY FOOD": "Key Food",
    "FOOD FAIR FRESH MARKET": "Food Fair",
    "FINE FARE SUPERMARKET": "Fine Fare",
    "FOOD UNIVERSE": "Food Universe",
    "C-TOWN SUPERMARKET": "C-Town (564)",
    "C TOWN SUPERMARKET": "C-Town (809)",
    "ANTILLANA FRESH MEAT MARKET": "Antillana",
    "SAGAL MEAT MARKET": "Sagal",
    "JJ SOUTHERN FARM FRUIT": "JJ Southern Farm",
    "N.Y.C. GROCERIES (PLANNED)": "N.Y.C. Groceries (planned)",
}


# ── households by tract ───────────────────────────────────────────────────────
def build_tracts() -> tuple[pd.DataFrame, gpd.GeoDataFrame]:
    acs = pd.read_csv(INCOME_CSV, dtype={"GEOID": str})
    geo = gpd.read_file(TRACTS_GEOJSON)
    geo["shape_area"] = geo["shape_area"].astype(float)
    df = acs[["GEOID", "n_low", "n_mid", "n_high"]].rename(columns={"GEOID": "tract_id"})
    df = df.merge(geo[["geoid", "ctlabel", "ntaname", "shape_area"]],
                  left_on="tract_id", right_on="geoid").drop(columns="geoid")
    df["n_total"] = df[["n_low", "n_mid", "n_high"]].sum(axis=1)
    df["active_tract"] = df["n_total"] > 0
    for g, col, _ in GROUPS:
        df[f"share_{g}"] = np.where(df["active_tract"], df[col] / df["n_total"].where(df["n_total"] > 0), np.nan)
    df["largest_group"] = np.where(
        df["active_tract"],
        df[["n_low", "n_mid", "n_high"]].idxmax(axis=1).str.replace("n_", ""), "")
    df["area_sq_mi"] = df["shape_area"] / SQFT_PER_SQMI
    df["hh_per_sq_mi"] = np.where(df["active_tract"], df["n_total"] / df["area_sq_mi"], 0.0)
    df = df.drop(columns="shape_area").rename(columns={"ntaname": "nta"})
    df = df.sort_values(["active_tract", "n_total"], ascending=[False, False]).reset_index(drop=True)
    geo = geo.merge(df[["tract_id", "active_tract", "share_low", "share_mid", "share_high"]],
                    left_on="geoid", right_on="tract_id")
    return df, geo


def group_summary(tr: pd.DataFrame) -> pd.DataFrame:
    act = tr[tr["active_tract"]]
    n_total = act["n_total"].sum()
    rows = []
    for g, col, label in GROUPS + [("total", "n_total", "All households")]:
        x = act[col]
        row = {
            "group": label, "total_hh": int(x.sum()), "cd2_share": x.sum() / n_total,
            "n_tracts": len(x), "mean": x.mean(), "sd": x.std(ddof=1),
            "min": x.min(), "p25": x.quantile(0.25), "median": x.median(),
            "p75": x.quantile(0.75), "max": x.max(), "cv": x.std(ddof=1) / x.mean(),
        }
        if g != "total":
            s = act[f"share_{g}"]
            row.update({"within_tract_share_mean": s.mean(), "within_tract_share_sd": s.std(ddof=1),
                        "within_tract_share_min": s.min(), "within_tract_share_max": s.max(),
                        "tracts_where_largest": int((act["largest_group"] == g).sum())})
        rows.append(row)
    return pd.DataFrame(rows)


def dissimilarity(a: pd.Series, b: pd.Series) -> float:
    return 0.5 * np.abs(a / a.sum() - b / b.sum()).sum()


def balance_tests(tr: pd.DataFrame) -> pd.DataFrame:
    act = tr[tr["active_tract"]]
    table = act[["n_low", "n_mid", "n_high"]].to_numpy()
    totals = table.sum(axis=0)
    n = table.sum()

    chi2, p, dof, _ = stats.chi2_contingency(table)
    cramers_v = np.sqrt(chi2 / (n * (min(table.shape) - 1)))
    gof = stats.chisquare(totals)
    small = act.loc[act[["n_low", "n_mid", "n_high"]].min(axis=1).idxmin()]
    small_col = small[["n_low", "n_mid", "n_high"]].astype(int).idxmin()

    rows = [
        ("group_sizes", f"Low {totals[0]:,} / Mid {totals[1]:,} / High {totals[2]:,}",
         "Households, 13 active tracts, ACS 2024"),
        ("largest_to_smallest_group_ratio", round(totals.max() / totals.min(), 3), "Low / Mid"),
        ("gof_equal_thirds_chi2", round(gof.statistic, 1),
         "Chi-square goodness of fit: are the 3 groups equal in size? (df = 2)"),
        ("gof_equal_thirds_p", f"{gof.pvalue:.2e}", "p < 0.05 means group sizes are not equal"),
        ("independence_chi2", round(chi2, 1),
         f"Chi-square test of independence, tract x group (df = {dof})"),
        ("independence_p", f"{p:.2e}",
         "p < 0.05 means group mix differs across tracts (large N makes this easy to reject)"),
        ("cramers_v", round(cramers_v, 3),
         "Effect size for tract x group association: <0.1 negligible, 0.1-0.3 small, 0.3-0.5 moderate"),
        ("dissimilarity_low_mid", round(dissimilarity(act["n_low"], act["n_mid"]), 3),
         "Index of dissimilarity: share of one group that would have to move tracts to match the other's distribution"),
        ("dissimilarity_low_high", round(dissimilarity(act["n_low"], act["n_high"]), 3), ""),
        ("dissimilarity_mid_high", round(dissimilarity(act["n_mid"], act["n_high"]), 3), ""),
        ("smallest_cell", f"{int(small[small_col]):,} ({small_col.replace('n_', '').title()}, tract {small['ctlabel']})",
         "Smallest n_{t,g} among the 39 active consumer groups"),
        ("largest_cell", f"{int(table.max()):,}", "Largest n_{t,g}"),
        ("cells_under_200", int((table < 200).sum()), "Number of the 39 groups with fewer than 200 households"),
    ]
    return pd.DataFrame(rows, columns=["metric", "value", "note"])


def build_trend() -> pd.DataFrame:
    t = pd.read_csv(TREND_CSV)
    for g, col, _ in GROUPS:
        t[f"share_{g}"] = t[col] / t["N_HH"]
    return t[["year", "N_HH", "n_low", "n_mid", "n_high", "share_low", "share_mid", "share_high"]]


# ── food spending and kappa ───────────────────────────────────────────────────
def build_fbar_kappa() -> pd.DataFrame:
    fb = pd.read_csv(FBAR_CSV)
    fb = fb[fb["acs_year"] == ACS_YEAR]
    kp = pd.read_csv(KAPPA_CSV)
    kp = kp[kp["acs_year"] == ACS_YEAR]
    core = pd.read_csv(FBAR_CORE_CSV)
    core = core[(core["acs_year"] == ACS_YEAR) & (core["kappa_version"] == "base")]
    df = fb[["group", "n_hh", "f_bar_weekly_usd_nyc", "f_bar_annual_usd_nyc"]].merge(
        kp[["group", "kappa_low", "kappa_base", "kappa_high"]], on="group").merge(
        core[["group", "f_core_weekly_usd_nyc", "f_noncore_weekly_usd_nyc",
              "M_core_usd_nyc", "M_noncore_usd_nyc"]], on="group")
    df["M_g_usd_nyc"] = df["M_core_usd_nyc"] + df["M_noncore_usd_nyc"]
    return df.rename(columns={"f_core_weekly_usd_nyc": "f_core_weekly_usd_nyc_base",
                              "f_noncore_weekly_usd_nyc": "f_noncore_weekly_usd_nyc_base",
                              "M_core_usd_nyc": "M_core_usd_nyc_base",
                              "M_noncore_usd_nyc": "M_noncore_usd_nyc_base"})


# ── stores ────────────────────────────────────────────────────────────────────
def revenue_rates() -> dict[str, float]:
    r = pd.read_csv(RATE_CSV).set_index("variant")["sales_per_sqft_2024"]
    pooled = r.loc[POOLED_VARIANTS]
    return {"central": r["pooled_4451"], "low": pooled.min(), "high": pooled.max()}


def build_stores(M_usd: float) -> tuple[pd.DataFrame, dict]:
    rev = pd.read_csv(REV_CSV)
    rent = pd.read_csv(RENT_CSV)
    tax = pd.read_csv(TAX_CSV)
    df = rev[["store", "address", "snap_store_type", "square_footage", "p_j",
              "revenue_census_v2", "revenue_census_v2_low", "revenue_census_v2_high",
              "Q_j_census_v2", "share_of_M", "revenue_rusa_2024"]].merge(
        rent[["store", "occupied_sqft", "Rent_j", "Rent_j_low", "Rent_j_high",
              "rent_psf_used", "size_group", "rent_psf_nopv_peer_median"]], on="store").merge(
        tax[["store", "Tax_j", "Tax_j_high"]], on="store")
    df = df.rename(columns={"square_footage": "agm_sqft", "revenue_census_v2": "R_j_v2",
                            "revenue_census_v2_low": "R_j_v2_low",
                            "revenue_census_v2_high": "R_j_v2_high", "Q_j_census_v2": "Q_j_v2"})
    df["tax_psf_occupied"] = df["Tax_j"] / df["occupied_sqft"]

    large = df[df["occupied_sqft"] >= LARGE_STORE_SQFT]
    rates = revenue_rates()
    rent_psf = large["rent_psf_nopv_peer_median"].iloc[0]
    tax_psf = large["tax_psf_occupied"].median()
    sqft = NYCG["sqft"]
    nycg = {
        "store": NYCG["store"], "address": NYCG["address"], "snap_store_type": NYCG["snap_store_type"],
        "agm_sqft": sqft, "occupied_sqft": sqft, "p_j": NYCG["p_j"],
        "R_j_v2": round(sqft * rates["central"], -3), "R_j_v2_low": round(sqft * rates["low"], -3),
        "R_j_v2_high": round(sqft * rates["high"], -3),
        "Rent_j": round(sqft * rent_psf), "Rent_j_low": np.nan, "Rent_j_high": np.nan,
        "rent_psf_used": rent_psf, "Tax_j": round(sqft * tax_psf), "Tax_j_high": np.nan,
        "tax_psf_occupied": tax_psf, "size_group": "large (5,000+ sq ft)",
    }
    nycg["Q_j_v2"] = round(nycg["R_j_v2"] / nycg["p_j"])
    nycg["share_of_M"] = round(nycg["R_j_v2"] / M_usd, 4)
    nycg_meta = {"rate_central": rates["central"], "rate_low": rates["low"], "rate_high": rates["high"],
                 "rent_psf": rent_psf, "tax_psf": tax_psf, "n_large_stores": len(large),
                 "large_stores": ", ".join(SHORT[s] for s in large["store"])}

    df["store_status"] = "existing"
    nycg["store_status"] = "planned"
    df = pd.concat([df, pd.DataFrame([nycg])], ignore_index=True)
    df["store_short"] = df["store"].map(SHORT)
    df["revenue_psf"] = df["R_j_v2"] / df["agm_sqft"]
    df["rent_plus_tax"] = df["Rent_j"] + df["Tax_j"]
    df["rent_plus_tax_share_of_R"] = df["rent_plus_tax"] / df["R_j_v2"]
    df = df.drop(columns=["rent_psf_nopv_peer_median"])
    df.insert(0, "row_type", "store")

    existing = df[df["store_status"] == "existing"]
    num_cols = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]
    summary = []
    for name, fn in [("Total (9 existing)", "sum"), ("Mean (9 existing)", "mean"),
                     ("Median (9 existing)", "median"), ("Min (9 existing)", "min"),
                     ("Max (9 existing)", "max")]:
        row = existing[num_cols].agg(fn).to_dict()
        row.update({"row_type": "summary", "store": name, "store_short": name})
        summary.append(row)
    total = summary[0]
    for c in ["p_j", "rent_psf_used", "tax_psf_occupied", "revenue_psf"]:
        total[c] = np.nan
    total["rent_plus_tax_share_of_R"] = total["rent_plus_tax"] / total["R_j_v2"]
    df = pd.concat([df, pd.DataFrame(summary)], ignore_index=True)
    return df, nycg_meta


# ── distances ─────────────────────────────────────────────────────────────────
def build_distances(tr: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    d = pd.read_csv(DIST_TRACT_CSV, dtype={"tract_id": str})
    d = d.merge(tr[["tract_id", "ctlabel", "n_total", "active_tract"]], on="tract_id")
    act = d[d["active_tract"]].copy()

    def nearest_counts(sub: pd.DataFrame, label: str) -> pd.DataFrame:
        idx = sub.groupby("tract_id")["miles"].idxmin()
        near = sub.loc[idx]
        return near.groupby("store").agg(**{f"tracts_nearest_{label}": ("tract_id", "size"),
                                            f"hh_nearest_{label}": ("n_total", "sum")})

    rows = []
    for store, g in act.groupby("store", sort=False):
        rows.append({"store": store, "store_status": g["store_status"].iloc[0],
                     "min_miles": g["miles"].min(), "mean_miles_unweighted": g["miles"].mean(),
                     "max_miles": g["miles"].max(),
                     "mean_miles_hh_weighted": np.average(g["miles"], weights=g["n_total"])})
    out = pd.DataFrame(rows)
    dij = pd.read_csv(DIST_GROUP_CSV).pivot(index="store", columns="income_group", values="d_ij_miles")
    dij = dij[["low", "mid", "high"]].add_prefix("d_ij_").reset_index()
    out = out.merge(dij, on="store")
    out = out.merge(nearest_counts(act[act["store_status"] == "existing"], "9stores"),
                    on="store", how="left")
    out = out.merge(nearest_counts(act, "10stores"), on="store", how="left")
    fill = [c for c in out.columns if c.startswith(("tracts_nearest", "hh_nearest"))]
    out[fill] = out[fill].fillna(0).astype(int)
    out.insert(1, "store_short", out["store"].map(SHORT))
    out = out.sort_values("mean_miles_hh_weighted").reset_index(drop=True)

    matrix = act.pivot(index="ctlabel", columns="store", values="miles")
    return out, matrix


def nearest_store_hh_distance(matrix: pd.DataFrame, tr: pd.DataFrame, planned: str) -> tuple[float, float]:
    w = tr.set_index("ctlabel").loc[matrix.index, "n_total"]
    m9 = matrix.drop(columns=[planned]).min(axis=1)
    m10 = matrix.min(axis=1)
    return np.average(m9, weights=w), np.average(m10, weights=w)


# ── CD2 characteristics ───────────────────────────────────────────────────────
def build_characteristics(tr, stores, M_row, matrix) -> pd.DataFrame:
    act = tr[tr["active_tract"]]
    existing = stores[(stores["row_type"] == "store") & (stores["store_status"] == "existing")]
    n_hh = act["n_total"].sum()
    near9, near10 = nearest_store_hh_distance(matrix, tr, NYCG["store"])
    nta = act.groupby("nta")["n_total"].agg(["sum", "size"])
    rows = [
        ("Census tracts (2020 geography)", len(tr), "tracts", "bronx_cd2_tracts.geojson"),
        ("Tracts with households (active)", len(act), "tracts", "cd2_B19001_2024.csv"),
        ("Tracts with 0 households (omitted)", int((~tr["active_tract"]).sum()),
         ", ".join(tr.loc[~tr["active_tract"], "ctlabel"]), "cd2_B19001_2024.csv"),
        ("Consumer groups i = (t, g)", len(act) * 3, "groups", "13 tracts x 3 income groups"),
        ("Households N_HH", int(n_hh), "households", "ACS 2024 B19001"),
        ("Land area, all 16 tracts", tr["area_sq_mi"].sum(), "sq mi", "tract shape_area"),
        ("Land area, 13 active tracts", act["area_sq_mi"].sum(), "sq mi", "tract shape_area"),
        ("Household density, active tracts", n_hh / act["area_sq_mi"].sum(), "households per sq mi", ""),
        ("Median tract household density", act["hh_per_sq_mi"].median(), "households per sq mi", ""),
    ]
    for name, r in nta.iterrows():
        rows.append((f"Households in {name}", int(r["sum"]), f"{int(r['size'])} active tracts", "NTA 2020"))
    rows += [
        ("Existing large grocery stores", len(existing), "stores", "large_grocery_stores_cd2.csv"),
        ("Stores per 10,000 households", len(existing) / n_hh * 10000, "stores", ""),
        ("Grocery floor area, 9 stores (Ag & Markets)", existing["agm_sqft"].sum(), "sq ft", ""),
        ("Grocery floor area per household", existing["agm_sqft"].sum() / n_hh, "sq ft per household", ""),
        ("Annual grocery market M", M_row["M_usd_nyc_scaled"], "USD per year", "cd2_market_size_M_northeast_cd2weighted.csv"),
        ("M per household", M_row["M_usd_nyc_scaled"] / n_hh, "USD per year", ""),
        ("Average weekly food-at-home spending (CD2)", M_row["f_bar_weekly_cd2_nyc"], "USD per week", ""),
        ("9-store revenue, v2 pooled rate", existing["R_j_v2"].sum(), "USD per year", "revenue_j_census_v2_cd2_candidate_stores.csv"),
        ("9-store revenue as share of M", existing["R_j_v2"].sum() / M_row["M_usd_nyc_scaled"], "share", ""),
        ("Median basket price p_j (9 stores)", existing["p_j"].median(), "USD per 10-item basket", "p_j_cd2_candidate_stores.csv"),
        ("HH-weighted distance to nearest existing store", near9, "miles (Manhattan)", "d_tract_store_miles.csv"),
        ("HH-weighted distance to nearest store incl. N.Y.C. Groceries", near10, "miles (Manhattan)", "d_tract_store_miles.csv"),
    ]
    return pd.DataFrame(rows, columns=["metric", "value", "unit_or_detail", "source"])


# ── figures ───────────────────────────────────────────────────────────────────
def fig_stacked(tr: pd.DataFrame) -> None:
    act = tr[tr["active_tract"]].sort_values("n_total", ascending=False)
    fig, ax = plt.subplots(figsize=(9, 4.5), dpi=150)
    bottom = np.zeros(len(act))
    x = np.arange(len(act))
    for g, col, label in GROUPS:
        ax.bar(x, act[col], bottom=bottom, color=GROUP_COLORS[g], label=label, edgecolor="white", lw=0.5)
        bottom += act[col].to_numpy()
    for xi, tot in zip(x, act["n_total"]):
        ax.text(xi, tot + 25, f"{tot:,}", ha="center", fontsize=7)
    ax.set_xticks(x, act["ctlabel"], fontsize=8)
    ax.set_xlabel("Census tract (13 with households; 19.04, 93.02, 117.02 have 0)")
    ax.set_ylabel("Households")
    ax.set_title("Households by tract and income group (ACS 2024)", fontweight="bold")
    ax.legend(frameon=False, fontsize=8)
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(FIG_DIR / "hh_by_tract_income_group.png")
    plt.close(fig)


def fig_share(tr: pd.DataFrame) -> None:
    act = tr[tr["active_tract"]].sort_values("share_low", ascending=False)
    cd2 = act[["n_low", "n_mid", "n_high"]].sum() / act["n_total"].sum()
    fig, ax = plt.subplots(figsize=(9, 4.5), dpi=150)
    x = np.arange(len(act))
    bottom = np.zeros(len(act))
    for g, col, label in GROUPS:
        ax.bar(x, act[f"share_{g}"], bottom=bottom, color=GROUP_COLORS[g], label=label,
               edgecolor="white", lw=0.5)
        bottom += act[f"share_{g}"].to_numpy()
    cum = np.cumsum(cd2.to_numpy())[:2]
    for level, name in zip(cum, ["Low | Mid", "Mid | High"]):
        ax.axhline(level, color="black", ls="--", lw=0.9)
        ax.text(len(act) - 0.4, level + 0.01, f"CD2 average {name} boundary ({level:.0%})",
                ha="right", fontsize=7)
    ax.set_xticks(x, act["ctlabel"], fontsize=8)
    ax.set_ylim(0, 1)
    ax.yaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1.0))
    ax.set_xlabel("Census tract (sorted by Low share)")
    ax.set_ylabel("Share of tract households")
    ax.set_title("Income-group mix by tract vs. CD2 average", fontweight="bold")
    ax.legend(frameon=False, fontsize=8, loc="upper center", bbox_to_anchor=(0.5, -0.15), ncol=3)
    fig.tight_layout()
    fig.savefig(FIG_DIR / "hh_share_by_tract_income_group.png")
    plt.close(fig)


def fig_box(tr: pd.DataFrame) -> None:
    act = tr[tr["active_tract"]]
    fig, axes = plt.subplots(1, 2, figsize=(9, 4), dpi=150)
    rng = np.random.default_rng(0)
    for ax, kind in zip(axes, ["count", "share"]):
        data = [act[col] if kind == "count" else act[f"share_{g}"] for g, col, _ in GROUPS]
        ax.boxplot(data, tick_labels=[lab for _, _, lab in GROUPS], widths=0.5,
                   medianprops=dict(color="black"))
        for k, ((g, _, _), vals) in enumerate(zip(GROUPS, data), start=1):
            ax.scatter(k + rng.uniform(-0.12, 0.12, len(vals)), vals, color=GROUP_COLORS[g],
                       s=18, alpha=0.8, zorder=3)
        ax.tick_params(labelsize=8)
        ax.spines[["top", "right"]].set_visible(False)
    axes[0].set_ylabel(r"Households per tract, $n_{t,g}$")
    axes[0].set_title("Households per tract", fontsize=10, fontweight="bold")
    axes[1].set_ylabel("Share of tract households")
    axes[1].yaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1.0))
    axes[1].set_title("Within-tract share", fontsize=10, fontweight="bold")
    fig.suptitle("Distribution across the 13 active tracts", fontweight="bold")
    fig.tight_layout()
    fig.savefig(FIG_DIR / "hh_by_income_group_boxplot.png")
    plt.close(fig)


def fig_choropleth(geo: gpd.GeoDataFrame) -> None:
    cd2 = gpd.read_file(CD2_GEOJSON)
    fig, axes = plt.subplots(1, 3, figsize=(12, 4.8), dpi=150)
    vmax = np.nanmax(geo[["share_low", "share_mid", "share_high"]].to_numpy())
    for ax, (g, _, label) in zip(axes, GROUPS):
        act = geo[geo["active_tract"]]
        zero = geo[~geo["active_tract"]]
        act.plot(column=f"share_{g}", ax=ax, cmap="YlOrRd", vmin=0, vmax=vmax,
                 edgecolor="#777", linewidth=0.5)
        zero.plot(ax=ax, facecolor="white", edgecolor="#9dafc0", hatch="///", linewidth=0.5)
        cd2.boundary.plot(ax=ax, color="#1a3a5c", linewidth=1.2)
        for _, r in act.iterrows():
            pt = r.geometry.representative_point()
            ax.text(pt.x, pt.y, f"{r[f'share_{g}']:.0%}", ha="center", va="center", fontsize=5.5)
        ax.set_title(f"{label} share", fontsize=10, fontweight="bold")
        ax.set_axis_off()
    sm = plt.cm.ScalarMappable(cmap="YlOrRd", norm=plt.Normalize(0, vmax))
    cbar = fig.colorbar(sm, ax=axes, fraction=0.025, pad=0.02)
    cbar.ax.yaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1.0))
    fig.suptitle("Share of tract households in each income group (hatched = 0 households, omitted)",
                 fontweight="bold")
    fig.savefig(FIG_DIR / "income_group_share_choropleth.png", bbox_inches="tight")
    plt.close(fig)


def fig_trend(trend: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(7, 4), dpi=150)
    for g, col, label in GROUPS:
        ax.plot(trend["year"], trend[col], marker="o", color=GROUP_COLORS[g], label=label)
        ax.text(trend["year"].iloc[-1] + 0.08, trend[col].iloc[-1], f"{int(trend[col].iloc[-1]):,}",
                va="center", fontsize=7, color=GROUP_COLORS[g])
    ax.set_xticks(trend["year"])
    ax.set_ylabel("Households")
    ax.set_xlabel("ACS 5-year vintage")
    ax.set_title("CD2 households by income group, 2020-2024", fontweight="bold")
    ax.legend(frameon=False, fontsize=8)
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(FIG_DIR / "hh_by_income_group_trend.png")
    plt.close(fig)


def fig_fbar(fk: pd.DataFrame) -> None:
    sub = fk[fk["group"] != "CD2 overall"]
    fig, ax = plt.subplots(figsize=(7, 4), dpi=150)
    x = np.arange(len(sub))
    ax.bar(x, sub["f_core_weekly_usd_nyc_base"], color="#2b8cbe",
           label=r"Core basket ($\kappa_{\mathrm{base}}$)")
    ax.bar(x, sub["f_noncore_weekly_usd_nyc_base"], bottom=sub["f_core_weekly_usd_nyc_base"],
           color="#a6bddb", label="Non-core")
    for xi, (tot, k) in enumerate(zip(sub["f_bar_weekly_usd_nyc"], sub["kappa_base"])):
        ax.text(xi, tot + 2, f"\\${tot:.2f}/wk\n$\\kappa$ = {k:.3f}", ha="center", fontsize=7.5)
    ax.set_xticks(x, sub["group"])
    ax.set_ylabel("Weekly food-at-home spending (USD, NYC-scaled)")
    ax.set_ylim(0, sub["f_bar_weekly_usd_nyc"].max() * 1.25)
    ax.set_title(r"$\bar{f}_g$ by income group, core vs. non-core (2024)", fontweight="bold")
    ax.legend(frameon=False, fontsize=8, loc="upper left")
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(FIG_DIR / "fbar_core_noncore_by_group.png")
    plt.close(fig)


def fig_stores(stores: pd.DataFrame) -> None:
    s = stores[stores["row_type"] == "store"].sort_values("R_j_v2")
    y = np.arange(len(s))
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.8), dpi=150, sharey=True)
    colors = ["#e65100" if st == "planned" else "#1565c0" for st in s["store_status"]]
    err = np.vstack([s["R_j_v2"] - s["R_j_v2_low"], s["R_j_v2_high"] - s["R_j_v2"]]) / 1e6
    axes[0].barh(y, s["R_j_v2"] / 1e6, color=colors, xerr=err, error_kw=dict(lw=0.8, capsize=2))
    axes[0].set_xlabel(r"Annual revenue $R_j$ v2 (USD millions; whiskers = \$698-\$845/sq ft range)")
    axes[0].set_title(r"Revenue (v2 pooled \$801/sq ft)", fontsize=10, fontweight="bold")
    axes[1].barh(y, s["Rent_j"] / 1e3, color="#78909c", label=r"$\mathrm{Rent}_j$ v2")
    axes[1].barh(y, s["Tax_j"] / 1e3, left=s["Rent_j"] / 1e3, color="#ffb74d", label=r"$\mathrm{Tax}_j$ v2")
    axes[1].set_xlabel("USD thousands per year")
    axes[1].set_title("Rent + property tax (v2)", fontsize=10, fontweight="bold")
    axes[1].legend(frameon=False, fontsize=8, loc="lower right")
    axes[0].set_yticks(y, s["store_short"], fontsize=8)
    for ax in axes:
        ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(FIG_DIR / "store_revenue_rent_tax.png")
    plt.close(fig)


def fig_distance_heatmap(matrix: pd.DataFrame, tr: pd.DataFrame) -> None:
    order_t = tr[tr["active_tract"]].sort_values("n_total", ascending=False)["ctlabel"]
    m = matrix.loc[order_t]
    m = m[m.mean().sort_values().index]
    fig, ax = plt.subplots(figsize=(10, 5.5), dpi=150)
    im = ax.imshow(m.to_numpy(), cmap="viridis_r", aspect="auto")
    for i in range(m.shape[0]):
        for j in range(m.shape[1]):
            v = m.iat[i, j]
            ax.text(j, i, f"{v:.2f}", ha="center", va="center", fontsize=6.5,
                    color="white" if v > m.to_numpy().mean() else "black")
    ax.set_xticks(range(m.shape[1]), [SHORT[c] for c in m.columns], rotation=35, ha="right", fontsize=8)
    ax.set_yticks(range(m.shape[0]), [f"Tract {t}" for t in m.index], fontsize=8)
    fig.colorbar(im, ax=ax, label="Manhattan distance (miles)")
    ax.set_title(r"Tract-to-store distance $d_{tj}$ (13 active tracts x 10 stores)", fontweight="bold")
    fig.tight_layout()
    fig.savefig(FIG_DIR / "distance_tract_store_heatmap.png")
    plt.close(fig)


def main() -> None:
    tr, geo = build_tracts()
    summary = group_summary(tr)
    balance = balance_tests(tr)
    trend = build_trend()
    fk = build_fbar_kappa()
    M_row = pd.read_csv(M_CSV).set_index("acs_year").loc[ACS_YEAR]
    stores, nycg_meta = build_stores(M_row["M_usd_nyc_scaled"])
    dist, matrix = build_distances(tr)
    chars = build_characteristics(tr, stores, M_row, matrix)

    tr.to_csv(OUT_DIR / "hh_by_tract_income_group_v2.csv", index=False, float_format="%.4f")
    summary.to_csv(OUT_DIR / "income_group_summary_stats_v2.csv", index=False, float_format="%.4f")
    balance.to_csv(OUT_DIR / "income_group_balance_v2.csv", index=False)
    trend.to_csv(OUT_DIR / "hh_by_income_group_trend_v2.csv", index=False, float_format="%.4f")
    fk.to_csv(OUT_DIR / "fbar_kappa_summary_2024_v2.csv", index=False, float_format="%.4f")
    stores.to_csv(OUT_DIR / "store_summary_stats_v2.csv", index=False, float_format="%.4f")
    dist.to_csv(OUT_DIR / "distance_summary_by_store_v2.csv", index=False, float_format="%.4f")
    chars.to_csv(OUT_DIR / "cd2_characteristics_v2.csv", index=False, float_format="%.4f")

    fig_stacked(tr)
    fig_share(tr)
    fig_box(tr)
    fig_choropleth(geo)
    fig_trend(trend)
    fig_fbar(fk)
    fig_stores(stores)
    fig_distance_heatmap(matrix, tr)

    pd.set_option("display.width", 220)
    pd.set_option("display.max_columns", 40)
    print("Households by tract\n", tr.to_string(), "\n")
    print("Group summary\n", summary.to_string(), "\n")
    print("Balance\n", balance.to_string(), "\n")
    print("Trend\n", trend.to_string(), "\n")
    print("f_bar / kappa\n", fk.to_string(), "\n")
    print("Stores\n", stores.to_string(), "\n")
    print("N.Y.C. Groceries inputs\n", nycg_meta, "\n")
    print("Distances\n", dist.to_string(), "\n")
    print("CD2 characteristics\n", chars.to_string(), "\n")
    print(f"Saved CSVs to {OUT_DIR.relative_to(ROOT)} and figures to {FIG_DIR.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
