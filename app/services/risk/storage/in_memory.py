"""Thread-safe in-memory risk governance store.

Provides isolated test, offline, and simulation persistence capabilities for
drawdown state, kill switches, audit logs, policies, and decisions.
"""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from threading import RLock
from typing import Protocol

from app.services.risk.models import (
    DrawdownState,
    KillSwitchReason,
    KillSwitchStateEnum,
    PolicyRule,
    RiskAuditEvent,
    RiskDecisionPackage,
)
from app.services.risk.storage.ports import (
    PersistenceResult,
    RiskAuditSink,
    RiskDecisionStore,
    RiskPolicyStore,
    RiskStateStore,
    _check_schema_version,
    compute_decision_material_hash,
)
from app.utils.errors import DataError, ValidationError
from app.utils.logger import logger


class StorageOperation(StrEnum):
    """Types of storage operations that can be performed."""

    READ = "read"
    WRITE = "write"
    DELETE = "delete"
    REVOKE = "revoke"


class FailingStore(Protocol):
    """Protocol for a storage provider that can simulate storage failures."""

    def set_simulate_failure(self, enabled: bool) -> None:
        """Enable or disable simulated storage failures.

        Args:
            enabled: True to enable failure simulation, False to disable.
        """
        ...


class InMemoryRiskStateStore(
    RiskStateStore, RiskAuditSink, RiskPolicyStore, RiskDecisionStore
):
    """Thread-safe all-in-one in-memory implementation of risk storage ports."""

    def __init__(self) -> None:
        """Initialize the store maps and lock."""
        logger.info("Initializing InMemoryRiskStateStore")
        self._lock = RLock()
        self._simulate_failure: bool = False
        self._drawdown_states: dict[str, DrawdownState] = {}
        self._kill_switches: dict[
            str,
            dict[
                str,
                tuple[
                    KillSwitchStateEnum,
                    KillSwitchReason | None,
                    datetime | None,
                    str | None,
                ],
            ],
        ] = {
            "global": {"*": (KillSwitchStateEnum.INACTIVE, None, None, None)},
            "portfolio": {"*": (KillSwitchStateEnum.INACTIVE, None, None, None)},
            "strategy": {},
            "symbol": {},
            "currency": {},
        }
        self._revoked_tokens: set[str] = set()
        self._audit_events: list[RiskAuditEvent] = []
        self._policy_rules: dict[str, PolicyRule] = {}
        self._decisions: dict[str, RiskDecisionPackage] = {}
        self._decisions_by_request: dict[str, RiskDecisionPackage] = {}
        self._decisions_by_idempotency_key: dict[
            tuple[str, str, str, str], RiskDecisionPackage
        ] = {}

    def set_simulate_failure(self, enabled: bool) -> None:
        """Enable or disable simulated persistence failures for testing.

        Args:
            enabled: True to simulate failure on operations, False to work normally.
        """
        logger.info(f"Setting simulated persistence failure: enabled={enabled}")
        with self._lock:
            self._simulate_failure = enabled

    def _check_failure(self) -> None:
        """Raise DataError if simulated failure is enabled.

        Raises:
            DataError: When simulated failure is enabled.
        """
        if self._simulate_failure:
            logger.warning("Simulated persistence failure triggered.")
            raise DataError("Simulated persistence failure.")

    def get_drawdown_state(
        self, strategy_id: str | None = None
    ) -> DrawdownState | None:
        """Retrieve drawdown state from memory.

        Args:
            strategy_id: Optional strategy identifier.

        Returns:
            DrawdownState | None: Stored drawdown state, or None.

        Raises:
            DataError: When simulated failure is enabled.
        """
        logger.debug(f"Retrieving drawdown state for strategy_id={strategy_id}")
        self._check_failure()
        key = strategy_id or "portfolio"
        with self._lock:
            result = self._drawdown_states.get(key)
            logger.debug(f"Drawdown state retrieved: {result is not None}")
            return result

    def save_drawdown_state(
        self, state: DrawdownState, strategy_id: str | None = None
    ) -> None:
        """Save drawdown state to memory.

        Args:
            state: The drawdown state object.
            strategy_id: Optional strategy identifier.

        Raises:
            DataError: When simulated failure is enabled.
            ValidationError: For invalid state parameters.
        """
        if not isinstance(state, DrawdownState):
            logger.error("Attempted to save invalid DrawdownState object.")
            raise ValidationError("Invalid DrawdownState object.")
        _check_schema_version(state)
        logger.info(f"Saving drawdown state for strategy_id={strategy_id}")
        self._check_failure()
        key = strategy_id or "portfolio"
        with self._lock:
            self._drawdown_states[key] = state
            logger.info("Saved drawdown state successfully.")

    def get_kill_switch_state(
        self, scope: str, target: str
    ) -> tuple[
        KillSwitchStateEnum, KillSwitchReason | None, datetime | None, str | None
    ]:
        """Retrieve kill switch state from memory.

        Args:
            scope: Scope of the switch.
            target: Scope identifier target.

        Returns:
            tuple: (state, reason, triggered_at, triggered_by)

        Raises:
            DataError: When simulated failure is enabled.
        """
        logger.debug(f"Retrieving kill switch state for scope={scope}, target={target}")
        self._check_failure()
        with self._lock:
            scope_map = self._kill_switches.get(scope)
            if scope_map is None:
                logger.debug(
                    f"No scope map found for scope={scope}, returning defaults"
                )
                return KillSwitchStateEnum.INACTIVE, None, None, None
            result = scope_map.get(
                target, (KillSwitchStateEnum.INACTIVE, None, None, None)
            )
            logger.debug(f"Kill switch state resolved: state={result[0]}")
            return result

    def save_kill_switch_state(
        self,
        scope: str,
        target: str,
        state: KillSwitchStateEnum,
        reason: KillSwitchReason | None = None,
        triggered_at: datetime | None = None,
        triggered_by: str | None = None,
    ) -> None:
        """Save kill switch state updates to memory.

        Args:
            scope: Target scope.
            target: Scope identifier.
            state: Target switch status.
            reason: Optional trigger reason.
            triggered_at: Optional timestamp.
            triggered_by: Optional operator name.

        Raises:
            DataError: When simulated failure is enabled.
            ValidationError: For invalid parameters.
        """
        logger.info(
            f"Saving kill switch state scope={scope}, target={target}, state={state}"
        )
        self._check_failure()
        if scope not in self._kill_switches:
            msg = f"Invalid kill switch scope: {scope}"
            logger.error(msg)
            raise ValidationError(msg)
        with self._lock:
            t = triggered_at or datetime.now(UTC)
            by = triggered_by or "system"
            self._kill_switches[scope][target] = (state, reason, t, by)
            logger.info("Saved kill switch state successfully.")

    def is_token_revoked(self, token_id: str) -> bool:
        """Check token revocation in memory.

        Args:
            token_id: The token identifier.

        Returns:
            bool: True if revoked, False otherwise.

        Raises:
            DataError: When simulated failure is enabled.
        """
        logger.debug(f"Checking token revocation for token_id={token_id}")
        self._check_failure()
        with self._lock:
            result = token_id in self._revoked_tokens
            logger.debug(f"Token revocation check: revoked={result}")
            return result

    def revoke_token(self, token_id: str) -> None:
        """Revoke a token in memory.

        Args:
            token_id: The token identifier.

        Raises:
            DataError: When simulated failure is enabled.
            ValidationError: If token ID is empty.
        """
        logger.info(f"Revoking token_id={token_id}")
        self._check_failure()
        if not token_id:
            logger.error("Token revocation failed: empty token_id.")
            raise ValidationError("token_id is required.")
        with self._lock:
            self._revoked_tokens.add(token_id)
            logger.info("Token revoked successfully.")

    def write_event(self, event: RiskAuditEvent) -> None:
        """Write audit event block to memory.

        Args:
            event: The audit event object.

        Raises:
            DataError: When simulated failure is enabled.
            ValidationError: For invalid event objects.
        """
        if not isinstance(event, RiskAuditEvent):
            logger.error("Attempted to write invalid RiskAuditEvent object.")
            raise ValidationError("Invalid RiskAuditEvent object.")
        _check_schema_version(event)
        logger.info(f"Appending risk audit event: event_id={event.event_id}")
        self._check_failure()
        with self._lock:
            self._audit_events.append(event)
            logger.info("Audit event appended successfully.")

    def get_last_event(self) -> RiskAuditEvent | None:
        """Retrieve the latest block in memory.

        Returns:
            RiskAuditEvent | None: Latest block or None.

        Raises:
            DataError: When simulated failure is enabled.
        """
        logger.debug("Retrieving last audit event from memory")
        self._check_failure()
        with self._lock:
            if not self._audit_events:
                logger.debug("No audit events recorded.")
                return None
            result = self._audit_events[-1]
            logger.debug(f"Last audit event resolved: event_id={result.event_id}")
            return result

    def get_all_events(self) -> list[RiskAuditEvent]:
        """Retrieve all events.

        Returns:
            list[RiskAuditEvent]: Sorted audit event logs.

        Raises:
            DataError: When simulated failure is enabled.
        """
        logger.debug("Retrieving all audit events from memory")
        self._check_failure()
        with self._lock:
            logger.debug(f"Retrieved {len(self._audit_events)} audit events.")
            return list(self._audit_events)

    def get_rules(self) -> list[PolicyRule]:
        """Retrieve active policy rules.

        Returns:
            list[PolicyRule]: Active policy rules.

        Raises:
            DataError: When simulated failure is enabled.
        """
        logger.debug("Retrieving all policy rules from memory")
        self._check_failure()
        with self._lock:
            logger.debug(f"Retrieved {len(self._policy_rules)} policy rules.")
            return list(self._policy_rules.values())

    def save_rule(self, rule: PolicyRule) -> None:
        """Store policy rule in memory.

        Args:
            rule: PolicyRule object.

        Raises:
            DataError: When simulated failure is enabled.
            ValidationError: For invalid rule objects.
        """
        if not isinstance(rule, PolicyRule):
            logger.error("Attempted to save invalid PolicyRule object.")
            raise ValidationError("Invalid PolicyRule object.")
        _check_schema_version(rule)
        logger.info(f"Saving policy rule: rule_id={rule.rule_id}")
        self._check_failure()
        with self._lock:
            self._policy_rules[rule.rule_id] = rule
            logger.info("Saved policy rule successfully.")

    def get_decision(self, decision_id: str) -> RiskDecisionPackage | None:
        """Retrieve decision by ID.

        Args:
            decision_id: Decision identifier.

        Returns:
            RiskDecisionPackage | None: The matched package or None.

        Raises:
            DataError: When simulated failure is enabled.
        """
        logger.debug(f"Retrieving decision_id={decision_id}")
        self._check_failure()
        with self._lock:
            result = self._decisions.get(decision_id)
            logger.debug(f"Decision resolved: {result is not None}")
            return result

    def save_decision(self, decision: RiskDecisionPackage) -> None:
        """Persist decision in memory with idempotency handling.

        Args:
            decision: RiskDecisionPackage object.

        Raises:
            DataError: On idempotency conflict or simulated failure.
            ValidationError: For invalid decision packages.
        """
        if not isinstance(decision, RiskDecisionPackage):
            logger.error("Attempted to save invalid RiskDecisionPackage object.")
            raise ValidationError("Invalid RiskDecisionPackage object.")
        _check_schema_version(decision)
        logger.info(f"Saving decision package: decision_id={decision.decision_id}")
        self._check_failure()

        # Compound key construction
        req_id = decision.request_id
        wf_id = decision.workflow_id
        details = decision.details or {}
        proposed = details.get("proposed_action") or {}
        sig_id = proposed.get("signal_id") or details.get("signal_id") or ""
        mat_hash = details.get(
            "decision_material_hash"
        ) or compute_decision_material_hash(decision)

        key = (req_id, wf_id, str(sig_id), str(mat_hash))

        with self._lock:
            # Check duplicate request same material idempotency
            existing = self._decisions_by_request.get(decision.request_id)
            if existing is not None and existing.decision_id != decision.decision_id:
                msg = (
                    f"Idempotency conflict: request_id '{decision.request_id}' "
                    f"already processed with decision '{existing.decision_id}'."
                )
                logger.error(msg)
                raise DataError(msg)

            # Check compound key idempotency
            existing_by_key = self._decisions_by_idempotency_key.get(key)
            if (
                existing_by_key is not None
                and existing_by_key.decision_id != decision.decision_id
            ):
                msg = (
                    f"Idempotency conflict: decision for key {key} "
                    f"already processed with decision '{existing_by_key.decision_id}'."
                )
                logger.error(msg)
                raise DataError(msg)

            self._decisions[decision.decision_id] = decision
            self._decisions_by_request[decision.request_id] = decision
            self._decisions_by_idempotency_key[key] = decision
            logger.info("Saved decision package successfully.")

    def get_decision_by_request_id(self, request_id: str) -> RiskDecisionPackage | None:
        """Retrieve decision by request ID.

        Args:
            request_id: Request identifier.

        Returns:
            RiskDecisionPackage | None: Stored package or None.

        Raises:
            DataError: When simulated failure is enabled.
        """
        logger.debug(f"Retrieving decision by request_id={request_id}")
        self._check_failure()
        with self._lock:
            result = self._decisions_by_request.get(request_id)
            logger.debug(f"Decision resolved by request_id: {result is not None}")
            return result

    def get_decision_by_key(
        self,
        request_id: str,
        workflow_id: str,
        signal_id: str,
        decision_material_hash: str,
    ) -> RiskDecisionPackage | None:
        """Retrieve decision by idempotency keys.

        Args:
            request_id: Request identifier.
            workflow_id: Workflow execution identifier.
            signal_id: Signal correlation identifier.
            decision_material_hash: Hash of decision inputs.

        Returns:
            RiskDecisionPackage | None: Matched package or None.

        Raises:
            DataError: When simulated failure is enabled.
            ValidationError: If required keys are empty.
        """
        logger.debug(
            f"Retrieving decision by compound key: "
            f"request={request_id}, workflow={workflow_id}, "
            f"signal={signal_id}, material={decision_material_hash}"
        )
        self._check_failure()
        if not request_id or not workflow_id:
            logger.error("Query failed: missing request_id or workflow_id.")
            raise ValidationError("request_id and workflow_id are required.")
        key = (request_id, workflow_id, signal_id or "", decision_material_hash or "")
        with self._lock:
            result = self._decisions_by_idempotency_key.get(key)
            logger.debug(f"Decision resolved by compound key: {result is not None}")
            return result


def create_in_memory_risk_store() -> InMemoryRiskStateStore:
    """Create an isolated InMemoryRiskStateStore instance.

    Returns:
        InMemoryRiskStateStore: A fresh state store instance.
    """
    logger.info("Creating fresh in-memory risk store instance.")
    return InMemoryRiskStateStore()


def simulate_storage_failure(
    store: FailingStore, operation: StorageOperation
) -> PersistenceResult:
    """Inject a failure state into the failing storage provider.

    Args:
        store: Target storage store client.
        operation: Target storage operation.

    Returns:
        PersistenceResult: Success state status.
    """
    logger.info(f"Simulating storage failure on operations: operation={operation}")
    store.set_simulate_failure(True)
    return {
        "success": False,
        "message": f"Simulated failure injected for operation: {operation.value}",
        "code": "SIMULATED_FAILURE",
        "details": {"operation": operation},
    }
