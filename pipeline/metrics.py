"""Onset detection, per-crop season checks, counts and sensitivity scenarios.

All functions are pure (frame in, values out) except the small file loaders at
the bottom, so they are easy to test with hand-built rainfall.

Semantics that matter for honesty:

* ``bad_data`` years are excluded from every count and reduce ``n_total``.
* ``no_onset`` years stay in ``n_total`` and contribute zero passes to every
  crop. They are never silently dropped, which would overstate reliability.
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


# --------------------------------------------------------------------------
# Primitives
# --------------------------------------------------------------------------
def longest_run(mask) -> int:
    """Length of the longest run of truthy values."""
    best = current = 0
    for value in mask:
        current = current + 1 if bool(value) else 0
        best = max(best, current)
    return best


def find_onset(rain: pd.Series, year: int, cfg: dict | None = None) -> tuple[pd.Timestamp | None, str]:
    """Return (onset date, status). Status is 'ok', 'no_onset' or 'bad_data'.

    A false start is a qualifying 3-day total followed within the lookahead
    window by a dry run of at least ``dry_days`` days. Missing values never
    compare as dry, so gaps cannot manufacture a drought.
    """
    settings = dict(config.ONSET)
    if cfg:
        settings.update(cfg)

    start = pd.Timestamp(f"{year}-{settings['earliest']}")
    end = pd.Timestamp(f"{year}-{settings['latest']}")
    search = rain.loc[start:end]

    if len(search) == 0 or search.isna().mean() > config.MAX_MISSING_FRAC:
        return None, "bad_data"

    window_days = int(settings["window_days"])
    amount = float(settings["amount_mm"])
    dry_days = int(settings["dry_days"])
    lookahead = int(settings["lookahead_days"])

    rolling = search.rolling(window_days, min_periods=window_days).sum()
    for day, total in rolling.items():
        if not (total >= amount):  # NaN compares False
            continue
        following = rain.loc[
            day + pd.Timedelta(days=1):
            day + pd.Timedelta(days=lookahead)
        ]
        if following.empty:
            continue
        if following.isna().mean() > config.MAX_MISSING_FRAC:
            continue
        if longest_run((following < config.DRY_DAY_MM).fillna(False)) <= dry_days:
            return pd.Timestamp(day), "ok"

    return None, "no_onset"


def crop_year(df: pd.DataFrame, onset: pd.Timestamp | None, crop: dict) -> dict:
    """Evaluate one crop for one season from its onset date."""
    empty = {
        "valid": False,
        "rain_ok": False,
        "dry_ok": False,
        "heat_ok": False,
        "all_ok": False,
    }
    if onset is None:
        return empty

    cycle = int(crop["cycle_days"])
    end = onset + pd.Timedelta(days=cycle - 1)
    window = df.loc[onset:end]
    if len(window) < cycle:
        return empty  # the record ends before this crop can finish

    rain = window[RAIN]
    if rain.isna().mean() > config.MAX_MISSING_FRAC:
        return empty

    flower_start = onset + pd.Timedelta(days=round(crop["flower_frac"][0] * cycle))
    flower_end = onset + pd.Timedelta(days=round(crop["flower_frac"][1] * cycle))
    flowering = df.loc[flower_start:flower_end]
    heat_metric = crop.get("heat_metric", "tmax")
    heat_column = TMIN if heat_metric == "tmin" else TMAX
    if (flowering.empty
            or flowering[heat_column].isna().mean() > config.MAX_MISSING_FRAC
            or flowering[RAIN].isna().mean() > config.MAX_MISSING_FRAC):
        return empty

    rain_mm = float(rain.sum())
    flowering_rain = flowering[RAIN]
    dry_days = longest_run((flowering_rain < config.DRY_DAY_MM).fillna(False))
    heat_days = int((flowering[heat_column] > crop["heat_threshold_c"]).sum())

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
        "dry_days": int(dry_days),
        "heat_days": heat_days,
    }


# --------------------------------------------------------------------------
# Year-by-year aggregation
# --------------------------------------------------------------------------
def onsets_by_year(df: pd.DataFrame, cfg: dict | None = None) -> dict[int, pd.Timestamp | None]:
    years = sorted({int(year) for year in df.index.year})
    return {year: find_onset(df[RAIN], year, cfg)[0] for year in years}


def _counts(flags: list[dict], n_total: int) -> dict:
    return {
        "rain_ok": sum(1 for flag in flags if flag.get("rain_ok")),
        "dry_ok": sum(1 for flag in flags if flag.get("dry_ok")),
        "heat_ok": sum(1 for flag in flags if flag.get("heat_ok")),
        "all_ok": sum(1 for flag in flags if flag.get("all_ok")),
        "n_total": int(n_total),
    }


def _onsets_and_bad(df: pd.DataFrame, years: list[int]) -> tuple[dict, list[int], int]:
    onsets: dict[int, pd.Timestamp | None] = {}
    bad_years: list[int] = []
    for year in years:
        onset, status = find_onset(df[RAIN], year)
        if status == "bad_data":
            bad_years.append(year)
        else:
            onsets[year] = onset
    return onsets, bad_years, len(years) - len(bad_years)


def scenario_blocks(df: pd.DataFrame, crops: dict, years: list[int]) -> dict:
    """Counts for the base case and all 12 rain x temperature scenarios."""
    onsets, bad_years, n_total = _onsets_and_bad(df, years)
    blocks = {
        key: _scenario_counts(df, onsets, crops, n_total)
        for key in config.all_scenarios()
    }
    return {
        "scenarios": blocks,
        "onsets": onsets,
        "bad_years": bad_years,
        "n_total": n_total,
    }


def _scenario_counts(df: pd.DataFrame, onsets: dict[int, pd.Timestamp | None],
                     crops: dict, n_total: int) -> dict:
    out = {}
    for crop_id, crop in crops.items():
        flags = [
            crop_year(df, onset, crop) if onset is not None else {"valid": False}
            for onset in onsets.values()
        ]
        out[crop_id] = _counts(flags, n_total)
    return out


def compute_scenarios(df: pd.DataFrame, crops: dict, years: list[int]) -> dict:
    """Base scenario plus every scaled-rain / warmed scenario."""
    onsets, bad_years, n_total = _onsets_and_bad(df, years)
    scenarios = {config.BASE_SCENARIO: _scenario_counts(df, onsets, crops, n_total)}

    for multiplier in config.RAIN_MULTS:
        for delta in config.TEMP_DELTAS:
            key = config.scenario_key(multiplier, delta)
            if key == config.BASE_SCENARIO:
                continue
            adjusted = df.copy()
            adjusted[RAIN] = adjusted[RAIN] * multiplier
            adjusted[TMAX] = adjusted[TMAX] + delta
            adjusted[TMIN] = adjusted[TMIN] + delta
            adjusted_onsets, _bad, adjusted_total = _onsets_and_bad(adjusted, years)
            scenarios[key] = _scenario_counts(adjusted, adjusted_onsets, crops, adjusted_total)

    scenarios["base"] = config.BASE_SCENARIO
    return {
        "scenarios": scenarios,
        "onsets": onsets,
        "bad_years": bad_years,
        "n_total": n_total,
    }


# --------------------------------------------------------------------------
# Confidence
# --------------------------------------------------------------------------
def seasonal_total(df: pd.DataFrame, year: int) -> float | None:
    """June-September rainfall total, used for the IMERG cross-check."""
    season = df.loc[f"{year}-06-01":f"{year}-09-30", RAIN]
    if season.empty or season.isna().mean() > config.MAX_MISSING_FRAC:
        return None
    return float(season.sum())


def confidence_label(df: pd.DataFrame, years: list[int], data_mode: str,
                     imerg: pd.DataFrame | None = None) -> tuple[str, str]:
    """Return (label, one-sentence reason). Documented as a heuristic."""
    if data_mode == "synthetic":
        return (
            "Not applicable (demo data)",
            "This build is showing synthetic demo data, so a confidence label would be meaningless.",
        )

    if imerg is None or imerg.empty:
        return (
            "Medium (single source)",
            "Only NASA POWER rainfall was available, so there was no second satellite source to cross-check.",
        )

    merged = imerg.copy()
    merged["date"] = pd.to_datetime(merged["date"])
    merged = merged.set_index("date").sort_index()
    power_totals = []
    imerg_totals = []
    for year in years:
        power = seasonal_total(df, year)
        other = merged.loc[f"{year}-06-01":f"{year}-09-30", "rain_mm"]
        if power is None or other.empty or other.isna().mean() > config.MAX_MISSING_FRAC:
            continue
        power_totals.append(power)
        imerg_totals.append(float(other.sum()))

    usable = len(power_totals)
    if usable < 10 or np.std(power_totals) == 0 or np.std(imerg_totals) == 0:
        return (
            "Low",
            f"Only {usable} usable seasons could be matched between POWER and IMERG, which is too few for a reliable comparison.",
        )

    correlation = float(np.corrcoef(power_totals, imerg_totals)[0, 1])
    if correlation >= 0.7 and usable >= 15:
        return (
            "High",
            f"POWER and IMERG seasonal rainfall agreed with a correlation of {correlation:.2f} across {usable} seasons.",
        )
    if correlation >= 0.4:
        return (
            "Medium",
            f"POWER and IMERG seasonal rainfall agreed only partly (correlation {correlation:.2f} across {usable} seasons).",
        )
    return (
        "Low",
        f"POWER and IMERG seasonal rainfall disagreed (correlation {correlation:.2f} across {usable} seasons).",
    )


# --------------------------------------------------------------------------
# Whole-location result
# --------------------------------------------------------------------------
def compute_location(df: pd.DataFrame, crops: dict, harmonized: pd.DataFrame,
                     data_mode: str, years: list[int] | None = None,
                     imerg: pd.DataFrame | None = None) -> dict:
    """Compute every metric and scenario for one location."""
    from . import harmonize  # local import avoids a cycle at module load

    years = years or config.data_years()
    result = compute_scenarios(df, crops, years)
    onsets = result["onsets"]
    no_onset_years = sorted(year for year, onset in onsets.items() if onset is None)
    onset_by_year = {
        str(year): int(onset.dayofyear)
        for year, onset in sorted(onsets.items())
        if onset is not None
    }

    means = harmonize.ndvi_dekad_means(harmonized)
    share, flags = harmonize.bare_share_from_means(means)
    label, reason = confidence_label(df, years, data_mode, imerg)

    return {
        "n_total": result["n_total"],
        "no_onset_years": no_onset_years,
        "bad_data_years": sorted(result["bad_years"]),
        "confidence": label,
        "confidence_reason": reason,
        "bare_share": share,
        "ndvi_dekad": means,
        "bare_flags": flags,
        "onset_by_year": onset_by_year,
        "scenarios": result["scenarios"],
    }


# --------------------------------------------------------------------------
# File loaders used by run_all / diagnostics
# --------------------------------------------------------------------------
def load_power(location_id: str, raw_dir: Path | None = None) -> pd.DataFrame:
    path = Path(raw_dir or config.RAW_DIR) / f"power_{location_id}.csv"
    if not path.exists():
        raise FileNotFoundError(
            f"{path} is missing. Run: python -m pipeline.run_all --mode nasa --refresh"
        )
    frame = pd.read_csv(path, parse_dates=["date"], index_col="date").sort_index()
    frame = frame.replace(config.POWER_FILL_VALUE, np.nan)
    return frame


def load_synthetic(location_id: str, raw_dir: Path | None = None) -> pd.DataFrame:
    path = Path(raw_dir or config.RAW_DIR) / f"synth_{location_id}.csv"
    frame = pd.read_csv(path, comment="#", parse_dates=["date"], index_col="date")
    return frame.sort_index()


def main() -> int:
    """Quick hand check for one location (default: gombe)."""
    import json

    from . import harmonize, synth

    daily = synth.load_daily("gombe")
    table = harmonize.harmonize(daily, synth.load_ndvi("gombe"))
    with (config.DATA_DIR / "crops.json").open(encoding="utf-8") as handle:
        crops = json.load(handle)
    block = compute_location(daily, crops, table, "synthetic")
    print(f'Seasons: {block["n_total"]}, no onset: {len(block["no_onset_years"])}, '
          f'bad data: {len(block["bad_data_years"])}')
    print(f'Confidence: {block["confidence"]}')
    print(f'NDVI dekads: {0 if block["ndvi_dekad"] is None else len(block["ndvi_dekad"])}')
    for crop_id, counts in block["scenarios"][config.BASE_SCENARIO].items():
        print(f'  {crop_id:<10} all_ok {counts["all_ok"]:>2}/{counts["n_total"]}'
              f'  rain {counts["rain_ok"]:>2}  dry {counts["dry_ok"]:>2}'
              f'  heat {counts["heat_ok"]:>2}')
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
