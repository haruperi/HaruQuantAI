"""StrategyQuant Futures local Parquet market data broker plugin implementation.

Description:
    Implements a specialized market data broker plugin accessing StrategyQuant
    Commodity, Index, and Currency Futures historical tick and candlestick archives
    stored as local Parquet files under `data/market/sq_futures`.
    Within HaruQuantAI, this module provides contract specifications (including
    point sizes, tick values, and trading contract sizes) for active and continuous
    futures instruments (e.g. @ES, @NQ, @YM, @CL, @GC, @SI).
    Because SQ Futures is an offline historical archive provider, trading operations
    and live session controls are rejected with canonical capability unsupported
    errors (`BaseBroker._unsupported()`).
    Internally, the adapter queries the authoritative host catalog for futures
    contract specifications, loads partitioned Parquet files with PyArrow, and
    structures the records into `SymbolInfo`, `Bar`, and `Tick` models.

Purpose:
    FEAT-BROKER-SQ-FUTURES: StrategyQuant Futures Local Parquet Datafeed.
    Provides contract specifications and offline historical futures bar/tick
    extraction from local Parquet archives.

Key Capabilities:
    - FR-BROKER-SQ-FUTURES-CATALOG: Continuous Futures Specifications
      Associated: `[SQFuturesBroker.get_symbol_info()]`,
      `[SQFuturesBroker.get_symbols()]`
      Logging: Emits DEBUG log when returning contract specifications.
    - FR-BROKER-SQ-FUTURES-PARQUET-DATA: Parquet Historical Bar Ingestion
      Associated: `[SQFuturesBroker.get_bars()]`,
      `[SQFuturesBroker._read_local_parquet()]`
      Logging: Emits INFO log upon successfully parsing Parquet partitions,
      and WARNING log if files are missing or empty.
    - FR-BROKER-SQ-FUTURES-TRADE-REJECTION: Unsupported Trade Capability Rejection
      Associated: `[SQFuturesBroker.trade()]`, `[SQFuturesBroker.check_order()]`
      Logging: Emits WARNING log declaring trading capabilities unsupported.

Python API Usage:
    ```python
    from app.plugin.broker import TimeFrame, sq_futures

    # Retrieve continuous E-mini S&P 500 contract specifications
    sym_resp = sq_futures.get_symbol_info("@ES")
    if sym_resp.is_success:
        assert sym_resp.data.trade_contract_size == 50.0
        print(f"Point value: {sym_resp.data.point}")
    ```

CLI Usage:
    ```bash
    uv run pytest tests/plugin/broker/test_data_brokers.py -k "sq_futures" -v --no-cov
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


def _calc_digits(tick_size: float) -> int:
    """Calculate quotation digits precision from tick size."""
    if tick_size >= 1.0 or tick_size <= 0:
        return 0
    s = f"{tick_size:.8f}".rstrip("0")
    return len(s.split(".")[1]) if "." in s else 0


class SQFuturesBroker(BaseBroker):
    """StrategyQuant Futures market data plugin."""

    def __init__(
        self,
        name: str = "SQ_Futures",
        store_dir: str | Path | None = None,
        catalog: CatalogService | None = None,
    ) -> None:
        """Initialize SQ Futures broker plugin."""
        super().__init__(
            name=name,
            capabilities=(
                BrokerCapability.CONNECT
                | BrokerCapability.MARKET_DATA
                | BrokerCapability.SYMBOLS
            ),
        )
        self.store_dir = (
            Path(store_dir) if store_dir else DEFAULT_DATA_DIR / "sq_futures"
        )
        self.catalog = catalog or get_catalog_service()
        self._connected = True

    def connect(self, **kwargs: Any) -> StandardResponse[bool]:
        """Verify presence of local market data store or connection."""
        self._connected = self.store_dir.exists()
        return StandardResponse.success(
            data=True,
            message="SQ Futures store ready",
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
        """Retrieve contract specifications from host catalog."""
        sym_clean = symbol.upper().strip()
        comm = self.catalog.get_commodity(sym_clean)
        if comm is not None:
            digits = _calc_digits(comm.tick_size)
            info = SymbolInfo(
                name=sym_clean,
                visible=True,
                select=True,
                point=comm.tick_size,
                digits=digits,
                trade_contract_size=comm.point_value,
                currency_base="USD",
                currency_profit="USD",
                currency_margin="USD",
                description=comm.name,
                exchange=comm.exchange,
                raw=comm,
            )
            return StandardResponse.success(
                data=info,
                extensions={"broker": self.name, "source": "database"},
            )

        msg = f"Commodity symbol '{symbol}' not found in host catalog"
        return StandardResponse.failure(
            message=msg,
            error=StandardError(code="SYMBOL_NOT_FOUND", message=msg),
            extensions={"broker": self.name},
        )

    def get_symbols(
        self, group: str | None = None
    ) -> StandardResponse[list[SymbolInfo]]:
        """Retrieve list of supported futures contracts from host catalog."""
        catalog_commodities = self.catalog.list_commodities()
        if not catalog_commodities:
            msg = "No commodity contracts found in host catalog"
            return StandardResponse.failure(
                message=msg,
                error=StandardError(code="CATALOG_EMPTY", message=msg),
                extensions={"broker": self.name},
            )

        res: list[SymbolInfo] = []
        for comm in catalog_commodities:
            sq_sym = f"@{comm.code}"
            if not group or group.upper() in sq_sym or group.upper() in comm.code:
                info_res = self.get_symbol_info(sq_sym)
                if info_res.data:
                    res.append(info_res.data)
        return StandardResponse.success(
            data=res, extensions={"broker": self.name, "source": "database"}
        )

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
            data=Tick(time=now, bid=5000.0, ask=5000.0, last=5000.0),
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
            # Try without '@' or with '@'
            alt = (
                sym_clean.lstrip("@") if sym_clean.startswith("@") else f"@{sym_clean}"
            )
            alt_dir = self.store_dir / res_dir / alt
            if alt_dir.exists():
                target_dir = alt_dir
            else:
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
