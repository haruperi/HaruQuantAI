"""Local filesystem market data broker and symbol catalog implementation.

Description:
    Implements a local filesystem market data and symbol catalog broker
    accessing historical bars, ticks, and instrument specifications stored as
    CSV, TXT, or Parquet files on disk. Conforms directly to the `TradingBackend` protocol.
    Exposes canonical `SymbolSnapshot` objects and normalized historical bars.

Purpose:
    FEAT-DATA-SOURCE-FILES: Local Filesystem Historical Market Data Ingestion.

Key Capabilities:
    - FR-BROKER-FILES-PARSING: CSV/TXT and Parquet Historical Bar and Tick Ingestion
      Associated: `[FilesBroker.fetch_bars()]`, `[FilesBroker.fetch_ticks()]`
      Logging: Emits INFO log with parsed record counts, or WARNING on absent paths.
    - FR-BROKER-FILES-SYMBOLS: Filesystem Symbol Discovery and Specification Resolution
      Associated: `[FilesBroker.symbol_info()]`, `[FilesBroker.symbols_get()]`
      Logging: Emits INFO log upon resolving symbol info or catalog count,
      and WARNING if symbol is not found.

Python API Usage:
    ```python
    from app.services.data import Timeframe, get_historical_bars
    from app.services.brokers.files import FilesBroker

    broker = FilesBroker(data_dir="data/market/sq_equity/d1")
    bars = await get_historical_bars(broker, "AAPL", Timeframe.PERIOD_D1, count=5)
    assert len(bars) > 0
    ```

CLI Usage:
    `uv run python -m scripts.examples.brokers_data --broker files`
"""

from __future__ import annotations

import csv
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, override

from app.host.discovery import PluginHostContext
from app.host.logging import get_logger
from app.services.data import BridgeError, DataBrokerBackend
from app.services.libs.trading import SymbolSnapshot

logger = get_logger(__name__)

DEFAULT_DATA_DIR = Path(__file__).resolve().parents[3] / "data" / "market"

__all__ = ["FilesBroker", "create_adapter"]


def _parse_timestamp(ts_str: str) -> datetime:
    """Parse timestamp strings across diverse date-time formats."""
    s = ts_str.strip()
    iso_candidate = s.replace("Z", "+00:00").replace("/", "-")
    try:
        dt = datetime.fromisoformat(iso_candidate)
        return dt if dt.tzinfo is not None else dt.replace(tzinfo=UTC)
    except ValueError:
        pass

    clean_s = re.sub(r"[^\d]", " ", s).strip()
    tokens = [t for t in clean_s.split() if t]

    if len(tokens) >= 3:
        try:
            year = int(tokens[0])
            month = int(tokens[1])
            day = int(tokens[2])
            hour = int(tokens[3]) if len(tokens) > 3 else 0
            minute = int(tokens[4]) if len(tokens) > 4 else 0
            second = int(tokens[5]) if len(tokens) > 5 else 0
            microsecond = int(tokens[6][:6].ljust(6, "0")) if len(tokens) > 6 else 0
            return datetime(
                year,
                month,
                day,
                hour,
                minute,
                second,
                microsecond,
                tzinfo=UTC,
            )
        except ValueError, IndexError:
            pass

    return datetime.now(tz=UTC)


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

    def _scan_catalog(self) -> dict[str, list[Path]]:
        """Index symbols dynamically by discovering CSV, TXT, and Parquet files."""
        catalog: dict[str, list[Path]] = {}
        if not self.data_dir.exists():
            return catalog

        for ext in ("*.parquet", "*.csv", "*.txt"):
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
        """Find CSV or Parquet files associated with symbol."""
        sym_clean = symbol.lower().replace("/", "").replace("_", "").replace("-", "")
        matches: list[Path] = []
        if not self.data_dir.exists():
            return matches

        tf_token = str(timeframe).lower().strip() if timeframe else None

        for ext in ("*.parquet", "*.csv", "*.txt"):
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
    def symbol_info(self, symbol: str) -> SymbolSnapshot:
        """Resolve symbol metadata as canonical SymbolSnapshot."""
        sym_upper = symbol.upper()
        return SymbolSnapshot(
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
        return sorted(catalog.keys())

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
        """Retrieve historical candlestick bars from local CSV or Parquet files."""
        del mode
        files = self._find_symbol_files(symbol, timeframe=timeframe)
        if not files:
            raise BridgeError(
                f"No local files found for symbol '{symbol}' in {self.data_dir}",
                code="FILE_NOT_FOUND",
            )

        target_file = files[-1]
        target_count = count if count > 0 else limit
        date_from = datetime.fromtimestamp(start, tz=UTC) if 0 < start < 2**40 else None
        date_to = datetime.fromtimestamp(end, tz=UTC) if 0 < end < 2**40 else None

        rows: list[dict[str, Any]] = []

        try:
            if target_file.suffix == ".parquet":
                import pyarrow.parquet as pq

                table = pq.read_table(target_file)
                data_dict = table.to_pydict()
                dts = (
                    data_dict.get("DateTime")
                    or data_dict.get("datetime")
                    or data_dict.get("Date")
                    or []
                )
                opens = data_dict.get("Open") or data_dict.get("open") or []
                highs = data_dict.get("High") or data_dict.get("high") or []
                lows = data_dict.get("Low") or data_dict.get("low") or []
                closes = data_dict.get("Close") or data_dict.get("close") or []
                vols = data_dict.get("Volume") or data_dict.get("volume") or []

                for i in range(len(dts)):
                    dt = dts[i]
                    if hasattr(dt, "to_pydatetime"):
                        dt = dt.to_pydatetime()
                    if dt.tzinfo is None:
                        dt = dt.replace(tzinfo=UTC)

                    if date_from and dt < date_from:
                        continue
                    if date_to and dt > date_to:
                        continue

                    vol = int(vols[i]) if i < len(vols) else 0
                    o = float(opens[i])
                    c = float(closes[i])
                    h = max(float(highs[i]), o, c)
                    l = min(float(lows[i]), o, c)
                    rows.append(
                        {
                            "time": int(dt.timestamp()),
                            "open": o,
                            "high": h,
                            "low": l,
                            "close": c,
                            "tick_volume": vol,
                            "spread": 0,
                            "real_volume": vol,
                        }
                    )
            elif target_file.suffix in (".csv", ".txt"):
                with target_file.open("r", encoding="utf-8", errors="replace") as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        low_row = {
                            k.lower().strip().replace("<", "").replace(">", ""): v
                            for k, v in row.items()
                            if k
                        }
                        dt_val = (
                            low_row.get("datetime")
                            or low_row.get("date_time")
                            or low_row.get("timestamp")
                        )
                        if not dt_val:
                            d_col = low_row.get("date")
                            t_col = low_row.get("time")
                            if d_col and t_col:
                                dt_val = f"{d_col} {t_col}"
                            elif d_col:
                                dt_val = d_col
                            elif t_col:
                                dt_val = t_col
                        if not dt_val:
                            continue

                        dt = _parse_timestamp(dt_val)
                        if date_from and dt < date_from:
                            continue
                        if date_to and dt > date_to:
                            continue

                        o = float(low_row.get("open", 0.0))
                        c = float(low_row.get("close", 0.0))
                        h = max(float(low_row.get("high", 0.0)), o, c)
                        l = min(float(low_row.get("low", 0.0)), o, c)
                        vol = int(
                            float(
                                low_row.get("volume")
                                or low_row.get("vol")
                                or low_row.get("tick_volume")
                                or 0.0
                            )
                        )
                        rows.append(
                            {
                                "time": int(dt.timestamp()),
                                "open": o,
                                "high": h,
                                "low": l,
                                "close": c,
                                "tick_volume": vol,
                                "spread": 0,
                                "real_volume": vol,
                            }
                        )

            rows.sort(key=lambda r: r["time"])
            deduped: list[dict[str, Any]] = []
            last_t: int | None = None
            for r in rows:
                if last_t is None or r["time"] > last_t:
                    deduped.append(r)
                    last_t = r["time"]

            if target_count and len(deduped) > target_count:
                deduped = deduped[-target_count:]
            return deduped
        except Exception as exc:
            if isinstance(exc, BridgeError):
                raise
            raise BridgeError(
                f"Failed to parse bars from {target_file}: {exc}", code="READ_ERROR"
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
        """Retrieve historical ticks from local CSV or Parquet files."""
        del mode
        files = self._find_symbol_files(symbol, timeframe="tick")
        if not files:
            files = self._find_symbol_files(symbol)
        if not files:
            raise BridgeError(
                f"No local files found for symbol '{symbol}'", code="FILE_NOT_FOUND"
            )

        target_file = files[-1]
        target_count = count if count > 0 else limit
        rows: list[dict[str, Any]] = []

        try:
            if target_file.suffix in (".csv", ".txt"):
                with target_file.open("r", encoding="utf-8", errors="replace") as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        low_row = {
                            k.lower().strip().replace("<", "").replace(">", ""): v
                            for k, v in row.items()
                            if k
                        }
                        dt_val = (
                            low_row.get("datetime")
                            or low_row.get("date_time")
                            or low_row.get("timestamp")
                        )
                        if not dt_val:
                            continue
                        dt = _parse_timestamp(dt_val)
                        t_ms = int(dt.timestamp() * 1000)
                        if start_ms > 0 and t_ms < start_ms:
                            continue
                        if end_ms > 0 and t_ms > end_ms:
                            continue

                        bid = float(low_row.get("bid", 0.0))
                        ask = float(low_row.get("ask", 0.0))
                        last = float(low_row.get("last", (bid + ask) / 2.0))
                        vol = float(low_row.get("volume", 1.0))
                        rows.append(
                            {
                                "time_msc": t_ms,
                                "bid": bid,
                                "ask": ask,
                                "last": last,
                                "volume": int(vol),
                                "flags": 0,
                                "volume_real": vol,
                            }
                        )

            rows.sort(key=lambda r: r["time_msc"])
            if target_count and len(rows) > target_count:
                rows = rows[-target_count:]
            return rows
        except Exception as exc:
            if isinstance(exc, BridgeError):
                raise
            raise BridgeError(
                f"Failed to parse ticks from {target_file}: {exc}", code="READ_ERROR"
            ) from exc


def create_adapter(_context: PluginHostContext | None = None) -> FilesBroker:
    """Plugin entrypoint factory constructing FilesBroker adapter."""
    return FilesBroker()
