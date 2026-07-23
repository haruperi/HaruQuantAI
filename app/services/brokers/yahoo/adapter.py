"""Research-only Yahoo historical-bars adapter."""

from collections.abc import Mapping
from datetime import UTC, datetime
from typing import override

from app.services.brokers.contracts import (
    BrokerBar,
    BrokerCapability,
    BrokerCapabilityId,
    BrokerConnectionConfig,
    BrokerConnectionState,
    BrokerEnvironment,
    BrokerError,
    BrokerErrorCode,
    BrokerPage,
    BrokerPlatformInfo,
    BrokerResult,
)
from app.services.brokers.contracts.protocols import _UnsupportedAdapterBase
from app.services.brokers.yahoo.mapping import _map_history, _provider_interval
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
        """Initialize the YahooBrokerAdapter instance.

        Args:
            config: Value supplied to the operation.
            capabilities: Value supplied to the operation.
            transport: Value supplied to the operation.

        Raises:
            ValueError: If the documented operation cannot complete.
        """
        if config.environment != BrokerEnvironment.SANDBOX:
            raise ValueError("Yahoo is sandbox-only")
        if config.credentials or config.account_reference or config.endpoint:
            raise ValueError("Yahoo accepts no credentials, account, or endpoint")
        super().__init__(config, capabilities)
        self._transport = transport or _YahooTransport(
            config, self._record_provider_latency
        )

    @override
    async def connect(self) -> BrokerResult[None]:
        """Verify the provider using the caller's configured probe symbol.

        No probe symbol is ever assumed: a hidden default provider symbol is
        prohibited by this domain's boundary.

        Returns:
            Canonical verified connection result.
        """
        await self._transition(BrokerConnectionState.CONNECTING)
        if self._config.probe_symbol is None:
            await self._transition(
                BrokerConnectionState.FAILED, reason="probe_symbol_required"
            )
            return self._error(
                BrokerCapabilityId.CONNECT,
                BrokerErrorCode.BROKER_CONFIGURATION_INVALID,
            )
        try:
            await self._probe()
        except (OSError, TimeoutError, ValueError, ConnectionError) as error:
            await self._transition(
                BrokerConnectionState.FAILED, reason=type(error).__name__
            )
            return self._error(
                BrokerCapabilityId.CONNECT,
                BrokerErrorCode.BROKER_CONNECTION_FAILED,
            )
        self._session_generation += 1
        await self._transition(BrokerConnectionState.READY)
        return self._result(BrokerCapabilityId.CONNECT)

    @override
    async def is_connected(self) -> BrokerResult[bool]:
        """Re-run the explicit provider probe for current connectivity evidence.

        Returns:
            Canonical current connectivity evidence.
        """
        if self._config.probe_symbol is None:
            return self._result(BrokerCapabilityId.IS_CONNECTED, data=False)
        await self._probe()
        return self._result(BrokerCapabilityId.IS_CONNECTED, data=True)

    async def ping(self) -> BrokerResult[None]:
        """Run the configured explicit provider probe.

        Returns:
            Canonical provider-health result.
        """
        if self._config.probe_symbol is None:
            return self._error(
                BrokerCapabilityId.PING,
                BrokerErrorCode.BROKER_CONFIGURATION_INVALID,
            )
        await self._probe()
        return self._result(BrokerCapabilityId.PING)

    async def get_historical_bars(
        self,
        symbol: str,
        timeframe: str,
        start: datetime | None = None,
        end: datetime | None = None,
        cursor: str | None = None,
        limit: int | None = None,
    ) -> BrokerResult[BrokerPage[BrokerBar]]:
        """Return one genuine bounded Yahoo history response.

        Raises:
            ValueError: If limit is not positive.
        """
        del cursor
        if limit is None or limit <= 0:
            raise ValueError("positive Yahoo history limit is required")
        provider_timeframe = _provider_interval(timeframe)
        table = await self._transport.history(
            symbol=symbol,
            timeframe=provider_timeframe,
            start=start,
            end=end,
        )
        page = _map_history(
            table,
            symbol=symbol,
            timeframe=provider_timeframe,
            limit=limit,
            requested_timeframe=timeframe,
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

    async def _probe(self) -> None:
        """Perform one genuine Yahoo call using only the caller's probe symbol.

        Raises:
            ValueError: If probe configuration or provider evidence is absent.
        """
        probe_symbol = self._config.probe_symbol
        if probe_symbol is None:
            raise ValueError("Yahoo probe_symbol is required")
        table = await self._transport.history(
            symbol=probe_symbol,
            timeframe="1d",
            start=None,
            end=None,
        )
        if getattr(table, "empty", False):
            raise ValueError("Yahoo probe returned no provider evidence")

    def _error[T](
        self, operation: BrokerCapabilityId, code: BrokerErrorCode
    ) -> BrokerResult[T]:
        """Build one canonical Yahoo failure result.

        Returns:
            Canonical error result.
        """
        error = BrokerError(
            code=code,
            message=f"Yahoo {operation.value} failed",
            capability=operation,
        )
        self._last_error = error
        return self._result(operation, error=error)
