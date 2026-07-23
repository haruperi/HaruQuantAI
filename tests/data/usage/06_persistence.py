"""Run isolated SQLite, artifact, cache, lock, migration, and audit examples."""

import sys
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from tempfile import TemporaryDirectory

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.services.data._settings import DataSettings, data_settings_context
from app.services.data.audit import persist_audit_event, query_audit_events
from app.services.data.audit.contracts import (
    AuditEventQuery,
)
from app.services.data.contracts import (
    DataQualityReport,
    MarketDataset,
    OHLCVRecord,
)
from app.services.data.local_datasets.contracts import DatasetLoadRequest
from app.services.data.persistence.backup import (
    create_backup,
    enforce_retention_policy,
    restore_from_backup,
)
from app.services.data.persistence.cache import (
    clear_data_cache,
    get_cache_entry,
    put_cache_entry,
)
from app.services.data.persistence.contracts import (
    BackupTarget,
    CacheClearRequest,
    CacheReadRequest,
    CacheWriteRequest,
    DatasetSaveRequest,
    MigrationRequest,
    MigrationStep,
    StatementPlan,
    TransactionRequest,
)
from app.services.data.persistence.dataset_writer import (
    load_dataset,
    save_dataset,
    save_market_data,
)
from app.services.data.persistence.external_import import (
    ExternalImportRequest,
    import_external_dataset,
)
from app.services.data.persistence.locking import acquire_write_lock
from app.services.data.persistence.migrations import (
    run_data_migrations,
    run_domain_migrations,
)
from app.services.data.persistence.transactions import execute_transaction
from app.utils import AuditEvent, AuthContext, generate_id, logger

_OBSERVED_AT = datetime(2026, 7, 1, 12, 0, tzinfo=UTC)


def _header(title: str) -> None:
    """Print the header for an example section."""
    print(f"\n{'=' * 100}")
    print(f"--- {title} ---")
    print(f"{'=' * 100}")


def _configure_environment(root: Path) -> None:
    """Configure an isolated DATA persistence profile for this script."""
    logger.info("Configuring isolated DATA storage under %s", root)
    for relative in ("data/raw", "data/processed", "data/cache", "artifacts/data"):
        (root / relative).mkdir(parents=True, exist_ok=True)
    run_data_migrations(generate_id("req"))


def _quality() -> DataQualityReport:
    """Build clean quality evidence for one persisted dataset."""
    logger.info("Building storage example quality evidence")
    return DataQualityReport(
        quality_status="passed",
        quality_score=Decimal(1),
        issues=(),
        warnings=(),
        record_count=2,
        checked_count=2,
        truncated=False,
        sample_limit=10,
        schema_version="v1",
        generated_at=_OBSERVED_AT + timedelta(minutes=2),
    )


def _dataset() -> MarketDataset:
    """Build a small realistic dataset for persistence examples."""
    logger.info("Building storage example market dataset")
    records = tuple(
        OHLCVRecord(
            timestamp=_OBSERVED_AT + timedelta(minutes=index),
            open=Decimal(100) + index,
            high=Decimal(101) + index,
            low=Decimal(99) + index,
            close=Decimal("100.5") + index,
            volume=Decimal(1000) + (index * 100),
            price_unit="USD",
            volume_unit="shares",
            source="local_csv",
            source_symbol="AAPL",
            source_revision="download-20260701",
            available_at=_OBSERVED_AT + timedelta(minutes=index, seconds=1),
        )
        for index in range(2)
    )
    return MarketDataset(
        normalization_version="v1",
        data_kind="bars",
        symbol="AAPL",
        timeframe="M1",
        records=records,
        start=records[0].timestamp,
        end=records[-1].timestamp,
        available_at=records[-1].available_at,
        record_count=len(records),
        quality_report=_quality(),
        source_metadata={"source": "local_csv"},
        license_metadata={"license": "internal-research-only"},
        cache_status="not_used",
        workflow_context="research",
        precision_policy="decimal_string",
        request_id=generate_id("req"),
    )


def example_fr_data_014_transaction() -> None:
    """Run one raw transaction using the shared persistence connection."""
    _header("FR-DATA-014: executing one bounded SQLite transaction")
    request = TransactionRequest(
        plan=StatementPlan(
            statements=("SELECT 1;",),
            parameter_sets=((),),
            max_rows=10,
        )
    )
    outcome = execute_transaction(request)
    print(f"Transaction committed and returned {len(outcome.rows)} rows")


def example_fr_data_015_migration() -> None:
    """Run step-level domain migrations with ledger verification."""
    _header("FR-DATA-015: applying an idempotent usage migration")
    req_id = generate_id("req")
    step = MigrationStep(
        step_id="001_create_usage_notes",
        domain="usage",
        up_statement="CREATE TABLE IF NOT EXISTS usage_notes (id TEXT PRIMARY KEY, content TEXT);",
        down_statement="DROP TABLE IF EXISTS usage_notes;",
    )
    request = MigrationRequest(
        domain="usage",
        steps=(step,),
        request_id=req_id,
    )
    report = run_domain_migrations(request)
    print(f"Applied migration IDs={report.applied_step_ids}")


def example_fr_data_016_write_lock(root: Path) -> None:
    """Acquire one path-scoped write lease for atomic writes."""
    _header("FR-DATA-016: acquiring a path-scoped write lease")
    req_id = generate_id("req")
    target_file = root / "data/processed/AAPL.parquet"
    with acquire_write_lock(target_file, req_id) as lease:
        print(f"Lease acquired for {lease.path} by {lease.request_id}")


def example_fr_data_017_load_dataset(root: Path) -> None:
    """Load one dataset artifact and manifest via DatasetLoadRequest."""
    _header("FR-DATA-017: loading a governed CSV artifact")
    ds = _dataset()
    save_dataset(
        DatasetSaveRequest(
            dataset=ds,
            destination_relative_path=Path("data/raw/AAPL.csv"),
            request_id=generate_id("req"),
        )
    )
    request = DatasetLoadRequest(
        relative_path=Path("data/raw/AAPL.csv"),
        format="csv",
        request_id=generate_id("req"),
    )
    loaded = load_dataset(request)
    checksum = loaded.source_metadata.get("sha256")
    print(f"Verified {root / request.relative_path} with sha256={checksum}")


def example_fr_data_018_save_dataset(root: Path) -> None:
    """Write one dataset artifact and its sidecar manifest atomically."""
    _header("FR-DATA-018: saving a governed CSV artifact")
    ds = _dataset()
    save_dataset(
        DatasetSaveRequest(
            dataset=ds,
            destination_relative_path=Path("data/raw/AAPL.csv"),
            request_id=generate_id("req"),
        )
    )
    loaded = load_dataset(
        DatasetLoadRequest(
            relative_path=Path("data/raw/AAPL.csv"),
            format="csv",
            request_id=generate_id("req"),
        )
    )
    checksum = loaded.source_metadata.get("sha256")
    print(f"Verified {root / 'data/raw/AAPL.csv'} with sha256={checksum}")


def example_fr_data_019_read_cache() -> None:
    """Read one entry from the local SQLite cache."""
    _header("FR-DATA-019: reading a compatible cache entry")
    ds = _dataset()
    req_id = generate_id("req")
    put_cache_entry(
        CacheWriteRequest(
            dataset=ds,
            source_revision="rev-1",
            raw_data_hash="abc123hash",
            ttl_seconds=3600,
            request_id=req_id,
        )
    )
    entry = get_cache_entry(
        CacheReadRequest(
            key=ds.cache_key,
            request_id=req_id,
        )
    )
    print(f"Cache entry read: found={entry is not None}")


def example_fr_data_020_write_cache() -> None:
    """Write one dataset entry into the local SQLite cache."""
    _header("FR-DATA-020: writing a bounded cache entry")
    ds = _dataset()
    outcome = put_cache_entry(
        CacheWriteRequest(
            dataset=ds,
            source_revision="rev-1",
            raw_data_hash="abc123hash",
            ttl_seconds=3600,
            request_id=generate_id("req"),
        )
    )
    print(f"Cache write={outcome.written} records={outcome.record_count}")


def example_13_csv_saver() -> None:
    """Save and reload CSV market-data artifacts via save_market_data."""
    _header("FR-DATA-018: CSV Saver (save_market_data)")
    ds = _dataset()
    manifest = save_market_data(ds, destination_path=Path("data/raw/AAPL_saver.csv"))
    print(f"CSV save status: committed={manifest.committed} path={manifest.relative_path}")


def example_14_parquet_saver() -> None:
    """Save and reload Parquet market-data artifacts via save_market_data."""
    _header("FR-DATA-018: Parquet Saver (save_market_data)")
    ds = _dataset()
    manifest = save_market_data(ds, destination_path=Path("data/processed/AAPL_saver.parquet"))
    print(f"Parquet save status: committed={manifest.committed} path={manifest.relative_path}")


def example_18_caching() -> None:
    """Demonstrate cache behavior and clearing via clear_data_cache."""
    _header("FR-DATA-020: Data Caching (clear_data_cache)")
    result = clear_data_cache(source_id="local_csv", symbol="AAPL", dry_run=False)
    print(f"Cleared cache entries: deleted={result.deleted_count}")


def example_35_cleanup() -> None:
    """Clear local data cache as cleanup."""
    _header("Cleanup: clear_data_cache")
    result = clear_data_cache(dry_run=False)
    print(f"Data cache cleanup result: deleted={result.deleted_count}")


def example_fr_data_021_persist_audit() -> None:
    """Persist one audit event to the durable SQLite store."""
    _header("FR-DATA-021: persisting redacted audit evidence")
    req_id = generate_id("req")
    event = AuditEvent(
        contract_version="v1",
        schema_id="utils.audit_event.v1",
        event_id=generate_id("evt"),
        timestamp=_OBSERVED_AT,
        domain="data",
        action="usage_test",
        principal_id="user_admin",
        request_id=req_id,
        correlation_id=generate_id("cor"),
        causation_id=generate_id("cau"),
        payload={"secret_key": "[REDACTED]", "status": "ok"},
    )
    page = persist_audit_event(event)
    print(f"Queried {len(page.events)} redacted audit events")


def example_fr_data_077_query_audit() -> None:
    """Query audit events with authorized AuthContext."""
    _header("FR-DATA-077: querying redacted audit evidence")
    req_id = generate_id("req")
    query = AuditEventQuery(
        start=_OBSERVED_AT - timedelta(hours=1),
        end=_OBSERVED_AT + timedelta(hours=1),
        limit=10,
        request_id=req_id,
    )
    auth = AuthContext(
        contract_version="v1",
        schema_id="utils.auth_context.v1",
        principal_id="user_admin",
        principal_type="USER",
        roles=("admin", "auditor"),
        permissions=("audit:read",),
        scopes=("data:read",),
        tenant_or_environment="research",
        request_id=req_id,
        workflow_id=generate_id("wf"),
        correlation_id=generate_id("cor"),
        issued_at=_OBSERVED_AT,
    )
    page = query_audit_events(query, auth)
    print(f"Queried {len(page.events)} redacted audit events")


def example_fr_data_105_106_external_import() -> None:
    """Import an external raw CSV file using standard dialect."""
    _header("FR-DATA-106 describe_import_dialects")
    for dialect in describe_import_dialects():
        print(f" - {dialect.dialect_id}: {dialect.description}")

    _header("FR-DATA-105 import_external_dataset")
    with TemporaryDirectory(prefix="haru-external-import-") as directory:
        root = Path(directory)
        raw_csv = root / "data/raw/EURUSD.csv"
        raw_csv.parent.mkdir(parents=True, exist_ok=True)
        raw_csv.write_text(
            "timestamp,open,high,low,close,volume\n"
            "2026-07-01T12:00:00Z,1.1000,1.1020,1.0990,1.1010,1000\n"
            "2026-07-01T12:01:00Z,1.1010,1.1025,1.1005,1.1015,1200\n",
            encoding="utf-8",
        )
        settings = DataSettings(
            database_url=f"sqlite:///{root / 'data/storage.sqlite3'}",
            data_dir=root,
        )
        request = ExternalImportRequest(
            source_file_path=Path("raw/EURUSD.csv"),
            dialect_id="standard",
            column_mapping=dict(
                timestamp="timestamp",
                open="open",
                high="high",
                low="low",
                close="close",
                volume="volume",
            ),
            symbol="EURUSD",
            data_kind="bars",
            timeframe="M1",
            source_id="vendor_export",
            workflow_context="research",
            precision_policy="decimal_string",
            price_unit="USD",
            volume_unit="lots",
            destination_path=Path("raw/EURUSD_M1.csv"),
            request_id=generate_id("req"),
        )
        try:
            with data_settings_context(settings):
                run_data_migrations(generate_id("req"))
                manifest = import_external_dataset(request)
            print("Imported rows:", manifest.row_count)
            print("Committed artifact:", manifest.relative_path)
        except Exception as error:
            print("External import error:", type(error).__name__)


def example_fr_data_108_110_backup_and_retention() -> None:
    """Create, restore, and inspect retention for one governed raw artifact."""
    _header("FR-DATA-108..110: backup, restore, and retention")
    manifest = create_backup(
        (
            BackupTarget(
                relative_path=Path("data/raw/AAPL.csv"),
                schema_version="v1",
                normalization_version="v1",
            ),
        )
    )
    report = restore_from_backup(manifest.manifest_id)
    retained = enforce_retention_policy("AAPL.csv", 365, dry_run=True)
    print("Backup entries:", len(manifest.entries))
    print("Restored entries:", report.restored_count)
    print("Expired raw payloads:", retained)


def main() -> None:
    """Call every storage operation in isolated state."""
    with TemporaryDirectory(prefix="haru-data-storage-") as directory:
        demo_root = Path(directory)
        settings = DataSettings(
            database_url="sqlite:///usage.sqlite3",
            data_dir=demo_root,
            sqlite_busy_timeout_seconds=1.5,
            write_lock_lease_seconds=30,
        )
        with data_settings_context(settings):
            _configure_environment(demo_root)
            example_fr_data_014_transaction()
            example_fr_data_015_migration()
            example_fr_data_016_write_lock(demo_root)
            example_fr_data_017_load_dataset(demo_root)
            example_fr_data_018_save_dataset(demo_root)
            example_13_csv_saver()
            example_14_parquet_saver()
            example_fr_data_019_read_cache()
            example_fr_data_020_write_cache()
            example_18_caching()
            example_35_cleanup()
            example_fr_data_021_persist_audit()
            example_fr_data_077_query_audit()
            example_fr_data_108_110_backup_and_retention()
    example_fr_data_105_106_external_import()


if __name__ == "__main__":
    main()
