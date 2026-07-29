"""Unit tests for app/services/data/sources/broker_adapter.py to reach >80% coverage."""

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

import pytest
from app.services.data.contracts import DataError
from app.services.data.market_data.symbol_metadata import (
    SymbolListRequest,
    SymbolMetadataRequest,
)
from app.services.data.sources.broker_adapter import (
    ExternalMarketDataSource,
    _require_result,
    _run,
)
from app.services.data.sources.contracts import SourceReadRequest

_REQ_ID = "req-11111111-1111-4111-8111-111111111111"
_NOW = datetime.now(UTC)
_PAST = _NOW - timedelta(days=1)


def test_init_invalid_source_id() -> None:
    """Test ExternalMarketDataSource init with blank or untrimmed source_id."""
    adapter = MagicMock()
    with pytest.raises(
        ValueError, match="source_id must be a non-empty trimmed string"
    ):
        ExternalMarketDataSource("", adapter)
    with pytest.raises(
        ValueError, match="source_id must be a non-empty trimmed string"
    ):
        ExternalMarketDataSource(" mt5 ", adapter)


def test_run_exception_mapping() -> None:
    """Test _run maps general exceptions to SOURCE_UNAVAILABLE DataError."""

    async def bad_coro():
        raise RuntimeError("Network down")

    with pytest.raises(DataError) as exc_info:
        _run(bad_coro(), _REQ_ID)
    assert exc_info.value.code == "SOURCE_UNAVAILABLE"


def test_require_result_error() -> None:
    """Test _require_result raises DataError when result has error or no data."""
    res_err = MagicMock()
    res_err.error = "ERROR"
    res_err.data = None
    with pytest.raises(DataError) as exc_info:
        _require_result(res_err, "test_op", _REQ_ID)
    assert exc_info.value.code == "SOURCE_UNAVAILABLE"


@pytest.mark.anyio
async def test_fetch_async_source_id_mismatch() -> None:
    """Test _fetch_async with mismatched source_id."""
    adapter = MagicMock()
    src = ExternalMarketDataSource("mt5", adapter)
    req = SourceReadRequest(
        source_id="ctrader",
        provider_symbol="EURUSD",
        data_kind="bars",
        timeframe="M1",
        start=_PAST,
        end=_NOW,
        limit=100,
        request_id=_REQ_ID,
    )
    with pytest.raises(DataError) as exc_info:
        await src._fetch_async(req)
    assert exc_info.value.code == "INVALID_INPUT"


@pytest.mark.anyio
async def test_fetch_async_unsupported_data_kind() -> None:
    """Test _fetch_async with unsupported data_kind (volume)."""
    adapter = MagicMock()
    src = ExternalMarketDataSource("mt5", adapter)
    req = SourceReadRequest(
        source_id="mt5",
        provider_symbol="EURUSD",
        data_kind="volume",
        start=_PAST,
        end=_NOW,
        limit=100,
        request_id=_REQ_ID,
    )
    with pytest.raises(DataError) as exc_info:
        await src._fetch_async(req)
    assert exc_info.value.code == "UNSUPPORTED_OPERATION"


@pytest.mark.anyio
async def test_fetch_async_bars_missing_volume() -> None:
    """Test _fetch_async bars raising DATA_QUALITY_FAILED when volume is None."""
    adapter = MagicMock()
    bar = MagicMock()
    bar.trade_volume = None
    bar.tick_volume = None
    bar.opening_timestamp = _NOW
    bar.closing_timestamp = _NOW

    bar_page = MagicMock()
    bar_page.items = [bar]

    bar_res = MagicMock()
    bar_res.error = None
    bar_res.data = bar_page
    bar_res.metadata.extensions = {
        "adapter_version": "v1",
        "timestamp": "2026-07-01T12:00:00.000000Z",
    }

    adapter.get_historical_bars = AsyncMock(return_value=bar_res)
    src = ExternalMarketDataSource("mt5", adapter)

    req = SourceReadRequest(
        source_id="mt5",
        provider_symbol="EURUSD",
        data_kind="bars",
        timeframe="M1",
        start=_PAST,
        end=_NOW,
        limit=100,
        request_id=_REQ_ID,
    )
    with pytest.raises(DataError) as exc_info:
        await src._fetch_async(req)
    assert exc_info.value.code == "DATA_QUALITY_FAILED"


@pytest.mark.anyio
async def test_fetch_async_empty_result() -> None:
    """Test _fetch_async raising EMPTY_RESULT when items list is empty."""
    adapter = MagicMock()
    bar_page = MagicMock()
    bar_page.items = []

    bar_res = MagicMock()
    bar_res.error = None
    bar_res.data = bar_page
    bar_res.metadata.extensions = {
        "adapter_version": "v1",
        "timestamp": "2026-07-01T12:00:00.000000Z",
    }

    adapter.get_historical_bars = AsyncMock(return_value=bar_res)
    src = ExternalMarketDataSource("mt5", adapter)

    req = SourceReadRequest(
        source_id="mt5",
        provider_symbol="EURUSD",
        data_kind="bars",
        timeframe="M1",
        start=_PAST,
        end=_NOW,
        limit=100,
        request_id=_REQ_ID,
    )
    with pytest.raises(DataError) as exc_info:
        await src._fetch_async(req)
    assert exc_info.value.code == "EMPTY_RESULT"


@pytest.mark.anyio
async def test_fetch_async_spreads_missing_precision() -> None:
    """
    Test _fetch_async spreads raising MISSING_ASSET_METADATA when precision is None.
    """
    adapter = MagicMock()

    spread_res = MagicMock()
    spread_res.error = None
    spread_res.data = Decimal("1.5")
    spread_res.metadata.extensions = {
        "adapter_version": "v1",
        "timestamp": "2026-07-01T12:00:00.000000Z",
    }
    adapter.get_spread = AsyncMock(return_value=spread_res)

    meta = MagicMock()
    meta.price_precision = None

    meta_res = MagicMock()
    meta_res.error = None
    meta_res.data = meta

    adapter.get_symbol_info = AsyncMock(return_value=meta_res)
    src = ExternalMarketDataSource("mt5", adapter)

    req = SourceReadRequest(
        source_id="mt5",
        provider_symbol="EURUSD",
        data_kind="spreads",
        start=_PAST,
        end=_NOW,
        limit=100,
        request_id=_REQ_ID,
    )
    with pytest.raises(DataError) as exc_info:
        await src._fetch_async(req)
    assert exc_info.value.code == "MISSING_ASSET_METADATA"


@pytest.mark.anyio
async def test_list_symbols_async_source_id_mismatch() -> None:
    """Test _list_symbols_async raising INVALID_INPUT on source_id mismatch."""
    adapter = MagicMock()
    src = ExternalMarketDataSource("mt5", adapter)
    req = SymbolListRequest(source_id="ctrader", limit=10, request_id=_REQ_ID)
    with pytest.raises(DataError) as exc_info:
        await src._list_symbols_async(req)
    assert exc_info.value.code == "INVALID_INPUT"


@pytest.mark.anyio
async def test_get_symbol_metadata_async_invalid_timezone() -> None:
    """
    Test _get_symbol_metadata_async raising MISSING_ASSET_METADATA when timezone non-str.
    """
    adapter = MagicMock()
    info = MagicMock()
    info.provider_metadata = {"timezone": 12345}  # non-string timezone
    info.provider_symbol = "EURUSD"

    info_res = MagicMock()
    info_res.error = None
    info_res.data = info
    info_res.metadata.extensions = {
        "adapter_version": "v1",
        "timestamp": "2026-07-01T12:00:00.000000Z",
    }

    adapter.get_symbol_info = AsyncMock(return_value=info_res)
    src = ExternalMarketDataSource("mt5", adapter)

    req = SymbolMetadataRequest(source_id="mt5", symbol="EURUSD", request_id=_REQ_ID)
    with pytest.raises(DataError) as exc_info:
        await src._get_symbol_metadata_async(req)
    assert exc_info.value.code == "MISSING_ASSET_METADATA"
