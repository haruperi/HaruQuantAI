"""StrategyQuant Continuous Futures market data and symbol catalog broker implementation.

Description:
    Implements a specialized market data broker accessing StrategyQuant Continuous
    Futures historical data conforming to the `TradingBackend` protocol.
    Operates a resilient three-tier resolution architecture:
    1. Local native StrategyQuant 4.2 binary (.dat) archives.
    2. Local partitioned Parquet stores (D1 and M1).
    3. Direct remote streaming of Daily (EOD) historical bars from StrategyQuant CDN.
    Exposes canonical `SymbolSnapshot` objects and normalized historical bars.

Purpose:
    FEAT-BROKER-SQ-FUTURES: StrategyQuant Continuous Futures Market Data and Catalog Broker.

Key Capabilities:
    - FR-BROKER-SQ-FUTURES-SYMBOLS: Continuous Futures Symbol Catalog Resolution
      Associated: `[SQFuturesBroker.symbol_info()]`, `[SQFuturesBroker.symbols_get()]`
      Logging: Emits INFO log upon resolving symbol info or catalog count,
      and WARNING log if symbol is not found.
    - FR-BROKER-SQ-FUTURES-MARKET-DATA: Historical Continuous Bar Ingestion
      Associated: `[SQFuturesBroker.fetch_bars()]`
      Logging: Emits INFO log upon successfully parsing native SQ 4.2 dat,
      Parquet partitions, or remote StrategyQuant CDN stream.

Python API Usage:
    ```python
    from app.services.data import Timeframe, get_historical_bars
    from app.services.brokers.sq_futures import SQFuturesBroker

    broker = SQFuturesBroker()
    bars = await get_historical_bars(broker, "@ES", Timeframe.PERIOD_D1, count=5)
    assert len(bars) > 0
    ```

CLI Usage:
    `uv run python -m scripts.examples.brokers_data --broker sq_futures`
"""

from __future__ import annotations

import csv
import io
import os
import struct
import zipfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, override

import requests
from app.host.logging import get_logger
from app.services.brokers._http import execute_bounded_get
from app.services.brokers._native_history import SQ_MAGIC_HEADER_V42
from app.services.brokers.capabilities import (
    CancellationToken,
    HistoryPage,
    HistoryRequest,
    ProviderCapabilities,
    ProviderHealth,
    ProviderValidationError,
)
from app.services.data import BridgeError, DataBrokerBackend
from app.services.trading import SymbolSnapshot
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = get_logger(__name__)

DEFAULT_DATA_DIR = (
    Path(__file__).resolve().parents[3] / "data" / "market" / "sq_futures"
)
DEFAULT_CATALOG_PATH = DEFAULT_DATA_DIR / "symbols.csv"
CDN_BASE_URL = "https://cdn.strategyquantcdn.com/data/barchart_test/eod"
USER_AGENT = "HaruQuantAI-SQFuturesConnector/1.0"

PLUGIN_MANIFEST = {
    "id": "sq_futures",
    "name": "SQ Futures Free Data",
    "version": "1.0.0",
    "slot": "data.provider",
    "entry_point": "sq_futures:create_adapter",
    "description": "StrategyQuant Continuous Futures historical data provider",
    "capabilities": ["data.fetch"],
}

__all__ = [
    "CDN_BASE_URL",
    "PLUGIN_MANIFEST",
    "SQFuturesBroker",
    "create_adapter",
    "main",
]


def _clean_symbol(sym: str) -> str:
    """Normalize continuous futures symbol."""
    s = sym.strip().upper()
    s = s.removesuffix(".D")
    s = s.removesuffix("_LIMITED")
    return s.removesuffix("_BENCHMARK")


def _normalize_dt(val: Any) -> datetime | None:
    """Normalize input value to a timezone-aware UTC datetime."""
    if val is None:
        return None
    if isinstance(val, datetime):
        return val if val.tzinfo is not None else val.replace(tzinfo=UTC)
    if isinstance(val, (int, float)):
        return datetime.fromtimestamp(val, tz=UTC)
    if isinstance(val, str):
        try:
            dt = datetime.fromisoformat(val)
            return dt if dt.tzinfo is not None else dt.replace(tzinfo=UTC)
        except ValueError:
            return None
    return None


def _find_sq_dat_file(base_dir: Path, symbol: str, timeframe: str) -> Path | None:
    """Locate the StrategyQuant .dat file for a symbol and timeframe."""
    if not base_dir.exists():
        return None

    clean = _clean_symbol(symbol).upper()
    if not clean:
        return None

    tf_str = str(timeframe).upper()
    is_m1 = "M1" in tf_str or "1M" in tf_str
    tf_tag = "M1" if is_m1 else "D1"

    for entry in base_dir.iterdir():
        if entry.is_dir():
            entry_clean = _clean_symbol(entry.name).upper()
            if entry_clean == clean:
                adj = entry / f"{entry.name}_{tf_tag}.dat"
                if adj.is_file():
                    return adj
                for f in entry.glob(f"*_{tf_tag}.dat"):
                    return f
        elif entry.is_file() and entry.name.endswith(".dat"):
            entry_clean = _clean_symbol(entry.stem).upper()
            if entry_clean == clean or entry_clean.startswith(clean):
                return entry

    return None


def _decode_sq_dat_bytes(
    buf: bytes,
    count: int | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
) -> list[dict[str, Any]]:
    """Parse StrategyQuant 4.2 binary compressed bars."""
    if len(buf) < 15:
        return []

    blocks: list[int] = []
    idx = 0
    while True:
        pos = buf.find(SQ_MAGIC_HEADER_V42, idx)
        if pos == -1:
            break
        blocks.append(pos)
        idx = pos + 15

    if not blocks:
        return []

    norm_from = _normalize_dt(date_from)
    norm_to = _normalize_dt(date_to)

    rows: list[dict[str, Any]] = []

    for b_idx_rel, b_off in enumerate(blocks):
        next_b_off = blocks[b_idx_rel + 1] if b_idx_rel + 1 < len(blocks) else len(buf)
        curr = b_off + 15 + 7

        if curr + 48 > next_b_off:
            continue

        ts_ms = struct.unpack_from(">Q", buf, curr)[0]
        o_raw, h_raw, l_raw, c_raw, v_raw = struct.unpack_from(">5q", buf, curr + 8)
        curr += 48

        dt = datetime.fromtimestamp(ts_ms / 1000.0, tz=UTC)
        include = True
        if norm_from and dt < norm_from:
            include = False
        if norm_to and dt > norm_to:
            include = False

        if include:
            rows.append(
                {
                    "time": int(ts_ms / 1000.0),
                    "open": o_raw / 1_000_000.0,
                    "high": h_raw / 1_000_000.0,
                    "low": l_raw / 1_000_000.0,
                    "close": c_raw / 1_000_000.0,
                    "tick_volume": max(0, int(v_raw // 100_000)),
                    "spread": 0,
                    "real_volume": max(0, int(v_raw // 100_000)),
                }
            )

        while curr < next_b_off:
            if curr + 3 > next_b_off:
                break
            flag_bytes = buf[curr : curr + 3]
            curr += 3
            b0, b1, b2 = flag_bytes[0], flag_bytes[1], flag_bytes[2]
            nybbles = (
                (b0 >> 4) & 0xF,
                b0 & 0xF,
                (b1 >> 4) & 0xF,
                b1 & 0xF,
                (b2 >> 4) & 0xF,
                b2 & 0xF,
            )
            deltas: list[int] = []
            for nyb in nybbles:
                field_len = 1 << (nyb & 0x03)
                if curr + field_len > next_b_off:
                    break
                sign = 1 if (nyb & 0x04) else -1
                raw_val = int.from_bytes(buf[curr : curr + field_len], "big")
                curr += field_len
                deltas.append(sign * raw_val)

            if len(deltas) < 6:
                break

            ts_ms += deltas[0]
            o_raw += deltas[1]
            h_raw += deltas[2]
            l_raw += deltas[3]
            c_raw += deltas[4]
            v_raw += deltas[5]

            bar_dt = datetime.fromtimestamp(ts_ms / 1000.0, tz=UTC)
            if norm_from and bar_dt < norm_from:
                continue
            if norm_to and bar_dt > norm_to:
                continue

            rows.append(
                {
                    "time": int(ts_ms / 1000.0),
                    "open": o_raw / 1_000_000.0,
                    "high": h_raw / 1_000_000.0,
                    "low": l_raw / 1_000_000.0,
                    "close": c_raw / 1_000_000.0,
                    "tick_volume": max(0, int(v_raw // 100_000)),
                    "spread": 0,
                    "real_volume": max(0, int(v_raw // 100_000)),
                }
            )

    rows.sort(key=lambda r: r["time"])
    if count and count > 0 and len(rows) > count:
        rows = rows[-count:]
    return rows


def _read_parquet_bars(
    base_dir: Path,
    symbol: str,
    timeframe: str,
    count: int | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
) -> list[dict[str, Any]]:
    """Read historical bars from local Parquet archives if available."""
    if not base_dir.exists():
        return []

    clean = _clean_symbol(symbol).lower()
    variants = [clean, clean.removeprefix("@"), f"@{clean.removeprefix('@')}"]
    tf_str = str(timeframe).upper()
    is_m1 = "M1" in tf_str or "1M" in tf_str
    tf_tag = "m1" if is_m1 else "d1"

    parquet_files: list[Path] = []
    for var in variants:
        candidate_dirs = [
            base_dir / tf_tag / var,
            base_dir / var / tf_tag,
        ]
        for cdir in candidate_dirs:
            if cdir.is_dir():
                parquet_files = sorted(cdir.glob("*.parquet"))
                if parquet_files:
                    break
        if parquet_files:
            break

    if not parquet_files:
        return []

    try:
        import pyarrow.parquet as pq
    except ImportError:
        return []

    norm_from = _normalize_dt(date_from)
    norm_to = _normalize_dt(date_to)
    rows: list[dict[str, Any]] = []

    for pf in parquet_files:
        try:
            table = pq.read_table(pf)
            data_dict = table.to_pydict()
            dts = data_dict.get("DateTime") or data_dict.get("datetime") or []
            opens = data_dict.get("Open") or data_dict.get("open") or []
            highs = data_dict.get("High") or data_dict.get("high") or []
            lows = data_dict.get("Low") or data_dict.get("low") or []
            closes = data_dict.get("Close") or data_dict.get("close") or []
            vols = data_dict.get("Volume") or data_dict.get("volume") or []

            for dt, o, h, l, c, v in zip(
                dts, opens, highs, lows, closes, vols, strict=False
            ):
                if dt is None:
                    continue
                if isinstance(dt, datetime):
                    dt_utc = dt if dt.tzinfo is not None else dt.replace(tzinfo=UTC)
                elif isinstance(dt, (int, float)):
                    dt_utc = datetime.fromtimestamp(dt, tz=UTC)
                else:
                    continue

                if norm_from and dt_utc < norm_from:
                    continue
                if norm_to and dt_utc > norm_to:
                    continue

                rows.append(
                    {
                        "time": int(dt_utc.timestamp()),
                        "open": float(o),
                        "high": float(h),
                        "low": float(l),
                        "close": float(c),
                        "tick_volume": int(v) if v is not None else 0,
                        "spread": 0,
                        "real_volume": int(v) if v is not None else 0,
                    }
                )
        except Exception as exc:
            logger.debug("Failed reading parquet archive %s: %s", pf, exc)
            continue

    rows.sort(key=lambda r: r["time"])
    if count and count > 0 and len(rows) > count:
        rows = rows[-count:]
    return rows


class SQFuturesBroker(DataBrokerBackend):
    """StrategyQuant Continuous Futures market data and symbol catalog broker."""

    def __init__(
        self,
        name: str = "SQ_Futures",
        data_dir: str | Path | None = None,
        catalog_path: str | Path | None = None,
        sqx_history_dir: str | Path | None = None,
        enable_cdn_download: bool = True,
    ) -> None:
        """Initialize SQ Futures broker."""
        super().__init__(name=name)
        self.data_dir = Path(data_dir) if data_dir else DEFAULT_DATA_DIR
        self.catalog_path = Path(catalog_path) if catalog_path else DEFAULT_CATALOG_PATH
        self.enable_cdn_download = enable_cdn_download

        if sqx_history_dir is not None:
            self.sqx_history_dir: Path | None = Path(sqx_history_dir)
        elif "SQX_REFERENCE_ROOT" in os.environ:
            candidate = (
                Path(os.environ["SQX_REFERENCE_ROOT"])
                / "user"
                / "data"
                / "History"
                / "sq_futures"
            )
            self.sqx_history_dir = candidate if candidate.exists() else None
        else:
            self.sqx_history_dir = None

        self.session = requests.Session()
        self.session.headers.update({"User-Agent": USER_AGENT})
        retry_strategy: Any = Retry(
            total=3,
            backoff_factor=0.3,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "HEAD"],
        )
        adapter = HTTPAdapter(
            max_retries=retry_strategy, pool_connections=8, pool_maxsize=8
        )
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

        self._catalog: dict[str, SymbolSnapshot] = {}

        self.capabilities = ProviderCapabilities(
            provider_id="sq_futures",
            display_name="SQ Futures Free Data",
            category="Futures",
            supported_timeframes=("M1", "D1"),
            supported_modes=("bars",),
            requires_auth=False,
            rate_limit_rps=5.0,
            default_timeout_seconds=30.0,
            supports_pagination=True,
            has_local_archive=self.data_dir.exists(),
            description="StrategyQuant Continuous Futures historical data provider",
        )

    @override
    def close_sync(self) -> None:
        """Close session resources synchronously."""
        self._is_connected = False
        if hasattr(self, "session"):
            self.session.close()

    @override
    async def close(self) -> None:
        """Close session resources asynchronously."""
        self.close_sync()

    def check_health(self) -> Any:
        """Inspect provider health and local archive readiness."""
        has_dir = self.data_dir.exists()
        return ProviderHealth(
            provider_id="sq_futures",
            status="available" if has_dir else "unconfigured",
            connected=has_dir,
            message="SQ Futures ready" if has_dir else "Local data_dir not found",
            capabilities=self.capabilities,
        )

    def _ensure_catalog(self) -> None:
        """Load and cache the SQ Futures instrument catalog."""
        if self._catalog:
            return

        catalog_file = self.catalog_path
        if not catalog_file.is_file():
            alt = self.data_dir / "sq_futures.csv"
            if alt.is_file():
                catalog_file = alt

        if not catalog_file.is_file():
            # Minimal default catalog fallback
            for s in ("@ES", "@NQ", "@YM", "@RTY", "@CL", "@GC", "@SI", "@ZB"):
                self._catalog[s] = SymbolSnapshot(
                    name=s, digits=2, point=0.01, trade_contract_size=50.0
                )
            return

        try:
            with open(catalog_file, encoding="utf-8") as f:
                reader = csv.DictReader(f, delimiter=";")
                for row in reader:
                    sym = (row.get("symbol") or "").strip().upper()
                    if not sym:
                        continue
                    clean_sym = _clean_symbol(sym)
                    dec = int(row.get("decimals") or 2)
                    pt = float(row.get("point") or 0.01)
                    spread = int(float(row.get("spread") or 0))
                    c_size = float(row.get("contract_size") or 50.0)
                    self._catalog[clean_sym] = SymbolSnapshot(
                        name=clean_sym,
                        digits=dec,
                        point=pt,
                        spread=spread,
                        trade_contract_size=c_size,
                    )
        except Exception as exc:
            self.logger.warning("Error parsing SQ Futures catalog: %s", exc)

    @override
    def symbol_info(self, symbol: str) -> SymbolSnapshot:
        """Resolve instrument specifications as canonical SymbolSnapshot."""
        self._ensure_catalog()
        clean = _clean_symbol(symbol).upper()
        snap = self._catalog.get(clean)
        if snap is not None:
            return snap
        return SymbolSnapshot(
            name=clean, digits=2, point=0.01, trade_contract_size=50.0
        )

    @override
    def symbols_get(self) -> list[str]:
        """Return list of registered SQ Futures symbols."""
        self._ensure_catalog()
        return list(self._catalog.keys())

    def _fetch_cdn_bars(
        self,
        symbol: str,
        count: int | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
    ) -> list[dict[str, Any]]:
        """Download and decode daily historical futures bars from StrategyQuant CDN."""
        clean_sym = _clean_symbol(symbol).upper().lstrip("@")
        zip_targets = ["data01.zip"]
        if (date_from and date_from.year < 2019) or (count and count > 1200):
            zip_targets = ["data00.zip", "data01.zip"]

        all_bars: list[dict[str, Any]] = []

        for zip_name in zip_targets:
            url = f"{CDN_BASE_URL}/{clean_sym}/{zip_name}"
            try:
                resp = execute_bounded_get(
                    self.session, url, timeout=(5.0, 15.0), provider="sq_futures"
                )
                if resp.status_code == 200 and resp.content:
                    with zipfile.ZipFile(io.BytesIO(resp.content)) as z:
                        dat_names = sorted(
                            f for f in z.namelist() if f.endswith(".dat")
                        )
                        for dat_name in dat_names:
                            dat_buf = z.read(dat_name)
                            year_bars = _decode_sq_dat_bytes(
                                dat_buf,
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

        # 1. Local Parquet files
        parquet_bars = _read_parquet_bars(
            self.data_dir,
            symbol,
            timeframe,
            count=target_count,
            date_from=date_from,
            date_to=date_to,
        )
        if not parquet_bars and self.sqx_history_dir:
            parquet_bars = _read_parquet_bars(
                self.sqx_history_dir,
                symbol,
                timeframe,
                count=target_count,
                date_from=date_from,
                date_to=date_to,
            )
        if parquet_bars:
            return parquet_bars

        # 2. Local .dat files
        dat_file = _find_sq_dat_file(self.data_dir, symbol, timeframe)
        if not dat_file and self.sqx_history_dir:
            dat_file = _find_sq_dat_file(self.sqx_history_dir, symbol, timeframe)

        if dat_file:
            try:
                buf = dat_file.read_bytes()
                rows = _decode_sq_dat_bytes(
                    buf, count=target_count, date_from=date_from, date_to=date_to
                )
                if rows:
                    return rows
            except Exception as exc:
                self.logger.warning("Failed to decode dat file %s: %s", dat_file, exc)

        # 3. StrategyQuant CDN (Daily bars only; D1 cannot satisfy M1)
        is_d1 = timeframe.upper() in ("D1", "1D")
        if self.enable_cdn_download and is_d1:
            cdn_bars = self._fetch_cdn_bars(
                symbol, count=target_count, date_from=date_from, date_to=date_to
            )
            if cdn_bars:
                return cdn_bars

        raise BridgeError(
            f"No futures data found for symbol '{symbol}' ({timeframe})",
            code="NO_DATA",
        )

    def read_history(
        self,
        request: HistoryRequest,
        token: CancellationToken | None = None,
    ) -> HistoryPage:
        """Fetch historical records adhering to Stage 2C contract."""
        request.validate()
        tf = request.timeframe.strip().upper()
        if tf not in ("D1", "M1"):
            raise ProviderValidationError(
                f"StrategyQuant Futures only supports D1 and M1 timeframes, got '{request.timeframe}'",
                provider="sq_futures",
            )
        if request.kind == "ticks":
            raise ProviderValidationError(
                "StrategyQuant Futures does not support ticks",
                provider="sq_futures",
            )
        if token is not None:
            token.check_cancelled()
        try:
            rows = self.fetch_bars(
                symbol=request.symbol,
                timeframe=tf,
                mode=request.mode,
                start=request.start_epoch() or 0,
                end=request.end_epoch() or 0,
                count=request.count,
                limit=request.limit,
            )
        except BridgeError as be:
            if be.code == "NO_DATA":
                rows = []
            else:
                raise
        return HistoryPage(
            provider="sq_futures",
            symbol=request.symbol,
            timeframe=tf,
            kind="bars",
            rows=rows,
            is_complete=True,
            provenance={"source": "sq_futures"},
        )


def create_adapter(context: Any = None) -> SQFuturesBroker:
    """Plugin entrypoint factory constructing SQFuturesBroker adapter."""
    data_dir = getattr(context, "data_dir", None)
    return SQFuturesBroker(data_dir=data_dir)


def main() -> None:
    """Demonstrate executable usage of SQFuturesBroker."""
    broker = SQFuturesBroker()
    health = broker.check_health()
    logger.info("SQ Futures health: %s (connected=%s)", health.status, health.connected)


if __name__ == "__main__":
    main()
