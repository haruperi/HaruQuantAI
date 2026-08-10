"""Authoritative reads and route discipline (``FEAT-BRK-07``).

The application Phase 0 reconciliation (``feature``) requires a
health-aware primary/backup route discipline that is fail-closed, never
submits a duplicate order, and never silently reroutes a write across brokers.

This package owns two versioned cross-domain contracts (settled decision D-1):
``RoutePlan v1`` (``brokers.route_plan.v1``) and ``FailoverDecision v1``
(``brokers.failover_decision.v1``), each transported as a validated JSON-safe
mapping behind a ``build_*``/``parse_*`` function pair.
"""

from app.services.brokers.reconciliation.failover import (
    build_failover_decision,
    parse_failover_decision,
)
from app.services.brokers.reconciliation.plans import (
    build_route_plan,
    parse_route_plan,
)

__all__ = [
    "build_failover_decision",
    "build_route_plan",
    "parse_failover_decision",
    "parse_route_plan",
]
