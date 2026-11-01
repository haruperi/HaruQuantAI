"""Unit tests for SaverHTMLService."""

from __future__ import annotations

import pytest
from app.core.lib.errors import DomainError
from app.core.trading.results.contracts import RunResult
from app.workspace.results.saver_h_t_m_l import SaverHTMLService


def _create_html_result(strategy_id: str = "Strat_01") -> RunResult:
    return RunResult(
        result_id=f"res_{strategy_id}",
        databank_id="Results",
        strategy_id=strategy_id,
        strategy_name="Strat_01",
        metrics={"net_profit": 750.0, "profit_factor": 2.1},
        trades=(
            {"ticket": 101, "type": "BUY", "profit_loss": 500.0},
            {"ticket": 102, "type": "SELL", "profit_loss": 250.0},
        ),
    )


class TestSaverHTMLService:
    """Test suite for SaverHTMLService."""

    def test_golden_fixture_export_html(self) -> None:
        """Verify exporting Strat_01 returns valid HTML with doctype, metrics, and trades."""
        service = SaverHTMLService()
        sample = _create_html_result("Strat_01")
        service.register_in_memory_result(sample)

        receipt = service.export_strategy_html("p1", "Results", "Strat_01")
        assert receipt.filename == "Strat_01.html"
        assert receipt.mime_type == "text/html; charset=utf-8"
        assert receipt.size_bytes > 0
        assert receipt.content_bytes.startswith(b"<!DOCTYPE html>")

        html_text = receipt.content_bytes.decode("utf-8")
        assert "Strategy Report: Strat_01" in html_text
        assert "750.0" in html_text
        assert "101" in html_text

    def test_export_html_without_trades(self) -> None:
        """Verify export with include_trades=False omits trade table."""
        service = SaverHTMLService()
        sample = _create_html_result("Strat_01")
        service.register_in_memory_result(sample)

        receipt = service.export_strategy_html(
            "p1", "Results", "Strat_01", include_trades=False
        )
        html_text = receipt.content_bytes.decode("utf-8")
        assert "Executed Trades" not in html_text

    def test_export_html_not_found(self) -> None:
        """Verify DomainError when strategy not found."""
        service = SaverHTMLService()
        with pytest.raises(DomainError) as exc_info:
            service.export_strategy_html("p1", "Results", "NonExistent")
        assert exc_info.value.code == "RESULTS_STRATEGY_NOT_FOUND"
