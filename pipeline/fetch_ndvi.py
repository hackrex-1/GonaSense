"""Read a human-exported NDVI CSV for a location.

This fetcher deliberately does not call AppEEARS automatically. A human
exports MOD13Q1 16-day NDVI for the LGA point and saves it as
``raw/ndvi_<id>.csv`` with columns ``date,ndvi``. Missing files are skipped
silently; the dashboard then shows the default-bare-share note.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

try:
    from . import config, locations
except ImportError:  # pragma: no cover - script mode
    import config
    import locations


def path_for(location_id: str, raw_dir: Path | None = None) -> Path:
    return Path(raw_dir or config.RAW_DIR) / f"ndvi_{location_id}.csv"


def load(location_id: str, raw_dir: Path | None = None) -> pd.DataFrame | None:
    """Return a validated ``date, ndvi`` frame, or None when unavailable."""
    path = path_for(location_id, raw_dir)
    if not path.exists():
        return None
    try:
        frame = pd.read_csv(path, comment="#")
        frame.columns = [column.strip().lower() for column in frame.columns]
        if "date" not in frame.columns or "ndvi" not in frame.columns:
            print(f"  NDVI skipped for {location_id}: expected columns date,ndvi",
                  file=sys.stderr)
            return None
        frame["date"] = pd.to_datetime(frame["date"], errors="coerce")
        frame["ndvi"] = pd.to_numeric(frame["ndvi"], errors="coerce")
        frame = frame.dropna(subset=["date", "ndvi"]).sort_values("date")
        if frame.empty:
            return None
        # AppEEARS sometimes returns scaled integers; normalise to 0..1.
        if frame["ndvi"].max() > 1.5:
            frame["ndvi"] = frame["ndvi"] / 10000.0
        frame["ndvi"] = frame["ndvi"].clip(0.0, 1.0)
        return frame[["date", "ndvi"]].reset_index(drop=True)
    except Exception as exc:  # noqa: BLE001 - a broken export must not crash
        print(f"  NDVI skipped for {location_id}: {exc}", file=sys.stderr)
        return None


def main() -> int:
    found = 0
    for entry in locations.load_locations():
        frame = load(entry["id"])
        if frame is None:
            print(f'{entry["name"]:<14} no raw/ndvi_{entry["id"]}.csv')
        else:
            found += 1
            print(f'{entry["name"]:<14} {len(frame)} NDVI values '
                  f'({frame["date"].min().date()} to {frame["date"].max().date()})')
    print(f"\n{found} location(s) have NDVI. See HUMAN_TODO.md item 5.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
