"""Unit and functional tests for Historical Data Ingestion service."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

import pytest
from app.contracts.common.models import Timeframe, Uuid7
from app.contracts.data.errors import DataFailure
from app.contracts.data.models import (
    DataConnectionRef,
    DataImportPlan,
    IngestHistoryRequest,
    IngestHistorySuccess,
)
from app.services.data.historical_data_ingestion.config import (
    HistoricalDataIngestionConfig,
)
from app.services.data.historical_data_ingestion.historical_data_ingestion import (
    HistoricalDataIngestionService,
    _generate_uuid7,
    data_import_csv_data,
    data_pin_data_provenance,
    data_publish_data_versions,
    data_register_data_connections,
    data_report_import_counts,
    main,
)


@pytest.fixture
def service(tmp_path: Path) -> HistoricalDataIngestionService:
    """Provide a fresh HistoricalDataIngestionService instance."""
    db_path = tmp_path / "test_ingestion.db"
    config = HistoricalDataIngestionConfig(database_path=db_path)
    return HistoricalDataIngestionService(config=config)


def _build_test_plan(
    connection: DataConnectionRef,
    source_artifact_id: Uuid7,
    *,
    delimiter: str = ",",
    has_header: bool = True,
    decimal_separator: str = ".",
    malformed_row_policy: Literal["REJECT_ROW", "ABORT_IMPORT"] = "REJECT_ROW",
    deduplication_policy: Literal["KEEP_FIRST", "KEEP_LAST", "REJECT"] = "KEEP_FIRST",
) -> DataImportPlan:
    """Helper to create a DataImportPlan for testing."""
    return DataImportPlan(
        plan_id=_generate_uuid7(),
        connection=connection,
        source_artifact_id=source_artifact_id,
        delimiter=delimiter,
        has_header=has_header,
        encoding="utf-8",
        timezone="UTC",
        column_mapping={
            "timestamp": "Timestamp",
            "open": "Open",
            "high": "High",
            "low": "Low",
            "close": "Close",
            "volume": "Volume",
        },
        decimal_separator=decimal_separator,
        malformed_row_policy=malformed_row_policy,
        deduplication_policy=deduplication_policy,
    )


def test_data_register_data_connections(
    service: HistoricalDataIngestionService,
) -> None:
    """FR-DATA-REGISTER_DATA_CONNECTIONS: Register connections by type and capabilities."""
    conn_csv = data_register_data_connections(
        service,
        connection_type="CSV",
        declared_capabilities=("data.ingest-history@1", "data.import-csv@1"),
    )
    assert conn_csv.connection_type == "CSV"
    assert "data.ingest-history@1" in conn_csv.declared_capabilities

    conn_parquet = data_register_data_connections(
        service,
        connection_type="PARQUET",
        declared_capabilities=("data.ingest-history@1", "data.export-parquet@1"),
    )
    assert conn_parquet.connection_type == "PARQUET"

    fetched = service.get_connection_by_id(conn_csv.connection_id)
    assert fetched is not None
    assert fetched.connection_id == conn_csv.connection_id


@pytest.mark.asyncio
async def test_data_import_csv_data(
    service: HistoricalDataIngestionService,
) -> None:
    """FR-DATA-IMPORT_CSV_DATA: Import valid CSV with custom settings."""
    conn = data_register_data_connections(service, connection_type="CSV")
    artifact_id = _generate_uuid7()
    plan = _build_test_plan(conn, artifact_id)

    csv_data = (
        "Timestamp,Open,High,Low,Close,Volume\n"
        "2026-01-01T00:00:00Z,1.1000,1.1050,1.0950,1.1020,1000\n"
        "2026-01-01T00:01:00Z,1.1020,1.1060,1.1000,1.1040,1200\n"
    )

    result = await data_import_csv_data(service, plan, csv_content=csv_data)
    assert isinstance(result, IngestHistorySuccess)
    assert result.outcome == "SUCCESS"
    assert result.receipt is not None
    assert result.receipt.input_rows == 2
    assert result.receipt.accepted_rows == 2
    assert result.receipt.rejected_rows == 0
    assert result.receipt.published_rows == 2
    assert result.version is not None
    assert result.version.row_count == 2


@pytest.mark.asyncio
async def test_data_malformed_row_policy_abort(
    service: HistoricalDataIngestionService,
) -> None:
    """FR-DATA-IMPORT_CSV_DATA: ABORT_IMPORT policy aborts on malformed row."""
    conn = data_register_data_connections(service, connection_type="CSV")
    artifact_id = _generate_uuid7()
    plan = _build_test_plan(
        conn,
        artifact_id,
        malformed_row_policy="ABORT_IMPORT",
    )

    csv_data = (
        "Timestamp,Open,High,Low,Close,Volume\n"
        "2026-01-01T00:00:00Z,1.1000,1.1050,1.0950,1.1020,1000\n"
        "2026-01-01T00:01:00Z,1.1020,1.0900,1.1060,1.1040,1200\n"  # malformed (high < low)
    )

    result = await data_import_csv_data(service, plan, csv_content=csv_data)
    assert isinstance(result, DataFailure)
    assert result.code == "DATA_VALIDATION_FAILED"
    assert result.problem.status == 422


@pytest.mark.asyncio
async def test_data_malformed_row_policy_reject(
    service: HistoricalDataIngestionService,
) -> None:
    """FR-DATA-IMPORT_CSV_DATA: REJECT_ROW policy rejects invalid rows and imports valid."""
    conn = data_register_data_connections(service, connection_type="CSV")
    artifact_id = _generate_uuid7()
    plan = _build_test_plan(
        conn,
        artifact_id,
        malformed_row_policy="REJECT_ROW",
    )

    csv_data = (
        "Timestamp,Open,High,Low,Close,Volume\n"
        "2026-01-01T00:00:00Z,1.1000,1.1050,1.0950,1.1020,1000\n"
        "2026-01-01T00:01:00Z,1.1020,1.0900,1.1060,1.1040,1200\n"  # malformed (high < low)
        "2026-01-01T00:02:00Z,1.1040,1.1070,1.1020,1.1050,1500\n"
    )

    result = await data_import_csv_data(service, plan, csv_content=csv_data)
    assert isinstance(result, IngestHistorySuccess)
    assert result.receipt is not None
    assert result.receipt.input_rows == 3
    assert result.receipt.accepted_rows == 2
    assert result.receipt.rejected_rows == 1
    assert result.receipt.duplicate_rows == 0
    assert result.receipt.published_rows == 2


@pytest.mark.asyncio
async def test_data_deduplication_policies(
    service: HistoricalDataIngestionService,
) -> None:
    """FR-DATA-IMPORT_CSV_DATA: Deduplication policies (KEEP_FIRST, REJECT_ALL)."""
    conn = data_register_data_connections(service, connection_type="CSV")
    csv_data = (
        "Timestamp,Open,High,Low,Close,Volume\n"
        "2026-01-01T00:00:00Z,1.1000,1.1050,1.0950,1.1020,1000\n"
        "2026-01-01T00:00:00Z,1.1000,1.1050,1.0950,1.1020,1000\n"  # duplicate
        "2026-01-01T00:01:00Z,1.1020,1.1060,1.1000,1.1040,1200\n"
    )

    # KEEP_FIRST
    plan_first = _build_test_plan(
        conn,
        _generate_uuid7(),
        deduplication_policy="KEEP_FIRST",
    )
    res_first = await data_import_csv_data(service, plan_first, csv_content=csv_data)
    assert isinstance(res_first, IngestHistorySuccess)
    assert res_first.receipt is not None
    assert res_first.receipt.duplicate_rows == 1
    assert res_first.receipt.accepted_rows == 2

    # REJECT
    plan_reject = _build_test_plan(
        conn,
        _generate_uuid7(),
        deduplication_policy="REJECT",
    )
    res_reject = await data_import_csv_data(service, plan_reject, csv_content=csv_data)
    assert isinstance(res_reject, IngestHistorySuccess)
    assert res_reject.receipt is not None
    assert res_reject.receipt.duplicate_rows == 1
    assert res_reject.receipt.accepted_rows == 2


@pytest.mark.asyncio
async def test_data_publish_data_versions(
    service: HistoricalDataIngestionService,
) -> None:
    """FR-DATA-PUBLISH_DATA_VERSIONS: Atomically publish and retrieve a series version."""
    conn = data_register_data_connections(service, connection_type="CSV")
    artifact_id = _generate_uuid7()
    plan = _build_test_plan(conn, artifact_id)
    csv_data = (
        "Timestamp,Open,High,Low,Close,Volume\n"
        "2026-01-01T00:00:00Z,1.1000,1.1050,1.0950,1.1020,1000\n"
    )

    version = await data_publish_data_versions(service, plan, csv_content=csv_data)
    assert version.version == 1
    assert version.row_count == 1
    assert len(version.content_hash) == 64

    fetched = service.get_series_version(version.series_id, version=1)
    assert fetched is not None
    assert fetched.series_id == version.series_id
    assert fetched.content_hash == version.content_hash


@pytest.mark.asyncio
async def test_data_pin_data_provenance(
    service: HistoricalDataIngestionService,
) -> None:
    """FR-DATA-PIN_DATA_PROVENANCE: Pin instrument, timeframe, timezone, hash, etc."""
    conn = data_register_data_connections(service, connection_type="CSV")
    artifact_id = _generate_uuid7()
    plan = _build_test_plan(conn, artifact_id)
    csv_data = (
        "Timestamp,Open,High,Low,Close,Volume\n"
        "2026-01-01T00:00:00Z,1.1000,1.1050,1.0950,1.1020,1000\n"
    )

    version = await data_publish_data_versions(service, plan, csv_content=csv_data)
    provenance = data_pin_data_provenance(version)
    assert provenance["series_id"] == version.series_id
    assert provenance["timeframe"] == Timeframe(unit="MINUTE", multiple=1)
    assert provenance["timezone"] == "UTC"
    assert provenance["content_hash"] == version.content_hash
    assert provenance["row_count"] == 1


@pytest.mark.asyncio
async def test_data_report_import_counts(
    service: HistoricalDataIngestionService,
) -> None:
    """FR-DATA-REPORT_IMPORT_COUNTS: Verify deterministic counter reconciliation."""
    conn = data_register_data_connections(service, connection_type="CSV")
    artifact_id = _generate_uuid7()
    plan = _build_test_plan(conn, artifact_id, malformed_row_policy="REJECT_ROW")
    csv_data = (
        "Timestamp,Open,High,Low,Close,Volume\n"
        "2026-01-01T00:00:00Z,1.1000,1.1050,1.0950,1.1020,1000\n"
        "2026-01-01T00:01:00Z,1.1020,1.0900,1.1060,1.1040,1200\n"  # rejected
        "2026-01-01T00:02:00Z,1.1040,1.1070,1.1020,1.1050,1500\n"
        "2026-01-01T00:02:00Z,1.1040,1.1070,1.1020,1.1050,1500\n"  # duplicate
    )

    result = await data_import_csv_data(service, plan, csv_content=csv_data)
    assert isinstance(result, IngestHistorySuccess)
    assert result.receipt is not None

    counts = data_report_import_counts(result.receipt)
    assert counts["input_rows"] == 4
    assert counts["accepted_rows"] == 2
    assert counts["rejected_rows"] == 1
    assert counts["duplicate_rows"] == 1
    assert counts["published_rows"] == 2
    assert (
        counts["accepted_rows"] + counts["rejected_rows"] + counts["duplicate_rows"]
        == counts["input_rows"]
    )


@pytest.mark.asyncio
async def test_data_export_operations(
    service: HistoricalDataIngestionService,
) -> None:
    """Test exporting series version to CSV and Parquet."""
    conn = data_register_data_connections(service, connection_type="CSV")
    artifact_id = _generate_uuid7()
    plan = _build_test_plan(conn, artifact_id)
    csv_data = (
        "Timestamp,Open,High,Low,Close,Volume\n"
        "2026-01-01T00:00:00Z,1.1000,1.1050,1.0950,1.1020,1000\n"
    )
    version = await data_publish_data_versions(service, plan, csv_content=csv_data)

    # Export CSV
    req_csv = IngestHistoryRequest(
        request_id=_generate_uuid7(),
        capability_snapshot_id=_generate_uuid7(),
        operation="EXPORT",
        series_version_id=version.series_id,
        export_format="CSV",
    )
    res_csv = await service.ingest_history(req_csv)
    assert isinstance(res_csv, IngestHistorySuccess)
    assert res_csv.outcome == "SUCCESS"

    # Export Parquet
    req_parquet = IngestHistoryRequest(
        request_id=_generate_uuid7(),
        capability_snapshot_id=_generate_uuid7(),
        operation="EXPORT",
        series_version_id=version.series_id,
        export_format="PARQUET",
    )
    res_parquet = await service.ingest_history(req_parquet)
    assert isinstance(res_parquet, IngestHistorySuccess)
    assert res_parquet.outcome == "SUCCESS"

    # Export Not Found
    req_nf = IngestHistoryRequest(
        request_id=_generate_uuid7(),
        capability_snapshot_id=_generate_uuid7(),
        operation="EXPORT",
        series_version_id=_generate_uuid7(),
        export_format="CSV",
    )
    res_nf = await service.ingest_history(req_nf)
    assert isinstance(res_nf, DataFailure)
    assert res_nf.code == "DATA_NOT_FOUND"


@pytest.mark.asyncio
async def test_data_import_missing_artifact(
    service: HistoricalDataIngestionService,
) -> None:
    """Test importing when source artifact is not staged."""
    conn = data_register_data_connections(service, connection_type="CSV")
    plan = _build_test_plan(conn, _generate_uuid7())
    req = IngestHistoryRequest(
        request_id=_generate_uuid7(),
        capability_snapshot_id=_generate_uuid7(),
        operation="IMPORT",
        plan=plan,
    )
    res = await service.ingest_history(req)
    assert isinstance(res, DataFailure)
    assert res.code == "DATA_NOT_FOUND"


@pytest.mark.asyncio
async def test_malformed_row_abort_and_reject(
    service: HistoricalDataIngestionService,
) -> None:
    """Test malformed row handling under ABORT_IMPORT and REJECT_ROW policies."""
    conn = data_register_data_connections(service, connection_type="CSV")
    artifact_id = _generate_uuid7()

    # 1. Fewer columns with ABORT_IMPORT
    plan_abort_short = _build_test_plan(
        conn, artifact_id, malformed_row_policy="ABORT_IMPORT"
    )
    csv_short = "Timestamp,Open,High,Low,Close,Volume\n2026-01-01T00:00:00Z,1.1000\n"
    res1 = await data_import_csv_data(service, plan_abort_short, csv_content=csv_short)
    assert isinstance(res1, DataFailure)
    assert res1.code == "DATA_VALIDATION_FAILED"

    # 2. Fewer columns with REJECT_ROW
    plan_reject_short = _build_test_plan(
        conn, artifact_id, malformed_row_policy="REJECT_ROW"
    )
    res2 = await data_import_csv_data(service, plan_reject_short, csv_content=csv_short)
    assert isinstance(res2, IngestHistorySuccess)
    assert res2.receipt is not None
    assert res2.receipt.rejected_rows == 1

    # 3. Missing/empty mapped field with ABORT_IMPORT
    csv_empty_field = (
        "Timestamp,Open,High,Low,Close,Volume\n"
        "2026-01-01T00:00:00Z,1.1000,1.1050,,1.1020,1000\n"
    )
    res3 = await data_import_csv_data(
        service, plan_abort_short, csv_content=csv_empty_field
    )
    assert isinstance(res3, DataFailure)
    assert res3.code == "DATA_VALIDATION_FAILED"

    # 4. Missing/empty mapped field with REJECT_ROW
    res4 = await data_import_csv_data(
        service, plan_reject_short, csv_content=csv_empty_field
    )
    assert isinstance(res4, IngestHistorySuccess)
    assert res4.receipt is not None
    assert res4.receipt.rejected_rows == 1


@pytest.mark.asyncio
async def test_main_executable_harness() -> None:
    """Test the executable scenario harness."""
    await main()
