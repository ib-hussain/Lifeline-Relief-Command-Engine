"""The four trap cases (tier X). Only the signature rules are waived; every sheet rule still holds.

46 Dock-order trap (study 5 story): 1,500..3,000 crates already monotone in ALL five fields:
   value non-decreasing, weight non-increasing (=> value/kg non-decreasing), expiry and serial
   non-decreasing. Hostile to sorts that assume random input (e.g. quicksort, first pivot).
47 Best-looking-crate trap (study 6 story): capacity 40; two crates (20 kg, 100) fill it exactly;
   one decoy (1 kg, 10) has the best value/kg and steals 1 kg, so greedy-by-ratio gets
   10 + 100 = 110 while the optimum is 200 (55%). Fillers weigh 20 kg with low value and never
   fit in the 19 kg greedy leaves. At most 20 crates keeps capacity >= 10% of total weight.
48 Shortest-looks-cheapest trap (study 1 story): 1,500..3,000 locations. A highway of
   560..700 locations; every other location hangs off it and extra roads only join locations
   whose highway position differs by <= 1, so the two highway ends stay >= 559 roads apart.
   Gadget at the HQ: HQ -x- T with 60-minute roads and penalty 6 at x (2 roads), and a detour
   HQ -c1-c2-c3- T of 1-minute roads with penalty 0 (4 roads). The only fewest-roads route to
   T costs >= 126, the cheapest <= 4 (+ penalty of T): far beyond the required 1.5x.
49 Near-miss trap (study 2 story): 50,000..100,000 symbols, ~93% long runs of the block "A".
   A block with period p matches a fixed (length-1) prefix at only ~1/p of positions, so
   "at least half of all start positions" needs period 1. Patterns are A^(L-1) + "B": their
   prefixes match almost everywhere but the full patterns almost never. Noise sits in a few
   clumps (no 'A', no 'B') so the long runs survive; one clump holds "AAAB" so the length-2
   and length-4 patterns occur once and the four longer ones never occur.
"""
import math

from common import ceil_div, count_overlapping, route_costs, bfs_order, adjacency, \
    greedy_ratio_value, knapsack_value
from gen_crates import draw_serials
from gen_network import relabel, assign_types, make_waves
from spec import ALPHABET, PATTERN_LENGTHS, PENALTIES


# ---------------------------------------------------------------- 46

def trap46_crates(rng, n, used_serials):
    values = sorted(rng.randint(10, 100) for _ in range(n))
    weights = sorted((rng.randint(1, 20) for _ in range(n)), reverse=True)
    expiry = sorted(rng.randint(0, 999) for _ in range(n))
    serials = sorted(draw_serials(rng, n, used_serials))
    crates = [dict(crate_id=i + 1, cat=rng.randrange(5), weight=weights[i], value=values[i],
                   expiry=expiry[i], serial=serials[i]) for i in range(n)]
    total = sum(weights)
    cap = max(ceil_div(total, 10), total * rng.randint(10, 15) // 100)
    return crates, cap


# ---------------------------------------------------------------- 47

def trap47_crates(rng, used_serials):
    n = rng.randint(12, 20)
    specs = [(20, 100, 2), (20, 100, 2), (1, 10, 1)]                    # (weight, value, cat)
    specs += [(20, rng.randint(10, 14), rng.choice((1, 2))) for _ in range(n - 3)]
    rng.shuffle(specs)
    serials = draw_serials(rng, n, used_serials)
    crates = [dict(crate_id=i + 1, cat=c, weight=w, value=v, expiry=rng.randint(0, 300),
                   serial=serials[i]) for i, (w, v, c) in enumerate(specs)]
    cap = 40
    total = sum(w for w, _, _ in specs)
    assert 10 * total <= 100 * cap <= 70 * total
    greedy, best = greedy_ratio_value(crates, cap), knapsack_value(crates, cap)
    assert 10 * greedy <= 6 * best, (greedy, best)
    return crates, cap


# ---------------------------------------------------------------- 48

def trap48_network(rng):
    V = rng.randint(1500, 3000)
    B = rng.randint(560, 700)
    x, c1, c2, c3, T = B, B + 1, B + 2, B + 3, B + 4
    protected = {x, c1, c2, c3, T}
    edges, pos = [], [0] * V
    for i in range(1, B):
        edges.append((i - 1, i))
        pos[i] = i
    edges += [(0, x), (x, T), (0, c1), (c1, c2), (c2, c3), (c3, T)]
    for i in range(B + 5, V):
        while True:
            j = rng.randrange(i)
            if j not in protected:
                break
        edges.append((j, i))
        pos[i] = pos[j]
    E = rng.randint(math.ceil(1.25 * V), math.floor(1.6 * V))
    have = {(min(a, b), max(a, b)) for a, b in edges}
    by_pos = {}
    for i in range(V):
        if i not in protected:
            by_pos.setdefault(pos[i], []).append(i)
    free = [i for i in range(V) if i not in protected]
    while len(edges) < E:
        u = rng.choice(free)
        group = by_pos.get(pos[u] + rng.choice((-1, 0, 1)))
        if not group:
            continue
        v = rng.choice(group)
        key = (min(u, v), max(u, v))
        if u != v and key not in have:
            have.add(key)
            edges.append(key)

    # fixed minutes for the gadget, random for the rest
    gadget_minutes = {(0, x): 60, (x, T): 60, (0, c1): 1, (c1, c2): 1, (c2, c3): 1, (c3, T): 1}
    minutes_old = {}
    for a, b in edges:
        key = (min(a, b), max(a, b))
        minutes_old[key] = gadget_minutes.get(key, rng.randint(1, 60))

    new_edges, new_id = relabel(rng, V, edges)
    types = assign_types(rng, V, 1)
    pen = [0] + [rng.choice(PENALTIES) for _ in range(V - 1)]
    for old in (x, c1, c2, c3):
        types[new_id[old]] = "J"
    pen[new_id[x]] = 6
    for old in (c1, c2, c3):
        pen[new_id[old]] = 0
    tT = new_id[T]
    types[tT] = "H"
    t_far = new_id[B - 1]                       # end of the highway, >= 559 roads away
    types[t_far] = "S"
    others = [i for i in range(1, V) if types[i] in "SH" and i not in (tT, t_far)]
    targets = [tT, t_far, rng.choice(others)]
    rng.shuffle(targets)

    order = list(range(len(edges)))
    rng.shuffle(order)
    roads = []
    for road_no, ei in enumerate(order):
        a, b = edges[ei]
        u, v = new_edges[ei]
        roads.append(dict(road_no=road_no, u=u, v=v, minutes=minutes_old[(min(a, b), max(a, b))],
                          cable=rng.randint(1, 100)))

    # self-checks of the trap rules
    _, dist, fewest = route_costs(V, roads, pen)
    assert 2 * fewest[tT] >= 3 * dist[tT], (fewest[tT], dist[tT])
    adj = adjacency(V, roads)
    hops, _ = bfs_order(V, adj, 0)
    far = max(range(V), key=lambda i: hops[i])
    hops2, _ = bfs_order(V, adj, far)
    assert max(hops2) >= 500

    waves = make_waves(rng, len(roads), 1)
    locations = [dict(loc_id=i, type=types[i], penalty=pen[i]) for i in range(V)]
    return dict(locations=locations, roads=roads, waves=waves, targets=targets)


# ---------------------------------------------------------------- 49

def _split(rng, total, parts, minimum):
    """Split `total` into `parts` positive integers, each >= minimum."""
    cuts = sorted(rng.sample(range(1, total - parts * minimum + parts), parts - 1))
    sizes, prev = [], 0
    for c in cuts + [total - parts * minimum + parts]:
        sizes.append(c - prev - 1 + minimum)
        prev = c
    return sizes


def trap49_log(rng, N):
    noise_alphabet = [ch for ch in ALPHABET if ch not in "AB"]
    clumps = rng.randint(8, 14)
    noise_total = int(N * rng.uniform(0.04, 0.065))
    clump_sizes = _split(rng, noise_total, clumps, 20)
    run_sizes = _split(rng, N - noise_total, clumps + 1, 500)
    planted_in = rng.randrange(clumps)
    pieces = []
    for i in range(clumps):
        pieces.append("A" * run_sizes[i])
        clump = [rng.choice(noise_alphabet) for _ in range(clump_sizes[i])]
        if i == planted_in:
            mid = len(clump) // 2
            clump[mid:mid + 4] = list("AAAB")
            clump[mid - 1] = rng.choice(noise_alphabet)      # a non-A before the plant
        pieces.append("".join(clump))
    pieces.append("A" * run_sizes[-1])
    log = "".join(pieces)
    assert len(log) == N, (len(log), N)

    rows = []
    for no, L in enumerate(PATTERN_LENGTHS):
        p = "A" * (L - 1) + "B"
        rows.append(dict(pattern_no=no, pattern=p, count=count_overlapping(log, p)))
    # self-checks
    occurring = sum(1 for r in rows if r["count"] > 0)
    assert occurring >= 2 and occurring < 6
    for r in rows:
        L = len(r["pattern"])
        prefix = r["pattern"][:-1]
        matches = sum(1 for i in range(N - L + 1) if log.startswith(prefix, i))
        assert 2 * matches >= N - L + 1
    assert 10 * log.count("A") >= 9 * N
    return log, rows
