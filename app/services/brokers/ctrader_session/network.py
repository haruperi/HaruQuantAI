"""Concrete cTrader Open API network client (Twisted reactor bridge).

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
import threading
from collections.abc import Callable
from typing import Any

from app.services.brokers.contracts import BrokerConnectionConfig, BrokerEnvironment
from app.utils import logger

_reactor_lock = threading.Lock()
_reactor_running = False


def _ensure_reactor_thread() -> None:  # pragma: no cover - requires Twisted + network
    """Start the single shared Twisted reactor on a daemon thread exactly once."""
    global _reactor_running  # noqa: PLW0603 - one process-wide reactor by design.
    with _reactor_lock:
        if _reactor_running:
            return
        from twisted.internet import (
            reactor,  # type: ignore[import-untyped, unused-ignore]
        )

        if not reactor.running:  # type: ignore[attr-defined]
            thread = threading.Thread(
                target=reactor.run,  # type: ignore[attr-defined]
                kwargs={"installSignalHandlers": False},
                daemon=True,
                name="ctrader-reactor",
            )
            thread.start()
        _reactor_running = True
        logger.bind(component="ctrader_reactor").info(
            "Shared cTrader Twisted reactor started"
        )


class _CTraderNetworkClient:
    """One isolated real cTrader Open API session over the shared reactor."""

    def __init__(self, config: BrokerConnectionConfig) -> None:
        """Extract resolved credentials for one isolated cTrader session."""
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
        from ctrader_open_api.messages.OpenApiMessages_pb2 import (  # type: ignore[import-untyped, unused-ignore]
            ProtoOAAccountAuthReq,
            ProtoOAApplicationAuthReq,
            ProtoOAGetAccountListByAccessTokenReq,
            ProtoOATraderReq,
        )
        from ctrader_open_api.protobuf import (  # type: ignore[import-untyped, unused-ignore]
            Protobuf,
        )
        from twisted.internet import (
            reactor,  # type: ignore[import-untyped, unused-ignore]
        )

        self._loop = asyncio.get_running_loop()
        host = (
            EndPoints.PROTOBUF_LIVE_HOST
            if self._config.environment == BrokerEnvironment.LIVE
            else EndPoints.PROTOBUF_DEMO_HOST
        )
        logger.bind(
            broker=self._config.broker_id.value,
            environment=self._config.environment.value,
            host=host,
        ).info("Connecting cTrader network client")

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
                loop.call_soon_threadsafe(handler, extracted)

        client = Client(host, EndPoints.PROTOBUF_PORT, TcpProtocol)
        client.setConnectedCallback(_on_connected)
        client.setDisconnectedCallback(_on_disconnected)
        client.setMessageReceivedCallback(_on_message)
        self._client = client
        reactor.callFromThread(client.startService)  # type: ignore[attr-defined]
        await asyncio.wait_for(connected, timeout=self._config.connect_timeout_sec)

        app_request = ProtoOAApplicationAuthReq()
        app_request.clientId = self._client_id
        app_request.clientSecret = self._client_secret
        await self._request(app_request)

        list_request = ProtoOAGetAccountListByAccessTokenReq()
        list_request.accessToken = self._access_token
        await self._request(list_request)

        account_request = ProtoOAAccountAuthReq()
        account_request.ctidTraderAccountId = self._account_id
        account_request.accessToken = self._access_token
        await self._request(account_request)

        trader_request = ProtoOATraderReq()
        trader_request.ctidTraderAccountId = self._account_id
        await self._request(trader_request)

        self._connected = True
        logger.bind(
            broker=self._config.broker_id.value,
            environment=self._config.environment.value,
            result="success",
        ).info("cTrader session authenticated")
        return True

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
        client = self._client
        if client is not None:
            from twisted.internet import (
                reactor,  # type: ignore[import-untyped, unused-ignore]
            )

            reactor.callFromThread(client.stopService)  # type: ignore[attr-defined]
            self._client = None
            logger.bind(
                broker=self._config.broker_id.value,
                environment=self._config.environment.value,
            ).info("cTrader network client session released")

    async def _request(self, message: Any) -> Any:  # pragma: no cover - live only
        """Bridge one reactor-thread send Deferred to an awaitable future.

        Returns:
            Exact provider response message.

        Raises:
            ConnectionError: If the client event loop is unavailable.
        """
        from twisted.internet import (
            reactor,  # type: ignore[import-untyped, unused-ignore]
        )

        loop = self._loop
        if loop is None:
            raise ConnectionError("cTrader event loop is not bound")
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

        reactor.callFromThread(_fire)  # type: ignore[attr-defined]
        return await asyncio.wait_for(future, timeout=self._config.request_timeout_sec)

    def _resolve(  # pragma: no cover - live only
        self, future: asyncio.Future[Any], *, value: Any
    ) -> None:
        """Resolve a future from the reactor thread onto the asyncio loop."""
        loop = self._loop
        if loop is None:
            return

        def _set() -> None:
            """Handle set."""
            if not future.done():
                future.set_result(value)

        loop.call_soon_threadsafe(_set)

    def _reject(  # pragma: no cover - live only
        self, future: asyncio.Future[Any], error: Exception
    ) -> None:
        """Fail a future from the reactor thread onto the asyncio loop."""
        loop = self._loop
        if loop is None:
            return

        def _set() -> None:
            """Handle set."""
            if not future.done():
                future.set_exception(error)

        loop.call_soon_threadsafe(_set)
