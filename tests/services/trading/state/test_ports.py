"""Tests for trading state protocol ports."""
# ruff: noqa: ARG002

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from typing import cast

import pytest
from app.services.trading import TradingRoute
from app.services.trading.state import (
    RNG,
    AuditSink,
    Clock,
    EncryptionProvider,
    EventJournal,
    IdempotencyStore,
    TradeStore,
    TradingStateStore,
)


class DummyClock:
    def now_utc(self) -> datetime:
        return datetime(2026, 7, 9, tzinfo=UTC)

    def now_ptp(self) -> datetime:
        return datetime(2026, 7, 9, tzinfo=UTC)

    def monotonic(self) -> float:
        return 10.0


class DummyRNG:
    def random(self) -> float:
        return 0.5

    def randint(self, lower_inclusive: int, upper_inclusive: int) -> int:
        return lower_inclusive + (upper_inclusive - lower_inclusive) // 2


class DummyEncryptionProvider:
    def encrypt(self, plaintext: str) -> str:
        return f"enc:{plaintext}"

    def decrypt(self, ciphertext: str) -> str:
        return ciphertext.removeprefix("enc:")

    def sign(self, payload: str) -> str:
        return f"sig:{payload}"


class DummyTradeStore:
    def save_order_state(
        self,
        *,
        route: TradingRoute,
        tenant_id: str,
        order_state: dict[str, object],
        expected_version: int | None,
    ) -> str:
        return f"{route.value}:{tenant_id}:{expected_version}:{order_state['id']}"

    def save_position_state(
        self,
        *,
        route: TradingRoute,
        tenant_id: str,
        position_state: dict[str, object],
        expected_version: int | None,
    ) -> str:
        return f"{route.value}:{tenant_id}:{expected_version}:{position_state['id']}"

    def record_execution_fill(
        self,
        *,
        route: TradingRoute,
        tenant_id: str,
        order_id: str,
        filled_volume: Decimal,
        fill_price: Decimal,
        broker_event_id: str,
    ) -> dict[str, object]:
        return {
            "route": route.value,
            "tenant_id": tenant_id,
            "order_id": order_id,
            "filled_volume": str(filled_volume),
            "fill_price": str(fill_price),
            "broker_event_id": broker_event_id,
        }

    def apply_corporate_action(
        self,
        *,
        route: TradingRoute,
        tenant_id: str,
        corporate_action: dict[str, object],
        audit_ref: str,
    ) -> dict[str, object]:
        return {
            "route": route.value,
            "tenant_id": tenant_id,
            "corporate_action": corporate_action,
            "audit_ref": audit_ref,
        }

    def get_order_state(
        self,
        *,
        route: TradingRoute,
        tenant_id: str,
        order_id: str,
    ) -> dict[str, object] | None:
        return {"id": order_id, "route": route, "tenant_id": tenant_id}

    def get_position_state(
        self,
        *,
        route: TradingRoute,
        tenant_id: str,
        position_id: str,
    ) -> dict[str, object] | None:
        return {"id": position_id, "route": route, "tenant_id": tenant_id}

    def list_order_states(
        self,
        *,
        route: TradingRoute,
        tenant_id: str,
    ) -> list[dict[str, object]]:
        return []

    def list_position_states(
        self,
        *,
        route: TradingRoute,
        tenant_id: str,
    ) -> list[dict[str, object]]:
        return []


class DummyTradingStateStore:
    def save_state(
        self,
        *,
        route: TradingRoute,
        tenant_id: str,
        snapshot: dict[str, object],
        expected_version: int | None,
    ) -> str:
        return f"{route.value}:{tenant_id}:{expected_version}:{snapshot['id']}"

    def load_state(
        self,
        *,
        route: TradingRoute,
        tenant_id: str,
        snapshot_id: str,
    ) -> dict[str, object] | None:
        return {"route": route.value, "tenant_id": tenant_id, "id": snapshot_id}


class DummyAuditSink:
    def append(self, *, event: dict[str, object], recorded_at: datetime) -> str:
        return f"audit:{event['id']}:{recorded_at.isoformat()}"

    def flush(self) -> None:
        return None


class DummyIdempotencyStore:
    def reserve(
        self,
        *,
        route: TradingRoute,
        tenant_id: str,
        key: str,
        material_hash: str,
        expires_at: datetime,
    ) -> dict[str, object]:
        return {
            "route": route.value,
            "tenant_id": tenant_id,
            "key": key,
            "material_hash": material_hash,
            "expires_at": expires_at.isoformat(),
        }

    def resolve(
        self,
        *,
        route: TradingRoute,
        tenant_id: str,
        key: str,
        material_hash: str,
    ) -> dict[str, object] | None:
        return {
            "route": route.value,
            "tenant_id": tenant_id,
            "key": key,
            "material_hash": material_hash,
        }

    def complete(
        self,
        *,
        route: TradingRoute,
        tenant_id: str,
        key: str,
        outcome: dict[str, object],
        completed_at: datetime,
    ) -> None:
        return None


class DummyEventJournal:
    def append(self, *, event: dict[str, object], recorded_at: datetime) -> str:
        return f"journal:{event['id']}:{recorded_at.isoformat()}"

    def scan_unresolved(
        self,
        *,
        route: TradingRoute,
        tenant_id: str,
    ) -> tuple[dict[str, object], ...]:
        return ({"route": route.value, "tenant_id": tenant_id},)


def test_protocols_are_runtime_checkable() -> None:
    assert isinstance(DummyClock(), Clock)
    assert isinstance(DummyRNG(), RNG)
    assert isinstance(DummyEncryptionProvider(), EncryptionProvider)
    assert isinstance(DummyTradeStore(), TradeStore)
    assert isinstance(DummyTradingStateStore(), TradingStateStore)
    assert isinstance(DummyAuditSink(), AuditSink)
    assert isinstance(DummyIdempotencyStore(), IdempotencyStore)
    assert isinstance(DummyEventJournal(), EventJournal)


def test_ports_express_injected_time_rng_and_isolated_route_contracts() -> None:
    clock = DummyClock()
    rng = DummyRNG()
    trade_store = DummyTradeStore()
    idempotency = DummyIdempotencyStore()
    journal = DummyEventJournal()

    now = clock.now_utc()

    assert clock.now_ptp() == now
    assert clock.monotonic() == 10.0
    assert rng.random() == 0.5
    assert rng.randint(1, 3) == 2
    assert (
        trade_store.record_execution_fill(
            route=TradingRoute.SIM,
            tenant_id="tenant-a",
            order_id="order-1",
            filled_volume=Decimal("0.10"),
            fill_price=Decimal("1.1000"),
            broker_event_id="event-1",
        )["route"]
        == "sim"
    )
    assert (
        idempotency.reserve(
            route=TradingRoute.PAPER,
            tenant_id="tenant-b",
            key="key-1",
            material_hash="hash-1",
            expires_at=now,
        )["tenant_id"]
        == "tenant-b"
    )
    assert (
        journal.scan_unresolved(
            route=TradingRoute.SHADOW,
            tenant_id="tenant-c",
        )[0]["route"]
        == "shadow"
    )


def test_clock_rng_and_crypto_protocol_placeholders_raise_not_implemented() -> None:
    clock = object()
    rng = object()
    encryption = object()

    with pytest.raises(NotImplementedError):
        Clock.now_utc(cast("Clock", clock))
    with pytest.raises(NotImplementedError):
        Clock.now_ptp(cast("Clock", clock))
    with pytest.raises(NotImplementedError):
        Clock.monotonic(cast("Clock", clock))
    with pytest.raises(NotImplementedError):
        RNG.random(cast("RNG", rng))
    with pytest.raises(NotImplementedError):
        RNG.randint(cast("RNG", rng), 1, 2)
    with pytest.raises(NotImplementedError):
        EncryptionProvider.encrypt(cast("EncryptionProvider", encryption), "plain")
    with pytest.raises(NotImplementedError):
        EncryptionProvider.decrypt(cast("EncryptionProvider", encryption), "cipher")
    with pytest.raises(NotImplementedError):
        EncryptionProvider.sign(cast("EncryptionProvider", encryption), "payload")


def test_store_protocol_placeholders_raise_not_implemented() -> None:
    trade_store = object()
    state_store = object()
    audit_sink = object()
    idempotency_store = object()
    event_journal = object()
    now = datetime(2026, 7, 9, tzinfo=UTC)

    with pytest.raises(NotImplementedError):
        TradeStore.save_order_state(
            cast("TradeStore", trade_store),
            route=TradingRoute.SIM,
            tenant_id="tenant",
            order_state={},
            expected_version=None,
        )
    with pytest.raises(NotImplementedError):
        TradeStore.save_position_state(
            cast("TradeStore", trade_store),
            route=TradingRoute.SIM,
            tenant_id="tenant",
            position_state={},
            expected_version=None,
        )
    with pytest.raises(NotImplementedError):
        TradeStore.record_execution_fill(
            cast("TradeStore", trade_store),
            route=TradingRoute.SIM,
            tenant_id="tenant",
            order_id="order",
            filled_volume=Decimal("0.1"),
            fill_price=Decimal("1.0"),
            broker_event_id="event",
        )
    with pytest.raises(NotImplementedError):
        TradeStore.apply_corporate_action(
            cast("TradeStore", trade_store),
            route=TradingRoute.SIM,
            tenant_id="tenant",
            corporate_action={},
            audit_ref="audit",
        )
    with pytest.raises(NotImplementedError):
        TradingStateStore.save_state(
            cast("TradingStateStore", state_store),
            route=TradingRoute.SIM,
            tenant_id="tenant",
            snapshot={},
            expected_version=None,
        )
    with pytest.raises(NotImplementedError):
        TradingStateStore.load_state(
            cast("TradingStateStore", state_store),
            route=TradingRoute.SIM,
            tenant_id="tenant",
            snapshot_id="snapshot",
        )
    with pytest.raises(NotImplementedError):
        AuditSink.append(cast("AuditSink", audit_sink), event={}, recorded_at=now)
    with pytest.raises(NotImplementedError):
        AuditSink.flush(cast("AuditSink", audit_sink))
    with pytest.raises(NotImplementedError):
        IdempotencyStore.reserve(
            cast("IdempotencyStore", idempotency_store),
            route=TradingRoute.SIM,
            tenant_id="tenant",
            key="key",
            material_hash="hash",
            expires_at=now,
        )
    with pytest.raises(NotImplementedError):
        IdempotencyStore.resolve(
            cast("IdempotencyStore", idempotency_store),
            route=TradingRoute.SIM,
            tenant_id="tenant",
            key="key",
            material_hash="hash",
        )
    with pytest.raises(NotImplementedError):
        IdempotencyStore.complete(
            cast("IdempotencyStore", idempotency_store),
            route=TradingRoute.SIM,
            tenant_id="tenant",
            key="key",
            outcome={},
            completed_at=now,
        )
    with pytest.raises(NotImplementedError):
        EventJournal.append(
            cast("EventJournal", event_journal),
            event={},
            recorded_at=now,
        )
    with pytest.raises(NotImplementedError):
        EventJournal.scan_unresolved(
            cast("EventJournal", event_journal),
            route=TradingRoute.SIM,
            tenant_id="tenant",
        )
