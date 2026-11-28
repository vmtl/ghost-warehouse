BEGIN;
CREATE TABLE IF NOT EXISTS ghost.employees (
 employee_id text PRIMARY KEY, employee_name text NOT NULL, department text NOT NULL,
 job_title text NOT NULL, shift text NOT NULL, shift_start time NOT NULL, shift_end time NOT NULL,
 hourly_rate_usd numeric(10,2) NOT NULL CHECK(hourly_rate_usd>=0), status text NOT NULL, simulated boolean NOT NULL
);
ALTER TABLE ghost.customers ADD COLUMN IF NOT EXISTS channel text, ADD COLUMN IF NOT EXISTS payment_terms text, ADD COLUMN IF NOT EXISTS status text, ADD COLUMN IF NOT EXISTS simulated boolean NOT NULL DEFAULT true;
ALTER TABLE ghost.suppliers ADD COLUMN IF NOT EXISTS supplier_type text, ADD COLUMN IF NOT EXISTS primary_manufacturer text, ADD COLUMN IF NOT EXISTS on_time_delivery_target_pct numeric CHECK(on_time_delivery_target_pct BETWEEN 0 AND 100), ADD COLUMN IF NOT EXISTS minimum_order_usd numeric CHECK(minimum_order_usd>=0), ADD COLUMN IF NOT EXISTS currency text, ADD COLUMN IF NOT EXISTS status text, ADD COLUMN IF NOT EXISTS simulated boolean NOT NULL DEFAULT true;
ALTER TABLE ghost.orders ADD COLUMN IF NOT EXISTS channel text, ADD COLUMN IF NOT EXISTS currency text, ADD COLUMN IF NOT EXISTS simulated boolean NOT NULL DEFAULT true;
ALTER TABLE ghost.orders DROP CONSTRAINT IF EXISTS orders_status_check;
ALTER TABLE ghost.orders ADD CONSTRAINT orders_status_check CHECK(status IN ('NEW','ALLOCATED','PICKING','PACKED','SHIPPED','CANCELLED','BACKORDER'));
ALTER TABLE ghost.order_lines ADD COLUMN IF NOT EXISTS source_line_code text UNIQUE;
CREATE TABLE IF NOT EXISTS ghost.allocations (
 order_line_id bigint NOT NULL REFERENCES ghost.order_lines, location_id bigint NOT NULL REFERENCES ghost.locations,
 quantity_reserved integer NOT NULL CHECK(quantity_reserved>0), reservation_status text NOT NULL,
 PRIMARY KEY(order_line_id,location_id)
);
CREATE TABLE IF NOT EXISTS ghost.pick_tasks (
 pick_task_id text PRIMARY KEY, order_id bigint NOT NULL REFERENCES ghost.orders, employee_id text NOT NULL REFERENCES ghost.employees,
 task_status text NOT NULL, estimated_route_ft numeric NOT NULL CHECK(estimated_route_ft>=0), estimated_pick_minutes numeric NOT NULL CHECK(estimated_pick_minutes>=0), route_method text NOT NULL
);
CREATE TABLE IF NOT EXISTS ghost.fulfillment_events (
 event_id text PRIMARY KEY, order_id bigint NOT NULL REFERENCES ghost.orders, event_type text NOT NULL CHECK(event_type IN ('ALLOCATED','PICKED','PACKED','SHIPPED')), occurred_at timestamptz NOT NULL, employee_id text REFERENCES ghost.employees
);
CREATE TABLE IF NOT EXISTS ghost.pilot_imports (batch_id text PRIMARY KEY, imported_at timestamptz NOT NULL DEFAULT now());
CREATE UNIQUE INDEX IF NOT EXISTS pilot_movement_reference_unique ON ghost.inventory_movements(reference_id) WHERE reference_type='PILOT_SHIPMENT';
CREATE INDEX IF NOT EXISTS fulfillment_events_order_idx ON ghost.fulfillment_events(order_id,occurred_at);
COMMIT;
