"""Crop-year, aggregation, scenario and harmonization tests."""

import math

import pandas as pd

from pipeline import config, metrics


def season_rain(daily, start="2001-05-01", end="2001-08-20", amount=6.0):
    for date in pd.date_range(start, end, freq="D"):
        daily.loc[date, "PRECTOTCORR"] = amount
    return daily


def test_crop_passes_when_all_limits_are_met(make_daily, crop):
    daily = season_rain(make_daily())
    result = metrics.crop_year(daily, pd.Timestamp("2001-05-01"), crop)

    assert result["valid"] is True
    assert result["rain_ok"] and result["dry_ok"] and result["heat_ok"]
    assert result["all_ok"] is True
    assert result["rain_mm"] >= crop["min_rain_mm"]
    assert result["heat_days"] == 0


def test_crop_fails_on_heat_during_flowering(make_daily, crop):
    daily = season_rain(make_daily(tmax=40.0))
    result = metrics.crop_year(daily, pd.Timestamp("2001-05-01"), crop)

    assert result["valid"] is True
    assert result["heat_ok"] is False
    assert result["all_ok"] is False


def test_crop_fails_on_season_rain(make_daily, crop):
    daily = season_rain(make_daily(), amount=1.0)
    result = metrics.crop_year(daily, pd.Timestamp("2001-05-01"), crop)

    assert result["rain_ok"] is False
    assert result["rain_mm"] < crop["min_rain_mm"]


def test_crop_fails_on_long_dry_spell(make_daily, crop):
    daily = make_daily()
    for date in pd.date_range("2001-05-01", "2001-08-08", freq="15D"):
        daily.loc[date, "PRECTOTCORR"] = 80.0
    result = metrics.crop_year(daily, pd.Timestamp("2001-05-01"), crop)

    assert result["rain_ok"] is True
    assert result["dry_ok"] is False
    assert result["dry_days"] > crop["dry_tolerance_days"]


def test_missing_onset_counts_as_a_failed_season(make_daily, crop):
    daily = make_daily()
    result = metrics.crop_year(daily, None, crop)

    assert result == {"valid": False}


def test_longest_dry_run_breaks_on_missing_days():
    rain = pd.Series([0.0, 0.0, float("nan"), 0.0, 0.0, 0.0])
    assert metrics.longest_dry_run(rain) == 3


def test_aggregate_counts_only_valid_years(make_daily, crop):
    results = [
        {"valid": True, "rain_ok": True, "dry_ok": True, "heat_ok": True, "all_ok": True},
        {"valid": True, "rain_ok": False, "dry_ok": True, "heat_ok": True, "all_ok": False},
        {"valid": False},
    ]
    counts = metrics.aggregate(results, 3)

    assert counts == {
        "rain_ok": 1, "dry_ok": 2, "heat_ok": 2, "all_ok": 1,
        "n_valid": 2, "n_total": 3,
    }


def test_every_scenario_is_generated(make_daily):
    daily = make_daily()
    scenarios = dict(metrics.repeat_scenarios(daily))

    assert len(scenarios) == 12
    assert set(scenarios) == set(config.all_scenarios())
    assert config.BASE_SCENARIO in scenarios

    low_hot = scenarios["rain-20_temp+2"]
    assert math.isclose(low_hot["PRECTOTCORR"].sum(), 0.0)
    assert (low_hot["T2M_MAX"] == daily["T2M_MAX"] + 2).all()
    assert (low_hot["T2M_MIN"] == daily["T2M_MIN"] + 2).all()


def test_scenario_rain_is_scaled(make_daily):
    daily = season_rain(make_daily(), start="2001-01-01", end="2001-12-31", amount=4.0)
    scenarios = dict(metrics.repeat_scenarios(daily))

    wetter = scenarios["rain+10_temp+0"]
    assert math.isclose(wetter["PRECTOTCORR"].sum(), daily["PRECTOTCORR"].sum() * 1.1)


def test_harmonize_builds_36_dekads(make_daily):
    daily = season_rain(make_daily(), start="2001-01-01", end="2001-01-31", amount=1.0)
    daily = daily.loc["2001-01-01":"2001-01-31"]

    dekads = metrics.harmonize(daily)

    assert len(dekads) == 3
    assert list(dekads["dekad"]) == [1, 2, 3]
    assert list(dekads["rain_mm"]) == [10.0, 10.0, 11.0]
    assert list(dekads["tmax"]) == [32.0, 32.0, 32.0]


def test_bare_share_flags_the_april_to_november_window():
    rows = [
        {"year": 2001, "dekad": dekad, "ndvi": 0.2 if 10 <= dekad <= 15 else 0.6}
        for dekad in range(1, 37)
    ]
    share, values, flags = metrics.bare_share(pd.DataFrame(rows))

    assert len(values) == 36 and len(flags) == 36
    assert sum(flags) == 6
    assert share == round(6 / 24, 3)


def test_bare_share_is_null_without_ndvi():
    assert metrics.bare_share(None) == (None, None, None)


def test_compute_location_has_every_scenario(make_daily, crop):
    events = {f"2001-05-{day:02d}": 10.0 for day in (1, 2, 3)}
    for date in pd.date_range("2001-05-04", "2001-09-30", freq="3D"):
        events[date] = 15.0
    daily = make_daily(events=events)

    result = metrics.compute_location(daily, {"maize": crop})

    assert result["n_total"] == 1
    assert result["no_onset_years"] == 0
    assert set(result["scenarios"]) == set(config.all_scenarios())
    assert result["scenarios"][config.BASE_SCENARIO]["maize"]["all_ok"] == 1
