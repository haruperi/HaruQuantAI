"""StrategyQuant Continuous Futures market data and symbol catalog broker plugin.

Description:
    Implements a specialized market data broker plugin accessing StrategyQuant
    Continuous Futures historical candlestick archives stored under
    `data/market/sq_futures`.
    Within HaruQuantAI, this module provides decoupled, fast in-memory access
    to normalized continuous futures datasets (e.g. @ES, @NQ, @YM, @CL, @GC, @SI)
    and exposes canonical instrument metadata (`get_symbol_info()`,
    `get_symbols()`, `get_num_of_symbols()`) alongside `get_bars()`.
    Supports multi-format bar ingestion including columnar Parquet partitions,
    StrategyQuant 4.2 binary archives (`.dat`), and optional remote StrategyQuant
    CDN archive streaming.
    All non-market-data and trading methods cleanly fallback to BaseBroker default
    unsupported capability handling.

Purpose:
    FEAT-BROKER-SQ-FUTURES: StrategyQuant Continuous Futures Datafeed & Catalog.
    Provides fast historical futures bar extraction and dynamic symbol metadata
    queries from local datasets and remote CDN without database coupling or disk mutations.

Key Capabilities:
    - FR-BROKER-SQ-FUTURES-SYMBOLS: Continuous Futures Symbol Catalog Resolution
      Associated: `[SQFuturesBroker.get_symbol_info()]`, `[SQFuturesBroker.get_symbols()]`
      Logging: Emits INFO log upon resolving symbol info or catalog count,
      and WARNING log if symbol is not found.
    - FR-BROKER-SQ-FUTURES-MARKET-DATA: Multi-Source Historical Candlestick Bar Ingestion
      Associated: `[SQFuturesBroker.get_bars()]`
      Logging: Emits INFO log upon successfully parsing Parquet partitions,
      StrategyQuant 4.2 `.dat` archives, or remote CDN streams, and WARNING log if files
      are missing or empty.

Python API Usage:
    ```python
    from app.plugins.brokers.sq_futures import SQFuturesBroker, create_adapter

    broker = create_adapter()
    info_resp = broker.get_symbol_info("@ES")
    if info_resp.is_success and info_resp.data:
        print(info_resp.data.description, info_resp.data.digits)

    bars_resp = broker.get_bars("@ES", count=5)
    if bars_resp.is_success and bars_resp.data:
        assert len(bars_resp.data) > 0
    ```

CLI Usage:
    ```bash
    uv run python -m app.plugins.brokers.sq_futures
    ```
"""

from __future__ import annotations

import csv
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
    "id": "broker-sq-futures",
    "name": "StrategyQuant Continuous Futures Connector",
    "version": "1.0.0",
    "description": (
        "StrategyQuant Continuous Futures historical market data and symbol catalog broker plugin"
    ),
    "author": "HaruQuantAI",
    "slot": "broker",
    "entrypoint": "create_adapter",
    "dependencies": [],
    "capabilities": ["bars", "symbols"],
    "enabled": True,
    "metadata": {
        "provider_name": "SQFutures",
        "display_name": "StrategyQuant Continuous Futures",
        "asset_classes": ["Futures"],
        "timeframes": ["M1", "D1"],
        "requires_auth": False,
        "rate_limit_rps": 10.0,
    },
}

DEFAULT_DATA_DIR = (
    Path(__file__).resolve().parents[3] / "data" / "market" / "sq_futures"
)
DEFAULT_CATALOG_PATH = DEFAULT_DATA_DIR / "sq_futures.csv"
CDN_BASE_URL = "https://cdn.strategyquantcdn.com/data/barchart_test/eod"
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)

__all__ = ["CDN_BASE_URL", "SQFuturesBroker", "create_adapter"]


def _clean_symbol(symbol: str) -> str:
    """Normalize continuous futures symbol stripping suffix artifacts like .D."""
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
    # process only the trailing blocks needed to satisfy count.
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
    data_dir: Path, symbol: str, timeframe: TimeFrame | str | int
) -> Path | None:
    """Search for StrategyQuant .dat file under data_dir using standard naming conventions."""
    sym_clean = symbol.lower().strip()
    sym_no_at = sym_clean.lstrip("@")
    sym_at = f"@{sym_no_at}"
    tf_str = str(timeframe).upper()
    tf_suffix = "M1" if "M1" in tf_str or "1M" in tf_str else "D1"

    candidates = [
        # 1. Structured partition dat directories
        data_dir / "dat" / tf_suffix.lower() / sym_at,
        data_dir / "dat" / tf_suffix.lower() / sym_no_at,
        data_dir / tf_suffix.lower() / sym_at,
        data_dir / tf_suffix.lower() / sym_no_at,
        # 2. StrategyQuant History folder layout: history/@/@EW/@EW_D1.dat
        data_dir / "history" / "@" / sym_at,
        data_dir / "history" / "@" / sym_no_at,
        data_dir / sym_at,
        data_dir / sym_no_at,
    ]

    for c in candidates:
        if c.is_dir():
            # Check for direct file matches first
            exact_match = c / f"{sym_at}_{tf_suffix}.dat"
            if exact_match.is_file():
                return exact_match
            exact_no_at = c / f"{sym_no_at}_{tf_suffix}.dat"
            if exact_no_at.is_file():
                return exact_no_at
            # Check for any .dat file in folder
            dat_files = sorted(c.glob("*.dat"))
            if dat_files:
                return dat_files[-1]

    # Check direct files in data_dir root
    direct_candidates = [
        data_dir / f"{sym_at}_{tf_suffix}.dat",
        data_dir / f"{sym_no_at}_{tf_suffix}.dat",
        data_dir / f"{sym_at}.dat",
        data_dir / f"{sym_no_at}.dat",
    ]
    for dc in direct_candidates:
        if dc.is_file():
            return dc

    return None


class SQFuturesBroker(BaseBroker):
    """StrategyQuant Continuous Futures market data and symbol catalog plugin."""

    def __init__(
        self,
        name: str = "SQ_Futures",
        data_dir: str | Path | None = None,
        catalog_path: str | Path | None = None,
    ) -> None:
        """Initialize SQ Futures broker plugin."""
        super().__init__(
            name=name,
            capabilities=(BrokerCapability.MARKET_DATA | BrokerCapability.SYMBOLS),
        )
        self.data_dir = Path(data_dir) if data_dir else DEFAULT_DATA_DIR
        self.catalog_path = Path(catalog_path) if catalog_path else DEFAULT_CATALOG_PATH
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
        """Load and cache the SQ Futures instrument catalog.

        Raises:
            FileNotFoundError: If the catalog CSV file does not exist.
            ValueError: If the catalog CSV contains no valid instruments.
        """
        if self._catalog:
            return

        if not self.catalog_path.is_file():
            self.logger.error(
                "FR-BROKER-SQ-FUTURES-SYMBOLS: StrategyQuant Continuous Futures catalog CSV not found: %s",
                self.catalog_path,
                extra={
                    "fr_id": "FR-BROKER-SQ-FUTURES-SYMBOLS",
                    "catalog_path": str(self.catalog_path),
                },
            )
            raise FileNotFoundError(
                f"StrategyQuant Continuous Futures catalog not found: {self.catalog_path}"
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
                    exchange = (row.get("exchange") or "CME").strip()
                    cat = (row.get("category") or "Indices").strip()
                    sec_type = (row.get("type") or "Continuous Futures").strip()
                    dec = int(row.get("decimals") or 2)
                    pt = float(row.get("point") or 0.25)
                    spread = int(float(row.get("spread") or 1))
                    c_size = float(row.get("contract_size") or 1.0)
                    pt_val = float(row.get("point_value") or 50.0)

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
                        path=f"Futures/{cat}/{exchange}",
                        trade_contract_size=c_size,
                        trade_tick_size=pt,
                        trade_tick_value=pt_val,
                        raw={
                            "symbol": sym,
                            "name": name,
                            "exchange": exchange,
                            "category": cat,
                            "type": sec_type,
                            "point_value": pt_val,
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
                        "point_value": pt_val,
                        "info": info,
                    }
                    if clean_sym not in catalog:
                        catalog[clean_sym] = spec
                        ordered.append(info)
                    catalog[sym] = spec
                    # Also map stripped ticker without '@' for flexible lookup (e.g. 'ES')
                    stripped = clean_sym.lstrip("@")
                    if stripped and stripped not in catalog:
                        catalog[stripped] = spec

            if not catalog:
                self.logger.error(
                    "FR-BROKER-SQ-FUTURES-SYMBOLS: Catalog at %s contains no valid instruments",
                    self.catalog_path,
                    extra={
                        "fr_id": "FR-BROKER-SQ-FUTURES-SYMBOLS",
                        "catalog_path": str(self.catalog_path),
                    },
                )
                raise ValueError(
                    f"StrategyQuant Continuous Futures catalog at {self.catalog_path} is empty or contains no valid instruments"
                )

            self.logger.info(
                "FR-BROKER-SQ-FUTURES-SYMBOLS: Loaded %d instruments from %s",
                len(ordered),
                self.catalog_path.name,
                extra={
                    "fr_id": "FR-BROKER-SQ-FUTURES-SYMBOLS",
                    "count": len(ordered),
                },
            )
        except Exception as exc:
            if not isinstance(exc, ValueError):
                self.logger.error(
                    "FR-BROKER-SQ-FUTURES-SYMBOLS: Error reading catalog CSV %s: %s",
                    self.catalog_path,
                    exc,
                    extra={
                        "fr_id": "FR-BROKER-SQ-FUTURES-SYMBOLS",
                        "error": str(exc),
                    },
                )
            raise

        self._catalog = catalog
        self._catalog_ordered = ordered

    @override
    def get_symbol_info(self, symbol: str) -> StandardResponse[SymbolInfo]:
        """Query canonical instrument specifications for an SQ Futures symbol."""
        self._ensure_catalog()
        sym_raw = symbol.strip().upper()
        sym_clean = _clean_symbol(sym_raw)
        sym_at = sym_clean if sym_clean.startswith("@") else f"@{sym_clean}"
        sym_no_at = sym_clean.lstrip("@")

        spec = (
            self._catalog.get(sym_raw)
            or self._catalog.get(sym_clean)
            or self._catalog.get(sym_at)
            or self._catalog.get(sym_no_at)
        )
        if spec:
            info: SymbolInfo = spec["info"]
            self.logger.info(
                "FR-BROKER-SQ-FUTURES-SYMBOLS: Resolved symbol info for %s",
                info.name,
                extra={"fr_id": "FR-BROKER-SQ-FUTURES-SYMBOLS", "symbol": info.name},
            )
            return StandardResponse.success(
                data=info,
                message=f"Symbol info retrieved for '{symbol}'",
                extensions={"broker": self.name},
            )

        self.logger.warning(
            "FR-BROKER-SQ-FUTURES-SYMBOLS: Symbol '%s' not found in catalog",
            symbol,
            extra={"fr_id": "FR-BROKER-SQ-FUTURES-SYMBOLS", "symbol": symbol},
        )
        msg = f"Symbol '{symbol}' not found in StrategyQuant Futures catalog."
        return StandardResponse.failure(
            message=msg,
            error=StandardError(code="SYMBOL_NOT_FOUND", message=msg),
            extensions={"broker": self.name},
        )

    @override
    def get_symbols(
        self, group: str | None = None
    ) -> StandardResponse[list[SymbolInfo]]:
        """Retrieve available continuous futures symbols, optionally filtered by group."""
        self._ensure_catalog()
        symbols = self._catalog_ordered
        if group:
            g_upper = group.strip().upper()
            symbols = [
                s
                for s in symbols
                if (s.category and g_upper in s.category.upper())
                or (s.path and g_upper in s.path.upper())
                or (s.description and g_upper in s.description.upper())
                or (s.raw and g_upper == str(s.raw.get("exchange", "")).upper())
            ]
            self.logger.info(
                "FR-BROKER-SQ-FUTURES-SYMBOLS: Filtered symbols by group '%s', count=%d",
                group,
                len(symbols),
                extra={
                    "fr_id": "FR-BROKER-SQ-FUTURES-SYMBOLS",
                    "group": group,
                    "count": len(symbols),
                },
            )
            return StandardResponse.success(
                data=symbols,
                message=f"Retrieved {len(symbols)} symbols matching group '{group}'",
                extensions={"broker": self.name},
            )

        self.logger.info(
            "FR-BROKER-SQ-FUTURES-SYMBOLS: Retrieved all %d continuous futures symbols",
            len(symbols),
            extra={"fr_id": "FR-BROKER-SQ-FUTURES-SYMBOLS", "count": len(symbols)},
        )
        return StandardResponse.success(
            data=symbols,
            message="Retrieved all continuous futures symbols",
            extensions={"broker": self.name},
        )

    @override
    def get_num_of_symbols(self) -> StandardResponse[int]:
        """Return the total number of continuous futures instruments in the catalog."""
        self._ensure_catalog()
        count = len(self._catalog_ordered)
        self.logger.info(
            "FR-BROKER-SQ-FUTURES-SYMBOLS: Catalog count query returned %d instruments",
            count,
            extra={"fr_id": "FR-BROKER-SQ-FUTURES-SYMBOLS", "count": count},
        )
        return StandardResponse.success(data=count, extensions={"broker": self.name})

    def _fetch_cdn_bars(
        self,
        symbol: str,
        target_dir: Path,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        count: int | None = None,
    ) -> list[Bar]:
        """Fetch continuous futures candlestick data from StrategyQuant CDN mirror."""
        clean_sym = _clean_symbol(symbol).lstrip("@")
        target_dir.mkdir(parents=True, exist_ok=True)

        zip_names = ["data01.zip"]
        if date_from and date_from.year < 2019:
            zip_names.insert(0, "data00.zip")

        found_any = False
        for zip_name in zip_names:
            zip_path = target_dir / zip_name
            if not zip_path.exists() or zip_path.stat().st_size == 0:
                url = f"{CDN_BASE_URL}/{clean_sym}/{zip_name}"
                try:
                    self.logger.info(
                        "FR-BROKER-SQ-FUTURES-MARKET-DATA: Downloading %s from %s",
                        zip_name,
                        url,
                        extra={
                            "fr_id": "FR-BROKER-SQ-FUTURES-MARKET-DATA",
                            "symbol": symbol,
                            "url": url,
                        },
                    )
                    resp = self.session.get(url, timeout=15)
                    if resp.status_code == 200 and len(resp.content) > 100:
                        zip_path.write_bytes(resp.content)
                        found_any = True
                    elif resp.status_code == 404:
                        self.logger.debug("CDN archive %s not found (HTTP 404)", url)
                except Exception as exc:
                    self.logger.debug("CDN download skipped for %s: %s", url, exc)
            else:
                found_any = True

        if not found_any and not any(target_dir.glob("*.dat")):
            return []

        # Unpack all downloaded zip archives
        for zp in sorted(target_dir.glob("*.zip")):
            try:
                with zipfile.ZipFile(zp) as zf:
                    zf.extractall(target_dir)
            except Exception:
                pass

        # Read and parse extracted .dat files
        dat_files = sorted(target_dir.glob("*.dat"))
        if not dat_files:
            return []

        all_bars: list[Bar] = []
        for df in dat_files:
            try:
                bars = _decode_sq_dat_bars(df)
                all_bars.extend(bars)
            except Exception as e:
                self.logger.warning("Failed to decode dat file %s: %s", df, e)

        all_bars.sort(key=lambda b: b.time)
        norm_from = _normalize_dt(date_from)
        norm_to = _normalize_dt(date_to)

        filtered = [
            b
            for b in all_bars
            if (norm_from is None or b.time >= norm_from)
            and (norm_to is None or b.time <= norm_to)
        ]

        if count and count > 0 and len(filtered) > count:
            filtered = filtered[-count:]

        return filtered

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
        """Retrieve historical candlestick bars from Parquet, StrategyQuant dat, or CDN mirror.

        Hierarchical fallback pipeline:
        1. Local Parquet partitions (`.parquet`).
        2. Local StrategyQuant 4.2 binary archives (`.dat`).
        3. Remote StrategyQuant CDN archive streaming.
        """
        sym_clean = _clean_symbol(symbol).lower().strip()
        sym_no_at = sym_clean.lstrip("@")
        sym_at = f"@{sym_no_at}"

        tf_str = str(timeframe).upper()
        res_dir = "m1" if "M1" in tf_str or "1M" in tf_str else "d1"

        # ----------------------------------------------------------------------
        # Priority 1: Check for Parquet partitions
        # ----------------------------------------------------------------------
        target_parquet_dir = self.data_dir / res_dir / sym_at
        if not target_parquet_dir.exists():
            target_parquet_dir = self.data_dir / res_dir / sym_no_at

        if not target_parquet_dir.exists():
            alt_res = "d1" if res_dir == "m1" else "m1"
            alt_dir = self.data_dir / alt_res / sym_at
            if not alt_dir.exists():
                alt_dir = self.data_dir / alt_res / sym_no_at
            if alt_dir.exists():
                target_parquet_dir = alt_dir

        if target_parquet_dir.exists():
            try:
                import pyarrow.parquet as pq

                parquet_files = sorted(target_parquet_dir.glob("*.parquet"))
                if parquet_files:
                    bars: list[Bar] = []
                    for pf_path in parquet_files:
                        pf = pq.ParquetFile(str(pf_path))
                        table = pf.read()
                        data_dict = table.to_pydict()
                        dts = data_dict.get("DateTime", [])
                        opens = data_dict.get("Open", [])
                        highs = data_dict.get("High", [])
                        lows = data_dict.get("Low", [])
                        closes = data_dict.get("Close", [])
                        vols = data_dict.get("Volume", [])

                        for i in range(len(dts)):
                            dt = dts[i]
                            if hasattr(dt, "to_pydatetime"):
                                dt = dt.to_pydatetime()
                            dt_norm = _normalize_dt(dt)
                            norm_from = _normalize_dt(date_from)
                            norm_to = _normalize_dt(date_to)

                            if norm_from and dt_norm and dt_norm < norm_from:
                                continue
                            if norm_to and dt_norm and dt_norm > norm_to:
                                continue

                            bars.append(
                                Bar(
                                    time=dt_norm or dt,
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

                    self.logger.info(
                        "FR-BROKER-SQ-FUTURES-MARKET-DATA: Loaded %d bars for %s from Parquet",
                        len(bars),
                        symbol,
                        extra={
                            "fr_id": "FR-BROKER-SQ-FUTURES-MARKET-DATA",
                            "symbol": symbol,
                            "count": len(bars),
                            "format": "parquet",
                        },
                    )
                    return StandardResponse.success(
                        data=bars,
                        message=f"Loaded {len(bars)} bars for '{symbol}' from Parquet",
                        extensions={"broker": self.name},
                    )

                msg = f"No parquet partitions found for '{symbol}' in {target_parquet_dir}"
                self.logger.warning(
                    "FR-BROKER-SQ-FUTURES-MARKET-DATA: %s",
                    msg,
                    extra={
                        "fr_id": "FR-BROKER-SQ-FUTURES-MARKET-DATA",
                        "symbol": symbol,
                    },
                )
                return StandardResponse.failure(
                    message=msg,
                    error=StandardError(code="NO_DATA", message=msg),
                    extensions={"broker": self.name},
                )
            except Exception as e:
                msg = f"Failed to read parquet bars for '{symbol}': {e}"
                self.logger.error(
                    "FR-BROKER-SQ-FUTURES-MARKET-DATA: Error reading parquet bars for %s: %s",
                    symbol,
                    e,
                    extra={
                        "fr_id": "FR-BROKER-SQ-FUTURES-MARKET-DATA",
                        "error": str(e),
                    },
                )
                return StandardResponse.failure(
                    message=msg,
                    error=StandardError(code="READ_ERROR", message=msg),
                    extensions={"broker": self.name},
                )

        # ----------------------------------------------------------------------
        # Priority 2: Check for local StrategyQuant 4.2 .dat binary files
        # ----------------------------------------------------------------------
        dat_file = _find_sq_dat_file(self.data_dir, symbol, timeframe)
        if dat_file and dat_file.is_file():
            try:
                bars = _decode_sq_dat_bars(
                    dat_file,
                    count=count,
                    date_from=date_from,
                    date_to=date_to,
                    start_pos=start_pos,
                )
                self.logger.info(
                    "FR-BROKER-SQ-FUTURES-MARKET-DATA: Loaded %d bars for %s from StrategyQuant dat: %s",
                    len(bars),
                    symbol,
                    dat_file.name,
                    extra={
                        "fr_id": "FR-BROKER-SQ-FUTURES-MARKET-DATA",
                        "symbol": symbol,
                        "count": len(bars),
                        "file": str(dat_file),
                        "format": "dat",
                    },
                )
                return StandardResponse.success(
                    data=bars,
                    message=f"Loaded {len(bars)} bars for '{symbol}' from SQ dat",
                    extensions={"broker": self.name},
                )
            except Exception as e:
                msg = f"Failed to read SQ dat archive {dat_file}: {e}"
                self.logger.error(
                    "FR-BROKER-SQ-FUTURES-MARKET-DATA: Error reading SQ dat for %s: %s",
                    symbol,
                    e,
                    extra={
                        "fr_id": "FR-BROKER-SQ-FUTURES-MARKET-DATA",
                        "error": str(e),
                    },
                )
                return StandardResponse.failure(
                    message=msg,
                    error=StandardError(code="READ_ERROR", message=msg),
                    extensions={"broker": self.name},
                )

        # ----------------------------------------------------------------------
        # Priority 3: Remote CDN Fallback
        # ----------------------------------------------------------------------
        cdn_target_dir = self.data_dir / "dat" / res_dir / sym_no_at
        try:
            cdn_bars = self._fetch_cdn_bars(
                symbol=symbol,
                target_dir=cdn_target_dir,
                date_from=date_from,
                date_to=date_to,
                count=count,
            )
            if cdn_bars:
                self.logger.info(
                    "FR-BROKER-SQ-FUTURES-MARKET-DATA: Loaded %d bars for %s from remote CDN mirror",
                    len(cdn_bars),
                    symbol,
                    extra={
                        "fr_id": "FR-BROKER-SQ-FUTURES-MARKET-DATA",
                        "symbol": symbol,
                        "count": len(cdn_bars),
                        "format": "cdn",
                    },
                )
                return StandardResponse.success(
                    data=cdn_bars,
                    message=f"Loaded {len(cdn_bars)} bars for '{symbol}' from SQ CDN mirror",
                    extensions={"broker": self.name},
                )
        except Exception as e:
            self.logger.warning(
                "FR-BROKER-SQ-FUTURES-MARKET-DATA: Remote CDN download error for %s: %s",
                symbol,
                e,
            )

        msg = f"No local futures data found for symbol '{symbol}' in {self.data_dir}"
        self.logger.warning(
            "FR-BROKER-SQ-FUTURES-MARKET-DATA: %s",
            msg,
            extra={"fr_id": "FR-BROKER-SQ-FUTURES-MARKET-DATA", "symbol": symbol},
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
        """Return unsupported capability response as SQ Futures does not store tick archives."""
        msg = f"Tick data is not supported by {self.name}"
        return StandardResponse.failure(
            message=msg,
            error=StandardError(code="UNSUPPORTED_CAPABILITY", message=msg),
            extensions={"broker": self.name},
        )


def create_adapter(_context: PluginHostContext | None = None) -> SQFuturesBroker:
    """Plugin entrypoint factory constructing SQFuturesBroker adapter."""
    logger.info("Initializing SQ Futures broker plugin adapter.")
    return SQFuturesBroker()


if __name__ == "__main__":
    print("=" * 60)
    print("SQ Futures Broker Plugin Self-Test")
    print("=" * 60)

    broker = create_adapter()

    # 1. Test symbol info query
    info_resp = broker.get_symbol_info("@ES")
    print(
        f"[1] Symbol Info @ES: success={info_resp.is_success}, "
        f"description='{info_resp.data.description if info_resp.data else None}'"
    )
    assert info_resp.is_success, f"@ES symbol info failed: {info_resp.message}"
    assert info_resp.data is not None
    assert info_resp.data.name == "@ES"

    # 2. Test total count
    count_resp = broker.get_num_of_symbols()
    print(f"[2] Total Symbols: {count_resp.data}")
    assert count_resp.is_success
    assert count_resp.data is not None
    assert count_resp.data >= 50

    # 3. Test symbols listing
    syms_resp = broker.get_symbols(group="Energies")
    print(f"[3] Energies Symbols count: {len(syms_resp.data) if syms_resp.data else 0}")
    assert syms_resp.is_success
    assert syms_resp.data is not None
    assert len(syms_resp.data) > 0

    # 4. Test historical bars
    bars_resp = broker.get_bars("@ES", count=5)
    print(
        f"[4] Bars @ES: success={bars_resp.is_success}, "
        f"count={len(bars_resp.data) if bars_resp.data else 0}"
    )
    assert bars_resp.is_success, f"Bars retrieval failed: {bars_resp.message}"
    assert bars_resp.data is not None
    assert len(bars_resp.data) == 5

    # 5. Test trading rejection
    from app.plugins.brokers.contracts import TradeRequest

    trade_resp = broker.trade(TradeRequest(symbol="@ES", volume=1.0))
    print(
        f"[5] Trade Rejection: success={trade_resp.is_success}, "
        f"message='{trade_resp.message}'"
    )
    assert not trade_resp.is_success
    assert "doesn't have trading capabilities" in trade_resp.message

    print("=" * 60)
    print("ALL SQ FUTURES SELF-TESTS PASSED!")
    print("=" * 60)
    sys.exit(0)
