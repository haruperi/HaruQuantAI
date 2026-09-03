"""Market catalogue browsing gateway: the capability provider.

Purpose:
    Project the Catalogue-owned instrument catalogue
    (``catalogue.catalog-instruments@1``) into the Interfaces browse
    contract: bounded catalogue pages with identity and precision fields,
    continuation cursors, and page-level revision identity. Live price
    fields stay null — the catalogue owns no market prices and none are
    invented.

Key capabilities:
    * Serve bounded LIST pages with continuation cursors.
    * Clamp requested page sizes to the configured maximum.
    * Fail closed with CAPABILITY_UNAVAILABLE after disposal.

Python API usage:
    gateway = MarketCatalogueGateway(provider, ObserveMarketCatalogueConfig())
    result = await gateway.observe_market_catalogue(request)

CLI usage:
    uv run python -m app.services.interfaces.observe_market_catalogue.gateway
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING
from uuid import uuid7

from app.contracts.catalogue.capabilities import CATALOG_INSTRUMENTS_CAPABILITY
from app.contracts.catalogue.models import (
    CatalogInstrumentsRequest,
    CatalogInstrumentsSuccess,
)
from app.contracts.common.models import ProblemDetails
from app.contracts.interfaces.errors import InterfaceFailure, InterfaceFailureCode
from app.contracts.interfaces.models import (
    MarketCatalogueEntry,
    ObserveMarketCatalogueRequest,
    ObserveMarketCatalogueSuccess,
)
from app.services.interfaces.observe_market_catalogue.config import (
    ObserveMarketCatalogueConfig,
)

if TYPE_CHECKING:
    from app.contracts.catalogue.models import InstrumentVersion
    from app.contracts.catalogue.ports import CatalogInstrumentsCapability

_TIMESTAMP_FORMAT = "%Y-%m-%dT%H:%M:%S.%fZ"
_PROVIDER_SOURCE_ID = CATALOG_INSTRUMENTS_CAPABILITY.identifier
_EXPECTED_PRICE_DECIMALS = 5


def _utc_now() -> str:
    """Return the current instant as a canonical wire timestamp.

    Returns:
        Fixed-width UTC timestamp string.
    """
    return datetime.now(UTC).strftime(_TIMESTAMP_FORMAT)


def _failure(
    request_id: str,
    code: InterfaceFailureCode,
    title: str,
    detail: str,
    status: int,
) -> InterfaceFailure:
    """Build a structured gateway failure envelope.

    Args:
        request_id: Echoed request identifier.
        code: Closed interface failure code.
        title: Short failure title.
        detail: Bounded human-readable failure detail.
        status: HTTP-equivalent status code.

    Returns:
        Structured InterfaceFailure envelope.
    """
    return InterfaceFailure(
        request_id=request_id,
        code=code,
        problem=ProblemDetails(
            title=title,
            status=status,
            code=code,
            detail=detail,
        ),
    )


def _project_entry(instrument: InstrumentVersion) -> MarketCatalogueEntry:
    """Project one catalogue instrument version into a browse row.

    Args:
        instrument: Canonical instrument version.

    Returns:
        Catalogue row with identity and precision; prices stay null.
    """
    return MarketCatalogueEntry(
        symbol=instrument.symbol,
        name=instrument.display_name,
        asset_class=instrument.asset_class,
        source_id=_PROVIDER_SOURCE_ID,
        digits=instrument.price_decimals,
    )


class MarketCatalogueGateway:
    """ObserveMarketCatalogueCapability provider for one mounted generation.

    The gateway resolves the Catalogue-owned capability through the
    feature context, never imports a Catalogue implementation, and adds
    no business policy: it projects catalogue pages and reports absence
    truthfully.
    """

    def __init__(
        self,
        provider: CatalogInstrumentsCapability,
        config: ObserveMarketCatalogueConfig,
    ) -> None:
        """Assemble the gateway around the resolved provider.

        Args:
            provider: Active catalogue.catalog-instruments provider.
            config: Feature configuration with page-size bounds.
        """
        self._provider = provider
        self._config = config
        self._closed = False

    @property
    def config(self) -> ObserveMarketCatalogueConfig:
        """Return the validated gateway configuration."""
        return self._config

    async def observe_market_catalogue(
        self,
        request: ObserveMarketCatalogueRequest,
    ) -> ObserveMarketCatalogueSuccess | InterfaceFailure:
        """Project one bounded catalogue page.

        Args:
            request: Operation-discriminated catalogue browse request.

        Returns:
            The projected catalogue page on success, otherwise a
            structured interface failure.
        """
        if self._closed:
            return _failure(
                request.request_id,
                "CAPABILITY_UNAVAILABLE",
                "Gateway unavailable",
                "The market catalogue gateway is disposed.",
                503,
            )
        page_size = min(request.page_size, self._config.max_page_size)
        provider_request = CatalogInstrumentsRequest(
            request_id=request.request_id,
            capability_snapshot_id=request.capability_snapshot_id,
            operation="LIST",
            page_size=page_size,
            page_cursor=request.page_cursor,
        )
        result = await self._provider.catalog_instruments(provider_request)
        if not isinstance(result, CatalogInstrumentsSuccess):
            failure = result
            return _failure(
                request.request_id,
                "CAPABILITY_UNAVAILABLE",
                "Catalogue unavailable",
                f"The catalogue provider failed: {failure.problem.detail}",
                503,
            )
        return ObserveMarketCatalogueSuccess(
            request_id=request.request_id,
            entries=tuple(
                _project_entry(instrument) for instrument in result.instruments
            ),
            next_cursor=result.next_cursor,
            revision=str(request.capability_snapshot_id),
            generated_at=_utc_now(),
        )

    def close(self) -> None:
        """Dispose the gateway; safe to call repeatedly."""
        self._closed = True


class _ScriptedCatalogueProvider:
    """Bounded in-memory provider for the usage demonstration."""

    def __init__(
        self,
        pages: dict[str, tuple[InstrumentVersion, ...]],
    ) -> None:
        """Store scripted pages keyed by cursor."""
        self._pages = pages

    async def catalog_instruments(
        self,
        request: CatalogInstrumentsRequest,
    ) -> CatalogInstrumentsSuccess:
        """Serve the scripted page for the requested cursor.

        Args:
            request: Catalogue request carrying the cursor.

        Returns:
            The scripted page success result.
        """
        cursor = request.page_cursor or ""
        instruments = self._pages.get(cursor, ())
        return CatalogInstrumentsSuccess(
            request_id=request.request_id,
            instruments=instruments,
            next_cursor=cursor + "next" if cursor == "" and instruments else None,
        )


def _instrument(symbol: str, name: str) -> InstrumentVersion:
    """Build one minimal instrument fixture for the demonstration.

    Args:
        symbol: Instrument symbol.
        name: Display name.

    Returns:
        Canonical instrument version fixture.
    """
    from app.contracts.catalogue.models import InstrumentVersion, OrderConstraints

    return InstrumentVersion(
        instrument_id=str(uuid7()),
        version=1,
        symbol=symbol,
        display_name=name,
        asset_class="FOREX",
        base_currency="EUR",
        quote_currency="USD",
        settlement_currency="USD",
        point_value="1",
        tick_size="0.00001",
        price_decimals=5,
        quantity_multiplier="1",
        order_constraints=OrderConstraints(
            min_quantity="0.01",
            max_quantity="100",
            quantity_step="0.01",
            min_order_distance="0",
            supported_order_types=("MARKET",),
            supported_time_in_force=("GTC",),
        ),
        default_spread="0.0001",
        exchange="OTC",
        timezone="UTC",
        session_id=str(uuid7()),
        effective_from="2026-01-01T00:00:00.000000Z",
        content_hash="a" * 64,
    )


def _browse_request(
    page_size: int, cursor: str | None = None
) -> ObserveMarketCatalogueRequest:
    """Build a demonstration LIST request.

    Args:
        page_size: Requested page size.
        cursor: Optional continuation cursor.

    Returns:
        Operation-discriminated LIST request.
    """
    return ObserveMarketCatalogueRequest(
        request_id=str(uuid7()),
        capability_snapshot_id=str(uuid7()),
        operation="LIST",
        page_size=page_size,
        page_cursor=cursor,
    )


def _page(
    result: ObserveMarketCatalogueSuccess | InterfaceFailure,
) -> ObserveMarketCatalogueSuccess:
    """Extract the page from a demonstration result.

    Args:
        result: Gateway browse result.

    Returns:
        The projected page.

    Raises:
        TypeError: When the result is a failure without a page.
    """
    if not isinstance(result, ObserveMarketCatalogueSuccess):
        raise TypeError("usage verification: page missing")
    return result


async def _run_usage_example() -> None:
    """Run the bounded public usage demonstration.

    Raises:
        RuntimeError: If any verified behavior differs from the contract.
        TypeError: If a verification result has an unexpected type.
    """
    provider = _ScriptedCatalogueProvider(
        {
            "": (
                _instrument("EURUSD", "Euro vs US Dollar"),
                _instrument("GBPUSD", "British Pound vs US Dollar"),
            )
        }
    )
    gateway = MarketCatalogueGateway(
        provider,
        ObserveMarketCatalogueConfig(default_page_size=2, max_page_size=2),
    )

    first = _page(await gateway.observe_market_catalogue(_browse_request(500)))
    if [entry.symbol for entry in first.entries] != ["EURUSD", "GBPUSD"]:
        raise RuntimeError("usage verification: page projection mismatch")
    if (
        first.entries[0].digits != _EXPECTED_PRICE_DECIMALS
        or first.entries[0].bid is not None
    ):
        raise RuntimeError("usage verification: price fields must stay null")
    if first.next_cursor != "next":
        raise RuntimeError("usage verification: cursor mismatch")

    second = _page(await gateway.observe_market_catalogue(_browse_request(2, "next")))
    if second.entries or second.next_cursor is not None:
        raise RuntimeError("usage verification: terminal page mismatch")

    gateway.close()
    closed = await gateway.observe_market_catalogue(_browse_request(2))
    if (
        not isinstance(closed, InterfaceFailure)
        or closed.code != "CAPABILITY_UNAVAILABLE"
    ):
        raise TypeError("usage verification: disposal did not fail closed")
    print(
        "Usage verification passed: "
        f"first_page={len(first.entries)} "
        f"cursor={first.next_cursor} "
        f"closed_code={closed.code}"
    )


if __name__ == "__main__":
    import asyncio

    asyncio.run(_run_usage_example())
