"""Private package-root construction, getter, and predicate adapters.

This reconciliation-excluded support module contains no feature behavior. It
adapts private feature-owned contract types and constants to the function-only
package-root boundary without making those private values public.
"""

# These package-root builders intentionally forward heterogeneous private
# constructor signatures while keeping every public export a function.
# ruff: noqa: ANN401

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from app.services.data.contracts import dataset as _dataset_contracts
from app.services.data.contracts import errors as _error_contracts
from app.services.data.contracts.dataset import (
    MARKET_DATASET_SCHEMA,
    NORMALIZATION_VERSION,
    PRECISION_POLICIES,
    QUALITY_SAMPLE_LIMIT,
    WORKFLOW_CONTEXTS,
    DataQualityReport,
    MarketDataset,
)
from app.services.data.contracts.errors import (
    DATA_ERROR_MANIFEST,
    ErrorDefinition,
)
from app.services.data.contracts.records import (
    OHLCVRecord,
    SpreadRecord,
    TickRecord,
)
from app.services.data.contracts.responses import OPERATION_TRAITS, OperationTraits
from app.services.data.data_jobs import contracts as _job_contracts
from app.services.data.datasets import contracts as _local_contracts
from app.services.data.economic_calendar import (
    DEFAULT_MINIMUM_IMPACT,
    SYMBOL_EVENT_PROFILES,
    SymbolEventProfile,
)
from app.services.data.economic_calendar import events as _calendar_events
from app.services.data.economic_calendar import (
    firecrawl_transport as _calendar_firecrawl,
)
from app.services.data.economic_calendar import providers as _calendar_providers
from app.services.data.economic_calendar import reader_transport as _calendar_reader
from app.services.data.economic_calendar import scraper as _calendar_scraper
from app.services.data.economic_calendar import store as _calendar_store
from app.services.data.economic_calendar.scraper import CALENDAR_SITES
from app.services.data.evidence import account_contracts as _account_contracts
from app.services.data.evidence import fx_contracts as _fx_contracts
from app.services.data.evidence import market_context_contracts as _context_contracts
from app.services.data.evidence.account_contracts import (
    ACCOUNT_SNAPSHOT_SCHEMA,
    AccountSnapshotRequest,
    AccountStateSnapshot,
)
from app.services.data.evidence.audit_contracts import (
    AUDIT_QUERY_HARD_MAX_LIMIT,
    AuditEventPage,
    AuditEventQuery,
)
from app.services.data.evidence.fx_contracts import (
    FX_CONVERSION_EVIDENCE_SCHEMA,
    FXConversionRequest,
)
from app.services.data.evidence.market_context_contracts import (
    MARKET_CONTEXT_SCHEMA,
    MarketContextRequest,
)
from app.services.data.market_data import asset_classifier as _asset_classifier
from app.services.data.market_data import level1 as _level1
from app.services.data.market_data import requests as _market_requests
from app.services.data.market_data import snapshot as _snapshot
from app.services.data.market_data import symbol_metadata as _symbol_metadata
from app.services.data.market_data.requests import MarketDataRequest
from app.services.data.market_data.symbol_metadata import SymbolMetadata
from app.services.data.market_events import contracts as _feed_contracts
from app.services.data.persistence import DATA_MIGRATION_STEPS
from app.services.data.persistence import contracts as _persistence_contracts
from app.services.data.sources import contracts as _source_contracts
from app.services.data.sources import read_only as _read_only
from app.services.data.sources import research_contracts as _research_source_contracts
from app.services.data.sources.contracts import (
    SourceDescriptor,
    SourceIdentity,
    SourceLicensePolicy,
)
from app.services.data.sources.local_adapter import LocalMarketDataSource
from app.services.data.sources.policy import SourcePolicyConfig
from app.services.data.sources.read_only import READ_ONLY_BROKER_METHODS
from app.services.data.synthetic_data.contracts import SyntheticRequest
from app.services.data.time_sessions import (
    FOREX_NAMED_SESSIONS,
    TIMEFRAME_MANIFEST,
    NamedSessionDefinition,
    TimeframeSpec,
)
from app.services.data.time_sessions import contracts as _time_contracts
from app.services.data.time_sessions import weekly_schedule as _weekly_schedule

if TYPE_CHECKING:
    from app.services.data.persistence.contracts import MigrationStep


def build_account_order(*args: Any, **kwargs: Any) -> Any:
    """Build one AccountOrder value through the Data public boundary.

    Args:
        args: The ``args`` argument.
        kwargs: The ``kwargs`` argument.

    Returns:
        The result produced by the operation.
    """
    return _account_contracts.AccountOrder(*args, **kwargs)


def build_active_market_sessions_request(*args: Any, **kwargs: Any) -> Any:
    """Build one ActiveMarketSessionsRequest value through the Data public boundary.

    Args:
        args: The ``args`` argument.
        kwargs: The ``kwargs`` argument.

    Returns:
        The result produced by the operation.
    """
    return _time_contracts.ActiveMarketSessionsRequest(*args, **kwargs)


def build_availability_request(*args: Any, **kwargs: Any) -> Any:
    """Build one AvailabilityRequest value through the Data public boundary.

    Args:
        args: The ``args`` argument.
        kwargs: The ``kwargs`` argument.

    Returns:
        The result produced by the operation.
    """
    return _market_requests.AvailabilityRequest(*args, **kwargs)


def build_backup_target(*args: Any, **kwargs: Any) -> Any:
    """Build one BackupTarget value through the Data public boundary.

    Args:
        args: The ``args`` argument.
        kwargs: The ``kwargs`` argument.

    Returns:
        The result produced by the operation.
    """
    return _persistence_contracts.BackupTarget(*args, **kwargs)


def build_cache_clear_request(*args: Any, **kwargs: Any) -> Any:
    """Build one CacheClearRequest value through the Data public boundary.

    Args:
        args: The ``args`` argument.
        kwargs: The ``kwargs`` argument.

    Returns:
        The result produced by the operation.
    """
    return _persistence_contracts.CacheClearRequest(*args, **kwargs)


def build_cache_read_request(*args: Any, **kwargs: Any) -> Any:
    """Build one CacheReadRequest value through the Data public boundary.

    Args:
        args: The ``args`` argument.
        kwargs: The ``kwargs`` argument.

    Returns:
        The result produced by the operation.
    """
    return _persistence_contracts.CacheReadRequest(*args, **kwargs)


def build_cache_write_request(*args: Any, **kwargs: Any) -> Any:
    """Build one CacheWriteRequest value through the Data public boundary.

    Args:
        args: The ``args`` argument.
        kwargs: The ``kwargs`` argument.

    Returns:
        The result produced by the operation.
    """
    return _persistence_contracts.CacheWriteRequest(*args, **kwargs)


def build_calendar_scrape_provider(*args: Any, **kwargs: Any) -> Any:
    """Build one CalendarScrapeProvider value through the Data public boundary.

    Args:
        args: The ``args`` argument.
        kwargs: The ``kwargs`` argument.

    Returns:
        The result produced by the operation.
    """
    return _calendar_providers.CalendarScrapeProvider(*args, **kwargs)


def build_firecrawl_calendar_transport(*args: Any, **kwargs: Any) -> Any:
    """Build the licensed Firecrawl transport through the Data public boundary.

    Args:
        args: The ``args`` argument.
        kwargs: The ``kwargs`` argument.

    Returns:
        The result produced by the operation.
    """
    return _calendar_firecrawl.build_firecrawl_calendar_transport(*args, **kwargs)


def build_reader_calendar_transport(*args: Any, **kwargs: Any) -> Any:
    """Build the bounded Reader transport through the Data public boundary.

    Args:
        args: The ``args`` argument.
        kwargs: The ``kwargs`` argument.

    Returns:
        The result produced by the operation.
    """
    return _calendar_reader.build_reader_calendar_transport(*args, **kwargs)


def build_column_mapping(*args: Any, **kwargs: Any) -> Any:
    """Build one ColumnMapping value through the Data public boundary.

    Args:
        args: The ``args`` argument.
        kwargs: The ``kwargs`` argument.

    Returns:
        The result produced by the operation.
    """
    return _persistence_contracts.ColumnMapping(*args, **kwargs)


def build_data_gap(*args: Any, **kwargs: Any) -> Any:
    """Build one DataGap value through the Data public boundary.

    Args:
        args: The ``args`` argument.
        kwargs: The ``kwargs`` argument.

    Returns:
        The result produced by the operation.
    """
    return _dataset_contracts.DataGap(*args, **kwargs)


def build_data_range(*args: Any, **kwargs: Any) -> Any:
    """Build one DataRange value through the Data public boundary.

    Args:
        args: The ``args`` argument.
        kwargs: The ``kwargs`` argument.

    Returns:
        The result produced by the operation.
    """
    return _dataset_contracts.DataRange(*args, **kwargs)


def build_dataset_load_request(*args: Any, **kwargs: Any) -> Any:
    """Build one DatasetLoadRequest value through the Data public boundary.

    Args:
        args: The ``args`` argument.
        kwargs: The ``kwargs`` argument.

    Returns:
        The result produced by the operation.
    """
    return _local_contracts.DatasetLoadRequest(*args, **kwargs)


def build_dataset_save_request(*args: Any, **kwargs: Any) -> Any:
    """Build one DatasetSaveRequest value through the Data public boundary.

    Args:
        args: The ``args`` argument.
        kwargs: The ``kwargs`` argument.

    Returns:
        The result produced by the operation.
    """
    return _persistence_contracts.DatasetSaveRequest(*args, **kwargs)


def build_data_error(*args: Any, **kwargs: Any) -> BaseException:
    """Build one redacted Data boundary error without exposing its class.

    Args:
        args: The ``args`` argument.
        kwargs: The ``kwargs`` argument.

    Returns:
        The result produced by the operation.
    """
    from app.services.data.contracts.errors import DataError

    return DataError(*args, **kwargs)


def build_economic_event(*args: Any, **kwargs: Any) -> Any:
    """Build one EconomicEvent value through the Data public boundary.

    Args:
        args: The ``args`` argument.
        kwargs: The ``kwargs`` argument.

    Returns:
        The result produced by the operation.
    """
    return _calendar_events.EconomicEvent(*args, **kwargs)


def build_economic_event_store(*args: Any, **kwargs: Any) -> Any:
    """Build one EconomicEventStore value through the Data public boundary.

    Args:
        args: The ``args`` argument.
        kwargs: The ``kwargs`` argument.

    Returns:
        The result produced by the operation.
    """
    return _calendar_store.EconomicEventStore(*args, **kwargs)


def build_error_definition(*args: Any, **kwargs: Any) -> Any:
    """Build one ErrorDefinition value through the Data public boundary.

    Args:
        args: The ``args`` argument.
        kwargs: The ``kwargs`` argument.

    Returns:
        The result produced by the operation.
    """
    return _error_contracts.ErrorDefinition(*args, **kwargs)


def build_event_impact(*args: Any, **kwargs: Any) -> Any:
    """Build one EventImpact value through the Data public boundary.

    Args:
        args: The ``args`` argument.
        kwargs: The ``kwargs`` argument.

    Returns:
        The result produced by the operation.
    """
    return _calendar_events.EventImpact(*args, **kwargs)


def build_exchange_session_request(*args: Any, **kwargs: Any) -> Any:
    """Build one ExchangeSessionRequest value through the Data public boundary.

    Args:
        args: The ``args`` argument.
        kwargs: The ``kwargs`` argument.

    Returns:
        The result produced by the operation.
    """
    return _time_contracts.ExchangeSessionRequest(*args, **kwargs)


def build_external_import_request(*args: Any, **kwargs: Any) -> Any:
    """Build one ExternalImportRequest value through the Data public boundary.

    Args:
        args: The ``args`` argument.
        kwargs: The ``kwargs`` argument.

    Returns:
        The result produced by the operation.
    """
    return _persistence_contracts.ExternalImportRequest(*args, **kwargs)


def build_feed_config(*args: Any, **kwargs: Any) -> Any:
    """Build one FeedConfig value through the Data public boundary.

    Args:
        args: The ``args`` argument.
        kwargs: The ``kwargs`` argument.

    Returns:
        The result produced by the operation.
    """
    return _feed_contracts.FeedConfig(*args, **kwargs)


def build_feed_status_request(*args: Any, **kwargs: Any) -> Any:
    """Build one FeedStatusRequest value through the Data public boundary.

    Args:
        args: The ``args`` argument.
        kwargs: The ``kwargs`` argument.

    Returns:
        The result produced by the operation.
    """
    return _feed_contracts.FeedStatusRequest(*args, **kwargs)


def build_fx_conversion_evidence(*args: Any, **kwargs: Any) -> Any:
    """Build one FXConversionEvidence value through the Data public boundary.

    Args:
        args: The ``args`` argument.
        kwargs: The ``kwargs`` argument.

    Returns:
        The result produced by the operation.
    """
    return _fx_contracts.FXConversionEvidence(*args, **kwargs)


def build_fx_rate_leg(*args: Any, **kwargs: Any) -> Any:
    """Build one FXRateLeg value through the Data public boundary.

    Args:
        args: The ``args`` argument.
        kwargs: The ``kwargs`` argument.

    Returns:
        The result produced by the operation.
    """
    return _fx_contracts.FXRateLeg(*args, **kwargs)


def build_job_definition(*args: Any, **kwargs: Any) -> Any:
    """Build one JobDefinition value through the Data public boundary.

    Args:
        args: The ``args`` argument.
        kwargs: The ``kwargs`` argument.

    Returns:
        The result produced by the operation.
    """
    return _job_contracts.JobDefinition(*args, **kwargs)


def build_job_status_request(*args: Any, **kwargs: Any) -> Any:
    """Build one JobStatusRequest value through the Data public boundary.

    Args:
        args: The ``args`` argument.
        kwargs: The ``kwargs`` argument.

    Returns:
        The result produced by the operation.
    """
    return _job_contracts.JobStatusRequest(*args, **kwargs)


def build_market_context_evidence(*args: Any, **kwargs: Any) -> Any:
    """Build one MarketContextEvidence value through the Data public boundary.

    Args:
        args: The ``args`` argument.
        kwargs: The ``kwargs`` argument.

    Returns:
        The result produced by the operation.
    """
    return _context_contracts.MarketContextEvidence(*args, **kwargs)


def build_market_hours_request(*args: Any, **kwargs: Any) -> Any:
    """Build one MarketHoursRequest value through the Data public boundary.

    Args:
        args: The ``args`` argument.
        kwargs: The ``kwargs`` argument.

    Returns:
        The result produced by the operation.
    """
    return _time_contracts.MarketHoursRequest(*args, **kwargs)


def build_market_schedule(*args: Any, **kwargs: Any) -> Any:
    """Build one MarketSchedule value through the Data public boundary.

    Args:
        args: The ``args`` argument.
        kwargs: The ``kwargs`` argument.

    Returns:
        The result produced by the operation.
    """
    return _time_contracts.MarketSchedule(*args, **kwargs)


def build_migration_request(*args: Any, **kwargs: Any) -> Any:
    """Build one MigrationRequest value through the Data public boundary.

    Args:
        args: The ``args`` argument.
        kwargs: The ``kwargs`` argument.

    Returns:
        The result produced by the operation.
    """
    return _persistence_contracts.MigrationRequest(*args, **kwargs)


def build_quality_issue(*args: Any, **kwargs: Any) -> Any:
    """Build one QualityIssue value through the Data public boundary.

    Args:
        args: The ``args`` argument.
        kwargs: The ``kwargs`` argument.

    Returns:
        The result produced by the operation.
    """
    return _dataset_contracts.QualityIssue(*args, **kwargs)


def build_raw_feed_event(*args: Any, **kwargs: Any) -> Any:
    """Build one RawFeedEvent value through the Data public boundary.

    Args:
        args: The ``args`` argument.
        kwargs: The ``kwargs`` argument.

    Returns:
        The result produced by the operation.
    """
    return _feed_contracts.RawFeedEvent(*args, **kwargs)


def build_read_only_broker_proxy(*args: Any, **kwargs: Any) -> Any:
    """Build one ReadOnlyBrokerProxy value through the Data public boundary.

    Args:
        args: The ``args`` argument.
        kwargs: The ``kwargs`` argument.

    Returns:
        The result produced by the operation.
    """
    return _read_only.ReadOnlyBrokerProxy(*args, **kwargs)


def build_reconnect_policy(*args: Any, **kwargs: Any) -> Any:
    """Build one ReconnectPolicy value through the Data public boundary.

    Args:
        args: The ``args`` argument.
        kwargs: The ``kwargs`` argument.

    Returns:
        The result produced by the operation.
    """
    return _feed_contracts.ReconnectPolicy(*args, **kwargs)


def build_research_source_ingest_request(*args: Any, **kwargs: Any) -> Any:
    """Build one opaque point-in-time source ingestion request.

    Args:
        args: The ``args`` argument.
        kwargs: The ``kwargs`` argument.

    Returns:
        The result produced by the operation.
    """
    return _research_source_contracts.ResearchSourceIngestRequest(*args, **kwargs)


def build_research_source_policy(*args: Any, **kwargs: Any) -> Any:
    """Build one opaque governed research-source policy.

    Args:
        args: The ``args`` argument.
        kwargs: The ``kwargs`` argument.

    Returns:
        The result produced by the operation.
    """
    return _research_source_contracts.ResearchSourcePolicy(*args, **kwargs)


def build_research_source_query(*args: Any, **kwargs: Any) -> Any:
    """Build one opaque point-in-time research-source query.

    Args:
        args: The ``args`` argument.
        kwargs: The ``kwargs`` argument.

    Returns:
        The result produced by the operation.
    """
    return _research_source_contracts.ResearchSourceQuery(*args, **kwargs)


def build_verified_research_source(*args: Any, **kwargs: Any) -> Any:
    """Build one opaque verified-provider manifest.

    Args:
        args: The ``args`` argument.
        kwargs: The ``kwargs`` argument.

    Returns:
        The result produced by the operation.
    """
    return _research_source_contracts.VerifiedResearchSource(*args, **kwargs)


def get_research_source_value_field(value: object, field: str) -> object:
    """Return one public field from a Data research-source value.

    Args:
        value: The ``value`` argument.
        field: The ``field`` argument.

    Returns:
        The result produced by the operation.

    Raises:
        ValueError: If the field is private or unavailable.
    """
    if not field or field.startswith("_") or not hasattr(value, field):
        raise ValueError("Data research-source value does not expose the field")
    return getattr(value, field)


def is_research_source_value(value: object, value_type: str) -> bool:
    """Return whether a value is one registered research-source contract.

    Args:
        value: The ``value`` argument.
        value_type: The ``value_type`` argument.

    Returns:
        The result produced by the operation.
    """
    model = getattr(_research_source_contracts, value_type, None)
    return isinstance(value, model) if isinstance(model, type) else False


def build_schedule_request(*args: Any, **kwargs: Any) -> Any:
    """Build one ScheduleRequest value through the Data public boundary.

    Args:
        args: The ``args`` argument.
        kwargs: The ``kwargs`` argument.

    Returns:
        The result produced by the operation.
    """
    return _time_contracts.ScheduleRequest(*args, **kwargs)


def build_scrape_options(*args: Any, **kwargs: Any) -> Any:
    """Build one ScrapeOptions value through the Data public boundary.

    Args:
        args: The ``args`` argument.
        kwargs: The ``kwargs`` argument.

    Returns:
        The result produced by the operation.
    """
    return _calendar_scraper.ScrapeOptions(*args, **kwargs)


def build_scrape_result(*args: Any, **kwargs: Any) -> Any:
    """Build one ScrapeResult value through the Data public boundary.

    Args:
        args: The ``args`` argument.
        kwargs: The ``kwargs`` argument.

    Returns:
        The result produced by the operation.
    """
    return _calendar_scraper.ScrapeResult(*args, **kwargs)


def build_session_window(*args: Any, **kwargs: Any) -> Any:
    """Build one SessionWindow value through the Data public boundary.

    Args:
        args: The ``args`` argument.
        kwargs: The ``kwargs`` argument.

    Returns:
        The result produced by the operation.
    """
    return _time_contracts.SessionWindow(*args, **kwargs)


def build_source_promotion_request(*args: Any, **kwargs: Any) -> Any:
    """Build one SourcePromotionRequest value through the Data public boundary.

    Args:
        args: The ``args`` argument.
        kwargs: The ``kwargs`` argument.

    Returns:
        The result produced by the operation.
    """
    return _source_contracts.SourcePromotionRequest(*args, **kwargs)


def build_source_read_request(*args: Any, **kwargs: Any) -> Any:
    """Build one SourceReadRequest value through the Data public boundary.

    Args:
        args: The ``args`` argument.
        kwargs: The ``kwargs`` argument.

    Returns:
        The result produced by the operation.
    """
    return _source_contracts.SourceReadRequest(*args, **kwargs)


def build_statement_plan(*args: Any, **kwargs: Any) -> Any:
    """Build one StatementPlan value through the Data public boundary.

    Args:
        args: The ``args`` argument.
        kwargs: The ``kwargs`` argument.

    Returns:
        The result produced by the operation.
    """
    return _persistence_contracts.StatementPlan(*args, **kwargs)


def build_symbol_list_request(*args: Any, **kwargs: Any) -> Any:
    """Build one SymbolListRequest value through the Data public boundary.

    Args:
        args: The ``args`` argument.
        kwargs: The ``kwargs`` argument.

    Returns:
        The result produced by the operation.
    """
    return _symbol_metadata.SymbolListRequest(*args, **kwargs)


def build_symbol_metadata_request(*args: Any, **kwargs: Any) -> Any:
    """Build one SymbolMetadataRequest value through the Data public boundary.

    Args:
        args: The ``args`` argument.
        kwargs: The ``kwargs`` argument.

    Returns:
        The result produced by the operation.
    """
    return _symbol_metadata.SymbolMetadataRequest(*args, **kwargs)


def build_transaction_request(*args: Any, **kwargs: Any) -> Any:
    """Build one TransactionRequest value through the Data public boundary.

    Args:
        args: The ``args`` argument.
        kwargs: The ``kwargs`` argument.

    Returns:
        The result produced by the operation.
    """
    return _persistence_contracts.TransactionRequest(*args, **kwargs)


def build_weekly_holiday(*args: Any, **kwargs: Any) -> Any:
    """Build one WeeklyHoliday value through the Data public boundary.

    Args:
        args: The ``args`` argument.
        kwargs: The ``kwargs`` argument.

    Returns:
        The result produced by the operation.
    """
    return _time_contracts.WeeklyHoliday(*args, **kwargs)


def build_weekly_schedule_definition(*args: Any, **kwargs: Any) -> Any:
    """Build one WeeklyScheduleDefinition value through the Data public boundary.

    Args:
        args: The ``args`` argument.
        kwargs: The ``kwargs`` argument.

    Returns:
        The result produced by the operation.
    """
    return _time_contracts.WeeklyScheduleDefinition(*args, **kwargs)


def build_weekly_schedule_provider(*args: Any, **kwargs: Any) -> Any:
    """Build one WeeklyScheduleProvider value through the Data public boundary.

    Args:
        args: The ``args`` argument.
        kwargs: The ``kwargs`` argument.

    Returns:
        The result produced by the operation.
    """
    return _weekly_schedule.WeeklyScheduleProvider(*args, **kwargs)


def build_volume_request(*args: Any, **kwargs: Any) -> Any:
    """Build one VolumeRequest value through the Data public boundary.

    Args:
        args: The ``args`` argument.
        kwargs: The ``kwargs`` argument.

    Returns:
        The result produced by the operation.
    """
    return _market_requests.VolumeRequest(*args, **kwargs)


def is_data_error(value: BaseException) -> bool:
    """Return whether an exception is a Data-owned boundary error.

    Args:
        value: Exception to inspect.

    Returns:
        Whether ``value`` is an internal Data error without exposing its class.
    """
    return (
        value.__class__.__module__.startswith("app.services.data")
        and value.__class__.__name__ == "DataError"
    )


def is_market_dataset(value: Any) -> bool:
    """Return whether a value is a canonical Data market dataset.

    Args:
        value: The ``value`` argument.

    Returns:
        The result produced by the operation.
    """
    return bool(
        value.__class__.__module__.startswith("app.services.data")
        and value.__class__.__name__ == "MarketDataset"
    )


def is_ohlcv_record(value: Any) -> bool:
    """Return whether a value is a canonical Data OHLCV record.

    Args:
        value: The ``value`` argument.

    Returns:
        The result produced by the operation.
    """
    return bool(
        value.__class__.__module__.startswith("app.services.data")
        and value.__class__.__name__ == "OHLCVRecord"
    )


def is_tick_record(value: Any) -> bool:
    """Return whether a value is a canonical Data tick record.

    Args:
        value: The ``value`` argument.

    Returns:
        The result produced by the operation.
    """
    return bool(
        value.__class__.__module__.startswith("app.services.data")
        and value.__class__.__name__ == "TickRecord"
    )


def is_account_state_snapshot(value: Any) -> bool:
    """Return whether a value is a canonical Data account snapshot.

    Args:
        value: The ``value`` argument.

    Returns:
        The result produced by the operation.
    """
    return bool(
        value.__class__.__module__.startswith("app.services.data")
        and value.__class__.__name__ == "AccountStateSnapshot"
    )


def is_market_context_evidence(value: Any) -> bool:
    """Return whether a value is canonical market-context evidence.

    Args:
        value: The ``value`` argument.

    Returns:
        The result produced by the operation.
    """
    return bool(
        value.__class__.__module__.startswith("app.services.data")
        and value.__class__.__name__ == "MarketContextEvidence"
    )


def is_fx_conversion_evidence(value: Any) -> bool:
    """Check if value is an FXConversionEvidence instance.

    Args:
        value: The ``value`` argument.

    Returns:
        The result produced by the operation.
    """
    return bool(
        value.__class__.__module__.startswith("app.services.data")
        and value.__class__.__name__ == "FXConversionEvidence"
    )


def is_read_only_broker_proxy(value: Any) -> bool:
    """Check if value is a _ReadOnlyBrokerProxy instance.

    Args:
        value: The ``value`` argument.

    Returns:
        The result produced by the operation.
    """
    return bool(
        value.__class__.__module__.startswith("app.services.data")
        and value.__class__.__name__ in ("ReadOnlyBrokerProxy", "_ReadOnlyBrokerProxy")
    )


def get_data_error_manifest() -> dict[str, ErrorDefinition]:
    """Get the immutable Data error manifest catalog.

    Returns:
        The result produced by the operation.
    """
    return dict(DATA_ERROR_MANIFEST)


def get_market_dataset_schema() -> str:
    """Get the canonical MarketDataset schema identifier.

    Returns:
        The result produced by the operation.
    """
    return MARKET_DATASET_SCHEMA


def get_normalization_version() -> str:
    """Get the canonical dataset normalization version.

    Returns:
        The result produced by the operation.
    """
    return NORMALIZATION_VERSION


def get_precision_policies() -> list[str]:
    """Get the list of supported precision policies.

    Returns:
        The result produced by the operation.
    """
    return list(PRECISION_POLICIES)


def get_quality_sample_limit() -> int:
    """Get the quality sample limit.

    Returns:
        The result produced by the operation.
    """
    return QUALITY_SAMPLE_LIMIT


def get_workflow_contexts() -> list[str]:
    """Get the list of valid workflow context names.

    Returns:
        The result produced by the operation.
    """
    return list(WORKFLOW_CONTEXTS)


def get_operation_traits() -> dict[str, OperationTraits]:
    """Get the operation traits mapping catalog.

    Returns:
        The result produced by the operation.
    """
    return dict(OPERATION_TRAITS)


def get_calendar_sites() -> tuple[str, ...]:
    """Get the configured economic calendar sites.

    Returns:
        The result produced by the operation.
    """
    return CALENDAR_SITES


def get_default_minimum_impact() -> str:
    """Get the default minimum economic event impact level.

    Returns:
        The result produced by the operation.
    """
    return str(DEFAULT_MINIMUM_IMPACT.value)


def get_symbol_event_profiles() -> dict[str, SymbolEventProfile]:
    """Get the symbol event profiles dictionary.

    Returns:
        The result produced by the operation.
    """
    return dict(SYMBOL_EVENT_PROFILES)


def get_read_only_broker_methods() -> set[str]:
    """Get the set of permitted read-only broker methods.

    Returns:
        The result produced by the operation.
    """
    return set(READ_ONLY_BROKER_METHODS)


def get_timeframe_manifest() -> dict[str, TimeframeSpec]:
    """Get the timeframe manifest mapping.

    Returns:
        The result produced by the operation.
    """
    return dict(TIMEFRAME_MANIFEST)


def get_forex_named_sessions() -> dict[str, NamedSessionDefinition]:
    """Get the forex named sessions dictionary.

    Returns:
        The result produced by the operation.
    """
    return {s.name: s for s in FOREX_NAMED_SESSIONS}


def get_audit_query_hard_max_limit() -> int:
    """Get the audit query hard max limit.

    Returns:
        The result produced by the operation.
    """
    return AUDIT_QUERY_HARD_MAX_LIMIT


def get_data_migration_steps() -> list[MigrationStep]:
    """Get the ordered sequence of Data migration steps.

    Returns:
        The result produced by the operation.
    """
    return list(DATA_MIGRATION_STEPS)


def get_account_snapshot_schema() -> str:
    """Get the AccountStateSnapshot schema identifier.

    Returns:
        The result produced by the operation.
    """
    return ACCOUNT_SNAPSHOT_SCHEMA


def get_fx_conversion_evidence_schema() -> str:
    """Get the FXConversionEvidence schema identifier.

    Returns:
        The result produced by the operation.
    """
    return FX_CONVERSION_EVIDENCE_SCHEMA


def get_market_context_schema() -> str:
    """Get the MarketContextEvidence schema identifier.

    Returns:
        The result produced by the operation.
    """
    return MARKET_CONTEXT_SCHEMA


def build_migration_step(*args: Any, **kwargs: Any) -> Any:
    """Build one immutable domain migration step.

    Args:
        args: The ``args`` argument.
        kwargs: The ``kwargs`` argument.

    Returns:
        The result produced by the operation.
    """
    from app.services.data.persistence.contracts import MigrationStep

    return MigrationStep(*args, **kwargs)


def build_market_data_request(*args: Any, **kwargs: Any) -> Any:
    """Build a MarketDataRequest instance.

    Args:
        args: The ``args`` argument.
        kwargs: The ``kwargs`` argument.

    Returns:
        The result produced by the operation.
    """
    return MarketDataRequest(*args, **kwargs)


def build_synthetic_request(*args: Any, **kwargs: Any) -> Any:
    """Build a SyntheticRequest instance.

    Args:
        args: The ``args`` argument.
        kwargs: The ``kwargs`` argument.

    Returns:
        The result produced by the operation.
    """
    return SyntheticRequest(*args, **kwargs)


def build_ohlcv_record(*args: Any, **kwargs: Any) -> Any:
    """Build an OHLCVRecord instance.

    Args:
        args: The ``args`` argument.
        kwargs: The ``kwargs`` argument.

    Returns:
        The result produced by the operation.
    """
    return OHLCVRecord(*args, **kwargs)


def build_tick_record(*args: Any, **kwargs: Any) -> Any:
    """Build a TickRecord instance.

    Args:
        args: The ``args`` argument.
        kwargs: The ``kwargs`` argument.

    Returns:
        The result produced by the operation.
    """
    return TickRecord(*args, **kwargs)


def build_spread_record(*args: Any, **kwargs: Any) -> Any:
    """Build a SpreadRecord instance.

    Args:
        args: The ``args`` argument.
        kwargs: The ``kwargs`` argument.

    Returns:
        The result produced by the operation.
    """
    return SpreadRecord(*args, **kwargs)


def build_market_dataset(*args: Any, **kwargs: Any) -> Any:
    """Build a MarketDataset instance.

    Args:
        args: The ``args`` argument.
        kwargs: The ``kwargs`` argument.

    Returns:
        The result produced by the operation.
    """
    return MarketDataset(*args, **kwargs)


def build_data_settings(**kwargs: Any) -> Any:
    """Build one Data runtime-settings value through the public boundary.

    Args:
        kwargs: The ``kwargs`` argument.

    Returns:
        The result produced by the operation.
    """
    from app.services.data._settings import DataSettings

    return DataSettings(**kwargs)


def build_data_quality_report(*args: Any, **kwargs: Any) -> Any:
    """Build one canonical quality-report value.

    Args:
        args: The ``args`` argument.
        kwargs: The ``kwargs`` argument.

    Returns:
        The result produced by the operation.
    """
    return DataQualityReport(*args, **kwargs)


def build_symbol_metadata(*args: Any, **kwargs: Any) -> Any:
    """Build one normalized symbol-metadata value.

    Args:
        args: The ``args`` argument.
        kwargs: The ``kwargs`` argument.

    Returns:
        The result produced by the operation.
    """
    return SymbolMetadata(*args, **kwargs)


def build_source_descriptor(*args: Any, **kwargs: Any) -> Any:
    """Build one governed source descriptor.

    Args:
        args: The ``args`` argument.
        kwargs: The ``kwargs`` argument.

    Returns:
        The result produced by the operation.
    """
    return SourceDescriptor(*args, **kwargs)


def build_source_identity(*args: Any, **kwargs: Any) -> Any:
    """Build one immutable source identity.

    Args:
        args: The ``args`` argument.
        kwargs: The ``kwargs`` argument.

    Returns:
        The result produced by the operation.
    """
    return SourceIdentity(*args, **kwargs)


def build_source_license_policy(*args: Any, **kwargs: Any) -> Any:
    """Build one source-license policy.

    Args:
        args: The ``args`` argument.
        kwargs: The ``kwargs`` argument.

    Returns:
        The result produced by the operation.
    """
    return SourceLicensePolicy(*args, **kwargs)


def build_source_policy_config(*args: Any, **kwargs: Any) -> Any:
    """Build one source-policy configuration.

    Args:
        args: The ``args`` argument.
        kwargs: The ``kwargs`` argument.

    Returns:
        The result produced by the operation.
    """
    return SourcePolicyConfig(*args, **kwargs)


def build_local_market_data_source(*args: Any, **kwargs: Any) -> Any:
    """Build one local read-only market-data source.

    Args:
        args: The ``args`` argument.
        kwargs: The ``kwargs`` argument.

    Returns:
        The result produced by the operation.
    """
    return LocalMarketDataSource(*args, **kwargs)


def build_account_snapshot_request(*args: Any, **kwargs: Any) -> Any:
    """Build an AccountSnapshotRequest instance.

    Args:
        args: The ``args`` argument.
        kwargs: The ``kwargs`` argument.

    Returns:
        The result produced by the operation.
    """
    return AccountSnapshotRequest(*args, **kwargs)


def build_account_state_snapshot(*args: Any, **kwargs: Any) -> Any:
    """Build one normalized account-state snapshot.

    Args:
        args: The ``args`` argument.
        kwargs: The ``kwargs`` argument.

    Returns:
        The result produced by the operation.
    """
    return AccountStateSnapshot(*args, **kwargs)


def build_fx_conversion_request(*args: Any, **kwargs: Any) -> Any:
    """Build an FXConversionRequest instance.

    Args:
        args: The ``args`` argument.
        kwargs: The ``kwargs`` argument.

    Returns:
        The result produced by the operation.
    """
    return FXConversionRequest(*args, **kwargs)


def build_market_context_request(*args: Any, **kwargs: Any) -> Any:
    """Build a MarketContextRequest instance.

    Args:
        args: The ``args`` argument.
        kwargs: The ``kwargs`` argument.

    Returns:
        The result produced by the operation.
    """
    return MarketContextRequest(*args, **kwargs)


def build_audit_event_query(*args: Any, **kwargs: Any) -> Any:
    """Build an AuditEventQuery instance.

    Args:
        args: The ``args`` argument.
        kwargs: The ``kwargs`` argument.

    Returns:
        The result produced by the operation.
    """
    return AuditEventQuery(*args, **kwargs)


def build_audit_event_page(*args: Any, **kwargs: Any) -> Any:
    """Build one bounded audit-event query page.

    Args:
        args: The ``args`` argument.
        kwargs: The ``kwargs`` argument.

    Returns:
        The result produced by the operation.
    """
    return AuditEventPage(*args, **kwargs)


def build_trade_payload(*args: Any, **kwargs: Any) -> Any:
    """Build one TradePayload value through the Data public boundary.

    Args:
        args: The ``args`` argument.
        kwargs: The ``kwargs`` argument.

    Returns:
        The result produced by the operation.
    """
    return _feed_contracts.TradePayload(*args, **kwargs)


def build_depth_update_payload(*args: Any, **kwargs: Any) -> Any:
    """Build one DepthUpdatePayload value through the Data public boundary.

    Args:
        args: The ``args`` argument.
        kwargs: The ``kwargs`` argument.

    Returns:
        The result produced by the operation.
    """
    return _feed_contracts.DepthUpdatePayload(*args, **kwargs)


def build_venue_state_payload(*args: Any, **kwargs: Any) -> Any:
    """Build one VenueStatePayload value through the Data public boundary.

    Args:
        args: The ``args`` argument.
        kwargs: The ``kwargs`` argument.

    Returns:
        The result produced by the operation.
    """
    return _feed_contracts.VenueStatePayload(*args, **kwargs)


def build_halt_payload(*args: Any, **kwargs: Any) -> Any:
    """Build one HaltPayload value through the Data public boundary.

    Args:
        args: The ``args`` argument.
        kwargs: The ``kwargs`` argument.

    Returns:
        The result produced by the operation.
    """
    return _feed_contracts.HaltPayload(*args, **kwargs)


def build_auction_payload(*args: Any, **kwargs: Any) -> Any:
    """Build one AuctionPayload value through the Data public boundary.

    Args:
        args: The ``args`` argument.
        kwargs: The ``kwargs`` argument.

    Returns:
        The result produced by the operation.
    """
    return _feed_contracts.AuctionPayload(*args, **kwargs)


def build_corporate_action_payload(*args: Any, **kwargs: Any) -> Any:
    """Build one CorporateActionPayload value through the Data public boundary.

    Args:
        args: The ``args`` argument.
        kwargs: The ``kwargs`` argument.

    Returns:
        The result produced by the operation.
    """
    return _feed_contracts.CorporateActionPayload(*args, **kwargs)


def build_level1_snapshot_request(*args: Any, **kwargs: Any) -> Any:
    """Build one Level1SnapshotRequest value through the Data public boundary.

    Args:
        args: The ``args`` argument.
        kwargs: The ``kwargs`` argument.

    Returns:
        The result produced by the operation.
    """
    return _level1.Level1SnapshotRequest(*args, **kwargs)


def build_market_snapshot_request(*args: Any, **kwargs: Any) -> Any:
    """Build one MarketSnapshotRequest value through the Data public boundary.

    Args:
        args: The ``args`` argument.
        kwargs: The ``kwargs`` argument.

    Returns:
        The result produced by the operation.
    """
    return _snapshot.MarketSnapshotRequest(*args, **kwargs)


def get_display_asset_classes() -> tuple[str, ...]:
    """Return the supported market-directory asset classes.

    Returns:
        Immutable ordered asset-class tokens.
    """
    return _asset_classifier.DISPLAY_ASSET_CLASSES
