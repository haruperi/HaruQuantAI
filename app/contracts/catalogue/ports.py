"""Public capability protocols (ports) for Catalogue capabilities."""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    from app.contracts.catalogue.errors import CatalogueFailure
    from app.contracts.catalogue.models import (
        CatalogInstrumentsRequest,
        CatalogInstrumentsSuccess,
        ConvertCurrenciesRequest,
        ConvertCurrenciesSuccess,
        DefineSessionsRequest,
        DefineSessionsSuccess,
        DefineTradingRulesRequest,
        DefineTradingRulesSuccess,
        ExchangeCatalogueRequest,
        ExchangeCatalogueSuccess,
        ManageUniversesRequest,
        ManageUniversesSuccess,
        MapProvidersRequest,
        MapProvidersSuccess,
    )


@runtime_checkable
class CatalogInstrumentsCapability(Protocol):
    """Capability protocol for instrument catalogue operations."""

    async def catalog_instruments(
        self,
        request: CatalogInstrumentsRequest,
    ) -> CatalogInstrumentsSuccess | CatalogueFailure:
        """Manage and query versioned canonical instruments.

        Args:
            request: Operation-discriminated instrument catalogue request.

        Returns:
            The matching instrument versions, page cursor, or deletion flag
            on success, otherwise a structured catalogue failure.
        """
        ...


@runtime_checkable
class MapProvidersCapability(Protocol):
    """Capability protocol for provider and broker mapping operations."""

    async def map_providers(
        self,
        request: MapProvidersRequest,
    ) -> MapProvidersSuccess | CatalogueFailure:
        """Map provider and broker identities to canonical instruments.

        Args:
            request: Operation-discriminated provider mapping request.

        Returns:
            The resolved or persisted provider symbol mappings on success,
            otherwise a structured catalogue failure.
        """
        ...


@runtime_checkable
class DefineSessionsCapability(Protocol):
    """Capability protocol for session and calendar operations."""

    async def define_sessions(
        self,
        request: DefineSessionsRequest,
    ) -> DefineSessionsSuccess | CatalogueFailure:
        """Manage and preview effective trading intervals.

        Args:
            request: Operation-discriminated session and calendar request.

        Returns:
            The stored session or calendar version plus previewed effective
            intervals on success, otherwise a structured catalogue failure.
        """
        ...


@runtime_checkable
class DefineTradingRulesCapability(Protocol):
    """Capability protocol for trading rules and cost operations."""

    async def define_trading_rules(
        self,
        request: DefineTradingRulesRequest,
    ) -> DefineTradingRulesSuccess | CatalogueFailure:
        """Resolve rounding, distance, and default cost rules.

        Args:
            request: Operation-discriminated trading rules request.

        Returns:
            The rule set, normalized values, and resolved cost model on
            success, otherwise a structured catalogue failure.
        """
        ...


@runtime_checkable
class ManageUniversesCapability(Protocol):
    """Capability protocol for basket and universe operations."""

    async def manage_universes(
        self,
        request: ManageUniversesRequest,
    ) -> ManageUniversesSuccess | CatalogueFailure:
        """Version instrument sets and resolve timebound membership.

        Args:
            request: Operation-discriminated universe management request.

        Returns:
            The universe version or resolved members on success, otherwise
            a structured catalogue failure.
        """
        ...


@runtime_checkable
class ConvertCurrenciesCapability(Protocol):
    """Capability protocol for currency conversion graph queries."""

    async def convert_currencies(
        self,
        request: ConvertCurrenciesRequest,
    ) -> ConvertCurrenciesSuccess | CatalogueFailure:
        """Resolve a deterministic currency conversion path.

        Args:
            request: Currency conversion query request.

        Returns:
            The converted amount and its conversion path on success,
            otherwise a structured catalogue failure.
        """
        ...


@runtime_checkable
class ExchangeCatalogueCapability(Protocol):
    """Capability protocol for catalogue interchange operations."""

    async def exchange_catalogue(
        self,
        request: ExchangeCatalogueRequest,
    ) -> ExchangeCatalogueSuccess | CatalogueFailure:
        """Import and export versioned catalogue definitions.

        Args:
            request: Operation-discriminated catalogue interchange request.

        Returns:
            The exported package, imported references, and validation
            warnings on success, otherwise a structured catalogue failure.
        """
        ...
