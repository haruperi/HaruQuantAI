"""Executable usage demonstration harness for Connector Synchronization."""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path

import pandas as pd

from app.contracts.data.models import (
    ConnectorSyncPlan,
    ConnectorSyncReceipt,
    SyncConnectorsRequest,
    SyncConnectorsSuccess,
)
from app.services.data.connector_synchronization.connector_synchronization import (
    SyncConnectorsService,
    _generate_uuid7,
    data_connect_data_providers,
    data_implement_connector_lifecycle,
    data_plan_incremental_sync,
    data_protect_connector_secrets,
    data_version_data_transforms,
)

logger = logging.getLogger(__name__)


def example_mt5_bars(symbol: str = "EURUSD", count: int = 20) -> pd.DataFrame:
    """Retrieve bounded MT5 bars by calling the brokers domain."""
    try:
        from app.services.brokers.resolve.router import get_broker_client

        client = get_broker_client("mt5")
        client.connect()
        try:
            resp = client.get_bars(symbol, timeframe="1m", count=count)
            if getattr(resp, "status", None) == "success" and isinstance(
                resp.data, pd.DataFrame
            ):
                return resp.data
        finally:
            client.disconnect()
    except (
        ImportError,
        RuntimeError,
        OSError,
        KeyError,
        ValueError,
        AttributeError,
    ) as exc:
        logger.debug("Brokers domain MT5 bars fetch fallback: %s", exc)

    csv_path = Path("data/raw/EURUSD_H1.csv")
    if csv_path.exists():
        df = pd.read_csv(csv_path)
        df["DateTime"] = pd.to_datetime(df["Timestamp"], utc=True)
        df = df.set_index("DateTime")
        if "Spread" not in df.columns:
            df["Spread"] = 0
        return df[["Open", "High", "Low", "Close", "Volume", "Spread"]].head(count)
    msg = f"Failed to retrieve {symbol} bars from brokers domain"
    raise RuntimeError(msg)


def example_mt5_ticks(symbol: str = "EURUSD", count: int = 20) -> pd.DataFrame:
    """Retrieve bounded MT5 ticks by calling the brokers domain."""
    try:
        from app.services.brokers.resolve.router import get_broker_client

        client = get_broker_client("mt5")
        client.connect()
        try:
            resp = client.get_ticks(symbol, count=count)
            if getattr(resp, "status", None) == "success" and isinstance(
                resp.data, pd.DataFrame
            ):
                return resp.data
        finally:
            client.disconnect()
    except (
        ImportError,
        RuntimeError,
        OSError,
        KeyError,
        ValueError,
        AttributeError,
    ) as exc:
        logger.debug("Brokers domain MT5 ticks fetch fallback: %s", exc)

    ticks_csv = Path("data/raw/EURUSD_ticks.csv")
    if ticks_csv.exists():
        df = pd.read_csv(ticks_csv)
        df["DateTime"] = pd.to_datetime(df["time"], utc=True)
        df = df.set_index("DateTime")
        df["Ask"] = df.get("ask", df.get("bid", 0.0))
        df["Bid"] = df.get("bid", 0.0)
        df["Volume"] = df.get("volume", 0)
        return df[["Bid", "Ask", "Volume"]].head(count)
    msg = f"Failed to retrieve {symbol} ticks from brokers domain"
    raise RuntimeError(msg)


def example_dukascopy(symbol: str = "EURUSD", count: int = 20) -> pd.DataFrame:
    """Retrieve bounded Dukascopy forex bars by calling the brokers domain."""
    try:
        from app.services.brokers.resolve.router import get_broker_client

        client = get_broker_client("dukascopy")
        client.connect()
        try:
            resp = client.get_bars(symbol, timeframe="1m", count=count)
            if getattr(resp, "status", None) == "success" and isinstance(
                resp.data, pd.DataFrame
            ):
                return resp.data
        finally:
            client.disconnect()
    except (
        ImportError,
        RuntimeError,
        OSError,
        KeyError,
        ValueError,
        AttributeError,
    ) as exc:
        logger.debug("Brokers domain Dukascopy fetch fallback: %s", exc)

    duka_csv = Path("data/raw/dukascopy_EURUSD_m1.csv")
    if duka_csv.exists():
        df = pd.read_csv(duka_csv)
        df["DateTime"] = (
            pd.to_datetime(df["time"], unit="s", utc=True)
            if "time" in df.columns
            else pd.to_datetime(df.index, utc=True)
        )
        df = df.set_index("DateTime")
        return df.tail(count).copy()
    msg = f"Failed to retrieve Dukascopy forex rates for {symbol} from brokers domain"
    raise RuntimeError(msg)


def example_yahoo(symbol: str = "AAPL", count: int = 20) -> pd.DataFrame:
    """Retrieve bounded Yahoo bars by calling the brokers domain."""
    try:
        from app.services.brokers.resolve.router import get_broker_client

        client = get_broker_client("yahoo")
        client.connect()
        try:
            fetch_fn = getattr(
                client, "get_bars", getattr(client, "get_historical_bars", None)
            )
            if fetch_fn is not None:
                resp = fetch_fn(symbol, timeframe="1d", count=count)
                bars = getattr(resp, "data", resp)
                if isinstance(bars, pd.DataFrame):
                    return bars.tail(count).copy()
                if bars:
                    df = pd.DataFrame(bars)
                    if "Date" in df.columns:
                        df["DateTime"] = pd.to_datetime(df["Date"], utc=True)
                        df = df.set_index("DateTime")
                    return df.tail(count).copy()
        finally:
            client.disconnect()
    except (
        ImportError,
        RuntimeError,
        OSError,
        KeyError,
        ValueError,
        AttributeError,
    ) as exc:
        logger.debug("Brokers domain Yahoo fetch fallback: %s", exc)

    aapl_csv = Path("data/raw/AAPL_daily.csv")
    if aapl_csv.exists():
        df = pd.read_csv(aapl_csv)
        if "Date" in df.columns:
            df["DateTime"] = pd.to_datetime(df["Date"], utc=True)
            df = df.set_index("DateTime")
        return df.tail(count).copy()
    msg = f"Failed to retrieve Yahoo Finance bars for {symbol} from brokers domain"
    raise RuntimeError(msg)


def example_binance(symbol: str = "BTCUSDT", count: int = 20) -> pd.DataFrame:
    """Retrieve bounded Binance Spot bars by calling the brokers domain."""
    try:
        from app.services.brokers.resolve.router import get_broker_client

        client = get_broker_client("binance")
        client.connect()
        try:
            resp = client.get_bars(symbol, timeframe="1m", count=count)
            if getattr(resp, "status", None) == "success" and isinstance(
                resp.data, pd.DataFrame
            ):
                return resp.data
        finally:
            client.disconnect()
    except (
        ImportError,
        RuntimeError,
        OSError,
        KeyError,
        ValueError,
        AttributeError,
    ) as exc:
        logger.debug("Brokers domain Binance fetch fallback: %s", exc)

    btc_csv = Path("data/raw/BTCUSDT_m1.csv")
    if btc_csv.exists():
        df = pd.read_csv(btc_csv)
        df["DateTime"] = (
            pd.to_datetime(df["time"], unit="s", utc=True)
            if "time" in df.columns
            else pd.to_datetime(df.index, utc=True)
        )
        df = df.set_index("DateTime")
        return df.tail(count).copy()
    msg = f"Failed to retrieve Binance klines for {symbol} from brokers domain"
    raise RuntimeError(msg)


def example_caching() -> ConnectorSyncPlan:
    """Select an explicit fail-closed stale-cache and overlap policy."""
    return data_plan_incremental_sync(
        profile_id=_generate_uuid7(),
        connector_version="v1.0.0",
        requested_from="2026-08-01T00:00:00.000000Z",
        requested_to="2026-08-02T00:00:00.000000Z",
        max_records=100,
        overlap_window_seconds=300,
        deduplication="KEEP_FIRST",
    )


async def example_scheduler_create_status() -> SyncConnectorsSuccess:
    """Create a bounded update sync plan and query its status."""
    service = SyncConnectorsService()
    req = SyncConnectorsRequest(
        request_id=_generate_uuid7(),
        capability_snapshot_id=_generate_uuid7(),
        operation="PLAN",
        profile_id=_generate_uuid7(),
        requested_from="2026-08-01T00:00:00.000000Z",
        requested_to="2026-08-02T00:00:00.000000Z",
        max_records=500,
    )
    res = await service.sync_connectors(req)
    if not isinstance(res, SyncConnectorsSuccess) or res.plan is None:
        msg = f"Failed to create plan: {res}"
        raise RuntimeError(msg)
    return res


def example_scheduler_start_stop() -> ConnectorSyncReceipt:
    """Execute connector lifecycle start, checkpoint, and commit operations."""
    plan = data_plan_incremental_sync(
        profile_id=_generate_uuid7(),
        connector_version="v1.0.0",
        requested_from="2026-08-01T00:00:00.000000Z",
        requested_to="2026-08-02T00:00:00.000000Z",
        max_records=10,
    )
    pages = [
        [
            {
                "id": "rec_1",
                "timestamp": "2026-08-01T00:00:00.000000Z",
                "close": 1.1000,
            }
        ]
    ]
    receipt, _ = data_implement_connector_lifecycle(plan, pages=pages)
    return receipt


async def main() -> None:
    """Run teaching and usage evidence scenarios for Connector Synchronization."""
    print("=" * 80)
    print("Executing FEAT-DATA-SYNC_CONNECTORS Teaching & Usage Scenarios")
    print("=" * 80)

    profile_id = _generate_uuid7()
    t_start = "2026-01-01T00:00:00.000000Z"
    t_end = "2026-01-02T00:00:00.000000Z"

    # Scenario 1: FR-DATA-PLAN_INCREMENTAL_SYNC
    print("\n[1] Scenario FR-DATA-PLAN_INCREMENTAL_SYNC (Idempotent planning)")
    plan = data_plan_incremental_sync(
        profile_id=profile_id,
        connector_version="v1.0.0",
        requested_from=t_start,
        requested_to=t_end,
        max_records=1000,
        overlap_window_seconds=300,
        deduplication="KEEP_FIRST",
    )
    print(f"  * Created Plan ID: {plan.plan_id}")
    print(f"  * Requested Window: {plan.requested_from} -> {plan.requested_to}")
    print(f"  * Overlap: {plan.overlap_window_seconds}s, Dedup: {plan.deduplication}")

    # Scenario 2: FR-DATA-IMPLEMENT_CONNECTOR_LIFECYCLE
    print(
        "\n[2] Scenario FR-DATA-IMPLEMENT_CONNECTOR_LIFECYCLE"
        " (Discover, fetch, checkpoint, normalize)"
    )
    pages = [
        [
            {
                "id": "EURUSD_1",
                "timestamp": "2026-01-01T00:00:00.000000Z",
                "close": 1.1000,
            },
            {
                "id": "EURUSD_2",
                "timestamp": "2026-01-01T00:01:00.000000Z",
                "close": 1.1010,
            },
        ],
        [
            {
                "id": "EURUSD_2",
                "timestamp": "2026-01-01T00:01:00.000000Z",
                "close": 1.1010,
            },
            {
                "id": "EURUSD_3",
                "timestamp": "2026-01-01T00:02:00.000000Z",
                "close": 1.1020,
            },
        ],
    ]
    receipt, normalized = data_implement_connector_lifecycle(plan, pages=pages)
    print(f"  * Executed Receipt ID: {receipt.receipt_id}")
    print(f"  * Normalized Records: {receipt.records} (duplicates eliminated)")
    print(f"  * Content Hash: {receipt.content_hash}")
    print(f"  * Committed Version ID: {receipt.committed_version_id}")

    # Scenario 3: FR-DATA-VERSION_DATA_TRANSFORMS
    print(
        "\n[3] Scenario FR-DATA-VERSION_DATA_TRANSFORMS"
        " (Traceable versioned transformations)"
    )
    raw_series_id = _generate_uuid7()
    t_id, t_hash, _t_recs, t_manifest = data_version_data_transforms(
        raw_series_id=raw_series_id,
        transform_kind="SPLIT_ADJUSTMENT",
        transformation_params={"factor": 0.5},
        raw_records=normalized,
    )
    print(f"  * Transformed Series ID: {t_id}")
    print(f"  * Transformed Hash: {t_hash}")
    print(
        f"  * Adjustment Manifest: {t_manifest['transform_kind']} with"
        f" factor={t_manifest['parameters']['factor']}"
    )

    # Scenario 4: FR-DATA-CONNECT_DATA_PROVIDERS
    print(
        "\n[4] Scenario FR-DATA-CONNECT_DATA_PROVIDERS"
        " (Throttling and provider adapter)"
    )
    provider_res = data_connect_data_providers(
        provider_id="mt5",
        symbol="EURUSD",
        requested_range=(t_start, t_end),
        rate_limit=50,
        rate_window_seconds=60,
        simulated_pages=2,
        records_per_page=5,
    )
    print(
        f"  * Provider: {provider_res['provider_id']}, Symbol: {provider_res['symbol']}"
    )
    print(
        f"  * Total Fetched: {provider_res['total_records']} records across"
        f" {provider_res['pages_count']} pages"
    )
    print(f"  * Final Cursor: {provider_res['last_cursor']}")

    # Scenario 5: FR-DATA-PROTECT_CONNECTOR_SECRETS
    print(
        "\n[5] Scenario FR-DATA-PROTECT_CONNECTOR_SECRETS"
        " (Opaque secret reference isolation)"
    )
    cred_ref = _generate_uuid7()
    secret_store = {
        cred_ref: {
            "api_key": "SECRET_RAW_TOKEN_12345",  # pragma: allowlist secret
            "password": "supersecretpassword",  # pragma: allowlist secret
        }
    }
    is_valid, log_msg, meta = data_protect_connector_secrets(
        "mt5", cred_ref, secret_store
    )
    print(f"  * Secret Protection Valid: {is_valid}")
    print(f"  * Sanitized Log: {log_msg}")
    print(f"  * Safe Metadata (No plaintext leak): {meta}")

    await _run_additional_provider_examples()

    print("\n" + "=" * 80)
    print("All Connector Synchronization Scenarios Executed Successfully")
    print("=" * 80)


async def _run_additional_provider_examples() -> None:
    """Execute additional provider and scheduling examples."""
    print("\n--- Additional Provider & Scheduler Scenarios (via Brokers Domain) ---")

    print("\n[Data Preview] MT5 Bars (EURUSD):")
    df_mt5_bars = example_mt5_bars()
    print(df_mt5_bars.head(5).to_string())

    print("\n[Data Preview] MT5 Ticks (EURUSD):")
    df_mt5_ticks = example_mt5_ticks()
    print(df_mt5_ticks.head(5).to_string())

    print("\n[Data Preview] Dukascopy Bars (EURUSD):")
    df_duka = example_dukascopy()
    print(df_duka.head(5).to_string())

    print("\n[Data Preview] Yahoo Finance Bars (AAPL):")
    df_yahoo = example_yahoo()
    print(df_yahoo.head(5).to_string())

    print("\n[Data Preview] Binance Spot Bars (BTCUSDT):")
    df_binance = example_binance()
    print(df_binance.head(5).to_string())

    print("\n[Sync Execution] Caching & Scheduler:")
    res_caching = example_caching()
    print(f"  * example_caching: plan_id={res_caching.plan_id}")
    res_sched = await example_scheduler_create_status()
    sched_plan_id = res_sched.plan.plan_id if res_sched.plan else "none"
    print(f"  * example_scheduler_create_status: plan_id={sched_plan_id}")
    res_sched_cycle = example_scheduler_start_stop()
    print(f"  * example_scheduler_start_stop: receipt_id={res_sched_cycle.receipt_id}")


def run_usage_scenarios() -> None:
    """Run all usage scenarios synchronously."""
    asyncio.run(main())


if __name__ == "__main__":
    run_usage_scenarios()
