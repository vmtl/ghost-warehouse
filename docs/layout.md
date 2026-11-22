# Ghost Warehouse — physical layout v0.2

**Fictional 80,000 sq ft regional DC** with 75 planned staff and hybrid retail/wholesale operations. Counts, capacities and dimensions are simulation assumptions, not architectural or engineering specifications.

## Zones and space

| Zone | Function | Space (sq ft) | Storage locations | Storage system |
|---|---|---:|---:|---|
| RCV | Receiving and inbound staging | 9,000 | 0 | Work area |
| QAR | Quality inspection and returns | 4,000 | 0 | Work area |
| BLK | Bulk replenishment reserve | 25,000 | 1,400 | Pallet racks |
| SML | Small parts forward pick | 10,000 | 4,000 | Drawers |
| MED | Medium parts forward pick | 9,000 | 1,600 | Shelving |
| HVY | Oversize and heavy products | 8,000 | 600 | Floor bays |
| SEC | High-value controlled access | 3,000 | 400 | Secure cabinets |
| PCK | Packing and consolidation | 5,000 | 0 | Work area |
| SHP | Outbound staging and dispatch | 7,000 | 0 | Work area |
| **Total** | | **80,000** | **8,000** | |

## Storage master data

| Type | Dimensions (cm) L×W×H | Max load kg per slot | Unit capacity | Access |
|---|---|---:|---:|---|
| PALLET_RACK | 120×100×150 | 850 | 1 palletized handling unit | Forklift |
| PARTS_DRAWER | 30×40×20 | 25 | 40 small units | Manual |
| SHELVING | 80×60×60 | 110 | 12 units | Manual |
| FLOOR_BAY | 250×200×180 | 1500 | 1 oversize handling unit | Pallet jack |
| SECURE_CABINET | 60×50×50 | 60 | 8 units | Authorized |

Location codes follow `BLK-A01-B01-L01-P01`. Each address is unique; location level and position are modeled separately. Capacity is illustrative and **must not** be treated as validated engineering rack ratings. Floor-bay load handling must be checked against actual equipment and floor ratings before any real-world application.

## Intended part routing

- **BLK:** sealed cases of rotors, brake kits, bulk service kits and replenishment pallets
- **SML:** sensors, ignition coils, gaskets, spark plugs, small electrical parts and fasteners
- **MED:** brake pads, pumps, mounts, small cooling assemblies and control arms when size permits
- **HVY:** long exhaust systems, oversized diffusers, bulky body components and crated assemblies
- **SEC:** valuable electronic modules, tuning accessories and specialty parts that fit cabinet dimensions

Storage assignment must check physical dimensions, weight, handling-unit packaging, security, and available capacity; category alone is insufficient. The current catalog has **weight estimates but no verified packaged dimensions**, so automated product-to-location assignment is deliberately deferred. No initial inventory is claimed to have been placed yet.

## Generation and import

```bash
python scripts/generate_locations.py
python -m unittest discover -s tests
psql -d ghost_warehouse -v ON_ERROR_STOP=1 -f sql/004_storage_locations.sql
DATABASE_URL=postgresql:///ghost_warehouse python scripts/load_locations.py
```

Requires `pip install psycopg[binary]` for database loading. The CSV is committed; SQL execution against a live database remains a separate step.
