"""Exclusive database access and storage CRUD for the application.

Description:
    This is the only application module permitted to import database drivers,
    open connections, execute SQL, or manage schemas and database transactions.
    Small stores group related CRUD, queries, aggregates, storage serialization,
    and atomic conditional writes. DatabaseManager owns handles; stores return
    records and results. Connection/transaction methods are internal infrastructure:
    other application modules must never borrow handles or supply connections.

    Business logic MUST NOT be added here. Configuration validation and snapshots
    belong to app.host.settings; job lifecycle and worker lease policy belong to
    app.host.jobs; scope binding belongs to app.host.session; startup recovery
    sequencing belongs to app.host.bootstrap. Trading defaults and interpretation
    belong to workspace services. Python, HTTP and CLI access belongs to each
    business owner: settings access in settings, lease access in jobs, recovery
    access in bootstrap, and database inspection in diagnostics.
    No service callbacks, domain-model imports, business seeds, job-state
    decisions, authorization decisions, or transport dependencies
    are allowed in this module. Future features add narrow CRUD operations here
    and call them from their owning service.

    Domain services supply complete creation records, business defaults, domain
    timestamps and conflict-update field choices. CRUD must not invent missing
    trading values, session definitions, dataset IDs or quality scores. Existing
    schema DEFAULT declarations remain compatibility infrastructure; storage
    audit timestamps, revisions and serialization constraints belong here.

Purpose:
    FEAT-HOST-PERSISTENCE: Exclusive transactional database access and storage CRUD.
    Preserve storage consistency without deciding application behavior.

Key Capabilities:
    - FR-HOST-PERSISTENCE-SCHEMA-VERIFICATION: Create and inspect storage schemas.
      Associated: `SchemaManager.initialize()`, `SchemaManager.verify_schema()`,
        `SchemaManager.drop_obsolete_sessions()`
      Logging: INFO initialization; ERROR incompatible required tables/version.
    - FR-HOST-PERSISTENCE-TRANSACTIONS: Atomic writes and connection ownership.
      Associated: `DatabaseManager.connection()`, `DatabaseManager.transaction()`
      Logging: DEBUG access/commit; WARNING rollback; ERROR contention.
    - FR-HOST-PERSISTENCE-TYPED-REPOSITORY: Scoped JSON entity CRUD and revisions.
      Associated: `TypedRepository.get()`, `save()`, `delete()`, `list()`
      Logging: DEBUG reads; INFO writes; WARNING revision conflicts.
    - FR-HOST-PERSISTENCE-SETTINGS: Setting reads, batch writes/deletes and backups.
      Associated: `SettingsStore.read_all()`, `SettingsStore.update_batch()`,
        `SettingsStore.backup_to()`
      Logging: DEBUG reads; INFO changes; WARNING unavailable/corrupt data.
    - FR-HOST-PERSISTENCE-JOBS: Job row reads/writes and conditional field updates.
      Associated: `JobStore.get_job()`, `upsert_job()`, `update_statuses()`
      Logging: DEBUG reads; INFO writes and affected-row count.
    - FR-HOST-PERSISTENCE-LEASES: Atomic reservation row predicates and CRUD.
      Associated: `LeaseStore.acquire()`, `renew()`, `release()`, `prune_expired()`
      Logging: DEBUG conditional results/reads; INFO deleted-row count.
    - FR-HOST-PERSISTENCE-INSTRUMENTS: Instrument row CRUD.
      Associated: `InstrumentStore.create()`, `get_by_symbol()`, `update()`, `delete()`
      Logging: DEBUG reads; INFO writes without payload values.
    - FR-HOST-PERSISTENCE-SESSIONS: Trading-session row CRUD.
      Associated: `SessionStore.upsert()`, `get_by_name()`, `delete()`
      Logging: DEBUG reads; INFO write results.
    - FR-HOST-PERSISTENCE-HOST-SESSIONS: Login lifecycle record CRUD.
      Associated: `HostSessionStore.initialize()`, `create()`, `list_records()`,
        `update_status()`
      Logging: INFO storage verification/writes and counts; DEBUG reads.
    - FR-HOST-PERSISTENCE-DATASETS: Metadata CRUD and bar aggregates.
      Associated: `DatasetStore.save()`, `get_by_id()`, `sum_bars()`
      Logging: DEBUG reads; INFO writes.
    - FR-HOST-PERSISTENCE-BASKETS: Transactional group and membership CRUD.
      Associated: `BasketStore.save()`, `get()`, `delete()`, `count()`
      Logging: DEBUG reads; INFO write/delete results.
    - FR-HOST-PERSISTENCE-BROKERS: Broker profile and stock configuration persistence.
      Associated: `BrokerStore.list_profiles()`, `BrokerStore.get_profile()`,
        `BrokerStore.get_profile_by_name()`, `BrokerStore.create_profile()`,
        `BrokerStore.update_profile()`, `BrokerStore.delete_profile()`,
        `BrokerStore.list_stocks()`, `BrokerStore.replace_stocks()`,
        `BrokerStore.get_counts()`, `BrokerStore.ensure_defaults()`
      Logging: DEBUG reads; INFO writes and lifecycle events.
    - FR-HOST-PERSISTENCE-LOGS: Data Manager operational audit log CRUD.
      Associated: `LogStore.create()`, `LogStore.list_logs()`, `LogStore.clear()`,
        `LogStore.count()`
      Logging: DEBUG reads; INFO writes and clears.
    - FR-HOST-PERSISTENCE-ANALYTICAL-QUERY: Direct DuckDB analytical query execution.
      Associated: `query_duckdb()`, `DatabaseManager.query_duckdb()`
      Logging: DEBUG execution with query text.
    - FR-HOST-PERSISTENCE-INTEGRITY-CHECK: Query physical SQLite integrity.
      Associated: `DatabaseManager.check_integrity()`
      Logging: INFO clean result; ERROR detected corruption.

Python API Usage:
    ```python
    from app.host.persistence import DatabaseManager

    db = DatabaseManager(":memory:")
    db.initialize()  # Storage only; domain services initialize business defaults.
    rows = db.datasets.list_datasets(limit=50)
    db.close()
    ```

CLI Usage:
    No persistence CLI or business orchestration lives here. Diagnostics owns it:
    ```bash
    uv run python -m app.host.diagnostics --status --db path/to/database.db
    uv run python -m app.host.diagnostics --integrity-check --db path/to/database.db
    ```
"""

from __future__ import annotations

from app.host.persistence.base import TypedRepository
from app.host.persistence.engine import (
    DEFAULT_DATABASE_PATH,
    DEFAULT_READ_LIMIT,
    MAX_BATCH_SIZE,
    MAX_READ_LIMIT,
    SCHEMA_VERSION,
    DatabaseManager,
    canonical_json,
    get_database_manager,
    now_utc_iso,
    query_duckdb,
    validate_identifier,
    validate_json_depth,
)
from app.host.persistence.errors import (
    CorruptDataError,
    IncompatibleSchemaError,
    LeaseExpiredError,
    PersistenceError,
    RevisionConflictError,
    StorageBusyError,
    ValidationError,
)
from app.host.persistence.models import (
    DatabaseStatus,
    EntityRecord,
    HostSessionRecord,
    MigrationRecord,
    Page,
    SettingRecord,
    SettingsPage,
)
from app.host.persistence.schema import (
    SchemaManager,
    _migrate_datamgr_tables,
)
from app.host.persistence.stores.baskets import BasketStore
from app.host.persistence.stores.brokers import BrokerStore
from app.host.persistence.stores.datasets import DatasetStore
from app.host.persistence.stores.host_sessions import HostSessionStore
from app.host.persistence.stores.instruments import InstrumentStore
from app.host.persistence.stores.jobs import JobStore, LeaseStore, normalize_sqx_date
from app.host.persistence.stores.logs import LogStore
from app.host.persistence.stores.settings import SettingsStore
from app.host.persistence.stores.trading_sessions import SessionStore

__all__ = [
    "DEFAULT_DATABASE_PATH",
    "DEFAULT_READ_LIMIT",
    "MAX_BATCH_SIZE",
    "MAX_READ_LIMIT",
    "SCHEMA_VERSION",
    "BasketStore",
    "BrokerStore",
    "CorruptDataError",
    "DatabaseManager",
    "DatabaseStatus",
    "DatasetStore",
    "EntityRecord",
    "HostSessionRecord",
    "HostSessionStore",
    "IncompatibleSchemaError",
    "InstrumentStore",
    "JobStore",
    "LeaseExpiredError",
    "LeaseStore",
    "LogStore",
    "MigrationRecord",
    "Page",
    "PersistenceError",
    "RevisionConflictError",
    "SchemaManager",
    "SessionStore",
    "SettingRecord",
    "SettingsPage",
    "SettingsStore",
    "StorageBusyError",
    "TypedRepository",
    "ValidationError",
    "_migrate_datamgr_tables",
    "canonical_json",
    "get_database_manager",
    "normalize_sqx_date",
    "now_utc_iso",
    "query_duckdb",
    "validate_identifier",
    "validate_json_depth",
]
