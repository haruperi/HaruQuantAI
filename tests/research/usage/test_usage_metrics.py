"""Runnable usage examples for Research metric profiles."""

from dataclasses import dataclass

import pandas as pd
from app.services.research.contracts import (
    DataQualityReport,
    PreparedDataset,
    ResearchResourceLimits,
)
from app.services.research.metrics import (
    MetricCalculator,
    MetricRegistry,
    build_core_metric_profile,
    build_default_registry,
)
from app.services.research.metrics.registry import MetricContext, MetricValue
from app.utils import logger

_HASH = "f" * 64


@dataclass(frozen=True)
class _ExampleCalculator:
    """Usage calculator satisfying the public metric protocol."""

    family: str

    def compute(self, context: MetricContext) -> tuple[MetricValue, ...]:
        """Compute one example metric.

        Args:
            context: Detached metric context.

        Returns:
            One normalized metric value.
        """
        logger.debug("Computing example Research metric")
        return (MetricValue(self.family, 1.0, "ratio", len(context.data)),)


def _context() -> MetricContext:
    """Build an example metric context.

    Returns:
        Detached context.
    """
    logger.debug("Building example metric context")
    return MetricContext(pd.DataFrame({"value": [1.0]}))


def test_usage_registry_metric_calculator() -> None:
    """Use a structural metric calculator."""
    logger.debug("Running MetricCalculator usage")
    assert isinstance(_ExampleCalculator("returns"), MetricCalculator)


def test_usage_registry_compute() -> None:
    """Compute one normalized metric value."""
    logger.debug("Running metric compute usage")
    assert _ExampleCalculator("returns").compute(_context())[0].value == 1.0


def test_usage_registry_metric_registry() -> None:
    """Construct an immutable metric registry."""
    logger.debug("Running MetricRegistry usage")
    assert MetricRegistry((_ExampleCalculator("returns"),)).all()


def test_usage_registry_from_calculators() -> None:
    """Construct an isolated metric registry."""
    logger.debug("Running registry factory usage")
    assert MetricRegistry.from_calculators((_ExampleCalculator("returns"),)).all()


def test_usage_registry_resolve() -> None:
    """Resolve a metric family exactly."""
    logger.debug("Running metric resolve usage")
    assert build_default_registry().resolve("returns").family == "returns"


def test_usage_registry_all() -> None:
    """List ordered metric calculators."""
    logger.debug("Running metric membership usage")
    assert isinstance(build_default_registry().all(), tuple)


def test_usage_registry_build_default() -> None:
    """Build a fresh seven-family registry."""
    logger.debug("Running default registry usage")
    assert len(build_default_registry().all()) == 7


def test_usage_profile_build_core_metric_profile() -> None:
    """Build a complete metric profile."""
    logger.debug("Running metric-profile usage")
    frame = pd.DataFrame(
        {
            "open": [1.0, 2.0],
            "high": [2.0, 3.0],
            "low": [0.5, 1.5],
            "close": [1.5, 2.5],
            "volume": [10.0, 20.0],
            "spread": [0.1, 0.2],
        },
        index=pd.date_range("2026-01-01", periods=2, tz="UTC"),
    )
    prepared = PreparedDataset(
        frame,
        "v1",
        DataQualityReport((), (), ("schema",), ()),
        _HASH,
        _HASH,
        ("fixture",),
    )
    profile = build_core_metric_profile(
        prepared,
        registry=build_default_registry(),
        limits=ResearchResourceLimits(10, 10.0, 1024),
    )
    assert len(profile.metrics) == 7
