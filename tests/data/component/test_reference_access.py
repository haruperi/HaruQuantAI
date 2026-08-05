"""Component tests for symbol reference and availability orchestration."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace

import pytest
from app.services.data.contracts import (
    DataQualityReport,
    MarketDataset,
    OHLCVRecord,
)
from app.services.data.contracts.responses import unwrap_data_response
from app.services.data.market_data.requests import (
    AvailabilityRequest,
    MarketDataRequest,
)
from app.services.data.market_data.symbol_discovery import (
    discover_symbols,
    fetch_symbol_metadata,
    inspect_availability,
)
from app.services.data.market_data.symbol_metadata import (
    SymbolListRequest,
    SymbolMetadata,
    SymbolMetadataRequest,
)
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
        quality_status="perfect",
        quality_decision="accepted",
        quality_score=Decimal(100),
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

_REQ_ID = "req-00000000-0000-4000-8000-000000000000"


def _unwrap(response):
    """Extract the raw payload from a StandardResponse for assertions."""
    return unwrap_data_response(
        response, operation="data.market_data.test", request_id=_REQ_ID
    )


def _configure_database(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("DATABASE_URL", "sqlite:///test_reference_access.sqlite3")
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    monkeypatch.setenv("SQLITE_BUSY_TIMEOUT_SECONDS", "1.0")
    monkeypatch.setenv("WRITE_LOCK_LEASE_SECONDS", "30")
    from app.services.data.persistence.migrations import run_data_migrations

    run_data_migrations(
        "req-60d56de3ff8bb20750e936377422e90f785e5ecfef35c15300af6cade7ff5e9d"
    )


@pytest.fixture(autouse=True)
def _setup(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    _reset_registry()
    _reset_policy_registry()
    _configure_database(monkeypatch, tmp_path)
    raw_root = tmp_path / "data" / "raw"
    raw_root.mkdir(parents=True, exist_ok=True)
    register_local_test_source(raw_root, ("AAPL", "MSFT", "TSLA"))


def test_discover_symbols_cursor_is_stable(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Verify symbol paginated discovery handles stable cursor pagination."""
    (tmp_path / "data" / "raw").mkdir(parents=True, exist_ok=True)

    # Save multiple dummy symbols
    (tmp_path / "data" / "raw" / "AAPL.csv").write_text("dummy")
    (tmp_path / "data" / "raw" / "MSFT.csv").write_text("dummy")
    (tmp_path / "data" / "raw" / "TSLA.csv").write_text("dummy")

    req_page1 = SymbolListRequest(
        source_id="local_csv",
        limit=1,
        request_id="req-6db5d884ba341a7b10e272a1ae77bbc1ccb6b53a6ff1a75c88fc511a799b06bd",
    )
    page1 = _unwrap(discover_symbols(req_page1))
    assert len(page1.items) == 1
    assert page1.next_cursor == "AAPL"

    req_page2 = SymbolListRequest(
        source_id="local_csv",
        cursor=page1.next_cursor,
        limit=1,
        request_id="req-d88461f85431a9aff500fb7615831c70cb225248b12d466b15eb9067a414e18b",
    )
    page2 = _unwrap(discover_symbols(req_page2))
    assert len(page2.items) == 1
    assert page2.items[0] == "MSFT"


def test_fetch_metadata_preserves_unknown_fields(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Verify metadata retrieval is asset-aware and lists missing fields."""
    (tmp_path / "data" / "raw").mkdir(parents=True, exist_ok=True)
    (tmp_path / "data" / "raw" / "AAPL.csv").write_text("dummy")

    req = SymbolMetadataRequest(
        source_id="local_csv",
        symbol="AAPL",
        request_id="req-539196dd947fb4026e1c6e1c9f5b443b4e9b22c247c95f32667f30977d85b3f3",
    )
    meta = _unwrap(fetch_symbol_metadata(req))
    assert meta.canonical_symbol == "AAPL"
    assert "digits" in meta.missing_fields or meta.digits is None


def test_availability_never_hardcodes_ready(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Verify completeness and gaps are calculated dynamically from manifests."""
    (tmp_path / "data" / "raw").mkdir(parents=True, exist_ok=True)

    # Save a dataset with exact boundaries
    dataset = make_dataset().model_copy(
        update={
            "symbol": "AAPL",
            "start": START,
            "end": END,
            "records": (
                make_dataset()
                .records[0]
                .model_copy(
                    update={
                        "timestamp": START,
                        "available_at": END + timedelta(seconds=1),
                    }
                ),
                make_dataset()
                .records[0]
                .model_copy(
                    update={
                        "timestamp": END,
                        "available_at": END + timedelta(seconds=1),
                    }
                ),
            ),
            "record_count": 2,
            "available_at": END + timedelta(seconds=1),
            "quality_report": make_quality(count=2).model_copy(
                update={"generated_at": END + timedelta(seconds=1)}
            ),
            "request_id": (
                "req-9c636641eff0a51c8f89ca4c5cffc7c489601541600e326818191b669dd0af71"
            ),
        }
    )
    save_req = DatasetSaveRequest(
        dataset=dataset,
        relative_path=Path("data/raw/AAPL.csv"),
        format="csv",
        overwrite=True,
        request_id="req-9c636641eff0a51c8f89ca4c5cffc7c489601541600e326818191b669dd0af71",
    )
    save_dataset(save_req)

    # Inspect availability with a range exceeding the dataset range
    query_start = START - timedelta(hours=1)
    query_end = END + timedelta(hours=1)
    avail_req = AvailabilityRequest(
        source_id="local_csv",
        symbol="AAPL",
        data_kind="ohlcv",
        timeframe="1m",
        start=query_start,
        end=query_end,
        max_probe_records=1000,
        request_id="req-a7568abaa3e3b459d8ea90f379a8f8436241a8eb8a75133827e845001c5df427",
    )

    avail = _unwrap(inspect_availability(avail_req))
    assert avail.completeness < Decimal("1.0")
    assert len(avail.gaps) == 2
    assert avail.gaps[0].start == query_start
    assert avail.gaps[0].end == START
    assert avail.gaps[1].start == END
    assert avail.gaps[1].end == query_end


def test_provider_availability_uses_bounded_observed_probe(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Provider availability derives its range from one bounded canonical read."""
    request_id = generate_id("req")
    descriptor = SourceDescriptor(
        source_id="binance_spot",
        readiness="staging",
        capabilities=("bars",),
        requires_credentials=False,
        requires_network=True,
        supports_writes=False,
        schema_version="v1",
        timezone="UTC",
        revision="descriptor-v1",
        license_policy=SourceLicensePolicy(
            source_id="binance_spot",
            status="restricted",
            permitted_workflows=("research",),
            export_allowed=False,
            attribution_required=False,
        ),
        identity_mapping_revision="provider-confirmed-v1",
    )
    first = make_dataset().records[0]
    second = first.model_copy(
        update={"timestamp": END, "available_at": END + timedelta(seconds=1)}
    )
    dataset = make_dataset().model_copy(
        update={
            "symbol": "BTCUSDT",
            "timeframe": "H1",
            "records": (first, second),
            "start": START,
            "end": END,
            "record_count": 2,
            "available_at": END + timedelta(seconds=1),
            "quality_report": make_quality(count=2).model_copy(
                update={"generated_at": END + timedelta(seconds=1)}
            ),
            "source_metadata": {
                "source_id": "binance_spot",
                "source_revision": "binance-adapter-v1",
            },
            "request_id": request_id,
        }
    )
    captured: list[MarketDataRequest] = []

    def fetch(probe: MarketDataRequest) -> MarketDataset:
        captured.append(probe)
        return dataset

    register_source(
        descriptor,
        factory=lambda *_args: SimpleNamespace(fetch_market_dataset=fetch),
        identities=(
            SourceIdentity(
                source_id="binance_spot",
                canonical_symbol="BTCUSDT",
                friendly_name="BTCUSDT",
                provider_symbol="BTCUSDT",
                mapping_revision="provider-confirmed-v1",
                provenance={"method": "unit_test"},
                request_id=request_id,
            ),
        ),
    )
    from app.services.data.sources.policy import (
        SourcePolicyConfig,
        register_source_policy,
    )

    register_source_policy(
        SourcePolicyConfig(
            source_id="binance_spot",
            rate_limit=10,
            rate_window_seconds=1,
            breaker_failure_threshold=5,
            breaker_recovery_seconds=60,
        )
    )
    monkeypatch.setattr(
        "app.services.data.sources.composition.ensure_storage",
        lambda _request_id: None,
    )
    monkeypatch.setattr(
        "app.services.data.sources.composition.ensure_identity",
        lambda _source_id, _symbol, _request_id: None,
    )
    monkeypatch.setattr(
        "app.services.data.market_data.pipeline._fetch_market_dataset_raw",
        fetch,
    )

    request = AvailabilityRequest(
        source_id="binance_spot",
        symbol="BTCUSDT",
        data_kind="ohlcv",
        timeframe="H1",
        start=START - timedelta(hours=1),
        end=END + timedelta(hours=1),
        max_probe_records=2,
        request_id=request_id,
    )

    availability = _unwrap(inspect_availability(request))

    assert len(captured) == 1
    assert captured[0].limit == 2
    assert captured[0].use_cache is False
    assert availability.record_count == 2
    assert availability.source_revision == "binance-adapter-v1"
    assert availability.source_readiness == "staging"
    assert availability.completeness == Decimal(1) / Decimal(3)
    assert availability.provenance["inspection_method"] == "bounded_provider_probe"
    assert availability.provenance["probe_limit_reached"] == "true"
    assert len(availability.gaps) == 2


def test_reference_limits_are_validated_at_call_time(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Reject malformed configuration before resolving a source."""
    monkeypatch.setenv("SYMBOL_LIST_MAX_LIMIT", "invalid")
    request = SymbolListRequest(
        source_id="local_csv",
        limit=1,
        request_id=(
            "req-3c1a7e2bed217a9dcf951ea33b8dc5aca4230cb80abf292dce3b5078bd3c180d"
        ),
    )
    response = discover_symbols(request)
    assert response.status != "success"
    assert response.error is not None
    assert response.error.code == "INVALID_INPUT"
