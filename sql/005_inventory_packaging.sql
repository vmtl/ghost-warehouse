-- Phase 4: synthetic packaged dimensions and replenishment targets.
-- Run after 001_schema.sql, 002_seed.sql, 003_catalog_classification.sql, 004_storage_locations.sql.
ALTER TABLE ghost.products ADD COLUMN IF NOT EXISTS package_length_cm numeric(10,1);
ALTER TABLE ghost.products ADD COLUMN IF NOT EXISTS package_width_cm numeric(10,1);
ALTER TABLE ghost.products ADD COLUMN IF NOT EXISTS package_height_cm numeric(10,1);
ALTER TABLE ghost.products ADD COLUMN IF NOT EXISTS packaging_source text;
CREATE TABLE IF NOT EXISTS ghost.reorder_targets (
 product_id bigint PRIMARY KEY REFERENCES ghost.products(product_id),
 reorder_point integer NOT NULL CHECK(reorder_point>=0)
);
