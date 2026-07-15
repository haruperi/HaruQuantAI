"""Research-only Yahoo historical-bars adapter."""

from collections.abc import Mapping
from datetime import UTC, datetime

from app.services.brokers.contracts import (
    BrokerBar,
    BrokerCapability,
    BrokerCapabilityId,
    BrokerConnectionConfig,
    BrokerConnectionState,
    BrokerEnvironment,
    BrokerPage,
    BrokerPlatformInfo,
    BrokerResult,
)
from app.services.brokers.contracts.protocols import _UnsupportedAdapterBase
from app.services.brokers.yahoo.mapping import _map_history
from app.services.brokers.yahoo.transport import _YahooTransport


class YahooBrokerAdapter(_UnsupportedAdapterBase):
    """Genuine caller-bounded Yahoo bars for sandbox research."""

    def __init__(
        self,
        config: BrokerConnectionConfig,
        capabilities: Mapping[BrokerCapabilityId, BrokerCapability],
        *,
        transport: _YahooTransport | None = None,
    ) -> None:
        if config.environment != BrokerEnvironment.SANDBOX:
            raise ValueError("Yahoo is sandbox-only")
        if config.credentials or config.account_reference or config.endpoint:
            raise ValueError("Yahoo accepts no credentials, account, or endpoint")
        super().__init__(config, capabilities)
        self._transport = transport or _YahooTransport(config)

    async def connect(self) -> BrokerResult[None]:
        """Verify the provider using the caller's configured probe symbol.

        No probe symbol is ever assumed: a hidden default provider symbol is
        prohibited by this domain's boundary. When ``probe_symbol`` is unset,
        the session is verified at the transport/session level only.
        """
        await self._transition(BrokerConnectionState.CONNECTING)
        if self._config.probe_symbol is not None:
            try:
                await self._transport.history(
                    symbol=self._config.probe_symbol,
                    timeframe="1d",
                    start=None,
                    end=None,
                )
            except (OSError, TimeoutError, ValueError, ConnectionError) as error:
                await self._transition(
                    BrokerConnectionState.FAILED, reason=type(error).__name__
                )
                return self._unsupported(BrokerCapabilityId.CONNECT)
        self._session_generation += 1
        await self._transition(BrokerConnectionState.READY)
        return self._result(BrokerCapabilityId.CONNECT)

    async def get_historical_bars(
        self,
        symbol: str,
        timeframe: str,
        start: datetime | None = None,
        end: datetime | None = None,
        cursor: str | None = None,
        limit: int | None = None,
    ) -> BrokerResult[BrokerPage[BrokerBar]]:
        """Return one genuine bounded Yahoo history response."""
        del cursor
        if limit is None or limit <= 0:
            raise ValueError("positive Yahoo history limit is required")
        table = await self._transport.history(
            symbol=symbol,
            timeframe=timeframe,
            start=start,
            end=end,
        )
        page = _map_history(
            table,
            symbol=symbol,
            timeframe=timeframe,
            limit=limit,
        )
        return self._result(BrokerCapabilityId.GET_HISTORICAL_BARS, data=page)

    async def get_platform_info(self) -> BrokerResult[BrokerPlatformInfo]:
        """Return redacted research-only provider metadata."""
        return self._result(
            BrokerCapabilityId.GET_PLATFORM_INFO,
            data=BrokerPlatformInfo(
                broker_id=self._config.broker_id,
                provider_name="Yahoo Finance",
                product_profile="yfinance_history",
                environment=self._config.environment,
                observed_at=datetime.now(UTC),
                endpoint_metadata={"research_only": True},
            ),
        )
