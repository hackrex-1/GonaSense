"""The validator must reject deliberately broken contracts."""

import json

from pipeline import validate


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def write(path, payload):
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_valid_dataset_passes(dataset):
    assert validate.validate_all(dataset) == []


def test_count_above_n_total_fails(dataset):
    metrics = read(dataset / "metrics.json")
    metrics["locations"]["gombe"]["scenarios"]["rain+0_temp+0"]["maize"]["all_ok"] = 11
    write(dataset / "metrics.json", metrics)

    errors = validate.validate_all(dataset)
    assert any("outside 0..n_total" in error for error in errors)


def test_missing_scenario_key_fails(dataset):
    metrics = read(dataset / "metrics.json")
    del metrics["locations"]["gombe"]["scenarios"]["rain-10_temp+1"]
    write(dataset / "metrics.json", metrics)

    errors = validate.validate_all(dataset)
    assert any("missing scenarios" in error for error in errors)


def test_nan_literal_fails(dataset):
    path = dataset / "metrics.json"
    text = path.read_text(encoding="utf-8").replace('"bare_share": null', '"bare_share": NaN')
    path.write_text(text, encoding="utf-8")

    errors = validate.validate_all(dataset)
    assert any("cannot parse" in error for error in errors)


def test_all_ok_larger_than_a_single_count_fails(dataset):
    metrics = read(dataset / "metrics.json")
    entry = metrics["locations"]["gombe"]["scenarios"]["rain+0_temp+0"]["maize"]
    entry["rain_ok"] = 1
    entry["all_ok"] = 2
    write(dataset / "metrics.json", metrics)

    errors = validate.validate_all(dataset)
    assert any("all_ok cannot exceed" in error for error in errors)


def test_invalid_data_mode_fails(dataset):
    metrics = read(dataset / "metrics.json")
    metrics["data_mode"] = "demo"
    write(dataset / "metrics.json", metrics)

    errors = validate.validate_all(dataset)
    assert any("data_mode" in error for error in errors)


def test_ndvi_wrong_length_fails(dataset):
    metrics = read(dataset / "metrics.json")
    block = metrics["locations"]["gombe"]
    block["ndvi_dekad"] = [0.2] * 10
    block["bare_flags"] = [False] * 36
    write(dataset / "metrics.json", metrics)

    errors = validate.validate_all(dataset)
    assert any("expected 36 values" in error for error in errors)


def test_unknown_strategy_crop_fails(dataset):
    strategies = read(dataset / "strategies.json")
    strategies[0]["sequence"] = ["not_a_crop"]
    write(dataset / "strategies.json", strategies)

    errors = validate.validate_all(dataset)
    assert any("unknown crop" in error for error in errors)


def test_invalid_crop_heat_metric_fails(dataset):
    crops = read(dataset / "crops.json")
    crops["maize"]["heat_metric"] = "average"
    write(dataset / "crops.json", crops)

    errors = validate.validate_all(dataset)
    assert any("heat_metric" in error for error in errors)
