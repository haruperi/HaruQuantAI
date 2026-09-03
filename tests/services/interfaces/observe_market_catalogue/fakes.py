"""Shared fakes for observe-market-catalogue gateway tests."""

from __future__ import annotations

from uuid import uuid7

from app.contracts.catalogue.errors import CatalogueFailure
from app.contracts.catalogue.models import (
    CatalogInstrumentsRequest,
    CatalogInstrumentsSuccess,
    InstrumentVersion,
    OrderConstraints,
)
from app.contracts.common.models import ProblemDetails


def make_instrument(
    symbol: str, name: str | None = None, digits: int = 5
) -> InstrumentVersion:
    """Build one canonical instrument version fixture."""
    return InstrumentVersion(
        instrument_id=str(uuid7()),
        version=1,
        symbol=symbol,
        display_name=name or f"{symbol} Instrument",
        asset_class="FOREX",
        base_currency="EUR",
        quote_currency="USD",
        settlement_currency="USD",
        point_value="1",
        tick_size="0.00001",
        price_decimals=digits,
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


class FakeCatalogueProvider:
    """In-memory catalogue.catalog-instruments provider."""

    def __init__(
        self,
        pages: dict[str, tuple[InstrumentVersion, ...]],
        fail: bool = False,
    ) -> None:
        """Store scripted pages and record received requests."""
        self.pages = pages
        self.fail = fail
        self.requests: list[CatalogInstrumentsRequest] = []

    async def catalog_instruments(
        self,
        request: CatalogInstrumentsRequest,
    ) -> CatalogInstrumentsSuccess | CatalogueFailure:
        """Serve the scripted page or a structured failure."""
        self.requests.append(request)
        if self.fail:
            return CatalogueFailure(
                request_id=request.request_id,
                code="CAPABILITY_UNAVAILABLE",
                problem=ProblemDetails(
                    title="Catalogue unavailable",
                    status=503,
                    code="CAPABILITY_UNAVAILABLE",
                    detail="The catalogue store is not reachable.",
                ),
            )
        cursor = request.page_cursor or ""
        instruments = self.pages.get(cursor, ())
        next_cursor = f"{cursor}-page2" if cursor == "" and instruments else None
        return CatalogInstrumentsSuccess(
            request_id=request.request_id,
            instruments=instruments,
            next_cursor=next_cursor,
        )
