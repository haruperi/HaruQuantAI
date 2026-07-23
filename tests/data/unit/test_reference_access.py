"""Unit tests for symbol reference and availability access orchestration."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

import pytest
from app.services.data.contracts import DataError, MarketDataset
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
    SymbolMetadataRequest,
)
from app.services.data.persistence.contracts import DatasetSaveRequest
from app.services.data.persistence.dataset_writer import save_dataset
from app.services.data.sources.contracts import SourceDescriptor, SourceLicensePolicy
from app.services.data.sources.policy import _reset_policy_registry
from app.services.data.sources.registry import _reset_registry
from app.utils import generate_id

from tests.data.helpers import make_dataset, make_quality, register_local_test_source

START = datetime(2026, 1, 1, tzinfo=UTC)
END = START + timedelta(hours=1)


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
    page1 = discover_symbols(req_page1)
    assert len(page1.items) == 1
    assert page1.next_cursor == "AAPL"

    req_page2 = SymbolListRequest(
        source_id="local_csv",
        cursor=page1.next_cursor,
        limit=1,
        request_id="req-d88461f85431a9aff500fb7615831c70cb225248b12d466b15eb9067a414e18b",
    )
    page2 = discover_symbols(req_page2)
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
    meta = fetch_symbol_metadata(req)
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

    avail = inspect_availability(avail_req)
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
    monkeypatch.setattr(
        "app.services.data.market_data.symbol_discovery.get_source_descriptor",
        lambda _source_id: descriptor,
    )
    monkeypatch.setattr(
        "app.services.data.market_data.symbol_discovery.ensure_storage",
        lambda _request_id: None,
    )
    monkeypatch.setattr(
        "app.services.data.market_data.symbol_discovery.ensure_identity",
        lambda _source_id, _symbol, _request_id: None,
    )

    def fetch(probe: MarketDataRequest) -> MarketDataset:
        captured.append(probe)
        return dataset

    monkeypatch.setattr(
        "app.services.data.market_data.pipeline.fetch_market_dataset",
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

    availability = inspect_availability(request)

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
    with pytest.raises(DataError) as captured:
        discover_symbols(request)
    assert captured.value.code == "INVALID_INPUT"
