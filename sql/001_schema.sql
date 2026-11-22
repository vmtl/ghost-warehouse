-- Ghost Warehouse v0.1: PostgreSQL 15+
CREATE SCHEMA IF NOT EXISTS ghost;
CREATE TABLE ghost.facilities (facility_id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY, code text NOT NULL UNIQUE, name text NOT NULL, square_feet integer NOT NULL CHECK(square_feet>0));
CREATE TABLE ghost.zones (zone_id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY, facility_id bigint NOT NULL REFERENCES ghost.facilities, code text NOT NULL, name text NOT NULL, zone_type text NOT NULL CHECK(zone_type IN ('STORAGE','RECEIVING','QUALITY','PACKING','SHIPPING')), UNIQUE(facility_id,code));
CREATE TABLE ghost.locations (location_id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY, zone_id bigint NOT NULL REFERENCES ghost.zones, location_code text NOT NULL UNIQUE, aisle text, bay text, level_no integer, position_no integer, capacity_units integer CHECK(capacity_units>0), max_weight_kg numeric(12,2) CHECK(max_weight_kg>0), active boolean NOT NULL DEFAULT true);
CREATE TABLE ghost.brands (brand_id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY, name text NOT NULL UNIQUE, brand_type text NOT NULL CHECK(brand_type IN ('GENUINE','AFTERMARKET','SIMULATED')));
CREATE TABLE ghost.categories (category_id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY, name text NOT NULL UNIQUE);
CREATE TABLE ghost.products (product_id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY, sku text NOT NULL UNIQUE, product_name text NOT NULL, category_id bigint NOT NULL REFERENCES ghost.categories, brand_id bigint NOT NULL REFERENCES ghost.brands, unit_cost numeric(12,2) NOT NULL CHECK(unit_cost>=0), retail_price numeric(12,2) NOT NULL CHECK(retail_price>=0), weight_kg numeric(10,3) CHECK(weight_kg>0), active boolean NOT NULL DEFAULT true, simulated boolean NOT NULL DEFAULT true);
CREATE TABLE ghost.vehicle_platforms (platform_id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY, chassis_code text NOT NULL UNIQUE, model_name text NOT NULL, generation text);
CREATE TABLE ghost.product_fitments (product_id bigint NOT NULL REFERENCES ghost.products, platform_id bigint NOT NULL REFERENCES ghost.vehicle_platforms, fitment_note text, PRIMARY KEY(product_id,platform_id));
CREATE TABLE ghost.suppliers (supplier_id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY, supplier_code text NOT NULL UNIQUE, supplier_name text NOT NULL, lead_time_days integer NOT NULL CHECK(lead_time_days>=0));
CREATE TABLE ghost.product_suppliers (product_id bigint NOT NULL REFERENCES ghost.products, supplier_id bigint NOT NULL REFERENCES ghost.suppliers, preferred boolean NOT NULL DEFAULT false, PRIMARY KEY(product_id,supplier_id));
CREATE TABLE ghost.customers (customer_id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY, customer_code text NOT NULL UNIQUE, customer_type text NOT NULL CHECK(customer_type IN ('RETAIL','WHOLESALE')), company_name text);
CREATE TABLE ghost.orders (order_id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY, order_number text NOT NULL UNIQUE, customer_id bigint NOT NULL REFERENCES ghost.customers, placed_at timestamptz NOT NULL, status text NOT NULL CHECK(status IN ('NEW','ALLOCATED','PICKING','PACKED','SHIPPED','CANCELLED')));
CREATE TABLE ghost.order_lines (order_line_id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY, order_id bigint NOT NULL REFERENCES ghost.orders, product_id bigint NOT NULL REFERENCES ghost.products, quantity integer NOT NULL CHECK(quantity>0), unit_price numeric(12,2) NOT NULL CHECK(unit_price>=0));
CREATE TABLE ghost.inventory_movements (movement_id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY, product_id bigint NOT NULL REFERENCES ghost.products, from_location_id bigint REFERENCES ghost.locations, to_location_id bigint REFERENCES ghost.locations, quantity integer NOT NULL CHECK(quantity>0), movement_type text NOT NULL CHECK(movement_type IN ('RECEIPT','PUTAWAY','TRANSFER','PICK','SHIP','ADJUSTMENT','RETURN')), occurred_at timestamptz NOT NULL, reference_type text, reference_id text, CHECK(from_location_id IS DISTINCT FROM to_location_id));
CREATE INDEX idx_orders_placed ON ghost.orders(placed_at);
CREATE INDEX idx_movements_product_time ON ghost.inventory_movements(product_id,occurred_at);
CREATE INDEX idx_movements_from ON ghost.inventory_movements(from_location_id);
CREATE INDEX idx_movements_to ON ghost.inventory_movements(to_location_id);
-- Stock balance derives from signed movement entries, not orders.
CREATE VIEW ghost.inventory_balance AS
SELECT product_id, location_id, SUM(delta) AS on_hand
FROM (SELECT product_id,to_location_id AS location_id,quantity::bigint AS delta FROM ghost.inventory_movements WHERE to_location_id IS NOT NULL
UNION ALL SELECT product_id,from_location_id AS location_id,-quantity::bigint AS delta FROM ghost.inventory_movements WHERE from_location_id IS NOT NULL) m
GROUP BY product_id,location_id;
