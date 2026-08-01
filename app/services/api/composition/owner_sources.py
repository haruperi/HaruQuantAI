"""Concrete read-only in-process sources built from owner package-root APIs."""

from __future__ import annotations

import os
from datetime import timedelta
from typing import Any, Protocol, cast

from app.services.analytics import get_analytics_dashboard_snapshot
from app.services.brokers import get_broker_dashboard_snapshot
from app.services.data import (
    build_audit_event_query,
    get_calendar_dashboard_snapshot,
    get_market_hours_dashboard_snapshot,
    query_audit_events,
    unwrap_data_response,
)
from app.services.trading import get_trading_operational_events
from app.utils import generate_id, utc_now

type AuthContext = Any

_AUDIT_LOOKBACK_DAYS = 30


class _AuditPage(Protocol):
    """Structural Data audit page view consumed by the API boundary."""

    events: tuple[object, ...]


def read_dashboard_snapshot(name: str, _auth: AuthContext) -> dict[str, object]:
    """Route one dashboard read to its authoritative owner.

    Args:
        name: Canonical dashboard view name.
        _auth: Validated caller context; authorization occurs in the route.

    Returns:
        Owner-authored or host-observed timestamped snapshot.

    Raises:
        ValueError: If the view is not part of the canonical dashboard set.
    """
    if name == "broker":
        return get_broker_dashboard_snapshot()
    if name in {"equity_curve", "summary"}:
        return get_analytics_dashboard_snapshot(name)
    if name == "market_hours":
        return get_market_hours_dashboard_snapshot()
    if name == "calendar":
        return get_calendar_dashboard_snapshot()
    if name == "resources":
        return {
            "view": "resources",
            "owner": "api-host",
            "status": "available",
            "logical_cpu_count": os.cpu_count(),
            "observed_at": utc_now(),
        }
    raise ValueError("unsupported dashboard view")


def read_audit_events(auth: AuthContext, limit: int) -> tuple[object, ...]:
    """Read one bounded recent Data-owned audit page.

    Args:
        auth: Validated operator context used by Data authorization.
        limit: Requested page bound.

    Returns:
        Ordered immutable audit events.
    """
    end = utc_now()
    request_id = generate_id("req")
    query = build_audit_event_query(
        start=end - timedelta(days=_AUDIT_LOOKBACK_DAYS),
        end=end,
        limit=limit,
        request_id=request_id,
    )
    page = cast(
        "_AuditPage",
        unwrap_data_response(
            query_audit_events(query, auth),
            operation="api.operator.read_audit_events",
            request_id=request_id,
        ),
    )
    return tuple(page.events)


def read_trading_events(_auth: AuthContext) -> tuple[object, ...]:
    """Read the bounded durable Trading operational-event view.

    Returns:
        Ordered unresolved operational events.
    """
    return tuple(get_trading_operational_events())


__all__ = (
    "read_audit_events",
    "read_dashboard_snapshot",
    "read_trading_events",
)
