#!/usr/bin/env python3
"""Preflight for the Iteration 1 repository or final local submission folder.

    python tools/preflight_submission.py --profile repo
    python tools/preflight_submission.py --profile submission

No files are changed. The repository profile intentionally does not require
private/ignored submission files. The submission profile does require them.
"""
import argparse
from collections import Counter
from pathlib import Path
import sys

from openpyxl import load_workbook

ROOT = Path(__file__).resolve().parents[1]
SHEETS = (
    "cases", "crates", "locations", "roads", "waves", "radio_log",
    "radio_patterns", "radio_reports", "windows", "incidents", "sites",
    "tour", "pipeline_dims", "drum_prices", "sensor_edges", "sensor_cover",
    "safety_rules", "safety_planted", "rations", "claims",
)
CORE_FILES = (
    "cases.xlsx", "README.md", "requirements.txt", "generator/generate.py",
    "generator/spec.py", "validator/validate.py", "validator/make_report.py",
    "validator/tests/expected.txt", "data/populate.py", "docs/make_proposal.py",
    "docs/make_approach.py",
)
SUBMISSION_FILES = (
    "APPROACH.md", "members.txt", "repository.txt", "validation_report.txt",
    "approach_note.pdf",
)


def inspect(root: Path, submission: bool):
    errors, warnings = [], []
    for relative in CORE_FILES + (SUBMISSION_FILES if submission else ()):
        if not (root / relative).is_file():
            errors.append(f"Required file missing: {relative}")
    proposal = root / "proposal.pdf"
    proposal_alt = root / "Proposal.pdf"
    if not proposal.is_file() and not proposal_alt.is_file():
        errors.append("Algorithm proposal missing: proposal.pdf or Proposal.pdf")
    elif not proposal.is_file():
        warnings.append("Proposal.pdf uses uppercase P; the brief specifies proposal.pdf")

    data = root / "data"
    for name in SHEETS:
        if not (data / f"{name}.csv").is_file():
            errors.append(f"Missing derived CSV: data/{name}.csv")
    if not (data / "manifest.json").is_file():
        errors.append("Missing data/manifest.json")

    xlsx = root / "cases.xlsx"
    if xlsx.is_file():
        try:
            wb = load_workbook(xlsx, read_only=True)
            try:
                if tuple(wb.sheetnames) != SHEETS:
                    errors.append("Workbook sheet names/order differ from specification")
                if "cases" in wb:
                    ids = [row[0] for row in wb["cases"].iter_rows(min_row=2, max_col=1,
                                                                     values_only=True)]
                    if ids != [f"18-{i:02d}" for i in range(50)]:
                        errors.append("Workbook cases IDs must run 18-00 to 18-49")
            finally:
                wb.close()
        except Exception as exc:
            errors.append(f"Cannot inspect workbook: {exc}")

    expected = root / "validator/tests/expected.txt"
    if expected.is_file():
        entries = []
        for line in expected.read_text(encoding="utf-8").splitlines():
            if not line.strip() or line.startswith("#"):
                continue
            try:
                name, code, _ = line.split(" | ", 2)
            except ValueError:
                errors.append(f"Malformed expected.txt line: {line!r}")
                continue
            entries.append((name, code))
            if not (root / "validator/tests" / name).is_file():
                errors.append(f"Missing listed fixture: {name}")
        bases = Counter()
        valid = set()
        for name, code in entries:
            if code == "PASS" and name.startswith("valid_"):
                valid.add(name[len("valid_"):-len(".xlsx")])
            elif code != "PASS" and name.startswith("broken_"):
                # IDs: 18-03, 18-25, etc.
                bases[name.split("_")[1]] += 1
        qualified = [cid for cid in valid if bases[cid] >= 5]
        if len(qualified) < 2:
            errors.append("Need 2 valid base cases with at least 5 rejected mutations each")
        if len(entries) < 12:
            errors.append("Too few test fixtures in validator/tests/expected.txt")

    if submission:
        repofile = root / "repository.txt"
        if repofile.is_file():
            uri = repofile.read_text(encoding="utf-8").strip()
            if not uri.startswith("https://github.com/") or uri.count("/") < 4:
                errors.append("repository.txt must contain a real GitHub repository URL")
        members = root / "members.txt"
        if members.is_file() and not members.read_text(encoding="utf-8").strip():
            errors.append("members.txt is empty")

    # A PDF page count is checked only when pypdf is already installed. The
    # preflight does not silently claim to have checked the number of pages.
    try:
        from pypdf import PdfReader
    except ImportError:
        warnings.append("PDF page counts not checked (optional: pip install pypdf)")
    else:
        pdfs = [root / "approach_note.pdf"] if submission else []
        pdfs.append(proposal if proposal.is_file() else proposal_alt)
        for path in pdfs:
            if path.is_file():
                try:
                    pages = len(PdfReader(str(path)).pages)
                except Exception as exc:
                    errors.append(f"PDF unreadable: {path.name}: {exc}")
                else:
                    if pages != 2:
                        errors.append(f"{path.name}: expected 2 pages, got {pages}")
    return errors, warnings


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", choices=("repo", "submission"), default="repo")
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args()
    errors, warnings = inspect(args.root.resolve(), args.profile == "submission")
    print(f"LIFELINE {args.profile} preflight: {args.root.resolve()}")
    for warning in warnings:
        print("WARNING:", warning)
    for error in errors:
        print("ERROR:  ", error)
    if errors:
        print(f"FAIL: {len(errors)} issue(s)")
        return 1
    print("PASS: no preflight errors (validator and unittest suite run separately)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
