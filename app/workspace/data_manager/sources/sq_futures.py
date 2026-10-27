"""StrategyQuant Futures historical market data source."""

from __future__ import annotations

from typing import Any, override

from ._base import BaseSource

__all__ = ["SQFutures"]


class SQFutures(BaseSource):
    """StrategyQuant Futures daily historical data source."""

    source_id = "sq_futures"
    default_category = "Futures"

    @override
    def add(
        self,
        definitions_or_provider: list[dict[str, Any]] | str,
        definitions: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """Register StrategyQuant Futures dataset definitions."""
        if isinstance(definitions_or_provider, str):
            return super().add(definitions_or_provider, definitions or [])
        return super().add(self.source_id, definitions_or_provider)
