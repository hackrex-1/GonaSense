"""Download NASA POWER daily data for every configured LGA centroid.

One request per location covers the full period in ``config.YEARS``.
Responses are cached in ``raw/power_<id>.csv`` and reused on later runs
unless ``--force`` is passed.

Usage:
    python pipeline/fetch_power.py
    python pipeline/fetch_power.py --locations gombe dukku
    python pipeline/fetch_power.py --force

Requires: pandas, requests
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import pandas as pd
import requests

try:  # works both as `python pipeline/fetch_power.py` and `python -m pipeline.fetch_power`
    from . import config
except ImportError:  # pragma: no cover - script mode
    import config


def fetch_location(lat: float, lon: float, start: str, end: str,
                   retries: int = config.POWER_RETRIES) -> dict:
    """Call the POWER point API with a small retry loop."""
    params = {
        "parameters": ",".join(config.POWER_PARAMS),
        "community": config.POWER_COMMUNITY,
        "latitude": lat,
        "longitude": lon,
        "start": start,
        "end": end,
        "format": "JSON",
    }
    last_error: Exception | None = None
    for attempt in range(1, retries + 1):
        try:
            response = requests.get(config.POWER_API, params=params, timeout=120)
            response.raise_for_status()
            payload = response.json()
            if "properties" not in payload:
                raise ValueError(f"unexpected POWER payload: {str(payload)[:200]}")
            return payload
        except Exception as exc:  # noqa: BLE001 - report and retry any failure
            last_error = exc
            print(f"    attempt {attempt}/{retries} failed: {exc}", file=sys.stderr)
            if attempt < retries:
                time.sleep(2 * attempt)
    raise RuntimeError(f"POWER download failed after {retries} attempts") from last_error


def payload_to_frame(payload: dict) -> pd.DataFrame:
    """Turn the POWER parameter mapping into a tidy daily DataFrame."""
    parameters = payload["properties"]["parameter"]
    frame = pd.DataFrame(parameters)
    if frame.empty:
        raise ValueError("POWER returned no parameter data")
    frame.index = pd.to_datetime(frame.index, format="%Y%m%d")
    frame.index.name = "date"
    frame = frame.sort_index()
    frame = frame.replace(config.POWER_FILL_VALUE, float("nan"))
    for column in frame.columns:
        frame[column] = pd.to_numeric(frame[column], errors="coerce")
    return frame


def report_missing(frame: pd.DataFrame) -> None:
    """Print the share of missing values and warn above the configured limit."""
    print(f"    rows: {len(frame)}  span: {frame.index.min().date()} -> {frame.index.max().date()}")
    for column in frame.columns:
        share = float(frame[column].isna().mean())
        flag = "  <-- above limit" if share > config.POWER_MAX_MISSING_SHARE else ""
        print(f"    missing {column:<12} {share:6.2%}{flag}")


def read_cached(path: Path) -> pd.DataFrame:
    """Read a cached CSV, restoring the date index."""
    frame = pd.read_csv(path, parse_dates=["date"], index_col="date")
    return frame.sort_index()


def download_all(location_ids: list[str] | None = None, force: bool = False) -> int:
    """Download every requested location. Returns the number of failures."""
    config.RAW_DIR.mkdir(parents=True, exist_ok=True)
    start = f"{config.YEARS[0]}0101"
    end = f"{config.YEARS[1]}1231"

    wanted = location_ids or list(config.LOCATIONS)
    unknown = [loc for loc in wanted if loc not in config.LOCATIONS]
    if unknown:
        print(f"Unknown location id(s): {', '.join(unknown)}", file=sys.stderr)
        print(f"Known ids: {', '.join(config.LOCATIONS)}", file=sys.stderr)
        return len(unknown)

    failures = 0
    for index, location_id in enumerate(wanted, start=1):
        name, lat, lon = config.LOCATIONS[location_id]
        target = config.RAW_DIR / f"power_{location_id}.csv"
        print(f"[{index}/{len(wanted)}] {name} ({lat:.4f}, {lon:.4f})")

        if target.exists() and not force:
            try:
                report_missing(read_cached(target))
                print(f"    cached: {target.relative_to(config.BASE_DIR)} (use --force to refresh)")
                continue
            except Exception as exc:  # noqa: BLE001 - corrupt cache should be refetched
                print(f"    cache unreadable ({exc}); downloading again", file=sys.stderr)

        try:
            payload = fetch_location(lat, lon, start, end)
            frame = payload_to_frame(payload)
            frame.to_csv(target, index=True)
            report_missing(frame)
            print(f"    saved: {target.relative_to(config.BASE_DIR)}")
        except Exception as exc:  # noqa: BLE001 - keep going, report at the end
            failures += 1
            print(f"    FAILED: {exc}", file=sys.stderr)

        if index < len(wanted):
            time.sleep(config.POWER_PAUSE_SECONDS)

    return failures


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--locations", nargs="+", metavar="ID",
        help="only fetch these location ids (default: all configured)",
    )
    parser.add_argument(
        "--force", action="store_true",
        help="re-download even when a cached CSV exists",
    )
    args = parser.parse_args(argv)

    failures = download_all(args.locations, args.force)
    if failures:
        print(f"\n{failures} location(s) failed.", file=sys.stderr)
        return 1
    print("\nAll requested locations are cached in raw/.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
