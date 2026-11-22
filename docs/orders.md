# Phase 7 — customer and pilot order generation

Run `python scripts/generate_orders.py` at repository root. Uses only Python standard library and existing `data/products.csv` and `data/initial_inventory.csv`.

Creates `data/customers.csv` (60 fictional customers: 20 wholesale, 40 retail), `data/orders.csv` (25 synthetic NEW orders) and `data/order_lines.csv` (50 lines, two per order). Prices come from the catalog, with a hypothetical 15% B2B discount. Every ordered SKU is checked against opening inventory and aggregate pilot demand cannot exceed the opening quantity for that SKU.

**Important distinction:** The generator validates that pilot demand is feasible but does **not** reserve or decrement stock, create picking tasks, assign employees, dispatch orders, or change order status. All 25 orders remain NEW. A subsequent transactional allocation layer must enforce reservations and prevent double allocation across runs.

Customer names, orders, discounts, timestamps and prices are synthetic. Do not interpret them as real sales or actual BMW fitment data.

Next: run and test the generator, connect order lines to storage locations, enforce atomic reservations, and integrate the pick-path engine after equipment access constraints are modeled.
