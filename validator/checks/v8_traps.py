"""V8: the trap rules of cases 46 to 49."""
from algos import (neighbours, bfs, dijkstra, cheapest_fewest_roads, knapsack, greedy_by_ratio)


def _monotone(seq, le):
    """True if seq is all non-decreasing or all non-increasing under the order `le`."""
    up = all(le(a, b) for a, b in zip(seq, seq[1:]))
    down = all(le(b, a) for a, b in zip(seq, seq[1:]))
    return up or down


def trap46(c):
    e = []
    crates = sorted(c.crates, key=lambda x: x["crate_id"])
    if not 1500 <= len(crates) <= 3000:
        e.append(f"dock-order trap needs 1,500..3,000 crates, has {len(crates)}")
    num_le = lambda a, b: a <= b
    fields = {name: _monotone([x[name] for x in crates], num_le)
              for name in ("value", "weight", "expiry", "serial")}
    ratios = [(x["value"], x["weight"]) for x in crates]
    fields["value-per-kg"] = _monotone(ratios, lambda a, b: a[0] * b[1] <= b[0] * a[1])
    mono = [name for name, ok in fields.items() if ok]
    if len(mono) < 3:
        e.append(f"dock-order trap: monotone in only {mono}, need at least three of five fields")
    return e


def trap47(c):
    e = []
    n = len(c.crates)
    if not 12 <= n <= 60:
        e.append(f"best-looking-crate trap needs 12..60 crates, has {n}")
    cap = c.row["capacity"]
    best = knapsack([(x["weight"], x["value"]) for x in c.crates], cap)
    greedy = greedy_by_ratio(c.crates, cap)
    if 10 * greedy > 6 * best:
        e.append(f"best-looking-crate trap: greedy reaches {greedy} of {best} (> 60%)")
    return e


def trap48(c):
    e = []
    V = len(c.locations)
    if not 1500 <= V <= 3000:
        e.append(f"shortest-looks-cheapest trap needs 1,500..3,000 locations, has {V}")
    adj = neighbours(V, c.roads)
    hops, _ = bfs(adj, 0)
    far = max(range(V), key=lambda i: hops[i])
    hops2, _ = bfs(adj, far)                     # double sweep: a lower bound on the diameter
    if max(hops2) < 500:
        e.append(f"longest distance found is {max(hops2)} roads, need >= 500")
    pen = [0] * V
    for x in c.locations:
        pen[x["loc_id"]] = x["penalty"]
    dist = dijkstra(adj, pen, 0)
    fewest = cheapest_fewest_roads(adj, pen, 0)
    targets = [c.row["target_0"], c.row["target_1"], c.row["target_2"]]
    if not any(2 * fewest[t] >= 3 * dist[t] for t in targets):
        e.append("no target where every fewest-roads route costs >= 1.5 x a cheapest route")
    return e


def _repetition_coverage(log, max_block=8):
    """Largest number of symbols covered by repetitions (>= 2 copies) of one block of
    length <= max_block, blocks compared up to rotation."""
    N = len(log)
    best = 0
    for p in range(1, max_block + 1):
        segments = {}
        i = 0
        while i < N - p:
            if log[i] != log[i + p]:
                i += 1
                continue
            j = i
            while j < N - p and log[j] == log[j + p]:
                j += 1
            start, end = i, j + p                # log[start:end] has period p
            if end - start >= 2 * p:
                block = log[start:start + p]
                key = min(block[r:] + block[:r] for r in range(p))
                segments.setdefault(key, []).append((start, end))
            i = j + 1
        for spans in segments.values():
            covered, last_end = 0, -1
            for s, t in sorted(spans):
                s = max(s, last_end)
                if t > s:
                    covered += t - s
                    last_end = t
            best = max(best, covered)
    return best


def trap49(c):
    e = []
    log = c.log()
    N = len(log)
    if not 50000 <= N <= 100000:
        e.append(f"near-miss trap needs 50,000..100,000 symbols, has {N}")
    cov = _repetition_coverage(log)
    if 10 * cov < 9 * N:
        e.append(f"only {cov} of {N} symbols are repetitions of one block of <= 8 symbols (need 90%)")
    near = 0
    for p in c.radio_patterns:
        pat = p["pattern"]
        L = len(pat)
        prefix = pat[:-1]
        positions = N - L + 1
        matches = sum(1 for i in range(positions) if log.startswith(prefix, i))
        if positions > 0 and 2 * matches >= positions:
            near += 1
    if near < 4:
        e.append(f"only {near} patterns whose first (length-1) symbols match at >= half of all start positions (need 4)")
    return e


TRAPS = {46: trap46, 47: trap47, 48: trap48, 49: trap49}


def check_case(c, book, ctx):
    fn = TRAPS.get(c.row["case_no"])
    return fn(c) if fn else []
