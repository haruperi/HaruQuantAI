"""Contract builders bound to the new ``models`` package.

``CAP-DATA-026`` Phase 2 exposed a coexistence hazard that Phase 1 could not: while
``contracts`` and ``models`` both define ``MarketDataset``, they are two distinct
Python classes with identical schemas. Pydantic validates by type identity, so a
legacy-built dataset is rejected by a new-package request and vice versa.

``tests/data/helpers.py`` keeps building legacy contracts for the legacy tests. This
module is its mirror for tests targeting the new packages. Both disappear into one
helper in Phase 11, when the legacy package is deleted.
"""

from datetime import UTC, datetime, timedelta
from decimal import Decimal

from app.services.data.contracts import (
    DataQualityReport,
    MarketDataset,
    OHLCVRecord,
)
from app.services.data.sources.contracts import (
    SourceLicensePolicy,
)
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
