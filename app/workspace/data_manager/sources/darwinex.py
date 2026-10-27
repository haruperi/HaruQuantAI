"""Darwinex historical tick and bar market data source."""

from __future__ import annotations

from typing import Any, override

from ._base import BaseSource

__all__ = ["Darwinex"]


class Darwinex(BaseSource):
    """Darwinex tick and M1 bar market data source."""

    source_id = "darwinex"
    default_category = "Forex"

    @override
    def add(
        self,
        definitions_or_provider: list[dict[str, Any]] | str,
        definitions: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """Register Darwinex dataset definitions."""
        if isinstance(definitions_or_provider, str):
            return super().add(definitions_or_provider, definitions or [])
        return super().add(self.source_id, definitions_or_provider)
