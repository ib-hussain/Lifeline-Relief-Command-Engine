"""rations sheet (subset sum with a planted selection).

Correct by construction: pick a non-empty planted subset FIRST; rations_target is its sum.
"""


def gen_rations(rng, n):
    values = [rng.randint(1, 1000) for _ in range(n)]
    size = rng.randint(2, max(2, n // 3))
    planted = set(rng.sample(range(n), size))
    target = sum(values[i] for i in planted)
    rows = [dict(item=i, value=values[i], planted=1 if i in planted else 0) for i in range(n)]
    return rows, target
