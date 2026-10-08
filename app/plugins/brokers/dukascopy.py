"""Dukascopy market data and authoritative symbol catalog broker plugin.

Description:
    Implements an unauthenticated market data and symbol metadata broker plugin
    for Dukascopy Bank SA. Operating under strict single-responsibility
    principles, this plugin exclusively fetches historical candlestick bars and
    ticks over HTTP in memory, and dynamically resolves instrument specifications
    from the authoritative catalog at `data/market/dukascopy/dukascopy.csv`.
    Data retrieval operates via a resilient dual-endpoint model: queries default
    to high-speed pre-packaged StrategyQuant CDN archives, automatically falling
    back to direct Dukascopy datafeed endpoints (`datafeed.dukascopy.com`) with
    LZMA `.bi5` decompression if CDN bundles are missing or unavailable.
    In alignment with the HaruQuantAI broker architecture (mirroring Yahoo Finance),
    this plugin performs zero data manipulation: no Parquet writing, no local
    filesystem caching, no database management, and no Data Manager DTO coupling.
    All non-data and trading methods cleanly reject unsupported execution
    capabilities via BaseBroker defaults.

Purpose:
    FEAT-BROKER-DUKASCOPY: Dukascopy Market Data and Symbol Catalog Provider.
    Provides unauthenticated candlestick and tick extraction from StrategyQuant
    CDN feeds with automatic direct datafeed fallback, and dynamic symbol metadata
    resolution from the 725-instrument catalog.

Key Capabilities:
    - FR-BROKER-DUKASCOPY-MARKET-DATA: Historical Candlestick Bars and Ticks
      Associated: `[DukascopyBroker.get_bars()]`, `[DukascopyBroker.get_ticks()]`
      Logging: Emits INFO log upon successfully downloading and parsing bars with
      extracted count, and WARNING log on network failure or non-200 HTTP response.
    - FR-BROKER-DUKASCOPY-SYMBOLS: Authoritative Symbol Catalog Resolution
      Associated: `[DukascopyBroker.get_symbol_info()]`,
      `[DukascopyBroker.get_symbols()]`, `[DukascopyBroker.get_num_of_symbols()]`
      Logging: Emits INFO log upon successfully loading or querying catalog items,
      and WARNING log if symbol is not found in the CSV catalog.

Python API Usage:
    ```python
    from app.plugins.brokers.dukascopy import DukascopyBroker, create_adapter

    broker = create_adapter()
    info_resp = broker.get_symbol_info("EURUSD")
    assert info_resp.is_success
    assert info_resp.data.digits == 5

    bars_resp = broker.get_bars("EURUSD", count=5)
    assert bars_resp.is_success
    assert len(bars_resp.data) == 5
    ```

CLI Usage:
    ```bash
    uv run python scripts/brokers_all.py
    ```
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
    "id": "broker-dukascopy",
    "name": "Dukascopy Connector",
    "version": "1.0.0",
    "description": (
        "Dukascopy Bank SA historical market data and symbol catalog broker plugin"
    ),
    "author": "HaruQuantAI",
    "slot": "broker",
    "entrypoint": "create_adapter",
    "dependencies": [],
    "capabilities": ["bars", "ticks", "symbols"],
    "enabled": True,
    "metadata": {
        "provider_name": "Dukascopy",
        "display_name": "Dukascopy Bank SA",
        "asset_classes": ["Forex", "Commodities", "Indices", "Crypto", "Stocks"],
        "timeframes": ["M1", "H1", "D1"],
        "requires_auth": False,
        "rate_limit_rps": 10.0,
        "base_url": "https://cdn.strategyquantcdn.com/data/dukascopy",
    },
}

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


class DukascopyBroker(BaseBroker):
    """Dukascopy market data and symbol catalog broker plugin."""

    CDN_BASE_URL = "https://cdn.strategyquantcdn.com/data/dukascopy"
    DATAFEED_BASE_URL = "https://datafeed.dukascopy.com/datafeed"

    def __init__(
        self,
        name: str = "Dukascopy",
        catalog_path: str | Path | None = None,
    ) -> None:
        """Initialize Dukascopy broker plugin.

        Args:
            name: Plugin identifier name.
            catalog_path: Optional path to dukascopy.csv catalog file.
        """
        super().__init__(
            name=name,
            capabilities=BrokerCapability.MARKET_DATA | BrokerCapability.SYMBOLS,
        )
        self.catalog_path = Path(catalog_path) if catalog_path else DEFAULT_CATALOG_PATH
        self._catalog: dict[str, SymbolInfo] | None = None
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

    def _ensure_catalog(self) -> dict[str, SymbolInfo]:
        """Parse and cache symbol definitions from data/market/dukascopy/dukascopy.csv."""
        if self._catalog is not None:
            return self._catalog

        catalog: dict[str, SymbolInfo] = {}
        if not self.catalog_path.exists():
            self.logger.warning(
                "FR-BROKER-DUKASCOPY-SYMBOLS: Catalog CSV file not found at %s",
                self.catalog_path,
                extra={
                    "fr_id": "FR-BROKER-DUKASCOPY-SYMBOLS",
                    "path": str(self.catalog_path),
                },
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
                    desc = parts[1].strip()
                    cat = parts[2].strip()
                    subcat = parts[3].strip()
                    date_from = parts[4].strip()
                    date_from_m1 = parts[5].strip()
                    try:
                        dec = int(parts[6].strip())
                        point_sz = float(parts[7].strip())
                        spread = float(parts[8].strip())
                        pip_sz = float(parts[9].strip())
                        pt = float(parts[10].strip())
                    except ValueError:
                        continue

                    if cat == "Forex" and len(sym) == 6:
                        base_curr = sym[:3]
                        profit_curr = sym[3:]
                    elif sym.endswith("USD"):
                        base_curr = sym[:-3] or "USD"
                        profit_curr = "USD"
                    elif sym.endswith("EUR"):
                        base_curr = sym[:-3] or "EUR"
                        profit_curr = "EUR"
                    else:
                        base_curr = sym
                        profit_curr = "USD"

                    catalog[sym] = SymbolInfo(
                        name=sym,
                        custom=False,
                        digits=dec,
                        point=pt,
                        spread=int(spread),
                        currency_base=base_curr,
                        currency_profit=profit_curr,
                        description=f"{desc} ({cat}/{subcat})",
                        category=cat,
                        path=f"{cat}/{subcat}",
                        raw={
                            "symbol": sym,
                            "name": desc,
                            "category": cat,
                            "subcategory": subcat,
                            "date_from": date_from,
                            "date_from_m1": date_from_m1,
                            "decimals": dec,
                            "contract_size": point_sz,
                            "spread": spread,
                            "pip_size": pip_sz,
                            "point": pt,
                            "instrument_type": (
                                parts[11].strip() if len(parts) > 11 else ""
                            ),
                        },
                    )
            self.logger.info(
                "FR-BROKER-DUKASCOPY-SYMBOLS: Successfully loaded %d symbols from %s",
                len(catalog),
                self.catalog_path.name,
                extra={
                    "fr_id": "FR-BROKER-DUKASCOPY-SYMBOLS",
                    "count": len(catalog),
                    "path": str(self.catalog_path),
                },
            )
        except Exception as exc:
            self.logger.error(
                "FR-BROKER-DUKASCOPY-SYMBOLS: Error parsing catalog CSV: %s",
                exc,
                extra={"fr_id": "FR-BROKER-DUKASCOPY-SYMBOLS", "error": str(exc)},
            )

        self._catalog = catalog
        return self._catalog

    def _fetch_datafeed_bars(
        self,
        sym_clean: str,
        dt: datetime,
        decimals: int,
        count: int = 100,
    ) -> list[Bar]:
        """Fetch and decompress daily M1 candles from Dukascopy direct datafeed.

        Args:
            sym_clean: Sanitized symbol name.
            dt: Target date.
            decimals: Precision digits for price scaling.
            count: Maximum number of bars to return.

        Returns:
            List of parsed Bar entities, or empty list on failure.
        """
        scale = 10.0**decimals
        # Dukascopy datafeed month is 0-indexed (00 = January, 11 = December)
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
            bars: list[Bar] = []
            base_dt = datetime(dt.year, dt.month, dt.day, tzinfo=UTC)
            for i in range(min(rec_count, count)):
                offset_sec, o, c, l, h, v = struct.unpack_from(
                    ">iiiii f", decomp, i * 24
                )
                bars.append(
                    Bar(
                        time=base_dt + timedelta(seconds=offset_sec),
                        open=o / scale,
                        high=h / scale,
                        low=l / scale,
                        close=c / scale,
                        tick_volume=int(v),
                        real_volume=int(v),
                    )
                )
            return bars
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
    ) -> list[Tick]:
        """Fetch and decompress hourly ticks from Dukascopy direct datafeed.

        Args:
            sym_clean: Sanitized symbol name.
            dt: Target date and hour.
            decimals: Precision digits for price scaling.
            count: Maximum number of ticks to return.

        Returns:
            List of parsed Tick entities, or empty list on failure.
        """
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
            ticks: list[Tick] = []
            base_dt = datetime(dt.year, dt.month, dt.day, dt.hour, tzinfo=UTC)
            for i in range(min(rec_count, count)):
                offset_ms, ask_int, bid_int, ask_v, bid_v = struct.unpack_from(
                    ">iii f f", decomp, i * 20
                )
                ask = ask_int / scale
                bid = bid_int / scale
                ticks.append(
                    Tick(
                        time=base_dt + timedelta(milliseconds=offset_ms),
                        bid=bid,
                        ask=ask,
                        last=(ask + bid) / 2.0,
                        volume=float(ask_v + bid_v),
                    )
                )
            return ticks
        except Exception as exc:
            self.logger.debug(
                "FR-BROKER-DUKASCOPY-MARKET-DATA: Datafeed tick fetch failed: %s",
                exc,
            )
            return []

    @override
    def get_symbol_info(self, symbol: str) -> StandardResponse[SymbolInfo]:
        """Retrieve instrument specifications and metadata from the CSV catalog."""
        sym_clean = symbol.upper().replace("/", "").replace("_", "").replace("-", "")
        catalog = self._ensure_catalog()
        info = catalog.get(sym_clean)
        if not info:
            msg = f"Symbol '{sym_clean}' not found in Dukascopy catalog"
            self.logger.warning(
                "FR-BROKER-DUKASCOPY-SYMBOLS: %s",
                msg,
                extra={"fr_id": "FR-BROKER-DUKASCOPY-SYMBOLS", "symbol": sym_clean},
            )
            return StandardResponse.failure(
                message=msg,
                error=StandardError(code="SYMBOL_NOT_FOUND", message=msg),
                extensions={"broker": self.name},
            )

        self.logger.info(
            "FR-BROKER-DUKASCOPY-SYMBOLS: Resolved metadata for '%s' (%s, %d digits)",
            sym_clean,
            info.description,
            info.digits,
            extra={
                "fr_id": "FR-BROKER-DUKASCOPY-SYMBOLS",
                "symbol": sym_clean,
                "digits": info.digits,
            },
        )
        return StandardResponse.success(
            data=info,
            message=f"Symbol info retrieved for '{sym_clean}'",
            extensions={"broker": self.name},
        )

    @override
    def get_symbols(
        self, group: str | None = None
    ) -> StandardResponse[list[SymbolInfo]]:
        """Retrieve symbols list from the CSV catalog, optionally filtered by group."""
        catalog = self._ensure_catalog()
        symbols = list(catalog.values())
        if group:
            group_clean = group.upper().strip()
            symbols = [
                s
                for s in symbols
                if group_clean in (s.category or "").upper()
                or group_clean in (s.path or "").upper()
            ]
        self.logger.info(
            "FR-BROKER-DUKASCOPY-SYMBOLS: Symbols listed (%d items, filter='%s')",
            len(symbols),
            group or "ALL",
            extra={
                "fr_id": "FR-BROKER-DUKASCOPY-SYMBOLS",
                "count": len(symbols),
                "group": group,
            },
        )
        return StandardResponse.success(data=symbols, extensions={"broker": self.name})

    @override
    def get_num_of_symbols(self) -> StandardResponse[int]:
        """Get the total count of symbols available in the CSV catalog."""
        catalog = self._ensure_catalog()
        self.logger.info(
            "FR-BROKER-DUKASCOPY-SYMBOLS: Catalog count query returned %d instruments",
            len(catalog),
            extra={"fr_id": "FR-BROKER-DUKASCOPY-SYMBOLS", "count": len(catalog)},
        )
        return StandardResponse.success(
            data=len(catalog), extensions={"broker": self.name}
        )

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
        """Retrieve historical candlestick bars from CDN with standard datafeed fallback.

        Fetches the yearly bundle from StrategyQuant CDN by default. If the CDN
        archive is missing or unavailable, automatically falls back to Dukascopy's
        direct datafeed (.bi5 LZMA stream) in memory. No disk caching or persistence
        is performed.

        Args:
            symbol: Instrument symbol identifier (e.g. 'EURUSD').
            timeframe: Data timeframe (default TimeFrame.H1).
            count: Maximum number of bars to return (default 100).
            date_from: Optional starting boundary datetime.
            date_to: Optional ending boundary datetime.
            start_pos: Optional starting offset position.

        Returns:
            StandardResponse containing list of Bar entities.
        """
        sym_clean = symbol.upper().replace("/", "").replace("_", "").replace("-", "")
        catalog = self._ensure_catalog()
        sym_info = catalog.get(sym_clean)
        decimals = sym_info.digits if sym_info else 5
        scale = 10.0 ** (decimals + 1)
        target_count = count or 100

        target_year = date_from.year if date_from else 2023
        cdn_url = f"{self.CDN_BASE_URL}/m1/{sym_clean}/{target_year}.zip"

        try:
            resp = self.session.get(cdn_url, timeout=(5.0, 30.0))
            if resp.status_code == 200 and resp.content:
                bars: list[Bar] = []
                with zipfile.ZipFile(io.BytesIO(resp.content)) as z:
                    names = sorted(z.namelist())
                    if date_from or date_to:
                        filtered_names: list[str] = []
                        for n in names:
                            base_name = n.replace(".dat", "").replace(".bi5", "")
                            try:
                                parts = base_name.split("_")
                                file_dt = datetime(
                                    int(parts[0]),
                                    int(parts[1]),
                                    int(parts[2]),
                                    tzinfo=UTC,
                                )
                                if date_from and file_dt < datetime(
                                    date_from.year,
                                    date_from.month,
                                    date_from.day,
                                    tzinfo=UTC,
                                ):
                                    continue
                                if date_to and file_dt > datetime(
                                    date_to.year,
                                    date_to.month,
                                    date_to.day,
                                    tzinfo=UTC,
                                ):
                                    continue
                                filtered_names.append(n)
                            except ValueError, IndexError:
                                filtered_names.append(n)
                        names = filtered_names

                    for name in names[-target_count:]:
                        content = z.read(name)
                        idx = content.find(b"\xbb\xbb\xbb")
                        if idx != -1 and len(content) >= idx + 3 + 48:
                            offset = idx + 3
                            ts, o, h, l, c, v = struct.unpack_from(
                                ">QQQQQQ", content, offset
                            )
                            dt = datetime.fromtimestamp(ts / 1000, tz=UTC)
                            bars.append(
                                Bar(
                                    time=dt,
                                    open=o / scale,
                                    high=h / scale,
                                    low=l / scale,
                                    close=c / scale,
                                    tick_volume=int(v),
                                    real_volume=int(v),
                                )
                            )

                if bars:
                    if count and len(bars) > count:
                        bars = bars[-count:]
                    self.logger.info(
                        "FR-BROKER-DUKASCOPY-MARKET-DATA: Extracted %d bars for %s from CDN",
                        len(bars),
                        sym_clean,
                        extra={
                            "fr_id": "FR-BROKER-DUKASCOPY-MARKET-DATA",
                            "symbol": sym_clean,
                            "count": len(bars),
                        },
                    )
                    return StandardResponse.success(
                        data=bars,
                        message=f"Retrieved {len(bars)} bars for '{sym_clean}' from CDN",
                        extensions={
                            "broker": self.name,
                            "symbol": sym_clean,
                            "count": len(bars),
                            "source": "cdn",
                        },
                    )
        except Exception as exc:
            self.logger.debug(
                "FR-BROKER-DUKASCOPY-MARKET-DATA: CDN download failed: %s", exc
            )

        # Automatic fallback to direct Dukascopy datafeed
        self.logger.info(
            "FR-BROKER-DUKASCOPY-MARKET-DATA: CDN unavailable for '%s', falling back to direct datafeed",
            sym_clean,
            extra={"fr_id": "FR-BROKER-DUKASCOPY-MARKET-DATA", "symbol": sym_clean},
        )
        target_dt = date_from or datetime(target_year, 1, 1, tzinfo=UTC)
        feed_bars = self._fetch_datafeed_bars(
            sym_clean=sym_clean,
            dt=target_dt,
            decimals=decimals,
            count=target_count,
        )
        if feed_bars:
            if count and len(feed_bars) > count:
                feed_bars = feed_bars[-count:]
            self.logger.info(
                "FR-BROKER-DUKASCOPY-MARKET-DATA: Fallback retrieved %d bars from direct datafeed for %s",
                len(feed_bars),
                sym_clean,
                extra={
                    "fr_id": "FR-BROKER-DUKASCOPY-MARKET-DATA",
                    "symbol": sym_clean,
                    "count": len(feed_bars),
                },
            )
            return StandardResponse.success(
                data=feed_bars,
                message=f"Retrieved {len(feed_bars)} bars for '{sym_clean}' from datafeed fallback",
                extensions={
                    "broker": self.name,
                    "symbol": sym_clean,
                    "count": len(feed_bars),
                    "source": "datafeed_fallback",
                },
            )

        msg = f"No bars available for '{sym_clean}' via CDN or direct datafeed fallback"
        self.logger.warning(
            "FR-BROKER-DUKASCOPY-MARKET-DATA: %s",
            msg,
            extra={"fr_id": "FR-BROKER-DUKASCOPY-MARKET-DATA", "symbol": sym_clean},
        )
        return StandardResponse.failure(
            message=msg,
            error=StandardError(code="NO_DATA", message=msg),
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
        """Retrieve historical tick data with direct datafeed fallback."""
        sym_clean = symbol.upper().replace("/", "").replace("_", "").replace("-", "")
        catalog = self._ensure_catalog()
        sym_info = catalog.get(sym_clean)
        decimals = sym_info.digits if sym_info else 5

        # Attempt direct datafeed ticks if date is specified
        if date_from:
            feed_ticks = self._fetch_datafeed_ticks(
                sym_clean=sym_clean,
                dt=date_from,
                decimals=decimals,
                count=count or 100,
            )
            if feed_ticks:
                self.logger.info(
                    "FR-BROKER-DUKASCOPY-MARKET-DATA: Retrieved %d ticks from direct datafeed for %s",
                    len(feed_ticks),
                    sym_clean,
                    extra={
                        "fr_id": "FR-BROKER-DUKASCOPY-MARKET-DATA",
                        "symbol": sym_clean,
                        "count": len(feed_ticks),
                    },
                )
                return StandardResponse.success(
                    data=feed_ticks,
                    message=f"Retrieved {len(feed_ticks)} ticks for '{sym_clean}' from datafeed",
                    extensions={"broker": self.name, "source": "datafeed"},
                )

        # Fallback to deriving ticks from bars
        bars_res = self.get_bars(
            symbol=sym_clean,
            timeframe=TimeFrame.M1,
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
            self.logger.info(
                "FR-BROKER-DUKASCOPY-MARKET-DATA: Derived %d ticks for %s",
                len(ticks),
                sym_clean,
                extra={
                    "fr_id": "FR-BROKER-DUKASCOPY-MARKET-DATA",
                    "symbol": sym_clean,
                    "count": len(ticks),
                },
            )
            return StandardResponse.success(
                data=ticks,
                message=f"Retrieved {len(ticks)} ticks for '{sym_clean}'",
                extensions={"broker": self.name},
            )
        return StandardResponse.success(
            data=[],
            message=bars_res.message,
            extensions={"broker": self.name},
        )


def create_adapter(_context: PluginHostContext | None = None) -> DukascopyBroker:
    """Plugin entrypoint factory constructing DukascopyBroker adapter."""
    logger.info("Initializing Dukascopy broker plugin adapter.")
    return DukascopyBroker()


if __name__ == "__main__":
    from app.plugins.brokers import get_bars, get_symbol_info

    dukascopy = create_adapter()
    print("\n[3] DUKASCOPY:")
    d_info = get_symbol_info(broker=dukascopy, symbol="EURUSD")
    print(
        f"    Symbol Info: {d_info.data.description if d_info.data else 'None'}, "
        f"digits={d_info.data.digits if d_info.data else 'None'}"
    )
    assert d_info.is_success
    assert d_info.data is not None
    assert d_info.data.digits == 5

    d_num = dukascopy.get_num_of_symbols()
    print(f"    Catalog Symbols: {d_num.data}")
    assert d_num.is_success
    assert d_num.data == 725

    d_bars = get_bars(broker=dukascopy, symbol="EURUSD", count=5)
    print(
        f"    CDN Bars: count={len(d_bars.data) if d_bars.data else 0} "
        f"(success={d_bars.is_success})"
    )
    assert d_bars.is_success
    assert d_bars.data is not None
    assert len(d_bars.data) == 5
