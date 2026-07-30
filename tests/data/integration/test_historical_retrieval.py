"""Integration evidence for WF-DATA-007 recoverable historical backfill."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

import pytest
from app.services.data import (
    build_data_quality_report,
    build_data_settings,
    build_dataset_save_request,
    build_job_definition,
    build_job_status_request,
    build_local_market_data_source,
    build_market_dataset,
    build_ohlcv_record,
    build_source_descriptor,
    build_source_identity,
    build_source_license_policy,
    build_source_policy_config,
    build_symbol_metadata,
    create_data_update_job,
    data_settings_context,
    get_data_update_job_status,
    register_source,
    register_source_policy,
    run_data_migrations,
    run_data_update_job_once,
    save_dataset,
)
from app.utils import generate_id

START = datetime(2026, 1, 1, tzinfo=UTC)
END = START + timedelta(minutes=1)
AVAILABLE = END + timedelta(seconds=1)


def make_bar(timestamp=START):
    """Return one exact canonical OHLCV record."""
    return build_ohlcv_record(
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
    return build_data_quality_report(
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


def make_dataset():
    """Return one immutable provider-neutral market dataset."""
    bar = make_bar()
    return build_market_dataset(
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


def register_local_test_source(raw_root, symbols, source_id="local_csv"):
    """Register one explicitly rooted local source with complete test policy."""
    request_id = generate_id("req")
    metadata = {
        symbol: build_symbol_metadata(
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
        build_source_identity(
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
    descriptor = build_source_descriptor(
        source_id=source_id,
        readiness="production",
        capabilities=("bars", "ticks", "spreads"),
        requires_credentials=False,
        requires_network=False,
        supports_writes=False,
        schema_version="v1",
        timezone="UTC",
        revision="source-v1",
        license_policy=build_source_license_policy(
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
        lambda: build_local_market_data_source(
            source_id=source_id, raw_root=raw_root, metadata=metadata
        ),
        identities,
    )
    register_source_policy(
        build_source_policy_config(
            source_id=source_id,
            rate_limit=1_000,
            rate_window_seconds=60,
            breaker_failure_threshold=3,
            breaker_recovery_seconds=60,
        )
    )


@pytest.fixture(autouse=True)
def isolated_runtime(monkeypatch: pytest.MonkeyPatch) -> None:
    """Reset process-local source composition state around the workflow."""
    for target in (
        "app.services.data.sources.registry._registry",
        "app.services.data.sources.registry._instances",
        "app.services.data.sources.registry._identities",
        "app.services.data.sources.policy._policy_configs",
    ):
        monkeypatch.setattr(target, {})


def test_wf_data_007_commits_data_and_resumable_checkpoint(tmp_path: Path) -> None:
    """Run retrieval through a real local source into a durable job checkpoint."""
    root = tmp_path.resolve()
    raw_root = root / "data" / "raw"
    raw_root.mkdir(parents=True)
    settings = build_data_settings(
        database_url="sqlite:///workflow.sqlite3",
        data_dir=root,
        sqlite_busy_timeout_seconds=1.5,
        write_lock_lease_seconds=30.0,
        approved_storage_roots=(Path("data/raw"),),
    )
    request_id = generate_id("req")

    with data_settings_context(settings):
        mig_res = run_data_migrations(request_id)
        assert mig_res.status == "success"
        save_res = save_dataset(
            build_dataset_save_request(
                dataset=make_dataset().model_copy(update={"request_id": request_id}),
                relative_path=Path("data/raw/ABC_1m.csv"),
                format="csv",
                overwrite=False,
                request_id=request_id,
            )
        )
        assert save_res.status == "success", f"save_dataset failed: {save_res.error}"
        register_local_test_source(raw_root, ("ABC",), source_id="local_csv")
        created = create_data_update_job(
            build_job_definition(
                job_id="wf-data-007",
                source_id="local_csv",
                symbols=("ABC",),
                timeframes=("1m",),
                data_kinds=("ohlcv",),
                start=START,
                end=END,
                interval_seconds=60,
                enabled=True,
                created_at=START - timedelta(minutes=1),
                request_id=request_id,
            ),
            request_id=request_id,
        )
        result = run_data_update_job_once("wf-data-007", request_id=request_id)
        status = get_data_update_job_status(
            build_job_status_request(job_id="wf-data-007", request_id=request_id)
        )

    assert created.state == "created"
    assert result.state == "succeeded"
    assert result.committed_chunks == 1
    assert result.record_count == 1
    assert result.last_checkpoint is not None
    assert (tmp_path / result.last_checkpoint).is_file()
    assert (
        (tmp_path / result.last_checkpoint)
        .with_suffix(".parquet.manifest.json")
        .is_file()
    )
    assert status.last_run_status == "succeeded"
    assert status.last_checkpoint == result.last_checkpoint
