"""Unit, contract, and scenario tests for Data Inspection and Retention."""

from datetime import UTC, datetime, timedelta

import pytest
from app.contracts.data.errors import DataFailure
from app.contracts.data.models import (
    ManageRetentionRequest,
    ManageRetentionSuccess,
    RetentionPolicy,
)
from app.services.data.data_inspection_retention.data_inspection_retention import (
    DataInspectionRetentionService,
    DatasetManifest,
    StorageArtifact,
    _generate_uuid7,
    data_collect_reachable_artifacts,
    data_export_data_series,
    data_preview_data_coverage,
    main,
)


def _generate_sample_bars(count: int = 20) -> list[dict[str, str]]:
    return [
        {
            "timestamp": f"2026-08-28T12:{i:02d}:00.000000Z",
            "open": f"{100.0 + i * 0.1:.4f}",
            "high": f"{100.5 + i * 0.1:.4f}",
            "low": f"{99.5 + i * 0.1:.4f}",
            "close": f"{100.2 + i * 0.1:.4f}",
            "volume": "500",
        }
        for i in range(count)
    ]


def test_data_preview_data_coverage() -> None:
    """Verify FR-DATA-PREVIEW_DATA_COVERAGE: coverage, row count, precision, gaps."""
    bars = _generate_sample_bars(20)
    bars.append(
        {
            "timestamp": "2026-08-28T13:00:00.000000Z",
            "open": "102.5000",
            "high": "103.0000",
            "low": "102.0000",
            "close": "102.8000",
            "volume": "600",
        }
    )

    res = data_preview_data_coverage(
        bars, limit=5, max_preview_limit=10, expected_step_seconds=60.0
    )
    assert res.row_count == 21
    assert len(res.preview_rows) == 5
    assert res.start_timestamp == "2026-08-28T12:00:00.000000Z"
    assert res.end_timestamp == "2026-08-28T13:00:00.000000Z"
    assert res.precision_summary.get("open") == 4
    assert len(res.gaps) >= 1
    assert res.gaps[0]["gap_seconds"] > 60.0


def test_data_export_data_series_csv_and_parquet() -> None:
    """Verify FR-DATA-EXPORT_DATA_SERIES: export with explicit metadata."""
    bars = _generate_sample_bars(10)
    csv_res = data_export_data_series(bars, export_format="CSV", timezone="UTC")
    assert csv_res.format == "CSV"
    assert csv_res.row_count == 10
    assert b"HARUQUANT_TIMEZONE=UTC" in csv_res.data_bytes

    parquet_res = data_export_data_series(bars, export_format="PARQUET", timezone="UTC")
    assert parquet_res.format == "PARQUET"
    assert parquet_res.row_count == 10

    assert csv_res.canonical_content_hash == parquet_res.canonical_content_hash


def test_data_export_unsupported_format() -> None:
    """Verify error on unsupported export format."""
    bars = _generate_sample_bars(5)
    with pytest.raises(ValueError, match="Unsupported export format"):
        data_export_data_series(bars, export_format="XML")  # type: ignore[arg-type]


def test_data_collect_reachable_artifacts() -> None:
    """Verify FR-DATA-COLLECT_REACHABLE_ARTIFACTS: reachability and quarantine rules."""
    now = datetime(2026, 8, 28, 12, 0, 0, tzinfo=UTC)
    manifest = DatasetManifest(
        manifest_id="manifest-a",
        referenced_artifact_ids=frozenset({"art-1", "art-2"}),
        committed_at=now - timedelta(days=40),
    )

    artifacts = [
        StorageArtifact("art-1", created_at=now - timedelta(days=50)),
        StorageArtifact("art-2", created_at=now - timedelta(days=20)),
        StorageArtifact("art-3", created_at=now - timedelta(days=10)),
        StorageArtifact("art-4", created_at=now - timedelta(days=35)),
    ]

    gc_res = data_collect_reachable_artifacts(
        [manifest], artifacts, quarantine_days=30, reference_time=now
    )

    assert gc_res.reachable_count == 2
    assert gc_res.quarantined_count == 1
    assert gc_res.collected_count == 1
    assert set(gc_res.preserved_artifact_ids) == {"art-1", "art-2"}
    assert set(gc_res.quarantined_artifact_ids) == {"art-3"}
    assert set(gc_res.collected_artifact_ids) == {"art-4"}


@pytest.mark.asyncio
async def test_service_manage_retention_operations() -> None:
    """Verify DataInspectionRetentionService contract and operation execution."""
    service = DataInspectionRetentionService()
    now = datetime(2026, 8, 28, 12, 0, 0, tzinfo=UTC)

    manifest = DatasetManifest(
        manifest_id="manifest-1",
        referenced_artifact_ids=frozenset({"art-a"}),
        committed_at=now - timedelta(days=60),
    )
    art_a = StorageArtifact("art-a", created_at=now - timedelta(days=60))
    art_b = StorageArtifact("art-b", created_at=now - timedelta(days=40))

    service.register_manifest(manifest)
    service.register_artifact(art_a)
    service.register_artifact(art_b)

    policy = RetentionPolicy(
        policy_id="018f673e-3240-7e33-8a3c-53531b26ea89",
        retention_days=60,
        quarantine_days=30,
    )
    req_def = ManageRetentionRequest(
        request_id="018f673e-3240-7e33-8a3c-53531b26ea90",
        capability_snapshot_id="018f673e-3240-7e33-8a3c-53531b26ea91",
        operation="DEFINE_POLICY",
        policy=policy,
    )
    res_def = await service.manage_retention(req_def)
    assert isinstance(res_def, ManageRetentionSuccess)
    assert res_def.outcome == "SUCCESS"
    assert res_def.policy == policy

    req_col = ManageRetentionRequest(
        request_id="018f673e-3240-7e33-8a3c-53531b26ea92",
        capability_snapshot_id="018f673e-3240-7e33-8a3c-53531b26ea93",
        operation="COLLECT",
    )
    res_col = await service.manage_retention(req_col)
    assert isinstance(res_col, ManageRetentionSuccess)
    assert res_col.outcome == "SUCCESS"
    assert res_col.collected_count == 1


@pytest.mark.asyncio
async def test_service_methods_and_properties() -> None:
    """Verify service properties, preview_coverage, and export_series methods."""
    service = DataInspectionRetentionService()
    assert service.current_policy is None
    assert service.config is not None

    bars = _generate_sample_bars(5)
    preview = service.preview_coverage(bars, limit=3)
    assert preview.row_count == 5
    assert len(preview.preview_rows) == 3

    export = service.export_series(bars, export_format="CSV")
    assert export.row_count == 5
    assert len(export.data_bytes) > 0


@pytest.mark.asyncio
async def test_service_error_handling() -> None:
    """Verify DataFailure results when policy is missing."""
    service = DataInspectionRetentionService()

    # Missing policy for DEFINE_POLICY
    req_missing_pol = ManageRetentionRequest.model_construct(
        request_id=_generate_uuid7(),
        capability_snapshot_id=_generate_uuid7(),
        operation="DEFINE_POLICY",
        policy=None,
        schema_version=1,
    )
    res1 = await service.manage_retention(req_missing_pol)
    assert isinstance(res1, DataFailure)
    assert res1.code == "DATA_VALIDATION_FAILED"


@pytest.mark.asyncio
async def test_main_scenario_harness() -> None:
    """Verify execution of the main scenario harness."""
    await main()
