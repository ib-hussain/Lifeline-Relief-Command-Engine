"""V7: the signature rules of each case (0 to 45) and the four variety rules."""
from bisect import bisect_left
from collections import Counter
from fractions import Fraction

from algos import neighbours, bfs, dijkstra, cheapest_fewest_roads, knapsack, greedy_by_ratio
from spec import expected_scenario, expected_tier

F = Fraction


def _pct(count, total, pct):
    """count/total >= pct% with integers only."""
    return 100 * count >= pct * total


def _overlap_pairs(windows):
    iv = sorted((w["start"], w["finish"]) for w in windows)
    starts = [s for s, _ in iv]
    return sum(bisect_left(starts, f) - (i + 1) for i, (s, f) in enumerate(iv))


def check_case(c, book, ctx):
    k = c.row["case_no"]
    if not 0 <= k <= 45:
        return []
    e = []
    study = expected_scenario(k)
    V, E = len(c.locations), len(c.roads)
    deg = F(2 * E, V)
    cats = Counter(x["cat"] for x in c.crates)
    n_cr = len(c.crates)
    n_waves = len({w["wave_no"] for w in c.waves})
    pens = [x["penalty"] for x in c.locations]
    types = [x["type"] for x in c.locations]
    log = c.log()

    def need(cond, msg):
        if not cond:
            e.append(f"study {study}: {msg}")

    if study == 1:
        need(F(22, 10) <= deg <= F(32, 10), f"average degree {float(deg):.3f} not in 2.2..3.2")
        need(_pct(sum(p >= 2 for p in pens), V, 40), "fewer than 40% of locations have penalty >= 2")
        need(n_waves >= 3, f"{n_waves} waves, need at least 3")
        need(_pct(cats[0] + cats[1], n_cr, 55), "food+water crates below 55%")
    elif study == 2:
        need(F(2) <= deg <= F(26, 10), f"average degree {float(deg):.3f} not in 2.0..2.6")
        need(_pct(cats[2] + cats[3], n_cr, 45), "medicine+tool crates below 45%")
        need(sum(a["priority"] for a in c.incidents) >= 6 * len(c.incidents), "mean alarm priority below 6.0")
    elif study == 3:
        need(_pct(types.count("S"), V, 25), "fewer than 25% shelters")
        need(n_waves >= 3, f"{n_waves} waves, need at least 3")
        pairs = _overlap_pairs(c.windows)
        need(2 * pairs >= 2 * len(c.windows),
             f"average overlaps per window {2 * pairs / len(c.windows):.2f} < 2")
        need(len(set(log)) >= 30, f"log uses {len(set(log))} symbols, need >= 30")
    elif study == 4:
        need(deg >= F(35, 10), f"average degree {float(deg):.3f} below 3.5")
        if expected_tier(k) in ("M", "L"):
            n = len(c.incidents)
            T = max(a["tick"] for a in c.incidents) + 1
            need(10 * n >= 15 * T, f"alarms per tick {n / T:.3f} below 1.5")
        need(_pct(cats[4], n_cr, 10), "rare crates below 10%")
    elif study == 5:
        need(deg <= F(24, 10), f"average degree {float(deg):.3f} above 2.4")
        degree = Counter()
        for x in c.roads:
            degree[x["u"]] += 1
            degree[x["v"]] += 1
        need(max(degree.values()) <= 4, f"a location has {max(degree.values())} roads (max 4)")
        hops, _ = bfs(neighbours(V, c.roads), 0)
        need(max(hops) >= V // 4, f"farthest location is {max(hops)} roads away, need >= {V // 4}")
        need(n_waves >= 3, f"{n_waves} waves, need at least 3")
        closed = frozenset(w["road_no"] for w in c.waves)
        after, _ = bfs(neighbours(V, c.roads, closed), 0)
        targets = [c.row["target_0"], c.row["target_1"], c.row["target_2"]]
        need(any(after[t] < 0 for t in targets), "union of all waves leaves every target reachable")
    elif study == 6:
        need(_pct(cats[2] + cats[1], n_cr, 55), "medicine+water crates below 55%")
        need(2 * sum(x["expiry"] <= 300 for x in c.crates) >= n_cr, "fewer than half the crates expire by hour 300")
        top = max(Counter(log).values()) if log else 0
        need(4 * top >= len(log), "no symbol is at least 25% of the log")
    return e


# ------------------------------------------------------------ variety rules (whole workbook)

def _fewest_costs_more(c):
    V = len(c.locations)
    pen = [0] * V
    for x in c.locations:
        pen[x["loc_id"]] = x["penalty"]
    adj = neighbours(V, c.roads)
    dist = dijkstra(adj, pen, 0)
    fewest = cheapest_fewest_roads(adj, pen, 0)
    return any(fewest[t] > dist[t] for t in (c.row["target_0"], c.row["target_1"], c.row["target_2"]))


def _module_signatures(c):
    """(module, size, content without case_id) for variety rule 4."""
    def rows(sheet, drop=("case_id",)):
        return tuple(tuple(v for kk, v in sorted(r.items()) if kk not in drop) for r in c.sheets[sheet])
    yield "crates", len(c.crates), rows("crates")
    yield "network", len(c.locations), (rows("locations"), rows("roads"))
    yield "radio", len(c.log()), c.log()
    yield "windows", len(c.windows), rows("windows")
    yield "incidents", len(c.incidents), rows("incidents")
    yield "tour", len(c.sites), (rows("sites"), rows("tour"))
    yield "pipeline", len(c.pipeline_dims) - 1, rows("pipeline_dims")
    yield "drum", len(c.drum_prices), rows("drum_prices")
    yield "sensors", c.row["sensor_nodes"], (rows("sensor_edges"), rows("sensor_cover"))
    yield "safety", c.row["safety_vars"], (rows("safety_rules"), rows("safety_planted"))
    yield "rations", len(c.rations), rows("rations")


def check_book(book, ctx):
    if ctx.partial:
        return []
    e = []
    cases = list(book.cases.values())
    tier_s = [c for c in cases if c.row["case_no"] <= 19]

    v1 = [c.case_id for c in tier_s if greedy_by_ratio(c.crates, c.row["capacity"]) <
          knapsack([(x["weight"], x["value"]) for x in c.crates], c.row["capacity"])]
    if len(v1) < 5:
        e.append(f"variety 1: greedy-by-ratio is not optimal in only {len(v1)} tier-S cases (need >= 5)")

    v2 = [c.case_id for c in tier_s if _fewest_costs_more(c)]
    if len(v2) < 5:
        e.append(f"variety 2: only {len(v2)} tier-S cases where every fewest-roads route to a target "
                 f"costs more than a cheapest route (need >= 5)")

    ml = [c for c in cases if 20 <= c.row["case_no"] <= 45]
    low = mid = high = 0
    for c in ml:
        m, n = len(c.safety_rules), c.row["safety_vars"]
        if not (5 * n <= 2 * m and m <= 6 * n):
            e.append(f"variety 3: {c.case_id} rules/switches {m}/{n} not in 2.5..6.0")
        if 2 * m < 7 * n:
            low += 1
        elif 5 * m <= 24 * n:
            mid += 1
        else:
            high += 1
    if len(ml) != 26 or low < 5 or mid < 8 or high < 5:
        e.append(f"variety 3: tiers M+L have {low} cases < 3.5, {mid} in 3.5..4.8, {high} > 4.8 "
                 f"(need >= 5, >= 8, >= 5 over 26 cases)")

    seen = {}
    for c in cases:
        for module, size, content in _module_signatures(c):
            if size < 8:
                continue
            key = (module, content)
            if key in seen:
                e.append(f"variety 4: module {module} of {c.case_id} equals that of {seen[key]}")
            else:
                seen[key] = c.case_id
    ctx.notes.append(f"variety 1 holds in {len(v1)} tier-S cases: {', '.join(v1)}")
    ctx.notes.append(f"variety 2 holds in {len(v2)} tier-S cases: {', '.join(v2)}")
    ctx.notes.append(f"variety 3 (M+L safety ratio bins): {low} low, {mid} mid, {high} high")
    return e
