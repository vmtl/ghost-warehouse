-- Apply after 001_schema.sql. Synthetic catalog classification extensions.
ALTER TABLE ghost.products ADD COLUMN IF NOT EXISTS product_type text;
ALTER TABLE ghost.products ADD COLUMN IF NOT EXISTS fitment_status text NOT NULL DEFAULT 'UNVERIFIED';
ALTER TABLE ghost.products ADD CONSTRAINT product_type_allowed CHECK (product_type IN ('OEM-style Replacement','Aftermarket Replacement','Performance Upgrade','Service/Consumable'));
-- The existing brand_type SIMULATED is used for every fictional manufacturer.
