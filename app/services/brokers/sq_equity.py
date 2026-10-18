"""StrategyQuant US Equity market data and symbol catalog broker implementation.

Description:
    Implements a specialized market data broker accessing StrategyQuant US Equities
    historical data conforming to the `TradingBackend` protocol.
    Operates a resilient three-tier resolution architecture:
    1. Local native StrategyQuant 4.2 binary (.dat) archives.
    2. Local partitioned Parquet stores (D1 and M1).
    3. Direct remote streaming of Daily (EOD) historical bars from StrategyQuant CDN.
    Exposes canonical `SymbolInfo` objects and normalized historical bars.

Purpose:
    FEAT-BROKER-SQ-EQUITY: StrategyQuant US Equity Market Data and Catalog Broker.

Key Capabilities:
    - FR-BROKER-SQ-EQUITY-SYMBOLS: US Equity Symbol Catalog Resolution
      Associated: `[SQEquityBroker.symbol_info()]`, `[SQEquityBroker.symbols_get()]`
      Logging: Emits INFO log upon resolving symbol info or catalog count,
      and WARNING log if symbol is not found.
    - FR-BROKER-SQ-EQUITY-MARKET-DATA: Historical Bar Ingestion
      Associated: `[SQEquityBroker.fetch_bars()]`
      Logging: Emits INFO log upon successfully parsing native SQ 4.2 dat,
      Parquet partitions, or remote StrategyQuant CDN stream.

Python API Usage:
    ```python
    from app.services.brokers.sq_equity import SQEquityBroker
    from app.workspace.data_manager.history import get_historical_bars
    from app.workspace.data_manager import Timeframe

    broker = SQEquityBroker()
    bars = await get_historical_bars(broker, "AAPL", Timeframe.PERIOD_D1, count=5)
    assert len(bars) > 0
    ```

CLI Usage:
    `uv run python -m scripts.examples.brokers_data --broker sq_equity`
"""

from __future__ import annotations

import csv
import io
import os
import zipfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, override

from app.host.logging import get_logger
from app.services.brokers._file_history import load_local_partition_bars
from app.services.brokers._http import create_http_session, execute_bounded_get
from app.services.brokers._native_history import decode_sq_dat_bytes
from app.services.brokers.base import BridgeError
from app.services.brokers.capabilities import (
    CancellationToken,
    HistoryPage,
    HistoryRequest,
    ProviderCapabilities,
    ProviderHealth,
    ProviderValidationError,
)
from app.services.include.contracts import SymbolInfo
from app.workspace.data_manager.history import DataBrokerBackend

logger = get_logger(__name__)

DEFAULT_DATA_DIR = Path(__file__).resolve().parents[3] / "data" / "market" / "sq_equity"
DEFAULT_CATALOG_PATH = DEFAULT_DATA_DIR / "symbols.csv"
CDN_BASE_URL = "https://cdn.strategyquantcdn.com/data/barchart_test/eod"
USER_AGENT = "HaruQuantAI-SQEquityConnector/1.0"

PLUGIN_MANIFEST = {
    "id": "sq_equity",
    "name": "SQ Equity Free Data",
    "version": "1.0.0",
    "slot": "data.provider",
    "entry_point": "sq_equity:create_adapter",
    "description": "StrategyQuant US Equities historical data provider",
    "capabilities": ["data.fetch"],
}

__all__ = ["PLUGIN_MANIFEST", "SQEquityBroker", "create_adapter", "main"]


def _clean_symbol(sym: str) -> str:
    """Strip common exchange or packaging suffixes."""
    s = sym.strip()
    for suffix in ("_US", "_D1", "_M1", "-US", ".US"):
        if s.upper().endswith(suffix):
            s = s[: -len(suffix)]
    return s.upper()


def _find_sq_dat_file(base_dir: Path, symbol: str, timeframe: str) -> Path | None:
    """Locate the StrategyQuant .dat file for a symbol and timeframe."""
    if not base_dir.exists():
        return None

    clean = _clean_symbol(symbol).upper()
    if not clean:
        return None
    letter = clean[0]

    tf_str = timeframe.upper()
    is_m1 = "M1" in tf_str or "1M" in tf_str
    tf_tag = "M1" if is_m1 else "D1"

    letter_dir = base_dir / letter
    search_dirs = [letter_dir] if letter_dir.exists() else [base_dir]

    for sdir in search_dirs:
        for entry in sdir.iterdir():
            if not entry.is_dir():
                continue
            entry_clean = _clean_symbol(entry.name).upper()
            if entry_clean == clean:
                adj_candidate = entry / f"{entry.name}_{tf_tag}.dat"
                if adj_candidate.is_file():
                    return adj_candidate
                for f in entry.glob(f"*_{tf_tag}.dat"):
                    if "unadjusted" not in f.name.lower():
                        return f
                for f in entry.glob(f"*_{tf_tag}.dat"):
                    return f

    return None


def _find_parquet_files(base_dir: Path, symbol: str, timeframe: str) -> list[Path]:
    """Find local Parquet partition files for a symbol and timeframe."""
    if not base_dir.exists():
        return []
    clean = _clean_symbol(symbol).lower()
    tf_str = timeframe.upper()
    is_m1 = "M1" in tf_str or "1M" in tf_str
    tf_tag = "m1" if is_m1 else "d1"
    for cdir in (base_dir / tf_tag / clean, base_dir / clean / tf_tag):
        if cdir.is_dir():
            p_files = sorted(cdir.glob("*.parquet"))
            if p_files:
                return p_files
    return []


class SQEquityBroker(DataBrokerBackend):
    """StrategyQuant US Equity market data and symbol catalog broker."""

    _provider_id: str = "sq_equity"
    _display_name: str = "SQ Equity Free Data"
    _health_label: str = "SQ Equity"
    _asset_label: str = "equity"
    _category: str = "Equities"
    _supported_timeframes: tuple[str, ...] = ("D1", "M1")
    _allowed_history_timeframes: tuple[str, ...] = ("D1",)
    _history_tf_error_prefix: str = "StrategyQuant Equity only supports D1 timeframe"
    _description: str = "StrategyQuant US Equities historical data provider"
    _default_data_dir: Path = DEFAULT_DATA_DIR
    _default_catalog_path: Path = DEFAULT_CATALOG_PATH
    _alt_catalog_filename: str = "sq_equity.csv"
    _default_symbols: tuple[str, ...] = (
        "AAPL",
        "MSFT",
        "GOOGL",
        "AMZN",
        "SPY",
        "QQQ",
        "NVDA",
        "TSLA",
    )
    _default_contract_size: float = 1.0
    _user_agent: str = USER_AGENT
    _cdn_base_url: str = CDN_BASE_URL

    def __init__(
        self,
        name: str = "SQ_Equity",
        data_dir: str | Path | None = None,
        catalog_path: str | Path | None = None,
        sqx_history_dir: str | Path | None = None,
        enable_cdn_download: bool = True,
    ) -> None:
        """Initialize StrategyQuant catalog/CDN broker."""
        super().__init__(name=name)
        self.data_dir = Path(data_dir) if data_dir else self._default_data_dir
        self.catalog_path = (
            Path(catalog_path) if catalog_path else self._default_catalog_path
        )
        self.enable_cdn_download = enable_cdn_download

        if sqx_history_dir is not None:
            self.sqx_history_dir: Path | None = Path(sqx_history_dir)
        elif "SQX_REFERENCE_ROOT" in os.environ:
            candidate = (
                Path(os.environ["SQX_REFERENCE_ROOT"])
                / "user"
                / "data"
                / "History"
                / self._provider_id
            )
            self.sqx_history_dir = candidate if candidate.exists() else None
        else:
            self.sqx_history_dir = None

        self.session = create_http_session(
            user_agent=self._user_agent, retries=3, backoff=0.3, pool_size=8
        )
        self._catalog: dict[str, SymbolInfo] = {}
        self.capabilities = ProviderCapabilities(
            provider_id=self._provider_id,
            display_name=self._display_name,
            category=self._category,
            supported_timeframes=self._supported_timeframes,
            supported_modes=("bars",),
            requires_auth=False,
            rate_limit_rps=5.0,
            default_timeout_seconds=30.0,
            supports_pagination=True,
            has_local_archive=self.data_dir.exists(),
            description=self._description,
        )

    def _clean_sym(self, symbol: str) -> str:
        return _clean_symbol(symbol)

    def _find_dat(self, base_dir: Path, symbol: str, timeframe: str) -> Path | None:
        return _find_sq_dat_file(base_dir, symbol, timeframe)

    def _find_parquet(self, base_dir: Path, symbol: str, timeframe: str) -> list[Path]:
        return _find_parquet_files(base_dir, symbol, timeframe)

    def _http_get(self, url: str) -> Any:
        return execute_bounded_get(
            self.session, url, timeout=(5.0, 15.0), provider=self._provider_id
        )

    def check_health(self) -> Any:
        """Inspect provider health and local archive readiness."""
        has_dir = self.data_dir.exists()
        return ProviderHealth(
            provider_id=self._provider_id,
            status="available" if has_dir else "unconfigured",
            connected=has_dir,
            message=f"{self._health_label} ready"
            if has_dir
            else "Local data_dir not found",
            capabilities=self.capabilities,
        )

    def _ensure_catalog(self) -> None:
        """Load and cache the StrategyQuant instrument catalog."""
        if self._catalog:
            return

        catalog_file = self.catalog_path
        if not catalog_file.is_file():
            alt = self.data_dir / self._alt_catalog_filename
            if alt.is_file():
                catalog_file = alt

        if not catalog_file.is_file():
            for s in self._default_symbols:
                self._catalog[s] = SymbolInfo(
                    name=s,
                    digits=2,
                    point=0.01,
                    trade_contract_size=self._default_contract_size,
                )
            return

        try:
            with open(catalog_file, encoding="utf-8") as f:
                reader = csv.DictReader(f, delimiter=";")
                for row in reader:
                    sym = (row.get("symbol") or "").strip().upper()
                    if not sym:
                        continue
                    clean_sym = self._clean_sym(sym)
                    dec = int(row.get("decimals") or 2)
                    pt = float(row.get("point") or 0.01)
                    spread = int(float(row.get("spread") or 0))
                    c_size = float(
                        row.get("contract_size") or self._default_contract_size
                    )
                    self._catalog[clean_sym] = SymbolInfo(
                        name=clean_sym,
                        digits=dec,
                        point=pt,
                        spread=spread,
                        trade_contract_size=c_size,
                    )
        except Exception as exc:
            self.logger.warning("Error parsing %s catalog: %s", self._health_label, exc)

    @override
    def symbol_info(self, symbol: str) -> SymbolInfo:
        """Resolve instrument specifications as canonical SymbolInfo."""
        self._ensure_catalog()
        clean = self._clean_sym(symbol).upper()
        snap = self._catalog.get(clean)
        if snap is not None:
            return snap
        return SymbolInfo(
            name=clean,
            digits=2,
            point=0.01,
            trade_contract_size=self._default_contract_size,
        )

    @override
    def symbols_get(self) -> list[str]:
        """Return list of registered catalog symbols."""
        self._ensure_catalog()
        return list(self._catalog.keys())

    def _fetch_cdn_bars(
        self,
        symbol: str,
        count: int | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
    ) -> list[dict[str, Any]]:
        """Download and decode daily historical bars from StrategyQuant CDN."""
        clean_sym = self._clean_sym(symbol).upper().lstrip("@")
        zip_targets = ["data01.zip"]
        if (date_from and date_from.year < 2019) or (count and count > 1200):
            zip_targets = ["data00.zip", "data01.zip"]

        all_bars: list[dict[str, Any]] = []
        for zip_name in zip_targets:
            url = f"{self._cdn_base_url}/{clean_sym}/{zip_name}"
            try:
                resp = self._http_get(url)
                if resp.status_code == 200 and resp.content:
                    with zipfile.ZipFile(io.BytesIO(resp.content)) as z:
                        dat_names = sorted(
                            f for f in z.namelist() if f.endswith(".dat")
                        )
                        for dat_name in dat_names:
                            year_bars = decode_sq_dat_bytes(
                                z.read(dat_name),
                                date_from=date_from,
                                date_to=date_to,
                            )
                            all_bars.extend(year_bars)
            except Exception as exc:
                self.logger.warning("Error downloading CDN %s: %s", url, exc)

        all_bars.sort(key=lambda b: b["time"])
        if count and count > 0 and len(all_bars) > count:
            all_bars = all_bars[-count:]
        return all_bars

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
        """Retrieve historical candlestick bars from local storage or StrategyQuant CDN."""
        del mode
        target_count = count if count > 0 else limit
        date_from = datetime.fromtimestamp(start, tz=UTC) if 0 < start < 2**40 else None
        date_to = datetime.fromtimestamp(end, tz=UTC) if 0 < end < 2**40 else None

        parquet_files = self._find_parquet(self.data_dir, symbol, timeframe)
        if not parquet_files and self.sqx_history_dir:
            parquet_files = self._find_parquet(self.sqx_history_dir, symbol, timeframe)
        if parquet_files:
            parquet_bars = load_local_partition_bars(
                parquet_files,
                symbol=symbol,
                timeframe=timeframe,
                start=start,
                end=end,
                count=target_count,
            )
            if parquet_bars:
                return parquet_bars

        dat_file = self._find_dat(self.data_dir, symbol, timeframe)
        if not dat_file and self.sqx_history_dir:
            dat_file = self._find_dat(self.sqx_history_dir, symbol, timeframe)
        if dat_file:
            try:
                rows = decode_sq_dat_bytes(
                    dat_file.read_bytes(),
                    count=target_count,
                    date_from=date_from,
                    date_to=date_to,
                )
                if rows:
                    return rows
            except Exception as exc:
                self.logger.warning("Failed to decode dat file %s: %s", dat_file, exc)

        if self.enable_cdn_download and timeframe.upper() in ("D1", "1D"):
            cdn_bars = self._fetch_cdn_bars(
                symbol, count=target_count, date_from=date_from, date_to=date_to
            )
            if cdn_bars:
                return cdn_bars

        raise BridgeError(
            f"No {self._asset_label} data found for symbol '{symbol}' ({timeframe})",
            code="NO_DATA",
        )

    @override
    def read_history(
        self,
        request: HistoryRequest,
        token: CancellationToken | None = None,
    ) -> HistoryPage:
        """Fetch historical records adhering to Stage 2C contract."""
        request.validate()
        tf = request.timeframe.strip().upper()
        if tf not in self._allowed_history_timeframes:
            raise ProviderValidationError(
                f"{self._history_tf_error_prefix}, got '{request.timeframe}'",
                provider=self._provider_id,
            )
        try:
            return super().read_history(request, token)
        except BridgeError as be:
            if be.code == "NO_DATA":
                return HistoryPage(
                    provider=self._provider_id,
                    symbol=request.symbol,
                    timeframe=tf,
                    kind="bars",
                    rows=[],
                    is_complete=True,
                    provenance={"source": self._provider_id},
                )
            raise


def create_adapter(context: Any = None) -> SQEquityBroker:
    """Plugin entrypoint factory constructing SQEquityBroker adapter."""
    data_dir = getattr(context, "data_dir", None)
    return SQEquityBroker(data_dir=data_dir)


def main() -> None:
    """Demonstrate executable usage of SQEquityBroker."""
    broker = SQEquityBroker()
    health = broker.check_health()
    logger.info("SQ Equity health: %s (connected=%s)", health.status, health.connected)


if __name__ == "__main__":
    main()
