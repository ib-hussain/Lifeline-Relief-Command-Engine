"""V4: the network is connected before closures; waves are disjoint and within their size limit."""
from algos import neighbours, bfs


def check_case(c, book, ctx):
    e = []
    V, E = len(c.locations), len(c.roads)
    dist, _ = bfs(neighbours(V, c.roads), 0)
    cut = [i for i, d in enumerate(dist) if d < 0]
    if cut:
        e.append(f"network is not connected before closures: {len(cut)} locations unreachable "
                 f"from the HQ (e.g. {cut[:5]})")
    limit = max(1, E // 4)
    waves = {}
    for w in c.waves:
        waves.setdefault(w["wave_no"], []).append(w["road_no"])
    owner = {}
    for no in sorted(waves):
        roads = waves[no]
        if len(set(roads)) != len(roads):
            e.append(f"wave {no} lists a road twice")
        if not 1 <= len(set(roads)) <= limit:
            e.append(f"wave {no} closes {len(set(roads))} roads, allowed 1..{limit}")
        for road in set(roads):
            if road in owner:
                e.append(f"road {road} is in wave {owner[road]} and wave {no}: waves must be disjoint")
            owner[road] = no
    return e
