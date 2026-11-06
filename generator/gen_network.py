"""locations, roads, waves and the three targets.

Construction:
  1. a random spanning tree (so the map is connected before any closure),
  2. extra roads until E matches the average degree of the case study,
  3. random relabelling of locations 1..V-1 (HQ stays 0),
  4. types, penalties, minutes, cable, targets and closure waves.

Story -> numbers (average degree = 2E/V):
  1 Delta Flood        2.2..3.2, chain-like villages, >= 45% of locations penalty >= 2, >= 3 waves
  2 Mountain Earthq.   2.0..2.6, "few roads and almost no alternatives", slow roads (5..60 min)
  3 Coastal Cyclone    2.4..4.0, >= 30% shelters, >= 3 waves
  4 Urban Flash Flood  3.5..5.0, "many alternative routes", short city roads (1..25 min)
  5 Landslide Corridor <= 2.4, a long path (the highway) with short spurs, max degree 4,
                       a bridge of the corridor is put in a wave so a target is cut off
  6 Outbreak Camp      2.2..3.6
"""
import math
from fractions import Fraction

from common import ceil_div, adjacency, bfs_order, route_costs, find_bridges

DEGREE = {
    1: (Fraction(22, 10), Fraction(32, 10)),
    2: (Fraction(2), Fraction(26, 10)),
    3: (Fraction(24, 10), Fraction(4)),
    4: (Fraction(35, 10), Fraction(5)),
    5: (Fraction(0), Fraction(24, 10)),
    6: (Fraction(22, 10), Fraction(36, 10)),
}
MINUTES = {2: (5, 60), 4: (1, 25)}


def edge_range(V, study):
    lo, hi = DEGREE[study]
    emin = max(V - 1, math.ceil(lo * V / 2))
    emax = min(3 * V, math.floor(hi * V / 2), V * (V - 1) // 2)
    return emin, emax


# ---------------------------------------------------------------- structure

def _tree(rng, V, study):
    edges, pos, deg = [], [0] * V, [0] * V
    if study == 5:
        P = rng.randint(max(2, (2 * V) // 3), V)        # nodes on the highway
        for i in range(1, P):
            edges.append((i - 1, i))
            pos[i] = i
            deg[i - 1] += 1
            deg[i] += 1
        for i in range(P, V):                            # short spurs, degree stays <= 3 here
            while True:
                j = rng.randrange(i)
                if deg[j] < 3:
                    break
            edges.append((j, i))
            pos[i] = pos[j]
            deg[j] += 1
            deg[i] += 1
    else:
        spread = {1: max(2, V // 4), 2: max(2, V // 6), 3: max(2, V // 2),
                  4: V, 6: max(2, V // 2)}[study]
        for i in range(1, V):
            j = rng.randint(max(0, i - spread), i - 1)
            edges.append((j, i))
            pos[i] = pos[j] + 1
            deg[j] += 1
            deg[i] += 1
    return edges, pos, deg


def _add_extra(rng, V, E, edges, pos, deg, study):
    have = {(min(a, b), max(a, b)) for a, b in edges}
    by_pos = {}
    for i in range(V):
        by_pos.setdefault(pos[i], []).append(i)
    local = max(2, V // 8)
    tries, limit = 0, 400 * E + 2000
    while len(edges) < E:
        tries += 1
        if tries > limit:
            return False
        u = rng.randrange(V)
        if study == 5:
            group = by_pos.get(pos[u] + rng.randint(-2, 2))
            if not group:
                continue
            v = rng.choice(group)
            if deg[u] >= 4 or deg[v] >= 4:
                continue
        elif study in (1, 2) and tries < limit // 2:
            v = u + rng.randint(-local, local)
        else:
            v = rng.randrange(V)
        if v < 0 or v >= V or u == v:
            continue
        key = (min(u, v), max(u, v))
        if key in have:
            continue
        have.add(key)
        edges.append(key)
        deg[u] += 1
        deg[v] += 1
    return True


def relabel(rng, V, edges):
    """Shuffle ids 1..V-1 (the HQ keeps id 0) so ids carry no structure."""
    perm = list(range(1, V))
    rng.shuffle(perm)
    new_id = [0] + perm
    out = [(min(new_id[a], new_id[b]), max(new_id[a], new_id[b])) for a, b in edges]
    return out, new_id


# ---------------------------------------------------------------- attributes

def assign_types(rng, V, study):
    others = V - 1
    n_s = ceil_div(3 * V, 10) if study == 3 else max(1, round(0.22 * others))
    n_h = max(1, round(0.12 * others))
    n_d = round(0.03 * others)
    if n_s + n_h < 3:
        n_s = 3 - n_h
    while n_s + n_h + n_d > others:
        n_d -= 1
    types = ["S"] * n_s + ["H"] * n_h + ["D"] * n_d + ["J"] * (others - n_s - n_h - n_d)
    rng.shuffle(types)
    return ["D"] + types


def assign_penalties(rng, V, study):
    pen = [0] * V
    if study == 1:
        high = set(rng.sample(range(1, V), ceil_div(45 * V, 100)))
        for i in range(1, V):
            pen[i] = rng.choice((2, 4, 6)) if i in high else rng.choice((0, 0, 1, 2))
    else:
        for i in range(1, V):
            pen[i] = rng.choice((0, 0, 0, 1, 1, 2, 4, 6))
    return pen


def make_roads(rng, edges, study):
    lo, hi = MINUTES.get(study, (1, 60))
    order = list(edges)
    rng.shuffle(order)
    return [dict(road_no=i, u=u, v=v, minutes=rng.randint(lo, hi), cable=rng.randint(1, 100))
            for i, (u, v) in enumerate(order)]


def make_waves(rng, E, study, required=()):
    """Disjoint waves of 1..max(1, E//4) roads each. `required` roads must be closed."""
    n_waves = rng.randint(3, 5) if study in (1, 3, 5) else rng.randint(2, 5)
    cap = max(1, E // 4)
    soft = max(1, min(cap, E // 12))
    sizes = [rng.randint(1, soft) for _ in range(n_waves)]
    waves = [[] for _ in range(n_waves)]
    for r in required:
        waves[rng.randrange(n_waves)].append(r)
    pool = [r for r in range(E) if r not in set(required)]
    rng.shuffle(pool)
    for w in range(n_waves):
        while len(waves[w]) < sizes[w]:
            waves[w].append(pool.pop())
    rows = []
    for w, roads in enumerate(waves):
        for r in sorted(roads):
            rows.append(dict(wave_no=w, road_no=r))
    return rows


def avg_degree_ok(V, E, study):
    lo, hi = DEGREE[study]
    return lo <= Fraction(2 * E, V) <= hi


# ---------------------------------------------------------------- main entry

def gen_network(rng, V, study, need_variety2=False):
    """Returns dict(locations, roads, waves, targets) or None to ask for a retry."""
    emin, emax = edge_range(V, study)
    if emin > emax:
        return None
    E = rng.randint(emin, emax)
    edges, pos, deg = _tree(rng, V, study)
    if not _add_extra(rng, V, E, edges, pos, deg, study):
        return None
    edges, _ = relabel(rng, V, edges)
    types = assign_types(rng, V, study)
    pen = assign_penalties(rng, V, study)
    roads = make_roads(rng, edges, study)
    E = len(roads)
    if not avg_degree_ok(V, E, study):
        return None

    required = []
    targets = None
    candidates = [i for i in range(1, V) if types[i] in "SH"]

    if study == 5:
        degree = [0] * V
        for r in roads:
            degree[r["u"]] += 1
            degree[r["v"]] += 1
        if max(degree) > 4:
            return None
        adj = adjacency(V, roads)
        hops, _ = bfs_order(V, adj)
        if max(hops) < V // 4:
            return None
        # find a target behind a bridge and close that bridge in a wave
        pairs = [(r["u"], r["v"]) for r in roads]
        bridges = find_bridges(V, pairs)
        non_bridge = {(r["u"], r["v"]) for i, r in enumerate(roads) if i not in bridges}
        # component of the HQ without bridges
        comp = {0}
        stack = [0]
        while stack:
            u = stack.pop()
            for v, _ in adj[u]:
                if v not in comp and (min(u, v), max(u, v)) in non_bridge:
                    comp.add(v)
                    stack.append(v)
        outside = [i for i in range(1, V) if i not in comp]
        if not outside:
            return None
        far = max(outside, key=lambda i: (hops[i], -i))
        if types[far] not in "SH":
            types[far] = rng.choice("SH")
        # walk back along a BFS path from `far` to the HQ and collect its bridges
        parent = {0: None}
        order = [0]
        for u in order:
            for v, _ in adj[u]:
                if v not in parent:
                    parent[v] = u
                    order.append(v)
        index = {(r["u"], r["v"]): i for i, r in enumerate(roads)}
        path_bridges, x = [], far
        while parent[x] is not None:
            key = (min(x, parent[x]), max(x, parent[x]))
            if index[key] in bridges:
                path_bridges.append(index[key])
            x = parent[x]
        required = [rng.choice(path_bridges)]
        candidates = [i for i in range(1, V) if types[i] in "SH" and i != far]
        if len(candidates) < 2:
            return None
        targets = [far] + rng.sample(candidates, 2)
        rng.shuffle(targets)

    elif need_variety2:
        _, dist, fewest = route_costs(V, roads, pen)
        good = [i for i in candidates if fewest[i] > dist[i]]
        if not good:
            return None
        first = rng.choice(good)
        others = [i for i in candidates if i != first]
        targets = [first] + rng.sample(others, 2)
        rng.shuffle(targets)
    else:
        targets = rng.sample(candidates, 3)

    if types.count("S") < 1 or types.count("H") < 1:
        return None
    if study == 3 and 100 * types.count("S") < 25 * V:
        return None
    if study == 1 and 100 * sum(1 for p in pen if p >= 2) < 40 * V:
        return None

    waves = make_waves(rng, E, study, required)
    locations = [dict(loc_id=i, type=types[i], penalty=pen[i]) for i in range(V)]
    return dict(locations=locations, roads=roads, waves=waves, targets=targets)
