"""Import synthetic catalog into Ghost Warehouse PostgreSQL.
Requires: pip install psycopg[binary]
Set DATABASE_URL before running. Apply schema, seed and migration first.
"""
import csv
import os
from pathlib import Path
import psycopg

PATH = Path(__file__).resolve().parents[1] / "data" / "products.csv"

def main():
    dsn = os.environ["DATABASE_URL"]
    with psycopg.connect(dsn) as conn, conn.cursor() as cur:
        with PATH.open(encoding="utf-8", newline="") as f:
            records = list(csv.DictReader(f))
        if len(records) != 2500 or len({r["sku"] for r in records}) != 2500:
            raise ValueError("Expected 2500 unique SKUs")
        for row in records:
            cur.execute("INSERT INTO ghost.categories(name) VALUES (%s) ON CONFLICT DO NOTHING", (row["component_category"],))
            cur.execute("INSERT INTO ghost.brands(name,brand_type) VALUES (%s,'SIMULATED') ON CONFLICT DO NOTHING", (row["manufacturer"],))
            cur.execute("""INSERT INTO ghost.products(sku,product_name,category_id,brand_id,unit_cost,retail_price,weight_kg,product_type,fitment_status,simulated)
                SELECT %s,%s,c.category_id,b.brand_id,%s,%s,%s,%s,%s,true
                FROM ghost.categories c CROSS JOIN ghost.brands b
                WHERE c.name=%s AND b.name=%s
                ON CONFLICT(sku) DO UPDATE SET
                product_name=EXCLUDED.product_name,category_id=EXCLUDED.category_id,
                brand_id=EXCLUDED.brand_id,unit_cost=EXCLUDED.unit_cost,
                retail_price=EXCLUDED.retail_price,weight_kg=EXCLUDED.weight_kg,
                product_type=EXCLUDED.product_type,fitment_status=EXCLUDED.fitment_status""",
                (row["sku"],row["product_name"],row["unit_cost_usd"],row["retail_price_usd"],
                 row["weight_kg"],row["product_type"],row["fitment_status"],
                 row["component_category"],row["manufacturer"]))
            chassis=row["vehicle_platform"].split()[0]
            cur.execute("""INSERT INTO ghost.product_fitments(product_id,platform_id,fitment_note)
                SELECT p.product_id,v.platform_id,%s FROM ghost.products p CROSS JOIN ghost.vehicle_platforms v
                WHERE p.sku=%s AND v.chassis_code=%s ON CONFLICT(product_id,platform_id)
                DO UPDATE SET fitment_note=EXCLUDED.fitment_note""",
                (row["fitment_status"],row["sku"],chassis))
        print("Loaded 2500 synthetic products and unverified platform associations")

if __name__ == "__main__":
    main()
