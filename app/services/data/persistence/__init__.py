"""Shared DATA persistence infrastructure: SQLite, locks, migrations, files, cache.

Owns storage mechanics only. Durable audit evidence lives in ``app.services.data.audit``
because it carries a cross-domain contract with its own authorization semantics.

The package surface exposes the governed storage operations while focused files own
their individual persistence use cases.
"""

from app.services.data.persistence.backup import (
    create_backup,
    enforce_retention_policy,
    restore_from_backup,
)
from app.services.data.persistence.cache import (
    clear_cache_entry,
    clear_data_cache,
    get_cache_entry,
    put_cache_entry,
)
from app.services.data.persistence.dataset_writer import (
    load_dataset,
    load_local_dataset,
    save_dataset,
    save_market_data,
)
from app.services.data.persistence.external_import import (
    describe_import_dialects,
    import_external_dataset,
)
from app.services.data.persistence.locking import WriteLock, acquire_write_lock
from app.services.data.persistence.migrations import (
    DATA_MIGRATION_STEPS,
    run_data_migrations,
    run_domain_migrations,
)
from app.services.data.persistence.transactions import execute_transaction

__all__ = [
    "DATA_MIGRATION_STEPS",
    "WriteLock",
    "acquire_write_lock",
    "clear_cache_entry",
    "clear_data_cache",
    "create_backup",
    "describe_import_dialects",
    "enforce_retention_policy",
    "execute_transaction",
    "get_cache_entry",
    "import_external_dataset",
    "load_dataset",
    "load_local_dataset",
    "put_cache_entry",
    "restore_from_backup",
    "run_data_migrations",
    "run_domain_migrations",
    "save_dataset",
    "save_market_data",
]
