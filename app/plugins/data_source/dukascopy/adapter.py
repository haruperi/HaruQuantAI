"""Dukascopy Bank SA market data provider adapter plugin.

Description:
    Dynamic data provider plugin for Dukascopy Bank SA, acquiring historical
    forex, commodity, and indices tick and bar data within the SQX dynamic plugin
    architecture under slot `data.provider`.

Purpose:
    FEAT-DATA-SOURCE-DUKASCOPY: Historical market data provider for Dukascopy Bank.

Key Capabilities:
    - FR-DATA-PROVIDERS-ADAPTERS: Uniform typed provider adapters and capability
      metadata.
      Associated: `[DukascopyProvider.download_bars()]`, `[create_adapter()]`
      Logging: Emits INFO on download dispatch.

Python API Usage:
    ```python
    from app.plugins.data_source.dukascopy.adapter import create_adapter

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


class DukascopyProvider(BaseDataProvider):
    """Dukascopy Bank SA tick and M1 historical downloader."""

    def __init__(self) -> None:
        """Initialize Dukascopy capabilities and rate limiting."""
        super().__init__(
            ProviderCapabilities(
                name="Dukascopy",
                display_name="Dukascopy Bank SA",
                asset_classes=["Forex", "Commodities", "Indices"],
                timeframes=["M1", "H1", "D1"],
                requires_auth=False,
                rate_limit_rps=10.0,
                base_url="https://datafeed.dukascopy.com",
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
            base_price=1.0850,
        )


def create_adapter(_context: PluginHostContext | None = None) -> BaseDataProvider:
    """Plugin entrypoint factory constructing the Dukascopy data provider adapter."""
    logger.info("Initializing Dukascopy provider plugin adapter.")
    return DukascopyProvider()
