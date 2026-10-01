"""Script-derived Yahoo Finance acquisition.

Description:
    Preserves the owner's Yahoo timeframe, chart parsing and resampling behavior.
    The host supplies isolated HTTP sessions, jobs and immutable market custody;
    this module never opens a database or configures application logging.
Purpose:
    FEAT-DM-YAHOO_ACQUISITION: Real Yahoo Finance data acquisition.
Key Capabilities:
    - FR-YAHOO-CHART-QUERY: Decode Yahoo chart responses; log completed chunks.
    - FR-YAHOO-RESAMPLE: Preserve script OHLCV aggregation; log resulting rows.
    - FR-YAHOO-PUBLISH: Publish actual rows; log committed partition counts.
Python API Usage:
    contribution = await prepare(capabilities)
    catalog = await contribution.invoke("catalog", {})
CLI Usage:
    Invoke the declared operations through the authenticated host CLI.

Implementation input: SQX_REFERENCE_ROOT/scripts/yahoo.py; fingerprint in the
approved integration task's source-inventory.json. No independent SQX parity claim.
"""

# ruff: noqa: INP001 -- approved singular plugin namespace.

from __future__ import annotations

import asyncio
import datetime
import time
from dataclasses import dataclass, field
from typing import Any, cast
from urllib.parse import quote

import httpx
import pandas as pd  # type: ignore[import-untyped]
import pyarrow as pa  # type: ignore[import-untyped]
from app.host.capabilities import HostCapabilities, JobAccess, MarketAccess
from app.host.contracts import Document
from app.host.jobs import Budget
from app.host.logging import get_logger
from app.host.network import SourceNetwork
from app.host.packages import PreparedContribution
from pydantic import Field, JsonValue, model_validator

logger = get_logger(__name__)

PLUGIN = {
    "id": "plugin.data_manager.yahoo",
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
    "inputs": [{"name": "request", "type": "YahooDownload"}],
    "outputs": [{"name": "partitions", "type": "Parquet", "units": "source OHLCV"}],
}

PRIMARY_BASE_URL = "https://query1.finance.yahoo.com"
FALLBACK_BASE_URL = "https://query2.finance.yahoo.com"
MAX_ATTEMPTS = 5
COOKIE_LIFETIME = 1800
HTTP_OK = 200


class YahooDefinition(Document):
    """Provider identity and supported parameter defaults."""

    symbol: str = Field(min_length=1, max_length=128, pattern=r"^[A-Za-z0-9_.^=\-]+$")
    postfix: str = Field(default="", max_length=64, pattern=r"^[A-Za-z0-9_.\-]*$")
    timeframe: str = Field(default="D1", min_length=1, max_length=8)
    include_adj_close: bool = True

    @model_validator(mode="after")
    def timeframe_supported(self) -> YahooDefinition:
        """Validate against the same interval conversion used by acquisition."""
        _, rule = normalize_timeframe(self.timeframe)
        if rule is not None and rule.startswith("0"):
            raise ValueError("Timeframe must be positive")
        return self


class YahooDownload(Document):
    """One finite inclusive range for a registered dataset."""

    dataset_id: str = Field(pattern=r"^[0-9a-f]{32}$")
    date_from: datetime.date
    date_to: datetime.date
    overwrite: bool = False

    @model_validator(mode="after")
    def ordered_dates(self) -> YahooDownload:
        """Reject inverted or future ranges before submitting a job."""
        if (
            self.date_from > self.date_to
            or self.date_to > datetime.datetime.now(datetime.UTC).date()
        ):
            raise ValueError("Choose an ordered historical date range")
        return self


class YahooSession:
    """Script cookie/crumb and mirror behavior with host-scoped transport."""

    def __init__(self, network: SourceNetwork) -> None:
        self.network = network
        self.crumb: str | None = None
        self.expiry = 0.0
        self.lock = asyncio.Lock()

    async def get_crumb(self, *, refresh: bool = False) -> str | None:
        """Warm Yahoo cookies and cache the optional crumb for thirty minutes."""
        async with self.lock:
            if not refresh and self.crumb and time.monotonic() < self.expiry:
                return self.crumb
            self.crumb = None
            try:
                await self.network.get("https://fc.yahoo.com", request_seconds=8)
                response = await self.network.get(
                    PRIMARY_BASE_URL + "/v1/test/getcrumb", request_seconds=10
                )
                crumb = response.body.decode("utf-8").strip()
                if (
                    response.status == HTTP_OK
                    and crumb
                    and "{" not in crumb
                    and "<" not in crumb
                ):
                    self.crumb = crumb
                    self.expiry = time.monotonic() + COOKIE_LIFETIME
            except httpx.HTTPError, UnicodeError, TimeoutError:
                logger.info("Yahoo optional cookie initialization unavailable")
            return self.crumb

    async def fetch_json(
        self, path: str, params: dict[str, str | int]
    ) -> dict[str, Any]:
        """Use finite retries and the script's secondary chart origin."""
        for origin in (PRIMARY_BASE_URL, FALLBACK_BASE_URL):
            for attempt in range(MAX_ATTEMPTS):
                crumb = await self.get_crumb()
                query = {**params, **({"crumb": crumb} if crumb else {})}
                try:
                    response = await self.network.get(
                        origin + path, params=query, request_seconds=15
                    )
                except httpx.HTTPError, TimeoutError:
                    logger.info("Yahoo transport retry: attempt=%d", attempt + 1)
                else:
                    if response.status == HTTP_OK:
                        result = response.json()
                        if not isinstance(result, dict):
                            raise ValueError("Invalid Yahoo response document")
                        return result
                    if response.status in (404, 422):
                        raise ValueError("Yahoo symbol or requested data unavailable")
                    if response.status in (401, 403):
                        await self.get_crumb(refresh=True)
                    logger.info(
                        "Yahoo retry: status=%d attempt=%d",
                        response.status,
                        attempt + 1,
                    )
                await asyncio.sleep(min(0.5 * 2**attempt, 10))
        raise ValueError("Yahoo retrieval exhausted its retry budget")

    async def metadata(self, symbol: str) -> dict[str, Any]:
        """Read real symbol metadata rather than fabricating a catalog match."""
        data = await self.fetch_json(
            "/v8/finance/chart/" + quote(symbol, safe=""),
            {"interval": "1d", "range": "1d"},
        )
        results = data.get("chart", {}).get("result")
        if not results:
            raise ValueError("Yahoo symbol metadata unavailable")
        metadata = results[0].get("meta", {})
        if not isinstance(metadata, dict) or not metadata.get("symbol"):
            raise ValueError("Yahoo symbol metadata invalid")
        return metadata

    async def chart(
        self,
        symbol: str,
        interval: str,
        start: datetime.datetime,
        end: datetime.datetime,
        include_adj_close: bool,
    ) -> pd.DataFrame:
        """Fetch one source-script interval and apply its chart decoder."""
        data = await self.fetch_json(
            "/v8/finance/chart/" + quote(symbol, safe=""),
            {
                "interval": interval,
                "period1": int(start.timestamp()),
                "period2": int(end.timestamp()),
                "events": "div,splits",
                "includeAdjustedClose": "true" if include_adj_close else "false",
            },
        )
        return parse_chart(data, symbol, include_adj_close)


@dataclass
class YahooRuntime:
    """One prepared source, with real host jobs and no ambient global state."""

    market: MarketAccess
    jobs: JobAccess
    session: YahooSession
    progress: dict[str, dict[str, Any]] = field(default_factory=dict)

    async def acquire(self, request: YahooDownload, progress: dict[str, Any]) -> None:
        """Fetch every chunk, preserve the script's merge policy and publish years."""
        definition = self.market.source_definition(request.dataset_id)
        options = YahooDefinition.model_validate(definition["options"]["parameters"])
        metadata = definition["options"]["metadata"]
        interval, rule = normalize_timeframe(options.timeframe)
        start = parse_date_param(request.date_from)
        end = parse_date_param(request.date_to, end_of_day=True)
        chunks = _generate_date_chunks(start, end, interval)
        progress["total_chunks"] = len(chunks)
        frames = []
        for lower, upper in chunks:
            frame = await self.session.chart(
                options.symbol, interval, lower, upper, options.include_adj_close
            )
            if not frame.empty:
                frames.append(frame)
            progress["completed_chunks"] += 1
            logger.info(
                "Yahoo chunk completed: id=%s count=%d",
                request.dataset_id,
                progress["completed_chunks"],
            )
        if not frames:
            raise ValueError("Yahoo returned no rows for the requested range")
        data = pd.concat(frames)
        data = data[~data.index.duplicated(keep="last")].sort_index()
        data = data.loc[(data.index >= start) & (data.index <= end)]
        if rule:
            data = resample_to_timeframe(data, rule)
        prices = [
            c
            for c in ("Open", "High", "Low", "Close", "Adj Close")
            if c in data.columns
        ]
        data[prices] = data[prices].round(int(metadata.get("priceHint", 2)))
        revisions = {
            record["period"]: record
            for record in self.market.source_partitions(request.dataset_id)
        }
        for year, incoming in data.groupby(data.index.year):
            period = str(year)
            prior = revisions.get(period)
            merged = incoming
            if prior:
                old = (
                    self.market.read_source_partition(request.dataset_id, period)
                    .to_pandas()
                    .set_index("DateTime")
                )
                merged = pd.concat([old, incoming])
                merged = merged[
                    ~merged.index.duplicated(
                        keep="last" if request.overwrite else "first"
                    )
                ].sort_index()
            table = pa.Table.from_pandas(merged.reset_index(), preserve_index=False)
            stamp_index = table.schema.get_field_index("DateTime")
            table = table.set_column(
                stamp_index,
                "DateTime",
                table.column("DateTime").cast(pa.timestamp("ms", tz="UTC")),
            )
            self.market.publish_source(
                request.dataset_id,
                period,
                table,
                expected_revision=prior["revision"] if prior else 0,
            )
            progress["published_partitions"] += 1
        progress["rows"] = len(data)
        logger.info(
            "Yahoo published: id=%s rows=%d partitions=%d",
            request.dataset_id,
            len(data),
            progress["published_partitions"],
        )

    async def invoke(self, operation: str, payload: JsonValue) -> JsonValue:
        """Validate and dispatch only declared source operations."""
        logger.info("Yahoo operation: %s", operation)
        values = payload if isinstance(payload, dict) else {}
        if operation == "catalog":
            ready = self.market.source_available()
            return cast(
                "JsonValue",
                {
                    "source": "yahoo",
                    "available": ready,
                    "definitions_available": ready,
                    "datasets": list(self.market.source_definitions()) if ready else [],
                    "schema": YahooDefinition.model_json_schema(),
                    "reason": ""
                    if ready
                    else "Script-backed catalog migration is required",
                },
            )
        if operation == "add":
            definition = YahooDefinition.model_validate(values)
            metadata = await self.session.metadata(definition.symbol.upper())
            dataset_id = self.market.register_source(
                source="Yahoo",
                symbol=definition.symbol.upper() + definition.postfix,
                underlying=definition.symbol.upper(),
                instrument=definition.symbol.upper(),
                timeframe=definition.timeframe,
                options={
                    "parameters": definition.model_dump(mode="json"),
                    "metadata": metadata,
                },
            )
            return {"id": dataset_id}
        if operation == "download.start":
            request = YahooDownload.model_validate(values)
            self.market.source_definition(request.dataset_id)
            progress: dict[str, Any] = {
                "completed_chunks": 0,
                "total_chunks": 0,
                "published_partitions": 0,
                "rows": 0,
            }

            async def run() -> None:
                await self.acquire(request, progress)

            job = self.jobs.submit(Budget(1, 256 * 1024 * 1024, 3600), run)
            self.progress[job.id] = progress
            return {"job_id": job.id, "state": job.state}
        if operation in ("download.status", "download.cancel"):
            job_id = str(values.get("job_id", ""))
            if operation == "download.cancel":
                self.jobs.cancel(job_id)
            job = self.jobs.status(job_id)
            return cast(
                "JsonValue",
                {"job_id": job.id, "state": job.state, **self.progress[job.id]},
            )
        raise ValueError("Unknown Yahoo operation")

    async def close(self) -> None:
        """Cancel owned jobs before releasing the source's network session."""
        await self.jobs.close()
        await self.session.network.close()
        logger.info("Yahoo source closed")


async def prepare(context: HostCapabilities) -> PreparedContribution:
    """Bind the script-derived implementation to explicit host capabilities."""
    if context.market_data is None or context.jobs is None or context.network is None:
        raise ValueError("Yahoo requires market data, jobs and network capabilities")
    session = YahooSession(
        context.network.source_session(
            (PRIMARY_BASE_URL, FALLBACK_BASE_URL, "https://fc.yahoo.com")
        )
    )
    runtime = YahooRuntime(context.market_data, context.jobs, session)
    return PreparedContribution(
        ("catalog", "add", "download.start", "download.status", "download.cancel"),
        runtime.invoke,
        runtime.close,
    )


# The following pure routines are copied from the fingerprinted owner script.

TIMEFRAME_MAP: dict[str, str] = {
    # Daily
    "D1": "1d",
    "1D": "1d",
    "1d": "1d",
    "d1": "1d",
    "DAILY": "1d",
    "DAY": "1d",
    # Weekly
    "W1": "1wk",
    "1W": "1wk",
    "1WK": "1wk",
    "1wk": "1wk",
    "w1": "1wk",
    "WEEKLY": "1wk",
    # Monthly
    "MN1": "1mo",
    "1MO": "1mo",
    "1mo": "1mo",
    "mn1": "1mo",
    "MONTHLY": "1mo",
    # Intraday 1-Minute
    "M1": "1m",
    "1M": "1m",
    "1m": "1m",
    "m1": "1m",
    # Intraday 2-Minute
    "M2": "2m",
    "2M": "2m",
    "2m": "2m",
    "m2": "2m",
    # Intraday 5-Minute
    "M5": "5m",
    "5M": "5m",
    "5m": "5m",
    "m5": "5m",
    # Intraday 15-Minute
    "M15": "15m",
    "15M": "15m",
    "15m": "15m",
    "m15": "15m",
    # Intraday 30-Minute
    "M30": "30m",
    "30M": "30m",
    "30m": "30m",
    "m30": "30m",
    # Intraday 60-Minute / 1-Hour
    "H1": "1h",
    "1H": "1h",
    "60M": "1h",
    "60m": "1h",
    "1h": "1h",
    "h1": "1h",
    # Intraday 90-Minute
    "M90": "90m",
    "90M": "90m",
    "90m": "90m",
}

YAHOO_INTERVAL_WINDOW_DAYS: dict[str, int] = {
    "1m": 7,  # Yahoo limits 1m to 7-8 days per request (available for past 30 days)
    "2m": 50,  # 2m-30m up to 60 days total
    "5m": 50,
    "15m": 50,
    "30m": 50,
    "90m": 50,
    "1h": 365,  # 1h up to 730 days total
    "1d": 3650,  # Multi-year spans supported natively
    "1wk": 7300,
    "1mo": 18250,
}


def parse_date_param(
    val: str | datetime.datetime | datetime.date,
    end_of_day: bool = False,
) -> datetime.datetime:
    """Parses date string or datetime into UTC datetime."""
    if isinstance(val, datetime.datetime):
        if val.tzinfo is None:
            return val.replace(tzinfo=datetime.UTC)
        return val.astimezone(datetime.UTC)
    if isinstance(val, datetime.date):
        if end_of_day:
            return datetime.datetime(
                val.year,
                val.month,
                val.day,
                23,
                59,
                59,
                999999,
                tzinfo=datetime.UTC,
            )
        return datetime.datetime(
            val.year, val.month, val.day, 0, 0, 0, tzinfo=datetime.UTC
        )
    if isinstance(val, str):
        v = val.strip()
        for fmt in (
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d %H:%M",
            "%Y-%m-%d",
            "%Y/%m/%d",
            "%Y%m%d",
            "%Y.%m.%d",
        ):
            try:
                dt = datetime.datetime.strptime(v, fmt).replace(tzinfo=datetime.UTC)
                if end_of_day and fmt in ("%Y-%m-%d", "%Y/%m/%d", "%Y%m%d", "%Y.%m.%d"):
                    dt = dt.replace(hour=23, minute=59, second=59, microsecond=999999)
                return dt.replace(tzinfo=datetime.UTC)
            except ValueError:
                continue
        ts = pd.to_datetime(v, utc=True)
        return cast("datetime.datetime", ts.to_pydatetime())

    raise ValueError(f"Unsupported date format: {val}")


def normalize_timeframe(timeframe: str) -> tuple[str, str | None]:
    """
    Normalizes timeframe string into (native_yahoo_interval, resample_rule_if_needed).

    Examples:
        'D1'  -> ('1d', None)
        'H1'  -> ('1h', None)
        'H4'  -> ('1h', '4h')
        'M5'  -> ('5m', None)
        'M10' -> ('5m', '10min')
    """
    tf = timeframe.strip().upper()

    if tf in TIMEFRAME_MAP:
        return TIMEFRAME_MAP[tf], None

    lower_tf = timeframe.strip().lower()
    if lower_tf in YAHOO_INTERVAL_WINDOW_DAYS:
        return lower_tf, None

    if tf.startswith("H") and tf[1:].isdigit():
        hours = int(tf[1:])
        return "1h", f"{hours}h"

    if tf.startswith("M") and tf[1:].isdigit():
        mins = int(tf[1:])
        if mins in (1, 2, 5, 15, 30, 90):
            return f"{mins}m", None
        base_int = "5m" if mins % 5 == 0 else "1m"
        return base_int, f"{mins}min"

    raise ValueError(
        f"Unsupported timeframe '{timeframe}'. Use a standard interval "
        "or native Yahoo intervals (1d, 1wk, 1mo, 1h, 15m, 5m, 1m)."
    )


def _generate_date_chunks(
    start_dt: datetime.datetime,
    end_dt: datetime.datetime,
    interval: str,
) -> list[tuple[datetime.datetime, datetime.datetime]]:
    """Slices a date range into Yahoo-compliant maximum window chunks."""
    window_days = YAHOO_INTERVAL_WINDOW_DAYS.get(interval, 3650)
    chunks: list[tuple[datetime.datetime, datetime.datetime]] = []

    curr_start = start_dt
    while curr_start <= end_dt:
        curr_end = min(
            curr_start + datetime.timedelta(days=window_days),
            end_dt,
        )
        chunks.append((curr_start, curr_end))
        curr_start = curr_end + datetime.timedelta(seconds=1)

    return chunks


def parse_chart(
    data: dict[str, Any], symbol: str, include_adj_close: bool = True
) -> pd.DataFrame:
    """Decode chart fields using the owner script's null and adjusted-close policies."""
    result = data.get("chart", {}).get("result")
    if not result:
        err = data.get("chart", {}).get("error", {})
        desc = err.get("description", "Unknown error")
        raise ValueError(f"Symbol '{symbol}' not found or no data returned: {desc}")

    chart_node = result[0]
    timestamps = chart_node.get("timestamp", [])
    if not timestamps:
        return pd.DataFrame()

    indicators = chart_node.get("indicators", {})
    quote_list = indicators.get("quote", [{}])
    quote_data = quote_list[0] if quote_list else {}

    opens = quote_data.get("open", [])
    highs = quote_data.get("high", [])
    lows = quote_data.get("low", [])
    closes = quote_data.get("close", [])
    volumes = quote_data.get("volume", [])

    adj_closes: list[float | None] = []
    if include_adj_close:
        adj_list = indicators.get("adjclose", [{}])
        if adj_list and "adjclose" in adj_list[0]:
            adj_closes = adj_list[0]["adjclose"]

    records: list[dict[str, Any]] = []
    for i, ts in enumerate(timestamps):
        c = closes[i] if i < len(closes) else None
        o = opens[i] if i < len(opens) else None
        h = highs[i] if i < len(highs) else None
        l_val = lows[i] if i < len(lows) else None
        v = volumes[i] if i < len(volumes) else 0

        if c is None or o is None or h is None or l_val is None:
            continue

        rec: dict[str, Any] = {
            "DateTime": datetime.datetime.fromtimestamp(ts, tz=datetime.UTC),
            "Open": float(o),
            "High": float(h),
            "Low": float(l_val),
            "Close": float(c),
            "Volume": float(v) if v is not None else 0.0,
        }
        if include_adj_close:
            adj = adj_closes[i] if i < len(adj_closes) else c
            rec["Adj Close"] = float(adj) if adj is not None else float(c)

        records.append(rec)

    if not records:
        return pd.DataFrame()

    return pd.DataFrame(records).set_index("DateTime")


def resample_to_timeframe(df: pd.DataFrame, timeframe_rule: str) -> pd.DataFrame:
    """
    Resamples OHLCV DataFrame to higher timeframe using standard quantitative rules.

    Aggregation:
        Open: first, High: max, Low: min, Close: last, Volume: sum, Adj Close: last
    """
    if df.empty:
        return df

    tf = timeframe_rule.strip()
    rule_map = {
        "M1": "1min",
        "M2": "2min",
        "M3": "3min",
        "M5": "5min",
        "M10": "10min",
        "M15": "15min",
        "M30": "30min",
        "H1": "1h",
        "H2": "2h",
        "H3": "3h",
        "H4": "4h",
        "H6": "6h",
        "H8": "8h",
        "H12": "12h",
        "D1": "1D",
        "W1": "1W",
        "MN1": "1ME",
    }
    rule = rule_map.get(tf.upper(), tf)

    agg_dict: dict[str, str] = {
        "Open": "first",
        "High": "max",
        "Low": "min",
        "Close": "last",
        "Volume": "sum",
    }
    if "Adj Close" in df.columns:
        agg_dict["Adj Close"] = "last"

    resampled = (
        df.resample(rule, label="left", closed="left")
        .agg(agg_dict)
        .dropna(subset=["Close"])
    )

    logger.debug(
        "Resampled %d base bars to %d bars using rule %s", len(df), len(resampled), rule
    )
    return resampled
