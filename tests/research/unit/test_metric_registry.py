"""Unit tests for the immutable Research metric registry."""

from dataclasses import dataclass

import pandas as pd
import pytest
from app.services.research.metrics import (
    MetricCalculator,
    MetricRegistry,
    build_default_registry,
)
from app.services.research.metrics.registry import MetricContext, MetricValue
from app.utils import ValidationError, logger


@dataclass(frozen=True)
class _Calculator:
    """Small structural calculator used by registry tests."""

    family: str

    def compute(self, context: MetricContext) -> tuple[MetricValue, ...]:
        """Return one normalized test value.

        Args:
            context: Detached metric context.

        Returns:
            One normalized value.
        """
        logger.debug("Computing test metric for %d rows", len(context.data))
        return (MetricValue(self.family, 1.0, "ratio", len(context.data)),)


def test_calculator_protocol_contract() -> None:
    """Verify structural calculators satisfy the public protocol."""
    logger.debug("Testing Research calculator protocol")
    assert isinstance(_Calculator("returns"), MetricCalculator)


def test_calculator_returns_normalized_values() -> None:
    """Verify calculators return immutable normalized values."""
    logger.debug("Testing normalized Research metric values")
    values = _Calculator("returns").compute(MetricContext(pd.DataFrame({"x": [1]})))
    assert values[0].unit == "ratio"


def test_registry_rejects_duplicate_family() -> None:
    """Verify duplicate families fail."""
    logger.debug("Testing duplicate Research metric family")
    with pytest.raises(ValidationError):
        MetricRegistry.from_calculators(
            (_Calculator("returns"), _Calculator("returns"))
        )


def test_from_calculators_is_isolated() -> None:
    """Verify source iterable changes cannot mutate a registry."""
    logger.debug("Testing isolated Research metric registry")
    calculators = [_Calculator("returns")]
    registry = MetricRegistry.from_calculators(calculators)
    calculators.append(_Calculator("roc"))
    assert len(registry.all()) == 1


def test_resolve_missing_family() -> None:
    """Verify missing exact family resolution fails."""
    logger.debug("Testing missing Research metric family")
    with pytest.raises(ValidationError):
        build_default_registry().resolve("missing")


def test_all_is_immutable_and_ordered() -> None:
    """Verify all returns a deterministic tuple."""
    logger.debug("Testing ordered Research metric membership")
    families = tuple(item.family for item in build_default_registry().all())
    assert families[:2] == ("returns", "roc")


def test_default_registry_has_seven_families() -> None:
    """Verify the default registry contains exactly seven families."""
    logger.debug("Testing default Research metric registry")
    assert len(build_default_registry().all()) == 7
