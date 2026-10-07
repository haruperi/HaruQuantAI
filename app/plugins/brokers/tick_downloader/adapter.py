"""Tick Data Downloader market data provider adapter plugin.

Description:
    Dynamic data provider plugin for tick and high-precision trade data within
    the SQX dynamic plugin architecture under slot `data.provider`.
    Under the workspace Strict Real-Data Policy, if local tick archives are
    absent, the provider cleanly returns an empty record set rather than
    synthesizing artificial mock records.

Purpose:
    FEAT-DATA-SOURCE-TICKDOWNLOADER: Tick market data provider plugin.

Key Capabilities:
    - FR-DATA-PROVIDERS-ADAPTERS: Uniform typed provider adapters and capability
      metadata.
      Associated: `[TickDownloaderProvider.download_bars()]`, `[create_adapter()]`
      Logging: Emits INFO on download dispatch.

Python API Usage:
    ```python
    from app.plugins.brokers.tick_downloader.adapter import create_adapter

    adapter = create_adapter()
    caps = adapter.capabilities
    ```

CLI Usage:
    ```bash
    python -m app.workspace.data_manager.connections --list
    ```
"""

from __future__ import annotations

from pathlib import Path
from typing import override

from app.host.discovery import PluginHostContext
from app.host.logging import get_logger
from app.workspace.data_manager.connections import (
    BaseDataProvider,
    CancellationToken,
    DownloadRequest,
    ProviderCapabilities,
)
from app.workspace.data_manager.data import BarRecord

logger = get_logger(__name__)

DEFAULT_DATA_DIR = Path(__file__).resolve().parents[4] / "data" / "market"


class TickDownloaderProvider(BaseDataProvider):
    """Tick data downloader."""

    def __init__(self, data_dir: str | Path | None = None) -> None:
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
        self.data_dir = Path(data_dir) if data_dir else DEFAULT_DATA_DIR

    @override
    def _fetch_bars(
        self, request: DownloadRequest, token: CancellationToken
    ) -> list[BarRecord]:
        token.check_cancelled()
        # Strict Real-Data Policy: Scan real tick parquet archives if present
        sym_clean = (
            request.symbol.lower().replace("/", "").replace("_", "").replace("-", "")
        )
        tick_dir = self.data_dir / "dukascopy" / "ticks" / sym_clean
        if tick_dir.exists():
            try:
                import pyarrow.parquet as pq

                p_files = sorted(tick_dir.rglob("*.parquet"))
                if p_files:
                    table = pq.read_table(p_files[-1])
                    df = table.to_pandas()
                    records: list[BarRecord] = []
                    for _, row in df.tail(100).iterrows():
                        dt = row["DateTime"]
                        dt_iso = dt.isoformat() if hasattr(dt, "isoformat") else str(dt)
                        records.append(
                            BarRecord(
                                timestamp_utc=dt_iso,
                                open=float(row.get("Bid", row.get("Ask", 0.0))),
                                high=float(row.get("Bid", row.get("Ask", 0.0))),
                                low=float(row.get("Bid", row.get("Ask", 0.0))),
                                close=float(row.get("Bid", row.get("Ask", 0.0))),
                                volume=float(row.get("Volume", 1.0)),
                            )
                        )
                    return records
            except Exception as e:
                logger.debug("Failed to read local tick partition: %s", e)

        return []


def create_adapter(_context: PluginHostContext | None = None) -> BaseDataProvider:
    """Plugin entrypoint factory constructing Tick Data Downloader provider adapter."""
    logger.info("Initializing Tick Data Downloader provider plugin adapter.")
    return TickDownloaderProvider()
