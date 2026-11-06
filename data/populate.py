#!/usr/bin/env python3
"""Export the exact 20 sheets of cases.xlsx to data/<sheet>.csv without changing the workbook.

Run from any directory:
    python data/populate.py
    python data/populate.py --workbook cases.xlsx --out-dir data

CSV files are DERIVED read-only views, never inputs to the generator. Integer values
remain decimal integers and ASCII text stays plain text (no workbook formulas permitted).
"""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import sys

from openpyxl import load_workbook

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "generator"))
from spec import HEADERS  # noqa: E402


def export(workbook: Path, dest: Path) -> dict:
    if not workbook.is_file():
        raise FileNotFoundError(f"No workbook at {workbook}")
    wb = load_workbook(workbook, read_only=True, data_only=False)
    dest.mkdir(parents=True, exist_ok=True)
    manifest = {"source": "cases.xlsx", "sheet_count": len(HEADERS), "files": []}
    try:
        if wb.sheetnames != list(HEADERS):
            raise ValueError("Workbook sheets/order disagree with generator/spec.py")
        for sheet_name, expected_cols in HEADERS.items():
            path = dest / f"{sheet_name}.csv"
            rows = wb[sheet_name].iter_rows(values_only=True)
            header = next(rows)
            if tuple(header) != tuple(expected_cols):
                raise ValueError(f"Wrong columns in {sheet_name}: {header!r}")
            count = 0
            with path.open("w", encoding="ascii", newline="") as out:
                writer = csv.writer(out, lineterminator="\n")
                writer.writerow(header)
                for row in rows:
                    if len(row) != len(header) or any(v is None for v in row):
                        raise ValueError(f"Blank or inconsistent row in {sheet_name} at row {count+2}")
                    if any(isinstance(v, (float, bool)) or not isinstance(v, (str, int)) for v in row):
                        raise ValueError(f"Noninteger or nontext value in {sheet_name} row {count+2}")
                    if any(isinstance(v, str) and v.startswith("=") for v in row):
                        raise ValueError(f"Unexpected formula-like cell in {sheet_name} row {count+2}")
                    writer.writerow(row)
                    count += 1
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            manifest["files"].append({"file": path.name, "rows": count, "sha256": digest})
            print(f"{sheet_name:20s} {count:>8,} records -> {path.name}", flush=True)
        (dest / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="ascii")
        return manifest
    finally:
        wb.close()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--workbook", type=Path, default=ROOT / "cases.xlsx")
    p.add_argument("--out-dir", type=Path, default=ROOT / "data")
    opts = p.parse_args()
    manifest = export(opts.workbook.resolve(), opts.out_dir.resolve())
    print(f"Exported {len(manifest['files'])} CSVs; manifest.json includes row counts and SHA-256 hashes.")


if __name__ == "__main__":
    main()
