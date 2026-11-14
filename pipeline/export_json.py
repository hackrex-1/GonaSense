"""Build the frozen JSON contracts in ``web/data/`` from cached raw data.

Run:
    python pipeline/fetch_power.py      # once, fills raw/
    python pipeline/export_json.py      # writes metrics + locations, validates

Crops, strategies and glossary are research-owned source files; this script
reads them and never overwrites them.
"""

from __future__ import annotations

import json
import time

try:
    from . import config, metrics, validate
except ImportError:  # pragma: no cover - script mode
    import config
    import metrics
    import validate

DEFAULT_CONFIDENCE = "Medium (single source)"


def read_json(name: str):
    path = config.WEB_DATA_DIR / name
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def write_json(name: str, payload) -> None:
    path = config.WEB_DATA_DIR / name
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=1, ensure_ascii=False, allow_nan=False)
        handle.write("\n")


def build_locations() -> list[dict]:
    """Build locations.json, preserving confidence labels from a previous run."""
    previous = {}
    path = config.WEB_DATA_DIR / "locations.json"
    if path.exists():
        try:
            previous = {entry["id"]: entry for entry in read_json("locations.json")}
        except Exception:  # noqa: BLE001 - a broken file should not block export
            previous = {}

    return [
        {
            "id": location_id,
            "name": name,
            "lat": lat,
            "lon": lon,
            "confidence": previous.get(location_id, {}).get("confidence", DEFAULT_CONFIDENCE),
        }
        for location_id, (name, lat, lon) in config.LOCATIONS.items()
    ]


def main() -> int:
    started = time.perf_counter()
    config.WEB_DATA_DIR.mkdir(parents=True, exist_ok=True)

    crops = read_json("crops.json")
    read_json("strategies.json")   # parsed here so a bad file fails before compute
    read_json("glossary.json")

    locations = build_locations()
    write_json("locations.json", locations)

    results = {}
    total = len(config.LOCATIONS)
    for index, (location_id, (name, _lat, _lon)) in enumerate(config.LOCATIONS.items(), start=1):
        print(f"[{index}/{total}] {name}")
        try:
            daily = metrics.load_power(location_id)
        except FileNotFoundError as exc:
            print(f"    {exc}")
            return 1
        result = metrics.compute_location(daily, crops)
        results[location_id] = result
        base = result["scenarios"][config.BASE_SCENARIO]
        maize = base.get("maize", {})
        print(
            f"    onsets {result['n_valid']}/{result['n_total']}"
            f"  maize all_ok {maize.get('all_ok', 0)}/{maize.get('n_total', 0)}"
        )

    write_json("metrics.json", results)

    errors = validate.validate_all()
    elapsed = time.perf_counter() - started
    if errors:
        print(f"\nExport finished in {elapsed:.1f}s but validation failed:", flush=True)
        for error in errors:
            print(f"  - {error}")
        return 1

    print(f"\nExport valid: {len(results)} locations in {elapsed:.1f}s.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
