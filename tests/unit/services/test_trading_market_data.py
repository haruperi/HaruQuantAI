"""Verify shared historical data contracts without a live broker.

Description:
    Compare explicitly seeded simulation records with bounded native-response
    fixtures. Verify timestamps, limits, validation, receipt resolution and errors.

Purpose:
    FEAT-TRADING-MARKET-DATA: Protect broker-neutral historical reads.

Key Capabilities:
    - FR-TRADING-HISTORICAL-READS: Verify parity and read-only forwarding.
      Associated: `Trading.get_historical_bars()`, `Trading.get_ticks()`
      Logging: Spy on metadata-only read and validation logs.
    - FR-TRADING-HISTORY-VALIDATION: Verify missing and malformed data rejection.
      Associated: `validate_rows()`, `validate_request()`
      Logging: Exercise every validation path without dumping source records.

Python API Usage:
    Run via pytest; all native fixtures use temporary stores.

CLI Usage:
    uv run pytest tests/unit/services/test_trading_market_data.py --no-cov
"""

import asyncio
from dataclasses import asdict
from datetime import UTC, datetime, timedelta
from pathlib import Path
from unittest.mock import AsyncMock, Mock

import pytest
from app.services.brokers.contracts import (
    BridgeError,
    MarketBar,
    MarketTick,
    ReceiptStatus,
    SymbolSpec,
    Timeframe,
)
from app.services.brokers.metatrader import MT5Backend
from app.services.brokers.simulator import SimulationBackend
from app.services.trading import Trading, market_data

START = datetime(2026, 1, 1, tzinfo=UTC)
STAMP = int(START.timestamp())
BARS = [MarketBar(STAMP + i * 60, 1.1, 1.2, 1.0, 1.15, i, 2, 0) for i in range(3)]
TICKS = [
    MarketTick(STAMP * 1000 + i, 1.1, 1.2, 0.0, 0, 6, 0.0) for i in (0, 123, 123, 456)
]


def model() -> SimulationBackend:
    """Create an explicitly seeded model with no automatic historical aggregation."""
    backend = SimulationBackend()
    backend.add_symbol(SymbolSpec(name="EURUSD"))
    backend.seed_bar_history("EURUSD", Timeframe.PERIOD_M1, BARS)
    backend.seed_tick_history("EURUSD", TICKS)
    return backend


def test_native_model_parity_and_receipts(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Return identical DTOs, preserve duplicate tick milliseconds and resolve reads."""

    async def scenario() -> None:
        native = MT5Backend(
            auth_token="isolated-test-token", journal_path=tmp_path / "native.db"
        )
        local_backend = model()
        local = Trading(local_backend)
        clock = local_backend._clock
        call = AsyncMock(
            side_effect=[[asdict(row) for row in BARS], [asdict(row) for row in TICKS]]
        )
        monkeypatch.setattr(native.bridge, "call", call)
        try:
            assert (
                await native.get_historical_bars(
                    "EURUSD", Timeframe.PERIOD_M1, START, START + timedelta(minutes=2)
                )
                == await local.get_historical_bars(
                    "EURUSD", Timeframe.PERIOD_M1, START, START + timedelta(minutes=2)
                )
                == BARS
            )
            end = START + timedelta(milliseconds=456)
            assert (
                await native.get_ticks("EURUSD", START, end)
                == await local.get_ticks("EURUSD", START, end)
                == TICKS
            )
            assert call.call_args.kwargs["args"] == [
                "EURUSD",
                "range",
                STAMP * 1000,
                STAMP * 1000 + 456,
                0,
                1000,
            ]
            assert call.call_args.kwargs["timeout"] == 60.0
            assert call.call_args.kwargs["class_name"] == "MarketData"
            assert not call.call_args.kwargs.get("requires_arm", False)
            identity = local.last_command_id()
            assert identity is not None
            receipt = local.receipt(identity)
            assert receipt is not None and receipt.status == ReceiptStatus.RESOLVED
            assert local_backend._clock == clock
            assert not local_backend._armed
        finally:
            await native.close()
            await local.close()

    asyncio.run(scenario())


def test_subranges_and_explicit_empty_series() -> None:
    """Filter inclusively, keep millisecond bounds and distinguish seeded emptiness."""

    async def scenario() -> None:
        backend = model()
        trading = Trading(backend)
        try:
            assert (
                await trading.get_historical_bars(
                    "EURUSD",
                    Timeframe.PERIOD_M1,
                    START + timedelta(minutes=1),
                    START + timedelta(minutes=1),
                )
                == BARS[1:2]
            )
            assert (
                await trading.get_ticks(
                    "EURUSD",
                    START + timedelta(milliseconds=123),
                    START + timedelta(milliseconds=123),
                )
                == TICKS[1:3]
            )
            assert (
                await trading.get_ticks(
                    "EURUSD",
                    START + timedelta(milliseconds=124),
                    START + timedelta(milliseconds=455),
                )
                == []
            )
            backend.seed_tick_history("EURUSD", [])
            assert await trading.get_ticks("EURUSD", START, START) == []
        finally:
            await trading.close()

    asyncio.run(scenario())


@pytest.mark.parametrize(
    "problem", ["naive", "reversed", "limit", "current", "oversized"]
)
def test_bad_requests_do_not_dispatch(problem: str) -> None:
    """Reject invalid requests before a backend call or any external work."""
    backend = Mock()
    backend.call = AsyncMock()
    start, end, frame, limit = START, START, Timeframe.PERIOD_M1, 1000
    if problem == "naive":
        start = START.replace(tzinfo=None)
    if problem == "reversed":
        end = START - timedelta(seconds=1)
    if problem == "limit":
        limit = 1001
    if problem == "current":
        frame = Timeframe.PERIOD_CURRENT
    if problem == "oversized":
        end = START + timedelta(days=1)
    with pytest.raises(BridgeError):
        asyncio.run(
            market_data.get_historical_bars(
                backend, "EURUSD", frame, start, end, limit=limit
            )
        )
    backend.call.assert_not_awaited()


def test_unseeded_history_and_tick_overflow() -> None:
    """Missing history and too many in-range ticks fail explicitly."""

    async def scenario() -> None:
        backend = model()
        trading = Trading(backend)
        try:
            with pytest.raises(BridgeError) as missing:
                await trading.get_historical_bars(
                    "EURUSD", Timeframe.PERIOD_H1, START, START
                )
            assert missing.value.code == "DATA_NOT_READY"
            with pytest.raises(BridgeError) as overflow:
                await trading.get_ticks(
                    "EURUSD", START, START + timedelta(seconds=1), limit=2
                )
            assert overflow.value.code == "DATA_LIMIT_EXCEEDED"
            identity = trading.last_command_id()
            assert identity is not None
            receipt = trading.receipt(identity)
            assert receipt is not None and receipt.status == ReceiptStatus.REJECTED
        finally:
            await trading.close()

    asyncio.run(scenario())


@pytest.mark.parametrize(
    "problem", ["shape", "nan", "bool", "range", "order", "ohlc", "cap"]
)
def test_malformed_native_data_is_rejected(problem: str) -> None:
    """Reject malformed numeric values, impossible bars and invalid chronology."""
    rows = [asdict(row) for row in BARS]
    if problem == "shape":
        rows[0].pop("close")
    if problem == "nan":
        rows[0]["open"] = float("nan")
    if problem == "bool":
        rows[0]["tick_volume"] = True
    if problem == "range":
        rows[0]["time"] = STAMP - 1
    if problem == "order":
        rows.reverse()
    if problem == "ohlc":
        rows[0]["high"] = 0.9
    with pytest.raises(BridgeError) as caught:
        market_data.validate_rows(
            rows, "bars", STAMP, STAMP + 120, 2 if problem == "cap" else 3
        )
    assert caught.value.code == "INVALID_MARKET_DATA"


def test_read_and_validation_logs_are_metadata_only(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Every read logs metadata without symbol, record data or request arguments."""
    logger = Mock()
    monkeypatch.setattr(market_data, "logger", logger)
    backend = Mock()
    backend.call = AsyncMock(return_value=[])
    asyncio.run(market_data.get_ticks(backend, "private-symbol", START, START))
    assert logger.debug.call_count == 3
    assert "private-symbol" not in repr(logger.mock_calls)


def test_exact_datetime_rounding_and_negative_market_prices() -> None:
    """Preserve sub-millisecond boundaries and legitimate finite negative prices."""
    lower, upper = market_data._bounds(
        START + timedelta(microseconds=123001),
        START + timedelta(microseconds=456999),
        1000,
    )
    assert (lower, upper) == (STAMP * 1000 + 124, STAMP * 1000 + 456)
    negative = MarketBar(STAMP, -1.0, 0.0, -2.0, -0.5, 1, 0, 0)
    assert market_data.validate_rows([asdict(negative)], "bars", STAMP, STAMP, 1) == [
        negative
    ]


def test_epoch_zero_ticks_are_rejected_before_dispatch() -> None:
    """Native CopyTicks treats zero as a special latest-tick request."""
    backend = Mock()
    backend.call = AsyncMock()
    epoch = datetime(1970, 1, 1, tzinfo=UTC)
    with pytest.raises(BridgeError) as caught:
        asyncio.run(market_data.get_ticks(backend, "EURUSD", epoch, epoch))
    assert caught.value.code == "BAD_REQUEST"
    backend.call.assert_not_awaited()


@pytest.mark.parametrize(
    "selector,expected",
    [
        ({"date_from": START + timedelta(seconds=1), "count": 2}, BARS[1:]),
        ({"start_pos": 1, "count": 1}, BARS[1:2]),
        ({"count": 2}, BARS[-2:]),
        ({"start_pos": 1}, BARS[-2:]),
        ({"date_from": START + timedelta(minutes=1)}, BARS[1:]),
        ({}, BARS),
        ({"start_pos": 10, "count": 2}, []),
        ({"date_from": START + timedelta(days=1), "count": 2}, []),
    ],
)
def test_bar_modes_native_fixture_parity(
    selector: dict[str, object],
    expected: list[MarketBar],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Date counts move forward; indices start at the newest bar and include it."""

    class FixedNow(datetime):
        @classmethod
        def now(cls, tz: object = None) -> datetime:
            return START + timedelta(minutes=2)

    monkeypatch.setattr(market_data, "datetime", FixedNow)

    async def scenario() -> None:
        backend = model()
        native = MT5Backend(
            auth_token="isolated-test-token", journal_path=tmp_path / "native.db"
        )
        call = AsyncMock(return_value=[asdict(row) for row in expected])
        monkeypatch.setattr(native.bridge, "call", call)
        try:
            assert (
                await Trading(backend).get_historical_bars(
                    "EURUSD", Timeframe.PERIOD_M1, **selector
                )
                == expected
            )
            assert (
                await native.get_historical_bars(
                    "EURUSD", Timeframe.PERIOD_M1, **selector
                )
                == expected
            )
            assert call.call_args.kwargs["args"][2] in (
                "position",
                "date_count",
                "range",
            )
        finally:
            await native.close()
            await backend.close()

    asyncio.run(scenario())


@pytest.mark.parametrize(
    "selector,expected",
    [
        ({"date_from": START + timedelta(milliseconds=123), "count": 2}, TICKS[1:3]),
        ({"count": 2}, TICKS[-2:]),
        ({"date_from": START}, TICKS),
        ({}, TICKS),
    ],
)
def test_tick_modes(selector: dict[str, object], expected: list[MarketTick]) -> None:
    """Preserve duplicate milliseconds in forward counts and latest tick selection."""

    async def scenario() -> None:
        backend = model()
        try:
            assert await Trading(backend).get_ticks("EURUSD", **selector) == expected
        finally:
            await backend.close()

    asyncio.run(scenario())


@pytest.mark.parametrize(
    "selector",
    [
        {"count": 0},
        {"count": True},
        {"count": 1001},
        {"start_pos": -1},
        {"start_pos": True},
        {"start_pos": 2147483648, "count": 1},
        {"date_to": START},
        {"date_from": START, "start_pos": 0},
        {"date_from": START, "date_to": START, "count": 1},
        {"start_pos": 1000},
    ],
)
def test_invalid_optional_selectors_never_dispatch(selector: dict[str, object]) -> None:
    """Conflicting selectors, booleans and invalid sizes fail before backend work."""
    backend = Mock()
    backend.call = AsyncMock()
    with pytest.raises(BridgeError):
        asyncio.run(
            market_data.get_historical_bars(
                backend, "EURUSD", Timeframe.PERIOD_M1, **selector
            )
        )
    backend.call.assert_not_awaited()


def test_model_clock_prevents_history_lookahead() -> None:
    """New latest, forward and range routes never expose future seeded records."""

    async def scenario() -> None:
        backend = model()
        backend.set_clock(START + timedelta(minutes=1))
        before = backend._clock
        trading = Trading(backend)
        try:
            assert (
                await trading.get_historical_bars(
                    "EURUSD", Timeframe.PERIOD_M1, count=1
                )
                == BARS[1:2]
            )
            assert (
                await trading.get_historical_bars(
                    "EURUSD", Timeframe.PERIOD_M1, date_from=START, count=3
                )
                == BARS[:2]
            )
            assert (
                await trading.get_historical_bars(
                    "EURUSD", Timeframe.PERIOD_M1, START, START + timedelta(minutes=2)
                )
                == BARS[:2]
            )
            backend.set_clock(START + timedelta(milliseconds=123))
            assert await trading.get_ticks("EURUSD", count=3) == TICKS[:3]
            assert backend._clock != before
            assert backend._clock == START + timedelta(milliseconds=123)
        finally:
            await trading.close()

    asyncio.run(scenario())
