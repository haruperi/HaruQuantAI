"""Run realistic construction and validation examples for DATA contracts."""

import sys
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.services.data.contracts import (
    ACCOUNT_SNAPSHOT_SCHEMA,
    DATA_ERROR_MANIFEST,
    MARKET_DATASET_SCHEMA,
    AccountBalance,
    AccountSnapshotRequest,
    AccountStateSnapshot,
    DataAvailability,
    DataError,
    DataGap,
    DataQualityReport,
    DataRange,
    FXConversionRequest,
    MarketContextRequest,
    MarketDataRequest,
    MarketDataset,
    OHLCVRecord,
    QualityIssue,
    SourceDescriptor,
    SourceLicensePolicy,
    SpreadRecord,
    TickRecord,
)
from app.utils import generate_id, logger

_START = datetime(2026, 7, 1, 12, 0, tzinfo=UTC)
_END = _START + timedelta(minutes=5)
_AVAILABLE = _END + timedelta(seconds=1)


def _quality_report() -> DataQualityReport:
    """Build explicit bounded quality evidence for the examples."""
    logger.info("Building example DATA quality evidence")
    issue = QualityIssue(
        code="MEASURED_GAP",
        severity="warning",
        message="One expected minute was absent from the source",
        field="timestamp",
        affected_count=1,
        samples=("2026-07-01T12:03:00Z",),
        blocking_workflows=("execution_bound",),
    )
    return DataQualityReport(
        quality_status="passed_with_warnings",
        quality_score=Decimal("0.95"),
        issues=(issue,),
        warnings=("Measured gap retained in lineage",),
        record_count=1,
        checked_count=1,
        truncated=False,
        sample_limit=10,
        schema_version="v1",
        generated_at=_AVAILABLE,
    )


def _bar() -> OHLCVRecord:
    """Build one exact normalized OHLCV observation."""
    logger.info("Building example normalized OHLCV record")
    return OHLCVRecord(
        timestamp=_START,
        open=Decimal("100.00"),
        high=Decimal("102.50"),
        low=Decimal("99.75"),
        close=Decimal("101.25"),
        volume=Decimal(1250),
        price_unit="USD",
        volume_unit="shares",
        source="yahoo",
        source_symbol="AAPL",
        source_revision="provider-v1",
        available_at=_AVAILABLE,
    )





def _header(title: str) -> None:
    """Print the header for an example section."""
    print(f"\n{'=' * 100}")
    print(f"--- {title} ---")
    print(f"{'=' * 100}")


def example_fr_data_001_ohlcv_record() -> OHLCVRecord:
    """Construct exact UTC OHLCV evidence from a provider observation."""
    _header("FR-DATA-001: validating a normalized OHLCV observation")
    record = _bar()
    print(f"OHLCV Record close={record.close} timestamp={record.timestamp}")
    return record


def example_fr_data_002_tick_record() -> TickRecord:
    """Construct a genuine two-sided market tick."""
    _header("FR-DATA-002: validating a two-sided tick")
    tick = TickRecord(
        timestamp=_START,
        bid=Decimal("1.08495"),
        ask=Decimal("1.08505"),
        last=Decimal("1.08500"),
        volume=Decimal(2),
        price_unit="USD",
        volume_unit="lots",
        source="mt5-demo",
        source_symbol="EURUSD",
        source_revision="terminal-v1",
        available_at=_AVAILABLE,
    )
    print(f"Tick Record bid={tick.bid} ask={tick.ask} spread={tick.ask - tick.bid}")  # type: ignore[operator]
    return tick


def example_fr_data_003_spread_record() -> SpreadRecord:
    """Construct spread evidence with an explicit unit and scale."""
    _header("FR-DATA-003: validating spread evidence")
    spread = SpreadRecord(
        timestamp=_START,
        spread=Decimal("0.00010"),
        unit="USD",
        scale=5,
        source="mt5-demo",
        source_symbol="EURUSD",
        available_at=_AVAILABLE,
    )
    print(f"Spread Record spread={spread.spread} unit={spread.unit} scale={spread.scale}")
    return spread


def example_fr_data_004_quality_report() -> DataQualityReport:
    """Inspect bounded issue samples and workflow-blocking evidence."""
    _header("FR-DATA-004: inspecting bounded quality evidence")
    report = _quality_report()
    print(f"Quality status={report.quality_status} score={report.quality_score} issues={len(report.issues)}")
    return report


def example_fr_data_005_market_dataset() -> MarketDataset:
    """Package normalized observations without provider-native objects."""
    _header("FR-DATA-005: constructing an immutable market dataset")
    dataset = MarketDataset(
        normalization_version="v1",
        data_kind="bars",
        symbol="AAPL",
        timeframe="M5",
        records=(_bar(),),
        start=_START,
        end=_START,
        available_at=_AVAILABLE,
        record_count=1,
        quality_report=_quality_report(),
        source_metadata={"source_id": "yahoo", "revision": "provider-v1"},
        license_metadata={"status": "approved", "attribution": "Yahoo Finance"},
        cache_status="not_used",
        workflow_context="research",
        precision_policy="decimal_string",
        request_id=generate_id("req"),
    )
    if dataset.schema_id != MARKET_DATASET_SCHEMA:
        raise AssertionError("unexpected market dataset schema")
    print(f"Dataset schema={dataset.schema_id} records={dataset.record_count} symbol={dataset.symbol}")
    return dataset


def example_fr_data_006_market_request() -> MarketDataRequest:
    """Declare a bounded historical request and explicit fallback order."""
    _header("FR-DATA-006: constructing a bounded historical request")
    request = MarketDataRequest(
        source_id="yahoo",
        symbol="AAPL",
        data_kind="bars",
        timeframe="D1",
        start=_START - timedelta(days=30),
        end=_START,
        limit=31,
        use_cache=True,
        cache_ttl_seconds=3600,
        quality_failure_behavior="fail",
        workflow_context="research",
        precision_policy="decimal_string",
        fallback_sources=("local_parquet",),
        source_timezone="America/New_York",
        request_id=generate_id("req"),
    )
    print(f"Market Data Request source={request.source_id} fallbacks={request.fallback_sources}")
    return request


def example_fr_data_007_availability() -> DataAvailability:
    """Represent measured ranges and gaps without loading a full dataset."""
    _header("FR-DATA-007: constructing measured availability evidence")
    availability = DataAvailability(
        source_id="local_parquet",
        symbol="AAPL",
        data_kind="bars",
        timeframe="D1",
        ranges=(DataRange(start=_START - timedelta(days=30), end=_START),),
        gaps=(
            DataGap(start=_START - timedelta(days=10), end=_START - timedelta(days=9)),
        ),
        completeness=Decimal("0.9667"),
        record_count=30,
        source_revision="manifest-sha256",
        source_readiness="production",
        provenance={"index": "AAPL.parquet.manifest.json"},
        request_id=generate_id("req"),
    )
    print(f"Data Availability completeness={availability.completeness} records={availability.record_count}")
    return availability


def example_fr_data_008_account_snapshot() -> AccountStateSnapshot:
    """Construct immutable account evidence that carries an expiry."""
    _header("FR-DATA-008: constructing read-only account evidence")
    request = AccountSnapshotRequest(
        source_id="mt5-demo",
        account_id="demo-account-123",
        max_age_seconds=30,
        request_id=generate_id("req"),
    )
    snapshot = AccountStateSnapshot(
        account_id=request.account_id,
        currency="USD",
        balances=(
            AccountBalance(
                asset="USD",
                total=Decimal(10000),
                available=Decimal(9800),
            ),
        ),
        equity=Decimal("10025.50"),
        margin_used=Decimal(200),
        margin_available=Decimal("9825.50"),
        positions=(),
        orders=(),
        connected=True,
        trading_allowed=True,
        source_id=request.source_id,
        snapshot_at=_START,
        expires_at=_START + timedelta(seconds=request.max_age_seconds),
        request_id=request.request_id,
    )
    if snapshot.schema_id != ACCOUNT_SNAPSHOT_SCHEMA:
        raise AssertionError("unexpected account snapshot schema")
    print(f"Snapshot account={snapshot.account_id} expires={snapshot.expires_at} connected={snapshot.connected}")
    return snapshot


def example_fr_data_010_source_descriptor() -> SourceDescriptor:
    """Declare source readiness, capabilities, and evidence requirements."""
    _header("FR-DATA-010: declaring governed source metadata")
    policy = SourceLicensePolicy(
        source_id="yahoo",
        status="approved",
        permitted_workflows=("research", "backtest", "validation"),
        export_allowed=False,
        retention_days=30,
        attribution_required=True,
        attribution_text="Data supplied by Yahoo Finance",
    )
    descriptor = SourceDescriptor(
        source_id="yahoo",
        readiness="staging",
        capabilities=("bars", "symbol_metadata"),
        requires_credentials=False,
        requires_network=True,
        supports_writes=False,
        schema_version="v1",
        timezone="America/New_York",
        revision="adapter-v1",
        license_policy=policy,
        identity_mapping_revision="mapping-v1",
        promotion_evidence=("real-read-probe",),
    )
    print(f"Source={descriptor.source_id} readiness={descriptor.readiness}")
    return descriptor


def example_fr_data_011_license_policy() -> SourceLicensePolicy:
    """Inspect explicit retention, export, and attribution restrictions."""
    _header("FR-DATA-011: inspecting explicit source license policy")
    policy = example_fr_data_010_source_descriptor().license_policy
    print(f"License status={policy.status} export_allowed={policy.export_allowed} retention_days={policy.retention_days}")
    return policy


def example_fr_data_012_data_error() -> DataError:
    """Handle one failure without exposing unsafe details."""
    _header("FR-DATA-012: constructing a redacted deterministic failure")
    error = DataError(
        "DATA_NOT_FOUND",
        safe_details={"symbol": "AAPL"},
        request_id=generate_id("req"),
    )
    print(f"Failure code={error.code} details={error.safe_details}")
    return error


def example_fr_data_013_error_manifest() -> None:
    """Branch on stable manifest metadata rather than exception prose."""
    _header("FR-DATA-013: inspecting deterministic failure metadata")
    definition = DATA_ERROR_MANIFEST["TIMEOUT"]
    print(f"Failure definition code={definition.code} retryable={definition.retryable} action={definition.operator_action}")


def example_fr_data_075_market_context_request() -> MarketContextRequest:
    """Request only the market-context facts required by a consumer."""
    _header("FR-DATA-075: constructing a bounded market-context request")
    request = MarketContextRequest(
        symbol="EURUSD",
        as_of=_START,
        max_age_seconds=60,
        requested_evidence=("session", "spread", "volatility"),
        timezone="Europe/London",
        request_id=generate_id("req"),
    )
    print(f"Requested evidence={request.requested_evidence} timezone={request.timezone}")
    return request


def example_fr_data_078_fx_request() -> FXConversionRequest:
    """Declare a bounded, acyclic FX conversion-path policy."""
    _header("FR-DATA-078: constructing exact FX evidence policy")
    request = FXConversionRequest(
        source_currency="EUR",
        target_currency="JPY",
        as_of=_START,
        max_age_seconds=60,
        allowed_intermediates=("USD",),
        max_legs=2,
        path_policy_id="risk-approved-fx-paths",
        path_policy_version="v1",
        request_id=generate_id("req"),
    )
    print(f"FX path permits intermediates={request.allowed_intermediates} max_legs={request.max_legs}")
    return request


if __name__ == "__main__":
    example_fr_data_001_ohlcv_record()
    example_fr_data_002_tick_record()
    example_fr_data_003_spread_record()
    example_fr_data_004_quality_report()
    example_fr_data_005_market_dataset()
    example_fr_data_006_market_request()
    example_fr_data_007_availability()
    example_fr_data_008_account_snapshot()
    example_fr_data_010_source_descriptor()
    example_fr_data_011_license_policy()
    example_fr_data_012_data_error()
    example_fr_data_013_error_manifest()
    example_fr_data_075_market_context_request()
    example_fr_data_078_fx_request()
