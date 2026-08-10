"""Public reconciliation route-plan and failover operations."""

from collections.abc import Mapping
from datetime import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.services.brokers.canonical_contracts.enums import (
        BrokerEnvironment,
        BrokerId,
    )


def build_broker_route_plan(
    *,
    plan_id: str,
    primary_broker: BrokerId | str,
    primary_environment: BrokerEnvironment | str,
    primary_readiness: str,
    backup_broker: BrokerId | str | None,
    backup_environment: BrokerEnvironment | str | None,
    backup_readiness: str | None,
    selected_route: str | None,
    route_state: str,
    write_failover_policy: str,
    created_at: datetime,
) -> dict[str, object]:
    """Build and hash a redacted RoutePlan v1 mapping (``feature``).

    Args:
        plan_id: Caller-owned plan identifier.
        primary_broker: Primary broker identifier.
        primary_environment: Primary broker environment.
        primary_readiness: Primary route health readiness.
        backup_broker: Optional backup broker identifier.
        backup_environment: Optional backup broker environment.
        backup_readiness: Optional backup route health readiness.
        selected_route: Selected route identifier, or ``None`` when unavailable.
        route_state: Aggregate route state verdict.
        write_failover_policy: Write failover policy.
        created_at: Aware UTC plan creation instant.

    Returns:
        RoutePlan v1 mapping.
    """
    from app.services.brokers.reconciliation.plans import build_route_plan

    return build_route_plan(
        plan_id=plan_id,
        primary_broker=primary_broker,
        primary_environment=primary_environment,
        primary_readiness=primary_readiness,
        backup_broker=backup_broker,
        backup_environment=backup_environment,
        backup_readiness=backup_readiness,
        selected_route=selected_route,
        route_state=route_state,
        write_failover_policy=write_failover_policy,
        created_at=created_at,
    )


def parse_broker_route_plan(value: Mapping[str, object]) -> dict[str, object]:
    """Validate a RoutePlan v1 mapping and integrity hash (``feature``).

    Args:
        value: Candidate mapping.

    Returns:
        Validated detached route plan.
    """
    from app.services.brokers.reconciliation.plans import parse_route_plan

    return parse_route_plan(value)


def build_broker_failover_decision(
    *,
    decision_id: str,
    plan_id: str,
    decision: str,
    active_broker: BrokerId | str | None,
    active_environment: BrokerEnvironment | str | None,
    write_permitted: bool,
    read_permitted: bool,
    reason: str,
    decided_at: datetime,
) -> dict[str, object]:
    """Build and hash a redacted FailoverDecision v1 mapping (``feature``).

    Args:
        decision_id: Caller-owned decision identifier.
        plan_id: Originating route plan identifier.
        decision: Deterministic failover decision.
        active_broker: Active broker after the decision, or ``None`` when blocked.
        active_environment: Active broker environment, or ``None`` when blocked.
        write_permitted: Whether the active route may submit new writes.
        read_permitted: Whether the active route may be read.
        reason: Short deterministic reason label.
        decided_at: Aware UTC decision instant.

    Returns:
        FailoverDecision v1 mapping.
    """
    from app.services.brokers.reconciliation.failover import build_failover_decision

    return build_failover_decision(
        decision_id=decision_id,
        plan_id=plan_id,
        decision=decision,
        active_broker=active_broker,
        active_environment=active_environment,
        write_permitted=write_permitted,
        read_permitted=read_permitted,
        reason=reason,
        decided_at=decided_at,
    )


def parse_broker_failover_decision(value: Mapping[str, object]) -> dict[str, object]:
    """Validate a FailoverDecision v1 mapping and integrity hash (``feature``).

    Args:
        value: Candidate mapping.

    Returns:
        Validated detached failover decision.
    """
    from app.services.brokers.reconciliation.failover import parse_failover_decision

    return parse_failover_decision(value)
