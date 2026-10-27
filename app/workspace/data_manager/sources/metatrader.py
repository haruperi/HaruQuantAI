"""MetaTrader 5 historical market data bridge source."""

from __future__ import annotations

from typing import Any, override

from ._base import BaseSource

__all__ = ["MT5", "MetaTrader"]


class MetaTrader(BaseSource):
    """MetaTrader 5 broker terminal historical market data bridge source."""

    source_id = "mt5"
    default_category = "Forex"

    @override
    def add(
        self,
        definitions_or_provider: list[dict[str, Any]] | str,
        definitions: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """Register MetaTrader 5 dataset definitions."""
        if isinstance(definitions_or_provider, str):
            return super().add(definitions_or_provider, definitions or [])
        return super().add(self.source_id, definitions_or_provider)


MT5 = MetaTrader
