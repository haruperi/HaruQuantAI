"""StrategyQuant historical market data source (Equity and Futures)."""

from __future__ import annotations

from typing import Any, override

from ._base import BaseSource

__all__ = ["SQData"]


class SQData(BaseSource):
    """StrategyQuant historical market data source for both Equity and Futures."""

    default_category = "Stocks"

    def __init__(
        self,
        kind: str = "equity",
        gateway: Any = None,
        *,
        market_root: Any = None,
        client_factory: Any = None,
    ) -> None:
        super().__init__(
            gateway, market_root=market_root, client_factory=client_factory
        )
        self.source_id = "sq_futures" if "future" in kind.lower() else "sq_equity"
        self.default_category = (
            "Futures" if self.source_id == "sq_futures" else "Stocks"
        )

    @override
    def add(
        self,
        definitions_or_provider: list[dict[str, Any]] | str,
        definitions: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """Register StrategyQuant dataset definitions."""
        if isinstance(definitions_or_provider, str):
            return super().add(definitions_or_provider, definitions or [])
        return super().add(self.source_id, definitions_or_provider)
