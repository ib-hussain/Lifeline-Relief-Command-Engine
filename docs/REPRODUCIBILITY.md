# Reproducibility and verification (Iteration 1)

This document describes **repeatable checks**, not a claim that Iteration 2 has
already been implemented. Run commands from the repository root. Python 3.12
or 3.13 and dependencies from `requirements.txt` are recommended.

## Dataset source of truth

- `cases.xlsx` has 20 sheets and exactly 50 cases (seed 18).
- `generator/generate.py` generates the workbook; it does not import CSV data.
- `data/populate.py` makes 20 *derived* CSV copies and `data/manifest.json`.
- No external datasets are required. Do not edit `cases.xlsx` by hand.

The canonical **cell-content SHA-256** for seed 18 is:

`4c569e38aaedf5feec1b53c0898f5ff3fe3a61304ac70e67a11a9f6655a6ceb0`

This digest is calculated using the format in `generator/writer.py`, **not**
the SHA-256 of the `.xlsx` ZIP bytes, which can depend on serialization metadata.

## Checks used for review

| Check | Run | What it independently verifies |
|---|---|---|
| Workbook validator | `python validator/validate.py cases.xlsx` | V1–V8 over all cases |
| Tier-S oracles | `python -m unittest discover -s tests -p 'test_*.py' -v` | All six small-case optimum claims; workbook, exports and fixture checks |
| Mutant rejection | `python validator/make_report.py cases.xlsx validation_report.txt` | Valid bases pass; all 25 broken copies are rejected |
| CSV re-export | `python data/populate.py` | Rebuilds all 20 CSVs and `manifest.json` |
| Submission preflight | `python tools/preflight_submission.py --profile submission` | Required local deliverables and test fixture counts |
| Content digest | `python tools/verify_rebuild.py` | Digest matches the expected seed-18 value |
| Fresh regeneration | `python tools/verify_rebuild.py --regenerate` | Generator reruns in a temporary folder and reproduces the digest |

Windows PowerShell users can run `.\scripts\verify_project.ps1`; add
`-Submission` for the ignored local deliverables and `-FullRebuild` to rerun
the full generator without overwriting `cases.xlsx`.

## Why repository and submission checks differ

`APPROACH.md`, `members.txt`, `repository.txt`, and `validation_report.txt` may
be intentionally ignored in the GitHub presentation, but the course requires
them in the **final submission ZIP**. A clean clone may not contain those
files. Do not treat a passing CI workflow as proof that the final submission
ZIP has all required deliverables.

**Do not submit** secrets, private SSH keys, GitHub personal access tokens,
`.git` credentials or `.env` files. Grant course staff access through official
GitHub collaborator invitations, or ask for their preferred GitHub identities.

## Iteration 2 status

The proposal selects algorithms for modules A–I. The decisions' full
implementations, comparative experiments, Prediction Log and Recommendation
remain separate Iteration 2 work. Passing Iteration 1 validation is not a
substitute for those deliverables.
