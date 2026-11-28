-- Daily batch control; apply after 006. All counts refer to completed batches.
BEGIN;
CREATE TABLE IF NOT EXISTS ghost.daily_operations (
 operating_date date PRIMARY KEY,
 opening_inventory bigint NOT NULL CHECK (opening_inventory >= 0),
 opening_backlog integer NOT NULL CHECK (opening_backlog >= 0),
 new_orders integer NOT NULL CHECK (new_orders >= 0),
 shipped_orders integer NOT NULL CHECK (shipped_orders >= 0),
 shipped_units bigint NOT NULL CHECK (shipped_units >= 0),
 closing_backlog integer NOT NULL CHECK (closing_backlog >= 0),
 closing_inventory bigint NOT NULL CHECK (closing_inventory >= 0),
 completed_at timestamptz NOT NULL DEFAULT now(),
 CHECK (opening_backlog + new_orders = shipped_orders + closing_backlog),
 CHECK (opening_inventory - shipped_units = closing_inventory)
);
CREATE UNIQUE INDEX IF NOT EXISTS daily_movement_reference_unique
 ON ghost.inventory_movements(reference_id) WHERE reference_type='DAILY_SHIPMENT';
CREATE INDEX IF NOT EXISTS orders_pending_idx ON ghost.orders(placed_at,order_id)
 WHERE status IN ('NEW','BACKORDER');
COMMIT;
