"""Deterministic synthetic Ghost Warehouse product catalog generator.
All manufacturers, prices, SKUs and fitments are fictional or unverified.
Run: python scripts/generate_products.py
"""
import csv
from pathlib import Path

CATEGORIES = {"Engine & Induction":["Air Intake Assembly","Charge Pipe","Intake Manifold Gasket Set","Engine Mount Set","Oil Filter Housing Gasket"],"Electrical & Electronics":["Ignition Coil Set","Crankshaft Position Sensor","Oxygen Sensor","Battery Ground Cable","Alternator Assembly"],"Braking":["Front Brake Pad Set","Rear Brake Pad Set","Front Brake Rotor Pair","Rear Brake Rotor Pair","Big Brake Kit"],"Suspension & Steering":["Front Control Arm Set","Rear Toe Link Set","Coilover Suspension Kit","Sway Bar End Link Set","Tie Rod Assembly"],"Drivetrain":["Transmission Mount","Differential Bushing Set","Axle Shaft Assembly","Driveshaft Flex Disc","Clutch Kit"],"Cooling":["Engine Radiator","Coolant Expansion Tank","Water Pump Assembly","Thermostat Assembly","Oil Cooler Assembly"],"Exhaust & Emissions":["Cat-Back Exhaust System","Exhaust Mount Set","Exhaust Valve Actuator","Downpipe Assembly","Exhaust Temperature Sensor"],"Exterior & Aerodynamics":["Front Splitter","Rear Diffuser","Trunk Spoiler","Mirror Cap Set","Underbody Shield"],"Interior & Controls":["Steering Wheel Trim","Pedal Cover Set","Shift Paddle Set","Cabin Air Filter","Window Switch Assembly"],"Maintenance & Fluids":["Engine Oil Service Kit","Brake Fluid Service Kit","Differential Oil Service Kit","Spark Plug Set","Accessory Belt Kit"]}
PLATFORMS = ["F87 M2","G87 M2","F80 M3","G80 M3","F82 M4","G82 M4","F90 M5","G90 M5","F92 M8","F93 M8"]
BRANDS = [["Bavarian Core Components","OEM-style Replacement",1],["Alpenwerk Automotive","Aftermarket Replacement",1.12],["Williams Performance","Performance Upgrade",1.8],["NordTorque Engineering","Performance Upgrade",1.55],["RheinTech Parts","Aftermarket Replacement",1.2]]
HEADERS = ["sku","product_name","component_category","product_type","manufacturer","vehicle_platform","unit_cost_usd","retail_price_usd","weight_kg","fitment_status","simulated"]

def generate():
    records = []
    index = 0
    for category, parts in CATEGORIES.items():
        for part_index, part in enumerate(parts):
            for platform_index, platform in enumerate(PLATFORMS):
                for brand, product_type, multiplier in BRANDS:
                    index += 1
                    heavy = any(token in part for token in ("Rotor", "Radiator", "Exhaust System", "Axle", "Clutch", "Big Brake", "Coilover", "Downpipe"))
                    cost = round((175 if heavy else 32) * multiplier + platform_index * 13 + part_index * 19, 2)
                    price = round(cost * (1.62 if product_type == "Performance Upgrade" else 1.45), 2)
                    weight = 8 + platform_index * 0.7 if heavy else 1 + platform_index * 0.12
                    records.append([f"GH-{index:05d}", f"{brand} {part} — {platform}", category,
                        product_type, brand, platform, f"{cost:.2f}", f"{price:.2f}",
                        f"{weight:.3f}", "UNVERIFIED — requires engineering fitment validation", "true"])
    assert len(records) == 2500
    assert len({r[0] for r in records}) == len(records)
    assert all(float(r[6]) > 0 and float(r[7]) > float(r[6]) for r in records)
    assert any("Williams Performance Big Brake Kit" in r[1] for r in records)
    return records

def main():
    path = Path(__file__).resolve().parents[1] / "data" / "products.csv"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(HEADERS)
        writer.writerows(generate())
    print(f"Generated 2500 synthetic products at {path}")

if __name__ == "__main__":
    main()
