"""LIFELINE Iteration 1 generator: writes cases.xlsx (50 cases) from the group seed.

    python generator/generate.py --seed 18 --out cases.xlsx

Case k: tier S (0-19), M (20-39), L (40-45), X (46-49 traps); case study (k mod 6) + 1.
All randomness comes from make_rng(seed, k, module, attempt), so the same seed always
gives the same workbook content.
"""
import argparse
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from common import make_rng, retry, tier_of, scenario_of           # noqa: E402
from spec import ranges_for, HEADERS                                 # noqa: E402
from gen_crates import gen_crates, choose_capacity, greedy_is_suboptimal   # noqa: E402
from gen_network import gen_network                                  # noqa: E402
from gen_radio import gen_log, split_log, gen_patterns, gen_reports  # noqa: E402
from gen_windows import gen_windows                                  # noqa: E402
from gen_incidents import gen_incidents                              # noqa: E402
from gen_tour import gen_tour                                        # noqa: E402
from gen_pipeline import gen_dims, gen_drum                          # noqa: E402
from gen_sensors import gen_sensors                                  # noqa: E402
from gen_safety import gen_safety                                    # noqa: E402
from gen_rations import gen_rations                                  # noqa: E402
from traps import trap46_crates, trap47_crates, trap48_network, trap49_log   # noqa: E402
from claims import compute_claims                                    # noqa: E402
from writer import write_workbook                                    # noqa: E402

N_CASES = 50


def plan_variety(seed):
    """Decide up front which cases carry the variety rules (Section 3, 'Variety')."""
    rng = make_rng(seed, -1, "variety-plan")
    variety1 = set(rng.sample(range(20), 8))                    # greedy-by-ratio not optimal
    v2_pool = [k for k in range(20) if scenario_of(k) in (1, 3, 4, 6)]
    variety2 = set(rng.sample(v2_pool, 8))                     # fewest roads costs more
    ml = list(range(20, 46))
    rng.shuffle(ml)
    safety_bin = {k: ("low" if i < 7 else "mid" if i < 18 else "high") for i, k in enumerate(ml)}
    return variety1, variety2, safety_bin


def build_case(seed, k, plan, used_serials):
    variety1, variety2, safety_bin = plan
    tier, study = tier_of(k), scenario_of(k)
    size_tier = "L" if tier == "X" else tier
    R = ranges_for(k, tier)
    sizes = make_rng(seed, k, "sizes")
    n = {key: sizes.randint(*R[key]) for key in sorted(R)}

    case = {}
    # crates + capacity
    if k == 46:
        case["crates"], case["capacity"] = trap46_crates(make_rng(seed, k, "crates"), n["crates"], used_serials)
    elif k == 47:
        case["crates"], case["capacity"] = trap47_crates(make_rng(seed, k, "crates"), used_serials)
    else:
        def make_crates(rng):
            crates = gen_crates(rng, n["crates"], study, used_serials)
            cap = choose_capacity(rng, crates, tier)
            if k in variety1 and not greedy_is_suboptimal(crates, cap):
                return None
            return crates, cap
        case["crates"], case["capacity"] = retry(seed, k, "crates", make_crates)
    used_serials.update(c["serial"] for c in case["crates"])

    # network
    if k == 48:
        net = trap48_network(make_rng(seed, k, "network"))
    else:
        net = retry(seed, k, "network",
                    lambda rng: gen_network(rng, n["locations"], study, need_variety2=k in variety2))
    case.update(locations=net["locations"], roads=net["roads"], waves=net["waves"])
    case["targets"] = net["targets"]

    # radio
    if k == 49:
        log, patterns = trap49_log(make_rng(seed, k, "radio"), n["log"])
    else:
        rng = make_rng(seed, k, "radio")
        log = gen_log(rng, n["log"], study)
        patterns = gen_patterns(rng, log)
    case["radio_log"] = split_log(log)
    case["radio_patterns"] = patterns
    report, case["edit_bound"] = gen_reports(make_rng(seed, k, "reports"), *R["report"])
    case["radio_reports"] = [report]

    # windows, incidents
    case["windows"] = retry(seed, k, "windows", lambda rng: gen_windows(rng, n["windows"], study, size_tier))
    case["incidents"] = retry(seed, k, "incidents", lambda rng: gen_incidents(rng, n["alarms"], study, tier))

    # sites + planted tour
    case["sites"], case["tour"], case["tour_length"] = retry(
        seed, k, "tour", lambda rng: gen_tour(rng, n["sites"], size_tier))

    # pipeline
    case["pipeline_dims"] = gen_dims(make_rng(seed, k, "dims"), n["stages"])
    case["drum_prices"] = retry(seed, k, "drum", lambda rng: gen_drum(rng, n["drum"], size_tier))

    # sensors, safety, rations
    case["sensor_nodes"] = n["sensors"]
    case["sensor_edges"], case["sensor_cover"], case["sensor_k"] = gen_sensors(make_rng(seed, k, "sensors"), n["sensors"])
    case["safety_vars"] = n["safety_vars"]
    case["safety_rules"], case["safety_planted"] = retry(
        seed, k, "safety", lambda rng: gen_safety(rng, n["safety_vars"], safety_bin.get(k)))
    case["rations"], case["rations_target"] = gen_rations(make_rng(seed, k, "rations"), n["rations"])

    case["claims"] = [compute_claims(case)] if tier == "S" else []
    case["meta"] = dict(case_id=f"{seed}-{k:02d}", group_seed=seed, case_no=k, tier=tier, scenario=study)
    return case


def to_sheet_rows(case):
    m = case["meta"]
    cid = m["case_id"]
    t0, t1, t2 = case["targets"]
    rows = {"cases": [dict(m, capacity=case["capacity"], target_0=t0, target_1=t1, target_2=t2,
                           edit_bound=case["edit_bound"], tour_length=case["tour_length"],
                           sensor_nodes=case["sensor_nodes"], sensor_k=case["sensor_k"],
                           safety_vars=case["safety_vars"], rations_target=case["rations_target"])]}
    for sheet in HEADERS:
        if sheet != "cases":
            rows[sheet] = [dict(r, case_id=cid) for r in case[sheet]]
    return rows


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--seed", type=int, default=18, help="group seed = group number (default 18)")
    ap.add_argument("--out", default="cases.xlsx")
    args = ap.parse_args()

    plan = plan_variety(args.seed)
    used_serials = set()
    sheet_rows = {name: [] for name in HEADERS}
    start = time.time()
    for k in range(N_CASES):
        t = time.time()
        case = build_case(args.seed, k, plan, used_serials)
        for name, rows in to_sheet_rows(case).items():
            sheet_rows[name].extend(rows)
        print(f"  case {case['meta']['case_id']}  tier {case['meta']['tier']}  "
              f"study {case['meta']['scenario']}  ({time.time() - t:.1f}s)", flush=True)
    digest = write_workbook(args.out, sheet_rows)
    print(f"wrote {args.out}  ({time.time() - start:.0f}s)")
    print(f"content SHA-256: {digest}")


if __name__ == "__main__":
    main()
