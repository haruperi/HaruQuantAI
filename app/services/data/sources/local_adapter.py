"""Explicitly configured local CSV/Parquet market-data source."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import TYPE_CHECKING, Literal, override

from app.services.data.contracts import DataError
from app.services.data.local_datasets.contracts import DatasetLoadRequest
from app.services.data.market_data.symbol_metadata import (
    SymbolListRequest,
    SymbolMetadata,
    SymbolMetadataRequest,
    SymbolPage,
)
from app.services.data.persistence.dataset_writer import load_dataset
from app.services.data.sources.contracts import (
    RawSourceBatch,
    SourceReadRequest,
)
from app.services.data.sources.protocol import MarketDataSource
from app.utils import logger

if TYPE_CHECKING:
    from app.services.data.contracts.dataset import CanonicalRecord


class LocalMarketDataSource(MarketDataSource):
    """Read only explicitly rooted files with caller-supplied symbol metadata."""

    def __init__(
        self,
        *,
        source_id: str,
        raw_root: Path,
        metadata: Mapping[str, SymbolMetadata],
        format_preference: Literal["csv", "parquet"] = "csv",
    ) -> None:
        """Initialize an explicit local source without environment fallbacks.

        Args:
            source_id: DATA source identity represented by this instance.
            raw_root: Existing approved absolute raw-data directory.
            metadata: Authoritative metadata keyed by canonical symbol.
            format_preference: Preferred supported artifact format.

        Raises:
            ValueError: If the source identity or root is invalid.
        """
        logger.info("Initializing explicitly rooted local source %s", source_id)
        if not source_id or source_id != source_id.strip():
            raise ValueError("source_id must be a non-empty trimmed string")
        resolved_root = raw_root.resolve()
        if not raw_root.is_absolute() or not resolved_root.is_dir():
            raise ValueError("raw_root must be an existing absolute directory")
        if any(item.source_id != source_id for item in metadata.values()):
            raise ValueError("metadata source_id must match the local source")
        self._source_id = source_id
        self._raw_root = resolved_root
        self._metadata = dict(metadata)
        self._format_preference = format_preference

    def _artifact(
        self,
        symbol: str,
        timeframe: str | None = None,
    ) -> tuple[Path, Literal["csv", "parquet"]]:
        """Resolve one symbol artifact within the configured root.

        A timeframe-scoped stem is preferred so several timeframes for one symbol
        remain individually addressable; the bare symbol stem is the fallback for
        artifacts without a timeframe, such as ticks and spreads.

        Args:
            symbol: Provider symbol whose artifact is required.
            timeframe: Optional bar timeframe scoping the artifact stem.

        Returns:
            The resolved artifact path and its supported format.

        Raises:
            DataError: If no artifact exists for any candidate stem.
        """
        logger.debug("Resolving local artifact for symbol %s", symbol)
        stems = [symbol] if timeframe is None else [f"{symbol}_{timeframe}", symbol]
        for stem in stems:
            parquet_path = self._raw_root / f"{stem}.parquet"
            csv_path = self._raw_root / f"{stem}.csv"
            if parquet_path.exists() and (
                self._format_preference == "parquet" or not csv_path.exists()
            ):
                return parquet_path, "parquet"
            if csv_path.exists():
                return csv_path, "csv"
        raise DataError("DATA_NOT_FOUND", safe_details={"field": "symbol"})

    @override
    def fetch(self, request: SourceReadRequest) -> RawSourceBatch:
        """Load an exact local artifact through the governed dataset boundary."""
        logger.info("Fetching local data for source %s", self._source_id)
        if request.source_id != self._source_id:
            raise DataError(
                "INVALID_INPUT",
                safe_details={"field": "source_id"},
                request_id=request.request_id,
            )
        artifact, data_format = self._artifact(
            request.provider_symbol,
            request.timeframe,
        )
        data_directory = self._raw_root.parents[1]
        relative_path = artifact.relative_to(data_directory)
        dataset = load_dataset(
            DatasetLoadRequest(
                relative_path=relative_path,
                format=data_format,
                request_id=request.request_id,
            )
        )
        if dataset.symbol != request.provider_symbol:
            raise DataError(
                "FILE_CORRUPTED",
                safe_details={"field": "symbol"},
                request_id=request.request_id,
            )
        if dataset.data_kind != request.data_kind:
            raise DataError(
                "FILE_CORRUPTED",
                safe_details={"field": "data_kind"},
                request_id=request.request_id,
            )
        if not dataset.records:
            raise DataError("EMPTY_RESULT", request_id=request.request_id)
        selected = self._select(dataset.records, request)
        if not selected:
            raise DataError("EMPTY_RESULT", request_id=request.request_id)
        return RawSourceBatch(
            source_id=request.source_id,
            provider_symbol=request.provider_symbol,
            data_kind=request.data_kind,
            records=tuple(record.model_dump() for record in selected),
            retrieved_at=dataset.available_at,
            revision=dataset.normalization_version,
            request_id=request.request_id,
        )

    @staticmethod
    def _select(
        records: Sequence[CanonicalRecord],
        request: SourceReadRequest,
    ) -> tuple[CanonicalRecord, ...]:
        """Apply the requested UTC window and record limit at the source boundary.

        Bounds are inclusive of `start` and exclusive of `end`, matching the
        half-open convention used across DATA range handling. The limit keeps the
        earliest records so a bounded read stays deterministic.

        Args:
            records: Canonical records loaded from the artifact.
            request: Bounded source read request supplying range and limit.

        Returns:
            The records inside the requested window, truncated to the limit.
        """
        logger.debug("Applying local range and limit selection")
        selected = tuple(
            record
            for record in records
            if (request.start is None or record.timestamp >= request.start)
            and (request.end is None or record.timestamp < request.end)
        )
        return selected[: request.limit]

    @override
    def list_symbols(self, request: SymbolListRequest) -> SymbolPage:
        """Return a stable, cursor-bounded page of configured local symbols."""
        logger.info("Listing symbols for local source %s", self._source_id)
        if request.source_id != self._source_id:
            raise DataError(
                "INVALID_INPUT",
                safe_details={"field": "source_id"},
                request_id=request.request_id,
            )
        symbols = sorted(
            symbol
            for symbol in self._metadata
            if request.query is None or request.query.casefold() in symbol.casefold()
        )
        if request.cursor is not None:
            if request.cursor not in symbols:
                raise DataError(
                    "INVALID_INPUT",
                    safe_details={"field": "cursor"},
                    request_id=request.request_id,
                )
            symbols = symbols[symbols.index(request.cursor) + 1 :]
        has_more = len(symbols) > request.limit
        items = tuple(symbols[: request.limit])
        return SymbolPage(
            source_id=request.source_id,
            items=items,
            limit=request.limit,
            next_cursor=items[-1] if has_more and items else None,
            revision="v1",
            request_id=request.request_id,
        )

    @override
    def get_symbol_metadata(self, request: SymbolMetadataRequest) -> SymbolMetadata:
        """Return caller-supplied authoritative metadata for one local symbol."""
        logger.info("Reading configured local metadata for source %s", self._source_id)
        if request.source_id != self._source_id:
            raise DataError(
                "INVALID_INPUT",
                safe_details={"field": "source_id"},
                request_id=request.request_id,
            )
        metadata = self._metadata.get(request.symbol)
        if metadata is None:
            raise DataError(
                "MISSING_ASSET_METADATA",
                safe_details={"field": "symbol"},
                request_id=request.request_id,
            )
        return metadata


__all__ = ["LocalMarketDataSource"]
