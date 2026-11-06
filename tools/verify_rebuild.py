#!/usr/bin/env python3
"""Check the workbook's canonical content SHA-256; optionally regenerate seed 18.

Quick (no generator execution):
    python tools/verify_rebuild.py
Full end-to-end rebuild in a TEMPORARY directory:
    python tools/verify_rebuild.py --regenerate

Never overwrites cases.xlsx, output PDFs or tracked CSVs.
"""
import argparse
import hashlib
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory

from openpyxl import load_workbook

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_SHA256 = "4c569e38aaedf5feec1b53c0898f5ff3fe3a61304ac70e67a11a9f6655a6ceb0"


def content_digest(path: Path) -> str:
    """Match generator/writer.py's *content* digest, not XLSX ZIP bytes.

    The generator includes the header as a list in the repr; using a tuple
    for that one element gives a different digest even for the same workbook.
    """
    digest = hashlib.sha256()
    wb = load_workbook(path, read_only=True, data_only=False)
    try:
        for sheet in wb:
            rows = sheet.iter_rows(values_only=True)
            header = list(next(rows))
            digest.update(repr((sheet.title, header)).encode("utf-8"))
            for row in rows:
                digest.update(repr(tuple(row)).encode("utf-8"))
    finally:
        wb.close()
    return digest.hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workbook", type=Path, default=ROOT / "cases.xlsx")
    parser.add_argument("--regenerate", action="store_true")
    args = parser.parse_args()
    original = args.workbook.resolve()
    if not original.is_file():
        parser.error(f"Missing workbook {original}")
    actual = content_digest(original)
    print(f"Tracked workbook content SHA-256: {actual}", flush=True)
    if actual != EXPECTED_SHA256:
        print(f"FAIL: expected {EXPECTED_SHA256}; workbook content differs", file=sys.stderr)
        return 1
    if args.regenerate:
        with TemporaryDirectory(prefix="lifeline_rebuild_") as tmp:
            output = Path(tmp) / "cases.xlsx"
            cmd = [sys.executable, str(ROOT / "generator/generate.py"),
                   "--seed", "18", "--out", str(output)]
            print("Regenerating seed 18 into temporary directory...", flush=True)
            subprocess.run(cmd, cwd=ROOT, check=True)
            regenerated = content_digest(output)
            print(f"Regenerated content SHA-256:     {regenerated}")
            if regenerated != actual:
                print("FAIL: regenerated workbook does not match submitted workbook",
                      file=sys.stderr)
                return 1
    print("PASS: seed-18 content hash verified" +
          (" and regenerated workbook matches" if args.regenerate else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
