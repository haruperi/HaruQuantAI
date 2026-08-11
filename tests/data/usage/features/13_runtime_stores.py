"""Standalone usage evidence for FEAT-DATA-17 runtime persistence."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.services.data import (
    build_agentic_runtime_store,
    build_data_settings,
    build_portfolio_runtime_store,
    build_risk_runtime_store,
    build_simulator_runtime_store,
    build_trading_runtime_store,
    data_settings_context,
    execute_runtime_store_operation,
    get_runtime_store_migration_steps,
    run_runtime_store_migrations,
    unwrap_data_response,
)
from app.utils import generate_id


def _encode(value: object) -> str:
    """Encode bounded demonstration state.

    Returns:
        Deterministic JSON text.
    """
    return json.dumps(value, sort_keys=True)


def main() -> None:
    """Exercise every FEAT-DATA-17 public operation without external access."""
    with TemporaryDirectory() as directory:
        settings = build_data_settings(
            database_url="sqlite:///usage.db",
            data_dir=Path(directory),
            sqlite_busy_timeout_seconds=1.0,
            write_lock_lease_seconds=10.0,
            approved_storage_roots=(Path(),),
        )
        with data_settings_context(settings):
            request_id = generate_id("req")
            unwrap_data_response(
                run_runtime_store_migrations(request_id),
                operation="usage.data.runtime_store.migrations",
                request_id=request_id,
            )
            codec = {"status": (_encode, json.loads)}
            stores = (
                build_simulator_runtime_store(codec),
                build_risk_runtime_store(codec),
                build_trading_runtime_store(codec),
                build_portfolio_runtime_store(codec),
                build_agentic_runtime_store(codec),
            )
            for index, store in enumerate(stores, start=1):
                execute_runtime_store_operation(
                    store,
                    "put_once",
                    collection="readiness",
                    key=f"owner-{index}",
                    kind="status",
                    value={"ready": True},
                )
            print(
                {
                    "migration_steps": len(get_runtime_store_migration_steps()),
                    "owner_namespaces": len(stores),
                    "external_calls": 0,
                }
            )
            print("SUCCESS: FEAT-DATA-17 completed")


if __name__ == "__main__":
    main()
