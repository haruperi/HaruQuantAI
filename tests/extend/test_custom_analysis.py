"""Unit tests for CustomAnalysis extension cohort."""

from __future__ import annotations

from app.extend.columns.base import TradeRecord
from app.extend.custom_analysis import (
    CorrelationFilterAnalyzer,
    OutlierTradeAnalyzer,
)


class TestCustomAnalysis:
    """Test suite for CustomAnalysis analyzers."""

    def test_correlation_filter_analyzer(self) -> None:
        """Verify retaining only strategies with correlation below threshold."""
        matrix = {
            "S1": {"S1": 1.0, "S2": 0.8, "S3": 0.2},
            "S2": {"S1": 0.8, "S2": 1.0, "S3": 0.3},
            "S3": {"S1": 0.2, "S2": 0.3, "S3": 1.0},
        }

        retained = CorrelationFilterAnalyzer.evaluate(
            ["S1", "S2", "S3"], matrix, max_correlation=0.5
        )
        assert retained == ("S1", "S3")

    def test_outlier_trade_analyzer(self) -> None:
        """Verify outlier trade detection and adjusted net profit calculation."""
        trades = (
            *(TradeRecord(ticket=i, profit_loss=50.0) for i in range(1, 10)),
            TradeRecord(ticket=10, profit_loss=1000.0),
        )

        # Standard multiplier 2.5 flags the 1000.0 trade
        report = OutlierTradeAnalyzer.evaluate(trades, std_multiplier=2.5)
        assert report.outlier_tickets == (10,)
        assert report.adjusted_net_profit == 450.0
        assert report.mean_pl == 145.0
        assert report.std_pl > 0.0

        d = report.to_dict()
        assert d["outlier_tickets"] == [10]
        assert d["adjusted_net_profit"] == 450.0

    def test_outlier_trade_analyzer_empty(self) -> None:
        """Verify empty trades sequence produces zero report."""
        report = OutlierTradeAnalyzer.evaluate(())
        assert report.outlier_tickets == ()
        assert report.adjusted_net_profit == 0.0
        assert report.mean_pl == 0.0
