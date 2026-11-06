"""radio_log, radio_patterns, radio_reports.

The log is built from short radio messages (WORD-NUMBER_) with per-symbol noise.
  study 3 Coastal Cyclone "The radio is full of noise": 30% noise, and every one of the
          38 symbols is written at least once, so >= 30 distinct symbols holds by construction.
  study 6 Outbreak Camp "Radio beacons repeat the same messages": 3 beacon messages
          padded with '_' and topped up until '_' is >= 30% of the log.
Patterns: lengths 2,4,8,12,20,40. 1 or 2 of the long ones (length >= 8) are random strings
checked to be absent; the others are cut out of the log, so they occur.
Reports: report_b = report_a with random insertions/deletions/replacements;
edit_bound = the exact edit distance (dynamic programming).
"""
from common import count_overlapping, edit_distance
from spec import ALPHABET, PATTERN_LENGTHS, CELL_LIMIT

WORDS = ["SOS", "WATER", "FOOD", "MEDIC", "HELP", "ROAD", "BLOCKED", "CLEAR", "SECTOR",
         "BRIDGE", "SHELTER", "FLOOD", "TRUCK", "DEPOT", "OK", "NEED", "ASAP", "CAMP",
         "BEACON", "STATUS", "TEAM", "ALPHA", "BRAVO", "DELTA", "ECHO", "QUAKE", "SURGE",
         "RESCUE", "FUEL", "DOCTOR", "PUMP", "BOAT", "RADIO", "ZONE", "KIT", "VAX"]


def _message(rng):
    return f"{rng.choice(WORDS)}-{rng.randint(0, 999)}_"


def gen_log(rng, N, study):
    noise = 0.30 if study == 3 else 0.04
    beacons = [_message(rng) + rng.choice(WORDS) + "_" for _ in range(3)]
    chars = []
    while len(chars) < N:
        if study == 6:
            msg = rng.choice(beacons) if rng.random() < 0.8 else _message(rng)
            msg += "_" * rng.randint(4, 8)
        else:
            msg = _message(rng)
        for ch in msg:
            chars.append(rng.choice(ALPHABET) if rng.random() < noise else ch)
    chars = chars[:N]
    if study == 3:
        for ch, p in zip(ALPHABET, rng.sample(range(N), len(ALPHABET))):
            chars[p] = ch
    if study == 6:
        need = (3 * N + 9) // 10                  # '_' at least 30%
        others = [i for i, ch in enumerate(chars) if ch != "_"]
        rng.shuffle(others)
        have = N - len(others)
        for i in others[:max(0, need - have)]:
            chars[i] = "_"
    return "".join(chars)


def split_log(log, chunk=CELL_LIMIT):
    return [dict(part=i + 1, text=log[s:s + chunk]) for i, s in enumerate(range(0, len(log), chunk))]


def gen_patterns(rng, log):
    N = len(log)
    absent = set(rng.sample([2, 3, 4, 5], rng.randint(1, 2)))
    rows = []
    for no, L in enumerate(PATTERN_LENGTHS):
        if no in absent:
            while True:
                p = "".join(rng.choice(ALPHABET) for _ in range(L))
                if p not in log:
                    break
        else:
            s = rng.randrange(N - L + 1)
            p = log[s:s + L]
        rows.append(dict(pattern_no=no, pattern=p, count=count_overlapping(log, p)))
    return rows


def gen_reports(rng, lo, hi):
    while True:
        la = rng.randint(lo, hi)
        text = []
        while len(text) < la:
            text.extend(_message(rng))
        a = "".join(text[:la])
        b = list(a)
        for _ in range(rng.randint(max(1, la // 10), max(2, la // 4))):
            op = rng.randrange(3)
            if op == 0:
                b.insert(rng.randint(0, len(b)), rng.choice(ALPHABET))
            elif op == 1 and len(b) > 1:
                del b[rng.randrange(len(b))]
            else:
                b[rng.randrange(len(b))] = rng.choice(ALPHABET)
        b = "".join(b)
        if lo <= len(b) <= hi and a != b:
            return dict(report_a=a, report_b=b), edit_distance(a, b)
