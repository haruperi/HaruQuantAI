# ruff: noqa: INP001, PLR2004 -- source namespace and binary constants
"""Tick Downloader binary imports using owner-script numerical policies.

Description:
    Decodes supplied hourly BI5 bytes, preserves canonical source values and
    publishes immutable partitions through host custody.
Purpose:
    FEAT-DM-TICK_DOWNLOADER: Real Tick Downloader file acquisition.
Key Capabilities:
    - FR-TD-DECODE: Source big-endian decoding, logged per-file rows.
    - FR-TD-PUBLISH: Host-owned partition publication, logged revisions.
Python API Usage:
    contribution = await prepare(capabilities)
    await contribution.invoke("import.start", request)
CLI Usage:
    uv run pytest tests/plugin/DataSource/test_tick_downloader.py --no-cov
"""

from __future__ import annotations

import asyncio
import base64
import dataclasses
import lzma
import re
import struct
from datetime import UTC, datetime, timedelta
from typing import Any, Literal, cast

import numpy as np
import numpy.typing as npt
import pandas as pd  # type: ignore[import-untyped]
import pyarrow as pa  # type: ignore[import-untyped]
from app.host.capabilities import HostCapabilities, JobAccess, MarketAccess
from app.host.contracts import Document
from app.host.jobs import Budget
from app.host.logging import get_logger
from app.host.packages import PreparedContribution
from pydantic import Field, JsonValue

logger = get_logger(__name__)


def _decompress_bi5(data: bytes) -> bytes:
    """Source ALONE/header-repair/raw fallbacks, bounded before allocation."""
    if len(data) < 5:
        raise ValueError("Empty or truncated BI5 input")
    candidates = (
        (data, lzma.FORMAT_ALONE, None),
        (data[:5] + struct.pack("<Q", 2**64 - 1) + data[5:], lzma.FORMAT_ALONE, None),
        (data, lzma.FORMAT_RAW, [{"id": lzma.FILTER_LZMA1}]),
    )
    for content, mode, filters in candidates:
        try:
            decoder = lzma.LZMADecompressor(format=mode, filters=filters)
            result = decoder.decompress(content, max_length=128 * 1024 * 1024)
            if not decoder.eof:
                logger.warning("BI5 decompression incomplete or above limit")
                continue
            return result
        except lzma.LZMAError, ValueError:
            logger.debug("BI5 encoding fallback: format=%d", mode)
    raise ValueError("Corrupt or oversized BI5 input")


class TickFile(Document):
    """Uploaded content with explicit UTC hour and source decimal metadata."""

    content_base64: str = Field(min_length=1, max_length=8 * 1024 * 1024)
    hour: datetime


def symbol_decimals(symbol: str) -> int:
    """Resolve source catalog precision, then the script's explicit fallbacks."""
    clean = symbol.upper().replace("/", "").replace("_", "").replace("-", "")
    for suffix in ("_TD", "_RAW", "TD", "_DUKASCOPY"):
        if clean.endswith(suffix) and clean[: -len(suffix)] in SYMBOL_DECIMALS:
            clean = clean[: -len(suffix)]
            break
    if clean in SYMBOL_DECIMALS:
        return SYMBOL_DECIMALS[clean]
    if clean.endswith("JPY") or clean.startswith(("XAU", "GOLD", "XAG", "SILVER")):
        return 3
    if clean.startswith(("BTC", "ETH", "SOL")):
        return 2
    if any(
        token in clean
        for token in (
            "IDX",
            "500",
            "30",
            "100",
            "40",
            "2000",
            "DOW",
            "NAS",
            "DAX",
            "SPX",
            "CMD",
            "BRENT",
            "WTI",
            "OIL",
            "GAS",
        )
    ):
        return 3
    return 5


def inspect_paths(paths: list[str]) -> list[dict[str, Any]]:
    """Interpret logical uploaded TD paths with zero-based source month folders."""
    if not paths or len(paths) > 20000:
        raise ValueError("Select at most 20000 Tick Downloader files")
    result = []
    for path in paths:
        parts = path.replace("\\", "/").split("/")
        if any(part in ("", ".", "..") or ":" in part for part in parts):
            raise ValueError("Invalid uploaded relative path")
        match = re.fullmatch(r"([0-9]{2})(?:h_ticks)?\.bi5", parts[-1], re.IGNORECASE)
        if len(parts) < 6 or match is None:
            continue
        symbol, year, month, day = parts[-5:-1]
        hour = datetime(int(year), int(month) + 1, int(day), int(match[1]), tzinfo=UTC)
        result.append(
            {
                "path": path,
                "symbol": symbol,
                "hour": hour.isoformat(),
                "decimals": symbol_decimals(symbol),
            }
        )
    logger.info("Tick Downloader paths inspected: files=%d", len(result))
    return result


class TickImport(Document):
    """Bounded hourly batch; UI can submit successive batches without fake work."""

    symbol: str = Field(min_length=1, max_length=80, pattern=r"^[A-Za-z0-9_.-]+$")
    postfix: str = Field(default="", max_length=40, pattern=r"^[A-Za-z0-9_.-]*$")
    decimals: int = Field(ge=0, le=9)
    timeframe: Literal["TICK", "M1"] = "TICK"
    candle_type: Literal["BID", "ASK"] = "BID"
    files: tuple[TickFile, ...] = Field(min_length=1, max_length=128)


@dataclasses.dataclass
class TickRuntime:
    """Prepared decoder with exclusively host-owned jobs and persistence."""

    market: MarketAccess
    jobs: JobAccess
    progress: dict[str, dict[str, Any]] = dataclasses.field(default_factory=dict)

    async def acquire(self, request: TickImport, progress: dict[str, Any]) -> None:
        """Decode actual bytes and retain source incoming-first merge semantics."""
        frames = []
        for uploaded in sorted(request.files, key=lambda row: row.hour):
            hour = uploaded.hour
            if (
                hour.tzinfo is None
                or hour.utcoffset() != timedelta(0)
                or hour.minute
                or hour.second
                or hour.microsecond
            ):
                raise ValueError("BI5 input requires a complete UTC base hour")
            decoded = await self.jobs.offload(
                _read_tick_file,
                base64.b64decode(uploaded.content_base64, validate=True),
                hour,
                request.decimals,
            )
            if decoded is None:
                raise ValueError("BI5 file contains no complete tick records")
            stamps, asks, bids, ask_vols, bid_vols = decoded
            if request.timeframe == "M1":
                frame = _ticks_to_m1(
                    stamps, asks, bids, ask_vols, bid_vols, request.candle_type
                )
            else:
                frame = pd.DataFrame(
                    {
                        "timestamp": pd.to_datetime(stamps, unit="ms", utc=True),
                        "ask": asks,
                        "bid": bids,
                        "ask_volume": ask_vols,
                        "bid_volume": bid_vols,
                    }
                )
            frames.append(frame)
            progress["rows"] += len(frame)
            if progress["rows"] > 2_000_000:
                raise ValueError("Choose a smaller BI5 import batch")
            progress["completed_files"] += 1
            logger.info("Tick Downloader decoded: rows=%d", len(frame))
            await asyncio.sleep(0)
        frame = pd.concat(frames).sort_values("timestamp")
        dataset_id = self.market.register_source(
            source="TickDownloader",
            symbol=request.symbol + request.postfix,
            underlying=request.symbol,
            instrument=request.symbol,
            timeframe=request.timeframe,
            options={"decimals": request.decimals, "candle_type": request.candle_type},
        )
        progress["dataset_id"] = dataset_id
        revisions = {
            row["period"]: row for row in self.market.source_partitions(dataset_id)
        }
        periods = frame["timestamp"].dt.strftime(
            "%Y-%m" if request.timeframe == "TICK" else "%Y"
        )
        for period, incoming in frame.groupby(periods):
            table = (
                _dataframe_to_canonical_ticks(incoming)
                if request.timeframe == "TICK"
                else _dataframe_to_canonical_m1(incoming)
            )
            prior = revisions.get(str(period))
            if prior:
                combined = pa.concat_tables(
                    [table, self.market.read_source_partition(dataset_id, str(period))]
                )
                stamps = combined.column("DateTime").cast(pa.int64()).to_numpy()
                _, indices = np.unique(stamps, return_index=True)
                table = combined.take(pa.array(indices[np.argsort(stamps[indices])]))
            self.market.publish_source(
                dataset_id,
                str(period),
                table,
                expected_revision=prior["revision"] if prior else 0,
            )
            progress["published_partitions"] += 1
            logger.info(
                "Tick Downloader published: dataset=%s period=%s", dataset_id, period
            )
            await asyncio.sleep(0)

    async def invoke(self, operation: str, payload: JsonValue) -> JsonValue:
        """Expose real import admission, catalog and host job state."""
        logger.info("Tick Downloader operation: %s", operation)
        values = payload if isinstance(payload, dict) else {}
        if operation == "inspect":
            paths = values.get("paths", [])
            if not isinstance(paths, list) or not all(
                isinstance(path, str) for path in paths
            ):
                raise ValueError("Expected uploaded relative file paths")
            return cast("JsonValue", {"files": inspect_paths(cast("list[str]", paths))})
        if operation == "catalog":
            available = self.market.source_available()
            return cast(
                "JsonValue",
                {
                    "available": available,
                    "reason": ""
                    if available
                    else "Script-backed catalog migration is required",
                    "datasets": self.market.source_definitions() if available else [],
                    "schema": TickImport.model_json_schema(),
                },
            )
        if operation == "import.start":
            request = TickImport.model_validate(values)
            if sum(len(row.content_base64) for row in request.files) > 8 * 1024 * 1024:
                raise ValueError("BI5 batch exceeds upload limit")
            progress: dict[str, Any] = {
                "rows": 0,
                "published_partitions": 0,
                "completed_files": 0,
                "total_files": len(request.files),
            }

            async def run() -> None:
                await self.acquire(request, progress)

            job = self.jobs.submit(Budget(1, 512 * 1024 * 1024, 3600), run)
            self.progress[job.id] = progress
            return {"job_id": job.id, "state": job.state}
        if operation in ("import.status", "import.cancel"):
            job_id = str(values.get("job_id", ""))
            if operation == "import.cancel":
                self.jobs.cancel(job_id)
            job = self.jobs.status(job_id)
            return cast(
                "JsonValue",
                {"job_id": job.id, "state": job.state, **self.progress[job.id]},
            )
        raise ValueError("Unknown Tick Downloader operation")

    async def close(self) -> None:
        """Await owned jobs before releasing source state."""
        await self.jobs.close()
        logger.info("Tick Downloader source closed")


async def prepare(context: HostCapabilities) -> PreparedContribution:
    """Bind custody and jobs with no ambient file lookup."""
    if context.market_data is None or context.jobs is None:
        raise ValueError("Tick Downloader requires market and jobs capabilities")
    runtime = TickRuntime(context.market_data, context.jobs)
    return PreparedContribution(
        ("catalog", "inspect", "import.start", "import.status", "import.cancel"),
        runtime.invoke,
        runtime.close,
    )


PLUGIN = {
    "id": "plugin.data_manager.tick_downloader",
    "kind": "plugin",
    "version": "1.0.0",
    "compatibility": "1",
    "owner_workspace_id": "workspace.data_manager",
    "slot_id": "data_source.acquisition",
    "contract_version": "1.0.0",
    "requires": [
        {"id": "host.market_data", "version": "1.0.0"},
        {"id": "host.jobs", "version": "1.0.0"},
    ],
}


TICK_SCHEMA = pa.schema(
    [
        pa.field("DateTime", pa.timestamp("ms", tz="UTC"), nullable=False),
        pa.field("Ask", pa.int64(), nullable=False),
        pa.field("Bid", pa.int64(), nullable=False),
        pa.field("Volume", pa.uint64(), nullable=False),
    ]
)

M1_SCHEMA = pa.schema(
    [
        pa.field("DateTime", pa.timestamp("ms", tz="UTC"), nullable=False),
        pa.field("Open", pa.float64(), nullable=False),
        pa.field("High", pa.float64(), nullable=False),
        pa.field("Low", pa.float64(), nullable=False),
        pa.field("Close", pa.float64(), nullable=False),
        pa.field("Volume", pa.uint64(), nullable=False),
    ]
)

TICK_DTYPE = np.dtype(
    [
        ("offset_ms", ">i4"),
        ("ask", ">i4"),
        ("bid", ">i4"),
        ("ask_vol", ">f4"),
        ("bid_vol", ">f4"),
    ]
)


def _read_tick_file(
    raw_bytes: bytes, base_dt: datetime, decimals: int
) -> tuple[npt.NDArray[Any], ...] | None:
    """Decode one uploaded hour using source price and float32 volume rules."""
    decomp = _decompress_bi5(raw_bytes)
    if not decomp or len(decomp) % 20 != 0:
        return None
    arr = np.frombuffer(decomp, dtype=TICK_DTYPE)
    if len(arr) == 0:
        return None
    price_factor = 10.0 ** (-decimals)
    base_ms = np.int64(int(base_dt.timestamp() * 1000))
    timestamps_ms = base_ms + arr["offset_ms"].astype(np.int64)
    asks = np.round(arr["ask"] * price_factor, decimals)
    bids = np.round(arr["bid"] * price_factor, decimals)
    ask_vols = np.round(arr["ask_vol"] * 1000000.0, 2)
    bid_vols = np.round(arr["bid_vol"] * 1000000.0, 2)
    return (timestamps_ms, asks, bids, ask_vols, bid_vols)


def _ticks_to_m1(  # noqa: PLR0917 -- retained source array signature.
    ts_ms: npt.NDArray[Any],
    asks: npt.NDArray[Any],
    bids: npt.NDArray[Any],
    ask_vols: npt.NDArray[Any],
    bid_vols: npt.NDArray[Any],
    candle_type: str = "BID",
) -> pd.DataFrame:
    """Preserve the owner script's canonical data transformation."""
    if len(ts_ms) == 0:
        return pd.DataFrame(
            columns=["timestamp", "open", "high", "low", "close", "volume"]
        )
    prices = asks if candle_type.upper() == "ASK" else bids
    total_vol = ask_vols + bid_vols
    minute_ts = ts_ms // 60000 * 60000
    unique_minutes, first_indices = np.unique(minute_ts, return_index=True)
    _, last_rev = np.unique(minute_ts[::-1], return_index=True)
    last_indices = len(minute_ts) - 1 - last_rev
    opens = prices[first_indices]
    closes = prices[last_indices]
    highs = np.maximum.reduceat(prices, first_indices)
    lows = np.minimum.reduceat(prices, first_indices)
    vols = np.add.reduceat(total_vol, first_indices)
    df_m1 = pd.DataFrame(
        {
            "timestamp": pd.to_datetime(unique_minutes, unit="ms", utc=True),
            "open": opens,
            "high": highs,
            "low": lows,
            "close": closes,
            "volume": np.round(vols).astype(np.uint64),
        }
    )
    return df_m1  # noqa: RET504 -- retains source transformation.


def _dataframe_to_canonical_m1(df: pd.DataFrame) -> Any:
    """Preserve the owner script's canonical data transformation."""
    if pa is None or M1_SCHEMA is None:
        raise ImportError("pyarrow is required for canonical parquet conversion.")
    if df.empty:
        return pa.Table.from_arrays(
            [
                pa.array([], type=pa.timestamp("ms", tz="UTC")),
                pa.array([], type=pa.float64()),
                pa.array([], type=pa.float64()),
                pa.array([], type=pa.float64()),
                pa.array([], type=pa.float64()),
                pa.array([], type=pa.uint64()),
            ],
            schema=M1_SCHEMA,
        )
    ts_col = "timestamp" if "timestamp" in df.columns else "DateTime"
    ts = df[ts_col].values
    if ts.dtype.kind == "M":
        ts_ms = ts.astype("datetime64[ms]").astype(np.int64)
    else:
        ts_ms = (
            pd.to_datetime(ts, utc=True)
            .values.astype("datetime64[ms]")
            .astype(np.int64)
        )
    dt_arr = pa.array(ts_ms, type=pa.timestamp("ms", tz="UTC"))
    open_arr = pa.array(
        df["open" if "open" in df.columns else "Open"].values.astype(np.float64),
        type=pa.float64(),
    )
    high_arr = pa.array(
        df["high" if "high" in df.columns else "High"].values.astype(np.float64),
        type=pa.float64(),
    )
    low_arr = pa.array(
        df["low" if "low" in df.columns else "Low"].values.astype(np.float64),
        type=pa.float64(),
    )
    close_arr = pa.array(
        df["close" if "close" in df.columns else "Close"].values.astype(np.float64),
        type=pa.float64(),
    )
    vol_col = "volume" if "volume" in df.columns else "Volume"
    vol_arr = pa.array(np.round(df[vol_col].values).astype(np.uint64), type=pa.uint64())
    return pa.Table.from_arrays(
        [dt_arr, open_arr, high_arr, low_arr, close_arr, vol_arr], schema=M1_SCHEMA
    )


def _dataframe_to_canonical_ticks(df: pd.DataFrame) -> Any:
    """Preserve the owner script's canonical data transformation."""
    if pa is None or TICK_SCHEMA is None:
        raise ImportError("pyarrow is required for canonical parquet conversion.")
    if df.empty:
        return pa.Table.from_arrays(
            [
                pa.array([], type=pa.timestamp("ms", tz="UTC")),
                pa.array([], type=pa.int64()),
                pa.array([], type=pa.int64()),
                pa.array([], type=pa.uint64()),
            ],
            schema=TICK_SCHEMA,
        )
    ts_col = "timestamp" if "timestamp" in df.columns else "DateTime"
    ts = df[ts_col].values
    if ts.dtype.kind == "M":
        ts_ms = ts.astype("datetime64[ms]").astype(np.int64)
    else:
        ts_ms = (
            pd.to_datetime(ts, utc=True)
            .values.astype("datetime64[ms]")
            .astype(np.int64)
        )
    dt_arr = pa.array(ts_ms, type=pa.timestamp("ms", tz="UTC"))
    ask_col = "ask" if "ask" in df.columns else "Ask"
    bid_col = "bid" if "bid" in df.columns else "Bid"
    ask_vals = df[ask_col].values
    bid_vals = df[bid_col].values
    if ask_vals.dtype == np.int64:
        ask_scaled = ask_vals
        bid_scaled = bid_vals
    else:
        ask_scaled = np.round(ask_vals * 1000000).astype(np.int64)
        bid_scaled = np.round(bid_vals * 1000000).astype(np.int64)
    if "volume" in df.columns:
        vol_arr = np.round(df["volume"].values).astype(np.uint64)
    elif "Volume" in df.columns:
        vol_arr = np.round(df["Volume"].values).astype(np.uint64)
    else:
        av = df["ask_volume"].values if "ask_volume" in df.columns else 0.0
        bv = df["bid_volume"].values if "bid_volume" in df.columns else 0.0
        vol_arr = np.round(av + bv).astype(np.uint64)
    return pa.Table.from_arrays(
        [
            dt_arr,
            pa.array(ask_scaled, type=pa.int64()),
            pa.array(bid_scaled, type=pa.int64()),
            pa.array(vol_arr, type=pa.uint64()),
        ],
        schema=TICK_SCHEMA,
    )


# Decimal metadata read by the owner script from its source catalog.
SYMBOL_DECIMALS = {
    "EURUSD": 5,
    "GBPUSD": 5,
    "USDJPY": 3,
    "USDCHF": 5,
    "AUDUSD": 5,
    "NZDUSD": 5,
    "USDCAD": 5,
    "EURGBP": 5,
    "EURJPY": 3,
    "GBPJPY": 3,
    "AUDJPY": 3,
    "CADJPY": 3,
    "CHFJPY": 3,
    "NZDJPY": 3,
    "EURAUD": 5,
    "EURCAD": 5,
    "EURCHF": 5,
    "EURNZD": 5,
    "GBPAUD": 5,
    "GBPCAD": 5,
    "GBPCHF": 5,
    "GBPNZD": 5,
    "AUDCAD": 5,
    "AUDCHF": 5,
    "AUDNZD": 5,
    "NZDCAD": 5,
    "NZDCHF": 5,
    "CADCHF": 5,
    "XAUUSD": 3,
    "XAGUSD": 3,
    "XPTUSD": 3,
    "XPDUSD": 3,
    "USA500IDXUSD": 3,
    "US500": 3,
    "USA30IDXUSD": 3,
    "US30": 3,
    "USATECHIDXUSD": 3,
    "USTEC": 3,
    "DEUIDXEUR": 3,
    "GER40": 3,
    "GBRIDXGBP": 3,
    "UK100": 3,
    "JPNIDXJPY": 3,
    "JP225": 3,
    "BRENTCMDUSD": 3,
    "LIGHTCMDUSD": 3,
    "XNGUSD": 3,
    "BTCUSD": 1,
    "ETHUSD": 2,
    "SOLUSD": 2,
    "LTCUSD": 2,
    "AUDSGD": 5,
    "CADHKD": 5,
    "CHFSGD": 5,
    "EURCZK": 4,
    "EURDKK": 5,
    "EURHKD": 5,
    "EURHUF": 3,
    "EURNOK": 5,
    "EURPLN": 5,
    "EURRUB": 5,
    "EURSEK": 5,
    "EURSGD": 5,
    "EURTRY": 5,
    "HKDJPY": 5,
    "SGDJPY": 3,
    "TRYJPY": 3,
    "USDCNH": 5,
    "USDCZK": 4,
    "USDDKK": 5,
    "USDHKD": 5,
    "USDHUF": 3,
    "USDILS": 5,
    "USDMXN": 5,
    "USDNOK": 5,
    "USDPLN": 5,
    "USDRON": 5,
    "USDRUB": 3,
    "USDSEK": 5,
    "USDSGD": 5,
    "USDTHB": 5,
    "USDTRY": 5,
    "USDZAR": 5,
    "ZARJPY": 3,
    "CHFPLN": 5,
    "US BRENT CRUDE OIL": 3,
    "WTI LIGHT CRUDE OIL": 3,
    "GASCMDUSD": 4,
    "NATURAL GAS": 4,
    "DIESELCMDUSD": 3,
    "LOW SUPLHUR GASOIL": 3,
    "COPPERCMDUSD": 4,
    "HIGH GRADE COPPER": 4,
    "XPDCMDUSD": 3,
    "PALADIUM": 3,
    "XPTCMDUSD": 3,
    "PLATINUM": 3,
    "COFFEECMDUSX": 3,
    "COFFEE ARABICA": 3,
    "COCOACMDUSD": 3,
    "US COCOA": 3,
    "SUGARCMDUSD": 3,
    "SUGAR WHITE": 3,
    "COTTONCMDUSX": 3,
    "COTTON": 3,
    "OJUICECMDUSX": 3,
    "ORANGE JUICE": 3,
    "SOYBEANCMDUSX": 3,
    "SOYBEAN": 3,
    "USA 30 INDEX": 3,
    "USA 100 TECHNICAL INDEX": 3,
    "USA 500 INDEX": 3,
    "USSC2000IDXUSD": 3,
    "US SMALL CAP 2000 INDEX": 3,
    "DOLLARIDXUSD": 3,
    "US DOLLAR INDEX": 3,
    "HKGIDXHKD": 3,
    "HONG KONG 40 INDEX": 3,
    "JAPAN 225": 3,
    "AUSIDXAUD": 3,
    "AUSTRALIA 200 INDEX": 3,
    "CHIIDXUSD": 3,
    "CHINA A50": 3,
    "SGDIDXSGD": 3,
    "SINGAPORE BLUE CHIP INDEX": 3,
    "INDIDXUSD": 3,
    "INDIA 50 INDEX": 3,
    "GERMANY 30 INDEX": 3,
    "FRAIDXEUR": 3,
    "FRANCE 40 INDEX": 3,
    "EUSIDXEUR": 3,
    "EUROPE 50 INDEX": 3,
    "UK 100 INDEX": 3,
    "ESPIDXEUR": 3,
    "SPAIN 35 INDEX": 3,
    "CHEIDXCHF": 3,
    "SWITZERLAND 20 INDEX": 3,
    "NLDIDXEUR": 3,
    "NETHERLANDS 25 INDEX": 3,
    "PLNIDXPLN": 3,
    "POLAND 20 INDEX": 3,
    "EBSATEUR": 3,
    "ERSTE GROUP BANK AG": 3,
    "RBIATEUR": 3,
    "RAIFFEISEN BANK INTERNATIONAL AG": 3,
    "VOEATEUR": 3,
    "VOESTALPINE AG": 3,
    "ABIBEEUR": 3,
    "ANHEUSER-BUSCH INBEV NV": 3,
    "AGSBEEUR": 3,
    "AGEAS": 3,
    "BELGBEEUR": 3,
    "PROXIMUS": 3,
    "KBCBEEUR": 3,
    "KBC GROEP NV": 3,
    "SOLBBEEUR": 3,
    "SOLVAY SA": 3,
    "UCBBEEUR": 3,
    "UCB SA": 3,
    "UMIBEEUR": 3,
    "UMICORESA": 3,
    "CARLBDKDKK": 3,
    "CARLSBERG A/S": 3,
    "COLOBDKDKK": 3,
    "COLOPLAST A/S": 3,
    "DANSKEDKDKK": 3,
    "DANSKE BANK A/S": 3,
    "MAERSKBDKDKK": 3,
    "AP MOELLER - MAERSK A/S": 3,
    "NOVOBDKDKK": 3,
    "NOVO NORDISK A/S": 3,
    "NZYMBDKDKK": 3,
    "NOVOZYMES A/S": 3,
    "PNDORADKDKK": 3,
    "PANDORA A/S": 3,
    "VWSDKDKK": 3,
    "VESTAS WIND SYSTEMS A/S": 3,
    "ADSDEEUR": 3,
    "ADIDAS AG": 3,
    "ALVDEEUR": 3,
    "ALLIANZ SE": 3,
    "BASDEEUR": 3,
    "BASF SE": 3,
    "BAYNDEEUR": 3,
    "BAYER AG": 3,
    "BEIDEEUR": 3,
    "BEIERSDORF AG": 3,
    "BMWDEEUR": 3,
    "BAYERISCHE MOTOREN WERKE AG": 3,
    "BOSSDEEUR": 3,
    "HUGO BOSS AG": 3,
    "CBKDEEUR": 3,
    "COMMERZBANK AG": 3,
    "CONDEEUR": 3,
    "CONTINENTAL AG": 3,
    "DAIDEEUR": 3,
    "DAIMLER AG": 3,
    "DB1DEEUR": 3,
    "DEUTSCHE BOERSE AG": 3,
    "DBKDEEUR": 3,
    "DEUTSCHE BANK AG": 3,
    "DPWDEEUR": 3,
    "DEUTSCHE POST AG": 3,
    "DTEDEEUR": 3,
    "DEUTSCHE TELEKOM AG": 3,
    "EOANDEEUR": 3,
    "EON SE": 3,
    "FMEDEEUR": 3,
    "FRESENIUS MEDICAL CARE AG & CO KGAA": 3,
    "FREDEEUR": 3,
    "FRESENIUS SE & CO KGAA": 3,
    "HEIDEEUR": 3,
    "HEIDELBERGCEMENT AG": 3,
    "HEN3DEEUR": 3,
    "HENKEL AG & CO KGAA": 3,
    "IFXDEEUR": 3,
    "INFINEON TECHNOLOGIES AG": 3,
    "LHADEEUR": 3,
    "DEUTSCHE LUFTHANSA AG": 3,
    "LINDEEUR": 3,
    "LINDE AG": 3,
    "LXSDEEUR": 3,
    "LANXESS AG": 3,
    "MRKDEEUR": 3,
    "MERCK KGAA": 3,
    "MUV2DEEUR": 3,
    "MUENCHENER RUECKVERSICHERUNGS AG": 3,
    "PAH3DEEUR": 3,
    "PORSCHE AUTOMOBIL HOLDING SE": 3,
    "PSMDEEUR": 3,
    "PROSIEBENSAT1 MEDIA AG": 3,
    "RWEDEEUR": 3,
    "RWE AG": 3,
    "SAPDEEUR": 3,
    "SAP AG": 3,
    "SDFDEEUR": 3,
    "K+S AG": 3,
    "SIEDEEUR": 3,
    "SIEMENS AG": 3,
    "TKADEEUR": 3,
    "THYSSENKRUPP AG": 3,
    "TUI1DEEUR": 3,
    "TUI AG": 3,
    "VNADEEUR": 3,
    "VONOVIA SE": 3,
    "VOW3DEEUR": 3,
    "VOLKSWAGEN AG": 3,
    "ELI1VFIEUR": 3,
    "ELISA OYJ": 3,
    "NES1VFIEUR": 3,
    "NESTE OYJ": 3,
    "NRE1VFIEUR": 3,
    "NOKIAN RENKAAT OYJ": 3,
    "OTE1VFIEUR": 3,
    "OUTOTEC OYJ": 3,
    "OUT1VFIEUR": 3,
    "OUTOKUMPU OYJ": 3,
    "STERVFIEUR": 3,
    "STORA ENSO OYJ": 3,
    "TLS1VFIEUR": 3,
    "TELIA COMPANY AB": 3,
    "ACFREUR": 3,
    "ACCOR SA": 3,
    "ACAFREUR": 3,
    "CREDIT AGRICOLE SA": 3,
    "AFFREUR": 3,
    "AIR FRANCE-KLM": 3,
    "AIFREUR": 3,
    "AIR LIQUIDE SA": 3,
    "AIRFREUR": 3,
    "AIRBUS GROUP SE": 3,
    "ALOFREUR": 3,
    "ALSTOM SA": 3,
    "BNFREUR": 3,
    "DANONE SA": 3,
    "BNPFREUR": 3,
    "BNP PARIBAS SA": 3,
    "CAFREUR": 3,
    "CARREFOUR SA": 3,
    "CAPFREUR": 3,
    "CAP GEMINI SA": 3,
    "CSFREUR": 3,
    "AXA SA": 3,
    "DGFREUR": 3,
    "VINCI SA": 3,
    "EDFFREUR": 3,
    "ELECTRICITE DE FRANCE SA": 3,
    "EIFREUR": 3,
    "ESSILOR INTERNATIONAL SA": 3,
    "ENFREUR": 3,
    "BOUYGUES SA": 3,
    "ENGIFREUR": 3,
    "ENGIE": 3,
    "FPFREUR": 3,
    "TOTAL SA": 3,
    "FRFREUR": 3,
    "VALEO SA": 3,
    "GLEFREUR": 3,
    "SOCIETE GENERALE SA": 3,
    "KERFREUR": 3,
    "KERING": 3,
    "LIFREUR": 3,
    "KLEPIERRE": 3,
    "LRFREUR": 3,
    "LEGRAND SA": 3,
    "MCFREUR": 3,
    "LVMH MOET HENNESSY LOUIS VUITTON SA": 3,
    "ORFREUR": 3,
    "L'OREAL SA": 3,
    "ORAFREUR": 3,
    "ORANGE SA": 3,
    "PUBFREUR": 3,
    "PUBLICIS GROUPE SA": 3,
    "RIFREUR": 3,
    "PERNOD-RICARD SA": 3,
    "RNOFREUR": 3,
    "RENAULT SA": 3,
    "SAFFREUR": 3,
    "SAFRAN SA": 3,
    "SANFREUR": 3,
    "SANOFI": 3,
    "SGOFREUR": 3,
    "CIE DE ST-GOBAIN": 3,
    "SUFREUR": 3,
    "SCHNEIDER ELECTRIC SA": 3,
    "UGFREUR": 3,
    "PEUGEOT SA": 3,
    "VIEFREUR": 3,
    "VEOLIA ENVIRONNEMENT SA": 3,
    "VIVFREUR": 3,
    "VIVENDI SA": 3,
    "VKFREUR": 3,
    "VALLOUREC SA": 3,
    "BIRGIEEUR": 3,
    "BANK OF IRELAND PLC": 3,
    "KRXIEEUR": 3,
    "KINGSPAN GROUP PLC": 3,
    "CRGIEEUR": 3,
    "CRH PLC": 3,
    "KRZIEEUR": 3,
    "KERRY GROUP PLC": 3,
    "AGLITEUR": 3,
    "AUTOGRILL SPA": 3,
    "A2AITEUR": 3,
    "A2A SPA": 3,
    "AMPITEUR": 3,
    "AMPLIFON SPA": 3,
    "ATLITEUR": 3,
    "ATLANTIA SPA": 3,
    "AZMITEUR": 3,
    "AZIMUT HOLDING SPA": 3,
    "BAMIITEUR": 3,
    "BANCO BPM SPA": 3,
    "BCITEUR": 3,
    "BRUNELLO CUCINELLI SPA": 3,
    "BMPSITEUR": 3,
    "BANCA MONTE DEI PASCHI DI SIENA SPA": 3,
    "BPEITEUR": 3,
    "BPER BANCA SPA": 3,
    "BREITEUR": 3,
    "BREMBO SPA": 3,
    "BZUITEUR": 3,
    "BUZZI UNICEM SPA": 3,
    "CASSITEUR": 3,
    "CATTOLICA ASS COOP A": 3,
    "CERVITEUR": 3,
    "CERVED INFORMATION SOLIUTIONS SPA": 3,
    "CPRITEUR": 3,
    "DAVIDE CAMPARI-MILANO SPA": 3,
    "CVALITEUR": 3,
    "CREDITO VALTLINESE SPA": 3,
    "DANITEUR": 3,
    "DANIELI & CO SPA": 3,
    "DIAITEUR": 3,
    "DIASORIN SPA": 3,
    "ENELITEUR": 3,
    "ENEL SPA": 3,
    "ENIITEUR": 3,
    "ENI SPA": 3,
    "ERGITEUR": 3,
    "ERG SPA": 3,
    "FBKITEUR": 3,
    "FINECOBANK BANCA FINECO SPA": 3,
    "FCAITEUR": 3,
    "FIAT CHRYSLER AUTO NV": 3,
    "GITEUR": 3,
    "ASSICURAZIONI GENERALI SPA": 3,
    "IGITEUR": 3,
    "ITALGAS SPA": 3,
    "INWITEUR": 3,
    "INFRASTRUCTURE WIRELESS ITALIANE SPA": 3,
    "ISPITEUR": 3,
    "INTESA SANPAOLO SPA": 3,
    "JUVEITEUR": 3,
    "JUVENTUS FOOTBAL CLUB SPA": 3,
    "LDOITEUR": 3,
    "LEONARDO SPA": 3,
    "MBITEUR": 3,
    "MEDIOBANCA SPA": 3,
    "MONCITEUR": 3,
    "MONCLER SPA": 3,
    "MSITEUR": 3,
    "MEDIASET SPA": 3,
    "PIAITEUR": 3,
    "PIAGGIO & C. SPA": 3,
    "PRYITEUR": 3,
    "PRYSMIAN SPA": 3,
    "RACEITEUR": 3,
    "FERRAI NV": 3,
    "RECITEUR": 3,
    "RECORDATI INDUSTRIA CHIMICA E FARMA SPA": 3,
    "SFERITEUR": 3,
    "SALVAT FERRAGAMO SPA": 3,
    "SPMITEUR": 3,
    "SAIPEM SPA": 3,
    "SRGITEUR": 3,
    "SNAM SPA": 3,
    "SRSITEUR": 3,
    "SARAS SPA": 3,
    "STMITEUR": 3,
    "STMICROELECTRONICS SPA": 3,
    "TENITEUR": 3,
    "TENARIS SPA": 3,
    "TISITEUR": 3,
    "TISCALI SPA": 3,
    "TITITEUR": 3,
    "TELECOM ITALIA SPA": 3,
    "TODITEUR": 3,
    "TODS SPA": 3,
    "TRNITEUR": 3,
    "TERNA SPA": 3,
    "UCGITEUR": 3,
    "UNICREDIT SPA": 3,
    "USITEUR": 3,
    "UNIPOLSAI ASSICURAZIONI SPA": 3,
    "WBDITEUR": 3,
    "WEBUILD SPA": 3,
    "0005HKHKD": 3,
    "HSBC HOLDINGS PLC": 3,
    "0027HKHKD": 3,
    "GALAXY ENTERTAINMENT GROUP LTD": 3,
    "0175HKHKD": 3,
    "GEELY AUTOMOBILE HOLDINGS LTD": 3,
    "0291HKHKD": 3,
    "CHINA RESOURCES BEER HOLDINGS CO LTD": 3,
    "0386HKHKD": 3,
    "SINOPEC CORP": 3,
    "0388HKHKD": 3,
    "HK EXCHANGES & CLEARING LTD": 3,
    "0700HKHKD": 3,
    "TENCENT HOLDINGS LTD": 3,
    "0857HKHKD": 3,
    "PETROCHINA CO LTD": 3,
    "0883HKHKD": 3,
    "CHINA NATIONAL OFFSHORE OIL CORPORATION LTD": 3,
    "0939HKHKD": 3,
    "CHINA CONSTRUCTION BANK CORP": 3,
    "0941HKHKD": 3,
    "CHINA MOBILE LTD": 3,
    "0998HKHKD": 3,
    "CITIC BANK INTERNATIONAL CORP LTD": 3,
    "1093HKHKD": 3,
    "CSPC PHARMACEUTICAL GROUP LTD": 3,
    "1177HKHKD": 3,
    "SINO BIOPHARMECEUTICAL LTD": 3,
    "1288HKHKD": 3,
    "AGRICULTURAL BANK OF CHINA LTD": 3,
    "1299HKHKD": 3,
    "AIA GROUP LTD": 3,
    "1398HKHKD": 3,
    "INDUSTRIAL AND COMMERCIAL BANK OF CHINA LTD": 3,
    "1918HKHKD": 3,
    "SUNAC CHINA HOLDINGS LTD": 3,
    "2007HKHKD": 3,
    "COUNTRY GARDEN HOLDINGS LTD": 3,
    "2018HKHKD": 3,
    "AAC TECHNOLOGIES HOLDINGS INC": 3,
    "2318HKHKD": 3,
    "PING AN INSURANCE LTD": 3,
    "2388HKHKD": 3,
    "BOC HONG KONG (HOLDINGS) LTD": 3,
    "2628HKHKD": 3,
    "CHINA LIFE INSURANCE COMPANY LTD": 3,
    "3333HKHKD": 3,
    "CHINA EVERGRANDE GROUP": 3,
    "3968HKHKD": 3,
    "CHINA MERCHANTS BANK CO LTD": 3,
    "3988HKHKD": 3,
    "BANK OF CHINA LTD": 3,
    "1810HKHKD": 3,
    "XIAOMI CORP": 3,
    "AGNNLEUR": 3,
    "AEGON NV": 3,
    "AHNLEUR": 3,
    "KONINKLIJKE AHOLD DELHAIZE NV": 3,
    "AKZANLEUR": 3,
    "AKZO NOBEL NV": 3,
    "ASMLNLEUR": 3,
    "ASML HOLDING NV": 3,
    "DSMNLEUR": 3,
    "KONINKLIJKE DSM NV": 3,
    "GTONLEUR": 3,
    "GEMALTO NV": 3,
    "HEIANLEUR": 3,
    "HEINEKEN NV": 3,
    "INGANLEUR": 3,
    "ING GROEP NV": 3,
    "KPNNLEUR": 3,
    "KONINKLIJKE KPN NV": 3,
    "MTNLEUR": 3,
    "ARCELORMITTAL": 3,
    "PHIANLEUR": 3,
    "KONINKLIJKE PHILIPS NV": 3,
    "RANDNLEUR": 3,
    "RANDSTAD HOLDING NV": 3,
    "RDSANLEUR": 3,
    "ROYAL DUTCH SHELL PLC": 3,
    "RENNLEUR": 3,
    "RELX NV": 3,
    "ULNLEUR": 3,
    "UNIBAIL-RODAMCO SE": 3,
    "UNANLEUR": 3,
    "UNILEVER NV": 3,
    "VPKNLEUR": 3,
    "KONINKLIJKE VOPAK NV": 3,
    "WKLNLEUR": 3,
    "WOLTERS KLUWER NV": 3,
    "DNBNONOK": 3,
    "DNB ASA": 3,
    "MHGNONOK": 3,
    "MARINE HARVEST ASA": 3,
    "NHYNONOK": 3,
    "NORSK HYDRO ASA": 3,
    "ORKNONOK": 3,
    "ORKLA ASA": 3,
    "STLNONOK": 3,
    "STATOIL ASA": 3,
    "TELNONOK": 3,
    "TELENOR ASA": 3,
    "YARNONOK": 3,
    "YARA INTERNATIONAL ASA": 3,
    "EDPPTEUR": 3,
    "EDP - ENERGIAS DE PORTUGAL SA": 3,
    "GALPPTEUR": 3,
    "GALP ENERGIA SGPS SA": 3,
    "ABEESEUR": 3,
    "ABERTIS INFRAESTRUCTURAS SA": 3,
    "ACSESEUR": 3,
    "ACS ACTIVIDADES DE CONSTRUCCION Y SERVICIOS SA": 3,
    "ACXESEUR": 3,
    "ACERINOX SA": 3,
    "AENAESEUR": 3,
    "AENA SA": 3,
    "AMSESEUR": 3,
    "AMADEUS IT HOLDING SA": 3,
    "BBVAESEUR": 3,
    "BANCO BILBAO VIZCAYA ARGENTARIA SA": 3,
    "CABKESEUR": 3,
    "CAIXABANK": 3,
    "DIAESEUR": 3,
    "DISTRIBUIDORA INTERNACIONAL DE ALIMENTACION SA": 3,
    "ELEESEUR": 3,
    "ENDESA SA": 3,
    "ENGESEUR": 3,
    "ENAGAS SA": 3,
    "FERESEUR": 3,
    "FERROVIAL SA": 3,
    "GAMESEUR": 3,
    "GAMESA CORPORACION TECNOLOGICA SA": 3,
    "GASESEUR": 3,
    "GAS NATURAL SDG SA": 3,
    "IBEESEUR": 3,
    "IBERDROLA SA": 3,
    "ITXESEUR": 3,
    "INDITEX SA": 3,
    "MAPESEUR": 3,
    "MAPFRE SA": 3,
    "POPESEUR": 3,
    "BANCO POPULAR ESPANOL SA": 3,
    "REEESEUR": 3,
    "RED ELECTRICA CORP SA": 3,
    "REPESEUR": 3,
    "REPSOL SA": 3,
    "SABESEUR": 3,
    "BANCO DE SABADELL SA": 3,
    "SANESEUR": 3,
    "BANCO SANTANDER SA": 3,
    "TEFESEUR": 3,
    "TELEFONICA SA": 3,
    "ABBSESEK": 3,
    "ABB LTD": 3,
    "ALFASESEK": 3,
    "ALFA LAVAL AB": 3,
    "ATCOASESEK": 3,
    "ATLAS COPCO AB": 3,
    "AZNSESEK": 3,
    "ASTRAZENECA PLC": 3,
    "ELUXBSESEK": 3,
    "ELECTROLUX AB": 3,
    "ERICBSESEK": 3,
    "TELEFONAKTIEBOLAGET LM ERICSSON": 3,
    "GETIBSESEK": 3,
    "GETINGE AB": 3,
    "HMBSESEK": 3,
    "HENNES & MAURITZ AB": 3,
    "INVEBSESEK": 3,
    "INVESTOR AB": 3,
    "NDASESEK": 3,
    "NORDEA BANK AB": 3,
    "SANDSESEK": 3,
    "SANDVIK AB": 3,
    "SCABSESEK": 3,
    "SVENSKA CELLULOSA AB": 3,
    "SEBASESEK": 3,
    "SKANDINAVISKA ENSKILDA BANKEN AB": 3,
    "SECUBSESEK": 3,
    "SECURITAS AB": 3,
    "SKABSESEK": 3,
    "SKANSKA AB": 3,
    "SKFBSESEK": 3,
    "SKF AB": 3,
    "SWEDASESEK": 3,
    "SWEDBANK AB": 3,
    "SWMASESEK": 3,
    "SWEDISH MATCH AB": 3,
    "TEL2BSESEK": 3,
    "TELE2 AB": 3,
    "TLSNSESEK": 3,
    "VOLVBSESEK": 3,
    "VOLVO AB": 3,
    "ABBNCHCHF": 3,
    "ADENCHCHF": 3,
    "ADECCO SA": 3,
    "ATLNCHCHF": 3,
    "ACTELION LTD": 3,
    "BAERCHCHF": 3,
    "JULIUS BAER GROUP LTD": 3,
    "CLNCHCHF": 3,
    "CLARIANT AG": 3,
    "CSGNCHCHF": 3,
    "CREDIT SUISSE GROUP AG": 3,
    "GALNCHCHF": 3,
    "GALENICA AG": 3,
    "GIVNCHCHF": 3,
    "GIVAUDAN SA": 3,
    "KNINCHCHF": 3,
    "KUEHNE + NAGEL INTERNATIONAL AG": 3,
    "LHNCHCHF": 3,
    "LAFARGE HOLCIM LTD": 3,
    "LONNCHCHF": 3,
    "LONZA GROUP AG": 3,
    "NESNCHCHF": 3,
    "NESTLE SA": 3,
    "NOVNCHCHF": 3,
    "NOVARTIS AG": 3,
    "ROGCHCHF": 3,
    "ROCHE HOLDING AG": 3,
    "SCMNCHCHF": 3,
    "SWISSCOM AG": 3,
    "SGSNCHCHF": 3,
    "SGS SA": 3,
    "SIKCHCHF": 3,
    "SIKA AG": 3,
    "SLHNCHCHF": 3,
    "SWISS LIFE HOLDING AG": 3,
    "SOONCHCHF": 3,
    "SONOVA HOLDING AG": 3,
    "SRENCHCHF": 3,
    "SWISS RE AG": 3,
    "SYNNCHCHF": 3,
    "SYNGENTA AG": 3,
    "UBSGCHCHF": 3,
    "UBS GROUP AG": 3,
    "UHRCHCHF": 3,
    "SWATCH GROUP AGTHE": 3,
    "ZURNCHCHF": 3,
    "ZURICH INSURANCE GROUP AG": 3,
    "AALGBGBX": 3,
    "ANGLO AMERICAN PLC": 3,
    "ABFGBGBX": 3,
    "ASSOCIATED BRITISH FOODS PLC": 3,
    "ADMGBGBX": 3,
    "ADMIRAL GROUP PLC": 3,
    "ADNGBGBX": 3,
    "ABERDEEN ASSET MANAGEMENT PLC": 3,
    "AGKGBGBX": 3,
    "AGGREKO PLC": 3,
    "AHTGBGBX": 3,
    "ASHTEAD GROUP PLC": 3,
    "ANTOGBGBX": 3,
    "ANTOFAGASTA PLC": 3,
    "AVGBGBX": 3,
    "AVIVA PLC": 3,
    "AZNGBGBX": 3,
    "BAGBGBX": 3,
    "BAE SYSTEMS PLC": 3,
    "BABGBGBX": 3,
    "BABCOCK INTERNATIONAL GROUP PLC": 3,
    "BARCGBGBX": 3,
    "BARCLAYS PLC": 3,
    "BATSGBGBX": 3,
    "BRITISH AMERICAN TOBACCO PLCSTOCKS": 3,
    "BLNDGBGBX": 3,
    "BRITISH LAND CO PLC": 3,
    "BLTGBGBX": 3,
    "BHP BILLITON PLC": 3,
    "BNZLGBGBX": 3,
    "BUNZL PLC": 3,
    "BPGBGBX": 3,
    "BP PLC": 3,
    "BRBYGBGBX": 3,
    "BURBERRY GROUP PLC": 3,
    "BTGBGBX": 3,
    "BT GROUP PLC": 3,
    "CCLGBGBX": 3,
    "CARNIVAL PLC": 3,
    "CNAGBGBX": 3,
    "CENTRICA PLC": 3,
    "CPGGBGBX": 3,
    "COMPASS GROUP PLC": 3,
    "CPIGBGBX": 3,
    "CAPITA PLC": 3,
    "CRDAGBGBX": 3,
    "CRODA INTERNATIONAL PLC": 3,
    "CRHGBGBX": 3,
    "DGEGBGBX": 3,
    "DIAGEO PLC": 3,
    "EXPNGBGBX": 3,
    "EXPERIAN PLC": 3,
    "EZJGBGBX": 3,
    "EASYJET PLC": 3,
    "FRESGBGBX": 3,
    "FRESNILLO PLC": 3,
    "GFSGBGBX": 3,
    "G4S PLC": 3,
    "GKNGBGBX": 3,
    "GKN PLC": 3,
    "GLENGBGBX": 3,
    "GLENCORE PLC": 3,
    "GSKGBGBX": 3,
    "GLAXOSMITHKLINE PLC": 3,
    "HMSOGBGBX": 3,
    "HAMMERSON PLC": 3,
    "HSBAGBGBX": 3,
    "IAGGBGBX": 3,
    "INTERNATIONAL CONSOLIDATED AIRLINES GROU": 3,
    "IHGGBGBX": 3,
    "INTERCONTINENTAL HOTELS GROUP PLC": 3,
    "IMTGBGBX": 3,
    "IMPERIAL BRANDS PLC": 3,
    "ISATGBGBX": 3,
    "INMARSAT PLC": 3,
    "ITRKGBGBX": 3,
    "INTERTEK GROUP PLC": 3,
    "ITVGBGBX": 3,
    "ITV PLC": 3,
    "KGFGBGBX": 3,
    "KINGFISHER PLC": 3,
    "LANDGBGBX": 3,
    "LAND SECURITIES GROUP PLC": 3,
    "LGENGBGBX": 3,
    "LEGAL & GENERAL GROUP PLC": 3,
    "LLOYGBGBX": 3,
    "LLOYDS BANKING GROUP PLC": 3,
    "LSEGBGBX": 3,
    "LONDON STOCK EXCHANGE GROUP PLC": 3,
    "MKSGBGBX": 3,
    "MARKS & SPENCER GROUP PLC": 3,
    "MNDIGBGBX": 3,
    "MONDI PLC": 3,
    "MRWGBGBX": 3,
    "WM MORRISON SUPERMARKETS PLC": 3,
    "NGGBGBX": 3,
    "NATIONAL GRID PLC": 3,
    "NXTGBGBX": 3,
    "NEXT PLC": 3,
    "OMLGBGBX": 3,
    "OLD MUTUAL PLC": 3,
    "PFCGBGBX": 3,
    "PETROFAC LTD": 3,
    "PRUGBGBX": 3,
    "PRUDENTIAL PLC": 3,
    "PSNGBGBX": 3,
    "PERSIMMON PLC": 3,
    "PSONGBGBX": 3,
    "PEARSON PLC": 3,
    "RBGBGBX": 3,
    "RECKITT BENCKISER GROUP PLC": 3,
    "RBSGBGBX": 3,
    "ROYAL BANK OF SCOTLAND GROUP PLC": 3,
    "RDSBGBGBX": 3,
    "RELGBGBX": 3,
    "RELX PLC": 3,
    "RIOGBGBX": 3,
    "RIO TINTO PLC": 3,
    "RMGGBGBX": 3,
    "ROYAL MAIL PLC": 3,
    "RRGBGBX": 3,
    "ROLLS-ROYCE HOLDINGS PLC": 3,
    "RRSGBGBX": 3,
    "RANDGOLD RESOURCES LTD": 3,
    "RSAGBGBX": 3,
    "RSA INSURANCE GROUP PLC": 3,
    "SBRYGBGBX": 3,
    "J SAINSBURY PLC": 3,
    "SGEGBGBX": 3,
    "SAGE GROUP PLCTHE": 3,
    "SHPGBGBX": 3,
    "SHIRE PLC": 3,
    "SKYGBGBX": 3,
    "SKY PLC": 3,
    "SLGBGBX": 3,
    "STANDARD LIFE PLC": 3,
    "SMINGBGBX": 3,
    "SMITHS GROUP PLC": 3,
    "SNGBGBX": 3,
    "SMITH & NEPHEW PLC": 3,
    "SSEGBGBX": 3,
    "SSE PLC": 3,
    "STANGBGBX": 3,
    "STANDARD CHARTERED PLC": 3,
    "SVTGBGBX": 3,
    "SEVERN TRENT PLC": 3,
    "TATEGBGBX": 3,
    "TATE & LYLE PLC": 3,
    "TLWGBGBX": 3,
    "TULLOW OIL PLC": 3,
    "TPKGBGBX": 3,
    "TRAVIS PERKINS PLC": 3,
    "TSCOGBGBX": 3,
    "TESCO PLC": 3,
    "ULVRGBGBX": 3,
    "UNILEVER PLC": 3,
    "UUGBGBX": 3,
    "UNITED UTILITIES GROUP PLC": 3,
    "VODGBGBX": 3,
    "VODAFONE GROUP PLC": 3,
    "WEIRGBGBX": 3,
    "WEIR GROUP PLCTHE": 3,
    "WOSGBGBX": 3,
    "WOLSELEY PLC": 3,
    "WPPGBGBX": 3,
    "WPP PLC": 3,
    "WTBGBGBX": 3,
    "WHITBREAD PLC": 3,
    "MMMUSUSD": 3,
    "3M CO": 3,
    "ABTUSUSD": 3,
    "ABBOTT LABORATORIES": 3,
    "ATVIUSUSD": 3,
    "ACTIVISION BLIZZARD INC": 3,
    "ADBEUSUSD": 3,
    "ADOBE SYSTEMS INC": 3,
    "AMDUSUSD": 3,
    "ADVANCED MICRO DEVICES": 3,
    "AETUSUSD": 3,
    "AETNA INC": 3,
    "AUSUSD": 3,
    "AGILENT TECHNOLOGIES INC": 3,
    "APDUSUSD": 3,
    "AIR PRODUCTS & CHEMICALS INC": 3,
    "AAUSUSD": 3,
    "ALCOA INC": 3,
    "ALXNUSUSD": 3,
    "ALEXION PHARMACEUTICALS INC": 3,
    "BABAUSUSD": 3,
    "ALIBABA GROUP HOLDING-SP ADR": 3,
    "ALLUSUSD": 3,
    "ALLSTATE CORP": 3,
    "GOOGLUSUSD": 3,
    "ALPHABET INC-CL A": 3,
    "GOOGUSUSD": 3,
    "ALPHABET INC-CL C": 3,
    "MOUSUSD": 3,
    "ALTRIA GROUP INC": 3,
    "AMZNUSUSD": 3,
    "AMAZONCOM INC": 3,
    "ABEVUSUSD": 3,
    "AMBEV SA": 3,
    "AALUSUSD": 3,
    "AMERICAN AIRLINES GROUP INC": 3,
    "AXPUSUSD": 3,
    "AMERICAN EXPRESS CO": 3,
    "AEPUSUSD": 3,
    "AMERICAN ELECTRIC POWER": 3,
    "AIGUSUSD": 3,
    "AMERICAN INTERNATIONAL GROUP": 3,
    "AMTUSUSD": 3,
    "AMERICAN TOWER CORP": 3,
    "AMPUSUSD": 3,
    "AMERIPRISE FINANCIAL INC": 3,
    "ABCUSUSD": 3,
    "AMERISOURCEBERGEN CORP": 3,
    "AMGNUSUSD": 3,
    "AMGEN INC": 3,
    "APCUSUSD": 3,
    "ANADARKO PETROLEUM CORP": 3,
    "ANTMUSUSD": 3,
    "ANTHEM INC": 3,
    "APAUSUSD": 3,
    "APACHE CORP": 3,
    "AAPLUSUSD": 3,
    "APPLE INC": 3,
    "AMATUSUSD": 3,
    "APPLIED MATERIALS": 3,
    "AZNUSUSD": 3,
    "TUSUSD": 3,
    "AT&T INC": 3,
    "ADPUSUSD": 3,
    "AUTOMATIC DATA PROCESSING": 3,
    "AZOUSUSD": 3,
    "AUTOZONE INC": 3,
    "AVBUSUSD": 3,
    "AVALONBAY COMMUNITIES INC": 3,
    "BIDUUSUSD": 3,
    "BAIDU INC": 3,
    "BBDUSUSD": 3,
    "BANCO BRADESCO SA": 3,
    "BACUSUSD": 3,
    "BANK OF AMERICA CORP": 3,
    "BKUSUSD": 3,
    "BANK OF NEW YORK MELLON CORP": 3,
    "BBTUSUSD": 3,
    "BB&T CORP": 3,
    "BDXUSUSD": 3,
    "BECTON DICKINSON AND CO": 3,
    "BRKBUSUSD": 3,
    "BERKSHIRE HATHAWAY INC-CL B": 3,
    "BBYUSUSD": 3,
    "BEST BUY CO INC": 3,
    "BIIBUSUSD": 3,
    "BIOGEN INC": 3,
    "BAUSUSD": 3,
    "BOEING CO": 3,
    "BSXUSUSD": 3,
    "BOSTON SCIENTIFIC CORP": 3,
    "BMYUSUSD": 3,
    "BRISTOL-MYERS SQUIBB CO": 3,
    "BPUSUSD": 3,
    "AVGOUSUSD": 3,
    "BROADCOM LIMITED": 3,
    "CATUSUSD": 3,
    "CATERPILLLAR INC": 3,
    "COFUSUSD": 3,
    "CAPITAL ONE FINANCIAL CORP": 3,
    "CAHUSUSD": 3,
    "CARDINAL HEALTH INC": 3,
    "CBSUSUSD": 3,
    "CBS CORP-CLASS B NON VOTING": 3,
    "CTLUSUSD": 3,
    "CENTURYLINK INC": 3,
    "CVXUSUSD": 3,
    "CHEVRON CORP": 3,
    "CMGUSUSD": 3,
    "CHIPOTLE MEXICAN GRILL INC": 3,
    "CFUSUSD": 3,
    "CF INDUSTRIES HOLDINGS INC": 3,
    "CIUSUSD": 3,
    "CIGNA CORP": 3,
    "CSCOUSUSD": 3,
    "CISCO SYSTEMS INC": 3,
    "CUSUSD": 3,
    "CITIGROUP INC": 3,
    "KOUSUSD": 3,
    "COCA-COLA COTHE": 3,
    "CLUSUSD": 3,
    "COLGATE-PALMOLIVE CO": 3,
    "CMCSAUSUSD": 3,
    "COMCAST CORP-CLASS A": 3,
    "CAGUSUSD": 3,
    "CONAGRA FOODS INC": 3,
    "COPUSUSD": 3,
    "CONOCOPHILLIPS": 3,
    "STZUSUSD": 3,
    "CONSTELLATION BRANDS INC-A": 3,
    "XLYUSUSD": 3,
    "CONSUMER DISCRETIONARY SELECT SECTOR SPDR FUND": 3,
    "XLPUSUSD": 3,
    "CONSUMER STAPLES SELECT SECTOR SPDR FUND": 3,
    "GLWUSUSD": 3,
    "CORNING INC": 3,
    "CSUSUSD": 3,
    "CMIUSUSD": 3,
    "CUMMINS INC": 3,
    "CVSUSUSD": 3,
    "CVS HEALTH CORP": 3,
    "DHRUSUSD": 3,
    "DANAHER CORP": 3,
    "DVAUSUSD": 3,
    "DAVITA HEALTHCARE PARTNERS I": 3,
    "DEUSUSD": 3,
    "DEERE & CO": 3,
    "DALUSUSD": 3,
    "DELTA AIR LINES INC": 3,
    "DVNUSUSD": 3,
    "DEVON ENERGY CORP": 3,
    "DFSUSUSD": 3,
    "DISCOVER FINANCIAL SERVICES": 3,
    "DGUSUSD": 3,
    "DOLLAR GENERAL CORP": 3,
    "DUSUSD": 3,
    "DOMINION RESOURCES INCVA": 3,
    "DHIUSUSD": 3,
    "DR HORTON INC": 3,
    "DUKUSUSD": 3,
    "DUKE ENERGY CORP": 3,
    "EBAYUSUSD": 3,
    "EBAY INC": 3,
    "EIXUSUSD": 3,
    "EDISON INTERNATIONAL": 3,
    "LLYUSUSD": 3,
    "ELI LILLY & CO": 3,
    "EAUSUSD": 3,
    "ELECCTRONIC ARTS": 3,
    "EMRUSUSD": 3,
    "EMERSON ELECTRIC CO": 3,
    "XLEUSUSD": 3,
    "ENERGY SELECT SECTOR SPDR FUND": 3,
    "EOGUSUSD": 3,
    "EOG RESOURCES INC": 3,
    "EQTUSUSD": 3,
    "EQT CORP": 3,
    "EFXUSUSD": 3,
    "EQUIFAX INC": 3,
    "EXPEUSUSD": 3,
    "EXPEDEA INC": 3,
    "ESRXUSUSD": 3,
    "EXPRESS SCRIPTS HOLDING": 3,
    "ELUSUSD": 3,
    "ESTEE LAUDER COMPANIES-CL A": 3,
    "EXCUSUSD": 3,
    "EXELON CORP": 3,
    "XOMUSUSD": 3,
    "EXXON MOBIL CORP": 3,
    "FBUSUSD": 3,
    "FACEBOOK INC-A": 3,
    "FDXUSUSD": 3,
    "FEDEX CORP": 3,
    "XLFUSUSD": 3,
    "FINANCIAL SELECT SECTOR SPDR FUND": 3,
    "FEUSUSD": 3,
    "FIRSTENERGY CORP": 3,
    "FUSUSD": 3,
    "FORD MOTOR CO": 3,
    "FCXUSUSD": 3,
    "FREEPORT-MCMORAN INC": 3,
    "GPSUSUSD": 3,
    "GAP INCTHE": 3,
    "GEUSUSD": 3,
    "GENERAL ELECTRIC CO": 3,
    "GISUSUSD": 3,
    "GENERAL MILLS INC": 3,
    "GMUSUSD": 3,
    "GENERAL MOTORS CO": 3,
    "GILDUSUSD": 3,
    "GILEAD SCIENCES INC": 3,
    "GSUSUSD": 3,
    "GOLDMAN SACHS GROUP INC": 3,
    "HALUSUSD": 3,
    "HALLIBURTON CO": 3,
    "HCPUSUSD": 3,
    "HCP INC": 3,
    "XLVUSUSD": 3,
    "HEALTH CARE SELECT SECTOR SPDR FUND": 3,
    "HESUSUSD": 3,
    "HESS CORP": 3,
    "HDUSUSD": 3,
    "HOME DEPOT INC": 3,
    "HONUSUSD": 3,
    "HONEYWELL INTERNATIONAL INC": 3,
    "HPQUSUSD": 3,
    "HP INC": 3,
    "HUMUSUSD": 3,
    "HUMANA INC": 3,
    "ITWUSUSD": 3,
    "ILLINOIS TOOL WORKS": 3,
    "XLIUSUSD": 3,
    "INDUSTRIAL SELECT SECTOR SPDR FUND": 3,
    "INTCUSUSD": 3,
    "INTEL CORP": 3,
    "ICEUSUSD": 3,
    "INTERCONTINENTAL EXCHANGE IN": 3,
    "IPGUSUSD": 3,
    "INTERPUBLIC GROUP OF COS INC": 3,
    "IBMUSUSD": 3,
    "INTL BUSINESS MACHINES CORP": 3,
    "VXXUSUSD": 3,
    "IPATH S&P 500 VIX ST FUTURES ETN": 3,
    "TLTUSUSD": 3,
    "ISHARES 20+ YEAR TREASURY BOND ETF": 3,
    "IEFUSUSD": 3,
    "ISHARES 7-10 YEAR TREASURY BOND ETF": 3,
    "IJHUSUSD": 3,
    "ISHARES CORE S&P MID-CAP ETF": 3,
    "IJRUSUSD": 3,
    "ISHARES CORE S&P SMALL-CAP ETF": 3,
    "FXIUSUSD": 3,
    "ISHARES CHINA LARGE-CAP ETF": 3,
    "EMBUSUSD": 3,
    "ISHARES JP MORGAN USD EMERGING MARKETS BOND ETF": 3,
    "EWZUSUSD": 3,
    "ISHARES MSCI BRAZIL CAPPED": 3,
    "EFAUSUSD": 3,
    "ISHARES MSCI EAFE ETF": 3,
    "EEMUSUSD": 3,
    "ISHARES MSCI EMERGING MARKETS ETF": 3,
    "EWHUSUSD": 3,
    "ISHARES MSCI HONG KONG ETF": 3,
    "EWJUSUSD": 3,
    "ISHARES MSCI JAPAN ETF": 3,
    "EWWUSUSD": 3,
    "ISHARES MSCI MEXICO CAPPED": 3,
    "EZUUSUSD": 3,
    "ISHARES MSCI EMU ETF": 3,
    "IWFUSUSD": 3,
    "ISHARES RUSSELL 1000 GROWTH ETF": 3,
    "IWDUSUSD": 3,
    "ISHARES RUSSELL 1000 VALUE ETF": 3,
    "IWMUSUSD": 3,
    "ISHARES RUSSELL 2000 ETF": 3,
    "IVWUSUSD": 3,
    "ISHARES S&P 500 GROWTH ETF": 3,
    "IVEUSUSD": 3,
    "ISHARES S&P 500 VALUE ETF": 3,
    "DVYUSUSD": 3,
    "ISHARES SELECT DIVIDEND ETF": 3,
    "SLVUSUSD": 3,
    "ISHARES SILVER TRUST ETF": 3,
    "IYRUSUSD": 3,
    "ISHARES US REAL ESTATE ETF": 3,
    "ITUBUSUSD": 3,
    "ITAU UNIBANCO HOLDING SA": 3,
    "SJMUSUSD": 3,
    "JM SMUCKER COMPANY": 3,
    "JNJUSUSD": 3,
    "JOHNSON & JOHNSON": 3,
    "JCIUSUSD": 3,
    "JOHNSON CONTROLS INC": 3,
    "JPMUSUSD": 3,
    "JPMORGAN CHASE & CO": 3,
    "KUSUSD": 3,
    "KELLOGG CO": 3,
    "KEYUSUSD": 3,
    "KEYCORP": 3,
    "KMBUSUSD": 3,
    "KIMBERLY-CLARK CORP": 3,
    "KMIUSUSD": 3,
    "KINDER MORGAN INC": 3,
    "KSSUSUSD": 3,
    "KOHLS CORP": 3,
    "KRUSUSD": 3,
    "KROGER CO": 3,
    "LVSUSUSD": 3,
    "LAS VEGAS SANDS CORP": 3,
    "LENUSUSD": 3,
    "LENNAR CORP-A": 3,
    "LMTUSUSD": 3,
    "LOCKHEED MARTIN CORP": 3,
    "LUSUSD": 3,
    "LOEWS CORP": 3,
    "LOWUSUSD": 3,
    "LOWE'S COS INC": 3,
    "MUSUSD": 3,
    "MACY'S INC": 3,
    "MROUSUSD": 3,
    "MARATHON OIL CORP": 3,
    "MPCUSUSD": 3,
    "MARATHON PETROLEUM CORP": 3,
    "MAUSUSD": 3,
    "MASTERCARD INC-CLASS A": 3,
    "MCDUSUSD": 3,
    "MCDONALD'S CORP": 3,
    "MCKUSUSD": 3,
    "MCKESSON CORP": 3,
    "MRKUSUSD": 3,
    "MERCK & CO INC": 3,
    "METUSUSD": 3,
    "METLIFE INC": 3,
    "MGMUSUSD": 3,
    "MGM RESORTS INTERNATIONAL": 3,
    "MSFTUSUSD": 3,
    "MICROSOFT CORP": 3,
    "TAPUSUSD": 3,
    "MOLSON COORS BREWING CO -B": 3,
    "MONUSUSD": 3,
    "MONSANTO CO": 3,
    "MSUSUSD": 3,
    "MORGAN STANLEY": 3,
    "NFLXUSUSD": 3,
    "NETFLIX INC": 3,
    "NWLUSUSD": 3,
    "NEWELL BRANDS INC": 3,
    "NEMUSUSD": 3,
    "NEWMONT MINING CORP": 3,
    "NEEUSUSD": 3,
    "NEXTERA ENERGY INC": 3,
    "NKEUSUSD": 3,
    "NIKE INC": 3,
    "NBLUSUSD": 3,
    "NOBLE ENERGY INC": 3,
    "JWNUSUSD": 3,
    "NORDSTROM INC": 3,
    "NSCUSUSD": 3,
    "NORFOLK SOUTHERN CORP": 3,
    "NOCUSUSD": 3,
    "NORTHROP GRUMMAN CORP": 3,
    "NRGUSUSD": 3,
    "NRG ENERGY INC": 3,
    "NVDAUSUSD": 3,
    "NVIDIA CORP": 3,
    "OXYUSUSD": 3,
    "OCCIDENTAL PETROLEUM CORP": 3,
    "OMCUSUSD": 3,
    "OMNICOM GROUP": 3,
    "OKEUSUSD": 3,
    "ONEOK INC": 3,
    "ORCLUSUSD": 3,
    "ORACLE CORP": 3,
    "ORLYUSUSD": 3,
    "O'REILLY AUTOMOTIVE INC": 3,
    "PCGUSUSD": 3,
    "P G & E CORP": 3,
    "PYPLUSUSD": 3,
    "PAYPAL HOLDINGS INC": 3,
    "PHUSUSD": 3,
    "PARKER HANNIFIN CORP": 3,
    "PEPUSUSD": 3,
    "PEPSICO INC": 3,
    "PBRUSUSD": 3,
    "PETROLEO BRASILEIRO SA": 3,
    "PFEUSUSD": 3,
    "PFIZER INC": 3,
    "PMUSUSD": 3,
    "PHILIP MORRIS INTERNATIONAL": 3,
    "PSXUSUSD": 3,
    "PHILLIPS 66": 3,
    "PXDUSUSD": 3,
    "PIONEER NATURAL RESOURCES CO": 3,
    "PNCUSUSD": 3,
    "PNC FINANCIAL SERVICES GROUP": 3,
    "QQQUSUSD": 3,
    "POWERSHARES QQQ ETF": 3,
    "PPGUSUSD": 3,
    "PPG INDUSTRIES INC": 3,
    "PXUSUSD": 3,
    "PRAXAIR INC": 3,
    "PCLNUSUSD": 3,
    "PRICELINE GROUP INCTHE": 3,
    "PGUSUSD": 3,
    "PROCTER & GAMBLE COTHE": 3,
    "PGRUSUSD": 3,
    "PROGRESSIVE CORP": 3,
    "PRUUSUSD": 3,
    "PRUDENTIAL FINANCIAL INC": 3,
    "PSAUSUSD": 3,
    "PUBLIC STORAGE": 3,
    "RRCUSUSD": 3,
    "RANGE RESOURCES CORP": 3,
    "RTNUSUSD": 3,
    "RAYTHEON COMPANY": 3,
    "RHTUSUSD": 3,
    "RED HAT INC": 3,
    "RFUSUSD": 3,
    "REGIONS FINANCIAL CORP": 3,
    "COLUSUSD": 3,
    "ROCKWELL COLLINS INC": 3,
    "CRMUSUSD": 3,
    "SALESFORCECOM INC": 3,
    "SHWUSUSD": 3,
    "SHERWIN-WILLIAMS COMPANY": 3,
    "SCHWUSUSD": 3,
    "SCHWAB (CHARLES) CORP": 3,
    "SPGUSUSD": 3,
    "SIMON PROPERTY GROUP INC": 3,
    "SNAPUSUSD": 3,
    "SNAP INC": 3,
    "SOUSUSD": 3,
    "SOUTHERN COTHE": 3,
    "LUVUSUSD": 3,
    "SOUTHWEST AIRLINES CO": 3,
    "JNKUSUSD": 3,
    "SPDR BARCLAYS CAPITAL HIGH YIELD BOND ETF": 3,
    "DIAUSUSD": 3,
    "SPDR DOW JONES® INDUSTRIAL AVERAGE ETF": 3,
    "GLDUSUSD": 3,
    "SPDR GOLD SHARES ETF": 3,
    "SPYUSUSD": 3,
    "SPDR S&P 500 ETF": 3,
    "XOPUSUSD": 3,
    "SPDR S&P OIL & GAS EXPLOR & PRODTN ETF": 3,
    "SWKUSUSD": 3,
    "STANLEY BLACK & DECKER INC": 3,
    "STTUSUSD": 3,
    "STATE STREET CORP": 3,
    "SYKUSUSD": 3,
    "STRYKER CORP": 3,
    "STIUSUSD": 3,
    "SUNTRUST BANKS INC": 3,
    "SYYUSUSD": 3,
    "SYSCO CORP": 3,
    "TSMUSUSD": 3,
    "TAIWAN SEMICONDUCTOR MANUFACTURING COMPANY LIMITED": 3,
    "TGTUSUSD": 3,
    "TARGET CORP": 3,
    "XLKUSUSD": 3,
    "TECHNOLOGY SELECT SECTOR SPDR FUND": 3,
    "TSLAUSUSD": 3,
    "TESLA MOTORS INC": 3,
    "TEVAUSUSD": 3,
    "TEVA PHARMACEUTICAL-SP ADR": 3,
    "TMOUSUSD": 3,
    "THERMO FISHER SCIENTIFIC INC": 3,
    "TIFUSUSD": 3,
    "TIFFANY & CO": 3,
    "TWXUSUSD": 3,
    "TIME WARNER INC": 3,
    "TJXUSUSD": 3,
    "TJX COMPANIES INC": 3,
    "TRVUSUSD": 3,
    "TRAVELERS COS INCTHE": 3,
    "TWTRUSUSD": 3,
    "TWITTER INC": 3,
    "TSNUSUSD": 3,
    "TYSON FOODS INC-CL A": 3,
    "UNPUSUSD": 3,
    "UNION PACIFIC CORP": 3,
    "UPSUSUSD": 3,
    "UNITED PARCEL SERVICE-CL B": 3,
    "USOUSUSD": 3,
    "UNITED STATES OILSTOCKS": 3,
    "XUSUSD": 3,
    "UNITED STATES STEEL CORP": 3,
    "UTXUSUSD": 3,
    "UNITED TECHNOLOGIES CORP": 3,
    "UNHUSUSD": 3,
    "UNITEDHEALTH GROUP INC": 3,
    "USBUSUSD": 3,
    "US BANCORP": 3,
    "XLUUSUSD": 3,
    "UTILITIES SELECT SECTOR SPDR FUND": 3,
    "VALEUSUSD": 3,
    "VALE SA": 3,
    "VLOUSUSD": 3,
    "VALERO ENERGY CORP": 3,
    "GDXUSUSD": 3,
    "VANECK VECTORS GOLD MINERS ETF": 3,
    "IBBUSUSD": 3,
    "ISHARES NASDAQ BIOTECHNOLOGY ETF": 3,
    "GDXJUSUSD": 3,
    "VANECK VECTORS JUNIOR GOLD MINERS ETF": 3,
    "VEAUSUSD": 3,
    "VANGUARD FTSE DEVELOPED MARKETS ETF": 3,
    "VGKUSUSD": 3,
    "VANGUARD FTSE EUROPE ETF": 3,
    "VNQUSUSD": 3,
    "VANGUARD REIT ETF": 3,
    "XIVUSUSD": 3,
    "VELOCITYSHARES DAILY INVERSE VIX SHORT TERM ETN": 3,
    "VZUSUSD": 3,
    "VERIZON COMMUNICATIONS INC": 3,
    "VFCUSUSD": 3,
    "VF CORP": 3,
    "VUSUSD": 3,
    "VISA INC-CLASS A SHARES": 3,
    "VMCUSUSD": 3,
    "VULCAN MATERIALS CO": 3,
    "WMTUSUSD": 3,
    "WAL-MART STORES INC": 3,
    "DISUSUSD": 3,
    "WALT DISNEY COTHE": 3,
    "WFCUSUSD": 3,
    "WELLS FARGO & CO": 3,
    "HCNUSUSD": 3,
    "WELLTOWER INC": 3,
    "WHRUSUSD": 3,
    "WHIRLPOOL CORP": 3,
    "GWWUSUSD": 3,
    "WW GRAINGER INC": 3,
    "YUMUSUSD": 3,
    "YUM! BRANDS INC": 3,
    "ZBHUSUSD": 3,
    "ZIMMER BIOMET HOLDINGS INC": 3,
    "BUNDTREUR": 3,
    "GERMAN GOVERNMENT BOND": 3,
    "UKGILTTRGBP": 3,
    "UK GOVERNMENT BOND": 3,
    "USTBONDTRUSD": 3,
    "US GOVERNMENT BOND": 3,
}
