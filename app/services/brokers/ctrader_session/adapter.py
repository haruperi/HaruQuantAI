"""Canonical cTrader broker adapter."""

import asyncio
import importlib
from datetime import UTC, datetime
from decimal import Decimal
from types import ModuleType
from typing import cast, override

from app.services.brokers.adapter_runtime.subscription import (  # noqa: TC001
    _BrokerSubscription,
)
from app.services.brokers.contracts import (
    BrokerCapabilityId,
    BrokerConnectionConfig,
    BrokerConnectionState,
    BrokerEnvironment,
    BrokerError,
    BrokerErrorCode,
    BrokerPlatformInfo,
    BrokerQuote,
    BrokerResult,
)
from app.services.brokers.contracts.protocols import (
    _UnsupportedAdapterBase,
)
from app.services.brokers.ctrader_market_data.operations import _CTraderMarketDataMixin
from app.services.brokers.ctrader_mutations.operations import _CTraderMutationsMixin
from app.services.brokers.ctrader_session.network import _CTraderNetworkClient
from app.services.brokers.ctrader_session.transport import _CTraderTransport
from app.services.brokers.execution_history.ctrader import _CTraderExecutionHistoryMixin
from app.services.brokers.price_streams.ctrader import _CTraderPriceStreamsMixin
from app.services.brokers.provider_calculations.ctrader import _CTraderCalculationsMixin


class CTraderBrokerAdapter(
    _CTraderPriceStreamsMixin,
    _CTraderMarketDataMixin,
    _CTraderCalculationsMixin,
    _CTraderExecutionHistoryMixin,
    _CTraderMutationsMixin,
    _UnsupportedAdapterBase,
):
    """One isolated cTrader application/account session."""

    def __init__(
        self,
        config: BrokerConnectionConfig,
        *,
        transport: _CTraderTransport | None = None,
    ) -> None:
        """Initialize the CTraderBrokerAdapter instance.

        Args:
            config: Value supplied to the operation.
            transport: Value supplied to the operation.

        Raises:
            ValueError: If the documented operation cannot complete.
        """
        if config.environment not in {BrokerEnvironment.LIVE, BrokerEnvironment.DEMO}:
            raise ValueError("cTrader requires LIVE or DEMO")
        if config.endpoint is not None:
            raise ValueError("cTrader custom endpoints are unavailable")
        required = {"client_id", "client_secret", "access_token", "account_id"}
        if config.credentials is None or not required <= set(config.credentials):
            raise ValueError("resolved cTrader credentials are incomplete")
        if (
            config.account_reference
            != config.credentials["account_id"].get_secret_value()
        ):
            raise ValueError("cTrader account_reference must match account_id")
        super().__init__(config)
        if transport is not None:
            self._transport = transport
            self._network: _CTraderNetworkClient | None = None
        else:
            network = _CTraderNetworkClient(config)
            self._network = network
            self._transport = _CTraderTransport(
                config,
                sender=network.send,
                register_event_handler=network.add_event_handler,
                unregister_event_handler=network.remove_event_handler,
                latency_sink=self._record_provider_latency,
            )
        self._messages: ModuleType | None = None
        self._light_symbols: dict[str, object] = {}
        self._symbol_names: dict[int, str] = {}
        self._symbol_specs: dict[str, object] = {}
        self._symbol_lot_sizes: dict[int, Decimal] = {}
        self._subscriptions: dict[str, _BrokerSubscription[BrokerQuote]] = {}
        self._event_handler_registered = False
        self._publish_tasks: set[asyncio.Task[bool]] = set()

    @override
    async def connect(self) -> BrokerResult[None]:
        """Require application/account authentication transport evidence.

        Returns:
            Canonical verified connection result.
        """
        await self._transition(BrokerConnectionState.CONNECTING)
        try:
            if self._network is not None:
                await self._network.connect()
            verified = await self._transport.connect()
        except (
            ConnectionError,
            TimeoutError,
            OSError,
            ImportError,
            ValueError,
        ) as error:
            verified = False
            self._last_error = BrokerError(
                code=BrokerErrorCode.BROKER_CONNECTION_FAILED,
                message="cTrader connection verification failed",
                provider_message=type(error).__name__,
            )
        if not verified:
            await self._transition(
                BrokerConnectionState.FAILED, reason="auth_unverified"
            )
            if self._last_error is not None:
                return self._result(BrokerCapabilityId.CONNECT, error=self._last_error)
            return self._unsupported(BrokerCapabilityId.CONNECT)
        self._session_generation += 1
        await self._transition(BrokerConnectionState.READY)
        return self._result(BrokerCapabilityId.CONNECT)

    @override
    async def disconnect(self) -> BrokerResult[None]:
        """Release the exact owned cTrader session.

        Returns:
            Canonical idempotent disconnection result.
        """
        for subscription in tuple(self._subscriptions.values()):
            await subscription.unsubscribe()
        if self._event_handler_registered:
            self._transport.unregister_event_handler(self._on_provider_event)
            self._event_handler_registered = False
        await self._transport.close()
        if self._network is not None:
            await self._network.close()
        return await super().disconnect()

    @override
    async def is_connected(self) -> BrokerResult[bool]:
        """Verify current account reachability with one reconcile request.

        Returns:
            Canonical current connectivity evidence.
        """
        await self._request("ProtoOAReconcileReq", "ProtoOAReconcileRes")
        return self._result(BrokerCapabilityId.IS_CONNECTED, data=True)

    async def ping(self) -> BrokerResult[None]:
        """Verify current account reachability without mutation.

        Returns:
            Canonical provider-health result.
        """
        await self._request("ProtoOAReconcileReq", "ProtoOAReconcileRes")
        return self._result(BrokerCapabilityId.PING)

    async def get_platform_info(self) -> BrokerResult[BrokerPlatformInfo]:
        """Return redacted endpoint/environment metadata."""
        endpoint = (
            "live.ctraderapi.com:5035"
            if self._config.environment == BrokerEnvironment.LIVE
            else "demo.ctraderapi.com:5035"
        )
        return self._result(
            BrokerCapabilityId.GET_PLATFORM_INFO,
            data=BrokerPlatformInfo(
                broker_id=self._config.broker_id,
                provider_name="cTrader Open API",
                product_profile="ctrader",
                environment=self._config.environment,
                observed_at=datetime.now(UTC),
                endpoint_metadata={"endpoint": endpoint},
            ),
        )

    def _message_module(self) -> ModuleType:
        """Load the pinned cTrader protobuf message module lazily.

        Returns:
            Provider protobuf module.
        """
        if self._messages is None:
            self._messages = importlib.import_module(
                "ctrader_open_api.messages.OpenApiMessages_pb2"
            )
        return self._messages

    async def _request(
        self, request_name: str, response_name: str, **fields: object
    ) -> object:
        """Send one typed cTrader request through the correlated transport.

        Returns:
            Exact typed provider response.
        """
        messages = self._message_module()
        request = getattr(messages, request_name)()
        request.ctidTraderAccountId = int(cast("str", self._config.account_reference))
        for name, value in fields.items():
            target = getattr(request, name)
            if isinstance(value, tuple):
                target.extend(value)
            else:
                setattr(request, name, value)
        return await self._transport.send(request, getattr(messages, response_name))

    @staticmethod
    @staticmethod
    def _validate_page(cursor: str | None, limit: int | None) -> None:
        """Validate bounded cTrader page arguments before provider access.

        Raises:
            ValueError: If cursor is supplied or limit is not positive.
        """
        if cursor is not None:
            raise ValueError("cTrader cursors are unsupported")
        if limit is None or limit <= 0:
            raise ValueError("positive cTrader page limit is required")

    @classmethod
    def _validate_history(
        cls,
        start: datetime | None,
        end: datetime | None,
        cursor: str | None,
        limit: int | None,
    ) -> None:
        """Validate explicit bounded cTrader history arguments.

        Raises:
            ValueError: If range, cursor, or limit is invalid.
        """
        cls._validate_page(cursor, limit)
        if (
            start is None
            or end is None
            or start.tzinfo is None
            or start.utcoffset() is None
            or end.tzinfo is None
            or end.utcoffset() is None
            or start >= end
        ):
            raise ValueError("explicit ordered UTC-aware history range is required")

    def _error[T](
        self, operation: BrokerCapabilityId, code: BrokerErrorCode
    ) -> BrokerResult[T]:
        """Build one canonical cTrader failure result.

        Returns:
            Canonical error result.
        """
        error = BrokerError(
            code=code,
            message=f"cTrader {operation.value} failed",
            capability=operation,
        )
        self._last_error = error
        return self._result(operation, error=error)
