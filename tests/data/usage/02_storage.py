"""Run isolated SQLite, artifact, cache, lock, migration, and audit examples."""

import sys
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from tempfile import TemporaryDirectory

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.services.data.config import DataSettings, data_settings_context
from app.services.data.contracts import (
    AuditEventQuery,
    CacheReadRequest,
    CacheWriteRequest,
    DataQualityReport,
    DatasetLoadRequest,
    DatasetSaveRequest,
    MarketDataset,
    MigrationRequest,
    MigrationStep,
    OHLCVRecord,
    StatementPlan,
    TransactionRequest,
)
from app.services.data.storage.audit import persist_audit_event, query_audit_events
from app.services.data.storage.cache import get_cache_entry, put_cache_entry
from app.services.data.storage.database import execute_transaction
from app.services.data.storage.datasets import load_dataset, save_dataset
from app.services.data.storage.locking import acquire_write_lock
from app.services.data.storage.migrations import (
    run_data_migrations,
    run_domain_migrations,
)
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
        source_metadata={"source_id": "local_csv", "revision": "download-20260701"},
        license_metadata={"status": "approved"},
        cache_status="not_used",
        workflow_context="research",
        precision_policy="decimal_string",
        request_id=generate_id("req"),
    )


def example_fr_data_014_transaction() -> None:
    """Commit a bounded statement plan without exposing a connection."""
    _header("FR-DATA-014: executing one bounded SQLite transaction")
    result = execute_transaction(
        TransactionRequest(
            plan=StatementPlan(
                statements=(
                    "CREATE TABLE usage_facts "
                    "(id INTEGER PRIMARY KEY, value TEXT NOT NULL)",
                    "INSERT INTO usage_facts (id, value) VALUES (?, ?)",
                    "SELECT id, value FROM usage_facts ORDER BY id",
                ),
                parameter_sets=((), (1, "verified"), ()),
                max_rows=10,
            ),
            request_id=generate_id("req"),
        )
    )
    if not result.committed:
        raise AssertionError("transaction did not commit")
    print(f"Transaction committed and returned {len(result.rows)} rows")


def example_fr_data_015_migration() -> None:
    """Apply one checksummed domain-owned migration exactly once."""
    _header("FR-DATA-015: applying an idempotent usage migration")
    step = MigrationStep(
        domain="usage",
        migration_id="001_create_usage_notes",
        checksum="usage-notes-v1",
        statements=(
            "CREATE TABLE usage_notes (id INTEGER PRIMARY KEY, note TEXT NOT NULL)",
        ),
    )
    result = run_domain_migrations(
        MigrationRequest(
            domain="usage",
            steps=(step,),
            request_id=generate_id("req"),
        )
    )
    print(f"Applied migration IDs={result.applied_ids}")


def example_fr_data_016_write_lock(root: Path) -> None:
    """Acquire and release an exclusive path-scoped writer lease."""
    _header("FR-DATA-016: acquiring a path-scoped write lease")
    target = root / "data" / "processed" / "AAPL.parquet"
    with acquire_write_lock(target, generate_id("req")) as lock:
        print(f"Lease acquired for {lock.path} by {lock.request_id}")


def _save_and_load_dataset(root: Path) -> MarketDataset:
    """Atomically save and manifest-verify a normalized CSV dataset."""
    dataset = _dataset()
    path = Path("data/raw/AAPL.csv")
    manifest = save_dataset(
        DatasetSaveRequest(
            dataset=dataset,
            relative_path=path,
            format="csv",
            overwrite=True,
            request_id=dataset.request_id,
        )
    )
    loaded = load_dataset(
        DatasetLoadRequest(
            relative_path=path,
            format="csv",
            request_id=generate_id("req"),
        )
    )
    if loaded.record_count != manifest.row_count:
        raise AssertionError("loaded row count does not match the manifest")
    print(f"Verified {root / path} with sha256={manifest.content_hash}")
    return loaded


def example_fr_data_017_load_dataset(root: Path) -> MarketDataset:
    """Load one manifest-verified CSV dataset from the approved root."""
    _header("FR-DATA-017: loading a governed CSV artifact")
    return _save_and_load_dataset(root)


def example_fr_data_018_save_dataset(root: Path) -> MarketDataset:
    """Atomically save one quality-checked normalized dataset."""
    _header("FR-DATA-018: saving a governed CSV artifact")
    return _save_and_load_dataset(root)


def _write_and_read_cache() -> None:
    """Write and read one identity-bound, TTL-limited cache entry."""
    key = "usage-aapl-m1-v1"
    write = put_cache_entry(
        CacheWriteRequest(
            key=key,
            dataset=_dataset(),
            ttl_seconds=3600,
            source_revision="download-20260701",
            raw_data_hash="sha256-example-source-content",
            request_id=generate_id("req"),
        )
    )
    entry = get_cache_entry(
        CacheReadRequest(
            key=key,
            allow_stale=False,
            request_id=generate_id("req"),
        )
    )
    if entry is None:
        raise AssertionError("fresh cache entry was not returned")
    print(f"Cache write={write.written} records={entry.dataset.record_count}")


def example_fr_data_019_read_cache() -> None:
    """Read one compatible and fresh versioned cache entry."""
    _header("FR-DATA-019: reading a compatible cache entry")
    _write_and_read_cache()


def example_fr_data_020_write_cache() -> None:
    """Write one identity-complete TTL-limited cache entry."""
    _header("FR-DATA-020: writing a bounded cache entry")
    _write_and_read_cache()


def _persist_and_query_audit() -> None:
    """Persist and query a redacted audit event through owned contracts."""
    event = AuditEvent(
        contract_version="v1",
        schema_id="utils.audit_event.v1",
        event_id=generate_id("evt"),
        timestamp=_OBSERVED_AT,
        domain="data",
        action="USAGE_DATASET_VERIFIED",
        principal_id="usage-operator",
        request_id=generate_id("req"),
        correlation_id=generate_id("cor"),
        payload={"symbol": "AAPL", "result": "verified"},
    )
    persist_audit_event(event)
    auth = AuthContext(
        contract_version="v1",
        schema_id="utils.auth_context.v1",
        principal_id="usage-operator",
        principal_type="USER",
        roles=("admin",),
        permissions=(),
        scopes=("data:read",),
        tenant_or_environment="dev",
        request_id=generate_id("req"),
        workflow_id=generate_id("wf"),
        correlation_id=generate_id("cor"),
        issued_at=_OBSERVED_AT,
    )
    page = query_audit_events(
        AuditEventQuery(
            start=_OBSERVED_AT - timedelta(seconds=1),
            end=_OBSERVED_AT + timedelta(seconds=1),
            limit=10,
            request_id=generate_id("req"),
        ),
        auth,
    )
    if not page.events:
        raise AssertionError("persisted audit event was not returned")
    print(f"Queried {len(page.events)} redacted audit events")


def example_fr_data_021_persist_audit() -> None:
    """Persist one redacted audit event idempotently."""
    _header("FR-DATA-021: persisting redacted audit evidence")
    _persist_and_query_audit()


def example_fr_data_077_query_audit() -> None:
    """Execute one authorized, bounded audit query."""
    _header("FR-DATA-077: querying redacted audit evidence")
    _persist_and_query_audit()


if __name__ == "__main__":
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
            example_fr_data_019_read_cache()
            example_fr_data_020_write_cache()
            example_fr_data_021_persist_audit()
            example_fr_data_077_query_audit()
