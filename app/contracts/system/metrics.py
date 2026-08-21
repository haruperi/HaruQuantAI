"""System telemetry and metrics capability contract."""

from collections.abc import Mapping
from typing import Protocol, runtime_checkable

from app.kernel.capability import CapabilityKey


@runtime_checkable
class MetricsCollector(Protocol):
    """Protocol for recording operational and business metrics."""

    def increment(
        self,
        name: str,
        value: float = 1.0,
        tags: Mapping[str, str] | None = None,
    ) -> None:
        """Increment a metric counter.

        Args:
            name: Metric counter name.
            value: Increment value.
            tags: Optional key-value metric tags.
        """
        ...

    def gauge(
        self,
        name: str,
        value: float,
        tags: Mapping[str, str] | None = None,
    ) -> None:
        """Record an instantaneous metric gauge value.

        Args:
            name: Metric gauge name.
            value: Current gauge value.
            tags: Optional key-value metric tags.
        """
        ...


SYSTEM_METRICS = CapabilityKey[MetricsCollector](
    name="system.metrics",
    major=1,
)
