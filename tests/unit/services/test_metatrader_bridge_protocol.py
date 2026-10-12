"""Verify the MT5 bridge's wire compatibility and redacted codec logging.

Description:
    Exercise frame conversion without sockets and facade wiring with an isolated
    temporary journal. Validate
    precision, framing, rejection boundaries and log redaction with isolated data.

Purpose:
    FEAT-MT5-BRIDGE: Protect the wire contract when consolidating codec ownership.

Key Capabilities:
    - FR-MT5-BRIDGE-FRAME-ENCODING: Verify bytes, value tags and rejection limits.
      Associated: `encode_frame()`
      Logging: Verify DEBUG encode attempts contain operation metadata only.
    - FR-MT5-BRIDGE-FRAME-DECODING: Verify restoration and invalid frame rejection.
      Associated: `decode_frame()`
      Logging: Verify DEBUG decode attempts contain operation and byte count.

Python API Usage:
    Invoke through pytest; no broker session or credentials are required.

CLI Usage:
    uv run pytest tests/unit/services/test_metatrader_bridge_protocol.py --no-cov
"""

import asyncio
import json
from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast
from unittest.mock import AsyncMock, Mock

import pytest
from app.host.persistence.engine import DEFAULT_DATABASE_PATH
from app.services.brokers import metatrader
from app.services.brokers.contracts import Receipt, ReceiptStatus, SymbolSpec
from app.services.brokers.metatrader import Bridge, MT5Backend
from app.services.brokers.simulator import SimulationBackend
from app.services.trading import (
    AccountInfo,
    DealInfo,
    HistoryOrderInfo,
    OrderInfo,
    PositionInfo,
    SymbolInfo,
    TerminalInfo,
    Trade,
    Trading,
)
from scripts.examples import brokers


def test_wire_bytes_and_round_trip() -> None:
    """Keep compact JSON framing and nested values compatible with the EA."""
    message = {
        "v": 1,
        "args": [2**64 - 1, -(2**63), True, None, 1.25, "@i64:42", "€"],
        "nested": {"items": (0, "@@prefix")},
    }
    frame = metatrader.encode_frame(message)
    expected = (
        '{"v":"@i64:1","args":["@i64:18446744073709551615",'
        '"@i64:-9223372036854775808",true,null,1.25,"@@i64:42","€"],'
        '"nested":{"items":["@i64:0","@@@prefix"]}}\n'
    ).encode()
    assert frame == expected
    assert metatrader.decode_frame(frame) == {
        **message,
        "nested": {"items": [0, "@@prefix"]},
    }


def test_native_unsigned_response() -> None:
    """Restore full unsigned IDs sent by the EA without float conversion."""
    assert metatrader.decode_frame(b'{"v":1,"value":"@u64:18446744073709551615"}') == {
        "v": 1,
        "value": 2**64 - 1,
    }


def test_frame_limit_boundary() -> None:
    """Retain the payload limit and the newline's existing separate accounting."""
    overhead = len(metatrader.encode_frame({"v": 1, "text": ""})) - 1
    message = {"v": 1, "text": "x" * (metatrader.MAX_FRAME_BYTES - overhead)}
    frame = metatrader.encode_frame(message)
    assert len(frame) == metatrader.MAX_FRAME_BYTES + 1
    assert metatrader.decode_frame(frame[:-1]) == message
    with pytest.raises(ValueError, match="frame too large"):
        metatrader.decode_frame(frame)
    message["text"] = str(message["text"]) + "x"
    with pytest.raises(ValueError, match="frame exceeds"):
        metatrader.encode_frame(message)


@pytest.mark.parametrize(
    ("data", "error", "match"),
    [
        (b"[]", ValueError, "JSON object"),
        (b"{}", ValueError, "unsupported protocol version"),
        (b'{"v":2}', ValueError, "unsupported protocol version"),
        (b"{", json.JSONDecodeError, "Expecting property name"),
        (b"\xff", UnicodeDecodeError, "invalid start byte"),
        (b'{"v":1,"value":"@i64:invalid"}', ValueError, "invalid literal"),
    ],
)
def test_invalid_incoming_frames(
    data: bytes, error: type[Exception], match: str
) -> None:
    """Reject malformed and incompatible messages with the existing errors."""
    with pytest.raises(error, match=match):
        metatrader.decode_frame(data)


@pytest.mark.parametrize("value", [float("nan"), float("inf"), -float("inf")])
def test_nonfinite_outgoing_values(value: float) -> None:
    """Reject non-finite floats instead of emitting non-standard JSON."""
    with pytest.raises(ValueError, match="Out of range float"):
        metatrader.encode_frame({"v": 1, "value": value})


def test_unsupported_outgoing_value() -> None:
    """Reject Python objects with no wire representation."""
    with pytest.raises(TypeError, match="unsupported wire value"):
        metatrader.encode_frame({"v": 1, "value": object()})


def test_codec_logs_are_redacted(monkeypatch: pytest.MonkeyPatch) -> None:
    """Log each attempt without leaking token or payload contents."""
    logger = Mock()
    monkeypatch.setattr(metatrader, "logger", logger)
    message: dict[str, Any] = {"v": 1, "token": "private-test-token"}
    frame = metatrader.encode_frame(message)
    metatrader.decode_frame(frame)
    with pytest.raises(ValueError, match="JSON object"):
        metatrader.decode_frame(b"[]")
    with pytest.raises(TypeError, match="unsupported wire value"):
        metatrader.encode_frame({"v": 1, "value": object()})
    assert logger.debug.call_count == 4
    metadata = [call.kwargs["extra"] for call in logger.debug.call_args_list]
    assert metadata == [
        {"operation": "encode"},
        {"operation": "decode", "frame_bytes": len(frame)},
        {"operation": "decode", "frame_bytes": 2},
        {"operation": "encode"},
    ]
    assert "private-test-token" not in repr(logger.mock_calls)
    assert "token" not in repr(logger.mock_calls)


def test_facade_proxy_wiring(tmp_path: Path) -> None:
    """Keep package exports and all native proxy bindings intact after the move."""
    assert Bridge is metatrader.Bridge
    assert MT5Backend is metatrader.MT5Backend
    mt5 = MT5Backend(
        auth_token="isolated-test-token",
        journal_path=tmp_path / "bridge.sqlite3",
    )
    try:
        proxies = (
            (mt5.trade, Trade),
            (mt5.account, AccountInfo),
            (mt5.symbol, SymbolInfo),
            (mt5.order, OrderInfo),
            (mt5.history_order, HistoryOrderInfo),
            (mt5.position, PositionInfo),
            (mt5.deal, DealInfo),
            (mt5.terminal, TerminalInfo),
        )
        for proxy, expected_type in proxies:
            assert isinstance(proxy, expected_type)
            assert proxy.backend is mt5
        assert len({proxy.object_id for proxy, _ in proxies}) == len(proxies)
        assert not mt5.bridge.connected
        assert not mt5.bridge.armed
    finally:
        asyncio.run(mt5.close())


@pytest.mark.parametrize("backend_type", [Bridge, MT5Backend])
def test_native_backend_default_journal_path(
    backend_type: type[Bridge | MT5Backend],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Both entry points select shared storage independently of the working directory."""
    monkeypatch.chdir(tmp_path)
    journal = Mock()
    factory = Mock(return_value=journal)
    monkeypatch.setattr(metatrader, "Journal", factory)
    backend = backend_type(auth_token="isolated-test-token")
    try:
        factory.assert_called_once_with(DEFAULT_DATABASE_PATH)
    finally:
        asyncio.run(backend.close())
    journal.close.assert_called_once()
    assert list(tmp_path.iterdir()) == []


def test_native_history_selection_precedes_deal_access() -> None:
    """Guard native wiring; this source check does not certify terminal execution."""
    root = Path(__file__).resolve().parents[3]
    source = (root / "scripts/mql5/Experts/PythonBridge.mq5").read_text(
        encoding="utf-8"
    )
    deal = source.split("void DispatchDeal(", 1)[1].split("void DispatchTerminal(", 1)[
        0
    ]
    ticket = deal.split('if(method=="Ticket")', 1)[1].split(
        'if(method=="SelectByIndex")', 1
    )[0]
    assert "bool selected=HistoryDealSelect(ticket);" in ticket
    assert "obj.Ticket(selected ? ticket : 0);" in ticket
    assert ticket.index("HistoryDealSelect(ticket)") < ticket.index(
        "obj.Ticket(selected"
    )
    assert "RespondBool(command_id,true,selected);" in ticket
    history = source.split("void DispatchHistory(", 1)[1].split(
        "void DispatchPosition(", 1
    )[0]
    for dispatcher in (deal, history):
        index = dispatcher.split('if(method=="SelectByIndex")', 1)[1]
        assert index.index("HistorySelect(0,TimeCurrent())") < index.index(
            "obj.SelectByIndex"
        )
        assert "if(selected) selected=obj.SelectByIndex" in index


def test_native_market_data_bounds_and_integer_framing() -> None:
    """Guard bounded native copy wiring without claiming live-data certification."""
    root = Path(__file__).resolve().parents[3]
    source = (root / "scripts/mql5/Experts/PythonBridge.mq5").read_text(
        encoding="utf-8"
    )
    dispatch = source.split("void DispatchMarketData(", 1)[1].split(
        "void ProcessCall(", 1
    )[0]
    assert "capacity>1000" in dispatch
    assert "MathCeil((double)(end-start)/period)+1>limit" in dispatch
    assert "CopyRates(symbol,timeframe,(datetime)start,(datetime)end,rates)" in dispatch
    assert "(uint)(range ? limit+1 : requested_count)" in dispatch
    assert "ticks[i].time_msc<start || ticks[i].time_msc>end" in dispatch
    assert "JsonLong(ticks[i].time_msc)" in dispatch
    assert "JsonULong(ticks[i].volume)" in dispatch
    assert "DATA_LIMIT_EXCEEDED" in dispatch
    assert 'class_name=="MarketData"' in source


def test_native_bar_count_uses_forward_index_selection() -> None:
    """Guard date-to-index conversion so native date/count cannot count backwards."""
    root = Path(__file__).resolve().parents[3]
    source = (root / "scripts/mql5/Experts/PythonBridge.mq5").read_text(
        encoding="utf-8"
    )
    dispatch = source.split("void DispatchMarketData(", 1)[1].split(
        "void ProcessCall(", 1
    )[0]
    assert "iBarShift(symbol,timeframe,(datetime)start,false)" in dispatch
    assert "if(iTime(symbol,timeframe,oldest)<(datetime)start) oldest--;" in dispatch
    assert "oldest-available+1" in dispatch
    assert "CopyRates(symbol,timeframe,(int)start,requested_count,rates)" in dispatch
    assert "CopyRates(symbol,timeframe,first,available,rates)" in dispatch


def test_native_reconnect_logs_suppress_identical_failures() -> None:
    """Guard quiet default, error capture/reset and independent retry scheduling."""
    root = Path(__file__).resolve().parents[3]
    source = (root / "scripts/mql5/Experts/PythonBridge.mq5").read_text(
        encoding="utf-8"
    )
    assert "input bool   InpVerboseReconnectLogs = false;" in source
    assert "int    g_last_connect_error = -1;" in source
    connect = source.split("bool ConnectBridge()", 1)[1].split(
        "bool AcquireTerminalLock()", 1
    )[0]
    assert connect.count("const int error=GetLastError();") == 2
    assert (
        connect.count("if(InpVerboseReconnectLogs || error!=g_last_connect_error)") == 2
    )
    assert connect.count("g_last_connect_error=error;") == 2
    assert connect.index("g_last_connect_error=-1;") > connect.index(
        "if(!SendJson(hello))"
    )
    assert connect.index("g_last_connect_error=-1;") < connect.index(
        'Print("PythonBridge: connected to "'
    )
    timer = source.split("void OnTimer()", 1)[1].split("void OnTradeTransaction(", 1)[0]
    assert "now-g_last_connect_try>=InpReconnectMs" in timer
    assert "g_last_connect_try=now;" in timer
    assert "ConnectBridge();" in timer
    assert "InpVerboseReconnectLogs" not in timer
    assert "g_last_connect_error" not in timer


def test_connection_example_displays_observed_receipt(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Read an actual local probe and expose its matching resolved receipt."""
    backend = brokers.create_backend("simulator")
    ctx = brokers.ExampleContext(brokers.Trading(backend))

    async def scenario() -> None:
        try:
            await brokers.example_01_connect(ctx)
            command = ctx.trading.terminal.last_command_id
            assert command is not None
            receipt = ctx.trading.receipt(command)
            assert receipt is not None and receipt.status == ReceiptStatus.RESOLVED
            assert receipt.value is True
        finally:
            await brokers.example_17_shutdown(ctx)

    asyncio.run(scenario())
    output = capsys.readouterr().out
    assert "Command ID" in output and "Terminal connected" in output
    assert "TerminalInfo.IsConnected" in output
    assert "Acknowledged at" in output
    assert "Resolved at" in output


@pytest.mark.parametrize(
    "mismatch",
    [
        "missing",
        "status",
        "command",
        "object",
        "class",
        "method",
        "value",
        "error",
        "sent",
        "acknowledged",
        "resolved",
        "nan_timestamp",
        "boolean_timestamp",
        "string_timestamp",
    ],
)
def test_connection_example_rejects_invalid_receipt(
    mismatch: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Missing or mismatched evidence cannot become a passed connection example."""
    backend = brokers.create_backend("simulator")
    ctx = brokers.ExampleContext(brokers.Trading(backend))
    original_receipt = backend.receipt

    def altered_receipt(command_id: str) -> Receipt | None:
        receipt = original_receipt(command_id)
        assert receipt is not None
        if mismatch == "missing":
            return None
        changes: dict[str, Any] = {
            "status": {"status": ReceiptStatus.CREATED},
            "command": {"command_id": "different-command"},
            "object": {"object_id": "different-object"},
            "class": {"class_name": "Trade"},
            "method": {"method_name": "Buy"},
            "value": {"value": False},
            "error": {"error": {"message": "private-message"}},
            "sent": {"sent_at": None},
            "acknowledged": {"acknowledged_at": None},
            "resolved": {"resolved_at": None},
            "nan_timestamp": {"acknowledged_at": float("nan")},
            "boolean_timestamp": {"sent_at": False},
            "string_timestamp": {"resolved_at": "private-value"},
        }[mismatch]
        return replace(receipt, **changes)

    monkeypatch.setattr(backend, "receipt", altered_receipt)

    async def scenario() -> None:
        try:
            with pytest.raises(brokers.ExampleError, match="missing or mismatched"):
                await brokers.example_01_connect(ctx)
            assert ctx.results == []
        finally:
            await brokers.example_17_shutdown(ctx)

    asyncio.run(scenario())


@pytest.mark.parametrize("probe_value", [False, 1])
def test_connection_example_rejects_false_or_nonboolean_probe(
    probe_value: bool | int,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A resolved response must be a genuine True boolean, not truthy data."""
    backend = brokers.create_backend("simulator")
    ctx = brokers.ExampleContext(brokers.Trading(backend))
    original_probe = ctx.trading.terminal.IsConnected

    async def probe() -> bool | int:
        await original_probe()
        command = ctx.trading.terminal.last_command_id
        assert command is not None
        receipt = backend.receipt(command)
        assert receipt is not None
        backend._receipts[command] = replace(receipt, value=probe_value)
        return probe_value

    monkeypatch.setattr(ctx.trading.terminal, "IsConnected", probe)

    async def scenario() -> None:
        try:
            with pytest.raises(brokers.ExampleError):
                await brokers.example_01_connect(ctx)
            assert ctx.results == []
        finally:
            await brokers.example_17_shutdown(ctx)

    asyncio.run(scenario())


def test_connection_example_timeout_closes_backend(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The runner closes on readiness failure without issuing a success/probe."""
    backend = brokers.create_backend("simulator")
    trading = brokers.Trading(backend)
    close = AsyncMock(wraps=trading.close)
    probe = AsyncMock()
    monkeypatch.setattr(trading, "close", close)
    monkeypatch.setattr(trading, "wait_connected", AsyncMock(side_effect=TimeoutError))
    monkeypatch.setattr(trading.terminal, "IsConnected", probe)
    monkeypatch.setattr(brokers, "Trading", Mock(return_value=trading))
    with pytest.raises(TimeoutError):
        asyncio.run(brokers.run_examples(backend))
    close.assert_awaited_once()
    probe.assert_not_awaited()


@pytest.mark.parametrize("valid_token", [True, False])
def test_hello_ack_and_correlated_probe_without_listener(
    valid_token: bool,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Exercise real handshake/framing/receipts through isolated in-memory streams."""

    async def scenario() -> None:
        native = MT5Backend(
            auth_token="isolated-test-token", journal_path=tmp_path / "handshake.db"
        )
        monkeypatch.setattr(native, "start", AsyncMock())
        reader = asyncio.StreamReader()
        writer = Mock()
        writer.get_extra_info.return_value = ("127.0.0.1", 12345)
        writer.is_closing.return_value = False
        writer.drain = AsyncMock()
        writer.wait_closed = AsyncMock()
        frames: list[dict[str, Any]] = []

        def write(data: bytes) -> None:
            frame = metatrader.decode_frame(data)
            frames.append(frame)
            if frame["kind"] == "call":
                reader.feed_data(
                    metatrader.encode_frame(
                        {
                            "v": 1,
                            "kind": "response",
                            "command_id": frame["command_id"],
                            "ok": True,
                            "value": True,
                        }
                    )
                )

        writer.write.side_effect = write
        reader.feed_data(
            metatrader.encode_frame(
                {
                    "v": 1,
                    "kind": "hello",
                    "token": "isolated-test-token"
                    if valid_token
                    else "wrong-test-token",
                }
            )
        )
        accepted = asyncio.create_task(
            native.bridge._accept(reader, cast("asyncio.StreamWriter", writer))
        )
        ctx = brokers.ExampleContext(brokers.Trading(native))
        try:
            if valid_token:
                await asyncio.wait_for(brokers.example_01_connect(ctx), timeout=1)
                assert native.bridge.connected
                assert [frame["kind"] for frame in frames] == ["hello_ack", "call"]
                assert frames[1]["class"] == "TerminalInfo"
                assert frames[1]["method"] == "IsConnected"
                receipt = native.receipt(frames[1]["command_id"])
                assert receipt is not None and receipt.status == ReceiptStatus.RESOLVED
            else:
                await asyncio.wait_for(accepted, timeout=1)
                with pytest.raises(TimeoutError):
                    await native.wait_connected(timeout=0.01)
                assert not native.bridge.connected
                assert frames[0]["code"] == "AUTH_FAILED"
                assert not any(frame["kind"] == "call" for frame in frames)
        finally:
            reader.feed_eof()
            await asyncio.wait_for(accepted, timeout=1)
            await native.close()

    asyncio.run(scenario())


def test_connection_evidence_preserves_complete_simulation_walkthrough(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Run all examples through actual model operations with observed first evidence."""
    examples = tuple(
        getattr(brokers, name)
        for name in (
            "example_01_connect",
            "example_02_terminal",
            "example_03_account",
            "example_04_symbol",
            "example_05_position",
            "example_06_order",
            "example_07_history_order",
            "example_08_history_deal",
            "example_09_open_position",
            "example_10_calc_profit_margin",
            "example_11_modify_position",
            "example_12_close_partial_position",
            "example_13_close_position",
            "example_14_pending_orders",
            "example_15_modify_pending_orders",
            "example_16_delete_pending_orders",
            "example_18_historical_bars",
            "example_19_tick_data",
        )
    )
    monkeypatch.setattr(brokers, "EXAMPLES", examples)
    backend = brokers.create_backend("simulator")
    results = asyncio.run(brokers.run_examples(backend, allow_writes=True))
    assert results == []
    assert backend.positions() == [] and backend.orders() == []


def test_terminal_info_extended_properties_parity() -> None:
    """Verify new TerminalInfo properties resolve on simulator."""
    sim = SimulationBackend()
    trading = Trading(sim)
    terminal = trading.terminal

    async def scenario() -> None:
        assert await terminal.CommunityAccount() is False
        assert await terminal.CommunityConnection() is False
        assert await terminal.TradeAPIDisabled() is False
        assert await terminal.NotificationsEnabled() is False
        assert await terminal.MQID() is False
        assert await terminal.PingLast() == 0
        assert await terminal.CommunityBalance() == 0.0
        assert await terminal.Retransmission() == 0.0

    asyncio.run(scenario())


def test_account_info_extended_properties_parity() -> None:
    """Verify new AccountInfo properties resolve on simulator."""
    sim = SimulationBackend()
    trading = Trading(sim)
    account = trading.account

    async def scenario() -> None:
        assert await account.CurrencyDigits() == 2
        assert await account.FifoClose() is False
        assert await account.MarginInitial() == 0.0
        assert await account.MarginMaintenance() == 0.0
        assert await account.Assets() == 0.0
        assert await account.Liabilities() == 0.0
        assert await account.CommissionBlocked() == 0.0

    asyncio.run(scenario())


def test_symbol_info_extended_properties_and_search_parity() -> None:
    """Verify SymbolsTotal, SymbolsGet, and extended SymbolInfo properties on simulator."""
    sim = SimulationBackend()
    sim.add_symbol(SymbolSpec(name="EURUSD", selected=True))
    sim.add_symbol(SymbolSpec(name="USDRUB", selected=False))
    sim.add_symbol(SymbolSpec(name="XAUUSD", selected=True))
    sim.add_symbol(SymbolSpec(name="BTCUSD", selected=False))
    trading = Trading(sim)
    symbol = trading.symbol

    async def scenario() -> None:
        await symbol.Name("EURUSD")
        # 1. SymbolsTotal
        assert await symbol.SymbolsTotal(False) == 4
        assert await symbol.SymbolsTotal(True) == 2

        # 2. SymbolsGet
        all_syms = await symbol.SymbolsGet()
        assert set(all_syms) == {"EURUSD", "USDRUB", "XAUUSD", "BTCUSD"}
        rub_syms = await symbol.SymbolsGet("*RUB*")
        assert rub_syms == ["USDRUB"]
        no_majors = await symbol.SymbolsGet("*,!*USD*,!*EUR*,!*JPY*,!*GBP*")
        assert no_majors == []

        # 3. Extended Properties
        assert await symbol.Custom() is False
        assert await symbol.ChartMode() == 0
        assert await symbol.Visible() is True
        assert await symbol.MarginHedged() == 0.0
        assert await symbol.PriceChange() == 0.0

        # 4. as_dict
        d = await symbol.as_dict()
        assert isinstance(d, dict)
        assert len(d) == 96
        assert d["name"] == "EURUSD"
        assert d["digits"] == 5
        assert d["select"] is True
        assert d["custom"] is False

        # 5. SymbolSelect
        assert await symbol.SymbolSelect("USDRUB", True) is True
        assert await symbol.SymbolsTotal(True) == 3
        assert await symbol.SymbolSelect("USDRUB", False) is True
        assert await symbol.SymbolsTotal(True) == 2

        # 6. SymbolInfoTick
        sim.feed_tick(
            "EURUSD",
            bid=1.0950,
            ask=1.0952,
            time=datetime(2026, 10, 12, 12, 0, 0, tzinfo=UTC),
        )
        tick = await symbol.SymbolInfoTick("EURUSD")
        assert tick is not None
        assert tick["bid"] == 1.0950
        assert tick["ask"] == 1.0952
        assert tick["flags"] == 6

        # Unseeded tick returns None
        assert await symbol.SymbolInfoTick("BTCUSD") is None

    asyncio.run(scenario())
