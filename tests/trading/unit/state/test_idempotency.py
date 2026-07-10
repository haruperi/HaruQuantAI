"""Tests for trading idempotency persistence."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from app.services.trading import TradingAction, TradingRoute
from app.services.trading.state import (
    IDEMPOTENCY_MATERIAL_FIELDS,
    IdempotencyDecision,
    IdempotencyMaterial,
    IdempotencyRecord,
    IdempotencyStatus,
    JsonlIdempotencyStore,
    compute_idempotency_key,
    compute_material_hash,
)


class MutableClock:
    """Mutable test clock."""

    def __init__(self) -> None:
        """Initialize the clock."""
        self.current = datetime(2026, 7, 9, 12, 0, tzinfo=UTC)

    def now_utc(self) -> datetime:
        """Return current UTC timestamp."""
        return self.current

    def now_ptp(self) -> datetime:
        """Return current PTP timestamp."""
        return self.current

    def monotonic(self) -> float:
        """Return deterministic monotonic value."""
        return 10.0


def _material() -> IdempotencyMaterial:
    """Build canonical idempotency material."""
    return IdempotencyMaterial(
        account_id="acct-1",
        strategy_id="strategy-1",
        route=TradingRoute.LIVE,
        promotion_stage="micro_live",
        broker="mt5",
        symbol="EURUSD",
        action=TradingAction.SUBMIT_ORDER,
        type="market",
        side="buy",
        volume="0.10",
        price="1.1000",
        allocation_vector={"child": "1.0"},
    )


def test_idempotency_key_uses_canonical_material_fields() -> None:
    """Canonical material hash is stable and field-bounded."""
    material = _material()
    payload = material.canonical_payload()

    key = compute_idempotency_key(material)
    material_hash = compute_material_hash(payload)

    assert tuple(payload) == IDEMPOTENCY_MATERIAL_FIELDS
    assert len(key) == 64
    assert len(material_hash) == 64
    assert compute_idempotency_key(material) == key


def test_idempotency_material_rejects_blank_required_values() -> None:
    """Required hash material fields fail closed when blank."""
    with pytest.raises(ValueError, match="account_id"):
        IdempotencyMaterial(
            account_id=" ",
            strategy_id="strategy",
            route=TradingRoute.LIVE,
            promotion_stage="micro_live",
            broker="mt5",
            symbol="EURUSD",
            action=TradingAction.SUBMIT_ORDER,
        )


def test_reserve_duplicate_complete_and_restart_survival(tmp_path: Path) -> None:
    """In-progress duplicates are rejected and completed duplicates are cached."""
    clock = MutableClock()
    path = tmp_path / "idempotency.jsonl"
    store = JsonlIdempotencyStore(path=path, clock=clock)
    material = _material()

    first = store.reserve(
        route=TradingRoute.LIVE,
        tenant_id="tenant",
        material=material,
        ttl=timedelta(minutes=5),
    )
    duplicate = store.reserve(
        route=TradingRoute.LIVE,
        tenant_id="tenant",
        material=material,
        ttl=timedelta(minutes=5),
    )
    completed = store.complete(
        route=TradingRoute.LIVE,
        tenant_id="tenant",
        key=first.record.key,
        outcome={"status": "success"},
    )
    restarted = JsonlIdempotencyStore(path=path, clock=clock)
    cached = restarted.reserve(
        route=TradingRoute.LIVE,
        tenant_id="tenant",
        material=material,
        ttl=timedelta(minutes=5),
    )

    assert first.decision is IdempotencyDecision.RESERVED
    assert duplicate.decision is IdempotencyDecision.DUPLICATE_IN_PROGRESS
    assert completed.status is IdempotencyStatus.COMPLETED
    assert cached.decision is IdempotencyDecision.DUPLICATE_COMPLETED
    assert cached.cached_outcome == {"status": "success"}


def test_expired_in_progress_lease_requires_reconciliation(tmp_path: Path) -> None:
    """Expired in-progress leases transition to reconciliation-required."""
    clock = MutableClock()
    store = JsonlIdempotencyStore(path=tmp_path / "idempotency.jsonl", clock=clock)
    material = _material()

    store.reserve(
        route=TradingRoute.LIVE,
        tenant_id="tenant",
        material=material,
        ttl=timedelta(seconds=1),
    )
    clock.current = datetime(2026, 7, 9, 12, 1, tzinfo=UTC)
    duplicate = store.reserve(
        route=TradingRoute.LIVE,
        tenant_id="tenant",
        material=material,
        ttl=timedelta(seconds=1),
    )
    transitioned = store.mark_expired_leases()

    assert duplicate.decision is IdempotencyDecision.RECONCILIATION_REQUIRED
    assert duplicate.record.status is IdempotencyStatus.RECONCILIATION_REQUIRED
    assert transitioned == ()


def test_mark_expired_leases_transitions_records(tmp_path: Path) -> None:
    """Bulk expiry transitions active leases."""
    clock = MutableClock()
    store = JsonlIdempotencyStore(path=tmp_path / "idempotency.jsonl", clock=clock)

    store.reserve(
        route=TradingRoute.LIVE,
        tenant_id="tenant",
        material=_material(),
        ttl=timedelta(seconds=1),
    )
    clock.current = datetime(2026, 7, 9, 12, 1, tzinfo=UTC)
    transitioned = store.mark_expired_leases()

    assert len(transitioned) == 1
    assert transitioned[0].status is IdempotencyStatus.RECONCILIATION_REQUIRED


def test_idempotency_validation_errors(tmp_path: Path) -> None:
    """Invalid store inputs fail closed."""
    store = JsonlIdempotencyStore(
        path=tmp_path / "idempotency.jsonl",
        clock=MutableClock(),
    )

    with pytest.raises(ValueError, match="ttl"):
        store.reserve(
            route=TradingRoute.LIVE,
            tenant_id="tenant",
            material=_material(),
            ttl=timedelta(seconds=0),
        )
    with pytest.raises(ValueError, match="tenant_id"):
        store.reserve(
            route=TradingRoute.LIVE,
            tenant_id=" ",
            material=_material(),
            ttl=timedelta(seconds=1),
        )
    with pytest.raises(KeyError, match="not found"):
        store.complete(
            route=TradingRoute.LIVE,
            tenant_id="tenant",
            key="missing",
            outcome={},
        )


def test_record_validation_rejects_blank_identifiers() -> None:
    """Record validation covers every required identifier branch."""
    valid = {
        "route": TradingRoute.LIVE,
        "tenant_id": "tenant",
        "key": "key",
        "material_hash": "hash",
        "status": IdempotencyStatus.IN_PROGRESS,
        "expires_at": "2026-07-09T12:00:00+00:00",
        "created_at": "2026-07-09T11:59:00+00:00",
    }

    for field_name in ("tenant_id", "key", "material_hash"):
        payload = dict(valid)
        payload[field_name] = " "
        with pytest.raises(ValueError, match=field_name):
            IdempotencyRecord.model_validate(payload)


def test_resolve_nonmatching_records_and_blank_lines(tmp_path: Path) -> None:
    """Resolve handles nonmatching records and ignores blank persisted lines."""
    clock = MutableClock()
    store = JsonlIdempotencyStore(path=tmp_path / "idempotency.jsonl", clock=clock)
    material = _material()
    reserved = store.reserve(
        route=TradingRoute.LIVE,
        tenant_id="tenant",
        material=material,
        ttl=timedelta(minutes=5),
    )
    with (tmp_path / "idempotency.jsonl").open("a", encoding="utf-8") as handle:
        handle.write("\n")

    missing = store.resolve(
        route=TradingRoute.PAPER,
        tenant_id="other",
        key=reserved.record.key,
    )

    assert missing is None


def test_reconciliation_required_and_naive_expiry_paths(tmp_path: Path) -> None:
    """Existing reconciliation records and naive expiry timestamps are handled."""
    clock = MutableClock()
    store = JsonlIdempotencyStore(path=tmp_path / "idempotency.jsonl", clock=clock)
    record = IdempotencyRecord(
        route=TradingRoute.LIVE,
        tenant_id="tenant",
        key="key",
        material_hash="hash",
        status=IdempotencyStatus.RECONCILIATION_REQUIRED,
        expires_at="2026-07-09T11:00:00",
        created_at="2026-07-09T10:00:00+00:00",
    )
    store._upsert(record)

    decision = store.reserve(
        route=TradingRoute.LIVE,
        tenant_id="tenant",
        material=_material().model_copy(
            update={"client_order_id": "other"},
        ),
        ttl=timedelta(minutes=1),
    )
    existing = store._decision_for_existing(record=record, now=clock.now_utc())

    assert decision.decision is IdempotencyDecision.RESERVED
    assert existing.decision is IdempotencyDecision.RECONCILIATION_REQUIRED
