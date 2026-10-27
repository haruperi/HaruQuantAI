"""Yahoo Finance historical market data source."""

from __future__ import annotations

from typing import Any, override

from ._base import BaseSource

__all__ = ["Yahoo"]


class Yahoo(BaseSource):
    """Yahoo Finance equity and ETF historical market data source."""

    source_id = "yahoo"
    default_category = "Stocks"

    @override
    def add(
        self,
        definitions_or_provider: list[dict[str, Any]] | str,
        definitions: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """Register Yahoo Finance dataset definitions."""
        if isinstance(definitions_or_provider, str):
            return super().add(definitions_or_provider, definitions or [])
        return super().add(self.source_id, definitions_or_provider)
