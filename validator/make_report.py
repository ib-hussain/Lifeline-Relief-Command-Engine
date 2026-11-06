"""Writes validation_report.txt: the full validator output for cases.xlsx, then every test
workbook in validator/tests/ with the expected and the actual outcome.

    python validator/make_report.py cases.xlsx validation_report.txt
"""
import argparse
import os
import platform
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from validate import run, format_result, passed     # noqa: E402

TESTS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tests")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("workbook", nargs="?", default="cases.xlsx")
    ap.add_argument("report", nargs="?", default="validation_report.txt")
    args = ap.parse_args()

    out = ["LIFELINE - Iteration 1 validation report",
           f"Generated {datetime.now():%Y-%m-%d %H:%M} with Python {platform.python_version()}",
           "=" * 78, "", "PART 1. cases.xlsx (all 50 cases)", "-" * 78]
    main_result = run(args.workbook)
    out.append(format_result(main_result))

    out += ["", "", "PART 2. Rejection of broken copies (validator/tests/)", "-" * 78,
            "Each broken copy holds ONE case with ONE deliberate defect. The validator runs in",
            "--partial mode (a single case, so the 50-case and variety rules are skipped).", ""]
    with open(os.path.join(TESTS, "expected.txt")) as f:
        tests = [line.strip().split(" | ") for line in f if line.strip() and not line.startswith("#")]
    all_ok = passed(main_result)
    summary = []
    for name, expect, desc in tests:
        result = run(os.path.join(TESTS, name), partial=True)
        failed = sorted({code for code, _ in result["book"]} |
                        {code for errs in result["cases"].values() for code, _ in errs})
        if expect == "PASS":
            ok = passed(result)
            got = "PASS" if ok else "FAIL " + ",".join(failed)
        else:
            ok = expect in failed
            got = "REJECTED by " + ",".join(failed) if failed else "ACCEPTED (not rejected!)"
        all_ok &= ok
        summary.append(f"{'OK      ' if ok else 'MISMATCH'} {name:<34} expected {expect:<5} got {got}")
        out += [f"### {name}", f"defect: {desc}", f"expected: {expect}", format_result(result), ""]
    out += ["", "PART 3. Summary of the test workbooks", "-" * 78] + summary
    out += ["", f"OVERALL: {'all 50 cases PASS and every broken copy is rejected for the expected rule' if all_ok else 'PROBLEMS FOUND'}"]
    with open(args.report, "w") as f:
        f.write("\n".join(out) + "\n")
    print("\n".join(summary))
    print(f"report written to {args.report}; overall {'OK' if all_ok else 'PROBLEMS'}")
    sys.exit(0 if all_ok else 1)


if __name__ == "__main__":
    main()
