# Validator

Checks `cases.xlsx` against Section 4 of the Iteration 1 document and prints `PASS` or the
broken rules for every case. It **recomputes everything** and never imports the generator.

```
python validator/validate.py cases.xlsx                     # full check, exit code 0 = PASS
python validator/validate.py validator/tests/x.xlsx --partial   # one-case workbooks
python validator/tests/make_broken.py cases.xlsx            # rebuild the test workbooks
python validator/make_report.py cases.xlsx validation_report.txt
```

| Check | File | What is recomputed |
|---|---|---|
| V1 | `checks/v1_structure.py` | 20 sheets in order, exact headers, 50 distinct `case_id`s `s-kk`, tier and scenario, integer vs text cells, no formulas or empty rows, rows sorted |
| V2 | `checks/v2_ranges.py` | every size per tier (with trap overrides) and every field range; capacity 10 to 70%; touching windows; alarm rate and priorities on M/L/X; prices not proportional; rules/switches 2.0 to 6.0 |
| V3 | `checks/v3_ids.py` | consecutive ids; distinct serials; road ends, targets (S/H, not HQ), wave roads, tour sites, cover nodes, rule switches exist |
| V4 | `checks/v4_network.py` | BFS connectivity before closures; waves disjoint, 1..max(1, ⌊E/4⌋) roads |
| V5 | `checks/v5_counts_claims.py` | pattern counts with overlaps (KMP); edit_bound vs. DP edit distance; 10,000-symbol cells; tier S claims by **different** methods than the generator (DP knapsack, earliest-finish greedy, weighted-interval DP, rod-cutting DP, Held-Karp, bounded-search vertex cover) |
| V6 | `checks/v6_planted.py` | planted tour (permutation from site 0, length, ≤ nearest-neighbour on L/X), cover, assignment, ration selection |
| V7 | `checks/v7_signatures_variety.py` | signature rules of cases 0 to 45 and the four variety rules. Variety 4 compares, between every pair of cases, each module of size 8 or more: crates, network (locations and roads), waves, radio log, radio reports, radio patterns, windows, incidents, tour, pipeline, drum, sensors, safety and rations |
| V8 | `checks/v8_traps.py` | trap rules 46 to 49 (monotone fields, greedy ≤ 60%, diameter ≥ 500 and fewest-roads ≥ 1.5× cheapest, ≥ 90% block repetition and ≥ 4 near-miss patterns) |

`tests/` holds three valid single-case workbooks (18-03 tier S, 18-25 tier M, 18-47 trap) and
25 broken copies. Each broken copy has one deliberate defect. `tests/expected.txt` names the
check that must reject it, and `make_report.py` confirms that it does.

Interpretations we fixed where the document is open:
- "overlap" (study 3) = strict intersection; touching windows do not overlap.
- Near-miss trap: the share is computed over the `N - length + 1` start positions where the whole pattern fits.
- The nearest-neighbour tour breaks distance ties by the lower `site_no`.
- The alarm-rate and priority rules of tiers M and L also apply to tier X, which uses tier L ranges.
- Average degree, percentages and ratios are compared with exact integer or fraction arithmetic.
- Variety 4 ("no two cases equal in any module of size 8 or more"): the size of a table module is its number of rows (waves: closed roads); the size of a text module is its number of symbols (radio log; radio reports: both reports together; radio patterns: the six patterns together, ignoring the derived `count` column).
