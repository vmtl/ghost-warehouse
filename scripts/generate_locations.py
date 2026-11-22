"""Generate 8,000 deterministic warehouse storage addresses and handling attributes.
Run: python scripts/generate_locations.py
"""
import csv
from pathlib import Path

DEFINITIONS = [["BLK","PALLET_RACK",14,10,5,2,120,100,150,850,"FORKLIFT",4,0],["SML","PARTS_DRAWER",20,10,5,4,30,40,20,25,"MANUAL",1,0],["MED","SHELVING",10,10,4,4,80,60,60,110,"MANUAL",2,0],["HVY","FLOOR_BAY",10,15,1,4,250,200,180,1500,"PALLET_JACK",5,0],["SEC","SECURE_CABINET",5,10,2,4,60,50,50,60,"AUTHORIZED",3,1]]
HEADERS = ["location_code","zone_code","storage_type","aisle","bay","level_no","position_no","capacity_units","max_weight_kg","length_cm","width_cm","height_cm","capacity_volume_m3","access_method","pick_priority","secure","active"]

def generate():
    result = []
    for zone, storage_type, aisles, bays, levels, positions, length, width, height, weight, access, priority, secure in DEFINITIONS:
        for a in range(1, aisles + 1):
            for b in range(1, bays + 1):
                for level in range(1, levels + 1):
                    for position in range(1, positions + 1):
                        code = f"{zone}-A{a:02d}-B{b:02d}-L{level:02d}-P{position:02d}"
                        capacity = {"PARTS_DRAWER": 40, "SHELVING": 12, "SECURE_CABINET": 8, "PALLET_RACK": 1, "FLOOR_BAY": 1}[storage_type]
                        result.append([code, zone, storage_type, f"A{a:02d}", f"B{b:02d}",
                            level, position, capacity, weight, length, width, height,
                            f"{length * width * height / 1_000_000:.4f}", access, priority,
                            "true" if secure else "false", "true"])
    assert len(result) == 8000
    assert len({row[0] for row in result}) == 8000
    return result

def main():
    target = Path(__file__).resolve().parents[1] / "data" / "locations.csv"
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(HEADERS)
        writer.writerows(generate())
    print(f"Generated 8000 storage locations: {target}")

if __name__ == "__main__":
    main()
