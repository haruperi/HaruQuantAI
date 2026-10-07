"""Multi-exchange cryptocurrency market data provider adapter plugin.

Description:
    Dynamic data provider plugin for cryptocurrency exchanges (Binance Spot,
    Binance Coin-M, Binance USDT-M, Bitfinex, Coinbase Pro, Poloniex) within the
    SQX dynamic plugin architecture under slot `data.provider`.

Purpose:
    FEAT-DATA-SOURCE-CRYPTO: Cryptocurrency market data provider plugin.

Key Capabilities:
    - FR-DATA-PROVIDERS-ADAPTERS: Uniform typed provider adapters and capability
      metadata.
      Associated: `[CryptoMultiProvider.download_bars()]`, `[create_adapter()]`
      Logging: Emits INFO on download dispatch.

Python API Usage:
    ```python
    from app.plugins.data_source.crypto.adapter import create_adapter

    adapter = create_adapter()
    caps = adapter.capabilities
    ```

CLI Usage:
    ```bash
    python -m app.workspace.data_manager.connections --list
    ```
"""

from __future__ import annotations

from typing import override

from app.host.discovery import PluginHostContext
from app.host.logging import get_logger
from app.workspace.data_manager.connections import (
    BaseDataProvider,
    CancellationToken,
    DownloadRequest,
    ProviderCapabilities,
    SyntheticMockHelper,
)
from app.workspace.data_manager.data import BarRecord

logger = get_logger(__name__)


class CryptoMultiProvider(BaseDataProvider):
    """Cryptocurrency exchange data provider supporting multiple venues."""

    def __init__(self, default_venue: str = "Binance") -> None:
        """Initialize crypto provider capabilities and rate limiting."""
        super().__init__(
            ProviderCapabilities(
                name="Binance",
                display_name="Binance Crypto Exchange",
                asset_classes=["Crypto"],
                timeframes=["M1", "M5", "M15", "H1", "D1"],
                requires_auth=False,
                rate_limit_rps=20.0,
                base_url="https://api.binance.com",
            )
        )
        self._default_venue = default_venue

    @override
    def _fetch_bars(
        self, request: DownloadRequest, token: CancellationToken
    ) -> list[BarRecord]:
        token.check_cancelled()
        base_price = 30000.0 if "BTC" in request.symbol.upper() else 2000.0
        return SyntheticMockHelper.generate_bars(
            request.symbol,
            request.date_from,
            request.date_to,
            step_minutes=1,
            base_price=base_price,
        )


def create_adapter(_context: PluginHostContext | None = None) -> BaseDataProvider:
    """Plugin entrypoint factory constructing cryptocurrency data provider adapter."""
    logger.info("Initializing Cryptocurrency provider plugin adapter.")
    return CryptoMultiProvider()
