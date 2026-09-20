"""Tests for FEAT-BROKERS-MT5 (app/services/brokers/mt5.py)."""

from __future__ import annotations

import asyncio

import pytest
from app.contracts.brokers import (
    BROKER_MT5,
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
from app.services.brokers.mt5 import (
    CALC_MODE_CFD,
    CALC_MODE_FOREX,
    CALC_MODE_FUTURES,
    Mt5Adapter,
    Mt5AdapterConfig,
    compute_sqx_point_value,
    feature,
)


def test_sqx_point_value_formulas() -> None:
    """Verify FR-BROKERS-CALCULATION_MODE: StrategyQuant X mt5api.py point_value calculation formulas."""
    # Forex mode 0: contract_size * tick_size
    pv_forex = compute_sqx_point_value(
        CALC_MODE_FOREX,
        trade_contract_size=100_000.0,
        trade_tick_size=0.00001,
        trade_tick_value=1.0,
    )
    assert pv_forex == 1.0

    # Futures mode 1: trade_tick_value directly (e.g. E-mini S&P: 12.50)
    pv_futures = compute_sqx_point_value(
        CALC_MODE_FUTURES,
        trade_contract_size=50.0,
        trade_tick_size=0.25,
        trade_tick_value=12.50,
    )
    assert pv_futures == 12.50

    # CFD mode 2: tick_value / tick_size
    pv_cfd = compute_sqx_point_value(
        CALC_MODE_CFD,
        trade_contract_size=1.0,
        trade_tick_size=0.1,
        trade_tick_value=1.0,
    )
    assert pv_cfd == 10.0


def test_mt5_adapter_order_lifecycle() -> None:
    """Verify FR-BROKERS-ORDER_IDEMPOTENCY: connect, submit_order, query, and cancel."""

    async def _test() -> None:
        adapter = Mt5Adapter(Mt5AdapterConfig(mock_mode=True))
        assert adapter.is_connected() is False

        # Submitting while disconnected raises error
        intent = BrokerOrderIntent(
            intent_id="mt5-intent-1",
            broker_id=2,
            symbol="EURUSD",
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            quantity=1.0,
        )
        with pytest.raises(BrokerConnectionError):
            await adapter.submit_order(intent)

        # Connect
        conn_config = BrokerConnectionConfig(
            connection_id="mt5-conn-01",
            broker_id=2,
            provider_name="mt5",
            environment="demo",
        )
        await adapter.connect(conn_config)
        assert adapter.is_connected() is True

        # Submit order
        ack = await adapter.submit_order(intent)
        assert ack.status == "FILLED"
        assert ack.intent_id == "mt5-intent-1"
        assert "MT5-mt5-intent-1" in ack.provider_ticket
        assert ack.is_simulated is True

        # Idempotency replay check (FR-BROKERS-ORDER_IDEMPOTENCY)
        ack_replay = await adapter.submit_order(intent)
        assert ack_replay.ack_id == ack.ack_id
        assert ack_replay.provider_ticket == ack.provider_ticket

        # Query open orders: still exactly 1
        orders = await adapter.get_open_orders()
        assert len(orders) == 1
        assert orders[0].provider_ticket == ack.provider_ticket

        # Check health
        health = await adapter.get_health()
        assert health.state == ConnectionState.READY
        assert health.latency_ms > 0

        # Cancel order
        cancelled = await adapter.cancel_order(ack.provider_ticket)
        assert cancelled is True
        assert len(await adapter.get_open_orders()) == 0

        # Disconnect
        await adapter.disconnect()
        assert adapter.is_connected() is False

    asyncio.run(_test())


def test_mt5_live_authorization_and_capability_gating() -> None:
    """Verify FR-BROKERS-LIVE_AUTHORIZATION and FR-BROKERS-CAPABILITY_DISCOVERY."""

    async def _test() -> None:
        adapter = Mt5Adapter(Mt5AdapterConfig(mock_mode=True, allow_live=False))
        live_conn = BrokerConnectionConfig(
            connection_id="mt5-live-01",
            broker_id=2,
            provider_name="mt5",
            environment="live",
        )
        # Live environment connection rejected when allow_live=False
        with pytest.raises(BrokerAuthenticationError):
            await adapter.connect(live_conn)

        demo_conn = BrokerConnectionConfig(
            connection_id="mt5-demo-01",
            broker_id=2,
            provider_name="mt5",
            environment="demo",
        )
        await adapter.connect(demo_conn)

        # Unsupported order type rejected
        unsupported_intent = BrokerOrderIntent(
            intent_id="mt5-bad-type",
            broker_id=2,
            symbol="EURUSD",
            side=OrderSide.BUY,
            order_type="TRAILING_STOP",  # type: ignore[arg-type]
            quantity=1.0,
        )
        with pytest.raises(UnsupportedCapabilityError):
            await adapter.submit_order(unsupported_intent)

    asyncio.run(_test())


def test_mt5_runtime_wiring() -> None:
    """Verify runtime composition and publication of BROKER_MT5."""

    async def _test() -> None:
        runtime = Runtime((feature,))
        async with runtime:
            svc = runtime.get(BROKER_MT5)
            assert svc is not None
            assert svc.provider_name == "mt5"

    asyncio.run(_test())
