"""Trading state protocol over Data-owned durable runtime records."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime
from typing import Literal, cast

from pydantic import BaseModel

from app.services.data import (
    build_trading_runtime_store,
    execute_runtime_store_operation,
)
from app.services.trading.contracts.models import JsonValue, TradingRoute
from app.services.trading.state.events import TradingEvent
from app.services.trading.state.idempotency import IdempotencyReservation
from app.services.trading.state.projections import TradingProjection
from app.utils import canonical_digest, get_logger

logger = get_logger(__name__)
type TradingScope = tuple[TradingRoute, str, str]


def _encode(value: object) -> str:
    """Encode one validated Trading model.

    Returns:
        JSON text.

    Raises:
        TypeError: If the value is not a model.
    """
    if not isinstance(value, BaseModel):
        raise TypeError("Trading runtime state must be a validated model")
    return value.model_dump_json()


def _scope_key(scope: TradingScope) -> str:
    """Derive a storage-safe exact-scope key.

    Returns:
        Bounded key.
    """
    return f"scope-{canonical_digest(tuple(str(item) for item in scope))}"


class _DurableTradingStateStore:
    """Concrete Trading adapter over Data runtime records."""

    def __init__(self) -> None:
        """Construct the adapter without opening a connection."""
        self._store = build_trading_runtime_store(
            {
                "event": (_encode, TradingEvent.model_validate_json),
                "projection": (_encode, TradingProjection.model_validate_json),
                "reservation": (_encode, IdempotencyReservation.model_validate_json),
            }
        )

    def reserve_idempotency(
        self,
        key: str,
        material_hash: str,
        material_version: str,
        reserved_at: datetime,
        expires_at: datetime,
    ) -> IdempotencyReservation:
        """Atomically reserve or compare one caller key.

        Returns:
            Exact reservation outcome.
        """
        existing = cast(
            "IdempotencyReservation | None",
            execute_runtime_store_operation(
                self._store, "get", collection="idempotency", key=key
            ),
        )
        if existing is not None:
            matching = (
                existing.material_hash == material_hash
                and existing.material_version == material_version
            )
            return existing.model_copy(
                update={"status": "duplicate_active" if matching else "conflict"}
            )
        reservation = IdempotencyReservation(
            key=key,
            material_hash=material_hash,
            material_version=material_version,
            status="new",
            reserved_at=reserved_at,
            expires_at=expires_at,
        )
        try:
            execute_runtime_store_operation(
                self._store,
                "put_once",
                collection="idempotency",
                key=key,
                kind="reservation",
                value=reservation,
            )
        except ValueError:
            return self.reserve_idempotency(
                key, material_hash, material_version, reserved_at, expires_at
            )
        return reservation

    def complete_idempotency(
        self,
        key: str,
        material_hash: str,
        receipt_id: str,
        completed_at: datetime,
        *,
        status: Literal["completed", "reconciliation_required"],
    ) -> None:
        """Persist one terminal reservation outcome.

        Raises:
            ValueError: If the reservation is missing or mismatched.
        """
        stored = cast(
            "tuple[IdempotencyReservation, int] | None",
            execute_runtime_store_operation(
                self._store,
                "get_with_revision",
                collection="idempotency",
                key=key,
            ),
        )
        if stored is None or stored[0].material_hash != material_hash:
            raise ValueError("idempotency completion does not match a reservation")
        reservation, revision = stored
        updated = reservation.model_copy(
            update={
                "status": (
                    "duplicate_completed"
                    if status == "completed"
                    else "reconciliation_required"
                ),
                "receipt_id": receipt_id,
                "reserved_at": completed_at,
            }
        )
        execute_runtime_store_operation(
            self._store,
            "compare_and_swap",
            collection="idempotency",
            key=key,
            kind="reservation",
            value=updated,
            expected_revision=revision,
        )

    def append_event(self, event: TradingEvent) -> None:
        """Append one immutable versioned Trading event."""
        scope = (event.route, event.tenant_id, event.authority_id)
        execute_runtime_store_operation(
            self._store,
            "append",
            collection="events",
            key=event.event_id,
            partition=_scope_key(scope),
            sequence=event.aggregate_version + 1,
            kind="event",
            value=event,
        )

    def load_projection(self, scope: TradingScope) -> TradingProjection | None:
        """Load one exact-scope projection.

        Returns:
            Stored projection or ``None``.
        """
        return cast(
            "TradingProjection | None",
            execute_runtime_store_operation(
                self._store,
                "get",
                collection="projections",
                key=_scope_key(scope),
            ),
        )

    def save_projection(
        self, projection: TradingProjection, expected_version: int
    ) -> None:
        """Save a projection under optimistic owner and storage guards.

        Raises:
            ValueError: If the optimistic version is stale.
        """
        scope = (projection.route, projection.tenant_id, projection.authority_id)
        key = _scope_key(scope)
        stored = cast(
            "tuple[TradingProjection, int] | None",
            execute_runtime_store_operation(
                self._store,
                "get_with_revision",
                collection="projections",
                key=key,
            ),
        )
        current_version = 0 if stored is None else stored[0].version
        if current_version != expected_version:
            raise ValueError("Trading projection version conflict")
        execute_runtime_store_operation(
            self._store,
            "put_once" if stored is None else "compare_and_swap",
            collection="projections",
            key=key,
            kind="projection",
            value=projection,
            expected_revision=None if stored is None else stored[1],
        )

    def load_unresolved_attempts(self, scope: TradingScope) -> tuple[TradingEvent, ...]:
        """Load unresolved send attempts for one exact scope.

        Returns:
            Ordered unresolved events.
        """
        events = cast(
            "tuple[TradingEvent, ...]",
            execute_runtime_store_operation(
                self._store,
                "list",
                collection="events",
                partition=_scope_key(scope),
                limit=1_000,
            ),
        )
        projection = self.load_projection(scope)
        unresolved = (
            frozenset()
            if projection is None
            else frozenset(projection.unresolved_attempt_ids)
        )
        return tuple(
            event
            for event in events
            if event.event_type == "send_attempted"
            and (not unresolved or event.event_id in unresolved)
        )

    def load_all_unresolved_attempts(self, limit: int) -> tuple[TradingEvent, ...]:
        """Load bounded unresolved attempts across every exact scope.

        Returns:
            Deterministically ordered unresolved Trading events.
        """
        events = cast(
            "tuple[TradingEvent, ...]",
            execute_runtime_store_operation(
                self._store,
                "list_all_partitions",
                collection="events",
                limit=limit,
            ),
        )
        return tuple(event for event in events if event.event_type == "send_attempted")

    def load_report_evidence(self, scope: TradingScope) -> Mapping[str, JsonValue]:
        """Return exact stored projection evidence.

        Returns:
            JSON-safe stored evidence without enrichment.
        """
        projection = self.load_projection(scope)
        if projection is None:
            return {}
        return cast("Mapping[str, JsonValue]", projection.model_dump(mode="json"))


def build_trading_state_store() -> object:
    """Build the durable Trading state adapter.

    Returns:
        Opaque Trading state-store handle.
    """
    logger.info("Building durable Trading state adapter")
    return _DurableTradingStateStore()


def execute_trading_state_store_operation(
    store: object,
    operation: str,
    /,
    *args: object,
    **kwargs: object,
) -> object:
    """Execute one allowlisted Trading state operation.

    Returns:
        Exact state operation result.

    Raises:
        TypeError: If the handle is invalid.
        ValueError: If the operation is unsupported.
    """
    allowed = {
        "append_event",
        "complete_idempotency",
        "load_projection",
        "load_all_unresolved_attempts",
        "load_report_evidence",
        "load_unresolved_attempts",
        "reserve_idempotency",
        "save_projection",
    }
    if not isinstance(store, _DurableTradingStateStore):
        raise TypeError("invalid Trading state-store handle")
    if operation not in allowed:
        raise ValueError("unsupported Trading state-store operation")
    return getattr(store, operation)(*args, **kwargs)


__all__ = ("build_trading_state_store", "execute_trading_state_store_operation")
