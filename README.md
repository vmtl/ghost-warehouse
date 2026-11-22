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
