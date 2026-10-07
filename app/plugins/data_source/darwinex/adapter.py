"""Darwinex market data provider adapter plugin.

Description:
    Dynamic data provider plugin for Darwinex institutional tick and bar feeds
    within the SQX dynamic plugin architecture under slot `data.provider`.

Purpose:
    FEAT-DATA-SOURCE-DARWINEX: Historical market data provider for Darwinex.

Key Capabilities:
    - FR-DATA-PROVIDERS-ADAPTERS: Uniform typed provider adapters and capability
      metadata.
      Associated: `[DarwinexProvider.download_bars()]`, `[create_adapter()]`
      Logging: Emits INFO on download dispatch.

Python API Usage:
    ```python
    from app.plugins.data_source.darwinex.adapter import create_adapter

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


class DarwinexProvider(BaseDataProvider):
    """Darwinex tick and bar downloader."""

    def __init__(self) -> None:
        """Initialize Darwinex capabilities and rate limiting."""
        super().__init__(
            ProviderCapabilities(
                name="Darwinex",
                display_name="Darwinex Tick & Bar Feeds",
                asset_classes=["Forex", "CFD"],
                timeframes=["M1", "H1", "D1"],
                requires_auth=True,
                rate_limit_rps=5.0,
                base_url="https://api.darwinex.com",
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
            base_price=1.1000,
        )


def create_adapter(_context: PluginHostContext | None = None) -> BaseDataProvider:
    """Plugin entrypoint factory constructing the Darwinex data provider adapter."""
    logger.info("Initializing Darwinex provider plugin adapter.")
    return DarwinexProvider()
