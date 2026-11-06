"""safety_rules (3-literal rules = 3-SAT clauses) and safety_planted.

Correct by construction: draw the planted ON/OFF assignment FIRST. Each rule uses three
different switches with random signs; if the planted assignment satisfies none of its three
conditions, one literal's sign is flipped, which makes that condition true.
Rules / switches is set per case:
  tier S and X : 2.2 .. 5.8
  tiers M and L: a planned bin (variety rule 3): low 2.6..3.3, mid 3.7..4.6, high 5.0..5.8
"""
BIN_RATIO = {"low": (2.6, 3.3), "mid": (3.7, 4.6), "high": (5.0, 5.8), None: (2.2, 5.8)}


def ratio_in_bin(rules, n, bin_name):
    if not (2 * n <= rules <= 6 * n):
        return False
    if bin_name is None:
        return True
    if 2 * rules < 5 * n:                       # M/L must be >= 2.5
        return False
    if bin_name == "low":
        return 2 * rules < 7 * n                # < 3.5
    if bin_name == "mid":
        return 7 * n <= 2 * rules and 5 * rules <= 24 * n   # 3.5 .. 4.8
    return 5 * rules > 24 * n                   # > 4.8


def gen_safety(rng, n, bin_name):
    lo, hi = BIN_RATIO[bin_name]
    m = round(rng.uniform(lo, hi) * n)
    if not ratio_in_bin(m, n, bin_name):
        return None
    planted = [None] + [rng.randint(0, 1) for _ in range(n)]     # 1-based switches
    rules, seen = [], set()
    while len(rules) < m:
        switches = rng.sample(range(1, n + 1), 3)
        lits = [s if rng.random() < 0.5 else -s for s in switches]
        if not any((l > 0) == (planted[abs(l)] == 1) for l in lits):
            i = rng.randrange(3)
            lits[i] = -lits[i]
        key = tuple(sorted(lits))
        if key in seen:
            continue
        seen.add(key)
        rules.append(lits)
    rule_rows = [dict(rule_no=i + 1, lit_1=a, lit_2=b, lit_3=c) for i, (a, b, c) in enumerate(rules)]
    planted_rows = [dict(switch=s, value=planted[s]) for s in range(1, n + 1)]
    return rule_rows, planted_rows
