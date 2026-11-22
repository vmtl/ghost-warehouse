"""Load opening inventory as idempotent receipts in the movement ledger.
Requires populated products and locations; DATABASE_URL and psycopg[binary].
"""
import csv
import os
from pathlib import Path
import psycopg

ROOT = Path(__file__).resolve().parents[1] / "data"

def read(filename):
    with (ROOT / filename).open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))

def main():
    packaging = read("product_packaging.csv")
    inventory = read("initial_inventory.csv")
    if len(packaging) != 2500 or len(inventory) != 2500:
        raise ValueError("Expected 2500 packaging and inventory rows")
    with psycopg.connect(os.environ["DATABASE_URL"]) as conn:
        with conn.cursor() as cur:
            for r in packaging:
                cur.execute("""UPDATE ghost.products SET package_length_cm=%s,package_width_cm=%s,
                    package_height_cm=%s,packaging_source=%s WHERE sku=%s""",
                    (r["package_length_cm"],r["package_width_cm"],r["package_height_cm"],r["dimension_source"],r["sku"]))
                if cur.rowcount != 1:
                    raise ValueError(f"Missing product {r['sku']}")
            for r in inventory:
                cur.execute("""SELECT p.product_id,l.location_id,l.capacity_units,l.max_weight_kg,
                    l.length_cm,l.width_cm,l.height_cm,p.weight_kg,
                    p.package_length_cm,p.package_width_cm,p.package_height_cm
                    FROM ghost.products p CROSS JOIN ghost.locations l
                    WHERE p.sku=%s AND l.location_code=%s""", (r["sku"],r["location_code"]))
                found = cur.fetchone()
                if not found:
                    raise ValueError(f"Missing product/location for {r['receipt_id']}")
                pid,lid,capacity,max_weight,ll,lw,lh,pw,pl,pwidth,ph=found
                qty=int(r["quantity"])
                if qty > capacity or pw > max_weight or pl > ll or pwidth > lw or ph > lh:
                    raise ValueError(f"Invalid location capacity or dimensions for {r['sku']}")
                cur.execute("""INSERT INTO ghost.reorder_targets(product_id,reorder_point) VALUES (%s,%s)
                    ON CONFLICT(product_id) DO UPDATE SET reorder_point=EXCLUDED.reorder_point""",
                    (pid,int(r["reorder_point"])))
                cur.execute("""SELECT movement_id FROM ghost.inventory_movements
                    WHERE reference_type='INITIAL_RECEIPT' AND reference_id=%s""",(r["receipt_id"],))
                if cur.fetchone() is None:
                    cur.execute("""INSERT INTO ghost.inventory_movements
                        (product_id,to_location_id,quantity,movement_type,occurred_at,reference_type,reference_id)
                        VALUES (%s,%s,%s,'RECEIPT',%s,'INITIAL_RECEIPT',%s)""",
                        (pid,lid,qty,r["occurred_at"],r["receipt_id"]))
    print("Opening inventory loaded; reruns do not duplicate initial receipts")

if __name__ == "__main__":
    main()
