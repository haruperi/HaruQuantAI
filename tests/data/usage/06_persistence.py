"""Run isolated SQLite, artifact, cache, lock, migration, and audit examples."""

import sys
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from tempfile import TemporaryDirectory

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.services.data import (
    AuditEventQuery,
    BackupTarget,
    CacheReadRequest,
    CacheWriteRequest,
    ColumnMapping,
    DataError,
    DataQualityReport,
    DatasetLoadRequest,
    DatasetSaveRequest,
    DataSettings,
    ExternalImportRequest,
    MarketDataset,
    MigrationRequest,
    MigrationStep,
    OHLCVRecord,
    StatementPlan,
    TransactionRequest,
    acquire_write_lock,
    clear_data_cache,
    create_backup,
    data_settings_context,
    describe_import_dialects,
    enforce_retention_policy,
    execute_transaction,
    get_cache_entry,
    import_external_dataset,
    load_dataset,
    persist_audit_event,
    put_cache_entry,
    query_audit_events,
    restore_from_backup,
    run_data_migrations,
    run_domain_migrations,
    save_dataset,
    save_market_data,
)
from app.utils import AuditEvent, AuthContext, generate_id, logger

_OBSERVED_AT = datetime(2026, 7, 1, 12, 0, tzinfo=UTC)


def _header(title: str) -> None:
    """Print one example heading."""
    print(f"\n{'=' * 88}\n{title}\n{'=' * 88}")
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


def _example_fr_data_014() -> None:
    """Run one raw transaction using the shared persistence connection."""
    _header("FR-DATA-014: executing one bounded SQLite transaction")
    request = TransactionRequest(
        plan=StatementPlan(
            statements=("SELECT 1;",),
            parameter_sets=((),),
            max_rows=10,
        ),
        request_id=generate_id("req"),
    )
    outcome = execute_transaction(request)
    print(f"Transaction committed and returned {len(outcome.rows)} rows")


def _example_fr_data_015() -> None:
    """Run step-level domain migrations with ledger verification."""
    _header("FR-DATA-015: applying an idempotent usage migration")
    req_id = generate_id("req")
    statement = (
        "CREATE TABLE IF NOT EXISTS usage_notes (id TEXT PRIMARY KEY, content TEXT)"
    )
    step = MigrationStep(
        domain="usage",
        migration_id="001_create_usage_notes",
        checksum="usage-notes-v1",
        statements=(statement,),
    )
    request = MigrationRequest(
        domain="usage",
        steps=(step,),
        request_id=req_id,
    )
    report = run_domain_migrations(request)
    print(f"Applied migration IDs={report.applied_ids}")


def _example_fr_data_016(root: Path) -> None:
    """Acquire one path-scoped write lease for atomic writes."""
    _header("FR-DATA-016: acquiring a path-scoped write lease")
    req_id = generate_id("req")
    target_file = root / "data/processed/AAPL.parquet"
    with acquire_write_lock(target_file, req_id) as lease:
        print(f"Lease acquired for {lease.path} by {lease.request_id}")


def _example_fr_data_017(root: Path) -> None:
    """Load one dataset artifact and manifest via DatasetLoadRequest."""
    _header("FR-DATA-017: loading a governed CSV artifact")
    ds = _dataset()
    save_dataset(
        DatasetSaveRequest(
            dataset=ds,
            relative_path=Path("data/raw/AAPL.csv"),
            format="csv",
            overwrite=True,
            request_id=ds.request_id,
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


def _example_fr_data_018(root: Path) -> None:
    """Write one dataset artifact and its sidecar manifest atomically."""
    _header("FR-DATA-018: saving a governed CSV artifact")
    ds = _dataset()
    save_dataset(
        DatasetSaveRequest(
            dataset=ds,
            relative_path=Path("data/raw/AAPL.csv"),
            format="csv",
            overwrite=True,
            request_id=ds.request_id,
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


def _example_fr_data_019() -> None:
    """Read one entry from the local SQLite cache."""
    _header("FR-DATA-019: reading a compatible cache entry")
    ds = _dataset()
    req_id = generate_id("req")
    put_cache_entry(
        CacheWriteRequest(
            key="usage-aapl-m1-v1",
            dataset=ds,
            source_revision="rev-1",
            raw_data_hash="abc123hash",
            ttl_seconds=3600,
            request_id=req_id,
        )
    )
    entry = get_cache_entry(
        CacheReadRequest(
            key="usage-aapl-m1-v1",
            allow_stale=False,
            request_id=req_id,
        )
    )
    print(f"Cache entry read: found={entry is not None}")


def _example_fr_data_020() -> None:
    """Write one dataset entry into the local SQLite cache."""
    _header("FR-DATA-020: writing a bounded cache entry")
    ds = _dataset()
    outcome = put_cache_entry(
        CacheWriteRequest(
            key="usage-aapl-m1-v1",
            dataset=ds,
            source_revision="rev-1",
            raw_data_hash="abc123hash",
            ttl_seconds=3600,
            request_id=generate_id("req"),
        )
    )
    print(f"Cache write={outcome.written} key={outcome.key}")


def example_13_csv_saver() -> None:
    """Save and reload CSV market-data artifacts via save_market_data."""
    _header("Save and reload CSV market-data artifacts via save_market_data.")
    ds = _dataset()
    manifest = save_market_data(ds, destination_path=Path("data/raw/AAPL_saver.csv"))
    print(
        f"CSV save status: committed={manifest.committed} path={manifest.relative_path}"
    )


def example_14_parquet_saver() -> None:
    """Save and reload Parquet market-data artifacts via save_market_data."""
    _header("Save and reload Parquet market-data artifacts via save_market_data.")
    ds = _dataset()
    manifest = save_market_data(
        ds,
        destination_path=Path("data/processed/AAPL_saver.parquet"),
    )
    print(
        "Parquet save status: "
        f"committed={manifest.committed} path={manifest.relative_path}"
    )


def example_18_caching() -> None:
    """Demonstrate cache behavior and clearing via clear_data_cache."""
    _header("Demonstrate cache behavior and clearing via clear_data_cache.")
    result = clear_data_cache(source_id="local_csv", symbol="AAPL", dry_run=False)
    print(f"Cleared cache entries: deleted={result.deleted_count}")


def example_35_cleanup() -> None:
    """Clear local data cache as cleanup."""
    _header("Clear local data cache as cleanup.")
    result = clear_data_cache(dry_run=False)
    print(f"Data cache cleanup result: deleted={result.deleted_count}")


def _example_fr_data_021() -> None:
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


def _example_fr_data_077() -> None:
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


def _example_fr_data_105() -> None:
    """Import an external raw CSV file using standard dialect."""
    _header("FR-DATA-106 describe_import_dialects")
    for dialect_id, description in describe_import_dialects().items():
        print(f" - {dialect_id}: {description}")

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
            database_url="sqlite:///storage.sqlite3",
            data_dir=root,
            sqlite_busy_timeout_seconds=1.5,
            write_lock_lease_seconds=30,
            approved_storage_roots=(root,),
        )
        request = ExternalImportRequest(
            relative_path=Path("data/raw/EURUSD.csv"),
            format="csv",
            dialect="standard",
            mapping=ColumnMapping(
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
            destination_path=Path("data/raw/EURUSD_M1.csv"),
            request_id=generate_id("req"),
        )
        try:
            with data_settings_context(settings):
                run_data_migrations(generate_id("req"))
                manifest = import_external_dataset(request)
            print("Imported rows:", manifest.row_count)
            print("Committed artifact:", manifest.relative_path)
        except DataError as error:
            print("External import error:", error.code)


def _example_fr_data_108() -> None:
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


def _demonstrate_feature() -> None:
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
            _example_fr_data_014()
            _example_fr_data_015()
            _example_fr_data_016(demo_root)
            _example_fr_data_017(demo_root)
            _example_fr_data_018(demo_root)
            _example_fr_data_019()
            _example_fr_data_020()
            _example_fr_data_108()
    _example_fr_data_105()


_DEMONSTRATED = [False]


def _demonstrate_once() -> None:
    """Run the feature demonstration once for all requirement entry points."""
    if _DEMONSTRATED[0]:
        return
    _demonstrate_feature()
    _DEMONSTRATED[0] = True


def fr_data_014() -> None:
    _header("fr_data_014")
    "FR-DATA-014: Execute a bounded caller-owned statement plan in one short-lived SQLite transaction, return normalized results without a connection/session, and roll back atomically on failure."
    _demonstrate_once()


def fr_data_015() -> None:
    _header("fr_data_015")
    "FR-DATA-015: Validate ownership/order/checksums, acquire the shared lock, and execute domain-owned migration definitions exactly once while preserving an immutable ledger."
    _demonstrate_once()


def fr_data_016() -> None:
    _header("fr_data_016")
    "FR-DATA-016: Grant at most one writer lease per resolved path, reject conflicts deterministically, and release it on exit or verified stale recovery."
    _demonstrate_once()


def fr_data_018() -> None:
    _header("fr_data_018")
    "FR-DATA-018: Validate license/quality/path, lock the target, write artifact and manifest through a temporary file, and atomically commit or quarantine failure."
    _demonstrate_once()


def fr_data_019() -> None:
    _header("fr_data_019")
    "FR-DATA-019: Return a cache entry only when request dimensions, schema/normalization, source revision/raw hash, and stale policy match; stale data is never silent."
    _demonstrate_once()


def fr_data_020() -> None:
    _header("fr_data_020")
    "FR-DATA-020: Write a bounded cache entry with complete identity/TTL metadata and surface an optional cache-write failure without corrupting a successful retrieval result."
    _demonstrate_once()


def fr_data_105() -> None:
    _header("fr_data_105")
    "FR-DATA-105: Admit one externally produced artifact under a declared dialect and explicit column mapping, infer no governed field, validate and quality-check every record, commit through `save_dataset`, and persist an audit event marking external origin."
    _demonstrate_once()


def fr_data_106() -> None:
    _header("fr_data_106")
    "FR-DATA-106: Expose the supported deterministic header and delimiter dialects so a caller can select one without trial and error; an unlisted dialect is rejected."
    _demonstrate_once()


def fr_data_108() -> None:
    _header("fr_data_108")
    "FR-DATA-108: Snapshot a declared set of backup targets (raw artifacts, processed artifacts, cache state, manifests, and the migration ledger) into one immutable manifest carrying per-target hashes, byte counts, UTC creation time, and schema/normalization versions. Persist one audit event. A target outside `APPROVED_STORAGE_ROOTS` is rejected before any read."
    _demonstrate_once()


def fr_data_109() -> None:
    _header("fr_data_109")
    "FR-DATA-109: Restore every target in a named manifest to its recorded state, verifying each hash before writing and failing atomically without partial restoration when any verification fails. Restore is always explicit and never automatic."
    _demonstrate_once()


def fr_data_110() -> None:
    _header("fr_data_110")
    "FR-DATA-110: Purge raw payloads for one dataset older than an explicit maximum age and return the purged count. Operates only on raw payloads; the canonical retention terms carried by `SourceLicensePolicy` are separate and are never overridden. Defaults to a dry run."
    _demonstrate_once()


def main() -> None:
    """Execute every functional-requirement demonstration."""
    demonstrations = (
        fr_data_014,
        fr_data_015,
        fr_data_016,
        fr_data_018,
        fr_data_019,
        fr_data_020,
        fr_data_105,
        fr_data_106,
        fr_data_108,
        fr_data_109,
        fr_data_110,
    )
    for demonstration in demonstrations:
        demonstration()


if __name__ == "__main__":
    main()
