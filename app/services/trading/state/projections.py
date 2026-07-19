"""Deterministic optimistic projections of ordered Trading events."""

from collections.abc import Mapping
from datetime import datetime, timedelta
from types import MappingProxyType
from typing import Self

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.services.trading.contracts import TradingError, TradingRoute
from app.services.trading.contracts.models import JsonValue
from app.services.trading.state.events import TradingEvent
from app.services.trading.state.stores import TradingStateStore
from app.utils import logger, to_json_safe


def _freeze_mapping(value: Mapping[str, object]) -> Mapping[str, JsonValue]:
    """Validate and freeze a projection mapping.

    Args:
        value: Candidate projection mapping.

    Returns:
        Immutable JSON-safe mapping.

    Raises:
        TypeError: If the value is not a serializable mapping.
    """
    logger.debug("Freezing TradingProjection mapping")
    safe = to_json_safe(value)
    if not isinstance(safe, dict):
        raise TypeError("projection value must be a mapping")
    return MappingProxyType(safe)


class TradingProjection(BaseModel):
    """Route/tenant/authority-scoped optimistic execution projection.

    Attributes:
        version: Current optimistic projection version.
        event_ids: Ordered deduplication identities already applied.
        unresolved_attempt_ids: Send attempts awaiting proven authority outcome.
    """

    model_config = ConfigDict(frozen=True, extra="forbid", allow_inf_nan=False)

    route: TradingRoute
    tenant_id: str
    authority_id: str
    version: int
    event_ids: tuple[str, ...] = ()
    orders: Mapping[str, JsonValue]
    positions: Mapping[str, JsonValue]
    fills: Mapping[str, JsonValue]
    receipts: Mapping[str, JsonValue]
    authority_state: Mapping[str, JsonValue]
    trade_records: Mapping[str, JsonValue] = Field(default_factory=dict)
    incidents: Mapping[str, JsonValue] = Field(default_factory=dict)
    readiness: Mapping[str, JsonValue] = Field(default_factory=dict)
    unresolved_attempt_ids: tuple[str, ...] = ()
    updated_at: datetime

    @field_validator("tenant_id", "authority_id")
    @classmethod
    def _validate_text(cls, value: str) -> str:
        """Validate projection scope text.

        Args:
            value: Candidate scope identifier.

        Returns:
            Validated identifier.

        Raises:
            ValueError: If text is blank or untrimmed.
        """
        logger.debug("Validating TradingProjection scope text")
        if not value or value != value.strip():
            raise ValueError("projection scope must be non-empty and trimmed")
        return value

    @field_validator("event_ids", "unresolved_attempt_ids")
    @classmethod
    def _validate_ids(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        """Validate ordered unique projection identifiers.

        Args:
            value: Candidate identifiers.

        Returns:
            Validated identifiers.

        Raises:
            ValueError: If identifiers are blank or duplicated.
        """
        logger.debug("Validating TradingProjection event identities")
        if any(not item or item != item.strip() for item in value):
            raise ValueError("projection identifiers must be non-empty and trimmed")
        if len(set(value)) != len(value):
            raise ValueError("projection identifiers must be unique")
        return value

    @field_validator(
        "orders",
        "positions",
        "fills",
        "receipts",
        "authority_state",
        "trade_records",
        "incidents",
        "readiness",
        mode="before",
    )
    @classmethod
    def _validate_mapping(cls, value: Mapping[str, object]) -> Mapping[str, JsonValue]:
        """Validate an immutable JSON-safe projection mapping.

        Args:
            value: Candidate mapping.

        Returns:
            Immutable JSON-safe mapping.
        """
        logger.debug("Validating TradingProjection facts")
        return _freeze_mapping(value)

    @field_validator("updated_at")
    @classmethod
    def _validate_time(cls, value: datetime) -> datetime:
        """Validate projection UTC update time.

        Args:
            value: Candidate update time.

        Returns:
            Validated UTC timestamp.

        Raises:
            ValueError: If timestamp is naive or non-UTC.
        """
        logger.debug("Validating TradingProjection update time")
        if value.tzinfo is None or value.utcoffset() != timedelta(0):
            raise ValueError("projection update time must be timezone-aware UTC")
        return value

    @model_validator(mode="after")
    def _validate_version(self) -> Self:
        """Validate projection optimistic version.

        Returns:
            Validated projection.

        Raises:
            ValueError: If version is negative.
        """
        logger.debug("Validating TradingProjection optimistic version")
        if self.version < 0:
            raise ValueError("projection version must be non-negative")
        return self


def _empty_projection(event: TradingEvent) -> TradingProjection:
    """Create the zero-version projection for an event scope.

    Args:
        event: First event for one exact scope.

    Returns:
        Empty immutable projection.
    """
    logger.debug("Creating an empty Trading projection")
    return TradingProjection(
        route=event.route,
        tenant_id=event.tenant_id,
        authority_id=event.authority_id,
        version=0,
        orders={},
        positions={},
        fills={},
        receipts={},
        authority_state={},
        trade_records={},
        incidents={},
        readiness={},
        updated_at=event.occurred_at,
    )


def _merge_readiness(
    facts: dict[str, JsonValue],
    readiness: dict[str, JsonValue],
) -> None:
    """Merge explicitly recorded readiness facts into a projection.

    Args:
        facts: Reconciliation transition facts.
        readiness: Mutable next-projection readiness mapping.
    """
    logger.debug("Merging recorded Trading readiness facts")
    readiness_facts = facts.get("readiness")
    if isinstance(readiness_facts, dict):
        readiness.update(readiness_facts)


def _project_event(
    current: TradingProjection,
    event: TradingEvent,
) -> TradingProjection:
    """Return the next deterministic projection for one event.

    Args:
        current: Current projection.
        event: Ordered event to apply.

    Returns:
        Next immutable projection.
    """
    logger.debug("Projecting Trading event type %s", event.event_type)
    orders = dict(current.orders)
    positions = dict(current.positions)
    fills = dict(current.fills)
    receipts = dict(current.receipts)
    authority_state = dict(current.authority_state)
    trade_records = dict(current.trade_records)
    incidents = dict(current.incidents)
    readiness = dict(current.readiness)
    unresolved = list(current.unresolved_attempt_ids)
    facts = dict(event.payload)
    if event.event_type == "send_attempted":
        orders[event.event_id] = facts
        unresolved.append(event.event_id)
    elif event.event_type == "receipt_recorded":
        receipts[event.event_id] = facts
        trade_record = facts.get("trade_record")
        if isinstance(trade_record, dict):
            trade_records[event.event_id] = trade_record
        attempt_id = facts.get("attempt_event_id")
        if isinstance(attempt_id, str) and attempt_id in unresolved:
            unresolved.remove(attempt_id)
    elif event.event_type == "fill_recorded":
        fills[event.event_id] = facts
        position_id = facts.get("position_id")
        position = facts.get("position")
        if isinstance(position_id, str) and isinstance(position, dict):
            positions[position_id] = position
    elif event.event_type == "reconciliation_transitioned":
        authority_state[event.event_id] = facts
        _merge_readiness(facts, readiness)
        resolved_attempt_id = facts.get("resolved_attempt_event_id")
        if isinstance(resolved_attempt_id, str) and resolved_attempt_id in unresolved:
            unresolved.remove(resolved_attempt_id)
    elif event.event_type == "incident_recorded":
        incidents[event.event_id] = facts
    return TradingProjection(
        route=current.route,
        tenant_id=current.tenant_id,
        authority_id=current.authority_id,
        version=current.version + 1,
        event_ids=(*current.event_ids, event.event_id),
        orders=orders,
        positions=positions,
        fills=fills,
        receipts=receipts,
        authority_state=authority_state,
        trade_records=trade_records,
        incidents=incidents,
        readiness=readiness,
        unresolved_attempt_ids=tuple(unresolved),
        updated_at=event.occurred_at,
    )


def apply_execution_event(
    event: TradingEvent,
    store: TradingStateStore,
) -> TradingProjection:
    """Apply one deduplicated ordered event with optimistic version checks.

    Args:
        event: Versioned event to apply.
        store: Injected Trading state store.

    Returns:
        Existing duplicate or newly saved projection.

    Raises:
        TradingError: If scope, ordering, or persistence fails.
    """
    logger.info("Applying ordered Trading execution event %s", event.event_id)
    scope = (event.route, event.tenant_id, event.authority_id)
    try:
        current = store.load_projection(scope) or _empty_projection(event)
    except Exception as error:
        raise TradingError(
            "PERSISTENCE_FAILED",
            "Trading projection read failed",
            trace_context={"event_id": event.event_id},
        ) from error
    if event.event_id in current.event_ids:
        return current
    if event.aggregate_version != current.version:
        raise TradingError(
            "VERSION_CONFLICT",
            "Trading event optimistic version is stale",
            trace_context={"event_id": event.event_id},
        )
    if (current.route, current.tenant_id, current.authority_id) != scope:
        raise TradingError(
            "SCOPE_MISMATCH",
            "Trading event and projection scopes differ",
            trace_context={"event_id": event.event_id},
        )
    projected = _project_event(current, event)
    try:
        store.append_event(event)
        store.save_projection(projected, current.version)
    except Exception as error:
        raise TradingError(
            "PERSISTENCE_FAILED",
            "Trading projection persistence failed",
            trace_context={"event_id": event.event_id},
        ) from error
    return projected


__all__ = ["TradingProjection", "apply_execution_event"]
