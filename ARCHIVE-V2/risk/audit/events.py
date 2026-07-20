# ruff: noqa: ANN401, E501
"""Tamper-evident risk audit events and redacted payload construction.

Ensures all pre-trade decisions are documented in a standardized,
non-sensitive format before persistence.
"""

from __future__ import annotations

import hashlib
from collections.abc import Mapping
from typing import Any

from pydantic import Field, JsonValue

from app.services.risk.audit.hash_chain import (
    _coerce_types,
    append_audit_hash,
    verify_risk_audit_chain,
)
from app.services.risk.errors import RiskValidationError as ValidationError
from app.services.risk.models import (
    RiskAuditEvent,
    RiskContract,
    RiskDecisionPackage,
    RiskSeverity,
)
from app.services.risk.models.enums import RiskDecisionStatus
from app.utils.logger import logger
from app.utils.standard import canonical_json, stable_identifier


class AuditRedactionPolicy(RiskContract):
    """Defines sensitive keys to redact and safe keys to retain."""

    redacted_keys: list[str] = Field(
        default_factory=lambda: [
            "password",
            "passphrase",
            "secret",
            "credential",
            "api_key",
            "apikey",
            "authorization",
            "private",
            "account",
            "login",
            "payload",
            "signature",
            "packet",
            "token",
            "key",
        ],
        description="Keys that contain sensitive information.",
    )
    safe_keys: list[str] = Field(
        default_factory=lambda: [
            "rule_key",
            "severity",
            "reason_codes",
            "config_hash",
            "policy_hash",
            "decision_id",
            "request_id",
            "workflow_id",
            "policy_version",
            "policy_scope",
            "symbol",
            "side",
            "volume",
            "requested_size",
            "approved_size",
            "max_allowed_size",
            "price",
            "stop_loss",
            "timestamp",
            "status",
            "calculated_volume",
            "details",
            "positions",
            "pending_orders",
            "in_flight_orders",
            "exposure",
            "var_es",
            "var",
            "es",
            "stress_loss",
            "drawdown",
            "margin",
            "margin_used",
            "margin_usage",
            "drawdown_state",
            "composite_breach_flags",
            "expiry",
            "expiry_time",
            "nonce",
            "approver",
            "approved_action",
        ],
        description="Keys that are safe to expose even if they match sensitive terms.",
    )


class AuditContext(RiskContract):
    """Context holding the evaluation details and metadata for an audit record."""

    proposed_action: Any = Field(None, description="The proposed action payload.")
    previous_hash: str = Field("0" * 64, description="The previous block hash.")
    details: dict[str, Any] = Field(
        default_factory=dict, description="Arbitrary audit context details."
    )


def redact_audit_payload(
    payload: Mapping[str, JsonValue], policy: AuditRedactionPolicy
) -> dict[str, JsonValue]:
    """Removes protected values before persistence/logging.

    Args:
        payload: The payload mapping to redact.
        policy: The redaction policy config.

    Returns:
        dict[str, JsonValue]: Redacted payload dictionary.
    """
    logger.debug("Redacting audit payload according to policy.")

    def _redact(v: Any) -> Any:
        if isinstance(v, dict):
            redacted: dict[str, Any] = {}
            for k, val in v.items():
                k_lower = str(k).lower()
                if k_lower == "decision_token":
                    redacted[k] = None
                elif any(term in k_lower for term in policy.redacted_keys):
                    if k_lower in policy.safe_keys:
                        redacted[k] = _redact(val)
                    else:
                        redacted[k] = "[REDACTED]"
                else:
                    redacted[k] = _redact(val)
            return redacted
        if isinstance(v, list | tuple | set):
            return [_redact(val) for val in v]
        return v

    res = _redact(dict(payload))
    return res if isinstance(res, dict) else {}


def build_canonical_audit_payload(
    decision: RiskDecisionPackage, context: AuditContext
) -> dict[str, JsonValue]:
    """Builds stable, redacted audit material.

    Args:
        decision: The risk decision package.
        context: The audit context holding parameters.

    Returns:
        dict[str, JsonValue]: Canonical redacted details dictionary.
    """
    logger.info(
        "Building canonical audit payload for decision: %s",
        decision.decision_id,
    )

    action_dump = {}
    proposed_action = context.proposed_action
    if hasattr(proposed_action, "model_dump"):
        action_dump = proposed_action.model_dump()
    elif isinstance(proposed_action, dict):
        action_dump = proposed_action

    policy = AuditRedactionPolicy()
    redacted_action = redact_audit_payload(action_dump, policy)
    redacted_decision = redact_audit_payload(decision.model_dump(), policy)

    def _coerce_decimals(val: Any) -> Any:
        if isinstance(val, dict):
            return {k: _coerce_decimals(v) for k, v in val.items()}
        if isinstance(val, list | tuple | set):
            return [_coerce_decimals(v) for v in val]
        return (
            float(val)
            if isinstance(val, float | int) and not isinstance(val, bool)
            else val
        )

    details = {
        "decision": redacted_decision,
        "proposed_action": _coerce_decimals(redacted_action),
    }

    return details


def create_risk_audit_event(
    decision: RiskDecisionPackage,
    context: AuditContext | Any,
    audit_sink: Any = None,
) -> RiskAuditEvent:
    """Produces immutable audit record. Supports V1 active sink writing and pure V2 creation.

    Args:
        decision: RiskDecisionPackage result.
        context: AuditContext (V2) or proposed_action (V1).
        audit_sink: Mandatory state sink (V1 compatibility).

    Returns:
        RiskAuditEvent: Built and chained audit event.
    """
    if audit_sink is not None:
        proposed_action = context
        logger.info("Legacy V1 create_risk_audit_event wrapper invoked.")

        try:
            prev = audit_sink.get_last_event()
        except Exception as e:
            msg = f"Audit persistence query failed: {e}"
            raise ValidationError(msg, code="DATABASE_ERROR") from e

        previous_hash = prev.hash if prev else "0" * 64

        audit_context = AuditContext(
            proposed_action=proposed_action,
            previous_hash=previous_hash,
        )

        event = _create_pure_audit_event(decision, audit_context)

        try:
            audit_sink.write_event(event)
        except Exception as e:
            msg = f"Audit persistence write failed: {e}"
            raise ValidationError(msg, code="DATABASE_ERROR") from e

        return event

    if not isinstance(context, AuditContext):
        context = AuditContext(proposed_action=context, previous_hash="0" * 64)
    return _create_pure_audit_event(decision, context)


def _create_pure_audit_event(
    decision: RiskDecisionPackage, context: AuditContext
) -> RiskAuditEvent:
    """Pure implementation to create a chained RiskAuditEvent."""
    severity_map = {
        RiskDecisionStatus.APPROVE: RiskSeverity.INFO,
        RiskDecisionStatus.REDUCE_SIZE: RiskSeverity.WARNING,
        RiskDecisionStatus.NEEDS_APPROVAL: RiskSeverity.WARNING,
        RiskDecisionStatus.NEEDS_MORE_EVIDENCE: RiskSeverity.WARNING,
        RiskDecisionStatus.REJECT: RiskSeverity.HARD_BREACH,
        RiskDecisionStatus.BLOCK: RiskSeverity.CRITICAL_BREACH,
        RiskDecisionStatus.HALT_STRATEGY: RiskSeverity.EMERGENCY_HALT,
        RiskDecisionStatus.HALT_ALL: RiskSeverity.EMERGENCY_HALT,
    }
    severity = severity_map.get(
        RiskDecisionStatus(decision.status)
        if decision.status in list(RiskDecisionStatus)
        else RiskDecisionStatus.REJECT,
        RiskSeverity.HARD_BREACH,
    )

    details = build_canonical_audit_payload(decision, context)

    payload_hash = hashlib.sha256(
        canonical_json(_coerce_types(details.get("proposed_action", {}))).encode()
    ).hexdigest()

    event_id = stable_identifier(
        {"decision_id": decision.decision_id, "prev_hash": context.previous_hash},
        prefix="event",
    )

    from app.utils.normalization import utc_now

    event = RiskAuditEvent(
        event_id=event_id,
        decision_id=decision.decision_id,
        policy_name=decision.rule_key,
        action_taken=decision.status,
        payload_hash=payload_hash,
        severity=severity,
        previous_hash=context.previous_hash,
        hash="",
        timestamp=utc_now(),
        details=details,
    )

    event.hash = append_audit_hash(context.previous_hash, event.model_dump())
    return event


# Re-export verify_risk_audit_chain to comply with target API expectations in events module.
__all__ = [
    "AuditContext",
    "AuditRedactionPolicy",
    "build_canonical_audit_payload",
    "create_risk_audit_event",
    "redact_audit_payload",
    "verify_risk_audit_chain",
]
