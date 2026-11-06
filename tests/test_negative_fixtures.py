"""Regression suite for every valid and deliberately broken single-case fixture.

The expected validator code is taken from expected.txt, not from the workbook
filename or the actual validator output.
"""
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "validator" / "tests"
sys.path.insert(0, str(ROOT / "validator"))
from validate import passed, run  # noqa: E402


def expectations():
    entries = []
    for line in (FIXTURES / "expected.txt").read_text(encoding="utf-8").splitlines():
        if not line.strip() or line.startswith("#"):
            continue
        filename, code, explanation = line.split(" | ", 2)
        entries.append((filename, code, explanation))
    return entries


class NegativeFixtureTests(unittest.TestCase):
    def test_fixture_catalog_and_expected_codes(self):
        items = expectations()
        valid = [r for r in items if r[1] == "PASS"]
        broken = [r for r in items if r[1] != "PASS"]
        self.assertEqual(len(valid), 3)
        self.assertEqual(len(broken), 25)
        self.assertEqual({code for _, code, _ in broken},
                         {f"V{i}" for i in range(1, 9)})
        self.assertEqual(len({r[0] for r in items}), len(items))
        self.assertEqual({name for name, _, _ in items},
                         {p.name for p in FIXTURES.glob("*.xlsx")})

    def test_each_fixture_matches_its_expected_result(self):
        for filename, code, description in expectations():
            with self.subTest(file=filename, expected=code):
                result = run(str(FIXTURES / filename), partial=True)
                errors = result["book"] + [e for es in result["cases"].values() for e in es]
                failed_codes = {check for check, _ in errors}
                if code == "PASS":
                    self.assertTrue(passed(result), f"{filename}: {errors[:3]}")
                else:
                    self.assertFalse(passed(result), f"{filename}: validator accepted broken copy")
                    self.assertIn(code, failed_codes,
                                  f"{filename}: expected {code}, got {sorted(failed_codes)}")


if __name__ == "__main__":
    unittest.main()
