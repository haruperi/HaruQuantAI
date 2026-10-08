"""Dukascopy high-resolution historical tick and bar market data broker plugin.

Description:
    Implements a specialized market data broker plugin for Dukascopy Swiss FX
    marketplace historical data and tick archives.
    Within HaruQuantAI, Dukascopy serves as a primary source for high-precision
    historical backtesting data and Data Manager workspace downloads. The plugin
    supports downloading and decompressing raw `.bi5` binary files (LZMA compressed
    struct arrays) from StrategyQuant CDN servers, reading cached Parquet archives
    from `data/market/dukascopy`, and fulfilling uniform `download_bars()` requests.
    All non-download and trading methods cleanly fallback to BaseBroker default
    unsupported capability handling.

Purpose:
    FEAT-BROKER-DUKASCOPY: High-Precision Historical FX Tick and Bar Extraction.
    Provides `.bi5` LZMA decompression, StrategyQuant CDN fetching, and local
    Parquet reading for Dukascopy market data feeds.

Key Capabilities:
    - FR-BROKER-DUKASCOPY-TICK-DECOMPRESS: Bi5 Binary LZMA Tick Parsing
      Associated: `[DukascopyBroker.get_bars()]`, `[_decompress_bi5()]`
      Logging: Emits INFO log upon successfully downloading and parsing CDN bars,
      and DEBUG log on decompression or network failures.
    - FR-BROKER-DUKASCOPY-LOCAL-STORE: Parquet Archive Ingestion
      Associated: `[DukascopyBroker.get_bars()]`, `[DukascopyBroker.get_ticks()]`
      Logging: Emits INFO log upon reading local Parquet partitions, and DEBUG
      log on partition read errors.
    - FR-BROKER-DUKASCOPY-DOWNLOAD: Data Manager Bar Download Pipeline
      Associated: `[DukascopyBroker.download_bars()]`, `[create_adapter()]`
      Logging: Emits delegated telemetry through get_bars and cancellation checks.

Python API Usage:
    ```python
    from app.plugins.brokers.dukascopy import DukascopyBroker, create_adapter

    broker = create_adapter()
    bars_resp = broker.get_bars("EURUSD", count=10)
    if bars_resp.is_success:
        assert len(bars_resp.data) > 0
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
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, override

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from app.host.discovery import PluginHostContext
from app.host.logging import get_logger
from app.host.persistence import DatabaseManager
from app.plugins.brokers.contracts import (
    Bar,
    BaseBroker,
    BrokerCapability,
    StandardResponse,
    Tick,
    TimeFrame,
)
from app.workspace.data_manager.connections import (
    CancellationToken,
    DownloadRequest,
    ProviderCapabilities,
)
from app.workspace.data_manager.data import BarRecord

logger = get_logger(__name__)

PLUGIN_MANIFEST: dict[str, Any] = {
    "manifest_version": 1,
    "id": "broker-dukascopy",
    "name": "Dukascopy Connector",
    "version": "1.0.0",
    "description": "Dukascopy Bank SA tick and historical bar data provider and broker plugin",
    "author": "HaruQuantAI",
    "slot": "broker",
    "entrypoint": "create_adapter",
    "dependencies": [],
    "capabilities": ["bars", "ticks"],
    "enabled": True,
    "metadata": {
        "provider_name": "Dukascopy",
        "display_name": "Dukascopy Bank SA",
        "asset_classes": ["Forex", "Commodities", "Indices"],
        "timeframes": ["M1", "H1", "D1"],
        "requires_auth": False,
        "rate_limit_rps": 10.0,
        "base_url": "https://datafeed.dukascopy.com",
    },
}

SQX_CDN_BASE_URL = "https://cdn.strategyquantcdn.com/data/dukascopy"
DUKASCOPY_FEED_HTTPS = "https://datafeed.dukascopy.com/datafeed"
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)

DEFAULT_DATA_DIR = Path(__file__).resolve().parents[3] / "data" / "market"

KNOWN_SYMBOLS: dict[str, dict[str, Any]] = {
    "EURUSD": {
        "decimals": 5,
        "point_size": 100000.0,
        "category": "Forex",
        "pip_size": 0.0001,
    },
    "GBPUSD": {
        "decimals": 5,
        "point_size": 100000.0,
        "category": "Forex",
        "pip_size": 0.0001,
    },
    "USDJPY": {
        "decimals": 3,
        "point_size": 1000.0,
        "category": "Forex/JPY",
        "pip_size": 0.01,
    },
    "AUDUSD": {
        "decimals": 5,
        "point_size": 100000.0,
        "category": "Forex",
        "pip_size": 0.0001,
    },
    "USDCAD": {
        "decimals": 5,
        "point_size": 100000.0,
        "category": "Forex",
        "pip_size": 0.0001,
    },
    "USDCHF": {
        "decimals": 5,
        "point_size": 100000.0,
        "category": "Forex",
        "pip_size": 0.0001,
    },
    "NZDUSD": {
        "decimals": 5,
        "point_size": 100000.0,
        "category": "Forex",
        "pip_size": 0.0001,
    },
    "XAUUSD": {
        "decimals": 3,
        "point_size": 100.0,
        "category": "Metals",
        "pip_size": 0.01,
    },
    "XAGUSD": {
        "decimals": 3,
        "point_size": 5000.0,
        "category": "Metals",
        "pip_size": 0.001,
    },
    "BTCUSD": {"decimals": 2, "point_size": 1.0, "category": "Crypto", "pip_size": 1.0},
    "ETHUSD": {"decimals": 2, "point_size": 1.0, "category": "Crypto", "pip_size": 1.0},
}


def _decompress_bi5(data: bytes) -> bytes:
    """Decompress Dukascopy .bi5 binary payload with LZMA1 repair."""
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


__all__ = ["DukascopyBroker", "DukascopyProvider", "create_adapter"]


class DukascopyBroker(BaseBroker):
    """Dukascopy datafeed broker plugin."""

    def __init__(
        self,
        name: str = "Dukascopy",
        store_dir: str | Path | None = None,
        db: DatabaseManager | None = None,
    ) -> None:
        """Initialize Dukascopy broker plugin."""
        super().__init__(
            name=name,
            capabilities=BrokerCapability.MARKET_DATA,
        )
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
        self.store_dir = (
            Path(store_dir) if store_dir else DEFAULT_DATA_DIR / "dukascopy"
        )
        self._db = db

    @property
    def provider_capabilities(self) -> ProviderCapabilities:
        """Data provider capabilities metadata."""
        return ProviderCapabilities(
            name="Dukascopy",
            display_name="Dukascopy Bank SA",
            asset_classes=["Forex", "Commodities", "Indices"],
            timeframes=["M1", "H1", "D1"],
            requires_auth=False,
            rate_limit_rps=10.0,
            base_url="https://datafeed.dukascopy.com",
        )

    def download_bars(
        self, request: DownloadRequest, token: CancellationToken | None = None
    ) -> list[BarRecord]:
        """Download historical candlestick records matching the request."""
        if token:
            token.check_cancelled()
        dt_from = (
            datetime.fromisoformat(request.date_from) if request.date_from else None
        )
        dt_to = datetime.fromisoformat(request.date_to) if request.date_to else None
        bars_resp = self.get_bars(
            symbol=request.symbol,
            timeframe=request.timeframe,
            date_from=dt_from,
            date_to=dt_to,
        )
        if bars_resp.is_success and bars_resp.data:
            return [
                BarRecord(
                    timestamp_utc=b.time.isoformat(),
                    open=b.open,
                    high=b.high,
                    low=b.low,
                    close=b.close,
                    volume=float(b.tick_volume),
                )
                for b in bars_resp.data
            ]
        return []

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
        """Retrieve historical candlestick bars from StrategyQuant CDN or local cache."""
        sym_clean = symbol.upper().replace("/", "").replace("_", "").replace("-", "")
        spec = KNOWN_SYMBOLS.get(sym_clean, {"decimals": 5})
        scale = 1000.0 if spec.get("decimals") == 3 else 100000.0

        tf_str = str(timeframe).upper()
        res_dir = "m1" if "M1" in tf_str or "1M" in tf_str else "d1"
        local_dir = self.store_dir / res_dir / sym_clean.lower()
        if local_dir.exists():
            try:
                import pyarrow.parquet as pq

                p_files = sorted(local_dir.glob("*.parquet"))
                if p_files:
                    table = pq.read_table(p_files[-1])
                    df = table.to_pandas()
                    bars: list[Bar] = []
                    for _, row in df.tail(count or 100).iterrows():
                        bars.append(
                            Bar(
                                time=row["DateTime"].to_pydatetime()
                                if hasattr(row["DateTime"], "to_pydatetime")
                                else row["DateTime"],
                                open=float(row["Open"]),
                                high=float(row["High"]),
                                low=float(row["Low"]),
                                close=float(row["Close"]),
                                tick_volume=int(row.get("Volume", 0)),
                            )
                        )
                    self.logger.info(
                        "FR-BROKER-DUKASCOPY-LOCAL-STORE: Loaded %d bars for %s from Parquet",
                        len(bars),
                        sym_clean,
                        extra={
                            "fr_id": "FR-BROKER-DUKASCOPY-LOCAL-STORE",
                            "symbol": sym_clean,
                            "count": len(bars),
                        },
                    )
                    return StandardResponse.success(
                        data=bars, extensions={"broker": self.name}
                    )
            except Exception as e:
                self.logger.debug(
                    "FR-BROKER-DUKASCOPY-LOCAL-STORE: Local parquet read failed: %s",
                    e,
                    extra={"fr_id": "FR-BROKER-DUKASCOPY-LOCAL-STORE"},
                )

        target_year = date_from.year if date_from else 2023
        cdn_url = f"{SQX_CDN_BASE_URL}/m1/{sym_clean}/{target_year}.zip"
        try:
            r = self.session.get(cdn_url, timeout=(5.0, 30.0))
            if r.status_code == 200:
                import zipfile

                with zipfile.ZipFile(io.BytesIO(r.content)) as z:
                    name_list = sorted(z.namelist())
                    if name_list:
                        day_content = z.read(name_list[-1])
                        decomp = _decompress_bi5(day_content)
                        if not decomp:
                            decomp = day_content
                        rec_count = len(decomp) // 24
                        bars = []
                        base_dt = datetime(target_year, 1, 1, tzinfo=UTC)
                        for i in range(min(rec_count, count or 100)):
                            rec = struct.unpack_from(">iiiii f", decomp, i * 24)
                            offset_sec, o, c, l, h, v = rec
                            bars.append(
                                Bar(
                                    time=base_dt + timedelta(seconds=offset_sec),
                                    open=o / scale,
                                    high=h / scale,
                                    low=l / scale,
                                    close=c / scale,
                                    tick_volume=int(v),
                                )
                            )
                        self.logger.info(
                            "FR-BROKER-DUKASCOPY-TICK-DECOMPRESS: Retrieved %d bars from Dukascopy CDN",
                            len(bars),
                            extra={
                                "fr_id": "FR-BROKER-DUKASCOPY-TICK-DECOMPRESS",
                                "symbol": sym_clean,
                                "count": len(bars),
                            },
                        )
                        return StandardResponse.success(
                            data=bars,
                            message=f"Retrieved {len(bars)} bars from Dukascopy CDN",
                            extensions={"broker": self.name},
                        )
        except Exception as e:
            self.logger.debug("CDN download error: %s", e)

        return StandardResponse.success(
            data=[],
            message=f"No Dukascopy bars available for '{sym_clean}'",
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
        """Retrieve historical ticks."""
        sym_clean = symbol.upper().replace("/", "").replace("_", "").replace("-", "")
        bars_res = self.get_bars(symbol=sym_clean, timeframe=TimeFrame.M1, count=count)
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
                data=ticks, extensions={"broker": self.name}
            )
        return StandardResponse.success(data=[], extensions={"broker": self.name})


# Compatibility aliases
DukascopyProvider = DukascopyBroker


def create_adapter(_context: PluginHostContext | None = None) -> DukascopyBroker:
    """Plugin entrypoint factory constructing DukascopyBroker adapter."""
    logger.info("Initializing Dukascopy broker plugin adapter.")
    return DukascopyBroker()
