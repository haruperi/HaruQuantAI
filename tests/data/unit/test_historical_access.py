"""Unit tests for historical data access orchestration."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

import pytest
from app.services.data.contracts import (
    DataError,
    DataQualityReport,
    MarketDataset,
    OHLCVRecord,
)
from app.services.data.contracts.responses import unwrap_data_response
from app.services.data.market_data.pipeline import fetch_market_dataset
from app.services.data.market_data.requests import MarketDataRequest
from app.services.data.market_data.symbol_metadata import SymbolMetadata
from app.services.data.persistence.contracts import DatasetSaveRequest
from app.services.data.persistence.dataset_writer import save_dataset
from app.services.data.sources.contracts import (
    SourceDescriptor,
    SourceIdentity,
    SourceLicensePolicy,
)
from app.services.data.sources.local_adapter import LocalMarketDataSource
from app.services.data.sources.policy import (
    SourcePolicyConfig,
    _reset_policy_registry,
    register_source_policy,
)
from app.services.data.sources.registry import _reset_registry, register_source
from app.utils import generate_id

# --- Inlined fixtures (legacy helpers.py) --------------------------------------
# The original shared helper built contracts DIRECTLY via the contract classes
# (NOT via public builders). This exact behavior is preserved here.

START_FIXTURE = datetime(2026, 1, 1, tzinfo=UTC)
END_FIXTURE = START_FIXTURE + timedelta(minutes=1)
AVAILABLE_FIXTURE = END_FIXTURE + timedelta(seconds=1)


def make_bar(timestamp=START_FIXTURE):
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
        available_at=timestamp + timedelta(seconds=1),
    )


def make_quality(count=1):
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
        generated_at=AVAILABLE_FIXTURE,
    )


def make_dataset():
    """Return one immutable provider-neutral market dataset."""
    bar = make_bar()
    return MarketDataset(
        normalization_version="v1",
        data_kind="bars",
        symbol="ABC",
        timeframe="1m",
        records=(bar,),
        start=START_FIXTURE,
        end=START_FIXTURE,
        available_at=AVAILABLE_FIXTURE,
        record_count=1,
        quality_report=make_quality(),
        source_metadata={"source": "fixture"},
        license_metadata={"status": "approved"},
        cache_status="miss",
        workflow_context="research",
        precision_policy="decimal_string",
        request_id="req-491e2e64ca4b441c7f08620130e0e40d107775c753ca238bea74d87a1dd9f667",
    )


def register_local_test_source(raw_root, symbols, source_id="local_csv"):
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
            retrieved_at=AVAILABLE_FIXTURE,
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
            permitted_workflows=("backtest", "research", "risk", "validation"),
            export_allowed=True,
            attribution_required=False,
        ),
        identity_mapping_revision="mapping-v1",
        promotion_evidence=("fixture",),
    )
    register_source(
        descriptor,
        lambda: LocalMarketDataSource(
            source_id=source_id, raw_root=raw_root, metadata=metadata
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


# --- Test local constants ------------------------------------------------------

START = datetime(2026, 1, 1, tzinfo=UTC)
END = START + timedelta(hours=1)


def _unwrap(response):
    return unwrap_data_response(
        response,
        operation="data.persistence.test",
        request_id="req-00000000-0000-4000-8000-000000000000",
    )


def test_serve_stale_is_rejected_outside_research() -> None:
    """FR-DATA-107 limits stale serving to the research workflow."""
    with pytest.raises(DataError) as captured:
        MarketDataRequest(
            source_id="fixture",
            symbol="EURUSD",
            data_kind="bars",
            timeframe="M1",
            limit=1,
            use_cache=True,
            stale_cache_policy="serve_stale",
            quality_failure_behavior="reject",
            workflow_context="validation",
            precision_policy="decimal_string",
            request_id=(
                "req-9456bdfa12ea76959c94a3572f5d91c73d838622df0a8d9b4e815c276c6b7880"
            ),
        )
    assert captured.value.code == "INVALID_INPUT"


def _configure_database(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("DATABASE_URL", "sqlite:///test_historical_access.sqlite3")
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    monkeypatch.setenv("SQLITE_BUSY_TIMEOUT_SECONDS", "1.0")
    monkeypatch.setenv("WRITE_LOCK_LEASE_SECONDS", "30")
    from app.services.data.persistence.migrations import run_data_migrations

    _unwrap(
        run_data_migrations(
            "req-60d56de3ff8bb20750e936377422e90f785e5ecfef35c15300af6cade7ff5e9d"
        )
    )


@pytest.fixture(autouse=True)
def _setup(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    _reset_registry()
    _reset_policy_registry()
    _configure_database(monkeypatch, tmp_path)


def test_fetch_market_dataset_reports_actual_source(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Verify source reporting and multi-million-bar request acceptance."""
    raw_root = tmp_path / "data" / "raw"
    raw_root.mkdir(parents=True, exist_ok=True)
    register_local_test_source(raw_root, ("AAPL",))

    dataset = make_dataset().model_copy(
        update={
            "symbol": "AAPL",
            "records": (
                make_dataset()
                .records[0]
                .model_copy(
                    update={
                        "source": "local_csv",
                        "source_symbol": "AAPL",
                        "timestamp": START,
                    }
                ),
            ),
            "start": START,
            "end": START,
            "request_id": (
                "req-9e79c6ea45b572dd655e077ea534a48a4593ad8eacf1dbd3edfe0d4dc6bb2859"
            ),
        }
    )

    save_req = DatasetSaveRequest(
        dataset=dataset,
        relative_path=Path("data/raw/AAPL.csv"),
        format="csv",
        overwrite=True,
        request_id="req-9e79c6ea45b572dd655e077ea534a48a4593ad8eacf1dbd3edfe0d4dc6bb2859",
    )
    _unwrap(save_dataset(save_req))

    # 1. Successful retrieval
    req = MarketDataRequest(
        source_id="local_csv",
        symbol="AAPL",
        data_kind="bars",
        timeframe="1m",
        start=START,
        end=END,
        limit=10,
        use_cache=False,
        quality_failure_behavior="warn",
        workflow_context="research",
        precision_policy="decimal_string",
        request_id="req-12273c6b83cd2187ad2952ac03f30810a02043fe67f88d81fa02ef4053aa64e4",
    )

    res = _unwrap(fetch_market_dataset(req))
    assert isinstance(res, MarketDataset)
    assert res.symbol == "AAPL"
    assert res.records[0].source == "local_csv"

    # 2. OHLCV requests are not capped by an app-wide record-count limit.
    large_req = req.model_copy(update={"limit": 8_000_000})
    large_result = _unwrap(fetch_market_dataset(large_req))
    assert isinstance(large_result, MarketDataset)
    assert large_result.records
