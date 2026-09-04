"""Market reference gateway: translating HTTP/interface requests to Data domain."""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.contracts.common.models import ProblemDetails
from app.contracts.data.errors import DataFailure
from app.contracts.data.models import BrowseReferenceRequest
from app.contracts.interfaces.errors import InterfaceFailure
from app.contracts.interfaces.models import (
    ObserveMarketReferenceRequest,
    ObserveMarketReferenceSuccess,
)

if TYPE_CHECKING:
    from app.contracts.data.ports import BrowseReferenceCapability
    from app.services.interfaces.observe_market_reference.config import (
        ObserveMarketReferenceConfig,
    )


def _failure_from_data(failure: DataFailure) -> InterfaceFailure:
    """Map one data failure into the interface failure envelope.

    Args:
        failure: Data-domain typed failure.

    Returns:
        Structured InterfaceFailure envelope.
    """
    return InterfaceFailure(
        request_id=failure.request_id,
        code="INTERFACE_VALIDATION_FAILED",
        problem=ProblemDetails(
            title=failure.problem.title,
            status=failure.problem.status,
            code=failure.problem.code or failure.code,
            detail=failure.problem.detail,
        ),
    )


class MarketReferenceGateway:
    """Capability provider implementing ObserveMarketReferenceCapability."""

    def __init__(
        self,
        config: ObserveMarketReferenceConfig,
        provider: BrowseReferenceCapability | None = None,
    ) -> None:
        """Initialize the market reference gateway.

        Args:
            config: Validated runtime configuration.
            provider: Optional browse reference capability provider.
        """
        self._config = config
        self._provider = provider
        self._closed = False

    @property
    def closed(self) -> bool:
        """Return True if the gateway has been disposed."""
        return self._closed

    async def close(self) -> None:
        """Dispose of the gateway."""
        self._closed = True

    async def observe_market_reference(
        self,
        request: ObserveMarketReferenceRequest,
    ) -> ObserveMarketReferenceSuccess | InterfaceFailure:
        """Translate and delegate market reference requests to BrowseReference.

        Args:
            request: Observe market reference request.

        Returns:
            ObserveMarketReferenceSuccess on success, or InterfaceFailure on error.
        """
        if self._closed:
            return InterfaceFailure(
                request_id=request.request_id,
                code="CAPABILITY_UNAVAILABLE",
                problem=ProblemDetails(
                    title="Capability Unavailable",
                    detail="The market reference gateway has been disposed.",
                    status=503,
                    code="CAPABILITY_UNAVAILABLE",
                ),
            )

        if self._provider is None:
            return InterfaceFailure(
                request_id=request.request_id,
                code="CAPABILITY_UNAVAILABLE",
                problem=ProblemDetails(
                    title="Capability Unavailable",
                    detail="Market reference capability is not mounted.",
                    status=503,
                    code="CAPABILITY_UNAVAILABLE",
                ),
            )

        browse_req = BrowseReferenceRequest(
            request_id=request.request_id,
            operation=request.operation,
            limit=request.limit,
            cursor=request.cursor,
            query=request.query,
            source_id=request.source_id,
            symbols=request.symbols,
            symbol=request.symbol,
            timeframe=request.timeframe,
            start=request.start,
            end=request.end,
            series_id=request.series_id,
            instrument=request.instrument,
            payload=request.payload,
        )
        result = await self._provider.browse_reference(browse_req)
        if isinstance(result, DataFailure):
            return _failure_from_data(result)
        return ObserveMarketReferenceSuccess(
            request_id=result.request_id,
            data=result.data,
        )


if __name__ == "__main__":
    import asyncio

    from app.services.interfaces.observe_market_reference.config import (
        ObserveMarketReferenceConfig,
    )

    async def main() -> None:
        """Execute bounded usage demonstration of MarketReferenceGateway."""
        gw = MarketReferenceGateway(config=ObserveMarketReferenceConfig())
        print("MarketReferenceGateway initialized successfully.")
        await gw.close()

    asyncio.run(main())
