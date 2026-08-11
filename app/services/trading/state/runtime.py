"""Trading state protocol over Data-owned durable runtime records."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime
from typing import Literal, cast

from pydantic import BaseModel

from app.services.trading.contracts.models import JsonValue, TradingRoute
from app.services.trading.persistence import (
    create_event_record,
    create_idempotency_record,
    create_projection_record,
    create_trading_runtime_store,
    read_all_event_records,
    read_event_records,
    read_idempotency_record,
    read_idempotency_record_with_revision,
    read_projection_record,
    read_projection_record_with_revision,
    update_event_projection_records,
    update_idempotency_record,
    update_projection_record,
)
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
        self._store = create_trading_runtime_store(
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

        Args:
            key: Idempotency key string.
            material_hash: Hash of key material.
            material_version: Version of key material.
            reserved_at: Aware UTC reservation timestamp.
            expires_at: Aware UTC expiration timestamp.

        Returns:
            Exact reservation outcome.
        """
        existing = cast(
            "IdempotencyReservation | None",
            read_idempotency_record(self._store, key),
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
            create_idempotency_record(self._store, key, reservation)
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

        Args:
            key: Idempotency key string.
            material_hash: Hash of key material.
            receipt_id: Outcome receipt identifier string.
            completed_at: Aware UTC completion timestamp.
            status: Terminal status literal.

        Raises:
            ValueError: If the reservation is missing or mismatched.
        """
        stored = cast(
            "tuple[IdempotencyReservation, str] | None",
            read_idempotency_record_with_revision(self._store, key),
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
        update_idempotency_record(
            self._store,
            key=key,
            value=updated,
            expected_revision=revision,
        )

    def append_event(self, event: TradingEvent) -> None:
        """Append one immutable versioned Trading event.

        Args:
            event: TradingEvent instance to append.
        """
        scope = (event.route, event.tenant_id, event.authority_id)
        create_event_record(
            self._store,
            key=event.event_id,
            partition=_scope_key(scope),
            sequence=event.aggregate_version + 1,
            value=event,
        )

    def apply_event(
        self,
        event: TradingEvent,
        projection: TradingProjection,
        expected_version: int,
    ) -> None:
        """Atomically persist an event and every derived projection.

        Args:
            event: Authoritative event to append.
            projection: Deterministic state after the event.
            expected_version: Optimistic version observed before projection.
        """
        scope = (event.route, event.tenant_id, event.authority_id)
        update_event_projection_records(
            self._store,
            event=event,
            projection=projection,
            scope_key=_scope_key(scope),
            expected_version=expected_version,
        )

    def load_projection(self, scope: TradingScope) -> TradingProjection | None:
        """Load one exact-scope projection.

        Args:
            scope: Target TradingScope tuple.

        Returns:
            Stored projection or ``None``.
        """
        return cast(
            "TradingProjection | None",
            read_projection_record(self._store, _scope_key(scope)),
        )

    def save_projection(
        self, projection: TradingProjection, expected_version: int
    ) -> None:
        """Save a projection under optimistic owner and storage guards.

        Args:
            projection: TradingProjection instance to save.
            expected_version: Expected optimistic projection version integer.

        Raises:
            ValueError: If the optimistic version is stale.
        """
        scope = (projection.route, projection.tenant_id, projection.authority_id)
        key = _scope_key(scope)
        stored = cast(
            "tuple[TradingProjection, int] | None",
            read_projection_record_with_revision(self._store, key),
        )
        current_version = 0 if stored is None else stored[0].version
        if current_version != expected_version:
            raise ValueError("Trading projection version conflict")
        if stored is None:
            create_projection_record(self._store, key, projection)
            return
        update_projection_record(
            self._store,
            key=key,
            value=projection,
            expected_revision=stored[1],
        )

    def load_unresolved_attempts(self, scope: TradingScope) -> tuple[TradingEvent, ...]:
        """Load unresolved send attempts for one exact scope.

        Args:
            scope: Target TradingScope tuple.

        Returns:
            Ordered unresolved events.
        """
        events = cast(
            "tuple[TradingEvent, ...]",
            read_event_records(self._store, _scope_key(scope)),
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

        Args:
            limit: Maximum number of attempts to return.

        Returns:
            Deterministically ordered unresolved Trading events.
        """
        events = cast(
            "tuple[TradingEvent, ...]",
            read_all_event_records(self._store, limit),
        )
        return tuple(event for event in events if event.event_type == "send_attempted")

    def load_report_evidence(self, scope: TradingScope) -> Mapping[str, JsonValue]:
        """Return exact stored projection evidence.

        Args:
            scope: Target TradingScope tuple.

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

    Args:
        store: Durable Trading state-store adapter handle.
        operation: Name of state operation method to invoke.
        *args: Positional arguments for state operation.
        **kwargs: Keyword arguments for state operation.

    Returns:
        Exact state operation result.

    Raises:
        TypeError: If the handle is invalid.
        ValueError: If the operation is unsupported.
    """
    allowed = {
        "apply_event",
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


def get_trading_projection(
    route: str,
    tenant_id: str,
    authority_id: str,
) -> object | None:
    """Read one exact-scope aggregate Trading projection.

    Args:
        route: Canonical ``sim``, ``paper``, or ``live`` route.
        tenant_id: Authenticated tenant or environment identifier.
        authority_id: Exact account/session authority identifier.

    Returns:
        Canonical Trading projection or ``None`` when no event exists.

    Raises:
        ValueError: If the exact scope is incomplete.
    """
    if not tenant_id or not authority_id:
        raise ValueError("Trading projection scope is incomplete")
    store = build_trading_state_store()
    scope: TradingScope = (TradingRoute(route), tenant_id, authority_id)
    return execute_trading_state_store_operation(store, "load_projection", scope)


__all__ = (
    "build_trading_state_store",
    "execute_trading_state_store_operation",
    "get_trading_projection",
)
