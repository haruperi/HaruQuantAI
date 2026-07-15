"""Base market data source protocol definitions."""

from __future__ import annotations

import abc
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.services.data.contracts.sources import (
        RawSourceBatch,
        SourceReadRequest,
        SymbolListRequest,
        SymbolMetadata,
        SymbolMetadataRequest,
        SymbolPage,
    )


class MarketDataSource(abc.ABC):
    """Abstract base class defining the minimum read-only source behavior."""

    @abc.abstractmethod
    def fetch(self, request: SourceReadRequest) -> RawSourceBatch:
        """Fetch provider-neutral raw records and metadata.

        Args:
            request: Bounded source read parameters.

        Returns:
            Batch of raw records with retrieved metadata.

        Raises:
            DataError: If the source is unavailable or encounters a network timeout.
        """
        raise NotImplementedError

    @abc.abstractmethod
    def list_symbols(self, request: SymbolListRequest) -> SymbolPage:
        """List provider symbols with cursor pagination support.

        Args:
            request: Symbol-discovery filter and limit parameters.

        Returns:
            Sorted page of symbol strings with cursor evidence.

        Raises:
            DataError: If the limit is exceeded or the operation is unsupported.
        """
        raise NotImplementedError

    @abc.abstractmethod
    def get_symbol_metadata(self, request: SymbolMetadataRequest) -> SymbolMetadata:
        """Retrieve normalized symbol metadata.

        Args:
            request: Target symbol descriptor parameters.

        Returns:
            Normalized symbol metadata with provenance and missing-field catalog.

        Raises:
            DataError: If the symbol is not found or missing metadata.
        """
        raise NotImplementedError
