"""DATA-specific construction and consumption of canonical standard responses.

This focused module owns only Data's use of the Utils-owned
``StandardResponse[T]`` envelope. It contains:

- Static per-operation capability traits (risk and side-effect declarations).
- Monotonic timing capture (``data_start_time``).
- One Data response factory (``build_data_response``).
- A typed boundary runner (``run_data_operation``) for the common
  success/``DataError``/unexpected-exception pattern that keeps public
  signatures, request identity, and error types fully explicit.
- Safe preservation of legacy ``DataError`` evidence.
- A nested-response consumption helper for public-to-public Data calls.

It does not duplicate any Utils-owned contract and contains no feature
algorithm.
"""

from __future__ import annotations

import asyncio
import time
from collections.abc import Awaitable, Callable, Mapping
from dataclasses import dataclass
from typing import Any

from app.services.data.contracts.errors import DATA_ERROR_MANIFEST, DataError
from app.utils import (
    JsonValue,
    ResponseMetadata,
    RiskLevel,
    StandardResponse,
    error_response,
    exception_response,
    generate_id,
    logger,
    success_response,
    validate_id,
)

# Utils re-raises these from ``exception_response``; mirrored here only so the
# boundary runners can document the propagation contract without importing the
# private Utils sentinel module.
_PROPAGATED_EXCEPTIONS = (
    asyncio.CancelledError,
    GeneratorExit,
    KeyboardInterrupt,
    SystemExit,
)


@dataclass(frozen=True, slots=True)
class OperationTraits:
    """Static capability declaration for one DATA public operation.

    Describes what an operation CAN do, independent of one invocation. All Data
    operations carry ``places_trade=False``; Data owns no trade authority.

    Attributes:
        risk_level: Static invocation-risk classification.
        read_only: Whether the operation has no externally observable mutation.
        writes_file: Whether the operation can write a file.
        modifies_database: Whether the operation can modify a database.
        requires_network: Whether the operation can require network access.
    """

    risk_level: RiskLevel
    read_only: bool
    writes_file: bool
    modifies_database: bool
    requires_network: bool


def _traits(
    risk_level: RiskLevel,
    *,
    read_only: bool,
    writes_file: bool = False,
    modifies_database: bool = False,
    requires_network: bool = False,
) -> OperationTraits:
    """Build one immutable static capability declaration."""
    return OperationTraits(
        risk_level=risk_level,
        read_only=read_only,
        writes_file=writes_file,
        modifies_database=modifies_database,
        requires_network=requires_network,
    )


# ---------------------------------------------------------------------------
# Static per-operation capability registry.
#
# Every qualifying DATA public operation appears exactly once. The qualified
# name (``data.<feature>.<operation>``) is the ``ResponseMetadata.name`` and the
# registry key. Trait classification follows the migration metadata policy:
#
#   * Pure operations ............... risk=none, read_only=True, no side effects.
#   * Local/file/database reads ..... risk=low,  read_only=True, no side effects.
#                                    (Reading is never writes_file/modifies_database.)
#   * Provider/network reads ........ risk=low,  read_only=True, requires_network=True.
#   * In-memory state mutation ...... risk=low/medium, read_only=False.
#   * File writes ................... risk=medium, read_only=False, writes_file=True.
#   * Database writes ............... risk=medium, modifies_database=True.
#   * Destructive/schema-sensitive .. risk=high, read_only=False (+ side effects).
#
# ``places_trade`` is always False for Data and is enforced by
# ``build_data_response``.
# ---------------------------------------------------------------------------
_TRAITS: Mapping[str, OperationTraits] = {
    # FEAT-DATA-02 - Market Data Retrieval (provider/network reads).
    "data.market_data.fetch_market_dataset": _traits(
        RiskLevel.LOW, read_only=True, requires_network=True
    ),
    "data.market_data.get_market_data": _traits(
        RiskLevel.LOW, read_only=True, requires_network=True
    ),
    "data.market_data.get_tick_data": _traits(
        RiskLevel.LOW, read_only=True, requires_network=True
    ),
    "data.market_data.get_spread_data": _traits(
        RiskLevel.LOW, read_only=True, requires_network=True
    ),
    "data.market_data.discover_symbols": _traits(
        RiskLevel.LOW, read_only=True, requires_network=True
    ),
    "data.market_data.fetch_symbol_metadata": _traits(
        RiskLevel.LOW, read_only=True, requires_network=True
    ),
    "data.market_data.inspect_availability": _traits(
        RiskLevel.LOW, read_only=True, requires_network=True
    ),
    "data.market_data.fetch_historical_volume": _traits(
        RiskLevel.LOW, read_only=True, requires_network=True
    ),
    "data.market_data.get_symbol_metadata": _traits(
        RiskLevel.LOW, read_only=True, requires_network=True
    ),
    "data.market_data.list_symbols": _traits(
        RiskLevel.LOW, read_only=True, requires_network=True
    ),
    "data.market_data.get_data_availability": _traits(
        RiskLevel.LOW, read_only=True, requires_network=True
    ),
    "data.market_data.get_historical_volume": _traits(
        RiskLevel.LOW, read_only=True, requires_network=True
    ),
    # FEAT-DATA-03 - Local Dataset Loading (local file reads).
    "data.local_datasets.load_csv": _traits(RiskLevel.LOW, read_only=True),
    "data.local_datasets.load_parquet": _traits(RiskLevel.LOW, read_only=True),
    "data.local_datasets.load_local_dataset": _traits(RiskLevel.LOW, read_only=True),
    # FEAT-DATA-04 - Synthetic Data Generation (pure, no I/O).
    "data.synthetic_data.generate_synthetic_dataset": _traits(
        RiskLevel.NONE, read_only=True
    ),
    "data.synthetic_data.generate_synthetic_ticks": _traits(
        RiskLevel.NONE, read_only=True
    ),
    "data.synthetic_data.generate_synthetic_bars": _traits(
        RiskLevel.NONE, read_only=True
    ),
    # FEAT-DATA-05 - Tick-Series Derivation.
    "data.tick_derivation.generate_tick_series": _traits(
        RiskLevel.NONE, read_only=True
    ),
    "data.tick_derivation.generate_tick_series_to_parquet": _traits(
        RiskLevel.MEDIUM, read_only=False, writes_file=True
    ),
    # FEAT-DATA-06 - Data Persistence and Storage.
    "data.persistence.acquire_write_lock": _traits(
        RiskLevel.LOW, read_only=False, writes_file=True
    ),
    "data.persistence.clear_cache_entry": _traits(
        RiskLevel.MEDIUM, read_only=False, modifies_database=True
    ),
    "data.persistence.clear_data_cache": _traits(
        RiskLevel.MEDIUM, read_only=False, modifies_database=True
    ),
    "data.persistence.create_backup": _traits(
        RiskLevel.MEDIUM, read_only=False, writes_file=True
    ),
    "data.persistence.describe_import_dialects": _traits(
        RiskLevel.NONE, read_only=True
    ),
    "data.persistence.enforce_retention_policy": _traits(
        RiskLevel.HIGH, read_only=False, writes_file=True
    ),
    "data.persistence.execute_transaction": _traits(
        RiskLevel.MEDIUM, read_only=False, modifies_database=True
    ),
    "data.persistence.get_cache_entry": _traits(RiskLevel.LOW, read_only=True),
    "data.persistence.import_external_dataset": _traits(
        RiskLevel.MEDIUM,
        read_only=False,
        writes_file=True,
        modifies_database=True,
    ),
    "data.persistence.load_dataset": _traits(RiskLevel.LOW, read_only=True),
    "data.persistence.put_cache_entry": _traits(
        RiskLevel.MEDIUM, read_only=False, modifies_database=True
    ),
    "data.persistence.restore_from_backup": _traits(
        RiskLevel.HIGH, read_only=False, modifies_database=True, writes_file=True
    ),
    "data.persistence.run_data_migrations": _traits(
        RiskLevel.HIGH, read_only=False, modifies_database=True
    ),
    "data.persistence.run_domain_migrations": _traits(
        RiskLevel.HIGH, read_only=False, modifies_database=True
    ),
    "data.persistence.save_dataset": _traits(
        RiskLevel.MEDIUM, read_only=False, writes_file=True
    ),
    "data.persistence.save_market_data": _traits(
        RiskLevel.MEDIUM, read_only=False, writes_file=True
    ),
    # FEAT-DATA-07 - Data Quality and Validation (pure).
    "data.quality.aggregate_flags": _traits(RiskLevel.NONE, read_only=True),
    "data.quality.detect_extreme_spread_widening": _traits(
        RiskLevel.NONE, read_only=True
    ),
    "data.quality.detect_flatline_periods": _traits(RiskLevel.NONE, read_only=True),
    "data.quality.detect_price_jumps": _traits(RiskLevel.NONE, read_only=True),
    "data.quality.detect_timestamp_gaps": _traits(RiskLevel.NONE, read_only=True),
    "data.quality.detect_zero_volume_bars": _traits(RiskLevel.NONE, read_only=True),
    "data.quality.get_quality_policy": _traits(RiskLevel.NONE, read_only=True),
    "data.quality.inspect_data_quality": _traits(RiskLevel.NONE, read_only=True),
    "data.quality.inspect_dataset_quality": _traits(RiskLevel.NONE, read_only=True),
    "data.quality.inspect_records_quality": _traits(RiskLevel.NONE, read_only=True),
    "data.quality.summarize_quality_remediation": _traits(
        RiskLevel.NONE, read_only=True
    ),
    "data.quality.validate_symbol_metadata": _traits(RiskLevel.NONE, read_only=True),
    # FEAT-DATA-08 - Data Transformation and Resampling (pure in-memory).
    "data.transformation.aggregate_ticks": _traits(RiskLevel.NONE, read_only=True),
    "data.transformation.aggregate_ticks_to_bars": _traits(
        RiskLevel.NONE, read_only=True
    ),
    "data.transformation.align_datasets": _traits(RiskLevel.NONE, read_only=True),
    "data.transformation.align_multitimeframe_data": _traits(
        RiskLevel.NONE, read_only=True
    ),
    "data.transformation.resample_dataset": _traits(RiskLevel.NONE, read_only=True),
    "data.transformation.resample_ohlcv": _traits(RiskLevel.NONE, read_only=True),
    "data.transformation.to_ohlcv_dataframe": _traits(RiskLevel.NONE, read_only=True),
    "data.transformation.to_tick_dataframe": _traits(RiskLevel.NONE, read_only=True),
    # FEAT-DATA-09 - Time and Session Handling (pure).
    "data.time_sessions.require_utc": _traits(RiskLevel.NONE, read_only=True),
    "data.time_sessions.get_timeframe_spec": _traits(RiskLevel.NONE, read_only=True),
    "data.time_sessions.validate_resample_target": _traits(
        RiskLevel.NONE, read_only=True
    ),
    "data.time_sessions.classify_gap": _traits(RiskLevel.NONE, read_only=True),
    "data.time_sessions.get_active_market_sessions": _traits(
        RiskLevel.NONE, read_only=True
    ),
    "data.time_sessions.get_exchange_sessions": _traits(RiskLevel.NONE, read_only=True),
    "data.time_sessions.get_current_schedule": _traits(RiskLevel.NONE, read_only=True),
    "data.time_sessions.get_market_hours": _traits(RiskLevel.NONE, read_only=True),
    "data.time_sessions.get_trading_sessions": _traits(RiskLevel.NONE, read_only=True),
    "data.time_sessions.market_calendar.get_schedule": _traits(
        RiskLevel.NONE, read_only=True
    ),
    "data.time_sessions.weekly_schedule_provider.get_sessions": _traits(
        RiskLevel.NONE, read_only=True
    ),
    "data.time_sessions.weekly_schedule_provider.get_schedule": _traits(
        RiskLevel.NONE, read_only=True
    ),
    # FEAT-DATA-10 - Data Source Governance.
    "data.sources.ensure_source": _traits(RiskLevel.LOW, read_only=False),
    "data.sources.ensure_source_access": _traits(RiskLevel.LOW, read_only=False),
    "data.sources.evaluate_source_policy": _traits(RiskLevel.LOW, read_only=True),
    "data.sources.get_source_descriptor": _traits(RiskLevel.LOW, read_only=True),
    "data.sources.list_composable_sources": _traits(RiskLevel.LOW, read_only=True),
    "data.sources.list_registered_sources": _traits(RiskLevel.LOW, read_only=True),
    "data.sources.promote_source": _traits(RiskLevel.MEDIUM, read_only=False),
    "data.sources.register_source": _traits(RiskLevel.LOW, read_only=False),
    "data.sources.resolve_source": _traits(RiskLevel.LOW, read_only=True),
    "data.sources.verify_read_only_call": _traits(RiskLevel.NONE, read_only=True),
    "data.sources.wrap_broker_client": _traits(RiskLevel.NONE, read_only=True),
    "data.sources.market_data_source.fetch": _traits(
        RiskLevel.LOW, read_only=True, requires_network=True
    ),
    "data.sources.market_data_source.list_symbols": _traits(
        RiskLevel.LOW, read_only=True, requires_network=True
    ),
    "data.sources.market_data_source.get_symbol_metadata": _traits(
        RiskLevel.LOW, read_only=True, requires_network=True
    ),
    "data.sources.local_market_data_source.fetch": _traits(
        RiskLevel.LOW, read_only=True
    ),
    "data.sources.local_market_data_source.list_symbols": _traits(
        RiskLevel.LOW, read_only=True
    ),
    "data.sources.local_market_data_source.get_symbol_metadata": _traits(
        RiskLevel.LOW, read_only=True
    ),
    # FEAT-DATA-11 - Economic Calendar.
    "data.economic_calendar.calendar_state_provenance": _traits(
        RiskLevel.NONE, read_only=True
    ),
    "data.economic_calendar.derive_calendar_state": _traits(
        RiskLevel.NONE, read_only=True
    ),
    "data.economic_calendar.evaluate_calendar_state": _traits(
        RiskLevel.NONE, read_only=True
    ),
    "data.economic_calendar.from_row": _traits(RiskLevel.NONE, read_only=True),
    "data.economic_calendar.get_economic_events": _traits(
        RiskLevel.LOW, read_only=True
    ),
    "data.economic_calendar.get_persisted_events": _traits(
        RiskLevel.LOW, read_only=True
    ),
    "data.economic_calendar.get_symbol_economic_events": _traits(
        RiskLevel.LOW, read_only=True
    ),
    "data.economic_calendar.get_symbol_event_profile": _traits(
        RiskLevel.LOW, read_only=True
    ),
    "data.economic_calendar.is_news_restricted": _traits(RiskLevel.LOW, read_only=True),
    "data.economic_calendar.is_news_restricted_events": _traits(
        RiskLevel.NONE, read_only=True
    ),
    "data.economic_calendar.populate_market_context_calendar": _traits(
        RiskLevel.NONE, read_only=True
    ),
    "data.economic_calendar.scrape_economic_calendar": _traits(
        RiskLevel.LOW, read_only=True, requires_network=True
    ),
    "data.economic_calendar.calendar_transport.fetch_site": _traits(
        RiskLevel.LOW, read_only=True, requires_network=True
    ),
    "data.economic_calendar.economic_calendar_provider.get_events": _traits(
        RiskLevel.LOW, read_only=True, requires_network=True
    ),
    "data.economic_calendar.calendar_scrape_provider.get_events": _traits(
        RiskLevel.LOW, read_only=True, requires_network=True
    ),
    "data.economic_calendar.economic_event_store.upsert": _traits(
        RiskLevel.MEDIUM, read_only=False, modifies_database=True
    ),
    "data.economic_calendar.economic_event_store.query": _traits(
        RiskLevel.LOW, read_only=True
    ),
    "data.economic_calendar.economic_event_store.refresh_windows": _traits(
        RiskLevel.NONE, read_only=True
    ),
    "data.economic_calendar.scrape_result.to_dataframe": _traits(
        RiskLevel.NONE, read_only=True
    ),
    "data.economic_calendar.scrape_result.save": _traits(
        RiskLevel.MEDIUM, read_only=False, writes_file=True
    ),
    "data.economic_calendar.scrape_result.serialize": _traits(
        RiskLevel.NONE, read_only=True
    ),
    "data.economic_calendar.scrape_result.deserialize": _traits(
        RiskLevel.NONE, read_only=True
    ),
    # FEAT-DATA-12 - Real-Time Feed Lifecycle and Observability.
    "data.realtime_feeds.start_internal_feed": _traits(RiskLevel.LOW, read_only=False),
    "data.realtime_feeds.ingest_feed_event": _traits(RiskLevel.LOW, read_only=False),
    "data.realtime_feeds.reconcile_feed_gap": _traits(RiskLevel.LOW, read_only=False),
    "data.realtime_feeds.reconnect_feed": _traits(RiskLevel.LOW, read_only=False),
    "data.realtime_feeds.read_feed_status": _traits(RiskLevel.LOW, read_only=True),
    "data.realtime_feeds.get_feed_status": _traits(RiskLevel.LOW, read_only=True),
    # FEAT-DATA-13 - Scheduler and Job Management.
    "data.data_jobs.derive_backfill_key": _traits(RiskLevel.NONE, read_only=True),
    "data.data_jobs.execute_backfill_chunk": _traits(
        RiskLevel.MEDIUM,
        read_only=False,
        modifies_database=True,
        requires_network=True,
    ),
    "data.data_jobs.schedule_update_job": _traits(
        RiskLevel.MEDIUM, read_only=False, modifies_database=True
    ),
    "data.data_jobs.read_update_job_status": _traits(RiskLevel.LOW, read_only=True),
    "data.data_jobs.run_data_update_job_once": _traits(
        RiskLevel.MEDIUM,
        read_only=False,
        modifies_database=True,
        requires_network=True,
    ),
    "data.data_jobs.create_data_update_job": _traits(
        RiskLevel.MEDIUM, read_only=False, modifies_database=True
    ),
    "data.data_jobs.start_data_update_job": _traits(
        RiskLevel.MEDIUM, read_only=False, modifies_database=True
    ),
    "data.data_jobs.stop_data_update_job": _traits(
        RiskLevel.MEDIUM, read_only=False, modifies_database=True
    ),
    "data.data_jobs.get_data_update_job_status": _traits(RiskLevel.LOW, read_only=True),
    "data.data_jobs.recover_update_jobs": _traits(
        RiskLevel.HIGH, read_only=False, modifies_database=True
    ),
    # FEAT-DATA-14 - Cross-Domain Evidence (provider reads).
    "data.evidence.get_account_state_snapshot": _traits(
        RiskLevel.LOW, read_only=True, requires_network=True
    ),
    "data.evidence.get_fx_conversion_evidence": _traits(
        RiskLevel.LOW, read_only=True, requires_network=True
    ),
    "data.evidence.get_market_context_evidence": _traits(
        RiskLevel.LOW, read_only=True, requires_network=True
    ),
    "data.evidence.fx_rate_provider.get_rate_leg": _traits(
        RiskLevel.LOW, read_only=True, requires_network=True
    ),
    "data.evidence.market_context_provider.get_market_context": _traits(
        RiskLevel.LOW, read_only=True, requires_network=True
    ),
    # FEAT-DATA-15 - Audit Evidence.
    "data.audit.persist_audit_event": _traits(
        RiskLevel.MEDIUM, read_only=False, modifies_database=True
    ),
    "data.audit.query_audit_events": _traits(RiskLevel.LOW, read_only=True),
}

OPERATION_TRAITS: Mapping[str, OperationTraits] = _TRAITS


def data_start_time() -> int:
    """Return a monotonic start value for a DATA public operation.

    Returns:
        Current ``time.perf_counter_ns`` value.
    """
    return time.perf_counter_ns()


def _operation_traits(operation: str) -> OperationTraits:
    """Return the static capability traits for one registered operation.

    Args:
        operation: Qualified operation name (``data.<feature>.<op>``).

    Returns:
        Immutable static capability declaration.

    Raises:
        KeyError: If the operation is not registered (a programming error).
    """
    try:
        return _TRAITS[operation]
    except KeyError as error:  # pragma: no cover - programming-error guard.
        message = f"unregistered DATA operation metadata: {operation!r}"
        raise KeyError(message) from error


def _data_error_details(error: DataError) -> Mapping[str, JsonValue]:
    """Preserve all safe legacy ``DataError`` evidence in error details.

    Args:
        error: Canonical redacted Data-domain failure.

    Returns:
        JSON-safe structured error details carrying retryable, severity,
        operator action, and any caller-provided request identity.
    """
    details: dict[str, JsonValue] = {
        "retryable": error.retryable,
        "severity": error.severity,
        "operator_action": error.operator_action,
    }
    if error.request_id is not None:
        details["request_id"] = error.request_id
    for key, value in error.safe_details.items():
        # safe_details values are already JSON scalars (validated by DataError).
        details[str(key)] = value  # type: ignore[assignment]
    return details


def build_data_response[T](
    *,
    operation: str,
    request_id: str | None = None,
    start_time: int,
    data: T | None = None,
    error: DataError | None = None,
    correlation_id: str | None = None,
    extensions: Mapping[str, JsonValue] | None = None,
) -> StandardResponse[T]:
    """Build one lossless standard DATA operation response.

    Args:
        operation: Qualified operation name (``data.<feature>.<op>``).
        request_id: Canonical request trace identifier. When ``None`` or invalid a
            fresh ``req-`` UUID4 identifier is generated so the response itself always
            carries valid trace identity.
        start_time: Starting ``time.perf_counter_ns`` value.
        data: Raw successful result.
        error: Canonical Data-domain failure.
        correlation_id: Optional canonical correlation trace identifier.
        extensions: Optional additional non-payload envelope evidence.

    Returns:
        Validated standard response retaining all safe Data evidence.

    Raises:
        KeyError: If the operation metadata is not registered.
    """
    resolved_id, _ = resolve_operation_request_id(explicit=request_id)
    traits = _operation_traits(operation)
    metadata = ResponseMetadata(
        name=operation,
        domain="data",
        risk_level=traits.risk_level,
        request_id=resolved_id,
        correlation_id=correlation_id,
        execution_ms=_elapsed_ms(start_time),
        read_only=traits.read_only,
        writes_file=traits.writes_file,
        modifies_database=traits.modifies_database,
        places_trade=False,
        requires_network=traits.requires_network,
        extensions=extensions or {},
    )
    if error is None:
        return success_response(
            data,
            message=f"Data operation {operation} completed",
            metadata=metadata,
        )
    return error_response(
        code=error.code,
        details=_data_error_details(error),
        message=error.safe_message,
        metadata=metadata,
        catalog=DATA_ERROR_MANIFEST,
    )


def build_exception_response[T](
    *,
    operation: str,
    request_id: str | None = None,
    start_time: int,
    exception: BaseException,
    correlation_id: str | None = None,
    extensions: Mapping[str, JsonValue] | None = None,
) -> StandardResponse[T]:
    """Map an unexpected exception to a secret-safe DATA error response.

    Cancellation and process-control exceptions propagate unchanged.

    Args:
        operation: Qualified operation name.
        request_id: Canonical request trace identifier. When ``None`` or invalid a
            fresh ``req-`` UUID4 identifier is generated.
        start_time: Starting ``time.perf_counter_ns`` value.
        exception: Caught exception to normalize without retaining it.
        correlation_id: Optional canonical correlation trace identifier.
        extensions: Optional additional safe diagnostic details.

    Returns:
        Immutable failed standard response.

    Raises:
        CancelledError: If asynchronous cancellation is supplied.
        GeneratorExit: If generator termination is supplied.
        KeyboardInterrupt: If process interruption is supplied.
        SystemExit: If process exit is supplied.
    """
    resolved_id, _ = resolve_operation_request_id(explicit=request_id)
    traits = _operation_traits(operation)
    metadata = ResponseMetadata(
        name=operation,
        domain="data",
        risk_level=traits.risk_level,
        request_id=resolved_id,
        correlation_id=correlation_id,
        execution_ms=_elapsed_ms(start_time),
        read_only=traits.read_only,
        writes_file=traits.writes_file,
        modifies_database=traits.modifies_database,
        places_trade=False,
        requires_network=traits.requires_network,
        extensions={},
    )
    return exception_response(
        exception,
        message=f"Data operation {operation} failed",
        metadata=metadata,
        catalog=DATA_ERROR_MANIFEST,
        extensions=extensions,
    )


def run_data_operation[T](
    *,
    operation: str,
    request_id: str | None = None,
    start_time: int,
    raw: Callable[[], T],
    correlation_id: str | None = None,
    extensions: Mapping[str, JsonValue] | None = None,
) -> StandardResponse[T]:
    """Run one synchronous raw core and wrap its outcome in a standard response.

    This is a typed boundary helper, not a decorator: the public operation
    retains its full signature, resolves its own request identity, and passes an
    inline thunk. Expected failures surface as ``DataError`` and become error
    responses; cancellation and process-control exceptions propagate;
    everything else is normalized through the safe exception mapper.

    Args:
        operation: Qualified operation name.
        request_id: Canonical request trace identifier. When ``None`` or invalid a
            fresh ``req-`` UUID4 identifier is generated.
        start_time: Starting ``time.perf_counter_ns`` value.
        raw: Thunk invoking the private raw core with no arguments.
        correlation_id: Optional canonical correlation trace identifier.
        extensions: Optional additional non-payload envelope evidence.

    Returns:
        Standard response carrying the exact raw result on success.

    Raises:
        CancelledError: If asynchronous cancellation occurs inside ``raw``.
        GeneratorExit: If generator termination occurs inside ``raw``.
        KeyboardInterrupt: If process interruption occurs inside ``raw``.
        SystemExit: If process exit occurs inside ``raw``.
    """
    resolved_id, _ = resolve_operation_request_id(explicit=request_id)
    try:
        result = raw()
    except DataError as error:
        return build_data_response(
            operation=operation,
            request_id=resolved_id,
            start_time=start_time,
            error=error,
            correlation_id=correlation_id,
            extensions=extensions,
        )
    except _PROPAGATED_EXCEPTIONS:
        raise
    except Exception as exception:  # noqa: BLE001 - safe normalization boundary.
        logger.warning("Data operation %s raised an unexpected exception", operation)
        return build_exception_response(
            operation=operation,
            request_id=resolved_id,
            start_time=start_time,
            exception=exception,
            correlation_id=correlation_id,
        )
    return build_data_response(
        operation=operation,
        request_id=resolved_id,
        start_time=start_time,
        data=result,
        correlation_id=correlation_id,
        extensions=extensions,
    )


async def run_data_operation_async[T](
    *,
    operation: str,
    request_id: str | None = None,
    start_time: int,
    raw: Callable[[], Awaitable[T]],
    correlation_id: str | None = None,
    extensions: Mapping[str, JsonValue] | None = None,
) -> StandardResponse[T]:
    """Run one asynchronous raw core and wrap its outcome in a standard response.

    Async analogue of :func:`run_data_operation`. ``asyncio.CancelledError``
    propagates so cancellation semantics are preserved.

    Args:
        operation: Qualified operation name.
        request_id: Canonical request trace identifier. When ``None`` or invalid a
            fresh ``req-`` UUID4 identifier is generated.
        start_time: Starting ``time.perf_counter_ns`` value.
        raw: Coroutine-returning thunk invoking the private raw core.
        correlation_id: Optional canonical correlation trace identifier.
        extensions: Optional additional non-payload envelope evidence.

    Returns:
        Standard response carrying the exact raw result on success.

    Raises:
        CancelledError: If asynchronous cancellation occurs inside ``raw``.
        GeneratorExit: If generator termination occurs inside ``raw``.
        KeyboardInterrupt: If process interruption occurs inside ``raw``.
        SystemExit: If process exit occurs inside ``raw``.
    """
    resolved_id, _ = resolve_operation_request_id(explicit=request_id)
    try:
        result = await raw()
    except DataError as error:
        return build_data_response(
            operation=operation,
            request_id=resolved_id,
            start_time=start_time,
            error=error,
            correlation_id=correlation_id,
            extensions=extensions,
        )
    except _PROPAGATED_EXCEPTIONS:
        raise
    except Exception as exception:  # noqa: BLE001 - safe normalization boundary.
        logger.warning("Data operation %s raised an unexpected exception", operation)
        return build_exception_response(
            operation=operation,
            request_id=resolved_id,
            start_time=start_time,
            exception=exception,
            correlation_id=correlation_id,
        )
    return build_data_response(
        operation=operation,
        request_id=resolved_id,
        start_time=start_time,
        data=result,
        correlation_id=correlation_id,
        extensions=extensions,
    )


def unwrap_data_response[T](
    response: StandardResponse[T],
    *,
    operation: str,
    request_id: str,
) -> T:
    """Consume a nested standard DATA response and return its raw data.

    Used when one Data public operation invokes another Data public protocol.
    The outer operation must never return ``StandardResponse[StandardResponse[T]]``:
    on success the raw ``data`` is returned to the outer raw core, and on failure
    the nested error is converted into a ``DataError`` carrying the original code
    and request identity.

    Args:
        response: Nested standard response received from a Data public call.
        operation: Qualified name of the consuming (outer) operation, for logs.
        request_id: Outer-operation trace identifier carried into the failure.

    Returns:
        The raw successful result extracted from the nested response.

    Raises:
        DataError: If the nested response reports a failure, preserving the
            original code and safe details.
    """
    if response.status != "success":
        nested_error = response.error
        code = nested_error.code if nested_error is not None else "UNKNOWN_ERROR"
        details: dict[str, Any] = {}
        if nested_error is not None:
            for key, value in nested_error.details.items():
                if isinstance(value, str | bool | int | float) or value is None:
                    details[str(key)] = value
        logger.debug("Data operation %s propagated nested failure %s", operation, code)
        raise DataError(
            code,
            safe_details=details or None,
            request_id=request_id,
        )
    # ``None`` is a legitimate raw success result for some Data operations
    # (for example ``validate_resample_target``). Callers requiring a non-null
    # business result must check ``data`` themselves.
    return response.data


def resolve_operation_request_id(
    request: object | None = None,
    *,
    explicit: str | None = None,
) -> tuple[str, DataError | None]:
    """Resolve a DATA boundary request identifier per the trace policy.

    Resolution order (migration request-identity policy):

    1. A validated request object's existing ``request_id`` attribute.
    2. An explicit valid ``request_id`` argument.
    3. A generated ``req-`` UUID4 identifier.

    An invalid caller-supplied identifier must not be silently accepted for a
    successful operation. A valid response trace identifier is always generated
    so the error response itself is valid, and a ``VALIDATION_FAILED`` error is
    returned identifying ``request_id`` as the invalid field.

    Args:
        request: Optional typed request contract exposing ``request_id``.
        explicit: Optional explicit request identifier argument.

    Returns:
        Tuple of ``(response_request_id, validation_error)``. The identifier is
        always valid; ``validation_error`` is ``None`` unless an explicit
        caller-supplied identifier was rejected.
    """
    candidate: str | None = None
    if request is not None:
        candidate = getattr(request, "request_id", None)
    if candidate is None:
        candidate = explicit
    if candidate is None:
        return generate_id("req"), None
    try:
        validate_id(candidate, expected_prefix="req")
    except Exception:  # noqa: BLE001 - any validation failure is handled alike.
        response_id = generate_id("req")
        error = DataError(
            "VALIDATION_FAILED",
            safe_details={"field": "request_id"},
            request_id=response_id,
        )
        return response_id, error
    return candidate, None


def _elapsed_ms(start_time: int) -> float:
    """Return monotonic elapsed milliseconds rounded to three decimals.

    Imported lazily through the public Utils name so the rounding invariant is
    owned by Utils, not duplicated here.

    Args:
        start_time: Starting ``time.perf_counter_ns`` value.

    Returns:
        Non-negative elapsed milliseconds rounded to three decimal places.
    """
    # Local import keeps this module free of an unused-name at the top if the
    # timing helper is ever renamed upstream; the contract remains Utils-owned.
    from app.utils import get_execution_ms

    return get_execution_ms(start_time)


__all__ = [
    "OPERATION_TRAITS",
    "OperationTraits",
    "build_data_response",
    "build_exception_response",
    "data_start_time",
    "resolve_operation_request_id",
    "run_data_operation",
    "run_data_operation_async",
    "unwrap_data_response",
]
