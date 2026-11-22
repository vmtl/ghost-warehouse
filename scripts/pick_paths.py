"""Phase 6: deterministic conceptual aisle graph and warehouse pick routing.

Run: python scripts/pick_paths.py
Uses only the Python standard library and data/locations.csv.
Coordinates are illustrative feet, not a surveyed or safety-approved facility plan.
"""
import csv
import heapq
import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ZONE_LAYOUT = {
    # x origin, y origin, aisle count, bay count, aisle spacing, bay spacing
    "BLK": (20, 100, 14, 10, 8, 9),
    "SML": (150, 100, 20, 10, 4, 7),
    "MED": (20, 215, 10, 10, 8, 7),
    "HVY": (115, 215, 10, 15, 8, 5),
    "SEC": (205, 215, 5, 10, 8, 7),
}
PACK = (140, 25)
# Common pedestrian transfer corridor at y=80, connected to each aisle.
CROSS_AISLE_Y = 80
# Another transfer corridor at y=205 links southern zone aisles.
SOUTH_CROSS_Y = 205


def read_locations(path=ROOT / "data" / "locations.csv"):
    with open(path, newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def build_network(locations):
    """Build orthogonal travel graph. Vertical aisle edges and horizontal cross-aisles."""
    graph = defaultdict(dict)
    access = {}
    coords = {}
    def edge(a, b):
        if a == b:
            return
        distance = abs(a[0] - b[0]) + abs(a[1] - b[1])
        graph[a][b] = distance
        graph[b][a] = distance

    # Shared transfer corridors; all aisle entrances attach to these.
    x_values = {PACK[0]}
    for zone, (ox, oy, count, bays, dx, dy) in ZONE_LAYOUT.items():
        for aisle in range(1, count + 1):
            x_values.add(ox + (aisle - 1) * dx)
    x_sorted = sorted(x_values)
    for y in (CROSS_AISLE_Y, SOUTH_CROSS_Y):
        for x1, x2 in zip(x_sorted, x_sorted[1:]):
            edge((x1, y), (x2, y))
    edge(PACK, (PACK[0], CROSS_AISLE_Y))
    edge((PACK[0], CROSS_AISLE_Y), (PACK[0], SOUTH_CROSS_Y))

    for zone, (ox, oy, count, bays, dx, dy) in ZONE_LAYOUT.items():
        entrance_y = CROSS_AISLE_Y if oy == 100 else SOUTH_CROSS_Y
        for aisle in range(1, count + 1):
            x = ox + (aisle - 1) * dx
            previous = (x, entrance_y)
            for bay in range(1, bays + 1):
                point = (x, oy + (bay - 1) * dy)
                edge(previous, point)
                previous = point
    for row in locations:
        zone = row["zone_code"]
        ox, oy, _, _, dx, dy = ZONE_LAYOUT[zone]
        point = (ox + (int(row["aisle"][1:]) - 1) * dx,
                 oy + (int(row["bay"][1:]) - 1) * dy)
        coords[row["location_code"]] = point
        access[row["location_code"]] = row["access_method"]
    return graph, coords, access


def shortest_path(graph, start, finish):
    queue = [(0, start)]
    best = {start: 0}
    previous = {}
    while queue:
        distance, node = heapq.heappop(queue)
        if distance != best[node]:
            continue
        if node == finish:
            break
        for nxt, weight in graph[node].items():
            candidate = distance + weight
            if candidate < best.get(nxt, float("inf")):
                best[nxt] = candidate
                previous[nxt] = node
                heapq.heappush(queue, (candidate, nxt))
    if finish not in best:
        raise ValueError("Disconnected route: %r to %r" % (start, finish))
    nodes = [finish]
    while nodes[-1] != start:
        nodes.append(previous[nodes[-1]])
    nodes.reverse()
    return best[finish], nodes


def route(graph, coords, location_codes, optimize=False):
    """Return walking distance in feet and graph polyline; starts/ends at packing."""
    missing = [code for code in location_codes if code not in coords]
    if missing:
        raise KeyError("Unknown location(s): " + ", ".join(missing))
    remaining = list(dict.fromkeys(location_codes))
    current = PACK
    visited = [PACK]
    sequence = []
    total = 0
    while remaining:
        if optimize:
            code = min(remaining, key=lambda c: (shortest_path(graph, current, coords[c])[0], c))
        else:
            code = remaining[0]
        distance, segment = shortest_path(graph, current, coords[code])
        total += distance
        visited.extend(segment[1:])
        sequence.append(code)
        current = coords[code]
        remaining.remove(code)
    distance, segment = shortest_path(graph, current, PACK)
    total += distance
    visited.extend(segment[1:])
    return {"distance_ft": round(total, 2), "pick_sequence": sequence,
            "polyline_xy_ft": [list(p) for p in visited]}


def main():
    locations = read_locations()
    assert len(locations) == 8000
    graph, coords, access = build_network(locations)
    # One pick from each zone, illustrating multi-zone travel.
    sample = [next(row["location_code"] for row in locations if row["zone_code"] == z and row["bay"] == "B05")
              for z in ("HVY", "BLK", "SML", "SEC", "MED")]
    standard = route(graph, coords, sample)
    optimized = route(graph, coords, sample, optimize=True)
    result = {
        "scenario": "illustrative five-location pick tour",
        "units": "feet",
        "facility": "fictional conceptual aisle layout",
        "picks": sample,
        "standard": standard,
        "nearest_neighbor": optimized,
        "savings_ft": round(standard["distance_ft"] - optimized["distance_ft"], 2),
        "caveats": [
            "Nearest neighbor is a heuristic, not a globally optimal route.",
            "Access methods are metadata; forklift/pedestrian separation is not yet enforced.",
            "Dimensions and aisle spacing are conceptual, not engineering-validated.",
        ],
    }
    target = ROOT / "data" / "pick_route_demo.json"
    target.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print("Locations:", len(coords), "Graph nodes:", len(graph))
    print("Standard:", standard["distance_ft"], "ft")
    print("Nearest-neighbor:", optimized["distance_ft"], "ft")
    print("Saved:", result["savings_ft"], "ft")
    print("Wrote:", target)


if __name__ == "__main__":
    main()
