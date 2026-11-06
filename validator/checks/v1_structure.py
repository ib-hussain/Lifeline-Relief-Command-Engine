"""V1: exactly the 20 sheets and headers of Section 3; 50 distinct case_ids in the right
format; the correct tier and scenario for each case_no. Also: integers are numbers, text is
text, no formulas, no empty rows, rows sorted by case_id then by the second column."""
from spec import SHEET_NAMES, HEADERS, expected_tier, expected_scenario


def _sort_key(values):
    return (str(values[0]), values[1] if len(values) > 1 else None)


def check_book(book, ctx):
    errs = []
    if book.sheet_names != SHEET_NAMES:
        missing = [s for s in SHEET_NAMES if s not in book.sheet_names]
        extra = [s for s in book.sheet_names if s not in SHEET_NAMES]
        errs.append(f"sheet list/order is wrong (missing {missing}, extra {extra}, "
                    f"found order {book.sheet_names})")
    for name in SHEET_NAMES:
        if name in book.headers and list(book.headers[name]) != HEADERS[name]:
            errs.append(f"{name}: header is {list(book.headers[name])}, expected {HEADERS[name]}")
    errs.extend(book.problems)
    errs.extend(book.orphans[:20])
    for name in SHEET_NAMES:
        rows = book.raw.get(name, [])
        for (r1, a), (r2, b) in zip(rows, rows[1:]):
            try:
                if _sort_key(b) < _sort_key(a):
                    errs.append(f"{name}: row {r2} is out of order (rows must be sorted by "
                                f"case_id, then {HEADERS[name][1]})")
                    break
            except TypeError:
                errs.append(f"{name}: rows {r1}-{r2} cannot be ordered (mixed types)")
                break
    seeds = {c.row["group_seed"] for c in book.cases.values()}
    if len(seeds) > 1:
        errs.append(f"more than one group_seed: {sorted(map(str, seeds))}")
    if not ctx.partial:
        if len(book.cases) != 50:
            errs.append(f"{len(book.cases)} cases, expected exactly 50")
        nos = sorted(c.row["case_no"] for c in book.cases.values() if isinstance(c.row["case_no"], int))
        if nos != list(range(50)):
            errs.append("case_no values are not exactly 0..49")
    return errs


def check_case(c, book, ctx):
    errs = list(c.cell_errors[:15])
    if len(c.cell_errors) > 15:
        errs.append(f"... {len(c.cell_errors) - 15} more cell type errors")
    r = c.row
    k = r["case_no"]
    if not (isinstance(k, int) and 0 <= k <= 49):
        return errs + [f"case_no {k!r} is not 0..49"]
    want = f"{r['group_seed']}-{k:02d}"
    if c.case_id != want:
        errs.append(f"case_id {c.case_id!r} should be {want!r} (seed, hyphen, two-digit case number)")
    if r["tier"] != expected_tier(k):
        errs.append(f"tier {r['tier']!r} should be {expected_tier(k)!r} for case {k}")
    if r["scenario"] != expected_scenario(k):
        errs.append(f"scenario {r['scenario']} should be {expected_scenario(k)} = (case_no mod 6) + 1")
    for name in SHEET_NAMES[1:]:
        rows = c.sheets[name]
        if name == "claims":
            want_rows = 1 if expected_tier(k) == "S" else 0
            if len(rows) != want_rows:
                errs.append(f"claims has {len(rows)} rows, expected {want_rows} (tier S only)")
        elif name == "radio_reports":
            if len(rows) != 1:
                errs.append(f"radio_reports has {len(rows)} rows, expected 1")
        elif not rows:
            errs.append(f"{name} has no rows for this case")
    return errs
