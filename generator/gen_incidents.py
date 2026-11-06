"""incidents sheet (alarm stream).

alarm_id 1.., tick starts at 0 and never decreases, priority 1..10.
Tiers M, L (and X, which uses tier L ranges): alarms per tick = n / (last tick + 1)
in 1.2..1.8 and at least 6 distinct priorities including 1.
  study 2 Mountain Earthquake "Bursts of urgent calls follow each aftershock":
          ticks clustered after aftershock times, priorities skewed high (mean >= 6.0).
  study 4 Urban Flash Flood "Calls arrive faster than anyone can answer them":
          rate 1.5..1.8 on tiers M and L.
"""

HIGH_WEIGHTS = [1, 1, 1, 2, 2, 3, 4, 5, 5, 4]        # for priorities 1..10, mean ~7


def _tick_count(rng, n, tier, study):
    if tier == "S":
        return max(2, round(n / rng.uniform(0.8, 2.0)))
    lo, hi = (15, 18) if study == 4 else (12, 18)     # rate in tenths
    T = round(10 * n / rng.uniform(lo + 0.5, hi - 0.5))
    while 10 * n > hi * T:
        T += 1
    while 10 * n < lo * T:
        T -= 1
    return T


def gen_incidents(rng, n, study, tier):
    T = _tick_count(rng, n, tier, study)
    last = T - 1
    if study == 2:
        shocks = sorted(rng.randint(0, last) for _ in range(max(1, n // 25)))
        ticks = [min(last, rng.choice(shocks) + rng.randint(0, 3)) for _ in range(n - 2)]
        prios = rng.choices(range(1, 11), weights=HIGH_WEIGHTS, k=n)
    else:
        ticks = [rng.randint(0, last) for _ in range(n - 2)]
        prios = [rng.randint(1, 10) for _ in range(n)]
    ticks = sorted(ticks + [0, last])

    if tier != "S":
        if 1 not in prios:
            prios[rng.randrange(n)] = 1
        missing = [p for p in range(2, 11) if p not in prios]
        while len(set(prios)) < 6 and missing:
            prios[rng.randrange(n)] = missing.pop()
        if len(set(prios)) < 6 or 1 not in prios:
            return None
    if study == 2 and sum(prios) < 6 * n:
        return None
    return [dict(alarm_id=i + 1, tick=ticks[i], priority=prios[i]) for i in range(n)]
