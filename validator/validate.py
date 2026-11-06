"""LIFELINE Iteration 1 validator. Recomputes everything; trusts no field.

    python validator/validate.py cases.xlsx              # the full 50-case workbook
    python validator/validate.py some.xlsx --partial     # a workbook with only some cases
                                                         # (skips "exactly 50" and variety rules)

Prints PASS or the broken rules for every case. Exit code 0 only if everything passes.
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from loader import Book          # noqa: E402
from checks import CHECKS        # noqa: E402

MAX_PER_CHECK = 8


class Context:
    def __init__(self, partial):
        self.partial = partial
        self.notes = []


def _safe(fn, *args):
    try:
        return list(fn(*args))
    except Exception as ex:          # malformed data must be reported, never crash the run
        return [f"could not be checked ({type(ex).__name__}: {ex})"]


def run(path, partial=False):
    book = Book(path)
    ctx = Context(partial)
    result = {"path": path, "partial": partial, "book": [], "cases": {}, "notes": ctx.notes}
    for code, mod in CHECKS:
        if hasattr(mod, "check_book"):
            result["book"] += [(code, m) for m in _safe(mod.check_book, book, ctx)]
    for cid, case in book.cases.items():
        errs = []
        for code, mod in CHECKS:
            msgs = _safe(mod.check_case, case, book, ctx)
            if len(msgs) > MAX_PER_CHECK:
                msgs = msgs[:MAX_PER_CHECK] + [f"... and {len(msgs) - MAX_PER_CHECK} more"]
            errs += [(code, m) for m in msgs]
        result["cases"][cid] = errs
    return result


def passed(result):
    return not result["book"] and all(not errs for errs in result["cases"].values())


def format_result(result):
    lines = [f"Validating {os.path.basename(result['path'])}"
             f"{'  (partial workbook: count and variety rules skipped)' if result['partial'] else ''}"]
    if result["book"]:
        lines.append("WORKBOOK FAIL")
        lines += [f"    [{code}] {msg}" for code, msg in result["book"]]
    else:
        lines.append("WORKBOOK PASS  (sheets, headers, order, case ids"
                     f"{'' if result['partial'] else ', variety rules'})")
    for note in result["notes"]:
        lines.append(f"    note: {note}")
    for cid, errs in result["cases"].items():
        if not errs:
            lines.append(f"{cid} PASS")
        else:
            lines.append(f"{cid} FAIL")
            lines += [f"    [{code}] {msg}" for code, msg in errs]
    ok = sum(1 for errs in result["cases"].values() if not errs)
    lines.append(f"Summary: {ok}/{len(result['cases'])} cases PASS; workbook checks "
                 f"{'PASS' if not result['book'] else 'FAIL'}")
    lines.append(f"RESULT: {'PASS' if passed(result) else 'FAIL'}")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("workbook")
    ap.add_argument("--partial", action="store_true")
    args = ap.parse_args()
    result = run(args.workbook, args.partial)
    print(format_result(result))
    sys.exit(0 if passed(result) else 1)


if __name__ == "__main__":
    main()
