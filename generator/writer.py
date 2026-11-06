"""Writes cases.xlsx: exactly the 20 sheets in order, header in row 1, rows sorted by
case_id then by the following columns, integers as numbers and text as text, no formulas.
Also returns a SHA-256 of the cell contents (the xlsx zip itself stores timestamps, so the
content hash is what proves that a rerun reproduces the same data)."""
import hashlib
from datetime import datetime

from openpyxl import Workbook

from spec import SHEETS

FIXED_TIME = datetime(2026, 11, 1, 0, 0, 0)


def write_workbook(path, sheet_rows):
    wb = Workbook(write_only=True)
    wb.properties.creator = "LIFELINE generator"
    wb.properties.created = FIXED_TIME
    wb.properties.modified = FIXED_TIME
    digest = hashlib.sha256()
    for name, header in SHEETS:
        ws = wb.create_sheet(title=name)
        ws.append(header)
        digest.update(repr((name, header)).encode())
        rows = [tuple(r[col] for col in header) for r in sheet_rows[name]]
        rows.sort()
        for row in rows:
            for value in row:
                assert isinstance(value, (int, str)) and not isinstance(value, bool), (name, row)
                assert not (isinstance(value, str) and value.startswith("=")), (name, row)
            ws.append(list(row))
            digest.update(repr(row).encode())
    wb.save(path)
    return digest.hexdigest()
