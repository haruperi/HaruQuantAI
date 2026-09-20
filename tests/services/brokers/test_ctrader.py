"""Tests for FEAT-BROKERS-CTRADER (app/services/brokers/ctrader.py)."""

from __future__ import annotations

import asyncio

import pytest
from app.contracts.brokers import (
    BROKER_CTRADER,
    BrokerAuthenticationError,
    BrokerConnectionConfig,
    BrokerConnectionError,
    BrokerOrderIntent,
    ConnectionState,
    OrderSide,
    OrderType,
    UnsupportedCapabilityError,
)
from app.kernel.bootstrapper import Runtime
from app.services.brokers.ctrader import (
    CTraderAdapter,
    CTraderAdapterConfig,
    feature,
)


def test_ctrader_adapter_order_lifecycle() -> None:
    """Verify FR-BROKERS-LIVE_AUTHORIZATION: cTrader connect, submit_order, query, and cancel."""

    async def _test() -> None:
        adapter = CTraderAdapter(CTraderAdapterConfig(mock_mode=True))
        assert adapter.is_connected() is False

        intent = BrokerOrderIntent(
            intent_id="ct-intent-101",
            broker_id=3,
            symbol="GBPUSD",
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            quantity=0.5,
            price=1.2650,
            idempotency_key="ct-idem-101",
        )
        with pytest.raises(BrokerConnectionError):
            await adapter.submit_order(intent)

        conn_config = BrokerConnectionConfig(
            connection_id="conn-ct-01",
            broker_id=3,
            provider_name="ctrader",
            environment="demo",
            endpoint="demo.ctraderapi.com:5035",
        )
        await adapter.connect(conn_config)
        assert adapter.is_connected() is True

        # Submit
        ack = await adapter.submit_order(intent)
        assert ack.status == "FILLED"
        assert ack.intent_id == "ct-intent-101"
        assert "CT-ct-idem-101" in ack.provider_ticket
        assert ack.is_simulated is True

        # Idempotency replay check (FR-BROKERS-ORDER_IDEMPOTENCY)
        ack_replay = await adapter.submit_order(intent)
        assert ack_replay.ack_id == ack.ack_id
        assert ack_replay.provider_ticket == ack.provider_ticket

        # Query
        orders = await adapter.get_open_orders()
        assert len(orders) == 1

        # Cancel
        assert await adapter.cancel_order(ack.provider_ticket) is True
        assert len(await adapter.get_open_orders()) == 0

        # Health
        health = await adapter.get_health()
        assert health.state == ConnectionState.READY

        # Disconnect
        await adapter.disconnect()
        assert adapter.is_connected() is False

    asyncio.run(_test())


def test_ctrader_live_authorization_and_capability_gating() -> None:
    """Verify FR-BROKERS-LIVE_AUTHORIZATION and FR-BROKERS-CAPABILITY_DISCOVERY."""

    async def _test() -> None:
        adapter = CTraderAdapter(CTraderAdapterConfig(mock_mode=True, allow_live=False))
        live_conn = BrokerConnectionConfig(
            connection_id="ct-live-01",
            broker_id=3,
            provider_name="ctrader",
            environment="live",
        )
        with pytest.raises(BrokerAuthenticationError):
            await adapter.connect(live_conn)

        demo_conn = BrokerConnectionConfig(
            connection_id="ct-demo-01",
            broker_id=3,
            provider_name="ctrader",
            environment="demo",
        )
        await adapter.connect(demo_conn)

        unsupported_intent = BrokerOrderIntent(
            intent_id="ct-bad-type",
            broker_id=3,
            symbol="GBPUSD",
            side=OrderSide.BUY,
            order_type="ICEBERG",  # type: ignore[arg-type]
            quantity=1.0,
        )
        with pytest.raises(UnsupportedCapabilityError):
            await adapter.submit_order(unsupported_intent)

    asyncio.run(_test())


def test_ctrader_real_mode_tls_seam(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify real-mode socket connection seam using monkeypatched _open_tls."""
    import app.services.brokers.ctrader as ct_mod

    class _MockSock:
        def close(self) -> None:
            pass

    monkeypatch.setattr(
        ct_mod,
        "_open_tls",
        lambda host, port, timeout_s: (_MockSock(), 8.5),
    )

    async def _test() -> None:
        adapter = CTraderAdapter(CTraderAdapterConfig(mock_mode=False))
        conn_config = BrokerConnectionConfig(
            connection_id="conn-ct-real-01",
            broker_id=3,
            provider_name="ctrader",
            environment="demo",
        )
        await adapter.connect(conn_config)
        assert adapter.is_connected() is True
        health = await adapter.get_health()
        assert health.latency_ms == 8.5

    asyncio.run(_test())


def test_ctrader_runtime_wiring() -> None:
    """Verify runtime composition and publication of BROKER_CTRADER."""

    async def _test() -> None:
        runtime = Runtime((feature,))
        async with runtime:
            svc = runtime.get(BROKER_CTRADER)
            assert svc is not None
            assert svc.provider_name == "ctrader"

    asyncio.run(_test())
