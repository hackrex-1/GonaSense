"""Optional SMAP surface soil moisture fetcher and reader.

Requires ``earthaccess`` plus Earthdata credentials and ``xarray``/``h5netcdf``.
The SMAP record starts around 2015, so early years have no SMAP value. Without
credentials or packages the pipeline prints a skip message and continues.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pandas as pd

try:
    from . import config, locations
except ImportError:  # pragma: no cover - script mode
    import config
    import locations

PRODUCT = "SPL3SMP"
VERSION = "008"
FIRST_YEAR = 2015
BOX_DEGREES = 0.36  # SMAP's 36 km footprint


def path_for(location_id: str, raw_dir: Path | None = None) -> Path:
    return Path(raw_dir or config.RAW_DIR) / f"smap_{location_id}.csv"


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


def download(entry: dict, refresh: bool = False) -> bool:
    target = path_for(entry["id"])
    if target.exists() and not refresh:
        print(f"    SMAP cached: {target.name}")
        return True
    if not credentials_available():
        print("SMAP skipped: no credentials.")
        return False
    earthaccess = _import_earthaccess()
    if earthaccess is None:
        print("SMAP skipped: earthaccess is not installed.")
        return False
    try:
        import xarray as xr
    except Exception:  # noqa: BLE001
        print("SMAP skipped: xarray is not installed.")
        return False

    lat, lon = entry["lat"], entry["lon"]
    half = BOX_DEGREES / 2
    try:
        earthaccess.login(strategy="environment", persist=False)
        granules = earthaccess.search_data(
            short_name=PRODUCT,
            version=VERSION,
            bounding_box=(lon - half, lat - half, lon + half, lat + half),
            temporal=(f"{max(FIRST_YEAR, config.YEARS[0])}-01-01",
                      f"{config.YEARS[1]}-12-31"),
        )
        if not granules:
            print("SMAP skipped: the search returned no granules.")
            return False
        files = earthaccess.download(granules, str(config.RAW_DIR / "smap"))
        rows = []
        for path in files:
            with xr.open_dataset(path, decode_times=True) as dataset:
                variable = next(
                    (name for name in ("soil_moisture", "sm_surface")
                     if name in dataset.data_vars),
                    None,
                )
                if variable is None:
                    continue
                subset = dataset[variable].sel(
                    lat=slice(lat - half, lat + half),
                    lon=slice(lon - half, lon + half),
                )
                rows.append({
                    "date": pd.Timestamp(dataset["time"].values[0]).normalize(),
                    "sm": round(float(subset.mean(skipna=True)), 4),
                })
        if not rows:
            return False
        frame = pd.DataFrame(rows).groupby("date", as_index=False)["sm"].mean()
        frame.to_csv(target, index=False)
        print(f"    SMAP saved: {target.name} ({len(frame)} days)")
        return True
    except Exception as exc:  # noqa: BLE001
        print(f"SMAP skipped: download failed ({exc})", file=sys.stderr)
        return False


def load(location_id: str, raw_dir: Path | None = None) -> pd.DataFrame | None:
    path = path_for(location_id, raw_dir)
    if not path.exists():
        return None
    try:
        frame = pd.read_csv(path, comment="#")
        frame.columns = [column.strip().lower() for column in frame.columns]
        if "date" not in frame.columns or "sm" not in frame.columns:
            return None
        frame["date"] = pd.to_datetime(frame["date"], errors="coerce")
        frame["sm"] = pd.to_numeric(frame["sm"], errors="coerce")
        frame = frame.dropna(subset=["date", "sm"]).sort_values("date")
        return frame.reset_index(drop=True) if not frame.empty else None
    except Exception as exc:  # noqa: BLE001
        print(f"  SMAP unreadable for {location_id}: {exc}", file=sys.stderr)
        return None


def main() -> int:
    if not credentials_available():
        print("SMAP skipped: no credentials. See HUMAN_TODO.md item 4.")
        return 0
    for entry in locations.load_locations():
        download(entry)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
