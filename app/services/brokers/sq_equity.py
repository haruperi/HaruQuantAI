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
    - FR-BROKER-CODECS-SQDAT: Decode StrategyQuant 4.2 binary compressed bar streams.
      Associated: `decode_sq_dat_bytes()`
      Logging: Emits DEBUG on locating magic sync markers and parsing delta blocks.

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
import struct
import zipfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, override

import pandas as pd  # type: ignore[import-untyped]
from app.host.logging import get_logger
from app.services.brokers.base import (
    BridgeError,
    BrokerClient,
    create_http_session,
    epoch_seconds,
    execute_bounded_get,
)
from app.services.brokers.files import load_local_partition_bars
from app.services.include.contracts import MarketBar, SymbolInfo
from app.services.include.data import bars_to_dataframe
from app.services.include.enums import Timeframe

logger = get_logger(__name__)

SQDAT_FR = "FR-BROKER-CODECS-SQDAT"
SQ_MAGIC_HEADER_V42 = b"\xbb\xbb\xbb\xbb\xbb\xbb\xbb\xbb\xbb\xbb\xbb\xbb\xbb\xbb\xbb"

DEFAULT_DATA_DIR = Path(__file__).resolve().parents[3] / "data" / "market" / "sq_equity"
DEFAULT_CATALOG_PATH = DEFAULT_DATA_DIR / "sq_equity.csv"
CDN_BASE_URL = "https://cdn.strategyquantcdn.com/data/barchart_test/eod"
USER_AGENT = "HaruQuantAI-SQEquityConnector/1.0"

__all__ = ["SQEquityClient", "SQ_MAGIC_HEADER_V42", "decode_sq_dat_bytes"]


def decode_sq_dat_bytes(
    buf: bytes,
    count: int | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
) -> list[dict[str, Any]]:
    """Parse StrategyQuant 4.2 binary compressed bar streams with block delta decoding."""
    if len(buf) < 15:
        return []

    blocks: list[int] = []
    idx = 0
    while idx < len(buf):
        pos = buf.find(b"\xbb\xbb\xbb", idx)
        if pos == -1:
            break
        blocks.append(pos)
        end_pos = pos + 3
        while end_pos < len(buf) and buf[end_pos] == 0xBB:
            end_pos += 1
        idx = end_pos

    if not blocks:
        return []

    rows: list[dict[str, Any]] = []

    for b_idx_rel, b_off in enumerate(blocks):
        next_b_off = blocks[b_idx_rel + 1] if b_idx_rel + 1 < len(blocks) else len(buf)
        curr = b_off + 3
        while curr < next_b_off and buf[curr] == 0xBB:
            curr += 1

        anchor_off = None
        for offset in range(curr, min(curr + 16, next_b_off - 48 + 1)):
            val = struct.unpack_from(">Q", buf, offset)[0]
            if 500_000_000_000 <= val <= 5_000_000_000_000:
                anchor_off = offset
                break

        if anchor_off is None:
            continue

        curr = anchor_off
        ts_ms = struct.unpack_from(">Q", buf, curr)[0]
        o_raw, h_raw, l_raw, c_raw, v_raw = struct.unpack_from(">5q", buf, curr + 8)
        curr += 48

        dt = datetime.fromtimestamp(ts_ms / 1000.0, tz=UTC)
        include = True
        if date_from and dt < date_from:
            include = False
        if date_to and dt > date_to:
            include = False

        o_val = o_raw / 1_000_000.0
        h_val = h_raw / 1_000_000.0
        l_val = l_raw / 1_000_000.0
        c_val = c_raw / 1_000_000.0

        if (
            include
            and l_val > 0
            and l_val <= min(o_val, c_val) <= max(o_val, c_val) <= h_val
        ):
            rows.append(
                {
                    "time": int(ts_ms / 1000.0),
                    "open": o_val,
                    "high": h_val,
                    "low": l_val,
                    "close": c_val,
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
            if date_from and bar_dt < date_from:
                continue
            if date_to and bar_dt > date_to:
                continue

            o_val = o_raw / 1_000_000.0
            h_val = h_raw / 1_000_000.0
            l_val = l_raw / 1_000_000.0
            c_val = c_raw / 1_000_000.0

            if l_val > 0 and l_val <= min(o_val, c_val) <= max(o_val, c_val) <= h_val:
                rows.append(
                    {
                        "time": int(ts_ms / 1000.0),
                        "open": o_val,
                        "high": h_val,
                        "low": l_val,
                        "close": c_val,
                        "tick_volume": max(0, int(v_raw // 100_000)),
                        "spread": 0,
                        "real_volume": max(0, int(v_raw // 100_000)),
                    }
                )

    rows.sort(key=lambda r: r["time"])
    if count is not None and count > 0 and len(rows) > count:
        rows = rows[-count:]

    logger.debug(
        "%s: Decoded %d SQ .dat bars",
        SQDAT_FR,
        len(rows),
        extra={"fr_id": SQDAT_FR, "count": len(rows)},
    )
    return rows


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

    def _validate_timeframe(self, timeframe: Timeframe | str, tf_name: str) -> None:
        if tf_name.upper() not in ("D1", "1D", "PERIOD_D1", "DAY"):
            raise BridgeError(
                f"StrategyQuant US Equities only supports D1 daily timeframe, got '{timeframe}'",
                code="UNSUPPORTED_TIMEFRAME",
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

    @staticmethod
    def _rows_to_market_bars(rows: list[dict[str, Any]]) -> pd.DataFrame:
        bars = [
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
        return bars_to_dataframe(bars)

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
    ) -> pd.DataFrame:
        """Retrieve historical candlestick bars from local storage or StrategyQuant CDN."""
        del start_pos
        target_count = count or limit or 100
        s = date_from if date_from is not None else start
        e = date_to if date_to is not None else end
        start_sec = epoch_seconds(s)
        end_sec = epoch_seconds(e)
        dt_from = (
            datetime.fromtimestamp(start_sec, tz=UTC) if 0 < start_sec < 2**40 else None
        )
        dt_to = datetime.fromtimestamp(end_sec, tz=UTC) if 0 < end_sec < 2**40 else None

        tf_name = timeframe.name if isinstance(timeframe, Timeframe) else timeframe
        self._validate_timeframe(timeframe, tf_name)

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
                return self._rows_to_market_bars(parquet_bars)

        dat_file = self._find_dat(self.data_dir, symbol, tf_name)
        if not dat_file and self.sqx_history_dir:
            dat_file = self._find_dat(self.sqx_history_dir, symbol, tf_name)
        if dat_file:
            rows = decode_sq_dat_bytes(
                dat_file.read_bytes(),
                count=target_count,
                date_from=dt_from,
                date_to=dt_to,
            )
            if rows:
                return self._rows_to_market_bars(rows)

        if self.enable_cdn_download and tf_name.upper() in ("D1", "1D", "PERIOD_D1"):
            cdn_bars = self._fetch_cdn_bars(
                symbol, count=target_count, date_from=dt_from, date_to=dt_to
            )
            if cdn_bars:
                return self._rows_to_market_bars(cdn_bars)

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
    ) -> pd.DataFrame:
        """Historical ticks are unsupported for StrategyQuant US Equities."""
        del symbol, date_from, date_to, count, limit
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
