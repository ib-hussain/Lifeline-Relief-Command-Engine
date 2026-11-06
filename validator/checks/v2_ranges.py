"""V2: every size and every value is inside its range."""
from spec import size_ranges, expected_tier, ALPHABET, PENALTIES


def check_case(c, book, ctx):
    e = []
    r = c.row
    k = r["case_no"]
    tier = expected_tier(k)
    R = size_ranges(k)

    def within(label, val, lo, hi):
        if not (lo <= val <= hi):
            e.append(f"{label} = {val} not in {lo}..{hi}")

    # crates + capacity
    within("number of crates", len(c.crates), *R["crates"])
    for x in c.crates:
        i = x["crate_id"]
        within(f"crate {i} cat", x["cat"], 0, 4)
        within(f"crate {i} weight", x["weight"], 1, 20)
        within(f"crate {i} value", x["value"], 10, 100)
        within(f"crate {i} expiry", x["expiry"], 0, 999)
        within(f"crate {i} serial", x["serial"], 10_000_000, 99_999_999)
    total = sum(x["weight"] for x in c.crates)
    cap = r["capacity"]
    if cap < 1 or not (10 * total <= 100 * cap <= 70 * total):
        e.append(f"capacity {cap} is not 10%..70% of total crate weight {total} (and >= 1)")

    # network
    V, E = len(c.locations), len(c.roads)
    within("V (locations)", V, *R["locations"])
    within("E (roads)", E, V - 1, 3 * V)
    for x in c.locations:
        if x["type"] not in ("D", "S", "H", "J"):
            e.append(f"location {x['loc_id']} type {x['type']!r} not in D/S/H/J")
        if x["penalty"] not in PENALTIES:
            e.append(f"location {x['loc_id']} penalty {x['penalty']} not in {{0,1,2,4,6}}")
    hq = [x for x in c.locations if x["loc_id"] == 0]
    if not hq or hq[0]["type"] != "D" or hq[0]["penalty"] != 0:
        e.append("location 0 (HQ) must be type D with penalty 0")
    types = [x["type"] for x in c.locations]
    if "S" not in types or "H" not in types:
        e.append("needs at least one shelter (S) and one hospital (H)")
    for x in c.roads:
        within(f"road {x['road_no']} minutes", x["minutes"], 1, 60)
        within(f"road {x['road_no']} cable", x["cable"], 1, 100)
        if not x["u"] < x["v"]:
            e.append(f"road {x['road_no']}: u < v is required ({x['u']}, {x['v']})")
    within("number of waves", len({w["wave_no"] for w in c.waves}), *R["waves"])

    # radio
    log = c.log()
    within("log length", len(log), *R["log"])
    bad = set(log) - ALPHABET
    if bad:
        e.append(f"log uses symbols outside the 38-symbol alphabet: {sorted(bad)[:10]}")
    for rep in c.radio_reports:
        for col in ("report_a", "report_b"):
            within(f"length of {col}", len(rep[col]), *R["report"])
            if set(rep[col]) - ALPHABET:
                e.append(f"{col} uses symbols outside the alphabet")

    # windows
    W = c.windows
    within("number of windows", len(W), *R["windows"])
    for w in W:
        i = w["window_id"]
        if not (0 <= w["start"] < w["finish"] <= 1440):
            e.append(f"window {i}: need 0 <= start < finish <= 1440 ({w['start']}, {w['finish']})")
        within(f"window {i} duration", w["finish"] - w["start"], 5, 480)
        within(f"window {i} value", w["value"], 1, 100)
    if len(W) >= 8:
        starts = {}
        for w in W:
            starts[w["start"]] = starts.get(w["start"], 0) + 1
        touching = sum(starts.get(w["finish"], 0) for w in W)
        if touching < 2:
            e.append(f"only {touching} touching pairs of windows, need at least 2")

    # incidents
    A = sorted(c.incidents, key=lambda a: a["alarm_id"])
    within("number of alarms", len(A), *R["alarms"])
    if A:
        if A[0]["tick"] != 0:
            e.append(f"first tick is {A[0]['tick']}, must start at 0")
        for a, b in zip(A, A[1:]):
            if b["tick"] < a["tick"]:
                e.append(f"tick decreases at alarm {b['alarm_id']}")
                break
        for a in A:
            within(f"alarm {a['alarm_id']} priority", a["priority"], 1, 10)
        if tier != "S":
            n, T = len(A), A[-1]["tick"] + 1
            if not (12 * T <= 10 * n <= 18 * T):
                e.append(f"alarms per tick = {n}/{T} = {n / T:.3f} not in 1.2..1.8")
            prios = {a["priority"] for a in A}
            if len(prios) < 6 or 1 not in prios:
                e.append(f"priorities {sorted(prios)}: need >= 6 distinct including 1")

    # sites
    within("number of sites", len(c.sites), *R["sites"])
    pts = set()
    for s in c.sites:
        within(f"site {s['site_no']} x", s["x"], 0, 999)
        within(f"site {s['site_no']} y", s["y"], 0, 999)
        pts.add((s["x"], s["y"]))
    if len(pts) != len(c.sites):
        e.append("two sites are equal")

    # pipeline + drum
    within("pipeline stages", len(c.pipeline_dims) - 1, *R["stages"])
    for d in c.pipeline_dims:
        within(f"dim idx {d['idx']}", d["dim"], 2, 100)
    P = sorted(c.drum_prices, key=lambda p: p["length"])
    within("drum length L", len(P), *R["drum"])
    for p in P:
        within(f"price of length {p['length']}", p["price"], 1, 500)
    if P and all(p["price"] * P[0]["length"] == P[0]["price"] * p["length"] for p in P):
        e.append("drum prices are all proportional to length")

    # sensors
    n = r["sensor_nodes"]
    within("sensor_nodes", n, *R["sensors"])
    if not (2 <= r["sensor_k"] and 2 * r["sensor_k"] <= n):
        e.append(f"sensor_k = {r['sensor_k']} must satisfy 2 <= k <= n/2 (n = {n})")

    # safety
    nv, m = r["safety_vars"], len(c.safety_rules)
    within("safety_vars", nv, *R["safety_vars"])
    if not (2 * nv <= m <= 6 * nv):
        e.append(f"rules/switches = {m}/{nv} not in 2.0..6.0")
    for p in c.safety_planted:
        if p["value"] not in (0, 1):
            e.append(f"planted switch {p['switch']} value {p['value']} not 0/1")

    # rations
    within("number of ration quantities", len(c.rations), *R["rations"])
    for x in c.rations:
        within(f"ration item {x['item']} value", x["value"], 1, 1000)
        if x["planted"] not in (0, 1):
            e.append(f"ration item {x['item']} planted must be 0 or 1")
    if r["rations_target"] < 1:
        e.append("rations_target must be positive")
    return e
