"""Runnable deterministic Portfolio construction usage example."""

from __future__ import annotations

from decimal import Decimal

from app.services.portfolio.construction.methods import equal_weights
from app.utils import logger


def test_calculate_equal_portfolio_weights() -> None:
    """Calculate explicit bounded equal weights through the approved method."""
    logger.info("Running equal Portfolio construction usage example")
    rows = equal_weights(
        ("component-a", "component-b"),
        minimum=Decimal(0),
        maximum=Decimal(1),
    )

    assert rows == (
        ("component-a", Decimal("0.5"), Decimal("0.5")),
        ("component-b", Decimal("0.5"), Decimal("0.5")),
    )
