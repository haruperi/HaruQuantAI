"""Risk persistence protocols over Risk-owned relational records."""

from __future__ import annotations

from decimal import Decimal
from typing import Literal, cast

from pydantic import BaseModel

from app.composition.logging import get_logger
from app.kernel.serialization import canonical_digest
from app.services.risk.contracts import (
    AllocationRiskDecision,
    KillSwitchState,
    RiskAuditRecord,
    RiskDecisionPackage,
    StrategyOperationalEligibilityDecision,
)
from app.services.risk.persistence import (
    create_active_allocation_record,
    create_allocation_review_record,
    create_audit_record,
    create_decision_record,
    create_eligibility_record,
    create_risk_runtime_store,
    read_active_allocation_record,
    read_active_allocation_record_with_revision,
    read_audit_record,
    read_audit_records,
    read_decision_record,
    read_decision_records,
    read_kill_switch_record,
    update_active_allocation_record,
    update_kill_switch_with_audit,
)

logger = get_logger(__name__)
_MAX_DECISION_PAGE = 200


def _kill_switch_key(scope_level: str, scope: object) -> str:
    """Derive one stable scope identity for versioned kill-switch state.

    Returns:
        Storage-safe stable scope key.
    """
    return f"kill-switch-{canonical_digest((scope_level, scope))}"


def _encode(value: object) -> str:
    """Encode one immutable Risk result.

    Returns:
        Validated JSON text.

    Raises:
        TypeError: If the value is not a validated model.
    """
    if not isinstance(value, BaseModel):
        raise TypeError("Risk runtime state must be a validated model")
    return value.model_dump_json()


class _DurableRiskStore:
    """Combined structural adapter for Risk's narrow state protocols."""

    def __init__(self) -> None:
        """Construct the adapter without opening a database connection."""
        self._store = create_risk_runtime_store(
            {
                "allocation": (_encode, AllocationRiskDecision.model_validate_json),
                "audit": (_encode, RiskAuditRecord.model_validate_json),
                "decision": (_encode, RiskDecisionPackage.model_validate_json),
                "eligibility": (
                    _encode,
                    StrategyOperationalEligibilityDecision.model_validate_json,
                ),
                "kill-switch": (_encode, KillSwitchState.model_validate_json),
            }
        )

    def read_head(self, *, timeout_seconds: Decimal | None) -> RiskAuditRecord | None:
        """Return the current Risk audit head.

        Returns:
            Latest audit record or ``None``.
        """
        records = self.read_all(timeout_seconds=timeout_seconds)
        return records[-1] if records else None

    def append_atomic(
        self,
        record: RiskAuditRecord,
        *,
        expected_sequence: int,
        expected_previous_hash: str,
        timeout_seconds: Decimal | None,
    ) -> Literal["appended", "already_appended", "conflict"]:
        """Append one sealed audit record under its chain-head guard.

        Returns:
            Exact append outcome.
        """
        existing = read_audit_record(self._store, record.record_id)
        if existing is not None:
            return "already_appended" if existing == record else "conflict"
        head = self.read_head(timeout_seconds=timeout_seconds)
        actual_sequence = 0 if head is None else cast("int", head.sequence) + 1
        actual_previous = "0" * 64 if head is None else cast("str", head.record_hash)
        if (
            expected_sequence != actual_sequence
            or expected_previous_hash != actual_previous
        ):
            return "conflict"
        try:
            create_audit_record(
                self._store,
                record_id=record.record_id,
                sequence=expected_sequence + 1,
                value=record,
            )
        except ValueError:
            return "conflict"
        return "appended"

    def read_all(
        self, *, timeout_seconds: Decimal | None
    ) -> tuple[RiskAuditRecord, ...]:
        """Return the complete ordered Risk audit chain.

        Returns:
            Ordered sealed audit records.
        """
        del timeout_seconds
        return cast("tuple[RiskAuditRecord, ...]", read_audit_records(self._store))

    def save_decision(self, decision: RiskDecisionPackage) -> None:
        """Persist one immutable canonical Risk decision.

        Raises:
            ValueError: If the decision identity conflicts.
        """
        existing = read_decision_record(self._store, decision.decision_id)
        if existing is not None:
            if existing == decision:
                return
            raise ValueError("Risk decision identity conflict")
        try:
            create_decision_record(
                self._store,
                decision_id=decision.decision_id,
                value=decision,
            )
        except ValueError:
            stored = read_decision_record(self._store, decision.decision_id)
            if stored is not None:
                if stored == decision:
                    return
                raise ValueError("Risk decision identity conflict") from None
            raise

    def list_decisions(self, limit: int) -> tuple[RiskDecisionPackage, ...]:
        """Return a bounded newest-first Risk decision page.

        Raises:
            ValueError: If the requested page bound is invalid.
        """
        if isinstance(limit, bool) or limit <= 0 or limit > _MAX_DECISION_PAGE:
            raise ValueError("Risk decision limit must be between 1 and 200")
        records = cast(
            "tuple[RiskDecisionPackage, ...]",
            read_decision_records(self._store, limit),
        )
        return records

    def save_if_absent(
        self,
        decision: StrategyOperationalEligibilityDecision,
        *,
        timeout_seconds: Decimal | None,
    ) -> bool:
        """Persist an exact eligibility decision once.

        Returns:
            True for an exact first or idempotent write.
        """
        del timeout_seconds
        try:
            create_eligibility_record(self._store, decision.decision_id, decision)
        except ValueError:
            return False
        return True

    def save_review_if_absent(
        self,
        decision: AllocationRiskDecision,
        *,
        timeout_seconds: Decimal | None,
    ) -> bool:
        """Persist an exact allocation review once.

        Returns:
            True for an exact first or idempotent write.
        """
        del timeout_seconds
        try:
            create_allocation_review_record(self._store, decision.decision_id, decision)
        except ValueError:
            return False
        return True

    def get_active(
        self,
        portfolio_id: str,
        *,
        timeout_seconds: Decimal | None,
    ) -> AllocationRiskDecision | None:
        """Return one portfolio's active allocation decision.

        Returns:
            Active decision or ``None``.
        """
        del timeout_seconds
        return cast(
            "AllocationRiskDecision | None",
            read_active_allocation_record(self._store, portfolio_id),
        )

    def activate_compare_and_swap(
        self,
        decision: AllocationRiskDecision,
        *,
        expected_predecessor_version: str | None,
        timeout_seconds: Decimal | None,
    ) -> bool:
        """Activate one allocation decision under predecessor and revision guards.

        Returns:
            Whether the activation committed.
        """
        del timeout_seconds
        stored = cast(
            "tuple[AllocationRiskDecision, str] | None",
            read_active_allocation_record_with_revision(
                self._store, decision.portfolio_id
            ),
        )
        if stored is None:
            if expected_predecessor_version is not None:
                return False
            try:
                create_active_allocation_record(
                    self._store, decision.portfolio_id, decision
                )
            except ValueError:
                return False
            return True
        current, revision = stored
        if current.reviewed_version != expected_predecessor_version:
            return False
        try:
            update_active_allocation_record(
                self._store,
                key=decision.portfolio_id,
                value=decision,
                expected_revision=revision,
            )
        except ValueError:
            return False
        return True

    def compare_and_swap_with_audit(
        self,
        state: KillSwitchState,
        record: RiskAuditRecord,
        *,
        expected_version: int,
        expected_sequence: int,
        expected_previous_hash: str,
        timeout_seconds: Decimal | None,
    ) -> Literal["committed", "already_committed", "conflict"]:
        """Atomically commit kill-switch state and sealed audit evidence.

        Returns:
            Exact atomic transition outcome.
        """
        existing = read_audit_record(self._store, record.record_id)
        if existing is not None:
            return "already_committed" if existing == record else "conflict"
        head = self.read_head(timeout_seconds=timeout_seconds)
        actual_sequence = 0 if head is None else cast("int", head.sequence) + 1
        actual_previous = "0" * 64 if head is None else cast("str", head.record_hash)
        if (
            actual_sequence != expected_sequence
            or actual_previous != expected_previous_hash
        ):
            return "conflict"
        committed = update_kill_switch_with_audit(
            self._store,
            state_key=_kill_switch_key(state.scope_level, state.scope),
            state_value=state,
            expected_revision=expected_version,
            audit_key=record.record_id,
            audit_sequence=expected_sequence + 1,
            audit_value=record,
        )
        return "committed" if committed else "conflict"

    def load_kill_switch(
        self, scope_level: str, scope: object
    ) -> KillSwitchState | None:
        """Load current canonical kill-switch state for one exact scope.

        Returns:
            Current state or ``None`` before the first transition.
        """
        return cast(
            "KillSwitchState | None",
            read_kill_switch_record(self._store, _kill_switch_key(scope_level, scope)),
        )


def build_risk_state_store() -> object:
    """Build one durable adapter satisfying Risk state protocols.

    Returns:
        Opaque Risk-owned protocol adapter.
    """
    logger.info("Building durable Risk state adapter")
    return _DurableRiskStore()


def execute_risk_state_store_operation(
    store: object,
    operation: str,
    /,
    *args: object,
    **kwargs: object,
) -> object:
    """Execute one allowlisted Risk state operation.

    Returns:
        Exact Risk state operation result.

    Raises:
        TypeError: If the handle was not built by this adapter.
        ValueError: If the operation is not part of the state boundary.
    """
    allowed = {
        "activate_compare_and_swap",
        "append_atomic",
        "compare_and_swap_with_audit",
        "get_active",
        "load_kill_switch",
        "list_decisions",
        "read_all",
        "read_head",
        "save_if_absent",
        "save_decision",
        "save_review_if_absent",
    }
    if not isinstance(store, _DurableRiskStore):
        raise TypeError("invalid Risk state-store handle")
    if operation not in allowed:
        raise ValueError("unsupported Risk state-store operation")
    logger.info("Executing Risk state store operation: %s", operation)
    try:
        result = getattr(store, operation)(*args, **kwargs)
        logger.info("Risk state store operation %s completed successfully", operation)
        return result
    except Exception:
        logger.exception("Risk state store operation %s failed", operation)
        raise


def get_kill_switch_state(scope_level: str, scope: object) -> object | None:
    """Return current canonical kill-switch state for one exact scope."""
    logger.info("Getting kill switch state for scope_level=%s", scope_level)
    store = build_risk_state_store()
    result = execute_risk_state_store_operation(
        store,
        "load_kill_switch",
        scope_level,
        scope,
    )
    logger.info(
        "Kill switch state for scope_level=%s found=%s",
        scope_level,
        result is not None,
    )
    return result


def persist_risk_decision(decision: object) -> None:
    """Persist one immutable ``RiskDecisionPackage v1``.

    Raises:
        TypeError: If the value is not a canonical Risk decision.
    """
    if not isinstance(decision, RiskDecisionPackage):
        raise TypeError("decision must be RiskDecisionPackage v1")
    logger.info(
        "Persisting risk decision decision_id=%s state=%s "
        "request_id=%s correlation_id=%s",
        getattr(decision, "decision_id", None),
        getattr(decision, "state", None),
        getattr(decision, "request_id", None),
        getattr(decision, "correlation_id", None),
    )
    store = build_risk_state_store()
    execute_risk_state_store_operation(store, "save_decision", decision)


def list_risk_decisions(limit: int = 50) -> tuple[object, ...]:
    """Return a bounded newest-first page of canonical Risk decisions."""
    logger.info("Listing risk decisions with limit=%s", limit)
    store = build_risk_state_store()
    records = cast(
        "tuple[object, ...]",
        execute_risk_state_store_operation(store, "list_decisions", limit),
    )
    logger.info("Listed %s risk decisions", len(records))
    return records


__all__ = (
    "build_risk_state_store",
    "execute_risk_state_store_operation",
    "get_kill_switch_state",
    "list_risk_decisions",
    "persist_risk_decision",
)
