"""Canonical cTrader broker adapter."""

from collections.abc import Mapping
from datetime import UTC, datetime

from app.services.brokers.contracts import (
    BrokerCapability,
    BrokerCapabilityId,
    BrokerConnectionConfig,
    BrokerConnectionState,
    BrokerEnvironment,
    BrokerError,
    BrokerErrorCode,
    BrokerPlatformInfo,
    BrokerResult,
)
from app.services.brokers.contracts.protocols import _UnsupportedAdapterBase
from app.services.brokers.ctrader.network import _CTraderNetworkClient
from app.services.brokers.ctrader.transport import _CTraderTransport


class CTraderBrokerAdapter(_UnsupportedAdapterBase):
    """One isolated cTrader application/account session."""

    def __init__(
        self,
        config: BrokerConnectionConfig,
        capabilities: Mapping[BrokerCapabilityId, BrokerCapability],
        *,
        transport: _CTraderTransport | None = None,
    ) -> None:
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
        super().__init__(config, capabilities)
        if transport is not None:
            self._transport = transport
            self._network: _CTraderNetworkClient | None = None
        else:
            network = _CTraderNetworkClient(config)
            self._network = network
            self._transport = _CTraderTransport(config, sender=network.send)

    async def connect(self) -> BrokerResult[None]:
        """Require application/account authentication transport evidence."""
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

    async def disconnect(self) -> BrokerResult[None]:
        """Release the exact owned cTrader session."""
        await self._transport.close()
        if self._network is not None:
            await self._network.close()
        return await super().disconnect()

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
