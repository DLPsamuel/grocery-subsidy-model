# NOTE: This script is no longer used in the project (Data is manually downloaded)
"""Download BLS CES income / quintile XLSX tables (2020–2024).

Preferred path (user-confirmed 2024 URLs):
  .../mean-item-share-average-standard-error/cu-income-before-taxes-{year}.xlsx
  .../mean-item-share-average-standard-error/cu-income-quintiles-before-taxes-{year}.xlsx

bls.gov often returns HTTP 403 to automated clients. If that happens, open the
URLs in a browser and save the files into data/bls/, then re-run this script
(it will skip existing files and extract food-at-home rows when possible).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from data_paths import BLS_DIR, SESSION  # noqa: E402

BASE = (
    "https://www.bls.gov/cex/tables/calendar-year/"
    "mean-item-share-average-standard-error"
)
YEARS = list(range(2020, 2025))
STEMS = [
    "cu-income-before-taxes",
    "cu-income-quintiles-before-taxes",
]


def urls_for_year(year: int) -> list[tuple[str, str]]:
    out = []
    for stem in STEMS:
        name = f"{stem}-{year}.xlsx"
        out.append((name, f"{BASE}/{name}"))
    return out


def write_url_checklist() -> Path:
    lines = [
        "# Open these in a browser if automated download gets HTTP 403.",
        "# Save each file into data/bls/ with the same filename.",
        "",
    ]
    for year in YEARS:
        for name, url in urls_for_year(year):
            lines.append(f"{name}")
            lines.append(url)
            lines.append("")
    path = BLS_DIR / "ces_xlsx_download_urls.txt"
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def try_download(name: str, url: str) -> tuple[bool, str]:
    dest = BLS_DIR / name
    if dest.exists() and dest.stat().st_size > 5000:
        return True, f"already present ({dest.stat().st_size} bytes)"
    try:
        SESSION.headers.update(
            {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/122.0.0.0 Safari/537.36"
                ),
                "Referer": "https://www.bls.gov/cex/tables.htm",
                "Accept": (
                    "application/vnd.openxmlformats-officedocument"
                    ".spreadsheetml.sheet,*/*"
                ),
            }
        )
        r = SESSION.get(url, timeout=120)
        if r.status_code != 200:
            return False, f"HTTP {r.status_code}"
        ctype = (r.headers.get("content-type") or "").lower()
        if "html" in ctype or len(r.content) < 5000:
            return False, f"blocked/small response ({len(r.content)} bytes, {ctype})"
        dest.write_bytes(r.content)
        return True, f"downloaded ({len(r.content)} bytes)"
    except Exception as e:
        return False, str(e)


def extract_food_rows(xlsx_path: Path) -> pd.DataFrame | None:
    try:
        xl = pd.ExcelFile(xlsx_path)
    except Exception as e:
        print(f"  cannot open {xlsx_path.name}: {e}")
        return None
    frames = []
    for sheet in xl.sheet_names:
        try:
            df = pd.read_excel(xlsx_path, sheet_name=sheet, header=None)
        except Exception:
            continue
        mask = df.astype(str).apply(
            lambda col: col.str.contains("food at home", case=False, na=False)
        ).any(axis=1)
        hit = df.loc[mask].copy()
        if not hit.empty:
            hit.insert(0, "sheet", sheet)
            hit.insert(0, "source_file", xlsx_path.name)
            frames.append(hit)
    if not frames:
        return None
    return pd.concat(frames, ignore_index=True)


def main() -> None:
    BLS_DIR.mkdir(parents=True, exist_ok=True)
    checklist = write_url_checklist()
    print(f"Wrote URL checklist: {checklist}")

    meta = {"downloaded": [], "failed": {}, "sources": {}, "url_base": BASE}
    food_frames = []

    for year in YEARS:
        for name, url in urls_for_year(year):
            print(f"{name} ...")
            ok, msg = try_download(name, url)
            print(f"  {msg}")
            if ok:
                meta["downloaded"].append(name)
                meta["sources"][name] = url
                food = extract_food_rows(BLS_DIR / name)
                if food is not None:
                    food.insert(0, "year", year)
                    food_frames.append(food)
                    food.to_csv(BLS_DIR / f"ces_food_rows_{Path(name).stem}.csv", index=False)
            else:
                meta["failed"][name] = {"url": url, "error": msg}

    if food_frames:
        all_food = pd.concat(food_frames, ignore_index=True)
        all_food.to_csv(BLS_DIR / "ces_food_at_home_rows_from_xlsx.csv", index=False)
        print(f"Extracted food-at-home rows -> ces_food_at_home_rows_from_xlsx.csv")

    with open(BLS_DIR / "bls_xlsx_download_meta.json", "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)

    print(f"OK: {len(meta['downloaded'])}  FAILED: {len(meta['failed'])}")
    if meta["failed"]:
        print(
            "Automated download blocked. Open data/bls/ces_xlsx_download_urls.txt "
            "in a browser, save files into data/bls/, then re-run this script."
        )


if __name__ == "__main__":
    main()
