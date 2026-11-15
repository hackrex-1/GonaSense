"""Onset detection tests using hand-built rainfall (plan section 14)."""

import pandas as pd

from pipeline import metrics


def test_known_onset_is_found(make_daily):
    events = {f"2001-05-{day}": 10.0 for day in (20, 21, 22)}
    for date in pd.date_range("2001-05-23", "2001-09-30", freq="3D"):
        events[date] = 5.0

    daily = make_daily(events=events)
    onset, status = metrics.find_onset(daily["PRECTOTCORR"], 2001)

    # The 3-day window that reaches 20 mm ends on 21 May (day 141).
    assert status == "ok"
    assert onset.dayofyear == 141


def test_false_start_is_rejected_and_later_onset_found(make_daily):
    # A 30 mm burst on 10-12 April, then nothing until 1 July.
    events = {f"2001-04-{day}": 10.0 for day in (10, 11, 12)}
    events.update({f"2001-07-{day}": 10.0 for day in (1, 2, 3)})
    for date in pd.date_range("2001-07-04", "2001-10-15", freq="3D"):
        events[date] = 5.0

    daily = make_daily(events=events)
    onset, status = metrics.find_onset(daily["PRECTOTCORR"], 2001)

    # The April burst is followed by a long dry spell, so it is rejected.
    # The first reliable 3-day window ends on 2 July (day 183).
    assert status == "ok"
    assert onset.dayofyear == 183


def test_no_qualifying_rain_returns_no_onset(make_daily):
    onset, status = metrics.find_onset(make_daily()["PRECTOTCORR"], 2001)
    assert onset is None
    assert status == "no_onset"


def test_year_with_too_much_missing_rain_is_bad_data(make_daily):
    events = {date: 5.0 for date in pd.date_range("2001-05-20", "2001-09-30", freq="3D")}
    daily = make_daily(events=events)

    # Blank every sixth day from April to October: about 17% missing.
    search = daily.loc["2001-04-01":"2001-10-31"].index[::6]
    daily.loc[search, "PRECTOTCORR"] = float("nan")

    onset, status = metrics.find_onset(daily["PRECTOTCORR"], 2001)
    assert onset is None
    assert status == "bad_data"


def test_missing_onset_counts_as_a_failed_season(make_daily, crop):
    daily = make_daily()
    result = metrics.crop_year(daily, None, crop)
    assert result["valid"] is False
    assert result["all_ok"] is False
