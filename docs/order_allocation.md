# Phase 8 — reservation and pick-task pilot

Run `python scripts/allocate_orders.py` from repository root. This uses existing Phase 6 routing and Phase 7 orders. Outputs: `data/order_allocations.csv`, `data/pick_tasks.csv`, and `data/order_allocation_status.csv`.

For each order, the allocator finds opening inventory by SKU and location, reserves quantities without exceeding available stock, and assigns an active Picking department employee to a simulated pick task. If any line cannot be fully allocated, the entire order is marked BACKORDER and no stock is reserved for it. A nearest-neighbor route is calculated using the conceptual aisle graph.

**Important:** This is a deterministic batch simulation, not a concurrent transactional WMS. Running it again recomputes reservations from the opening snapshot; it does not persist an ongoing inventory ledger or decrement physical on-hand stock. Order headers remain NEW, pick tasks remain ASSIGNED, and nothing is marked shipped. Employee assignments are round-robin and do not yet enforce shift times, capacity, access permissions or equipment qualifications. The routing model currently permits all access types and is unsuitable for real forklift/pedestrian routing.

Next: add an immutable inventory movement ledger, event timestamps, pick confirmations, equipment-aware route restrictions, and tests for partial fulfillment, duplicate inputs and repeated simulation runs.
