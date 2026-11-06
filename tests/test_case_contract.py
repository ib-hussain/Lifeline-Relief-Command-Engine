"""Independent, read-only checks for the released LIFELINE workbook.

Run: python -m unittest discover -s tests -p 'test_*.py' -v
This deliberately does not import the group's generator or validator.
"""
from collections import defaultdict, deque
from pathlib import Path
import unittest

from openpyxl import load_workbook

ROOT = Path(__file__).resolve().parents[1]
SHEETS = (
    "cases", "crates", "locations", "roads", "waves", "radio_log",
    "radio_patterns", "radio_reports", "windows", "incidents", "sites",
    "tour", "pipeline_dims", "drum_prices", "sensor_edges", "sensor_cover",
    "safety_rules", "safety_planted", "rations", "claims",
)


def records(sheet):
    iterator = sheet.iter_rows(values_only=True)
    header = next(iterator)
    return [dict(zip(header, row)) for row in iterator]


class CaseContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.workbook = load_workbook(ROOT / "cases.xlsx", read_only=True)
        cls.cases = records(cls.workbook["cases"])
        cls.crates = records(cls.workbook["crates"])
        cls.locations = records(cls.workbook["locations"])
        cls.roads = records(cls.workbook["roads"])

    @classmethod
    def tearDownClass(cls):
        cls.workbook.close()

    def test_exact_sheet_order_and_identifiers(self):
        self.assertEqual(tuple(self.workbook.sheetnames), SHEETS)
        self.assertEqual(len(self.cases), 50)
        self.assertEqual([r["case_id"] for r in self.cases],
                         [f"18-{k:02d}" for k in range(50)])
        for k, row in enumerate(self.cases):
            with self.subTest(case=k):
                self.assertEqual(row["group_seed"], 18)
                self.assertEqual(row["case_no"], k)
                self.assertEqual(row["scenario"], k % 6 + 1)
                self.assertEqual(row["tier"],
                                 "S" if k < 20 else "M" if k < 40 else
                                 "L" if k < 46 else "X")

    def test_all_modules_reference_existing_case_ids(self):
        valid = {r["case_id"] for r in self.cases}
        for name in SHEETS[1:]:
            with self.subTest(sheet=name):
                sheet = self.workbook[name]
                self.assertEqual(sheet.cell(1, 1).value, "case_id")
                seen = set()
                last_id = ""
                for (cid, *_) in sheet.iter_rows(min_row=2, values_only=True):
                    self.assertIn(cid, valid)
                    self.assertGreaterEqual(cid, last_id)
                    last_id = cid
                    seen.add(cid)
                # The claims sheet applies only to S-tier; all other sheets
                # must represent every case.
                self.assertEqual(seen, {f"18-{k:02d}" for k in range(20)}
                                 if name == "claims" else valid)

    def test_crates_capacity_and_unique_serials(self):
        grouped = defaultdict(list)
        serials = set()
        for crate in self.crates:
            with self.subTest(case=crate["case_id"], crate=crate["crate_id"]):
                self.assertIn(crate["cat"], range(5))
                self.assertTrue(1 <= crate["weight"] <= 20)
                self.assertTrue(10 <= crate["value"] <= 100)
                self.assertTrue(0 <= crate["expiry"] <= 999)
                serial = crate["serial"]
                self.assertTrue(10_000_000 <= serial <= 99_999_999)
                self.assertNotIn(serial, serials)
                serials.add(serial)
            grouped[crate["case_id"]].append(crate)
        for row in self.cases:
            cid = row["case_id"]
            total = sum(c["weight"] for c in grouped[cid])
            with self.subTest(case=cid):
                self.assertGreaterEqual(row["capacity"], 1)
                self.assertGreaterEqual(row["capacity"] * 10, total)
                self.assertLessEqual(row["capacity"] * 10, total * 7)
                self.assertEqual([c["crate_id"] for c in grouped[cid]],
                                 list(range(1, len(grouped[cid]) + 1)))

    def test_road_endpoints_and_original_network_connectivity(self):
        by_case = defaultdict(dict)
        for loc in self.locations:
            by_case[loc["case_id"]][loc["loc_id"]] = loc
        roads_by_case = defaultdict(list)
        for road in self.roads:
            roads_by_case[road["case_id"]].append(road)
        for case in self.cases:
            cid = case["case_id"]
            locations = by_case[cid]
            with self.subTest(case=cid):
                self.assertIn(0, locations)
                self.assertEqual(locations[0]["type"], "D")
                self.assertEqual(locations[0]["penalty"], 0)
                self.assertEqual(set(locations), set(range(len(locations))))
                neighbours = defaultdict(set)
                undirected = set()
                for road in roads_by_case[cid]:
                    u, v = road["u"], road["v"]
                    self.assertTrue(u < v)
                    self.assertIn(u, locations)
                    self.assertIn(v, locations)
                    self.assertNotIn((u, v), undirected)
                    undirected.add((u, v))
                    neighbours[u].add(v)
                    neighbours[v].add(u)
                visited = {0}
                queue = deque([0])
                while queue:
                    for neighbour in neighbours[queue.popleft()]:
                        if neighbour not in visited:
                            visited.add(neighbour)
                            queue.append(neighbour)
                self.assertEqual(len(visited), len(locations))
                for target in (case["target_0"], case["target_1"], case["target_2"]):
                    self.assertIn(target, locations)
                    self.assertIn(locations[target]["type"], ("S", "H"))
                self.assertEqual(len({case[k] for k in
                                      ("target_0", "target_1", "target_2")}), 3)


if __name__ == "__main__":
    unittest.main()
