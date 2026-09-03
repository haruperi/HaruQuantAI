"""Executable usage demonstration harness for Data Inspection and Retention."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta

from app.contracts.data.models import (
    ManageRetentionRequest,
    ManageRetentionSuccess,
    RetentionPolicy,
)
from app.services.data.data_inspection_retention.data_inspection_retention import (
    CoveragePreviewResult,
    DataInspectionRetentionService,
    DatasetManifest,
    ExportSeriesResult,
    GarbageCollectionResult,
    StorageArtifact,
    _generate_uuid7,
    data_collect_reachable_artifacts,
    data_export_data_series,
    data_preview_data_coverage,
)

_EXPECTED_SAMPLE_ROWS = 50
_EXPECTED_PREVIEW_LIMIT = 5


async def _run_preview_scenario() -> list[dict[str, str]]:
    """Execute scenario 1: coverage preview.

    Returns:
        Sample records list.

    Raises:
        RuntimeError: If scenario check fails.
    """
    print("[SCENARIO 1] FR-DATA-PREVIEW_DATA_COVERAGE: Previewing coverage...")
    sample_records = [
        {
            "timestamp": f"2026-08-28T10:{i:02d}:00.000000Z",
            "open": f"{100.0 + i * 0.5:.2f}",
            "high": f"{100.5 + i * 0.5:.2f}",
            "low": f"{99.5 + i * 0.5:.2f}",
            "close": f"{100.2 + i * 0.5:.2f}",
            "volume": "1000",
        }
        for i in range(_EXPECTED_SAMPLE_ROWS)
    ]
    preview_res = data_preview_data_coverage(
        sample_records, limit=_EXPECTED_PREVIEW_LIMIT, expected_step_seconds=60.0
    )
    print(f" -> Total rows: {preview_res.row_count}")
    print(f" -> Coverage: {preview_res.start_timestamp} -> {preview_res.end_timestamp}")
    print(f" -> Preview sample size: {len(preview_res.preview_rows)}")
    print(f" -> Precisions: {preview_res.precision_summary}")
    print(f" -> Findings: {preview_res.findings}")
    print(f" -> Gaps: {preview_res.gaps}")
    if (
        preview_res.row_count != _EXPECTED_SAMPLE_ROWS
        or len(preview_res.preview_rows) != _EXPECTED_PREVIEW_LIMIT
    ):
        msg = f"Unexpected preview result: {preview_res}"
        raise RuntimeError(msg)
    return sample_records


def _run_export_scenario(sample_records: list[dict[str, str]]) -> None:
    """Execute scenario 2: series export with canonical hash.

    Args:
        sample_records: Sample records to export.

    Raises:
        RuntimeError: If exported hashes do not match.
    """
    print("[SCENARIO 2] FR-DATA-EXPORT_DATA_SERIES: Exporting series...")
    export_csv = data_export_data_series(
        sample_records, export_format="CSV", timezone="UTC"
    )
    print(f" -> CSV Exported bytes: {len(export_csv.data_bytes)} bytes")
    print(f" -> Canonical content hash: {export_csv.canonical_content_hash[:16]}...")

    export_parquet = data_export_data_series(
        sample_records, export_format="PARQUET", timezone="UTC"
    )
    print(f" -> Parquet Exported bytes: {len(export_parquet.data_bytes)} bytes")
    if export_csv.canonical_content_hash != export_parquet.canonical_content_hash:
        msg = (
            "Canonical content hash must be identical across export formats "
            "for identical records"
        )
        raise RuntimeError(msg)
    print(" -> Canonical hashes match across CSV and Parquet export.")


async def _run_gc_scenario() -> None:
    """Execute scenario 3: garbage collection and service operations.

    Raises:
        RuntimeError: If GC partitioning or service calls fail.
    """
    print("[SCENARIO 3] FR-DATA-COLLECT_REACHABLE_ARTIFACTS: Reachability GC...")
    now = datetime(2026, 8, 28, 12, 0, 0, tzinfo=UTC)
    manifest = DatasetManifest(
        manifest_id="manifest-1",
        referenced_artifact_ids=frozenset({"art-reachable-1", "art-reachable-2"}),
        committed_at=now - timedelta(days=60),
    )
    artifacts = [
        StorageArtifact("art-reachable-1", created_at=now - timedelta(days=90)),
        StorageArtifact("art-unreachable-fresh", created_at=now - timedelta(days=10)),
        StorageArtifact("art-unreachable-expired", created_at=now - timedelta(days=45)),
    ]

    gc_res = data_collect_reachable_artifacts(
        [manifest], artifacts, quarantine_days=30, reference_time=now
    )
    print(f" -> Reachable preserved: {gc_res.preserved_artifact_ids}")
    print(f" -> Quarantined: {gc_res.quarantined_artifact_ids}")
    print(f" -> Collected: {gc_res.collected_artifact_ids}")

    if (
        gc_res.preserved_artifact_ids != ("art-reachable-1",)
        or gc_res.quarantined_artifact_ids != ("art-unreachable-fresh",)
        or gc_res.collected_artifact_ids != ("art-unreachable-expired",)
    ):
        msg = f"Unexpected GC partitioning: {gc_res}"
        raise RuntimeError(msg)

    print("[SERVICE] Verifying DataInspectionRetentionService...")
    service = DataInspectionRetentionService()
    for a in artifacts:
        service.register_artifact(a)
    service.register_manifest(manifest)

    pol_req = ManageRetentionRequest(
        request_id=_generate_uuid7(),
        capability_snapshot_id=_generate_uuid7(),
        operation="DEFINE_POLICY",
        policy=RetentionPolicy(
            policy_id=_generate_uuid7(),
            retention_days=90,
            quarantine_days=30,
        ),
    )
    pol_res = await service.manage_retention(pol_req)
    if not isinstance(pol_res, ManageRetentionSuccess) or pol_res.outcome != "SUCCESS":
        msg = f"Unexpected policy definition response: {pol_res}"
        raise RuntimeError(msg)
    print(" -> Service DEFINE_POLICY invocation succeeded.")

    col_req = ManageRetentionRequest(
        request_id=_generate_uuid7(),
        capability_snapshot_id=_generate_uuid7(),
        operation="COLLECT",
    )
    col_res = await service.manage_retention(col_req)
    if not isinstance(col_res, ManageRetentionSuccess) or col_res.collected_count != 1:
        msg = f"Unexpected collect response: {col_res}"
        raise RuntimeError(msg)
    print(" -> Service COLLECT invocation succeeded.")


def _load_real_raw_records() -> list[dict[str, str]]:
    """Load real actual records from persisted raw dataset."""
    import csv
    from pathlib import Path

    csv_path = Path("data/raw/EURUSD_H1.csv")
    if csv_path.exists():
        with csv_path.open(encoding="utf-8") as f:
            reader = csv.DictReader(f)
            return [
                {
                    "timestamp": row["Timestamp"],
                    "open": row["Open"],
                    "high": row["High"],
                    "low": row["Low"],
                    "close": row["Close"],
                    "volume": row["Volume"],
                }
                for row in reader
            ]
    return [
        {
            "timestamp": "2026-08-28T10:00:00.000000Z",
            "open": "100.00",
            "high": "100.50",
            "low": "99.50",
            "close": "100.20",
            "volume": "1000",
        }
    ]


def example_csv_fetch_range(
    records: list[dict[str, str]] | None = None,
) -> CoveragePreviewResult:
    """Request bounded CSV availability and preview before loading records."""
    recs = records or _load_real_raw_records()
    return data_preview_data_coverage(recs, limit=5, expected_step_seconds=3600.0)


def example_csv_saver(
    records: list[dict[str, str]] | None = None,
) -> ExportSeriesResult:
    """Save a canonical dataset as CSV through the public boundary."""
    recs = records or _load_real_raw_records()
    return data_export_data_series(recs, export_format="CSV", timezone="UTC")


def example_parquet_saver(
    records: list[dict[str, str]] | None = None,
) -> ExportSeriesResult:
    """Save a canonical dataset as Parquet through the public boundary."""
    recs = records or _load_real_raw_records()
    return data_export_data_series(recs, export_format="PARQUET", timezone="UTC")


def example_data_availability(
    records: list[dict[str, str]] | None = None,
) -> CoveragePreviewResult:
    """Inspect bounded local-source availability."""
    return example_csv_fetch_range(records)


def example_cleanup() -> GarbageCollectionResult:
    """Clear Data cache and retention entries through the current public boundary."""
    now = datetime.now(tz=UTC)
    manifest = DatasetManifest(
        manifest_id=_generate_uuid7(),
        referenced_artifact_ids=frozenset({"art-reachable-1"}),
        committed_at=now - timedelta(days=60),
    )
    artifacts = [
        StorageArtifact("art-reachable-1", created_at=now - timedelta(days=90)),
        StorageArtifact("art-orphan-expired", created_at=now - timedelta(days=60)),
    ]
    return data_collect_reachable_artifacts(
        [manifest], artifacts, quarantine_days=30, reference_time=now
    )


async def main() -> None:
    """Executable scenario harness demonstrating all feature requirements.

    Raises:
        RuntimeError: If any scenario assertion fails.
    """
    print("=" * 80)
    print("RUNNING FEAT-DATA-MANAGE_RETENTION USAGE HARNESS")
    print("=" * 80)

    sample_records = await _run_preview_scenario()
    _run_export_scenario(sample_records)
    await _run_gc_scenario()

    print("\n--- Additional Inspection & Retention Examples ---")
    res_range = example_csv_fetch_range(sample_records)
    print(f"  * example_csv_fetch_range: row_count={res_range.row_count}")
    res_csv = example_csv_saver(sample_records)
    print(f"  * example_csv_saver: bytes={len(res_csv.data_bytes)}")
    res_parquet = example_parquet_saver(sample_records)
    print(f"  * example_parquet_saver: bytes={len(res_parquet.data_bytes)}")
    res_avail = example_data_availability(sample_records)
    print(f"  * example_data_availability: row_count={res_avail.row_count}")
    res_clean = example_cleanup()
    print(f"  * example_cleanup: collected={res_clean.collected_artifact_ids}")

    print("=" * 80)
    print("ALL SCENARIOS PASSED")
    print("=" * 80)


def run_usage_scenarios() -> None:
    """Run all usage scenarios synchronously."""
    asyncio.run(main())


if __name__ == "__main__":
    run_usage_scenarios()
