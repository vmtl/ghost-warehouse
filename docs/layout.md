# Ghost Warehouse — physical layout v0.1

**Fictional scenario:** 80,000 sq ft, 75 employees, two shifts Monday–Saturday, hybrid B2B/B2C, target 2,500 SKUs and 8,000 storage locations. None of these are real BMW operational statistics.

| Zone | Function | Suggested space (sq ft) |
|---|---|---:|
| RCV | Receiving docks and staging | 9,000 |
| QAR | Inspection and returns | 4,000 |
| BLK | Pallet reserve | 25,000 |
| SML | Small-parts forward pick | 10,000 |
| MED | Medium-parts pick | 9,000 |
| HVY | Heavy/bulky pick | 8,000 |
| SEC | High-value secure cage | 3,000 |
| PCK | Packing and consolidation | 5,000 |
| SHP | Shipping and dispatch | 7,000 |
| **Total** | | **80,000** |

Location code pattern: `SML-A03-B12-L02-P04`. Locations should be created only for storage zones. Warehouse square footage includes circulation/staging within these zone allocations.

Location capacity is measured in units in the starter schema; future releases should model cubic volume, slotting constraints, and pallet capacity separately.
