"""Tests for FEAT-BROKERS-RECONCILIATION (app/services/brokers/reconciliation.py)."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime

import pytest
from app.contracts.brokers import (
    BROKER_RECONCILIATION,
    BrokerExecutionAck,
    BrokerOrderIntent,
    BrokerReconciliationError,
    OrderSide,
    OrderType,
)
from app.kernel.bootstrapper import Runtime
from app.services.brokers.isolation_fencing import (
    BrokerFencingService,
)
from app.services.brokers.isolation_fencing import (
    feature as fencing_feature,
)
from app.services.brokers.reconciliation import (
    BrokerReconciler,
    feature,
)


def test_reconciliation_clean_and_ambiguous() -> None:
    """Verify FR-BROKERS-STATE_RECONCILIATION: reports on matched and ambiguous intents."""

    async def _test() -> None:
        fencing = BrokerFencingService()
        reconciler = BrokerReconciler(fencing)

        # Fenced beforehand
        fencing.trip_fence("mt5", "Disconnect")
        assert fencing.is_fenced("mt5") is True

        intents = [
            BrokerOrderIntent(
                intent_id="intent-1",
                broker_id=2,
                symbol="EURUSD",
                side=OrderSide.BUY,
                order_type=OrderType.MARKET,
                quantity=1.0,
                idempotency_key="idem-1",
            ),
            BrokerOrderIntent(
                intent_id="intent-2",
                broker_id=2,
                symbol="GBPUSD",
                side=OrderSide.SELL,
                order_type=OrderType.LIMIT,
                quantity=0.5,
                price=1.2500,
                idempotency_key="idem-2",
            ),
        ]

        report = await reconciler.reconcile("mt5", intents)
        assert report.matched_count == 2
        assert report.ambiguous_count == 0
        assert report.missing_count == 0
        # Auto-reset fence
        assert fencing.is_fenced("mt5") is False

        # Intent with missing idempotency key
        ambiguous_intents = [
            BrokerOrderIntent(
                intent_id="intent-bad",
                broker_id=2,
                symbol="EURUSD",
                side=OrderSide.BUY,
                order_type=OrderType.MARKET,
                quantity=1.0,
                idempotency_key="",
            )
        ]
        fencing.trip_fence("mt5", "Unacknowledged")
        report2 = await reconciler.reconcile("mt5", ambiguous_intents)
        assert report2.ambiguous_count == 1
        assert len(report2.discrepancies) == 1
        # Remains fenced due to ambiguity
        assert fencing.is_fenced("mt5") is True

    asyncio.run(_test())


def test_reconciliation_provider_orders_matching_and_missing() -> None:
    """Verify state reconciliation against remote provider order snapshots."""

    async def _test() -> None:
        reconciler = BrokerReconciler()
        now = datetime.now(UTC)

        intents = [
            BrokerOrderIntent(
                intent_id="intent-matched",
                broker_id=1,
                symbol="EURUSD",
                side=OrderSide.BUY,
                order_type=OrderType.MARKET,
                quantity=1.0,
                idempotency_key="key-matched",
            ),
            BrokerOrderIntent(
                intent_id="intent-missing",
                broker_id=1,
                symbol="GBPUSD",
                side=OrderSide.SELL,
                order_type=OrderType.LIMIT,
                quantity=2.0,
                price=1.25,
                idempotency_key="key-missing",
            ),
        ]

        provider_orders = [
            BrokerExecutionAck(
                ack_id="ack-1",
                intent_id="intent-matched",
                provider_ticket="MT5-key-matched",
                status="FILLED",
                price=1.1000,
                filled_quantity=1.0,
                timestamp_utc=now,
            )
        ]

        report = await reconciler.reconcile("mt5", intents, provider_orders)
        assert report.matched_count == 1
        assert report.missing_count == 1
        assert report.ambiguous_count == 0
        assert len(report.discrepancies) == 1
        assert "intent-missing" in report.discrepancies[0]

    asyncio.run(_test())


def test_reconciliation_duplicate_intent_rejection() -> None:
    """Verify duplicate intent_id raises BrokerReconciliationError."""

    async def _test() -> None:
        reconciler = BrokerReconciler()
        duplicate_intents = [
            BrokerOrderIntent(
                intent_id="dupe-1",
                broker_id=1,
                symbol="EURUSD",
                side=OrderSide.BUY,
                order_type=OrderType.MARKET,
                quantity=1.0,
                idempotency_key="key-1",
            ),
            BrokerOrderIntent(
                intent_id="dupe-1",
                broker_id=1,
                symbol="EURUSD",
                side=OrderSide.SELL,
                order_type=OrderType.MARKET,
                quantity=1.0,
                idempotency_key="key-2",
            ),
        ]
        with pytest.raises(BrokerReconciliationError):
            await reconciler.reconcile("mt5", duplicate_intents)

    asyncio.run(_test())


def test_reconciliation_runtime_wiring() -> None:
    """Verify runtime composition of reconciliation feature."""

    async def _test() -> None:
        runtime = Runtime((fencing_feature, feature))
        async with runtime:
            rec = runtime.get(BROKER_RECONCILIATION)
            assert rec is not None

    asyncio.run(_test())
