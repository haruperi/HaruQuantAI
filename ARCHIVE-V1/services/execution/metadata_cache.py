"""Symbol metadata cache models for pre-submit execution validation.

Classes and functions:
    SymbolMetadataCacheEntry: Class. Provides SymbolMetadataCacheEntry behavior for execution workflows.
    SymbolMetadataCache: Class. Provides SymbolMetadataCache behavior for execution workflows.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class SymbolMetadataCacheEntry(BaseModel):
    """Cached symbol metadata required by execution readiness checks."""

    model_config = ConfigDict(extra="forbid")

    snapshot_id: str = Field(min_length=1)
    symbol: str = Field(min_length=1)
    observed_at: datetime
    market_open: bool
    tradable: bool
    supported_fill_modes: tuple[str, ...]
    stop_level_points: int = Field(ge=0)
    freeze_level_points: int = Field(ge=0)
    tick_size: float = Field(gt=0.0)
    point_value: float = Field(gt=0.0)
    contract_size: float = Field(gt=0.0)
    max_age_seconds: int = Field(gt=0)


class SymbolMetadataCache:
    """Small in-memory metadata cache keyed by symbol."""

    def __init__(self) -> None:
        self._entries: dict[str, SymbolMetadataCacheEntry] = {}

    def put(self, entry: SymbolMetadataCacheEntry) -> SymbolMetadataCacheEntry:
        """Perform the put execution service operation."""
        self._entries[entry.symbol] = entry
        return entry

    def get(self, symbol: str) -> SymbolMetadataCacheEntry | None:
        """Perform the get execution service operation."""
        return self._entries.get(symbol)

    def get_many(self, symbols: tuple[str, ...]) -> dict[str, SymbolMetadataCacheEntry]:
        """Perform the get_many execution service operation."""
        return {
            symbol: entry
            for symbol in symbols
            if (entry := self._entries.get(symbol)) is not None
        }
