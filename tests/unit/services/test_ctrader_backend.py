"""Unit tests for the cTrader Open API trading backend.

Description:
    Verifies the asynchronous TradingBackend lifecycle, protocol conformity,
    receipt generation, arm/disarm execution gates, fail-closed unauthenticated
    hard failures, and trading facade dispatch for CTraderBackend in
    app.services.brokers.ctrader.

Purpose:
    FEAT-BROKER-CTRADER: cTrader Open API Protocol Buffer Integration.

Key Capabilities:
    - FR-BROKER-CTRADER-BACKEND-TESTS: Verify backend protocol, arming, and receipts.
      Associated: `[CTraderBackend.call()]`, `[CTraderBackend.arm()]`, `[CTraderBackend.receipt()]`
      Logging: Validates that operations record receipts and respect arming gates.
    - FR-BROKER-CTRADER-FAIL-CLOSED: Verify fail-closed hard failures without credentials.
      Associated: `[CTraderClient]`, `[CTraderBackend]`
      Logging: Validates that unauthenticated operations raise BridgeError(code="NOT_AUTHENTICATED").

Python API Usage:
    ```python
    uv run pytest tests/unit/services/test_ctrader_backend.py --no-cov
    ```

CLI Usage:
    ```bash
    uv run pytest tests/unit/services/test_ctrader_backend.py --no-cov
    ```
"""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from app.services.brokers.contracts import (
    AccountSnapshot,
    BridgeError,
    ReceiptStatus,
    SymbolSnapshot,
    TradeAction,
    TradeRequest,
    TradeResult,
)
from app.services.brokers.ctrader import (
    DEFAULT_GATEWAY_PORT,
    CTraderBackend,
)
from app.services.libs.trading import Trading


def test_ctrader_backend_initialization() -> None:
    """CTraderBackend initializes with parameters and implements TradingBackend."""
    backend = CTraderBackend(
        client_id="test_client",
        client_secret="test_secret",
        access_token="test_token",
        account_id=1234567,
        gateway_host="demo.ctraderapi.com",
        gateway_port=DEFAULT_GATEWAY_PORT,
        environment="demo",
        command_timeout=5.0,
    )
    assert hasattr(backend, "start")
    assert hasattr(backend, "call")
    assert hasattr(backend, "arm")
    assert hasattr(backend, "disarm")
    assert hasattr(backend, "last_command_id")
    assert hasattr(backend, "receipt")
    assert isinstance(backend, Trading)
    assert backend.client.client_id == "test_client"
    assert backend.client.account_id == 1234567
    assert backend.client.environment == "demo"
    assert backend.last_command_id() is None


def test_ctrader_fail_closed_unauthenticated() -> None:
    """CTraderClient hard-fails with NOT_AUTHENTICATED on all query/mutation endpoints."""
    backend = CTraderBackend(account_id=12345)
    client = backend.client

    assert not client.is_connected

    with pytest.raises(BridgeError) as exc:
        client.account_info()
    assert exc.value.code == "NOT_AUTHENTICATED"

    with pytest.raises(BridgeError) as exc:
        client.symbols_list()
    assert exc.value.code == "NOT_AUTHENTICATED"

    with pytest.raises(BridgeError) as exc:
        client.symbol_info("EURUSD")
    assert exc.value.code == "NOT_AUTHENTICATED"

    with pytest.raises(BridgeError) as exc:
        client.trendbars("EURUSD", "PERIOD_M1")
    assert exc.value.code == "NOT_AUTHENTICATED"

    with pytest.raises(BridgeError) as exc:
        client.reconcile()
    assert exc.value.code == "NOT_AUTHENTICATED"

    with pytest.raises(BridgeError) as exc:
        client.order_send(TradeRequest(action=TradeAction.DEAL, symbol="EURUSD"))
    assert exc.value.code == "NOT_AUTHENTICATED"


@pytest.mark.anyio
async def test_ctrader_backend_fail_closed_lifecycle() -> None:
    """CTraderBackend fails closed when starting without network/credentials."""
    backend = CTraderBackend(account_id=12345)

    with patch.object(
        backend.client,
        "connect",
        side_effect=BridgeError("Connection failed", code="CONNECT_FAILED"),
    ):
        with pytest.raises(BridgeError) as exc_start:
            await backend.start()
        assert exc_start.value.code == "CONNECT_FAILED"

    with pytest.raises(BridgeError) as exc_wait:
        await backend.wait_connected()
    assert exc_wait.value.code in {"NOT_CONNECTED", "CONNECT_FAILED"}


@pytest.mark.anyio
async def test_ctrader_backend_authenticated_lifecycle() -> None:
    """CTraderBackend async context manager starts and closes cleanly when authenticated."""
    backend = CTraderBackend(account_id=12345)

    def mock_connect() -> None:
        backend.client._sock = MagicMock()
        backend.client._authenticated = True

    with patch.object(backend.client, "connect", side_effect=mock_connect):
        async with backend:
            await backend.wait_connected()
            assert backend.client.is_connected
    assert not backend.client.is_connected


@pytest.mark.anyio
async def test_ctrader_backend_arming_gate() -> None:
    """CTraderBackend enforces arming for mutating trade calls."""
    backend = CTraderBackend(account_id=12345)

    with pytest.raises(BridgeError) as exc_info:
        await backend.call(
            object_id="trade_1",
            class_name="Trade",
            method_name="OrderSend",
            args=[{}],
            requires_arm=True,
        )
    assert exc_info.value.code == "NOT_ARMED"

    backend.arm()

    mock_order_res = TradeResult(retcode=10009, deal=101, order=202)
    with patch.object(backend.client, "order_send", return_value=mock_order_res):
        req = TradeRequest(action=TradeAction.DEAL, symbol="EURUSD", volume=0.01)
        res = await backend.call(
            object_id="trade_1",
            class_name="Trade",
            method_name="OrderSend",
            args=[req],
            requires_arm=True,
        )
        assert res["retcode"] == 10009
        cmd_id = backend.last_command_id()
        assert cmd_id is not None
        rcpt = backend.receipt(cmd_id)
        assert rcpt is not None
        assert rcpt.status == ReceiptStatus.RESOLVED

    backend.disarm()
    with pytest.raises(BridgeError) as exc_info2:
        await backend.call(
            object_id="trade_1",
            class_name="Trade",
            method_name="OrderSend",
            args=[{}],
            requires_arm=True,
        )
    assert exc_info2.value.code == "NOT_ARMED"


@pytest.mark.anyio
async def test_ctrader_backend_facade_dispatch() -> None:
    """CTraderBackend correctly resolves facade queries across categories."""
    backend = CTraderBackend(account_id=98765)
    trading = Trading(backend)

    # 1. Terminal
    term_snap = await trading.terminal.TerminalInfo()
    assert term_snap.name == "cTrader"
    assert not term_snap.connected

    # 2. Account
    mock_acc = AccountSnapshot(
        login=98765,
        balance=50_000.0,
        equity=50_000.0,
        currency="USD",
        server="cTrader-Demo",
        company="Spotware",
    )
    with patch.object(backend.client, "account_info", return_value=mock_acc):
        acc_snap = await trading.account.AccountInfo()
        assert acc_snap.balance == 50_000.0
        assert acc_snap.login == 98765

    # 3. Symbol
    mock_sym = SymbolSnapshot(
        name="EURUSD",
        digits=5,
        point=0.00001,
        bid=1.08500,
        ask=1.08510,
    )
    with patch.object(backend.client, "symbol_info", return_value=mock_sym):
        sym_snap = await trading.symbol.SymbolInfo("EURUSD")
        assert sym_snap.point == 0.00001
        assert sym_snap.bid == 1.08500

    # 4. Market Book
    with patch.object(backend.client, "symbol_info", return_value=mock_sym):
        add_ok = await trading.symbol.MarketBookAdd("EURUSD")
        assert add_ok
        book = await trading.symbol.MarketBookGet("EURUSD")
        assert len(book) == 5
        rel_ok = await trading.symbol.MarketBookRelease("EURUSD")
        assert rel_ok

    # 5. Order Check fails when disconnected
    with pytest.raises(BridgeError) as exc_chk:
        await backend.call(
            object_id="trade",
            class_name="Trade",
            method_name="OrderCheck",
            args=[TradeRequest(action=TradeAction.DEAL, symbol="EURUSD", volume=0.05)],
        )
    assert exc_chk.value.code == "NOT_AUTHENTICATED"

    # 6. Order Check succeeds when connected
    backend.client._sock = MagicMock()
    backend.client._authenticated = True
    with patch.object(backend.client, "account_info", return_value=mock_acc):
        chk_res = await backend.call(
            object_id="trade",
            class_name="Trade",
            method_name="OrderCheck",
            args=[TradeRequest(action=TradeAction.DEAL, symbol="EURUSD", volume=0.05)],
        )
        assert chk_res["retcode"] == 10009
        assert chk_res["balance"] == 50_000.0


@pytest.mark.anyio
async def test_ctrader_backend_market_data_bars_and_ticks() -> None:
    """CTraderBackend formats historical trendbars and ticks for MarketData helpers."""
    backend = CTraderBackend(account_id=123)

    mock_trendbars = [
        {
            "time": 1700000000,
            "open": 1.0800,
            "high": 1.0850,
            "low": 1.0790,
            "close": 1.0840,
            "tick_volume": 120,
            "spread": 10,
            "real_volume": 0,
        }
    ]
    with patch.object(
        backend.client, "trendbars", return_value=mock_trendbars
    ) as fetch_bars:
        bars = await backend.call(
            object_id="market-data",
            class_name="MarketData",
            method_name="Bars",
            args=["EURUSD", "PERIOD_M1", 1700000000, 1700003600],
        )
        assert len(bars) == 1
        assert bars[0]["open"] == 1.0800
        assert bars[0]["close"] == 1.0840
        fetch_bars.assert_called_once_with(
            "EURUSD", "PERIOD_M1", count=100, start_sec=1700000000, end_sec=1700003600
        )

    with patch.object(
        backend.client, "historical_ticks", return_value=[{"bid": 1.08500}]
    ) as fetch_ticks:
        ticks = await backend.call(
            object_id="market-data",
            class_name="MarketData",
            method_name="Ticks",
            args=["EURUSD", 1700000000, 1700003600],
        )
        assert len(ticks) == 1
        assert ticks[0]["bid"] == 1.08500
        fetch_ticks.assert_called_once_with("EURUSD", 1700000000, 1700003600, 3)


@pytest.fixture
def auth_client(monkeypatch: pytest.MonkeyPatch) -> Any:
    """Isolate all credentials and network operations from real settings."""
    from types import SimpleNamespace

    from app.services.brokers import ctrader

    for name in (
        "CLIENT_ID",
        "CLIENT_SECRET",
        "ACCESS_TOKEN",
        "REFRESH_TOKEN",
        "ACCOUNT_ID",
        "ENVIRONMENT",
        "GATEWAY_HOST",
        "GATEWAY_PORT",
    ):
        monkeypatch.delenv(f"CTRADER_{name}", raising=False)
    host = MagicMock()
    host.config_ctrader = SimpleNamespace(
        client_id="client",
        client_secret="secret",
        access_token="old-access",
        refresh_token="old-refresh",
        account_id="42",
        environment="demo",
        gateway_host="",
        gateway_port=5035,
    )
    host.get_snapshot.return_value = SimpleNamespace(
        revision=5,
        values={"application": {"config_ctrader": vars(host.config_ctrader).copy()}},
    )
    monkeypatch.setattr(ctrader, "settings", host)
    client = ctrader.CTraderClient()
    return client, host


def _auth_response(message: Any) -> tuple[int, bytes]:
    return message.payloadType, message.SerializeToString()


def _account_list(*, account_id: int = 42, login: int = 123, live: bool = False) -> Any:
    from app.services.brokers.ctrader import oamsg

    result = oamsg.ProtoOAGetAccountListByAccessTokenRes(accessToken="old-access")
    result.ctidTraderAccount.add(
        ctidTraderAccountId=account_id, traderLogin=login, isLive=live
    )
    return result


def test_ctrader_config_precedence(
    auth_client: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    from app.services.brokers.ctrader import CTraderBackend

    _, host = auth_client
    host.config_ctrader.environment = "live"
    host.config_ctrader.gateway_port = 5040
    client = CTraderBackend().client
    assert client.environment == "live"
    assert client.gateway_host == "live.ctraderapi.com"
    assert client.gateway_port == 5040
    monkeypatch.setenv("CTRADER_ENVIRONMENT", "demo")
    monkeypatch.setenv("CTRADER_GATEWAY_PORT", "5050")
    assert CTraderBackend().client.environment == "demo"
    assert CTraderBackend().client.gateway_port == 5050
    explicit = CTraderBackend(environment="live", gateway_port=5035).client
    assert explicit.environment == "live"
    assert explicit.gateway_port == 5035


@pytest.mark.parametrize(
    ("attribute", "value", "code"),
    [
        ("environment", "unknown", "CTRADER_CONFIG_INVALID"),
        ("gateway_host", "live.ctraderapi.com", "CTRADER_ENVIRONMENT_MISMATCH"),
        ("gateway_port", 0, "CTRADER_CONFIG_INVALID"),
        ("account_id", 0, "CTRADER_CONFIG_INVALID"),
        ("command_timeout", 0, "CTRADER_CONFIG_INVALID"),
        ("access_token", "", "AUTH_FAILED"),
        ("client_secret", "", "AUTH_FAILED"),
    ],
)
def test_ctrader_invalid_config_never_opens_socket(
    auth_client: Any, attribute: Any, value: Any, code: Any
) -> None:
    client, _ = auth_client
    setattr(client, attribute, value)
    with patch("app.services.brokers.ctrader.socket.socket") as socket_factory:
        with pytest.raises(BridgeError) as caught:
            client.connect()
        assert caught.value.code == code
        socket_factory.assert_not_called()


def test_ctrader_account_auth_uses_api_id(auth_client: Any) -> None:
    from app.services.brokers.ctrader import oamsg

    client, _ = auth_client
    with (
        patch.object(client, "_send_msg", return_value=True) as send,
        patch.object(
            client,
            "_recv_msg",
            side_effect=[
                _auth_response(_account_list()),
                _auth_response(oamsg.ProtoOAAccountAuthRes(ctidTraderAccountId=42)),
            ],
        ),
    ):
        client._auth_account()
    assert client._authenticated
    request = oamsg.ProtoOAAccountAuthReq()
    request.ParseFromString(send.call_args_list[-1].args[1])
    assert request.ctidTraderAccountId == 42


@pytest.mark.parametrize(
    ("account_id", "live", "code"),
    [
        (123, False, "CTRADER_ACCOUNT_ID_IS_LOGIN"),
        (99, False, "CTRADER_ACCOUNT_NOT_AUTHORIZED"),
        (42, True, "CTRADER_ENVIRONMENT_MISMATCH"),
    ],
)
def test_ctrader_invalid_account_never_sends_account_auth(
    auth_client: Any, account_id: Any, live: Any, code: Any
) -> None:
    client, _ = auth_client
    client.account_id = account_id
    with (
        patch.object(client, "_send_msg", return_value=True) as send,
        patch.object(
            client,
            "_recv_msg",
            return_value=_auth_response(_account_list(live=live)),
        ),
    ):
        with pytest.raises(BridgeError) as caught:
            client._auth_account()
    assert caught.value.code == code
    assert send.call_count == 1
    assert not client._authenticated
    if account_id == 123:
        assert "ctidTraderAccountId=42" in str(caught.value)


def test_ctrader_refresh_once_and_persist_pair(auth_client: Any) -> None:
    from app.services.brokers.ctrader import oamsg

    client, host = auth_client
    rejected = oamsg.ProtoOAErrorRes(
        errorCode="CH_ACCESS_TOKEN_INVALID", description="SECRET-DO-NOT-LOG"
    )
    refreshed = oamsg.ProtoOARefreshTokenRes(
        accessToken="new-access",
        refreshToken="new-refresh",
        tokenType="bearer",
        expiresIn=3600,
    )
    with (
        patch.object(client, "_send_msg", return_value=True) as send,
        patch.object(
            client,
            "_recv_msg",
            side_effect=[
                _auth_response(rejected),
                _auth_response(refreshed),
                _auth_response(_account_list()),
                _auth_response(oamsg.ProtoOAAccountAuthRes(ctidTraderAccountId=42)),
            ],
        ),
    ):
        client._auth_account()
    host.update.assert_called_once_with(
        {
            "config_ctrader": {
                "access_token": "new-access",
                "refresh_token": "new-refresh",
            }
        },
        expected_revision=5,
    )
    assert client.access_token == "new-access"
    assert client.refresh_token == "new-refresh"
    assert send.call_count == 4
    request = oamsg.ProtoOAGetAccountListByAccessTokenReq()
    request.ParseFromString(send.call_args_list[2].args[1])
    assert request.accessToken == "new-access"


@pytest.mark.parametrize(
    "failure", ["no-refresh", "refresh-rejected", "retry-rejected"]
)
def test_ctrader_refresh_failure_is_bounded(auth_client: Any, failure: Any) -> None:
    from app.services.brokers.ctrader import oamsg

    client, host = auth_client
    rejection = _auth_response(
        oamsg.ProtoOAErrorRes(
            errorCode="CH_ACCESS_TOKEN_INVALID", description="SECRET-DO-NOT-LOG"
        )
    )
    responses = [rejection]
    if failure == "no-refresh":
        client.refresh_token = ""
    elif failure == "refresh-rejected":
        responses.append(rejection)
    else:
        responses.extend(
            [
                _auth_response(
                    oamsg.ProtoOARefreshTokenRes(
                        accessToken="new-access",
                        refreshToken="new-refresh",
                        tokenType="bearer",
                        expiresIn=3600,
                    )
                ),
                rejection,
            ]
        )
    with (
        patch.object(client, "_send_msg", return_value=True) as send,
        patch.object(
            client,
            "_recv_msg",
            side_effect=responses,
        ),
    ):
        with pytest.raises(BridgeError) as caught:
            client._authorized_accounts()
    assert caught.value.code == "CTRADER_REAUTHORIZE_REQUIRED"
    assert "SECRET" not in str(caught.value)
    assert send.call_count == len(responses)
    if failure != "retry-rejected":
        host.update.assert_not_called()


@pytest.mark.parametrize("failure", ["source-changed", "save-conflict"])
def test_ctrader_refresh_persistence_conflicts(auth_client: Any, failure: Any) -> None:
    from app.services.brokers.ctrader import oamsg

    client, host = auth_client
    if failure == "source-changed":
        host.get_snapshot.return_value.values["application"]["config_ctrader"][
            "access_token"
        ] = "other"
    else:
        host.update.side_effect = RuntimeError("SECRET-SAVE-ERROR")
    with (
        patch.object(client, "_send_msg", return_value=True) as send,
        patch.object(
            client,
            "_recv_msg",
            return_value=_auth_response(
                oamsg.ProtoOARefreshTokenRes(
                    accessToken="new-access",
                    refreshToken="new-refresh",
                    tokenType="bearer",
                    expiresIn=3600,
                )
            ),
        ),
    ):
        with pytest.raises(BridgeError) as caught:
            client._refresh_access_token()
    assert caught.value.code == "CTRADER_TOKEN_PERSIST_FAILED"
    assert "SECRET" not in str(caught.value)
    if failure == "source-changed":
        send.assert_not_called()
    else:
        assert client.refresh_token == "new-refresh"


def test_ctrader_explicit_tokens_are_caller_owned(auth_client: Any) -> None:
    from app.services.brokers.ctrader import CTraderClient, oamsg

    _, host = auth_client
    client = CTraderClient(access_token="explicit", refresh_token="explicit-refresh")
    with (
        patch.object(client, "_send_msg", return_value=True),
        patch.object(
            client,
            "_recv_msg",
            return_value=_auth_response(
                oamsg.ProtoOARefreshTokenRes(
                    accessToken="new-access",
                    refreshToken="new-refresh",
                    tokenType="bearer",
                    expiresIn=3600,
                )
            ),
        ),
    ):
        client._refresh_access_token()
    host.get_snapshot.assert_not_called()
    host.update.assert_not_called()
    assert client.refresh_token == "new-refresh"


def test_ctrader_auth_heartbeat_and_unrelated_response(auth_client: Any) -> None:
    from app.services.brokers.ctrader import commonmsg, oamsg

    client, _ = auth_client
    with (
        patch.object(client, "_send_msg", return_value=True) as send,
        patch.object(
            client,
            "_recv_msg",
            side_effect=[
                _auth_response(commonmsg.ProtoHeartbeatEvent()),
                (9999, b""),
                _auth_response(oamsg.ProtoOAApplicationAuthRes()),
            ],
        ),
    ):
        client._auth_application()
    assert client._app_authorized
    assert send.call_count == 2


@pytest.mark.parametrize(
    "failure", ["timeout", "malformed", "incomplete", "disconnect", "unknown-error"]
)
def test_ctrader_auth_safe_failures(auth_client: Any, failure: Any) -> None:
    from app.services.brokers.ctrader import oamsg

    client, _ = auth_client
    responses = {
        "timeout": None,
        "malformed": (oamsg.ProtoOAAccountAuthRes().payloadType, b"\xff"),
        "incomplete": (oamsg.ProtoOAAccountAuthRes().payloadType, b""),
        "disconnect": _auth_response(oamsg.ProtoOAClientDisconnectEvent()),
        "unknown-error": _auth_response(oamsg.ProtoOAErrorRes(errorCode="SECRET")),
    }
    with (
        patch.object(client, "_send_msg", return_value=True),
        patch.object(
            client,
            "_recv_msg",
            return_value=responses[failure],
        ),
    ):
        with pytest.raises(BridgeError) as caught:
            client._auth_request(
                oamsg.ProtoOAAccountAuthReq(
                    ctidTraderAccountId=42, accessToken="token"
                ),
                oamsg.ProtoOAAccountAuthRes,
            )
    assert caught.value.code == {
        "timeout": "COMMAND_TIMEOUT",
        "disconnect": "CONNECTION_LOST",
    }.get(failure, "AUTH_FAILED")
    assert "SECRET" not in str(caught.value)


def test_ctrader_connect_cleans_up_failed_auth(auth_client: Any) -> None:
    client, _ = auth_client
    sock = MagicMock()
    with (
        patch("app.services.brokers.ctrader.socket.socket"),
        patch("app.services.brokers.ctrader.ssl.create_default_context") as context,
        patch.object(client, "_auth_application"),
        patch.object(
            client,
            "_auth_account",
            side_effect=BridgeError("Rejected", code="AUTH_FAILED"),
        ),
    ):
        context.return_value.wrap_socket.return_value = sock
        with pytest.raises(BridgeError):
            client.connect()
    sock.close.assert_called_once()
    assert client._sock is None
    assert not client.is_connected


def test_ctrader_fragmented_tls_frame(auth_client: Any) -> None:
    import struct

    from app.services.brokers.ctrader import commonmsg, oamsg

    client, _ = auth_client
    response = oamsg.ProtoOAApplicationAuthRes()
    frame = commonmsg.ProtoMessage(
        payloadType=response.payloadType, payload=response.SerializeToString()
    ).SerializeToString()
    header = struct.pack(">I", len(frame))
    client._sock = MagicMock()
    client._sock.recv.side_effect = [
        header[:1],
        header[1:3],
        header[3:],
        frame[:1],
        frame[1:],
    ]
    assert client._recv_msg() == _auth_response(response)


def test_ctrader_snapshot_read_failure_prevents_rotation(auth_client: Any) -> None:
    client, host = auth_client
    host.get_snapshot.side_effect = RuntimeError("PRIVATE-STORAGE-DETAIL")
    with patch.object(client, "_send_msg") as send:
        with pytest.raises(BridgeError) as caught:
            client._refresh_access_token()
    assert caught.value.code == "CTRADER_TOKEN_PERSIST_FAILED"
    assert "PRIVATE" not in str(caught.value)
    send.assert_not_called()


@pytest.mark.parametrize(
    "failure", ["empty-list", "missing-environment", "wrong-auth-account"]
)
def test_ctrader_unverified_account_fails_closed(
    auth_client: Any, failure: str
) -> None:
    from app.services.brokers.ctrader import oamsg

    client, _ = auth_client
    result = _account_list()
    if failure == "empty-list":
        result.ClearField("ctidTraderAccount")
    elif failure == "missing-environment":
        result.ctidTraderAccount[0].ClearField("isLive")
    responses = [_auth_response(result)]
    if failure == "wrong-auth-account":
        responses.append(
            _auth_response(oamsg.ProtoOAAccountAuthRes(ctidTraderAccountId=99))
        )
    with (
        patch.object(client, "_send_msg", return_value=True),
        patch.object(
            client,
            "_recv_msg",
            side_effect=responses,
        ),
    ):
        with pytest.raises(BridgeError) as caught:
            client._auth_account()
    assert caught.value.code == (
        "CTRADER_ACCOUNT_NOT_AUTHORIZED" if failure == "empty-list" else "AUTH_FAILED"
    )
    assert not client.is_connected


def test_ctrader_auth_deadline_is_not_reset_by_unrelated_messages(
    auth_client: Any,
) -> None:

    client, _ = auth_client
    client.command_timeout = 1
    with (
        patch.object(client, "_send_msg", return_value=True),
        patch.object(
            client,
            "_recv_msg",
            return_value=(9999, b""),
        ) as receive,
        patch(
            "app.services.brokers.ctrader.time.monotonic", side_effect=[0, 0, 0.5, 2]
        ),
    ):
        with pytest.raises(BridgeError) as caught:
            client._auth_application()
    assert caught.value.code == "COMMAND_TIMEOUT"
    receive.assert_called_once_with(timeout=0.5)


def test_ctrader_truncated_frame_is_rejected(auth_client: Any) -> None:
    client, _ = auth_client
    client._sock = MagicMock()
    client._sock.recv.side_effect = [b"\x00", b""]
    assert client._recv_msg() is None
    assert client.last_error[0] == "RECV_ERROR"


def test_ctrader_example_keeps_auth_error_and_stays_disarmed(
    auth_client: Any, capsys: Any
) -> None:
    from importlib import import_module

    brokers = import_module("scripts.examples.brokers")

    assert brokers.ALLOW_LIVE_TRADING is False
    with patch.object(
        brokers,
        "create_backend",
        side_effect=BridgeError("safe", code="CTRADER_REAUTHORIZE_REQUIRED"),
    ):
        assert brokers.main() == 1
    assert "Example failed: CTRADER_REAUTHORIZE_REQUIRED" in capsys.readouterr().out


def test_ctrader_environment_tokens_are_caller_owned(
    auth_client: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    from app.services.brokers.ctrader import CTraderClient

    monkeypatch.setenv("CTRADER_ACCESS_TOKEN", "environment-access")
    client = CTraderClient()
    assert client.access_token == "environment-access"
    assert not client._host_owned_tokens


@pytest.mark.parametrize("failure", ["send", "empty-token-pair", "invalid-envelope"])
def test_ctrader_transport_and_refresh_reject_incomplete_results(
    auth_client: Any, failure: str
) -> None:
    from app.services.brokers.ctrader import oamsg

    client, host = auth_client
    if failure == "send":
        with patch.object(client, "_send_msg", return_value=False):
            with pytest.raises(BridgeError) as caught:
                client._auth_application()
        assert caught.value.code == "AUTH_FAILED"
    elif failure == "empty-token-pair":
        response = oamsg.ProtoOARefreshTokenRes(
            accessToken="", refreshToken="", tokenType="bearer", expiresIn=3600
        )
        with (
            patch.object(client, "_send_msg", return_value=True),
            patch.object(client, "_recv_msg", return_value=_auth_response(response)),
        ):
            with pytest.raises(BridgeError) as caught:
                client._refresh_access_token()
        assert caught.value.code == "CTRADER_REAUTHORIZE_REQUIRED"
        assert client.access_token == "old-access"
        host.update.assert_not_called()
    else:
        client._sock = MagicMock()
        client._sock.recv.side_effect = [b"\x00\x00\x00\x01", b"\xff"]
        with pytest.raises(BridgeError) as caught:
            client._recv_msg()
        assert caught.value.code == "AUTH_FAILED"


@pytest.fixture
def history_client(auth_client: Any, monkeypatch: pytest.MonkeyPatch) -> Any:
    """Isolate historical socket traffic and pacing from the real gateway."""
    client, _ = auth_client
    client._authenticated = True
    client._symbol_name_map["EURUSD"] = 7
    monkeypatch.setattr("app.services.brokers.ctrader.time.sleep", lambda _: None)
    return client


def _bar_response(stamps: list[int], *, account: int = 42, period: int = 1) -> Any:
    from app.services.brokers.ctrader import oamsg

    response = oamsg.ProtoOAGetTrendbarsRes(
        ctidTraderAccountId=account, period=period, timestamp=1, symbolId=7
    )
    for stamp in stamps:
        response.trendbar.add(
            utcTimestampInMinutes=stamp // 60,
            low=110000,
            deltaOpen=5,
            deltaHigh=20,
            deltaClose=10,
            volume=12,
        )
    return response


def _tick_response(ticks: list[tuple[int, int]], more: bool = False) -> Any:
    from app.services.brokers.ctrader import oamsg

    result = oamsg.ProtoOAGetTickDataRes(ctidTraderAccountId=42, hasMore=more)
    previous_stamp = previous_price = 0
    for index, (stamp, price) in enumerate(ticks):
        result.tickData.add(
            timestamp=stamp if index == 0 else stamp - previous_stamp,
            tick=price if index == 0 else price - previous_price,
        )
        previous_stamp, previous_price = stamp, price
    return result


def test_ctrader_bars_emit_complete_request_and_decode(history_client: Any) -> None:
    from app.services.brokers.ctrader import oamsg

    client = history_client
    response = _bar_response([180, 120, 120, 60])
    with (
        patch.object(client, "_send_msg", return_value=True) as send,
        patch.object(client, "_recv_msg", return_value=_auth_response(response)),
    ):
        rows = client.trendbars(
            "EURUSD", "PERIOD_M1", count=10, start_sec=60, end_sec=180
        )
    request = oamsg.ProtoOAGetTrendbarsReq()
    request.ParseFromString(send.call_args.args[1])
    assert request.IsInitialized()
    assert (request.symbolId, request.period) == (7, 1)
    assert (request.fromTimestamp, request.toTimestamp, request.count) == (
        60000,
        180000,
        11,
    )
    assert [row["time"] for row in rows] == [60, 120, 180]
    assert rows[0]["open"] == 1.10005
    assert rows[0]["close"] == 1.1001
    assert rows[0]["spread"] == 0


@pytest.mark.parametrize(
    ("timeframe", "start", "end", "limit", "code"),
    [
        ("CURRENT", 60, 120, 10, "UNSUPPORTED_TIMEFRAME"),
        ("M1", 120, 60, 10, "BAD_REQUEST"),
        ("M1", 60, 120, 0, "BAD_REQUEST"),
        ("M1", -1, 120, 10, "BAD_REQUEST"),
    ],
)
def test_ctrader_bad_history_request_never_sends(
    history_client: Any, timeframe: str, start: int, end: int, limit: int, *, code: str
) -> None:
    with patch.object(history_client, "_send_msg") as send:
        with pytest.raises(BridgeError) as caught:
            history_client.trendbars(
                "EURUSD", timeframe, limit, start_sec=start, end_sec=end
            )
    assert caught.value.code == code
    send.assert_not_called()


def test_ctrader_history_resolves_real_symbol_on_demand(history_client: Any) -> None:
    client = history_client
    client._symbol_name_map.clear()

    def populate() -> list[str]:
        client._symbol_name_map["EURUSD"] = 99
        return ["EURUSD"]

    with patch.object(client, "symbols_list", side_effect=populate) as discover:
        assert client._history_symbol_id("eurusd") == 99
    discover.assert_called_once()
    with patch.object(client, "symbols_list", return_value=[]):
        with pytest.raises(BridgeError) as caught:
            client._history_symbol_id("UNKNOWN")
    assert caught.value.code == "SYMBOL_NOT_FOUND"


@pytest.mark.parametrize(
    "failure", ["account", "period", "symbol", "timestamp", "limit"]
)
def test_ctrader_invalid_bar_response_fails_closed(
    history_client: Any, failure: str
) -> None:
    response = _bar_response([60, 120])
    if failure == "account":
        response.ctidTraderAccountId = 99
    elif failure == "period":
        response.period = 9
    elif failure == "symbol":
        response.symbolId = 99
    elif failure == "timestamp":
        response.trendbar[0].ClearField("utcTimestampInMinutes")
    with (
        patch.object(history_client, "_send_msg", return_value=True),
        patch.object(
            history_client, "_recv_msg", return_value=_auth_response(response)
        ),
    ):
        with pytest.raises(BridgeError) as caught:
            history_client.trendbars(
                "EURUSD",
                "M1",
                1 if failure == "limit" else 10,
                start_sec=60,
                end_sec=120,
            )
    assert caught.value.code == (
        "DATA_LIMIT_EXCEEDED" if failure == "limit" else "INVALID_MARKET_DATA"
    )


def test_ctrader_bars_walk_date_windows_without_gaps(history_client: Any) -> None:
    from app.services.brokers.ctrader import oamsg

    with (
        patch.object(history_client, "_send_msg", return_value=True) as send,
        patch.object(
            history_client,
            "_recv_msg",
            side_effect=[
                _auth_response(_bar_response([86460])),
                _auth_response(_bar_response([60])),
            ],
        ),
    ):
        rows = history_client.trendbars("EURUSD", "M1", 10, start_sec=60, end_sec=86460)
    requests = []
    for call in send.call_args_list:
        request = oamsg.ProtoOAGetTrendbarsReq()
        request.ParseFromString(call.args[1])
        requests.append(request)
    assert requests[1].toTimestamp == 86460000 - 1
    assert [row["time"] for row in rows] == [60, 86460]


def test_ctrader_ticks_decode_signed_time_and_price_deltas(history_client: Any) -> None:
    from app.services.brokers.ctrader import oamsg

    bid = _tick_response([(3000, 110002), (2000, 110003), (1000, 110001)])
    ask = _tick_response([(2500, 110005), (1500, 110004)])
    with (
        patch.object(history_client, "_send_msg", return_value=True) as send,
        patch.object(
            history_client,
            "_recv_msg",
            side_effect=[_auth_response(bid), _auth_response(ask)],
        ),
    ):
        rows = history_client.historical_ticks("EURUSD", 1000, 3000, 10)
    requests = []
    for call in send.call_args_list:
        request = oamsg.ProtoOAGetTickDataReq()
        request.ParseFromString(call.args[1])
        assert request.IsInitialized()
        assert (request.symbolId, request.fromTimestamp, request.toTimestamp) == (
            7,
            1000,
            3000,
        )
        requests.append(request)
    assert [request.type for request in requests] == [1, 2]
    assert [row["time_msc"] for row in rows] == [1000, 1500, 2000, 2500, 3000]
    assert rows[0]["bid"] == 1.10001
    assert rows[0]["ask"] == 0.0
    assert rows[-1]["bid"] == 1.10002
    assert rows[-1]["ask"] == 1.10005
    assert [row["flags"] for row in rows] == [2, 4, 2, 4, 2]


def test_ctrader_tick_pagination_overlaps_and_deduplicates(history_client: Any) -> None:
    from app.services.brokers.ctrader import oamsg

    with (
        patch.object(history_client, "_send_msg", return_value=True) as send,
        patch.object(
            history_client,
            "_recv_msg",
            side_effect=[
                _auth_response(_tick_response([(3000, 110003), (2000, 110002)], True)),
                _auth_response(_tick_response([(2000, 110002), (1000, 110001)])),
            ],
        ),
    ):
        ticks = history_client._tick_side(7, 1, 1000, 3000, 10)
    request = oamsg.ProtoOAGetTickDataReq()
    request.ParseFromString(send.call_args_list[-1].args[1])
    assert request.toTimestamp == 2000
    assert ticks == [(1000, 110001), (2000, 110002), (3000, 110003)]


@pytest.mark.parametrize(
    "failure", ["no-progress", "out-of-range", "combined-limit", "bad-price"]
)
def test_ctrader_tick_history_never_returns_partial_or_fake_data(
    history_client: Any, failure: str
) -> None:
    if failure == "no-progress":
        responses = [_tick_response([(3000, 110003)], True)]
    elif failure == "out-of-range":
        responses = [_tick_response([(4000, 110003)])]
    elif failure == "bad-price":
        responses = [_tick_response([(3000, -1)])]
    else:
        responses = [_tick_response([(2000, 110002)]), _tick_response([(2500, 110005)])]
    with (
        patch.object(history_client, "_send_msg", return_value=True),
        patch.object(
            history_client,
            "_recv_msg",
            side_effect=[_auth_response(r) for r in responses],
        ),
        patch.object(history_client, "symbol_info") as synthetic_snapshot,
    ):
        with pytest.raises(BridgeError) as caught:
            history_client.historical_ticks(
                "EURUSD", 1000, 3000, 1 if failure == "combined-limit" else 10
            )
    assert caught.value.code in {"DATA_LIMIT_EXCEEDED", "INVALID_MARKET_DATA"}
    synthetic_snapshot.assert_not_called()


def test_ctrader_history_empty_response_stays_empty(history_client: Any) -> None:
    with (
        patch.object(history_client, "_send_msg", return_value=True),
        patch.object(
            history_client, "_recv_msg", return_value=_auth_response(_tick_response([]))
        ),
    ):
        assert history_client.historical_ticks("EURUSD", 1000, 3000, 10) == []


@pytest.mark.anyio
async def test_ctrader_shared_history_limit_and_bounds_forwarded(
    auth_client: Any,
) -> None:
    from datetime import UTC, datetime

    from app.services.brokers.contracts import Timeframe
    from app.services.libs.data import get_historical_bars, get_ticks

    backend = CTraderBackend()
    start = datetime.fromtimestamp(60, UTC)
    end = datetime.fromtimestamp(120, UTC)
    with (
        patch.object(backend.client, "trendbars", return_value=[]) as bars,
        patch.object(backend.client, "historical_ticks", return_value=[]) as ticks,
    ):
        assert (
            await get_historical_bars(
                backend, "EURUSD", Timeframe.PERIOD_M1, start, end, limit=50
            )
            == []
        )
        assert await get_ticks(backend, "EURUSD", start, end, limit=51) == []
    bars.assert_called_once_with("EURUSD", "M1", count=50, start_sec=60, end_sec=120)
    ticks.assert_called_once_with("EURUSD", 60000, 120000, 51)


@pytest.mark.parametrize("method", ["Bars", "Ticks"])
def test_ctrader_unsupported_history_modes_fail_explicitly(
    history_client: Any, method: str
) -> None:
    backend = CTraderBackend(client_id="test")
    args = (
        ["EURUSD", "M1", "position", 0, 100, 10]
        if method == "Bars"
        else ["EURUSD", "latest", 0, 100, 10]
    )
    with pytest.raises(BridgeError) as caught:
        backend._dispatch_market_data(method, args)
    assert caught.value.code == "UNSUPPORTED_OPERATION"


def test_ctrader_tick_updates_same_millisecond_preserve_order(
    history_client: Any,
) -> None:
    with (
        patch.object(history_client, "_send_msg", return_value=True),
        patch.object(
            history_client,
            "_recv_msg",
            side_effect=[
                _auth_response(
                    _tick_response([(2000, 110001), (2000, 110003), (1000, 110002)])
                ),
                _auth_response(_tick_response([])),
            ],
        ),
    ):
        rows = history_client.historical_ticks("EURUSD", 1000, 2000, 10)
    assert [(row["time_msc"], row["bid"]) for row in rows] == [
        (1000, 1.10002),
        (2000, 1.10003),
        (2000, 1.10001),
    ]


def test_ctrader_bar_request_handles_heartbeat(history_client: Any) -> None:
    from app.services.brokers.ctrader import commonmsg

    with (
        patch.object(history_client, "_send_msg", return_value=True) as send,
        patch.object(
            history_client,
            "_recv_msg",
            side_effect=[
                _auth_response(commonmsg.ProtoHeartbeatEvent()),
                _auth_response(_bar_response([60])),
            ],
        ),
    ):
        rows = history_client.trendbars("EURUSD", "M1", 10, start_sec=60, end_sec=120)
    assert len(rows) == 1
    assert send.call_count == 2


def test_ctrader_history_pacing_keeps_request_rate_bounded(history_client: Any) -> None:
    from app.services.brokers.ctrader import oamsg

    history_client._history_next_request = 10.21
    with (
        patch("app.services.brokers.ctrader.time.monotonic", return_value=10),
        patch("app.services.brokers.ctrader.time.sleep") as sleep,
        patch.object(history_client, "_auth_request", return_value=_bar_response([])),
    ):
        history_client._history_request(
            oamsg.ProtoOAGetTrendbarsReq(), oamsg.ProtoOAGetTrendbarsRes
        )
    assert sleep.call_args.args[0] == pytest.approx(0.21)


def test_ctrader_historical_error_excludes_server_description(
    history_client: Any,
) -> None:
    from app.services.brokers.ctrader import oamsg

    error = oamsg.ProtoOAErrorRes(
        errorCode="SYMBOL_NOT_FOUND", description="PRIVATE-DETAIL"
    )
    with (
        patch.object(history_client, "_send_msg", return_value=True),
        patch.object(history_client, "_recv_msg", return_value=_auth_response(error)),
    ):
        with pytest.raises(BridgeError) as caught:
            history_client.trendbars("EURUSD", "M1", 10, start_sec=60, end_sec=120)
    assert caught.value.code == "SYMBOL_NOT_FOUND"
    assert "PRIVATE" not in str(caught.value)


def test_ctrader_short_bar_pages_do_not_silently_truncate(history_client: Any) -> None:
    with (
        patch.object(history_client, "_send_msg", return_value=True),
        patch.object(
            history_client,
            "_recv_msg",
            side_effect=[
                _auth_response(_bar_response([180])),
                _auth_response(_bar_response([120])),
                _auth_response(_bar_response([60])),
            ],
        ),
    ):
        rows = history_client.trendbars("EURUSD", "M1", 10, start_sec=60, end_sec=180)
    assert [row["time"] for row in rows] == [60, 120, 180]
