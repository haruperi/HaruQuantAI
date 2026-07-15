"""Shared deterministic factories for Data contract tests."""

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

from app.services.data.contracts import (
    DataQualityReport,
    MarketDataset,
    OHLCVRecord,
    SourceDescriptor,
    SourceIdentity,
    SourceLicensePolicy,
    SymbolMetadata,
)
from app.services.data.sources.local import LocalMarketDataSource
from app.services.data.sources.policy import SourcePolicyConfig, register_source_policy
from app.services.data.sources.registry import register_source
from app.utils import AuditEvent, generate_id

START = datetime(2026, 1, 1, tzinfo=UTC)
END = START + timedelta(minutes=1)
AVAILABLE = END + timedelta(seconds=1)


def make_license() -> SourceLicensePolicy:
    """Return an approved research license contract."""
    return SourceLicensePolicy(
        source_id="fixture",
        status="approved",
        permitted_workflows=("research",),
        export_allowed=True,
        attribution_required=False,
    )


def make_bar(*, timestamp: datetime = START) -> OHLCVRecord:
    """Return one exact canonical OHLCV record."""
    return OHLCVRecord(
        timestamp=timestamp,
        open=Decimal("10.0"),
        high=Decimal("11.0"),
        low=Decimal("9.0"),
        close=Decimal("10.5"),
        volume=Decimal(100),
        price_unit="USD",
        volume_unit="shares",
        source="fixture",
        source_symbol="ABC",
        source_revision="rev-1",
        available_at=AVAILABLE,
    )


def make_quality(*, count: int = 1) -> DataQualityReport:
    """Return passing bounded quality evidence."""
    return DataQualityReport(
        quality_status="passed",
        quality_score=Decimal(1),
        issues=(),
        warnings=(),
        record_count=count,
        checked_count=count,
        truncated=False,
        sample_limit=10,
        schema_version="v1",
        generated_at=AVAILABLE,
    )


def make_dataset() -> MarketDataset:
    """Return one immutable provider-neutral market dataset."""
    bar = make_bar()
    return MarketDataset(
        normalization_version="v1",
        data_kind="bars",
        symbol="ABC",
        timeframe="1m",
        records=(bar,),
        start=START,
        end=START,
        available_at=AVAILABLE,
        record_count=1,
        quality_report=make_quality(),
        source_metadata={"source": "fixture"},
        license_metadata={"status": "approved"},
        cache_status="miss",
        workflow_context="research",
        precision_policy="decimal_string",
        request_id="req-491e2e64ca4b441c7f08620130e0e40d107775c753ca238bea74d87a1dd9f667",
    )


def make_audit_event(*, timestamp: datetime = START) -> AuditEvent:
    """Return one valid Utils-owned audit event."""
    return AuditEvent(
        contract_version="v1",
        schema_id="utils.audit_event.v1",
        event_id=generate_id("evt"),
        timestamp=timestamp,
        domain="data",
        action="read",
        request_id=generate_id("req"),
        correlation_id=generate_id("cor"),
        payload={"source": "fixture"},
    )


def register_local_test_source(
    raw_root: Path,
    symbols: tuple[str, ...],
    *,
    source_id: str = "local_csv",
) -> None:
    """Register one explicitly rooted local source with complete test policy."""
    request_id = generate_id("req")
    metadata = {
        symbol: SymbolMetadata(
            canonical_symbol=symbol,
            provider_symbol=symbol,
            asset_class="equity",
            quote_currency="USD",
            timezone="UTC",
            source_id=source_id,
            revision="metadata-v1",
            retrieved_at=AVAILABLE,
            missing_fields=("base_currency", "digits", "price_step", "quantity_step"),
            request_id=request_id,
        )
        for symbol in symbols
    }
    identities = tuple(
        SourceIdentity(
            source_id=source_id,
            canonical_symbol=symbol,
            friendly_name=symbol,
            provider_symbol=symbol,
            mapping_revision="mapping-v1",
            provenance={"fixture": "explicit"},
            request_id=request_id,
        )
        for symbol in symbols
    )
    descriptor = SourceDescriptor(
        source_id=source_id,
        readiness="production",
        capabilities=("bars", "ticks", "spreads"),
        requires_credentials=False,
        requires_network=False,
        supports_writes=False,
        schema_version="v1",
        timezone="UTC",
        revision="source-v1",
        license_policy=SourceLicensePolicy(
            source_id=source_id,
            status="approved",
            permitted_workflows=(
                "backtest",
                "research",
                "risk",
                "validation",
            ),
            export_allowed=True,
            attribution_required=False,
        ),
        identity_mapping_revision="mapping-v1",
        promotion_evidence=("fixture",),
    )
    register_source(
        descriptor,
        lambda: LocalMarketDataSource(
            source_id=source_id,
            raw_root=raw_root,
            metadata=metadata,
        ),
        identities,
    )
    register_source_policy(
        SourcePolicyConfig(
            source_id=source_id,
            rate_limit=1_000,
            rate_window_seconds=60,
            breaker_failure_threshold=3,
            breaker_recovery_seconds=60,
        )
    )
