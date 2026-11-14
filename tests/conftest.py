import pandas as pd
import pytest


@pytest.fixture
def make_daily():
    """Build a synthetic daily POWER-shaped frame for one year."""

    def _make(year=2001, events=None, tmax=32.0, tmin=22.0, soil=0.4):
        index = pd.date_range(f"{year}-01-01", f"{year}-12-31", freq="D")
        frame = pd.DataFrame({
            "PRECTOTCORR": 0.0,
            "T2M_MAX": float(tmax),
            "T2M_MIN": float(tmin),
            "GWETROOT": float(soil),
        }, index=index)
        for date, amount in (events or {}).items():
            frame.loc[pd.Timestamp(date), "PRECTOTCORR"] = float(amount)
        return frame

    return _make


@pytest.fixture
def crop():
    """A local crop definition, independent of the researched crop table."""
    return {
        "cycle_days": 100,
        "min_rain_mm": 450,
        "dry_tolerance_days": 10,
        "heat_threshold_c": 35,
        "heat_days_limit": 4,
        "flower_frac": [0.4, 0.6],
    }
