# ruff: noqa: E402, PLR0915, E501
"""Manual live-connectivity checker for the Brokers domain (D-BROKERS).

Purpose:
    Probes external market data feeds and trading adapter network endpoints in
    real mode (mock_mode=False) using Python standard library transports.
    Outputs a structured status table reporting reachability, latency, and
    credential requirements.

Safety & Operational Notes:
    * READ-ONLY: Never submits live orders or modifies remote state.
    * MANUAL ONLY: Excluded from automated test suites (ci_check.py).
    * NO THIRD-PARTY NETWORK LIBS: Uses urllib.request, socket, ssl.

Run with:
    `uv run python scripts/brokers_live_check.py`
"""

from __future__ import annotations

import asyncio
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.contracts.brokers import (
    BrokerAuthenticationError,
    BrokerConnectionConfig,
    BrokerConnectionError,
    UnsupportedCapabilityError,
)
from app.services.brokers.crypto import (
    CryptoFeedConfig,
    CryptoFeedService,
)
from app.services.brokers.ctrader import (
    CTraderAdapter,
    CTraderAdapterConfig,
)
from app.services.brokers.darwinex import (
    DarwinexFeedConfig,
    DarwinexFeedService,
)
from app.services.brokers.dukascopy import (
    DukascopyFeedConfig,
    DukascopyFeedService,
)
from app.services.brokers.equity import (
    SQEquityFeedConfig,
    SQEquityFeedService,
)
from app.services.brokers.futures import (
    SQFuturesFeedConfig,
    SQFuturesFeedService,
)
from app.services.brokers.mt5 import (
    Mt5Adapter,
    Mt5AdapterConfig,
)
from app.services.brokers.yahoo import (
    YahooFeedConfig,
    YahooFeedService,
)


async def probe_provider(
    name: str,
    feed_type: str,
    probe_coro_fn: Any,
) -> dict[str, str]:
    """Execute a single provider probe and return row data."""
    try:
        latency_str, detail = await probe_coro_fn()
        return {
            "provider": name,
            "type": feed_type,
            "status": "PASS",
            "latency": latency_str,
            "detail": detail,
        }
    except BrokerAuthenticationError as exc:
        return {
            "provider": name,
            "type": feed_type,
            "status": "AUTH_REQUIRED",
            "latency": "N/A",
            "detail": str(exc),
        }
    except BrokerConnectionError as exc:
        return {
            "provider": name,
            "type": feed_type,
            "status": "FAIL",
            "latency": "N/A",
            "detail": str(exc),
        }
    except UnsupportedCapabilityError as exc:
        return {
            "provider": name,
            "type": feed_type,
            "status": "UNSUPPORTED",
            "latency": "N/A",
            "detail": str(exc),
        }
    except Exception as exc:
        return {
            "provider": name,
            "type": feed_type,
            "status": "ERROR",
            "latency": "N/A",
            "detail": f"{type(exc).__name__}: {exc}",
        }


async def main() -> None:
    """Run live network probes across all 8 external broker endpoints."""
    print("=" * 88)
    print("HARUQUANTAI BROKERS DOMAIN (D-BROKERS) LIVE CONNECTIVITY CHECKER")
    print("Testing real stdlib network transports (mock_mode=False) — READ-ONLY PROBES")
    print("=" * 88)

    start = datetime(2026, 1, 1, 0, 0, tzinfo=UTC)
    end = datetime(2026, 1, 1, 1, 0, tzinfo=UTC)
    conn = BrokerConnectionConfig("probe", 1, "probe")

    rows: list[dict[str, str]] = []

    # 1. Crypto (Binance public klines)
    async def _probe_crypto() -> tuple[str, str]:
        svc = CryptoFeedService(CryptoFeedConfig(mock_mode=False, timeout_s=5.0))
        await svc.connect(conn)
        chunks = [c async for c in svc.stream_raw_data("BTCUSDT", start, end)]
        h = await svc.get_health()
        await svc.disconnect()
        return (
            f"{h.latency_ms:.1f}ms",
            f"{len(chunks)} chunks, first={len(chunks[0].payload_bytes)}B",
        )

    rows.append(await probe_provider("Crypto (Binance)", "Public Feed", _probe_crypto))

    # 2. Yahoo Finance (v8 chart)
    async def _probe_yahoo() -> tuple[str, str]:
        svc = YahooFeedService(YahooFeedConfig(mock_mode=False, timeout_s=5.0))
        await svc.connect(conn)
        chunks = [c async for c in svc.stream_raw_data("SPY", start, end)]
        h = await svc.get_health()
        await svc.disconnect()
        return (
            f"{h.latency_ms:.1f}ms",
            f"{len(chunks)} chunks, first={len(chunks[0].payload_bytes)}B",
        )

    rows.append(await probe_provider("Yahoo Finance", "Public Feed", _probe_yahoo))

    # 3. Dukascopy (bi5 hourly ticks)
    async def _probe_dukascopy() -> tuple[str, str]:
        svc = DukascopyFeedService(
            DukascopyFeedConfig(mock_mode=False, timeout_s=25.0, max_retries=1)
        )
        await svc.connect(conn)
        dk_start = datetime(2024, 5, 15, 10, 0, tzinfo=UTC)
        dk_end = datetime(2024, 5, 15, 11, 0, tzinfo=UTC)
        chunks = [c async for c in svc.stream_raw_data("EURUSD", dk_start, dk_end)]
        h = await svc.get_health()
        await svc.disconnect()
        return (
            f"{h.latency_ms:.1f}ms",
            f"{len(chunks)} chunks, first={len(chunks[0].payload_bytes)}B",
        )

    rows.append(await probe_provider("Dukascopy", "Public Feed", _probe_dukascopy))

    # 4. SQ Equity (Credentialed feed)
    async def _probe_sq_equity() -> tuple[str, str]:
        svc = SQEquityFeedService(SQEquityFeedConfig(mock_mode=False, timeout_s=5.0))
        await svc.connect(conn)
        chunks = [c async for c in svc.stream_raw_data("AAPL", start, end)]
        h = await svc.get_health()
        await svc.disconnect()
        return f"{h.latency_ms:.1f}ms", f"{len(chunks)} chunks"

    rows.append(
        await probe_provider("SQ Equity", "Credentialed Feed", _probe_sq_equity)
    )

    # 5. SQ Futures (Credentialed feed)
    async def _probe_sq_futures() -> tuple[str, str]:
        svc = SQFuturesFeedService(SQFuturesFeedConfig(mock_mode=False, timeout_s=5.0))
        await svc.connect(conn)
        chunks = [c async for c in svc.stream_raw_data("ES", start, end)]
        h = await svc.get_health()
        await svc.disconnect()
        return f"{h.latency_ms:.1f}ms", f"{len(chunks)} chunks"

    rows.append(
        await probe_provider("SQ Futures", "Credentialed Feed", _probe_sq_futures)
    )

    # 6. Darwinex (Credentialed feed)
    async def _probe_darwinex() -> tuple[str, str]:
        svc = DarwinexFeedService(DarwinexFeedConfig(mock_mode=False, timeout_s=5.0))
        await svc.connect(conn)
        chunks = [c async for c in svc.stream_raw_data("EURUSD", start, end)]
        h = await svc.get_health()
        await svc.disconnect()
        return f"{h.latency_ms:.1f}ms", f"{len(chunks)} chunks"

    rows.append(await probe_provider("Darwinex", "Credentialed Feed", _probe_darwinex))

    # 7. cTrader Open API (TLS Probe)
    async def _probe_ctrader() -> tuple[str, str]:
        adapter = CTraderAdapter(
            CTraderAdapterConfig(mock_mode=False, default_timeout_s=5.0)
        )
        await adapter.connect(
            BrokerConnectionConfig("ct-probe", 6, "ctrader", environment="demo")
        )
        h = await adapter.get_health()
        await adapter.disconnect()
        return (
            f"{h.latency_ms:.1f}ms",
            "TLS handshake verified (demo.ctraderapi.com:5035)",
        )

    rows.append(
        await probe_provider("cTrader Open API", "Trading Adapter", _probe_ctrader)
    )

    # 8. MetaTrader 5 (Local IPC probe)
    async def _probe_mt5() -> tuple[str, str]:
        adapter = Mt5Adapter(Mt5AdapterConfig(mock_mode=False, default_timeout_s=5.0))
        await adapter.connect(
            BrokerConnectionConfig("mt5-probe", 2, "mt5", environment="demo")
        )
        h = await adapter.get_health()
        await adapter.disconnect()
        return f"{h.latency_ms:.1f}ms", "MT5 terminal initialized"

    rows.append(await probe_provider("MetaTrader 5", "Trading Adapter", _probe_mt5))

    # Print summary table
    print(
        f"\n{'Provider':<20} | {'Type':<18} | {'Status':<14} | {'Latency':<10} | {'Details'}"
    )
    print("-" * 88)
    for r in rows:
        print(
            f"{r['provider']:<20} | {r['type']:<18} | {r['status']:<14} | {r['latency']:<10} | {r['detail'][:35]}"
        )
    print("=" * 88)


if __name__ == "__main__":
    asyncio.run(main())
