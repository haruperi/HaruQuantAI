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
from pathlib import Path
from typing import Any
from unittest.mock import Mock

import pytest
from app.host.persistence.engine import DEFAULT_DATABASE_PATH
from app.services.brokers import metatrader
from app.services.brokers.metatrader import Bridge, MT5Backend
from app.services.trading import (
    AccountInfo,
    DealInfo,
    HistoryOrderInfo,
    OrderInfo,
    PositionInfo,
    SymbolInfo,
    TerminalInfo,
    Trade,
)


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
