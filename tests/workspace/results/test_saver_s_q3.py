"""Unit tests for SaverSQ3Service."""

from __future__ import annotations

import pytest
from app.core.lib.errors import DomainError
from app.core.trading.results.contracts import RunResult
from app.workspace.results.loader_s_q3 import LoaderSQ3Service
from app.workspace.results.saver_s_q3 import (
    SaverSQ3Service,
)


def _create_export_result(strategy_id: str = "Strat_01") -> RunResult:
    return RunResult(
        result_id=f"res_{strategy_id}",
        databank_id="Results",
        strategy_id=strategy_id,
        strategy_name="RoundtripStrat",
        parameters={"Period": 14, "TakeProfit": 100},
        trades=(
            {"ticket": 1, "type": "BUY", "profit_loss": 250.0},
            {"ticket": 2, "type": "SELL", "profit_loss": -50.0},
        ),
        strategy_payload={"symbol": "USDJPY", "timeframe": "H4"},
    )


class TestSaverSQ3Service:
    """Test suite for SaverSQ3Service."""

    def test_golden_fixture_roundtrip(self) -> None:
        """Verify export_sq3 produces valid archive readable by LoaderSQ3."""
        saver = SaverSQ3Service()
        sample = _create_export_result("Strat_01")
        saver.register_in_memory_result(sample)

        receipt = saver.export_sq3("p1", "Results", "Strat_01")
        assert receipt.filename == "RoundtripStrat.str"
        assert receipt.mime_type == "application/zip"
        assert receipt.size_bytes > 0

        # Roundtrip into LoaderSQ3
        archive = LoaderSQ3Service.load_bytes(receipt.filename, receipt.content_bytes)
        assert archive.strategy_name == "RoundtripStrat"
        assert archive.symbol == "USDJPY"
        assert archive.timeframe == "H4"
        assert archive.trade_count == 2
        assert archive.parameters["Period"] == "14"

        d = receipt.to_dict()
        assert d["filename"] == "RoundtripStrat.str"

    def test_strategy_not_found(self) -> None:
        """Verify DomainError when strategy does not exist."""
        saver = SaverSQ3Service()
        with pytest.raises(DomainError) as exc_info:
            saver.export_sq3("p1", "Results", "NonExistent")
        assert exc_info.value.code == "RESULTS_STRATEGY_NOT_FOUND"
