# mypy: ignore-errors
"""Concrete cTrader direct-channel network client (Twisted reactor bridge).

This module owns the real Spotware Open API connection that the injected
``_CTraderTransport`` sender abstracts away. It runs a single process-wide
Twisted reactor on a daemon thread (Twisted's reactor cannot be restarted once
stopped), while every client instance keeps its own isolated ``Client``,
pending-request futures, and connection state so independent adapters never
share mutable session state (``NFR-BRK-005``).

The provider SDK and Twisted are imported lazily inside methods so importing
this module performs no side effect and pulls in no optional dependency.
"""

# ruff: noqa: ANN401 - dynamic cTrader SDK types; long SDK import / type-ignore lines.
import asyncio
import logging
import threading
from collections.abc import Callable
from typing import Any, cast

from app.services.brokers.ctrader._legacy_types import (
    BrokerConnectionConfig,
    BrokerEnvironment,
)

logger = logging.getLogger(__name__)

_reactor_lock = threading.Lock()
_reactor_running = False


def _expect_response(
    response: object,
    expected_type: type[object],
    *,
    step: str,
) -> Any:
    """Validate one cTrader lifecycle response without exposing provider payloads.

    Args:
        response: Extracted provider response.
        expected_type: Exact protobuf response class required by the step.
        step: Bounded lifecycle-step label for safe error reporting.

    Returns:
        The validated provider response.

    Raises:
        ConnectionError: If the provider rejects the request or returns an
            unexpected response type.
    """
    if type(response).__name__ == "ProtoOAErrorRes":
        provider_code = str(getattr(response, "errorCode", "UNKNOWN"))
        message = f"cTrader {step} rejected: {provider_code}"
        raise ConnectionError(message)
    if not isinstance(response, expected_type):
        message = f"cTrader {step} returned an unexpected response"
        raise ConnectionError(message)
    return response


def _validate_account_environment(
    response: object,
    *,
    account_id: int,
    environment: BrokerEnvironment,
) -> None:
    """Require the configured account and its provider-reported environment.

    Args:
        response: Validated ``ProtoOAGetAccountListByAccessTokenRes``.
        account_id: Configured cTrader account identifier.
        environment: Configured broker environment.

    Raises:
        ConnectionError: If the account is unavailable or its provider-reported
            live/demo classification conflicts with configuration.
    """
    accounts = tuple(getattr(response, "ctidTraderAccount", ()))
    account = next(
        (
            item
            for item in accounts
            if int(getattr(item, "ctidTraderAccountId", -1)) == account_id
        ),
        None,
    )
    if account is None:
        raise ConnectionError("configured cTrader account is unavailable")
    is_live = bool(getattr(account, "isLive", False))
    expected_live = environment == BrokerEnvironment.LIVE
    if is_live != expected_live:
        raise ConnectionError("cTrader account environment mismatch")


def _validate_account_response(response: object, *, account_id: int, step: str) -> None:
    """Require a lifecycle response to refer to the configured account.

    Args:
        response: Validated provider response.
        account_id: Configured cTrader account identifier.
        step: Bounded lifecycle-step label for safe error reporting.

    Raises:
        ConnectionError: If the response refers to another account.
    """
    response_account_id = int(getattr(response, "ctidTraderAccountId", -1))
    if response_account_id != account_id:
        message = f"cTrader {step} account mismatch"
        raise ConnectionError(message)


def _ensure_reactor_thread() -> None:  # pragma: no cover - requires Twisted + network
    """Start the single shared Twisted reactor on a daemon thread exactly once."""
    global _reactor_running  # noqa: PLW0603 - one process-wide reactor by design.
    with _reactor_lock:
        if _reactor_running:
            return
        from twisted.internet import (
            reactor,  # type: ignore[import-untyped, unused-ignore]
        )

        typed_reactor = cast("Any", reactor)

        if not typed_reactor.running:
            thread = threading.Thread(
                target=typed_reactor.run,
                kwargs={"installSignalHandlers": False},
                daemon=True,
                name="ctrader-reactor",
            )
            thread.start()
        _reactor_running = True
        logger.info("Shared cTrader Twisted reactor started")


class _CTraderNetworkClient:
    """One isolated real cTrader Open API session over the shared reactor."""

    def __init__(self, config: BrokerConnectionConfig) -> None:
        """Extract resolved credentials for one isolated cTrader session.

        Args:
            config: Value supplied to the operation.
        """
        self._config = config
        credentials = config.credentials or {}
        self._client_id = credentials["client_id"].get_secret_value()
        self._client_secret = credentials["client_secret"].get_secret_value()
        self._access_token = credentials["access_token"].get_secret_value()
        self._account_id = int(credentials["account_id"].get_secret_value())
        self._client: Any = None
        self._loop: asyncio.AbstractEventLoop | None = None
        self._connected = False
        self._event_handlers: list[Callable[[object], None]] = []

    async def connect(self) -> bool:  # pragma: no cover - requires Twisted + network
        """Establish transport and run the full authentication handshake.

        Returns:
            ``True`` once application auth, account authorization, and trader
            details all succeed.

        Raises:
            ConnectionError: The transport, application auth, account
                authorization, or trader lookup is rejected by the provider.
            TimeoutError: A handshake step exceeds its configured bound.
        """
        _ensure_reactor_thread()
        from ctrader_open_api import (  # type: ignore[import-untyped, unused-ignore]
            Client,
            EndPoints,
            TcpProtocol,
        )
        from ctrader_open_api.protobuf import (  # type: ignore[import-untyped, unused-ignore]
            Protobuf,
        )
        from twisted.internet import (
            reactor,  # type: ignore[import-untyped, unused-ignore]
        )

        typed_reactor = cast("Any", reactor)

        self._loop = asyncio.get_running_loop()
        host = (
            EndPoints.PROTOBUF_LIVE_HOST
            if self._config.environment == BrokerEnvironment.LIVE
            else EndPoints.PROTOBUF_DEMO_HOST
        )
        logger.info("Connecting cTrader network client")

        connected: asyncio.Future[bool] = self._loop.create_future()

        def _on_connected(_client: Any) -> None:
            """Handle on connected.

            Args:
                _client: Value supplied to the operation.
            """
            self._resolve(connected, value=True)

        def _on_disconnected(_client: Any, reason: Any) -> None:
            """Handle on disconnected.

            Args:
                _client: Value supplied to the operation.
                reason: Value supplied to the operation.
            """
            self._connected = False
            self._reject(connected, ConnectionError(str(reason)))

        def _on_message(_client: Any, message: Any) -> None:
            """Handle on message.

            Args:
                _client: Value supplied to the operation.
                message: Value supplied to the operation.

            """
            extracted = Protobuf.extract(message)
            loop = self._loop
            if loop is None:
                return
            for handler in tuple(self._event_handlers):
                if loop.is_closed():
                    return

                def _call(h: Any = handler) -> Any:
                    """Deliver one extracted provider event to a registered handler.

                    Args:
                        h: Registered event callback.

                    Returns:
                        Callback return value.
                    """
                    return h(extracted)

                self._post_to_asyncio_loop(
                    loop,
                    _call,
                    callback_id="message",
                )

        client = Client(host, EndPoints.PROTOBUF_PORT, TcpProtocol)
        client.setConnectedCallback(_on_connected)
        client.setDisconnectedCallback(_on_disconnected)
        client.setMessageReceivedCallback(_on_message)
        self._client = client
        typed_reactor.callFromThread(client.startService)
        await asyncio.wait_for(connected, timeout=self._config.connect_timeout_sec)

        try:
            await self._authenticate(Protobuf)
        except Exception:
            await self.close()
            raise

        self._connected = True
        logger.info("cTrader session authenticated")
        return True

    async def _authenticate(self, protobuf: Any) -> None:
        """Run and validate the provider's complete authentication handshake.

        Args:
            protobuf: Lazily imported cTrader protobuf helper.

        Raises:
            ConnectionError: If any provider response or account classification
                fails validation.
            TimeoutError: If a provider response exceeds its configured bound.
        """
        from ctrader_open_api.messages.OpenApiMessages_pb2 import (  # type: ignore[import-untyped, unused-ignore]
            ProtoOAAccountAuthReq,
            ProtoOAAccountAuthRes,
            ProtoOAApplicationAuthReq,
            ProtoOAApplicationAuthRes,
            ProtoOAGetAccountListByAccessTokenReq,
            ProtoOAGetAccountListByAccessTokenRes,
            ProtoOATraderReq,
            ProtoOATraderRes,
        )

        app_request = ProtoOAApplicationAuthReq()
        app_request.clientId = self._client_id
        app_request.clientSecret = self._client_secret
        app_response = protobuf.extract(await self._request(app_request))
        _expect_response(
            app_response,
            ProtoOAApplicationAuthRes,
            step="application authentication",
        )

        list_request = ProtoOAGetAccountListByAccessTokenReq()
        list_request.accessToken = self._access_token
        list_response = _expect_response(
            protobuf.extract(await self._request(list_request)),
            ProtoOAGetAccountListByAccessTokenRes,
            step="account discovery",
        )
        _validate_account_environment(
            list_response,
            account_id=self._account_id,
            environment=self._config.environment,
        )

        account_request = ProtoOAAccountAuthReq()
        account_request.ctidTraderAccountId = self._account_id
        account_request.accessToken = self._access_token
        account_response = _expect_response(
            protobuf.extract(await self._request(account_request)),
            ProtoOAAccountAuthRes,
            step="account authentication",
        )
        _validate_account_response(
            account_response,
            account_id=self._account_id,
            step="account authentication",
        )

        trader_request = ProtoOATraderReq()
        trader_request.ctidTraderAccountId = self._account_id
        trader_response = _expect_response(
            protobuf.extract(await self._request(trader_request)),
            ProtoOATraderRes,
            step="trader lookup",
        )
        _validate_account_response(
            trader_response,
            account_id=self._account_id,
            step="trader lookup",
        )

    async def send(self, request: object) -> object:  # pragma: no cover - live only
        """Send one correlated request and return the extracted response.

        Args:
            request: The provider-native protobuf request object.

        Returns:
            The extracted typed protobuf response for exactly this request.

        Raises:
            ConnectionError: If this client is not connected.
        """
        if not self._connected or self._client is None:
            raise ConnectionError("cTrader session is not connected")
        from ctrader_open_api.protobuf import (  # type: ignore[import-untyped, unused-ignore]
            Protobuf,
        )

        response = await self._request(request)
        return Protobuf.extract(response)

    def add_event_handler(self, handler: Callable[[object], None]) -> None:
        """Register one adapter-local provider-event callback.

        Args:
            handler: Callback invoked on the adapter asyncio loop.
        """
        if handler not in self._event_handlers:
            self._event_handlers.append(handler)

    def remove_event_handler(self, handler: Callable[[object], None]) -> None:
        """Remove one adapter-local provider-event callback.

        Args:
            handler: Previously registered callback.
        """
        if handler in self._event_handlers:
            self._event_handlers.remove(handler)

    async def close(self) -> None:  # pragma: no cover - requires Twisted + network
        """Release only this client's session; the shared reactor keeps running."""
        self._connected = False
        self._loop = None
        self._event_handlers.clear()
        client = self._client
        if client is not None:
            self._client = None
            from twisted.internet import (
                reactor,  # type: ignore[import-untyped, unused-ignore]
            )

            typed_reactor = cast("Any", reactor)

            typed_reactor.callFromThread(client.stopService)
            logger.info("cTrader network client session released")

    async def _request(self, message: Any) -> Any:  # pragma: no cover - live only
        """Bridge one reactor-thread send Deferred to an awaitable future.

        Args:
            message: Value supplied to the operation.

        Returns:
            Exact provider response message.

        Raises:
            ConnectionError: If the client event loop is unavailable.
        """
        from twisted.internet import (
            reactor,  # type: ignore[import-untyped, unused-ignore]
        )

        typed_reactor = cast("Any", reactor)

        loop = self._loop
        if loop is None:
            raise ConnectionError("cTrader event loop is not bound")
        if loop.is_closed():
            raise ConnectionError("cTrader event loop is closed")
        future: asyncio.Future[Any] = loop.create_future()

        def _on_ok(response: Any) -> None:
            """Handle on ok.

            Args:
                response: Value supplied to the operation.
            """
            self._resolve(future, value=response)

        def _on_err(failure: Any) -> None:
            """Handle on err.

            Args:
                failure: Value supplied to the operation.
            """
            self._reject(future, ConnectionError(str(failure)))

        def _fire() -> None:
            """Handle fire."""
            deferred = self._client.send(message)
            deferred.addCallbacks(_on_ok, _on_err)

        typed_reactor.callFromThread(_fire)
        return await asyncio.wait_for(future, timeout=self._config.request_timeout_sec)

    def _resolve(  # pragma: no cover - live only
        self, future: asyncio.Future[Any], *, value: Any
    ) -> None:
        """Resolve a future from the reactor thread onto the asyncio loop.

        Args:
            future: Value supplied to the operation.
            value: Value supplied to the operation.
        """
        loop = self._loop
        if loop is None:
            return

        def _set() -> None:
            """Handle set."""
            if not future.done():
                future.set_result(value)

        self._post_to_asyncio_loop(loop, _set, callback_id="resolve")

    def _reject(  # pragma: no cover - live only
        self, future: asyncio.Future[Any], error: Exception
    ) -> None:
        """Fail a future from the reactor thread onto the asyncio loop.

        Args:
            future: Value supplied to the operation.
            error: Value supplied to the operation.
        """
        loop = self._loop
        if loop is None:
            return

        def _set() -> None:
            """Handle set."""
            if not future.done():
                future.set_exception(error)

        self._post_to_asyncio_loop(loop, _set, callback_id="reject")

    def _post_to_asyncio_loop(
        self,
        loop: asyncio.AbstractEventLoop,
        callback: Callable[[], None],
        *,
        callback_id: str,
    ) -> None:
        """Post a callback only when the loop is still usable.

        Args:
            loop: Target event loop.
            callback: Callback to execute in loop context.
            callback_id: Internal trace tag for debug logs.

        Raises:
            RuntimeError: If the event loop error is not a loop-closed condition.
        """
        if loop.is_closed():
            return
        try:
            loop.call_soon_threadsafe(callback)
        except RuntimeError as error:
            if "Event loop is closed" in str(error):
                logger.debug(
                    "Ignoring cTrader callback after loop close: %s", callback_id
                )
                return
            raise
