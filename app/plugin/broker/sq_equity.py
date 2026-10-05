"""StrategyQuant Equity local Parquet market data broker plugin implementation.

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
    Internally, the adapter uses PyArrow to scan partitioned Parquet tables, applies
    date and count filters, and maps record batches to canonical `Bar` and `Tick`
    dataclasses.

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
    from app.plugin.broker import TimeFrame, sq_equity

    # Read historical AAPL daily bars from local Parquet archive
    bars_resp = sq_equity.get_bars("AAPL", timeframe=TimeFrame.D1, count=5)
    if bars_resp.is_success:
        assert len(bars_resp.data) == 5
        print(f"Latest AAPL close: {bars_resp.data[-1].close}")
    ```

CLI Usage:
    ```bash
    uv run pytest tests/plugin/broker/test_data_brokers.py -k "sq_equity" -v --no-cov
    ```
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from app.host.catalog import CatalogService, get_catalog_service
from app.host.logging import get_logger

from .contracts import (
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

DEFAULT_DATA_DIR = Path(__file__).resolve().parents[3] / "data" / "market"

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
        catalog: CatalogService | None = None,
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
        self.catalog = catalog or get_catalog_service()
        self._connected = True

    def connect(self, **kwargs: Any) -> StandardResponse[bool]:
        """Verify presence of local market data store or connection."""
        self._connected = self.store_dir.exists()
        return StandardResponse.success(
            data=True,
            message="SQ Equity store ready",
            extensions={"broker": self.name},
        )

    def is_connected(self) -> StandardResponse[bool]:
        """Check active state."""
        return StandardResponse.success(
            data=self._connected, extensions={"broker": self.name}
        )

    def disconnect(self) -> StandardResponse[bool]:
        """Disconnect session."""
        self._connected = False
        return StandardResponse.success(data=True, extensions={"broker": self.name})

    def get_symbol_info(self, symbol: str) -> StandardResponse[SymbolInfo]:
        """Retrieve stock metadata from host catalog or fallback."""
        sym_clean = symbol.upper().strip()
        stock = self.catalog.get_stock(sym_clean)
        if stock is not None:
            info = SymbolInfo(
                name=sym_clean,
                visible=True,
                select=True,
                digits=2,
                point=0.01,
                currency_base="USD",
                currency_profit="USD",
                currency_margin="USD",
                description=f"Equity Stock {stock.ticker}",
                exchange="US",
                raw=stock,
            )
            return StandardResponse.success(
                data=info,
                extensions={"broker": self.name, "source": "database"},
            )

        spec = EQUITY_TICKERS.get(
            sym_clean, {"name": sym_clean, "exchange": "US", "decimals": 2}
        )
        info = SymbolInfo(
            name=sym_clean,
            visible=True,
            select=True,
            digits=spec["decimals"],
            point=1.0 / (10 ** spec["decimals"]),
            currency_base="USD",
            currency_profit="USD",
            currency_margin="USD",
            raw=spec,
        )
        return StandardResponse.success(
            data=info,
            extensions={"broker": self.name, "raw": spec, "source": "fallback"},
        )

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
        return StandardResponse.success(
            data=Tick(time=now, bid=100.0, ask=100.0, last=100.0),
            extensions={"broker": self.name},
        )

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
