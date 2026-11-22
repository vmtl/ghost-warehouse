"""Tests for reproducible location layout. Run: python -m unittest discover -s tests"""
import csv
import sys
import unittest
from collections import Counter
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from generate_locations import generate, HEADERS

class LocationTests(unittest.TestCase):
    def test_generated_count_and_unique_addresses(self):
        rows = generate()
        self.assertEqual(len(rows), 8000)
        self.assertEqual(len({r[0] for r in rows}), 8000)
        self.assertEqual(dict(Counter(r[1] for r in rows)), {"BLK": 1400, "SML": 4000, "MED": 1600, "HVY": 600, "SEC": 400})

    def test_capacity_and_security(self):
        for row in generate():
            self.assertGreater(row[7], 0)
            self.assertGreater(row[8], 0)
            self.assertGreater(float(row[12]), 0)
            self.assertEqual(row[15] == "true", row[1] == "SEC")

    def test_committed_csv_matches_generator(self):
        with (ROOT / "data" / "locations.csv").open(newline="", encoding="utf-8") as f:
            reader = csv.reader(f)
            self.assertEqual(next(reader), HEADERS)
            self.assertEqual(list(reader), [[str(value) for value in row] for row in generate()])

if __name__ == "__main__":
    unittest.main()
