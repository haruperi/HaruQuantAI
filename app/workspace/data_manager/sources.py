"""Register and ingest historical datasets using the existing broker clients."""

from __future__ import annotations

import asyncio
import inspect
import json
import math
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any, cast

import pandas as pd  # type: ignore[import-untyped]

from app.host.persistence import HostPersistence
from app.include.contracts import BridgeError
from app.include.enums import Timeframe
from app.include.market_storage import price_columns, safe_component
from app.workspace.data_manager.coverage import missing_ranges, record_checked_ranges
from app.workspace.data_manager.dukascopy import Dukascopy
from app.workspace.data_manager.storage import dataset_root, publish_frame, require_data

CRYPTO = {
    "binance": ("binance", "spot"),
    "binance_coinm": ("binance", "coin-m"),
    "binance_usdtm": ("binance", "usdt-m"),
    "bitfinex": ("bitfinex", "spot"),
    "poloniex": ("poloniex", "spot"),
    "coinbase": ("coinbase", "spot"),
}
_MAX_DATASETS = 1000
_MAX_SYMBOL = 128
_CONTROL_LIMIT = 32

PROVIDERS = ("darwinex", *CRYPTO, "yahoo", "sq_equity", "sq_futures", "mt5")
_CRYPTO_TIMEFRAMES = {
    "binance": "M1 M3 M5 M15 M30 H1 H2 H4 H6 H8 H12 D1",
    "binance_coinm": "M1 M3 M5 M15 M30 H1 H2 H4 H6 H8 H12 D1",
    "binance_usdtm": "M1 M3 M5 M15 M30 H1 H2 H4 H6 H8 H12 D1",
    "bitfinex": "M1 M5 M15 M30 H1 H3 H6 H12 D1",
    "coinbase": "M1 M5 M15 H1 H6 D1",
    "poloniex": "M5 M15 M30 H2 H4 D1",
}


def provider_id(value: str) -> str:
    """Normalize menu and CLI names without conflating the six crypto markets."""
    key = value.strip().lower().replace("-", "_")
    key = {
        "binancecoinm": "binance_coinm",
        "binanceusdtm": "binance_usdtm",
        "equity": "sq_equity",
        "futures": "sq_futures",
        "metatrader": "mt5",
    }.get(key, key)
    if key not in PROVIDERS:
        raise ValueError("Unknown historical data source")
    return key


def capabilities(provider: str) -> dict[str, Any]:
    """Expose supported native resolutions; do not label daily data as M1."""
    source = provider_id(provider)
    frames = _CRYPTO_TIMEFRAMES.get(
        source,
        {
            "darwinex": "M1 D1 TICK",
            "yahoo": "M1 M5 M15 M30 H1 D1 W1 MN1",
            "sq_equity": "D1",
            "sq_futures": "D1",
            "mt5": "M1 M5 M15 M30 H1 H4 D1",
        }.get(source, ""),
    )
    return {
        "provider": source,
        "timeframes": frames.split(),
        "default_timeframe": "D1"
        if source in ("yahoo", "sq_equity", "sq_futures")
        else "M5"
        if source == "poloniex"
        else "M1",
    }


def make_client(provider: str) -> Any:
    """Construct a data-only client; MT5 reuses its connected native bridge."""
    from app.workspace.brokers import (
        CryptoClient,
        DarwinexClient,
        SQEquityClient,
        SQFuturesClient,
        YahooClient,
    )
    from app.workspace.brokers.base import get_broker

    if provider in CRYPTO:
        exchange, venue = CRYPTO[provider]
        return CryptoClient(exchange=exchange, venue=venue)
    if provider == "mt5":
        client = get_broker("metatrader")
        if not client.bridge.connected:
            raise ValueError("Connect the MT5 terminal EA to the backend bridge first")
        return client
    factories = {
        "darwinex": DarwinexClient,
        "yahoo": YahooClient,
        "sq_equity": SQEquityClient,
        "sq_futures": SQFuturesClient,
    }
    client = factories[provider]()
    # Ingestion must fetch the source, not rediscover its own cached dataset.
    if provider.startswith("sq_"):
        client.use_cache = False
    return client


def resolve_result(value: Any, client: Any) -> Any:
    """Execute asynchronous MT5 reads on their owning bridge event loop."""
    if not inspect.isawaitable(value):
        return value
    loop = getattr(client, "_loop", None)
    if loop is not None and loop.is_running():
        return asyncio.run_coroutine_threadsafe(_await_result(value), loop).result(
            timeout=120
        )
    return asyncio.run(_await_result(value))


async def _await_result(value: Any) -> Any:
    return await value


class Sources:
    """Persist source definitions and publish actual broker DataFrames to Parquet."""

    def __init__(
        self,
        gateway: HostPersistence | None = None,
        *,
        market_root: Path | None = None,
        client_factory: Any = None,
    ) -> None:
        self.gateway = gateway if gateway is not None else HostPersistence()
        self.market_root = market_root or Path("data/market")
        self.client_factory = client_factory or make_client

    def add(self, provider: str, definitions: list[dict[str, Any]]) -> dict[str, Any]:
        """Atomically register a batch without inventing data or record counts."""
        source = provider_id(provider)
        if (
            not isinstance(definitions, list)
            or not definitions
            or len(definitions) > _MAX_DATASETS
        ):
            raise ValueError("Register between one and 1,000 datasets")
        require_data(self.gateway.ensure_datasets_schema())
        rows = [self._definition(source, definition) for definition in definitions]
        if len({row["id"] for row in rows}) != len(rows):
            raise ValueError("Duplicate dataset in registration")
        with self.gateway.transaction() as tx:
            for row in rows:
                existing = require_data(
                    tx.read_records(
                        "datamgr_datasets", filters={"id": row["id"]}, limit=1
                    )
                )["records"]
                if existing:
                    raise ValueError(
                        f"Dataset already exists: {row['symbol']} {row['timeframe']}"
                    )
                require_data(tx.create_records("datamgr_datasets", row))
        return {"success": True, "data": {"records": rows}}

    def _definition(self, source: str, definition: dict[str, Any]) -> dict[str, Any]:
        if not isinstance(definition, dict):
            raise TypeError("A dataset definition must be an object")
        symbol = safe_component(str(definition.get("symbol", "")).strip().upper())
        underlying = str(definition.get("underlying") or symbol).strip()
        if (
            not underlying
            or len(underlying) > _MAX_SYMBOL
            or any(ord(c) < _CONTROL_LIMIT for c in underlying)
        ):
            raise ValueError("Invalid provider symbol")
        timeframe = str(
            definition.get("timeframe") or capabilities(source)["default_timeframe"]
        ).upper()
        if timeframe not in capabilities(source)["timeframes"]:
            raise ValueError(f"{source} does not supply {timeframe} historical data")
        raw_step = definition.get("tick_size", 0.00000001)
        if isinstance(raw_step, bool):
            raise TypeError("Price unit must be a positive number")
        step = float(raw_step)
        if not math.isfinite(step) or step <= 0:
            raise ValueError("Price unit must be finite and positive")
        now = datetime.now(UTC).isoformat()
        return {
            "id": f"{source}:{symbol}:{timeframe}",
            "source": source,
            "symbol": symbol,
            "underlying": underlying,
            "timeframe": timeframe,
            "broker": str(definition.get("broker") or "SQ default"),
            "timezone": "UTC",
            "category": str(
                definition.get("category")
                or (
                    "Crypto"
                    if source in CRYPTO
                    else "Forex"
                    if source in ("darwinex", "mt5")
                    else "Stocks"
                    if source != "sq_futures"
                    else "Futures"
                )
            ),
            "date_from": "",
            "date_to": "",
            "bars": 0,
            "path": str(dataset_root(self.market_root / source, symbol, timeframe)),
            "data_kind": "ticks" if timeframe == "TICK" else "bars",
            "created_at": now,
            "updated_at": now,
            "schema_version": 2,
            "lineage_json": json.dumps(
                {
                    "tick_size": step,
                    "partitions": [],
                    "price_policy": "round-half-even-to-storage-unit",
                    "provider": source,
                }
            ),
        }

    def record(self, dataset_id: str) -> dict[str, Any]:
        """Resolve a persisted identity instead of trusting browser target metadata."""
        rows = require_data(
            self.gateway.read_records(
                "datamgr_datasets", filters={"id": dataset_id}, limit=1
            )
        )["records"]
        if not rows or rows[0]["source"] not in (*PROVIDERS, "dukascopy"):
            raise ValueError("Choose a registered historical dataset")
        return cast("dict[str, Any]", rows[0])

    def download(
        self,
        dataset_id: str,
        date_from: Any,
        date_to: Any,
        *,
        overwrite: bool = False,
        context: Any = None,
    ) -> dict[str, Any]:
        """Fetch complete bounded intervals and commit each independently."""
        row = self.record(dataset_id)
        lower = Dukascopy.parse_date_bound(date_from)
        upper = Dukascopy.parse_date_bound(date_to, is_end=True)
        if (
            lower is None
            or upper is None
            or lower > upper
            or not isinstance(overwrite, bool)
        ):
            raise ValueError("Choose a valid date range and overwrite option")
        source, timeframe = row["source"], row["timeframe"]
        if source == "dukascopy":
            result = Dukascopy(self.gateway).download(
                row["symbol"],
                timeframe=timeframe,
                underlying=row["underlying"],
                date_from=lower,
                date_to=upper,
                overwrite=overwrite,
                context=context,
            )
            require_data(result)
            return result
        missing = missing_ranges(row, lower, upper, overwrite=overwrite)
        if not missing:
            _report_progress(context, 100, "Requested history is already downloaded")
            return {
                "success": True,
                "data": {
                    "dataset_id": dataset_id,
                    "received_rows": 0,
                    "published_intervals": 0,
                    "already_downloaded": True,
                    "record": self.record(dataset_id),
                },
            }
        chunks = [
            interval
            for start, stop in missing
            for interval in intervals(source, timeframe, start, stop)
        ]
        client = self.client_factory(source)
        published, received = 0, 0
        empty = []
        try:
            for index, (start, stop) in enumerate(chunks):
                if context is not None:
                    context.wait_if_paused()
                    context.raise_if_cancelled()
                frame = _fetch_frame(client, row, start, stop)
                count = self._publish(
                    row, frame, start, stop, overwrite=overwrite, context=context
                )
                published += bool(count)
                received += count
                if not count:
                    empty.append((start, stop))
                _report_progress(
                    context,
                    100 * (index + 1) / len(chunks),
                    f"{row['symbol']}: {stop.isoformat()}",
                )
        finally:
            if source != "mt5":
                client.disconnect()
        if not published and missing == [(lower, upper)]:
            raise ValueError("No historical observations were returned for this range")
        record_checked_ranges(self.gateway, dataset_id, empty)
        return {
            "success": True,
            "data": {
                "dataset_id": dataset_id,
                "received_rows": received,
                "published_intervals": published,
                "record": self.record(dataset_id),
            },
        }

    def _publish(
        self,
        row: dict[str, Any],
        frame: pd.DataFrame,
        start: datetime,
        stop: datetime,
        *,
        overwrite: bool,
        context: Any,
    ) -> int:
        if frame.empty:
            return 0
        frame = frame.copy()
        if "DateTime" in frame:
            frame = frame.set_index("DateTime")
        frame.index = pd.to_datetime(frame.index, utc=True)
        frame = frame.loc[(frame.index >= start) & (frame.index <= stop)]
        if frame.empty:
            return 0
        step = json.loads(row["lineage_json"])["tick_size"]
        digits = max(0, -int(Decimal(str(step)).as_tuple().exponent))
        for column in price_columns(row["timeframe"]):
            frame[column] = ((frame[column] / step).round() * step).round(digits)
        publish_frame(
            self.gateway,
            self.market_root / row["source"],
            row,
            frame,
            step,
            overwrite=overwrite,
            date_from=start,
            date_to=stop,
            context=Checkpoints(context) if context is not None else None,
            coverage=(start, stop),
        )
        return len(frame)


def _fetch_frame(
    client: Any, row: dict[str, Any], start: datetime, stop: datetime
) -> pd.DataFrame:
    try:
        value = (
            client.get_ticks(
                row["underlying"], date_from=start, date_to=stop, count=None
            )
            if row["timeframe"] == "TICK"
            else client.get_bars(
                row["underlying"],
                row["timeframe"],
                date_from=start,
                date_to=stop,
                count=None,
                limit=1000,
            )
        )
        frame = resolve_result(value, client)
    except BridgeError as error:
        if error.code != "NO_DATA":
            raise
        return pd.DataFrame()
    if not isinstance(frame, pd.DataFrame):
        raise TypeError("Provider did not return a market DataFrame")
    return frame


class Checkpoints:
    """Forward cancellation without restarting overall progress for each file."""

    def __init__(self, context: Any) -> None:
        self.context = context

    def wait_if_paused(self) -> None:
        """Wait at a cooperative pause checkpoint."""
        self.context.wait_if_paused()

    def raise_if_cancelled(self) -> None:
        """Abort before publishing cancelled work."""
        self.context.raise_if_cancelled()

    def report_progress(self, progress: float, message: str = "") -> None:
        """Leave overall progress to the interval coordinator."""
        del progress, message


def intervals(
    source: str, timeframe: str, lower: datetime, upper: datetime
) -> list[tuple[datetime, datetime]]:
    """Bound REST requests below candle limits, and CDN requests to a year."""
    if source in CRYPTO:
        step = timedelta(seconds=200 * Timeframe.resolve(timeframe).to_seconds())
    elif source == "yahoo":
        step = timedelta(days=5 if timeframe != "D1" else 200)
    elif source == "mt5":
        step = (
            timedelta(hours=1)
            if timeframe == "TICK"
            else timedelta(seconds=500 * Timeframe.resolve(timeframe).to_seconds())
        )
    else:
        step = None
    current, result = lower, []
    while current <= upper:
        boundary = (
            current + step
            if step is not None
            else datetime(current.year + 1, 1, 1, tzinfo=UTC)
        )
        stop = min(upper, boundary - timedelta(microseconds=1))
        result.append((current, stop))
        current = boundary
    return result


def _report_progress(context: Any, progress: float, message: str) -> None:
    if context is not None:
        context.report_progress(progress, message)
