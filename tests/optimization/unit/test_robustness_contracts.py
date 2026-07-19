"""Tests for Optimization robustness contracts."""

# ruff: noqa: INP001

from decimal import Decimal

import pytest
from app.services.optimization.robustness import (
    ExecutionStressRequest,
    MonteCarloMethod,
    MonteCarloRequest,
    MonteCarloResult,
)
from pydantic import ValidationError


def monte_carlo_request(**overrides: object) -> MonteCarloRequest:
    """Build a valid Monte Carlo request."""
    payload: dict[str, object] = {
        "outcomes": (Decimal(10), Decimal(-5), Decimal(3)),
        "initial_balance": Decimal(100),
        "method": "resample_returns",
        "simulations": 5,
        "seed": 17,
        "ruin_threshold": Decimal(50),
        "confidence_level": 0.8,
    }
    payload.update(overrides)
    return MonteCarloRequest.model_validate(payload)


def test_monte_carlo_method_values() -> None:
    """Only the three initial methods are cataloged."""
    assert tuple(MonteCarloMethod) == (
        MonteCarloMethod.SHUFFLE_TRADES,
        MonteCarloMethod.RESAMPLE_RETURNS,
        MonteCarloMethod.BLOCK_BOOTSTRAP,
    )


def test_monte_carlo_request_rejects_empty_outcomes() -> None:
    """Empty outcome samples fail contract validation."""
    with pytest.raises(ValidationError, match="non-empty"):
        monte_carlo_request(outcomes=())


def test_monte_carlo_result_validates_path_count() -> None:
    """Result distributions pair exactly with path count."""
    with pytest.raises(ValidationError, match="path count"):
        MonteCarloResult(
            method="shuffle_trades",
            simulations=2,
            seed=1,
            sub_seed_policy="v1",
            final_equity=(Decimal(1),),
            max_drawdowns=(Decimal(0), Decimal(0)),
            percentiles={},
            ruin_probability=None,
            warnings=(),
        )


def test_execution_stress_request_requires_seed_for_skip() -> None:
    """Random skip stress cannot run without deterministic seed evidence."""
    with pytest.raises(ValidationError, match="requires probability and seed"):
        ExecutionStressRequest(kind="skip_trade", value=Decimal("0.1"))
