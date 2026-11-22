"""Generate deterministic fictional customers and 25 pilot orders.

Run: python scripts/generate_orders.py
Requires existing data/products.csv and data/initial_inventory.csv.
No database, network connection, or external packages.
"""
import csv
from collections import Counter
from datetime import datetime, timedelta, timezone
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "data"
START = datetime(2026, 11, 23, 9, 0, tzinfo=timezone.utc)


def read(name):
    with (ROOT / name).open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def write(name, columns, rows):
    with (ROOT / name).open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=columns, lineterminator="\\n")
        writer.writeheader()
        writer.writerows(rows)


def generate():
    customers = []
    for i in range(1, 61):
        wholesale = i <= 20
        customers.append(dict(
            customer_id=f"CUS-{i:03d}",
            customer_name=f"Performance Partner {i:02d}" if wholesale else f"Retail Customer {i-20:02d}",
            customer_type="WHOLESALE" if wholesale else "RETAIL",
            channel="B2B" if wholesale else "B2C",
            payment_terms="NET30" if wholesale else "PREPAID",
            status="ACTIVE", simulated="true"))
    write("customers.csv", list(customers[0]), customers)

    products = {r["sku"]: r for r in read("products.csv")}
    inventory = {r["sku"]: r for r in read("initial_inventory.csv")}
    assert len(products) == 2500 and len(inventory) == 2500
    orders, lines = [], []
    reserved = Counter()
    for i in range(1, 26):
        customer = customers[(i * 7) % len(customers)]
        order_id = f"ORD-{i:05d}"
        created = START + timedelta(minutes=17 * (i - 1))
        orders.append(dict(order_id=order_id, customer_id=customer["customer_id"],
                           order_placed_at=created.isoformat(), channel=customer["channel"],
                           order_status="NEW", currency="USD", simulated="true"))
        for j in range(1, 3):
            # Deterministic distinct SKUs; inventory demand never exceeds opening stock.
            number = ((i * 97 + j * 31) % 2500) + 1
            sku = f"GH-{number:05d}"
            item = products[sku]
            assert sku in inventory
            qty = 1
            reserved[sku] += qty
            assert reserved[sku] <= int(inventory[sku]["quantity"]), sku
            unit_price = Decimal(item["retail_price_usd"])
            if customer["channel"] == "B2B":
                unit_price = (unit_price * Decimal("0.85")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            lines.append(dict(order_line_id=f"OL-{i:05d}-{j:02d}", order_id=order_id,
                              sku=sku, quantity_ordered=qty,
                              unit_price_usd=f"{unit_price:.2f}",
                              line_total_usd=f"{unit_price * qty:.2f}",
                              simulated="true"))
    write("orders.csv", list(orders[0]), orders)
    write("order_lines.csv", list(lines[0]), lines)
    assert len(orders) == 25 and len(lines) == 50
    assert len({o["order_id"] for o in orders}) == 25
    assert {r["order_id"] for r in lines} == {r["order_id"] for r in orders}
    print("Generated 60 customers, 25 pilot orders and 50 order lines; opening stock checks passed.")


if __name__ == "__main__":
    generate()
