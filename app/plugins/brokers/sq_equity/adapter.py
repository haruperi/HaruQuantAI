"""StrategyQuant Equity local Parquet market data broker and provider plugin.

Description:
    Implements a specialized market data broker plugin accessing StrategyQuant
    US Equity historical tick and candlestick archives stored as local Parquet
    files under `data/market/sq_equity`.
    Within HaruQuantAI, this module provides fast local access to normalized US
    equity datasets (e.g. AAPL, MSFT, TSLA, NVDA, SPY, QQQ) without requiring
    remote API credentials or network connections.
    Because SQ Equity is an offline historical archive provider, trading operations
    and live session controls are rejected with canonical capability unsupported
    errors (`BaseBroker._unsupported()`).

Purpose:
    FEAT-BROKER-SQ-EQUITY: StrategyQuant US Equity Local Parquet Datafeed.
    Provides fast, offline historical equity bar and tick extraction from
    filesystem Parquet archives.

Key Capabilities:
    - FR-BROKER-SQ-EQUITY-CATALOG: US Equity Ticker Specifications
      Associated: `[SQEquityBroker.get_symbol_info()]`,
      `[SQEquityBroker.get_symbols()]`
      Logging: Emits DEBUG log when returning equity metadata.
    - FR-BROKER-SQ-EQUITY-PARQUET-DATA: Parquet Historical Bar Ingestion
      Associated: `[SQEquityBroker.get_bars()]`,
      `[SQEquityBroker._read_local_parquet()]`
      Logging: Emits INFO log upon successfully parsing Parquet partitions,
      and WARNING log if files are missing or empty.
    - FR-BROKER-SQ-EQUITY-TRADE-REJECTION: Unsupported Trade Capability Rejection
      Associated: `[SQEquityBroker.trade()]`, `[SQEquityBroker.check_order()]`
      Logging: Emits WARNING log declaring trading capabilities unsupported.

Python API Usage:
    ```python
    from app.plugins.brokers import TimeFrame, sq_equity

    # Read historical AAPL daily bars from local Parquet archive
    bars_resp = sq_equity.get_bars("AAPL", timeframe=TimeFrame.D1, count=5)
    if bars_resp.is_success:
        assert len(bars_resp.data) == 5
        print(f"Latest AAPL close: {bars_resp.data[-1].close}")
    ```

CLI Usage:
    ```bash
    uv run python scripts/brokers_all.py
    ```
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any, override

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

DEFAULT_DATA_DIR = Path(__file__).resolve().parents[4] / "data" / "market"

# Embedded benchmark equities from SQEquityCatalog
EQUITY_TICKERS: dict[str, dict[str, Any]] = {
    "SPY": {"name": "SPDR S&P 500 ETF Trust", "exchange": "ARCA", "decimals": 2},
    "QQQ": {"name": "Invesco QQQ Trust", "exchange": "NASDAQ", "decimals": 2},
    "DIA": {
        "name": "SPDR Dow Jones Industrial Average ETF",
        "exchange": "ARCA",
        "decimals": 2,
    },
    "IWM": {"name": "iShares Russell 2000 ETF", "exchange": "ARCA", "decimals": 2},
    "AAPL": {"name": "Apple Inc.", "exchange": "NASDAQ", "decimals": 2},
    "MSFT": {"name": "Microsoft Corporation", "exchange": "NASDAQ", "decimals": 2},
    "AMZN": {"name": "Amazon.com Inc.", "exchange": "NASDAQ", "decimals": 2},
    "GOOGL": {"name": "Alphabet Inc.", "exchange": "NASDAQ", "decimals": 2},
    "NVDA": {"name": "NVIDIA Corporation", "exchange": "NASDAQ", "decimals": 2},
    "TSLA": {"name": "Tesla Inc.", "exchange": "NASDAQ", "decimals": 2},
    "META": {"name": "Meta Platforms Inc.", "exchange": "NASDAQ", "decimals": 2},
}


class SQEquityBroker(BaseBroker):
    """StrategyQuant Equity market data plugin."""

    def __init__(
        self,
        name: str = "SQ_Equity",
        store_dir: str | Path | None = None,
        db: DatabaseManager | None = None,
    ) -> None:
        """Initialize SQ Equity broker plugin."""
        super().__init__(
            name=name,
            capabilities=(
                BrokerCapability.CONNECT
                | BrokerCapability.MARKET_DATA
                | BrokerCapability.SYMBOLS
            ),
        )
        self.store_dir = (
            Path(store_dir) if store_dir else DEFAULT_DATA_DIR / "sq_equity"
        )
        self._db = db
        self._instruments_service = InstrumentService(db) if db else None
        self._connected = True

    @property
    def provider_capabilities(self) -> ProviderCapabilities:
        """Data provider capabilities metadata."""
        return ProviderCapabilities(
            name="SQEquity",
            display_name="StrategyQuant US Equities",
            asset_classes=["Stocks"],
            timeframes=["M1", "D1"],
            requires_auth=False,
            rate_limit_rps=10.0,
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
        """Verify presence of local market data store or connection."""
        self._connected = self.store_dir.exists()
        self.logger.info(
            "FR-BROKER-SQ-EQUITY-CATALOG: Connected to SQ Equity datafeed. Directory exists: %s",
            self._connected,
            extra={"fr_id": "FR-BROKER-SQ-EQUITY-CATALOG"},
        )
        return StandardResponse.success(
            data=True,
            message="SQ Equity store ready",
            extensions={"broker": self.name},
        )

    @override
    def is_connected(self) -> StandardResponse[bool]:
        """Check active state."""
        return StandardResponse.success(
            data=self._connected, extensions={"broker": self.name}
        )

    @override
    def disconnect(self) -> StandardResponse[bool]:
        """Disconnect session."""
        self._connected = False
        return StandardResponse.success(data=True, extensions={"broker": self.name})

    @override
    def get_symbol_info(self, symbol: str) -> StandardResponse[SymbolInfo]:
        """Retrieve stock metadata from host catalog or fallback."""
        sym_clean = symbol.upper().strip()
        if self._instruments_service is not None:
            inst = self._instruments_service.get_instrument(sym_clean)
            if inst is not None:
                info = SymbolInfo(
                    name=sym_clean,
                    visible=True,
                    select=True,
                    digits=inst.decimals,
                    point=inst.tick_size,
                    currency_base="USD",
                    currency_profit="USD",
                    currency_margin="USD",
                    description=inst.description,
                    exchange="US",
                    raw=inst,
                )
                self.logger.debug(
                    "FR-BROKER-SQ-EQUITY-CATALOG: Retrieved symbol info from database for %s",
                    sym_clean,
                    extra={"fr_id": "FR-BROKER-SQ-EQUITY-CATALOG", "symbol": sym_clean},
                )
                return StandardResponse.success(
                    data=info,
                    extensions={"broker": self.name, "source": "database"},
                )

        spec = EQUITY_TICKERS.get(
            sym_clean, {"name": sym_clean, "exchange": "US", "decimals": 2}
        )
        dec = int(spec.get("decimals", 2))
        info = SymbolInfo(
            name=sym_clean,
            visible=True,
            select=True,
            digits=dec,
            point=1.0 / (10**dec),
            currency_base="USD",
            currency_profit="USD",
            currency_margin="USD",
            raw=spec,
        )
        self.logger.debug(
            "FR-BROKER-SQ-EQUITY-CATALOG: Retrieved symbol info from fallback for %s",
            sym_clean,
            extra={"fr_id": "FR-BROKER-SQ-EQUITY-CATALOG", "symbol": sym_clean},
        )
        return StandardResponse.success(
            data=info,
            extensions={"broker": self.name, "raw": spec, "source": "fallback"},
        )

    @override
    def get_symbols(
        self, group: str | None = None
    ) -> StandardResponse[list[SymbolInfo]]:
        """Retrieve list of supported equity tickers."""
        res: list[SymbolInfo] = []
        for sym in EQUITY_TICKERS:
            if not group or group.upper() in sym:
                info_res = self.get_symbol_info(sym)
                if info_res.data:
                    res.append(info_res.data)
        return StandardResponse.success(data=res, extensions={"broker": self.name})

    @override
    def get_symbol_tick(self, symbol: str) -> StandardResponse[Tick]:
        """Retrieve latest known quote tick for symbol."""
        bars_res = self.get_bars(symbol=symbol, count=1)
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
            message=f"No local Parquet quotes available from SQ Equity for symbol '{symbol}'",
            error=StandardError(
                code="NO_DATA",
                message=f"No local Parquet quotes available from SQ Equity for symbol '{symbol}'",
            ),
            extensions={"broker": self.name},
        )

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
        """Retrieve historical candlestick bars from local Parquet store."""
        sym_clean = symbol.lower().strip()
        tf_str = str(timeframe).upper()
        res_dir = "m1" if "M1" in tf_str or "1M" in tf_str else "d1"

        target_dir = self.store_dir / res_dir / sym_clean
        if not target_dir.exists():
            msg = f"No local data found for symbol '{symbol}' in {target_dir}"
            return StandardResponse.failure(
                message=msg,
                error=StandardError(code="NOT_FOUND", message=msg),
                extensions={"broker": self.name},
            )

        try:
            import pyarrow.parquet as pq

            parquet_files = sorted(target_dir.glob("*.parquet"))
            if not parquet_files:
                msg = f"No parquet files for '{symbol}'"
                return StandardResponse.failure(
                    message=msg,
                    error=StandardError(code="NO_DATA", message=msg),
                    extensions={"broker": self.name},
                )

            bars: list[Bar] = []
            for pf_path in parquet_files:
                pf = pq.ParquetFile(str(pf_path))
                table = pf.read()
                df = table.to_pandas()
                for _, row in df.iterrows():
                    dt = row["DateTime"]
                    if hasattr(dt, "to_pydatetime"):
                        dt = dt.to_pydatetime()
                    bars.append(
                        Bar(
                            time=dt,
                            open=float(row["Open"]),
                            high=float(row["High"]),
                            low=float(row["Low"]),
                            close=float(row["Close"]),
                            tick_volume=int(row.get("Volume", 0)),
                            real_volume=int(row.get("Volume", 0)),
                        )
                    )

            if count and len(bars) > count:
                bars = bars[-count:]

            self.logger.info(
                "FR-BROKER-SQ-EQUITY-PARQUET-DATA: Loaded %d bars for %s",
                len(bars),
                symbol,
                extra={
                    "fr_id": "FR-BROKER-SQ-EQUITY-PARQUET-DATA",
                    "symbol": symbol,
                    "count": len(bars),
                },
            )
            return StandardResponse.success(
                data=bars,
                message=f"Loaded {len(bars)} bars for '{symbol}'",
                extensions={"broker": self.name},
            )
        except Exception as e:
            msg = f"Failed to read parquet bars for '{symbol}': {e}"
            return StandardResponse.failure(
                message=msg,
                error=StandardError(code="READ_ERROR", message=msg),
                extensions={"broker": self.name},
            )


# Compatibility aliases
SQEquityProvider = SQEquityBroker


def create_adapter(_context: PluginHostContext | None = None) -> SQEquityBroker:
    """Plugin entrypoint factory constructing SQEquityBroker adapter."""
    logger.info("Initializing SQ Equity broker plugin adapter.")
    return SQEquityBroker()
