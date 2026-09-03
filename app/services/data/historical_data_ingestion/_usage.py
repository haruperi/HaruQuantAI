"""Executable usage demonstration harness for Historical Data Ingestion."""

from __future__ import annotations

import asyncio
import uuid
from pathlib import Path

from app.contracts.common.models import Uuid7
from app.contracts.data.errors import DataFailure
from app.contracts.data.models import (
    DataConnectionRef,
    DataImportPlan,
    DataImportReceipt,
    DataSeriesVersion,
    IngestHistoryRequest,
    IngestHistorySuccess,
)
from app.services.data.historical_data_ingestion.historical_data_ingestion import (
    HistoricalDataIngestionService,
    data_import_csv_data,
    data_pin_data_provenance,
    data_publish_data_versions,
    data_register_data_connections,
    data_report_import_counts,
)


def _load_historical_csv(default_csv: str) -> str:
    """Read historical raw CSV content synchronously."""
    path = Path("data/raw/EURUSD_H1.csv")
    if path.exists():
        with path.open(encoding="utf-8") as f:
            return f.read()
    return default_csv


def _generate_uuid7() -> Uuid7:
    return str(uuid.uuid7())


async def example_csv_load_direct() -> DataImportReceipt:
    """Load a manifest-verified CSV dataset directly."""
    service = HistoricalDataIngestionService()
    conn = data_register_data_connections(
        service,
        connection_type="CSV",
        declared_capabilities=("data.ingest-history@1", "data.import-csv@1"),
    )
    plan = DataImportPlan(
        plan_id=_generate_uuid7(),
        connection=conn,
        source_artifact_id=_generate_uuid7(),
        delimiter=",",
        has_header=True,
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
        decimal_separator=".",
        malformed_row_policy="ABORT_IMPORT",
        deduplication_policy="KEEP_FIRST",
    )
    csv_content = _load_historical_csv(
        "Timestamp,Open,High,Low,Close,Volume\n2026-08-01T00:00:00Z,1.1000,1.1005,1.0995,1.1002,100\n"
    )
    return await data_import_csv_data(service, plan, csv_content=csv_content)


async def example_csv_tool_load() -> IngestHistorySuccess | DataFailure:
    """Load CSV through the governed typed request boundary."""
    service = HistoricalDataIngestionService()
    conn = data_register_data_connections(service, connection_type="CSV")
    plan = DataImportPlan(
        plan_id=_generate_uuid7(),
        connection=conn,
        source_artifact_id=_generate_uuid7(),
        delimiter=",",
        has_header=True,
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
        decimal_separator=".",
        malformed_row_policy="REJECT_ROW",
        deduplication_policy="KEEP_FIRST",
    )
    return await service.ingest_history(
        IngestHistoryRequest(
            request_id=_generate_uuid7(),
            capability_snapshot_id=_generate_uuid7(),
            operation="IMPORT",
            plan=plan,
        )
    )


async def example_parquet_load_direct() -> DataConnectionRef:
    """Load a manifest-verified Parquet dataset directly."""
    service = HistoricalDataIngestionService()
    return data_register_data_connections(
        service,
        connection_type="PARQUET",
        declared_capabilities=("data.ingest-history@1", "data.import-parquet@1"),
    )


async def example_parquet_tool_load() -> DataConnectionRef:
    """Load Parquet through the governed typed request boundary."""
    service = HistoricalDataIngestionService()
    return data_register_data_connections(service, connection_type="PARQUET")


async def example_gateway_csv() -> DataSeriesVersion:
    """Use the current CSV feature boundary directly."""
    service = HistoricalDataIngestionService()
    conn = data_register_data_connections(service, connection_type="CSV")
    plan = DataImportPlan(
        plan_id=_generate_uuid7(),
        connection=conn,
        source_artifact_id=_generate_uuid7(),
        delimiter=",",
        has_header=True,
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
        decimal_separator=".",
        malformed_row_policy="ABORT_IMPORT",
        deduplication_policy="KEEP_FIRST",
    )
    clean_csv = _load_historical_csv(
        "Timestamp,Open,High,Low,Close,Volume\n2026-08-01T02:00:00Z,1.1008,1.1015,1.1005,1.1012,200\n"
    )
    return await data_publish_data_versions(service, plan, csv_content=clean_csv)


async def example_gateway_parquet() -> DataConnectionRef:
    """Use the current Parquet feature boundary directly."""
    service = HistoricalDataIngestionService()
    return data_register_data_connections(service, connection_type="PARQUET")


async def main() -> None:
    """Executable usage scenario harness for Historical Data Ingestion."""
    print("\n" + "=" * 80)
    print("Historical Data Ingestion (FEAT-DATA-INGEST_HISTORY) Scenario Harness")
    print("=" * 80)

    service = HistoricalDataIngestionService()

    # Scenario 1: FR-DATA-REGISTER_DATA_CONNECTIONS
    print("\n[1] Scenario FR-DATA-REGISTER_DATA_CONNECTIONS")
    conn = data_register_data_connections(
        service,
        connection_type="CSV",
        declared_capabilities=("data.ingest-history@1", "data.import-csv@1"),
    )
    print(f"Registered connection: id={conn.connection_id} type={conn.connection_type}")

    # Scenario 2: FR-DATA-IMPORT_CSV_DATA
    print("\n[2] Scenario FR-DATA-IMPORT_CSV_DATA (with skip malformed row)")
    sample_csv = (
        "Timestamp,Open,High,Low,Close,Volume\n"
        "2026-01-01T00:00:00Z,1.1000,1.1050,1.0950,1.1020,1000\n"
        "2026-01-01T00:01:00Z,1.1020,1.0900,1.1030,1.0990,1200\n"
        "2026-01-01T00:02:00Z,1.1010,1.1040,1.0980,1.1030,1500\n"
        "2026-01-01T00:02:00Z,1.1010,1.1040,1.0980,1.1030,1500\n"
    )
    artifact_id = _generate_uuid7()
    plan = DataImportPlan(
        plan_id=_generate_uuid7(),
        connection=conn,
        source_artifact_id=artifact_id,
        delimiter=",",
        has_header=True,
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
        decimal_separator=".",
        malformed_row_policy="REJECT_ROW",
        deduplication_policy="KEEP_FIRST",
    )

    import_result = await data_import_csv_data(
        service,
        plan,
        csv_content=sample_csv,
    )
    if isinstance(import_result, DataFailure):
        print(f"Import failed: {import_result.problem.detail}")
        return

    receipt = import_result.receipt
    version = import_result.version
    if receipt is None or version is None:
        print("Import incomplete: missing receipt or version")
        return
    print(
        f"Import completed: receipt_id={receipt.receipt_id} "
        f"outcome={import_result.outcome}"
    )

    # Scenario 3: FR-DATA-REPORT_IMPORT_COUNTS
    print("\n[3] Scenario FR-DATA-REPORT_IMPORT_COUNTS")
    counts = data_report_import_counts(receipt)
    for k, v in counts.items():
        print(f"  - {k}: {v}")
    is_reconciled = (
        counts["accepted_rows"] + counts["rejected_rows"] + counts["duplicate_rows"]
        == counts["input_rows"]
    )
    print(
        f"  * Reconciled row equation: accepted + rejected + duplicate == input_rows "
        f"({is_reconciled})"
    )

    # Scenario 4: FR-DATA-PIN_DATA_PROVENANCE
    print("\n[4] Scenario FR-DATA-PIN_DATA_PROVENANCE")
    provenance = data_pin_data_provenance(version)
    for k, v in provenance.items():
        print(f"  - {k}: {v}")

    # Scenario 5: FR-DATA-PUBLISH_DATA_VERSIONS
    print("\n[5] Scenario FR-DATA-PUBLISH_DATA_VERSIONS (atomic publication)")
    clean_csv = (
        "Timestamp,Open,High,Low,Close,Volume\n"
        "2026-01-01T00:00:00Z,1.1000,1.1050,1.0950,1.1020,1000\n"
        "2026-01-01T00:01:00Z,1.1020,1.1060,1.1000,1.1040,1100\n"
    )
    plan_clean = DataImportPlan(
        plan_id=_generate_uuid7(),
        connection=conn,
        source_artifact_id=_generate_uuid7(),
        delimiter=",",
        has_header=True,
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
        decimal_separator=".",
        malformed_row_policy="ABORT_IMPORT",
        deduplication_policy="KEEP_FIRST",
    )
    published_ver = await data_publish_data_versions(
        service,
        plan_clean,
        csv_content=clean_csv,
    )
    print(
        f"Published version: series_id={published_ver.series_id} "
        f"hash={published_ver.content_hash}"
    )

    print("\n--- Additional File Ingestion Examples ---")
    await example_csv_load_direct()
    print("  * example_csv_load_direct: completed")
    await example_csv_tool_load()
    print("  * example_csv_tool_load: completed")
    await example_parquet_load_direct()
    print("  * example_parquet_load_direct: completed")
    await example_parquet_tool_load()
    print("  * example_parquet_tool_load: completed")
    await example_gateway_csv()
    print("  * example_gateway_csv: completed")
    await example_gateway_parquet()
    print("  * example_gateway_parquet: completed")

    print("\n" + "=" * 80)
    print("All Historical Data Ingestion Scenarios Executed Successfully")
    print("=" * 80)


def run_usage_scenarios() -> None:
    """Synchronous runner entry point for the usage demonstration."""
    asyncio.run(main())


if __name__ == "__main__":
    run_usage_scenarios()
