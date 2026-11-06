"""crates sheet + truck capacity (cases sheet).

Story -> numbers:
  study 1 Delta Flood       "Food and water matter most"           -> >= 60% cat 0/1
  study 2 Mountain Earthq.  "The injured need medicine and tools"  -> >= 52% cat 2/3
  study 4 Urban Flash Flood "Rare equipment is available"          -> >= 15% cat 4
  study 6 Outbreak Camp     "Medicine and water count, supplies spoil"
                                                                    -> >= 62% cat 1/2, 60% expire by hour 300
Quotas are set a little above the signature thresholds so they hold with margin.
Value grows with weight and category (medicine and rare items are worth more per kg),
with noise, so the value-per-kg order is not trivial.
"""
from common import ceil_div, greedy_ratio_value, knapsack_value
from spec import CAT_FOOD, CAT_WATER, CAT_MEDICINE, CAT_TOOL, CAT_RARE

CAT_MULT = {CAT_FOOD: 1.0, CAT_WATER: 0.9, CAT_MEDICINE: 1.6, CAT_TOOL: 1.2, CAT_RARE: 2.0}

CAPACITY_PCT = {"S": (30, 60), "M": (25, 50), "L": (12, 30), "X": (10, 15)}


def draw_serials(rng, n, used):
    """n distinct 8-digit serials, also distinct from every serial already used in the workbook."""
    chosen = set()
    while len(chosen) < n:
        x = rng.randint(10_000_000, 99_999_999)
        if x not in used:
            chosen.add(x)
    out = sorted(chosen)
    rng.shuffle(out)
    return out


def _categories(rng, n, study):
    cats = [rng.randrange(5) for _ in range(n)]

    def force(count, allowed):
        for i in rng.sample(range(n), count):
            cats[i] = rng.choice(allowed)

    if study == 1:
        force(ceil_div(60 * n, 100), (CAT_FOOD, CAT_WATER))
    elif study == 2:
        force(ceil_div(52 * n, 100), (CAT_MEDICINE, CAT_TOOL))
    elif study == 4:
        force(ceil_div(15 * n, 100), (CAT_RARE,))
    elif study == 6:
        force(ceil_div(62 * n, 100), (CAT_WATER, CAT_MEDICINE))
    return cats


def gen_crates(rng, n, study, used_serials):
    cats = _categories(rng, n, study)
    perishable = set(rng.sample(range(n), ceil_div(60 * n, 100))) if study == 6 else set()
    serials = draw_serials(rng, n, used_serials)
    crates = []
    for i in range(n):
        w = rng.randint(1, 20)
        v = round(w * 3.5 * CAT_MULT[cats[i]] * rng.uniform(0.5, 1.5)) + rng.randint(0, 12)
        v = min(100, max(10, v))
        expiry = rng.randint(0, 300) if i in perishable else rng.randint(0, 999)
        crates.append(dict(crate_id=i + 1, cat=cats[i], weight=w, value=v,
                           expiry=expiry, serial=serials[i]))
    return crates


def choose_capacity(rng, crates, tier):
    """10% to 70% of the total weight, at least 1 (checked with integers)."""
    total = sum(c["weight"] for c in crates)
    lo, hi = CAPACITY_PCT[tier]
    cap = total * rng.randint(lo, hi) // 100
    cap = max(cap, ceil_div(total, 10), 1)
    cap = min(cap, total * 7 // 10)
    return cap


def greedy_is_suboptimal(crates, capacity):
    return greedy_ratio_value(crates, capacity) < knapsack_value(crates, capacity)
