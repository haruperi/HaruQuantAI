"""Private persistence and HTTP schemas for account watchlists."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime
from typing import Self

from pydantic import BaseModel, ConfigDict, field_validator


class WatchlistItem(BaseModel):
    """One symbol entry within a watchlist."""

    model_config = ConfigDict(extra="forbid", frozen=True)
    source_id: str
    symbol: str
    sort_order: int


class Watchlist(BaseModel):
    """One account-owned named, ordered collection of watched symbols."""

    model_config = ConfigDict(extra="forbid", frozen=True)
    watchlist_id: str
    account_id: str
    name: str
    is_default: bool
    sort_order: int
    items: tuple[WatchlistItem, ...]
    created_at: datetime
    updated_at: datetime

    @field_validator("watchlist_id", "account_id", "name")
    @classmethod
    def _validate_text(cls, value: str) -> str:
        """Validate one required trimmed text field.

        Args:
            value: Candidate text.

        Returns:
            Validated text.

        Raises:
            ValueError: If the value is empty or padded.
        """
        if not value or value != value.strip():
            raise ValueError("watchlist text fields must be non-empty and trimmed")
        return value

    @classmethod
    def from_row(
        cls, row: Mapping[str, object], items: tuple[WatchlistItem, ...]
    ) -> Self:
        """Build one watchlist from a persisted row and item rows.

        Args:
            row: Normalized watchlist persistence row.
            items: Pre-grouped item rows owned by this watchlist.

        Returns:
            Validated watchlist.
        """
        return cls(
            watchlist_id=str(row["watchlist_id"]),
            account_id=str(row["account_id"]),
            name=str(row["name"]),
            is_default=bool(row["is_default"]),
            sort_order=int(str(row["sort_order"])),
            items=items,
            created_at=datetime.fromisoformat(str(row["created_at"])),
            updated_at=datetime.fromisoformat(str(row["updated_at"])),
        )


class _WatchlistCreate(BaseModel):
    """New watchlist request body."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    name: str


class _WatchlistUpdate(BaseModel):
    """Partial watchlist update request body.

    Each present field applies independently: a caller may rename, replace
    the item list, promote to default, or any combination, in one request.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    name: str | None = None
    symbols: tuple[str, ...] | None = None
    is_default: bool | None = None


__all__ = ("Watchlist", "WatchlistItem")
