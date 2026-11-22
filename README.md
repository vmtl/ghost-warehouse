# Ghost Warehouse

A **fictional** hybrid wholesale/retail BMW M performance parts warehouse simulation for data engineering, analytics, and BI case studies.

> Independent portfolio simulation. Not affiliated with, sponsored by, or endorsed by BMW. All starter SKU identifiers, product descriptions, prices, costs, and inventory assumptions are synthetic. Vehicle fitments are not verified.

## Phase 1 — foundation

- `docs/layout.md`: 80,000 sq ft conceptual warehouse with nine operating zones.
- `data/sample_products.csv`: 20 illustrative synthetic SKUs, not the target 2,500.
- `sql/001_schema.sql`: PostgreSQL 15+ operational schema, constraints, indexes, and inventory balance view.
- `sql/002_seed.sql`: reference data for facilities, zones, categories, fictional brands, and BMW M chassis codes.

## Local PostgreSQL setup

```bash
createdb ghost_warehouse
psql -d ghost_warehouse -v ON_ERROR_STOP=1 -f sql/001_schema.sql
psql -d ghost_warehouse -v ON_ERROR_STOP=1 -f sql/002_seed.sql
```

These SQL scripts have been committed but have **not yet been executed against a live PostgreSQL server**.

## Modeling notes

- Inventory on hand is calculated from a movement ledger, not from order counts.
- Application validation or stored procedures are still needed to enforce nonnegative inventory, valid movement endpoints, and order-state transitions.
- The product CSV is reference data only; the product importer and full catalog generator have not been implemented.
- No real BMW part numbers or verified product-to-vehicle compatibility claims are included.
- Wholesale contract pricing, employees, shipments, procurement, and analytics star schema are future work.

## Next steps

1. Build deterministic Python generators for the 2,500-SKU catalog and 8,000 storage locations.
2. Add inventory seeding and transactional simulation.
3. Add PostgreSQL integration tests and GitHub Actions validation.
4. Build inventory accuracy, fulfillment, and demand forecasting case studies.

## Phase 2 — 2,500-SKU synthetic catalog

- `data/products.csv`: 2,500 fictional product records with component category, product type, manufacturer, indicative synthetic costs/prices and **unverified** BMW chassis association.
- `scripts/generate_products.py`: deterministic Python generator (50 component families × 10 chassis codes × 5 fictional manufacturers).
- `sql/003_catalog_classification.sql`: adds product type and fitment status fields.
- `scripts/load_products.py`: PostgreSQL importer; requires `pip install psycopg[binary]` and `DATABASE_URL`.

Run in this order after initial setup:

```bash
psql -d ghost_warehouse -v ON_ERROR_STOP=1 -f sql/003_catalog_classification.sql
python scripts/generate_products.py
DATABASE_URL=postgresql:///ghost_warehouse python scripts/load_products.py
```

**Safety/accuracy:** These are hypothetical catalog offerings, not verified BMW-compatible products or real market prices. `OEM-style Replacement` describes a fictional replacement tier, **not** a genuine BMW OEM part. Brake fitments in particular require rotor, caliper, hub, wheel clearance, and vehicle-specific engineering checks. The generator has not been run against a production database.

## Phase 3 — 8,000 warehouse storage locations

- `data/locations.csv`: 8,000 deterministic location records (1,400 pallet rack, 4,000 small drawer, 1,600 shelving, 600 floor bays, 400 secure cabinets).
- `scripts/generate_locations.py`: regenerates location master data.
- `scripts/load_locations.py`: idempotent PostgreSQL location loader.
- `sql/004_storage_locations.sql`: adds physical slot attributes and constraints.
- `tests/test_locations.py`: count, uniqueness, capacity and committed-CSV consistency tests.
- `docs/layout.md`: facility plan, location dimensions, handling and storage rules.

```bash
python scripts/generate_locations.py
python -m unittest discover -s tests
psql -d ghost_warehouse -v ON_ERROR_STOP=1 -f sql/004_storage_locations.sql
DATABASE_URL=postgresql:///ghost_warehouse python scripts/load_locations.py
```

**Status:** Location master data has been committed, but no PostgreSQL deployment or physical product-to-location slotting has been executed. Storage capacities and weights are hypothetical, not real rack certifications.
