"""MetaTrader 5 market data provider adapter plugin.

Description:
    Dynamic data provider plugin for MetaTrader 5 terminal connector within the
    SQX dynamic plugin architecture under slot `data.provider`.

Purpose:
    FEAT-DATA-SOURCE-METATRADER: Historical market data provider for MetaTrader.

Key Capabilities:
    - FR-DATA-PROVIDERS-ADAPTERS: Uniform typed provider adapters and capability
      metadata.
      Associated: `[MT5Provider.download_bars()]`, `[create_adapter()]`
      Logging: Emits INFO on download dispatch.

Python API Usage:
    ```python
    from app.plugins.data_source.metatrader.adapter import create_adapter

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


class MT5Provider(BaseDataProvider):
    """MetaTrader 5 terminal connector downloader."""

    def __init__(self) -> None:
        """Initialize MetaTrader 5 capabilities and rate limiting."""
        super().__init__(
            ProviderCapabilities(
                name="MetaTrader5",
                display_name="MetaTrader 5 Connector",
                asset_classes=["Forex", "Futures", "Indices", "Stocks"],
                timeframes=["M1", "M5", "M15", "H1", "D1"],
                requires_auth=False,
                rate_limit_rps=50.0,
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
    """Plugin entrypoint factory constructing the MetaTrader data provider adapter."""
    logger.info("Initializing MetaTrader 5 provider plugin adapter.")
    return MT5Provider()
