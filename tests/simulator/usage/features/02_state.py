"""Executable Simulation state usage example.

Demonstrates FEAT-SIM-02 simulation state protocol, idempotency recording, and migrations.
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path
from typing import Any

# Add repository root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.services.simulator import (
    get_simulation_migrations,
    unwrap_simulation_response,
)
from tests.simulator._fixtures.sqlite_store import SqliteSimulationStateStore


def _feature_header(title: str) -> None:
    """Print the feature header banner."""
    print(f"\n{'=' * 88}\n{title}\n{'=' * 88}")


def _header(title: str) -> None:
    """Print one example heading."""
    print(f"\n{'=' * 88}\n{title}\n{'=' * 88}")


def _format_result(obj: Any) -> str:
    """Dynamically format the output result type name and field/key signature."""
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


def fr_sim_041() -> None:
    """
    FR-SIM-041: Stage 3 — Depend on state persistence protocol and expose domain migrations.

    The system shall depend on persistence only through an injected runtime-checkable `Protocol` exposing `append_journal`, `flush_journal`, `finalize_journal`, `load_run`, and `record_idempotency`, and shall declare its own migrations using the Data-owned `MigrationStep` contract. Simulation imports no Data storage, connection, or locking module, no `sqlite3`, and executes no schema statement of its own.
    """
    _header(
        "Stage 3: State Protocol - Record Run Idempotency & Migrations (FR-SIM-041)"
    )
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        store = SqliteSimulationStateStore(
            tmp_path / "simulation.db", tmp_path / "artifacts"
        )
        store.record_idempotency("req-usage", "a" * 64, "run-usage", "started")
        run_info = store.load_run("req-usage")
        print(_format_result(run_info))
        print(
            f"Data -> run_id='{run_info.get('run_id') if isinstance(run_info, dict) else None}'"
        )

    resp = get_simulation_migrations()
    migrations = unwrap_simulation_response(
        resp, operation="usage.state.get_simulation_migrations"
    )
    print(_format_result(resp))
    print(
        f"Data -> migration_step_count={len(migrations if isinstance(migrations, tuple) else ())}"
    )


def main() -> None:
    """Run all feature examples in sequential module flow order."""
    _feature_header(
        "FEATURE: FEAT-SIM-02 — state/ — Simulation-Owned State\n\n"
        "Purpose: Maintain run idempotency state and expose Simulation migration declarations.\n\n"
        "Module flow:\n"
        "-> Stage 1: State store interface initialization\n"
        "-> Stage 2: Migration declaration inspection\n"
        "-> Stage 3: Idempotency state recording and run metadata retrieval"
    )

    # Stage 3: State protocol & Migrations
    fr_sim_041()


if __name__ == "__main__":
    main()
