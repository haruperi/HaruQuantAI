"""Unit tests for CrossCheckWalkForwardOptimizationService.

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

import pytest
from app.core.data.contracts import MarketBar
from app.core.lib.errors import DomainError
from app.workspace.algo_wizard.models import (
    HSLStrategyDocument,
    HSLStrategyPayload,
    TimeframeSpec,
)
from app.workspace.retester.cross_check_walk_forward_optimization import (
    CrossCheckWalkForwardOptimizationService,
    WFOptimizationConfig,
)
from app.workspace.retester.settings_cross_checks import CrossCheckCondition


def _make_strategy() -> HSLStrategyDocument:
    payload = HSLStrategyPayload(
        id="strat_test", name="TestStrategy", timeframe=TimeframeSpec(primary="H1")
    )
    return HSLStrategyDocument(strategy=payload)


class TestCrossCheckWalkForwardOptimization:
    """Test suite for CrossCheckWalkForwardOptimizationService."""

    def test_golden_fixture_five_windows(self) -> None:
        """5 windows with 4 profitable OOS runs yield profitable_runs_pct == 80.0."""
        strat = _make_strategy()
        bars: list[MarketBar] = []
        window_returns = [100.0, 50.0, -20.0, 80.0, 120.0]
        config = WFOptimizationConfig(
            enabled=True,
            runs_count=5,
            oos_pct=30,
            anchored=False,
            acceptance_conditions=(
                CrossCheckCondition(
                    name="MinProfitable",
                    metric="ProfitableRunsPct",
                    operator=">=",
                    threshold=75.0,
                ),
            ),
        )
        with pytest.raises(DomainError) as error:
            CrossCheckWalkForwardOptimizationService.run(
                strategy=strat,
                bars=bars,
                config=config,
                custom_window_returns=window_returns,
            )
        assert error.value.code == "HSL_RETEST_EVALUATOR_REQUIRED"
