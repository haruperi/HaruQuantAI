"""Unit tests for SaverPDFService."""

from __future__ import annotations

import pytest
from app.core.lib.errors import DomainError
from app.core.trading.results.contracts import RunResult
from app.workspace.results.saver_p_d_f import SaverPDFService


def _create_pdf_result(strategy_id: str = "Strat_01") -> RunResult:
    return RunResult(
        result_id=f"res_{strategy_id}",
        databank_id="Results",
        strategy_id=strategy_id,
        strategy_name="Strat_01",
        metrics={"NetProfit": 1200.0, "ProfitFactor": 2.5},
        trades=(
            {"ticket": 1, "type": "BUY", "profit_loss": 600.0},
            {"ticket": 2, "type": "SELL", "profit_loss": 600.0},
        ),
    )


class TestSaverPDFService:
    """Test suite for SaverPDFService."""

    def test_golden_fixture_export_pdf(self) -> None:
        """Verify exporting Strat_01 produces valid %PDF-1.4 header and %%EOF trailer."""
        service = SaverPDFService()
        sample = _create_pdf_result("Strat_01")
        service.register_in_memory_result(sample)

        receipt = service.export_strategy_pdf(
            "p1", "Results", "Strat_01", include_trades=True
        )
        assert receipt.filename == "Strat_01.pdf"
        assert receipt.mime_type == "application/pdf"
        assert receipt.size_bytes > 0
        assert receipt.content_bytes.startswith(b"%PDF-1.4")
        assert receipt.content_bytes.strip().endswith(b"%%EOF")

    def test_export_pdf_not_found(self) -> None:
        """Verify DomainError when strategy is not found."""
        service = SaverPDFService()
        with pytest.raises(DomainError) as exc_info:
            service.export_strategy_pdf("p1", "Results", "UnknownStrat")
        assert exc_info.value.code == "RESULTS_STRATEGY_NOT_FOUND"
