"""Builds the validator test workbooks in validator/tests/ from cases.xlsx.

For each chosen valid case (18-03 tier S, 18-25 tier M, 18-47 trap) it writes
  valid_<case>.xlsx                 the case on its own (must PASS)
  broken_<case>_<n>_<what>.xlsx     the case with exactly one deliberate defect
and expected.txt, which lists the check each broken copy must fail.

    python validator/tests/make_broken.py cases.xlsx
"""
import argparse
import copy
import os

from openpyxl import Workbook, load_workbook

HERE = os.path.dirname(os.path.abspath(__file__))


def read_book(path):
    wb = load_workbook(path, read_only=True)
    data = {}
    for name in wb.sheetnames:
        rows = list(wb[name].iter_rows(values_only=True))
        data[name] = (list(rows[0]), [list(r) for r in rows[1:]])
    wb.close()
    return data


def only_case(data, cid):
    return {name: (header, [r for r in rows if r[0] == cid]) for name, (header, rows) in data.items()}


def write_book(path, data, rename=None):
    wb = Workbook(write_only=True)
    for name, (header, rows) in data.items():
        ws = wb.create_sheet(title=name)
        ws.append(rename(name, header) if rename else header)
        for r in sorted(rows, key=lambda r: tuple(r)):
            ws.append(r)
    wb.save(path)


def col(data, sheet, name):
    return data[sheet][0].index(name)


# ------------------------------------------------------------ the deliberate defects
# Each returns (description, expected check, mutated data, header-rename function or None).

def m_header(d):
    def rename(sheet, header):
        return [("wt" if (sheet == "crates" and h == "weight") else h) for h in header]
    return "crates header 'weight' renamed to 'wt'", "V1", d, rename


def m_weight(d):
    d["crates"][1][0][col(d, "crates", "weight")] = 25
    return "crate 1 weight set to 25 kg (range 1..20)", "V2", d, None


def m_duplicate_id(d):
    d["crates"][1][1][col(d, "crates", "crate_id")] = d["crates"][1][0][col(d, "crates", "crate_id")]
    return "two crates share the same crate_id", "V3", d, None


def m_bad_road_end(d):
    V = len(d["locations"][1])
    d["roads"][1][0][col(d, "roads", "v")] = V + 5
    return f"road 0 ends at location {V + 5}, which does not exist", "V3", d, None


def m_wave_overlap(d):
    waves = d["waves"][1]
    wn, rn = col(d, "waves", "wave_no"), col(d, "waves", "road_no")
    first = [r for r in waves if r[wn] == 0][0]
    waves.append([first[0], 1, first[rn]])
    return f"road {first[rn]} closed in wave 0 and again in wave 1", "V4", d, None


def m_disconnect(d):
    roads = d["roads"][1]
    u, v = col(d, "roads", "u"), col(d, "roads", "v")
    victim = roads[0][v]                         # v > u >= 0, so never the HQ
    keep = [r for r in roads if victim not in (r[u], r[v])]
    removed = len(roads) - len(keep)
    d["roads"] = (d["roads"][0], keep)
    rn = col(d, "roads", "road_no")
    for i, r in enumerate(sorted(keep, key=lambda r: r[rn])):
        r[rn] = i
    wv = col(d, "waves", "road_no")
    d["waves"] = (d["waves"][0], [w for w in d["waves"][1] if w[wv] < len(keep)])
    return f"every road of location {victim} removed ({removed} road(s)), cutting it off", "V4", d, None


def m_pattern_count(d):
    d["radio_patterns"][1][0][col(d, "radio_patterns", "count")] += 1
    return "pattern 0 count increased by 1", "V5", d, None


def m_edit_bound(d):
    d["cases"][1][0][col(d, "cases", "edit_bound")] = 0
    return "edit_bound set to 0 (below the true edit distance)", "V5", d, None


def m_claim(d):
    d["claims"][1][0][col(d, "claims", "cargo_opt")] += 1
    return "claim cargo_opt increased by 1", "V5", d, None


def m_planted_switch(d):
    rules = d["safety_rules"][1]
    planted = d["safety_planted"][1]
    sw, val = col(d, "safety_planted", "switch"), col(d, "safety_planted", "value")
    value = {r[sw]: r[val] for r in planted}
    lits = [col(d, "safety_rules", f"lit_{i}") for i in (1, 2, 3)]

    def broken_after_flip(s):
        flipped = dict(value)
        flipped[s] = 1 - flipped[s]
        return any(not any(flipped[abs(r[i])] == (1 if r[i] > 0 else 0) for i in lits) for r in rules)

    s = next(s for s in sorted(value) if broken_after_flip(s))
    for r in planted:
        if r[sw] == s:
            r[val] = 1 - r[val]
    return f"planted switch {s} flipped, so a safety rule is violated", "V6", d, None


def m_tour_length(d):
    d["cases"][1][0][col(d, "cases", "tour_length")] += 7
    return "tour_length increased by 7", "V6", d, None


def m_rations(d):
    d["cases"][1][0][col(d, "cases", "rations_target")] += 1
    return "rations_target increased by 1 (planted selection no longer sums to it)", "V6", d, None


def m_signature_cats(study_cats, label):
    def mutate(d):
        cat = col(d, "crates", "cat")
        for r in d["crates"][1]:
            if r[cat] in study_cats:
                r[cat] = 0 if 0 not in study_cats else 3
        return f"all {label} crates relabelled (signature rule broken)", "V7", d, None
    return mutate


def m_trap47(d):
    w, v = col(d, "crates", "weight"), col(d, "crates", "value")
    decoy = next(r for r in d["crates"][1] if r[w] == 1)
    decoy[w] = 20
    return "decoy crate made 20 kg, so greedy-by-ratio becomes optimal", "V8", d, None


PLAN = {
    "18-03": [m_header, m_weight, m_duplicate_id, m_bad_road_end, m_wave_overlap,
              m_pattern_count, m_claim, m_planted_switch, m_signature_cats({4}, "rare (cat 4)")],
    "18-25": [m_header, m_weight, m_duplicate_id, m_disconnect, m_wave_overlap, m_edit_bound,
              m_tour_length, m_rations, m_signature_cats({2, 3}, "medicine/tool (cat 2, 3)")],
    "18-47": [m_header, m_weight, m_duplicate_id, m_bad_road_end,
              m_pattern_count, m_tour_length, m_trap47],
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("workbook", nargs="?", default="cases.xlsx")
    args = ap.parse_args()
    data = read_book(args.workbook)
    for old in os.listdir(HERE):
        if old.endswith(".xlsx"):
            os.remove(os.path.join(HERE, old))
    expected = []
    for cid, mutations in PLAN.items():
        base = only_case(data, cid)
        name = f"valid_{cid}.xlsx"
        write_book(os.path.join(HERE, name), base)
        expected.append((name, "PASS", f"case {cid} unchanged"))
        for i, mutate in enumerate(mutations, 1):
            desc, check, mutated, rename = mutate(copy.deepcopy(base))
            name = f"broken_{cid}_{i}_{check}.xlsx"
            write_book(os.path.join(HERE, name), mutated, rename)
            expected.append((name, check, desc))
    with open(os.path.join(HERE, "expected.txt"), "w") as f:
        f.write("# file | expected result | defect\n")
        for name, check, desc in expected:
            f.write(f"{name} | {check} | {desc}\n")
    print(f"wrote {len(expected)} test workbooks to {HERE}")


if __name__ == "__main__":
    main()
