from unittest.mock import MagicMock, patch

from app.agentic.tools.simulation.tools import run_backtest


@patch("app.agentic.tools.simulation.tools._run_backtest")
def test_run_backtest(mock_run: MagicMock) -> None:
    mock_run.return_value = {"status": "success", "data": {}}
    result = run_backtest(
        strategy_ref="dummy",
        symbols=["EURUSD"],
        timeframe="H1",
        start="2026-01-01",
        end="2026-01-02",
    )

    assert result == {"status": "success", "data": {}}

    # Check that payload contains defaults where we didn't specify them
    mock_run.assert_called_once()
    payload = mock_run.call_args[0][0]
    assert payload["strategy_ref"] == "dummy"
    assert payload["symbols"] == ["EURUSD"]
    assert payload["timeframe"] == "H1"
    assert payload["start"] == "2026-01-01"
    assert payload["end"] == "2026-01-02"
    assert payload["strategy_config"] == {}
    assert payload["initial_balance"] == 10000.0
    assert payload["account_currency"] == "USD"
    assert payload["tick_model"] == "M1_TICKS"
    assert payload["spread_model"] == "NATIVE_SPREAD"
    assert payload["slippage_model"] == "NO_SLIPPAGE"
    assert payload["commission_model"] == "NO_COMMISSION"
    assert payload["swap_model"] == "NO_SWAP"
    assert payload["broker_profile_ref"] == "mt5_demo_reference_fx_v1"
    assert payload["journal_persistence"] == {}
    assert payload["request_id"] is None
