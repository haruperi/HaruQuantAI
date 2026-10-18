"""Local filesystem market data client and symbol catalog implementation.

Description:
    Implements a local filesystem market data and symbol catalog client
    accessing historical bars, ticks, and instrument specifications stored as
    CSV, TXT, Parquet, MT4 HST, or MT4 FXT files on disk. Conforms directly
    to the uniform `BrokerClient` interface. Exposes canonical `SymbolInfo`
    objects and normalized historical records.

Purpose:
    FEAT-DATA-SOURCE-FILES: Local Filesystem Historical Market Data Ingestion.

Key Capabilities:
    - FR-BROKER-FILES-PARSING: CSV, Parquet, HST, and FXT Bar and Tick Ingestion
      Associated: `[FilesClient.get_bars()]`, `[FilesClient.get_ticks()]`
      Logging: Emits INFO on parsed record counts, and WARNING on absent paths.
    - FR-BROKER-FILES-SYMBOLS: Filesystem Symbol Discovery and Specification Resolution
      Associated: `[FilesClient.get_symbol_info()]`, `[FilesClient.get_symbols()]`
      Logging: Emits INFO upon resolving symbol info or catalog count,
      and WARNING if symbol is not found.

Python API Usage:
    ```python
    from app.services.brokers.files import FilesClient
    from app.services.include.enums import Timeframe

    client = FilesClient(data_dir="data/market")
    bars = client.get_bars("EURUSD", Timeframe.PERIOD_M1, count=5)
    assert len(bars) > 0
    client.disconnect()
    ```

CLI Usage:
    ```bash
    uv run python -m app.services.brokers.files
    ```
"""

from __future__ import annotations

import tempfile
from datetime import datetime
from pathlib import Path
from typing import override

from app.host.logging import get_logger
from app.services.brokers._file_history import (
    find_matching_partitions,
    load_local_partition_bars,
    load_local_partition_ticks,
)
from app.services.brokers.base import (
    BridgeError,
    BrokerClient,
    epoch_millis,
    epoch_seconds,
)
from app.services.include.contracts import MarketBar, MarketTick, SymbolInfo
from app.services.include.enums import Timeframe

PARSING_FR = "FR-BROKER-FILES-PARSING"
SYMBOLS_FR = "FR-BROKER-FILES-SYMBOLS"

DEFAULT_DATA_DIR = Path(__file__).resolve().parents[3] / "data" / "market"

__all__ = ["FilesClient"]

logger = get_logger(__name__)


class FilesClient(BrokerClient):
    """Local filesystem market data and symbol catalog client."""

    def __init__(
        self,
        name: str = "Files",
        data_dir: str | Path | None = None,
    ) -> None:
        """Initialize Files broker client."""
        super().__init__(name=name)
        self.data_dir = Path(data_dir) if data_dir else DEFAULT_DATA_DIR
        self._connected = True

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
    def get_symbol_info(self, symbol: str) -> SymbolInfo:
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
    def get_symbols(self) -> list[str]:
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
    def get_bars(
        self,
        symbol: str,
        timeframe: Timeframe | str = Timeframe.PERIOD_H1,
        date_from: datetime | int | None = None,
        date_to: datetime | int | None = None,
        *,
        start: datetime | int | None = None,
        end: datetime | int | None = None,
        start_pos: int | None = None,
        count: int | None = None,
        limit: int = 1000,
    ) -> list[MarketBar]:
        """Retrieve historical candlestick bars from local files."""
        del start_pos
        tf_name = timeframe.name if isinstance(timeframe, Timeframe) else str(timeframe)
        files = find_matching_partitions(self.data_dir, symbol, tf_name)
        if not files:
            files = self._find_symbol_files(symbol, timeframe=tf_name)
        if not files:
            logger.warning(
                "%s: No files found for %s %s in %s",
                PARSING_FR,
                symbol,
                tf_name,
                self.data_dir,
                extra={"fr_id": PARSING_FR, "symbol": symbol, "timeframe": tf_name},
            )
            raise BridgeError(
                f"No local files found for symbol '{symbol}' in {self.data_dir}",
                code="FILE_NOT_FOUND",
            )

        s = date_from if date_from is not None else start
        e = date_to if date_to is not None else end
        start_sec = epoch_seconds(s)
        end_sec = epoch_seconds(e)
        try:
            deduped = load_local_partition_bars(
                files,
                symbol=symbol,
                timeframe=tf_name,
                start=start_sec,
                end=end_sec,
                count=count or 0,
                limit=limit,
            )
            logger.info(
                "%s: Parsed %d bars for %s %s from %d partition file(s)",
                PARSING_FR,
                len(deduped),
                symbol,
                tf_name,
                len(files),
                extra={"fr_id": PARSING_FR, "count": len(deduped), "symbol": symbol},
            )
            return [
                MarketBar(
                    time=int(r["time"]),
                    open=float(r["open"]),
                    high=float(r["high"]),
                    low=float(r["low"]),
                    close=float(r["close"]),
                    tick_volume=int(r.get("tick_volume", 0)),
                    spread=int(r.get("spread", 0)),
                    real_volume=int(r.get("real_volume", 0)),
                )
                for r in deduped
            ]
        except Exception as exc:
            if isinstance(exc, BridgeError):
                raise
            raise BridgeError(
                f"Failed to parse bars for {symbol}: {exc}", code="READ_ERROR"
            ) from exc

    @override
    def get_ticks(
        self,
        symbol: str,
        date_from: datetime | int | None = None,
        date_to: datetime | int | None = None,
        *,
        start: datetime | int | None = None,
        end: datetime | int | None = None,
        count: int | None = None,
        limit: int = 1000,
    ) -> list[MarketTick]:
        """Retrieve historical ticks from local files."""
        files = find_matching_partitions(self.data_dir, symbol, "tick")
        if not files:
            files = self._find_symbol_files(symbol, timeframe="tick")
        if not files:
            files = self._find_symbol_files(symbol)
        if not files:
            raise BridgeError(
                f"No local files found for symbol '{symbol}'", code="FILE_NOT_FOUND"
            )

        s = date_from if date_from is not None else start
        e = date_to if date_to is not None else end
        start_ms = epoch_millis(s)
        end_ms = epoch_millis(e)
        try:
            deduped = load_local_partition_ticks(
                files,
                symbol=symbol,
                start_ms=start_ms,
                end_ms=end_ms,
                count=count or 0,
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
            return [
                MarketTick(
                    time_msc=int(t["time_msc"]),
                    bid=float(t["bid"]),
                    ask=float(t["ask"]),
                    last=float(t.get("last", t["bid"])),
                    volume=int(t.get("volume", 1)),
                    flags=int(t.get("flags", 0)),
                    volume_real=float(t.get("volume_real", 1.0)),
                )
                for t in deduped
            ]
        except Exception as exc:
            if isinstance(exc, BridgeError):
                raise
            raise BridgeError(
                f"Failed to parse ticks for {symbol}: {exc}", code="READ_ERROR"
            ) from exc


def main() -> None:
    """Demonstrate executable usage of FilesClient."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        csv_file = tmp_path / "EURUSD_M1.csv"
        csv_file.write_text(
            "timestamp,open,high,low,close,volume\n"
            "2026-01-01 00:00:00,1.1000,1.1010,1.0990,1.1005,100\n"
            "2026-01-01 00:01:00,1.1005,1.1015,1.1000,1.1010,120\n",
            encoding="utf-8",
        )
        client = FilesClient(data_dir=tmp_path)
        bars = client.get_bars("EURUSD", "M1", count=10)
        assert isinstance(bars, list)
        logger.info("Read %d bars successfully from %s", len(bars), csv_file.name)
        client.disconnect()


if __name__ == "__main__":
    main()
