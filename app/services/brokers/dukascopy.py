"""Dukascopy market data and authoritative symbol catalog client implementation.

Description:
    Implements an unauthenticated market data and symbol metadata client
    for Dukascopy Bank SA conforming to the uniform `BrokerClient` interface.
    Fetches historical candlestick bars and ticks over HTTP in memory or from local
    data directories, decodes native LZMA `.bi5` streams, and dynamically resolves
    instrument specifications from the authoritative catalog CSV
    (`data/market/dukascopy/dukascopy.csv`) returning canonical `SymbolInfo` objects.

Purpose:
    FEAT-BROKER-DUKASCOPY: Dukascopy Market Data and Symbol Catalog Provider.

Key Capabilities:
    - FR-BROKER-DUKASCOPY-MARKET-DATA: Historical Candlestick Bars and Ticks
      Associated: `[DukascopyClient.get_bars()]`, `[DukascopyClient.get_ticks()]`
      Logging: Emits INFO log upon successfully downloading and parsing bars with
      extracted count, and WARNING log on network failure or non-200 HTTP response.
    - FR-BROKER-DUKASCOPY-SYMBOLS: Authoritative Symbol Catalog Resolution
      Associated: `[DukascopyClient.get_symbol_info()]`, `[DukascopyClient.get_symbols()]`
      Logging: Emits INFO log upon successfully loading or querying catalog items,
      and WARNING log if symbol is not found in the CSV catalog.
    - FR-BROKER-CODECS-BI5: Decompress and decode Dukascopy LZMA tick/bar streams.
      Associated: `decompress_bi5()`, `decode_bi5_ticks()`, `decode_bi5_bars()`
      Logging: Emits DEBUG on parsing compressed payload and reporting decoded count.

Python API Usage:
    ```python
    from app.services.brokers.dukascopy import DukascopyClient
    from app.services.include.enums import Timeframe

    client = DukascopyClient()
    bars = client.get_bars("EURUSD", Timeframe.PERIOD_M1, count=5)
    assert len(bars) > 0
    client.disconnect()
    ```

CLI Usage:
    `uv run python -m scripts.examples.brokers_data --broker dukascopy`
"""

from __future__ import annotations

import lzma
import struct
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, override

from app.host.logging import get_logger
from app.services.brokers.base import (
    BridgeError,
    BrokerClient,
    create_http_session,
    epoch_millis,
    epoch_seconds,
    execute_bounded_get,
)
from app.services.brokers.files import (
    find_matching_partitions,
    parse_delimited_bars,
    read_parquet_bars,
)
from app.services.include.contracts import MarketBar, MarketTick, SymbolInfo
from app.services.include.enums import Timeframe

logger = get_logger(__name__)

BI5_FR = "FR-BROKER-CODECS-BI5"
MAX_DECOMPRESSED_BYTES = 50 * 1024 * 1024  # 50 MB safety budget

assert struct.calcsize(">IIIff") == 20, "Dukascopy BI5 tick record must be 20 bytes"
assert struct.calcsize(">IIIIIf") == 24, "Dukascopy BI5 M1 bar record must be 24 bytes"

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)

DEFAULT_DATA_DIR = Path(__file__).resolve().parents[3] / "data" / "market" / "dukascopy"
DEFAULT_CATALOG_PATH = DEFAULT_DATA_DIR / "dukascopy.csv"

__all__ = [
    "DukascopyClient",
    "decode_bi5_bars",
    "decode_bi5_ticks",
    "decompress_bi5",
]


def decompress_bi5(data: bytes, max_bytes: int = MAX_DECOMPRESSED_BYTES) -> bytes:
    """Decompress Dukascopy .bi5 binary payload with LZMA header recovery and size limits."""
    if not data or len(data) < 5:
        return b""
    try:
        decomp = lzma.decompress(data, format=lzma.FORMAT_ALONE)
        if len(decomp) > max_bytes:
            raise BridgeError(
                f"Decompressed BI5 payload exceeds limit ({len(decomp)} > {max_bytes})"
            )
        return decomp
    except BridgeError:
        raise
    except Exception:
        pass
    try:
        props = data[:5]
        payload = data[5:]
        alone_header = props + struct.pack("<Q", 2**64 - 1)
        decomp = lzma.decompress(alone_header + payload, format=lzma.FORMAT_ALONE)
        if len(decomp) > max_bytes:
            raise BridgeError(
                f"Decompressed BI5 payload exceeds limit ({len(decomp)} > {max_bytes})"
            )
        return decomp
    except BridgeError:
        raise
    except Exception:
        pass
    try:
        decomp = lzma.decompress(data, format=lzma.FORMAT_RAW)
        if len(decomp) > max_bytes:
            raise BridgeError(
                f"Decompressed BI5 payload exceeds limit ({len(decomp)} > {max_bytes})"
            )
        return decomp
    except BridgeError:
        raise
    except Exception:
        return b""


def decode_bi5_ticks(
    decomp: bytes,
    base_dt: datetime,
    digits: int = 5,
    count: int | None = None,
) -> list[dict[str, Any]]:
    """Decode uncompressed Dukascopy BI5 tick records."""
    if not decomp:
        return []
    rec_count = len(decomp) // 20
    target_count = (
        min(rec_count, count) if count is not None and count > 0 else rec_count
    )
    scale = 10.0**digits
    rows: list[dict[str, Any]] = []

    for i in range(target_count):
        offset_ms, ask_int, bid_int, ask_v, bid_v = struct.unpack_from(
            ">IIIff", decomp, i * 20
        )
        ask = ask_int / scale
        bid = bid_int / scale
        tick_dt = base_dt + timedelta(milliseconds=offset_ms)
        rows.append(
            {
                "time_msc": int(tick_dt.timestamp() * 1000),
                "bid": bid,
                "ask": ask,
                "last": (ask + bid) / 2.0,
                "volume": int(ask_v + bid_v),
                "flags": 0,
                "volume_real": float(ask_v + bid_v),
            }
        )
    logger.debug(
        "%s: Decoded %d BI5 ticks",
        BI5_FR,
        len(rows),
        extra={"fr_id": BI5_FR, "count": len(rows)},
    )
    return rows


def decode_bi5_bars(
    decomp: bytes,
    base_dt: datetime,
    digits: int = 5,
    count: int | None = None,
) -> list[dict[str, Any]]:
    """Decode uncompressed Dukascopy BI5 M1 candle records."""
    if not decomp:
        return []
    rec_count = len(decomp) // 24
    target_count = (
        min(rec_count, count) if count is not None and count > 0 else rec_count
    )
    scale = 10.0**digits
    rows: list[dict[str, Any]] = []

    for i in range(target_count):
        offset_sec, o, c, l, h, v = struct.unpack_from(">IIIIIf", decomp, i * 24)
        bar_dt = base_dt + timedelta(seconds=offset_sec)
        rows.append(
            {
                "time": int(bar_dt.timestamp()),
                "open": o / scale,
                "high": h / scale,
                "low": l / scale,
                "close": c / scale,
                "tick_volume": int(v),
                "spread": 0,
                "real_volume": int(v),
            }
        )
    logger.debug(
        "%s: Decoded %d BI5 M1 bars",
        BI5_FR,
        len(rows),
        extra={"fr_id": BI5_FR, "count": len(rows)},
    )
    return rows


# Compatibility alias
_decompress_bi5 = decompress_bi5


class DukascopyClient(BrokerClient):
    """Dukascopy market data and symbol catalog client."""

    CDN_BASE_URL = "https://cdn.strategyquantcdn.com/data/dukascopy"
    DATAFEED_BASE_URL = "https://datafeed.dukascopy.com/datafeed"

    def __init__(
        self,
        name: str = "Dukascopy",
        catalog_path: str | Path | None = None,
        data_dir: str | Path | None = None,
    ) -> None:
        """Initialize Dukascopy broker client."""
        super().__init__(name=name)
        self.catalog_path = Path(catalog_path) if catalog_path else DEFAULT_CATALOG_PATH
        self.data_dir: Path | None = (
            Path(data_dir)
            if data_dir is not None
            else (DEFAULT_DATA_DIR if DEFAULT_DATA_DIR.exists() else None)
        )
        self._catalog: dict[str, SymbolInfo] | None = None
        self.session = create_http_session(
            USER_AGENT, retries=3, backoff=0.3, pool_size=16
        )
        self._connected = True

    def _ensure_catalog(self) -> dict[str, SymbolInfo]:
        """Parse and cache symbol definitions from data/market/dukascopy/dukascopy.csv."""
        if self._catalog is not None:
            return self._catalog

        if not self.catalog_path.exists():
            raise BridgeError(
                f"Dukascopy catalog CSV file not found at {self.catalog_path}",
                code="CATALOG_NOT_FOUND",
            )

        catalog: dict[str, SymbolInfo] = {}
        try:
            with open(self.catalog_path, encoding="latin1") as f:
                for line in f:
                    line_str = line.strip()
                    if not line_str:
                        continue
                    parts = line_str.split(";")
                    if len(parts) < 11:
                        raise BridgeError(
                            f"Malformed Dukascopy catalog row: {line_str}",
                            code="INVALID_CATALOG",
                        )
                    sym = parts[0].strip().upper()
                    dec = int(parts[6].strip())
                    point_sz = float(parts[7].strip())
                    spread = float(parts[8].strip())
                    contract_sz = float(parts[10].strip())

                    catalog[sym] = SymbolInfo(
                        name=sym,
                        digits=dec,
                        point=point_sz,
                        spread=int(spread),
                        trade_contract_size=contract_sz,
                    )
            self._catalog = catalog
            self.logger.info(
                "FR-BROKER-DUKASCOPY-SYMBOLS: Loaded %d symbols from catalog CSV",
                len(catalog),
            )
            return catalog
        except Exception as exc:
            if isinstance(exc, BridgeError):
                raise
            raise BridgeError(
                f"Error parsing Dukascopy catalog CSV at {self.catalog_path}: {exc}",
                code="INVALID_CATALOG",
            ) from exc

    def _clean_symbol(self, symbol: str) -> str:
        """Strip delimiters and match symbol against catalog."""
        catalog = self._ensure_catalog()
        s = symbol.upper().strip()
        if s in catalog:
            return s
        s_nodelim = (
            s.replace("_", "").replace("/", "").replace("-", "").replace(".", "")
        )
        if s_nodelim in catalog:
            return s_nodelim
        for delim in ("_", "/", "-", "."):
            if delim in s:
                prefix = s.split(delim)[0]
                if prefix in catalog:
                    return prefix
        for length in (7, 6, 5, 4, 3):
            if len(s_nodelim) >= length and s_nodelim[:length] in catalog:
                return s_nodelim[:length]
        return s

    @override
    def get_symbol_info(self, symbol: str) -> SymbolInfo:
        """Retrieve instrument specifications strictly from the Dukascopy catalog."""
        sym_clean = self._clean_symbol(symbol)
        catalog = self._ensure_catalog()
        snap = catalog.get(sym_clean)
        if snap is None:
            raise BridgeError(
                f"Symbol '{symbol}' not found in Dukascopy catalog",
                code="SYMBOL_NOT_FOUND",
            )
        return snap

    @override
    def get_symbols(self) -> list[str]:
        """Get the list of symbol names available in the catalog."""
        catalog = self._ensure_catalog()
        return list(catalog.keys())

    def _fetch_datafeed_bars(
        self,
        sym_clean: str,
        dt: datetime,
        decimals: int,
        count: int = 100,
    ) -> list[dict[str, Any]]:
        """Fetch and decompress daily candles from Dukascopy direct datafeed."""
        feed_url = (
            f"{self.DATAFEED_BASE_URL}/{sym_clean}/{dt.year}/{dt.month - 1:02d}/"
            f"{dt.day:02d}/BID_candles_min_1.bi5"
        )
        resp = execute_bounded_get(
            self.session,
            feed_url,
            timeout=(5.0, 15.0),
            provider="dukascopy",
        )
        if resp.status_code != 200 or not resp.content:
            raise BridgeError(
                f"No bars available for '{sym_clean}' from Dukascopy datafeed (HTTP {resp.status_code})",
                code="NO_DATA",
            )
        decomp = decompress_bi5(resp.content)
        if not decomp:
            raise BridgeError(
                f"Empty or corrupt BI5 bar payload for '{sym_clean}' from Dukascopy",
                code="INVALID_MARKET_DATA",
            )
        base_dt = datetime(dt.year, dt.month, dt.day, tzinfo=UTC)
        return decode_bi5_bars(decomp, base_dt, digits=decimals, count=count)

    def _fetch_datafeed_ticks(
        self,
        sym_clean: str,
        dt: datetime,
        decimals: int,
        count: int = 100,
    ) -> list[dict[str, Any]]:
        """Fetch and decompress hourly ticks from Dukascopy direct datafeed."""
        feed_url = (
            f"{self.DATAFEED_BASE_URL}/{sym_clean}/{dt.year}/{dt.month - 1:02d}/"
            f"{dt.day:02d}/{dt.hour:02d}h_ticks.bi5"
        )
        resp = execute_bounded_get(
            self.session,
            feed_url,
            timeout=(5.0, 15.0),
            provider="dukascopy",
        )
        if resp.status_code != 200 or not resp.content:
            raise BridgeError(
                f"No ticks available for '{sym_clean}' from Dukascopy datafeed (HTTP {resp.status_code})",
                code="NO_DATA",
            )
        decomp = decompress_bi5(resp.content)
        if not decomp:
            raise BridgeError(
                f"Empty or corrupt BI5 tick payload for '{sym_clean}' from Dukascopy",
                code="INVALID_MARKET_DATA",
            )
        base_dt = datetime(dt.year, dt.month, dt.day, dt.hour, tzinfo=UTC)
        return decode_bi5_ticks(decomp, base_dt, digits=decimals, count=count)

    @override
    def get_bars(
        self,
        symbol: str,
        timeframe: Timeframe | str = Timeframe.PERIOD_M1,
        date_from: datetime | int | None = None,
        date_to: datetime | int | None = None,
        *,
        start: datetime | int | None = None,
        end: datetime | int | None = None,
        start_pos: int | None = None,
        count: int | None = None,
        limit: int = 1000,
    ) -> list[MarketBar]:
        """Download candlestick bars from local storage or Dukascopy datafeed."""
        del start_pos
        sym_clean = self._clean_symbol(symbol)
        snap = self.get_symbol_info(sym_clean)
        decimals = snap.digits
        target_count = count or limit or 100

        tf_name = timeframe.name if isinstance(timeframe, Timeframe) else timeframe
        tf_norm = tf_name.strip().upper()
        if tf_norm not in ("M1", "PERIOD_M1", "TICK"):
            raise BridgeError(
                f"Timeframe '{timeframe}' not supported by Dukascopy. Supported: M1, TICK",
                code="UNSUPPORTED_TIMEFRAME",
            )

        s = date_from if date_from is not None else start
        e = date_to if date_to is not None else end
        start_sec = epoch_seconds(s)
        end_sec = epoch_seconds(e)
        date_from = (
            datetime.fromtimestamp(start_sec, tz=UTC) if 0 < start_sec < 2**40 else None
        )
        date_to = (
            datetime.fromtimestamp(end_sec, tz=UTC) if 0 < end_sec < 2**40 else None
        )

        # Check local data_dir if available
        if self.data_dir is not None and self.data_dir.exists():
            matched = find_matching_partitions(self.data_dir, sym_clean, tf_norm)
            all_local_bars: list[dict[str, Any]] = []
            for p in matched:
                if p.suffix.lower() == ".parquet":
                    all_local_bars.extend(read_parquet_bars(p, count=target_count))
                elif p.suffix.lower() in (".csv", ".tsv", ".txt"):
                    all_local_bars.extend(
                        parse_delimited_bars(
                            p.read_text(encoding="utf-8", errors="replace"),
                            sym_clean,
                            tf_norm,
                        )
                    )
                elif p.suffix.lower() == ".bi5":
                    decomp = decompress_bi5(p.read_bytes())
                    base_dt = date_from or datetime(2023, 1, 1, tzinfo=UTC)
                    all_local_bars.extend(
                        decode_bi5_bars(
                            decomp, base_dt, digits=decimals, count=target_count
                        )
                    )
            if all_local_bars:
                all_local_bars.sort(key=lambda r: r["time"])
                filtered = [
                    r
                    for r in all_local_bars
                    if (not date_from or r["time"] >= int(date_from.timestamp()))
                    and (not date_to or r["time"] <= int(date_to.timestamp()))
                ]
                if filtered:
                    selected = filtered[-target_count:] if target_count else filtered
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
                        for r in selected
                    ]

        feed_dt = date_to or (
            date_from + timedelta(days=1)
            if date_from
            else datetime(2023, 1, 2, tzinfo=UTC)
        )
        feed_bars = self._fetch_datafeed_bars(
            sym_clean=sym_clean,
            dt=feed_dt,
            decimals=decimals,
            count=target_count,
        )
        feed_bars.sort(key=lambda r: r["time"])
        filtered = [
            r
            for r in feed_bars
            if (not date_from or r["time"] >= int(date_from.timestamp()))
            and (not date_to or r["time"] <= int(date_to.timestamp()))
        ]
        if not filtered:
            raise BridgeError(
                f"No bars available for '{sym_clean}' from Dukascopy",
                code="NO_DATA",
            )
        selected = filtered[-target_count:] if target_count else filtered
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
            for r in selected
        ]

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
        """Download tick data from local archives or Dukascopy direct datafeed."""
        sym_clean = self._clean_symbol(symbol)
        snap = self.get_symbol_info(sym_clean)
        decimals = snap.digits
        target_count = count or limit or 100
        s = date_from if date_from is not None else start
        e = date_to if date_to is not None else end
        start_ms = epoch_millis(s)
        end_ms = epoch_millis(e)

        # Check local data_dir if available
        if self.data_dir is not None and self.data_dir.exists():
            matched = find_matching_partitions(self.data_dir, sym_clean, "TICK")
            all_local_ticks: list[dict[str, Any]] = []
            for p in matched:
                if p.suffix.lower() == ".bi5":
                    decomp = decompress_bi5(p.read_bytes())
                    base_dt = (
                        datetime.fromtimestamp(start_ms / 1000.0, tz=UTC)
                        if start_ms > 0
                        else datetime(2023, 1, 1, tzinfo=UTC)
                    )
                    all_local_ticks.extend(
                        decode_bi5_ticks(
                            decomp, base_dt, digits=decimals, count=target_count
                        )
                    )
            if all_local_ticks:
                all_local_ticks.sort(key=lambda r: r["time_msc"])
                filtered = [
                    r
                    for r in all_local_ticks
                    if (start_ms <= 0 or r["time_msc"] >= start_ms)
                    and (end_ms <= 0 or r["time_msc"] <= end_ms)
                ]
                if filtered:
                    selected = filtered[-target_count:] if target_count else filtered
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
                        for t in selected
                    ]

        target_dt = (
            datetime.fromtimestamp(start_ms / 1000.0, tz=UTC)
            if 0 < start_ms < 2**50
            else datetime(2023, 1, 2, 10, tzinfo=UTC)
        )
        ticks = self._fetch_datafeed_ticks(
            sym_clean=sym_clean,
            dt=target_dt,
            decimals=decimals,
            count=target_count,
        )
        ticks.sort(key=lambda r: r["time_msc"])
        if end_ms > 0:
            ticks = [t for t in ticks if t["time_msc"] <= end_ms]
        if not ticks:
            raise BridgeError(
                f"No ticks available for '{sym_clean}' from Dukascopy",
                code="NO_DATA",
            )
        if target_count and len(ticks) > target_count:
            ticks = ticks[-target_count:]
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
            for t in ticks
        ]


def main() -> None:
    """Demonstrate executable usage of DukascopyClient."""
    client = DukascopyClient()
    symbols = client.get_symbols()
    logger.info("Dukascopy catalog symbols: %d available", len(symbols))
    client.disconnect()


if __name__ == "__main__":
    main()
