"""Dukascopy acquisition contracts and independently checked BI5 decoding.

The live acquisition operation fails closed until host market custody has an
approved catalog schema. CDN package transport remains unavailable pending a
reviewed reuse contract and independently verified package parser.
"""
# ruff: noqa: INP001 -- owner-approved singular backend root is a namespace package.

from __future__ import annotations

import lzma
import math
import re
import struct
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from decimal import ROUND_HALF_EVEN, Decimal
from typing import Any, Literal
from uuid import uuid4

import pyarrow as pa
from app.host.capabilities import HostCapabilities, NetworkAccess
from app.host.composition import PreparedContribution
from app.host.jobs import Budget
from app.host.market_data import (
    M1_SCHEMA,
    TICK_SCHEMA,
    DefinitionRequest,
    MarketDataset,
)
from pydantic import JsonValue

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
                    "mode": {"const": "standard", "default": "standard"},
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
    """Build SQX's date-indexed HTTPS provider URL for one BI5 object."""
    point_value(symbol)
    if day.tzinfo is None or day.utcoffset() != timedelta(0):
        raise ValueError("Provider date must be UTC")
    if not 0 <= hour < HOURS_PER_DAY or kind not in ("ticks", "m1"):
        raise ValueError("Invalid BI5 request")
    parent = (
        f"https://datafeed.dukascopy.com/datafeed/{symbol}/"
        f"{day.year:04d}/{day.month - 1:02d}/{day.day:02d}"
    )
    suffix = f"/{hour:02d}h_ticks.bi5" if kind == "ticks" else "/BID_candles_min_1.bi5"
    return parent + suffix


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
    """Convert float32 millions to integer units within half a unit tolerance.

    The small tolerance accounts only for float32 representation error. A source
    quantity genuinely between integer units is rejected; no volume is clamped.
    """
    if not math.isfinite(value) or value < 0:
        raise ValueError("Invalid provider volume")
    units = Decimal(value) * 1_000_000
    nearest = units.to_integral_value(rounding=ROUND_HALF_EVEN)
    if abs(units - nearest) >= Decimal("0.05") or nearest > UINT64_MAX:
        raise ValueError("Provider volume is not integral in base units")
    return int(nearest)


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
    """Validated one-dataset direct acquisition request."""

    dataset_id: str
    first: date
    last: date
    overwrite: bool
    mode: Literal["standard"]


def _spec(payload: JsonValue) -> DownloadSpec:
    if not isinstance(payload, dict):
        raise TypeError("Invalid Dukascopy download request")
    dataset_id = payload.get("dataset_id")
    first_raw = payload.get("date_from")
    last_raw = payload.get("date_to")
    overwrite = payload.get("overwrite", False)
    mode = payload.get("mode", "standard")
    if (
        not isinstance(dataset_id, str)
        or not isinstance(first_raw, str)
        or not isinstance(last_raw, str)
    ):
        raise TypeError("Invalid Dukascopy download request")
    if not isinstance(overwrite, bool):
        raise TypeError("Invalid overwrite policy")
    if mode != "standard":
        raise ValueError("Requested CDN mode is unavailable")
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
    return DownloadSpec(dataset_id, first, last, overwrite, "standard")


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
    network: NetworkAccess, dataset: MarketDataset, day: date
) -> pa.Table:
    """Fetch one UTC day with no fallback or fabricated missing records."""
    symbol = dataset.symbol.upper()
    midnight = datetime(day.year, day.month, day.day, tzinfo=UTC)
    rows: list[tuple[Any, ...]] = []
    missing_hours = 0
    hours = range(HOURS_PER_DAY) if dataset.kind == "ticks" else range(1)
    for hour in hours:
        url = standard_url(symbol, midnight, dataset.kind, hour)
        response = await network.get(url)
        if response.status == HTTP_MISSING:
            missing_hours += 1
            continue
        if response.status == HTTP_RATE_LIMIT:
            raise ValueError("Dukascopy rate limit reached")
        if response.status != HTTP_OK:
            raise ValueError("Dukascopy provider request failed")
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

    async def run_download(
        request_id: str, spec: DownloadSpec, dataset: MarketDataset
    ) -> None:
        """Process finite UTC days and publish only verified nonempty intervals."""
        result = results[request_id]
        days = (spec.last - spec.first).days + 1
        for offset in range(days):
            day = spec.first + timedelta(days=offset)
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
                table = await _fetch_day(network, dataset, day)
                if table.num_rows:
                    market.replace_interval(
                        kind=dataset.kind,
                        symbol=dataset.symbol,
                        period=period,
                        incoming=table,
                        start_ms=start_ms,
                        end_ms=end_ms,
                        mode=spec.mode,
                    )
                    result["published_days"] = int(result["published_days"]) + 1
                else:
                    result["missing_days"] = int(result["missing_days"]) + 1
            else:
                result["skipped_days"] = int(result["skipped_days"]) + 1
            result["completed_days"] = offset + 1
            result["progress"] = (offset + 1) / days

    async def invoke(operation: str, payload: JsonValue) -> JsonValue:  # noqa: C901, PLR0912, PLR0915 -- fixed owner operation dispatch.
        """Dispatch dataset, job and catalog requests through owner capabilities."""
        if operation == "catalog":
            try:
                brokers = [
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
                    "cdn": "unavailable",
                    "cdn-cn": "unavailable",
                },
                "reason": "market_catalog_migration_required"
                if not market.available()
                else "cdn_contract_unverified",
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
            return vars(market.register_dataset(symbol.lower(), kind, instrument))
        if operation == "download.start":
            spec = _spec(payload)
            dataset = market.get_dataset(spec.dataset_id)
            point_value(dataset.symbol.upper())
            request_id = uuid4().hex
            results[request_id] = {
                "requested_mode": spec.mode,
                "effective_mode": "standard",
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
            return {
                "job_id": job.id,
                "request_id": request_id,
                "requested_mode": spec.mode,
                "effective_mode": "standard",
            }
        if operation in ("download.status", "download.cancel"):
            if not isinstance(payload, dict) or not isinstance(
                payload.get("job_id"), str
            ):
                raise ValueError("Invalid Dukascopy job request")
            job_id = payload["job_id"]
            if job_id not in request_by_job:
                raise ValueError("Dukascopy job unavailable")
            if operation == "download.cancel":
                jobs.cancel(job_id)
            job = jobs.status(job_id)
            return {
                "job_id": job.id,
                "state": job.state,
                **results[request_by_job[job_id]],
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
        raise ValueError("Missing Dukascopy operation")

    async def close() -> None:
        """Release local result references; the host owns task cancellation."""
        results.clear()
        request_by_job.clear()

    return PreparedContribution(
        (
            "catalog",
            "definitions.add",
            "add",
            "download.start",
            "download.status",
            "download.cancel",
            "files.list",
        ),
        invoke,
        close,
    )
