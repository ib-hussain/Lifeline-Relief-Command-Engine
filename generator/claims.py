"""claims sheet: tier S optima computed by EXHAUSTIVE SEARCH (the validator re-checks them
with different, polynomial or dynamic-programming methods).

cargo_opt        every subset of crates (2^n, built by doubling the list of subset sums)
window_count_opt every set of pairwise compatible windows (touching allowed), enumerated
window_value_opt   by depth-first search over compatibility bitmasks
drum_opt         every way to cut the drum (all 2^(L-1) compositions of L)
tour_opt         every closed tour starting at site 0 ((n-1)! permutations), Manhattan length
cover_min        every subset of sensor nodes (2^n), smallest one touching every edge
"""
from itertools import permutations

from common import closed_tour_length


def cargo_opt(crates, capacity):
    weights, values = [0], [0]
    for c in crates:
        weights = weights + [w + c["weight"] for w in weights]
        values = values + [v + c["value"] for v in values]
    return max(v for w, v in zip(weights, values) if w <= capacity)


def window_opts(windows):
    n = len(windows)
    iv = [(w["start"], w["finish"], w["value"]) for w in windows]
    compat = [0] * n
    for i in range(n):
        for j in range(n):
            if i != j and (iv[i][1] <= iv[j][0] or iv[j][1] <= iv[i][0]):
                compat[i] |= 1 << j
    best = [0, 0]

    def search(start, allowed, count, value):
        if count > best[0]:
            best[0] = count
        if value > best[1]:
            best[1] = value
        for j in range(start, n):
            if allowed >> j & 1:
                search(j + 1, allowed & compat[j], count + 1, value + iv[j][2])

    search(0, (1 << n) - 1, 0, 0)
    return best[0], best[1]


def drum_opt(prices):
    price = {p["length"]: p["price"] for p in prices}

    def best(rest):                      # no memo: tries every composition
        if rest == 0:
            return 0
        return max(price[j] + best(rest - j) for j in range(1, rest + 1))

    return best(len(prices))


def tour_opt(sites):
    pts = [(s["x"], s["y"]) for s in sites]
    return min(closed_tour_length(pts, (0,) + p) for p in permutations(range(1, len(pts))))


def cover_min(n, edges):
    pairs = [(e["u"], e["v"]) for e in edges]
    best = n
    for mask in range(1 << n):
        size = bin(mask).count("1")
        if size < best and all(mask >> u & 1 or mask >> v & 1 for u, v in pairs):
            best = size
    return best


def compute_claims(case):
    wc, wv = window_opts(case["windows"])
    return dict(cargo_opt=cargo_opt(case["crates"], case["capacity"]),
                window_count_opt=wc, window_value_opt=wv,
                drum_opt=drum_opt(case["drum_prices"]),
                tour_opt=tour_opt(case["sites"]),
                cover_min=cover_min(case["sensor_nodes"], case["sensor_edges"]))
