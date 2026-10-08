"""StrategyQuant US Equity market data and symbol catalog broker plugin.

Description:
    Implements a specialized market data broker plugin accessing StrategyQuant
    US Equities historical candlestick archives stored under `data/market/sq_equity`.
    Within HaruQuantAI, this module provides decoupled, fast in-memory access
    to normalized US equity and benchmark ETF datasets (e.g. AAPL, MSFT, TSLA,
    NVDA, SPY, QQQ) and exposes canonical instrument metadata (`get_symbol_info()`,
    `get_symbols()`, `get_num_of_symbols()`) alongside `get_bars()`.
    All non-download and trading methods cleanly fallback to BaseBroker default
    unsupported capability handling.

Purpose:
    FEAT-BROKER-SQ-EQUITY: StrategyQuant US Equity Market Data and Catalog Broker.
    Provides fast historical equity bar extraction and dynamic symbol metadata
    queries from local datasets without database coupling or disk mutations.

Key Capabilities:
    - FR-BROKER-SQ-EQUITY-SYMBOLS: US Equity Symbol Catalog Resolution
      Associated: `[SQEquityBroker.get_symbol_info()]`, `[SQEquityBroker.get_symbols()]`
      Logging: Emits INFO log upon resolving symbol info or catalog count,
      and WARNING log if symbol is not found.
    - FR-BROKER-SQ-EQUITY-MARKET-DATA: Historical Bar Ingestion
      Associated: `[SQEquityBroker.get_bars()]`
      Logging: Emits INFO log upon successfully parsing Parquet partitions,
      and WARNING log if files are missing or empty.

Python API Usage:
    ```python
    from app.plugins.brokers.sq_equity import SQEquityBroker, create_adapter

    broker = create_adapter()
    info_resp = broker.get_symbol_info("AAPL")
    if info_resp.is_success and info_resp.data:
        print(info_resp.data.description, info_resp.data.digits)

    bars_resp = broker.get_bars("AAPL", count=5)
    if bars_resp.is_success and bars_resp.data:
        assert len(bars_resp.data) > 0
    ```

CLI Usage:
    ```bash
    uv run python -m app.plugins.brokers.sq_equity
    ```
"""

from __future__ import annotations

import csv
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, override

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
    "id": "broker-sq-equity",
    "name": "StrategyQuant US Equities Connector",
    "version": "1.0.0",
    "description": (
        "StrategyQuant US Equities historical market data and symbol catalog broker plugin"
    ),
    "author": "HaruQuantAI",
    "slot": "broker",
    "entrypoint": "create_adapter",
    "dependencies": [],
    "capabilities": ["bars", "symbols"],
    "enabled": True,
    "metadata": {
        "provider_name": "SQEquity",
        "display_name": "StrategyQuant US Equities",
        "asset_classes": ["Stocks", "ETFs"],
        "timeframes": ["M1", "D1"],
        "requires_auth": False,
        "rate_limit_rps": 10.0,
    },
}

DEFAULT_DATA_DIR = Path(__file__).resolve().parents[3] / "data" / "market" / "sq_equity"
DEFAULT_CATALOG_PATH = DEFAULT_DATA_DIR / "sq_equity.csv"

__all__ = ["SQEquityBroker", "create_adapter"]


def _clean_symbol(symbol: str) -> str:
    """Normalize symbol string stripping suffix artifacts like .D or _limited."""
    s = symbol.strip().upper()
    s = s.removesuffix(".D")
    s = s.removesuffix("_LIMITED")
    return s.removesuffix("_BENCHMARK")


class SQEquityBroker(BaseBroker):
    """StrategyQuant US Equity market data and symbol catalog plugin."""

    def __init__(
        self,
        name: str = "SQ_Equity",
        data_dir: str | Path | None = None,
        catalog_path: str | Path | None = None,
    ) -> None:
        """Initialize SQ Equity broker plugin."""
        super().__init__(
            name=name,
            capabilities=(BrokerCapability.MARKET_DATA | BrokerCapability.SYMBOLS),
        )
        self.data_dir = Path(data_dir) if data_dir else DEFAULT_DATA_DIR
        self.catalog_path = Path(catalog_path) if catalog_path else DEFAULT_CATALOG_PATH
        self._catalog: dict[str, dict[str, Any]] = {}
        self._catalog_ordered: list[SymbolInfo] = []

    def _ensure_catalog(self) -> None:
        """Load and cache the SQ Equity instrument catalog.

        Raises:
            FileNotFoundError: If the catalog CSV file does not exist.
            ValueError: If the catalog CSV contains no valid instruments.
        """
        if self._catalog:
            return

        if not self.catalog_path.is_file():
            self.logger.error(
                "FR-BROKER-SQ-EQUITY-SYMBOLS: StrategyQuant US Equity catalog CSV not found: %s",
                self.catalog_path,
                extra={
                    "fr_id": "FR-BROKER-SQ-EQUITY-SYMBOLS",
                    "catalog_path": str(self.catalog_path),
                },
            )
            raise FileNotFoundError(
                f"StrategyQuant US Equity catalog not found: {self.catalog_path}"
            )

        catalog: dict[str, dict[str, Any]] = {}
        ordered: list[SymbolInfo] = []

        try:
            with open(self.catalog_path, encoding="utf-8") as f:
                reader = csv.DictReader(f, delimiter=";")
                for row in reader:
                    sym = (row.get("symbol") or "").strip().upper()
                    if not sym:
                        continue
                    clean_sym = _clean_symbol(sym)
                    name = (row.get("name") or clean_sym).strip()
                    exchange = (row.get("exchange") or "NASDAQ").strip()
                    cat = (row.get("category") or "Stocks").strip()
                    sec_type = (row.get("type") or "Common Stock").strip()
                    dec = int(row.get("decimals") or 2)
                    pt = float(row.get("point") or 0.01)
                    spread = int(float(row.get("spread") or 0))
                    c_size = float(row.get("contract_size") or 1.0)

                    info = SymbolInfo(
                        name=clean_sym,
                        custom=False,
                        digits=dec,
                        point=pt,
                        spread=spread,
                        currency_base="USD",
                        currency_profit="USD",
                        description=f"{name} ({exchange})",
                        category=cat,
                        path=f"US Equities/{cat}/{exchange}",
                        trade_contract_size=c_size,
                        trade_tick_size=pt,
                        trade_tick_value=pt,
                        raw={
                            "symbol": sym,
                            "name": name,
                            "exchange": exchange,
                            "category": cat,
                            "type": sec_type,
                            "date_from": row.get("date_from", ""),
                        },
                    )
                    spec = {
                        "symbol": clean_sym,
                        "name": name,
                        "exchange": exchange,
                        "category": cat,
                        "type": sec_type,
                        "decimals": dec,
                        "point": pt,
                        "spread": spread,
                        "contract_size": c_size,
                        "info": info,
                    }
                    if clean_sym not in catalog:
                        catalog[clean_sym] = spec
                        ordered.append(info)
                    catalog[sym] = spec

            if not catalog:
                self.logger.error(
                    "FR-BROKER-SQ-EQUITY-SYMBOLS: Catalog at %s contains no valid instruments",
                    self.catalog_path,
                    extra={
                        "fr_id": "FR-BROKER-SQ-EQUITY-SYMBOLS",
                        "catalog_path": str(self.catalog_path),
                    },
                )
                raise ValueError(
                    f"StrategyQuant US Equity catalog at {self.catalog_path} is empty or contains no valid instruments"
                )

            self.logger.info(
                "FR-BROKER-SQ-EQUITY-SYMBOLS: Loaded %d instruments from %s",
                len(ordered),
                self.catalog_path.name,
                extra={
                    "fr_id": "FR-BROKER-SQ-EQUITY-SYMBOLS",
                    "count": len(ordered),
                },
            )
        except Exception as exc:
            if not isinstance(exc, ValueError):
                self.logger.error(
                    "FR-BROKER-SQ-EQUITY-SYMBOLS: Error reading catalog CSV %s: %s",
                    self.catalog_path,
                    exc,
                    extra={
                        "fr_id": "FR-BROKER-SQ-EQUITY-SYMBOLS",
                        "error": str(exc),
                    },
                )
            raise

        self._catalog = catalog
        self._catalog_ordered = ordered

    @override
    def get_symbol_info(self, symbol: str) -> StandardResponse[SymbolInfo]:
        """Query canonical instrument specifications for an SQ Equity symbol."""
        self._ensure_catalog()
        sym_raw = symbol.strip().upper()
        sym_clean = _clean_symbol(sym_raw)

        spec = self._catalog.get(sym_raw) or self._catalog.get(sym_clean)
        if spec:
            info: SymbolInfo = spec["info"]
            self.logger.info(
                "FR-BROKER-SQ-EQUITY-SYMBOLS: Resolved symbol info for %s",
                sym_clean,
                extra={"fr_id": "FR-BROKER-SQ-EQUITY-SYMBOLS", "symbol": sym_clean},
            )
            return StandardResponse.success(
                data=info,
                message=f"Symbol info retrieved for '{symbol}'",
                extensions={"broker": self.name},
            )

        self.logger.warning(
            "FR-BROKER-SQ-EQUITY-SYMBOLS: Symbol '%s' not found in catalog",
            symbol,
            extra={"fr_id": "FR-BROKER-SQ-EQUITY-SYMBOLS", "symbol": symbol},
        )
        msg = f"Symbol '{symbol}' not found in StrategyQuant US Equity catalog"
        return StandardResponse.failure(
            message=msg,
            error=StandardError(code="SYMBOL_NOT_FOUND", message=msg),
            extensions={"broker": self.name},
        )

    @override
    def get_symbols(
        self, group: str | None = None
    ) -> StandardResponse[list[SymbolInfo]]:
        """Retrieve registered SQ Equity instruments, optionally filtered by group."""
        self._ensure_catalog()
        if not group:
            return StandardResponse.success(
                data=list(self._catalog_ordered),
                message=f"Retrieved {len(self._catalog_ordered)} SQ Equity symbols",
                extensions={"broker": self.name},
            )

        grp_lower = group.lower().strip()
        filtered = [
            item["info"]
            for item in self._catalog.values()
            if grp_lower in item["category"].lower()
            or grp_lower in item["exchange"].lower()
            or grp_lower in item["type"].lower()
        ]
        # Deduplicate while preserving order
        seen: set[str] = set()
        deduped: list[SymbolInfo] = []
        for s in filtered:
            if s.name not in seen:
                seen.add(s.name)
                deduped.append(s)

        return StandardResponse.success(
            data=deduped,
            message=f"Retrieved {len(deduped)} symbols matching group '{group}'",
            extensions={"broker": self.name},
        )

    @override
    def get_num_of_symbols(self) -> StandardResponse[int]:
        """Return the count of distinct instruments registered in the catalog."""
        self._ensure_catalog()
        count = len(self._catalog_ordered)
        self.logger.info(
            "FR-BROKER-SQ-EQUITY-SYMBOLS: Catalog count query returned %d instruments",
            count,
            extra={"fr_id": "FR-BROKER-SQ-EQUITY-SYMBOLS", "count": count},
        )
        return StandardResponse.success(data=count, extensions={"broker": self.name})

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
        """Retrieve historical candlestick bars from local partitioned Parquet store."""
        sym_clean = _clean_symbol(symbol).lower()
        tf_str = str(timeframe).upper()
        res_dir = "m1" if "M1" in tf_str or "1M" in tf_str else "d1"

        target_dir = self.data_dir / res_dir / sym_clean
        if not target_dir.exists():
            # Check fallback to d1 if requested m1 partition does not exist
            fallback_dir = self.data_dir / "d1" / sym_clean
            if fallback_dir.exists():
                target_dir = fallback_dir
            else:
                msg = (
                    f"No local equity data found for symbol '{symbol}' in {target_dir}"
                )
                return StandardResponse.failure(
                    message=msg,
                    error=StandardError(code="NOT_FOUND", message=msg),
                    extensions={"broker": self.name},
                )

        try:
            import pyarrow.parquet as pq

            parquet_files = sorted(target_dir.glob("*.parquet"))
            if not parquet_files:
                msg = f"No parquet partitions found for '{symbol}' in {target_dir}"
                return StandardResponse.failure(
                    message=msg,
                    error=StandardError(code="NO_DATA", message=msg),
                    extensions={"broker": self.name},
                )

            bars: list[Bar] = []
            for pf_path in parquet_files:
                pf = pq.ParquetFile(str(pf_path))
                table = pf.read()
                data_dict = table.to_pydict()
                dts = data_dict.get("DateTime", [])
                opens = data_dict.get("Open", [])
                highs = data_dict.get("High", [])
                lows = data_dict.get("Low", [])
                closes = data_dict.get("Close", [])
                vols = data_dict.get("Volume", [])

                for i in range(len(dts)):
                    dt = dts[i]
                    if hasattr(dt, "to_pydatetime"):
                        dt = dt.to_pydatetime()

                    # Apply date filters
                    if date_from and dt < date_from:
                        continue
                    if date_to and dt > date_to:
                        continue

                    bars.append(
                        Bar(
                            time=dt,
                            open=float(opens[i]),
                            high=float(highs[i]),
                            low=float(lows[i]),
                            close=float(closes[i]),
                            tick_volume=int(vols[i] if i < len(vols) else 0),
                            real_volume=int(vols[i] if i < len(vols) else 0),
                        )
                    )

            if start_pos and start_pos > 0 and len(bars) > start_pos:
                bars = bars[start_pos:]

            if count and count > 0 and len(bars) > count:
                bars = bars[-count:]

            self.logger.info(
                "FR-BROKER-SQ-EQUITY-MARKET-DATA: Loaded %d bars for %s",
                len(bars),
                symbol,
                extra={
                    "fr_id": "FR-BROKER-SQ-EQUITY-MARKET-DATA",
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

    @override
    def get_ticks(
        self,
        symbol: str,
        count: int | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        flags: int | None = None,
    ) -> StandardResponse[list[Tick]]:
        """Return unsupported capability response as SQ Equity does not store tick archives."""
        msg = f"Tick data is not supported by {self.name}"
        return StandardResponse.failure(
            message=msg,
            error=StandardError(code="UNSUPPORTED_CAPABILITY", message=msg),
            extensions={"broker": self.name},
        )


def create_adapter(_context: PluginHostContext | None = None) -> SQEquityBroker:
    """Plugin entrypoint factory constructing SQEquityBroker adapter."""
    logger.info("Initializing SQ Equity broker plugin adapter.")
    return SQEquityBroker()


if __name__ == "__main__":
    print("=" * 60)
    print("SQ Equity Broker Plugin Self-Test")
    print("=" * 60)

    broker = create_adapter()

    # 1. Test symbol info query
    info_resp = broker.get_symbol_info("AAPL")
    print(
        f"[1] Symbol Info AAPL: success={info_resp.is_success}, "
        f"description='{info_resp.data.description if info_resp.data else None}'"
    )
    assert info_resp.is_success, f"AAPL symbol info failed: {info_resp.message}"
    assert info_resp.data is not None
    assert info_resp.data.name == "AAPL"

    # 2. Test total count
    count_resp = broker.get_num_of_symbols()
    print(f"[2] Total Symbols: {count_resp.data}")
    assert count_resp.is_success
    assert count_resp.data is not None
    assert count_resp.data >= 10

    # 3. Test symbols listing
    syms_resp = broker.get_symbols(group="ETFs")
    print(f"[3] ETFs Symbols count: {len(syms_resp.data) if syms_resp.data else 0}")
    assert syms_resp.is_success
    assert syms_resp.data is not None
    assert len(syms_resp.data) > 0

    # 4. Test historical bars
    bars_resp = broker.get_bars("AAPL", count=5)
    print(
        f"[4] Parquet Bars AAPL: success={bars_resp.is_success}, "
        f"count={len(bars_resp.data) if bars_resp.data else 0}"
    )
    assert bars_resp.is_success, f"Bars retrieval failed: {bars_resp.message}"
    assert bars_resp.data is not None
    assert len(bars_resp.data) == 5

    # 5. Test trading rejection
    from app.plugins.brokers.contracts import TradeRequest

    trade_resp = broker.trade(TradeRequest(symbol="AAPL", volume=1.0))
    print(
        f"[5] Trade Rejection: success={trade_resp.is_success}, "
        f"message='{trade_resp.message}'"
    )
    assert not trade_resp.is_success
    assert "doesn't have trading capabilities" in trade_resp.message

    print("=" * 60)
    print("ALL SQ EQUITY SELF-TESTS PASSED!")
    print("=" * 60)
    sys.exit(0)
