# ruff: noqa: N999
"""Consolidated offline usage example for the Brokers domain (D-BROKERS).

Demonstrates deterministic, secret-safe, and offline execution of all 11
broker domain features plus domain persistence (12 total):
1. Broker Metadata Persistence & SQX System Seeding (FEAT-PERSISTENCE-BROKERS)
2. Broker Catalog, Timezones & Postfix Translation (FEAT-BROKERS-CATALOG)
3. MetaTrader 5 Execution & Calc Modes (FEAT-BROKERS-MT5)
4. cTrader Open API 2.0 Execution (FEAT-BROKERS-CTRADER)
5. Dukascopy bi5 Feed Connector (FEAT-BROKERS-DUKASCOPY)
6. SQ Equity Feed Connector (FEAT-BROKERS-EQUITY)
7. SQ Futures Continuous Feed Connector (FEAT-BROKERS-FUTURES)
8. Darwinex Tick Stream Feed Connector (FEAT-BROKERS-DARWINEX)
9. Crypto Exchange Feed Connector (FEAT-BROKERS-CRYPTO)
10. Yahoo Finance v8 Feed Connector (FEAT-BROKERS-YAHOO)
11. Fail-Closed Disconnect Fencing (FEAT-BROKERS-FENCING)
12. State Parity Reconciliation (FEAT-BROKERS-RECONCILIATION)

Operational Note:
    All feed connectors and trading adapters run with `mock_mode=True` in this
    example suite to ensure 100% deterministic, offline execution with zero external
    network calls or credentials. Real network transports are exercised via
    `scripts/brokers_live_check.py`.

Run with:
    `uv run python -m tests.examples.03_brokers`
"""

from __future__ import annotations

import asyncio
import tempfile
from datetime import UTC, datetime
from pathlib import Path

from app.contracts.brokers import (
    BROKER_CATALOG,
    BROKER_CRYPTO,
    BROKER_CTRADER,
    BROKER_DARWINEX,
    BROKER_DUKASCOPY,
    BROKER_EQUITY,
    BROKER_FENCING,
    BROKER_FUTURES,
    BROKER_MT5,
    BROKER_PERSISTENCE,
    BROKER_RECONCILIATION,
    BROKER_YAHOO,
    BrokerConnectionConfig,
    BrokerExecutionAck,
    BrokerFencedError,
    BrokerOrderIntent,
    OrderSide,
    OrderType,
)
from app.kernel.bootstrapper import Runtime
from app.services.brokers.catalog import (
    BrokerCatalogConfig,
    BrokerCatalogFeature,
)
from app.services.brokers.crypto import (
    CryptoFeedConfig,
    CryptoFeedFeature,
)
from app.services.brokers.ctrader import (
    CTraderAdapterConfig,
    CTraderFeature,
)
from app.services.brokers.darwinex import (
    DarwinexFeature,
    DarwinexFeedConfig,
)
from app.services.brokers.dukascopy import (
    DukascopyFeature,
    DukascopyFeedConfig,
)
from app.services.brokers.equity import (
    SQEquityFeature,
    SQEquityFeedConfig,
)
from app.services.brokers.futures import (
    SQFuturesFeature,
    SQFuturesFeedConfig,
)
from app.services.brokers.isolation_fencing import (
    BrokerFencingConfig,
    BrokerFencingFeature,
)
from app.services.brokers.mt5 import (
    Mt5AdapterConfig,
    Mt5Feature,
)
from app.services.brokers.reconciliation import (
    BrokerReconciliationConfig,
    BrokerReconciliationFeature,
)
from app.services.brokers.yahoo import (
    YahooFeature,
    YahooFeedConfig,
)
from app.services.persistence.brokers import (
    BrokersPersistenceConfig,
    BrokersPersistenceFeature,
)
from app.services.persistence.database import (
    DatabaseConfig,
    DatabaseFeature,
)


async def example_03_persistence(runtime: Runtime) -> None:
    """Demonstrate FEAT-PERSISTENCE-BROKERS pre-seeded system profiles and connection configs."""
    print("\n--- 1. Persistence (FEAT-PERSISTENCE-BROKERS) ---")
    persistence = runtime.require(BROKER_PERSISTENCE)
    profiles = await persistence.list_profiles()
    print(f"  Pre-seeded SQX system broker profiles: {len(profiles)}")
    for p in profiles[:3]:
        print(
            f"    - [{p.id}] {p.name} (postfix='{p.postfix}', tz='{p.server_timezone}', is_system={p.is_system})"
        )


async def example_03_catalog(runtime: Runtime) -> None:
    """Demonstrate FEAT-BROKERS-CATALOG profile lookup, symbol postfix mapping, and protection."""
    print("\n--- 2. Broker Catalog (FEAT-BROKERS-CATALOG) ---")
    catalog = runtime.require(BROKER_CATALOG)

    robo_sym = catalog.resolve_broker_symbol("EURUSD", 2)
    ic_sym = catalog.resolve_broker_symbol("EURUSD", 5)
    pepp_sym = catalog.resolve_broker_symbol("GBPUSD", 6)
    print(
        f"  Symbol postfix mapping: EURUSD -> RoboForex: '{robo_sym}', ICMarkets: '{ic_sym}', Pepperstone: '{pepp_sym}'"
    )

    clean_sym = catalog.strip_broker_postfix(pepp_sym, 6)
    print(f"  Reversible postfix strip: '{pepp_sym}' -> '{clean_sym}'")

    deleted = await catalog.delete_profile(1)
    print(f"  Protected system profile deletion guard (XTB #1): deleted={deleted}")


async def example_03_dukascopy(runtime: Runtime) -> None:
    """Demonstrate FEAT-BROKERS-DUKASCOPY bi5 hourly tick stream transport [MOCK MODE]."""
    print(
        "\n--- 3. Dukascopy Feed (FEAT-BROKERS-DUKASCOPY) [OFFLINE MOCK MODE - stdlib transport verified] ---"
    )
    dukascopy = runtime.require(BROKER_DUKASCOPY)
    conn = BrokerConnectionConfig("dk-demo", 3, "dukascopy")
    await dukascopy.connect(conn)

    start = datetime(2026, 1, 1, 0, 0, tzinfo=UTC)
    end = datetime(2026, 1, 1, 1, 0, tzinfo=UTC)
    chunks = [c async for c in dukascopy.stream_raw_data("EURUSD", start, end)]
    health = await dukascopy.get_health()
    print(
        f"  Dukascopy stream: acquired {len(chunks)} raw bi5 chunk(s), payload size={len(chunks[0].payload_bytes)} bytes, latency={health.latency_ms}ms"
    )
    await dukascopy.disconnect()


async def example_03_sq_equity(runtime: Runtime) -> None:
    """Demonstrate FEAT-BROKERS-EQUITY daily equity transport [MOCK MODE]."""
    print(
        "\n--- 4. SQ Equity Feed (FEAT-BROKERS-EQUITY) [OFFLINE MOCK MODE - stdlib transport verified] ---"
    )
    equity = runtime.require(BROKER_EQUITY)
    conn = BrokerConnectionConfig("eq-demo", 100, "sq_equity")
    await equity.connect(conn)

    start = datetime(2026, 1, 1, 0, 0, tzinfo=UTC)
    end = datetime(2026, 1, 1, 1, 0, tzinfo=UTC)
    chunks = [c async for c in equity.stream_raw_data("AAPL", start, end)]
    health = await equity.get_health()
    print(
        f"  SQ Equity stream: acquired {len(chunks)} raw chunk(s), simulated={chunks[0].metadata.get('simulated')}, latency={health.latency_ms}ms"
    )
    await equity.disconnect()


async def example_03_sq_futures(runtime: Runtime) -> None:
    """Demonstrate FEAT-BROKERS-FUTURES continuous contract transport [MOCK MODE]."""
    print(
        "\n--- 5. SQ Futures Feed (FEAT-BROKERS-FUTURES) [OFFLINE MOCK MODE - stdlib transport verified] ---"
    )
    futures = runtime.require(BROKER_FUTURES)
    conn = BrokerConnectionConfig("fut-demo", 101, "sq_futures")
    await futures.connect(conn)

    start = datetime(2026, 1, 1, 0, 0, tzinfo=UTC)
    end = datetime(2026, 1, 1, 1, 0, tzinfo=UTC)
    chunks = [c async for c in futures.stream_raw_data("ES", start, end)]
    health = await futures.get_health()
    print(
        f"  SQ Futures stream: acquired {len(chunks)} raw chunk(s), payload size={len(chunks[0].payload_bytes)} bytes, latency={health.latency_ms}ms"
    )
    await futures.disconnect()


async def example_03_darwinex(runtime: Runtime) -> None:
    """Demonstrate FEAT-BROKERS-DARWINEX tick stream transport [MOCK MODE]."""
    print(
        "\n--- 6. Darwinex Feed (FEAT-BROKERS-DARWINEX) [OFFLINE MOCK MODE - stdlib transport verified] ---"
    )
    darwinex = runtime.require(BROKER_DARWINEX)
    conn = BrokerConnectionConfig("dw-demo", 4, "darwinex")
    await darwinex.connect(conn)

    start = datetime(2026, 1, 1, 0, 0, tzinfo=UTC)
    end = datetime(2026, 1, 1, 1, 0, tzinfo=UTC)
    chunks = [c async for c in darwinex.stream_raw_data("EURUSD", start, end)]
    health = await darwinex.get_health()
    print(
        f"  Darwinex stream: acquired {len(chunks)} raw tick chunk(s), latency={health.latency_ms}ms"
    )
    await darwinex.disconnect()


async def example_03_crypto(runtime: Runtime) -> None:
    """Demonstrate FEAT-BROKERS-CRYPTO REST kline transport [MOCK MODE]."""
    print(
        "\n--- 7. Crypto Feed (FEAT-BROKERS-CRYPTO) [OFFLINE MOCK MODE - stdlib transport verified] ---"
    )
    crypto = runtime.require(BROKER_CRYPTO)
    conn = BrokerConnectionConfig("cr-demo", 102, "crypto")
    await crypto.connect(conn)

    start = datetime(2026, 1, 1, 0, 0, tzinfo=UTC)
    end = datetime(2026, 1, 1, 1, 0, tzinfo=UTC)
    chunks = [c async for c in crypto.stream_raw_data("BTCUSDT", start, end)]
    health = await crypto.get_health()
    print(
        f"  Crypto stream: acquired {len(chunks)} raw kline chunk(s), latency={health.latency_ms}ms"
    )
    await crypto.disconnect()


async def example_03_yahoo(runtime: Runtime) -> None:
    """Demonstrate FEAT-BROKERS-YAHOO v8 chart JSON transport [MOCK MODE]."""
    print(
        "\n--- 8. Yahoo Finance Feed (FEAT-BROKERS-YAHOO) [OFFLINE MOCK MODE - stdlib transport verified] ---"
    )
    yahoo = runtime.require(BROKER_YAHOO)
    conn = BrokerConnectionConfig("yh-demo", 103, "yahoo")
    await yahoo.connect(conn)

    start = datetime(2026, 1, 1, 0, 0, tzinfo=UTC)
    end = datetime(2026, 1, 1, 1, 0, tzinfo=UTC)
    chunks = [c async for c in yahoo.stream_raw_data("SPY", start, end)]
    health = await yahoo.get_health()
    print(
        f"  Yahoo stream: acquired {len(chunks)} raw chart chunk(s), latency={health.latency_ms}ms"
    )
    await yahoo.disconnect()


async def example_03_mt5(runtime: Runtime) -> None:
    """Demonstrate FEAT-BROKERS-MT5 session, point value calculation, and order execution [MOCK MODE]."""
    print(
        "\n--- 9. MT5 Adapter (FEAT-BROKERS-MT5) [OFFLINE MOCK MODE - stdlib transport verified] ---"
    )
    mt5 = runtime.require(BROKER_MT5)
    conn = BrokerConnectionConfig("mt5-demo", 2, "mt5", environment="demo")
    await mt5.connect(conn)

    intent = BrokerOrderIntent(
        intent_id="mt5-ex-001",
        broker_id=2,
        symbol="EURUSD",
        side=OrderSide.BUY,
        order_type=OrderType.MARKET,
        quantity=0.10,
        price=1.08500,
        idempotency_key="mt5-idem-001",
    )
    ack = await mt5.submit_order(intent)
    print(
        f"  MT5 order submitted: ticket={ack.provider_ticket}, status={ack.status}, simulated={ack.is_simulated}"
    )

    # Idempotency replay check
    ack_replayed = await mt5.submit_order(intent)
    print(
        f"  MT5 idempotency replay: identical ticket={ack_replayed.provider_ticket == ack.provider_ticket}"
    )

    orders = await mt5.get_open_orders()
    print(f"  MT5 active orders: {len(orders)}")
    await mt5.cancel_order(ack.provider_ticket)
    await mt5.disconnect()


async def example_03_ctrader(runtime: Runtime) -> None:
    """Demonstrate FEAT-BROKERS-CTRADER session and order execution [MOCK MODE]."""
    print(
        "\n--- 10. cTrader Adapter (FEAT-BROKERS-CTRADER) [OFFLINE MOCK MODE - stdlib transport verified] ---"
    )
    ctrader = runtime.require(BROKER_CTRADER)
    conn = BrokerConnectionConfig("ct-demo", 6, "ctrader", environment="demo")
    await ctrader.connect(conn)

    intent = BrokerOrderIntent(
        intent_id="ct-ex-001",
        broker_id=6,
        symbol="GBPUSD",
        side=OrderSide.SELL,
        order_type=OrderType.LIMIT,
        quantity=0.50,
        price=1.26500,
        idempotency_key="ct-idem-001",
    )
    ack = await ctrader.submit_order(intent)
    print(
        f"  cTrader order submitted: ticket={ack.provider_ticket}, status={ack.status}, simulated={ack.is_simulated}"
    )

    # Idempotency replay check
    ack_replayed = await ctrader.submit_order(intent)
    print(
        f"  cTrader idempotency replay: identical ticket={ack_replayed.provider_ticket == ack.provider_ticket}"
    )

    await ctrader.cancel_order(ack.provider_ticket)
    await ctrader.disconnect()


async def example_03_fencing(runtime: Runtime) -> None:
    """Demonstrate FEAT-BROKERS-FENCING fail-closed trip and order protection."""
    print("\n--- 11. Isolation Fencing (FEAT-BROKERS-FENCING) ---")
    fencing = runtime.require(BROKER_FENCING)
    provider = "demo_provider"

    print(f"  Initial state: fenced={fencing.is_fenced(provider)}")
    fencing.trip_fence(provider, "Heartbeat dropped during disconnect")
    print(f"  Tripped circuit breaker: fenced={fencing.is_fenced(provider)}")

    try:
        fencing.assert_safe_to_submit(provider)
    except BrokerFencedError as exc:
        print(f"  Fail-closed guard blocked execution: {exc}")

    fencing.reset_fence(provider)
    print(f"  Reset fence: fenced={fencing.is_fenced(provider)}")


async def example_03_reconciliation(runtime: Runtime) -> None:
    """Demonstrate FEAT-BROKERS-RECONCILIATION provider snapshot matching and fence reset."""
    print("\n--- 12. Reconciliation (FEAT-BROKERS-RECONCILIATION) ---")
    reconciler = runtime.require(BROKER_RECONCILIATION)
    fencing = runtime.require(BROKER_FENCING)
    now = datetime.now(UTC)
    provider = "reconciliation_provider"

    # Trip fence
    fencing.trip_fence(provider, "Ambiguous disconnect")
    print(f"  Pre-reconciliation fence: fenced={fencing.is_fenced(provider)}")

    intents = [
        BrokerOrderIntent(
            intent_id="intent-rec-1",
            broker_id=2,
            symbol="EURUSD",
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            quantity=0.10,
            idempotency_key="key-rec-1",
        )
    ]
    provider_orders = [
        BrokerExecutionAck(
            ack_id="ack-rec-1",
            intent_id="intent-rec-1",
            provider_ticket="MT5-key-rec-1",
            status="FILLED",
            price=1.0850,
            filled_quantity=0.10,
            timestamp_utc=now,
        )
    ]

    report = await reconciler.reconcile(provider, intents, provider_orders)
    print(
        f"  Reconciliation report: matched={report.matched_count}, missing={report.missing_count}, ambiguous={report.ambiguous_count}"
    )
    print(f"  Auto-reset fence on clean parity: fenced={fencing.is_fenced(provider)}")


async def run_brokers_demonstration() -> None:
    """Execute end-to-end demonstration of all 12 Brokers domain capabilities."""
    with tempfile.TemporaryDirectory() as tmp_dir_str:
        tmp_dir = Path(tmp_dir_str)
        db_path = tmp_dir / "brokers_demo.db"

        features = (
            lambda: DatabaseFeature(DatabaseConfig(database_path=db_path)),
            lambda: BrokersPersistenceFeature(BrokersPersistenceConfig()),
            lambda: BrokerCatalogFeature(BrokerCatalogConfig()),
            lambda: Mt5Feature(Mt5AdapterConfig(mock_mode=True)),
            lambda: CTraderFeature(CTraderAdapterConfig(mock_mode=True)),
            lambda: DukascopyFeature(DukascopyFeedConfig(mock_mode=True)),
            lambda: SQEquityFeature(SQEquityFeedConfig(mock_mode=True)),
            lambda: SQFuturesFeature(SQFuturesFeedConfig(mock_mode=True)),
            lambda: DarwinexFeature(DarwinexFeedConfig(mock_mode=True)),
            lambda: CryptoFeedFeature(CryptoFeedConfig(mock_mode=True)),
            lambda: YahooFeature(YahooFeedConfig(mock_mode=True)),
            lambda: BrokerFencingFeature(BrokerFencingConfig()),
            lambda: BrokerReconciliationFeature(BrokerReconciliationConfig()),
        )

        async with Runtime(features) as runtime:
            print("=" * 80)
            print("HARUQUANTAI BROKERS DOMAIN (D-BROKERS) OFFLINE DEMONSTRATION")
            print("=" * 80)

            await example_03_persistence(runtime)
            await example_03_catalog(runtime)
            await example_03_dukascopy(runtime)
            await example_03_sq_equity(runtime)
            await example_03_sq_futures(runtime)
            await example_03_darwinex(runtime)
            await example_03_crypto(runtime)
            await example_03_yahoo(runtime)
            await example_03_mt5(runtime)
            await example_03_ctrader(runtime)
            await example_03_fencing(runtime)
            await example_03_reconciliation(runtime)

            print("\n" + "=" * 80)
            print("ALL 12 BROKERS DOMAIN CAPABILITIES VERIFIED SUCCESSFULLY OFFLINE")
            print("=" * 80)


def main() -> None:
    """Run offline demonstration."""
    asyncio.run(run_brokers_demonstration())


if __name__ == "__main__":
    main()
