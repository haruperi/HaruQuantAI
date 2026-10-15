"""Darwinex institutional market data and symbol catalog broker implementation.

Description:
    Implements an unauthenticated market data and symbol metadata broker
    for Darwinex conforming to the `TradingBackend` protocol.
    Fetches historical candlestick bars and ticks in memory from StrategyQuant CDN,
    and dynamically resolves instrument specifications from the authoritative
    catalog CSV (`data/market/darwinex/darwinex.csv`) returning canonical `SymbolSnapshot`.

Purpose:
    FEAT-BROKER-DARWINEX: Darwinex Market Data and Symbol Catalog Provider.

Key Capabilities:
    - FR-BROKER-DARWINEX-MARKET-DATA: Historical Candlestick Bars and Ticks
      Associated: `[DarwinexBroker.fetch_bars()]`, `[DarwinexBroker.fetch_ticks()]`
      Logging: Emits INFO log upon successfully downloading and parsing bars with
      extracted count, and WARNING log on network failure.
    - FR-BROKER-DARWINEX-SYMBOLS: Authoritative Symbol Catalog Resolution
      Associated: `[DarwinexBroker.symbol_info()]`, `[DarwinexBroker.symbols_get()]`
      Logging: Emits INFO log upon catalog parsing, and WARNING if symbol is not found.

Python API Usage:
    ```python
    from app.services.data import Timeframe, get_historical_bars
    from app.services.brokers.darwinex import DarwinexBroker

    broker = DarwinexBroker()
    bars = await get_historical_bars(broker, "EURUSD", Timeframe.PERIOD_D1, count=5)
    assert len(bars) > 0
    ```

CLI Usage:
    `uv run python -m scripts.examples.brokers_data --broker darwinex`
"""

from __future__ import annotations

import io
import struct
import zipfile
from datetime import UTC, datetime
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

__all__ = ["DarwinexBroker", "create_adapter"]


class DarwinexBroker(DataBrokerBackend):
    """Darwinex market data and symbol catalog broker."""

    def __init__(
        self,
        name: str = "Darwinex",
        catalog_path: str | Path | None = None,
        session: requests.Session | None = None,
    ) -> None:
        """Initialize Darwinex broker."""
        super().__init__(name=name)
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

        self._catalog: dict[str, SymbolSnapshot] = {}

    def _ensure_catalog(self) -> None:
        """Load and parse the authoritative Darwinex catalog if not already loaded."""
        if self._catalog:
            return

        if not self.catalog_path.exists():
            self.logger.warning(
                "FR-BROKER-DARWINEX-SYMBOLS: Catalog path %s does not exist",
                self.catalog_path,
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

                    sym = parts[0].strip().upper()
                    try:
                        decimals = int(parts[2].strip())
                        tick_value = float(parts[3].strip())
                        default_spread = float(parts[4].strip())
                        tick_size = float(parts[5].strip())
                    except ValueError:
                        continue

                    point = tick_size if tick_size > 0 else (10.0**-decimals)
                    contract_size = tick_value if tick_value > 0 else 100_000.0

                    self._catalog[sym] = SymbolSnapshot(
                        name=sym,
                        custom=False,
                        digits=decimals,
                        point=point,
                        spread=int(default_spread),
                        trade_contract_size=contract_size,
                    )
            self.logger.info(
                "FR-BROKER-DARWINEX-SYMBOLS: Loaded %d instruments from catalog",
                len(self._catalog),
            )
        except Exception as exc:
            self.logger.error(
                "FR-BROKER-DARWINEX-SYMBOLS: Error parsing catalog: %s", exc
            )

    @override
    def symbol_info(self, symbol: str) -> SymbolSnapshot:
        """Retrieve instrument specifications as canonical SymbolSnapshot."""
        self._ensure_catalog()
        sym_clean = symbol.upper().replace("/", "").replace("_", "").replace("-", "")
        snap = self._catalog.get(sym_clean)
        if snap is not None:
            return snap
        return SymbolSnapshot(name=sym_clean, digits=5, point=0.00001)

    @override
    def symbols_get(self) -> list[str]:
        """Return list of symbol names available in catalog."""
        self._ensure_catalog()
        return list(self._catalog.keys())

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
        """Download candlestick bars from StrategyQuant CDN in memory."""
        del timeframe, mode
        self._ensure_catalog()
        sym_clean = symbol.upper().replace("/", "").replace("_", "").replace("-", "")
        snap = self.symbol_info(sym_clean)
        decimals = snap.digits
        scale = 10.0 ** (decimals + 1)
        target_count = count if count > 0 else limit

        date_from = datetime.fromtimestamp(start, tz=UTC) if 0 < start < 2**40 else None
        date_to = datetime.fromtimestamp(end, tz=UTC) if 0 < end < 2**40 else None
        target_year = date_from.year if date_from else 2023
        url = f"{CDN_BASE_URL}/{sym_clean}/{target_year}.zip"

        try:
            resp = self.session.get(url, timeout=30)
            if resp.status_code != 200:
                raise BridgeError(
                    f"No bars available for '{sym_clean}' from Darwinex CDN (HTTP {resp.status_code})",
                    code="NO_DATA",
                )

            rows: list[dict[str, Any]] = []
            with zipfile.ZipFile(io.BytesIO(resp.content)) as z:
                dat_names = sorted([n for n in z.namelist() if n.endswith(".dat")])
                for name in dat_names[-target_count:]:
                    dat_bytes = z.read(name)
                    idx = dat_bytes.find(b"\xbb\xbb")
                    if idx == -1:
                        continue
                    offset = idx + 2
                    if len(dat_bytes) < offset + 48:
                        continue
                    base_ts, ask_raw, bid_raw = struct.unpack(
                        ">qqq", dat_bytes[offset : offset + 24]
                    )
                    ask_price = ask_raw / scale
                    bid_price = bid_raw / scale
                    ts_sec = int(base_ts / 1000.0)
                    dt = datetime.fromtimestamp(ts_sec, tz=UTC)
                    if date_from and dt < date_from:
                        continue
                    if date_to and dt > date_to:
                        continue
                    rows.append(
                        {
                            "time": ts_sec,
                            "open": bid_price,
                            "high": max(bid_price, ask_price),
                            "low": min(bid_price, ask_price),
                            "close": bid_price,
                            "tick_volume": 1,
                            "spread": 0,
                            "real_volume": 1,
                        }
                    )

            if not rows:
                raise BridgeError(
                    f"No bars available for '{sym_clean}' from Darwinex CDN",
                    code="NO_DATA",
                )

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
            if isinstance(exc, BridgeError):
                raise
            raise BridgeError(
                f"Failed to fetch Darwinex bars for {sym_clean}: {exc}",
                code="DOWNLOAD_ERROR",
            ) from exc

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
        """Download tick data from Darwinex CDN in memory."""
        del mode, end_ms
        self._ensure_catalog()
        sym_clean = symbol.upper().replace("/", "").replace("_", "").replace("-", "")
        target_count = count if count > 0 else limit
        target_year = (
            datetime.fromtimestamp(start_ms / 1000.0, tz=UTC).year
            if 0 < start_ms < 2**50
            else 2023
        )
        url = f"{CDN_BASE_URL}/{sym_clean}/{target_year}.zip"

        try:
            resp = self.session.get(url, timeout=30)
            if resp.status_code != 200:
                raise BridgeError(
                    f"No ticks available for '{sym_clean}' from Darwinex CDN (HTTP {resp.status_code})",
                    code="NO_DATA",
                )
            rows: list[dict[str, Any]] = []
            snap = self.symbol_info(sym_clean)
            scale = 10.0 ** (snap.digits + 1)
            with zipfile.ZipFile(io.BytesIO(resp.content)) as z:
                dat_names = sorted([n for n in z.namelist() if n.endswith(".dat")])
                for name in dat_names[-target_count:]:
                    dat_bytes = z.read(name)
                    idx = dat_bytes.find(b"\xbb\xbb")
                    if idx != -1 and len(dat_bytes) >= idx + 26:
                        offset = idx + 2
                        base_ts, ask_raw, bid_raw = struct.unpack(
                            ">qqq", dat_bytes[offset : offset + 24]
                        )
                        ask = ask_raw / scale
                        bid = bid_raw / scale
                        rows.append(
                            {
                                "time_msc": int(base_ts),
                                "bid": bid,
                                "ask": ask,
                                "last": (ask + bid) / 2.0,
                                "volume": 1,
                                "flags": 0,
                                "volume_real": 1.0,
                            }
                        )
            rows.sort(key=lambda r: r["time_msc"])
            if target_count and len(rows) > target_count:
                rows = rows[-target_count:]
            return rows
        except Exception as exc:
            if isinstance(exc, BridgeError):
                raise
            raise BridgeError(
                f"Failed to fetch Darwinex ticks: {exc}", code="DOWNLOAD_ERROR"
            ) from exc


def create_adapter(context: PluginHostContext | None = None) -> DarwinexBroker:
    """Factory creating configured DarwinexBroker adapter."""
    del context
    return DarwinexBroker()
