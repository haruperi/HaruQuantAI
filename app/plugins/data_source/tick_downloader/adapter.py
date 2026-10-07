"""Tick Data Downloader market data provider adapter plugin.

Description:
    Dynamic data provider plugin for tick and high-precision trade data within
    the SQX dynamic plugin architecture under slot `data.provider`.

Purpose:
    FEAT-DATA-SOURCE-TICKDOWNLOADER: Tick market data provider plugin.

Key Capabilities:
    - FR-DATA-PROVIDERS-ADAPTERS: Uniform typed provider adapters and capability
      metadata.
      Associated: `[TickDownloaderProvider.download_bars()]`, `[create_adapter()]`
      Logging: Emits INFO on download dispatch.

Python API Usage:
    ```python
    from app.plugins.data_source.tick_downloader.adapter import create_adapter

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


class TickDownloaderProvider(BaseDataProvider):
    """Tick data downloader."""

    def __init__(self) -> None:
        """Initialize tick downloader capabilities and rate limiting."""
        super().__init__(
            ProviderCapabilities(
                name="TickDownloader",
                display_name="Tick Data Downloader",
                asset_classes=["Forex", "Futures", "Crypto"],
                timeframes=["TICK", "M1"],
                requires_auth=False,
                rate_limit_rps=20.0,
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
            base_price=100.0,
        )


def create_adapter(_context: PluginHostContext | None = None) -> BaseDataProvider:
    """Plugin entrypoint factory constructing Tick Data Downloader provider adapter."""
    logger.info("Initializing Tick Data Downloader provider plugin adapter.")
    return TickDownloaderProvider()
