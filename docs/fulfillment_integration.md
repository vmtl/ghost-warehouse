# Phase 10 — reproducible fulfillment integration

Run `python scripts/run_fulfillment.py` to generate deterministic `data/fulfillment_*.csv` outputs. Run `python -m unittest discover -s tests` to execute the integration tests.

The runner reads the 25 pilot orders, existing inventory, 20 active pickers, and warehouse locations; allocates each order atomically (all-or-nothing); computes conceptual nearest-neighbor pick routes; produces order event histories and shipment ledger entries; reconciles opening/ending inventory; and generates a single-row KPI summary for dashboard use.

**Status:** The Python integration runner and tests are committed; execution in a local Python environment is required before asserting that the suite passes or that routing KPIs have been measured. The existing Phase 9 snapshot is preserved. New outputs use the `fulfillment_` prefix and will be written by the runner, not pre-committed here.

**Limitations:** Travel speed 240 feet/minute, 1.5 minutes per pick, five minutes packing and seven minutes dispatch are synthetic assumptions. Routes do not enforce forklift or authorized-access restrictions. Employees are assigned round-robin without actual shift scheduling. Orders are simulated, not real sales; outputs are regenerated from the opening snapshot on each run. A live warehouse would need durable transaction processing and concurrency control.

**Dashboard connection:** `data/fulfillment_kpis.csv` provides total orders, shipped orders, backorders, units, opening/ending inventory, total route distance in feet and average cycle time in minutes. `fulfillment_order_status.csv` supports order drill-down.
