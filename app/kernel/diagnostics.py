"""Bounded secret-safe diagnostics serialization for kernel resolution reports.

Traces to: P4-T06, Gate G4
"""

from __future__ import annotations

from collections.abc import Mapping
from types import MappingProxyType
from typing import Any

from app.kernel.health import evaluate_kernel_health
from app.kernel.resolver import ResolutionReport


def project_diagnostics(
    report: ResolutionReport,
    *,
    maximum_items: int = 1000,
) -> Mapping[str, object]:
    """Project a bounded, JSON-serializable diagnostic snapshot of kernel resolution.

    Args:
        report: Resolution report.
        maximum_items: Maximum total binding + inactive entries to serialize (>= 1).

    Returns:
        Immutable dictionary containing kernel health, bindings, and inactive items.

    Raises:
        ValueError: If maximum_items < 1.
    """
    if maximum_items < 1:
        raise ValueError("maximum_items must be >= 1")

    health = evaluate_kernel_health(report)

    all_bindings: list[dict[str, str]] = [
        {
            "capability_id": str(b.capability_id),
            "provider_id": str(b.provider_id),
            "provider_version": str(b.provider_version),
        }
        for b in report.bindings
    ]

    all_inactive: list[dict[str, Any]] = [
        {
            "capability_id": str(i.capability_id),
            "reason_code": str(i.detail.reason_code),
            "provider_id": str(i.detail.provider_id) if i.detail.provider_id else None,
            "provider_state": i.detail.provider_state,
        }
        for i in report.inactive
    ]

    total_items = len(all_bindings) + len(all_inactive)
    truncated = total_items > maximum_items

    if truncated:
        budget = maximum_items
        bounded_bindings = all_bindings[:budget]
        budget -= len(bounded_bindings)
        bounded_inactive = all_inactive[:budget]
    else:
        bounded_bindings = all_bindings
        bounded_inactive = all_inactive

    diag: dict[str, object] = {
        "kernel": {
            "live": health.live,
            "ready": health.ready,
            "active_count": health.active_count,
            "inactive_count": health.inactive_count,
        },
        "bindings": bounded_bindings,
        "inactive": bounded_inactive,
        "truncated": truncated,
    }

    return MappingProxyType(diag)


__all__ = ("project_diagnostics",)
