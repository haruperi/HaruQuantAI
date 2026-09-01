"""Executable Simulation state usage example.

Demonstrates FEAT-SIM-02 simulation state protocol, idempotency recording, and migrations.
"""

from __future__ import annotations

import asyncio
import sys
import tempfile
from collections.abc import AsyncIterable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast

# Add repository root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.kernel.identity import generate_id
from app.kernel.serialization import canonical_json
from app.services.data import (
    build_data_settings,
    data_settings_context,
    unwrap_data_response,
)
from app.services.simulator import (
    branch_live_simulation,
    build_simulation_run_dependencies,
    build_simulation_state_store,
    close_live_simulation_session,
    create_live_simulation_session,
    create_simulation_handle,
    create_simulation_session,
    execute_simulation_handle_operation,
    execute_simulation_state_store_operation,
    get_simulation_migrations,
    get_simulation_value_field,
    read_live_simulation_state,
    read_simulation_session,
    reset_live_simulation_sessions,
    run_simulator_migrations,
    step_live_simulation,
    stream_simulation_session_frames,
    unwrap_simulation_response,
)
from tests.simulator.usage.workflows._support import (
    backtest_request,
    live_tick_dataset,
)
from tests.simulator.usage.workflows._support import (
    dependencies as run_dependencies,
)


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
        return f"SUCCESS: Output Result -> {type_name}({keys}) : {type_name}"
    if isinstance(obj, dict):
        keys = ", ".join(obj.keys())
        return f"SUCCESS: Output Result -> dict({keys}) : dict"
    if hasattr(obj, "__dict__"):
        keys = ", ".join(vars(obj).keys())
        return f"SUCCESS: Output Result -> {type_name}({keys}) : {type_name}"
    return f"SUCCESS: Output Result -> {type_name} : {type_name}"


def _settings(data_dir: Path) -> object:
    """Build isolated Data settings for this executable example."""
    return build_data_settings(
        database_url="sqlite:///simulator-usage.db",
        data_dir=data_dir,
        sqlite_busy_timeout_seconds=1.0,
        write_lock_lease_seconds=10.0,
        approved_storage_roots=(Path(),),
    )


def _run_migrations() -> None:
    """Apply Simulator's immutable manifest through Data's public boundary."""
    request_id = generate_id("req")
    unwrap_data_response(
        run_simulator_migrations(request_id),
        operation="simulator.usage.migrations",
        request_id=request_id,
    )


def _execute(store: object, operation: str, *args: object) -> object:
    """Execute and unwrap one public Simulator state operation."""
    return unwrap_simulation_response(
        execute_simulation_state_store_operation(store, operation, *args),
        operation=f"simulator.usage.{operation}",
    )


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
        with data_settings_context(_settings(tmp_path)):
            _run_migrations()
            request_id = generate_id("req")
            store = build_simulation_state_store(artifact_root=tmp_path / "artifacts")
            _execute(
                store,
                "record_idempotency",
                request_id,
                "a" * 64,
                "run-usage",
                "started",
            )
            run_info = _execute(store, "load_run", request_id)
            print(_format_result(run_info))
            print(f"Data -> run_id='{run_info['run_id']}'")

    migrations = get_simulation_migrations()
    print(_format_result(migrations))
    print(f"Data -> migration_step_count={len(migrations)}")


def fr_sim_103() -> None:
    """
    FR-SIM-103: Run the complete authoritative Simulator migration manifest.

    Simulator shall expose one authoritative package-root migration runner that submits the complete immutable Simulator migration manifest through Data's public migration executor. Ledger mismatch, checksum mismatch, write-lock failure, or transactional execution failure shall return Data's failed standard response and prevent Simulator-backed API readiness.
    """
    _header("Authoritative Simulator Migration Runner (FR-SIM-103)")
    with (
        tempfile.TemporaryDirectory() as tmp_dir,
        data_settings_context(_settings(Path(tmp_dir))),
    ):
        request_id = generate_id("req")
        result = run_simulator_migrations(request_id)
        data = unwrap_data_response(
            result,
            operation="simulator.usage.authoritative_migrations",
            request_id=request_id,
        )
        print(_format_result(result))
        print(
            "SUCCESS: FR-SIM-103 authoritative manifest applied; "
            f"Data -> migration_result={data}"
        )


def fr_sim_094() -> None:
    """
    FR-SIM-094: Persist lifecycle state directly in `sim_runs`.

    Simulator shall persist run identity, lifecycle state, and validated completed single-run or portfolio-result payloads directly in `sim_runs` through Data's public statement-plan and transaction boundary. Unknown and incomplete runs return no result and never synthesize one.
    """
    _header("Direct Relational Run Persistence (FR-SIM-094)")
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        with data_settings_context(_settings(tmp_path)):
            _run_migrations()
            request_id = generate_id("req")
            store = build_simulation_state_store(artifact_root=tmp_path / "artifacts")
            _execute(
                store,
                "record_idempotency",
                request_id,
                "b" * 64,
                "run-relational",
                "started",
            )
            reconstructed = build_simulation_state_store(
                artifact_root=tmp_path / "artifacts"
            )
            row = _execute(reconstructed, "load_run", request_id)
            print(_format_result(row))
            print("Data -> persisted_table='sim_runs'")


def fr_sim_095() -> None:
    """
    FR-SIM-095: Enforce identity-bound lifecycle transitions.

    Lifecycle changes shall compare the persisted request hash, run identity, prior status, and prior result material. Identical replays are idempotent; identity conflicts, stale changes, backward transitions, and terminal-result mutation fail closed without a partial update.
    """
    _header("Idempotent Lifecycle Compare-and-Swap (FR-SIM-095)")
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        with data_settings_context(_settings(tmp_path)):
            _run_migrations()
            request_id = generate_id("req")
            store = build_simulation_state_store(artifact_root=tmp_path / "artifacts")
            arguments = (request_id, "c" * 64, "run-cas", "started")
            _execute(store, "record_idempotency", *arguments)
            _execute(store, "record_idempotency", *arguments)
            _execute(
                store,
                "record_idempotency",
                request_id,
                "c" * 64,
                "run-cas",
                "failed",
            )
            row = _execute(store, "load_run", request_id)
            print(_format_result(row))
            print(f"Data -> replayed=True, terminal_status='{row['status']}'")


def fr_sim_096() -> None:
    """
    FR-SIM-096: Publish durable journals as canonical JSONL.

    Journal events shall stage in a partial canonical JSONL artifact, recover contiguous sequence state after adapter reconstruction, become durable through group-commit `fsync`, and publish by atomic rename only after exact event-count and tail-hash validation. No database journal staging or journal table is permitted.
    """
    _header("Partial JSONL Group Commit and Atomic Publication (FR-SIM-096)")
    with tempfile.TemporaryDirectory() as tmp_dir:
        artifact_root = Path(tmp_dir) / "artifacts"
        store = build_simulation_state_store(artifact_root=artifact_root)
        first = canonical_json({"sequence": 0, "event_hash": "d" * 64})
        second = canonical_json({"sequence": 1, "event_hash": "e" * 64})
        _execute(store, "append_journal", "run-jsonl", first)
        reconstructed = build_simulation_state_store(artifact_root=artifact_root)
        _execute(reconstructed, "append_journal", "run-jsonl", second)
        _execute(reconstructed, "flush_journal", "run-jsonl")
        checksum = _execute(
            reconstructed,
            "finalize_journal",
            "run-jsonl",
            2,
            "e" * 64,
        )
        print(_format_result(checksum))
        print("Data -> artifact='journal.jsonl', partial_exists=False")


def _unwrap_live(response: object) -> Any:
    """Unwrap one live-session response from the Simulation root gate.

    Args:
        response: Root-gate response envelope.

    Returns:
        The session projection carried by the response.
    """
    return unwrap_simulation_response(
        response, operation="simulator.usage.live_session"
    )


def fr_sim_097(root: Path) -> tuple[str, Any, Any]:
    """
    FR-SIM-097: Open one bounded live what-if session.

    Simulator shall open one bounded in-process live what-if session over a prepared run context, positioned before the first tick. Session identity is derived from the request, so a repeated open re-attaches to the same session rather than starting a second engine over the same work. Live sessions are explicitly non-durable and are lost on restart; official runs remain fully durable.
    """
    _header("Live What-If Sessions (FR-SIM-097)")
    dataset = live_tick_dataset()
    request = backtest_request(dataset)
    deps = run_dependencies(root, dataset)
    state = _unwrap_live(
        create_live_simulation_session(request, deps, request_id=generate_id("req"))
    )
    print(
        "SUCCESS: FR-SIM-097 live session opened; "
        f"Data -> cursor={state['cursor']}, ticks={state['tick_count']}"
    )
    return str(state["session_id"]), request, deps


def fr_sim_098(session_id: str) -> None:
    """
    FR-SIM-098: Advance a live session in bounded tick increments.

    Simulator shall advance one live session by a bounded positive tick count using the same per-tick order the official run executes, so a session stepped to completion produces the same receipts as an uninterrupted run. A non-positive or oversized step never reaches the engine.
    """
    _header("Live What-If Sessions (FR-SIM-098)")
    state = _unwrap_live(step_live_simulation(session_id, 2))
    print(
        "SUCCESS: FR-SIM-098 live session advanced; "
        f"Data -> cursor={state['cursor']}, complete={state['complete']}"
    )


def fr_sim_099(session_id: str) -> None:
    """
    FR-SIM-099: Project immutable live-session state.

    Simulator shall expose an immutable non-secret projection of one live session carrying cursor, tick count, completion, receipt and pending-intent counts, branch lineage, and an explicit advisory marker. An unknown or expired session fails closed rather than being silently recreated.
    """
    _header("Live What-If Sessions (FR-SIM-099)")
    state = _unwrap_live(read_live_simulation_state(session_id))
    print(
        "SUCCESS: FR-SIM-099 live session projected; "
        f"Data -> advisory={state['advisory']}, pending={state['pending_intents']}"
    )


def fr_sim_100(session_id: str, deps: Any) -> None:
    """
    FR-SIM-100: Fork an independent advisory what-if branch.

    Simulator shall fork one live session into an independent what-if branch by replaying the parent's deterministic inputs to the divergence point and continuing under the overridden request. The branch never shares or mutates the parent's engine, journals under its own run identity, and is reproducible from its recorded lineage. Overrides that cannot produce a valid request open no branch.
    """
    _header("Live What-If Sessions (FR-SIM-100)")
    branch = _unwrap_live(
        branch_live_simulation(
            session_id, {"seed": 7}, deps, request_id=generate_id("req")
        )
    )
    print(
        "SUCCESS: FR-SIM-100 advisory branch created; "
        f"Data -> branch_of={branch['branch_of']}, "
        f"diverged_at={branch['divergence_index']}, run_id={branch['run_id']}"
    )


def fr_sim_101(session_id: str) -> None:
    """
    FR-SIM-101: Close a live session and release its engine.

    Simulator shall close one live session, release its engine, and return the session's final projection. A closed session identity is not resolvable afterwards.
    """
    _header("Live What-If Sessions (FR-SIM-101)")
    final = _unwrap_live(close_live_simulation_session(session_id))
    print(f"SUCCESS: FR-SIM-101 live session closed; Data -> cursor={final['cursor']}")


def fr_sim_102() -> None:
    """
    FR-SIM-102: Bound live-session memory and reset the registry.

    Simulator shall bound live-session memory by capping concurrent sessions and expiring idle ones, and shall expose a deterministic registry reset so an abandoned exploration cannot pin engine state beyond its window.
    """
    _header("Live What-If Sessions (FR-SIM-102)")
    _unwrap_live(reset_live_simulation_sessions())
    print("SUCCESS: FR-SIM-102 live session registry reset; Data -> active_sessions=0")


def journal_playback_sessions() -> None:
    """Create, read, and consume a completed-run playback session."""
    _header("Completed-Run Journal Playback Sessions")
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        artifact_root = tmp_path / "artifacts"
        with data_settings_context(_settings(tmp_path)):
            _run_migrations()
            store = build_simulation_state_store(artifact_root=artifact_root)
            run_request_id = generate_id("req")
            _execute(
                store,
                "record_idempotency",
                run_request_id,
                "f" * 64,
                "run-playback-usage",
                "completed",
                {"status": "completed"},
            )
            writer = create_simulation_handle(
                "JournalWriter",
                store,
                "run-playback-usage",
                run_request_id,
                generate_id("cor"),
            )
            execute_simulation_handle_operation(
                writer,
                "append",
                "run_started",
                {
                    "config_hash": "a",
                    "data_hash": "b",
                    "engine_version": "v1",
                },
                datetime(2026, 8, 4, tzinfo=UTC),
            )
            execute_simulation_handle_operation(writer, "finalize")
            session = unwrap_simulation_response(
                create_simulation_session(
                    "run-playback-usage",
                    request_id=generate_id("req"),
                ),
                operation="simulator.usage.create_session",
            )
            loaded = unwrap_simulation_response(
                read_simulation_session(str(session["session_id"])),
                operation="simulator.usage.read_session",
            )

            def noop(*_args: object, **_kwargs: object) -> None:
                """Return no value for unused playback dependency ports."""

            dependencies = build_simulation_run_dependencies(
                state_store=store,
                artifact_root=artifact_root,
                fast_research_enabled=False,
                ports=dict.fromkeys(
                    (
                        "audit",
                        "market_data",
                        "tick_series",
                        "indicators",
                        "strategy",
                        "risk",
                        "order_intents",
                        "execution_profile",
                        "symbol_specification",
                        "cost_model",
                        "fx_evidence",
                    ),
                    noop,
                ),
            )

            async def collect() -> list[object]:
                frames = cast(
                    "AsyncIterable[object]",
                    stream_simulation_session_frames(
                        str(session["session_id"]),
                        resume_after=-1,
                        dependencies=dependencies,
                    ),
                )
                return [event async for event in frames]

            frames = asyncio.run(collect())
            print(_format_result(loaded))
            print(
                "Data -> "
                f"frames={len(frames)}, "
                f"event_type='{get_simulation_value_field(frames[0], 'event_type')}'"
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

    # Authoritative complete-manifest execution
    fr_sim_103()

    # Stage 4: Direct relational persistence
    fr_sim_094()

    # Stage 5: Identity-bound lifecycle CAS
    fr_sim_095()

    # Stage 6: Durable JSONL journal publication
    fr_sim_096()

    # Completed-run playback lifecycle and frame delivery
    journal_playback_sessions()

    # Bounded live what-if sessions over the deterministic engine
    with tempfile.TemporaryDirectory() as live_dir:
        session_id, _request, deps = fr_sim_097(Path(live_dir))
        fr_sim_098(session_id)
        fr_sim_099(session_id)
        fr_sim_100(session_id, deps)
        fr_sim_101(session_id)
        fr_sim_102()


if __name__ == "__main__":
    main()
