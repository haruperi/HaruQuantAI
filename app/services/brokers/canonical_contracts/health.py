# ruff: noqa: DOC501, N812
"""BrokerHealth v1 cross-domain contract transport.

The application Phase 0 reconciliation (``feature``) requires a
normalized ``BrokerHealth`` extending the adapter runtime and connection state
with heartbeat, latency, error rate, maintenance, and route readiness. The
contract is fail-closed: a health sample that is stale beyond the caller-declared
freshness budget is reported as ``DEGRADED`` / ``STALE`` and never as a healthy
default.
"""

from __future__ import annotations

from collections.abc import Mapping
from datetime import UTC, datetime, timedelta
from typing import cast

from app.services.brokers.canonical_contracts.enums import BrokerEnvironment, BrokerId
from app.utils import canonical_digest, to_json_safe
from app.utils import create_validation_error as ValidationError

CONTRACT_VERSION = "v1"
SCHEMA_ID = "brokers.health.v1"

_AUTH_STATES = frozenset({"AUTHENTICATED", "UNAUTHENTICATED", "EXPIRED", "UNKNOWN"})
_SESSION_STATES = frozenset({"READY", "CONNECTING", "DEGRADED", "FAILED", "UNKNOWN"})
_HEARTBEAT_STATES = frozenset({"ALIVE", "DEGRADED", "DEAD", "STALE"})
_ROUTE_READINESS = frozenset(
    {"READY", "DEGRADED", "UNAVAILABLE", "STALE", "MAINTENANCE"}
)
_FIELDS = frozenset(
    {
        "contract_version",
        "schema_id",
        "broker",
        "environment",
        "observed_at",
        "freshness_budget_sec",
        "as_of",
        "authentication_state",
        "session_state",
        "api_heartbeat",
        "stream_heartbeat",
        "round_trip_latency_ms",
        "error_rate",
        "in_maintenance",
        "route_readiness",
        "qualifying_failure_count",
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
        raise ValidationError("BROKER_HEALTH_INVALID")
    return value


def _require_choice(value: object, allowed: frozenset[str]) -> str:
    """Validate an enumeration member.

    Args:
        value: Candidate value.
        allowed: Permitted members.

    Returns:
        Validated member.

    Raises:
        ValidationError: If the value is not permitted.
    """
    text = _require_text(value)
    if text not in allowed:
        raise ValidationError("BROKER_HEALTH_INVALID")
    return text


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
        raise ValidationError("BROKER_HEALTH_INVALID")
    return value.isoformat().replace("+00:00", "Z")


def _require_non_negative_float(value: object) -> float:
    """Validate a finite non-negative float.

    Args:
        value: Candidate value.

    Returns:
        Validated float.

    Raises:
        ValidationError: If the value is not finite or non-negative.
    """
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValidationError("BROKER_HEALTH_INVALID")
    import math

    if math.isnan(value) or math.isinf(value) or value < 0:
        raise ValidationError("BROKER_HEALTH_INVALID")
    return float(value)


def _is_stale(
    observed_at: datetime,
    freshness_budget: timedelta,
    as_of: datetime,
) -> bool:
    """Return whether the observed sample exceeds the freshness budget.

    Args:
        observed_at: Sample observation instant.
        freshness_budget: Caller-declared freshness budget.
        as_of: Current evaluation instant.

    Returns:
        Whether the sample is stale.
    """
    return (as_of - observed_at) > freshness_budget


def _stale_route_readiness(route_readiness: str) -> str:
    """Downgrade route readiness when the sample is stale.

    Args:
        route_readiness: Original readiness value.

    Returns:
        ``STALE`` when the original readiness was healthy, otherwise unchanged.
    """
    if route_readiness in {"READY", "DEGRADED"}:
        return "STALE"
    return route_readiness


def build_broker_health(
    *,
    broker: BrokerId | str,
    environment: BrokerEnvironment | str,
    observed_at: datetime,
    freshness_budget_sec: float,
    as_of: datetime,
    authentication_state: str,
    session_state: str,
    api_heartbeat: str,
    stream_heartbeat: str,
    round_trip_latency_ms: float,
    error_rate: float,
    in_maintenance: bool,
    route_readiness: str,
    qualifying_failure_count: int,
) -> dict[str, object]:
    """Build and hash a redacted BrokerHealth v1 mapping.

    A health sample whose ``observed_at`` exceeds ``freshness_budget_sec`` as of
    ``as_of`` is fail-closed: ``route_readiness`` is downgraded to ``STALE`` and
    both heartbeat values are clamped to ``STALE`` when they were healthy. The
    original broker evidence is preserved verbatim; only the readiness verdict
    is fail-closed so a stale sample can never report ``READY``.

    Args:
        broker: Owning broker identifier.
        environment: Configured broker environment.
        observed_at: Aware UTC sample observation instant.
        freshness_budget_sec: Caller-declared freshness budget in seconds.
        as_of: Aware UTC evaluation instant.
        authentication_state: Normalized authentication state.
        session_state: Normalized session state.
        api_heartbeat: API heartbeat verdict.
        stream_heartbeat: Stream heartbeat verdict.
        round_trip_latency_ms: Last measured round-trip latency in milliseconds.
        error_rate: Rolling error rate in the closed interval ``[0.0, 1.0]``.
        in_maintenance: Provider maintenance indicator.
        route_readiness: Normalized route readiness verdict.
        qualifying_failure_count: Circuit-qualifying failure count.

    Returns:
        BrokerHealth v1 mapping.

    Raises:
        ValidationError: If any field evidence is invalid.
    """
    broker_value = (
        broker if isinstance(broker, BrokerId) else BrokerId(_require_text(broker))
    )
    env_value = (
        environment
        if isinstance(environment, BrokerEnvironment)
        else BrokerEnvironment(_require_text(environment))
    )
    if isinstance(qualifying_failure_count, bool) or qualifying_failure_count < 0:
        raise ValidationError("BROKER_HEALTH_INVALID")
    budget = _require_non_negative_float(freshness_budget_sec)
    latency = _require_non_negative_float(round_trip_latency_ms)
    rate = _require_non_negative_float(error_rate)
    if rate > 1.0:
        raise ValidationError("BROKER_HEALTH_INVALID")
    if not isinstance(in_maintenance, bool):
        raise ValidationError("BROKER_HEALTH_INVALID")
    observed_text = _require_timestamp(observed_at)
    as_of_text = _require_timestamp(as_of)
    stale = _is_stale(observed_at, timedelta(seconds=budget), as_of)
    readiness_value = _require_choice(route_readiness, _ROUTE_READINESS)
    api_value = _require_choice(api_heartbeat, _HEARTBEAT_STATES)
    stream_value = _require_choice(stream_heartbeat, _HEARTBEAT_STATES)
    if stale:
        readiness_value = _stale_route_readiness(readiness_value)
        api_value = "STALE" if api_value == "ALIVE" else api_value
        stream_value = "STALE" if stream_value == "ALIVE" else stream_value
    health: dict[str, object] = {
        "contract_version": CONTRACT_VERSION,
        "schema_id": SCHEMA_ID,
        "broker": broker_value.value,
        "environment": env_value.value,
        "observed_at": observed_text,
        "freshness_budget_sec": budget,
        "as_of": as_of_text,
        "authentication_state": _require_choice(authentication_state, _AUTH_STATES),
        "session_state": _require_choice(session_state, _SESSION_STATES),
        "api_heartbeat": api_value,
        "stream_heartbeat": stream_value,
        "round_trip_latency_ms": latency,
        "error_rate": rate,
        "in_maintenance": in_maintenance,
        "route_readiness": readiness_value,
        "qualifying_failure_count": qualifying_failure_count,
    }
    health["integrity_hash"] = canonical_digest(health)
    return health


def parse_broker_health(value: Mapping[str, object]) -> dict[str, object]:
    """Validate a BrokerHealth v1 mapping and integrity hash.

    Args:
        value: Candidate mapping.

    Returns:
        Validated detached health mapping.

    Raises:
        ValidationError: If version, shape, or hash is invalid.
    """
    if (
        set(value) != _FIELDS
        or value.get("contract_version") != CONTRACT_VERSION
        or value.get("schema_id") != SCHEMA_ID
    ):
        raise ValidationError("BROKER_HEALTH_VERSION_INCOMPATIBLE")
    expected_hash = value.get("integrity_hash")
    unhashed = {key: value[key] for key in value if key != "integrity_hash"}
    if (
        not isinstance(expected_hash, str)
        or canonical_digest(unhashed) != expected_hash
    ):
        raise ValidationError("BROKER_HEALTH_INTEGRITY_INVALID")
    observed_at_text = value.get("observed_at")
    as_of_text = value.get("as_of")
    if not isinstance(observed_at_text, str) or not isinstance(as_of_text, str):
        raise ValidationError("BROKER_HEALTH_INVALID")
    in_maintenance = value.get("in_maintenance")
    qualifying_failure_count = value.get("qualifying_failure_count")
    if (
        not isinstance(in_maintenance, bool)
        or isinstance(qualifying_failure_count, bool)
        or not isinstance(qualifying_failure_count, int)
        or qualifying_failure_count < 0
    ):
        raise ValidationError("BROKER_HEALTH_INVALID")
    rebuilt = build_broker_health(
        broker=cast("str", value["broker"]),
        environment=cast("str", value["environment"]),
        observed_at=datetime.fromisoformat(observed_at_text),
        freshness_budget_sec=cast("float", value["freshness_budget_sec"]),
        as_of=datetime.fromisoformat(as_of_text),
        authentication_state=cast("str", value["authentication_state"]),
        session_state=cast("str", value["session_state"]),
        api_heartbeat=cast("str", value["api_heartbeat"]),
        stream_heartbeat=cast("str", value["stream_heartbeat"]),
        round_trip_latency_ms=cast("float", value["round_trip_latency_ms"]),
        error_rate=cast("float", value["error_rate"]),
        in_maintenance=in_maintenance,
        route_readiness=cast("str", value["route_readiness"]),
        qualifying_failure_count=qualifying_failure_count,
    )
    safe: object = to_json_safe(rebuilt)
    if not isinstance(safe, dict):
        raise ValidationError("BROKER_HEALTH_INVALID")
    return dict(safe)


__all__ = [
    "CONTRACT_VERSION",
    "SCHEMA_ID",
    "build_broker_health",
    "parse_broker_health",
]
