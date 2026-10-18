"""Local filesystem market data broker and symbol catalog implementation.

Description:
    Implements a local filesystem market data and symbol catalog broker
    accessing historical bars, ticks, and instrument specifications stored as
    CSV, TXT, Parquet, MT4 HST, or MT4 FXT files on disk. Conforms directly
    to the `TradingBackend` protocol and Stage 2C `data.provider` specification.
    Exposes canonical `SymbolInfo` objects and normalized historical records.

Purpose:
    FEAT-DATA-SOURCE-FILES: Local Filesystem Historical Market Data Ingestion.

Key Capabilities:
    - FR-BROKER-FILES-PARSING: CSV, Parquet, HST, and FXT Bar and Tick Ingestion
      Associated: `[FilesBroker.fetch_bars()]`, `[FilesBroker.fetch_ticks()]`, `[FilesBroker.read_history()]`
      Logging: Emits INFO on parsed record counts, and WARNING on absent paths.
    - FR-BROKER-FILES-SYMBOLS: Filesystem Symbol Discovery and Specification Resolution
      Associated: `[FilesBroker.symbol_info()]`, `[FilesBroker.symbols_get()]`
      Logging: Emits INFO upon resolving symbol info or catalog count,
      and WARNING if symbol is not found.
    - FR-BROKER-FILES-HEALTH: Filesystem Directory Accessibility and Health Inspection
      Associated: `[FilesBroker.check_health()]`
      Logging: Emits INFO on accessible directory probe and WARNING on inaccessible path.

Python API Usage:
    ```python
    from app.services.brokers.files import FilesBroker
    from app.workspace.data_manager.history import get_historical_bars
    from app.workspace.data_manager import Timeframe

    broker = FilesBroker(data_dir="data/market")
    health = broker.check_health()
    assert health.connected is True
    bars = await get_historical_bars(broker, "EURUSD", Timeframe.PERIOD_M1, count=5)
    ```

CLI Usage:
    ```bash
    uv run python -m app.services.brokers.files
    ```
"""

from __future__ import annotations

import tempfile
import time
from pathlib import Path
from typing import Any, override

from app.host.discovery import PluginHostContext
from app.host.logging import get_logger
from app.services.brokers._file_history import (
    find_matching_partitions,
    load_local_partition_bars,
    load_local_partition_ticks,
)
from app.services.brokers.base import BridgeError
from app.services.brokers.capabilities import (
    CancellationToken,
    HistoryPage,
    HistoryRequest,
    ProviderCapabilities,
    ProviderHealth,
)
from app.services.include.contracts import SymbolInfo
from app.workspace.data_manager.history import DataBrokerBackend

PARSING_FR = "FR-BROKER-FILES-PARSING"
SYMBOLS_FR = "FR-BROKER-FILES-SYMBOLS"
HEALTH_FR = "FR-BROKER-FILES-HEALTH"

DEFAULT_DATA_DIR = Path(__file__).resolve().parents[3] / "data" / "market"

PLUGIN_MANIFEST: dict[str, Any] = {
    "id": "files",
    "name": "Local Files",
    "version": "1.0.0",
    "slot": "data.provider",
    "entry_point": "files:create_adapter",
    "description": "Local filesystem market data broker supporting CSV, Parquet, HST, and FXT historical files.",
    "capabilities": ["data.fetch"],
}

__all__ = ["PLUGIN_MANIFEST", "FilesBroker", "create_adapter"]

logger = get_logger(__name__)


class FilesBroker(DataBrokerBackend):
    """Local filesystem market data and symbol catalog broker."""

    def __init__(
        self,
        name: str = "Files",
        data_dir: str | Path | None = None,
    ) -> None:
        """Initialize Files broker."""
        super().__init__(name=name)
        self.data_dir = Path(data_dir) if data_dir else DEFAULT_DATA_DIR
        self._is_connected = True
        self.capabilities = ProviderCapabilities(
            provider_id="files",
            display_name="Local File Storage",
            category="Multi-Asset",
            supported_timeframes=(
                "TICK",
                "M1",
                "M5",
                "M15",
                "M30",
                "H1",
                "H4",
                "D1",
                "W1",
                "MN1",
            ),
            supported_modes=("bars", "ticks"),
            requires_auth=False,
            rate_limit_rps=100.0,
            default_timeout_seconds=30.0,
            supports_pagination=False,
            has_local_archive=True,
            description="Local filesystem market data broker supporting CSV, Parquet, HST, and FXT files.",
        )

    @override
    def close_sync(self) -> None:
        """Synchronously release local resources."""
        self._is_connected = False

    @override
    async def close(self) -> None:
        """Asynchronously release local resources."""
        self.close_sync()

    def check_health(self) -> ProviderHealth:
        """Check accessibility and readability of the local data directory."""
        t0 = time.monotonic()
        if not self.data_dir.exists():
            latency = (time.monotonic() - t0) * 1000.0
            logger.warning(
                "%s: Local data directory does not exist: %s",
                HEALTH_FR,
                self.data_dir,
                extra={"fr_id": HEALTH_FR, "data_dir": str(self.data_dir)},
            )
            return ProviderHealth(
                provider_id="files",
                status="DEGRADED",
                connected=False,
                message=f"Local data directory does not exist: {self.data_dir}",
                latency_ms=latency,
                capabilities=self.capabilities,
            )

        try:
            # Verify readability
            _ = list(self.data_dir.glob("*"))[:5]
            latency = (time.monotonic() - t0) * 1000.0
            logger.info(
                "%s: Local data directory is accessible: %s (latency=%.2fms)",
                HEALTH_FR,
                self.data_dir,
                latency,
                extra={"fr_id": HEALTH_FR, "data_dir": str(self.data_dir)},
            )
            return ProviderHealth(
                provider_id="files",
                status="HEALTHY",
                connected=True,
                message=f"Local data directory accessible: {self.data_dir}",
                latency_ms=latency,
                capabilities=self.capabilities,
            )
        except Exception as exc:
            latency = (time.monotonic() - t0) * 1000.0
            logger.warning(
                "%s: Failed to read local data directory: %s",
                HEALTH_FR,
                exc,
                extra={"fr_id": HEALTH_FR, "error": str(exc)},
            )
            return ProviderHealth(
                provider_id="files",
                status="UNHEALTHY",
                connected=False,
                message=f"Cannot read local data directory: {exc}",
                latency_ms=latency,
                capabilities=self.capabilities,
            )

    def _scan_catalog(self) -> dict[str, list[Path]]:
        """Index symbols dynamically by discovering files."""
        catalog: dict[str, list[Path]] = {}
        if not self.data_dir.exists():
            return catalog

        for ext in ("*.parquet", "*.csv", "*.txt", "*.hst", "*.fxt", "*.tsv"):
            for p in self.data_dir.rglob(ext):
                raw_sym = p.stem.upper()
                for token in ("_M1", "_D1", "_H1", "_TICK", "_TICKS", "_BARS"):
                    raw_sym = raw_sym.replace(token, "")
                clean_sym = raw_sym.split(".")[0]
                if clean_sym:
                    catalog.setdefault(clean_sym, []).append(p)
        return catalog

    def _find_symbol_files(
        self,
        symbol: str,
        timeframe: str | None = None,
    ) -> list[Path]:
        """Find data files associated with symbol."""
        sym_clean = symbol.lower().replace("/", "").replace("_", "").replace("-", "")
        matches: list[Path] = []
        if not self.data_dir.exists():
            return matches

        tf_token = timeframe.lower().strip() if timeframe else None

        for ext in ("*.parquet", "*.csv", "*.txt", "*.hst", "*.fxt", "*.tsv"):
            for p in self.data_dir.rglob(ext):
                name_clean = (
                    p.stem.lower().replace("/", "").replace("_", "").replace("-", "")
                )
                parent_clean = (
                    p.parent.name.lower()
                    .replace("/", "")
                    .replace("_", "")
                    .replace("-", "")
                )
                if sym_clean in name_clean or sym_clean == parent_clean:
                    matches.append(p)

        if not matches:
            return []

        if tf_token:
            tf_matches = [
                p
                for p in matches
                if tf_token in p.name.lower()
                or tf_token in [x.lower() for x in p.parts]
            ]
            if tf_matches:
                return sorted(tf_matches)

        return sorted(matches)

    @override
    def symbol_info(self, symbol: str) -> SymbolInfo:
        """Resolve symbol metadata as canonical SymbolInfo."""
        sym_upper = symbol.upper()
        logger.info(
            "%s: Resolved symbol info for %s",
            SYMBOLS_FR,
            sym_upper,
            extra={"fr_id": SYMBOLS_FR, "symbol": sym_upper},
        )
        return SymbolInfo(
            name=sym_upper,
            custom=True,
            digits=2,
            point=0.01,
            trade_contract_size=1.0,
        )

    @override
    def symbols_get(self) -> list[str]:
        """Return list of distinct symbol names discovered in filesystem."""
        catalog = self._scan_catalog()
        symbols = sorted(catalog.keys())
        logger.info(
            "%s: Discovered %d symbols in filesystem catalog",
            SYMBOLS_FR,
            len(symbols),
            extra={"fr_id": SYMBOLS_FR, "count": len(symbols)},
        )
        return symbols

    @override
    def fetch_bars(
        self,
        *,
        symbol: str,
        timeframe: str,
        mode: str,
        start: int,
        end: int,
        count: int,
        limit: int,
    ) -> list[dict[str, Any]]:
        """Retrieve historical candlestick bars from local files."""
        del mode
        # Exact partition matching first
        files = find_matching_partitions(self.data_dir, symbol, timeframe)
        if not files:
            files = self._find_symbol_files(symbol, timeframe=timeframe)
        if not files:
            logger.warning(
                "%s: No files found for %s %s in %s",
                PARSING_FR,
                symbol,
                timeframe,
                self.data_dir,
                extra={"fr_id": PARSING_FR, "symbol": symbol, "timeframe": timeframe},
            )
            raise BridgeError(
                f"No local files found for symbol '{symbol}' in {self.data_dir}",
                code="FILE_NOT_FOUND",
            )

        try:
            deduped = load_local_partition_bars(
                files,
                symbol=symbol,
                timeframe=timeframe,
                start=start,
                end=end,
                count=count,
                limit=limit,
            )
            logger.info(
                "%s: Parsed %d bars for %s %s from %d partition file(s)",
                PARSING_FR,
                len(deduped),
                symbol,
                timeframe,
                len(files),
                extra={"fr_id": PARSING_FR, "count": len(deduped), "symbol": symbol},
            )
            return deduped
        except Exception as exc:
            if isinstance(exc, BridgeError):
                raise
            raise BridgeError(
                f"Failed to parse bars for {symbol}: {exc}", code="READ_ERROR"
            ) from exc

    @override
    def fetch_ticks(
        self,
        *,
        symbol: str,
        mode: str,
        start_ms: int,
        end_ms: int,
        count: int,
        limit: int,
    ) -> list[dict[str, Any]]:
        """Retrieve historical ticks from local files."""
        del mode
        files = find_matching_partitions(self.data_dir, symbol, "tick")
        if not files:
            files = self._find_symbol_files(symbol, timeframe="tick")
        if not files:
            files = self._find_symbol_files(symbol)
        if not files:
            raise BridgeError(
                f"No local files found for symbol '{symbol}'", code="FILE_NOT_FOUND"
            )

        try:
            deduped = load_local_partition_ticks(
                files,
                symbol=symbol,
                start_ms=start_ms,
                end_ms=end_ms,
                count=count,
                limit=limit,
            )
            logger.info(
                "%s: Parsed %d ticks for %s from %d partition file(s)",
                PARSING_FR,
                len(deduped),
                symbol,
                len(files),
                extra={"fr_id": PARSING_FR, "count": len(deduped), "symbol": symbol},
            )
            return deduped
        except Exception as exc:
            if isinstance(exc, BridgeError):
                raise
            raise BridgeError(
                f"Failed to parse ticks for {symbol}: {exc}", code="READ_ERROR"
            ) from exc

    @override
    def read_history(
        self,
        request: HistoryRequest,
        token: CancellationToken | None = None,
    ) -> HistoryPage:
        """Acquire historical bars or ticks according to typed request specification."""
        page = super().read_history(request, token)
        page.provenance = {"source": "local_files", "data_dir": str(self.data_dir)}
        return page


def create_adapter(_context: PluginHostContext | None = None) -> FilesBroker:
    """Plugin entrypoint factory constructing FilesBroker adapter."""
    return FilesBroker()


def main() -> None:
    """Demonstrate executable usage of FilesBroker."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        csv_file = tmp_path / "EURUSD_M1.csv"
        csv_file.write_text(
            "timestamp,open,high,low,close,volume\n"
            "2026-01-01 00:00:00,1.1000,1.1010,1.0990,1.1005,100\n"
            "2026-01-01 00:01:00,1.1005,1.1015,1.1000,1.1010,120\n",
            encoding="utf-8",
        )
        broker = FilesBroker(data_dir=tmp_path)
        health = broker.check_health()
        print(f"Health: {health.status} (connected={health.connected})")
        bars = broker.fetch_bars(
            symbol="EURUSD",
            timeframe="M1",
            mode="range",
            start=0,
            end=0,
            count=10,
            limit=10,
        )
        print(f"Read {len(bars)} bars successfully from {csv_file.name}")
        req = HistoryRequest(
            provider="files",
            symbol="EURUSD",
            timeframe="M1",
            kind="bars",
            count=5,
        )
        page = broker.read_history(req)
        print(f"Page rows: {page.row_count}")
        broker.close_sync()


if __name__ == "__main__":
    main()
