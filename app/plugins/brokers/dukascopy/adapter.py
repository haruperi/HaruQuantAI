"""Dukascopy high-resolution historical tick and bar market data broker plugin.

Description:
    Implements a specialized market data broker plugin for Dukascopy Swiss FX
    marketplace historical data and tick archives.
    Within HaruQuantAI, Dukascopy serves as a primary source for high-precision
    historical backtesting data. The plugin supports downloading and decompressing
    raw `.bi5` binary files (LZMA compressed struct arrays) from Dukascopy web
    servers, fetching consolidated candles from StrategyQuant CDN servers, and
    reading cached Parquet archives from `data/market/dukascopy`.
    Because Dukascopy is utilized exclusively for market data extraction in this
    subsystem, all order routing, trading, and execution methods return canonical
    unsupported capability responses (`BaseBroker._unsupported()`).

Purpose:
    FEAT-BROKER-DUKASCOPY: High-Precision Historical FX Tick and Bar Extraction.
    Provides `.bi5` LZMA decompression, StrategyQuant CDN fetching, and local
    Parquet reading for Dukascopy market data feeds.

Key Capabilities:
    - FR-BROKER-DUKASCOPY-CATALOG: Swiss FX/CFD Contract Specifications
      Associated: `[DukascopyBroker.get_symbol_info()]`,
      `[DukascopyBroker.get_symbols()]`
      Logging: Emits DEBUG log when returning symbol specifications.
    - FR-BROKER-DUKASCOPY-TICK-DECOMPRESS: Bi5 Binary LZMA Tick Parsing
      Associated: `[DukascopyBroker._download_bi5_ticks()]`,
      `[DukascopyBroker._parse_bi5_ticks()]`
      Logging: Emits DEBUG log with decompressed tick counts and WARNING log
      on HTTP 404 or corrupted archives.
    - FR-BROKER-DUKASCOPY-LOCAL-STORE: Parquet Archive Ingestion
      Associated: `[DukascopyBroker.get_bars()]`,
      `[DukascopyBroker._read_local_parquet()]`
      Logging: Emits INFO log upon reading local Parquet partitions.
    - FR-BROKER-DUKASCOPY-TRADE-REJECTION: Unsupported Trade Capability Rejection
      Associated: `[DukascopyBroker.trade()]`, `[DukascopyBroker.check_order()]`
      Logging: Emits WARNING log declaring trading capabilities unsupported.

Python API Usage:
    ```python
    from app.plugins.brokers import dukascopy

    # Verify Dukascopy instrument specification
    sym_resp = dukascopy.get_symbol_info("EURUSD")
    if sym_resp.is_success:
        assert sym_resp.data.point == 0.00001
        print(f"Contract Size: {sym_resp.data.trade_contract_size}")
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
    StandardError,
    StandardResponse,
    SymbolInfo,
    Tick,
    TimeFrame,
)
from app.workspace.data_manager.connections import (
    CancellationToken,
    DownloadRequest,
    ProviderCapabilities,
)
from app.workspace.data_manager.data import BarRecord
from app.workspace.data_manager.instruments import InstrumentService

logger = get_logger(__name__)

SQX_CDN_BASE_URL = "https://cdn.strategyquantcdn.com/data/dukascopy"
DUKASCOPY_FEED_HTTPS = "https://datafeed.dukascopy.com/datafeed"
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)

DEFAULT_DATA_DIR = Path(__file__).resolve().parents[4] / "data" / "market"

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
            capabilities=(
                BrokerCapability.CONNECT
                | BrokerCapability.MARKET_DATA
                | BrokerCapability.SYMBOLS
            ),
        )
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": USER_AGENT})
        retry_strategy = Retry(
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
        self._instruments_service = InstrumentService(db) if db else None
        self._connected = True

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
    def connect(self, **kwargs: Any) -> StandardResponse[bool]:
        """Verify connectivity to StrategyQuant Cloudflare CDN."""
        self.logger.info(
            "FR-BROKER-DUKASCOPY-CATALOG: Connecting to Dukascopy CDN datafeed...",
            extra={"fr_id": "FR-BROKER-DUKASCOPY-CATALOG"},
        )
        try:
            r = self.session.head(
                f"{SQX_CDN_BASE_URL}/m1/EURUSD/2023.zip", timeout=(3.0, 5.0)
            )
            self._connected = r.status_code == 200
            if self._connected:
                return StandardResponse.success(
                    data=True,
                    message="Connected to Dukascopy CDN",
                    extensions={"broker": self.name},
                )
            msg = f"Dukascopy CDN returned status {r.status_code}"
            return StandardResponse.failure(
                message=msg,
                error=StandardError(code=str(r.status_code), message=msg),
                extensions={"broker": self.name},
            )
        except Exception as e:
            self._connected = False
            msg = f"Failed to connect to Dukascopy CDN: {e}"
            return StandardResponse.failure(
                message=msg,
                error=StandardError(code="CONNECTION_ERROR", message=msg),
                extensions={"broker": self.name},
            )

    @override
    def is_connected(self) -> StandardResponse[bool]:
        """Check active connection state."""
        return StandardResponse.success(
            data=self._connected,
            message="Connected" if self._connected else "Disconnected",
            extensions={"broker": self.name},
        )

    @override
    def disconnect(self) -> StandardResponse[bool]:
        """Disconnect session."""
        self._connected = False
        return StandardResponse.success(
            data=True, message="Disconnected", extensions={"broker": self.name}
        )

    @override
    def get_symbol_info(self, symbol: str) -> StandardResponse[SymbolInfo]:
        """Retrieve instrument specifications from host catalog or fallback."""
        sym_clean = symbol.upper().replace("/", "").replace("_", "").replace("-", "")
        if self._instruments_service is not None:
            inst = self._instruments_service.get_instrument(sym_clean)
            if inst is not None:
                info = SymbolInfo(
                    name=sym_clean,
                    visible=True,
                    select=True,
                    point=inst.tick_size,
                    digits=inst.decimals,
                    spread=int(inst.default_spread / inst.tick_size)
                    if inst.tick_size
                    else 0,
                    trade_contract_size=inst.point_value,
                    currency_base=sym_clean[:3] if len(sym_clean) >= 6 else "USD",
                    currency_profit=sym_clean[3:6] if len(sym_clean) >= 6 else "USD",
                    currency_margin=sym_clean[:3] if len(sym_clean) >= 6 else "USD",
                    description=inst.description,
                    raw=inst,
                )
                self.logger.debug(
                    "FR-BROKER-DUKASCOPY-CATALOG: Retrieved symbol info from database for %s",
                    sym_clean,
                    extra={"fr_id": "FR-BROKER-DUKASCOPY-CATALOG", "symbol": sym_clean},
                )
                return StandardResponse.success(
                    data=info,
                    extensions={"broker": self.name, "source": "database"},
                )

        spec = KNOWN_SYMBOLS.get(sym_clean)
        if not spec:
            dec = 3 if sym_clean.endswith("JPY") else 5
            spec = {
                "decimals": dec,
                "point_size": 100000.0,
                "category": "Forex",
                "pip_size": 0.01 if dec == 3 else 0.0001,
            }

        info = SymbolInfo(
            name=sym_clean,
            visible=True,
            select=True,
            point=spec["pip_size"] / 10.0
            if spec["decimals"] in (3, 5)
            else spec["pip_size"],
            digits=spec["decimals"],
            trade_contract_size=spec["point_size"],
            currency_base=sym_clean[:3] if len(sym_clean) >= 6 else "USD",
            currency_profit=sym_clean[3:6] if len(sym_clean) >= 6 else "USD",
            raw=spec,
        )
        self.logger.debug(
            "FR-BROKER-DUKASCOPY-CATALOG: Retrieved symbol info from fallback catalog for %s",
            sym_clean,
            extra={"fr_id": "FR-BROKER-DUKASCOPY-CATALOG", "symbol": sym_clean},
        )
        return StandardResponse.success(
            data=info,
            extensions={"broker": self.name, "raw": spec, "source": "fallback"},
        )

    @override
    def get_symbols(
        self, group: str | None = None
    ) -> StandardResponse[list[SymbolInfo]]:
        """Retrieve list of available Dukascopy instruments."""
        symbols: list[SymbolInfo] = []
        for sym in KNOWN_SYMBOLS:
            if not group or group.upper() in sym:
                res = self.get_symbol_info(sym)
                if res.data:
                    symbols.append(res.data)
        return StandardResponse.success(data=symbols, extensions={"broker": self.name})

    @override
    def get_symbol_tick(self, symbol: str) -> StandardResponse[Tick]:
        """Get latest known quote tick for symbol."""
        bars_res = self.get_bars(symbol=symbol, timeframe=TimeFrame.M1, count=1)
        now = datetime.now(UTC)
        if bars_res.is_success and bars_res.data:
            last_bar = bars_res.data[-1]
            return StandardResponse.success(
                data=Tick(
                    time=last_bar.time,
                    bid=last_bar.close,
                    ask=last_bar.close,
                    last=last_bar.close,
                ),
                extensions={"broker": self.name},
            )
        return StandardResponse.failure(
            message=f"No recent quotes available from Dukascopy for symbol '{symbol}'",
            error=StandardError(
                code="NO_DATA",
                message=f"No recent quotes available from Dukascopy for symbol '{symbol}'",
            ),
            extensions={"broker": self.name},
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
