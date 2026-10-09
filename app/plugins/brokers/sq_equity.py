"""StrategyQuant US Equity market data and symbol catalog broker plugin.

Description:
    Implements a specialized market data broker plugin accessing StrategyQuant
    US Equities historical data. Operates a resilient three-tier resolution
    architecture:
    1. Local native StrategyQuant 4.2 binary (.dat) archives stored under
       `data/market/sq_equity` or optional external `SQX_REFERENCE_ROOT`.
    2. Local partitioned Parquet stores under `data/market/sq_equity` (D1 and M1)
       with PyArrow table-slicing acceleration.
    3. Direct remote streaming and in-memory decoding of Daily (EOD) historical
       bars from StrategyQuant's public CDN mirror (`cdn.strategyquantcdn.com`)
       for instruments absent from local storage.
    Within HaruQuantAI, this module provides decoupled, fast in-memory access
    to normalized US equity and benchmark ETF datasets (e.g. AAPL, MSFT, TSLA,
    NVDA, SPY, QQQ) and exposes canonical instrument metadata (`get_symbol_info()`,
    `get_symbols()`, `get_num_of_symbols()`) alongside `get_bars()`.
    All non-download and trading methods cleanly fallback to BaseBroker default
    unsupported capability handling.

Purpose:
    FEAT-BROKER-SQ-EQUITY: StrategyQuant US Equity Market Data and Catalog Broker.
    Provides fast historical equity bar extraction and dynamic symbol metadata
    queries from local datasets and StrategyQuant CDN without database coupling
    or disk mutations.

Key Capabilities:
    - FR-BROKER-SQ-EQUITY-SYMBOLS: US Equity Symbol Catalog Resolution
      Associated: `[SQEquityBroker.get_symbol_info()]`, `[SQEquityBroker.get_symbols()]`
      Logging: Emits INFO log upon resolving symbol info or catalog count,
      and WARNING log if symbol is not found.
    - FR-BROKER-SQ-EQUITY-MARKET-DATA: Historical Bar Ingestion
      Associated: `[SQEquityBroker.get_bars()]`
      Logging: Emits INFO log upon successfully parsing native SQ 4.2 dat,
      Parquet partitions, or remote StrategyQuant CDN stream, and WARNING log
      if files are missing or empty.

Python API Usage:
    ```python
    from app.plugins.brokers.sq_equity import SQEquityBroker, create_adapter

    broker = create_adapter()
    info_resp = broker.get_symbol_info("AAPL")
    if info_resp.is_success and info_resp.data:
        print(info_resp.data.description, info_resp.data.digits)

    bars_resp = broker.get_bars("AAPL", count=5)
    if bars_resp.is_success and bars_resp.data:
        assert len(bars_resp.data) > 0
    ```

CLI Usage:
    ```bash
    uv run python -m app.plugins.brokers.sq_equity
    ```
"""

from __future__ import annotations

import csv
import io
import os
import struct
import sys
import zipfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, override

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

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
    "id": "broker-sq-equity",
    "name": "StrategyQuant US Equities Connector",
    "version": "1.0.0",
    "description": (
        "StrategyQuant US Equities historical market data and symbol catalog broker"
        " plugin"
    ),
    "author": "HaruQuantAI",
    "slot": "broker",
    "entrypoint": "create_adapter",
    "dependencies": [],
    "capabilities": ["bars", "symbols"],
    "enabled": True,
    "metadata": {
        "provider_name": "SQEquity",
        "display_name": "StrategyQuant US Equities",
        "asset_classes": ["Stocks", "ETFs"],
        "timeframes": ["M1", "D1"],
        "requires_auth": False,
        "rate_limit_rps": 10.0,
    },
}

DEFAULT_DATA_DIR = Path(__file__).resolve().parents[3] / "data" / "market" / "sq_equity"
DEFAULT_CATALOG_PATH = DEFAULT_DATA_DIR / "sq_equity.csv"
CDN_BASE_URL = "https://cdn.strategyquantcdn.com/data/barchart_test/eod"
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)

__all__ = ["CDN_BASE_URL", "SQEquityBroker", "create_adapter"]


def _clean_symbol(symbol: str) -> str:
    """Normalize symbol string stripping suffix artifacts like .D or _limited."""
    s = symbol.strip().upper()
    s = s.removesuffix(".D")
    s = s.removesuffix("_LIMITED")
    return s.removesuffix("_BENCHMARK")


def _normalize_dt(dt: datetime | None) -> datetime | None:
    """Ensure datetime is UTC timezone-aware for clean comparison."""
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC)


def _decode_sq_dat_bytes(
    buf: bytes,
    source_name: str = "buffer",
    count: int | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    start_pos: int | None = 0,
) -> list[Bar]:
    """Decode historical candlestick bars from a StrategyQuant 4.2 binary archive buffer."""
    if len(buf) < 48:
        raise ValueError(f"Corrupt or incomplete SQ dat archive: {source_name}")

    offset = 0

    def read_utf(off: int) -> tuple[str, int]:
        if off + 2 > len(buf):
            raise ValueError(
                f"Unexpected end of file reading UTF length in {source_name}"
            )
        length = struct.unpack_from(">H", buf, off)[0]
        off += 2
        if off + length > len(buf):
            raise ValueError(
                f"Unexpected end of file reading UTF string in {source_name}"
            )
        s = buf[off : off + length].decode("utf-8")
        return s, off + length

    _version, offset = read_utf(offset)
    _timeframe, offset = read_utf(offset)
    _layout, offset = read_utf(offset)

    if offset + 12 > len(buf):
        raise ValueError(f"Invalid header size in {source_name}")

    _total_records, cols = struct.unpack_from(">QI", buf, offset)
    offset += 12 + cols * 7

    _sync_magic, offset = read_utf(offset)

    # Locate all block sync sequences (0x00, 0x01, ..., 0x0e)
    sync_token = bytes(range(15))
    blocks: list[int] = []
    pos = offset
    while True:
        pos = buf.find(sync_token, pos)
        if pos == -1:
            break
        blocks.append(pos)
        pos += 15

    if not blocks:
        return []

    # Optimization: if only tail count is requested without date filters or start_pos,
    # process only the trailing blocks needed to satisfy count (approx 1000 bars per block).
    if (
        date_from is None
        and date_to is None
        and (start_pos is None or start_pos == 0)
        and count is not None
        and count > 0
    ):
        needed_blocks = max(1, (count // 500) + 1)
        start_b_idx = max(0, len(blocks) - needed_blocks)
        blocks_to_process = blocks[start_b_idx:]
    else:
        start_b_idx = 0
        blocks_to_process = blocks

    norm_from = _normalize_dt(date_from)
    norm_to = _normalize_dt(date_to)

    bars: list[Bar] = []

    for b_idx_rel, b_off in enumerate(blocks_to_process):
        abs_idx = start_b_idx + b_idx_rel
        next_b_off = blocks[abs_idx + 1] if abs_idx + 1 < len(blocks) else len(buf)
        curr = b_off + 15 + 7  # 15 bytes sync token + 7 bytes header prefix

        if curr + 48 > next_b_off:
            continue

        ts_ms = struct.unpack_from(">Q", buf, curr)[0]
        o_raw, h_raw, l_raw, c_raw, v_raw = struct.unpack_from(">5q", buf, curr + 8)
        curr += 48

        dt = datetime.fromtimestamp(ts_ms / 1000.0, tz=UTC)
        include_keyframe = True
        if norm_from and dt < norm_from:
            include_keyframe = False
        if norm_to and dt > norm_to:
            include_keyframe = False

        if include_keyframe:
            bars.append(
                Bar(
                    time=dt,
                    open=o_raw / 1_000_000.0,
                    high=h_raw / 1_000_000.0,
                    low=l_raw / 1_000_000.0,
                    close=c_raw / 1_000_000.0,
                    tick_volume=max(0, int(v_raw // 100_000)),
                    real_volume=max(0, int(v_raw // 100_000)),
                )
            )

        while curr < next_b_off:
            if curr + 3 > next_b_off:
                break
            flag_bytes = buf[curr : curr + 3]
            curr += 3

            b0, b1, b2 = flag_bytes[0], flag_bytes[1], flag_bytes[2]
            nybbles = (
                (b0 >> 4) & 0xF,
                b0 & 0xF,
                (b1 >> 4) & 0xF,
                b1 & 0xF,
                (b2 >> 4) & 0xF,
                b2 & 0xF,
            )

            deltas: list[int] = []
            for nyb in nybbles:
                field_len = 1 << (nyb & 0x03)
                if curr + field_len > next_b_off:
                    break
                sign = 1 if (nyb & 0x04) else -1
                raw_val = int.from_bytes(buf[curr : curr + field_len], "big")
                curr += field_len
                deltas.append(sign * raw_val)

            if len(deltas) < 6:
                break

            ts_ms += deltas[0]
            o_raw += deltas[1]
            h_raw += deltas[2]
            l_raw += deltas[3]
            c_raw += deltas[4]
            v_raw += deltas[5]

            bar_dt = datetime.fromtimestamp(ts_ms / 1000.0, tz=UTC)
            if norm_from and bar_dt < norm_from:
                continue
            if norm_to and bar_dt > norm_to:
                continue

            bars.append(
                Bar(
                    time=bar_dt,
                    open=o_raw / 1_000_000.0,
                    high=h_raw / 1_000_000.0,
                    low=l_raw / 1_000_000.0,
                    close=c_raw / 1_000_000.0,
                    tick_volume=max(0, int(v_raw // 100_000)),
                    real_volume=max(0, int(v_raw // 100_000)),
                )
            )

    if start_pos and start_pos > 0 and len(bars) > start_pos:
        bars = bars[start_pos:]

    if count and count > 0 and len(bars) > count:
        bars = bars[-count:]

    return bars


def _decode_sq_dat_bars(
    file_path: Path,
    count: int | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    start_pos: int | None = 0,
) -> list[Bar]:
    """Decode historical candlestick bars from a StrategyQuant 4.2 binary archive."""
    buf = file_path.read_bytes()
    return _decode_sq_dat_bytes(
        buf,
        source_name=str(file_path),
        count=count,
        date_from=date_from,
        date_to=date_to,
        start_pos=start_pos,
    )


def _find_sq_dat_file(
    base_dir: Path,
    symbol: str,
    timeframe: TimeFrame | str | int = TimeFrame.D1,
) -> Path | None:
    """Locate the StrategyQuant .dat file for a symbol and timeframe."""
    if not base_dir.exists():
        return None

    clean = _clean_symbol(symbol).upper()
    if not clean:
        return None
    letter = clean[0]

    tf_str = str(timeframe).upper()
    is_m1 = "M1" in tf_str or "1M" in tf_str
    tf_tag = "M1" if is_m1 else "D1"

    letter_dir = base_dir / letter
    search_dirs = [letter_dir] if letter_dir.exists() else [base_dir]

    for sdir in search_dirs:
        for entry in sdir.iterdir():
            if not entry.is_dir():
                continue
            entry_clean = _clean_symbol(entry.name).upper()
            if entry_clean == clean:
                adj_candidate = entry / f"{entry.name}_{tf_tag}.dat"
                if adj_candidate.is_file():
                    return adj_candidate
                for f in entry.glob(f"*_{tf_tag}.dat"):
                    if "unadjusted" not in f.name.lower():
                        return f
                for f in entry.glob(f"*_{tf_tag}.dat"):
                    return f

    return None


class SQEquityBroker(BaseBroker):
    """StrategyQuant US Equity market data and symbol catalog plugin."""

    def __init__(
        self,
        name: str = "SQ_Equity",
        data_dir: str | Path | None = None,
        catalog_path: str | Path | None = None,
        sqx_history_dir: str | Path | None = None,
        enable_cdn_download: bool = True,
    ) -> None:
        """Initialize SQ Equity broker plugin."""
        super().__init__(
            name=name,
            capabilities=(BrokerCapability.MARKET_DATA | BrokerCapability.SYMBOLS),
        )
        self.data_dir = Path(data_dir) if data_dir else DEFAULT_DATA_DIR
        self.catalog_path = Path(catalog_path) if catalog_path else DEFAULT_CATALOG_PATH
        self.enable_cdn_download = enable_cdn_download

        if sqx_history_dir is not None:
            self.sqx_history_dir: Path | None = Path(sqx_history_dir)
        elif "SQX_REFERENCE_ROOT" in os.environ:
            candidate = (
                Path(os.environ["SQX_REFERENCE_ROOT"])
                / "user"
                / "data"
                / "History"
                / "sq_equity"
            )
            self.sqx_history_dir = candidate if candidate.exists() else None
        else:
            self.sqx_history_dir = None

        self.session = requests.Session()
        self.session.headers.update({"User-Agent": USER_AGENT})
        retry_strategy: Any = Retry(
            total=3,
            backoff_factor=0.3,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "HEAD"],
        )
        adapter = HTTPAdapter(
            max_retries=retry_strategy, pool_connections=8, pool_maxsize=8
        )
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

        self._catalog: dict[str, dict[str, Any]] = {}
        self._catalog_ordered: list[SymbolInfo] = []

    def _ensure_catalog(self) -> None:
        """Load and cache the SQ Equity instrument catalog.

        Raises:
            FileNotFoundError: If the catalog CSV file does not exist.
            ValueError: If the catalog CSV contains no valid instruments.
        """
        if self._catalog:
            return

        if not self.catalog_path.is_file():
            self.logger.error(
                "FR-BROKER-SQ-EQUITY-SYMBOLS: StrategyQuant US Equity catalog CSV"
                " not found: %s",
                self.catalog_path,
                extra={
                    "fr_id": "FR-BROKER-SQ-EQUITY-SYMBOLS",
                    "catalog_path": str(self.catalog_path),
                },
            )
            raise FileNotFoundError(
                f"StrategyQuant US Equity catalog not found: {self.catalog_path}"
            )

        catalog: dict[str, dict[str, Any]] = {}
        ordered: list[SymbolInfo] = []

        try:
            with open(self.catalog_path, encoding="utf-8") as f:
                reader = csv.DictReader(f, delimiter=";")
                for row in reader:
                    sym = (row.get("symbol") or "").strip().upper()
                    if not sym:
                        continue
                    clean_sym = _clean_symbol(sym)
                    name = (row.get("name") or clean_sym).strip()
                    exchange = (row.get("exchange") or "NASDAQ").strip()
                    cat = (row.get("category") or "Stocks").strip()
                    sec_type = (row.get("type") or "Common Stock").strip()
                    dec = int(row.get("decimals") or 2)
                    pt = float(row.get("point") or 0.01)
                    spread = int(float(row.get("spread") or 0))
                    c_size = float(row.get("contract_size") or 1.0)

                    info = SymbolInfo(
                        name=clean_sym,
                        custom=False,
                        digits=dec,
                        point=pt,
                        spread=spread,
                        currency_base="USD",
                        currency_profit="USD",
                        description=f"{name} ({exchange})",
                        category=cat,
                        path=f"US Equities/{cat}/{exchange}",
                        trade_contract_size=c_size,
                        trade_tick_size=pt,
                        trade_tick_value=pt,
                        raw={
                            "symbol": sym,
                            "name": name,
                            "exchange": exchange,
                            "category": cat,
                            "type": sec_type,
                            "date_from": row.get("date_from", ""),
                        },
                    )
                    spec = {
                        "symbol": clean_sym,
                        "name": name,
                        "exchange": exchange,
                        "category": cat,
                        "type": sec_type,
                        "decimals": dec,
                        "point": pt,
                        "spread": spread,
                        "contract_size": c_size,
                        "info": info,
                    }
                    if clean_sym not in catalog:
                        catalog[clean_sym] = spec
                        ordered.append(info)
                    catalog[sym] = spec

            if not catalog:
                self.logger.error(
                    "FR-BROKER-SQ-EQUITY-SYMBOLS: Catalog at %s contains no valid"
                    " instruments",
                    self.catalog_path,
                    extra={
                        "fr_id": "FR-BROKER-SQ-EQUITY-SYMBOLS",
                        "catalog_path": str(self.catalog_path),
                    },
                )
                raise ValueError(
                    f"StrategyQuant US Equity catalog at {self.catalog_path} is"
                    " empty or contains no valid instruments"
                )

            self.logger.info(
                "FR-BROKER-SQ-EQUITY-SYMBOLS: Loaded %d instruments from %s",
                len(ordered),
                self.catalog_path.name,
                extra={
                    "fr_id": "FR-BROKER-SQ-EQUITY-SYMBOLS",
                    "count": len(ordered),
                },
            )
        except Exception as exc:
            if not isinstance(exc, ValueError):
                self.logger.error(
                    "FR-BROKER-SQ-EQUITY-SYMBOLS: Error reading catalog CSV %s: %s",
                    self.catalog_path,
                    exc,
                    extra={
                        "fr_id": "FR-BROKER-SQ-EQUITY-SYMBOLS",
                        "error": str(exc),
                    },
                )
            raise

        self._catalog = catalog
        self._catalog_ordered = ordered

    @override
    def get_symbol_info(self, symbol: str) -> StandardResponse[SymbolInfo]:
        """Query canonical instrument specifications for an SQ Equity symbol."""
        self._ensure_catalog()
        sym_raw = symbol.strip().upper()
        sym_clean = _clean_symbol(sym_raw)

        spec = self._catalog.get(sym_raw) or self._catalog.get(sym_clean)
        if spec:
            info: SymbolInfo = spec["info"]
            self.logger.info(
                "FR-BROKER-SQ-EQUITY-SYMBOLS: Resolved symbol info for %s",
                sym_clean,
                extra={"fr_id": "FR-BROKER-SQ-EQUITY-SYMBOLS", "symbol": sym_clean},
            )
            return StandardResponse.success(
                data=info,
                message=f"Symbol info retrieved for '{symbol}'",
                extensions={"broker": self.name},
            )

        self.logger.warning(
            "FR-BROKER-SQ-EQUITY-SYMBOLS: Symbol '%s' not found in catalog",
            symbol,
            extra={"fr_id": "FR-BROKER-SQ-EQUITY-SYMBOLS", "symbol": symbol},
        )
        msg = f"Symbol '{symbol}' not found in StrategyQuant US Equity catalog"
        return StandardResponse.failure(
            message=msg,
            error=StandardError(code="SYMBOL_NOT_FOUND", message=msg),
            extensions={"broker": self.name},
        )

    @override
    def get_symbols(
        self, group: str | None = None
    ) -> StandardResponse[list[SymbolInfo]]:
        """Retrieve registered SQ Equity instruments, optionally filtered by group."""
        self._ensure_catalog()
        if not group:
            return StandardResponse.success(
                data=list(self._catalog_ordered),
                message=f"Retrieved {len(self._catalog_ordered)} SQ Equity symbols",
                extensions={"broker": self.name},
            )

        grp_lower = group.lower().strip()
        filtered = [
            item["info"]
            for item in self._catalog.values()
            if grp_lower in item["category"].lower()
            or grp_lower in item["exchange"].lower()
            or grp_lower in item["type"].lower()
        ]
        seen: set[str] = set()
        deduped: list[SymbolInfo] = []
        for s in filtered:
            if s.name not in seen:
                seen.add(s.name)
                deduped.append(s)

        return StandardResponse.success(
            data=deduped,
            message=f"Retrieved {len(deduped)} symbols matching group '{group}'",
            extensions={"broker": self.name},
        )

    @override
    def get_num_of_symbols(self) -> StandardResponse[int]:
        """Return the count of distinct instruments registered in the catalog."""
        self._ensure_catalog()
        count = len(self._catalog_ordered)
        self.logger.info(
            "FR-BROKER-SQ-EQUITY-SYMBOLS: Catalog count query returned %d instruments",
            count,
            extra={"fr_id": "FR-BROKER-SQ-EQUITY-SYMBOLS", "count": count},
        )
        return StandardResponse.success(data=count, extensions={"broker": self.name})

    def _fetch_cdn_bars(
        self,
        symbol: str,
        count: int | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        start_pos: int | None = 0,
    ) -> list[Bar] | None:
        """Download and decode daily historical equity bars from StrategyQuant CDN."""
        clean_sym = _clean_symbol(symbol).upper()
        # StrategyQuant CDN packages EOD data into data01.zip (2019+) and data00.zip (pre-2019)
        needs_pre_2019 = False
        if date_from and date_from.year < 2019:
            needs_pre_2019 = True

        zip_targets = ["data01.zip"]
        if needs_pre_2019 or (count and count > 1200):
            zip_targets = ["data00.zip", "data01.zip"]

        all_bars: list[Bar] = []
        downloaded_any = False

        for zip_name in zip_targets:
            url = f"{CDN_BASE_URL}/{clean_sym}/{zip_name}"
            try:
                resp = self.session.get(url, timeout=10)
                if resp.status_code == 200 and resp.content:
                    downloaded_any = True
                    with zipfile.ZipFile(io.BytesIO(resp.content)) as z:
                        dat_names = sorted(
                            f for f in z.namelist() if f.endswith(".dat")
                        )
                        for dat_name in dat_names:
                            # Extract year from filename, e.g. '2023.dat' -> 2023
                            try:
                                file_year = int(dat_name.replace(".dat", ""))
                                if date_from and file_year < date_from.year:
                                    continue
                                if date_to and file_year > date_to.year:
                                    continue
                            except ValueError:
                                pass

                            dat_buf = z.read(dat_name)
                            year_bars = _decode_sq_dat_bytes(
                                dat_buf,
                                source_name=f"{clean_sym}/{zip_name}/{dat_name}",
                                date_from=date_from,
                                date_to=date_to,
                            )
                            all_bars.extend(year_bars)
                elif resp.status_code == 404:
                    self.logger.debug("CDN archive %s not found (HTTP 404)", url)
            except Exception as exc:
                self.logger.warning(
                    "FR-BROKER-SQ-EQUITY-MARKET-DATA: Error downloading from CDN %s: %s",
                    url,
                    exc,
                    extra={
                        "fr_id": "FR-BROKER-SQ-EQUITY-MARKET-DATA",
                        "url": url,
                        "error": str(exc),
                    },
                )

        if not downloaded_any or not all_bars:
            return None

        all_bars.sort(key=lambda b: b.time)
        if start_pos and start_pos > 0 and len(all_bars) > start_pos:
            all_bars = all_bars[start_pos:]
        if count and count > 0 and len(all_bars) > count:
            all_bars = all_bars[-count:]

        return all_bars

    @override
    def get_bars(
        self,
        symbol: str,
        timeframe: TimeFrame | str | int = TimeFrame.D1,
        count: int | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        start_pos: int | None = 0,
    ) -> StandardResponse[list[Bar]]:
        """Retrieve historical candlestick bars using three-tier resolution.

        Resolution tiers:
        1. Local StrategyQuant .dat binary archives.
        2. Local partitioned Parquet store.
        3. Direct StrategyQuant CDN stream (for Daily bars).
        """
        # Tier 1: Check for native StrategyQuant .dat archives
        dat_file = _find_sq_dat_file(self.data_dir, symbol, timeframe)
        if not dat_file and self.sqx_history_dir:
            dat_file = _find_sq_dat_file(self.sqx_history_dir, symbol, timeframe)

        if dat_file:
            try:
                bars = _decode_sq_dat_bars(
                    dat_file,
                    count=count,
                    date_from=date_from,
                    date_to=date_to,
                    start_pos=start_pos,
                )
                self.logger.info(
                    "FR-BROKER-SQ-EQUITY-MARKET-DATA: Loaded %d bars from SQ dat for"
                    " %s",
                    len(bars),
                    symbol,
                    extra={
                        "fr_id": "FR-BROKER-SQ-EQUITY-MARKET-DATA",
                        "symbol": symbol,
                        "count": len(bars),
                        "file": str(dat_file),
                    },
                )
                return StandardResponse.success(
                    data=bars,
                    message=f"Loaded {len(bars)} bars for '{symbol}' from SQ dat",
                    extensions={"broker": self.name, "source": "sq_dat"},
                )
            except Exception as e:
                msg = f"Failed to read SQ dat archive for '{symbol}': {e}"
                return StandardResponse.failure(
                    message=msg,
                    error=StandardError(code="READ_ERROR", message=msg),
                    extensions={"broker": self.name},
                )

        # Tier 2: Check local partitioned Parquet store
        sym_clean = _clean_symbol(symbol).lower()
        tf_str = str(timeframe).upper()
        res_dir = "m1" if "M1" in tf_str or "1M" in tf_str else "d1"

        target_dir = self.data_dir / res_dir / sym_clean
        if not target_dir.exists():
            fallback_dir = self.data_dir / "d1" / sym_clean
            if fallback_dir.exists():
                target_dir = fallback_dir

        if target_dir.exists():
            try:
                import pyarrow.parquet as pq

                parquet_files = sorted(target_dir.glob("*.parquet"))
                if not parquet_files:
                    msg = f"No parquet partitions found for '{symbol}' in {target_dir}"
                    return StandardResponse.failure(
                        message=msg,
                        error=StandardError(code="NO_DATA", message=msg),
                        extensions={"broker": self.name},
                    )

                norm_from = _normalize_dt(date_from)
                norm_to = _normalize_dt(date_to)
                bars = []

                for pf_path in parquet_files:
                    pf = pq.ParquetFile(str(pf_path))
                    table = pf.read()

                    # Fast path table slicing when no date filtering is required
                    if (
                        norm_from is None
                        and norm_to is None
                        and (start_pos is None or start_pos == 0)
                        and count is not None
                        and count > 0
                    ):
                        total_rows = len(table)
                        if total_rows > count:
                            table = table.slice(total_rows - count, count)

                    data_dict = table.to_pydict()
                    dts = data_dict.get("DateTime", [])
                    opens = data_dict.get("Open", [])
                    highs = data_dict.get("High", [])
                    lows = data_dict.get("Low", [])
                    closes = data_dict.get("Close", [])
                    vols = data_dict.get("Volume", [])

                    for i in range(len(dts)):
                        raw_dt = dts[i]
                        if hasattr(raw_dt, "to_pydatetime"):
                            raw_dt = raw_dt.to_pydatetime()
                        if raw_dt is None:
                            continue
                        dt_norm = _normalize_dt(raw_dt)
                        if dt_norm is None:
                            continue

                        if norm_from and dt_norm < norm_from:
                            continue
                        if norm_to and dt_norm > norm_to:
                            continue

                        bars.append(
                            Bar(
                                time=dt_norm,
                                open=float(opens[i]),
                                high=float(highs[i]),
                                low=float(lows[i]),
                                close=float(closes[i]),
                                tick_volume=int(vols[i] if i < len(vols) else 0),
                                real_volume=int(vols[i] if i < len(vols) else 0),
                            )
                        )

                    if start_pos and start_pos > 0 and len(bars) > start_pos:
                        bars = bars[start_pos:]

                    if count and count > 0 and len(bars) > count:
                        bars = bars[-count:]

                    if bars:
                        self.logger.info(
                            "FR-BROKER-SQ-EQUITY-MARKET-DATA: Loaded %d bars for %s",
                            len(bars),
                            symbol,
                            extra={
                                "fr_id": "FR-BROKER-SQ-EQUITY-MARKET-DATA",
                                "symbol": symbol,
                                "count": len(bars),
                            },
                        )
                        return StandardResponse.success(
                            data=bars,
                            message=f"Loaded {len(bars)} bars for '{symbol}'",
                            extensions={"broker": self.name, "source": "parquet"},
                        )
            except Exception as e:
                msg = f"Failed to read parquet bars for '{symbol}': {e}"
                return StandardResponse.failure(
                    message=msg,
                    error=StandardError(code="READ_ERROR", message=msg),
                    extensions={"broker": self.name},
                )

        # Tier 3: Query StrategyQuant CDN for Daily (D1) historical bars
        is_daily = "D" in tf_str or "DAILY" in tf_str or tf_str in ("D1", "1D", "86400")
        if self.enable_cdn_download and is_daily:
            cdn_bars = self._fetch_cdn_bars(
                symbol,
                count=count,
                date_from=date_from,
                date_to=date_to,
                start_pos=start_pos,
            )
            if cdn_bars:
                self.logger.info(
                    "FR-BROKER-SQ-EQUITY-MARKET-DATA: Loaded %d bars for %s from"
                    " StrategyQuant CDN",
                    len(cdn_bars),
                    symbol,
                    extra={
                        "fr_id": "FR-BROKER-SQ-EQUITY-MARKET-DATA",
                        "symbol": symbol,
                        "count": len(cdn_bars),
                    },
                )
                return StandardResponse.success(
                    data=cdn_bars,
                    message=(
                        f"Loaded {len(cdn_bars)} bars for '{symbol}' from StrategyQuant"
                        " CDN"
                    ),
                    extensions={"broker": self.name, "source": "cdn"},
                )

        msg = (
            f"No equity data found for symbol '{symbol}' (timeframe={timeframe}) locally"
            " or on StrategyQuant CDN"
        )
        self.logger.warning(
            "FR-BROKER-SQ-EQUITY-MARKET-DATA: %s",
            msg,
            extra={
                "fr_id": "FR-BROKER-SQ-EQUITY-MARKET-DATA",
                "symbol": symbol,
                "timeframe": str(timeframe),
            },
        )
        return StandardResponse.failure(
            message=msg,
            error=StandardError(code="NOT_FOUND", message=msg),
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
        """Return unsupported capability response as SQ Equity does not store ticks."""
        msg = f"Tick data is not supported by {self.name}"
        return StandardResponse.failure(
            message=msg,
            error=StandardError(code="UNSUPPORTED_CAPABILITY", message=msg),
            extensions={"broker": self.name},
        )


def create_adapter(_context: PluginHostContext | None = None) -> SQEquityBroker:
    """Plugin entrypoint factory constructing SQEquityBroker adapter."""
    logger.info("Initializing SQ Equity broker plugin adapter.")
    return SQEquityBroker()


if __name__ == "__main__":
    print("=" * 60)
    print("SQ Equity Broker Plugin Self-Test")
    print("=" * 60)

    broker = create_adapter()

    # 1. Test symbol info query
    info_resp = broker.get_symbol_info("AAPL")
    print(
        f"[1] Symbol Info AAPL: success={info_resp.is_success}, "
        f"description='{info_resp.data.description if info_resp.data else None}'"
    )
    assert info_resp.is_success, f"AAPL symbol info failed: {info_resp.message}"
    assert info_resp.data is not None
    assert info_resp.data.name == "AAPL"

    # 2. Test total count
    count_resp = broker.get_num_of_symbols()
    print(f"[2] Total Symbols: {count_resp.data}")
    assert count_resp.is_success
    assert count_resp.data is not None
    assert count_resp.data >= 10

    # 3. Test symbols listing
    syms_resp = broker.get_symbols(group="ETFs")
    print(f"[3] ETFs Symbols count: {len(syms_resp.data) if syms_resp.data else 0}")
    assert syms_resp.is_success
    assert syms_resp.data is not None
    assert len(syms_resp.data) > 0

    # 4. Test real historical bars for AAPL (Daily)
    bars_resp = broker.get_bars("AAPL", timeframe=TimeFrame.D1, count=5)
    print(
        f"[4] Real SQ Equity Bars AAPL (D1): success={bars_resp.is_success}, "
        f"count={len(bars_resp.data) if bars_resp.data else 0}"
    )
    assert bars_resp.is_success, f"Bars retrieval failed: {bars_resp.message}"
    assert bars_resp.data is not None
    assert len(bars_resp.data) == 5
    first_b, last_b = bars_resp.data[0], bars_resp.data[-1]
    print(
        f"    AAPL First Bar: {first_b.time.date()} O={first_b.open:.2f} "
        f"H={first_b.high:.2f} L={first_b.low:.2f} C={first_b.close:.2f} "
        f"V={first_b.real_volume}"
    )
    print(
        f"    AAPL Last Bar:  {last_b.time.date()} O={last_b.open:.2f} "
        f"H={last_b.high:.2f} L={last_b.low:.2f} C={last_b.close:.2f} "
        f"V={last_b.real_volume}"
    )

    # 5. Test real historical bars for SPY Benchmark ETF (Daily)
    spy_resp = broker.get_bars("SPY", timeframe=TimeFrame.D1, count=5)
    print(
        f"[5] Real SQ Equity Bars SPY (D1): success={spy_resp.is_success}, "
        f"count={len(spy_resp.data) if spy_resp.data else 0}"
    )
    assert spy_resp.is_success, f"SPY bars failed: {spy_resp.message}"
    assert spy_resp.data is not None
    assert len(spy_resp.data) == 5
    spy_first, spy_last = spy_resp.data[0], spy_resp.data[-1]
    print(
        f"    SPY First Bar: {spy_first.time.date()} O={spy_first.open:.2f} "
        f"H={spy_first.high:.2f} L={spy_first.low:.2f} C={spy_first.close:.2f} "
        f"V={spy_first.real_volume}"
    )
    print(
        f"    SPY Last Bar:  {spy_last.time.date()} O={spy_last.open:.2f} "
        f"H={spy_last.high:.2f} L={spy_last.low:.2f} C={spy_last.close:.2f} "
        f"V={spy_last.real_volume}"
    )

    # 6. Test real M1 intraday bars for AAPL
    m1_resp = broker.get_bars("AAPL", timeframe=TimeFrame.M1, count=5)
    print(
        f"[6] Real SQ Equity Bars AAPL (M1): success={m1_resp.is_success}, "
        f"count={len(m1_resp.data) if m1_resp.data else 0}"
    )
    assert m1_resp.is_success, f"AAPL M1 bars failed: {m1_resp.message}"
    assert m1_resp.data is not None
    assert len(m1_resp.data) == 5
    m1_last = m1_resp.data[-1]
    print(
        f"    AAPL M1 Last Bar: {m1_last.time.isoformat()} O={m1_last.open:.2f} "
        f"C={m1_last.close:.2f} V={m1_last.real_volume}"
    )

    # 7. Test StrategyQuant CDN live remote download (EOD daily bars for NVDA)
    nvda_resp = broker.get_bars("NVDA", timeframe=TimeFrame.D1, count=5)
    print(
        f"[7] Remote SQ CDN Bars NVDA (D1): success={nvda_resp.is_success}, "
        f"count={len(nvda_resp.data) if nvda_resp.data else 0}, "
        f"source='{nvda_resp.metadata.extensions.get('source')}'"
    )
    assert nvda_resp.is_success, f"NVDA CDN bars failed: {nvda_resp.message}"
    assert nvda_resp.data is not None
    assert len(nvda_resp.data) == 5
    nvda_last = nvda_resp.data[-1]
    print(
        f"    NVDA CDN Last Bar: {nvda_last.time.date()} O={nvda_last.open:.2f} "
        f"H={nvda_last.high:.2f} L={nvda_last.low:.2f} C={nvda_last.close:.2f} "
        f"V={nvda_last.real_volume}"
    )

    # 8. Test trading rejection
    from app.plugins.brokers.contracts import TradeRequest

    trade_resp = broker.trade(TradeRequest(symbol="AAPL", volume=1.0))
    print(
        f"[8] Trade Rejection: success={trade_resp.is_success}, "
        f"message='{trade_resp.message}'"
    )
    assert not trade_resp.is_success
    assert "doesn't have trading capabilities" in trade_resp.message

    print("=" * 60)
    print("ALL SQ EQUITY REAL DATA & CDN SELF-TESTS PASSED!")
    print("=" * 60)
    sys.exit(0)
