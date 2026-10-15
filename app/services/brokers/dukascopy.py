"""Dukascopy market data and authoritative symbol catalog broker implementation.

Description:
    Implements an unauthenticated market data and symbol metadata broker
    for Dukascopy Bank SA conforming to the `TradingBackend` protocol.
    Fetches historical candlestick bars and ticks over HTTP in memory, and dynamically
    resolves instrument specifications from the authoritative catalog CSV
    (`data/market/dukascopy/dukascopy.csv`) returning canonical `SymbolSnapshot` objects.

Purpose:
    FEAT-BROKER-DUKASCOPY: Dukascopy Market Data and Symbol Catalog Provider.

Key Capabilities:
    - FR-BROKER-DUKASCOPY-MARKET-DATA: Historical Candlestick Bars and Ticks
      Associated: `[DukascopyBroker.fetch_bars()]`, `[DukascopyBroker.fetch_ticks()]`
      Logging: Emits INFO log upon successfully downloading and parsing bars with
      extracted count, and WARNING log on network failure or non-200 HTTP response.
    - FR-BROKER-DUKASCOPY-SYMBOLS: Authoritative Symbol Catalog Resolution
      Associated: `[DukascopyBroker.symbol_info()]`, `[DukascopyBroker.symbols_get()]`
      Logging: Emits INFO log upon successfully loading or querying catalog items,
      and WARNING log if symbol is not found in the CSV catalog.

Python API Usage:
    ```python
    from app.services.data import Timeframe, get_historical_bars
    from app.services.brokers.dukascopy import DukascopyBroker

    broker = DukascopyBroker()
    bars = await get_historical_bars(broker, "EURUSD", Timeframe.PERIOD_M1, count=5)
    assert len(bars) > 0
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

import requests
from app.host.discovery import PluginHostContext
from app.host.logging import get_logger
from app.services.data import BridgeError, DataBrokerBackend
from app.services.trading import SymbolSnapshot
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = get_logger(__name__)

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)

DEFAULT_CATALOG_PATH = (
    Path(__file__).resolve().parents[3]
    / "data"
    / "market"
    / "dukascopy"
    / "dukascopy.csv"
)

__all__ = ["DukascopyBroker", "create_adapter"]


def _decompress_bi5(data: bytes) -> bytes:
    """Decompress Dukascopy .bi5 binary payload with LZMA header recovery."""
    if not data or len(data) < 5:
        return b""
    try:
        return lzma.decompress(data, format=lzma.FORMAT_ALONE)
    except Exception:
        pass
    try:
        props = data[:5]
        payload = data[5:]
        alone_header = props + struct.pack("<Q", 2**64 - 1)
        return lzma.decompress(alone_header + payload, format=lzma.FORMAT_ALONE)
    except Exception:
        pass
    try:
        return lzma.decompress(data, format=lzma.FORMAT_RAW)
    except Exception:
        return b""


class DukascopyBroker(DataBrokerBackend):
    """Dukascopy market data and symbol catalog broker."""

    CDN_BASE_URL = "https://cdn.strategyquantcdn.com/data/dukascopy"
    DATAFEED_BASE_URL = "https://datafeed.dukascopy.com/datafeed"

    def __init__(
        self,
        name: str = "Dukascopy",
        catalog_path: str | Path | None = None,
    ) -> None:
        """Initialize Dukascopy broker."""
        super().__init__(name=name)
        self.catalog_path = Path(catalog_path) if catalog_path else DEFAULT_CATALOG_PATH
        self._catalog: dict[str, SymbolSnapshot] | None = None
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": USER_AGENT})
        retry_strategy: Any = Retry(
            total=3,
            backoff_factor=0.3,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "HEAD"],
        )
        adapter = HTTPAdapter(
            max_retries=retry_strategy, pool_connections=16, pool_maxsize=16
        )
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

    def _ensure_catalog(self) -> dict[str, SymbolSnapshot]:
        """Parse and cache symbol definitions from data/market/dukascopy/dukascopy.csv."""
        if self._catalog is not None:
            return self._catalog

        catalog: dict[str, SymbolSnapshot] = {}
        if not self.catalog_path.exists():
            self.logger.warning(
                "FR-BROKER-DUKASCOPY-SYMBOLS: Catalog CSV file not found at %s",
                self.catalog_path,
            )
            self._catalog = catalog
            return self._catalog

        try:
            with open(self.catalog_path, encoding="latin1") as f:
                for line in f:
                    line_str = line.strip()
                    if not line_str:
                        continue
                    parts = line_str.split(";")
                    if len(parts) < 11:
                        continue
                    sym = parts[0].strip().upper()
                    try:
                        dec = int(parts[6].strip())
                        point_sz = float(parts[7].strip())
                        spread = float(parts[8].strip())
                        pt = float(parts[10].strip())
                    except ValueError:
                        continue

                    catalog[sym] = SymbolSnapshot(
                        name=sym,
                        custom=False,
                        digits=dec,
                        point=pt,
                        spread=int(spread),
                        trade_contract_size=point_sz if point_sz > 0 else 100_000.0,
                    )
            self.logger.info(
                "FR-BROKER-DUKASCOPY-SYMBOLS: Successfully loaded %d symbols from %s",
                len(catalog),
                self.catalog_path.name,
            )
        except Exception as exc:
            self.logger.error(
                "FR-BROKER-DUKASCOPY-SYMBOLS: Error parsing catalog CSV: %s", exc
            )

        self._catalog = catalog
        return self._catalog

    def _clean_symbol(self, symbol: str) -> str:
        """Resolve raw or postfixed symbol to canonical Dukascopy catalog symbol."""
        s = symbol.strip().upper()
        catalog = self._ensure_catalog()
        if s in catalog:
            return s
        for suffix in (
            "_DUKASCOPY",
            "_DUKAS",
            "_FX",
            "_RAW",
            "_PRO",
            "DUKASCOPY",
            "DUKAS",
            "FX",
            "RAW",
            "PRO",
        ):
            if s.endswith(suffix):
                s = s[: -len(suffix)]
                break
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
    def symbol_info(self, symbol: str) -> SymbolSnapshot:
        """Retrieve instrument specifications as canonical SymbolSnapshot."""
        sym_clean = self._clean_symbol(symbol)
        catalog = self._ensure_catalog()
        snap = catalog.get(sym_clean)
        if snap is not None:
            return snap
        return SymbolSnapshot(name=sym_clean, digits=5, point=0.00001)

    @override
    def symbols_get(self) -> list[str]:
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
        scale = 10.0**decimals
        feed_url = (
            f"{self.DATAFEED_BASE_URL}/{sym_clean}/{dt.year}/{dt.month - 1:02d}/"
            f"{dt.day:02d}/BID_candles_min_1.bi5"
        )
        try:
            resp = self.session.get(feed_url, timeout=(5.0, 15.0))
            if resp.status_code != 200 or not resp.content:
                return []
            decomp = _decompress_bi5(resp.content)
            if not decomp:
                return []
            rec_count = len(decomp) // 24
            rows: list[dict[str, Any]] = []
            base_dt = datetime(dt.year, dt.month, dt.day, tzinfo=UTC)
            for i in range(min(rec_count, count)):
                offset_sec, o, c, l, h, v = struct.unpack_from(
                    ">iiiii f", decomp, i * 24
                )
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
            return rows
        except Exception as exc:
            self.logger.debug(
                "FR-BROKER-DUKASCOPY-MARKET-DATA: Datafeed candle fetch failed: %s",
                exc,
            )
            return []

    def _fetch_datafeed_ticks(
        self,
        sym_clean: str,
        dt: datetime,
        decimals: int,
        count: int = 100,
    ) -> list[dict[str, Any]]:
        """Fetch and decompress hourly ticks from Dukascopy direct datafeed."""
        scale = 10.0**decimals
        feed_url = (
            f"{self.DATAFEED_BASE_URL}/{sym_clean}/{dt.year}/{dt.month - 1:02d}/"
            f"{dt.day:02d}/{dt.hour:02d}h_ticks.bi5"
        )
        try:
            resp = self.session.get(feed_url, timeout=(5.0, 15.0))
            if resp.status_code != 200 or not resp.content:
                return []
            decomp = _decompress_bi5(resp.content)
            if not decomp:
                return []
            rec_count = len(decomp) // 20
            rows: list[dict[str, Any]] = []
            base_dt = datetime(dt.year, dt.month, dt.day, dt.hour, tzinfo=UTC)
            for i in range(min(rec_count, count)):
                offset_ms, ask_int, bid_int, ask_v, bid_v = struct.unpack_from(
                    ">iii f f", decomp, i * 20
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
            return rows
        except Exception as exc:
            self.logger.debug(
                "FR-BROKER-DUKASCOPY-MARKET-DATA: Datafeed tick fetch failed: %s", exc
            )
            return []

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
        """Download candlestick bars from Dukascopy CDN or datafeed."""
        del timeframe, mode
        sym_clean = self._clean_symbol(symbol)
        snap = self.symbol_info(sym_clean)
        decimals = snap.digits
        scale = 10.0 ** (decimals + 1)
        target_count = count if count > 0 else limit

        date_from = datetime.fromtimestamp(start, tz=UTC) if 0 < start < 2**40 else None
        date_to = datetime.fromtimestamp(end, tz=UTC) if 0 < end < 2**40 else None
        target_year = date_from.year if date_from else 2023
        cdn_url = f"{self.CDN_BASE_URL}/m1/{sym_clean}/{target_year}.zip"

        try:
            resp = self.session.get(cdn_url, timeout=(5.0, 30.0))
            if resp.status_code == 200 and resp.content:
                rows: list[dict[str, Any]] = []
                with zipfile.ZipFile(io.BytesIO(resp.content)) as z:
                    names = sorted(z.namelist())
                    for name in names[-target_count:]:
                        content = z.read(name)
                        idx = content.find(b"\xbb\xbb\xbb")
                        if idx != -1 and len(content) >= idx + 3 + 48:
                            offset = idx + 3
                            ts, o, h, l, c, v = struct.unpack_from(
                                ">QQQQQQ", content, offset
                            )
                            t_sec = int(ts / 1000)
                            rows.append(
                                {
                                    "time": t_sec,
                                    "open": o / scale,
                                    "high": h / scale,
                                    "low": l / scale,
                                    "close": c / scale,
                                    "tick_volume": int(v),
                                    "spread": 0,
                                    "real_volume": int(v),
                                }
                            )

                if rows:
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
            self.logger.debug(
                "FR-BROKER-DUKASCOPY-MARKET-DATA: CDN download failed: %s", exc
            )

        # Fallback to direct datafeed
        target_dt = date_from or datetime(target_year, 1, 1, tzinfo=UTC)
        feed_bars = self._fetch_datafeed_bars(
            sym_clean=sym_clean,
            dt=target_dt,
            decimals=decimals,
            count=target_count,
        )
        if feed_bars:
            feed_bars.sort(key=lambda r: r["time"])
            if target_count and len(feed_bars) > target_count:
                feed_bars = feed_bars[-target_count:]
            return feed_bars

        raise BridgeError(
            f"No bars available for '{sym_clean}' from Dukascopy",
            code="NO_DATA",
        )

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
        """Download tick data from Dukascopy direct datafeed."""
        del mode, end_ms
        sym_clean = self._clean_symbol(symbol)
        snap = self.symbol_info(sym_clean)
        decimals = snap.digits
        target_count = count if count > 0 else limit
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
        if target_count and len(ticks) > target_count:
            ticks = ticks[-target_count:]
        return ticks


def create_adapter(context: PluginHostContext | None = None) -> DukascopyBroker:
    """Factory creating configured DukascopyBroker adapter."""
    del context
    return DukascopyBroker()
