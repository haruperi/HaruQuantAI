"""Contracts for categorized market-directory and explicit-symbol reads."""

from __future__ import annotations

from datetime import datetime

from pydantic import field_validator

from app.services.data.contracts._base import TracedOpenContract as _Contract


def _text(value: str) -> str:
    """Validate one required identifier.

    Args:
        value: Candidate identifier.

    Returns:
        Validated identifier.

    Raises:
        ValueError: If the value is empty or contains surrounding whitespace.
    """
    if not value or value != value.strip():
        raise ValueError("value must be a non-empty trimmed string")
    return value


def _optional_text(value: str | None) -> str | None:
    """Validate one optional identifier.

    Args:
        value: Candidate identifier.

    Returns:
        Validated identifier or ``None``.
    """
    return None if value is None else _text(value)


class MarketDirectoryRequest(_Contract):
    """Bounded request for one categorized market-directory page."""

    source_id: str
    query: str | None = None
    cursor: str | None = None
    limit: int
    request_id: str

    @field_validator("source_id", "request_id")
    @classmethod
    def _validate_required_text(cls, value: str) -> str:
        """Validate one required request field.

        Args:
            value: Candidate identifier.

        Returns:
            Validated identifier.
        """
        return _text(value)

    @field_validator("query", "cursor")
    @classmethod
    def _validate_optional_text(cls, value: str | None) -> str | None:
        """Validate one optional request field.

        Args:
            value: Candidate identifier.

        Returns:
            Validated identifier or ``None``.
        """
        return _optional_text(value)

    @field_validator("limit")
    @classmethod
    def _validate_limit(cls, value: int) -> int:
        """Validate the page limit.

        Args:
            value: Candidate page limit.

        Returns:
            Positive page limit.

        Raises:
            ValueError: If the limit is not positive.
        """
        if value <= 0:
            raise ValueError("limit must be positive")
        return value


class SymbolsQuoteRequest(_Contract):
    """Bounded request for an explicit, caller-known symbol list."""

    source_id: str
    symbols: tuple[str, ...]
    request_id: str

    @field_validator("source_id", "request_id")
    @classmethod
    def _validate_required_text(cls, value: str) -> str:
        """Validate one required request field.

        Args:
            value: Candidate identifier.

        Returns:
            Validated identifier.
        """
        return _text(value)

    @field_validator("symbols")
    @classmethod
    def _validate_symbols(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        """Validate a non-empty ordered symbol tuple.

        Args:
            value: Candidate symbol tuple.

        Returns:
            Validated symbol tuple.

        Raises:
            ValueError: If no symbols are supplied.
        """
        if not value:
            raise ValueError("symbols must be non-empty")
        return tuple(_text(item) for item in value)


class MarketDirectoryRow(_Contract):
    """One categorized tradable-symbol evidence row."""

    symbol: str
    name: str
    asset_class: str
    source_id: str
    digits: int | None = None
    last: float | None = None
    bid: float | None = None
    ask: float | None = None
    spread: float | None = None
    volume: float | None = None
    open: float | None = None
    high: float | None = None
    low: float | None = None
    close: float | None = None
    change: float | None = None
    change_percent: float | None = None


class MarketDirectory(_Contract):
    """Categorized market-directory page."""

    source_id: str
    rows: tuple[MarketDirectoryRow, ...]
    limit: int
    next_cursor: str | None = None
    revision: str
    generated_at: datetime
    request_id: str

    @field_validator("source_id", "revision", "request_id")
    @classmethod
    def _validate_required_text(cls, value: str) -> str:
        """Validate one required result field.

        Args:
            value: Candidate identifier.

        Returns:
            Validated identifier.
        """
        return _text(value)

    @field_validator("next_cursor")
    @classmethod
    def _validate_cursor(cls, value: str | None) -> str | None:
        """Validate the optional result cursor.

        Args:
            value: Candidate cursor.

        Returns:
            Validated cursor or ``None``.
        """
        return _optional_text(value)


__all__ = (
    "MarketDirectory",
    "MarketDirectoryRequest",
    "MarketDirectoryRow",
    "SymbolsQuoteRequest",
)
