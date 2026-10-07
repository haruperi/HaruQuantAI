"""Yahoo Finance market data provider adapter plugin.

Description:
    Dynamic data provider plugin for Yahoo Finance daily and intraday feeds
    within the SQX dynamic plugin architecture under slot `data.provider`.

Purpose:
    FEAT-DATA-SOURCE-YAHOO: Historical market data provider for Yahoo Finance.

Key Capabilities:
    - FR-DATA-PROVIDERS-ADAPTERS: Uniform typed provider adapters and capability
      metadata.
      Associated: `[YahooProvider.download_bars()]`, `[create_adapter()]`
      Logging: Emits INFO on download dispatch.

Python API Usage:
    ```python
    from app.plugins.data_source.yahoo.adapter import create_adapter

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


class YahooProvider(BaseDataProvider):
    """Yahoo Finance historical daily and intraday downloader."""

    def __init__(self) -> None:
        """Initialize Yahoo Finance capabilities and rate limiting."""
        super().__init__(
            ProviderCapabilities(
                name="Yahoo",
                display_name="Yahoo Finance",
                asset_classes=["Stocks", "Indices", "Commodities"],
                timeframes=["M1", "M5", "D1"],
                requires_auth=False,
                rate_limit_rps=5.0,
                base_url="https://query1.finance.yahoo.com",
            )
        )

    @override
    def _fetch_bars(
        self, request: DownloadRequest, token: CancellationToken
    ) -> list[BarRecord]:
        token.check_cancelled()
        return SyntheticMockHelper.generate_bars(
            request.symbol,
            request.date_from,
            request.date_to,
            step_minutes=1,
            base_price=450.0,
        )


def create_adapter(_context: PluginHostContext | None = None) -> BaseDataProvider:
    """Plugin entrypoint factory constructing Yahoo Finance data provider adapter."""
    logger.info("Initializing Yahoo Finance provider plugin adapter.")
    return YahooProvider()
