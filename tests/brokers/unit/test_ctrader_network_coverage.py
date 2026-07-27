"""Coverage expansion tests for cTrader network operations."""

import asyncio
from typing import Any
from unittest.mock import MagicMock

import pytest
from app.services.brokers import BrokerConnectionConfig, BrokerEnvironment, BrokerId
from app.services.brokers.ctrader_session.network import (
    _CTraderNetworkClient,
    _expect_response,
    _validate_account_environment,
    _validate_account_response,
)
from pydantic import SecretStr


def _config(**overrides: object) -> BrokerConnectionConfig:
    values: dict[str, object] = {
        "broker_id": BrokerId.CTRADER,
        "environment": BrokerEnvironment.DEMO,
        "provider_enabled": True,
        "connect_timeout_sec": 1,
        "request_timeout_sec": 1,
        "transport_reconnect_max_attempts": 0,
        "stream_buffer_size": 2,
        "circuit_failure_threshold": 2,
        "circuit_recovery_timeout_sec": 1,
        "circuit_half_open_max_calls": 1,
        "account_reference": "998877",
        "credentials": {
            "client_id": SecretStr("client-id"),
            "client_secret": SecretStr("client-secret"),
            "access_token": SecretStr("access-token"),
            "account_id": SecretStr("998877"),
        },
    }
    values.update(overrides)
    return BrokerConnectionConfig(**values)  # type: ignore[arg-type]


class DummyExpectedRes:
    pass


class DummyOtherRes:
    pass


class ProtoOAErrorRes:
    errorCode = "INVALID_CREDENTIALS"  # noqa: N815


def test_expect_response_valid_and_errors() -> None:
    """Verify _expect_response validates expected type or raises ConnectionError."""
    ok_res = DummyExpectedRes()
    assert _expect_response(ok_res, DummyExpectedRes, step="test") is ok_res

    # Unexpected response class
    with pytest.raises(
        ConnectionError, match="cTrader test returned an unexpected response"
    ):
        _expect_response(DummyOtherRes(), DummyExpectedRes, step="test")

    # ProtoOAErrorRes error payload
    with pytest.raises(
        ConnectionError, match="cTrader test rejected: INVALID_CREDENTIALS"
    ):
        _expect_response(ProtoOAErrorRes(), DummyExpectedRes, step="test")


def test_validate_account_environment_matching_and_mismatches() -> None:
    """Verify _validate_account_environment validates configured cTrader account & live/demo status."""
    acc_demo = MagicMock(ctidTraderAccountId=998877, isLive=False)
    acc_live = MagicMock(ctidTraderAccountId=998877, isLive=True)
    response = MagicMock(ctidTraderAccount=(acc_demo,))

    # Valid demo account
    _validate_account_environment(
        response, account_id=998877, environment=BrokerEnvironment.DEMO
    )

    # Missing account
    with pytest.raises(
        ConnectionError, match="configured cTrader account is unavailable"
    ):
        _validate_account_environment(
            response, account_id=111111, environment=BrokerEnvironment.DEMO
        )

    # Environment mismatch (demo configured, live reported)
    response_live = MagicMock(ctidTraderAccount=(acc_live,))
    with pytest.raises(ConnectionError, match="cTrader account environment mismatch"):
        _validate_account_environment(
            response_live, account_id=998877, environment=BrokerEnvironment.DEMO
        )


def test_validate_account_response_matching_and_mismatches() -> None:
    """Verify _validate_account_response requires matching account ID."""
    res_valid = MagicMock(ctidTraderAccountId=998877)
    _validate_account_response(res_valid, account_id=998877, step="auth")

    res_invalid = MagicMock(ctidTraderAccountId=111111)
    with pytest.raises(ConnectionError, match="cTrader auth account mismatch"):
        _validate_account_response(res_invalid, account_id=998877, step="auth")


def test_network_client_event_handlers() -> None:
    """Verify adding and removing event handlers on _CTraderNetworkClient."""
    client = _CTraderNetworkClient(_config())
    handler = MagicMock()

    client.add_event_handler(handler)
    assert handler in client._event_handlers

    # Duplicate add is ignored
    client.add_event_handler(handler)
    assert len(client._event_handlers) == 1

    client.remove_event_handler(handler)
    assert handler not in client._event_handlers

    # Ignore removing non-existent handler
    client.remove_event_handler(handler)


def test_authenticate_success() -> None:
    """Verify _authenticate executes application auth, account discovery, account auth, and trader lookup."""
    client = _CTraderNetworkClient(_config())

    app_res = MagicMock()
    acc_item = MagicMock(ctidTraderAccountId=998877, isLive=False)
    list_res = MagicMock(ctidTraderAccount=(acc_item,))
    account_auth_res = MagicMock(ctidTraderAccountId=998877)
    trader_res = MagicMock(ctidTraderAccountId=998877)

    mock_protobuf = MagicMock()
    mock_protobuf.extract = lambda msg: msg

    async def run_test() -> None:
        from ctrader_open_api.messages.OpenApiMessages_pb2 import (
            ProtoOAAccountAuthRes,
            ProtoOAApplicationAuthRes,
            ProtoOAGetAccountListByAccessTokenRes,
            ProtoOATraderRes,
        )

        app_res.__class__ = ProtoOAApplicationAuthRes
        list_res.__class__ = ProtoOAGetAccountListByAccessTokenRes
        account_auth_res.__class__ = ProtoOAAccountAuthRes
        trader_res.__class__ = ProtoOATraderRes

        fut0: asyncio.Future[Any] = asyncio.Future()
        fut0.set_result(app_res)
        fut1: asyncio.Future[Any] = asyncio.Future()
        fut1.set_result(list_res)
        fut2: asyncio.Future[Any] = asyncio.Future()
        fut2.set_result(account_auth_res)
        fut3: asyncio.Future[Any] = asyncio.Future()
        fut3.set_result(trader_res)

        client._request = MagicMock(side_effect=[fut0, fut1, fut2, fut3])

        await client._authenticate(mock_protobuf)

    asyncio.run(run_test())
