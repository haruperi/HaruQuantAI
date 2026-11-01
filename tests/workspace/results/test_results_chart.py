"""Unit tests for ResultsChartService."""

from __future__ import annotations

import pytest
from app.core.lib.errors import DomainError
from app.core.trading.results.contracts import RunResult
from app.workspace.results.results_chart import (
    ChartCandle,
    ChartTradeMarker,
    ResultsChartService,
)


def _create_results_chart_result(strategy_id: str = "Strat_01") -> RunResult:
    return RunResult(
        result_id=f"res_{strategy_id}",
        databank_id="Results",
        strategy_id=strategy_id,
        strategy_name="ChartCandlesStrategy",
        trades=(
            {
                "ticket": 101,
                "open_time_ms": 1_000,
                "close_time_ms": 2_000,
                "open_price": 1.1000,
                "close_price": 1.1050,
                "type": "BUY",
                "profit_loss": 50.0,
                "sl_level": 1.0950,
                "pt_level": 1.1100,
            },
            {
                "ticket": 102,
                "open_time_ms": 3_000,
                "close_time_ms": 4_000,
                "open_price": 1.1050,
                "close_price": 1.1020,
                "type": "SELL",
                "profit_loss": 30.0,
            },
        ),
        strategy_payload={
            "symbol": "EURUSD",
            "timeframe": "H1",
            "candles": [
                {
                    "timestamp_ms": 1_000,
                    "open": 1.1000,
                    "high": 1.1020,
                    "low": 1.0990,
                    "close": 1.1010,
                    "volume": 100.0,
                },
                {
                    "timestamp_ms": 2_000,
                    "open": 1.1010,
                    "high": 1.1060,
                    "low": 1.1000,
                    "close": 1.1050,
                    "volume": 150.0,
                },
                {
                    "timestamp_ms": 3_000,
                    "open": 1.1050,
                    "high": 1.1070,
                    "low": 1.1040,
                    "close": 1.1045,
                    "volume": 120.0,
                },
            ],
        },
    )


class TestResultsChartService:
    """Test suite for ResultsChartService."""

    def test_load_chart_data(self) -> None:
        """Verify loading candles, trade markers, and payload metadata."""
        service = ResultsChartService()
        sample = _create_results_chart_result("Strat_01")
        service.register_in_memory_result(sample)

        resp = service.load_chart_data("p1", "Results", "Strat_01")
        payload = resp.data
        assert payload.symbol == "EURUSD"
        assert payload.timeframe == "H1"
        assert len(payload.candles) == 3
        assert len(payload.trades) == 2
        assert not payload.truncated

        t1 = payload.trades[0]
        assert t1.ticket == 101
        assert t1.direction == "BUY"
        assert t1.profit_loss == 50.0
        assert t1.sl_level == 1.0950
        assert t1.pt_level == 1.1100

        t2 = payload.trades[1]
        assert t2.sl_level is None
        assert t2.pt_level is None

        d = payload.to_dict()
        assert len(d["candles"]) == 3
        assert len(d["trades"]) == 2

    def test_load_chart_data_truncation_and_filtering(self) -> None:
        """Verify window filtering and max_bars truncation."""
        service = ResultsChartService()
        sample = _create_results_chart_result("Strat_01")
        service.register_in_memory_result(sample)

        # Filter by time window
        resp_filtered = service.load_chart_data(
            "p1", "Results", "Strat_01", start_ms=1500, end_ms=2500
        )
        assert len(resp_filtered.data.candles) == 1
        assert resp_filtered.data.candles[0].timestamp_ms == 2_000

        # Truncate with max_bars
        resp_trunc = service.load_chart_data("p1", "Results", "Strat_01", max_bars=2)
        assert len(resp_trunc.data.candles) == 2
        assert resp_trunc.data.truncated is True

    def test_cancel_loading(self) -> None:
        """Verify cancellation request tracking."""
        service = ResultsChartService()
        resp = service.cancel_loading("req_123")
        assert resp.data is True
        assert "req_123" in service._cancelled_requests

    def test_chart_strategy_not_found(self) -> None:
        """Verify DomainError when strategy is not registered."""
        service = ResultsChartService()
        with pytest.raises(DomainError) as exc_info:
            service.load_chart_data("p1", "Results", "Unknown")
        assert exc_info.value.code == "RESULTS_STRATEGY_NOT_FOUND"

    def test_chart_candle_and_trade_marker_to_dict(self) -> None:
        """Verify to_dict serialization for candle and marker."""
        candle = ChartCandle(
            timestamp_ms=1000,
            open=1.0,
            high=2.0,
            low=0.5,
            close=1.5,
            volume=10.0,
        )
        cd = candle.to_dict()
        assert cd["open"] == 1.0

        marker = ChartTradeMarker(
            ticket=1,
            open_time_ms=1000,
            close_time_ms=2000,
            open_price=1.0,
            close_price=1.5,
            direction="BUY",
            profit_loss=50.0,
            sl_level=None,
            pt_level=None,
        )
        md = marker.to_dict()
        assert md["ticket"] == 1
        assert md["sl_level"] is None
