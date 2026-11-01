"""Portfolio Composer selection criteria identifiers and precision.

Description:
    Defines and parses the five observed portfolio selection metric identifiers
    (SharpRatio, ReturnDrawdownRatio, CAGRMaxDrawdownRatio,
    CAGRMeanDrawdownRatio, NetProfit) and reports their decimal precision.
Purpose:
    FEAT-PORTFOLIO-COMPOSER: Configure composition and evaluation.
Key Capabilities:
    - FR-composer-selection: Parse selection type strings and return precision.
Python API Usage:
    from app.workspace.portfolio_composer.selection import ComposerSelection
    sel = ComposerSelection.parse("SharpRatio")
    decimals = sel.decimals()
CLI Usage:
    uv run python -m pytest tests/workspace/portfolio_composer/test_selection.py
"""

from __future__ import annotations

from enum import StrEnum

from app.core.host.logging import get_logger

logger = get_logger(__name__)


class ComposerSelection(StrEnum):
    """Observed Portfolio Composer selection objective types."""

    SHARPE = "SharpRatio"
    RETURN_DRAWDOWN = "ReturnDrawdownRatio"
    CAGR_MAX_DRAWDOWN = "CAGRMaxDrawdownRatio"
    CAGR_MEAN_DRAWDOWN = "CAGRMeanDrawdownRatio"
    NET_PROFIT = "NetProfit"

    @classmethod
    def parse(cls, value: str) -> ComposerSelection:
        """Parse an exact selection type string.

        Args:
            value: Exact selection type string.

        Returns:
            Matching ComposerSelection member.

        Raises:
            TypeError: If value is not a string.
            ValueError: If value is not an exact recognized selection type.
        """
        if not isinstance(value, str):
            raise TypeError("selection_type must be a string")

        for member in cls:
            if member.value == value:
                logger.info("FR-composer-selection: parsed selection_type=%s", value)
                return member

        raise ValueError(f"Invalid PortfolioSelectionType: {value}")

    def decimals(self) -> int:
        """Return the decimal precision associated with this selection metric.

        Returns:
            3 for Sharpe, 2 for CAGR drawdown metrics, 0 for net profit and return DD.
        """
        if self == ComposerSelection.SHARPE:
            return 3
        if self in (
            ComposerSelection.CAGR_MAX_DRAWDOWN,
            ComposerSelection.CAGR_MEAN_DRAWDOWN,
        ):
            return 2
        return 0
