"""Metrics core: onset, per-crop windows, pass/fail counts, scenarios.

PHASE 2 - NOT IMPLEMENTED YET.

This module will expose the functions the rest of the pipeline (and the
tests) depend on. The signatures are fixed now so ``export_json.py`` and the
tests can be written against them.

Contract with the rest of the pipeline:

    onset(daily) -> int | None
        Day-of-year of the first reliable rainy-season start, or None.

    crop_year(daily, onset_doy, crop) -> dict
        {"valid": bool, "rain_ok": bool, "dry_ok": bool,
         "heat_ok": bool, "soil": float | None}

    aggregate(crop_years) -> dict
        {"n_total", "n_valid", "rain_ok", "dry_ok", "heat_ok", "all_ok"}

    bare_share(daily_ndvi) -> tuple[float, list[float], list[bool]]
        Share of bare dekads, the 36-dekad means, and the 36 shading flags.

    repeat_scenarios(daily) -> iterator of (scenario_key, daily_frame)

All derived series are keyed by (location, year, dekad); see section 4.4 of
the implementation plan.
"""

from __future__ import annotations

import pandas as pd


def dekad_index(dates: pd.Series | pd.DatetimeIndex) -> pd.DataFrame:
    """Map dates to the 36-dekad grid (days 1-10, 11-20, 21-end of month)."""
    index = pd.DatetimeIndex(dates)
    dekad = ((index.day - 1) // 10) + 1
    return pd.DataFrame({
        "year": index.year,
        "month": index.month,
        "dekad": dekad,
        "index": (index.month - 1) * 3 + dekad,
    }, index=index)


def harmonize(daily: pd.DataFrame) -> pd.DataFrame:
    """Aggregate daily rain (sum) and temperature/soil (mean) into dekads."""
    raise NotImplementedError("Phase 2: implement dekad harmonization")


def onset(daily: pd.DataFrame) -> int | None:
    """Detect the rainfall onset, or return None for a failed season."""
    raise NotImplementedError("Phase 2: implement onset detection")


def longest_dry_run(rain: pd.Series, dry_day_mm: float) -> int:
    """Length in days of the longest run with rain below ``dry_day_mm``."""
    raise NotImplementedError("Phase 2: implement dry-spell counting")


def crop_year(daily: pd.DataFrame, onset_doy: int, crop: dict) -> dict:
    """Evaluate one crop in one season, following plan section 5.3."""
    raise NotImplementedError("Phase 2: implement crop-year evaluation")


def aggregate(crop_years: list[dict], n_total: int) -> dict:
    """Turn per-year results into the counts the front end consumes."""
    raise NotImplementedError("Phase 2: implement aggregation")


def bare_share(ndvi_dekad: pd.DataFrame, threshold: float) -> tuple:
    """Compute the bare-field share, per-dekad means and shading flags."""
    raise NotImplementedError("Phase 2: implement bare-field share")


def repeat_scenarios(daily: pd.DataFrame):
    """Yield (scenario_key, adjusted_daily_frame) for rain x temperature."""
    raise NotImplementedError("Phase 2: implement the scenario loop")


def main() -> int:
    raise SystemExit(
        "pipeline/metrics.py is a Phase 2 module and is not implemented yet.\n"
        "The web/data mock contracts exist so front-end work can start in parallel."
    )


if __name__ == "__main__":
    raise SystemExit(main())
