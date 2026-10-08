"""Darwinex institutional market data and authoritative symbol catalog broker plugin.

Description:
    Implements an unauthenticated market data and symbol metadata broker plugin
    for Darwinex (institutional FX, CFD, commodities, indices, and crypto).
    Operating under strict single-responsibility principles, this plugin
    exclusively fetches historical candlestick bars and ticks over HTTP in memory
    from the StrategyQuant CDN (`https://cdn.strategyquantcdn.com/data/darwinex`),
    and dynamically resolves instrument specifications from the authoritative
    catalog at `data/market/darwinex/darwinex.csv` (328 instruments).
    In alignment with the HaruQuantAI broker architecture (mirroring Yahoo Finance
    and Dukascopy), this plugin performs zero data manipulation: no Parquet
    writing, no local filesystem caching, no database management, and no Data
    Manager DTO coupling.
    All non-data and trading methods cleanly reject unsupported execution
    capabilities via BaseBroker defaults.

Purpose:
    FEAT-BROKER-DARWINEX: Darwinex Market Data and Symbol Catalog Provider.
    Provides unauthenticated candlestick and tick extraction from StrategyQuant
    CDN feeds, and dynamic symbol metadata resolution from the 328-instrument
    authoritative catalog.

Key Capabilities:
    - FR-BROKER-DARWINEX-MARKET-DATA: Historical Candlestick Bars and Ticks
      Associated: `[DarwinexBroker.get_bars()]`, `[DarwinexBroker.get_ticks()]`
      Logging: Emits INFO log upon successfully downloading and parsing bars with
      extracted count, and WARNING log on network failure or non-200 HTTP response.
    - FR-BROKER-DARWINEX-SYMBOLS: Authoritative Symbol Catalog Resolution
      Associated: `[DarwinexBroker.get_symbol_info()]`,
      `[DarwinexBroker.get_symbols()]`, `[DarwinexBroker.get_num_of_symbols()]`
      Logging: Emits INFO log upon successfully loading or querying catalog items,
      and WARNING log if symbol is not found in the CSV catalog.

Python API Usage:
    ```python
    from app.plugins.brokers.darwinex import DarwinexBroker, create_adapter

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
import struct
import zipfile
from datetime import UTC, datetime
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
    "id": "broker-darwinex",
    "name": "Darwinex Connector",
    "version": "1.0.0",
    "description": (
        "Darwinex institutional tick and bar market data and symbol catalog broker plugin"
    ),
    "author": "HaruQuantAI",
    "slot": "broker",
    "entrypoint": "create_adapter",
    "dependencies": [],
    "capabilities": ["bars", "ticks", "symbols"],
    "enabled": True,
    "metadata": {
        "provider_name": "Darwinex",
        "display_name": "Darwinex Institutional Feeds",
        "asset_classes": [
            "Forex",
            "CFD",
            "Commodities",
            "Indices",
            "Crypto",
            "Stocks",
        ],
        "timeframes": ["M1", "H1", "D1"],
        "requires_auth": False,
        "rate_limit_rps": 5.0,
        "base_url": "https://cdn.strategyquantcdn.com/data/darwinex",
    },
}

DEFAULT_CATALOG_PATH = (
    Path(__file__).resolve().parents[3]
    / "data"
    / "market"
    / "darwinex"
    / "darwinex.csv"
)

CDN_BASE_URL = "https://cdn.strategyquantcdn.com/data/darwinex"
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)

# SQX InstrumentType mapping: 1 -> Stocks, 3 -> Forex, 4 -> Commodities, 6 -> Indices, 7 -> Crypto
DARWINEX_TYPE_MAP: dict[int, tuple[str, str]] = {
    1: ("Stocks", "Equities"),
    3: ("Forex", "Majors/Minors"),
    4: ("Commodities", "Metals/Energy"),
    6: ("Indices", "Indices"),
    7: ("Crypto", "Cryptocurrency"),
}

INDEX_CURRENCY_MAP: dict[str, str] = {
    "AUS200": "AUD",
    "FCHI": "EUR",
    "GDAXIm": "EUR",
    "NI225": "JPY",
    "UK100": "GBP",
    "SP500": "USD",
    "NAS100": "USD",
    "NDXm": "USD",
    "WS30": "USD",
    "SPN35": "EUR",
    "STOXX50E": "EUR",
}

__all__ = ["DarwinexBroker", "create_adapter"]


class DarwinexBroker(BaseBroker):
    """Darwinex institutional market data and symbol catalog broker plugin."""

    def __init__(
        self,
        name: str = "Darwinex",
        catalog_path: str | Path | None = None,
        session: requests.Session | None = None,
    ) -> None:
        """Initialize Darwinex broker plugin."""
        super().__init__(
            name=name,
            capabilities=BrokerCapability.MARKET_DATA | BrokerCapability.SYMBOLS,
        )
        self.catalog_path = Path(catalog_path) if catalog_path else DEFAULT_CATALOG_PATH

        if session is not None:
            self.session = session
        else:
            self.session = requests.Session()
            retries: Any = Retry(
                total=3,
                backoff_factor=0.3,
                status_forcelist=[500, 502, 503, 504],
                raise_on_status=False,
            )
            adapter = HTTPAdapter(max_retries=retries)
            self.session.mount("https://", adapter)
            self.session.mount("http://", adapter)
            self.session.headers.update({"User-Agent": USER_AGENT})

        self._catalog: dict[str, dict[str, Any]] = {}
        self._catalog_ordered: list[SymbolInfo] = []

    def _ensure_catalog(self) -> None:
        """Load and parse the authoritative Darwinex catalog if not already loaded."""
        if self._catalog:
            return

        if not self.catalog_path.exists():
            self.logger.warning(
                "FR-BROKER-DARWINEX-SYMBOLS: Catalog path %s does not exist",
                self.catalog_path,
                extra={
                    "fr_id": "FR-BROKER-DARWINEX-SYMBOLS",
                    "path": str(self.catalog_path),
                },
            )
            return

        try:
            with open(self.catalog_path, encoding="latin1") as f:
                for raw_line in f:
                    line = raw_line.strip()
                    if not line:
                        continue
                    parts = line.split(";")
                    if len(parts) < 8:
                        continue

                    # Structure: symbol;dateFrom;decimals;tickValue;defaultSpread;tickSize;tickStep;instrumentType
                    sym = parts[0].strip()
                    date_from = parts[1].strip()
                    try:
                        decimals = int(parts[2].strip())
                        tick_value = float(parts[3].strip())
                        default_spread = float(parts[4].strip())
                        tick_size = float(parts[5].strip())
                        tick_step = float(parts[6].strip())
                        inst_type = int(parts[7].strip())
                    except ValueError:
                        continue

                    category, subcategory = DARWINEX_TYPE_MAP.get(
                        inst_type, ("CFD", "General")
                    )

                    # Currency derivation
                    curr_base = ""
                    curr_profit = "USD"
                    if inst_type == 3 and len(sym) == 6:  # Forex
                        curr_base = sym[:3]
                        curr_profit = sym[3:]
                    elif inst_type == 7 or inst_type == 4:  # Crypto or Commodities
                        curr_base = sym[:-3] if len(sym) > 3 else sym
                        curr_profit = sym[-3:] if len(sym) > 3 else "USD"
                    elif inst_type == 6:  # Indices
                        curr_profit = INDEX_CURRENCY_MAP.get(sym, "USD")
                        curr_base = sym
                    else:  # Stocks
                        curr_base = sym
                        curr_profit = "USD"

                    point = tick_size if tick_size > 0 else (10.0**-decimals)
                    contract_size = tick_value if tick_value > 0 else 100000.0

                    info = SymbolInfo(
                        name=sym,
                        digits=decimals,
                        point=point,
                        spread=int(default_spread),
                        trade_tick_value=tick_value,
                        trade_tick_size=tick_size,
                        trade_contract_size=contract_size,
                        volume_step=tick_step if tick_step > 0 else 0.01,
                        category=category,
                        currency_base=curr_base,
                        currency_profit=curr_profit,
                        currency_margin=curr_base or "USD",
                        description=f"Darwinex {sym} ({category}/{subcategory})",
                        path=f"Darwinex\\{category}\\{sym}",
                    )

                    spec = {
                        "symbol": sym,
                        "date_from": date_from,
                        "decimals": decimals,
                        "tick_value": tick_value,
                        "default_spread": default_spread,
                        "tick_size": tick_size,
                        "tick_step": tick_step,
                        "instrument_type": inst_type,
                        "category": category,
                        "subcategory": subcategory,
                        "currency_base": curr_base,
                        "currency_profit": curr_profit,
                        "info": info,
                    }

                    sym_clean = (
                        sym.upper().replace("/", "").replace("_", "").replace("-", "")
                    )
                    self._catalog[sym_clean] = spec
                    self._catalog_ordered.append(info)

            self.logger.info(
                "FR-BROKER-DARWINEX-SYMBOLS: Loaded %d instruments from %s",
                len(self._catalog),
                self.catalog_path.name,
                extra={
                    "fr_id": "FR-BROKER-DARWINEX-SYMBOLS",
                    "count": len(self._catalog),
                },
            )
        except Exception as e:
            self.logger.error(
                "FR-BROKER-DARWINEX-SYMBOLS: Failed to load Darwinex catalog: %s",
                e,
                extra={"fr_id": "FR-BROKER-DARWINEX-SYMBOLS"},
            )

    @override
    def get_symbol_info(self, symbol: str) -> StandardResponse[SymbolInfo]:
        """Query canonical instrument specifications for a Darwinex symbol."""
        self._ensure_catalog()
        sym_clean = symbol.upper().replace("/", "").replace("_", "").replace("-", "")

        spec = self._catalog.get(sym_clean)
        if spec:
            info: SymbolInfo = spec["info"]
            self.logger.info(
                "FR-BROKER-DARWINEX-SYMBOLS: Symbol info resolved for %s",
                sym_clean,
                extra={
                    "fr_id": "FR-BROKER-DARWINEX-SYMBOLS",
                    "symbol": sym_clean,
                },
            )
            return StandardResponse.success(
                data=info,
                message=f"Symbol info retrieved for '{symbol}'",
                extensions={"broker": self.name},
            )

        self.logger.warning(
            "FR-BROKER-DARWINEX-SYMBOLS: Symbol '%s' not found in Darwinex catalog",
            symbol,
            extra={"fr_id": "FR-BROKER-DARWINEX-SYMBOLS", "symbol": symbol},
        )
        msg = f"Symbol '{symbol}' not found in Darwinex catalog"
        return StandardResponse.failure(
            message=msg,
            error=StandardError(
                code="SYMBOL_NOT_FOUND",
                message=msg,
            ),
            extensions={"broker": self.name},
        )

    @override
    def get_symbols(
        self, group: str | None = None
    ) -> StandardResponse[list[SymbolInfo]]:
        """Retrieve list of instruments from the Darwinex catalog."""
        self._ensure_catalog()
        if not group:
            return StandardResponse.success(
                data=list(self._catalog_ordered),
                message=f"Retrieved {len(self._catalog_ordered)} Darwinex symbols",
                extensions={"broker": self.name},
            )

        grp_lower = group.lower()
        filtered = [
            item["info"]
            for item in self._catalog.values()
            if grp_lower in item["category"].lower()
            or grp_lower in item["subcategory"].lower()
        ]
        return StandardResponse.success(
            data=filtered,
            message=f"Retrieved {len(filtered)} symbols for group '{group}'",
            extensions={"broker": self.name},
        )

    @override
    def get_num_of_symbols(self) -> StandardResponse[int]:
        """Return the count of instruments registered in the catalog."""
        self._ensure_catalog()
        count = len(self._catalog)
        self.logger.info(
            "FR-BROKER-DARWINEX-SYMBOLS: Catalog count query returned %d instruments",
            count,
            extra={"fr_id": "FR-BROKER-DARWINEX-SYMBOLS", "count": count},
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
        """Retrieve historical candlestick bars from StrategyQuant CDN in memory."""
        self._ensure_catalog()
        sym_clean = symbol.upper().replace("/", "").replace("_", "").replace("-", "")
        spec = self._catalog.get(sym_clean)
        decimals = spec.get("decimals", 5) if spec else 5

        # Determine target year
        target_year = 2023
        if date_from is not None:
            target_year = date_from.year
        elif date_to is not None:
            target_year = date_to.year

        url = f"{CDN_BASE_URL}/{sym_clean}/{target_year}.zip"
        self.logger.info(
            "FR-BROKER-DARWINEX-MARKET-DATA: Fetching Darwinex CDN bundle: %s",
            url,
            extra={"fr_id": "FR-BROKER-DARWINEX-MARKET-DATA", "url": url},
        )

        try:
            resp = self.session.get(url, timeout=30)
            if resp.status_code != 200:
                self.logger.warning(
                    "FR-BROKER-DARWINEX-MARKET-DATA: CDN request for %s returned HTTP %d",
                    sym_clean,
                    resp.status_code,
                    extra={
                        "fr_id": "FR-BROKER-DARWINEX-MARKET-DATA",
                        "status": resp.status_code,
                    },
                )
                msg = f"No bars available for '{sym_clean}' from Darwinex CDN (HTTP {resp.status_code})"
                return StandardResponse.failure(
                    message=msg,
                    error=StandardError(
                        code="NO_DATA",
                        message=msg,
                    ),
                    extensions={"broker": self.name},
                )

            bars: list[Bar] = []
            scale = 10.0 ** (decimals + 1)

            with zipfile.ZipFile(io.BytesIO(resp.content)) as z:
                dat_names = sorted([n for n in z.namelist() if n.endswith(".dat")])
                for name in dat_names:
                    # Filter daily files by date if specified
                    # Expected format: YYYY_MM_DD.dat
                    base_name = name.split(".")[0]
                    parts = base_name.split("_")
                    if len(parts) == 3:
                        try:
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
                                23,
                                59,
                                59,
                                tzinfo=UTC,
                            ):
                                continue
                        except ValueError:
                            pass

                    dat_bytes = z.read(name)
                    idx = dat_bytes.find(b"\xbb\xbb")
                    if idx == -1:
                        continue

                    offset = idx + 2
                    if len(dat_bytes) < offset + 48:
                        continue

                    # Unpack base record: base_ts, ask_raw, bid_raw
                    base_ts, ask_raw, bid_raw = struct.unpack(
                        ">qqq", dat_bytes[offset : offset + 24]
                    )
                    ask_price = ask_raw / scale
                    bid_price = bid_raw / scale
                    bar_dt = datetime.fromtimestamp(base_ts / 1000.0, tz=UTC)

                    bars.append(
                        Bar(
                            time=bar_dt,
                            open=bid_price,
                            high=max(bid_price, ask_price),
                            low=min(bid_price, ask_price),
                            close=bid_price,
                            tick_volume=1,
                        )
                    )

            if not bars:
                msg = f"No valid bar records found for '{sym_clean}' in CDN archive"
                return StandardResponse.failure(
                    message=msg,
                    error=StandardError(
                        code="NO_DATA",
                        message=msg,
                    ),
                    extensions={"broker": self.name},
                )

            bars.sort(key=lambda b: b.time)

            # Apply slicing
            sp = start_pos or 0
            if sp > 0:
                bars = bars[sp:]
            if count is not None and count > 0:
                bars = bars[-count:]

            self.logger.info(
                "FR-BROKER-DARWINEX-MARKET-DATA: Extracted %d bars for %s from CDN",
                len(bars),
                sym_clean,
                extra={
                    "fr_id": "FR-BROKER-DARWINEX-MARKET-DATA",
                    "symbol": sym_clean,
                    "count": len(bars),
                },
            )

            return StandardResponse.success(
                data=bars,
                message=f"Retrieved {len(bars)} bars for '{sym_clean}' from Darwinex CDN",
                extensions={"broker": self.name, "source": "cdn"},
            )

        except Exception as e:
            self.logger.error(
                "FR-BROKER-DARWINEX-MARKET-DATA: Error reading Darwinex CDN archive: %s",
                e,
                extra={"fr_id": "FR-BROKER-DARWINEX-MARKET-DATA"},
            )
            msg = f"Failed to fetch or parse Darwinex CDN bars: {e}"
            return StandardResponse.failure(
                message=msg,
                error=StandardError(
                    code="FETCH_ERROR",
                    message=msg,
                ),
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
        """Retrieve historical ticks from Darwinex in memory."""
        sym_clean = symbol.upper().replace("/", "").replace("_", "").replace("-", "")

        bars_resp = self.get_bars(
            symbol=sym_clean,
            count=count,
            date_from=date_from,
            date_to=date_to,
        )

        if bars_resp.is_success and bars_resp.data:
            ticks = [
                Tick(
                    time=b.time,
                    bid=b.close,
                    ask=b.high,
                    last=b.close,
                    volume=float(b.tick_volume),
                )
                for b in bars_resp.data
            ]
            self.logger.info(
                "FR-BROKER-DARWINEX-MARKET-DATA: Extracted %d ticks for %s",
                len(ticks),
                sym_clean,
                extra={
                    "fr_id": "FR-BROKER-DARWINEX-MARKET-DATA",
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
            message=bars_resp.message,
            extensions={"broker": self.name},
        )


def create_adapter(_context: PluginHostContext | None = None) -> DarwinexBroker:
    """Plugin entrypoint factory constructing DarwinexBroker adapter."""
    logger.info("Initializing Darwinex broker plugin adapter.")
    return DarwinexBroker()


if __name__ == "__main__":
    from app.plugins.brokers import get_bars, get_symbol_info

    darwinex = create_adapter()
    print("\n[4] DARWINEX:")
    dw_info = get_symbol_info(broker=darwinex, symbol="EURUSD")
    print(
        f"    Symbol Info: {dw_info.data.description if dw_info.data else 'None'}, "
        f"digits={dw_info.data.digits if dw_info.data else 'None'}"
    )
    assert dw_info.is_success
    assert dw_info.data is not None
    assert dw_info.data.digits == 5

    dw_num = darwinex.get_num_of_symbols()
    print(f"    Catalog Symbols: {dw_num.data}")
    assert dw_num.is_success
    assert dw_num.data == 328

    dw_bars = get_bars(broker=darwinex, symbol="EURUSD", count=5)
    print(
        f"    CDN Bars: count={len(dw_bars.data) if dw_bars.data else 0} "
        f"(success={dw_bars.is_success})"
    )
    assert dw_bars.is_success
    assert dw_bars.data is not None
    assert len(dw_bars.data) == 5
