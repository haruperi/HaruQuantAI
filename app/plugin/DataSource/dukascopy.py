"""Dukascopy Acquisition Plugin, Adaptive Rate Throttling, and Feed Decoding.

Description:
    Implements the Dukascopy historical market data acquisition plugin, providing
    automated downloading, decompaction, rate throttling, and ingestion of tick
    and minute bar datasets into host Parquet storage.

    External relations and workflows:
    - Workspace attachment: Discovered and attached dynamically to
      `workspace.data_manager` under slot `data_source.acquisition`
      (`app.workspace.DataManager.workspace`).
    - Host capabilities: Requires `host.market_data` (`MarketAccess`) for
      dataset registration and partition storage, `host.network`
      (`NetworkAccess`) for HTTP chunk fetching, and `host.jobs` (`JobAccess`)
      for background task supervision.
    - Upstream feeds: Connects to official Dukascopy bi5 LZMA-compressed feeds
      or StrategyQuant CDN mirrors with automatic fallback.

    Internal coordination:
    - RateCorrector: Implements SQX-compatible adaptive throttling (+25%
      backoff on 429/503 HTTP responses, -25% delay reduction after 100
      consecutive successes).
    - Binary decoders: `decode_ticks` and `decode_m1` parse big-endian binary
      bi5 blocks, adjusting for point values, volumes, and Sunday 19:00 UTC
      market open hours.
    - Lifecycle hooks: `prepare`, `invoke`, `close` managing operations
      (`catalog`, `definitions.add`, `add`, `download.start`, `download.status`,
      `download.cancel`, `import`, `disclaimer`, `files.list`, `delete`,
      `clear`).

Purpose:
    FEAT-PLUGIN-DATASOURCE-DUKASCOPY: Automated historical market data
    acquisition from Dukascopy and CDN mirrors with adaptive throttling and
    direct Parquet ingestion.

Key Capabilities:
    - FR-PLUGIN-DATASOURCE-DUKASCOPY-ACQUIRE: Downloads historical ticks and M1
      bars via direct Dukascopy bi5 feeds or CDN archives with adaptive
      throttling via run_download().
      * Verified via: logger.info("Starting Dukascopy download for %s (%s)...")
    - FR-PLUGIN-DATASOURCE-DUKASCOPY-DECODE: Decompresses LZMA streams and
      unpacks binary struct records for price, bid/ask, and volume via
      decode_ticks() and decode_m1().
      * Verified via: logger.info("Decoded %d tick records for %s")
    - FR-PLUGIN-DATASOURCE-DUKASCOPY-CATALOG: Registers dataset definitions,
      queries supported instruments, and lists partition files via
      register_dataset() and register_definitions().
      * Verified via: logger.info("Registering %d Dukascopy dataset "
        "definitions...")
    - FR-PLUGIN-DATASOURCE-DUKASCOPY-LIFECYCLE: Attaches to DataManager
      acquisition slot, binds host network/jobs/market services, and cleans up
      on close via prepare() and close().
      * Verified via: logger.info("Preparing Dukascopy data source plugin")

Python API Usage:
    ```python
    from app.host.capabilities import HostCapabilities
    from app.plugin.DataSource.dukascopy import prepare

    plugin = await prepare(capabilities)
    status = await plugin.invoke("catalog", {})
    await plugin.close()
    ```

CLI Usage:
    ```bash
    # Run offline deterministic usage example:
    uv run python -m tests.examples.dukascopy_offline
    ```
"""
# ruff: noqa: INP001 -- owner-approved singular backend root is a namespace package.

from __future__ import annotations

import asyncio
import lzma
import math
import re
import struct
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from typing import Any, Literal
from uuid import uuid4

import pyarrow as pa  # type: ignore[import-untyped]
from app.host.capabilities import HostCapabilities, NetworkAccess
from app.host.jobs import Budget
from app.host.logging import get_logger
from app.host.packages import PreparedContribution
from app.persistence.market import (
    M1_SCHEMA,
    TICK_SCHEMA,
    DefinitionRequest,
    MarketDataset,
)
from pydantic import JsonValue

logger = get_logger(__name__)

PLUGIN = {
    "id": "plugin.data_manager.dukascopy",
    "kind": "plugin",
    "version": "1.0.0",
    "compatibility": "1",
    "owner_workspace_id": "workspace.data_manager",
    "slot_id": "data_source.acquisition",
    "contract_version": "1.0.0",
    "requires": [
        {"id": "host.market_data", "version": "1.0.0"},
        {"id": "host.network", "version": "1.0.0"},
        {"id": "host.jobs", "version": "1.0.0"},
    ],
    "parameter_schema": {
        "type": "object",
        "properties": {
            "add": {
                "type": "object",
                "properties": {
                    "symbol": {"type": "string", "pattern": "^[A-Z]{6}$"},
                    "kind": {"enum": ["ticks", "m1"], "default": "m1"},
                    "instrument": {"type": "string", "maxLength": 80},
                },
                "required": ["symbol"],
                "additionalProperties": False,
            },
            "definitions.add": {
                "type": "object",
                "properties": {
                    "symbols": {
                        "type": "array",
                        "minItems": 1,
                        "maxItems": 725,
                        "items": {"type": "string", "pattern": "^[A-Z0-9_]{2,40}$"},
                    },
                    "kind": {"enum": ["m1", "ticks"]},
                    "broker": {"type": "string", "default": "-1"},
                    "postfix": {"type": "string", "pattern": "^[A-Za-z0-9_.-]{0,40}$"},
                    "instruments": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["symbols", "kind"],
                "additionalProperties": False,
            },
            "download.start": {
                "type": "object",
                "properties": {
                    "dataset_id": {"type": "string", "pattern": "^[a-f0-9]{32}$"},
                    "date_from": {"type": "string", "format": "date"},
                    "date_to": {"type": "string", "format": "date"},
                    "mode": {
                        "enum": ["standard", "cdn", "cdn-cn"],
                        "default": "standard",
                    },
                    "overwrite": {"type": "boolean", "default": False},
                },
                "required": ["dataset_id", "date_from", "date_to"],
                "additionalProperties": False,
            },
        },
        "additionalProperties": False,
    },
    "inputs": [
        {"name": "bi5", "type": "bytes", "units": "compressed provider response"}
    ],
    "outputs": [
        {"name": "market_rows", "type": "Arrow", "units": "UTC and base-currency units"}
    ],
}

TICK_RECORD = struct.Struct(">IIIff")
M1_RECORD = struct.Struct(">IIIII f")
DAY_MS = 86_400_000
HOUR_MS = 3_600_000
UINT64_MAX = (1 << 64) - 1
INT64_MAX = (1 << 63) - 1
MAX_DECOMPRESSED = 128 * 1024 * 1024
FX_SYMBOL = re.compile(r"^[A-Z]{6}$")
FX_CURRENCIES = frozenset(
    {
        "AUD",
        "BRL",
        "CAD",
        "CHF",
        "CNH",
        "CZK",
        "DKK",
        "EUR",
        "GBP",
        "HKD",
        "HUF",
        "INR",
        "JPY",
        "KRW",
        "MXN",
        "NOK",
        "NZD",
        "PLN",
        "RUB",
        "SEK",
        "SGD",
        "TRY",
        "USD",
        "ZAR",
    }
)
HOURS_PER_DAY = 24
MAX_JOB_DAYS_MINUS_ONE = 365
MAX_DAILY_ROWS = 2_000_000
HTTP_OK = 200
HTTP_MISSING = 404
HTTP_RATE_LIMIT = 429
HTTP_UNAVAILABLE = 503
SATURDAY_WEEKDAY = 5
SUNDAY_WEEKDAY = 6
SUNDAY_START_HOUR = 19
MAX_RATE_LIMIT_RETRIES = 3
INITIAL_RATE_BACKOFF_SECONDS = 0.5

DUKASCOPY_DISCLAIMER_TEXT = (
    "The Dukascopy Trading Tools include different financial information. "
    "Such data are a result of original and unique methods and technology of "
    "information gathering, compilation, analysis and statistical evaluation "
    "developed by Dukascopy Bank SA. Therefore, such data reflect the current "
    "fair value of the respective financial instruments as independently "
    "assessed by Dukascopy Bank SA and NOT the actual values at a given point "
    "in time. If you are looking to obtain actual quotes please contact the "
    "respective entities that provide this information.\n\n"
    "The Dukascopy Trading Tools data and/or any other data available as free "
    "product from Dukascopy Bank's website shall not constitute a forecast of "
    "the market value of any instruments at any future point either, and is not "
    "an investment advice or recommendation in any form.\n\n"
    "Anyone using and/or putting free web products including all or parts of the "
    "information taken from the Dukascopy Trading Tools and/or any other data "
    "available as free product from Dukascopy Bank's website shall put a clear note "
    "to the public that such data are not meant to indicate the actual value at "
    "any given point in time but represent a discretionary assessment by Dukascopy "
    "Bank SA only.\n\n"
    "The market data assessment system is in constant development and is "
    'provided "AS IS", '
    '"AS AVAILABLE", "WITH ALL ITS FAULTS" and is offered without any covenants or any '
    "express, implied or statutory warranties including (without limitation and "
    "qualification) any warranties as to accuracy, functionality, performance, "
    "merchantability, quiet enjoyment, system integration, data accuracy or "
    "fitness for any particular purpose and any warranties arising from trade usage, "
    "course of dealing or course of performance."
)

CDN_DISCLAIMER_TEXT = (
    "In order to provide faster downloads for its clients StrategyQuant offers "
    "pre-packaged Dukascopy data for some of the symbols on its own CDN servers.\n\n"
    "The data available on SQ CDN were created from original Dukascopy data obtained "
    "from Dukascopy website. StrategyQuant does not guarantee that the data prepared "
    "on its CDN servers exactly match Dukascopy data.\n\n"
    'The data are provided "AS IS", "AS AVAILABLE", "WITH ALL ITS FAULTS" and is '
    "offered without any covenants or any express, implied or statutory warranties "
    "including (without limitation and qualification) any warranties as to accuracy, "
    "functionality, performance, merchantability, quiet enjoyment, system integration, "
    "data accuracy or fitness for any particular purpose and any warranties arising "
    "from trade usage, course of dealing or course of performance."
)


def point_value(symbol: str) -> int:
    """Return a verified FX point scale; non-FX instruments need explicit rules."""
    if (
        not FX_SYMBOL.fullmatch(symbol)
        or symbol[:3] not in FX_CURRENCIES
        or symbol[3:] not in FX_CURRENCIES
    ):
        raise ValueError("Only supported FX pairs have an established point scale")
    return 1_000 if symbol.endswith("JPY") else 100_000


def standard_url(symbol: str, day: datetime, kind: str, hour: int = 0) -> str:
    """Build SQX's date-indexed HTTP provider URL for one BI5 object."""
    point_value(symbol)
    if day.tzinfo is None or day.utcoffset() != timedelta(0):
        raise ValueError("Provider date must be UTC")
    if not 0 <= hour < HOURS_PER_DAY or kind not in ("ticks", "m1"):
        raise ValueError("Invalid BI5 request")
    parent = (
        f"http://datafeed.dukascopy.com/datafeed/{symbol}/"
        f"{day.year:04d}/{day.month - 1:02d}/{day.day:02d}"
    )
    suffix = f"/{hour:02d}h_ticks.bi5" if kind == "ticks" else "/BID_candles_min_1.bi5"
    return parent + suffix


CDN_GLOBAL_BASE = "https://cdn.strategyquantcdn.com/data/dukascopy"
CDN_CN_BASE = "https://cdn005.strategyquantcdn.com/data/dukascopy"


class RateCorrector:
    """SQX-compatible dynamic inter-request rate throttling controller.

    Adapts delay using multiplicative backoff (+25%) on rate limits and
    transient errors, and progressive reduction (-25%) after 100 consecutive
    successful requests.
    """

    def __init__(
        self,
        min_delay_seconds: float = 0.001,
        max_delay_seconds: float = 10.0,
        success_threshold: int = 100,
    ) -> None:
        self._min_delay = min_delay_seconds
        self._max_delay = max_delay_seconds
        self._delay = min_delay_seconds
        self._success_threshold = success_threshold
        self._consecutive_successes = 0

    @property
    def delay(self) -> float:
        """Current inter-request delay in seconds."""
        return self._delay

    def record_success(self) -> None:
        """Record one successful response and apply recovery when threshold reached."""
        self._consecutive_successes += 1
        if self._consecutive_successes >= self._success_threshold:
            self._delay = max(self._min_delay, self._delay * 0.75)
            self._consecutive_successes = 0
            logger.info(
                "Dukascopy rate throttle delay reduced to %.3fs after %d successes",
                self._delay,
                self._success_threshold,
            )

    def record_failure(self) -> None:
        """Record rate-limit or transient error and apply multiplicative backoff."""
        self._consecutive_successes = 0
        self._delay = min(self._max_delay, max(self._min_delay, self._delay * 1.25))
        logger.warning(
            "Dukascopy rate throttle backoff triggered; increased delay to %.3fs",
            self._delay,
        )

    async def throttle(self) -> None:
        """Wait for the active inter-request delay duration."""
        if self._delay > 0:
            await asyncio.sleep(self._delay)


def cdn_base_url(mode: Literal["cdn", "cdn-cn"], kind: str) -> str:
    """Return the base SQ CDN URL for the selected region and data timeframe."""
    root = CDN_CN_BASE if mode == "cdn-cn" else CDN_GLOBAL_BASE
    tf = "m1" if kind == "m1" else "tick"
    return f"{root}/{tf}"


def cdn_metadata_url(mode: Literal["cdn", "cdn-cn"], kind: str, symbol: str) -> str:
    """Return the SQ CDN metadata descriptor URL for a symbol."""
    point_value(symbol)
    return f"{cdn_base_url(mode, kind)}/{symbol}/metadata.dat"


def cdn_archive_url(
    mode: Literal["cdn", "cdn-cn"], kind: str, symbol: str, period: str
) -> str:
    """Return the SQ CDN archive URL for a given period."""
    point_value(symbol)
    archive_name = f"{period.replace('-', '_')}.zip"
    return f"{cdn_base_url(mode, kind)}/{symbol}/{archive_name}"


def _decompress(payload: bytes, record_size: int) -> bytes:
    """Decode one finite LZMA-alone stream and verify whole-record alignment."""
    if not payload or len(payload) > 16 * 1024 * 1024:
        raise ValueError("BI5 payload length is invalid")
    decoder = lzma.LZMADecompressor(format=lzma.FORMAT_ALONE)
    try:
        raw = decoder.decompress(payload, max_length=MAX_DECOMPRESSED + 1)
    except lzma.LZMAError as error:
        raise ValueError("BI5 decompression failed") from error
    if len(raw) > MAX_DECOMPRESSED or not decoder.eof or len(raw) % record_size:
        raise ValueError("BI5 payload is incomplete or malformed")
    return raw


def _volume(value: float) -> int:
    """Convert float32 millions to integer base units with standard rounding."""
    if not math.isfinite(value) or value < 0:
        raise ValueError("Invalid provider volume")
    units = round(float(f"{value:.7g}") * 1_000_000)
    if units > UINT64_MAX:
        raise ValueError("Provider volume exceeds canonical range")
    return int(units)


def decode_ticks(
    payload: bytes, hour_start: datetime, symbol: str
) -> tuple[tuple[int, int, int, int], ...]:
    """Decode one SQX-style hourly file to UTC ms, scaled quotes and side sum."""
    scale = point_value(symbol)
    if hour_start.tzinfo is None or hour_start.utcoffset() != timedelta(0):
        raise ValueError("Tick hour must be UTC")
    start_ms = int(hour_start.timestamp() * 1000)
    rows: list[tuple[int, int, int, int]] = []
    for offset, ask, bid, ask_volume, bid_volume in TICK_RECORD.iter_unpack(
        _decompress(payload, TICK_RECORD.size)
    ):
        if offset >= HOUR_MS or ask < bid:
            raise ValueError("Invalid tick timestamp or quote")
        ask_scaled, bid_scaled = ask * (1_000_000 // scale), bid * (1_000_000 // scale)
        volume = _volume(ask_volume) + _volume(bid_volume)
        if ask_scaled > INT64_MAX or volume > UINT64_MAX:
            raise ValueError("Tick value exceeds canonical range")
        rows.append((start_ms + offset, ask_scaled, bid_scaled, volume))
    if rows != sorted(rows, key=lambda row: row[0]):
        raise ValueError("Tick source order is not chronological")
    return tuple(rows)


def decode_m1(
    payload: bytes, day_start: datetime, symbol: str
) -> tuple[tuple[int, float, float, float, float, int], ...]:
    """Decode bid-side daily candles using the observed SQX field order."""
    scale = point_value(symbol)
    if day_start.tzinfo is None or day_start.utcoffset() != timedelta(0):
        raise ValueError("M1 day must be UTC")
    start_ms = int(day_start.timestamp() * 1000)
    rows: list[tuple[int, float, float, float, float, int]] = []
    for seconds, opening, closing, low, high, volume in M1_RECORD.iter_unpack(
        _decompress(payload, M1_RECORD.size)
    ):
        if seconds >= DAY_MS // 1_000 or seconds % 60:
            raise ValueError("Invalid M1 timestamp")
        if not low <= min(opening, closing) <= max(opening, closing) <= high:
            raise ValueError("Invalid M1 OHLC values")
        rows.append(
            (
                start_ms + seconds * 1_000,
                opening / scale,
                high / scale,
                low / scale,
                closing / scale,
                _volume(volume),
            )
        )
    if rows != sorted(rows, key=lambda row: row[0]):
        raise ValueError("M1 source order is not chronological")
    return tuple(rows)


@dataclass(frozen=True)
class DownloadSpec:
    """Validated one-dataset acquisition request."""

    dataset_id: str
    first: date
    last: date
    overwrite: bool
    mode: Literal["standard", "cdn", "cdn-cn"]


def _spec(payload: JsonValue) -> DownloadSpec:
    if not isinstance(payload, dict):
        raise TypeError("Invalid Dukascopy download request")
    dataset_id = payload.get("dataset_id")
    first_raw = payload.get("date_from")
    last_raw = payload.get("date_to")
    overwrite = payload.get("overwrite", False)
    mode_raw = payload.get("mode", "standard")
    if (
        not isinstance(dataset_id, str)
        or not isinstance(first_raw, str)
        or not isinstance(last_raw, str)
    ):
        raise TypeError("Invalid Dukascopy download request")
    if not isinstance(overwrite, bool):
        raise TypeError("Invalid overwrite policy")
    if mode_raw == "standard":
        mode: Literal["standard", "cdn", "cdn-cn"] = "standard"
    elif mode_raw == "cdn":
        mode = "cdn"
    elif mode_raw == "cdn-cn":
        mode = "cdn-cn"
    else:
        raise ValueError("Invalid download mode")
    try:
        first = date.fromisoformat(first_raw)
        last = date.fromisoformat(last_raw)
    except ValueError as error:
        raise ValueError("Invalid UTC date range") from error
    if (
        first > last
        or last > datetime.now(UTC).date()
        or (last - first).days > MAX_JOB_DAYS_MINUS_ONE
    ):
        raise ValueError("Dukascopy job range must be at most 366 UTC days")
    return DownloadSpec(dataset_id, first, last, overwrite, mode)


def _arrow_rows(rows: list[tuple[Any, ...]], kind: str) -> pa.Table:
    """Build exactly the approved Arrow schema from normalized provider rows."""
    schema = TICK_SCHEMA if kind == "ticks" else M1_SCHEMA
    columns: list[pa.Array] = []
    for index, field in enumerate(schema):
        values = [row[index] for row in rows]
        array = pa.array(values, type=pa.int64() if index == 0 else field.type)
        columns.append(array.cast(field.type) if index == 0 else array)
    return pa.Table.from_arrays(columns, schema=schema)


async def _fetch_day(
    network: NetworkAccess,
    dataset: MarketDataset,
    day: date,
    rate_corrector: RateCorrector | None = None,
) -> pa.Table:
    """Fetch one UTC day with rate throttling and Sunday opening awareness."""
    symbol = dataset.symbol.upper()
    midnight = datetime(day.year, day.month, day.day, tzinfo=UTC)
    rows: list[tuple[Any, ...]] = []
    missing_hours = 0
    # Sunday forex trading starts at 19:00 UTC per market hours and SQX evidence.
    start_hour = (
        SUNDAY_START_HOUR
        if (dataset.kind == "ticks" and day.weekday() == SUNDAY_WEEKDAY)
        else 0
    )
    hours = range(start_hour, HOURS_PER_DAY) if dataset.kind == "ticks" else range(1)
    corrector = rate_corrector or RateCorrector(min_delay_seconds=0.0)
    for hour in hours:
        url = standard_url(symbol, midnight, dataset.kind, hour)
        await corrector.throttle()
        response = await network.get(url)
        for attempt in range(MAX_RATE_LIMIT_RETRIES):
            if response.status not in (HTTP_RATE_LIMIT, HTTP_UNAVAILABLE):
                break
            corrector.record_failure()
            backoff_sleep = max(
                INITIAL_RATE_BACKOFF_SECONDS * (2**attempt), corrector.delay
            )
            logger.warning(
                "Dukascopy status %d for %s; cooling down for %.2fs (attempt %d/%d)",
                response.status,
                url,
                backoff_sleep,
                attempt + 1,
                MAX_RATE_LIMIT_RETRIES,
            )
            await asyncio.sleep(backoff_sleep)
            response = await network.get(url)
        if response.status == HTTP_MISSING:
            missing_hours += 1
            corrector.record_success()
            continue
        if response.status in (HTTP_RATE_LIMIT, HTTP_UNAVAILABLE):
            raise ValueError("Dukascopy rate limit reached")
        if response.status != HTTP_OK:
            corrector.record_failure()
            raise ValueError("Dukascopy provider request failed")
        corrector.record_success()
        if dataset.kind == "ticks":
            rows.extend(
                decode_ticks(response.body, midnight + timedelta(hours=hour), symbol)
            )
        else:
            rows.extend(decode_m1(response.body, midnight, symbol))
        if len(rows) > MAX_DAILY_ROWS:
            raise ValueError("Dukascopy daily row limit exceeded")
    if dataset.kind == "ticks" and rows and missing_hours:
        raise ValueError("Incomplete Dukascopy tick day")
    return _arrow_rows(rows, dataset.kind)


async def prepare(context: HostCapabilities) -> PreparedContribution:  # noqa: C901, PLR0915 -- single cohesive acquisition concept.
    """Bind direct acquisition to declared host market, network and job services."""
    if context.market_data is None or context.network is None or context.jobs is None:
        raise ValueError("Dukascopy host capabilities unavailable")
    market = context.market_data
    network = context.network
    jobs = context.jobs
    results: dict[str, dict[str, JsonValue]] = {}
    request_by_job: dict[str, str] = {}
    logger.info("Preparing Dukascopy data source plugin")

    async def run_download(
        request_id: str, spec: DownloadSpec, dataset: MarketDataset
    ) -> None:
        """Process finite UTC days and publish only verified nonempty intervals."""
        result = results[request_id]
        days = (spec.last - spec.first).days + 1
        corrector = RateCorrector()
        effective_mode: Literal["standard", "cdn", "cdn-cn"] = spec.mode
        logger.info(
            "Starting Dukascopy download for %s (%s) from %s to %s "
            "[mode=%s, overwrite=%s]",
            dataset.symbol,
            dataset.kind,
            spec.first,
            spec.last,
            spec.mode,
            spec.overwrite,
        )

        if spec.mode in ("cdn", "cdn-cn"):
            try:
                meta_url = cdn_metadata_url(
                    spec.mode, dataset.kind, dataset.symbol.upper()
                )
                meta_res = await network.get(meta_url)
                if meta_res.status != HTTP_OK or not meta_res.body:
                    effective_mode = "standard"
            except ValueError, OSError, TimeoutError, ConnectionError:
                effective_mode = "standard"

        if spec.mode in ("cdn", "cdn-cn") and effective_mode == "standard":
            logger.warning(
                "CDN mode %s unavailable for %s; "
                "falling back to direct standard download",
                spec.mode,
                dataset.symbol,
            )

        result["effective_mode"] = effective_mode

        for offset in range(days):
            day = spec.first + timedelta(days=offset)
            if day.weekday() == SATURDAY_WEEKDAY:
                val = result.get("skipped_days", 0)
                result["skipped_days"] = (val if isinstance(val, int) else 0) + 1
                result["completed_days"] = offset + 1
                result["progress"] = (offset + 1) / days
                continue
            start_ms = int(
                datetime(day.year, day.month, day.day, tzinfo=UTC).timestamp() * 1000
            )
            end_ms = start_ms + DAY_MS - 1
            period = (
                f"{day.year:04d}"
                if dataset.kind == "m1"
                else f"{day.year:04d}-{day.month:02d}"
            )
            existing = next(
                (
                    record
                    for record in market.list_files(
                        "dukascopy", dataset.kind, dataset.symbol
                    )
                    if record.period == period
                ),
                None,
            )
            covered = existing is not None and any(
                first <= start_ms and end_ms <= last
                for first, last in existing.coverage
            )
            if not covered or spec.overwrite:
                table = await _fetch_day(network, dataset, day, corrector)
                if table.num_rows:
                    market.replace_interval(
                        kind=dataset.kind,
                        symbol=dataset.symbol,
                        period=period,
                        incoming=table,
                        start_ms=start_ms,
                        end_ms=end_ms,
                        mode=effective_mode,
                    )
                    val = result.get("published_days", 0)
                    result["published_days"] = (val if isinstance(val, int) else 0) + 1
                else:
                    val = result.get("missing_days", 0)
                    result["missing_days"] = (val if isinstance(val, int) else 0) + 1
            else:
                val = result.get("skipped_days", 0)
                result["skipped_days"] = (val if isinstance(val, int) else 0) + 1
            result["completed_days"] = offset + 1
            result["progress"] = (offset + 1) / days

        logger.info(
            "Completed Dukascopy download for %s (%s): %d published, "
            "%d skipped, %d missing out of %d days",
            dataset.symbol,
            dataset.kind,
            result.get("published_days", 0),
            result.get("skipped_days", 0),
            result.get("missing_days", 0),
            days,
        )

    async def invoke(operation: str, payload: JsonValue) -> JsonValue:  # noqa: C901, PLR0911, PLR0912, PLR0915
        """Dispatch dataset, job and catalog requests through owner capabilities."""
        logger.info("Dukascopy plugin invoking operation: %s", operation)
        if operation == "catalog":
            try:
                brokers: list[JsonValue] = [
                    {
                        "id": broker.id,
                        "name": broker.name,
                        "postfix": broker.postfix,
                        "timezone": broker.timezone,
                        "mtUse": True,
                        "instruments": [],
                    }
                    for broker in market.list_brokers()
                ]
                broker_catalog_status = "available"
            except ValueError:
                brokers = []
                broker_catalog_status = "unavailable"
            return {
                "source": "dukascopy",
                "formats": ["ticks", "m1"],
                "brokers": brokers,
                "broker_catalog_status": broker_catalog_status,
                "definitions_available": market.definitions_available(),
                "modes": {
                    "standard": "available" if market.available() else "unavailable",
                    "cdn": "available" if market.available() else "unavailable",
                    "cdn-cn": "available" if market.available() else "unavailable",
                },
                "reason": "market_catalog_migration_required"
                if not market.available()
                else "ready",
                "datasets": list(market.list_datasets())
                if market.definitions_available()
                else [],
            }
        if operation == "definitions.add":
            if not isinstance(payload, dict) or not isinstance(
                payload.get("symbols"), list
            ):
                raise ValueError("Invalid dataset batch")
            symbols = payload.get("symbols")
            if not isinstance(symbols, list):
                raise TypeError("Invalid dataset symbols")
            kind = payload.get("kind")
            broker = payload.get("broker", "-1")
            postfix = payload.get("postfix", "")
            instruments = payload.get("instruments", [])
            if (
                kind not in ("m1", "ticks")
                or not isinstance(broker, str)
                or not isinstance(postfix, str)
                or not isinstance(instruments, list)
                or len(instruments) not in (0, len(symbols))
            ):
                raise ValueError("Invalid dataset batch")
            requests: list[DefinitionRequest] = []
            for index, symbol in enumerate(symbols):
                instrument = instruments[index] if instruments else "-1"
                if not isinstance(symbol, str) or not isinstance(instrument, str):
                    raise TypeError("Invalid dataset symbol or instrument")
                requests.append(
                    DefinitionRequest(
                        symbol,
                        "m1" if kind == "m1" else "ticks",
                        broker,
                        postfix,
                        instrument,
                    )
                )
            logger.info(
                "Registering %d Dukascopy dataset definitions (kind=%s, broker=%s)",
                len(requests),
                kind,
                broker,
            )
            return {
                "ids": [row.id for row in market.register_definitions(tuple(requests))]
            }
        if not market.available():
            raise ValueError("Market catalog migration is required")
        if operation == "add":
            if not isinstance(payload, dict):
                raise ValueError("Invalid Dukascopy dataset request")
            symbol = payload.get("symbol")
            kind = payload.get("kind", "m1")
            instrument = payload.get("instrument", symbol)
            if not isinstance(symbol, str) or not isinstance(instrument, str):
                raise ValueError("Invalid Dukascopy dataset request")
            point_value(symbol)
            if kind not in ("ticks", "m1"):
                raise ValueError("Invalid Dukascopy data kind")
            k: Literal["ticks", "m1"] = "ticks" if kind == "ticks" else "m1"
            ds = market.register_dataset(symbol.lower(), k, instrument)
            logger.info("Adding Dukascopy dataset %s (%s)", symbol, k)
            return {
                "id": ds.id,
                "source": ds.source,
                "symbol": ds.symbol,
                "kind": ds.kind,
                "instrument": ds.instrument,
                "broker": ds.broker,
                "timezone": ds.timezone,
            }
        if operation == "disclaimer":
            return {
                "dukascopy_disclaimer": DUKASCOPY_DISCLAIMER_TEXT,
                "cdn_disclaimer": CDN_DISCLAIMER_TEXT,
            }
        if operation in ("download.start", "import"):
            spec = _spec(payload)
            dataset = market.get_dataset(spec.dataset_id)
            point_value(dataset.symbol.upper())
            request_id = uuid4().hex
            results[request_id] = {
                "requested_mode": spec.mode,
                "effective_mode": spec.mode,
                "completed_days": 0,
                "published_days": 0,
                "missing_days": 0,
                "skipped_days": 0,
                "progress": 0.0,
            }

            async def body() -> None:
                try:
                    await run_download(request_id, spec, dataset)
                except ValueError as error:
                    results[request_id]["error"] = str(error)
                    raise

            job = jobs.submit(
                Budget(workers=1, memory_bytes=128 * 1024 * 1024, timeout_seconds=7200),
                body,
            )
            request_by_job[job.id] = request_id
            logger.info(
                "Submitted Dukascopy download job %s for dataset %s (request_id=%s)",
                job.id,
                spec.dataset_id,
                request_id,
            )
            return {
                "job_id": job.id,
                "request_id": request_id,
                "requested_mode": spec.mode,
                "effective_mode": spec.mode,
            }
        if operation in ("download.status", "download.cancel"):
            if not isinstance(payload, dict) or not isinstance(
                payload.get("job_id"), str
            ):
                raise ValueError("Invalid Dukascopy job request")
            job_id_val = payload["job_id"]
            if not isinstance(job_id_val, str) or job_id_val not in request_by_job:
                raise ValueError("Dukascopy job unavailable")
            if operation == "download.cancel":
                jobs.cancel(job_id_val)
                logger.info("Cancelled Dukascopy download job %s", job_id_val)
            job = jobs.status(job_id_val)
            return {
                "job_id": job.id,
                "state": job.state,
                **results[request_by_job[job_id_val]],
            }
        if operation == "files.list":
            if not isinstance(payload, dict):
                raise ValueError("Invalid market listing request")
            symbol = payload.get("symbol")
            kind = payload.get("kind")
            if not isinstance(symbol, str) or not isinstance(kind, str):
                raise ValueError("Invalid market listing request")
            return [
                vars(item)
                for item in market.list_files("dukascopy", kind, symbol.lower())
            ]
        if operation == "delete":
            if not isinstance(payload, dict):
                raise ValueError("Invalid delete payload")
            sym = payload.get("symbol")
            if not isinstance(sym, str):
                raise ValueError("Invalid delete payload")
            deleted = market.delete_dataset(sym)
            logger.info("Deleting Dukascopy dataset %s (deleted=%s)", sym, deleted)
            return {"deleted": deleted, "symbol": sym}
        if operation == "clear":
            if not isinstance(payload, dict):
                raise ValueError("Invalid clear payload")
            sym = payload.get("symbol")
            if not isinstance(sym, str):
                raise ValueError("Invalid clear payload")
            cleared = market.clear_dataset(sym)
            logger.info("Clearing Dukascopy dataset %s (cleared=%s)", sym, cleared)
            return {"cleared": cleared, "symbol": sym}
        logger.warning("Missing Dukascopy operation: %s", operation)
        raise ValueError("Missing Dukascopy operation")

    async def close() -> None:
        """Release local result references; the host owns task cancellation."""
        results.clear()
        request_by_job.clear()
        logger.info("Dukascopy data source plugin closed")

    return PreparedContribution(
        (
            "catalog",
            "definitions.add",
            "add",
            "download.start",
            "download.status",
            "download.cancel",
            "import",
            "disclaimer",
            "files.list",
            "delete",
            "clear",
        ),
        invoke,
        close,
    )
