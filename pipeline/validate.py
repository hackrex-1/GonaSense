"""Contract checks for the exported JSON in ``web/data/``.

Run standalone (``python pipeline/validate.py``) or let
``export_json.py`` call :func:`validate_all` as its last step.

Checks:
  * all five data files exist and parse, with no NaN/Infinity literals
  * location ids are unique and metrics cover every location
  * every crop referenced by a strategy exists in crops.json
  * every location has every scenario key from config
  * counts never exceed n_total and are never negative
  * onset values are day-of-year integers (or null)
  * total JSON payload stays under 5 MB

Exit code is 0 when clean and 1 when any error is found.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

try:
    from . import config
except ImportError:  # pragma: no cover - script mode
    import config

REQUIRED_FILES = ("locations.json", "crops.json", "strategies.json",
                  "metrics.json", "glossary.json")
MAX_TOTAL_BYTES = 5 * 1024 * 1024
COUNT_KEYS = ("rain_ok", "dry_ok", "heat_ok", "all_ok")


def _reject_constant(value: str):
    raise ValueError(f"invalid JSON constant {value!r} (use null instead)")


def load_json(path: Path):
    """Load JSON, rejecting NaN/Infinity so browsers never see invalid JSON."""
    with path.open(encoding="utf-8") as handle:
        return json.load(handle, parse_constant=_reject_constant)


def validate_all(data_dir: Path | None = None) -> list[str]:
    """Return a list of human-readable errors. Empty means the contract holds."""
    data_dir = Path(data_dir or config.WEB_DATA_DIR)
    errors: list[str] = []
    loaded: dict[str, object] = {}
    total_bytes = 0

    for filename in REQUIRED_FILES:
        path = data_dir / filename
        if not path.exists():
            errors.append(f"missing file: {filename}")
            continue
        total_bytes += path.stat().st_size
        try:
            loaded[filename] = load_json(path)
            print(f"  ok  {filename} ({path.stat().st_size / 1024:.1f} KB)")
        except Exception as exc:  # noqa: BLE001 - collect every problem
            errors.append(f"{filename}: cannot parse ({exc})")

    if errors:
        return errors

    locations = loaded["locations.json"]
    crops = loaded["crops.json"]
    strategies = loaded["strategies.json"]
    metrics = loaded["metrics.json"]
    glossary = loaded["glossary.json"]

    # ---- locations -------------------------------------------------------
    if not isinstance(locations, list) or not locations:
        errors.append("locations.json must be a non-empty array")
        locations = []
    location_ids: list[str] = []
    for entry in locations:
        if not isinstance(entry, dict):
            errors.append("locations.json entries must be objects")
            continue
        for key in ("id", "name", "lat", "lon", "confidence"):
            if key not in entry:
                errors.append(f"location {entry.get('id', '?')}: missing '{key}'")
        location_ids.append(entry.get("id"))
    if len(set(location_ids)) != len(location_ids):
        errors.append("locations.json contains duplicate ids")

    # ---- crops -----------------------------------------------------------
    if not isinstance(crops, dict) or not crops:
        errors.append("crops.json must be a non-empty object keyed by crop id")
        crops = {}
    for crop_id, crop in crops.items():
        for key in ("name", "cycle_days", "min_rain_mm", "dry_tolerance_days",
                    "heat_threshold_c", "heat_days_limit", "flower_frac",
                    "family", "water", "n_fixing", "cover", "market"):
            if key not in crop:
                errors.append(f"crop {crop_id}: missing '{key}'")
        frac = crop.get("flower_frac")
        if not (isinstance(frac, list) and len(frac) == 2
                and 0 <= frac[0] < frac[1] <= 1):
            errors.append(f"crop {crop_id}: flower_frac must be [start, end] in 0..1")

    # ---- strategies ------------------------------------------------------
    if not isinstance(strategies, list) or not strategies:
        errors.append("strategies.json must be a non-empty array")
        strategies = []
    for strategy in strategies:
        sid = strategy.get("id", "?") if isinstance(strategy, dict) else "?"
        for key in ("id", "name", "sequence", "benefits", "gaps", "risks"):
            if key not in strategy:
                errors.append(f"strategy {sid}: missing '{key}'")
        for crop_id in strategy.get("sequence", []):
            if crop_id not in crops:
                errors.append(f"strategy {sid}: unknown crop '{crop_id}'")

    # ---- metrics ---------------------------------------------------------
    if not isinstance(metrics, dict) or not metrics:
        errors.append("metrics.json must be a non-empty object keyed by location id")
        metrics = {}
    expected_scenarios = set(config.all_scenarios())
    for location_id in location_ids:
        if location_id not in metrics:
            errors.append(f"metrics: no entry for location '{location_id}'")
            continue
        block = metrics[location_id]
        n_total = block.get("n_total")
        if not isinstance(n_total, int) or n_total <= 0:
            errors.append(f"metrics.{location_id}: n_total must be a positive integer")
            continue
        scenarios = block.get("scenarios", {})
        missing = expected_scenarios - set(scenarios)
        if missing:
            errors.append(f"metrics.{location_id}: missing scenarios {sorted(missing)}")
        for scenario_key, by_crop in scenarios.items():
            if not isinstance(by_crop, dict):
                errors.append(f"metrics.{location_id}.{scenario_key}: expected an object")
                continue
            for crop_id, counts in by_crop.items():
                if crop_id not in crops:
                    errors.append(f"metrics.{location_id}.{scenario_key}: unknown crop '{crop_id}'")
                for key in COUNT_KEYS:
                    value = counts.get(key)
                    if not isinstance(value, int) or value < 0:
                        errors.append(
                            f"metrics.{location_id}.{scenario_key}.{crop_id}.{key}: "
                            f"expected a non-negative integer"
                        )
                    elif value > n_total:
                        errors.append(
                            f"metrics.{location_id}.{scenario_key}.{crop_id}.{key}: "
                            f"{value} exceeds n_total {n_total}"
                        )
        for year, onset in block.get("onset_by_year", {}).items():
            if onset is None:
                continue
            if not isinstance(onset, int) or not 1 <= onset <= 366:
                errors.append(f"metrics.{location_id}.onset_by_year[{year}]: invalid onset {onset!r}")
        ndvi = block.get("ndvi_dekad")
        flags = block.get("bare_flags")
        if ndvi is not None and (not isinstance(ndvi, list) or len(ndvi) != 36):
            errors.append(f"metrics.{location_id}.ndvi_dekad: expected 36 values or null")
        if flags is not None:
            if not isinstance(flags, list) or len(flags) != 36:
                errors.append(f"metrics.{location_id}.bare_flags: expected 36 booleans or null")
            elif any(not isinstance(flag, bool) for flag in flags):
                errors.append(f"metrics.{location_id}.bare_flags: values must be booleans")

    # ---- glossary --------------------------------------------------------
    if not isinstance(glossary, list) or not glossary:
        errors.append("glossary.json must be a non-empty array")
    else:
        for entry in glossary:
            if not isinstance(entry, dict) or "term" not in entry or "plain" not in entry:
                errors.append("glossary entries need 'term' and 'plain'")

    # ---- payload size ----------------------------------------------------
    if total_bytes > MAX_TOTAL_BYTES:
        errors.append(
            f"total JSON is {total_bytes / 1024 / 1024:.2f} MB, over the 5 MB budget"
        )

    return errors


def main() -> int:
    print(f"Validating {config.WEB_DATA_DIR}")
    try:
        errors = validate_all()
    except Exception as exc:  # noqa: BLE001 - a crash should read as a failure
        print(f"validation crashed: {exc}", file=sys.stderr)
        return 1
    if errors:
        print(f"\n{len(errors)} error(s):", file=sys.stderr)
        for error in errors:
            print(f"  - {error}", file=sys.stderr)
        return 1
    print("\nAll data contracts pass.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
