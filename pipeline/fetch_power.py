"""Download NASA POWER daily data for every configured LGA centroid.

One request per location covers the whole study period. Responses are cached
as ``raw/power_<id>.csv`` and reused unless ``--refresh`` is passed. A failed
request is reported per location and never leaves a half-written cache file.

Usage:
    python -m pipeline.run_all --mode nasa          # fetch when needed
    python -m pipeline.fetch_power --refresh        # force fresh downloads
    python -m pipeline.fetch_power --locations gombe dukku
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import pandas as pd
import requests

try:
    from . import config, locations
except ImportError:  # pragma: no cover - script mode
    import config
    import locations


class PowerError(RuntimeError):
    """Raised when POWER rejects a request or returns unusable data."""


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
            response = requests.get(
                config.POWER_API, params=params,
                timeout=config.POWER_TIMEOUT_SECONDS,
            )
            response.raise_for_status()
            payload = response.json()
            if "properties" not in payload or "parameter" not in payload["properties"]:
                raise PowerError(
                    "POWER returned no parameter block. The API message was: "
                    f"{str(payload)[:300]}"
                )
            returned = set(payload["properties"]["parameter"])
            rejected = [name for name in config.POWER_PARAMS if name not in returned]
            if rejected:
                # Do not invent replacements. Record and fail loudly for safety.
                raise PowerError(
                    f"POWER rejected parameter(s) {rejected}. "
                    "Check the POWER parameter documentation and update "
                    "config.POWER_PARAMS plus HUMAN_TODO.md."
                )
            return payload
        except Exception as exc:  # noqa: BLE001 - report and retry any failure
            last_error = exc
            print(f"    attempt {attempt}/{retries} failed: {exc}", file=sys.stderr)
            if attempt < retries:
                time.sleep(2 * attempt)
    raise PowerError(f"POWER download failed after {retries} attempts") from last_error


def payload_to_frame(payload: dict) -> pd.DataFrame:
    """Turn the POWER parameter mapping into a tidy daily DataFrame."""
    parameters = payload["properties"]["parameter"]
    frame = pd.DataFrame(parameters)
    if frame.empty:
        raise PowerError("POWER returned no parameter data")
    frame.index = pd.to_datetime(frame.index, format="%Y%m%d")
    frame.index.name = "date"
    frame = frame.sort_index()
    frame = frame.replace(config.POWER_FILL_VALUE, float("nan"))
    for column in frame.columns:
        frame[column] = pd.to_numeric(frame[column], errors="coerce")
    return frame


def report_missing(frame: pd.DataFrame) -> None:
    share = {column: float(frame[column].isna().mean()) for column in frame.columns}
    summary = ", ".join(f"{column} {value:.1%}" for column, value in share.items())
    print(f"    rows {len(frame)}, missing: {summary}")
    for column, value in share.items():
        if value > config.POWER_MAX_MISSING_SHARE:
            print(f"    WARNING: {column} is {value:.1%} missing "
                  f"(above {config.POWER_MAX_MISSING_SHARE:.0%}); "
                  "those days are excluded by the missing-data rule.",
                  file=sys.stderr)


def read_cached(path: Path) -> pd.DataFrame:
    frame = pd.read_csv(path, parse_dates=["date"], index_col="date")
    return frame.sort_index()


def ensure_location(entry: dict, refresh: bool = False) -> tuple[bool, str]:
    """Make sure one location has a cached CSV. Returns (ok, message)."""
    target = config.RAW_DIR / f"power_{entry['id']}.csv"
    if target.exists() and not refresh:
        try:
            report_missing(read_cached(target))
            return True, f"cached {target.name}"
        except Exception as exc:  # noqa: BLE001 - corrupt cache is refetched
            print(f"    cache unreadable ({exc}); downloading again", file=sys.stderr)

    start = f"{config.YEARS[0]}0101"
    end = f"{config.YEARS[1]}1231"
    payload = fetch_location(entry["lat"], entry["lon"], start, end)
    frame = payload_to_frame(payload)
    if frame.empty:
        return False, "POWER returned an empty frame"
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_suffix(".csv.part")
    frame.to_csv(temporary, index=True)
    temporary.replace(target)
    report_missing(frame)
    return True, f"saved {target.name}"


def download_all(location_ids: list[str] | None = None, refresh: bool = False) -> int:
    """Download every requested location. Returns the number of failures."""
    entries = locations.load_locations(verbose=True)
    known = {entry["id"]: entry for entry in entries}
    wanted = location_ids or list(known)
    unknown = [loc for loc in wanted if loc not in known]
    if unknown:
        print(f"Unknown location id(s): {', '.join(unknown)}", file=sys.stderr)
        print(f"Known ids: {', '.join(known)}", file=sys.stderr)
        return len(unknown)

    failures = 0
    for index, location_id in enumerate(wanted, start=1):
        entry = known[location_id]
        print(f"[{index}/{len(wanted)}] {entry['name']} "
              f"({entry['lat']:.4f}, {entry['lon']:.4f})")
        try:
            ok, message = ensure_location(entry, refresh)
            print(f"    {message}")
            if not ok:
                failures += 1
        except Exception as exc:  # noqa: BLE001 - keep going, report at the end
            failures += 1
            print(f"    FAILED: {exc}", file=sys.stderr)
        if index < len(wanted):
            time.sleep(config.POWER_PAUSE_SECONDS)
    return failures


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--locations", nargs="+", metavar="ID",
                        help="only fetch these location ids (default: all)")
    parser.add_argument("--refresh", "--force", dest="refresh", action="store_true",
                        help="re-download even when a cached CSV exists")
    args = parser.parse_args(argv)
    failures = download_all(args.locations, args.refresh)
    if failures:
        print(f"\n{failures} location(s) failed.", file=sys.stderr)
        return 1
    print("\nAll requested locations are cached in raw/.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
