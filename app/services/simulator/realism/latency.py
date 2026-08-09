"""Explicit propagation across simulation time domains."""

# ruff: noqa: TC001

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime, timedelta
from types import MappingProxyType

from app.services.simulator.realism.contracts import LatencyProfile


def project_latency_timestamps(
    market_at: datetime, profile: LatencyProfile
) -> Mapping[str, datetime]:
    """Project the full causal latency chain from one market timestamp.

    Args:
        market_at: Aware market timestamp.
        profile: Validated latency profile.

    Returns:
        Immutable timestamps for every modeled domain.

    Raises:
        ValueError: If the timestamp is naive.
    """
    if market_at.tzinfo is None or market_at.utcoffset() is None:
        raise ValueError("market timestamp must be timezone-aware")
    current = market_at + timedelta(
        milliseconds=float(profile.market_ms + profile.client_ms)
    )
    projected: dict[str, datetime] = {"market": market_at, "client": current}
    for name, delay in (
        ("network", profile.network_ms),
        ("broker", profile.broker_ms),
        ("venue", profile.venue_ms),
        ("report", profile.report_ms),
        ("processing", profile.processing_ms),
    ):
        current += timedelta(milliseconds=float(delay))
        projected[name] = current
    return MappingProxyType(projected)


__all__ = ["project_latency_timestamps"]
