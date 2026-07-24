"""Authoritative critical operational alert builders."""

from __future__ import annotations

import hashlib
from collections.abc import Mapping
from typing import TYPE_CHECKING

from app.services.api.alerts.models import (
    CriticalAlertError,
    CriticalAlertTrigger,
    CriticalOperationalAlert,
)
from app.utils import AuthContext, canonical_json, logger, redact_mapping_value

if TYPE_CHECKING:
    from app.services.risk import KillSwitchState
    from app.services.trading import OperationalEvent


def _alert_id(
    trigger: CriticalAlertTrigger,
    *,
    source_schema_id: str,
    source_id: str,
    source_version: str,
) -> str:
    """Derive deterministic alert identity from immutable source material.

    Args:
        trigger: Closed authoritative trigger.
        source_schema_id: Owner contract schema.
        source_id: Immutable source identity.
        source_version: Source version or sequence.

    Returns:
        Lowercase SHA-256 alert identity.
    """
    material = canonical_json(
        {
            "trigger": trigger.value,
            "source_schema_id": source_schema_id,
            "source_id": source_id,
            "source_version": source_version,
        }
    )
    return hashlib.sha256(material.encode("utf-8")).hexdigest()


def _redacted_text_mapping(
    value: Mapping[str, object],
    *,
    field_name: str,
) -> dict[str, str]:
    """Redact and normalize one bounded alert mapping.

    Args:
        value: Candidate source mapping.
        field_name: Mapping name for deterministic failures.

    Returns:
        Redacted text mapping.

    Raises:
        CriticalAlertError: If redaction cannot produce safe text.
    """
    redacted = redact_mapping_value(value).value
    if not isinstance(redacted, Mapping):
        raise CriticalAlertError(
            "ALERT_SOURCE_INVALID",
            f"{field_name} redaction failed",
        )
    normalized: dict[str, str] = {}
    for key, item in redacted.items():
        if not isinstance(key, str) or not isinstance(item, str | int | bool):
            raise CriticalAlertError(
                "ALERT_SOURCE_INVALID",
                f"{field_name} must contain scalar values",
            )
        normalized[key] = str(item).lower() if isinstance(item, bool) else str(item)
    return normalized


def build_kill_switch_activation_alert(
    state: KillSwitchState,
    context: AuthContext,
) -> CriticalOperationalAlert:
    """Build an alert from one active canonical Risk kill-switch state.

    Args:
        state: Authoritative Risk-owned state.
        context: Authenticated command trace context.

    Returns:
        Deterministic bounded critical alert.

    Raises:
        CriticalAlertError: If source or trace evidence is incompatible.
    """
    logger.warning("Building critical alert for active Risk kill switch")
    if state.state != "active":
        raise CriticalAlertError(
            "ALERT_SOURCE_INVALID",
            "kill-switch state must be active",
        )
    scope = {"scope_level": state.scope_level, **dict(state.scope)}
    try:
        return CriticalOperationalAlert(
            alert_id=_alert_id(
                CriticalAlertTrigger.RISK_KILL_SWITCH_ACTIVATED,
                source_schema_id=state.schema_id,
                source_id=state.state_id,
                source_version=str(state.version),
            ),
            trigger=CriticalAlertTrigger.RISK_KILL_SWITCH_ACTIVATED,
            title="Risk kill switch activated",
            summary=f"Risk kill switch activated for {state.scope_level} scope.",
            scope=_redacted_text_mapping(scope, field_name="kill-switch scope"),
            source_schema_id=state.schema_id,
            source_id=state.state_id,
            source_version=str(state.version),
            occurred_at=state.updated_at,
            request_id=context.request_id,
            workflow_id=context.workflow_id,
            correlation_id=context.correlation_id,
        )
    except ValueError as error:
        raise CriticalAlertError(
            "ALERT_SOURCE_INVALID",
            "kill-switch alert evidence is invalid",
        ) from error


def build_unknown_broker_state_alert(
    event: OperationalEvent,
) -> CriticalOperationalAlert:
    """Build an alert from one retry-locked unknown broker-state event.

    Args:
        event: Authoritative Trading-owned critical event.

    Returns:
        Deterministic bounded critical alert.

    Raises:
        CriticalAlertError: If the event is not the approved authoritative source.
    """
    logger.warning("Building critical alert for unknown Broker state")
    event_type = str(event.event_type)
    retry_locked = event.facts.get("retry_locked")
    if (
        event_type != "BROKER_STATE_UNKNOWN"
        or event.severity != "critical"
        or retry_locked is not True
        or "receipt_id" not in event.source_refs
        or "incident_id" not in event.source_refs
    ):
        raise CriticalAlertError(
            "ALERT_SOURCE_INVALID",
            "broker-state event is not authoritative",
        )
    scope = _redacted_text_mapping(
        {
            key: value
            for key, value in event.facts.items()
            if key in {"retry_locked", "account_id", "symbol", "unresolved_scope"}
        },
        field_name="broker-state facts",
    )
    try:
        return CriticalOperationalAlert(
            alert_id=_alert_id(
                CriticalAlertTrigger.TRADING_BROKER_STATE_UNKNOWN,
                source_schema_id=event.schema_id,
                source_id=event.event_id,
                source_version=event.contract_version,
            ),
            trigger=CriticalAlertTrigger.TRADING_BROKER_STATE_UNKNOWN,
            title="Broker state unknown",
            summary="Trading broker state is unknown and retry-locked.",
            scope=scope,
            source_schema_id=event.schema_id,
            source_id=event.event_id,
            source_version=event.contract_version,
            occurred_at=event.occurred_at,
            request_id=event.request_id,
            workflow_id=event.workflow_id,
            correlation_id=event.correlation_id,
        )
    except ValueError as error:
        raise CriticalAlertError(
            "ALERT_SOURCE_INVALID",
            "broker-state alert evidence is invalid",
        ) from error


__all__ = (
    "build_kill_switch_activation_alert",
    "build_unknown_broker_state_alert",
)
