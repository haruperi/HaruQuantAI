"""Darwinex institutional market data and symbol catalog broker implementation.

Description:
    Implements an unauthenticated market data and symbol metadata broker
    for Darwinex conforming to the `TradingBackend` protocol.
    Fetches historical candlestick bars and ticks in memory from StrategyQuant CDN
    or local archives, and dynamically resolves instrument specifications from the
    authoritative catalog CSV (`data/market/darwinex/darwinex.csv`) returning canonical
    `SymbolInfo`.

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
    - FR-BROKER-DARWINEX-HEALTH: Connectivity and health check reporting.
      Associated: `[DarwinexBroker.check_health()]`
      Logging: Emits INFO on successful probe and WARNING on network failures.

Python API Usage:
    ```python
    from app.services.brokers.darwinex import DarwinexBroker
    from app.workspace.data_manager.history import get_historical_bars
    from app.workspace.data_manager import Timeframe

    broker = DarwinexBroker()
    bars = await get_historical_bars(broker, "EURUSD", Timeframe.PERIOD_D1, count=5)
    assert len(bars) > 0
    ```

CLI Usage:
    `uv run python -m scripts.examples.brokers_data --broker darwinex`
"""

from __future__ import annotations

import io
import zipfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, override

import requests
from app.host.discovery import PluginHostContext
from app.host.logging import get_logger
from app.services.brokers._file_history import (
    find_matching_partitions,
    parse_delimited_bars,
    read_parquet_bars,
)
from app.services.brokers._http import create_http_session, execute_bounded_get
from app.services.brokers._native_history import decode_darwinex_dat
from app.services.brokers.base import BridgeError
from app.services.brokers.capabilities import (
    CancellationToken,
    HistoryPage,
    HistoryRequest,
    ProviderCapabilities,
    ProviderError,
    ProviderHealth,
    ProviderUnsupportedError,
)
from app.services.libs.contracts import SymbolInfo
from app.workspace.data_manager.history import DataBrokerBackend

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

PLUGIN_MANIFEST = {
    "id": "darwinex",
    "name": "Darwinex",
    "version": "1.0.0",
    "slot": "data.provider",
    "entry_point": "darwinex:create_adapter",
    "description": "Darwinex institutional tick and bar market data provider",
    "capabilities": ["data.fetch"],
}

__all__ = ["PLUGIN_MANIFEST", "DarwinexBroker", "create_adapter", "main"]


class DarwinexBroker(DataBrokerBackend):
    """Darwinex market data and symbol catalog broker."""

    def __init__(
        self,
        name: str = "Darwinex",
        catalog_path: str | Path | None = None,
        session: requests.Session | None = None,
        data_dir: str | Path | None = None,
    ) -> None:
        """Initialize Darwinex broker."""
        super().__init__(name=name)
        self.catalog_path = Path(catalog_path) if catalog_path else DEFAULT_CATALOG_PATH
        self.data_dir = Path(data_dir) if data_dir else None
        self.session = session or create_http_session(
            USER_AGENT, retries=3, backoff=0.3
        )
        self._catalog: dict[str, SymbolInfo] = {}
        self.capabilities = ProviderCapabilities(
            provider_id="darwinex",
            display_name="Darwinex",
            category="Forex",
            supported_timeframes=("M1", "TICK", "D1"),
            supported_modes=("bars", "ticks"),
            requires_auth=False,
            rate_limit_rps=3.0,
            default_timeout_seconds=30.0,
            supports_pagination=True,
            has_local_archive=self.data_dir is not None and self.data_dir.exists(),
            description="Darwinex institutional tick and bar market data provider",
        )

    @override
    def close_sync(self) -> None:
        """Synchronously close session resources."""
        self._is_connected = False
        if hasattr(self, "session"):
            self.session.close()

    @override
    async def close(self) -> None:
        """Asynchronously close session resources."""
        self.close_sync()

    def check_health(self) -> ProviderHealth:
        """Check Darwinex CDN connectivity."""
        try:
            resp = self.session.head(CDN_BASE_URL, timeout=5.0)
            connected = resp.status_code in (200, 301, 302, 403, 404)
            return ProviderHealth(
                provider_id="darwinex",
                status="available" if connected else "failed",
                connected=connected,
                message="Darwinex CDN reachable"
                if connected
                else "Darwinex CDN unreachable",
                capabilities=self.capabilities,
            )
        except Exception as exc:
            return ProviderHealth(
                provider_id="darwinex",
                status="failed",
                connected=False,
                message=f"Health probe error: {exc}",
                capabilities=self.capabilities,
            )

    def _ensure_catalog(self) -> None:
        """Parse and cache symbol definitions from CSV catalog."""
        if self._catalog:
            return
        if not self.catalog_path.exists():
            self.logger.warning(
                "FR-BROKER-DARWINEX-SYMBOLS: Catalog not found at %s", self.catalog_path
            )
            return

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
                    try:
                        dec = int(parts[6].strip())
                        point_sz = float(parts[7].strip())
                        spread = float(parts[8].strip())
                        contract_sz = float(parts[10].strip())
                    except ValueError, IndexError:
                        dec = 5
                        point_sz = 0.00001
                        spread = 0.0
                        contract_sz = 100000.0

                    self._catalog[sym] = SymbolInfo(
                        name=sym,
                        digits=dec,
                        point=point_sz,
                        spread=int(spread),
                        trade_contract_size=contract_sz,
                    )
            self.logger.info(
                "FR-BROKER-DARWINEX-SYMBOLS: Loaded %d symbols", len(self._catalog)
            )
        except Exception as exc:
            self.logger.warning(
                "FR-BROKER-DARWINEX-SYMBOLS: Error parsing catalog: %s", exc
            )

    @override
    def symbol_info(self, symbol: str) -> SymbolInfo:
        """Retrieve instrument specifications as canonical SymbolInfo."""
        self._ensure_catalog()
        sym_clean = symbol.upper().replace("/", "").replace("_", "").replace("-", "")
        snap = self._catalog.get(sym_clean)
        if snap is not None:
            return snap
        return SymbolInfo(name=sym_clean, digits=5, point=0.00001)

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
        mode: str = "range",
        start: int = 0,
        end: int = 0,
        count: int = 100,
        limit: int = 1000,
    ) -> list[dict[str, Any]]:
        """Download candlestick bars from local archives or Darwinex CDN."""
        self._ensure_catalog()
        sym_clean = symbol.upper().replace("/", "").replace("_", "").replace("-", "")
        snap = self.symbol_info(sym_clean)
        decimals = snap.digits
        target_count = count if count > 0 else limit

        tf_norm = timeframe.strip().upper()
        if tf_norm not in ("M1", "D1"):
            raise ProviderUnsupportedError(
                f"Darwinex only supports M1 and D1 bar aggregation, got '{timeframe}'",
                provider="darwinex",
            )

        date_from = datetime.fromtimestamp(start, tz=UTC) if 0 < start < 2**40 else None
        date_to = datetime.fromtimestamp(end, tz=UTC) if 0 < end < 2**40 else None

        # Check local data_dir
        if self.data_dir and self.data_dir.exists():
            matched = find_matching_partitions(self.data_dir, sym_clean, timeframe)
            all_local: list[dict[str, Any]] = []
            for p in matched:
                if p.suffix.lower() == ".parquet":
                    all_local.extend(read_parquet_bars(p, count=target_count))
                elif p.suffix.lower() in (".csv", ".tsv", ".txt"):
                    all_local.extend(
                        parse_delimited_bars(
                            p.read_text(encoding="utf-8", errors="replace"),
                            sym_clean,
                            timeframe,
                        )
                    )
            if all_local:
                all_local.sort(key=lambda r: r["time"])
                filtered = [
                    r
                    for r in all_local
                    if (not date_from or r["time"] >= int(date_from.timestamp()))
                    and (not date_to or r["time"] <= int(date_to.timestamp()))
                ]
                if filtered:
                    return filtered[-target_count:] if target_count else filtered

        start_year = date_from.year if date_from else 2023
        end_year = date_to.year if date_to else start_year
        years = list(range(start_year, min(end_year, start_year + 3) + 1))
        period_sec = 86400 if tf_norm == "D1" else 60
        buckets: dict[int, dict[str, Any]] = {}

        try:
            for target_year in years:
                url = f"{CDN_BASE_URL}/{sym_clean}/{target_year}.zip"
                try:
                    resp = execute_bounded_get(
                        self.session,
                        url,
                        timeout=(5.0, 30.0),
                        provider="darwinex",
                    )
                    if resp.status_code != 200 or not resp.content:
                        continue

                    with zipfile.ZipFile(io.BytesIO(resp.content)) as z:
                        dat_names = sorted(
                            [n for n in z.namelist() if n.endswith(".dat")]
                        )
                        for name in dat_names:
                            dat_bytes = z.read(name)
                            ticks = decode_darwinex_dat(dat_bytes, digits=decimals)
                            for t in ticks:
                                ts_sec = int(t["time_msc"] / 1000.0)
                                if date_from and ts_sec < int(date_from.timestamp()):
                                    continue
                                if date_to and ts_sec > int(date_to.timestamp()):
                                    continue
                                bucket_time = (ts_sec // period_sec) * period_sec
                                mid_p = round(
                                    (float(t["bid"]) + float(t["ask"])) / 2.0, decimals
                                )
                                if bucket_time not in buckets:
                                    buckets[bucket_time] = {
                                        "time": bucket_time,
                                        "open": mid_p,
                                        "high": mid_p,
                                        "low": mid_p,
                                        "close": mid_p,
                                        "tick_volume": 1,
                                        "spread": round(
                                            (float(t["ask"]) - float(t["bid"]))
                                            * (10**decimals)
                                        ),
                                        "real_volume": 1.0,
                                    }
                                else:
                                    b = buckets[bucket_time]
                                    b["high"] = max(b["high"], mid_p)
                                    b["low"] = min(b["low"], mid_p)
                                    b["close"] = mid_p
                                    b["tick_volume"] += 1
                                    b["real_volume"] += 1.0
                except ProviderError:
                    raise
                except Exception as exc:
                    self.logger.debug(
                        "FR-BROKER-DARWINEX-MARKET-DATA: Error downloading %d: %s",
                        target_year,
                        exc,
                    )

            if not buckets:
                raise BridgeError(
                    f"No bars available for '{sym_clean}' from Darwinex CDN",
                    code="NO_DATA",
                )

            rows = [buckets[k] for k in sorted(buckets.keys())]
            if target_count and len(rows) > target_count:
                rows = rows[-target_count:]
            return rows
        except Exception as exc:
            if isinstance(exc, (BridgeError, ProviderError)):
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
        mode: str = "range",
        start_ms: int = 0,
        end_ms: int = 0,
        count: int = 100,
        limit: int = 1000,
    ) -> list[dict[str, Any]]:
        """Download tick data from local archives or Darwinex CDN."""
        self._ensure_catalog()
        sym_clean = symbol.upper().replace("/", "").replace("_", "").replace("-", "")
        snap = self.symbol_info(sym_clean)
        decimals = snap.digits
        target_count = count if count > 0 else limit
        start_year = (
            datetime.fromtimestamp(start_ms / 1000.0, tz=UTC).year
            if 0 < start_ms < 2**50
            else 2023
        )
        end_year = (
            datetime.fromtimestamp(end_ms / 1000.0, tz=UTC).year
            if 0 < end_ms < 2**50
            else start_year
        )
        years = list(range(start_year, min(end_year, start_year + 3) + 1))
        all_ticks: list[dict[str, Any]] = []

        try:
            for target_year in years:
                url = f"{CDN_BASE_URL}/{sym_clean}/{target_year}.zip"
                try:
                    resp = execute_bounded_get(
                        self.session,
                        url,
                        timeout=(5.0, 30.0),
                        provider="darwinex",
                    )
                    if resp.status_code != 200 or not resp.content:
                        continue

                    with zipfile.ZipFile(io.BytesIO(resp.content)) as z:
                        dat_names = sorted(
                            [n for n in z.namelist() if n.endswith(".dat")]
                        )
                        for name in dat_names:
                            dat_bytes = z.read(name)
                            ticks = decode_darwinex_dat(dat_bytes, digits=decimals)
                            for t in ticks:
                                if start_ms > 0 and t["time_msc"] < start_ms:
                                    continue
                                if end_ms > 0 and t["time_msc"] > end_ms:
                                    continue
                                all_ticks.append(t)
                except ProviderError:
                    raise
                except Exception as exc:
                    self.logger.debug(
                        "FR-BROKER-DARWINEX-MARKET-DATA: Error downloading %d ticks: %s",
                        target_year,
                        exc,
                    )

            if not all_ticks:
                raise BridgeError(
                    f"No ticks available for '{sym_clean}' from Darwinex CDN",
                    code="NO_DATA",
                )

            all_ticks.sort(key=lambda r: r["time_msc"])
            if target_count and len(all_ticks) > target_count:
                all_ticks = all_ticks[-target_count:]
            return all_ticks
        except Exception as exc:
            if isinstance(exc, (BridgeError, ProviderError)):
                raise
            raise BridgeError(
                f"Failed to fetch Darwinex ticks for {sym_clean}: {exc}",
                code="DOWNLOAD_ERROR",
            ) from exc

    def read_history(
        self,
        request: HistoryRequest,
        token: CancellationToken | None = None,
    ) -> HistoryPage:
        """Acquire historical bars or ticks according to typed request specification."""
        if token is not None:
            token.check_cancelled()
        request.validate()

        if request.kind == "ticks" or request.timeframe.upper() == "TICK":
            start_ms = (request.start_epoch() or 0) * 1000
            end_ms = (request.end_epoch() or 0) * 1000
            rows = self.fetch_ticks(
                symbol=request.symbol,
                mode=request.mode,
                start_ms=start_ms,
                end_ms=end_ms,
                count=request.count,
                limit=request.limit,
            )
        else:
            tf = request.timeframe.upper()
            if tf not in ("M1", "D1"):
                raise ProviderUnsupportedError(
                    f"Timeframe '{request.timeframe}' not supported by Darwinex. Supported: M1, D1",
                    provider="darwinex",
                )
            start_s = request.start_epoch() or 0
            end_s = request.end_epoch() or 0
            rows = self.fetch_bars(
                symbol=request.symbol,
                timeframe=request.timeframe,
                mode=request.mode,
                start=start_s,
                end=end_s,
                count=request.count,
                limit=request.limit,
            )

        if token is not None:
            token.check_cancelled()

        return HistoryPage(
            provider="darwinex",
            symbol=request.symbol,
            timeframe=request.timeframe,
            kind=request.kind,
            rows=rows,
            cursor=None,
            is_complete=True,
            provenance={
                "source": "darwinex",
                "data_dir": str(self.data_dir) if self.data_dir else None,
            },
        )


def create_adapter(context: PluginHostContext | None = None) -> DarwinexBroker:
    """Factory creating configured DarwinexBroker adapter."""
    data_dir = context.data_dir if context is not None else None
    return DarwinexBroker(data_dir=data_dir)


def main() -> None:
    """Demonstrate executable usage of DarwinexBroker."""
    broker = DarwinexBroker()
    health = broker.check_health()
    logger.info("Darwinex health: %s (connected=%s)", health.status, health.connected)


if __name__ == "__main__":
    main()
