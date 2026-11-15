"""Optional GPM IMERG daily precipitation fetcher and reader.

Requires ``earthaccess`` and Earthdata credentials (``EARTHDATA_USERNAME`` /
``EARTHDATA_PASSWORD`` or ``~/.netrc``). Without them it prints a clear skip
message and the pipeline falls back to "Medium (single source)" confidence.
Importable and runnable with none of the optional packages installed.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

import pandas as pd

try:
    from . import config, locations
except ImportError:  # pragma: no cover - script mode
    import config
    import locations

PRODUCT = "GPM_3IMERGDF"
VERSION = "07"
BOX_DEGREES = 0.25  # a small box around the LGA point
DEFAULT_YEARS = 10


def path_for(location_id: str, raw_dir: Path | None = None) -> Path:
    return Path(raw_dir or config.RAW_DIR) / f"imerg_{location_id}.csv"


def credentials_available() -> bool:
    if os.environ.get("EARTHDATA_USERNAME") and os.environ.get("EARTHDATA_PASSWORD"):
        return True
    return (Path.home() / ".netrc").exists()


def _import_earthaccess():
    try:
        import earthaccess  # noqa: F401
        return earthaccess
    except Exception:  # noqa: BLE001 - optional dependency
        return None


def download(entry: dict, refresh: bool = False,
             start_year: int | None = None,
             end_year: int | None = None) -> bool:
    """Download IMERG daily rain for one LGA. False means skipped."""
    target = path_for(entry["id"])
    if target.exists() and not refresh:
        print(f"    IMERG cached: {target.name}")
        return True
    if not credentials_available():
        print("IMERG skipped: no credentials (set EARTHDATA_USERNAME and "
              "EARTHDATA_PASSWORD or a ~/.netrc entry).")
        return False
    earthaccess = _import_earthaccess()
    if earthaccess is None:
        print("IMERG skipped: earthaccess is not installed "
              "(pip install earthaccess xarray h5netcdf).")
        return False
    try:
        import xarray as xr
    except Exception:  # noqa: BLE001
        print("IMERG skipped: xarray is not installed.")
        return False

    lat, lon = entry["lat"], entry["lon"]
    half = BOX_DEGREES / 2
    start_year = start_year or max(config.YEARS[0], config.YEARS[1] - DEFAULT_YEARS + 1)
    end_year = end_year or config.YEARS[1]
    try:
        earthaccess.login(strategy="environment", persist=False)
        print(f"    IMERG searching {start_year}-{end_year} for {entry['name']}...",
              flush=True)
        granules = earthaccess.search_data(
            short_name=PRODUCT,
            version=VERSION,
            bounding_box=(lon - half, lat - half, lon + half, lat + half),
            temporal=(f"{start_year}-01-01", f"{end_year}-12-31"),
        )
        if not granules:
            print("IMERG skipped: the search returned no granules.")
            return False
        print(f"    IMERG found {len(granules)} granules; downloading...", flush=True)
        files = earthaccess.download(
            granules, str(config.RAW_DIR / "imerg"), show_progress=True,
        )
        print(f"    IMERG downloaded {len(files)} files; extracting daily rain...",
              flush=True)
        rows = []
        for index, path in enumerate(files, start=1):
            with xr.open_dataset(path, decode_times=True) as dataset:
                variable = next(
                    (name for name in ("precipitation", "precipitationCal")
                     if name in dataset.data_vars),
                    None,
                )
                if variable is None:
                    continue
                subset = dataset[variable].sel(
                    lat=slice(lat - half, lat + half),
                    lon=slice(lon - half, lon + half),
                )
                value = float(subset.mean(skipna=True))
                stamp = pd.Timestamp(dataset["time"].values[0]).normalize()
                rows.append({"date": stamp, "rain_mm": round(value, 3)})
            if index % 100 == 0 or index == len(files):
                print(f"    IMERG processed {index}/{len(files)} files", flush=True)
        if not rows:
            return False
        frame = pd.DataFrame(rows).groupby("date", as_index=False)["rain_mm"].sum()
        frame.to_csv(target, index=False)
        print(f"    IMERG saved: {target.name} ({len(frame)} days)")
        return True
    except Exception as exc:  # noqa: BLE001 - optional source must not crash a run
        print(f"IMERG skipped: download failed ({exc})", file=sys.stderr)
        return False


def load(location_id: str, raw_dir: Path | None = None) -> pd.DataFrame | None:
    """Return ``date, rain_mm`` for the confidence cross-check, or None."""
    path = path_for(location_id, raw_dir)
    if not path.exists():
        return None
    try:
        frame = pd.read_csv(path, comment="#")
        frame.columns = [column.strip().lower() for column in frame.columns]
        if "date" not in frame.columns or "rain_mm" not in frame.columns:
            return None
        frame["date"] = pd.to_datetime(frame["date"], errors="coerce")
        frame["rain_mm"] = pd.to_numeric(frame["rain_mm"], errors="coerce")
        frame = frame.dropna(subset=["date", "rain_mm"]).sort_values("date")
        return frame.reset_index(drop=True) if not frame.empty else None
    except Exception as exc:  # noqa: BLE001
        print(f"  IMERG unreadable for {location_id}: {exc}", file=sys.stderr)
        return None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    default_start = max(config.YEARS[0], config.YEARS[1] - DEFAULT_YEARS + 1)
    parser.add_argument("--start-year", type=int, default=default_start,
                        help=f"first data year (default: {default_start})")
    parser.add_argument("--end-year", type=int, default=config.YEARS[1],
                        help=f"last data year (default: {config.YEARS[1]})")
    parser.add_argument("--locations", nargs="+", metavar="ID",
                        help="location ids to fetch (default: all configured locations)")
    parser.add_argument("--refresh", action="store_true",
                        help="replace existing cached IMERG CSVs")
    args = parser.parse_args()
    if (args.start_year < config.YEARS[0] or args.end_year > config.YEARS[1]
            or args.start_year > args.end_year):
        parser.error(f"year range must be within {config.YEARS[0]}-{config.YEARS[1]}")

    entries = locations.load_locations()
    if not credentials_available():
        print("IMERG skipped: no credentials. See HUMAN_TODO.md item 4.")
        return 0
    known = {entry["id"]: entry for entry in entries}
    selected = args.locations or list(known)
    unknown = [location_id for location_id in selected if location_id not in known]
    if unknown:
        parser.error(f"unknown location id(s): {', '.join(unknown)}")
    for index, location_id in enumerate(selected, start=1):
        entry = known[location_id]
        print(f"[{index}/{len(selected)}] {entry['name']} ({location_id})", flush=True)
        download(entry, args.refresh, args.start_year, args.end_year)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
