"""WF-DATA-021: verify migration, backup, restore, and retention lifecycle."""

from __future__ import annotations

import sys
from pathlib import Path
from tempfile import TemporaryDirectory

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.kernel.identity import generate_id
from app.services.data import (
    build_backup_target,
    build_data_settings,
    create_backup,
    data_settings_context,
    enforce_retention_policy,
    restore_from_backup,
    run_data_migrations,
    unwrap_data_response,
)

WORKFLOW_ID = "WF-DATA-021"
STAGES = (
    "Apply the complete authoritative Data migration manifest.",
    "Verify the immutable ledger through an idempotent rerun.",
    "Create a content-addressed backup under the approved root.",
    "Restore and verify the exact original payload.",
    "Evaluate retention without deleting non-workflow data.",
)


def _stage(number: int) -> None:
    """Print one README-aligned stage separator."""
    print(f"\n{'=' * 88}\nStage {number}: {STAGES[number - 1]}\n{'=' * 88}")


def _unwrap(response: object, operation: str) -> object:
    """Unwrap one successful Data response."""
    return unwrap_data_response(
        response,
        operation=operation,
        request_id=generate_id("req"),
    )


def main() -> None:
    """Run the disposable persistence-maintenance lifecycle."""
    print("INPUT BOUNDARY: operator request against a disposable approved Data store")
    with TemporaryDirectory(prefix="wf-data-021-") as temporary:
        root = Path(temporary)
        for relative in ("data/raw", "data/cache", "artifacts/data"):
            (root / relative).mkdir(parents=True)
        settings = build_data_settings(
            database_url="sqlite:///data/cache/workflow.sqlite3",
            data_dir=root,
            sqlite_busy_timeout_seconds=1.0,
            write_lock_lease_seconds=10.0,
            approved_storage_roots=(
                Path("data/raw"),
                Path("data/cache"),
                Path("artifacts/data"),
            ),
        )
        with data_settings_context(settings):
            # Stage 1
            _stage(1)
            first = _unwrap(run_data_migrations(generate_id("req")), "migrate")

            # Stage 2
            _stage(2)
            second = _unwrap(run_data_migrations(generate_id("req")), "migrate")
            assert not second.applied_ids
            assert second.skipped_ids

            # Stage 3
            _stage(3)
            payload = root / "data/raw/EURUSD.csv"
            original = b"timestamp,close\n2026-07-30T12:00:00Z,1.1000\n"
            payload.write_bytes(original)
            target = build_backup_target(
                relative_path=Path("data/raw/EURUSD.csv"),
                schema_version="v1",
                normalization_version="v1",
            )
            manifest = _unwrap(create_backup((target,)), "backup")

            # Stage 4
            _stage(4)
            payload.write_bytes(b"changed")
            restore = _unwrap(
                restore_from_backup(manifest.manifest_id),
                "restore",
            )
            assert payload.read_bytes() == original

            # Stage 5
            _stage(5)
            retained = _unwrap(
                enforce_retention_policy("EURUSD.csv", 30, dry_run=True),
                "retention",
            )
            evidence = {
                "initially_applied": tuple(first.applied_ids),
                "idempotently_skipped": tuple(second.skipped_ids),
                "manifest_id": manifest.manifest_id,
                "restored": restore.restored_count,
                "retention_candidates": retained,
            }
            print(f"OUTPUT BOUNDARY: {evidence}")
            print(f"SUCCESS: {WORKFLOW_ID} completed")


if __name__ == "__main__":
    main()
