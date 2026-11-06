"""V3: identifiers are unique and consecutive where required; every reference exists
(road ends, targets, wave roads, tour sites, cover nodes, rule switches, planted items)."""


def _consecutive(e, label, ids, start):
    if sorted(ids) != list(range(start, start + len(ids))):
        e.append(f"{label} are not exactly {start}..{start + len(ids) - 1}, each once")


def check_case(c, book, ctx):
    e = []
    r = c.row
    _consecutive(e, "crate_id values", [x["crate_id"] for x in c.crates], 1)
    serials = [x["serial"] for x in c.crates]
    if len(set(serials)) != len(serials):
        e.append("crate serials are not distinct")

    V = len(c.locations)
    _consecutive(e, "loc_id values", [x["loc_id"] for x in c.locations], 0)
    E = len(c.roads)
    _consecutive(e, "road_no values", [x["road_no"] for x in c.roads], 0)
    pairs = set()
    for x in c.roads:
        for end in ("u", "v"):
            if not 0 <= x[end] < V:
                e.append(f"road {x['road_no']} {end} = {x[end]} is not a location (0..{V - 1})")
        key = (min(x["u"], x["v"]), max(x["u"], x["v"]))
        if key in pairs:
            e.append(f"road {x['road_no']} repeats the pair {key}")
        pairs.add(key)

    types = {x["loc_id"]: x["type"] for x in c.locations}
    targets = [r["target_0"], r["target_1"], r["target_2"]]
    if len(set(targets)) != 3:
        e.append(f"targets {targets} are not distinct")
    for t in targets:
        if t == 0 or types.get(t) not in ("S", "H"):
            e.append(f"target {t} must be a shelter or hospital and not the HQ")

    _consecutive(e, "wave_no values", sorted({w["wave_no"] for w in c.waves}), 0)
    for w in c.waves:
        if not 0 <= w["road_no"] < E:
            e.append(f"wave {w['wave_no']} closes road {w['road_no']}, which does not exist")

    _consecutive(e, "radio_log parts", [x["part"] for x in c.radio_log], 1)
    _consecutive(e, "pattern_no values", [x["pattern_no"] for x in c.radio_patterns], 0)
    if len(c.radio_patterns) != 6:
        e.append(f"{len(c.radio_patterns)} patterns, expected exactly 6")
    _consecutive(e, "window_id values", [x["window_id"] for x in c.windows], 1)
    _consecutive(e, "alarm_id values", [x["alarm_id"] for x in c.incidents], 1)

    n_sites = len(c.sites)
    _consecutive(e, "site_no values", [x["site_no"] for x in c.sites], 0)
    _consecutive(e, "tour steps", [x["step"] for x in c.tour], 0)
    for x in c.tour:
        if not 0 <= x["site_no"] < n_sites:
            e.append(f"tour step {x['step']} visits site {x['site_no']}, which does not exist")

    _consecutive(e, "pipeline idx values", [x["idx"] for x in c.pipeline_dims], 0)
    _consecutive(e, "drum lengths", [x["length"] for x in c.drum_prices], 1)

    n = r["sensor_nodes"]
    seen = set()
    for x in c.sensor_edges:
        u, v = x["u"], x["v"]
        if not (0 <= u < v < n):
            e.append(f"sensor edge ({u},{v}) needs 0 <= u < v < {n}")
        if (u, v) in seen:
            e.append(f"sensor edge ({u},{v}) is repeated")
        seen.add((u, v))
    cover = [x["node"] for x in c.sensor_cover]
    if len(set(cover)) != len(cover):
        e.append("sensor_cover nodes are not distinct")
    for x in cover:
        if not 0 <= x < n:
            e.append(f"cover node {x} is not a sensor node")

    nv = r["safety_vars"]
    _consecutive(e, "rule_no values", [x["rule_no"] for x in c.safety_rules], 1)
    for x in c.safety_rules:
        lits = [x["lit_1"], x["lit_2"], x["lit_3"]]
        if any(l == 0 or abs(l) > nv for l in lits):
            e.append(f"rule {x['rule_no']} literal outside +-1..{nv}: {lits}")
        if len({abs(l) for l in lits}) != 3:
            e.append(f"rule {x['rule_no']} does not use three different switches: {lits}")
    _consecutive(e, "safety_planted switches", [x["switch"] for x in c.safety_planted], 1)
    if len(c.safety_planted) != nv:
        e.append(f"safety_planted has {len(c.safety_planted)} switches, expected {nv}")

    _consecutive(e, "ration items", [x["item"] for x in c.rations], 0)
    return e
