"""Run isolated SQLite, artifact, cache, lock, migration, and audit examples (FEAT-DATA-06)."""

from __future__ import annotations

import sys
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.services.data import (
    acquire_write_lock,
    build_backup_target,
    build_cache_read_request,
    build_cache_write_request,
    build_column_mapping,
    build_data_quality_report,
    build_data_settings,
    build_dataset_load_request,
    build_dataset_save_request,
    build_external_import_request,
    build_market_dataset,
    build_migration_request,
    build_migration_step,
    build_ohlcv_record,
    build_statement_plan,
    build_transaction_request,
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
    restore_from_backup,
    run_data_migrations,
    run_domain_migrations,
    save_dataset,
)
from app.utils import create_audit_event, create_auth_context, generate_id

_OBSERVED_AT = datetime(2026, 7, 1, 12, 0, tzinfo=UTC)


def _header(title: str) -> None:
    """Print one example heading."""
    print(f"\n{'=' * 88}\n{title}\n{'=' * 88}")


def _format_result(obj: Any) -> str:
    """Dynamically format the output result type and field/key signature."""
    cls = type(obj)
    type_name = cls.__name__
    if hasattr(cls, "model_fields"):
        keys = ", ".join(cls.model_fields.keys())
        return f"Output Result -> {type_name}({keys}) : {type_name}"
    if isinstance(obj, dict):
        keys = ", ".join(obj.keys())
        return f"Output Result -> dict({keys}) : dict"
    if hasattr(obj, "__dict__"):
        keys = ", ".join(vars(obj).keys())
        return f"Output Result -> {type_name}({keys}) : {type_name}"
    return f"Output Result -> {type_name} : {type_name}"


def _quality():
    """Build clean quality evidence for one persisted dataset."""
    return build_data_quality_report(
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


def _dataset():
    """Build a small realistic dataset for persistence examples."""
    records = tuple(
        build_ohlcv_record(
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
    return build_market_dataset(
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


def fr_data_014() -> None:
    """FR-DATA-014: Stage 1 — Execute a bounded SQLite transaction with busy-timeout and lock governance."""
    _header(
        "Stage 1: SQLite Transaction Execution - Transaction Execution (FR-DATA-014)"
    )
    request = build_transaction_request(
        plan=build_statement_plan(
            statements=("SELECT 1;",),
            parameter_sets=((),),
            max_rows=10,
        ),
        request_id=generate_id("req"),
    )
    response = execute_transaction(request)
    print(_format_result(response))
    if response.status == "success" and response.data is not None:
        outcome = response.data
        print(f"Data -> TransactionOutcome(rows={len(outcome.rows)})")


def fr_data_015() -> None:
    """FR-DATA-015: Stage 2 — Apply step-level domain migrations with ledger verification and write-lock acquisition."""
    _header("Stage 2: Domain Schema Migration - Migration Step Execution (FR-DATA-015)")
    statement = (
        "CREATE TABLE IF NOT EXISTS usage_notes (id TEXT PRIMARY KEY, content TEXT)"
    )
    step = build_migration_step(
        domain="usage",
        migration_id="001_create_usage_notes",
        checksum="usage-notes-v1",
        statements=(statement,),
    )
    request = build_migration_request(
        domain="usage",
        steps=(step,),
        request_id=generate_id("req"),
    )
    response = run_domain_migrations(request)
    print(_format_result(response))
    if response.status == "success" and response.data is not None:
        result = response.data
        print(
            f"Data -> MigrationResult(domain={result.domain}, applied={len(result.applied_ids)})"
        )


def fr_data_016() -> None:
    """FR-DATA-016: Stage 3 — Acquire exclusive path-scoped write lock for safe file mutations."""
    _header("Stage 3: Exclusive Path Locking - Path Lock Acquisition (FR-DATA-016)")
    req_id = generate_id("req")
    target_path = Path("data/raw/AAPL_M1.csv")
    lock_res = acquire_write_lock(target_path, request_id=req_id)
    print(_format_result(lock_res))
    if lock_res.status == "success" and lock_res.data is not None:
        lock = lock_res.data
        print(
            f"Data -> WriteLockLease(path={getattr(lock, 'path', target_path)}, request_id={req_id})"
        )


def fr_data_017_018() -> None:
    """FR-DATA-017, FR-DATA-018: Stage 4 — Atomic dataset commit, versioned manifest generation, and manifest-verifying load."""
    _header(
        "Stage 4: Dataset Serialization & Commit - Save and Load Dataset (FR-DATA-017, FR-DATA-018)"
    )
    dataset = _dataset()
    req_id = dataset.request_id
    save_req = build_dataset_save_request(
        dataset=dataset,
        relative_path=Path("data/raw/AAPL_M1.csv"),
        format="csv",
        overwrite=True,
        request_id=req_id,
    )
    save_res = save_dataset(save_req)
    print(_format_result(save_res))

    load_req = build_dataset_load_request(
        relative_path=Path("data/raw/AAPL_M1.csv"),
        format="csv",
        request_id=req_id,
    )
    load_res = load_dataset(load_req)
    print(_format_result(load_res))
    if load_res.status == "success" and load_res.data is not None:
        ds = load_res.data
        print(f"Data -> MarketDataset(symbol={ds.symbol}, records={ds.record_count})")


def fr_data_019() -> None:
    """FR-DATA-019: Stage 5 — Versioned TTL cache read, write, and invalidation lifecycle."""
    _header(
        "Stage 5: Versioned TTL Cache Lifecycle - Cache Put/Get/Clear (FR-DATA-019)"
    )
    req_id = generate_id("req")
    dataset = _dataset()
    write_req = build_cache_write_request(
        dataset=dataset,
        key="cache-key-aapl-m1",
        ttl_seconds=300,
        source_revision="download-20260701",
        raw_data_hash="hash123",
        request_id=req_id,
    )
    write_res = put_cache_entry(write_req)
    print(_format_result(write_res))

    read_req = build_cache_read_request(
        key="cache-key-aapl-m1",
        allow_stale=False,
        request_id=req_id,
    )
    read_res = get_cache_entry(read_req)
    print(_format_result(read_res))

    clear_res = clear_data_cache(req_id)
    print(_format_result(clear_res))


def fr_data_105_106() -> None:
    """FR-DATA-105, FR-DATA-106: Stage 6 — External artifact admission under declared dialect, explicit column mapping, and audit event persistence."""
    _header(
        "Stage 6: External Artifact Admission & Audit - External Import (FR-DATA-105, FR-DATA-106)"
    )
    req_id = generate_id("req")
    dialects_res = describe_import_dialects()
    print(_format_result(dialects_res))
    valid_dialect = "standard"

    external_path = Path("data/raw/external_aapl.csv")
    external_path.parent.mkdir(parents=True, exist_ok=True)
    external_path.write_text(
        "Timestamp,Open,High,Low,Close,Volume\n2026-07-01T12:00:00Z,100,101,99,100.5,1000\n"
    )

    mapping = build_column_mapping(
        timestamp="Timestamp",
        open="Open",
        high="High",
        low="Low",
        close="Close",
        volume="Volume",
    )
    import_req = build_external_import_request(
        relative_path=external_path,
        destination_path=Path("data/processed/imported_aapl.csv"),
        format="csv",
        dialect=valid_dialect,
        mapping=mapping,
        symbol="AAPL",
        data_kind="bars",
        timeframe="M1",
        source_id="external_vendor",
        price_unit="USD",
        volume_unit="shares",
        workflow_context="research",
        precision_policy="decimal_string",
        overwrite=True,
        request_id=req_id,
    )
    import_res = import_external_dataset(import_req)
    print(_format_result(import_res))

    cor_id = generate_id("cor")
    auth = create_auth_context(
        principal_id="operator",
        principal_type="USER",
        roles=("admin",),
        permissions=("data:read", "data:write"),
        scopes=("system",),
        tenant_or_environment="dev",
        request_id=req_id,
        workflow_id=generate_id("wf"),
        correlation_id=cor_id,
        issued_at=_OBSERVED_AT,
    )
    print(_format_result(auth))
    event = create_audit_event(
        event_id=generate_id("evt"),
        timestamp=_OBSERVED_AT,
        domain="data",
        action="DATA_IMPORT",
        request_id=req_id,
        correlation_id=cor_id,
        payload={"imported": "aapl"},
    )
    persist_res = persist_audit_event(event)
    print(_format_result(persist_res))


def fr_data_020_021() -> None:
    """FR-DATA-020, FR-DATA-021: Stage 7 — Data backup snapshot, restore from backup, and retention policy enforcement."""
    _header(
        "Stage 7: Backup, Restore & Retention - Persistence Backup & Retention (FR-DATA-020, FR-DATA-021)"
    )
    backup_target = build_backup_target(
        relative_path=Path("data/cache/persistence.sqlite3"),
        schema_version="v1",
        normalization_version="v1",
    )
    backup_res = create_backup(backup_target)
    print(_format_result(backup_res))

    restore_res = restore_from_backup(backup_target)
    print(_format_result(restore_res))

    retention_res = enforce_retention_policy(
        "AAPL_M1.csv", max_age_days=30, dry_run=True
    )
    print(_format_result(retention_res))


def main() -> None:
    """Execute every functional-requirement demonstration."""
    with TemporaryDirectory(prefix="usage-persistence-") as directory:
        base_dir = Path(directory)
        (base_dir / "data" / "raw").mkdir(parents=True, exist_ok=True)
        (base_dir / "data" / "processed").mkdir(parents=True, exist_ok=True)
        (base_dir / "data" / "cache").mkdir(parents=True, exist_ok=True)
        (base_dir / "artifacts" / "data").mkdir(parents=True, exist_ok=True)
        settings = build_data_settings(
            database_url="sqlite:///data/cache/persistence.sqlite3",
            sqlite_busy_timeout_seconds=5.0,
            write_lock_lease_seconds=30.0,
            data_dir=base_dir,
            approved_storage_roots=(
                Path("data/raw"),
                Path("data/processed"),
                Path("data/cache"),
                Path("artifacts/data"),
            ),
            data_raw_root=Path("data/raw"),
        )
        with data_settings_context(settings):
            run_data_migrations(generate_id("req"))
            print("=" * 80)
            print("FEATURE: FEAT-DATA-06 - Data Persistence and Storage")
            print(
                "PURPOSE: Transaction, migration, locking, dataset, cache, import, backup, restore, retention, and path contracts/operations"
            )
            print(
                "MODULE FLOW: Stage 1 (SQLite Transaction) -> Stage 2 (Domain Migration) -> Stage 3 (Exclusive Locking) -> Stage 4 (Dataset Commit & Load) -> Stage 5 (Versioned Cache) -> Stage 6 (External Admission & Audit) -> Stage 7 (Backup & Retention)"
            )
            print("=" * 80)

            fr_data_014()
            fr_data_015()
            fr_data_016()
            fr_data_017_018()
            fr_data_019()
            fr_data_105_106()
            fr_data_020_021()


if __name__ == "__main__":
    main()
