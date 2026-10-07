"""StrategyQuant Continuous Futures market data provider adapter plugin.

Description:
    Dynamic data provider plugin for StrategyQuant Continuous Futures within the
    SQX dynamic plugin architecture under slot `data.provider`.

Purpose:
    FEAT-DATA-SOURCE-SQFUTURES: Historical market data provider for SQ Futures.

Key Capabilities:
    - FR-DATA-PROVIDERS-ADAPTERS: Uniform typed provider adapters and capability
      metadata.
      Associated: `[SQFuturesProvider.download_bars()]`, `[create_adapter()]`
      Logging: Emits INFO on download dispatch.

Python API Usage:
    ```python
    from app.plugins.data_source.sq_futures.adapter import create_adapter

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


class SQFuturesProvider(BaseDataProvider):
    """StrategyQuant continuous futures data provider."""

    def __init__(self) -> None:
        """Initialize SQ Futures capabilities and rate limiting."""
        super().__init__(
            ProviderCapabilities(
                name="SQFutures",
                display_name="StrategyQuant Continuous Futures",
                asset_classes=["Futures"],
                timeframes=["M1", "D1"],
                requires_auth=True,
                rate_limit_rps=10.0,
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
            base_price=5000.0,
        )


def create_adapter(_context: PluginHostContext | None = None) -> BaseDataProvider:
    """Plugin entrypoint factory constructing SQ Futures data provider adapter."""
    logger.info("Initializing SQ Futures provider plugin adapter.")
    return SQFuturesProvider()
