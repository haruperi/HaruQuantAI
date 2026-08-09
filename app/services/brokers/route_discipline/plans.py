# ruff: noqa: DOC501, N812
"""RoutePlan v1 cross-domain contract transport.

A ``RoutePlan`` names one explicit primary broker route and an optional backup
broker route, together with the health verdicts that admitted them. The plan is
fail-closed: when no route is health-ready, ``selected_route`` is ``None`` and
``route_state`` is ``UNAVAILABLE`` so the caller must not submit any order.
"""

from __future__ import annotations

from collections.abc import Mapping
from datetime import UTC, datetime
from typing import cast

from app.services.brokers.contracts.enums import BrokerEnvironment, BrokerId
from app.utils import canonical_digest, to_json_safe
from app.utils import create_validation_error as ValidationError

CONTRACT_VERSION = "v1"
SCHEMA_ID = "brokers.route_plan.v1"

_ROUTE_STATES = frozenset({"READY", "DEGRADED", "UNAVAILABLE", "FAILOVER_REQUIRED"})
_FAILOVER_POLICIES = frozenset({"NEVER", "READ_ONLY", "RECOVERY_ONLY", "UNKNOWN"})
_FIELDS = frozenset(
    {
        "contract_version",
        "schema_id",
        "plan_id",
        "primary_broker",
        "primary_environment",
        "primary_readiness",
        "backup_broker",
        "backup_environment",
        "backup_readiness",
        "selected_route",
        "route_state",
        "write_failover_policy",
        "created_at",
        "integrity_hash",
    }
)


def _require_text(value: object) -> str:
    """Validate non-empty text.

    Args:
        value: Candidate value.

    Returns:
        Validated text.

    Raises:
        ValidationError: If the value is not non-empty text.
    """
    if not isinstance(value, str) or not value.strip():
        raise ValidationError("BROKER_ROUTE_PLAN_INVALID")
    return value


def _require_optional_broker(value: object) -> str | None:
    """Validate an optional broker identifier.

    Args:
        value: Candidate value.

    Returns:
        Validated broker identifier text, or ``None``.

    Raises:
        ValidationError: If the value is not a known broker.
    """
    if value is None:
        return None
    return BrokerId(_require_text(value)).value


def _require_optional_environment(value: object) -> str | None:
    """Validate an optional broker environment.

    Args:
        value: Candidate value.

    Returns:
        Validated environment text, or ``None``.

    Raises:
        ValidationError: If the value is not a known environment.
    """
    if value is None:
        return None
    return BrokerEnvironment(_require_text(value)).value


def _require_timestamp(value: datetime) -> str:
    """Validate an aware UTC timestamp and return canonical text.

    Args:
        value: Candidate timestamp.

    Returns:
        Canonical ISO-8601 UTC text.

    Raises:
        ValidationError: If the timestamp is naive or non-UTC.
    """
    if (
        not isinstance(value, datetime)
        or value.tzinfo is None
        or value.utcoffset() != UTC.utcoffset(value)
    ):
        raise ValidationError("BROKER_ROUTE_PLAN_INVALID")
    return value.isoformat().replace("+00:00", "Z")


def _require_readiness_states(
    primary_readiness: str,
    backup_readiness: str | None,
    route_state: str,
    write_failover_policy: str,
) -> None:
    """Validate the readiness, state, and policy enumeration members.

    Args:
        primary_readiness: Primary route health readiness.
        backup_readiness: Optional backup route health readiness.
        route_state: Aggregate route state verdict.
        write_failover_policy: Write failover policy.

    Raises:
        ValidationError: If any member is not a permitted value.
    """
    if primary_readiness not in _ROUTE_STATES:
        raise ValidationError("BROKER_ROUTE_PLAN_INVALID")
    if backup_readiness is not None and backup_readiness not in _ROUTE_STATES:
        raise ValidationError("BROKER_ROUTE_PLAN_INVALID")
    if route_state not in _ROUTE_STATES:
        raise ValidationError("BROKER_ROUTE_PLAN_INVALID")
    if write_failover_policy not in _FAILOVER_POLICIES:
        raise ValidationError("BROKER_ROUTE_PLAN_INVALID")


def build_route_plan(
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
    """Build and hash a redacted RoutePlan v1 mapping.

    The plan is fail-closed. A primary route that is not health-ready must
    surface ``route_state`` of ``UNAVAILABLE`` or ``FAILOVER_REQUIRED`` and a
    ``selected_route`` of ``None`` when no backup is ready; it may never report
    a ready primary that contradicts the supplied readiness verdict. The
    ``write_failover_policy`` defaults to ``RECOVERY_ONLY`` for cockpit routes:
    a write is never silently rerouted to the backup broker.

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

    Raises:
        ValidationError: If any field evidence is invalid or contradictory.
    """
    _require_readiness_states(
        primary_readiness, backup_readiness, route_state, write_failover_policy
    )
    primary_broker_value = (
        primary_broker
        if isinstance(primary_broker, BrokerId)
        else BrokerId(_require_text(primary_broker))
    )
    primary_env_value = (
        primary_environment
        if isinstance(primary_environment, BrokerEnvironment)
        else BrokerEnvironment(_require_text(primary_environment))
    )
    backup_broker_text = (
        backup_broker.value
        if isinstance(backup_broker, BrokerId)
        else _require_optional_broker(backup_broker)
    )
    backup_env_text = (
        backup_environment.value
        if isinstance(backup_environment, BrokerEnvironment)
        else _require_optional_environment(backup_environment)
    )
    if (backup_broker_text is None) != (backup_env_text is None):
        raise ValidationError("BROKER_ROUTE_PLAN_INVALID")
    if backup_broker_text is not None and backup_readiness is None:
        raise ValidationError("BROKER_ROUTE_PLAN_INVALID")
    # Fail-closed: a selected route must match a ready primary or backup, and a
    # non-ready primary must never yield a ready aggregate verdict.
    ready_routes = {
        route
        for route, readiness in (
            (primary_broker_value.value, primary_readiness),
            (backup_broker_text, backup_readiness),
        )
        if route is not None and readiness in {"READY", "DEGRADED"}
    }
    if selected_route is not None and (
        not isinstance(selected_route, str) or selected_route not in ready_routes
    ):
        raise ValidationError("BROKER_ROUTE_PLAN_INVALID")
    if (
        primary_readiness in {"UNAVAILABLE", "FAILOVER_REQUIRED"}
        and backup_broker_text is None
        and route_state in {"READY", "DEGRADED"}
    ):
        raise ValidationError("BROKER_ROUTE_PLAN_INVALID")
    plan: dict[str, object] = {
        "contract_version": CONTRACT_VERSION,
        "schema_id": SCHEMA_ID,
        "plan_id": _require_text(plan_id),
        "primary_broker": primary_broker_value.value,
        "primary_environment": primary_env_value.value,
        "primary_readiness": primary_readiness,
        "backup_broker": backup_broker_text,
        "backup_environment": backup_env_text,
        "backup_readiness": backup_readiness,
        "selected_route": selected_route,
        "route_state": route_state,
        "write_failover_policy": write_failover_policy,
        "created_at": _require_timestamp(created_at),
    }
    plan["integrity_hash"] = canonical_digest(plan)
    return plan


def parse_route_plan(value: Mapping[str, object]) -> dict[str, object]:
    """Validate a RoutePlan v1 mapping and integrity hash.

    Args:
        value: Candidate mapping.

    Returns:
        Validated detached route plan.

    Raises:
        ValidationError: If version, shape, or hash is invalid.
    """
    if (
        set(value) != _FIELDS
        or value.get("contract_version") != CONTRACT_VERSION
        or value.get("schema_id") != SCHEMA_ID
    ):
        raise ValidationError("BROKER_ROUTE_PLAN_VERSION_INCOMPATIBLE")
    expected_hash = value.get("integrity_hash")
    unhashed = {key: value[key] for key in value if key != "integrity_hash"}
    if (
        not isinstance(expected_hash, str)
        or canonical_digest(unhashed) != expected_hash
    ):
        raise ValidationError("BROKER_ROUTE_PLAN_INTEGRITY_INVALID")
    created_at_text = value.get("created_at")
    selected_route = value.get("selected_route")
    backup_broker = value.get("backup_broker")
    backup_environment = value.get("backup_environment")
    backup_readiness = value.get("backup_readiness")
    if not isinstance(created_at_text, str):
        raise ValidationError("BROKER_ROUTE_PLAN_INVALID")
    if selected_route is not None and not isinstance(selected_route, str):
        raise ValidationError("BROKER_ROUTE_PLAN_INVALID")
    if backup_broker is not None and not isinstance(backup_broker, str):
        raise ValidationError("BROKER_ROUTE_PLAN_INVALID")
    if backup_environment is not None and not isinstance(backup_environment, str):
        raise ValidationError("BROKER_ROUTE_PLAN_INVALID")
    if backup_readiness is not None and not isinstance(backup_readiness, str):
        raise ValidationError("BROKER_ROUTE_PLAN_INVALID")
    rebuilt = build_route_plan(
        plan_id=cast("str", value["plan_id"]),
        primary_broker=cast("str", value["primary_broker"]),
        primary_environment=cast("str", value["primary_environment"]),
        primary_readiness=cast("str", value["primary_readiness"]),
        backup_broker=backup_broker,
        backup_environment=backup_environment,
        backup_readiness=backup_readiness,
        selected_route=selected_route,
        route_state=cast("str", value["route_state"]),
        write_failover_policy=cast("str", value["write_failover_policy"]),
        created_at=datetime.fromisoformat(created_at_text),
    )
    safe: object = to_json_safe(rebuilt)
    if not isinstance(safe, dict):
        raise ValidationError("BROKER_ROUTE_PLAN_INVALID")
    return dict(safe)


__all__ = [
    "CONTRACT_VERSION",
    "SCHEMA_ID",
    "build_route_plan",
    "parse_route_plan",
]
