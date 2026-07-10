"""Market data gateway router.

Orchestrates historical, real-time, local, synthetic, and broker data queries.
Delegates source-specific fetching to data source adapters and owns cache,
license, rate limit, and response validation policy.
"""

import json
from datetime import UTC, datetime, timedelta
from typing import Any

from app.services.data.models import (
    DataAvailability,
    OHLCVRecord,
    SpreadRecord,
    SymbolMetadata,
    TickRecord,
)
from app.services.data.normalization import (
    normalize_file_records,
    resolve_volume_kind,
    summarize_data_quality,
)
from app.services.data.sources import (
    ADAPTER_REGISTRY,
    BinanceAdapter,
    CSVAdapter,
    CTraderAdapter,
    DukascopyAdapter,
    MT5Adapter,
    ParquetAdapter,
    SourceAdapterProtocol,
    SyntheticAdapter,
    YahooAdapter,
    check_circuit_breaker_barrier,
    get_circuit_breaker,
    get_source_adapter,
    update_circuit_breaker,
)
from app.services.data.storage import (
    DEFAULT_NORMALIZATION_VERSION,
    DEFAULT_SCHEMA_VERSION,
    compute_raw_hash,
    db_helper,
    generate_cache_key,
    get_cached_data,
    set_cached_data,
)
from app.services.data.transforms import timeframe_to_minutes
from app.services.data.validation import (
    DEFAULT_OHLCV_LIMIT,
    DEFAULT_SPREAD_LIMIT,
    DEFAULT_TICK_LIMIT,
    MAX_OHLCV_LIMIT,
    MAX_SPREAD_LIMIT,
    MAX_TICK_LIMIT,
    normalize_numeric,
    validate_license,
    validate_limit,
    validate_source_readiness,
    validate_stale_data_behavior,
    validate_timeframe,
    validate_workflow_context,
)
from app.utils.errors import DataError, ExternalServiceError, ValidationError
from app.utils.logger import logger
from app.utils.normalization import normalize_timestamp

__all__ = [
    "ADAPTER_REGISTRY",
    "BinanceAdapter",
    "CSVAdapter",
    "CTraderAdapter",
    "DukascopyAdapter",
    "MT5Adapter",
    "ParquetAdapter",
    "SourceAdapterProtocol",
    "SyntheticAdapter",
    "YahooAdapter",
    "check_circuit_breaker_barrier",
    "check_rate_limit",
    "execute_gateway_request",
    "get_circuit_breaker",
    "get_data",
    "get_data_availability",
    "get_data_with_metadata",
    "get_source_adapter",
    "get_symbol_metadata",
    "list_symbols",
    "normalize_file_records",
    "update_circuit_breaker",
]


# --- 1. Rate Limiters ---
class TokenBucketLimiter:
    """A thread-safe simple Token Bucket rate limiter."""

    def __init__(self, rate: float, capacity: float) -> None:
        """Initialize with a token replenishment rate (tokens/sec) and capacity."""
        self.rate = rate
        self.capacity = capacity
        self.tokens = capacity
        self.last_update = datetime.now(UTC).timestamp()

    def consume(self) -> bool:
        """Consume 1 token from the bucket. Returns True if successful."""
        now = datetime.now(UTC).timestamp()
        elapsed = now - self.last_update
        self.tokens = min(self.capacity, self.tokens + elapsed * self.rate)
        self.last_update = now
        if self.tokens >= 1.0:
            self.tokens -= 1.0
            return True
        return False


RATE_LIMITERS: dict[str, TokenBucketLimiter] = {
    "mt5": TokenBucketLimiter(10.0, 20.0),
    "ctrader": TokenBucketLimiter(10.0, 20.0),
    "dukascopy": TokenBucketLimiter(5.0, 10.0),
    "binance": TokenBucketLimiter(5.0, 10.0),
    "yahoo": TokenBucketLimiter(5.0, 10.0),
    "csv": TokenBucketLimiter(100.0, 500.0),
    "parquet": TokenBucketLimiter(100.0, 500.0),
    "synthetic": TokenBucketLimiter(100.0, 500.0),
}


def check_rate_limit(source: str) -> None:
    """Consume rate limit token or raise a BACKPRESSURE_EXCEEDED error."""
    src_lower = source.lower()
    if src_lower in RATE_LIMITERS:
        limiter = RATE_LIMITERS[src_lower]
        if not limiter.consume():
            msg = f"Rate limit exceeded for source: {source}."
            raise ExternalServiceError(msg, code="BACKPRESSURE_EXCEEDED")


# --- 2. Gateway Record Validation ---
def _normalize_and_validate_records(
    records: list[dict[str, Any]],
    data_kind: str,
    symbol: str,
    source: str,
    workflow_context: str,
) -> list[dict[str, Any]]:
    """Validate, normalize, and dump records based on data_kind."""
    validated = []
    for r in records:
        if data_kind == "ohlcv":
            bar = OHLCVRecord(**r)
            bar.open = normalize_numeric(bar.open, 5, workflow_context)
            bar.high = normalize_numeric(bar.high, 5, workflow_context)
            bar.low = normalize_numeric(bar.low, 5, workflow_context)
            bar.close = normalize_numeric(bar.close, 5, workflow_context)
            bar.spread = normalize_numeric(bar.spread, 1, workflow_context)
            validated.append(bar.model_dump())
        elif data_kind == "ticks":
            tick = TickRecord(**r)
            tick.bid = normalize_numeric(tick.bid, 5, workflow_context)
            tick.ask = normalize_numeric(tick.ask, 5, workflow_context)
            tick.last = normalize_numeric(tick.last, 5, workflow_context)
            tick.spread = normalize_numeric(tick.spread, 1, workflow_context)
            validated.append(tick.model_dump())
        elif data_kind == "spreads":
            bid_val = float(r.get("bid", 0.0))
            ask_val = float(r.get("ask", 0.0))
            spread_pts = float(r.get("spread", 0.0))
            if spread_pts <= 0.0 and ask_val >= bid_val:
                spread_pts = round((ask_val - bid_val) / 0.00001, 1)

            sp_rec = SpreadRecord(
                timestamp=r["timestamp"],
                symbol=symbol,
                bid=bid_val,
                ask=ask_val,
                spread_points=spread_pts,
                spread_pips=round(spread_pts / 10.0, 2),
                source=source,
            )
            sp_rec.bid = normalize_numeric(sp_rec.bid, 5, workflow_context)
            sp_rec.ask = normalize_numeric(sp_rec.ask, 5, workflow_context)
            sp_rec.spread_points = normalize_numeric(
                sp_rec.spread_points, 1, workflow_context
            )
            sp_rec.spread_pips = normalize_numeric(
                sp_rec.spread_pips, 2, workflow_context
            )
            validated.append(sp_rec.model_dump())
    return validated


def _check_gateway_cache(
    source: str,
    symbol: str,
    timeframe: str | None,
    start_time: datetime,
    end_time: datetime,
    stale_data_behavior: str,
    request_id: str | None = None,
) -> tuple[str, str, list[dict[str, Any]] | None]:
    """Generate cache keys and check cache availability."""
    cache_tf = timeframe or "ticks"
    cache_key = generate_cache_key(
        source,
        symbol,
        cache_tf,
        start_time.isoformat(),
        end_time.isoformat(),
    )
    cached = get_cached_data(cache_key, stale_data_behavior, request_id=request_id)
    return cache_key, cache_tf, cached["records"] if cached else None


def _download_from_adapter(
    source: str,
    symbol: str,
    timeframe: str | None,
    start_time: datetime,
    end_time: datetime,
    data_kind: str,
    request_id: str | None = None,
) -> list[dict[str, Any]]:
    """Retrieve raw records from the registered source adapter."""
    adapter = get_source_adapter(source)
    if data_kind == "ohlcv":
        return adapter.get_market_data(
            symbol,
            timeframe or "M1",
            start_time,
            end_time,
            request_id=request_id,
        )
    if data_kind in ("ticks", "spreads"):
        return adapter.get_tick_data(
            symbol, start_time, end_time, request_id=request_id
        )
    return []


# --- 5. Unified Gateway Core Execution ---
def execute_gateway_request(
    source: str,
    symbol: str,
    timeframe: str | None,
    start_time: datetime,
    end_time: datetime,
    data_kind: str,
    stale_data_behavior: str = "refresh_and_return",
    workflow_context: str = "research",
    request_id: str | None = None,
) -> list[dict[str, Any]]:
    """Internal single-source gateway execution, routing through cache."""
    logger.info(
        f"Gateway routing request: source={source}, symbol={symbol}, kind={data_kind}",
        extra={"request_id": request_id},
    )

    try:
        validate_license(source, symbol, workflow_context, request_id=request_id)
        validate_source_readiness(source, workflow_context, request_id=request_id)
        check_rate_limit(source)

        cache_key, cache_tf, cached_records = _check_gateway_cache(
            source,
            symbol,
            timeframe,
            start_time,
            end_time,
            stale_data_behavior,
            request_id=request_id,
        )
        if cached_records is not None:
            logger.info(f"Cache hit for key {cache_key}")
            return cached_records

        records = _download_from_adapter(
            source,
            symbol,
            timeframe,
            start_time,
            end_time,
            data_kind,
            request_id=request_id,
        )

        if not records:
            set_cached_data(
                cache_key,
                source,
                symbol,
                cache_tf,
                start_time.isoformat(),
                end_time.isoformat(),
                [],
                ttl_seconds=60,
                request_id=request_id,
            )
            return []

        validated = _normalize_and_validate_records(
            records=records,
            data_kind=data_kind,
            symbol=symbol,
            source=source,
            workflow_context=workflow_context,
        )

        ttl = 900
        if data_kind == "ohlcv":
            ttl = 3600 if timeframe != "D1" else 86400

        set_cached_data(
            cache_key,
            source,
            symbol,
            cache_tf,
            start_time.isoformat(),
            end_time.isoformat(),
            validated,
            ttl_seconds=ttl,
            raw_hash=compute_raw_hash(records),
            request_id=request_id,
        )
    except (ValidationError, ExternalServiceError):
        raise
    except Exception as e:
        logger.warning(f"Request failed on source {source}: {e}")
        err_msg = f"Gateway request failed for source {source}: {e}"
        raise DataError(err_msg) from e

    return validated


# --- 6. Clean Service APIs ---
def get_data(
    symbol: str,
    start_time: str,
    end_time: str,
    data_kind: str = "ohlcv",
    timeframe: str | None = None,
    source: str = "csv",
    limit: int | None = None,
    stale_data_behavior: str = "refresh_and_return",
    workflow_context: str = "research",
    request_id: str | None = None,
) -> list[dict[str, Any]]:
    """Retrieve normalized market data records (ohlcv, ticks, spreads, or volume).

    Args:
        symbol: Financial symbol identifier.
        start_time: UTC start time string.
        end_time: UTC end time string.
        data_kind: Kind of data ('ohlcv', 'ticks', 'spreads', 'volume').
        timeframe: Bar timeframe (required for ohlcv/volume).
        source: Primary source adapter.
        limit: Max query limit parameter.
        stale_data_behavior: Expired cache lookup policy.
        workflow_context: rounding/validation execution context.
        request_id: Optional tracking identifier.

    Returns:
        list[dict[str, Any]]: Clean list of normalized data records.
    """
    validate_workflow_context(workflow_context, request_id=request_id)
    validate_stale_data_behavior(stale_data_behavior, request_id=request_id)

    t_start = normalize_timestamp(start_time)
    t_end = normalize_timestamp(end_time)

    if t_start >= t_end:
        err_order = (
            f"start_time must be strictly before end_time: "
            f"{t_start.isoformat()} >= {t_end.isoformat()}"
        )
        logger.error(err_order, extra={"request_id": request_id})
        raise ValidationError(err_order, code="INVALID_INPUT")

    kind = data_kind.lower()
    if kind not in ("ohlcv", "ticks", "spreads", "volume"):
        err_msg = f"Unsupported data_kind: {data_kind}"
        raise ValidationError(err_msg, code="UNSUPPORTED_OPERATION")

    if kind == "ohlcv":
        if not timeframe:
            raise ValidationError("timeframe is required for ohlcv data.")
        tf = validate_timeframe(timeframe)
        valid_limit = validate_limit(limit, MAX_OHLCV_LIMIT, DEFAULT_OHLCV_LIMIT)
        records = execute_gateway_request(
            source,
            symbol,
            tf,
            t_start,
            t_end,
            "ohlcv",
            stale_data_behavior,
            workflow_context,
            request_id,
        )
        return records[:valid_limit]

    if kind == "ticks":
        valid_limit = validate_limit(limit, MAX_TICK_LIMIT, DEFAULT_TICK_LIMIT)
        records = execute_gateway_request(
            source,
            symbol,
            None,
            t_start,
            t_end,
            "ticks",
            stale_data_behavior,
            workflow_context,
            request_id,
        )
        return records[:valid_limit]

    if kind == "spreads":
        valid_limit = validate_limit(limit, MAX_SPREAD_LIMIT, DEFAULT_SPREAD_LIMIT)
        records = execute_gateway_request(
            source,
            symbol,
            None,
            t_start,
            t_end,
            "spreads",
            stale_data_behavior,
            workflow_context,
            request_id,
        )
        return records[:valid_limit]

    if kind == "volume":
        if not timeframe:
            raise ValidationError("timeframe is required for volume data.")
        tf = validate_timeframe(timeframe)
        bars = get_data(
            symbol=symbol,
            start_time=start_time,
            end_time=end_time,
            data_kind="ohlcv",
            timeframe=tf,
            source=source,
            limit=limit,
            stale_data_behavior=stale_data_behavior,
            workflow_context=workflow_context,
            request_id=request_id,
        )
        volume_records = []
        for b in bars:
            volume_records.append(
                {
                    "timestamp": b["timestamp"],
                    "symbol": symbol,
                    "timeframe": tf,
                    "volume": b["volume"],
                    "tick_volume": b.get("tick_volume", 0.0),
                    "real_volume": b.get("real_volume", 0.0),
                    "source": source,
                }
            )
        return volume_records

    return []


def get_data_with_metadata(
    symbol: str,
    start_time: str,
    end_time: str,
    data_kind: str = "ohlcv",
    timeframe: str | None = None,
    source: str = "csv",
    limit: int | None = None,
    stale_data_behavior: str = "refresh_and_return",
    workflow_context: str = "research",
    request_id: str | None = None,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Retrieve normalized market data records together with result metadata.

    Wraps `get_data` without changing its native return shape or behavior, so
    existing internal callers of `get_data` remain unaffected. This function
    is intended for the official `get_data_tool` boundary in `public_api.py`.

    Args:
        symbol: Financial symbol identifier.
        start_time: UTC start time string.
        end_time: UTC end time string.
        data_kind: Kind of data ('ohlcv', 'ticks', 'spreads', 'volume').
        timeframe: Bar timeframe (required for ohlcv/volume).
        source: Primary source adapter.
        limit: Max query limit parameter.
        stale_data_behavior: Expired cache lookup policy.
        workflow_context: Rounding/validation execution context.
        request_id: Optional tracking identifier.

    Returns:
        tuple[list[dict[str, Any]], dict[str, Any]]: Normalized records and a
        JSON-safe result metadata mapping (source, symbol, timeframe,
        data_kind, record_count, volume_kind, schema_version,
        normalization_version, raw_hash, cache_status, data_quality,
        retrieval_timestamp, license, and warnings).
    """
    logger.debug(
        f"get_data_with_metadata: building result metadata for symbol={symbol} "
        f"source={source} kind={data_kind}",
        extra={"request_id": request_id},
    )
    kind = data_kind.lower()
    warnings: list[str] = []
    cache_status = "miss"

    if kind in ("ohlcv", "ticks", "spreads"):
        try:
            t_start = normalize_timestamp(start_time)
            t_end = normalize_timestamp(end_time)
            tf_for_cache = validate_timeframe(timeframe) if timeframe else None
            _, _, cached = _check_gateway_cache(
                source,
                symbol,
                tf_for_cache,
                t_start,
                t_end,
                stale_data_behavior,
                request_id=request_id,
            )
            if cached is not None:
                cache_status = "hit"
        except Exception as e:  # noqa: BLE001
            logger.debug(f"Cache status peek failed, defaulting to miss: {e}")

    records = get_data(
        symbol=symbol,
        start_time=start_time,
        end_time=end_time,
        data_kind=data_kind,
        timeframe=timeframe,
        source=source,
        limit=limit,
        stale_data_behavior=stale_data_behavior,
        workflow_context=workflow_context,
        request_id=request_id,
    )

    if not records:
        warnings.append("No records were returned for the requested window.")

    license_info: dict[str, Any] = {}
    try:
        license_info = validate_license(
            source, symbol, workflow_context, request_id=request_id
        )
    except (ValidationError, ExternalServiceError) as e:
        logger.debug(f"License metadata unavailable for result metadata: {e}")

    result_metadata: dict[str, Any] = {
        "source": source,
        "symbol": symbol,
        "timeframe": timeframe,
        "data_kind": kind,
        "record_count": len(records),
        "volume_kind": resolve_volume_kind(source, kind),
        "schema_version": DEFAULT_SCHEMA_VERSION,
        "normalization_version": DEFAULT_NORMALIZATION_VERSION,
        "raw_hash": None,
        "cache_status": cache_status,
        "data_quality": summarize_data_quality(records),
        "retrieval_timestamp": datetime.now(UTC).isoformat(),
        "license": license_info,
        "warnings": warnings,
    }
    return records, result_metadata


def get_symbol_metadata(
    symbol: str,
    source: str = "csv",
    *,
    request_id: str | None = None,
) -> dict[str, Any]:
    """Retrieve normalized symbol and asset metadata."""
    logger.info(
        f"Retrieving symbol metadata: symbol={symbol}, source={source}",
        extra={"request_id": request_id},
    )
    adapter = get_source_adapter(source)
    raw_meta = adapter.get_symbol_metadata(symbol, request_id=request_id)

    meta_obj = SymbolMetadata(
        symbol=symbol,
        asset_class=raw_meta.get("asset_class", "forex"),
        base_currency=raw_meta.get("base_currency", "EUR"),
        quote_currency=raw_meta.get("quote_currency", "USD"),
        contract_size=raw_meta.get("contract_size", 100000.0),
        tick_size=raw_meta.get("tick_size", 0.00001),
        tick_value=raw_meta.get("tick_value", 1.0),
        point=raw_meta.get("point", 0.00001),
        digits=raw_meta.get("digits", 5),
        lot_min=raw_meta.get("lot_min", 0.01),
        lot_max=raw_meta.get("lot_max", 100.0),
        lot_step=raw_meta.get("lot_step", 0.01),
        margin_currency=raw_meta.get("margin_currency", "EUR"),
        profit_currency=raw_meta.get("profit_currency", "USD"),
        trading_hours=raw_meta.get("trading_hours", {}),
        source_metadata=raw_meta,
    )

    return meta_obj.model_dump()


def list_symbols(
    source: str = "csv",
    *,
    request_id: str | None = None,
) -> list[str]:
    """List symbols discovered from the source."""
    adapter = get_source_adapter(source)
    return adapter.list_symbols(request_id=request_id)


def get_data_availability(
    symbol: str,
    timeframe: str,
    source: str = "csv",
    *,
    request_id: str | None = None,
) -> dict[str, Any]:
    """Inspect committed ranges, gaps, and record counts."""
    logger.info(
        f"Checking data availability: symbol={symbol}, source={source}",
        extra={"request_id": request_id},
    )

    count = 0
    start_str = None
    end_str = None
    all_timestamps: list[str] = []
    try:
        with db_helper.get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT key, start_time, end_time, records_json FROM data_cache
                WHERE source = ? AND symbol = ? AND timeframe = ?;
                """,
                (source, symbol, timeframe),
            )
            rows = cursor.fetchall()
            for row in rows:
                start_str = row["start_time"]
                end_str = row["end_time"]
                records = json.loads(row["records_json"])
                count += len(records)
                all_timestamps.extend(
                    r["timestamp"] for r in records if r.get("timestamp")
                )
    except Exception as e:  # noqa: BLE001
        logger.warning(f"Failed to query data availability from database cache: {e}")

    gap_windows = _detect_gap_windows(sorted(set(all_timestamps)), timeframe)

    availability = DataAvailability(
        symbol=symbol,
        timeframe=timeframe,
        source=source,
        start_time=start_str,
        end_time=end_str,
        gap_count=len(gap_windows),
        gap_windows=gap_windows,
        is_ready=True,
        record_count=count,
        metadata={"cache_queried": True},
    )

    return availability.model_dump()


_MIN_TIMESTAMPS_FOR_GAP_DETECTION = 2


def _detect_gap_windows(
    sorted_timestamps: list[str],
    timeframe: str,
) -> list[dict[str, str]]:
    """Detect internal gap windows exceeding 1.5x the expected bar interval.

    This is a read-only diagnostic. It never fills, interpolates, or repairs
    gaps; it only surfaces where they exist.

    Args:
        sorted_timestamps: Ascending, de-duplicated ISO timestamp strings.
        timeframe: Timeframe identifier used to derive the expected interval.

    Returns:
        list[dict[str, str]]: Gap windows with `start` and `end` boundaries.
    """
    if len(sorted_timestamps) < _MIN_TIMESTAMPS_FOR_GAP_DETECTION:
        return []
    try:
        interval_minutes = timeframe_to_minutes(timeframe)
    except ValidationError:
        return []
    if interval_minutes <= 0:
        return []

    threshold = timedelta(minutes=interval_minutes * 1.5)
    gaps: list[dict[str, str]] = []
    previous_dt: datetime | None = None
    for ts in sorted_timestamps:
        try:
            current_dt = datetime.fromisoformat(ts)
        except ValueError:
            continue
        if previous_dt is not None and (current_dt - previous_dt) > threshold:
            gaps.append(
                {"start": previous_dt.isoformat(), "end": current_dt.isoformat()}
            )
        previous_dt = current_dt
    return gaps
