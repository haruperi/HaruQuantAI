"""Risk persistence protocols over Data-owned durable runtime records."""

from __future__ import annotations

from decimal import Decimal
from typing import Literal, cast

from pydantic import BaseModel

from app.services.data import (
    build_risk_runtime_store,
    execute_runtime_store_operation,
    execute_runtime_store_transition,
)
from app.services.risk.contracts import (
    AllocationRiskDecision,
    KillSwitchState,
    RiskAuditRecord,
    StrategyOperationalEligibilityDecision,
)
from app.utils import canonical_digest, get_logger

logger = get_logger(__name__)


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
        self._store = build_risk_runtime_store(
            {
                "allocation": (_encode, AllocationRiskDecision.model_validate_json),
                "audit": (_encode, RiskAuditRecord.model_validate_json),
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
        existing = execute_runtime_store_operation(
            self._store, "get", collection="audit", key=record.record_id
        )
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
            execute_runtime_store_operation(
                self._store,
                "append",
                collection="audit",
                key=record.record_id,
                partition="chain",
                sequence=expected_sequence + 1,
                kind="audit",
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
        return cast(
            "tuple[RiskAuditRecord, ...]",
            execute_runtime_store_operation(
                self._store,
                "list",
                collection="audit",
                partition="chain",
                limit=1_000,
            ),
        )

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
        return self._put_once(
            "eligibility", decision.decision_id, "eligibility", decision
        )

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
        return self._put_once(
            "allocation-reviews", decision.decision_id, "allocation", decision
        )

    def _put_once(self, collection: str, key: str, kind: str, value: object) -> bool:
        """Persist one exact immutable Risk value.

        Returns:
            Whether the write was first or idempotent.
        """
        try:
            execute_runtime_store_operation(
                self._store,
                "put_once",
                collection=collection,
                key=key,
                kind=kind,
                value=value,
            )
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
            execute_runtime_store_operation(
                self._store,
                "get",
                collection="allocation-active",
                key=portfolio_id,
            ),
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
            "tuple[AllocationRiskDecision, int] | None",
            execute_runtime_store_operation(
                self._store,
                "get_with_revision",
                collection="allocation-active",
                key=decision.portfolio_id,
            ),
        )
        if stored is None:
            if expected_predecessor_version is not None:
                return False
            operation: Literal["compare_and_swap", "put_once"] = "put_once"
            revision = 0
        else:
            current, revision = stored
            if current.reviewed_version != expected_predecessor_version:
                return False
            operation = "compare_and_swap"
        try:
            execute_runtime_store_operation(
                self._store,
                operation,
                collection="allocation-active",
                key=decision.portfolio_id,
                kind="allocation",
                value=decision,
                expected_revision=revision or None,
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
        existing = execute_runtime_store_operation(
            self._store, "get", collection="audit", key=record.record_id
        )
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
        committed = execute_runtime_store_transition(
            self._store,
            state_collection="kill-switch",
            state_key=_kill_switch_key(state.scope_level, state.scope),
            state_kind="kill-switch",
            state_value=state,
            expected_revision=expected_version,
            event_collection="audit",
            event_key=record.record_id,
            event_partition="chain",
            event_sequence=expected_sequence + 1,
            event_kind="audit",
            event_value=record,
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
            execute_runtime_store_operation(
                self._store,
                "get",
                collection="kill-switch",
                key=_kill_switch_key(scope_level, scope),
            ),
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
        "read_all",
        "read_head",
        "save_if_absent",
        "save_review_if_absent",
    }
    if not isinstance(store, _DurableRiskStore):
        raise TypeError("invalid Risk state-store handle")
    if operation not in allowed:
        raise ValueError("unsupported Risk state-store operation")
    return getattr(store, operation)(*args, **kwargs)


__all__ = ("build_risk_state_store", "execute_risk_state_store_operation")
