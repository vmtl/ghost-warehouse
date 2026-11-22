-- Ghost Warehouse storage slot attributes (run after 001_schema.sql)
ALTER TABLE ghost.locations ADD COLUMN IF NOT EXISTS storage_type text;
ALTER TABLE ghost.locations ADD COLUMN IF NOT EXISTS capacity_volume_m3 numeric(12,4);
ALTER TABLE ghost.locations ADD COLUMN IF NOT EXISTS length_cm numeric(10,1);
ALTER TABLE ghost.locations ADD COLUMN IF NOT EXISTS width_cm numeric(10,1);
ALTER TABLE ghost.locations ADD COLUMN IF NOT EXISTS height_cm numeric(10,1);
ALTER TABLE ghost.locations ADD COLUMN IF NOT EXISTS access_method text;
ALTER TABLE ghost.locations ADD COLUMN IF NOT EXISTS pick_priority smallint;
ALTER TABLE ghost.locations ADD COLUMN IF NOT EXISTS secure boolean NOT NULL DEFAULT false;
ALTER TABLE ghost.locations ADD CONSTRAINT storage_type_allowed CHECK (storage_type IN ('PALLET_RACK','PARTS_DRAWER','SHELVING','FLOOR_BAY','SECURE_CABINET'));
ALTER TABLE ghost.locations ADD CONSTRAINT access_method_allowed CHECK (access_method IN ('FORKLIFT','MANUAL','PALLET_JACK','AUTHORIZED'));
ALTER TABLE ghost.locations ADD CONSTRAINT pick_priority_range CHECK (pick_priority BETWEEN 1 AND 5);
