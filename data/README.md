# Derived case-data CSV exports

`data/populate.py` exports **one CSV per workbook sheet** from the existing `cases.xlsx` (20 files: `cases.csv`, `crates.csv`, ... , `claims.csv`). These are convenience exports for analysis; **the XLSX is the source of truth**, and no CSV is an input to the generator or validator.

From the repository root, run:

```sh
python data/populate.py
```

The script reads the workbook without editing it, checks the canonical sheet order and headers from `generator/spec.py`, writes UTF-8-compatible ASCII CSV with LF line endings and integer values, and creates `data/manifest.json` containing per-sheet row counts and SHA-256 checksums. Re-running it overwrites only the generated CSV files and the manifest.

Load a single sheet with `csv.DictReader(open("data/crates.csv", encoding="ascii"))`. All CSV fields will be strings: convert numeric columns to integers in analysis code. CSV serial numbers and `case_id` remain text fields where appropriate.
