"""Metrics core: onset, per-crop windows, pass/fail counts, scenarios.

All functions are pure (frame in, values out) except the small file loader at
the bottom, so they are easy to test with synthetic rainfall.

Rainfall onset definition (config.ONSET):
  First day on which a 3-day total reaches 20 mm and no 7-day dry run follows
  within the next 30 days, searched from 1 April to 31 October. A year with
  no qualifying day returns None and is counted as a failed season for every
  crop, never skipped.
"""

from __future__ import annotations

import json

import pandas as pd

try:  # works both as `python pipeline/metrics.py` and `python -m pipeline.metrics`
    from . import config
except ImportError:  # pragma: no cover - script mode
    import config

RAIN = "PRECTOTCORR"
TMAX = "T2M_MAX"
TMIN = "T2M_MIN"
SOIL = "GWETROOT"


def dekad_index(dates: pd.Series | pd.DatetimeIndex) -> pd.DataFrame:
    """Map dates to the 36-dekad grid (days 1-10, 11-20, 21-end of month)."""
    index = pd.DatetimeIndex(dates)
    dekad = pd.Series(((index.day - 1) // 10 + 1), index=index).clip(upper=3)  # day 31 stays in dekad 3
    return pd.DataFrame({
        "year": index.year,
        "month": index.month,
        "dekad": dekad,
        "index": (index.month - 1) * 3 + dekad,
    }, index=index)


def harmonize(daily: pd.DataFrame) -> pd.DataFrame:
    """Aggregate daily data to (year, dekad): rain sums, the rest averages."""
    if daily.empty:
        return pd.DataFrame(columns=["year", "dekad", "rain_mm", "tmax", "tmin", "soil"])

    meta = dekad_index(daily.index)
    working = daily.copy()
    working["year"] = meta["year"].to_numpy()
    working["dekad"] = meta["index"].to_numpy()

    grouped = working.groupby(["year", "dekad"], sort=True).agg(
        rain_mm=(RAIN, "sum"),
        tmax=(TMAX, "mean"),
        tmin=(TMIN, "mean"),
        soil=(SOIL, "mean"),
    )
    return grouped.reset_index()


def longest_dry_run(rain: pd.Series, dry_day_mm: float = config.DRY_DAY_MM) -> int:
    """Length in days of the longest run with rain below ``dry_day_mm``.

    Missing days break a run rather than counting as dry, so a gap can never
    manufacture a drought.
    """
    longest = 0
    current = 0
    for value in rain.to_numpy():
        if pd.isna(value):
            current = 0
        elif value < dry_day_mm:
            current += 1
            longest = max(longest, current)
        else:
            current = 0
    return int(longest)


def onset(daily: pd.DataFrame, year: int | None = None,
          params: dict | None = None) -> int | None:
    """Return the day-of-year of the first reliable onset, or None."""
    settings = dict(config.ONSET)
    if params:
        settings.update(params)

    if daily.empty:
        return None
    rain = daily[RAIN]
    year = year or int(rain.index[0].year)

    start = pd.Timestamp(f"{year}-{settings['earliest']}")
    end = pd.Timestamp(f"{year}-{settings['latest']}")
    search = rain.loc[start:end]
    if search.empty or search.isna().mean() > config.ONSET_MAX_MISSING_SHARE:
        return None

    window_days = int(settings["window_days"])
    amount = float(settings["amount_mm"])
    dry_days = int(settings["dry_days"])
    lookahead = int(settings["lookahead_days"])

    for candidate in search.index:
        window = rain.loc[candidate:candidate + pd.Timedelta(days=window_days - 1)]
        if len(window) < window_days or window.isna().any():
            continue
        if float(window.sum()) < amount:
            continue

        check = rain.loc[
            candidate + pd.Timedelta(days=1):
            candidate + pd.Timedelta(days=lookahead)
        ]
        if check.empty or check.isna().mean() > config.ONSET_MAX_MISSING_SHARE:
            continue
        if longest_dry_run(check) >= dry_days:
            continue  # false start, keep searching

        return int(candidate.dayofyear)

    return None


def onsets_by_year(daily: pd.DataFrame) -> dict[str, int | None]:
    """Onset per calendar year present in the frame."""
    years = sorted({int(year) for year in daily.index.year})
    return {str(year): onset(daily, year) for year in years}


def crop_year(daily: pd.DataFrame, onset_date: pd.Timestamp | None,
              crop: dict) -> dict:
    """Evaluate one crop in one season. Invalid seasons count as failures."""
    if onset_date is None:
        return {"valid": False}

    start = pd.Timestamp(onset_date)
    cycle = int(crop["cycle_days"])
    end = start + pd.Timedelta(days=cycle - 1)
    window = daily.loc[start:end]
    if len(window) < cycle:
        return {"valid": False}  # not enough data to cover the cycle

    rain = window[RAIN]
    if rain.isna().mean() > config.WINDOW_MAX_MISSING_SHARE:
        return {"valid": False}

    flower_start = start + pd.Timedelta(days=round(crop["flower_frac"][0] * cycle))
    flower_end = start + pd.Timedelta(days=max(0, round(crop["flower_frac"][1] * cycle) - 1))
    flower = daily.loc[flower_start:flower_end]
    if flower.empty or flower[TMAX].isna().mean() > config.WINDOW_MAX_MISSING_SHARE:
        return {"valid": False}

    rain_mm = float(rain.sum())
    dry_days = longest_dry_run(rain)
    heat_days = int((flower[TMAX] > crop["heat_threshold_c"]).sum())
    soil = window[SOIL].mean()

    rain_ok = rain_mm >= crop["min_rain_mm"]
    dry_ok = dry_days <= crop["dry_tolerance_days"]
    heat_ok = heat_days <= crop["heat_days_limit"]

    return {
        "valid": True,
        "rain_ok": bool(rain_ok),
        "dry_ok": bool(dry_ok),
        "heat_ok": bool(heat_ok),
        "all_ok": bool(rain_ok and dry_ok and heat_ok),
        "rain_mm": round(rain_mm, 1),
        "dry_days": dry_days,
        "heat_days": heat_days,
        "soil": round(float(soil), 3) if pd.notna(soil) else None,
    }


def aggregate(crop_years: list[dict], n_total: int) -> dict:
    """Turn per-year results into the counts the front end consumes."""
    valid = [result for result in crop_years if result.get("valid")]
    return {
        "rain_ok": sum(1 for result in valid if result["rain_ok"]),
        "dry_ok": sum(1 for result in valid if result["dry_ok"]),
        "heat_ok": sum(1 for result in valid if result["heat_ok"]),
        "all_ok": sum(1 for result in valid if result["all_ok"]),
        "n_valid": len(valid),
        "n_total": int(n_total),
    }


def evaluate_crop(daily: pd.DataFrame, onsets: dict[str, int | None],
                  crop: dict) -> dict:
    """Run crop_year for every onset year and aggregate the counts."""
    results = []
    for year_text, day_of_year in onsets.items():
        if day_of_year is None:
            results.append({"valid": False})
            continue
        start = pd.Timestamp(year=int(year_text), month=1, day=1) + pd.Timedelta(days=day_of_year - 1)
        results.append(crop_year(daily, start, crop))
    return aggregate(results, len(onsets))


def repeat_scenarios(daily: pd.DataFrame):
    """Yield (scenario_key, adjusted daily frame) for the rain x temperature grid."""
    for multiplier in config.RAIN_MULTS:
        for delta in config.TEMP_DELTAS:
            percent = round((multiplier - 1) * 100)
            key = f"rain{percent:+d}_temp{delta:+d}"
            frame = daily.copy()
            frame[RAIN] = frame[RAIN] * multiplier
            frame[TMAX] = frame[TMAX] + delta
            frame[TMIN] = frame[TMIN] + delta
            yield key, frame


def bare_share(ndvi_dekad: pd.DataFrame | None,
               threshold: float = config.NDVI_BARE_THRESHOLD):
    """Return (share, 36 per-dekad means, 36 shading flags) or three Nones.

    ``ndvi_dekad`` needs columns ``year, dekad, ndvi`` with dekad in 1..36.
    Bare periods run from 1 April (index 9) to 30 November (index 32).
    """
    if ndvi_dekad is None or ndvi_dekad.empty:
        return None, None, None

    frame = ndvi_dekad.dropna(subset=["ndvi"])
    means = frame.groupby("dekad")["ndvi"].mean().reindex(range(1, 37))
    values = [
        round(float(value), 3) if pd.notna(value) else None
        for value in means.to_numpy()
    ]
    flags = [
        bool(value is not None and 9 <= position <= 32 and value < threshold)
        for position, value in enumerate(values)
    ]
    share = round(sum(flags) / 24, 3)
    return share, values, flags


def compute_location(daily: pd.DataFrame, crops: dict) -> dict:
    """Compute every metric and scenario for one location."""
    onsets = onsets_by_year(daily)
    no_onset = sum(1 for value in onsets.values() if value is None)
    n_total = len(onsets)

    base = {crop_id: evaluate_crop(daily, onsets, crop) for crop_id, crop in crops.items()}
    scenarios = {config.BASE_SCENARIO: base}
    for key, frame in repeat_scenarios(daily):
        if key == config.BASE_SCENARIO:
            continue
        scenario_onsets = onsets_by_year(frame)
        scenarios[key] = {
            crop_id: evaluate_crop(frame, scenario_onsets, crop)
            for crop_id, crop in crops.items()
        }

    share, values, flags = bare_share(None)  # NDVI is a Phase 5 add-on
    return {
        "n_total": n_total,
        "n_valid": n_total - no_onset,
        "no_onset_years": no_onset,
        "bare_share": share,
        "ndvi_dekad": values,
        "bare_flags": flags,
        "onset_by_year": onsets,
        "scenarios": scenarios,
    }


def load_power(location_id: str) -> pd.DataFrame:
    """Load the cached POWER CSV for a location."""
    path = config.RAW_DIR / f"power_{location_id}.csv"
    if not path.exists():
        raise FileNotFoundError(
            f"{path} is missing. Run: python pipeline/fetch_power.py --locations {location_id}"
        )
    frame = pd.read_csv(path, parse_dates=["date"], index_col="date").sort_index()
    return frame


def main() -> int:
    """Quick hand check for one location (default: gombe)."""
    daily = load_power("gombe")
    onsets = onsets_by_year(daily)
    print(f"Gombe onsets: {onsets}")
    found = [value for value in onsets.values() if value is not None]
    print(f"Seasons with onset: {len(found)}/{len(onsets)}")
    if found:
        print(f"Median onset day-of-year: {pd.Series(found).median():.0f}")

    with (config.WEB_DATA_DIR / "crops.json").open(encoding="utf-8") as handle:
        crops = json.load(handle)
    result = compute_location(daily, crops)
    for crop_id, counts in result["scenarios"][config.BASE_SCENARIO].items():
        print(f"  {crop_id:<10} all_ok {counts['all_ok']:>2}/{counts['n_total']}"
              f"  rain {counts['rain_ok']:>2}  dry {counts['dry_ok']:>2}"
              f"  heat {counts['heat_ok']:>2}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
