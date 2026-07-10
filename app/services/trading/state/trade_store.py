"""Concrete ``TradeStore`` implementations (BF-TRD-002).

Provides an in-memory store for tests and non-live routes, and a durable JSONL
store that survives process restart. Both satisfy the
:class:`~app.services.trading.state.ports.TradeStore` protocol, maintain
``Decimal`` VWAP and remaining-volume projections, enforce optimistic
concurrency through ``expected_version``, and namespace every projection by
``(route, tenant_id)`` so non-live routes never share storage with live.

Neither store performs broker calls or imports provider SDKs.
"""
# TODO: Add support for saving in database (sqlite)
#

from __future__ import annotations

import json
import threading
from decimal import Decimal
from typing import TYPE_CHECKING

from app.services.trading.security.error_mapping import TradingMappedError
from app.utils.logger import logger

if TYPE_CHECKING:
    from pathlib import Path

    from app.services.trading.contracts import JsonObject, TradingRoute

_ORDER_KIND = "order"
_POSITION_KIND = "position"

_SPLIT_KINDS = frozenset({"split", "reverse_split"})


def _scope(route: TradingRoute, tenant_id: str) -> str:
    """Build the storage namespace key for a route and tenant.

    Args:
        route: Runtime route.
        tenant_id: Tenant or session namespace.

    Returns:
        str: Stable namespace key isolating live from non-live storage.

    Raises:
        TradingMappedError: If ``tenant_id`` is blank.
    """
    if not tenant_id.strip():
        raise TradingMappedError(
            "tenant_id must be non-empty.",
            code="INVALID_INPUT",
        )
    return f"{route.value}:{tenant_id}"


def _require_id(state: JsonObject, field: str) -> str:
    """Extract a required identifier from a state projection.

    Args:
        state: JSON-safe state projection.
        field: Identifier field name.

    Returns:
        str: The identifier value.

    Raises:
        TradingMappedError: If the identifier is missing or blank.
    """
    value = state.get(field)
    if not isinstance(value, str) or not value.strip():
        message = f"{field} must be a non-empty string in the state projection."
        raise TradingMappedError(
            message,
            code="INVALID_INPUT",
            details={"field": field},
        )
    return value


def _decimal(value: object, default: str = "0") -> Decimal:
    """Coerce a JSON-safe value into a Decimal.

    Args:
        value: Stored value, typically a string.
        default: Fallback when the value is absent.

    Returns:
        Decimal: Parsed decimal value.
    """
    if value is None:
        return Decimal(default)
    return Decimal(str(value))


class _TradeStoreCore:
    """Shared projection logic for the in-memory and JSONL trade stores.

    Subclasses supply durability by overriding :meth:`_load` and :meth:`_persist`.
    All projection semantics — versioning, VWAP accumulation, fill dedupe, and
    corporate-action adjustment — live here so both backends behave identically.
    """

    def __init__(self) -> None:
        """Initialize the shared lock guarding read-modify-write cycles."""
        self._lock = threading.RLock()

    def _load(self) -> dict[str, dict[str, JsonObject]]:
        """Load the full projection table.

        Returns:
            dict[str, dict[str, JsonObject]]: Scope key to record-id to record.
        """
        raise NotImplementedError

    def _persist(self, table: dict[str, dict[str, JsonObject]]) -> None:
        """Persist the full projection table.

        Args:
            table: Scope key to record-id to record.
        """
        raise NotImplementedError

    def _record_key(self, kind: str, entity_id: str) -> str:
        """Build the per-entity record key.

        Args:
            kind: ``order`` or ``position``.
            entity_id: Entity identifier.

        Returns:
            str: Composite record key.
        """
        return f"{kind}:{entity_id}"

    def _save(
        self,
        *,
        kind: str,
        route: TradingRoute,
        tenant_id: str,
        state: JsonObject,
        expected_version: int | None,
        id_field: str,
    ) -> str:
        """Persist a state projection under optimistic concurrency control.

        Args:
            kind: ``order`` or ``position``.
            route: Runtime route.
            tenant_id: Tenant or session namespace.
            state: JSON-safe state projection.
            expected_version: Optimistic concurrency version, or None to skip
                the check.
            id_field: Name of the identifier field within ``state``.

        Returns:
            str: Persisted state reference.

        Raises:
            TradingMappedError: If ``expected_version`` does not match the
                stored version.
        """
        entity_id = _require_id(state, id_field)
        scope = _scope(route, tenant_id)
        key = self._record_key(kind, entity_id)
        with self._lock:
            table = self._load()
            bucket = table.setdefault(scope, {})
            existing = bucket.get(key)
            current_version = int(existing["version"]) if existing else 0  # type: ignore[arg-type]
            if expected_version is not None and expected_version != current_version:
                raise TradingMappedError(
                    "Optimistic concurrency check failed for state projection.",
                    code="LIVE_STATE_VERSION_CONFLICT",
                    details={
                        "entity_id": entity_id,
                        "expected_version": expected_version,
                        "current_version": current_version,
                    },
                )
            record: JsonObject = dict(existing or {})
            record.update(state)
            record["version"] = current_version + 1
            bucket[key] = record
            self._persist(table)
        reference = f"{scope}/{key}@{current_version + 1}"
        logger.debug("Persisted {} state projection {}.", kind, reference)
        return reference

    def _get(
        self,
        *,
        kind: str,
        route: TradingRoute,
        tenant_id: str,
        entity_id: str,
    ) -> JsonObject | None:
        """Retrieve one state projection.

        Args:
            kind: ``order`` or ``position``.
            route: Runtime route.
            tenant_id: Tenant or session namespace.
            entity_id: Entity identifier.

        Returns:
            JsonObject | None: The projection, or None when absent.
        """
        with self._lock:
            table = self._load()
            record = table.get(_scope(route, tenant_id), {}).get(
                self._record_key(kind, entity_id)
            )
        return dict(record) if record is not None else None

    def _list(
        self,
        *,
        kind: str,
        route: TradingRoute,
        tenant_id: str,
    ) -> list[JsonObject]:
        """List every state projection of one kind for a scope.

        Args:
            kind: ``order`` or ``position``.
            route: Runtime route.
            tenant_id: Tenant or session namespace.

        Returns:
            list[JsonObject]: Matching projections.
        """
        prefix = f"{kind}:"
        with self._lock:
            bucket = self._load().get(_scope(route, tenant_id), {})
            return [dict(v) for k, v in bucket.items() if k.startswith(prefix)]

    def save_order_state(
        self,
        *,
        route: TradingRoute,
        tenant_id: str,
        order_state: JsonObject,
        expected_version: int | None,
    ) -> str:
        """Persist an order state projection.

        Args:
            route: Runtime route.
            tenant_id: Tenant or session namespace.
            order_state: JSON-safe order state containing ``order_id``.
            expected_version: Optimistic concurrency version.

        Returns:
            str: Persisted order state reference.
        """
        logger.info("Saving order state for tenant {}.", tenant_id)
        return self._save(
            kind=_ORDER_KIND,
            route=route,
            tenant_id=tenant_id,
            state=order_state,
            expected_version=expected_version,
            id_field="order_id",
        )

    def save_position_state(
        self,
        *,
        route: TradingRoute,
        tenant_id: str,
        position_state: JsonObject,
        expected_version: int | None,
    ) -> str:
        """Persist a position state projection.

        Args:
            route: Runtime route.
            tenant_id: Tenant or session namespace.
            position_state: JSON-safe position state containing ``position_id``.
            expected_version: Optimistic concurrency version.

        Returns:
            str: Persisted position state reference.
        """
        logger.info("Saving position state for tenant {}.", tenant_id)
        return self._save(
            kind=_POSITION_KIND,
            route=route,
            tenant_id=tenant_id,
            state=position_state,
            expected_version=expected_version,
            id_field="position_id",
        )

    def record_execution_fill(
        self,
        *,
        route: TradingRoute,
        tenant_id: str,
        order_id: str,
        filled_volume: Decimal,
        fill_price: Decimal,
        broker_event_id: str,
    ) -> JsonObject:
        """Record a fill and update remaining-volume and VWAP projections.

        Fills are deduplicated on ``broker_event_id``: a replayed broker event
        returns the existing projection without double-counting volume, which
        matters because broker execution streams redeliver on reconnect.

        Args:
            route: Runtime route.
            tenant_id: Tenant or session namespace.
            order_id: Local order identifier.
            filled_volume: Newly filled volume.
            fill_price: Fill price.
            broker_event_id: Unique broker execution event identifier.

        Returns:
            JsonObject: Updated JSON-safe projection summary.

        Raises:
            TradingMappedError: If the order is unknown, the volume is not
                positive, or the fill exceeds the order's total volume.
        """
        logger.info("Recording execution fill for order {}.", order_id)
        if filled_volume <= 0:
            raise TradingMappedError(
                "filled_volume must be positive.",
                code="INVALID_INPUT",
                details={"order_id": order_id},
            )
        scope = _scope(route, tenant_id)
        key = self._record_key(_ORDER_KIND, order_id)
        with self._lock:
            table = self._load()
            bucket = table.setdefault(scope, {})
            record = bucket.get(key)
            if record is None:
                raise TradingMappedError(
                    "Cannot record a fill against an unknown order.",
                    code="DATA_NOT_FOUND",
                    details={"order_id": order_id},
                )

            seen = list(record.get("processed_event_ids", []))  # type: ignore[arg-type]
            if broker_event_id in seen:
                logger.debug(
                    "Duplicate broker event {} for order {}; projection unchanged.",
                    broker_event_id,
                    order_id,
                )
                return dict(record)

            total_volume = _decimal(record.get("total_volume"))
            prior_filled = _decimal(record.get("filled_volume"))
            prior_vwap = _decimal(record.get("vwap"))
            new_filled = prior_filled + filled_volume
            if total_volume > 0 and new_filled > total_volume:
                raise TradingMappedError(
                    "Cumulative fill volume exceeds the order's total volume.",
                    code="VALIDATION_FAILED",
                    details={
                        "order_id": order_id,
                        "total_volume": str(total_volume),
                        "attempted_filled_volume": str(new_filled),
                    },
                )
            new_vwap = (
                (prior_vwap * prior_filled + fill_price * filled_volume) / new_filled
                if new_filled > 0
                else Decimal(0)
            )

            seen.append(broker_event_id)
            record["filled_volume"] = str(new_filled)
            record["remaining_volume"] = str(max(total_volume - new_filled, Decimal(0)))
            record["vwap"] = str(new_vwap)
            record["processed_event_ids"] = seen
            record["version"] = int(record.get("version", 0)) + 1  # type: ignore[arg-type]
            bucket[key] = record
            self._persist(table)
            summary = dict(record)
        logger.debug("Order {} filled {} at vwap {}.", order_id, new_filled, new_vwap)
        return summary

    def apply_corporate_action(
        self,
        *,
        route: TradingRoute,
        tenant_id: str,
        corporate_action: JsonObject,
        audit_ref: str,
    ) -> JsonObject:
        """Atomically apply a corporate-action adjustment to held positions.

        Splits and reverse splits rescale position volume and VWAP by ``ratio``.
        Symbol changes rewrite the ``symbol`` field. Name changes are recorded
        without adjusting projections. Every adjusted position carries the
        ``audit_ref`` of the action that changed it.

        Args:
            route: Runtime route.
            tenant_id: Tenant or session namespace.
            corporate_action: JSON-safe classified corporate action event.
            audit_ref: Audit reference for the adjustment.

        Returns:
            JsonObject: Adjustment summary.

        Raises:
            TradingMappedError: If ``audit_ref`` is blank, or the action is
                missing a field its kind requires.
        """
        kind = str(corporate_action.get("kind", ""))
        symbol = str(corporate_action.get("symbol", ""))
        logger.info("Applying corporate action {} for {}.", kind, symbol)
        if not audit_ref.strip():
            raise TradingMappedError(
                "audit_ref must be non-empty to apply a corporate action.",
                code="INVALID_INPUT",
            )

        scope = _scope(route, tenant_id)
        adjusted: list[str] = []
        with self._lock:
            table = self._load()
            bucket = table.setdefault(scope, {})
            for key, record in bucket.items():
                if not key.startswith(f"{_POSITION_KIND}:"):
                    continue
                if str(record.get("symbol", "")) != symbol:
                    continue

                if kind in _SPLIT_KINDS:
                    ratio = _decimal(corporate_action.get("ratio"), default="0")
                    if ratio <= 0:
                        raise TradingMappedError(
                            "ratio must be positive for split/reverse_split.",
                            code="INVALID_INPUT",
                            details={"kind": kind},
                        )
                    volume = _decimal(record.get("volume"))
                    vwap = _decimal(record.get("vwap"))
                    if kind == "split":
                        record["volume"] = str(volume * ratio)
                        record["vwap"] = str(vwap / ratio)
                    else:
                        record["volume"] = str(volume / ratio)
                        record["vwap"] = str(vwap * ratio)
                elif kind == "symbol_change":
                    new_symbol = corporate_action.get("new_symbol")
                    if not isinstance(new_symbol, str) or not new_symbol.strip():
                        raise TradingMappedError(
                            "new_symbol is required for symbol_change actions.",
                            code="INVALID_INPUT",
                        )
                    record["symbol"] = new_symbol

                record["corporate_action_audit_ref"] = audit_ref
                record["version"] = int(record.get("version", 0)) + 1  # type: ignore[arg-type]
                adjusted.append(str(record.get("position_id", key)))
            self._persist(table)

        summary: JsonObject = {
            "kind": kind,
            "symbol": symbol,
            "audit_ref": audit_ref,
            "adjusted_position_ids": adjusted,
        }
        logger.debug("Corporate action adjusted {} position(s).", len(adjusted))
        return summary

    def get_order_state(
        self,
        *,
        route: TradingRoute,
        tenant_id: str,
        order_id: str,
    ) -> JsonObject | None:
        """Retrieve an order state projection by ID.

        Args:
            route: Runtime route.
            tenant_id: Tenant or session namespace.
            order_id: Local order identifier.

        Returns:
            JsonObject | None: The projection, or None when absent.
        """
        logger.info("Reading order state {}.", order_id)
        return self._get(
            kind=_ORDER_KIND, route=route, tenant_id=tenant_id, entity_id=order_id
        )

    def get_position_state(
        self,
        *,
        route: TradingRoute,
        tenant_id: str,
        position_id: str,
    ) -> JsonObject | None:
        """Retrieve a position state projection by ID.

        Args:
            route: Runtime route.
            tenant_id: Tenant or session namespace.
            position_id: Local position identifier.

        Returns:
            JsonObject | None: The projection, or None when absent.
        """
        logger.info("Reading position state {}.", position_id)
        return self._get(
            kind=_POSITION_KIND, route=route, tenant_id=tenant_id, entity_id=position_id
        )

    def list_order_states(
        self,
        *,
        route: TradingRoute,
        tenant_id: str,
    ) -> list[JsonObject]:
        """List every order state projection for the tenant.

        Args:
            route: Runtime route.
            tenant_id: Tenant or session namespace.

        Returns:
            list[JsonObject]: Order state projections.
        """
        logger.info("Listing order states for tenant {}.", tenant_id)
        return self._list(kind=_ORDER_KIND, route=route, tenant_id=tenant_id)

    def list_position_states(
        self,
        *,
        route: TradingRoute,
        tenant_id: str,
    ) -> list[JsonObject]:
        """List every position state projection for the tenant.

        Args:
            route: Runtime route.
            tenant_id: Tenant or session namespace.

        Returns:
            list[JsonObject]: Position state projections.
        """
        logger.info("Listing position states for tenant {}.", tenant_id)
        return self._list(kind=_POSITION_KIND, route=route, tenant_id=tenant_id)


class InMemoryTradeStore(_TradeStoreCore):
    """Volatile in-process trade projection store.

    Intended for unit tests and non-live routes. State is lost on restart, so
    live routes should use :class:`JsonlTradeStore`.
    """

    def __init__(self) -> None:
        """Initialize an empty in-memory projection table."""
        super().__init__()
        logger.info("Initializing in-memory trade store.")
        self._table: dict[str, dict[str, JsonObject]] = {}

    def _load(self) -> dict[str, dict[str, JsonObject]]:
        """Return the live projection table.

        Returns:
            dict[str, dict[str, JsonObject]]: Mutable projection table.
        """
        return self._table

    def _persist(self, table: dict[str, dict[str, JsonObject]]) -> None:
        """Retain the projection table in process memory.

        Args:
            table: Projection table, already mutated in place.
        """
        self._table = table


class JsonlTradeStore(_TradeStoreCore):
    """Durable JSONL-backed trade projection store.

    Each line is one ``{"scope": ..., "key": ..., "record": {...}}`` entry. The
    file is rewritten atomically through a sibling temp file on every mutation,
    matching the durability idiom of ``JsonlIdempotencyStore``.

    Args:
        path: Durable JSONL path.
    """

    def __init__(self, *, path: Path) -> None:
        """Initialize the durable trade store.

        Args:
            path: Durable JSONL path.
        """
        super().__init__()
        logger.info("Initializing durable trade store at {}.", path)
        self._path = path

    def _load(self) -> dict[str, dict[str, JsonObject]]:
        """Load the projection table from disk.

        Returns:
            dict[str, dict[str, JsonObject]]: Reconstructed projection table.
        """
        if not self._path.exists():
            return {}
        table: dict[str, dict[str, JsonObject]] = {}
        for line in self._path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            entry = json.loads(line)
            table.setdefault(entry["scope"], {})[entry["key"]] = entry["record"]
        return table

    def _persist(self, table: dict[str, dict[str, JsonObject]]) -> None:
        """Rewrite the durable projection file atomically.

        Args:
            table: Projection table to persist.
        """
        self._path.parent.mkdir(parents=True, exist_ok=True)
        lines = [
            json.dumps({"scope": scope, "key": key, "record": record}, sort_keys=True)
            for scope, bucket in sorted(table.items())
            for key, record in sorted(bucket.items())
        ]
        temp_path = self._path.with_suffix(f"{self._path.suffix}.tmp")
        temp_path.write_text(
            "\n".join(lines) + ("\n" if lines else ""), encoding="utf-8"
        )
        temp_path.replace(self._path)
        logger.debug("Rewrote durable trade store with {} record(s).", len(lines))
