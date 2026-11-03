"""Unit tests for CrossCheckRetestWithHigherPrecisionService.

Description:
    Verify declared strategy behavior and explicit rejection of unavailable inputs.
Purpose:
    FEAT-WIZARD-HSL-LANGUAGE: Regression evidence for shared strategy execution.
Key Capabilities:
    - FR-hsl-regression-evidence: Assert observable results and failure boundaries.
Python API Usage:
    Run this module through pytest.
CLI Usage:
    uv run pytest tests/workspace/retester --no-cov
"""

from app.core.trading.strategy.hsl.models import (
    HSLStrategyDocument,
    HSLStrategyPayload,
    TimeframeSpec,
)
from app.workspace.retester.cross_check_retest_with_higher_precision import (
    CrossCheckRetestWithHigherPrecisionService,
    HigherPrecisionConfig,
)
from app.workspace.retester.settings_cross_checks import CrossCheckCondition


def _make_strategy() -> HSLStrategyDocument:
    payload = HSLStrategyPayload(
        id="strat_test",
        name="TestStrategy",
        timeframe=TimeframeSpec(primary="H1"),
    )
    return HSLStrategyDocument(strategy=payload)


class TestCrossCheckRetestWithHigherPrecision:
    """Test suite for CrossCheckRetestWithHigherPrecisionService."""

    def test_golden_fixture_profit_retention(self) -> None:
        """Assert main_profit=1000.0 and hp_profit=850.0 yields 85.0% retention and passed=True."""
        strat = _make_strategy()
        main_stats = {"net_profit": 1000.0, "drawdown_pct": 12.0}
        hp_stats = {"net_profit": 850.0, "drawdown_pct": 13.5}

        config = HigherPrecisionConfig(
            enabled=True,
            precision="M1Data",
            min_profit_retention_pct=70.0,
            acceptance_conditions=(
                CrossCheckCondition(
                    name="MinRetention",
                    metric="ProfitRetentionPct",
                    operator=">=",
                    threshold=70.0,
                ),
            ),
        )

        result = CrossCheckRetestWithHigherPrecisionService.run(
            strategy=strat,
            main_stats=main_stats,
            config=config,
            hp_stats=hp_stats,
        )

        assert result.profit_retention_pct == 85.0
        assert result.passed is True
        assert len(result.failure_reasons) == 0

    def test_retention_below_threshold_fails(self) -> None:
        """Retention below threshold causes failure."""
        strat = _make_strategy()
        main_stats = {"net_profit": 1000.0}
        hp_stats = {"net_profit": 500.0, "drawdown_pct": 0.0}  # 50.0% retention

        config = HigherPrecisionConfig(
            enabled=True,
            min_profit_retention_pct=70.0,
        )

        result = CrossCheckRetestWithHigherPrecisionService.run(
            strategy=strat,
            main_stats=main_stats,
            config=config,
            hp_stats=hp_stats,
        )

        assert result.profit_retention_pct == 50.0
        assert result.passed is False
        assert len(result.failure_reasons) == 1
