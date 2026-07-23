"""Canonical authorized Risk kill-switch state and recovery policy."""

from __future__ import annotations

import hashlib
from collections.abc import Mapping, Sequence
from datetime import datetime, timedelta
from time import monotonic
from typing import TYPE_CHECKING, Literal

from app.services.risk.config import RiskConfig, compute_config_hash
from app.services.risk.contracts import (
    ApprovalAttestation,
    DecisionState,
    KillSwitchCommand,
    KillSwitchState,
    LimitStatus,
    RiskAuditRecord,
    RiskDecisionPackage,
    RiskDomainError,
    RiskErrorCode,
    RiskLimitResult,
)
from app.utils import AuthContext, canonical_json, logger

if TYPE_CHECKING:
    from app.services.risk.approvals import ApprovalTokenService
    from app.services.risk.audit import RiskAuditChain
    from app.services.risk.audit.storage import _KillSwitchStateStore

_SCOPE_PRECEDENCE = {"global": 0, "portfolio": 1, "strategy": 2, "symbol": 3}


def _utc(value: datetime) -> datetime:
    """Require an aware UTC timestamp.

    Args:
        value: Timestamp to validate.

    Returns:
        Validated timestamp.

    Raises:
        ValueError: If timestamp is not aware UTC.
    """
    logger.debug("Validating kill-switch UTC timestamp")
    if value.tzinfo is None or value.utcoffset() != timedelta(0):
        raise ValueError("kill-switch time must be aware UTC")
    return value


def _identity(prefix: str, material: Mapping[str, object]) -> str:
    """Derive one stable kill-switch SHA-256 identity.

    Args:
        prefix: Identity namespace.
        material: Exact canonical identity material.

    Returns:
        Lowercase hexadecimal identity.
    """
    logger.debug("Deriving canonical Risk kill-switch identity")
    serialized = canonical_json({"prefix": prefix, "material": dict(material)})
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def _command_scope(command: KillSwitchCommand) -> dict[str, str]:
    """Return the exact canonical state scope for one command.

    Args:
        command: Validated kill-switch command.

    Returns:
        Empty global scope or one exact scoped identifier.

    Raises:
        ValueError: If a required scope identifier is absent.
    """
    logger.debug("Normalizing exact Risk kill-switch command scope")
    if command.scope_level == "global":
        return {}
    field = {
        "portfolio": "portfolio_id",
        "strategy": "strategy_id",
        "symbol": "symbol",
    }[command.scope_level]
    value = getattr(command, field)
    if value is None:
        raise ValueError("kill-switch scope identifier is missing")
    return {field: value}


def _revocation_scope(scope: Mapping[str, str]) -> dict[str, str]:
    """Return non-empty token revocation scope including global selector.

    Args:
        scope: Canonical kill-switch state scope.

    Returns:
        Exact non-empty token-state revocation selector.
    """
    logger.debug("Mapping kill-switch scope to approval revocation scope")
    return dict(scope) if scope else {"global": "*"}


def _authorized(
    command: KillSwitchCommand,
    auth: AuthContext,
    config: RiskConfig,
    attestation: ApprovalAttestation | None,
    now: datetime,
) -> bool:
    """Check exact auth, permission, trace, and clearance evidence.

    Args:
        command: Validated requested state change.
        auth: Authenticated caller context.
        config: Active immutable Risk policy.
        attestation: Optional clearance approval evidence.
        now: Checked UTC command time.

    Returns:
        Whether all required authorization evidence is exact and current.
    """
    logger.debug("Checking exact Risk kill-switch authorization evidence")
    trace_matches = (
        auth.request_id == command.request_id
        and auth.workflow_id == command.workflow_id
        and auth.correlation_id == command.correlation_id
        and auth.tenant_or_environment == config.profile
        and command.requested_at <= now
    )
    permissions = (
        config.kill_switch_activation_permissions
        if command.action == "activate"
        else config.kill_switch_clearance_permissions
    )
    if not trace_matches or not set(permissions).issubset(auth.permissions):
        return False
    if command.action == "activate":
        return True
    if attestation is None:
        return False
    scope = _revocation_scope(_command_scope(command))
    return (
        attestation.principal_id == auth.principal_id
        and attestation.action == "risk.kill.clear"
        and dict(attestation.scope) == scope
        and attestation.policy_ref == compute_config_hash(config)
        and attestation.policy_version == config.policy_version
        and attestation.issued_at <= now < attestation.expires_at
        and attestation.request_id == command.request_id
        and attestation.workflow_id == command.workflow_id
        and attestation.correlation_id == command.correlation_id
    )


def _audit_input(
    command: KillSwitchCommand,
    state: KillSwitchState,
    config_hash: str,
    revoked_count: int,
    now: datetime,
) -> RiskAuditRecord:
    """Build one unsealed material kill-switch audit record.

    Args:
        command: Applied command.
        state: Durably stored resulting state.
        config_hash: Active exact Risk configuration hash.
        revoked_count: Number of approvals revoked on activation.
        now: Checked UTC apply time.

    Returns:
        Unsealed secret-safe audit input.
    """
    logger.debug("Building one material Risk kill-switch audit input")
    return RiskAuditRecord(
        record_id=_identity(
            "kill_switch.audit",
            {"state_id": state.state_id, "version": state.version},
        ),
        event_type=f"risk.kill_switch.{command.action}",
        payload={
            "scope_level": state.scope_level,
            "scope": dict(state.scope),
            "state": state.state,
            "reason": state.reason,
            "version": state.version,
            "revoked_count": revoked_count,
        },
        evidence_refs={"state": state.state_id, "command": command.request_id},
        config_hash=config_hash,
        decision_id=None,
        occurred_at=now,
        sequence=None,
        previous_hash=None,
        record_hash=None,
        sealed=False,
        request_id=command.request_id,
        correlation_id=command.correlation_id,
    )


def _validate_apply_request(
    command: KillSwitchCommand,
    current: KillSwitchState,
    auth: AuthContext,
    config: RiskConfig,
    attestation: ApprovalAttestation | None,
    now: datetime,
    scope: Mapping[str, str],
) -> None:
    """Validate command time, scope, version target, and authorization.

    Args:
        command: Requested state change.
        current: Exact current state.
        auth: Authenticated caller context.
        config: Active immutable Risk policy.
        attestation: Optional clearance evidence.
        now: Checked UTC apply time.
        scope: Canonical command scope.

    Raises:
        RiskDomainError: If command policy or authorization fails.
    """
    logger.debug("Validating complete Risk kill-switch apply request")
    tolerance = timedelta(seconds=float(config.clock_skew_tolerance_seconds or 0))
    if abs(command.requested_at - now) > tolerance:
        raise RiskDomainError(
            RiskErrorCode.POLICY_BLOCKED, "kill-switch command clock invalid"
        )
    if (
        current.scope_level != command.scope_level
        or dict(current.scope) != dict(scope)
        or not _authorized(command, auth, config, attestation, now)
    ):
        raise RiskDomainError(
            RiskErrorCode.PERMISSION_DENIED,
            "kill-switch authorization or scope invalid",
        )


def _require_persisted(persisted: bool) -> None:
    """Require atomic canonical state persistence success.

    Args:
        persisted: Receiver-owned compare-and-swap outcome.

    Raises:
        RiskDomainError: If version-exact persistence conflicts.
    """
    logger.debug("Requiring canonical kill-switch compare-and-swap success")
    if not persisted:
        raise RiskDomainError(
            RiskErrorCode.STORAGE_ERROR, "kill-switch version conflict"
        )


def _validate_check_request(
    scope: Mapping[str, str], config: RiskConfig, auth: AuthContext
) -> None:
    """Validate kill-switch read-side scope and environment context.

    Args:
        scope: Exact action scope.
        config: Active immutable Risk policy.
        auth: Authenticated caller trace context.

    Raises:
        RiskDomainError: If scope or environment is invalid.
    """
    logger.debug("Validating Risk kill-switch read-side request")
    if not scope or auth.tenant_or_environment != config.profile:
        raise RiskDomainError(
            RiskErrorCode.POLICY_BLOCKED, "kill-switch check scope invalid"
        )


def apply_kill_switch_command(
    command: KillSwitchCommand,
    current: KillSwitchState,
    auth: AuthContext,
    approvals: ApprovalTokenService,
    audit: RiskAuditChain,
    store: _KillSwitchStateStore,
    config: RiskConfig,
    *,
    attestation: ApprovalAttestation | None = None,
    now: datetime,
) -> KillSwitchState:
    """Authorize and atomically apply one canonical kill-switch command.

    Args:
        command: Requested activation or clearance.
        current: Exact current versioned scope state.
        auth: Authenticated caller context.
        approvals: Durable approval-token revocation coordinator.
        audit: Tamper-evident Risk audit chain.
        store: Atomic canonical kill-switch state store.
        config: Active immutable Risk policy.
        attestation: Required matching approval evidence for clearance only.
        now: Caller-supplied UTC apply time.

    Returns:
        Durably stored canonical resulting state.

    Raises:
        RiskDomainError: If authorization, scope, version, persistence,
            revocation, or audit fails.
    """
    logger.warning("Applying authorized canonical Risk kill-switch command")
    started_at = monotonic()
    try:
        checked_now = _utc(now)
        scope = _command_scope(command)
        _validate_apply_request(
            command, current, auth, config, attestation, checked_now, scope
        )
        state_value: Literal["active", "inactive"] = (
            "active" if command.action == "activate" else "inactive"
        )
        new_state = KillSwitchState(
            state_id=_identity(
                "kill_switch.state",
                {
                    "scope_level": command.scope_level,
                    "scope": scope,
                    "state": state_value,
                    "version": current.version + 1,
                    "command": command.request_id,
                },
            ),
            scope_level=command.scope_level,
            scope=scope,
            state=state_value,
            reason=command.reason,
            version=current.version + 1,
            updated_at=checked_now,
        )
        persisted = store.compare_and_swap(
            new_state,
            expected_version=current.version,
            timeout_seconds=config.dependency_timeouts_seconds.get("kill_switch"),
        )
        _require_persisted(persisted)
        revoked_count = 0
        if command.action == "activate":
            revoked_count = approvals.revoke_scope(
                _revocation_scope(scope), command.reason, now=checked_now
            )
        config_hash = compute_config_hash(config)
        audit.append(
            _audit_input(command, new_state, config_hash, revoked_count, checked_now)
        )
        logger.bind(
            request_id=command.request_id,
            workflow_id=command.workflow_id,
            correlation_id=command.correlation_id,
            verdict=new_state.state,
            reason_codes=(new_state.reason,),
            latency_ms=round((monotonic() - started_at) * 1000, 3),
            evidence_refs={"state": new_state.state_id},
            config_hash=config_hash,
        ).info("Completed canonical Risk kill-switch state decision")
        return new_state
    except RiskDomainError:
        logger.error("Risk kill-switch command failed closed")
        raise
    except Exception as error:
        raise RiskDomainError(
            RiskErrorCode.STORAGE_ERROR, "kill-switch persistence unavailable"
        ) from error


def _applicable_states(
    states: Sequence[KillSwitchState], scope: Mapping[str, str]
) -> tuple[KillSwitchState, ...]:
    """Select and order states applicable to one action scope.

    Args:
        states: Candidate canonical scope states.
        scope: Requested action scope.

    Returns:
        Applicable states in global-to-symbol precedence.
    """
    logger.debug("Selecting applicable hierarchical Risk kill-switch states")
    selected = (
        state
        for state in states
        if state.scope_level == "global"
        or all(scope.get(key) == value for key, value in state.scope.items())
    )
    return tuple(sorted(selected, key=lambda item: _SCOPE_PRECEDENCE[item.scope_level]))


def check_risk_kill_switch(
    states: Sequence[KillSwitchState],
    scope: Mapping[str, str],
    config: RiskConfig,
    auth: AuthContext,
    *,
    reconciled: bool,
    now: datetime,
) -> RiskDecisionPackage:
    """Return deterministic hierarchical block or recovery eligibility.

    Args:
        states: Canonical state collection.
        scope: Exact action portfolio/strategy/symbol scope.
        config: Active immutable Risk policy.
        auth: Authenticated caller trace context.
        reconciled: Whether Trading reconciliation has completed.
        now: Caller-supplied UTC evaluation time.

    Returns:
        Non-executing canonical block or recovery decision.

    Raises:
        RiskDomainError: If time, scope, policy, or state evidence is invalid.
    """
    logger.info("Checking hierarchical Risk kill-switch block and recovery state")
    started_at = monotonic()
    try:
        checked_now = _utc(now)
        _validate_check_request(scope, config, auth)
        applicable = _applicable_states(states, scope)
        active = next((item for item in applicable if item.state == "active"), None)
        unknown = next((item for item in applicable if item.state == "unknown"), None)
        if active is not None:
            reason = RiskErrorCode.KILL_SWITCH_ACTIVE
        elif unknown is not None or not applicable:
            reason = RiskErrorCode.KILL_SWITCH_UNKNOWN
        elif not reconciled:
            reason = RiskErrorCode.POLICY_BLOCKED
        else:
            reason = None
        status = LimitStatus.PASS if reason is None else LimitStatus.BLOCKED
        refs = tuple(item.state_id for item in applicable) or ("kill-switch:missing",)
        check = RiskLimitResult(
            limit_id="kill_switch",
            status=status,
            observed_value=None,
            threshold_value=None,
            reason_code=reason,
            evidence_refs=refs,
            precedence=0,
        )
        config_hash = compute_config_hash(config)
        decision_id = _identity(
            "kill_switch.check",
            {
                "states": refs,
                "scope": dict(scope),
                "reconciled": reconciled,
                "config_hash": config_hash,
            },
        )
        decision = RiskDecisionPackage(
            decision_id=decision_id,
            intent_id=None,
            state=DecisionState.APPROVE if reason is None else DecisionState.BLOCK,
            requested_size=None,
            approved_size=None,
            ordered_checks=(check,),
            primary_failure_limit=None if reason is None else "kill_switch",
            composite_breach_flags=() if reason is None else ("kill_switch",),
            evidence_refs={
                "kill_switch": ",".join(refs),
                "config": config_hash,
            },
            config_hash=config_hash,
            concurrency_disclosure="not_applicable:kill_switch_check",
            recommendations=(
                ("trading_reconciliation_required",)
                if reason is RiskErrorCode.POLICY_BLOCKED
                else ("risk_increase_blocked",)
                if reason is not None
                else ("recovery_eligible",)
            ),
            issued_at=checked_now,
            expires_at=checked_now
            + timedelta(seconds=float(config.decision_ttl_seconds)),
            token=None,
            request_id=auth.request_id,
            workflow_id=auth.workflow_id,
            correlation_id=auth.correlation_id,
        )
        logger.bind(
            request_id=decision.request_id,
            workflow_id=decision.workflow_id,
            correlation_id=decision.correlation_id,
            verdict=decision.state.value,
            reason_codes=() if reason is None else (reason.value,),
            latency_ms=round((monotonic() - started_at) * 1000, 3),
            evidence_refs=dict(decision.evidence_refs),
            config_hash=config_hash,
        ).info("Completed hierarchical Risk kill-switch decision")
        return decision
    except RiskDomainError:
        logger.error("Risk kill-switch check failed closed")
        raise
    except (KeyError, TypeError, ValueError) as error:
        raise RiskDomainError(
            RiskErrorCode.POLICY_BLOCKED, "kill-switch state evidence invalid"
        ) from error


__all__ = ["apply_kill_switch_command", "check_risk_kill_switch"]
