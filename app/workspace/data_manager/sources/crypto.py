"""Cryptocurrency exchanges historical market data source."""

from __future__ import annotations

from typing import Any, override

from ._base import BaseSource
from ._helpers import CRYPTO, provider_id

__all__ = ["Crypto"]


class Crypto(BaseSource):
    """Cryptocurrency exchange historical spot and futures market data source."""

    default_category = "Crypto"

    def __init__(
        self,
        exchange: str = "binance",
        gateway: Any = None,
        *,
        market_root: Any = None,
        client_factory: Any = None,
    ) -> None:
        super().__init__(
            gateway, market_root=market_root, client_factory=client_factory
        )
        self.source_id = provider_id(exchange) if exchange in CRYPTO else "binance"

    @override
    def add(
        self,
        definitions_or_provider: list[dict[str, Any]] | str,
        definitions: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """Register cryptocurrency exchange dataset definitions."""
        if isinstance(definitions_or_provider, str):
            return super().add(definitions_or_provider, definitions or [])
        return super().add(self.source_id, definitions_or_provider)
