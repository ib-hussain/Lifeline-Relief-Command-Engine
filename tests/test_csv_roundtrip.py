"""Check each published data CSV *against the XLSX* and the SHA-256 manifest.

Merely checking the manifest is insufficient: a stale manifest and CSV can be
mutually consistent while disagreeing with cases.xlsx.
"""
import csv
import hashlib
from itertools import zip_longest
import json
from pathlib import Path
import unittest

from openpyxl import load_workbook

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
SENTINEL = object()


class ExportRoundTripTests(unittest.TestCase):
    def test_exports_match_workbook_and_manifest(self):
        manifest = json.loads((DATA / "manifest.json").read_text(encoding="ascii"))
        records = manifest["files"]
        self.assertEqual(manifest["sheet_count"], 20)
        self.assertEqual(len(records), 20)
        self.assertEqual(len({rec["file"] for rec in records}), 20)
        wb = load_workbook(ROOT / "cases.xlsx", read_only=True)
        try:
            self.assertEqual([f"{s}.csv" for s in wb.sheetnames],
                             [rec["file"] for rec in records])
            for entry in records:
                name = entry["file"]
                with self.subTest(csv=name):
                    path = DATA / name
                    self.assertTrue(path.is_file())
                    self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(),
                                     entry["sha256"])
                    sheet = wb[name[:-4]]
                    count = 0
                    with path.open("r", encoding="ascii", newline="") as f:
                        csv_rows = csv.reader(f)
                        workbook_rows = sheet.iter_rows(values_only=True)
                        for excel_row, csv_row in enumerate(
                            zip_longest(workbook_rows, csv_rows, fillvalue=SENTINEL), 1
                        ):
                            xlsx_values, values = csv_row
                            self.assertIsNot(xlsx_values, SENTINEL,
                                             f"{name}: CSV contains extra row {excel_row}")
                            self.assertIsNot(values, SENTINEL,
                                             f"{name}: CSV is missing row {excel_row}")
                            self.assertEqual(values,
                                [str(v) for v in xlsx_values],
                                f"{name}: mismatch on row {excel_row}")
                            if excel_row > 1:
                                count += 1
                    self.assertEqual(entry["rows"], count)
        finally:
            wb.close()


if __name__ == "__main__":
    unittest.main()
