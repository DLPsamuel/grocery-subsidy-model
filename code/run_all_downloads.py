"""Run all Phase 2 public data downloads for Bronx CD2."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

SCRIPTS = [
    "download_geography.py",
    "download_acs.py",
    "download_bls_ces.py",
    "download_stores_agmarkets.py",
    "download_stores_snap.py",
    "download_stores_nyc_opendata.py",
]


def main() -> None:
    code_dir = Path(__file__).resolve().parent
    failed = []
    for name in SCRIPTS:
        print("\n" + "=" * 70)
        print(f"RUNNING {name}")
        print("=" * 70)
        rc = subprocess.call([sys.executable, str(code_dir / name)])
        if rc != 0:
            failed.append(name)
            print(f"FAILED: {name} (exit {rc})")
    if failed:
        print("\nCompleted with failures:", failed)
        sys.exit(1)
    print("\nAll downloads completed successfully.")


if __name__ == "__main__":
    main()
