"""Shared DATA persistence infrastructure: SQLite, locks, migrations, files, cache.

Owns storage mechanics only. Durable audit evidence lives in
``app.services.data.evidence`` because it carries a cross-domain contract with its
own authorization semantics.

The package surface exposes the governed storage operations while focused files own
their individual persistence use cases.
"""

import typing

# CRUD imports intentionally initialize first. Feature modules consume this package
# boundary, while some legacy infrastructure modules import those features.
# ruff: noqa: I001


# Explicit imports keep type checking exact; runtime stays lazy.
if typing.TYPE_CHECKING:
    from app.services.data.persistence.create import (
        create_catalog_artifact_records,
        create_catalog_reference_records,
        create_fetch_log_record,
        create_quality_event_record,
        create_provider_specification_revision,
        create_audit_event_record,
        create_backfill_checkpoint_record,
        create_feed_record,
        create_research_observation_record,
        create_research_source_record,
        create_runtime_append_record,
        create_runtime_put_once_record,
        create_source_attempt_record,
        create_update_job_record,
    )
    from app.services.data.persistence.delete import delete_cache_records
    from app.services.data.persistence.read import (
        read_economic_calendar_coverage_records,
        read_catalog_coverage,
        read_catalog_event_records,
        read_catalog_files_for_range,
        read_catalog_reference_records,
        read_catalog_unverified_count,
        read_audit_event_records,
        read_cache_record,
        read_cache_records,
        read_committed_backfill_record,
        read_economic_event_records,
        read_feed_record,
        read_latest_backfill_end,
        read_broker_records,
        read_instrument_records,
        read_instrument_spec_record,
        read_market_series_exists,
        read_market_series_records,
        read_latest_research_observation_record,
        read_latest_research_source_record,
        read_prepared_backfill_records,
        read_recent_source_attempt_records,
        read_ready_dataset_catalog_records,
        read_research_observation_records,
        read_research_source_records,
        read_runtime_collection_records,
        read_runtime_partition_records,
        read_runtime_record,
        read_source_attempt_count,
        read_source_state_record,
        read_update_job_definition_record,
        read_update_job_enabled,
        read_update_job_identity,
        read_update_job_start_state,
        read_update_job_status_record,
        read_verified_research_source_record,
        read_provider_specification_revision_as_of,
        read_provider_specification_revision_interval,
        read_provider_specification_revisions,
    )
    from app.services.data.persistence.update import (
        reconcile_economic_event_definition_records,
        update_economic_calendar_coverage_record,
        update_backfill_failure,
        update_backfill_finalization,
        update_backfill_lease,
        update_cache_record,
        update_economic_event_records,
        update_economic_event_definition_record,
        update_feed_record,
        update_market_series_records,
        update_instrument_spec_record,
        update_provider_specification_revision,
        update_job_recovery_blocked,
        update_job_run_failure,
        update_job_run_lease,
        update_job_run_success,
        update_job_start,
        update_job_stop,
        update_runtime_compare_and_swap_record,
        update_runtime_transition_records,
        update_runtime_upsert_record,
        update_source_state_with_audit,
        update_verified_research_source_record,
    )
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

# Public export name to the module and attribute that owns it. Resolved on
# first access so importing this boundary never loads every feature.
_EXPORTS: dict[str, tuple[str, str]] = {
    "read_instrument_spec_record": (
        "app.services.data.persistence.read",
        "read_instrument_spec_record",
    ),
    "read_market_series_exists": (
        "app.services.data.persistence.read",
        "read_market_series_exists",
    ),
    "update_market_series_records": (
        "app.services.data.persistence.update",
        "update_market_series_records",
    ),
    "update_instrument_spec_record": (
        "app.services.data.persistence.update",
        "update_instrument_spec_record",
    ),
    "DATA_MIGRATION_STEPS": (
        "app.services.data.persistence.migrations",
        "DATA_MIGRATION_STEPS",
    ),
    "WriteLock": ("app.services.data.persistence.locking", "WriteLock"),
    "acquire_write_lock": (
        "app.services.data.persistence.locking",
        "acquire_write_lock",
    ),
    "clear_cache_entry": ("app.services.data.persistence.cache", "clear_cache_entry"),
    "clear_data_cache": ("app.services.data.persistence.cache", "clear_data_cache"),
    "create_audit_event_record": (
        "app.services.data.persistence.create",
        "create_audit_event_record",
    ),
    "create_backfill_checkpoint_record": (
        "app.services.data.persistence.create",
        "create_backfill_checkpoint_record",
    ),
    "create_backup": ("app.services.data.persistence.backup", "create_backup"),
    "create_catalog_artifact_records": (
        "app.services.data.persistence.create",
        "create_catalog_artifact_records",
    ),
    "create_catalog_reference_records": (
        "app.services.data.persistence.create",
        "create_catalog_reference_records",
    ),
    "create_feed_record": (
        "app.services.data.persistence.create",
        "create_feed_record",
    ),
    "create_fetch_log_record": (
        "app.services.data.persistence.create",
        "create_fetch_log_record",
    ),
    "create_provider_specification_revision": (
        "app.services.data.persistence.create",
        "create_provider_specification_revision",
    ),
    "create_quality_event_record": (
        "app.services.data.persistence.create",
        "create_quality_event_record",
    ),
    "create_research_observation_record": (
        "app.services.data.persistence.create",
        "create_research_observation_record",
    ),
    "create_research_source_record": (
        "app.services.data.persistence.create",
        "create_research_source_record",
    ),
    "create_runtime_append_record": (
        "app.services.data.persistence.create",
        "create_runtime_append_record",
    ),
    "create_runtime_put_once_record": (
        "app.services.data.persistence.create",
        "create_runtime_put_once_record",
    ),
    "create_source_attempt_record": (
        "app.services.data.persistence.create",
        "create_source_attempt_record",
    ),
    "create_update_job_record": (
        "app.services.data.persistence.create",
        "create_update_job_record",
    ),
    "delete_cache_records": (
        "app.services.data.persistence.delete",
        "delete_cache_records",
    ),
    "describe_import_dialects": (
        "app.services.data.persistence.external_import",
        "describe_import_dialects",
    ),
    "enforce_retention_policy": (
        "app.services.data.persistence.backup",
        "enforce_retention_policy",
    ),
    "execute_transaction": (
        "app.services.data.persistence.transactions",
        "execute_transaction",
    ),
    "get_cache_entry": ("app.services.data.persistence.cache", "get_cache_entry"),
    "import_external_dataset": (
        "app.services.data.persistence.external_import",
        "import_external_dataset",
    ),
    "load_dataset": ("app.services.data.persistence.dataset_writer", "load_dataset"),
    "load_local_dataset": (
        "app.services.data.persistence.dataset_writer",
        "load_local_dataset",
    ),
    "put_cache_entry": ("app.services.data.persistence.cache", "put_cache_entry"),
    "read_audit_event_records": (
        "app.services.data.persistence.read",
        "read_audit_event_records",
    ),
    "read_broker_records": (
        "app.services.data.persistence.read",
        "read_broker_records",
    ),
    "read_cache_record": ("app.services.data.persistence.read", "read_cache_record"),
    "read_cache_records": ("app.services.data.persistence.read", "read_cache_records"),
    "read_catalog_coverage": (
        "app.services.data.persistence.read",
        "read_catalog_coverage",
    ),
    "read_catalog_event_records": (
        "app.services.data.persistence.read",
        "read_catalog_event_records",
    ),
    "read_catalog_files_for_range": (
        "app.services.data.persistence.read",
        "read_catalog_files_for_range",
    ),
    "read_catalog_reference_records": (
        "app.services.data.persistence.read",
        "read_catalog_reference_records",
    ),
    "read_catalog_unverified_count": (
        "app.services.data.persistence.read",
        "read_catalog_unverified_count",
    ),
    "read_committed_backfill_record": (
        "app.services.data.persistence.read",
        "read_committed_backfill_record",
    ),
    "read_economic_calendar_coverage_records": (
        "app.services.data.persistence.read",
        "read_economic_calendar_coverage_records",
    ),
    "read_economic_event_records": (
        "app.services.data.persistence.read",
        "read_economic_event_records",
    ),
    "read_feed_record": ("app.services.data.persistence.read", "read_feed_record"),
    "read_instrument_records": (
        "app.services.data.persistence.read",
        "read_instrument_records",
    ),
    "read_latest_backfill_end": (
        "app.services.data.persistence.read",
        "read_latest_backfill_end",
    ),
    "read_latest_research_observation_record": (
        "app.services.data.persistence.read",
        "read_latest_research_observation_record",
    ),
    "read_latest_research_source_record": (
        "app.services.data.persistence.read",
        "read_latest_research_source_record",
    ),
    "read_market_series_records": (
        "app.services.data.persistence.read",
        "read_market_series_records",
    ),
    "read_prepared_backfill_records": (
        "app.services.data.persistence.read",
        "read_prepared_backfill_records",
    ),
    "read_provider_specification_revision_as_of": (
        "app.services.data.persistence.read",
        "read_provider_specification_revision_as_of",
    ),
    "read_provider_specification_revision_interval": (
        "app.services.data.persistence.read",
        "read_provider_specification_revision_interval",
    ),
    "read_provider_specification_revisions": (
        "app.services.data.persistence.read",
        "read_provider_specification_revisions",
    ),
    "read_ready_dataset_catalog_records": (
        "app.services.data.persistence.read",
        "read_ready_dataset_catalog_records",
    ),
    "read_recent_source_attempt_records": (
        "app.services.data.persistence.read",
        "read_recent_source_attempt_records",
    ),
    "read_research_observation_records": (
        "app.services.data.persistence.read",
        "read_research_observation_records",
    ),
    "read_research_source_records": (
        "app.services.data.persistence.read",
        "read_research_source_records",
    ),
    "read_runtime_collection_records": (
        "app.services.data.persistence.read",
        "read_runtime_collection_records",
    ),
    "read_runtime_partition_records": (
        "app.services.data.persistence.read",
        "read_runtime_partition_records",
    ),
    "read_runtime_record": (
        "app.services.data.persistence.read",
        "read_runtime_record",
    ),
    "read_source_attempt_count": (
        "app.services.data.persistence.read",
        "read_source_attempt_count",
    ),
    "read_source_state_record": (
        "app.services.data.persistence.read",
        "read_source_state_record",
    ),
    "read_update_job_definition_record": (
        "app.services.data.persistence.read",
        "read_update_job_definition_record",
    ),
    "read_update_job_enabled": (
        "app.services.data.persistence.read",
        "read_update_job_enabled",
    ),
    "read_update_job_identity": (
        "app.services.data.persistence.read",
        "read_update_job_identity",
    ),
    "read_update_job_start_state": (
        "app.services.data.persistence.read",
        "read_update_job_start_state",
    ),
    "read_update_job_status_record": (
        "app.services.data.persistence.read",
        "read_update_job_status_record",
    ),
    "read_verified_research_source_record": (
        "app.services.data.persistence.read",
        "read_verified_research_source_record",
    ),
    "reconcile_economic_event_definition_records": (
        "app.services.data.persistence.update",
        "reconcile_economic_event_definition_records",
    ),
    "restore_from_backup": (
        "app.services.data.persistence.backup",
        "restore_from_backup",
    ),
    "run_data_migrations": (
        "app.services.data.persistence.migrations",
        "run_data_migrations",
    ),
    "run_domain_migrations": (
        "app.services.data.persistence.migrations",
        "run_domain_migrations",
    ),
    "save_dataset": ("app.services.data.persistence.dataset_writer", "save_dataset"),
    "save_market_data": (
        "app.services.data.persistence.dataset_writer",
        "save_market_data",
    ),
    "update_backfill_failure": (
        "app.services.data.persistence.update",
        "update_backfill_failure",
    ),
    "update_backfill_finalization": (
        "app.services.data.persistence.update",
        "update_backfill_finalization",
    ),
    "update_backfill_lease": (
        "app.services.data.persistence.update",
        "update_backfill_lease",
    ),
    "update_cache_record": (
        "app.services.data.persistence.update",
        "update_cache_record",
    ),
    "update_economic_calendar_coverage_record": (
        "app.services.data.persistence.update",
        "update_economic_calendar_coverage_record",
    ),
    "update_economic_event_definition_record": (
        "app.services.data.persistence.update",
        "update_economic_event_definition_record",
    ),
    "update_economic_event_records": (
        "app.services.data.persistence.update",
        "update_economic_event_records",
    ),
    "update_feed_record": (
        "app.services.data.persistence.update",
        "update_feed_record",
    ),
    "update_job_recovery_blocked": (
        "app.services.data.persistence.update",
        "update_job_recovery_blocked",
    ),
    "update_job_run_failure": (
        "app.services.data.persistence.update",
        "update_job_run_failure",
    ),
    "update_job_run_lease": (
        "app.services.data.persistence.update",
        "update_job_run_lease",
    ),
    "update_job_run_success": (
        "app.services.data.persistence.update",
        "update_job_run_success",
    ),
    "update_job_start": ("app.services.data.persistence.update", "update_job_start"),
    "update_job_stop": ("app.services.data.persistence.update", "update_job_stop"),
    "update_provider_specification_revision": (
        "app.services.data.persistence.update",
        "update_provider_specification_revision",
    ),
    "update_runtime_compare_and_swap_record": (
        "app.services.data.persistence.update",
        "update_runtime_compare_and_swap_record",
    ),
    "update_runtime_transition_records": (
        "app.services.data.persistence.update",
        "update_runtime_transition_records",
    ),
    "update_runtime_upsert_record": (
        "app.services.data.persistence.update",
        "update_runtime_upsert_record",
    ),
    "update_source_state_with_audit": (
        "app.services.data.persistence.update",
        "update_source_state_with_audit",
    ),
    "update_verified_research_source_record": (
        "app.services.data.persistence.update",
        "update_verified_research_source_record",
    ),
}


def __getattr__(name: str) -> object:
    """Resolve one public export on first access.

    Args:
        name: Public export name.

    Returns:
        The resolved public function.

    Raises:
        AttributeError: If the name is not part of the public boundary.
    """
    target = _EXPORTS.get(name)
    if target is None:
        message = f"module {__name__!r} has no attribute {name!r}"
        raise AttributeError(message)
    from importlib import import_module

    return getattr(import_module(target[0]), target[1])


def __dir__() -> list[str]:
    """List the public export surface.

    Returns:
        Sorted public export names.
    """
    return sorted(_EXPORTS)


__all__ = [
    "DATA_MIGRATION_STEPS",
    "WriteLock",
    "acquire_write_lock",
    "clear_cache_entry",
    "clear_data_cache",
    "create_audit_event_record",
    "create_backfill_checkpoint_record",
    "create_backup",
    "create_catalog_artifact_records",
    "create_catalog_reference_records",
    "create_feed_record",
    "create_fetch_log_record",
    "create_provider_specification_revision",
    "create_provider_specification_revision",
    "create_quality_event_record",
    "create_research_observation_record",
    "create_research_source_record",
    "create_runtime_append_record",
    "create_runtime_put_once_record",
    "create_source_attempt_record",
    "create_update_job_record",
    "delete_cache_records",
    "describe_import_dialects",
    "enforce_retention_policy",
    "execute_transaction",
    "get_cache_entry",
    "import_external_dataset",
    "load_dataset",
    "load_local_dataset",
    "put_cache_entry",
    "read_audit_event_records",
    "read_broker_records",
    "read_cache_record",
    "read_cache_records",
    "read_catalog_coverage",
    "read_catalog_event_records",
    "read_catalog_files_for_range",
    "read_catalog_reference_records",
    "read_catalog_unverified_count",
    "read_committed_backfill_record",
    "read_economic_calendar_coverage_records",
    "read_economic_event_records",
    "read_feed_record",
    "read_instrument_records",
    "read_instrument_spec_record",
    "read_latest_backfill_end",
    "read_latest_research_observation_record",
    "read_latest_research_source_record",
    "read_market_series_exists",
    "read_market_series_records",
    "read_prepared_backfill_records",
    "read_provider_specification_revision_as_of",
    "read_provider_specification_revision_as_of",
    "read_provider_specification_revision_interval",
    "read_provider_specification_revision_interval",
    "read_provider_specification_revisions",
    "read_provider_specification_revisions",
    "read_ready_dataset_catalog_records",
    "read_recent_source_attempt_records",
    "read_research_observation_records",
    "read_research_source_records",
    "read_runtime_collection_records",
    "read_runtime_partition_records",
    "read_runtime_record",
    "read_source_attempt_count",
    "read_source_state_record",
    "read_update_job_definition_record",
    "read_update_job_enabled",
    "read_update_job_identity",
    "read_update_job_start_state",
    "read_update_job_status_record",
    "read_verified_research_source_record",
    "reconcile_economic_event_definition_records",
    "restore_from_backup",
    "run_data_migrations",
    "run_domain_migrations",
    "save_dataset",
    "save_market_data",
    "update_backfill_failure",
    "update_backfill_finalization",
    "update_backfill_lease",
    "update_cache_record",
    "update_economic_calendar_coverage_record",
    "update_economic_event_definition_record",
    "update_economic_event_records",
    "update_feed_record",
    "update_job_recovery_blocked",
    "update_job_run_failure",
    "update_job_run_lease",
    "update_job_run_success",
    "update_job_start",
    "update_job_stop",
    "update_market_series_records",
    "update_provider_specification_revision",
    "update_provider_specification_revision",
    "update_runtime_compare_and_swap_record",
    "update_runtime_transition_records",
    "update_runtime_upsert_record",
    "update_source_state_with_audit",
    "update_verified_research_source_record",
]
