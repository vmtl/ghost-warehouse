# Phase 6 — conceptual warehouse aisle graph and pick paths

Run `python scripts/pick_paths.py` from the repository root. No PostgreSQL or third-party dependencies required.

The script reads the **existing 8,000 storage locations**, derives a two-dimensional aisle-side access point for each location, creates walkable vertical aisles and horizontal cross-aisles, and computes shortest-path distance along the graph using Dijkstra's algorithm. Every pick route begins and ends at the packing station. It compares the input pick order against a nearest-neighbor heuristic and writes `data/pick_route_demo.json` locally.

**Modeling constraints:** These are illustrative coordinates measured in feet, not a scaled CAD plan. Multiple storage levels/positions share an aisle-side access point. The current model does not include vertical handling time, congestion, pick service time, one-way aisles, safety clearances, forklift restrictions, or an actual physical separation of people and equipment. `access_method` is retained for future routing permissions. Do not treat this as a validated industrial facility layout or a safe operating route.

**Next steps:** Validate spatial fit against the 80,000 sq ft area budget; build explicit equipment-specific access graphs; add realistic travel speed and handling times; connect route simulations to orders and shift assignments; display polylines on the eventual Streamlit site. Route improvement is scenario-specific and should never be presented as measured operational savings.
