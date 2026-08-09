"""Deterministic root-cause grouping for simulated alerts."""

# ruff: noqa: TC001

from __future__ import annotations

from collections.abc import Mapping, Sequence
from types import MappingProxyType

from app.services.simulator.alerts.contracts import AlertEvent


def group_simulation_alerts(
    alerts: Sequence[AlertEvent],
) -> Mapping[str, tuple[AlertEvent, ...]]:
    """Group alerts by root cause with stable severity/time ordering.

    Args:
        alerts: Simulated alerts to group.

    Returns:
        Immutable root-cause mapping.
    """
    severity = {"critical": 0, "error": 1, "warning": 2, "info": 3}
    grouped: dict[str, list[AlertEvent]] = {}
    for alert in alerts:
        grouped.setdefault(alert.root_cause_id, []).append(alert)
    return MappingProxyType(
        {
            identity: tuple(
                sorted(
                    values,
                    key=lambda item: (
                        severity[item.severity],
                        item.first_observed_at,
                        item.alert_id,
                    ),
                )
            )
            for identity, values in sorted(grouped.items())
        }
    )


__all__ = ["group_simulation_alerts"]
