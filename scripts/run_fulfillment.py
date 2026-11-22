"""Reproducible pilot fulfillment runner. Python standard library only.

Run: python scripts/run_fulfillment.py
Writes data/fulfillment_* files without mutating opening inventory or source orders.
"""
import csv
import sys
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from pick_paths import build_network, read_locations, route

DATA = ROOT / "data"
BASE_TIME = datetime(2026, 11, 23, 10, tzinfo=timezone.utc)

def load(name):
    with (DATA / name).open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))

def write(name, rows, fields):
    with (DATA / name).open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)

def simulate(orders, lines, inventory, employees, locations):
    graph, coords, access = build_network(locations)
    picker_ids = [e["employee_id"] for e in employees if e["department"] == "Picking" and e["status"] == "ACTIVE"]
    if not picker_ids:
        raise ValueError("No active pickers")
    order_ids = [o["order_id"] for o in orders]
    if len(order_ids) != len(set(order_ids)):
        raise ValueError("Duplicate order ID")
    by_order = defaultdict(list)
    line_ids = set()
    for line in lines:
        if line["order_line_id"] in line_ids:
            raise ValueError("Duplicate order line ID")
        line_ids.add(line["order_line_id"])
        by_order[line["order_id"]].append(line)
    if set(by_order) != set(order_ids):
        raise ValueError("Order/line references do not match")
    stock = defaultdict(int)
    for row in inventory:
        stock[(row["sku"], row["location_code"])] += int(row["quantity"])
    original = stock.copy()
    sku_locations = defaultdict(list)
    for sku, loc in stock:
        sku_locations[sku].append(loc)
    for sku in sku_locations:
        sku_locations[sku].sort()
    allocation, tasks, events, movements, outcomes, kpis = [], [], [], [], [], []
    for i, order in enumerate(orders):
        oid = order["order_id"]
        tentative = []
        pending = stock.copy()
        complete = True
        for line in by_order[oid]:
            needed = int(line["quantity_ordered"])
            if needed <= 0:
                raise ValueError("Quantity must be positive")
            for loc in sku_locations.get(line["sku"], []):
                qty = min(needed, pending[(line["sku"], loc)])
                if qty:
                    tentative.append((line, loc, qty))
                    pending[(line["sku"], loc)] -= qty
                    needed -= qty
                if not needed:
                    break
            if needed:
                complete = False
                break
        if not complete:
            outcomes.append(dict(order_id=oid, status="BACKORDER", employee_id="", units_shipped=0, route_ft=0, cycle_minutes=0))
            continue
        stock = pending
        employee = picker_ids[len(tasks) % len(picker_ids)]
        pick_locs = [loc for _, loc, _ in tentative]
        trip = route(graph, coords, pick_locs, optimize=True)
        # Conceptual travel speed only; not a safety/handling-time validated estimate.
        travel_minutes = trip["distance_ft"] / 240
        pick_minutes = max(1, len(tentative) * 1.5) + travel_minutes
        cycle_minutes = round(pick_minutes + 5 + 7, 2)
        begin = BASE_TIME + timedelta(minutes=i * 25)
        schedule = [("ALLOCATED", 0), ("PICKED", pick_minutes), ("PACKED", pick_minutes + 5), ("SHIPPED", cycle_minutes)]
        for kind, minutes in schedule:
            events.append(dict(event_id=f"EVT-{len(events)+1:05d}", order_id=oid, event_type=kind,
                               occurred_at=(begin + timedelta(minutes=minutes)).isoformat(), employee_id=employee if kind in ("ALLOCATED", "PICKED") else ""))
        for line, loc, qty in tentative:
            allocation.append(dict(order_id=oid, order_line_id=line["order_line_id"], sku=line["sku"],
                                   location_code=loc, quantity_reserved=qty, reservation_status="FULFILLED"))
            movements.append(dict(movement_id=f"MOV-{len(movements)+1:05d}", order_id=oid, sku=line["sku"],
                                  location_code=loc, quantity_delta=-qty, movement_type="SHIPMENT",
                                  occurred_at=events[-1]["occurred_at"]))
        tasks.append(dict(pick_task_id=f"PICK-{len(tasks)+1:05d}", order_id=oid, employee_id=employee,
                          task_status="COMPLETED", estimated_route_ft=f'{trip["distance_ft"]:.2f}',
                          estimated_pick_minutes=f"{pick_minutes:.2f}", route_method="NEAREST_NEIGHBOR_CONCEPTUAL"))
        outcomes.append(dict(order_id=oid, status="SHIPPED", employee_id=employee,
                             units_shipped=sum(q for _, _, q in tentative), route_ft=trip["distance_ft"],
                             cycle_minutes=cycle_minutes))
    balances = [dict(sku=sku, location_code=loc, opening_quantity=qty, ending_quantity=stock[(sku, loc)])
                for (sku, loc), qty in sorted(original.items())]
    assert all(b["ending_quantity"] >= 0 for b in balances)
    assert sum(int(b["opening_quantity"]) - int(b["ending_quantity"]) for b in balances) == -sum(int(m["quantity_delta"]) for m in movements)
    assert sum(int(o["units_shipped"]) for o in outcomes) == -sum(int(m["quantity_delta"]) for m in movements)
    shipped = [o for o in outcomes if o["status"] == "SHIPPED"]
    kpis.append(dict(orders=len(orders), shipped_orders=len(shipped), backorders=len(orders)-len(shipped),
                     shipped_units=sum(int(o["units_shipped"]) for o in shipped),
                     opening_units=sum(original.values()), ending_units=sum(stock.values()),
                     total_route_ft=round(sum(float(o["route_ft"]) for o in shipped), 2),
                     average_cycle_minutes=round(sum(float(o["cycle_minutes"]) for o in shipped)/len(shipped), 2) if shipped else 0))
    return {"fulfillment_allocations.csv": allocation, "fulfillment_pick_tasks.csv": tasks,
            "fulfillment_events.csv": events, "fulfillment_movements.csv": movements,
            "fulfillment_order_status.csv": outcomes, "fulfillment_balances.csv": balances,
            "fulfillment_kpis.csv": kpis}

def main():
    result = simulate(load("orders.csv"), load("order_lines.csv"), load("initial_inventory.csv"),
                      load("employees.csv"), read_locations())
    for filename, rows in result.items():
        if rows:
            write(filename, rows, list(rows[0]))
    print(result["fulfillment_kpis.csv"][0])

if __name__ == "__main__":
    main()
