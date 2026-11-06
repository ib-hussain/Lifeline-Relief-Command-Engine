"""Reads cases.xlsx without trusting it.

Rows are mapped to the EXPECTED column names by position, so a wrong header is reported by
V1 but the remaining checks can still run. Cell types are recorded per case for V1.
"""
from openpyxl import load_workbook

from spec import SHEET_NAMES, HEADERS, TEXT_COLUMNS


class Case:
    def __init__(self, case_id):
        self.case_id = case_id
        self.row = None                       # its row of the 'cases' sheet
        self.sheets = {name: [] for name in SHEET_NAMES if name != "cases"}
        self.cell_errors = []

    def __getattr__(self, name):              # case.crates, case.roads, ...
        sheets = self.__dict__.get("sheets", {})
        if name in sheets:
            return sheets[name]
        raise AttributeError(name)

    @property
    def k(self):
        return self.row["case_no"]

    def log(self):
        return "".join(r["text"] for r in sorted(self.radio_log, key=lambda r: r["part"]))


class Book:
    def __init__(self, path):
        wb = load_workbook(path, read_only=True)
        self.sheet_names = list(wb.sheetnames)
        self.headers, self.raw = {}, {}
        self.problems = []                    # workbook-level reading problems (V1)
        for name in self.sheet_names:
            it = wb[name].iter_rows(values_only=True)
            header = next(it, None) or ()
            while header and header[-1] is None:
                header = header[:-1]
            self.headers[name] = tuple(header)
            rows = []
            for excel_row, values in enumerate(it, start=2):
                if values is None or all(v is None for v in values):
                    self.problems.append(f"{name}: row {excel_row} is empty")
                    continue
                rows.append((excel_row, values))
            self.raw[name] = rows
        wb.close()

        self.cases = {}                       # case_id -> Case, in order of the cases sheet
        self.orphans = []                     # rows whose case_id is not in the cases sheet
        for name in SHEET_NAMES:
            cols = HEADERS[name]
            for excel_row, values in self.raw.get(name, []):
                values = tuple(values) + (None,) * (len(cols) - len(values))
                rec = dict(zip(cols, values))
                cid = rec["case_id"]
                if name == "cases":
                    case = self.cases.setdefault(cid, Case(cid))
                    if case.row is not None:
                        self.problems.append(f"cases: case_id {cid} appears twice")
                    case.row = rec
                elif cid in self.cases:
                    case = self.cases[cid]
                    case.sheets[name].append(rec)
                else:
                    self.orphans.append(f"{name}: row {excel_row} has unknown case_id {cid!r}")
                    continue
                for col, val in rec.items():
                    if col in TEXT_COLUMNS:
                        ok = isinstance(val, str)
                    else:
                        ok = isinstance(val, int) and not isinstance(val, bool)
                    if not ok:
                        case.cell_errors.append(
                            f"{name} row {excel_row}: {col} = {val!r} is not "
                            f"{'text' if col in TEXT_COLUMNS else 'an integer'}")
                    elif isinstance(val, str) and val.startswith("="):
                        case.cell_errors.append(f"{name} row {excel_row}: {col} looks like a formula")
