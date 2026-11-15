"""Build the dashboard data end to end.

    python -m pipeline.run_all --mode synthetic   # default, no network
    python -m pipeline.run_all --mode nasa        # cached POWER, optional add-ons

Both modes write the same five JSON contracts into ``web/data/`` and finish by
running the contract validator. Synthetic output always carries
``data_mode: "synthetic"`` so the page can show its demo banner.
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

try:
    from . import (config, export_json, fetch_imerg, fetch_ndvi, fetch_power,
                   harmonize, locations, metrics, synth, validate)
except ImportError:  # pragma: no cover - script mode
    import config
    import export_json
    import fetch_imerg
    import fetch_ndvi
    import fetch_power
    import harmonize
    import locations
    import metrics
    import synth
    import validate


def prepare_synthetic(entry: dict, refresh: bool) -> None:
    daily_path = config.RAW_DIR / f"synth_{entry['id']}.csv"
    ndvi_path = config.RAW_DIR / f"synth_ndvi_{entry['id']}.csv"
    if refresh or not daily_path.exists() or not ndvi_path.exists():
        synth.write_location(entry["id"])


def process_location(entry: dict, mode: str, refresh: bool,
                     crops: dict) -> tuple[dict | None, bool, bool]:
    """Compute one location. Returns (block, has_ndvi, has_imerg)."""
    if mode == "synthetic":
        prepare_synthetic(entry, refresh)
        daily = synth.load_daily(entry["id"])
        ndvi = synth.load_ndvi(entry["id"])
        imerg = None
    else:
        ok, message = fetch_power.ensure_location(entry, refresh)
        print(f"    POWER: {message}")
        if not ok:
            print(f'    skipped {entry["name"]}: no POWER data', file=sys.stderr)
            return None, False, False
        daily = metrics.load_power(entry["id"])
        ndvi = fetch_ndvi.load(entry["id"])
        imerg = fetch_imerg.load(entry["id"])
        if ndvi is not None:
            print(f"    NDVI: {len(ndvi)} values")
        else:
            print("    NDVI: not present; using the documented default bare share")

    table = harmonize.harmonize(daily, ndvi)
    harmonize.write_harmonized(entry["id"], table)
    block = metrics.compute_location(
        daily, crops, table, mode, config.data_years(), imerg=imerg,
    )
    return block, ndvi is not None and bool(len(ndvi)), imerg is not None


def run(mode: str = "synthetic", refresh: bool = False,
        location_ids: list[str] | None = None, verbose: bool = True) -> int:
    if mode not in ("synthetic", "nasa"):
        print("mode must be 'synthetic' or 'nasa'", file=sys.stderr)
        return 2

    started = time.perf_counter()
    config.RAW_DIR.mkdir(parents=True, exist_ok=True)
    config.DATA_DIR.mkdir(parents=True, exist_ok=True)

    entries = locations.load_locations(verbose=verbose)
    if location_ids:
        entries = [entry for entry in entries if entry["id"] in set(location_ids)]
        if not entries:
            print("No matching locations.", file=sys.stderr)
            return 2

    crops = export_json.read_json("crops.json")
    results: dict[str, dict] = {}
    has_imerg = has_ndvi = False

    total = len(entries)
    for index, entry in enumerate(entries, start=1):
        if verbose:
            print(f"[{index}/{total}] {entry['name']} ({entry['id']})")
        try:
            block, ndvi_present, imerg_present = process_location(
                entry, mode, refresh, crops,
            )
        except Exception as exc:  # noqa: BLE001 - one bad LGA must not kill the run
            print(f'    FAILED {entry["name"]}: {exc}', file=sys.stderr)
            continue
        if block is None:
            continue
        results[entry["id"]] = block
        has_ndvi = has_ndvi or ndvi_present
        has_imerg = has_imerg or imerg_present

    if not results:
        print("\nNo location produced a result. Nothing was exported.", file=sys.stderr)
        return 1

    entries = [entry for entry in entries if entry["id"] in results]
    sources = (export_json.synthetic_sources() if mode == "synthetic"
               else export_json.nasa_sources(has_imerg, has_ndvi))
    export_json.export_all(results, mode, sources, entries)
    print(f"\nExported {len(results)} location(s) in {time.perf_counter() - started:.1f}s "
          f"with data_mode='{mode}'.")

    print("\nValidating contracts:")
    errors = validate.validate_all()
    if errors:
        print(f"\nValidation failed with {len(errors)} error(s):", file=sys.stderr)
        for error in errors:
            print(f"  - {error}", file=sys.stderr)
        return 1
    print("All data contracts pass.")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("synthetic", "nasa"), default="synthetic",
                        help="synthetic demo data (default) or real NASA POWER data")
    parser.add_argument("--refresh", action="store_true",
                        help="regenerate synthetic files or re-download POWER data")
    parser.add_argument("--locations", nargs="+", metavar="ID",
                        help="only process these location ids")
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args(argv)
    return run(args.mode, args.refresh, args.locations, verbose=not args.quiet)


if __name__ == "__main__":
    raise SystemExit(main())
