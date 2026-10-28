"""Unit tests for CodeEditorIndicatorTester."""

import pytest
from app.workspace.code_editor.indicator_tester import IndicatorTester


@pytest.fixture
def tester():
    return IndicatorTester()


def test_new_indy_test_config(tester: IndicatorTester):
    """Verify new test config creation."""
    config = tester.new_indy_test("SMA", symbol="EURUSD", timeframe="H1")
    assert "test_id" in config
    assert config["indicator_name"] == "SMA"
    assert config["symbol"] == "EURUSD"


def test_indicator_tester_runs_builtin_moving_average(tester: IndicatorTester):
    """Verify executing IndicatorTester with built-in SMA indicator."""
    res = tester.indicator_tester(
        indicator_name="SMA",
        symbol="EURUSD",
        timeframe="H1",
        params={"period": 5},
        bar_count=50,
    )
    assert res["status"] == "success"
    assert len(res["candlesticks"]) == 50
    assert len(res["indicator_plots"]) == 50
    assert len(res["table_rows"]) == 50
    assert res["table_rows"][0]["indicator_val"] != 0.0


def test_indicator_tester_with_reference_discrepancy(tester: IndicatorTester):
    """Verify discrepancy detection when comparing against reference values."""
    reference_values = [1.0] * 30
    res = tester.indicator_tester(
        indicator_name="SMA",
        symbol="EURUSD",
        timeframe="H1",
        params={"period": 5},
        bar_count=30,
        reference_values=reference_values,
    )
    assert res["status"] == "success"
    assert len(res["discrepancies"]) > 0


def test_edit_params_and_save_load_config(tester: IndicatorTester):
    """Verify editing parameters, saving, and loading test configuration."""
    cfg = tester.new_indy_test("SMA")
    test_id = cfg["test_id"]

    # Edit params and re-run
    res_edit = tester.edit_indy_params(test_id, {"period": 10})
    assert res_edit["status"] == "success"

    # Save config
    res_save = tester.save_test_config(test_id, "MyMATest")
    assert res_save["status"] == "saved"

    # Load config
    res_load = tester.load_test_config(test_id)
    assert res_load["status"] == "loaded"
    assert res_load["config"]["saved_name"] == "MyMATest"
