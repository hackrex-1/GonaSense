"""Contract checks for the exported JSON in ``web/data/``.

Run standalone with ``python -m pipeline.validate`` or let ``run_all.py`` call
:func:`validate_all` as its last step. Exit code is 0 only when every check
passes, which makes it safe to use in CI.
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

try:
    from . import config
except ImportError:  # pragma: no cover - script mode
    import config

REQUIRED_FILES = ("locations.json", "crops.json", "strategies.json",
                  "metrics.json", "glossary.json")
COUNT_KEYS = ("rain_ok", "dry_ok", "heat_ok", "all_ok")
CROP_KEYS = ("name", "family", "cycle_days", "min_rain_mm", "dry_tolerance_days",
             "heat_metric", "heat_threshold_c", "heat_days_limit", "flower_frac",
             "water", "n_fixing", "cover", "market", "field_status",
             "provisional", "source_status")
SCORE_KEYS = ("water", "n_fixing", "cover", "market")
FIELD_STATUSES = {"confirmed", "derived", "estimate"}
FIELD_STATUS_KEYS = {
    "cycle_days", "min_rain_mm", "dry_tolerance_days", "heat_metric",
    "heat_threshold_c", "heat_days_limit", "flower_frac", "water",
    "n_fixing", "cover", "market",
}


def _reject_constant(value: str):
    raise ValueError(f"invalid JSON constant {value!r} (use null instead)")


def load_json(path: Path):
    """Load JSON, rejecting NaN/Infinity so browsers never receive invalid JSON."""
    with path.open(encoding="utf-8") as handle:
        return json.load(handle, parse_constant=_reject_constant)


def _finite(value, path: str, errors: list[str]) -> None:
    if isinstance(value, float) and not math.isfinite(value):
        errors.append(f"{path}: non-finite number")
    elif isinstance(value, dict):
        for key, item in value.items():
            _finite(item, f"{path}.{key}", errors)
    elif isinstance(value, list):
        for index, item in enumerate(value):
            _finite(item, f"{path}[{index}]", errors)


def validate_all(data_dir: Path | None = None) -> list[str]:
    """Return a list of human-readable errors. Empty means the contract holds."""
    directory = Path(data_dir or config.DATA_DIR)
    errors: list[str] = []
    loaded: dict[str, object] = {}
    total_bytes = 0

    for filename in REQUIRED_FILES:
        path = directory / filename
        if not path.exists():
            errors.append(f"missing file: {filename}")
            continue
        total_bytes += path.stat().st_size
        try:
            loaded[filename] = load_json(path)
            _finite(loaded[filename], filename, errors)
        except Exception as exc:  # noqa: BLE001 - collect every problem
            errors.append(f"{filename}: cannot parse ({exc})")

    if errors:
        return errors

    if total_bytes > config.MAX_DATA_BYTES:
        errors.append(
            f"web/data is {total_bytes / 1024 / 1024:.2f} MB, over the 5 MB budget"
        )

    location_entries = loaded["locations.json"]
    crops = loaded["crops.json"]
    strategies = loaded["strategies.json"]
    metrics = loaded["metrics.json"]
    glossary = loaded["glossary.json"]

    # ---- locations -------------------------------------------------------
    if not isinstance(location_entries, list) or not location_entries:
        errors.append("locations.json must be a non-empty array")
        location_entries = []
    location_ids: list[str] = []
    for entry in location_entries:
        if not isinstance(entry, dict):
            errors.append("locations.json entries must be objects")
            continue
        for key in ("id", "name", "lat", "lon", "coords_status"):
            if key not in entry:
                errors.append(f"location {entry.get('id', '?')}: missing '{key}'")
        lat, lon = entry.get("lat"), entry.get("lon")
        if not (isinstance(lat, (int, float)) and -90 <= lat <= 90):
            errors.append(f"location {entry.get('id', '?')}: latitude out of range")
        if not (isinstance(lon, (int, float)) and -180 <= lon <= 180):
            errors.append(f"location {entry.get('id', '?')}: longitude out of range")
        if not entry.get("coords_status"):
            errors.append(f"location {entry.get('id', '?')}: empty coords_status")
        location_ids.append(entry.get("id"))
    if len(set(location_ids)) != len(location_ids):
        errors.append("locations.json contains duplicate ids")

    # ---- crops -----------------------------------------------------------
    if not isinstance(crops, dict) or not crops:
        errors.append("crops.json must be a non-empty object keyed by crop id")
        crops = {}
    for crop_id, crop in crops.items():
        if not isinstance(crop, dict):
            errors.append(f"crop {crop_id}: must be an object")
            continue
        for key in CROP_KEYS:
            if key not in crop:
                errors.append(f"crop {crop_id}: missing '{key}'")
        frac = crop.get("flower_frac")
        if not (isinstance(frac, list) and len(frac) == 2
                and isinstance(frac[0], (int, float)) and isinstance(frac[1], (int, float))
                and 0 <= frac[0] < frac[1] <= 1):
            errors.append(f"crop {crop_id}: flower_frac must be [start, end] in 0..1")
        if not isinstance(crop.get("provisional"), bool):
            errors.append(f"crop {crop_id}: provisional must be true or false")
        if crop.get("family") not in ("cereal", "legume"):
            errors.append(f"crop {crop_id}: family must be cereal or legume")
        if crop.get("heat_metric") not in ("tmax", "tmin"):
            errors.append(f"crop {crop_id}.heat_metric: must be tmax or tmin")
        field_status = crop.get("field_status")
        if not isinstance(field_status, dict):
            errors.append(f"crop {crop_id}.field_status: must be an object")
        else:
            missing_statuses = FIELD_STATUS_KEYS - field_status.keys()
            unknown_statuses = field_status.keys() - FIELD_STATUS_KEYS
            if missing_statuses:
                errors.append(
                    f"crop {crop_id}.field_status: missing statuses for "
                    f"{', '.join(sorted(missing_statuses))}"
                )
            if unknown_statuses:
                errors.append(
                    f"crop {crop_id}.field_status: unknown fields "
                    f"{', '.join(sorted(unknown_statuses))}"
                )
            for field, status in field_status.items():
                if status not in FIELD_STATUSES:
                    errors.append(
                        f"crop {crop_id}.field_status.{field}: "
                        "must be confirmed, derived or estimate"
                    )
        for key in SCORE_KEYS:
            value = crop.get(key)
            if not isinstance(value, (int, float)) or not 0 <= value <= 1:
                errors.append(f"crop {crop_id}.{key}: must be a number in 0..1")
        for key in ("cycle_days", "min_rain_mm", "dry_tolerance_days",
                    "heat_threshold_c", "heat_days_limit"):
            if not isinstance(crop.get(key), (int, float)) or crop.get(key) <= 0:
                errors.append(f"crop {crop_id}.{key}: must be a positive number")

    # ---- strategies ------------------------------------------------------
    if not isinstance(strategies, list) or not strategies:
        errors.append("strategies.json must be a non-empty array")
        strategies = []
    seen_strategies: list[str] = []
    for strategy in strategies:
        sid = strategy.get("id", "?") if isinstance(strategy, dict) else "?"
        seen_strategies.append(sid)
        for key in ("id", "name", "sequence", "benefits", "gaps", "risks"):
            if key not in strategy:
                errors.append(f"strategy {sid}: missing '{key}'")
        sequence = strategy.get("sequence", [])
        if not isinstance(sequence, list) or not sequence:
            errors.append(f"strategy {sid}: sequence must be a non-empty array")
        for crop_id in sequence if isinstance(sequence, list) else []:
            if crop_id not in crops:
                errors.append(f"strategy {sid}: unknown crop '{crop_id}'")
        for key in ("benefits", "gaps", "risks"):
            if not isinstance(strategy.get(key), list) or not strategy.get(key):
                errors.append(f"strategy {sid}: '{key}' must be a non-empty array")
    if len(set(seen_strategies)) != len(seen_strategies):
        errors.append("strategies.json contains duplicate ids")

    # ---- glossary --------------------------------------------------------
    if not isinstance(glossary, list) or not glossary:
        errors.append("glossary.json must be a non-empty array")
    else:
        for entry in glossary:
            if not isinstance(entry, dict) or not entry.get("term") or not entry.get("plain"):
                errors.append("glossary entries need non-empty 'term' and 'plain'")

    # ---- metrics ---------------------------------------------------------
    if not isinstance(metrics, dict) or not metrics:
        errors.append("metrics.json must be a non-empty object")
        metrics = {}

    if metrics.get("data_mode") not in ("synthetic", "nasa"):
        errors.append("metrics.data_mode must be 'synthetic' or 'nasa'")
    if not isinstance(metrics.get("years"), list) or metrics.get("years") != list(config.YEARS):
        errors.append(f"metrics.years must be {list(config.YEARS)}")
    if not isinstance(metrics.get("generated"), str) or not metrics.get("generated"):
        errors.append("metrics.generated must be a date string")
    if not isinstance(metrics.get("sources_used"), list) or not metrics.get("sources_used"):
        errors.append("metrics.sources_used must be a non-empty array")

    blocks = metrics.get("locations")
    if not isinstance(blocks, dict) or not blocks:
        errors.append("metrics.locations must be a non-empty object")
        blocks = {}

    expected = set(config.all_scenarios())
    for location_id in location_ids:
        if location_id not in blocks:
            errors.append(f"metrics: no entry for location '{location_id}'")
            continue
        block = blocks[location_id]
        n_total = block.get("n_total")
        if not isinstance(n_total, int) or n_total <= 0:
            errors.append(f"metrics.{location_id}: n_total must be a positive integer")
            continue

        for key in ("no_onset_years", "bad_data_years"):
            value = block.get(key)
            if not isinstance(value, list) or any(
                    not isinstance(year, int) or year not in config.data_years()
                    for year in value):
                errors.append(f"metrics.{location_id}.{key}: must be a list of study years")
        if len(block.get("no_onset_years", [])) + len(block.get("bad_data_years", [])) > len(config.data_years()):
            errors.append(f"metrics.{location_id}: more flagged years than study years")
        if not isinstance(block.get("confidence"), str) or not block.get("confidence"):
            errors.append(f"metrics.{location_id}.confidence: must be a non-empty string")
        if not isinstance(block.get("confidence_reason"), str) or not block.get("confidence_reason"):
            errors.append(f"metrics.{location_id}.confidence_reason: must be a non-empty string")

        bare_share = block.get("bare_share")
        if bare_share is not None and not (isinstance(bare_share, (int, float)) and 0 <= bare_share <= 1):
            errors.append(f"metrics.{location_id}.bare_share: expected a number in 0..1 or null")

        ndvi = block.get("ndvi_dekad")
        flags = block.get("bare_flags")
        if ndvi is not None:
            if not isinstance(ndvi, list) or len(ndvi) != 36:
                errors.append(f"metrics.{location_id}.ndvi_dekad: expected 36 values or null")
            elif any(value is not None and not (isinstance(value, (int, float)) and 0 <= value <= 1)
                     for value in ndvi):
                errors.append(f"metrics.{location_id}.ndvi_dekad: values must be 0..1 or null")
        if flags is not None:
            if not isinstance(flags, list) or len(flags) != 36:
                errors.append(f"metrics.{location_id}.bare_flags: expected 36 booleans or null")
            elif any(not isinstance(flag, bool) for flag in flags):
                errors.append(f"metrics.{location_id}.bare_flags: values must be booleans")
        if (ndvi is None) != (flags is None):
            errors.append(f"metrics.{location_id}: ndvi_dekad and bare_flags must both be null or both present")

        onset_by_year = block.get("onset_by_year")
        if not isinstance(onset_by_year, dict):
            errors.append(f"metrics.{location_id}.onset_by_year: must be an object")
        else:
            for year, day in onset_by_year.items():
                if not (isinstance(year, str) and year.isdigit() and int(year) in config.data_years()):
                    errors.append(f"metrics.{location_id}.onset_by_year: bad year key {year!r}")
                if not isinstance(day, int) or not 1 <= day <= 366:
                    errors.append(f"metrics.{location_id}.onset_by_year[{year}]: invalid day")

        scenarios = block.get("scenarios")
        if not isinstance(scenarios, dict):
            errors.append(f"metrics.{location_id}.scenarios: must be an object")
            continue

        base = scenarios.get("base")
        if base != config.BASE_SCENARIO:
            errors.append(f"metrics.{location_id}: scenarios.base must be '{config.BASE_SCENARIO}'")
        missing = expected - set(scenarios)
        if missing:
            errors.append(f"metrics.{location_id}: missing scenarios {sorted(missing)}")
        extra = set(scenarios) - expected - {"base"}
        if extra:
            errors.append(f"metrics.{location_id}: unexpected scenarios {sorted(extra)}")

        for scenario_key, by_crop in scenarios.items():
            if scenario_key == "base":
                continue
            if not isinstance(by_crop, dict):
                errors.append(f"metrics.{location_id}.{scenario_key}: expected an object")
                continue
            if not set(crops) <= set(by_crop):
                errors.append(
                    f"metrics.{location_id}.{scenario_key}: missing crops "
                    f"{sorted(set(crops) - set(by_crop))}"
                )
            for crop_id, counts in by_crop.items():
                if crop_id not in crops:
                    errors.append(f"metrics.{location_id}.{scenario_key}: unknown crop '{crop_id}'")
                    continue
                values = {}
                for key in COUNT_KEYS:
                    value = counts.get(key)
                    values[key] = value
                    if not isinstance(value, int) or isinstance(value, bool):
                        errors.append(
                            f"metrics.{location_id}.{scenario_key}.{crop_id}.{key}: "
                            "expected a non-negative integer"
                        )
                    elif value < 0 or value > n_total:
                        errors.append(
                            f"metrics.{location_id}.{scenario_key}.{crop_id}.{key}: "
                            f"{value} outside 0..n_total ({n_total})"
                        )
                if counts.get("n_total") != n_total:
                    errors.append(
                        f"metrics.{location_id}.{scenario_key}.{crop_id}.n_total: "
                        "must equal the location n_total"
                    )
                if all(isinstance(values[key], int) for key in COUNT_KEYS):
                    if values["all_ok"] > min(values["rain_ok"], values["dry_ok"], values["heat_ok"]):
                        errors.append(
                            f"metrics.{location_id}.{scenario_key}.{crop_id}: "
                            "all_ok cannot exceed the smallest single-condition count"
                        )

    return errors


def main() -> int:
    print(f"Validating {config.DATA_DIR}")
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
