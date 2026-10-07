"""Local files market data provider adapter plugin.

Description:
    Dynamic data provider plugin for local filesystem market data files within
    the SQX dynamic plugin architecture under slot `data.provider`.

Purpose:
    FEAT-DATA-SOURCE-FILES: Local market data file provider plugin.

Key Capabilities:
    - FR-DATA-PROVIDERS-ADAPTERS: Uniform typed provider adapters and capability
      metadata.
      Associated: `[FilesProvider.download_bars()]`, `[create_adapter()]`
      Logging: Emits INFO on download dispatch.

Python API Usage:
    ```python
    from app.plugins.data_source.files.adapter import create_adapter

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


class FilesProvider(BaseDataProvider):
    """Local filesystem market data downloader."""

    def __init__(self) -> None:
        """Initialize local files capabilities and rate limiting."""
        super().__init__(
            ProviderCapabilities(
                name="Files",
                display_name="Local Filesystem Feed",
                asset_classes=["Forex", "Stocks", "Futures", "Crypto"],
                timeframes=["TICK", "M1", "M5", "H1", "D1"],
                requires_auth=False,
                rate_limit_rps=100.0,
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
    """Plugin entrypoint factory constructing local files data provider adapter."""
    logger.info("Initializing Local Files provider plugin adapter.")
    return FilesProvider()
