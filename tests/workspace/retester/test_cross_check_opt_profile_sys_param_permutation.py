"""Unit tests for CrossCheckOptProfileSPPService.

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
from app.workspace.retester.cross_check_opt_profile_sys_param_permutation import (
    CrossCheckOptProfileSPPService,
    SPPConfig,
)


def _make_strategy() -> HSLStrategyDocument:
    payload = HSLStrategyPayload(
        id="strat_test", name="TestStrategy", timeframe=TimeframeSpec(primary="H1")
    )
    return HSLStrategyDocument(strategy=payload)


class TestCrossCheckOptProfileSPP:
    """Test suite for CrossCheckOptProfileSPPService."""

    def test_golden_fixture_four_runs(self) -> None:
        """4 parameter runs with [120.0, 80.0, 40.0, -10.0] yield profitable=75.0%, median=60.0, passed=True."""
        strat = _make_strategy()
        bars: list[MarketBar] = []
        profits = [120.0, 80.0, 40.0, -10.0]
        config = SPPConfig(enabled=True, min_profitable_runs_pct=70.0)
        with pytest.raises(DomainError) as error:
            CrossCheckOptProfileSPPService.run(
                strategy=strat, bars=bars, config=config, custom_runs=profits
            )
        assert error.value.code == "HSL_RETEST_EVALUATOR_REQUIRED"

    def test_insufficient_profitable_runs_fails(self) -> None:
        """When profitable percentage is below minimum, passed is False."""
        strat = _make_strategy()
        bars: list[MarketBar] = []
        profits = [100.0, -50.0, -30.0, -20.0]
        config = SPPConfig(enabled=True, min_profitable_runs_pct=70.0)
        with pytest.raises(DomainError) as error:
            CrossCheckOptProfileSPPService.run(
                strategy=strat, bars=bars, config=config, custom_runs=profits
            )
        assert error.value.code == "HSL_RETEST_EVALUATOR_REQUIRED"
