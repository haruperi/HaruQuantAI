"""Helper constants, validation, client factories, and intervals for sources."""

from __future__ import annotations

import asyncio
import inspect
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from app.include.enums import Timeframe

# --- Dukascopy constants and helpers ---

DEFAULT_STORAGE_ROOT = Path("data/market/dukascopy")
DEFAULT_CATALOG_PATH = DEFAULT_STORAGE_ROOT / "dukascopy.csv"
MIN_CATALOG_PARTS = 11

DISCLAIMER_PARAGRAPHS = [
    (
        "The Dukascopy Trading Tools include different financial information. "
        "Such data are a result of original and unique methods and technology of "
        "information gathering, compilation, analysis and statistical evaluation "
        "developed by Dukascopy Bank SA. Therefore, such data reflect the current "
        "fair value of the respective financial instruments as independently assessed "
        "by Dukascopy Bank SA and NOT the actual values at a given point in time. "
        "If you are looking to obtain actual quotes please contact the respective "
        "entities that provide this information."
    ),
    (
        "The Dukascopy Trading Tools data and/or any other data available as free "
        "product from Dukascopy Bank's website shall not constitute a forecast of "
        "the market value of any instruments at any future point either, and is "
        "not an investment advice or recommendation in any form."
    ),
    (
        "Anyone using and/or putting free web products including all or parts of the "
        "information taken from the Dukascopy Trading Tools and/or any other data "
        "available as free product from Dukascopy Bank's website shall put a clear "
        "note to the public that such data are not meant to indicate the actual value "
        "at any given point in time but represent a discretionary assessment by "
        "Dukascopy Bank SA only."
    ),
    (
        "The market data assessment system is in constant development and is provided "
        "'AS IS', 'AS AVAILABLE', 'WITH ALL ITS FAULTS' and is offered without any "
        "covenants or any express, implied or statutory warranties including "
        "(without limitation and qualification) any warranties as to accuracy, "
        "functionality, performance, merchantability, quiet enjoyment, system "
        "integration, data accuracy or fitness for any particular purpose and any "
        "warranties arising from trade usage, course of dealing or course of "
        "performance."
    ),
]


def _valid_add_inputs(
    symbols: Any, data_type: Any, postfix: Any, confirmed: Any
) -> bool:
    return (
        isinstance(data_type, str)
        and isinstance(postfix, str)
        and isinstance(confirmed, bool)
        and isinstance(symbols, (str, list))
        and (isinstance(symbols, str) or all(isinstance(item, str) for item in symbols))
    )


# --- Broker source constants and helpers ---

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


__all__ = [
    "CRYPTO",
    "DEFAULT_CATALOG_PATH",
    "DEFAULT_STORAGE_ROOT",
    "DISCLAIMER_PARAGRAPHS",
    "MIN_CATALOG_PARTS",
    "PROVIDERS",
    "_CONTROL_LIMIT",
    "_CRYPTO_TIMEFRAMES",
    "_MAX_DATASETS",
    "_MAX_SYMBOL",
    "Checkpoints",
    "_await_result",
    "_report_progress",
    "_valid_add_inputs",
    "capabilities",
    "intervals",
    "make_client",
    "provider_id",
    "resolve_result",
]
