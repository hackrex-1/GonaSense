"""Harmonize daily weather and 16-day NDVI onto one (year, dekad) grid.

A dekad is days 1-10, 11-20 or 21-end of month, so there are 36 per year.
Rain is summed; temperature and soil moisture are averaged. NDVI is
interpolated to daily values and then averaged per dekad. The tidy table is
written to ``raw/harmonized_<id>.csv`` and is the only source used for the
36-value NDVI series in the dashboard.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

try:
    from . import config
except ImportError:  # pragma: no cover - script mode
    import config

RAIN = "PRECTOTCORR"
TMAX = "T2M_MAX"
TMIN = "T2M_MIN"
SOIL = "GWETROOT"


def dekad_index(date) -> int:
    """Map a date to the 1..36 dekad grid."""
    stamp = pd.Timestamp(date)
    block = min((stamp.day - 1) // 10 + 1, 3)
    return (stamp.month - 1) * 3 + block


def dekad_start(year: int, index: int) -> pd.Timestamp:
    """First day of a 1..36 dekad index."""
    month = (index - 1) // 3 + 1
    block = (index - 1) % 3
    day = (1, 11, 21)[block]
    return pd.Timestamp(year=year, month=month, day=day)


def bare_dekads() -> list[int]:
    """Dekad indices inside BARE_SEASON (1 April - 30 November) -> 24 values."""
    start = pd.Timestamp(f"2001-{config.BARE_SEASON[0]}")
    end = pd.Timestamp(f"2001-{config.BARE_SEASON[1]}")
    first = dekad_index(start)
    last = dekad_index(end)
    return list(range(first, last + 1))


def _groupby_dekad(series: pd.Series, how: str) -> pd.Series:
    index = pd.DatetimeIndex(series.index)
    keys = pd.MultiIndex.from_arrays([
        index.year,
        [dekad_index(stamp) for stamp in index],
    ], names=["year", "dekad"])
    grouped = pd.Series(series.to_numpy(), index=keys)
    return grouped.groupby(level=["year", "dekad"]).agg(how)


def harmonize_daily(daily: pd.DataFrame) -> pd.DataFrame:
    """Aggregate daily columns to (year, dekad)."""
    if daily.empty:
        return pd.DataFrame(columns=["year", "dekad", "rain_mm", "tmax", "tmin", "soil"])

    frame = pd.DataFrame({
        "rain_mm": _groupby_dekad(daily[RAIN], "sum"),
        "tmax": _groupby_dekad(daily[TMAX], "mean"),
        "tmin": _groupby_dekad(daily[TMIN], "mean"),
        "soil": _groupby_dekad(daily[SOIL], "mean"),
    }).reset_index()
    return frame


def harmonize_ndvi(ndvi: pd.DataFrame | None) -> pd.DataFrame:
    """Interpolate NDVI to daily values, then average per (year, dekad)."""
    if ndvi is None or ndvi.empty:
        return pd.DataFrame(columns=["year", "dekad", "ndvi"])

    series = (
        ndvi.assign(date=pd.to_datetime(ndvi["date"]))
        .dropna(subset=["ndvi"])
        .sort_values("date")
        .set_index("date")["ndvi"]
    )
    if series.empty:
        return pd.DataFrame(columns=["year", "dekad", "ndvi"])

    daily = (
        series.resample("D").mean()
        .interpolate(method="time", limit_direction="both")
        .clip(lower=0.0, upper=1.0)
    )
    frame = _groupby_dekad(daily, "mean").rename("ndvi").reset_index()
    return frame


def harmonize(daily: pd.DataFrame, ndvi: pd.DataFrame | None = None) -> pd.DataFrame:
    """Build the complete (year, dekad) table for one location."""
    table = harmonize_daily(daily)
    green = harmonize_ndvi(ndvi)
    if green.empty:
        table["ndvi"] = np.nan
    else:
        table = table.merge(green, on=["year", "dekad"], how="left")
    return table.sort_values(["year", "dekad"]).reset_index(drop=True)


def write_harmonized(location_id: str, table: pd.DataFrame,
                     raw_dir: Path | None = None) -> Path:
    raw = Path(raw_dir or config.RAW_DIR)
    raw.mkdir(parents=True, exist_ok=True)
    path = raw / f"harmonized_{location_id}.csv"
    table.to_csv(path, index=False, float_format="%.4f")
    return path


def load_harmonized(location_id: str, raw_dir: Path | None = None) -> pd.DataFrame:
    raw = Path(raw_dir or config.RAW_DIR)
    return pd.read_csv(raw / f"harmonized_{location_id}.csv")


def ndvi_dekad_means(table: pd.DataFrame) -> list[float | None] | None:
    """Mean NDVI for each of the 36 dekads, or None when NDVI is absent."""
    if table is None or table.empty or "ndvi" not in table.columns:
        return None
    values = table.dropna(subset=["ndvi"])
    if values.empty:
        return None
    means = values.groupby("dekad")["ndvi"].mean().reindex(range(1, 37))
    return [round(float(value), 3) if pd.notna(value) else None for value in means]


def bare_share_from_means(means: list[float | None] | None,
                          threshold: float = config.NDVI_BARE_THRESHOLD) -> tuple[float | None, list[bool] | None]:
    """Share of BARE_SEASON dekads below the bare threshold, plus 36 flags."""
    if not means:
        return None, None
    window = set(bare_dekads())
    flags = [
        bool(index in window and value is not None and value < threshold)
        for index, value in enumerate(means, start=1)
    ]
    share = round(sum(flags) / len(window), 3)
    return share, flags


def main() -> int:
    from . import locations, synth

    for entry in locations.load_locations():
        table = harmonize(synth.load_daily(entry["id"]), synth.load_ndvi(entry["id"]))
        path = write_harmonized(entry["id"], table)
        print(f'{entry["name"]:<14} {len(table):>4} rows -> {path.name}')
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
