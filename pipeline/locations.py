"""Local government areas of Gombe State and their point coordinates.

Preferred source: the geoBoundaries NGA ADM2 release (gbOpen, GRID3 2022),
filtered to Gombe State with the GADM 4.1 level-2 state mask. Centroids are
area-weighted polygon centroids computed below, not typed coordinates.

If neither raw boundary file is present (for example on a fresh checkout with
no downloads), the approximate seed from the build specification is used and
every location is flagged ``approximate seed``. Those coordinates must never
be presented as surveyed.
"""

from __future__ import annotations

import io
import json
import math
import zipfile
from pathlib import Path

try:
    from . import config
except ImportError:  # pragma: no cover - script mode
    import config

BOUNDARY_FILE = "geoBoundaries-NGA-ADM2_simplified.geojson"
STATE_FILE = "gadm41_NGA_2.json.zip"
STATE_NAME = "Gombe"

COORDS_STATUS_BOUNDARY = (
    "area-weighted centroid of the geoBoundaries NGA ADM2 boundary "
    "(GRID3 2022 release), inside the GADM 4.1 Gombe mask"
)
COORDS_STATUS_FALLBACK = "approximate seed, replace with boundary centroids"

# Display-name fixes applied after matching boundary names.
DISPLAY_NAMES = {"Shomgom": "Shongom", "Yamaltu/Deba": "Yamaltu/Deba"}

# Guyuk is an Adamawa LGA whose simplified boundary and centroid graze the
# Gombe state mask. It is excluded so the tool never claims an out-of-state LGA.
EXCLUDED_NAMES = {"Guyuk"}

# Build-specification fallback (section 7). Only used when no boundary file
# is available; coordinates are approximate and must stay flagged.
FALLBACK_LOCATIONS = {
    "gombe": ("Gombe", 10.29, 11.17),
    "akko": ("Akko", 10.28, 10.95),
    "kaltungo": ("Kaltungo", 9.81, 11.31),
    "dukku": ("Dukku", 10.82, 10.77),
    "nafada": ("Nafada", 11.10, 11.33),
    "kwami": ("Kwami", 10.45, 10.97),
}


def slugify(name: str) -> str:
    return name.lower().replace(" ", "-").replace("/", "-")


# --------------------------------------------------------------------------
# Geometry helpers (standard library only, no geopandas requirement)
# --------------------------------------------------------------------------
def outer_rings(geometry: dict) -> list[list[list[float]]]:
    if geometry["type"] == "Polygon":
        return [geometry["coordinates"][0]]
    return [polygon[0] for polygon in geometry["coordinates"]]


def point_in_ring(point: tuple[float, float], ring: list[list[float]]) -> bool:
    x, y = point
    inside = False
    for (x1, y1), (x2, y2) in zip(ring, ring[1:] + ring[:1]):
        if (y1 > y) != (y2 > y):
            crossing = (x2 - x1) * (y - y1) / (y2 - y1) + x1
            if x < crossing:
                inside = not inside
    return inside


def inside_any(point: tuple[float, float], rings: list[list[list[float]]]) -> bool:
    return any(point_in_ring(point, ring) for ring in rings)


def ring_area_centroid(ring: list[list[float]]) -> tuple[float, float, float]:
    """Area and centroid of a lon/lat ring, weighted by cos(latitude)."""
    lat0 = sum(point[1] for point in ring) / len(ring)
    scale = math.cos(math.radians(lat0))
    twice_area = cx = cy = 0.0
    for (x0, y0), (x1, y1) in zip(ring, ring[1:] + ring[:1]):
        x0 *= scale
        x1 *= scale
        cross = x0 * y1 - x1 * y0
        twice_area += cross
        cx += (x0 + x1) * cross
        cy += (y0 + y1) * cross
    if twice_area == 0:
        return 0.0, 0.0, 0.0
    return abs(twice_area) / 2.0, cx / (3 * twice_area) / scale, cy / (3 * twice_area)


def centroid(feature: dict) -> tuple[float, float]:
    total = cx = cy = 0.0
    for ring in outer_rings(feature["geometry"]):
        area, x, y = ring_area_centroid(ring)
        total += area
        cx += x * area
        cy += y * area
    if total == 0:
        raise ValueError("boundary has zero area")
    return round(cy / total, 4), round(cx / total, 4)


# --------------------------------------------------------------------------
# Boundary loading
# --------------------------------------------------------------------------
def load_state_rings(raw_dir: Path | None = None) -> list[list[list[float]]]:
    path = Path(raw_dir or config.RAW_DIR) / STATE_FILE
    with zipfile.ZipFile(path) as archive:
        name = next(n for n in archive.namelist() if n.endswith(".json"))
        payload = json.load(io.TextIOWrapper(archive.open(name), encoding="utf-8"))
    rings: list[list[list[float]]] = []
    for feature in payload["features"]:
        if feature["properties"].get("NAME_1") == STATE_NAME:
            rings.extend(outer_rings(feature["geometry"]))
    return rings


def build_from_boundaries(raw_dir: Path | None = None) -> list[dict]:
    """Compute one centroid per Gombe LGA from the raw boundary files."""
    raw = Path(raw_dir or config.RAW_DIR)
    state_rings = load_state_rings(raw)
    with (raw / BOUNDARY_FILE).open(encoding="utf-8") as handle:
        geo = json.load(handle)

    locations = []
    for feature in geo["features"]:
        name = feature["properties"].get("shapeName", "")
        if not name or name in EXCLUDED_NAMES:
            continue
        lat, lon = centroid(feature)
        if not inside_any((lon, lat), state_rings):
            continue
        display = DISPLAY_NAMES.get(name, name)
        locations.append({
            "id": slugify(display),
            "name": display,
            "lat": lat,
            "lon": lon,
            "coords_status": COORDS_STATUS_BOUNDARY,
        })

    locations.sort(key=lambda entry: entry["name"].lower())
    return locations


def fallback_locations() -> list[dict]:
    return [
        {
            "id": location_id,
            "name": name,
            "lat": lat,
            "lon": lon,
            "coords_status": COORDS_STATUS_FALLBACK,
        }
        for location_id, (name, lat, lon) in FALLBACK_LOCATIONS.items()
    ]


def load_locations(raw_dir: Path | None = None, verbose: bool = False) -> list[dict]:
    """Return the location list, preferring boundary centroids."""
    raw = Path(raw_dir or config.RAW_DIR)
    if (raw / BOUNDARY_FILE).exists() and (raw / STATE_FILE).exists():
        try:
            locations = build_from_boundaries(raw)
            if locations:
                if verbose:
                    print(f"  {len(locations)} LGA centroids from boundary files")
                return locations
        except Exception as exc:  # noqa: BLE001 - fall back, never crash
            print(f"  boundary centroid build failed ({exc}); using seed coordinates")
    if verbose:
        print("  boundary files missing; using approximate seed coordinates")
    return fallback_locations()


def location_map(raw_dir: Path | None = None) -> dict[str, dict]:
    return {entry["id"]: entry for entry in load_locations(raw_dir)}


def main() -> int:
    for entry in load_locations(verbose=True):
        print(f'{entry["id"]:14s} {entry["name"]:14s} {entry["lat"]:.4f}, {entry["lon"]:.4f}')
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
