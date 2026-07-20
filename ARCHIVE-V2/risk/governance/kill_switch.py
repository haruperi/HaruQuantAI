# ruff: noqa: ANN401, C901, PLR0911, PLR0912, PLR2004, PLW0603, BLE001, EM102, E501
"""Emergency kill switch service and state manager.

Handles global, portfolio, strategy, symbol, and currency-level halts.
Supports persistence, gated resume approvals, and auto-triggering on breaches.
Also exposes a pure, canonically-typed V2 calculation surface
(:class:`KillSwitchService`, :func:`request_kill_switch_trigger`,
:func:`validate_resume_request`, :func:`clear_kill_switch_after_approval`) and
a dual-dispatch :func:`check_risk_kill_switch` that accepts either the V1
``(scope: str, target: str) -> bool`` calling convention or the canonical V2
``(scope: KillSwitchScope, state: KillSwitchState) -> KillSwitchAssessment``
convention.

Exports:
    KillSwitchScope, KillSwitchManager, RiskKillSwitch, PortfolioKillSwitch,
    StrategyKillSwitch, get_kill_switch_manager, trigger_kill_switch,
    resume_after_kill_switch, check_risk_kill_switch, KillSwitchService,
    KillSwitchState, KillSwitchAssessment, KillSwitchTriggerRequest,
    KillSwitchResumeRequest, ApprovalContext.
"""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from threading import RLock
from typing import TYPE_CHECKING, Any, Protocol, overload

from app.services.risk.errors import RiskValidationError as ValidationError
from app.services.risk.limits import LimitResult
from app.services.risk.models import (
    KillSwitchStateEnum,
    RiskAssessmentRequest,
    RiskContract,
    RiskDecisionStatus,
    RiskReasonCode,
    RiskSeverity,
)
from app.utils.logger import logger
from app.utils.security import redact_mapping
from pydantic import Field

if TYPE_CHECKING:
    from app.services.risk.storage.ports import RiskStateStore
    from app.services.risk.validations import ValidationResult


class _KillSwitchAuditBus(Protocol):
    """Minimal audit bus protocol for kill-switch audit events."""

    def publish(self, event: dict[str, object]) -> object:
        """Publish an audit event."""


def _build_kill_switch_event(
    *,
    event_type: str,
    source: str,
    severity: str,
    payload: dict[str, object],
) -> dict[str, object]:
    """Build a redacted kill-switch audit event."""
    return {
        "event_id": f"event_{uuid.uuid4()}",
        "event_type": event_type,
        "source": source,
        "severity": severity,
        "timestamp": datetime.now(UTC).isoformat(),
        "payload": redact_mapping(payload),
        "metadata": {},
    }


__all__ = [
    "ApprovalContext",
    "KillSwitchAssessment",
    "KillSwitchManager",
    "KillSwitchResumeRequest",
    "KillSwitchScope",
    "KillSwitchService",
    "KillSwitchState",
    "KillSwitchTriggerRequest",
    "PortfolioKillSwitch",
    "RiskKillSwitch",
    "StrategyKillSwitch",
    "check_risk_kill_switch",
    "clear_kill_switch_after_approval",
    "get_kill_switch_manager",
    "request_kill_switch_trigger",
    "resume_after_kill_switch",
    "trigger_kill_switch",
    "validate_resume_request",
]


class KillSwitchScope(StrEnum):
    """Scope boundaries for kill switches."""

    GLOBAL = "global"
    PORTFOLIO = "portfolio"
    STRATEGY = "strategy"
    SYMBOL = "symbol"
    CURRENCY = "currency"


@dataclass(frozen=True)
class RiskKillSwitch:
    """Typed immutable snapshot of a kill-switch record at a given scope.

    Attributes:
        scope: The KillSwitchScope this record belongs to.
        target: Target identifier (strategy ID, symbol, currency, or '*').
        state: Current KillSwitchStateEnum value.
        reason: Structured KillSwitchReason or free-text explanation, if any.
        triggered_at: UTC timestamp of the last state change, if any.
        triggered_by: Identifier of the system or operator that triggered, if any.
    """

    scope: KillSwitchScope
    target: str
    state: KillSwitchStateEnum
    reason: str | None
    triggered_at: datetime | None
    triggered_by: str | None


@dataclass(frozen=True)
class PortfolioKillSwitch(RiskKillSwitch):
    """Kill-switch snapshot scoped to portfolio level.

    Always carries scope=KillSwitchScope.PORTFOLIO. Provided for typed
    consumers that operate exclusively at the portfolio scope.
    """


@dataclass(frozen=True)
class StrategyKillSwitch(RiskKillSwitch):
    """Kill-switch snapshot scoped to a single strategy.

    Always carries scope=KillSwitchScope.STRATEGY. Provided for typed
    consumers that operate exclusively at the strategy scope.
    """


class KillSwitchManager:
    """Thread-safe manager for quantitative trading safety kill switches.

    Manages active, inactive, and locked states across different scopes.
    Persists changes to a local storage file to survive system restarts.
    """

    def __init__(self, persistence_path: str | Path | None = None) -> None:
        """Initialize KillSwitchManager with default states and optional persistence.

        Args:
            persistence_path: Local JSON path to read/write states.
        """
        self._lock = RLock()
        self.persistence_path = Path(persistence_path) if persistence_path else None

        # Base default states configuration
        self.states: dict[str, Any] = {
            "global": {
                "state": KillSwitchStateEnum.INACTIVE,
                "reason": None,
                "triggered_at": None,
                "triggered_by": None,
            },
            "portfolio": {
                "state": KillSwitchStateEnum.INACTIVE,
                "reason": None,
                "triggered_at": None,
                "triggered_by": None,
            },
            "strategies": {},  # strat_id -> dict
            "symbols": {},  # symbol -> dict
            "currencies": {},  # currency -> dict
        }
        self.load()
        logger.debug("KillSwitchManager initialized.")

    def load(self) -> None:
        """Load states from local JSON persistence path.

        Falls closed on missing keys, type mismatches, or file corruption.
        """
        if not self.persistence_path or not self.persistence_path.exists():
            return

        with self._lock:
            try:
                with self.persistence_path.open("r", encoding="utf-8") as f:
                    data = json.load(f)

                # Basic structural validation
                required_keys = {
                    "global",
                    "portfolio",
                    "strategies",
                    "symbols",
                    "currencies",
                }
                if not required_keys.issubset(data.keys()):
                    logger.warning(
                        "Corrupt kill switch persistence: missing root keys."
                    )
                    self._fail_closed()
                    return

                self.states = data
            except Exception as e:
                logger.warning(
                    f"Failed to load kill switch states, failing closed: {e}"
                )
                self._fail_closed()

    def _fail_closed(self) -> None:
        """Sets all base states to locked/active to prevent unauthorized trading."""
        self.states["global"] = {
            "state": KillSwitchStateEnum.LOCKED,
            "reason": "Persistence file corruption recovery",
            "triggered_at": datetime.now(UTC).isoformat(),
            "triggered_by": "system_recovery",
        }

    def save(self) -> None:
        """Write current states to persistence path."""
        if not self.persistence_path:
            return

        with self._lock:
            try:
                self.persistence_path.parent.mkdir(parents=True, exist_ok=True)
                with self.persistence_path.open("w", encoding="utf-8") as f:
                    # Coerce Decimal and timestamps if any
                    json.dump(self.states, f, indent=2)
            except Exception as e:
                logger.error(f"Failed to save kill switch states: {e}")

    def trigger(
        self,
        scope: str,
        target: str,
        reason: str,
        triggered_by: str = "system",
        audit_bus: _KillSwitchAuditBus | None = None,
    ) -> None:
        """Trigger an emergency halt/kill switch for a target scope.

        Args:
            scope: One of global, portfolio, strategy, symbol, currency.
            target: Identifier key (e.g. strategy ID, symbol name, '*' for global/portfolio).
            reason: Text detail explaining cause.
            triggered_by: Origin/initiator name.
            audit_bus: Optional audit bus to publish trigger event.

        Raises:
            ValidationError: If target scope is unknown.
        """
        clean_scope = scope.lower().strip()
        timestamp = datetime.now(UTC).isoformat()

        with self._lock:
            state_record = {
                "state": KillSwitchStateEnum.ACTIVE,
                "reason": reason,
                "triggered_at": timestamp,
                "triggered_by": triggered_by,
            }

            if clean_scope == KillSwitchScope.GLOBAL:
                self.states["global"] = state_record
            elif clean_scope == KillSwitchScope.PORTFOLIO:
                self.states["portfolio"] = state_record
            elif clean_scope == KillSwitchScope.STRATEGY:
                self.states["strategies"][target] = state_record
            elif clean_scope == KillSwitchScope.SYMBOL:
                self.states["symbols"][target] = state_record
            elif clean_scope == KillSwitchScope.CURRENCY:
                self.states["currencies"][target] = state_record
            else:
                raise ValidationError(
                    f"Invalid scope '{scope}' for kill switch trigger."
                )

            self.save()

            # Emit audit event
            logger.warning(
                f"Emergency kill switch triggered: scope={scope}, target={target}, reason={reason}"
            )
            if audit_bus:
                try:
                    event = _build_kill_switch_event(
                        event_type="risk.kill_switch.triggered",
                        source="kill_switch_governor",
                        severity="critical",
                        payload={
                            "scope": scope,
                            "target": target,
                            "reason": reason,
                            "triggered_by": triggered_by,
                            "triggered_at": timestamp,
                        },
                    )
                    audit_bus.publish(event)
                except Exception as e:
                    logger.error(f"Failed to publish kill switch event: {e}")

    def resume(
        self,
        scope: str,
        target: str,
        approval_token: str | None = None,
        operator_role: str | None = None,
        audit_bus: _KillSwitchAuditBus | None = None,
    ) -> None:
        """Deactivate a triggered kill switch after governed approval checks.

        Args:
            scope: Target scope.
            target: Identifier key.
            approval_token: Optional approval token validated by policy.
            operator_role: Optional role of the operator (e.g. 'admin', 'compliance').
            audit_bus: Optional audit bus.

        Raises:
            ValidationError: If approval requirements are not satisfied.
        """
        clean_scope = scope.lower().strip()

        with self._lock:
            # 1. Retrieve current state
            record: dict[str, Any] | None = None
            if clean_scope == KillSwitchScope.GLOBAL:
                record = self.states["global"]
            elif clean_scope == KillSwitchScope.PORTFOLIO:
                record = self.states["portfolio"]
            elif clean_scope == KillSwitchScope.STRATEGY:
                record = self.states["strategies"].get(target)
            elif clean_scope == KillSwitchScope.SYMBOL:
                record = self.states["symbols"].get(target)
            elif clean_scope == KillSwitchScope.CURRENCY:
                record = self.states["currencies"].get(target)
            else:
                raise ValidationError(f"Invalid scope '{scope}' for resume.")

            if not record or record.get("state") == KillSwitchStateEnum.INACTIVE:
                # Already inactive
                return

            current_state = record.get("state")

            # 2. Enforce governed approval gate
            # Locked state requires explicit admin/compliance roles and cannot be cleared by token alone
            if current_state == KillSwitchStateEnum.LOCKED:
                if operator_role not in {"admin", "compliance"}:
                    raise ValidationError(
                        "Cannot resume locked kill switch without compliance or admin role.",
                        code="PERMISSION_DENIED",
                    )
            else:
                # Active state requires admin/compliance role OR a valid approval token
                has_privilege = operator_role in {"admin", "compliance"}
                has_token = bool(approval_token and approval_token.strip())
                if not has_privilege and not has_token:
                    raise ValidationError(
                        "Governed resume requires a valid approval token or compliance/admin operator role.",
                        code="APPROVAL_REQUIRED",
                    )

            # 3. Clear state record
            inactive_record = {
                "state": KillSwitchStateEnum.INACTIVE,
                "reason": None,
                "triggered_at": None,
                "triggered_by": None,
            }

            if clean_scope == KillSwitchScope.GLOBAL:
                self.states["global"] = inactive_record
            elif clean_scope == KillSwitchScope.PORTFOLIO:
                self.states["portfolio"] = inactive_record
            elif clean_scope == KillSwitchScope.STRATEGY:
                self.states["strategies"].pop(target, None)
            elif clean_scope == KillSwitchScope.SYMBOL:
                self.states["symbols"].pop(target, None)
            elif clean_scope == KillSwitchScope.CURRENCY:
                self.states["currencies"].pop(target, None)

            self.save()

            logger.info(f"Kill switch resumed: scope={scope}, target={target}")
            if audit_bus:
                try:
                    event = _build_kill_switch_event(
                        event_type="risk.kill_switch.resumed",
                        source="kill_switch_governor",
                        severity="info",
                        payload={
                            "scope": scope,
                            "target": target,
                            "resumed_by": operator_role or "token",
                            "resumed_at": datetime.now(UTC).isoformat(),
                        },
                    )
                    audit_bus.publish(event)
                except Exception as e:
                    logger.error(f"Failed to publish resume event: {e}")

    def is_blocked(self, scope: str, target: str, is_live: bool = False) -> bool:
        """Verify whether trading is blocked for a given target.

        Supports hierarchical fallback checks:
        Checks global -> portfolio -> target (strategy, symbol, or quote/base currency legs).

        Args:
            scope: target query scope ('strategy', 'symbol', or 'currency').
            target: identifier key to verify.
            is_live: True if environment is live-sensitive (triggers strict fail-closed).

        Returns:
            bool: True if blocked (kill switch active/locked).
        """
        clean_scope = scope.lower().strip()

        def _is_active(record: Any) -> bool:
            if not isinstance(record, dict):
                return is_live  # Fail closed in live modes if shape is corrupted
            state = record.get("state")
            # Explicitly map every known state to a blocked/non-blocked decision.
            # UNKNOWN always fails closed regardless of live mode.
            if state == KillSwitchStateEnum.INACTIVE:
                return False
            if state == KillSwitchStateEnum.ACTIVE:
                return True
            if state == KillSwitchStateEnum.LOCKED:
                return True
            if state == KillSwitchStateEnum.TRIGGERED:
                return True  # halt signalled → treat as blocked until propagated
            if state == KillSwitchStateEnum.PENDING_RESUME:
                return True  # still blocked until fully deactivated
            # UNKNOWN or any unrecognised value → always fail closed
            return True

        with self._lock:
            # 1. Check Global
            if _is_active(self.states.get("global")):
                return True
            if clean_scope == KillSwitchScope.GLOBAL:
                return False

            # 2. Check Portfolio
            if _is_active(self.states.get("portfolio")):
                return True
            if clean_scope == KillSwitchScope.PORTFOLIO:
                return False

            # 3. Check Target-level specific halts
            if clean_scope == KillSwitchScope.STRATEGY:
                return _is_active(self.states["strategies"].get(target))

            if clean_scope == KillSwitchScope.SYMBOL:
                # Check symbol-level halt
                if _is_active(self.states["symbols"].get(target)):
                    return True

                # Check currency leg halts for base/quote legs
                # Extract currency legs by convention (e.g. first 3 and last 3 chars of symbol)
                if len(target) == 6:
                    base_ccy = target[:3].upper()
                    quote_ccy = target[3:].upper()
                    if _is_active(self.states["currencies"].get(base_ccy)):
                        return True
                    if _is_active(self.states["currencies"].get(quote_ccy)):
                        return True

            if clean_scope == KillSwitchScope.CURRENCY:
                return _is_active(self.states["currencies"].get(target))

            return False

    def evaluate_triggers(
        self,
        request: RiskAssessmentRequest,
        limit_results: list[LimitResult],
        is_live: bool = False,
        audit_bus: _KillSwitchAuditBus | None = None,
    ) -> list[str]:
        """Statelessly parse request context and limit results to trigger switches.

        Args:
            request: Active pre-trade risk query payload.
            limit_results: Stateless list of limit checks executed.
            is_live: True if environment is live-sensitive.
            audit_bus: Optional audit bus to dispatch audit payloads.

        Returns:
            list[str]: Names of scopes triggered in this review.
        """
        triggered_scopes: list[str] = []
        ctx = request.market_context or {}

        # 1. Manual Operator Halt
        if ctx.get("manual_operator_halt", False):
            self.trigger(
                scope="global",
                target="*",
                reason="Manual operator halt requested",
                triggered_by=ctx.get("operator_id", "operator"),
                audit_bus=audit_bus,
            )
            triggered_scopes.append("global")

        # 2. Audit-chain failure
        if ctx.get("audit_chain_verification_failed", False):
            # Audit failures lock the switch globally to require manual administrative reset
            with self._lock:
                self.states["global"] = {
                    "state": KillSwitchStateEnum.LOCKED,
                    "reason": "Audit chain verification failed",
                    "triggered_at": datetime.now(UTC).isoformat(),
                    "triggered_by": "audit_engine",
                }
                self.save()
            logger.critical(
                "Global kill switch locked due to audit-chain verification failure!"
            )
            triggered_scopes.append("global")

        # 3. Portfolio reconciliation check
        reconciliation_active = ctx.get("portfolio_reconciliation_active", True)
        portfolio_unreconciled = ctx.get("portfolio_unreconciled", False)
        if not reconciliation_active or portfolio_unreconciled:
            self.trigger(
                scope="portfolio",
                target="*",
                reason="Portfolio reconciliation failure or inactive monitoring",
                triggered_by="reconciliation_service",
                audit_bus=audit_bus,
            )
            triggered_scopes.append("portfolio")

        # 4. Broker Disconnect
        if is_live and ctx.get("provider_status") == "disconnected":
            self.trigger(
                scope="global",
                target="*",
                reason="Broker terminal disconnected in live execution mode",
                triggered_by="broker_monitor",
                audit_bus=audit_bus,
            )
            triggered_scopes.append("global")

        # 5. Evaluate breaches inside Limit Results
        for res in limit_results:
            if not res.breached:
                continue

            # Check for hard daily loss
            if res.limit_name == "daily_loss_limit" and res.status in {
                RiskDecisionStatus.REJECT,
                RiskDecisionStatus.BLOCK,
            }:
                self.trigger(
                    scope="global",
                    target="*",
                    reason=f"Hard daily loss threshold breached: {res.message}",
                    triggered_by="limit_engine",
                    audit_bus=audit_bus,
                )
                triggered_scopes.append("global")

            # Check for total drawdown limit
            if (
                res.limit_name == "drawdown_limit"
                and res.status
                in {
                    RiskDecisionStatus.REJECT,
                    RiskDecisionStatus.BLOCK,
                }
                and res.severity
                in {RiskSeverity.HARD_BREACH, RiskSeverity.CRITICAL_BREACH}
            ):
                self.trigger(
                    scope="global",
                    target="*",
                    reason=f"Total drawdown limit breached: {res.message}",
                    triggered_by="limit_engine",
                    audit_bus=audit_bus,
                )
                triggered_scopes.append("global")

            # Check for extreme spread event
            if res.limit_name == "spread_limit" and res.severity in {
                RiskSeverity.CRITICAL_BREACH,
                RiskSeverity.EMERGENCY_HALT,
            }:
                symbol = (
                    request.proposed_action.symbol
                    if hasattr(request.proposed_action, "symbol")
                    else "*"
                )
                self.trigger(
                    scope="symbol",
                    target=str(symbol),
                    reason=f"Extreme market spread event: {res.message}",
                    triggered_by="limit_engine",
                    audit_bus=audit_bus,
                )
                triggered_scopes.append("symbol")

            # Check for margin emergency (usage limit or free margin block)
            if (
                res.limit_name in {"margin_limit", "free_margin_check"}
                and res.status == RiskDecisionStatus.BLOCK
            ):
                self.trigger(
                    scope="portfolio",
                    target="*",
                    reason=f"Critical margin emergency triggered: {res.message}",
                    triggered_by="limit_engine",
                    audit_bus=audit_bus,
                )
                triggered_scopes.append("portfolio")

        return triggered_scopes


# Global singleton instance holder
_global_kill_switch_manager: KillSwitchManager | None = None
_manager_lock = RLock()


def get_kill_switch_manager(
    persistence_path: str | Path | None = None,
) -> KillSwitchManager:
    """Retrieve or initialize the global thread-safe KillSwitchManager instance.

    Args:
        persistence_path: Output target path for state serialization.

    Returns:
        KillSwitchManager: Singleton instance.
    """
    global _global_kill_switch_manager
    with _manager_lock:
        if _global_kill_switch_manager is None:
            _global_kill_switch_manager = KillSwitchManager(
                persistence_path=persistence_path
            )
        return _global_kill_switch_manager


def trigger_kill_switch(
    scope: str,
    target: str,
    reason: str,
    triggered_by: str = "system",
    audit_bus: _KillSwitchAuditBus | None = None,
) -> None:
    """Module-level convenience function to trigger a kill switch on the global manager.

    Delegates to :meth:`KillSwitchManager.trigger` on the singleton instance.
    This is the recommended entry point for external callers that do not hold
    a direct reference to the manager.

    Args:
        scope: Kill switch scope (e.g. 'global', 'strategy', 'symbol').
        target: Target identifier (e.g. strategy ID, symbol name, or '*').
        reason: Human-readable explanation for the trigger.
        triggered_by: Identifier of the operator or system component.
        audit_bus: Optional audit bus for audit event publication.
    """
    manager = get_kill_switch_manager()
    manager.trigger(
        scope=scope,
        target=target,
        reason=reason,
        triggered_by=triggered_by,
        audit_bus=audit_bus,
    )


def resume_after_kill_switch(
    scope: str,
    target: str,
    approval_token: str | None = None,
    operator_role: str | None = None,
    audit_bus: _KillSwitchAuditBus | None = None,
) -> None:
    """Module-level convenience function to resume trading after a governed kill switch.

    Delegates to :meth:`KillSwitchManager.resume` on the singleton instance.
    Resume is gated: requires either a valid approval token or admin/compliance
    operator role. Locked states require an admin/compliance role; tokens alone
    are insufficient.

    Args:
        scope: Kill switch scope to resume.
        target: Target identifier to resume.
        approval_token: Optional approval token from a governed approval workflow.
        operator_role: Operator role (e.g. 'admin', 'compliance').
        audit_bus: Optional audit bus for audit event publication.

    Raises:
        ValidationError: If approval requirements are not satisfied.
    """
    manager = get_kill_switch_manager()
    manager.resume(
        scope=scope,
        target=target,
        approval_token=approval_token,
        operator_role=operator_role,
        audit_bus=audit_bus,
    )


class KillSwitchState(RiskContract):
    """Typed canonical snapshot of a kill-switch state record (V2)."""

    state: KillSwitchStateEnum = Field(..., description="Current kill-switch state.")
    reason: str | None = Field(default=None, description="Trigger reason, if any.")
    triggered_at: datetime | None = Field(
        default=None, description="UTC timestamp of the last state change."
    )
    triggered_by: str | None = Field(
        default=None, description="Operator or system component that triggered."
    )


class KillSwitchAssessment(RiskContract):
    """Outcome of a canonical kill-switch scope/state evaluation (V2)."""

    scope: KillSwitchScope = Field(..., description="Evaluated kill-switch scope.")
    target: str = Field(..., description="Evaluated target identifier.")
    blocked: bool = Field(..., description="True if trading is blocked.")
    state: KillSwitchStateEnum = Field(..., description="Evaluated kill-switch state.")
    reason_code: RiskReasonCode = Field(..., description="Stable reason code.")
    message: str = Field(..., description="Human-readable outcome message.")


class KillSwitchTriggerRequest(RiskContract):
    """Canonical request to trigger a governed kill-switch transition (V2)."""

    scope: KillSwitchScope = Field(..., description="Target kill-switch scope.")
    target: str = Field(..., description="Target identifier.")
    reason: str = Field(..., description="Human-readable trigger reason.")
    triggered_by: str = Field(
        default="system", description="Operator or system component."
    )


class KillSwitchResumeRequest(RiskContract):
    """Canonical request to resume a governed kill-switch after approval (V2)."""

    scope: KillSwitchScope = Field(..., description="Target kill-switch scope.")
    target: str = Field(..., description="Target identifier.")
    approval_token: str | None = Field(
        default=None, description="Optional governed approval token."
    )
    operator_role: str | None = Field(
        default=None, description="Optional operator role (e.g. 'admin')."
    )


class ApprovalContext(RiskContract):
    """Canonical operator/approval context for a resume request (V2)."""

    operator_role: str | None = Field(default=None, description="Operator role.")
    approval_token: str | None = Field(
        default=None, description="Governed approval token."
    )


_BLOCKING_STATES = frozenset(
    {
        KillSwitchStateEnum.ACTIVE,
        KillSwitchStateEnum.LOCKED,
        KillSwitchStateEnum.TRIGGERED,
        KillSwitchStateEnum.PENDING_RESUME,
        KillSwitchStateEnum.UNKNOWN,
    }
)


def _check_risk_kill_switch_v1(scope: str, target: str) -> bool:
    """V1 kill-switch check delegating to the global manager singleton."""
    manager = get_kill_switch_manager()
    return manager.is_blocked(scope, target)


def _check_risk_kill_switch_v2(
    scope: KillSwitchScope, state: KillSwitchState
) -> KillSwitchAssessment:
    """V2 canonical kill-switch check from an already-resolved state snapshot."""
    blocked = state.state in _BLOCKING_STATES
    logger.info(f"Canonical kill switch check: scope={scope}, blocked={blocked}.")
    return KillSwitchAssessment(
        scope=scope,
        target="*",
        blocked=blocked,
        state=state.state,
        reason_code=(
            RiskReasonCode.KILL_SWITCH_ACTIVE if blocked else RiskReasonCode.OK
        ),
        message=(
            f"Kill switch state '{state.state}' blocks trading."
            if blocked
            else f"Kill switch state '{state.state}' permits trading."
        ),
    )


@overload
def check_risk_kill_switch(scope: str, target: str) -> bool: ...


@overload
def check_risk_kill_switch(
    scope: KillSwitchScope, state: KillSwitchState
) -> KillSwitchAssessment: ...


def check_risk_kill_switch(*args: Any, **kwargs: Any) -> Any:
    """Check kill-switch status, supporting V1 and V2 signatures.

    Args:
        *args: Positional arguments. For V1: (scope: str, target: str).
            For V2: (scope: KillSwitchScope, state: KillSwitchState).
        **kwargs: Keyword arguments mirroring the positional forms above.

    Returns:
        bool | KillSwitchAssessment: For V1, True if blocked. For V2, the
            canonical assessment.
    """
    logger.info("check_risk_kill_switch entry.")
    second = args[1] if len(args) > 1 else kwargs.get("state", kwargs.get("target"))
    if isinstance(second, KillSwitchState):
        scope: Any = kwargs.get("scope", args[0] if args else None)
        return _check_risk_kill_switch_v2(scope, second)

    scope = kwargs.get("scope", args[0] if args else None)
    target: Any = kwargs.get("target", args[1] if len(args) > 1 else None)
    return _check_risk_kill_switch_v1(scope, target)


def request_kill_switch_trigger(
    request: KillSwitchTriggerRequest, store: RiskStateStore
) -> KillSwitchState:
    """Record a governed risk kill-switch transition through a storage port.

    Args:
        request: The canonical trigger request.
        store: Injected risk state storage port.

    Returns:
        KillSwitchState: The persisted, now-active kill-switch state.
    """
    logger.warning(
        f"Requesting kill switch trigger: scope={request.scope}, "
        f"target={request.target}, reason={request.reason}."
    )
    triggered_at = datetime.now(UTC)
    store.save_kill_switch_state(
        scope=str(request.scope),
        target=request.target,
        state=KillSwitchStateEnum.ACTIVE,
        reason=None,
        triggered_at=triggered_at,
        triggered_by=request.triggered_by,
    )
    return KillSwitchState(
        state=KillSwitchStateEnum.ACTIVE,
        reason=request.reason,
        triggered_at=triggered_at,
        triggered_by=request.triggered_by,
    )


def validate_resume_request(
    request: KillSwitchResumeRequest,
    state: KillSwitchState,
    approval: ApprovalContext | None,
) -> ValidationResult:
    """Require governed approval before a kill switch may be resumed.

    Args:
        request: The canonical resume request.
        state: The current kill-switch state being resumed.
        approval: Optional operator/approval context.

    Returns:
        ValidationResult: Validation outcome with message and details.
    """
    logger.info(f"Validating kill switch resume request for scope={request.scope}.")
    operator_role = (
        approval.operator_role if approval else None
    ) or request.operator_role
    approval_token = (
        approval.approval_token if approval else None
    ) or request.approval_token

    if state.state == KillSwitchStateEnum.LOCKED:
        if operator_role not in {"admin", "compliance"}:
            msg = "Cannot resume locked kill switch without compliance or admin role."
            logger.info(msg)
            return {
                "valid": False,
                "message": msg,
                "code": "PERMISSION_DENIED",
                "details": {"scope": str(request.scope), "target": request.target},
            }
        return {
            "valid": True,
            "message": "Locked resume approved.",
            "code": "OK",
            "details": {},
        }

    has_privilege = operator_role in {"admin", "compliance"}
    has_token = bool(approval_token and approval_token.strip())
    if not has_privilege and not has_token:
        msg = (
            "Governed resume requires a valid approval token or "
            "compliance/admin operator role."
        )
        logger.info(msg)
        return {
            "valid": False,
            "message": msg,
            "code": "APPROVAL_REQUIRED",
            "details": {"scope": str(request.scope), "target": request.target},
        }

    logger.debug("Kill switch resume request approved.")
    return {"valid": True, "message": "Resume approved.", "code": "OK", "details": {}}


def clear_kill_switch_after_approval(
    request: KillSwitchResumeRequest, store: RiskStateStore
) -> KillSwitchState:
    """Persist an approved kill-switch resume state through a storage port.

    Args:
        request: The canonical resume request (already validated).
        store: Injected risk state storage port.

    Returns:
        KillSwitchState: The persisted, now-inactive kill-switch state.
    """
    logger.info(
        f"Clearing kill switch after approval: scope={request.scope}, "
        f"target={request.target}."
    )
    store.save_kill_switch_state(
        scope=str(request.scope),
        target=request.target,
        state=KillSwitchStateEnum.INACTIVE,
        reason=None,
        triggered_at=None,
        triggered_by=None,
    )
    return KillSwitchState(state=KillSwitchStateEnum.INACTIVE)


class KillSwitchService:
    """Kill-switch state and scoped evaluation façade (V2).

    State-mutating only through an injected `RiskStateStore`; never mutates
    broker state and never places, closes, or modifies orders.
    """

    def __init__(self, store: RiskStateStore) -> None:
        """Initialize the service with an injected risk state store.

        Args:
            store: Risk state storage port used for persistence.
        """
        self.store = store
        logger.debug("KillSwitchService initialized.")

    def check(self, scope: KillSwitchScope, target: str) -> KillSwitchAssessment:
        """Check the current kill-switch assessment for a scope/target.

        Args:
            scope: The kill-switch scope to check.
            target: The target identifier within that scope.

        Returns:
            KillSwitchAssessment: The canonical scoped assessment.
        """
        logger.info(f"KillSwitchService checking scope={scope}, target={target}.")
        state_enum, reason, triggered_at, triggered_by = (
            self.store.get_kill_switch_state(str(scope), target)
        )
        state = KillSwitchState(
            state=state_enum,
            reason=str(reason) if reason else None,
            triggered_at=triggered_at,
            triggered_by=triggered_by,
        )
        assessment = _check_risk_kill_switch_v2(scope, state)
        return assessment.model_copy(update={"target": target})

    def trigger(self, request: KillSwitchTriggerRequest) -> KillSwitchState:
        """Trigger a governed kill-switch transition.

        Args:
            request: The canonical trigger request.

        Returns:
            KillSwitchState: The persisted, now-active kill-switch state.
        """
        return request_kill_switch_trigger(request, self.store)

    def resume(
        self,
        request: KillSwitchResumeRequest,
        approval: ApprovalContext | None = None,
    ) -> KillSwitchState:
        """Resume a kill switch after validating governed approval.

        Args:
            request: The canonical resume request.
            approval: Optional operator/approval context.

        Returns:
            KillSwitchState: The persisted, now-inactive kill-switch state.

        Raises:
            ValidationError: If approval requirements are not satisfied.
        """
        state_enum, reason, triggered_at, triggered_by = (
            self.store.get_kill_switch_state(str(request.scope), request.target)
        )
        current_state = KillSwitchState(
            state=state_enum,
            reason=str(reason) if reason else None,
            triggered_at=triggered_at,
            triggered_by=triggered_by,
        )
        validation = validate_resume_request(request, current_state, approval)
        if not validation["valid"]:
            logger.error(f"Kill switch resume denied: {validation['message']}")
            raise ValidationError(validation["message"], code=validation["code"])
        return clear_kill_switch_after_approval(request, self.store)
