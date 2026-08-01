"""Durable Risk approval-token state over Data-owned runtime records."""

from __future__ import annotations

import json
from collections.abc import Mapping
from datetime import datetime
from decimal import Decimal
from typing import Literal, cast

from app.services.data import (
    build_risk_runtime_store,
    execute_runtime_store_operation,
    execute_runtime_store_transition,
)
from app.services.risk.contracts import RiskApprovalToken
from app.utils import canonical_digest, canonical_json, get_logger

logger = get_logger(__name__)
type _State = dict[str, object]


def _encode(value: object) -> str:
    """Encode one bounded token-state mapping.

    Returns:
        Canonical JSON text.

    Raises:
        TypeError: If the value is not a mapping.
    """
    if not isinstance(value, Mapping):
        raise TypeError("Risk approval state must be a mapping")
    return canonical_json(dict(value), max_items=None)


def _key(*values: str) -> str:
    """Derive a storage-safe state key.

    Returns:
        Bounded key.
    """
    return f"record-{canonical_digest(values)}"


def _state(token: RiskApprovalToken) -> _State:
    """Create the durable issued state without storing signing secrets.

    Returns:
        JSON-safe token state.
    """
    return {
        "approval_json": token.model_dump_json(),
        "consumed": False,
        "reservation_id": None,
        "revocation_reason": None,
        "revoked_at": None,
    }


def _approval(state: Mapping[str, object]) -> RiskApprovalToken:
    """Restore the validated signed approval contract.

    Returns:
        Validated approval token.

    Raises:
        TypeError: If stored state is malformed.
    """
    payload = state.get("approval_json")
    if not isinstance(payload, str):
        raise TypeError("stored Risk approval payload is malformed")
    return RiskApprovalToken.model_validate_json(payload)


def _scope_intersects(
    candidate: Mapping[str, str], selector: Mapping[str, str]
) -> bool:
    """Return whether every revocation selector field matches a token scope.

    Returns:
        True when the scopes intersect under Risk's exact selector rule.
    """
    return all(candidate.get(key) == value for key, value in selector.items())


class _DurableTokenStateStore:
    """Data-backed implementation of Risk's atomic token-state port."""

    def __init__(self) -> None:
        """Build the lazy Data runtime handle."""
        self._store = build_risk_runtime_store(
            {"approval-state": (_encode, json.loads)}
        )

    def save_issued(
        self,
        token: RiskApprovalToken,
        *,
        timeout_seconds: Decimal | None,
    ) -> Literal["saved", "already_saved", "conflict"]:
        """Atomically persist issuance and its enumerable index.

        Returns:
            Atomic persistence outcome.
        """
        del timeout_seconds
        value = _state(token)
        existing = execute_runtime_store_operation(
            self._store,
            "get",
            collection="approval-states",
            key=_key(token.token_id),
        )
        if existing is not None:
            return "already_saved" if existing == value else "conflict"
        index = cast(
            "tuple[object, ...]",
            execute_runtime_store_operation(
                self._store,
                "list",
                collection="approval-index",
                partition="approvals",
                limit=1_000,
            ),
        )
        committed = execute_runtime_store_transition(
            self._store,
            state_collection="approval-states",
            state_key=_key(token.token_id),
            state_kind="approval-state",
            state_value=value,
            expected_revision=0,
            event_collection="approval-index",
            event_key=_key("index", token.token_id),
            event_partition="approvals",
            event_sequence=len(index) + 1,
            event_kind="approval-state",
            event_value={"approval_id": token.token_id},
        )
        return "saved" if committed else "conflict"

    def consume_if_active(  # noqa: PLR0911
        self,
        token_id: str,
        *,
        expected_signature: str,
        reservation_id: str,
        workflow_id: str,
        action: str,
        scope: Mapping[str, str],
        now: datetime,
        timeout_seconds: Decimal | None,
    ) -> Literal[
        "consumed",
        "missing",
        "expired",
        "revoked",
        "already_consumed",
        "conflict",
    ]:
        """Atomically consume one matching active approval.

        Returns:
            Classified atomic outcome.
        """
        del timeout_seconds
        stored = cast(
            "tuple[_State, int] | None",
            execute_runtime_store_operation(
                self._store,
                "get_with_revision",
                collection="approval-states",
                key=_key(token_id),
            ),
        )
        if stored is None:
            return "missing"
        value, revision = stored
        token = _approval(value)
        if value.get("revoked_at") is not None:
            return "revoked"
        if value.get("consumed") is True:
            return "already_consumed"
        if token.expires_at <= now:
            return "expired"
        if (
            token.signature != expected_signature
            or token.workflow_id != workflow_id
            or token.action != action
            or dict(token.scope) != dict(scope)
        ):
            return "conflict"
        updated = {
            **value,
            "consumed": True,
            "reservation_id": reservation_id,
        }
        try:
            execute_runtime_store_operation(
                self._store,
                "compare_and_swap",
                collection="approval-states",
                key=_key(token_id),
                kind="approval-state",
                value=updated,
                expected_revision=revision,
            )
        except ValueError:
            return "conflict"
        return "consumed"

    def revoke_intersecting(
        self,
        scope: Mapping[str, str],
        *,
        reason: str,
        revoked_at: datetime,
        timeout_seconds: Decimal | None,
    ) -> int:
        """Revoke every active approval matching the exact selector.

        Returns:
            Number of newly revoked approvals.
        """
        del timeout_seconds
        index = cast(
            "tuple[Mapping[str, object], ...]",
            execute_runtime_store_operation(
                self._store,
                "list",
                collection="approval-index",
                partition="approvals",
                limit=1_000,
            ),
        )
        revoked = 0
        for item in index:
            approval_id = item.get("approval_id")
            if isinstance(approval_id, str) and self._revoke_one(
                approval_id, scope, reason, revoked_at
            ):
                revoked += 1
        return revoked

    def _revoke_one(
        self,
        approval_id: str,
        scope: Mapping[str, str],
        reason: str,
        revoked_at: datetime,
    ) -> bool:
        """Attempt one guarded revocation.

        Returns:
            True only when this call committed a new revocation.
        """
        stored = cast(
            "tuple[_State, int] | None",
            execute_runtime_store_operation(
                self._store,
                "get_with_revision",
                collection="approval-states",
                key=_key(approval_id),
            ),
        )
        if stored is None:
            return False
        value, revision = stored
        approval = _approval(value)
        if (
            value.get("consumed") is True
            or value.get("revoked_at") is not None
            or not _scope_intersects(approval.scope, scope)
        ):
            return False
        updated = {
            **value,
            "revocation_reason": reason,
            "revoked_at": revoked_at.isoformat(),
        }
        try:
            execute_runtime_store_operation(
                self._store,
                "compare_and_swap",
                collection="approval-states",
                key=_key(approval_id),
                kind="approval-state",
                value=updated,
                expected_revision=revision,
            )
        except ValueError:
            return False
        return True


def build_risk_approval_state_store() -> object:
    """Build the durable Risk approval-token state adapter.

    Returns:
        Opaque state-store handle.
    """
    logger.info("Building durable Risk approval-token state")
    return _DurableTokenStateStore()


__all__ = ("build_risk_approval_state_store",)
