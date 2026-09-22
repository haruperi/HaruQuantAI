"""Application composition root for approved host owners."""

from __future__ import annotations

from app.host.telemetry import (
    DEFAULT_DIAGNOSTIC_CAPACITY,
    DEFAULT_MAX_SUBSCRIBERS,
    _telemetry_feature,
)
from app.kernel.bootstrapper import Runtime
from app.kernel.feature import Feature


def create_runtime(
    *,
    telemetry_max_subscribers: int = DEFAULT_MAX_SUBSCRIBERS,
    diagnostic_capacity: int = DEFAULT_DIAGNOSTIC_CAPACITY,
) -> Runtime:
    """Construct a fresh, inactive runtime for the currently approved host."""
    telemetry = _telemetry_feature(
        max_subscribers=telemetry_max_subscribers,
        diagnostic_capacity=diagnostic_capacity,
    )

    def telemetry_factory() -> Feature:
        return telemetry

    return Runtime((telemetry_factory,), diagnostic_sink=telemetry.diagnose)


__all__ = ("create_runtime",)
