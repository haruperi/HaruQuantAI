# ruff: noqa: DOC501, N812

"""FailoverDecision v1 cross-domain contract transport.

A ``FailoverDecision`` records the deterministic outcome of evaluating a route
plan against current health: whether to keep the primary, fail over to the
backup for reads/recovery only, or block. The decision is fail-closed and
prohibits duplicate order submission and silent cross-broker write rerouting.
"""

from __future__ import annotations

from collections.abc import Mapping
from datetime import UTC, datetime
from typing import cast

from app.kernel.errors import create_validation_error as ValidationError
from app.kernel.serialization import canonical_digest, to_json_safe
from app.services.brokers.canonical_contracts.enums import BrokerEnvironment, BrokerId

CONTRACT_VERSION = "v1"
SCHEMA_ID = "brokers.failover_decision.v1"

_DECISIONS = frozenset(
    {"HOLD_PRIMARY", "FAILOVER_READ_ONLY", "FAILOVER_RECOVERY", "BLOCK"}
)
_FIELDS = frozenset(
    {
        "contract_version",
        "schema_id",
        "decision_id",
        "plan_id",
        "decision",
        "active_broker",
        "active_environment",
        "write_permitted",
        "read_permitted",
        "reason",
        "decided_at",
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
        raise ValidationError("BROKER_FAILOVER_DECISION_INVALID")
    return value


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
        raise ValidationError("BROKER_FAILOVER_DECISION_INVALID")
    return value.isoformat().replace("+00:00", "Z")


def build_failover_decision(
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
    """Build and hash a redacted FailoverDecision v1 mapping.

    The decision is fail-closed and never silently reroutes a write across
    brokers. ``FAILOVER_READ_ONLY`` and ``FAILOVER_RECOVERY`` admit the backup
    for reads or recovery only and force ``write_permitted=False``; only
    ``HOLD_PRIMARY`` may permit writes, and ``BLOCK`` permits neither.

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

    Raises:
        ValidationError: If any field evidence is invalid or contradictory.
    """
    if decision not in _DECISIONS:
        raise ValidationError("BROKER_FAILOVER_DECISION_INVALID")
    if not isinstance(write_permitted, bool) or not isinstance(read_permitted, bool):
        raise ValidationError("BROKER_FAILOVER_DECISION_INVALID")
    active_broker_text = (
        active_broker.value
        if isinstance(active_broker, BrokerId)
        else (
            BrokerId(_require_text(active_broker)).value
            if active_broker is not None
            else None
        )
    )
    active_env_text = (
        active_environment.value
        if isinstance(active_environment, BrokerEnvironment)
        else (
            BrokerEnvironment(_require_text(active_environment)).value
            if active_environment is not None
            else None
        )
    )
    # An active route must carry both a broker and an environment together, or
    # neither (the blocked case). A mismatched pair is rejected.
    if (active_broker_text is None) != (active_env_text is None):
        raise ValidationError("BROKER_FAILOVER_DECISION_INVALID")
    # Fail-closed policy: writes are never permitted on a failover decision,
    # and a BLOCK decision permits neither reads nor writes.
    if decision in {"FAILOVER_READ_ONLY", "FAILOVER_RECOVERY"} and write_permitted:
        raise ValidationError("BROKER_FAILOVER_DECISION_INVALID")
    if decision == "BLOCK" and (write_permitted or read_permitted):
        raise ValidationError("BROKER_FAILOVER_DECISION_INVALID")
    if decision == "BLOCK" and active_broker_text is not None:
        raise ValidationError("BROKER_FAILOVER_DECISION_INVALID")
    if decision != "BLOCK" and active_broker_text is None:
        raise ValidationError("BROKER_FAILOVER_DECISION_INVALID")
    verdict: dict[str, object] = {
        "contract_version": CONTRACT_VERSION,
        "schema_id": SCHEMA_ID,
        "decision_id": _require_text(decision_id),
        "plan_id": _require_text(plan_id),
        "decision": decision,
        "active_broker": active_broker_text,
        "active_environment": active_env_text,
        "write_permitted": write_permitted,
        "read_permitted": read_permitted,
        "reason": _require_text(reason),
        "decided_at": _require_timestamp(decided_at),
    }
    verdict["integrity_hash"] = canonical_digest(verdict)
    return verdict


def parse_failover_decision(value: Mapping[str, object]) -> dict[str, object]:
    """Validate a FailoverDecision v1 mapping and integrity hash.

    Args:
        value: Candidate mapping.

    Returns:
        Validated detached failover decision.

    Raises:
        ValidationError: If version, shape, or hash is invalid.
    """
    if (
        set(value) != _FIELDS
        or value.get("contract_version") != CONTRACT_VERSION
        or value.get("schema_id") != SCHEMA_ID
    ):
        raise ValidationError("BROKER_FAILOVER_DECISION_VERSION_INCOMPATIBLE")
    expected_hash = value.get("integrity_hash")
    unhashed = {key: value[key] for key in value if key != "integrity_hash"}
    if (
        not isinstance(expected_hash, str)
        or canonical_digest(unhashed) != expected_hash
    ):
        raise ValidationError("BROKER_FAILOVER_DECISION_INTEGRITY_INVALID")
    decided_at_text = value.get("decided_at")
    active_broker = value.get("active_broker")
    active_environment = value.get("active_environment")
    write_permitted = value.get("write_permitted")
    read_permitted = value.get("read_permitted")
    if not isinstance(decided_at_text, str):
        raise ValidationError("BROKER_FAILOVER_DECISION_INVALID")
    if active_broker is not None and not isinstance(active_broker, str):
        raise ValidationError("BROKER_FAILOVER_DECISION_INVALID")
    if active_environment is not None and not isinstance(active_environment, str):
        raise ValidationError("BROKER_FAILOVER_DECISION_INVALID")
    if not isinstance(write_permitted, bool) or not isinstance(read_permitted, bool):
        raise ValidationError("BROKER_FAILOVER_DECISION_INVALID")
    rebuilt = build_failover_decision(
        decision_id=cast("str", value["decision_id"]),
        plan_id=cast("str", value["plan_id"]),
        decision=cast("str", value["decision"]),
        active_broker=active_broker,
        active_environment=active_environment,
        write_permitted=write_permitted,
        read_permitted=read_permitted,
        reason=cast("str", value["reason"]),
        decided_at=datetime.fromisoformat(decided_at_text),
    )
    safe: object = to_json_safe(rebuilt)
    if not isinstance(safe, dict):
        raise ValidationError("BROKER_FAILOVER_DECISION_INVALID")
    return dict(safe)


__all__ = [
    "CONTRACT_VERSION",
    "SCHEMA_ID",
    "build_failover_decision",
    "parse_failover_decision",
]
