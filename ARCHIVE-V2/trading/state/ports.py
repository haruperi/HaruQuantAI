"""Trading runtime persistence and infrastructure ports.

The trading domain depends on these protocol interfaces only. Concrete
database, broker, encryption, clock, RNG, and distributed-store implementations
must live outside ``app/services/trading`` and be injected by callers.
"""
# ruff: noqa: ARG002

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Protocol, runtime_checkable

from app.services.trading.contracts import JsonObject, TradingRoute
from app.utils.logger import logger


@runtime_checkable
class Clock(Protocol):
    """Injected clock dependency for deterministic trading runtime time reads."""

    def now_utc(self) -> datetime:
        """Return the current UTC timestamp.

        Returns:
            datetime: Timezone-aware UTC timestamp.
        """
        logger.debug("Clock.now_utc protocol placeholder invoked.")
        raise NotImplementedError

    def now_ptp(self) -> datetime:
        """Return the current PTP-aligned timestamp.

        Returns:
            datetime: PTP-aligned timestamp.
        """
        logger.debug("Clock.now_ptp protocol placeholder invoked.")
        raise NotImplementedError

    def monotonic(self) -> float:
        """Return monotonic elapsed time from the injected clock.

        Returns:
            float: Monotonic elapsed time in seconds.
        """
        logger.debug("Clock.monotonic protocol placeholder invoked.")
        raise NotImplementedError


@runtime_checkable
class RNG(Protocol):
    """Injected pseudo-random generator for deterministic retry jitter."""

    def random(self) -> float:
        """Return a pseudo-random float in the half-open interval [0.0, 1.0).

        Returns:
            float: Deterministic random draw.
        """
        logger.debug("RNG.random protocol placeholder invoked.")
        raise NotImplementedError

    def randint(self, lower_inclusive: int, upper_inclusive: int) -> int:
        """Return a pseudo-random integer from an inclusive range.

        Args:
            lower_inclusive: Lower inclusive bound.
            upper_inclusive: Upper inclusive bound.

        Returns:
            int: Deterministic integer draw.
        """
        logger.debug(
            "RNG.randint protocol placeholder invoked for bounds {}..{}.",
            lower_inclusive,
            upper_inclusive,
        )
        raise NotImplementedError


@runtime_checkable
class EncryptionProvider(Protocol):
    """Injected encryption and signing boundary for external infrastructure."""

    def encrypt(self, plaintext: str) -> str:
        """Encrypt plaintext data.

        Args:
            plaintext: Redacted plaintext value to encrypt.

        Returns:
            str: Encrypted value.
        """
        logger.debug("EncryptionProvider.encrypt protocol placeholder invoked.")
        raise NotImplementedError

    def decrypt(self, ciphertext: str) -> str:
        """Decrypt ciphertext data.

        Args:
            ciphertext: Encrypted value.

        Returns:
            str: Decrypted plaintext value.
        """
        logger.debug("EncryptionProvider.decrypt protocol placeholder invoked.")
        raise NotImplementedError

    def sign(self, payload: str) -> str:
        """Sign a canonical payload.

        Args:
            payload: Canonical payload string.

        Returns:
            str: Detached signature.
        """
        logger.debug("EncryptionProvider.sign protocol placeholder invoked.")
        raise NotImplementedError


@runtime_checkable
class TradeStore(Protocol):
    """Injected trade projection store port.

    Implementations must isolate non-live routes from live production storage
    and maintain Decimal VWAP plus remaining-volume projections.
    """

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
            order_state: JSON-safe order state.
            expected_version: Optimistic concurrency version.

        Returns:
            str: Persisted order state reference.

        Raises:
            IOError: If persistence fails.
        """
        logger.debug("TradeStore.save_order_state protocol placeholder invoked.")
        raise NotImplementedError

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
            position_state: JSON-safe position state.
            expected_version: Optimistic concurrency version.

        Returns:
            str: Persisted position state reference.
        """
        logger.debug("TradeStore.save_position_state protocol placeholder invoked.")
        raise NotImplementedError

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
        """Record a fill and update remaining volume and VWAP projections.

        Args:
            route: Runtime route.
            tenant_id: Tenant or session namespace.
            order_id: Local order identifier.
            filled_volume: Newly filled volume.
            fill_price: Fill price.
            broker_event_id: Unique broker execution event identifier.

        Returns:
            JsonObject: Updated JSON-safe projection summary.
        """
        logger.debug("TradeStore.record_execution_fill protocol placeholder invoked.")
        raise NotImplementedError

    def apply_corporate_action(
        self,
        *,
        route: TradingRoute,
        tenant_id: str,
        corporate_action: JsonObject,
        audit_ref: str,
    ) -> JsonObject:
        """Atomically apply a corporate-action adjustment.

        Args:
            route: Runtime route.
            tenant_id: Tenant or session namespace.
            corporate_action: JSON-safe classified corporate action event.
            audit_ref: Audit reference for the adjustment.

        Returns:
            JsonObject: Adjustment summary.
        """
        logger.debug("TradeStore.apply_corporate_action protocol placeholder invoked.")
        raise NotImplementedError

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
            JsonObject | None: The order state projection or None if not found.
        """
        logger.debug("TradeStore.get_order_state protocol placeholder invoked.")
        raise NotImplementedError

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
            JsonObject | None: The position state projection or None if not found.
        """
        logger.debug("TradeStore.get_position_state protocol placeholder invoked.")
        raise NotImplementedError

    def list_order_states(
        self,
        *,
        route: TradingRoute,
        tenant_id: str,
    ) -> list[JsonObject]:
        """List all active or historical order states for the tenant.

        Args:
            route: Runtime route.
            tenant_id: Tenant or session namespace.

        Returns:
            list[JsonObject]: List of order states.
        """
        logger.debug("TradeStore.list_order_states protocol placeholder invoked.")
        raise NotImplementedError

    def list_position_states(
        self,
        *,
        route: TradingRoute,
        tenant_id: str,
    ) -> list[JsonObject]:
        """List all active or historical position states for the tenant.

        Args:
            route: Runtime route.
            tenant_id: Tenant or session namespace.

        Returns:
            list[JsonObject]: List of position states.
        """
        logger.debug("TradeStore.list_position_states protocol placeholder invoked.")
        raise NotImplementedError


@runtime_checkable
class TradingStateStore(Protocol):
    """Injected state snapshot store for trading runtime authority state."""

    def save_state(
        self,
        *,
        route: TradingRoute,
        tenant_id: str,
        snapshot: JsonObject,
        expected_version: int | None,
    ) -> str:
        """Persist a trading runtime state snapshot.

        Args:
            route: Runtime route.
            tenant_id: Tenant or session namespace.
            snapshot: JSON-safe state snapshot.
            expected_version: Optimistic concurrency version.

        Returns:
            str: Persisted snapshot reference.
        """
        logger.debug("TradingStateStore.save_state protocol placeholder invoked.")
        raise NotImplementedError

    def load_state(
        self,
        *,
        route: TradingRoute,
        tenant_id: str,
        snapshot_id: str,
    ) -> JsonObject | None:
        """Load a trading runtime state snapshot.

        Args:
            route: Runtime route.
            tenant_id: Tenant or session namespace.
            snapshot_id: Snapshot identifier.

        Returns:
            JsonObject | None: Snapshot if present.
        """
        logger.debug("TradingStateStore.load_state protocol placeholder invoked.")
        raise NotImplementedError


@runtime_checkable
class AuditSink(Protocol):
    """Injected audit sink that must succeed before live broker mutation."""

    def append(self, *, event: JsonObject, recorded_at: datetime) -> str:
        """Append a redacted audit event.

        Args:
            event: JSON-safe audit event.
            recorded_at: UTC timestamp from injected Clock.

        Returns:
            str: Audit reference.
        """
        logger.debug("AuditSink.append protocol placeholder invoked.")
        raise NotImplementedError

    def flush(self) -> None:
        """Flush pending audit records.

        Raises:
            IOError: If audit flushing fails.
        """
        logger.debug("AuditSink.flush protocol placeholder invoked.")
        raise NotImplementedError


@runtime_checkable
class IdempotencyStore(Protocol):
    """Injected idempotency reservation and lookup store."""

    def reserve(
        self,
        *,
        route: TradingRoute,
        tenant_id: str,
        key: str,
        material_hash: str,
        expires_at: datetime,
    ) -> JsonObject:
        """Reserve an idempotency key before audit or broker mutation.

        Args:
            route: Runtime route.
            tenant_id: Tenant or session namespace.
            key: Idempotency key.
            material_hash: Canonical material hash.
            expires_at: Expiry timestamp from injected Clock.

        Returns:
            JsonObject: Reservation outcome.
        """
        logger.debug("IdempotencyStore.reserve protocol placeholder invoked.")
        raise NotImplementedError

    def resolve(
        self,
        *,
        route: TradingRoute,
        tenant_id: str,
        key: str,
        material_hash: str,
    ) -> JsonObject | None:
        """Resolve a previously reserved idempotency key.

        Args:
            route: Runtime route.
            tenant_id: Tenant or session namespace.
            key: Idempotency key.
            material_hash: Canonical material hash.

        Returns:
            JsonObject | None: Existing reservation result if present.
        """
        logger.debug("IdempotencyStore.resolve protocol placeholder invoked.")
        raise NotImplementedError

    def complete(
        self,
        *,
        route: TradingRoute,
        tenant_id: str,
        key: str,
        outcome: JsonObject,
        completed_at: datetime,
    ) -> None:
        """Complete an idempotency record.

        Args:
            route: Runtime route.
            tenant_id: Tenant or session namespace.
            key: Idempotency key.
            outcome: JSON-safe final outcome.
            completed_at: Completion timestamp from injected Clock.
        """
        logger.debug("IdempotencyStore.complete protocol placeholder invoked.")
        raise NotImplementedError


@runtime_checkable
class EventJournal(Protocol):
    """Injected append-only trading command and event journal."""

    def append(self, *, event: JsonObject, recorded_at: datetime) -> str:
        """Append a trading command or event.

        Args:
            event: JSON-safe journal event.
            recorded_at: UTC timestamp from injected Clock.

        Returns:
            str: Journal event reference.
        """
        logger.debug("EventJournal.append protocol placeholder invoked.")
        raise NotImplementedError

    def scan_unresolved(
        self,
        *,
        route: TradingRoute,
        tenant_id: str,
    ) -> tuple[JsonObject, ...]:
        """Scan unresolved journal entries for recovery.

        Args:
            route: Runtime route.
            tenant_id: Tenant or session namespace.

        Returns:
            tuple[JsonObject, ...]: Unresolved journal events.
        """
        logger.debug("EventJournal.scan_unresolved protocol placeholder invoked.")
        raise NotImplementedError
