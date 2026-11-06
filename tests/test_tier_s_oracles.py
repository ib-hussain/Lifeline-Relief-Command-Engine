"""Independent DP and exhaustive oracles for all six tier-S claims.

Neither generator claims.py nor validator algorithms are imported. These
algorithms are small-case reference checks, not proposed L-tier solvers.
"""
from bisect import bisect_right
from collections import defaultdict
from itertools import combinations
from pathlib import Path
import unittest

from openpyxl import load_workbook

ROOT = Path(__file__).resolve().parents[1]


def group_rows(book, sheet):
    rows = book[sheet].iter_rows(values_only=True)
    header = next(rows)
    result = defaultdict(list)
    for row in rows:
        item = dict(zip(header, row))
        result[item["case_id"]].append(item)
    return result


def cargo_opt(crates, capacity):
    best = [0] * (capacity + 1)
    for crate in crates:
        weight, value = crate["weight"], crate["value"]
        for w in range(capacity, weight - 1, -1):
            best[w] = max(best[w], best[w - weight] + value)
    return best[capacity]


def window_opts(windows):
    windows = sorted(windows, key=lambda r: (r["finish"], r["start"], r["window_id"]))
    ends = [r["finish"] for r in windows]
    count_dp, value_dp = [0], [0]
    for i, window in enumerate(windows):
        prior = bisect_right(ends, window["start"], hi=i)
        count_dp.append(max(count_dp[-1], 1 + count_dp[prior]))
        value_dp.append(max(value_dp[-1], window["value"] + value_dp[prior]))
    return count_dp[-1], value_dp[-1]


def drum_opt(prices):
    prices = {row["length"]: row["price"] for row in prices}
    limit = max(prices)
    dp = [0] * (limit + 1)
    for size in range(1, limit + 1):
        dp[size] = max(prices[cut] + dp[size - cut] for cut in range(1, size + 1))
    return dp[limit]


def tour_opt(sites):
    sites = sorted(sites, key=lambda r: r["site_no"])
    coords = [(s["x"], s["y"]) for s in sites]
    assert sites[0]["site_no"] == 0
    n = len(coords)
    d = [[abs(x1-x2)+abs(y1-y2) for x2,y2 in coords] for x1,y1 in coords]
    # Held-Karp DP; bit i represents site (i+1), depot 0 excluded.
    dp = {(1 << (j-1), j): d[0][j] for j in range(1, n)}
    for mask in range(1, 1 << (n-1)):
        for j in range(1, n):
            bit = 1 << (j-1)
            if not mask & bit or (mask, j) in dp:
                continue
            prior = mask ^ bit
            dp[(mask, j)] = min(dp[(prior, k)] + d[k][j]
                                for k in range(1, n) if prior & (1 << (k-1)))
    full = (1 << (n-1)) - 1
    return min(dp[(full, j)] + d[j][0] for j in range(1, n))


def cover_min(edges, n):
    links = [(r["u"], r["v"]) for r in edges]
    for k in range(n + 1):
        for combo in combinations(range(n), k):
            cover = set(combo)
            if all(u in cover or v in cover for u, v in links):
                return k
    raise AssertionError("finite graph must have a cover")


class TierSOracleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        wb = load_workbook(ROOT / "cases.xlsx", read_only=True)
        try:
            cls.cases = {row["case_id"]: row
                         for group in group_rows(wb, "cases").values() for row in group}
            cls.claims = {row["case_id"]: row
                          for group in group_rows(wb, "claims").values() for row in group}
            cls.crates = group_rows(wb, "crates")
            cls.windows = group_rows(wb, "windows")
            cls.drums = group_rows(wb, "drum_prices")
            cls.sites = group_rows(wb, "sites")
            cls.edges = group_rows(wb, "sensor_edges")
        finally:
            wb.close()

    def test_every_tier_s_claim(self):
        self.assertEqual(set(self.claims), {f"18-{i:02d}" for i in range(20)})
        for cid in sorted(self.claims):
            row = self.cases[cid]
            expected = self.claims[cid]
            n = row["sensor_nodes"]
            calculated = {
                "cargo_opt": cargo_opt(self.crates[cid], row["capacity"]),
                "drum_opt": drum_opt(self.drums[cid]),
                "tour_opt": tour_opt(self.sites[cid]),
                "cover_min": cover_min(self.edges[cid], n),
            }
            count, value = window_opts(self.windows[cid])
            calculated["window_count_opt"] = count
            calculated["window_value_opt"] = value
            for name, result in calculated.items():
                with self.subTest(case=cid, claim=name):
                    self.assertEqual(expected[name], result,
                                     f"{cid} {name}: stored {expected[name]} computed {result}")


if __name__ == "__main__":
    unittest.main()
