"""V6: every planted object is valid: the tour and its length, the cover, the assignment,
the ration selection."""
from algos import manhattan, nearest_neighbour_length
from spec import expected_tier


def check_case(c, book, ctx):
    e = []
    r = c.row
    tier = expected_tier(r["case_no"])

    # tour
    pts = {s["site_no"]: (s["x"], s["y"]) for s in c.sites}
    order = [x["site_no"] for x in sorted(c.tour, key=lambda x: x["step"])]
    if sorted(order) != sorted(pts):
        e.append("planted tour is not a permutation of all sites")
    elif order[0] != 0:
        e.append(f"planted tour starts at site {order[0]}, must start at site 0")
    else:
        length = sum(manhattan(pts[order[i]], pts[order[(i + 1) % len(order)]]) for i in range(len(order)))
        if length != r["tour_length"]:
            e.append(f"tour_length {r['tour_length']} but the planted tour's closed Manhattan length is {length}")
        if tier in ("L", "X"):
            nn = nearest_neighbour_length([pts[i] for i in range(len(pts))])
            if length > nn:
                e.append(f"planted tour ({length}) is longer than the nearest-neighbour tour ({nn})")

    # cover
    n = r["sensor_nodes"]
    cover = {x["node"] for x in c.sensor_cover}
    if len(c.sensor_cover) != r["sensor_k"]:
        e.append(f"sensor_cover has {len(c.sensor_cover)} nodes, sensor_k is {r['sensor_k']}")
    missed = [(x["u"], x["v"]) for x in c.sensor_edges if x["u"] not in cover and x["v"] not in cover]
    if missed:
        e.append(f"planted cover misses {len(missed)} edges, e.g. {missed[:3]}")
    if len(c.sensor_edges) < n - 1:
        e.append(f"only {len(c.sensor_edges)} sensor edges, need at least n - 1 = {n - 1}")

    # assignment
    value = {x["switch"]: x["value"] for x in c.safety_planted}
    broken = []
    for x in c.safety_rules:
        lits = (x["lit_1"], x["lit_2"], x["lit_3"])
        if not any(abs(l) in value and value[abs(l)] == (1 if l > 0 else 0) for l in lits):
            broken.append(x["rule_no"])
    if broken:
        e.append(f"planted assignment violates {len(broken)} rules, e.g. rules {broken[:5]}")

    # rations
    chosen = [x["value"] for x in c.rations if x["planted"] == 1]
    if not chosen:
        e.append("no ration item is planted")
    elif sum(chosen) != r["rations_target"]:
        e.append(f"planted rations sum to {sum(chosen)}, rations_target is {r['rations_target']}")
    return e
