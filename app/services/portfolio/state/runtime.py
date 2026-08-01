"""Portfolio state protocol over Data-owned durable runtime records."""

from __future__ import annotations

import json
from collections.abc import Mapping
from datetime import datetime
from decimal import Decimal
from types import UnionType
from typing import Any, cast, get_args, get_origin

from pydantic import BaseModel

from app.services.data import (
    build_portfolio_runtime_store,
    execute_runtime_store_operation,
    execute_runtime_store_transition,
)
from app.services.portfolio.contracts import (
    ActivePortfolioAllocation,
    PortfolioConstructionResult,
    PortfolioRebalancePlan,
)
from app.utils import canonical_digest, canonical_json, get_logger

logger = get_logger(__name__)
type AuditOutboxRecord = Mapping[str, str]
_MAPPING_TYPE_ARGUMENT_COUNT = 2


def _encode_model(value: object) -> str:
    """Encode one allowlisted Portfolio model.

    Returns:
        JSON text.

    Raises:
        TypeError: If the value is not a validated model.
    """
    if not isinstance(value, BaseModel):
        raise TypeError("Portfolio runtime state must be a validated model")
    return value.model_dump_json()


def _encode_mapping(value: object) -> str:
    """Encode one bounded outbox envelope.

    Returns:
        Canonical JSON text.

    Raises:
        TypeError: If the value is not a mapping.
    """
    if not isinstance(value, Mapping):
        raise TypeError("Portfolio outbox value must be a mapping")
    return canonical_json(dict(value), max_items=None)


def _coerce_model_field(annotation: type[BaseModel], value: object) -> BaseModel:
    """Restore and validate one nested strict contract.

    Returns:
        Validated nested model.

    Raises:
        TypeError: If the stored value is not an object.
    """
    if not isinstance(value, dict):
        raise TypeError("nested Portfolio runtime model must be an object")
    return _construct_model(annotation, value)


def _coerce_sequence(
    arguments: tuple[object, ...], value: object
) -> tuple[object, ...]:
    """Restore one JSON array as a typed tuple.

    Returns:
        Restored tuple.

    Raises:
        TypeError: If the stored value is not an array.
    """
    if not isinstance(value, list):
        raise TypeError("Portfolio runtime tuple must be a JSON array")
    item_type = arguments[0] if arguments else Any
    return tuple(_coerce_field(item_type, item) for item in value)


def _coerce_mapping(
    arguments: tuple[object, ...], value: object
) -> dict[object, object]:
    """Restore one JSON object as a typed mapping.

    Returns:
        Restored mapping.

    Raises:
        TypeError: If the stored value is not an object.
    """
    if not isinstance(value, dict):
        raise TypeError("Portfolio runtime mapping must be an object")
    key_type, item_type = (
        arguments if len(arguments) == _MAPPING_TYPE_ARGUMENT_COUNT else (Any, Any)
    )
    return {
        _coerce_field(key_type, key): _coerce_field(item_type, item)
        for key, item in value.items()
    }


def _coerce_union(arguments: tuple[object, ...], value: object) -> object:
    """Restore one optional or union field using its declared alternatives.

    Returns:
        First compatible restored alternative, or the original value.
    """
    if value is None and type(None) in arguments:
        return None
    for member in arguments:
        if member is type(None):
            continue
        try:
            return _coerce_field(member, value)
        except TypeError, ValueError:
            continue
    return value


def _coerce_field(annotation: object, value: object) -> object:
    """Restore JSON values to the exact Python types used by strict contracts.

    Returns:
        Restored field value.

    Raises:
        TypeError: If a structured stored value has the wrong JSON shape.
    """
    result = value
    if isinstance(annotation, type) and issubclass(annotation, BaseModel):
        result = _coerce_model_field(annotation, value)
    elif annotation is datetime:
        if not isinstance(value, str):
            raise TypeError("Portfolio runtime datetime must be text")
        result = datetime.fromisoformat(value)
    elif annotation is Decimal:
        if not isinstance(value, (str, int, float)) or isinstance(value, bool):
            raise TypeError("Portfolio runtime decimal is malformed")
        result = Decimal(str(value))
    else:
        origin = get_origin(annotation)
        arguments = get_args(annotation)
        if origin is tuple:
            result = _coerce_sequence(arguments, value)
        elif origin in {dict, Mapping}:
            result = _coerce_mapping(arguments, value)
        elif origin is UnionType:
            result = _coerce_union(arguments, value)
    return result


def _construct_model(
    model_type: type[BaseModel], decoded: Mapping[str, object]
) -> BaseModel:
    """Construct one strict contract from an already decoded JSON object.

    Returns:
        Validated Portfolio model.
    """
    fields: dict[str, object] = {
        name: _coerce_field(field.annotation, decoded[name])
        for name, field in model_type.model_fields.items()
        if name in decoded
    }
    return model_type(**fields)


def _decode_model(model_type: type[BaseModel], payload: str) -> BaseModel:
    """Decode persisted JSON into strict Python field values before validation.

    Returns:
        Validated Portfolio model.

    Raises:
        TypeError: If the decoded JSON is not an object.
    """
    decoded = json.loads(payload)
    if not isinstance(decoded, dict):
        raise TypeError("Portfolio runtime model payload must be an object")
    return _construct_model(model_type, decoded)


def _key(*parts: str) -> str:
    """Derive one bounded stable record key.

    Returns:
        Storage-safe key.
    """
    return f"record-{canonical_digest(parts)}"


def _sequence(value: Mapping[str, object]) -> int:
    """Derive a positive deterministic outbox sequence.

    Returns:
        Positive SQLite-safe integer.
    """
    return int(canonical_digest(dict(value))[:15], 16) + 1


class _DurablePortfolioStateStore:
    """Concrete Portfolio adapter over Data runtime records."""

    def __init__(self) -> None:
        """Construct the adapter without opening a connection."""
        self._store = build_portfolio_runtime_store(
            {
                "allocation": (
                    _encode_model,
                    lambda payload: _decode_model(ActivePortfolioAllocation, payload),
                ),
                "construction": (
                    _encode_model,
                    lambda payload: _decode_model(PortfolioConstructionResult, payload),
                ),
                "outbox": (_encode_mapping, json.loads),
                "plan": (
                    _encode_model,
                    lambda payload: _decode_model(PortfolioRebalancePlan, payload),
                ),
            }
        )

    def _commit_immutable(
        self,
        *,
        collection: str,
        key: str,
        kind: str,
        value: object,
        audit_record: AuditOutboxRecord,
    ) -> None:
        """Atomically persist immutable state and its outbox evidence.

        Raises:
            ValueError: If stored material conflicts with the immutable value.
        """
        outbox = {
            "audit": dict(audit_record),
            "collection": collection,
            "record_key": key,
        }
        committed = execute_runtime_store_transition(
            self._store,
            state_collection=collection,
            state_key=key,
            state_kind=kind,
            state_value=value,
            expected_revision=0,
            event_collection="outbox",
            event_key=_key("outbox", collection, key),
            event_partition="events",
            event_sequence=_sequence(outbox),
            event_kind="outbox",
            event_value=outbox,
        )
        if not committed:
            existing = execute_runtime_store_operation(
                self._store, "get", collection=collection, key=key
            )
            if existing != value:
                raise ValueError("Portfolio immutable state conflicts")

    def save_construction(
        self,
        result: PortfolioConstructionResult,
        audit_record: AuditOutboxRecord,
    ) -> PortfolioConstructionResult:
        """Atomically save construction state and audit outbox.

        Returns:
            Persisted construction result.
        """
        self._commit_immutable(
            collection="constructions",
            key=result.canonical_hash,
            kind="construction",
            value=result,
            audit_record=audit_record,
        )
        return result

    def activate_allocation(
        self,
        allocation: ActivePortfolioAllocation,
        expected_predecessor: str | None,
        expected_revision: int,
        material_hash: str,
        audit_record: AuditOutboxRecord,
    ) -> ActivePortfolioAllocation:
        """Atomically activate an allocation and append history/audit evidence.

        Returns:
            Persisted active allocation.

        Raises:
            ValueError: If predecessor, material, or revision evidence conflicts.
        """
        if material_hash != allocation.canonical_hash:
            raise ValueError("Portfolio allocation material hash conflicts")
        active_key = _key(
            allocation.portfolio_id,
            canonical_json(dict(allocation.scope), max_items=None),
        )
        stored = cast(
            "tuple[ActivePortfolioAllocation, int] | None",
            execute_runtime_store_operation(
                self._store,
                "get_with_revision",
                collection="active",
                key=active_key,
            ),
        )
        if stored is None:
            if expected_predecessor is not None or expected_revision != 0:
                raise ValueError("Portfolio activation predecessor conflicts")
        elif (
            stored[0].allocation_version != expected_predecessor
            or stored[1] != expected_revision
        ):
            raise ValueError("Portfolio activation revision conflicts")
        history = {
            "allocation": json.loads(allocation.model_dump_json()),
            "audit": dict(audit_record),
        }
        existing_history = cast(
            "tuple[object, ...]",
            execute_runtime_store_operation(
                self._store,
                "list",
                collection="allocation-history",
                partition=_key("history", allocation.portfolio_id),
                limit=1_000,
            ),
        )
        committed = execute_runtime_store_transition(
            self._store,
            state_collection="active",
            state_key=active_key,
            state_kind="allocation",
            state_value=allocation,
            expected_revision=expected_revision,
            event_collection="allocation-history",
            event_key=_key(allocation.portfolio_id, allocation.allocation_version),
            event_partition=_key("history", allocation.portfolio_id),
            event_sequence=len(existing_history) + 1,
            event_kind="outbox",
            event_value=history,
        )
        if not committed:
            raise ValueError("Portfolio activation compare-and-swap failed")
        return allocation

    def save_plan(
        self,
        plan: PortfolioRebalancePlan,
        audit_record: AuditOutboxRecord,
    ) -> PortfolioRebalancePlan:
        """Atomically save a plan and its outbox evidence.

        Returns:
            Persisted plan.

        Raises:
            ValueError: If stored material conflicts with the immutable plan.
        """
        plan_key = _key(plan.plan_id, plan.plan_version)
        versions = cast(
            "tuple[Mapping[str, object], ...]",
            execute_runtime_store_operation(
                self._store,
                "list",
                collection="plan-versions",
                partition=_key("plans", plan.plan_id),
                limit=1_000,
            ),
        )
        history = {
            "audit": dict(audit_record),
            "plan": json.loads(plan.model_dump_json()),
        }
        committed = execute_runtime_store_transition(
            self._store,
            state_collection="plans",
            state_key=plan_key,
            state_kind="plan",
            state_value=plan,
            expected_revision=0,
            event_collection="plan-versions",
            event_key=plan_key,
            event_partition=_key("plans", plan.plan_id),
            event_sequence=len(versions) + 1,
            event_kind="outbox",
            event_value=history,
        )
        if not committed:
            existing = execute_runtime_store_operation(
                self._store, "get", collection="plans", key=plan_key
            )
            if existing != plan:
                raise ValueError("Portfolio immutable plan conflicts")
        return plan

    def load_active(
        self, portfolio_id: str, scope_key: str
    ) -> tuple[ActivePortfolioAllocation, int] | None:
        """Load active allocation and revision for an exact scope.

        Returns:
            Active allocation with revision or ``None``.
        """
        return cast(
            "tuple[ActivePortfolioAllocation, int] | None",
            execute_runtime_store_operation(
                self._store,
                "get_with_revision",
                collection="active",
                key=_key(portfolio_id, scope_key),
            ),
        )

    def load_allocation(
        self, portfolio_id: str, allocation_version: str
    ) -> ActivePortfolioAllocation | None:
        """Load one immutable allocation version.

        Returns:
            Allocation or ``None``.
        """
        return next(
            (
                allocation
                for allocation in self.load_history(portfolio_id)
                if allocation.allocation_version == allocation_version
            ),
            None,
        )

    def load_history(self, portfolio_id: str) -> tuple[ActivePortfolioAllocation, ...]:
        """Load ordered immutable allocation history.

        Returns:
            Ordered allocation versions.
        """
        rows = cast(
            "tuple[Mapping[str, object], ...]",
            execute_runtime_store_operation(
                self._store,
                "list",
                collection="allocation-history",
                partition=_key("history", portfolio_id),
                limit=1_000,
            ),
        )
        return tuple(
            cast(
                "ActivePortfolioAllocation",
                _decode_model(
                    ActivePortfolioAllocation,
                    canonical_json(row["allocation"], max_items=None),
                ),
            )
            for row in rows
        )

    def load_plan(
        self, plan_id: str, plan_version: str | None
    ) -> PortfolioRebalancePlan | None:
        """Load one exact or latest plan version.

        Returns:
            Plan or ``None``.
        """
        if plan_version is not None:
            return cast(
                "PortfolioRebalancePlan | None",
                execute_runtime_store_operation(
                    self._store,
                    "get",
                    collection="plans",
                    key=_key(plan_id, plan_version),
                ),
            )
        versions = cast(
            "tuple[Mapping[str, object], ...]",
            execute_runtime_store_operation(
                self._store,
                "list",
                collection="plan-versions",
                partition=_key("plans", plan_id),
                limit=1_000,
            ),
        )
        if not versions:
            return None
        return cast(
            "PortfolioRebalancePlan",
            _decode_model(
                PortfolioRebalancePlan,
                canonical_json(versions[-1]["plan"], max_items=None),
            ),
        )


def build_portfolio_state_store() -> object:
    """Build the durable Portfolio state adapter.

    Returns:
        Opaque Portfolio state-store handle.
    """
    logger.info("Building durable Portfolio state adapter")
    return _DurablePortfolioStateStore()


def execute_portfolio_state_store_operation(
    store: object, operation: str, /, *args: object, **kwargs: object
) -> object:
    """Execute one allowlisted Portfolio state operation.

    Returns:
        Exact state result.

    Raises:
        TypeError: If the handle is invalid.
        ValueError: If the operation is unsupported.
    """
    allowed = {
        "activate_allocation",
        "load_active",
        "load_allocation",
        "load_history",
        "load_plan",
        "save_construction",
        "save_plan",
    }
    if not isinstance(store, _DurablePortfolioStateStore):
        raise TypeError("invalid Portfolio state-store handle")
    if operation not in allowed:
        raise ValueError("unsupported Portfolio state-store operation")
    return getattr(store, operation)(*args, **kwargs)


__all__ = (
    "build_portfolio_state_store",
    "execute_portfolio_state_store_operation",
)
