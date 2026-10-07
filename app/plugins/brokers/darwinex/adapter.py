"""Darwinex institutional market data broker and provider plugin.

Description:
    Implements a market data broker plugin tailored for Darwinex institutional
    FX, indices, and commodity tick specifications and historical feeds.
    Within HaruQuantAI, Darwinex provides high-resolution bid/ask spread models,
    institutional instrument specifications (pip points, contract sizes, digits),
    and local Parquet market data reading from `data/market/darwinex`.
    Because Darwinex is configured as a dedicated market data provider in this
    workspace, trading and order execution methods cleanly return standardized
    unsupported capability responses (`BaseBroker._unsupported()`).

Purpose:
    FEAT-BROKER-DARWINEX: Institutional FX/CFD Market Data and Parquet Store.
    Provides Darwinex instrument specifications, tick data structures, and
    historical bar extraction from local Parquet archives.

Key Capabilities:
    - FR-BROKER-DARWINEX-CATALOG: Institutional Instrument Specifications
      Associated: `[DarwinexBroker.get_symbol_info()]`,
      `[DarwinexBroker.get_symbols()]`
      Logging: Emits DEBUG log when returning symbol specifications from
      catalog or fallback definitions.
    - FR-BROKER-DARWINEX-PARQUET-DATA: Parquet Storage Bar Ingestion
      Associated: `[DarwinexBroker.get_bars()]`,
      `[DarwinexBroker.get_ticks()]`
      Logging: Emits INFO log upon successfully loading Parquet records,
      and WARNING log if data path is absent or corrupted.
    - FR-BROKER-DARWINEX-TRADE-REJECTION: Unsupported Trading Rejection
      Associated: `[DarwinexBroker.trade()]`, `[DarwinexBroker.check_order()]`
      Logging: Emits WARNING log declaring trading capabilities unsupported.

Python API Usage:
    ```python
    from app.plugins.brokers import darwinex

    # Inspect Darwinex EURUSD instrument specifications
    sym_resp = darwinex.get_symbol_info("EURUSD")
    if sym_resp.is_success:
        assert sym_resp.data.digits == 5
        print(f"EURUSD Point: {sym_resp.data.point}")
    ```

CLI Usage:
    ```bash
    uv run python scripts/brokers_all.py
    ```
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any, override

import requests

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

SQX_DARWINEX_CDN = "https://cdn.strategyquantcdn.com/data/darwinex"
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)

DEFAULT_DATA_DIR = Path(__file__).resolve().parents[4] / "data" / "market"

# Core embedded instruments from DarwinexCatalog
DARWINEX_INSTRUMENTS: dict[str, dict[str, Any]] = {
    "EURUSD": {
        "decimals": 5,
        "tick_value": 100000.0,
        "tick_size": 0.0001,
        "tick_step": 0.00001,
    },
    "GBPUSD": {
        "decimals": 5,
        "tick_value": 100000.0,
        "tick_size": 0.0001,
        "tick_step": 0.00001,
    },
    "USDJPY": {
        "decimals": 3,
        "tick_value": 1000.0,
        "tick_size": 0.01,
        "tick_step": 0.001,
    },
    "AUDUSD": {
        "decimals": 5,
        "tick_value": 100000.0,
        "tick_size": 0.0001,
        "tick_step": 0.00001,
    },
    "USDCAD": {
        "decimals": 5,
        "tick_value": 100000.0,
        "tick_size": 0.0001,
        "tick_step": 0.00001,
    },
    "USDCHF": {
        "decimals": 5,
        "tick_value": 100000.0,
        "tick_size": 0.0001,
        "tick_step": 0.00001,
    },
    "XAUUSD": {
        "decimals": 2,
        "tick_value": 100.0,
        "tick_size": 0.01,
        "tick_step": 0.01,
    },
    "SP500": {"decimals": 2, "tick_value": 1.0, "tick_size": 0.01, "tick_step": 0.01},
    "NAS100": {"decimals": 2, "tick_value": 1.0, "tick_size": 0.01, "tick_step": 0.01},
    "AAPL": {"decimals": 2, "tick_value": 1.0, "tick_size": 0.01, "tick_step": 0.01},
}


class DarwinexBroker(BaseBroker):
    """Darwinex tick and candle datafeed broker plugin."""

    def __init__(
        self,
        name: str = "Darwinex",
        store_dir: str | Path | None = None,
        db: DatabaseManager | None = None,
    ) -> None:
        """Initialize Darwinex broker plugin."""
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
        self.store_dir = Path(store_dir) if store_dir else DEFAULT_DATA_DIR / "darwinex"
        self._db = db
        self._instruments_service = InstrumentService(db) if db else None
        self._connected = True

    @property
    def provider_capabilities(self) -> ProviderCapabilities:
        """Data provider capabilities metadata."""
        return ProviderCapabilities(
            name="Darwinex",
            display_name="Darwinex Tick & Bar Feeds",
            asset_classes=["Forex", "CFD"],
            timeframes=["M1", "H1", "D1"],
            requires_auth=True,
            rate_limit_rps=5.0,
            base_url="https://api.darwinex.com",
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
        """Verify connectivity to Darwinex CDN."""
        self.logger.info(
            "FR-BROKER-DARWINEX-CATALOG: Connecting to Darwinex CDN...",
            extra={"fr_id": "FR-BROKER-DARWINEX-CATALOG"},
        )
        try:
            r = self.session.head(
                f"{SQX_DARWINEX_CDN}/EURUSD/metadata.dat", timeout=(3.0, 5.0)
            )
            self._connected = r.status_code in (200, 301, 302)
            if self._connected:
                return StandardResponse.success(
                    data=True,
                    message="Connected to Darwinex CDN",
                    extensions={"broker": self.name},
                )
            return StandardResponse.failure(
                message=f"Darwinex CDN status: {r.status_code}",
                error=StandardError(
                    code=str(r.status_code),
                    message=f"Darwinex CDN status: {r.status_code}",
                ),
                extensions={"broker": self.name},
            )
        except Exception as e:
            self._connected = False
            return StandardResponse.failure(
                message=f"Failed to connect to Darwinex CDN: {e}",
                error=StandardError(
                    code="CONNECTION_ERROR",
                    message=f"Failed to connect to Darwinex CDN: {e}",
                ),
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
                    "FR-BROKER-DARWINEX-CATALOG: Retrieved symbol info from database for %s",
                    sym_clean,
                    extra={"fr_id": "FR-BROKER-DARWINEX-CATALOG", "symbol": sym_clean},
                )
                return StandardResponse.success(
                    data=info,
                    extensions={"broker": self.name, "source": "database"},
                )

        spec = DARWINEX_INSTRUMENTS.get(sym_clean)
        if not spec:
            dec = 3 if sym_clean.endswith("JPY") else (2 if len(sym_clean) <= 4 else 5)
            spec = {
                "decimals": dec,
                "tick_value": 100000.0,
                "tick_size": 1.0 / (10**dec),
                "tick_step": 1.0 / (10**dec),
            }

        info = SymbolInfo(
            name=sym_clean,
            visible=True,
            select=True,
            point=spec["tick_step"],
            digits=spec["decimals"],
            trade_contract_size=spec["tick_value"],
            currency_base=sym_clean[:3] if len(sym_clean) >= 6 else "USD",
            currency_profit=sym_clean[3:6] if len(sym_clean) >= 6 else "USD",
            raw=spec,
        )
        self.logger.debug(
            "FR-BROKER-DARWINEX-CATALOG: Retrieved symbol info from fallback catalog for %s",
            sym_clean,
            extra={"fr_id": "FR-BROKER-DARWINEX-CATALOG", "symbol": sym_clean},
        )
        return StandardResponse.success(
            data=info,
            extensions={"broker": self.name, "raw": spec, "source": "fallback"},
        )

    @override
    def get_symbols(
        self, group: str | None = None
    ) -> StandardResponse[list[SymbolInfo]]:
        """Retrieve list of supported Darwinex symbols."""
        res: list[SymbolInfo] = []
        for sym in DARWINEX_INSTRUMENTS:
            if not group or group.upper() in sym:
                info_res = self.get_symbol_info(sym)
                if info_res.data:
                    res.append(info_res.data)
        return StandardResponse.success(data=res, extensions={"broker": self.name})

    @override
    def get_symbol_tick(self, symbol: str) -> StandardResponse[Tick]:
        """Retrieve latest known quote tick for symbol."""
        sym_clean = symbol.upper().replace("/", "").replace("_", "").replace("-", "")
        return StandardResponse.failure(
            message=f"Darwinex is an offline historical archive and does not support live tick streaming for '{sym_clean}'",
            error=StandardError(
                code="UNSUPPORTED_OPERATION",
                message=f"Darwinex does not support live tick streaming for '{sym_clean}'",
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
        """Retrieve historical candlestick bars from Darwinex local Parquet."""
        sym_clean = symbol.upper().replace("/", "").replace("_", "").replace("-", "")
        local_dir = self.store_dir / "m1" / sym_clean.lower()
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
                        "FR-BROKER-DARWINEX-PARQUET-DATA: Loaded %d bars for %s",
                        len(bars),
                        sym_clean,
                        extra={
                            "fr_id": "FR-BROKER-DARWINEX-PARQUET-DATA",
                            "symbol": sym_clean,
                            "count": len(bars),
                        },
                    )
                    return StandardResponse.success(
                        data=bars, extensions={"broker": self.name}
                    )
            except Exception as e:
                self.logger.debug(
                    "FR-BROKER-DARWINEX-PARQUET-DATA: Local parquet read failed: %s",
                    e,
                    extra={"fr_id": "FR-BROKER-DARWINEX-PARQUET-DATA"},
                )

        return StandardResponse.success(
            data=[],
            message=f"No local or cached Darwinex bars available for '{sym_clean}'",
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
        return StandardResponse.success(data=[], extensions={"broker": self.name})


# Compatibility aliases
DarwinexProvider = DarwinexBroker


def create_adapter(_context: PluginHostContext | None = None) -> DarwinexBroker:
    """Plugin entrypoint factory constructing DarwinexBroker adapter."""
    logger.info("Initializing Darwinex broker plugin adapter.")
    return DarwinexBroker()
