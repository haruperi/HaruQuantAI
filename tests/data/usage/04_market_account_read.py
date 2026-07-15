"""Run market and account evidence read-orchestration examples."""

import sys
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from tempfile import TemporaryDirectory

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.services.data.access import (
    discover_symbols,
    fetch_historical_volume,
    fetch_market_dataset,
    fetch_symbol_metadata,
    get_current_schedule,
    get_fx_conversion_evidence,
    get_market_context_evidence,
    inspect_availability,
)
from app.services.data.config import DataSettings, data_settings_context
from app.services.data.contracts import (
    AvailabilityRequest,
    DataQualityReport,
    DatasetSaveRequest,
    FXConversionRequest,
    FXRateLeg,
    MarketContextEvidence,
    MarketContextRequest,
    MarketDataRequest,
    MarketDataset,
    MarketSchedule,
    OHLCVRecord,
    ScheduleRequest,
    SessionWindow,
    SourceDescriptor,
    SourceIdentity,
    SourceLicensePolicy,
    SymbolListRequest,
    SymbolMetadata,
    SymbolMetadataRequest,
    VolumeRequest,
)
from app.services.data.sources import register_source
from app.services.data.sources.local import LocalMarketDataSource
from app.services.data.sources.policy import SourcePolicyConfig, register_source_policy
from app.services.data.storage.datasets import save_dataset
from app.services.data.storage.migrations import run_data_migrations
from app.utils import generate_id, logger

_SOURCE_ID = "local_usage_csv"
_SYMBOL = "AAPL"
_START = datetime(2026, 7, 1, 13, 30, tzinfo=UTC)
_END = _START + timedelta(minutes=1)
_AVAILABLE = _END + timedelta(seconds=1)


def _configure_environment(root: Path) -> None:
    """Configure and migrate isolated state for read orchestration."""
    logger.info("Configuring isolated DATA access state under %s", root)
    for relative in ("data/raw", "data/processed", "data/cache", "artifacts/data"):
        (root / relative).mkdir(parents=True, exist_ok=True)
    run_data_migrations(generate_id("req"))


def _quality() -> DataQualityReport:
    """Build clean quality evidence for the local example dataset."""
    logger.info("Building access example quality evidence")
    return DataQualityReport(
        quality_status="passed",
        quality_score=Decimal(1),
        issues=(),
        warnings=(),
        record_count=2,
        checked_count=2,
        truncated=False,
        sample_limit=10,
        schema_version="v1",
        generated_at=_AVAILABLE,
    )


def _dataset() -> MarketDataset:
    """Build two genuine normalized minute bars for a local source."""
    logger.info("Building local historical AAPL bars")
    records = tuple(
        OHLCVRecord(
            timestamp=_START + timedelta(minutes=index),
            open=Decimal("210.00") + index,
            high=Decimal("211.00") + index,
            low=Decimal("209.50") + index,
            close=Decimal("210.50") + index,
            volume=Decimal(5000) + (index * 500),
            price_unit="USD",
            volume_unit="shares",
            source=_SOURCE_ID,
            source_symbol=_SYMBOL,
            source_revision="download-v1",
            available_at=_AVAILABLE,
        )
        for index in range(2)
    )
    return MarketDataset(
        normalization_version="v1",
        data_kind="bars",
        symbol=_SYMBOL,
        timeframe="M1",
        records=records,
        start=records[0].timestamp,
        end=records[-1].timestamp,
        available_at=_AVAILABLE,
        record_count=len(records),
        quality_report=_quality(),
        source_metadata={"source_id": _SOURCE_ID, "revision": "download-v1"},
        license_metadata={"status": "approved"},
        cache_status="not_used",
        workflow_context="research",
        precision_policy="decimal_string",
        request_id=generate_id("req"),
    )


def _register_local_source(root: Path) -> None:
    """Persist sample data and register an explicitly rooted local source."""
    logger.info("Registering explicitly rooted local historical data")
    dataset = _dataset()
    save_dataset(
        DatasetSaveRequest(
            dataset=dataset,
            relative_path=Path(f"data/raw/{_SYMBOL}.csv"),
            format="csv",
            overwrite=True,
            request_id=dataset.request_id,
        )
    )
    metadata = SymbolMetadata(
        canonical_symbol=_SYMBOL,
        provider_symbol=_SYMBOL,
        asset_class="equity",
        base_currency="USD",
        quote_currency=None,
        digits=2,
        price_step=Decimal("0.01"),
        quantity_step=Decimal(1),
        timezone="America/New_York",
        source_id=_SOURCE_ID,
        revision="download-v1",
        retrieved_at=_AVAILABLE,
        missing_fields=("quote_currency",),
        request_id=generate_id("req"),
    )
    descriptor = SourceDescriptor(
        source_id=_SOURCE_ID,
        readiness="production",
        capabilities=("bars", "symbol_discovery", "symbol_metadata"),
        requires_credentials=False,
        requires_network=False,
        supports_writes=False,
        schema_version="v1",
        timezone="America/New_York",
        revision="download-v1",
        license_policy=SourceLicensePolicy(
            source_id=_SOURCE_ID,
            status="approved",
            permitted_workflows=("research", "backtest", "validation"),
            export_allowed=True,
            attribution_required=False,
        ),
        identity_mapping_revision="mapping-v1",
        promotion_evidence=("manifest-verified",),
    )
    identity = SourceIdentity(
        source_id=_SOURCE_ID,
        canonical_symbol=_SYMBOL,
        friendly_name="Apple Inc.",
        provider_symbol=_SYMBOL,
        mapping_revision="mapping-v1",
        provenance={"catalog": "usage-v1"},
        request_id=generate_id("req"),
    )
    register_source(
        descriptor,
        lambda: LocalMarketDataSource(
            source_id=_SOURCE_ID,
            raw_root=(root / "data" / "raw").resolve(),
            metadata={_SYMBOL: metadata},
        ),
        identities=(identity,),
    )
    register_source_policy(
        SourcePolicyConfig(
            source_id=_SOURCE_ID,
            rate_limit=100,
            rate_window_seconds=60,
            breaker_failure_threshold=3,
            breaker_recovery_seconds=30,
        )
    )


def example_fr_data_030_historical_market_read() -> MarketDataset:
    """Read normalized historical bars through policy, cache, and quality gates."""
    logger.info("FR-DATA-030: reading governed historical bars")
    dataset = fetch_market_dataset(
        MarketDataRequest(
            source_id=_SOURCE_ID,
            symbol=_SYMBOL,
            data_kind="bars",
            timeframe="M1",
            start=_START,
            end=_END,
            limit=10,
            use_cache=True,
            cache_ttl_seconds=3600,
            quality_failure_behavior="fail",
            workflow_context="research",
            precision_policy="decimal_string",
            request_id=generate_id("req"),
        )
    )
    logger.info("Retrieved %d normalized bars", dataset.record_count)
    return dataset


def example_fr_data_031_symbol_discovery() -> None:
    """Discover a deterministic bounded page of configured symbols."""
    logger.info("FR-DATA-031: discovering configured symbols")
    page = discover_symbols(
        SymbolListRequest(
            source_id=_SOURCE_ID,
            limit=10,
            request_id=generate_id("req"),
        )
    )
    logger.info("Discovered symbols=%s", page.items)


def example_fr_data_032_symbol_metadata() -> None:
    """Retrieve asset-aware metadata without optimistic defaults."""
    logger.info("FR-DATA-032: reading normalized symbol metadata")
    metadata = fetch_symbol_metadata(
        SymbolMetadataRequest(
            source_id=_SOURCE_ID,
            symbol=_SYMBOL,
            request_id=generate_id("req"),
        )
    )
    logger.info("Metadata digits=%s timezone=%s", metadata.digits, metadata.timezone)


def example_fr_data_033_availability() -> None:
    """Inspect measured range, gap, overlap, and completeness evidence."""
    logger.info("FR-DATA-033: inspecting local historical availability")
    availability = inspect_availability(
        AvailabilityRequest(
            source_id=_SOURCE_ID,
            symbol=_SYMBOL,
            data_kind="ohlcv",
            timeframe="M1",
            start=_START,
            end=_END,
            max_probe_records=100,
            request_id=generate_id("req"),
        )
    )
    logger.info(
        "Availability records=%d completeness=%s",
        availability.record_count,
        availability.completeness,
    )


class ExampleCalendar:
    """Caller-injected calendar containing configured current sessions."""

    def get_schedule(
        self,
        *,
        source_id: str,
        symbol: str,
        timezone: str,
        observed_at: datetime,
        request_id: str,
    ) -> MarketSchedule:
        """Return a timezone-labeled current market session."""
        logger.info("Reading configured current session for %s", symbol)
        window = SessionWindow(
            label="regular",
            opens_at=observed_at,
            closes_at=observed_at + timedelta(hours=6, minutes=30),
        )
        return MarketSchedule(
            source_id=source_id,
            symbol=symbol,
            timezone=timezone,
            hours=(window,),
            sessions=(window,),
            observed_at=observed_at,
            request_id=request_id,
        )


class FixedClock:
    """Provide deterministic UTC time for a current-session example."""

    def now(self) -> datetime:
        """Return the fixed usage-example time."""
        logger.info("Reading fixed session-check time")
        return _START


def example_fr_data_034_current_schedule() -> None:
    """Normalize current session windows while preserving requested timezone."""
    logger.info("FR-DATA-034: reading the current configured trading session")
    schedule = get_current_schedule(
        ScheduleRequest(
            source_id=_SOURCE_ID,
            symbol=_SYMBOL,
            view="sessions",
            timezone="America/New_York",
            request_id=generate_id("req"),
        ),
        ExampleCalendar(),
        clock=FixedClock(),
    )
    logger.info(
        "Current sessions=%d timezone=%s", len(schedule.sessions), schedule.timezone
    )


def example_fr_data_035_historical_volume() -> None:
    """Summarize source-native historical volume with declared units."""
    logger.info("FR-DATA-035: summarizing historical volume")
    result = fetch_historical_volume(
        VolumeRequest(
            source_id=_SOURCE_ID,
            symbol=_SYMBOL,
            start=_START,
            end=_END,
            mode="summary",
            limit=10,
            request_id=generate_id("req"),
        )
    )
    if result.summary is None:
        raise AssertionError("volume summary was not returned")
    logger.info("Historical volume total=%s", result.summary.total)


class ExampleContextProvider:
    """Caller-injected provider for normalized market-context facts."""

    def get_market_context(
        self, request: MarketContextRequest
    ) -> MarketContextEvidence:
        """Return policy-neutral, explicitly incomplete market context."""
        logger.info("Reading policy-neutral market context for %s", request.symbol)
        return MarketContextEvidence(
            symbol=request.symbol,
            session_state="open",
            calendar_state="normal",
            spread=Decimal("0.02"),
            spread_unit="USD",
            liquidity=Decimal(500000),
            volatility=Decimal("0.18"),
            correlations={},
            crisis_flags=(),
            timezone=request.timezone,
            as_of=request.as_of,
            expires_at=request.as_of + timedelta(seconds=request.max_age_seconds),
            provenance={"source": _SOURCE_ID},
            missing_fields=(),
            request_id=request.request_id,
        )


def example_fr_data_076_market_context_evidence() -> None:
    """Acquire context facts without producing a Risk verdict."""
    logger.info("FR-DATA-076: acquiring policy-neutral market context")
    evidence = get_market_context_evidence(
        MarketContextRequest(
            symbol=_SYMBOL,
            as_of=_START,
            max_age_seconds=60,
            requested_evidence=(
                "session",
                "calendar",
                "spread",
                "liquidity",
                "volatility",
            ),
            timezone="America/New_York",
            request_id=generate_id("req"),
        ),
        ExampleContextProvider(),
    )
    logger.info("Context session=%s spread=%s", evidence.session_state, evidence.spread)


class ExampleFXProvider:
    """Caller-injected exact FX-rate provider."""

    def get_rate_leg(
        self,
        *,
        source_currency: str,
        target_currency: str,
        as_of: datetime,
        request_id: str,
    ) -> FXRateLeg:
        """Return one fresh, exact, provenanced rate leg."""
        logger.info(
            "Reading FX leg %s/%s for %s", source_currency, target_currency, request_id
        )
        return FXRateLeg(
            source_currency=source_currency,
            target_currency=target_currency,
            rate=Decimal("0.92"),
            source_id=_SOURCE_ID,
            provider_symbol="USDEUR",
            as_of=as_of,
            provenance={"revision": "usage-v1"},
        )


def example_fr_data_079_fx_evidence() -> None:
    """Acquire an exact fresh FX conversion without fabricating a path."""
    logger.info("FR-DATA-079: acquiring exact FX conversion evidence")
    evidence = get_fx_conversion_evidence(
        FXConversionRequest(
            source_currency="USD",
            target_currency="EUR",
            as_of=_START,
            max_age_seconds=60,
            allowed_intermediates=(),
            max_legs=1,
            path_policy_id="direct-only",
            path_policy_version="v1",
            request_id=generate_id("req"),
        ),
        ExampleFXProvider(),
    )
    logger.info("Composite FX rate=%s", evidence.composite_rate)


if __name__ == "__main__":
    with TemporaryDirectory(prefix="haru-data-access-") as directory:
        demo_root = Path(directory)
        settings = DataSettings(
            database_url="sqlite:///usage.sqlite3",
            data_dir=demo_root,
            sqlite_busy_timeout_seconds=1.5,
            write_lock_lease_seconds=30,
        )
        with data_settings_context(settings):
            _configure_environment(demo_root)
            _register_local_source(demo_root)
            example_fr_data_030_historical_market_read()
            example_fr_data_031_symbol_discovery()
            example_fr_data_032_symbol_metadata()
            example_fr_data_033_availability()
            example_fr_data_034_current_schedule()
            example_fr_data_035_historical_volume()
            example_fr_data_076_market_context_evidence()
            example_fr_data_079_fx_evidence()
