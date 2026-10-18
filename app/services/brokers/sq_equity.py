"""StrategyQuant US Equity market data and symbol catalog client implementation.

Description:
    Implements a specialized market data client accessing StrategyQuant US Equities
    historical data conforming to the uniform `BrokerClient` interface.
    Operates a resilient three-tier resolution architecture:
    1. Local native StrategyQuant 4.2 binary (.dat) archives.
    2. Local partitioned Parquet stores (D1 and M1).
    3. Direct remote streaming of Daily (EOD) historical bars from StrategyQuant CDN.
    Exposes canonical `SymbolInfo` objects and normalized historical bars.

Purpose:
    FEAT-BROKER-SQ-EQUITY: StrategyQuant US Equity Market Data and Catalog Broker.

Key Capabilities:
    - FR-BROKER-SQ-EQUITY-SYMBOLS: US Equity Symbol Catalog Resolution
      Associated: `[SQEquityClient.get_symbol_info()]`, `[SQEquityClient.get_symbols()]`
      Logging: Emits INFO log upon resolving symbol info or catalog count,
      and WARNING log if symbol is not found.
    - FR-BROKER-SQ-EQUITY-MARKET-DATA: Historical Bar Ingestion
      Associated: `[SQEquityClient.get_bars()]`
      Logging: Emits INFO log upon successfully parsing native SQ 4.2 dat,
      Parquet partitions, or remote StrategyQuant CDN stream.

Python API Usage:
    ```python
    from app.services.brokers.sq_equity import SQEquityClient
    from app.services.include.enums import Timeframe

    client = SQEquityClient()
    bars = client.get_bars("AAPL", Timeframe.PERIOD_D1, count=5)
    assert len(bars) > 0
    client.disconnect()
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
from app.services.brokers.base import (
    BridgeError,
    BrokerClient,
    epoch_seconds,
)
from app.services.include.contracts import MarketBar, MarketTick, SymbolInfo
from app.services.include.enums import Timeframe

logger = get_logger(__name__)

DEFAULT_DATA_DIR = Path(__file__).resolve().parents[3] / "data" / "market" / "sq_equity"
DEFAULT_CATALOG_PATH = DEFAULT_DATA_DIR / "sq_equity.csv"
CDN_BASE_URL = "https://cdn.strategyquantcdn.com/data/barchart_test/eod"
USER_AGENT = "HaruQuantAI-SQEquityConnector/1.0"

__all__ = ["SQEquityClient"]


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


class SQEquityClient(BrokerClient):
    """StrategyQuant US Equity market data and symbol catalog client."""

    _provider_id: str = "sq_equity"
    _display_name: str = "SQ Equity Free Data"
    _health_label: str = "SQ Equity"
    _asset_label: str = "equity"
    _category: str = "Equities"
    _supported_timeframes: tuple[str, ...] = ("D1", "M1")
    _default_data_dir: Path = DEFAULT_DATA_DIR
    _default_catalog_path: Path = DEFAULT_CATALOG_PATH
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
        """Initialize StrategyQuant catalog/CDN broker client."""
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
        self._connected = True

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

    def _ensure_catalog(self) -> None:
        """Load and cache the StrategyQuant instrument catalog."""
        if self._catalog:
            return

        if not self.catalog_path.is_file():
            raise BridgeError(
                f"{self._health_label} symbol catalog not found at {self.catalog_path}",
                code="CATALOG_NOT_FOUND",
            )

        with open(self.catalog_path, encoding="utf-8") as f:
            reader = csv.DictReader(f, delimiter=";")
            for row_num, row in enumerate(reader, start=2):
                sym = (row.get("symbol") or "").strip().upper()
                if not sym:
                    continue
                clean_sym = self._clean_sym(sym)
                try:
                    dec = int(row["decimals"])
                    pt = float(row["point"])
                    spread = int(float(row["spread"]))
                    c_size = float(row["contract_size"])
                except (KeyError, TypeError, ValueError) as exc:
                    raise BridgeError(
                        f"Invalid numeric field at row {row_num} in {self._health_label} catalog {self.catalog_path}: {exc}",
                        code="CATALOG_PARSE_ERROR",
                    ) from exc
                self._catalog[clean_sym] = SymbolInfo(
                    name=clean_sym,
                    digits=dec,
                    point=pt,
                    spread=spread,
                    trade_contract_size=c_size,
                )

    @override
    def get_symbol_info(self, symbol: str) -> SymbolInfo:
        """Resolve instrument specifications as canonical SymbolInfo."""
        self._ensure_catalog()
        clean = self._clean_sym(symbol).upper()
        snap = self._catalog.get(clean)
        if snap is not None:
            return snap
        raise BridgeError(
            f"Symbol '{symbol}' not found in {self._health_label} catalog",
            code="SYMBOL_NOT_FOUND",
        )

    @override
    def get_symbols(self) -> list[str]:
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
            resp = self._http_get(url)
            if resp.status_code != 200 or not resp.content:
                raise BridgeError(
                    f"No {self._asset_label} data found for symbol '{symbol}' from CDN (HTTP {resp.status_code})",
                    code="DOWNLOAD_ERROR",
                )
            with zipfile.ZipFile(io.BytesIO(resp.content)) as z:
                dat_names = sorted(f for f in z.namelist() if f.endswith(".dat"))
                for dat_name in dat_names:
                    year_bars = decode_sq_dat_bytes(
                        z.read(dat_name),
                        date_from=date_from,
                        date_to=date_to,
                    )
                    all_bars.extend(year_bars)

        all_bars.sort(key=lambda b: b["time"])
        if count and count > 0 and len(all_bars) > count:
            all_bars = all_bars[-count:]
        return all_bars

    @override
    def get_bars(
        self,
        symbol: str,
        timeframe: Timeframe | str = Timeframe.PERIOD_D1,
        date_from: datetime | int | None = None,
        date_to: datetime | int | None = None,
        *,
        start: datetime | int | None = None,
        end: datetime | int | None = None,
        start_pos: int | None = None,
        count: int | None = None,
        limit: int = 1000,
    ) -> list[MarketBar]:
        """Retrieve historical candlestick bars from local storage or StrategyQuant CDN."""
        del start_pos
        target_count = count or limit or 100
        s = date_from if date_from is not None else start
        e = date_to if date_to is not None else end
        start_sec = epoch_seconds(s)
        end_sec = epoch_seconds(e)
        date_from = (
            datetime.fromtimestamp(start_sec, tz=UTC) if 0 < start_sec < 2**40 else None
        )
        date_to = (
            datetime.fromtimestamp(end_sec, tz=UTC) if 0 < end_sec < 2**40 else None
        )

        tf_name = timeframe.name if isinstance(timeframe, Timeframe) else str(timeframe)
        if tf_name.upper() not in ("D1", "1D", "PERIOD_D1", "DAY"):
            raise BridgeError(
                f"StrategyQuant US Equities only supports D1 daily timeframe, got '{timeframe}'",
                code="UNSUPPORTED_TIMEFRAME",
            )
        parquet_files = self._find_parquet(self.data_dir, symbol, tf_name)
        if not parquet_files and self.sqx_history_dir:
            parquet_files = self._find_parquet(self.sqx_history_dir, symbol, tf_name)
        if parquet_files:
            parquet_bars = load_local_partition_bars(
                parquet_files,
                symbol=symbol,
                timeframe=tf_name,
                start=start_sec,
                end=end_sec,
                count=target_count,
            )
            if parquet_bars:
                return [
                    MarketBar(
                        time=int(r["time"]),
                        open=float(r["open"]),
                        high=float(r["high"]),
                        low=float(r["low"]),
                        close=float(r["close"]),
                        tick_volume=int(r.get("tick_volume", 0)),
                        spread=int(r.get("spread", 0)),
                        real_volume=int(r.get("real_volume", 0)),
                    )
                    for r in parquet_bars
                ]

        dat_file = self._find_dat(self.data_dir, symbol, tf_name)
        if not dat_file and self.sqx_history_dir:
            dat_file = self._find_dat(self.sqx_history_dir, symbol, tf_name)
        if dat_file:
            rows = decode_sq_dat_bytes(
                dat_file.read_bytes(),
                count=target_count,
                date_from=date_from,
                date_to=date_to,
            )
            if rows:
                return [
                    MarketBar(
                        time=int(r["time"]),
                        open=float(r["open"]),
                        high=float(r["high"]),
                        low=float(r["low"]),
                        close=float(r["close"]),
                        tick_volume=int(r.get("tick_volume", 0)),
                        spread=int(r.get("spread", 0)),
                        real_volume=int(r.get("real_volume", 0)),
                    )
                    for r in rows
                ]

        if self.enable_cdn_download and tf_name.upper() in ("D1", "1D", "PERIOD_D1"):
            cdn_bars = self._fetch_cdn_bars(
                symbol, count=target_count, date_from=date_from, date_to=date_to
            )
            if cdn_bars:
                return [
                    MarketBar(
                        time=int(r["time"]),
                        open=float(r["open"]),
                        high=float(r["high"]),
                        low=float(r["low"]),
                        close=float(r["close"]),
                        tick_volume=int(r.get("tick_volume", 0)),
                        spread=int(r.get("spread", 0)),
                        real_volume=int(r.get("real_volume", 0)),
                    )
                    for r in cdn_bars
                ]

        raise BridgeError(
            f"No {self._asset_label} data found for symbol '{symbol}' ({tf_name})",
            code="NO_DATA",
        )

    @override
    def get_ticks(
        self,
        symbol: str,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        *,
        count: int | None = None,
        limit: int = 1000,
    ) -> list[MarketTick]:
        """Historical ticks are unsupported for StrategyQuant US Equities."""
        del date_from, date_to, count, limit
        raise BridgeError(
            "StrategyQuant US Equities does not support tick history",
            code="UNSUPPORTED_OPERATION",
        )


def main() -> None:
    """Demonstrate executable usage of SQEquityClient."""
    client = SQEquityClient()
    symbols = client.get_symbols()
    logger.info("SQ Equity symbols: %d available", len(symbols))
    client.disconnect()


if __name__ == "__main__":
    main()
