"""V5: every pattern count and edit_bound is correct; log parts are in order and within
10,000 symbols; claims are correct on tier S (recomputed with different methods than the
generator: DP knapsack, greedy/DP interval scheduling, DP rod cutting, Held-Karp,
bounded-search vertex cover)."""
from algos import (kmp_count, levenshtein, knapsack, max_compatible_count, max_compatible_value,
                   rod_cutting, held_karp, min_vertex_cover)
from spec import PATTERN_LENGTHS, expected_tier


def check_case(c, book, ctx):
    e = []
    r = c.row
    parts = sorted(c.radio_log, key=lambda x: x["part"])
    for x in parts:
        if len(x["text"]) > 10000:
            e.append(f"radio_log part {x['part']} holds {len(x['text'])} symbols (max 10,000)")
    log = "".join(x["text"] for x in parts)

    pats = sorted(c.radio_patterns, key=lambda x: x["pattern_no"])
    lengths = [len(p["pattern"]) for p in pats]
    if lengths != PATTERN_LENGTHS:
        e.append(f"pattern lengths are {lengths}, expected {PATTERN_LENGTHS}")
    occurring = 0
    for p in pats:
        true = kmp_count(log, p["pattern"])
        if true != p["count"]:
            e.append(f"pattern {p['pattern_no']} count is {p['count']}, true count is {true}")
        occurring += true > 0
    if occurring < 2 or occurring == len(pats):
        e.append(f"{occurring} of {len(pats)} patterns occur: need at least two occurring and one not")

    for rep in c.radio_reports:
        a, b = rep["report_a"], rep["report_b"]
        d = levenshtein(a, b)
        bound = r["edit_bound"]
        if bound < d:
            e.append(f"edit_bound {bound} is below the true edit distance {d}")
        if bound > len(a) + len(b):
            e.append(f"edit_bound {bound} exceeds len(a) + len(b) = {len(a) + len(b)}")

    if expected_tier(r["case_no"]) == "S" and c.claims:
        cl = c.claims[0]
        prices = [p["price"] for p in sorted(c.drum_prices, key=lambda p: p["length"])]
        pts = [(s["x"], s["y"]) for s in sorted(c.sites, key=lambda s: s["site_no"])]
        edges = [(x["u"], x["v"]) for x in c.sensor_edges]
        truth = dict(
            cargo_opt=knapsack([(x["weight"], x["value"]) for x in c.crates], r["capacity"]),
            window_count_opt=max_compatible_count(c.windows),
            window_value_opt=max_compatible_value(c.windows),
            drum_opt=rod_cutting(prices),
            tour_opt=held_karp(pts),
            cover_min=min_vertex_cover(edges))
        for key, val in truth.items():
            if cl[key] != val:
                e.append(f"claim {key} = {cl[key]}, recomputed optimum is {val}")
    return e
