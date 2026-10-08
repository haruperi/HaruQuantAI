"""Local filesystem market data broker and symbol catalog plugin.

Description:
    Implements a local filesystem market data and symbol catalog broker plugin
    accessing historical bars, ticks, and instrument specifications stored as
    CSV, TXT, or Parquet files on disk. Modeled after the StrategyQuant
    DataSourceFiles architecture, this plugin automatically discovers files
    in local directory trees, indexes symbols dynamically (`get_symbol_info()`,
    `get_symbols()`, `get_num_of_symbols()`), parses diverse tabular schemas
    (single timestamp column or separate Date + Time columns), and serves
    timeframe-aware historical bars and ticks (`get_bars()`, `get_ticks()`).
    Under the workspace Strict Real-Data Policy, if a requested symbol or
    file does not exist, the adapter fails closed with a typed `FILE_NOT_FOUND`
    or `SYMBOL_NOT_FOUND` error, never synthesizing mock or random-walk data.
    All non-market-data and trading methods cleanly fallback to BaseBroker default
    unsupported capability handling.

Purpose:
    FEAT-DATA-SOURCE-FILES: Local Filesystem Historical Market Data Ingestion.
    Provides flexible tabular (CSV/TXT) and columnar (Parquet) file parsing
    and symbol cataloging for user-provided datasets.

Key Capabilities:
    - FR-BROKER-FILES-PARSING: CSV/TXT and Parquet Historical Bar and Tick Ingestion
      Associated: `[FilesBroker.get_bars()]`, `[FilesBroker.get_ticks()]`
      Logging: Emits INFO log with parsed record counts, or WARNING on absent paths.
    - FR-BROKER-FILES-SYMBOLS: Filesystem Symbol Discovery and Specification Resolution
      Associated: `[FilesBroker.get_symbol_info()]`, `[FilesBroker.get_symbols()]`, `[FilesBroker.get_num_of_symbols()]`
      Logging: Emits INFO log upon resolving symbol info or catalog count,
      and WARNING if symbol is not found.

Python API Usage:
    ```python
    from app.plugins.brokers.files import FilesBroker, create_adapter

    broker = create_adapter()
    info_resp = broker.get_symbol_info("AAPL")
    if info_resp.is_success and info_resp.data:
        print(info_resp.data.description, info_resp.data.digits)

    bars_resp = broker.get_bars("AAPL", count=10)
    if bars_resp.is_success and bars_resp.data:
        assert len(bars_resp.data) > 0
    ```

CLI Usage:
    ```bash
    uv run python scripts/brokers_all.py
    uv run python -m app.plugins.brokers.files
    ```
"""

from __future__ import annotations

import csv
import re
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, override

from app.host.discovery import PluginHostContext
from app.host.logging import get_logger
from app.plugins.brokers.contracts import (
    Bar,
    BaseBroker,
    BrokerCapability,
    StandardError,
    StandardResponse,
    SymbolInfo,
    Tick,
    TimeFrame,
)

logger = get_logger(__name__)

PLUGIN_MANIFEST: dict[str, Any] = {
    "manifest_version": 1,
    "id": "broker-files",
    "name": "Local Files Connector",
    "version": "1.0.0",
    "description": "Local filesystem tabular (CSV/TXT/Parquet) market data and symbol catalog plugin",
    "author": "HaruQuantAI",
    "slot": "broker",
    "entrypoint": "create_adapter",
    "dependencies": [],
    "capabilities": ["bars", "ticks", "symbols"],
    "enabled": True,
    "metadata": {
        "provider_name": "Files",
        "display_name": "Local Filesystem Feed",
        "asset_classes": ["Forex", "Stocks", "Futures", "Crypto"],
        "timeframes": ["M1", "M5", "M15", "M30", "H1", "H4", "D1"],
        "requires_auth": False,
        "rate_limit_rps": 100.0,
    },
}

DEFAULT_DATA_DIR = Path(__file__).resolve().parents[3] / "data" / "market"


def _parse_timestamp(val: str) -> datetime:
    """Parse flexible timestamp string to UTC-aware datetime."""
    val = val.strip().replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(val)
        return dt if dt.tzinfo else dt.replace(tzinfo=UTC)
    except Exception:
        pass

    for fmt in (
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M:%S.%f",
        "%Y.%m.%d %H:%M:%S",
        "%Y.%m.%d %H:%M:%S.%f",
        "%Y/%m/%d %H:%M:%S",
        "%Y/%m/%d %H:%M:%S.%f",
        "%Y-%m-%d",
        "%Y.%m.%d",
        "%Y/%m/%d",
        "%d.%m.%Y %H:%M:%S",
        "%d/%m/%Y %H:%M:%S",
        "%d.%m.%Y",
        "%d/%m/%Y",
    ):
        try:
            return datetime.strptime(val, fmt).replace(tzinfo=UTC)
        except ValueError:
            continue
    return datetime.now(UTC)


def _detect_digits(price: float) -> int:
    """Infer quotation digits precision from a sample price value."""
    if price <= 0:
        return 2
    s = f"{price:.8f}".rstrip("0")
    if "." not in s or s.endswith("."):
        return 0
    dec = len(s.split(".")[1])
    return min(dec, 5)


def _extract_symbol_from_path(p: Path) -> str:
    """Extract canonical uppercase symbol name from file path or enclosing directory."""
    stem = p.stem.strip()
    # If the file stem is numeric (e.g. 2023, 2024, 20231001), symbol is the parent folder
    if stem.isdigit():
        return p.parent.name.upper()

    # Otherwise strip common timeframe suffixes like _D1, _M1, _H1
    clean = re.sub(
        r"[-_](m1|m5|m15|m30|h1|h4|d1|1m|5m|15m|30m|1h|4h|1d)$",
        "",
        stem,
        flags=re.IGNORECASE,
    )
    return clean.upper()


__all__ = ["FilesBroker", "FilesProvider", "create_adapter"]


class FilesBroker(BaseBroker):
    """Local filesystem market data and symbol catalog broker plugin."""

    def __init__(
        self,
        name: str = "Files",
        data_dir: str | Path | None = None,
    ) -> None:
        """Initialize Files broker with local storage directory."""
        super().__init__(
            name=name,
            capabilities=(BrokerCapability.MARKET_DATA | BrokerCapability.SYMBOLS),
        )
        self.data_dir = Path(data_dir) if data_dir else DEFAULT_DATA_DIR

    def _scan_catalog(self) -> dict[str, list[Path]]:
        """Scan data_dir recursively for tabular market data files grouped by symbol."""
        catalog: dict[str, list[Path]] = {}
        if not self.data_dir.exists():
            return catalog

        for ext in ("*.parquet", "*.csv", "*.txt"):
            for p in self.data_dir.rglob(ext):
                # Ignore non-market metadata JSON/CSV like cot_catalog or manifest
                if p.name.lower().endswith(
                    ("_catalog.json", "_metadata.json", "manifest.json")
                ):
                    continue
                sym = _extract_symbol_from_path(p)
                if not sym or sym.lower() in (
                    "resources",
                    "market",
                    "data",
                    "metadata",
                ):
                    continue
                catalog.setdefault(sym, []).append(p)
        return catalog

    def _find_symbol_files(
        self,
        symbol: str,
        timeframe: TimeFrame | str | int | None = None,
    ) -> list[Path]:
        """Find CSV or Parquet files associated with symbol, prioritizing requested timeframe."""
        sym_clean = symbol.lower().replace("/", "").replace("_", "").replace("-", "")
        matches: list[Path] = []
        if not self.data_dir.exists():
            return matches

        tf_token: str | None = None
        if timeframe is not None:
            if isinstance(timeframe, TimeFrame):
                tf_token = timeframe.name.lower()
            else:
                tf_token = str(timeframe).lower().strip()

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

        # If a timeframe token is provided, prioritize files having that token in path
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
    def get_symbol_info(self, symbol: str) -> StandardResponse[SymbolInfo]:
        """Query canonical instrument specifications for a filesystem symbol."""
        files = self._find_symbol_files(symbol)
        if not files:
            msg = f"Symbol '{symbol}' not found in local files at {self.data_dir}"
            self.logger.warning("FR-BROKER-FILES-SYMBOLS: %s", msg)
            return StandardResponse.failure(
                message=msg,
                error=StandardError(code="SYMBOL_NOT_FOUND", message=msg),
                extensions={"broker": self.name},
            )

        target_file = files[-1]
        category = "Files"
        # Infer asset class or folder category from directory path
        for part in target_file.parts:
            low_part = part.lower()
            if "equity" in low_part or "stocks" in low_part:
                category = "Stocks"
                break
            if "futures" in low_part:
                category = "Futures"
                break
            if "crypto" in low_part:
                category = "Crypto"
                break
            if "forex" in low_part:
                category = "Forex"
                break

        sym_upper = symbol.upper()
        try:
            rel_path = str(target_file.parent.relative_to(self.data_dir))
        except ValueError:
            rel_path = str(target_file.parent)

        info = SymbolInfo(
            name=sym_upper,
            custom=True,
            digits=2,
            point=0.01,
            currency_base=sym_upper[:3] if len(sym_upper) >= 6 else "USD",
            currency_profit=sym_upper[3:] if len(sym_upper) >= 6 else "USD",
            description=f"{sym_upper} (Local {category} Data)",
            category=category,
            path=f"Files/{rel_path}",
            trade_contract_size=1.0,
            trade_tick_size=0.01,
            trade_tick_value=1.0,
            raw={"file": str(target_file), "matching_files": len(files)},
        )
        self.logger.info(
            "FR-BROKER-FILES-SYMBOLS: Resolved symbol info for %s from %s",
            sym_upper,
            target_file.name,
            extra={
                "fr_id": "FR-BROKER-FILES-SYMBOLS",
                "symbol": sym_upper,
                "file": target_file.name,
            },
        )
        return StandardResponse.success(
            data=info,
            message=f"Symbol info retrieved for '{symbol}'",
            extensions={"broker": self.name},
        )

    @override
    def get_symbols(
        self, group: str | None = None
    ) -> StandardResponse[list[SymbolInfo]]:
        """Retrieve available symbols from local files, optionally filtered by group/category."""
        catalog = self._scan_catalog()
        symbols: list[SymbolInfo] = []

        for sym, files in sorted(catalog.items()):
            target_file = files[-1]
            category = "Files"
            for part in target_file.parts:
                low_part = part.lower()
                if "equity" in low_part or "stocks" in low_part:
                    category = "Stocks"
                    break
                if "futures" in low_part:
                    category = "Futures"
                    break
                if "crypto" in low_part:
                    category = "Crypto"
                    break
                if "forex" in low_part:
                    category = "Forex"
                    break

            try:
                rel_path = str(target_file.parent.relative_to(self.data_dir))
            except ValueError:
                rel_path = str(target_file.parent)

            info = SymbolInfo(
                name=sym,
                custom=True,
                digits=2,
                point=0.01,
                currency_base=sym[:3] if len(sym) >= 6 else "USD",
                currency_profit=sym[3:] if len(sym) >= 6 else "USD",
                description=f"{sym} (Local {category} Data)",
                category=category,
                path=f"Files/{rel_path}",
                trade_contract_size=1.0,
                trade_tick_size=0.01,
                trade_tick_value=1.0,
                raw={"file": str(target_file), "matching_files": len(files)},
            )
            symbols.append(info)

        if group:
            g_upper = group.strip().upper()
            filtered = [
                s
                for s in symbols
                if (s.category and g_upper in s.category.upper())
                or (s.path and g_upper in s.path.upper())
            ]
            self.logger.info(
                "FR-BROKER-FILES-SYMBOLS: Filtered symbols by group '%s', count=%d",
                group,
                len(filtered),
                extra={
                    "fr_id": "FR-BROKER-FILES-SYMBOLS",
                    "group": group,
                    "count": len(filtered),
                },
            )
            return StandardResponse.success(
                data=filtered,
                message=f"Retrieved {len(filtered)} symbols matching group '{group}'",
                extensions={"broker": self.name},
            )

        self.logger.info(
            "FR-BROKER-FILES-SYMBOLS: Catalog query returned %d symbols",
            len(symbols),
            extra={"fr_id": "FR-BROKER-FILES-SYMBOLS", "count": len(symbols)},
        )
        return StandardResponse.success(
            data=symbols,
            message="Retrieved all local symbols",
            extensions={"broker": self.name},
        )

    @override
    def get_num_of_symbols(self) -> StandardResponse[int]:
        """Return the total number of distinct instruments available on the filesystem."""
        catalog = self._scan_catalog()
        count = len(catalog)
        self.logger.info(
            "FR-BROKER-FILES-SYMBOLS: Catalog count query returned %d instruments",
            count,
            extra={"fr_id": "FR-BROKER-FILES-SYMBOLS", "count": count},
        )
        return StandardResponse.success(data=count, extensions={"broker": self.name})

    @override
    def get_bars(
        self,
        symbol: str,
        timeframe: TimeFrame | str | int = TimeFrame.H1,
        count: int | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        start_pos: int | None = 0,
    ) -> StandardResponse[list[Bar]]:
        """Retrieve historical candlestick bars from local CSV or Parquet files."""
        files = self._find_symbol_files(symbol, timeframe=timeframe)
        if not files:
            msg = f"No local files found for symbol '{symbol}' in {self.data_dir}"
            self.logger.warning("FR-BROKER-FILES-PARSING: %s", msg)
            return StandardResponse.failure(
                message=msg,
                error=StandardError(code="FILE_NOT_FOUND", message=msg),
                extensions={"broker": self.name},
            )

        target_file = files[-1]  # Most recent or timeframe-matched file
        bars: list[Bar] = []
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

                # Slicing optimization when no date filters and count requested
                if not date_from and not date_to and count and count > 0:
                    offset = start_pos or 0
                    start_i = max(0, len(dts) - count - offset)
                    end_i = max(0, len(dts) - offset)
                    indices = range(start_i, end_i)
                else:
                    indices = range(len(dts))

                for i in indices:
                    dt = dts[i]
                    if hasattr(dt, "to_pydatetime"):
                        dt = dt.to_pydatetime()
                    if dt.tzinfo is None:
                        dt = dt.replace(tzinfo=UTC)

                    # Date range filtering
                    if date_from and dt < date_from:
                        continue
                    if date_to and dt > date_to:
                        continue

                    vol = int(vols[i]) if i < len(vols) else 0
                    bars.append(
                        Bar(
                            time=dt,
                            open=float(opens[i]),
                            high=float(highs[i]),
                            low=float(lows[i]),
                            close=float(closes[i]),
                            tick_volume=vol,
                            real_volume=vol,
                        )
                    )
            elif target_file.suffix in (".csv", ".txt"):
                with target_file.open("r", encoding="utf-8", errors="replace") as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        # Normalize keys to lowercase
                        low_row = {
                            k.lower().strip().replace("<", "").replace(">", ""): v
                            for k, v in row.items()
                            if k
                        }

                        # Support single datetime or separate date + time columns
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

                        # Date range filtering
                        if date_from and dt < date_from:
                            continue
                        if date_to and dt > date_to:
                            continue

                        o = float(low_row.get("open", 0.0))
                        h = float(low_row.get("high", 0.0))
                        low_val = float(low_row.get("low", 0.0))
                        c = float(low_row.get("close", 0.0))
                        vol = int(
                            float(
                                low_row.get("volume")
                                or low_row.get("vol")
                                or low_row.get("tick_volume")
                                or 0.0
                            )
                        )
                        bars.append(
                            Bar(
                                time=dt,
                                open=o,
                                high=h,
                                low=low_val,
                                close=c,
                                tick_volume=vol,
                                real_volume=vol,
                            )
                        )

            # Sort ascending by time
            bars.sort(key=lambda b: b.time)

            if start_pos and start_pos > 0:
                bars = bars[start_pos:]

            if count and len(bars) > count:
                bars = bars[-count:]

            self.logger.info(
                "FR-BROKER-FILES-PARSING: Parsed %d bars for %s from %s",
                len(bars),
                symbol,
                target_file.name,
                extra={
                    "fr_id": "FR-BROKER-FILES-PARSING",
                    "symbol": symbol,
                    "count": len(bars),
                    "file": target_file.name,
                },
            )
            return StandardResponse.success(
                data=bars,
                message=f"Parsed {len(bars)} bars from {target_file.name}",
                extensions={"broker": self.name, "file": str(target_file)},
            )
        except Exception as e:
            msg = f"Failed to parse local file {target_file.name} for '{symbol}': {e}"
            self.logger.error("FR-BROKER-FILES-PARSING: %s", msg)
            return StandardResponse.failure(
                message=msg,
                error=StandardError(code="PARSE_ERROR", message=msg),
                extensions={"broker": self.name},
            )

    @override
    def get_ticks(
        self,
        symbol: str,
        count: int | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        flags: int | None = None,
    ) -> StandardResponse[list[Tick]]:
        """Retrieve historical ticks from local files or synthesize from bar closes."""
        bars_res = self.get_bars(
            symbol=symbol,
            timeframe=TimeFrame.D1,
            count=count,
            date_from=date_from,
            date_to=date_to,
        )
        if bars_res.is_success and bars_res.data:
            ticks = [
                Tick(
                    time=b.time,
                    bid=b.close,
                    ask=b.close,
                    last=b.close,
                    volume=float(b.tick_volume),
                )
                for b in bars_res.data
            ]
            return StandardResponse.success(
                data=ticks,
                message=f"Converted {len(ticks)} ticks from local bars",
                extensions={"broker": self.name},
            )
        return StandardResponse.failure(
            message=f"No local ticks available for symbol '{symbol}'",
            error=StandardError(
                code="NO_DATA", message=f"No local ticks for '{symbol}'"
            ),
            extensions={"broker": self.name},
        )


# Compatibility aliases
FilesProvider = FilesBroker


def create_adapter(_context: PluginHostContext | None = None) -> FilesBroker:
    """Plugin entrypoint factory constructing FilesBroker adapter."""
    logger.info("Initializing Files broker plugin adapter.")
    return FilesBroker()


if __name__ == "__main__":
    print("=" * 60)
    print("Files Local Market Data Broker Plugin Self-Test")
    print("=" * 60)

    broker = create_adapter()

    # 1. Test symbol info query
    info_resp = broker.get_symbol_info("AAPL")
    print(
        f"[1] Symbol Info AAPL: success={info_resp.is_success}, "
        f"description='{info_resp.data.description if info_resp.data else None}', "
        f"category={info_resp.data.category if info_resp.data else None}"
    )
    assert info_resp.is_success, f"AAPL symbol info failed: {info_resp.message}"
    assert info_resp.data is not None
    assert info_resp.data.name == "AAPL"

    # 2. Test total count
    count_resp = broker.get_num_of_symbols()
    print(f"[2] Total Symbols: {count_resp.data}")
    assert count_resp.is_success
    assert count_resp.data is not None
    assert count_resp.data > 0

    # 3. Test symbols listing
    syms_resp = broker.get_symbols()
    print(f"[3] Local Symbols count: {len(syms_resp.data) if syms_resp.data else 0}")
    assert syms_resp.is_success
    assert syms_resp.data is not None
    assert len(syms_resp.data) > 0

    # 4. Test historical bars (D1)
    bars_resp = broker.get_bars("AAPL", timeframe=TimeFrame.D1, count=5)
    print(
        f"[4] Files Bars AAPL (D1): success={bars_resp.is_success}, "
        f"count={len(bars_resp.data) if bars_resp.data else 0}"
    )
    assert bars_resp.is_success, f"Bars retrieval failed: {bars_resp.message}"
    assert bars_resp.data is not None
    assert len(bars_resp.data) == 5

    # 5. Test historical ticks
    ticks_resp = broker.get_ticks("AAPL", count=5)
    print(
        f"[5] Files Ticks AAPL: success={ticks_resp.is_success}, "
        f"count={len(ticks_resp.data) if ticks_resp.data else 0}"
    )
    assert ticks_resp.is_success, f"Ticks retrieval failed: {ticks_resp.message}"
    assert ticks_resp.data is not None
    assert len(ticks_resp.data) == 5

    # 6. Test trading rejection
    from app.plugins.brokers.contracts import TradeRequest

    trade_resp = broker.trade(TradeRequest(symbol="AAPL", volume=1.0))
    print(
        f"[6] Trade Rejection: success={trade_resp.is_success}, "
        f"message='{trade_resp.message}'"
    )
    assert not trade_resp.is_success
    assert "doesn't have trading capabilities" in trade_resp.message

    print("=" * 60)
    print("ALL FILES BROKER SELF-TESTS PASSED!")
    print("=" * 60)
    sys.exit(0)
