"""windows sheet (rescue windows).

0 <= start < finish <= 1440, duration 5..480, value 1..100.
At least two touching pairs are planted (window j starts exactly when window i finishes).
study 3 Coastal Cyclone "Rescue windows are short and overlap": durations 5..60 packed
around 1-3 storm peaks; accepted only if the average number of overlaps per window is >= 2.
Overlap means a strict intersection (touching windows are compatible, so they do not overlap).
"""
from bisect import bisect_left

from spec import DAY_MINUTES


def overlap_pairs(windows):
    """Number of pairs with a strict intersection, O(n log n)."""
    iv = sorted((w["start"], w["finish"]) for w in windows)
    starts = [s for s, _ in iv]
    total = 0
    for i, (s, f) in enumerate(iv):
        total += bisect_left(starts, f) - (i + 1)
    return total


def touching_pairs(windows):
    starts = {}
    for w in windows:
        starts[w["start"]] = starts.get(w["start"], 0) + 1
    return sum(starts.get(w["finish"], 0) for w in windows)


def gen_windows(rng, n, study, tier):
    spans = []
    if study == 3:
        peaks = [rng.randint(60, DAY_MINUTES - 60) for _ in range(rng.randint(1, 3))]
        for _ in range(n):
            d = rng.randint(5, 60)
            s = rng.choice(peaks) + rng.randint(-60, 60)
            s = min(max(0, s), DAY_MINUTES - d)
            spans.append([s, s + d])
    else:
        max_d = 240 if tier == "S" else 480
        for _ in range(n):
            d = rng.randint(5, max_d)
            s = rng.randint(0, DAY_MINUTES - d)
            spans.append([s, s + d])

    k = rng.randint(2, 4)
    ids = rng.sample(range(n), 2 * k)
    for t in range(k):
        i, j = ids[2 * t], ids[2 * t + 1]
        if spans[i][1] > DAY_MINUTES - 5:                 # leave room for the follower
            shift = spans[i][1] - (DAY_MINUTES - 5)
            spans[i] = [spans[i][0] - shift, spans[i][1] - shift]
        d = min(spans[j][1] - spans[j][0], DAY_MINUTES - spans[i][1])
        spans[j] = [spans[i][1], spans[i][1] + d]

    windows = [dict(window_id=i + 1, start=s, finish=f, value=rng.randint(1, 100))
               for i, (s, f) in enumerate(spans)]
    if touching_pairs(windows) < 2:
        return None
    if study == 3 and overlap_pairs(windows) < n:       # average overlaps = 2*pairs/n >= 2
        return None
    return windows
