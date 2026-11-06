# LIFELINE: Iteration 1 (group 18)

Group 18 · Saneed Ullah (23i-2568), Hasnat Ahmed (23i-2652), Hussain Muhammad Ibrahim (23i-2626), section AI-B.

## Reproduce everything (from this folder)

```
pip install -r requirements.txt
python generator/generate.py --seed 18 --out cases.xlsx
python validator/validate.py cases.xlsx
python validator/tests/make_broken.py cases.xlsx
python validator/make_report.py cases.xlsx validation_report.txt
```

Expected content SHA-256 of `cases.xlsx` for seed 18 (printed by the generator):
`4c569e38aaedf5feec1b53c0898f5ff3fe3a61304ac70e67a11a9f6655a6ceb0`

## Contents
| Item | Where |
|---|---|
| 50 cases | `cases.xlsx` (written by the generator, never edited by hand) |
| Generator | `generator/` (see `generator/README.md`) |
| Validator | `validator/`, with test workbooks in `validator/tests/` |
| Validator output | `validation_report.txt` |
| Approach note | `approach.pdf` (to be written) |
| Proposal | `proposal.pdf` (to be written) |
| Repository link | `repository.txt` |
| Members | `members.txt` |

## Conventions we fixed where the document leaves a choice
- `case_id` = `18-kk`; `wave_no` starts at 0, `part` at 1, tour `step` at 0, `rule_no` at 1.
- Crate serials are distinct across the whole workbook, not only within a case.
- Study 3 "overlap" = strict intersection. Touching windows are compatible, so they do not overlap.
- Nearest-neighbour tour: distance ties go to the lower `site_no`.
- The M/L alarm-rate and priority rules are also applied to tier X.
- All percentage, degree and ratio rules use exact integer or fraction arithmetic.

## Requirement → construction → check
| Requirement (Iteration 1 doc) | How the generator meets it | Validator |
|---|---|---|
| 20 sheets, headers, order, sorted rows, int/text cells | `writer.py` | V1 |
| case_id, tier, scenario | `generate.py` | V1 |
| Tier ranges (+ trap overrides) | `spec.ranges_for` | V2 |
| Capacity 10 to 70% | `choose_capacity` clamps with integers | V2 |
| Connected network, waves disjoint and ≤ ⌊E/4⌋ | spanning tree first; waves drawn without replacement, ≤ ⌊E/12⌋ | V4 |
| Pattern counts, ≥2 occur, ≥1 absent | patterns cut from the log, or random strings proven absent | V5 |
| edit_bound | exact DP edit distance | V5 |
| Touching windows ≥ 2 pairs | planted (window j starts at window i's finish) | V2 |
| Alarm rate 1.2 to 1.8, ≥ 6 priorities including 1 | tick count solved from the rate; missing priorities inserted | V2 |
| Planted tour ≤ NN on L/X | NN tour + 2-opt (only shortens) | V6 |
| Planted cover / assignment / rations | cover first / assignment first / subset first | V6 |
| Tier S claims | exhaustive search (`claims.py`) | V5 (different methods) |
| Signature rules of the 6 studies | quotas and degree ranges, plus a self-check and retry | V7 |
| Variety 1 and 2 (≥ 5 tier-S cases each) | 8 cases planned for each, regenerated until true | V7 |
| Variety 3 (safety ratio bins over M+L) | 7 low / 11 mid / 8 high planned | V7 |
| Variety 4 (no equal modules) | independent random streams per case and module | V7 |
| Traps 46 to 49 | `traps.py` (each asserts its own rule) | V8 |
| Reject bad data | 19 broken copies of 3 valid cases | `validation_report.txt` |
