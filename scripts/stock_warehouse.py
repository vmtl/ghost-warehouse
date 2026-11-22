"""Generate deterministic opening stock from the committed catalog and location master.
No database needed. Run: python scripts/stock_warehouse.py
All packaging and quantities are synthetic. One SKU per occupied location.
"""
import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STAMP = "2026-11-22T00:00:00Z"

def read(name):
    with (ROOT / "data" / name).open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))

def classify(name):
    n = name.lower()
    if any(x in n for x in ("cat-back", "downpipe", "axle shaft", "front splitter", "rear diffuser", "trunk spoiler", "driveshaft", "coilover")):
        return ("FLOOR_BAY", 180, 65, 45)
    if any(x in n for x in ("big brake kit", "rotor pair", "radiator", "oil cooler", "clutch kit")):
        return ("PALLET_RACK", 95, 65, 45)
    if any(x in n for x in ("sensor", "spark plug", "gasket", "filter", "cable", "switch", "belt", "mount set", "bushing", "exhaust valve actuator")):
        return ("PARTS_DRAWER", 24, 16, 12)
    return ("SHELVING", 55, 40, 32)

def build():
    products, locations = read("products.csv"), read("locations.csv")
    assert len(products) == 2500 and len(locations) == 8000
    pools = {}
    for loc in locations:
        pools.setdefault(loc["storage_type"], []).append(loc)
    used = set()
    packaging, inventory = [], []
    for i, product in enumerate(products):
        sku = product["sku"]
        storage_type, length, width, height = classify(product["product_name"])
        fallbacks = {"PARTS_DRAWER": ["SHELVING"], "SHELVING": ["PALLET_RACK"], "PALLET_RACK": ["FLOOR_BAY"]}
        chosen = None
        for kind in [storage_type] + fallbacks.get(storage_type, []):
            chosen = next((loc for loc in pools.get(kind, [])
                if loc["location_code"] not in used
                and length <= float(loc["length_cm"])
                and width <= float(loc["width_cm"])
                and height <= float(loc["height_cm"])
                and float(product["weight_kg"]) <= float(loc["max_weight_kg"])), None)
            if chosen:
                break
        if chosen is None:
            raise ValueError(f"No fitting slot for {sku}")
        used.add(chosen["location_code"])
        kind = chosen["storage_type"]
        quantity = min(int(chosen["capacity_units"]),
            8 + i % 24 if kind == "PARTS_DRAWER" else 2 + i % 7 if kind == "SHELVING" else 1)
        reorder = max(1, (quantity * 35 + 99) // 100)
        packaging.append([sku, length, width, height, storage_type, "SYNTHETIC_ESTIMATE"])
        inventory.append([f"OPEN-{i+1:05d}", sku, chosen["location_code"], quantity, reorder,
                          f"{quantity * float(product['unit_cost_usd']):.2f}", STAMP, "INITIAL_RECEIPT"])
    assert len(used) == len(inventory) == len(packaging) == 2500
    return packaging, inventory

def write(name, header, rows):
    with (ROOT / "data" / name).open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, lineterminator="\n")
        writer.writerow(header)
        writer.writerows(rows)

def main():
    packaging, inventory = build()
    write("product_packaging.csv",
        ["sku", "package_length_cm", "package_width_cm", "package_height_cm", "preferred_storage_type", "dimension_source"], packaging)
    write("initial_inventory.csv",
        ["receipt_id", "sku", "location_code", "quantity", "reorder_point", "extended_cost_usd", "occurred_at", "movement_type"], inventory)
    print(f"Stocked {len(inventory)} SKUs in {len(inventory)} unique slots; {8000-len(inventory)} slots remain open.")

if __name__ == "__main__":
    main()
