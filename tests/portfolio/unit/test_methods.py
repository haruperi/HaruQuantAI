"""Unit tests for approved Portfolio construction methods."""

# ruff: noqa: INP001

from __future__ import annotations

from decimal import Decimal

import pytest
from app.services.portfolio.construction.methods import (
    equal_weights,
    fixed_weights,
    inverse_volatility_weights,
)
from app.services.portfolio.contracts import FixedWeightInput
from app.services.portfolio.exceptions import PortfolioError
from app.utils import logger


def test_fixed_equal_and_inverse_volatility_are_deterministic() -> None:
    """Verify all and only approved initial methods yield unit totals."""
    logger.info("Testing deterministic approved Portfolio construction methods")
    fixed_input = tuple(
        FixedWeightInput(
            component_id=component_id,
            capital_weight=weight,
            proposed_risk_budget_weight=weight,
        )
        for component_id, weight in (
            ("component-a", Decimal("0.4")),
            ("component-b", Decimal("0.6")),
        )
    )
    fixed = fixed_weights(
        fixed_input,
        tolerance=Decimal("0.0001"),
        minimum=Decimal(0),
        maximum=Decimal(1),
    )
    equal = equal_weights(
        ("component-a", "component-b"),
        minimum=Decimal(0),
        maximum=Decimal(1),
    )
    inverse = inverse_volatility_weights(
        {"component-a": Decimal("0.1"), "component-b": Decimal("0.2")},
        {"component-a": 30, "component-b": 30},
        minimum_observations=30,
        minimum=Decimal(0),
        maximum=Decimal(1),
    )

    for result in (fixed, equal, inverse):
        assert sum((row[1] for row in result), Decimal(0)) == Decimal(1)
        assert result == tuple(sorted(result))
    assert equal[0][1] == equal[1][1]
    assert inverse[0][1] > inverse[1][1]


@pytest.mark.parametrize(
    ("volatility", "observations", "detail"),
    [
        (Decimal(0), 30, "VOLATILITY"),
        (Decimal("-0.1"), 30, "VOLATILITY"),
        (Decimal("NaN"), 30, "VOLATILITY"),
        (Decimal("0.1"), 29, "OBSERVATIONS"),
    ],
)
def test_inverse_volatility_rejects_invalid_evidence(
    volatility: Decimal,
    observations: int,
    detail: str,
) -> None:
    """Verify invalid volatility evidence fails closed.

    Args:
        volatility: Candidate Analytics volatility.
        observations: Candidate Analytics observation count.
        detail: Expected symbolic failure detail.
    """
    logger.info("Testing inverse-volatility evidence rejection")
    with pytest.raises(PortfolioError, match=detail):
        inverse_volatility_weights(
            {"component-a": volatility},
            {"component-a": observations},
            minimum_observations=30,
            minimum=Decimal(0),
            maximum=Decimal(1),
        )


def test_fixed_weights_reject_invalid_total_and_bounds() -> None:
    """Verify explicit fixed inputs cannot bypass total or bound policy."""
    logger.info("Testing fixed Portfolio weight rejection")
    values = (
        FixedWeightInput(
            component_id="component-a",
            capital_weight=Decimal("0.9"),
            proposed_risk_budget_weight=Decimal("0.9"),
        ),
        FixedWeightInput(
            component_id="component-b",
            capital_weight=Decimal("0.9"),
            proposed_risk_budget_weight=Decimal("0.9"),
        ),
    )
    with pytest.raises(PortfolioError, match="TOTAL"):
        fixed_weights(
            values,
            tolerance=Decimal("0.01"),
            minimum=Decimal(0),
            maximum=Decimal(1),
        )


def test_advanced_methods_are_absent() -> None:
    """Verify speculative optimization methods are not exported."""
    logger.info("Testing absence of advanced Portfolio allocation methods")
    from app.services.portfolio.construction import methods

    for name in ("mvo", "black_litterman", "cvar", "optimize"):
        assert not hasattr(methods, name)
