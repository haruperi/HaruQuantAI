"""Unit tests for SaverStrategyTradesService."""

from __future__ import annotations

import pytest
from app.core.lib.errors import DomainError
from app.core.trading.results.contracts import RunResult
from app.workspace.results.saver_strategy_trades import SaverStrategyTradesService


def _create_trades_export_result(strategy_id: str = "Strat_01") -> RunResult:
    return RunResult(
        result_id=f"res_{strategy_id}",
        databank_id="Results",
        strategy_id=strategy_id,
        strategy_name="Strat_01",
        trades=(
            {
                "ticket": 1,
                "symbol": "EURUSD",
                "type": "BUY",
                "open_time": "2024-01-01T10:00:00Z",
                "open_price": 1.1000,
                "size": 1.0,
                "close_time": "2024-01-01T12:00:00Z",
                "close_price": 1.1050,
                "profit_loss": 500.0,
                "comment": "Trade 1",
            },
            {
                "ticket": 2,
                "symbol": "EURUSD",
                "type": "SELL",
                "open_time": "2024-01-02T10:00:00Z",
                "open_price": 1.1050,
                "size": 1.0,
                "close_time": "2024-01-02T11:00:00Z",
                "close_price": 1.1020,
                "profit_loss": 300.0,
                "comment": "Trade 2",
            },
        ),
        strategy_payload={"initial_capital": 10000.0},
    )


class TestSaverStrategyTradesService:
    """Test suite for SaverStrategyTradesService."""

    def test_golden_fixture_export_trades_csv(self) -> None:
        """Verify exporting 2 trades produces 3 lines with exact columns."""
        service = SaverStrategyTradesService()
        sample = _create_trades_export_result("Strat_01")
        service.register_in_memory_result(sample)

        cols = ("NumberOfTrade", "Ticket", "Symbol", "Type", "ProfitLoss", "Balance")
        receipt = service.export_trades_csv(
            "p1", "Results", "Strat_01", column_ids=cols
        )
        assert receipt.filename == "Strat_01_trades.csv"
        assert receipt.mime_type == "text/csv; charset=utf-8"

        csv_text = receipt.content_bytes.decode("utf-8")
        lines = csv_text.strip().split("\n")
        assert len(lines) == 3
        assert lines[0] == "NumberOfTrade,Ticket,Symbol,Type,ProfitLoss,Balance"
        assert lines[1] == "1,1,EURUSD,BUY,500.0,10500.0"
        assert lines[2] == "2,2,EURUSD,SELL,300.0,10800.0"

    def test_export_trades_not_found(self) -> None:
        """Verify DomainError when strategy is not found."""
        service = SaverStrategyTradesService()
        with pytest.raises(DomainError) as exc_info:
            service.export_trades_csv("p1", "Results", "NonExistent")
        assert exc_info.value.code == "RESULTS_STRATEGY_NOT_FOUND"
