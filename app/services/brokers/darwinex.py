"""Darwinex institutional market data and symbol catalog client implementation.

Description:
    Implements an unauthenticated market data and symbol metadata client
    for Darwinex conforming to the uniform `BrokerClient` interface.
    Fetches historical candlestick bars and ticks in memory from StrategyQuant CDN
    or local archives, and dynamically resolves instrument specifications from the
    authoritative catalog CSV (`data/market/darwinex/darwinex.csv`) returning canonical
    `SymbolInfo`.

Purpose:
    FEAT-BROKER-DARWINEX: Darwinex Market Data and Symbol Catalog Provider.

Key Capabilities:
    - FR-BROKER-DARWINEX-MARKET-DATA: Historical Candlestick Bars and Ticks
      Associated: `[DarwinexClient.get_bars()]`, `[DarwinexClient.get_ticks()]`
      Logging: Emits INFO log upon successfully downloading and parsing bars with
      extracted count, and WARNING log on network failure.
    - FR-BROKER-DARWINEX-SYMBOLS: Authoritative Symbol Catalog Resolution
      Associated: `[DarwinexClient.get_symbol_info()]`, `[DarwinexClient.get_symbols()]`
      Logging: Emits INFO log upon catalog parsing, and WARNING if symbol is not found.

Python API Usage:
    ```python
    from app.services.brokers.darwinex import DarwinexClient
    from app.services.include.enums import Timeframe

    client = DarwinexClient()
    bars = client.get_bars("EURUSD", Timeframe.PERIOD_D1, count=5)
    assert len(bars) > 0
    client.disconnect()
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
from app.host.logging import get_logger
from app.services.brokers._file_history import (
    find_matching_partitions,
    parse_delimited_bars,
    read_parquet_bars,
)
from app.services.brokers._http import create_http_session, execute_bounded_get
from app.services.brokers._native_history import decode_darwinex_dat
from app.services.brokers.base import (
    BridgeError,
    BrokerClient,
    epoch_millis,
    epoch_seconds,
)
from app.services.include.contracts import MarketBar, MarketTick, SymbolInfo
from app.services.include.enums import Timeframe

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

__all__ = ["DarwinexClient"]


class DarwinexClient(BrokerClient):
    """Darwinex market data and symbol catalog client."""

    def __init__(
        self,
        name: str = "Darwinex",
        catalog_path: str | Path | None = None,
        session: requests.Session | None = None,
        data_dir: str | Path | None = None,
    ) -> None:
        """Initialize Darwinex broker client."""
        super().__init__(name=name)
        self.catalog_path = Path(catalog_path) if catalog_path else DEFAULT_CATALOG_PATH
        self.data_dir = Path(data_dir) if data_dir else None
        self.session = session or create_http_session(
            USER_AGENT, retries=3, backoff=0.3
        )
        self._catalog: dict[str, SymbolInfo] = {}
        self._connected = True

    def _ensure_catalog(self) -> None:
        """Parse and cache symbol definitions from CSV catalog."""
        if self._catalog:
            return
        if not self.catalog_path.exists():
            raise BridgeError(
                f"Darwinex symbol catalog not found at {self.catalog_path}",
                code="CATALOG_NOT_FOUND",
            )

        with open(self.catalog_path, encoding="latin1") as f:
            for line_num, line in enumerate(f, start=1):
                line_str = line.strip()
                if not line_str:
                    continue
                parts = line_str.split(";")
                if len(parts) < 8:
                    raise BridgeError(
                        f"Malformed row {line_num} in Darwinex catalog {self.catalog_path}",
                        code="CATALOG_PARSE_ERROR",
                    )
                sym = parts[0].strip().upper()
                try:
                    dec = int(parts[2].strip())
                    contract_sz = float(parts[3].strip())
                    point_sz = float(parts[6].strip())
                    spread = float(parts[7].strip())
                except ValueError as exc:
                    raise BridgeError(
                        f"Invalid numeric field at row {line_num} in Darwinex catalog {self.catalog_path}: {exc}",
                        code="CATALOG_PARSE_ERROR",
                    ) from exc

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

    @override
    def get_symbol_info(self, symbol: str) -> SymbolInfo:
        """Retrieve instrument specifications as canonical SymbolInfo."""
        self._ensure_catalog()
        sym_clean = symbol.upper().replace("/", "").replace("_", "").replace("-", "")
        snap = self._catalog.get(sym_clean)
        if snap is not None:
            return snap
        raise BridgeError(
            f"Symbol '{symbol}' not found in Darwinex catalog",
            code="SYMBOL_NOT_FOUND",
        )

    @override
    def get_symbols(self) -> list[str]:
        """Return list of symbol names available in catalog."""
        self._ensure_catalog()
        return list(self._catalog.keys())

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
        """Download candlestick bars from local archives or Darwinex CDN."""
        del start_pos
        self._ensure_catalog()
        sym_clean = symbol.upper().replace("/", "").replace("_", "").replace("-", "")
        snap = self.get_symbol_info(sym_clean)
        decimals = snap.digits
        target_count = count or limit or 100

        tf_name = timeframe.name if isinstance(timeframe, Timeframe) else timeframe
        tf_norm = tf_name.strip().upper()
        if tf_norm in ("D1", "PERIOD_D1"):
            clean_tf = "D1"
            period_sec = 86400
        elif tf_norm in ("M1", "PERIOD_M1"):
            clean_tf = "M1"
            period_sec = 60
        else:
            raise BridgeError(
                f"Darwinex only supports M1 and D1 bar aggregation, got '{timeframe}'",
                code="UNSUPPORTED_TIMEFRAME",
            )

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

        # Check local data_dir
        if self.data_dir and self.data_dir.exists():
            matched = find_matching_partitions(self.data_dir, sym_clean, clean_tf)
            all_local: list[dict[str, Any]] = []
            for p in matched:
                if p.suffix.lower() == ".parquet":
                    all_local.extend(read_parquet_bars(p, count=target_count))
                elif p.suffix.lower() in (".csv", ".tsv", ".txt"):
                    all_local.extend(
                        parse_delimited_bars(
                            p.read_text(encoding="utf-8", errors="replace"),
                            sym_clean,
                            clean_tf,
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
                    selected = filtered[-target_count:] if target_count else filtered
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
                        for r in selected
                    ]

        start_year = date_from.year if date_from else 2023
        end_year = date_to.year if date_to else start_year
        years = list(range(start_year, min(end_year, start_year + 3) + 1))
        buckets: dict[int, dict[str, Any]] = {}

        for target_year in years:
            url = f"{CDN_BASE_URL}/{sym_clean}/{target_year}.zip"
            resp = execute_bounded_get(
                self.session,
                url,
                timeout=(10.0, 60.0),
                provider="darwinex",
                max_bytes=100 * 1024 * 1024,
            )
            if resp.status_code != 200 or not resp.content:
                raise BridgeError(
                    f"Darwinex CDN HTTP {resp.status_code} for '{sym_clean}' ({target_year})",
                    code="DOWNLOAD_ERROR",
                )

            with zipfile.ZipFile(io.BytesIO(resp.content)) as z:
                dat_names = sorted([n for n in z.namelist() if n.endswith(".dat")])
                if date_from or date_to:
                    filtered_names: list[str] = []
                    for name in dat_names:
                        stem = Path(name).stem
                        dt_parts = [int(x) for x in stem.split("_")]
                        f_dt = datetime(
                            dt_parts[0],
                            dt_parts[1],
                            dt_parts[2],
                            tzinfo=UTC,
                        )
                        if date_from and f_dt.date() < date_from.date():
                            continue
                        if date_to and f_dt.date() > date_to.date():
                            continue
                        filtered_names.append(name)
                    dat_names = filtered_names
                elif target_count and target_count > 0:
                    slice_count = (
                        max(target_count * 2, 10)
                        if clean_tf == "D1"
                        else max(target_count // 30, 2)
                    )
                    dat_names = dat_names[-slice_count:]

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
                                "spread": max(
                                    0,
                                    round(
                                        (float(t["ask"]) - float(t["bid"]))
                                        * (10**decimals)
                                    ),
                                ),
                                "real_volume": 1,
                            }
                        else:
                            b = buckets[bucket_time]
                            b["high"] = max(b["high"], mid_p)
                            b["low"] = min(b["low"], mid_p)
                            b["close"] = mid_p
                            b["tick_volume"] += 1
                            b["real_volume"] += 1

        if not buckets:
            raise BridgeError(
                f"No bars available for '{sym_clean}' from Darwinex CDN",
                code="NO_DATA",
            )

        rows = [buckets[k] for k in sorted(buckets.keys())]
        if target_count and len(rows) > target_count:
            rows = rows[-target_count:]
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

    @override
    def get_ticks(
        self,
        symbol: str,
        date_from: datetime | int | None = None,
        date_to: datetime | int | None = None,
        *,
        start: datetime | int | None = None,
        end: datetime | int | None = None,
        count: int | None = None,
        limit: int = 1000,
    ) -> list[MarketTick]:
        """Download tick data from local archives or Darwinex CDN."""
        self._ensure_catalog()
        sym_clean = symbol.upper().replace("/", "").replace("_", "").replace("-", "")
        snap = self.get_symbol_info(sym_clean)
        decimals = snap.digits
        target_count = count or limit or 100
        s = date_from if date_from is not None else start
        e = date_to if date_to is not None else end
        start_ms = epoch_millis(s)
        end_ms = epoch_millis(e)

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

        for target_year in years:
            url = f"{CDN_BASE_URL}/{sym_clean}/{target_year}.zip"
            resp = execute_bounded_get(
                self.session,
                url,
                timeout=(5.0, 30.0),
                provider="darwinex",
            )
            if resp.status_code != 200 or not resp.content:
                raise BridgeError(
                    f"Darwinex CDN HTTP {resp.status_code} for '{sym_clean}' ({target_year})",
                    code="DOWNLOAD_ERROR",
                )

            with zipfile.ZipFile(io.BytesIO(resp.content)) as z:
                dat_names = sorted([n for n in z.namelist() if n.endswith(".dat")])
                for name in dat_names:
                    dat_bytes = z.read(name)
                    ticks = decode_darwinex_dat(dat_bytes, digits=decimals)
                    for t in ticks:
                        if start_ms > 0 and t["time_msc"] < start_ms:
                            continue
                        if end_ms > 0 and t["time_msc"] > end_ms:
                            continue
                        all_ticks.append(t)

        if not all_ticks:
            raise BridgeError(
                f"No ticks available for '{sym_clean}' from Darwinex CDN",
                code="NO_DATA",
            )

        all_ticks.sort(key=lambda r: r["time_msc"])
        if target_count and len(all_ticks) > target_count:
            all_ticks = all_ticks[-target_count:]
        return [
            MarketTick(
                time_msc=int(t["time_msc"]),
                bid=float(t["bid"]),
                ask=float(t["ask"]),
                last=float(t.get("last", t["bid"])),
                volume=int(t.get("volume", 1)),
                flags=int(t.get("flags", 0)),
                volume_real=float(t.get("volume_real", 1.0)),
            )
            for t in all_ticks
        ]


def main() -> None:
    """Demonstrate executable usage of DarwinexClient."""
    client = DarwinexClient()
    symbols = client.get_symbols()
    logger.info("Darwinex catalog symbols: %d available", len(symbols))
    client.disconnect()


if __name__ == "__main__":
    main()
