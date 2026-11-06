# Generator

Writes `cases.xlsx` (50 cases, 20 sheets) from the group seed. Python 3.10+ and `openpyxl`.

## The one command (run from the repository root)

```
python generator/generate.py --seed 18 --out cases.xlsx
```

It prints one line per case and the **content SHA-256** of all cells. The xlsx zip stores
timestamps, so compare this hash, not the file bytes, to prove that a rerun reproduces the data.
Expected content SHA-256 for seed 18: `4c569e38aaedf5feec1b53c0898f5ff3fe3a61304ac70e67a11a9f6655a6ceb0` (also in the root `README.md`).

## Determinism
All randomness comes from `make_rng(seed, case_no, module, attempt)` in `common.py`, which is a
`random.Random` seeded with a string (hashed with SHA-512, so it is stable across machines and runs).
When a module must meet a soft rule (for example a signature rule), it is regenerated with
`attempt + 1`, which is deterministic too.

## Files
| File | Sheets | Main idea |
|---|---|---|
| `spec.py` | all | sheet order, headers, tier ranges, trap size overrides |
| `common.py` | - | RNG, BFS/Dijkstra/bridges, exact ratio greedy, edit distance |
| `gen_crates.py` | crates, capacity | category quotas per study, value grows with weight and category |
| `gen_network.py` | locations, roads, waves, targets | spanning tree + extra roads to the study's average degree |
| `gen_radio.py` | radio_log, radio_patterns, radio_reports | message-based log with noise, patterns cut from the log or proven absent |
| `gen_windows.py` | windows | planted touching pairs; clustered short windows for study 3 |
| `gen_incidents.py` | incidents | arrival rate 1.2 to 1.8 per tick on M/L/X; bursts for study 2 |
| `gen_tour.py` | sites, tour | planted tour = nearest neighbour + 2-opt (never longer than NN) |
| `gen_pipeline.py` | pipeline_dims, drum_prices | random dims; noisy per-length prices capped at 500 |
| `gen_sensors.py` | sensor_edges, sensor_cover | cover chosen first, edges only touch the cover |
| `gen_safety.py` | safety_rules, safety_planted | assignment chosen first, each rule repaired to hold |
| `gen_rations.py` | rations | planted subset first, target = its sum |
| `traps.py` | cases 46 to 49 | the four hostile cases, each with its own self-check |
| `claims.py` | claims | tier S optima by exhaustive search |
| `writer.py` | - | writes the workbook (sorted rows, ints as numbers, text as text) |
| `generate.py` | - | builds the 50 cases, plans the variety rules |
