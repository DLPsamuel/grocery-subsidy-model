# Git LFS team guide

This document tells teammates (and coding agents) how to install Git LFS, pull large data files, and decide when to use LFS for new commits. Follow it whenever working with files under `data/`, especially large SNAP retailer dumps.

## Why Git LFS

GitHub **warns** on files larger than **50 MB** and **rejects** files larger than **100 MB** when stored as normal git blobs.

This repo uses [Git Large File Storage (LFS)](https://git-lfs.com/) for large raw artifacts so the team can share the same files without hitting that limit.

### Files tracked with LFS in this repo

| Path | Role |
|------|------|
| `data/stores/snap_retailers_us_raw.csv` | US-wide SNAP retailer raw extract (~91 MB) |
| `data/stores/snap_retailers_raw_sample_cols.csv` | Related large SNAP CSV (~91 MB) |
| `data/stores/**/*.zip` | Zip archives under stores (e.g. SNAP locator dumps) |

Smaller **CD2-filtered** CSVs/GeoJSONs (ACS, BLS, `snap_bronx_cd2.csv`, etc.) stay in **normal git** — do not put every file on LFS.

Patterns live in the repo-root [`.gitattributes`](../.gitattributes).

## Same paths for everyone

All scripts resolve data from the **repository root**, not a personal absolute path:

- `code/data_paths.py` defines `ROOT`, `DATA`, `GEO_DIR`, `ACS_DIR`, `BLS_DIR`, `STORES_DIR`
- After clone + LFS pull, large files appear as normal files under `data/stores/` (and other `data/` subfolders)

**Do:** import or use paths from `code/data_paths.py` (or paths relative to repo root).  
**Do not:** hardcode machine-specific paths like `C:\Users\...` or `/Users/...`.

```text
<repo>/
  code/data_paths.py   → ROOT / "data" / ...
  data/
    stores/            ← LFS large files land here after git lfs pull
    acs/
    bls/
    geography/
```

## One-time install (every teammate machine)

### 1. Install the Git LFS program

**Windows (winget):**

```bash
winget install GitHub.GitLFS --accept-package-agreements --accept-source-agreements
```

**macOS (Homebrew):**

```bash
brew install git-lfs
```

**Linux (Debian/Ubuntu):**

```bash
sudo apt-get update && sudo apt-get install git-lfs
```

Or download from: https://git-lfs.com/

### 2. Enable LFS hooks for your user

```bash
git lfs install
```

Run this once per machine (not once per clone). Confirm with:

```bash
git lfs version
```

## Get the large files

Repo: `https://github.com/DLPsamuel/grocery-subsidy-model.git`

### Fresh clone (preferred)

```bash
git lfs install
git clone https://github.com/DLPsamuel/grocery-subsidy-model.git
cd grocery-subsidy-model
```

A modern `git clone` with LFS installed usually fetches LFS objects automatically. If large CSVs are missing or tiny, run:

```bash
git lfs pull
```

### Existing clone (especially after an LFS history migration)

If `main` was rewritten to move large files into LFS, reset to the remote and pull LFS objects:

```bash
git lfs install
git fetch origin
git reset --hard origin/main
git lfs pull
```

Coordinate with the team before `reset --hard` if you have unpushed local commits.

## Verify access

```bash
git lfs ls-files
```

You should see the large SNAP CSVs and zip paths listed.

Check file size on disk (should be ~90 MB for the SNAP CSVs, **not** a few hundred bytes):

```bash
# Windows PowerShell
Get-Item data/stores/snap_retailers_us_raw.csv, data/stores/snap_retailers_raw_sample_cols.csv |
  Select-Object Name, @{N='MB';E={[math]::Round($_.Length/1MB,1)}}

# macOS / Linux
ls -lh data/stores/snap_retailers_us_raw.csv data/stores/snap_retailers_raw_sample_cols.csv
```

**Pointer stub (bad — need `git lfs pull`):** a tiny text file containing lines like:

```text
version https://git-lfs.github.com/spec/v1
oid sha256:...
size 95123456
```

**Real file (good):** opens as a normal CSV with many rows; size on disk matches `size` above.

Then run project code as usual (`python code/...`). Paths under `data/` work the same for every teammate.

## Team habits going forward

Use these rules for humans and agents deciding how to commit data.

### When to use LFS

| Situation | Action |
|-----------|--------|
| New file **>~50 MB** | Track with LFS **before** `git add` |
| Raw dump **zip** under `data/stores/` | Covered by existing `data/stores/**/*.zip` pattern |
| Small CD2 / ACS / BLS extracts | Normal git (no LFS) |
| Regenerable raw dump already downloadable by a script | Prefer script + small outputs; only LFS-commit if the team needs the exact binary shared |

### How to add a new LFS-tracked file

1. Ensure Git LFS is installed (`git lfs install`).
2. Add a pattern if needed:

   ```bash
   git lfs track "data/stores/my_new_huge_file.csv"
   # or a pattern, e.g. git lfs track "data/raw/**/*.parquet"
   ```

3. Commit **`.gitattributes`** (created/updated by `git lfs track`) **before or together with** the large file — never push a large file as a normal blob first.
4. `git add .gitattributes <large-file>` → commit → push.

### After every `git pull`

If a tracked large file looks like a pointer stub (`oid sha256`), run:

```bash
git lfs pull
```

### Quota awareness

LFS storage and bandwidth count against the **repo owner** GitHub plan (Free typically **1 GB storage** and **1 GB bandwidth / month**). Prefer:

- Keeping only necessary large raw files on LFS
- Reusing an existing clone + `git lfs pull` instead of frequent full re-clones
- Committing small filtered extracts for day-to-day analysis

## Do / don’t checklist (for agents)

**Do**

- Read `.gitattributes` before adding large data files
- Use `git lfs track` and commit `.gitattributes` before/with large adds
- Resolve data via `code/data_paths.py` or repo-relative `data/...` paths
- Prefer CD2-scoped outputs in normal git
- Run `git lfs pull` if pointer stubs appear after clone/pull
- Tell the user if a commit would exceed ~50 MB without LFS

**Don’t**

- `git add` a >50 MB file without an LFS pattern already in `.gitattributes`
- Hardcode absolute local paths in scripts or notebooks
- Put every CSV in LFS “just in case”
- Rewrite git history (`lfs migrate`, force-push) without team coordination
- Assume a tiny “CSV” is valid data — check for `oid sha256` pointer text first
