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
    from app.workspace.brokers.dukascopy import DukascopyClient
    from app.core.enums import Timeframe

    client = DukascopyClient()
    bars = client.get_bars("EURUSD", Timeframe.PERIOD_M1, count=5)
    assert len(bars) > 0
    client.disconnect()
    ```

CLI Usage:
    `uv run python -m scripts.examples.brokers_data --broker dukascopy`
"""

from __future__ import annotations

import io
import lzma
import struct
import zipfile
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, override

import pandas as pd  # type: ignore[import-untyped]

from app.core.data.contracts import (
    MarketBar,
    MarketTick,
    SymbolInfo,
    SymbolPrice,
    SymbolSpread,
)
from app.core.enums import Timeframe
from app.core.host.logging import get_logger
from app.core.host.persistence import HostPersistence
from app.workspace.data_manager.data.conversions import (
    bars_to_dataframe,
    ticks_to_dataframe,
)

from .base import (
    BridgeError,
    BrokerClient,
    create_http_session,
    epoch_millis,
    epoch_seconds,
    execute_bounded_get,
)
from .canonical_history import cached_frame, fetch_interval
from .codecs import decode_sq_dat_bytes
from .files import (
    find_matching_partitions,
    parse_delimited_bars,
    read_parquet_bars,
)

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
        use_cache: bool = True,
        download_mode: str = "cdn",
        gateway: HostPersistence | None = None,
        context: Any = None,
    ) -> None:
        """Initialize Dukascopy broker client."""
        super().__init__(name=name)
        if download_mode not in ("standard", "cdn"):
            raise ValueError("download_mode must be standard or cdn")
        self.catalog_path = Path(catalog_path) if catalog_path else DEFAULT_CATALOG_PATH
        self.data_dir: Path | None = (
            Path(data_dir)
            if data_dir is not None
            else (DEFAULT_DATA_DIR if DEFAULT_DATA_DIR.exists() else None)
        )
        self.use_cache, self.download_mode = use_cache, download_mode
        self.gateway = gateway if gateway is not None else HostPersistence()
        self.context = context
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
                        price=SymbolPrice(
                            digits=dec, tick_size=point_sz, contract_size=contract_sz
                        ),
                        spread=SymbolSpread(default=int(spread)),
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
        count: int | None = 100,
    ) -> list[dict[str, Any]]:
        """Fetch and decompress daily candles from Dukascopy direct datafeed."""
        feed_url = (
            f"{self.DATAFEED_BASE_URL}/{sym_clean}/{dt.year}/{dt.month - 1:02d}/"
            f"{dt.day:02d}/BID_candles_min_1.bi5"
        )
        resp = execute_bounded_get(
            self.session,
            feed_url,
            timeout=(3.0, 5.0),
            provider="dukascopy",
        )
        if resp.status_code != 200 or not resp.content:
            raise BridgeError(
                f"No bars available for '{sym_clean}' from Dukascopy datafeed (HTTP {resp.status_code})",
                code="NO_DATA" if resp.status_code == 404 else "NETWORK_ERROR",
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
        count: int | None = 100,
    ) -> list[dict[str, Any]]:
        """Fetch and decompress hourly ticks from Dukascopy direct datafeed."""
        feed_url = (
            f"{self.DATAFEED_BASE_URL}/{sym_clean}/{dt.year}/{dt.month - 1:02d}/"
            f"{dt.day:02d}/{dt.hour:02d}h_ticks.bi5"
        )
        resp = execute_bounded_get(
            self.session,
            feed_url,
            timeout=(3.0, 5.0),
            provider="dukascopy",
        )
        if resp.status_code != 200 or not resp.content:
            raise BridgeError(
                f"No ticks available for '{sym_clean}' from Dukascopy datafeed (HTTP {resp.status_code})",
                code="NO_DATA" if resp.status_code == 404 else "NETWORK_ERROR",
            )
        decomp = decompress_bi5(resp.content)
        if not decomp:
            raise BridgeError(
                f"Empty or corrupt BI5 tick payload for '{sym_clean}' from Dukascopy",
                code="INVALID_MARKET_DATA",
            )
        base_dt = datetime(dt.year, dt.month, dt.day, dt.hour, tzinfo=UTC)
        return decode_bi5_ticks(decomp, base_dt, digits=decimals, count=count)

    @staticmethod
    def _rows_to_market_bars(rows: list[dict[str, Any]]) -> pd.DataFrame:
        """Convert list of bar dictionaries to a canonical MarketBar DataFrame."""
        bars = [
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
            for r in rows
        ]
        return bars_to_dataframe(bars)

    def _fetch_cdn_bars(
        self,
        sym_clean: str,
        count: int | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
    ) -> list[dict[str, Any]]:
        """Fetch and decompress M1 candlestick bars from StrategyQuant Dukascopy CDN."""
        meta_url = f"{self.CDN_BASE_URL}/m1/{sym_clean}/metadata.dat"
        try:
            resp = execute_bounded_get(
                self.session,
                meta_url,
                timeout=(3.0, 5.0),
                provider="dukascopy",
            )
            if resp.status_code != 200 or not resp.content:
                return []
        except Exception:
            return []

        available_zips = [
            z.strip()
            for z in resp.content.decode("latin1", errors="ignore").split(";")
            if z.strip().endswith(".zip")
        ]
        if not available_zips:
            return []

        selected_zips: list[str] = []
        if date_from or date_to:
            start_yr = date_from.year if date_from else 2003
            end_yr = date_to.year if date_to else datetime.now(UTC).year
            for zname in available_zips:
                stem = zname[:-4]
                parts = stem.split("_")
                try:
                    yr = int(parts[0])
                    if start_yr <= yr <= end_yr:
                        if len(parts) > 1:
                            mo = int(parts[1])
                            if yr == start_yr and date_from and mo < date_from.month:
                                continue
                            if yr == end_yr and date_to and mo > date_to.month:
                                continue
                        selected_zips.append(zname)
                except ValueError:
                    continue
        else:
            selected_zips = available_zips[-1:]

        all_bars: list[dict[str, Any]] = []
        for zname in selected_zips:
            if self.context is not None:
                self.context.wait_if_paused()
            zip_url = f"{self.CDN_BASE_URL}/m1/{sym_clean}/{zname}"
            try:
                zresp = execute_bounded_get(
                    self.session,
                    zip_url,
                    timeout=(5.0, 15.0),
                    provider="dukascopy",
                )
                if zresp.status_code != 200 or not zresp.content:
                    raise BridgeError("CDN archive unavailable", code="NETWORK_ERROR")
                with zipfile.ZipFile(io.BytesIO(zresp.content)) as zf:
                    for fname in sorted(zf.namelist()):
                        if fname.endswith(".dat"):
                            file_bars = decode_sq_dat_bytes(
                                zf.read(fname),
                                date_from=date_from,
                                date_to=date_to,
                            )
                            all_bars.extend(file_bars)
            except Exception as exc:
                raise BridgeError(
                    f"CDN archive failed: {zname}", code="NETWORK_ERROR"
                ) from exc

        all_bars.sort(key=lambda b: b["time"])
        if count and count > 0 and len(all_bars) > count:
            all_bars = all_bars[-count:]
        return all_bars

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
    ) -> pd.DataFrame:
        """Download candlestick bars from local storage or Dukascopy datafeed."""
        del start_pos
        sym_clean = self._clean_symbol(symbol)
        snap = self.get_symbol_info(sym_clean)
        decimals = snap.price.digits
        s = date_from if date_from is not None else start
        e = date_to if date_to is not None else end
        target_count = (
            count if (s is not None or e is not None) else (count or limit or 100)
        )

        tf_name = timeframe.name if isinstance(timeframe, Timeframe) else str(timeframe)
        tf_norm = tf_name.strip().upper()
        if tf_norm in ("M1", "PERIOD_M1"):
            tf_norm = "M1"
        elif tf_norm != "TICK":
            raise BridgeError(
                f"Timeframe '{timeframe}' not supported by Dukascopy. Supported: M1, TICK",
                code="UNSUPPORTED_TIMEFRAME",
            )

        start_sec = epoch_seconds(s)
        end_sec = epoch_seconds(e)
        date_from = (
            datetime.fromtimestamp(start_sec, tz=UTC) if 0 < start_sec < 2**40 else None
        )
        date_to = (
            datetime.fromtimestamp(end_sec, tz=UTC) if 0 < end_sec < 2**40 else None
        )

        if self.use_cache:
            cached = cached_frame(
                self.gateway,
                self.data_dir,
                "dukascopy",
                sym_clean,
                "M1",
                date_from,
                date_to,
                target_count,
            )
            if cached is not None:
                return cached

        # Check local canonical data directory
        search_dirs = (
            [self.data_dir]
            if self.use_cache and self.data_dir and self.data_dir.exists()
            else []
        )
        all_local_bars: list[dict[str, Any]] = []
        for sdir in search_dirs:
            matched = find_matching_partitions(sdir, sym_clean, tf_norm)
            for p in matched:
                if p.suffix.lower() == ".dat" and not p.stem.upper().endswith(
                    f"_{tf_norm}"
                ):
                    continue
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
                elif p.suffix.lower() == ".dat":
                    all_local_bars.extend(
                        decode_sq_dat_bytes(
                            p.read_bytes(),
                            count=target_count,
                            date_from=date_from,
                            date_to=date_to,
                        )
                    )
            if all_local_bars:
                break

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
                return self._rows_to_market_bars(selected)

        # 2. Try StrategyQuant pre-packaged Dukascopy CDN archives
        cdn_bars = (
            self._fetch_cdn_bars(
                sym_clean=sym_clean,
                count=target_count,
                date_from=date_from,
                date_to=date_to,
            )
            if self.download_mode != "standard"
            else []
        )
        if cdn_bars:
            return self._rows_to_market_bars(cdn_bars)

        rows = fetch_interval(
            self, sym_clean, "M1", date_from, date_to, target_count, decimals
        )
        if not rows:
            raise BridgeError("No bars in the requested range", code="NO_DATA")
        return self._rows_to_market_bars(rows)

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
    ) -> pd.DataFrame:
        """Download tick data from local archives or Dukascopy direct datafeed."""
        sym_clean = self._clean_symbol(symbol)
        snap = self.get_symbol_info(sym_clean)
        decimals = snap.price.digits
        s = date_from if date_from is not None else start
        e = date_to if date_to is not None else end
        target_count = count if s is not None or e is not None else count or limit
        begin = (
            datetime.fromtimestamp(epoch_millis(s) / 1000, tz=UTC)
            if s is not None
            else None
        )
        stop = (
            datetime.fromtimestamp(epoch_millis(e) / 1000, tz=UTC)
            if e is not None
            else None
        )
        if self.use_cache:
            cached = cached_frame(
                self.gateway,
                self.data_dir,
                "dukascopy",
                sym_clean,
                "TICK",
                begin,
                stop,
                target_count,
            )
            if cached is not None:
                return cached
        ticks = fetch_interval(
            self, sym_clean, "TICK", begin, stop, target_count, decimals
        )
        if not ticks:
            raise BridgeError("No ticks in the requested range", code="NO_DATA")
        parsed_ticks = [
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
        return ticks_to_dataframe(parsed_ticks)


def main() -> None:
    """Demonstrate executable usage of DukascopyClient."""
    client = DukascopyClient()
    symbols = client.get_symbols()
    logger.info("Dukascopy catalog symbols: %d available", len(symbols))
    client.disconnect()


if __name__ == "__main__":
    main()
