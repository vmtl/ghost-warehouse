"""Allocate pilot orders to opening inventory and assign simulated pick tasks.

Run: python scripts/allocate_orders.py
Produces data/order_allocations.csv, data/pick_tasks.csv, data/order_allocation_status.csv.
No inventory is shipped or decremented: allocations are reservations against opening stock.
"""
import csv
from collections import defaultdict
from pathlib import Path
from pick_paths import build_network, read_locations, route

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"

def read(name):
    with (DATA / name).open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))

def write(name, columns, rows):
    with (DATA / name).open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=columns, lineterminator="\n")
        w.writeheader()
        w.writerows(rows)

def allocate():
    orders = read("orders.csv")
    lines = read("order_lines.csv")
    stock = read("initial_inventory.csv")
    employees = [r for r in read("employees.csv")
                 if r["department"] == "Picking" and r["status"] == "ACTIVE"]
    if not employees:
        raise ValueError("No active picking employees")
    locations = read_locations()
    graph, coords, access = build_network(locations)
    by_sku = defaultdict(list)
    available = {}
    for r in stock:
        key = (r["sku"], r["location_code"])
        available[key] = available.get(key, 0) + int(r["quantity"])
        by_sku[r["sku"]].append(r["location_code"])
    order_lines = defaultdict(list)
    for line in lines:
        order_lines[line["order_id"]].append(line)
    if len({o["order_id"] for o in orders}) != len(orders):
        raise ValueError("Duplicate order IDs")
    if set(order_lines) != {o["order_id"] for o in orders}:
        raise ValueError("Order lines do not match order headers")

    allocations, tasks, statuses = [], [], []
    for idx, order in enumerate(orders):
        oid = order["order_id"]
        requested = order_lines[oid]
        pending = []
        # All-or-nothing allocation per order.
        for line in requested:
            needed = int(line["quantity_ordered"])
            if needed <= 0:
                raise ValueError("Invalid requested quantity")
            for loc in sorted(set(by_sku.get(line["sku"], []))):
                take = min(needed, available[(line["sku"], loc)])
                if take:
                    pending.append((line, loc, take))
                    needed -= take
                if needed == 0:
                    break
            if needed:
                pending = []
                break
        if not pending:
            statuses.append(dict(order_id=oid, allocation_status="BACKORDER",
                                 pick_task_id="", reason="INSUFFICIENT_AVAILABLE_STOCK"))
            continue
        for line, loc, qty in pending:
            available[(line["sku"], loc)] -= qty
            allocations.append(dict(order_id=oid, order_line_id=line["order_line_id"],
                                    sku=line["sku"], location_code=loc,
                                    quantity_reserved=qty, reservation_status="RESERVED"))
        task_id = f"PICK-{idx+1:05d}"
        employee = employees[idx % len(employees)]
        pick_locs = [loc for _, loc, _ in pending]
        # Routes are illustrative and NOT equipment-certified; use for analytics only.
        trip = route(graph, coords, pick_locs, optimize=True)
        tasks.append(dict(pick_task_id=task_id, order_id=oid,
                          employee_id=employee["employee_id"],
                          task_status="ASSIGNED", pick_locations=len(set(pick_locs)),
                          estimated_route_ft=f'{trip["distance_ft"]:.2f}',
                          route_method="NEAREST_NEIGHBOR_CONCEPTUAL"))
        statuses.append(dict(order_id=oid, allocation_status="ALLOCATED",
                             pick_task_id=task_id, reason=""))
    assert all(q >= 0 for q in available.values())
    write("order_allocations.csv", ["order_id","order_line_id","sku","location_code",
                                    "quantity_reserved","reservation_status"], allocations)
    write("pick_tasks.csv", ["pick_task_id","order_id","employee_id","task_status",
                             "pick_locations","estimated_route_ft","route_method"], tasks)
    write("order_allocation_status.csv", ["order_id","allocation_status","pick_task_id","reason"], statuses)
    print(f"Orders: {len(orders)} | Allocated: {len(tasks)} | Backordered: {len(orders)-len(tasks)}")
    print(f"Reservations: {len(allocations)} | Pick tasks: {len(tasks)}")
    return allocations, tasks, statuses

if __name__ == "__main__":
    allocate()
