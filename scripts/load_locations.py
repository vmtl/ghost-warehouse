"""Load location master data into PostgreSQL; requires psycopg 3.
Apply sql/001_schema.sql, 002_seed.sql and 004_storage_locations.sql first.
DATABASE_URL=postgresql:///ghost_warehouse python scripts/load_locations.py
"""
import csv
import os
from pathlib import Path
import psycopg

def main():
    path = Path(__file__).resolve().parents[1] / "data" / "locations.csv"
    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    if len(rows) != 8000 or len({r["location_code"] for r in rows}) != 8000:
        raise ValueError("Expected exactly 8000 unique locations")
    with psycopg.connect(os.environ["DATABASE_URL"]) as conn:
        with conn.cursor() as cur:
            for row in rows:
                cur.execute("""INSERT INTO ghost.locations
                  (zone_id,location_code,aisle,bay,level_no,position_no,capacity_units,
                   max_weight_kg,storage_type,capacity_volume_m3,length_cm,width_cm,height_cm,
                   access_method,pick_priority,secure,active)
                  SELECT z.zone_id,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s
                  FROM ghost.zones z JOIN ghost.facilities f ON f.facility_id=z.facility_id
                  WHERE f.code='GH01' AND z.code=%s AND z.zone_type='STORAGE'
                  ON CONFLICT(location_code) DO UPDATE SET
                    capacity_units=EXCLUDED.capacity_units,max_weight_kg=EXCLUDED.max_weight_kg,
                    storage_type=EXCLUDED.storage_type,capacity_volume_m3=EXCLUDED.capacity_volume_m3,
                    length_cm=EXCLUDED.length_cm,width_cm=EXCLUDED.width_cm,height_cm=EXCLUDED.height_cm,
                    access_method=EXCLUDED.access_method,pick_priority=EXCLUDED.pick_priority,
                    secure=EXCLUDED.secure,active=EXCLUDED.active""",
                  (row["location_code"],row["aisle"],row["bay"],int(row["level_no"]),
                   int(row["position_no"]),int(row["capacity_units"]),row["max_weight_kg"],
                   row["storage_type"],row["capacity_volume_m3"],row["length_cm"],
                   row["width_cm"],row["height_cm"],row["access_method"],
                   int(row["pick_priority"]),row["secure"]=="true",row["active"]=="true",row["zone_code"]))
            cur.execute("SELECT count(*) FROM ghost.locations")
            count=cur.fetchone()[0]
            if count != 8000:
                raise ValueError(f"Database contains {count} locations, expected 8000")
    print("Loaded 8000 storage locations")

if __name__ == "__main__":
    main()
