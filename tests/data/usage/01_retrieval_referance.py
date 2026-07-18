"""Executable package-root retrieval and reference examples."""

import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.services.data import (
    get_data_availability,
    get_historical_volume,
    get_market_data,
    get_market_hours,
    get_spread_data,
    get_symbol_metadata,
    get_tick_data,
    get_trading_sessions,
    list_symbols,
    to_ohlcv_dataframe,
    to_tick_dataframe,
)
from app.services.data.contracts import DataError

_SOURCE = "mt5"
_SYMBOL = "EURUSD"
_END = datetime.now(UTC).replace(second=0, microsecond=0) - timedelta(minutes=1)
_START = _END - timedelta(minutes=10)


def _header(title: str) -> None:
    """Print one example heading."""
    print(f"\n{'=' * 88}\n{title}\n{'=' * 88}")


_header("1. get_market_data")
try:
    market_data = get_market_data(
        source_id=_SOURCE,
        symbol=_SYMBOL,
        timeframe="M1",
        limit=10,
    )
    print("Market data records:", market_data.record_count)
    ohlcv = to_ohlcv_dataframe(market_data)
    print("OHLCV + spread dataframe:")
    print("Spread unit:", ohlcv.attrs["spread_unit"])
    print(ohlcv)
except DataError as error:
    print("Market data unavailable:", error.code)

_header("2. get_tick_data")
try:
    tick_data = get_tick_data(
        source_id=_SOURCE,
        symbol=_SYMBOL,
        start=_START,
        end=_END,
    )
    print("Tick records:", tick_data.record_count)
    ticks = to_tick_dataframe(tick_data)
    print("Tick dataframe:")
    print("Price unit:", ticks.attrs["price_unit"])
    print("Volume unit:", ticks.attrs["volume_unit"])
    print(ticks)
except DataError as error:
    print("Tick data unavailable:", error.code)

_header("3. get_spread_data")
try:
    spread_data = get_spread_data(
        source_id=_SOURCE,
        symbol=_SYMBOL,
    )
    print("Spread records:", spread_data.record_count)
except DataError as error:
    print("Spread data unavailable:", error.code)

_header("4. get_symbol_metadata")
try:
    metadata = get_symbol_metadata(
        source_id=_SOURCE,
        symbol=_SYMBOL,
    )
    print("Provider symbol:", metadata.provider_symbol)
    print("Price precision:", metadata.digits)
    print("Spread:", metadata.spread)
    print("Point:", metadata.point)
    print("Volume max:", metadata.volume_max)
    print("Volume min:", metadata.volume_min)
    print("Description:", metadata.description)
except DataError as error:
    print("Symbol metadata unavailable:", error.code)

_header("5. list_symbols")
try:
    symbols = list_symbols(
        source_id=_SOURCE,
        query="*EUR*",
        limit=10,
    )
    print("Symbols:", list(symbols.items))
except DataError as error:
    print("Symbol list unavailable:", error.code)

_header("6. get_data_availability")
try:
    availability = get_data_availability(
        source_id=_SOURCE,
        symbol=_SYMBOL,
        timeframe="M1",
    )
    print("Stored records:", availability.record_count)
    print("Completeness:", availability.completeness)
except DataError as error:
    print(
        "Local availability evidence is absent until a dataset is saved:",
        error.code,
    )

_header("7. get_market_hours")
try:
    market_hours = get_market_hours(
        source_id=_SOURCE,
        symbol=_SYMBOL,
        timezone="UTC",
    )
    print("Market-hour windows:", len(market_hours.hours))
except DataError as error:
    print("MT5 does not expose authoritative market hours:", error.code)

_header("8. get_trading_sessions")
try:
    trading_sessions = get_trading_sessions(
        source_id=_SOURCE,
        symbol=_SYMBOL,
        timezone="UTC",
    )
    print("Trading sessions:", len(trading_sessions.sessions))
except DataError as error:
    print("MT5 does not expose authoritative trading sessions:", error.code)

_header("9. get_historical_volume")
try:
    historical_volume = get_historical_volume(
        source_id=_SOURCE,
        symbol=_SYMBOL,
        start=_START,
        end=_END,
        mode="summary",
        limit=10,
    )
    print("Volume unit:", historical_volume.volume_unit)
    print("Volume summary:", historical_volume.summary)
except DataError as error:
    print("Historical volume unavailable:", error.code)
