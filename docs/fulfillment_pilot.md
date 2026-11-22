# Phase 9 — first synthetic fulfillment snapshot

This milestone commits a **generated demonstration snapshot**, not an executed production WMS.

- 25 pilot orders were matched against the existing opening stock and assigned to the 20 active Picking employees in round-robin order.
- 50 order-line reservations and 25 pick assignments were recorded.
- 100 synthetic order events cover ALLOCATED, PICKED, PACKED and SHIPPED.
- 50 shipment movement rows reduce opening on-hand units from 19,870 to 19,820; no negative balances.
- Event times are illustrative fixed intervals (8 minutes to PICKED, 13 to PACKED, 20 to SHIPPED from simulated allocation). They are **not observed performance measurements**.
- Pick-task route distances remain blank pending end-to-end execution and validation of the routing code. Equipment-aware routing and employee shift enforcement are not implemented.
- The existing `data/orders.csv` remains the original NEW order snapshot; use `data/order_allocation_status.csv` and `data/order_events.csv` for this simulated fulfillment outcome.
- The existing Python allocator was **not executed** in this milestone; the CSV snapshot was generated and reconciled separately. A reproducible end-to-end Python integration and automated tests are still needed before scaling.

Files: `data/order_allocations.csv`, `data/pick_tasks.csv`, `data/order_allocation_status.csv`, `data/order_events.csv`, `data/inventory_movements.csv`, `data/inventory_balances_pilot.csv`.

Next: run Python allocation and routing end-to-end, add a deterministic fulfillment generator and automated reconciliation tests, reconcile order-header status to events, then model true task durations and equipment-specific paths.
