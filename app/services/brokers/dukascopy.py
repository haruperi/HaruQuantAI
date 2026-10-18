"""Dukascopy market data and authoritative symbol catalog broker implementation.

Description:
    Implements an unauthenticated market data and symbol metadata broker
    for Dukascopy Bank SA conforming to the `TradingBackend` protocol.
    Fetches historical candlestick bars and ticks over HTTP in memory or from local
    data directories, and dynamically resolves instrument specifications from the
    authoritative catalog CSV (`data/market/dukascopy/dukascopy.csv`) returning canonical
    `SymbolInfo` objects.

Purpose:
    FEAT-BROKER-DUKASCOPY: Dukascopy Market Data and Symbol Catalog Provider.

Key Capabilities:
    - FR-BROKER-DUKASCOPY-MARKET-DATA: Historical Candlestick Bars and Ticks
      Associated: `[DukascopyBroker.fetch_bars()]`, `[DukascopyBroker.fetch_ticks()]`
      Logging: Emits INFO log upon successfully downloading and parsing bars with
      extracted count, and WARNING log on network failure or non-200 HTTP response.
    - FR-BROKER-DUKASCOPY-SYMBOLS: Authoritative Symbol Catalog Resolution
      Associated: `[DukascopyBroker.symbol_info()]`, `[DukascopyBroker.symbols_get()]`
      Logging: Emits INFO log upon successfully loading or querying catalog items,
      and WARNING log if symbol is not found in the CSV catalog.
    - FR-BROKER-DUKASCOPY-HEALTH: Provider health and connectivity inspection.
      Associated: `[DukascopyBroker.check_health()]`
      Logging: Emits INFO on successful probe and WARNING on network failures.

Python API Usage:
    ```python
    from app.services.brokers.dukascopy import DukascopyBroker
    from app.services.include.data import get_historical_bars
    from app.workspace.data_manager import Timeframe

    broker = DukascopyBroker()
    bars = await get_historical_bars(broker, "EURUSD", Timeframe.PERIOD_M1, count=5)
    assert len(bars) > 0
    ```

CLI Usage:
    `uv run python -m scripts.examples.brokers_data --broker dukascopy`
"""

from __future__ import annotations

import io
import zipfile
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, override

from app.host.discovery import PluginHostContext
from app.host.logging import get_logger
from app.services.brokers._file_history import (
    find_matching_partitions,
    parse_delimited_bars,
    read_parquet_bars,
)
from app.services.brokers._http import create_http_session, execute_bounded_get
from app.services.brokers._native_history import (
    decode_bi5_bars,
    decode_bi5_ticks,
    decode_sq_dat_bytes,
    decompress_bi5,
)
from app.services.brokers.base import BridgeError
from app.services.brokers.capabilities import (
    CancellationToken,
    HistoryPage,
    HistoryRequest,
    ProviderCapabilities,
    ProviderHealth,
    ProviderUnsupportedError,
)
from app.services.include.contracts import SymbolInfo
from app.services.include.data import DataBrokerBackend

logger = get_logger(__name__)

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)

DEFAULT_DATA_DIR = Path(__file__).resolve().parents[3] / "data" / "market" / "dukascopy"
DEFAULT_CATALOG_PATH = DEFAULT_DATA_DIR / "dukascopy.csv"

PLUGIN_MANIFEST = {
    "id": "dukascopy",
    "name": "Dukascopy",
    "version": "1.0.0",
    "slot": "data.provider",
    "entry_point": "dukascopy:create_adapter",
    "description": "Dukascopy Bank SA historical tick and bar provider",
    "capabilities": ["data.fetch"],
}

__all__ = ["PLUGIN_MANIFEST", "DukascopyBroker", "create_adapter", "main"]

# Compatibility alias
_decompress_bi5 = decompress_bi5


class DukascopyBroker(DataBrokerBackend):
    """Dukascopy market data and symbol catalog broker."""

    CDN_BASE_URL = "https://cdn.strategyquantcdn.com/data/dukascopy"
    DATAFEED_BASE_URL = "https://datafeed.dukascopy.com/datafeed"

    def __init__(
        self,
        name: str = "Dukascopy",
        catalog_path: str | Path | None = None,
        data_dir: str | Path | None = None,
    ) -> None:
        """Initialize Dukascopy broker."""
        super().__init__(name=name)
        self.catalog_path = Path(catalog_path) if catalog_path else DEFAULT_CATALOG_PATH
        self.data_dir: Path | None = (
            Path(data_dir)
            if data_dir is not None
            else (DEFAULT_DATA_DIR if DEFAULT_DATA_DIR.exists() else None)
        )
        self._catalog: dict[str, SymbolInfo] | None = None
        self.session = create_http_session(
            USER_AGENT, retries=3, backoff=0.3, pool_size=16
        )
        self.capabilities = ProviderCapabilities(
            provider_id="dukascopy",
            display_name="Dukascopy",
            category="Forex",
            supported_timeframes=("M1", "M5", "M15", "M30", "H1", "D1"),
            supported_modes=("bars", "ticks"),
            requires_auth=False,
            rate_limit_rps=5.0,
            default_timeout_seconds=30.0,
            supports_pagination=True,
            has_local_archive=self.data_dir is not None and self.data_dir.exists(),
            description="Dukascopy Bank SA historical tick and bar provider",
        )

    def check_health(self) -> ProviderHealth:
        """Check Dukascopy feed connectivity."""
        try:
            resp = self.session.head(self.CDN_BASE_URL, timeout=5.0)
            connected = resp.status_code in (200, 301, 302, 403, 404)
            return ProviderHealth(
                provider_id="dukascopy",
                status="available" if connected else "failed",
                connected=connected,
                message="Dukascopy CDN reachable"
                if connected
                else "Dukascopy CDN unreachable",
                capabilities=self.capabilities,
            )
        except Exception as exc:
            return ProviderHealth(
                provider_id="dukascopy",
                status="failed",
                connected=False,
                message=f"Health probe error: {exc}",
                capabilities=self.capabilities,
            )

    def _ensure_catalog(self) -> dict[str, SymbolInfo]:
        """Parse and cache symbol definitions from data/market/dukascopy/dukascopy.csv."""
        if self._catalog is not None:
            return self._catalog

        catalog: dict[str, SymbolInfo] = {}
        if not self.catalog_path.exists():
            self.logger.warning(
                "FR-BROKER-DUKASCOPY-SYMBOLS: Catalog CSV file not found at %s",
                self.catalog_path,
            )
            self._catalog = catalog
            return self._catalog

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

                    catalog[sym] = SymbolInfo(
                        name=sym,
                        digits=dec,
                        point=point_sz,
                        spread=int(spread),
                        trade_contract_size=contract_sz,
                    )
            self._catalog = catalog
            self.logger.info(
                "FR-BROKER-DUKASCOPY-SYMBOLS: Loaded %d symbols from catalog CSV",
                len(catalog),
            )
            return catalog
        except Exception as exc:
            self.logger.warning(
                "FR-BROKER-DUKASCOPY-SYMBOLS: Error parsing catalog CSV: %s", exc
            )
            self._catalog = catalog
            return catalog

    def _clean_symbol(self, symbol: str) -> str:
        """Strip delimiters and match symbol against catalog."""
        catalog = self._ensure_catalog()
        s = symbol.upper().strip()
        if s in catalog:
            return s
        s_nodelim = (
            s.replace("_", "").replace("/", "").replace("-", "").replace(".", "")
        )
        if s_nodelim in catalog:
            return s_nodelim
        for delim in ("_", "/", "-", "."):
            if delim in s:
                prefix = s.split(delim)[0]
                if prefix in catalog:
                    return prefix
        for length in (7, 6, 5, 4, 3):
            if len(s_nodelim) >= length and s_nodelim[:length] in catalog:
                return s_nodelim[:length]
        return s

    @override
    def symbol_info(self, symbol: str) -> SymbolInfo:
        """Retrieve instrument specifications as canonical SymbolInfo."""
        sym_clean = self._clean_symbol(symbol)
        catalog = self._ensure_catalog()
        snap = catalog.get(sym_clean)
        if snap is not None:
            return snap
        return SymbolInfo(name=sym_clean, digits=5, point=0.00001)

    @override
    def symbols_get(self) -> list[str]:
        """Get the list of symbol names available in the catalog."""
        catalog = self._ensure_catalog()
        return list(catalog.keys())

    def _fetch_datafeed_bars(
        self,
        sym_clean: str,
        dt: datetime,
        decimals: int,
        count: int = 100,
    ) -> list[dict[str, Any]]:
        """Fetch and decompress daily candles from Dukascopy direct datafeed."""
        feed_url = (
            f"{self.DATAFEED_BASE_URL}/{sym_clean}/{dt.year}/{dt.month - 1:02d}/"
            f"{dt.day:02d}/BID_candles_min_1.bi5"
        )
        try:
            resp = execute_bounded_get(
                self.session,
                feed_url,
                timeout=(5.0, 15.0),
                provider="dukascopy",
            )
            if resp.status_code != 200 or not resp.content:
                return []
            decomp = decompress_bi5(resp.content)
            base_dt = datetime(dt.year, dt.month, dt.day, tzinfo=UTC)
            return decode_bi5_bars(decomp, base_dt, digits=decimals, count=count)
        except Exception as exc:
            self.logger.debug(
                "FR-BROKER-DUKASCOPY-MARKET-DATA: Datafeed candle fetch failed: %s",
                exc,
            )
            return []

    def _fetch_datafeed_ticks(
        self,
        sym_clean: str,
        dt: datetime,
        decimals: int,
        count: int = 100,
    ) -> list[dict[str, Any]]:
        """Fetch and decompress hourly ticks from Dukascopy direct datafeed."""
        feed_url = (
            f"{self.DATAFEED_BASE_URL}/{sym_clean}/{dt.year}/{dt.month - 1:02d}/"
            f"{dt.day:02d}/{dt.hour:02d}h_ticks.bi5"
        )
        try:
            resp = execute_bounded_get(
                self.session,
                feed_url,
                timeout=(5.0, 15.0),
                provider="dukascopy",
            )
            if resp.status_code != 200 or not resp.content:
                return []
            decomp = decompress_bi5(resp.content)
            base_dt = datetime(dt.year, dt.month, dt.day, dt.hour, tzinfo=UTC)
            return decode_bi5_ticks(decomp, base_dt, digits=decimals, count=count)
        except Exception as exc:
            self.logger.debug(
                "FR-BROKER-DUKASCOPY-MARKET-DATA: Datafeed tick fetch failed: %s", exc
            )
            return []

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
        """Download candlestick bars from local storage, CDN, or datafeed."""
        sym_clean = self._clean_symbol(symbol)
        snap = self.symbol_info(sym_clean)
        decimals = snap.digits
        target_count = count if count > 0 else limit

        tf_norm = timeframe.strip().upper()
        if tf_norm not in ("M1", "TICK"):
            raise ProviderUnsupportedError(
                f"Timeframe '{timeframe}' not supported by Dukascopy. Supported: M1, TICK",
                provider="dukascopy",
            )

        date_from = datetime.fromtimestamp(start, tz=UTC) if 0 < start < 2**40 else None
        date_to = datetime.fromtimestamp(end, tz=UTC) if 0 < end < 2**40 else None

        # Check local data_dir if available
        if self.data_dir is not None and self.data_dir.exists():
            matched = find_matching_partitions(self.data_dir, sym_clean, timeframe)
            all_local_bars: list[dict[str, Any]] = []
            for p in matched:
                if p.suffix.lower() == ".parquet":
                    all_local_bars.extend(read_parquet_bars(p, count=target_count))
                elif p.suffix.lower() in (".csv", ".tsv", ".txt"):
                    all_local_bars.extend(
                        parse_delimited_bars(
                            p.read_text(encoding="utf-8", errors="replace"),
                            sym_clean,
                            timeframe,
                        )
                    )
                elif p.suffix.lower() == ".bi5":
                    decomp = decompress_bi5(p.read_bytes())
                    base_dt = date_from or datetime(2023, 1, 1, tzinfo=UTC)
                    all_local_bars.extend(
                        decode_bi5_bars(
                            decomp, base_dt, digits=decimals, count=target_count
                        )
                    )
            if all_local_bars:
                all_local_bars.sort(key=lambda r: r["time"])
                filtered = [
                    r
                    for r in all_local_bars
                    if (not date_from or r["time"] >= int(date_from.timestamp()))
                    and (not date_to or r["time"] <= int(date_to.timestamp()))
                ]
                if filtered:
                    return filtered[-target_count:] if target_count else filtered

        target_year = date_from.year if date_from else 2023
        cdn_url = f"{self.CDN_BASE_URL}/m1/{sym_clean}/{target_year}.zip"
        scale = 10.0 ** (decimals + 1)

        try:
            resp = execute_bounded_get(
                self.session,
                cdn_url,
                timeout=(5.0, 30.0),
                provider="dukascopy",
            )
            if resp.status_code == 200 and resp.content:
                rows: list[dict[str, Any]] = []
                with zipfile.ZipFile(io.BytesIO(resp.content)) as z:
                    for name in z.namelist():
                        if name.endswith(".bi5"):
                            decomp = decompress_bi5(z.read(name))
                            if not decomp:
                                continue
                            base_dt = datetime(target_year, 1, 1, tzinfo=UTC)
                            sub_bars = decode_bi5_bars(
                                decomp, base_dt, digits=decimals, count=target_count
                            )
                            rows.extend(sub_bars)
                        elif name.endswith(".dat"):
                            dat_buf = z.read(name)
                            sub_bars = decode_sq_dat_bytes(
                                dat_buf,
                                count=target_count,
                                date_from=date_from,
                                date_to=date_to,
                            )
                            rows.extend(sub_bars)

                if rows:
                    rows.sort(key=lambda r: r["time"])
                    deduped: list[dict[str, Any]] = []
                    last_t: int | None = None
                    for r in rows:
                        if (date_from and r["time"] < int(date_from.timestamp())) or (
                            date_to and r["time"] > int(date_to.timestamp())
                        ):
                            continue
                        if last_t is None or r["time"] > last_t:
                            deduped.append(r)
                            last_t = r["time"]
                    if deduped:
                        return deduped[-target_count:] if target_count else deduped
        except Exception as exc:
            self.logger.debug(
                "FR-BROKER-DUKASCOPY-MARKET-DATA: CDN download failed: %s", exc
            )

        feed_dt = date_to or (
            date_from + timedelta(days=1)
            if date_from
            else datetime(2023, 1, 2, tzinfo=UTC)
        )
        feed_bars = self._fetch_datafeed_bars(
            sym_clean=sym_clean,
            dt=feed_dt,
            decimals=decimals,
            count=target_count,
        )
        if feed_bars:
            feed_bars.sort(key=lambda r: r["time"])
            filtered = [
                r
                for r in feed_bars
                if (not date_from or r["time"] >= int(date_from.timestamp()))
                and (not date_to or r["time"] <= int(date_to.timestamp()))
            ]
            if filtered:
                return filtered[-target_count:] if target_count else filtered

        raise BridgeError(
            f"No bars available for '{sym_clean}' from Dukascopy",
            code="NO_DATA",
        )

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
        """Download tick data from local archives or Dukascopy direct datafeed."""
        sym_clean = self._clean_symbol(symbol)
        snap = self.symbol_info(sym_clean)
        decimals = snap.digits
        target_count = count if count > 0 else limit

        # Check local data_dir if available
        if self.data_dir is not None and self.data_dir.exists():
            matched = find_matching_partitions(self.data_dir, sym_clean, "TICK")
            all_local_ticks: list[dict[str, Any]] = []
            for p in matched:
                if p.suffix.lower() == ".bi5":
                    decomp = decompress_bi5(p.read_bytes())
                    base_dt = (
                        datetime.fromtimestamp(start_ms / 1000.0, tz=UTC)
                        if start_ms > 0
                        else datetime(2023, 1, 1, tzinfo=UTC)
                    )
                    all_local_ticks.extend(
                        decode_bi5_ticks(
                            decomp, base_dt, digits=decimals, count=target_count
                        )
                    )
            if all_local_ticks:
                all_local_ticks.sort(key=lambda r: r["time_msc"])
                filtered = [
                    r
                    for r in all_local_ticks
                    if (start_ms <= 0 or r["time_msc"] >= start_ms)
                    and (end_ms <= 0 or r["time_msc"] <= end_ms)
                ]
                if filtered:
                    return filtered[-target_count:] if target_count else filtered

        target_dt = (
            datetime.fromtimestamp(start_ms / 1000.0, tz=UTC)
            if 0 < start_ms < 2**50
            else datetime(2023, 1, 2, 10, tzinfo=UTC)
        )
        ticks = self._fetch_datafeed_ticks(
            sym_clean=sym_clean,
            dt=target_dt,
            decimals=decimals,
            count=target_count,
        )
        ticks.sort(key=lambda r: r["time_msc"])
        if end_ms > 0:
            ticks = [t for t in ticks if t["time_msc"] <= end_ms]
        if target_count and len(ticks) > target_count:
            ticks = ticks[-target_count:]
        return ticks

    @override
    def read_history(
        self,
        request: HistoryRequest,
        token: CancellationToken | None = None,
    ) -> HistoryPage:
        """Fetch historical records adhering to Stage 2C contract."""
        tf = request.timeframe.strip().upper()
        if request.kind != "ticks" and tf != "TICK" and tf != "M1":
            raise ProviderUnsupportedError(
                f"Timeframe '{request.timeframe}' not supported by Dukascopy. Supported: M1, TICK",
                provider="dukascopy",
            )
        try:
            return super().read_history(request, token)
        except BridgeError as be:
            if be.code == "NO_DATA":
                return HistoryPage(
                    provider="dukascopy",
                    symbol=request.symbol,
                    timeframe=request.timeframe,
                    kind=request.kind,
                    rows=[],
                    is_complete=True,
                    provenance={"source": "dukascopy"},
                )
            raise


def create_adapter(context: PluginHostContext | None = None) -> DukascopyBroker:
    """Factory creating configured DukascopyBroker adapter."""
    data_dir = context.data_dir if context is not None else None
    return DukascopyBroker(data_dir=data_dir)


def main() -> None:
    """Demonstrate executable usage of DukascopyBroker."""
    broker = DukascopyBroker()
    health = broker.check_health()
    logger.info("Dukascopy health: %s (connected=%s)", health.status, health.connected)


if __name__ == "__main__":
    main()
