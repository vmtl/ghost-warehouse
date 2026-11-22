"""Integration tests: run python -m unittest discover -s tests"""
import csv
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from run_fulfillment import load, simulate
from pick_paths import read_locations

class FulfillmentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.orders = load("orders.csv")
        cls.lines = load("order_lines.csv")
        cls.stock = load("initial_inventory.csv")
        cls.employees = load("employees.csv")
        cls.locations = read_locations()

    def test_pilot_reconciles_and_routes(self):
        r = simulate(self.orders, self.lines, self.stock, self.employees, self.locations)
        k = r["fulfillment_kpis.csv"][0]
        self.assertEqual((k["orders"], k["shipped_orders"], k["shipped_units"]), (25, 25, 50))
        self.assertEqual((k["opening_units"], k["ending_units"]), (19870, 19820))
        self.assertGreater(k["total_route_ft"], 0)
        self.assertEqual(len(r["fulfillment_events.csv"]), 100)
        self.assertEqual(len(r["fulfillment_pick_tasks.csv"]), 25)

    def test_repeatable(self):
        args = (self.orders, self.lines, self.stock, self.employees, self.locations)
        self.assertEqual(simulate(*args), simulate(*args))

    def test_backorder_never_consumes_partial_stock(self):
        line = dict(self.lines[0], quantity_ordered="999999")
        order = self.orders[0]
        r = simulate([order], [line], self.stock, self.employees, self.locations)
        self.assertEqual(r["fulfillment_order_status.csv"][0]["status"], "BACKORDER")
        self.assertEqual(len(r["fulfillment_movements.csv"]), 0)
        self.assertEqual(r["fulfillment_kpis.csv"][0]["opening_units"], r["fulfillment_kpis.csv"][0]["ending_units"])

if __name__ == "__main__":
    unittest.main()
