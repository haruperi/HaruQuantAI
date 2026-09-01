"""Standalone Simulation Workbench API feature usage."""

from __future__ import annotations

import json
import sys
import tempfile
from datetime import UTC, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.kernel.identity import generate_id
from app.services.api import (
    build_simulation_workbench_registry,
    build_simulation_workbench_source,
    register_api_user,
    run_api_migrations,
)
from app.services.api.widgets.simulator.migrations import (
    get_simulation_workbench_migration_steps,
)
from app.services.api.widgets.simulator.persistence import (
    create_simulation_result_record,
)
from app.services.api.widgets.simulator.workbench_schemas import (
    BatchCreateRequest,
    BatchRunSpec,
    LiveSessionCommandRequest,
    LiveSessionCreateRequest,
    RunCatalogueEntry,
    SeekRequest,
    StepRequest,
    ViewportQuery,
)
from app.services.data import (
    build_data_settings,
    build_migration_request,
    data_settings_context,
    run_domain_migrations,
)


def _live_authority(
    operation: str, *args: object, **kwargs: object
) -> dict[str, object]:
    """Replay one interactive authority operation."""
    del kwargs
    return {
        "operation": operation,
        "session_id": args[0] if args else None,
    }


def _batch_runner(operation: str, *args: object, **kwargs: object) -> dict[str, object]:
    """Replay one batch runner operation."""
    del args, kwargs
    return {"operation": operation, "batch_id": "batch-usage"}


def main() -> None:
    """Exercise the feature's public contracts and dispatch surface."""
    viewport = ViewportQuery()
    assert viewport.after == 0
    assert viewport.before == 300
    step = StepRequest(ticks=100)
    seek = SeekRequest(target_cursor=1_000)
    command = LiveSessionCommandRequest(command="submit_order", symbol="EURUSD")
    batch = BatchCreateRequest(
        items=(
            BatchRunSpec(
                symbol="EURUSD",
                timeframe="H1",
                strategy_id="naive-ma-trend",
                start=datetime(2026, 1, 1, tzinfo=UTC),
                end=datetime(2026, 2, 1, tzinfo=UTC),
            ),
        ),
        concurrency=2,
    )
    entry = RunCatalogueEntry(
        run_id="run-usage",
        principal_id="principal-usage",
        origin_kind="canonical_job",
        status="queued",
        evidence_class="canonical",
        created_at="2026-03-01T00:00:00Z",
    )
    assert entry.archive_state == "active"
    assert LiveSessionCreateRequest(run_id="run-usage").mode == "practice"

    with tempfile.TemporaryDirectory(prefix="swb-usage-") as directory:
        root = Path(directory)
        with data_settings_context(
            build_data_settings(
                database_url="sqlite:///swb-usage.db",
                data_dir=root,
                sqlite_busy_timeout_seconds=1.0,
                write_lock_lease_seconds=10.0,
                approved_storage_roots=(Path(),),
            )
        ):
            assert run_api_migrations(generate_id("req")).status == "success"
            assert (
                run_domain_migrations(
                    build_migration_request(
                        domain="api",
                        steps=get_simulation_workbench_migration_steps(),
                        request_id=generate_id("req"),
                    )
                ).status
                == "success"
            )
            user = register_api_user(
                username="swb-usage-user",
                password="bounded usage password",  # pragma: allowlist secret
                request_id=generate_id("req"),
                tenant_or_environment="development",
                runtime_profile="simulation",
            )
            principal_id = user.user_id
            now = "2026-03-01T00:00:00Z"
            create_simulation_result_record(
                {
                    "run_id": "run-usage",
                    "principal_id": principal_id,
                    "origin_kind": "canonical_job",
                    "origin_id": None,
                    "job_id": None,
                    "batch_id": None,
                    "session_id": None,
                    "strategy_id": "naive-ma-trend",
                    "strategy_version": "v1",
                    "strategy_label": None,
                    "symbols": json.dumps(["EURUSD"]),
                    "timeframe": "H1",
                    "measurement_start": None,
                    "measurement_end": None,
                    "status": "completed",
                    "result_ref": None,
                    "report_id": None,
                    "report_ref": None,
                    "artifact_manifest_ref": None,
                    "quality_status": None,
                    "evidence_class": "canonical",
                    "created_at": now,
                    "completed_at": now,
                    "name": None,
                    "alias": None,
                    "description": None,
                    "tags": "[]",
                    "run_reason": None,
                    "archive_state": "active",
                    "updated_at": now,
                },
                request_id=generate_id("req"),
            )
            source = build_simulation_workbench_source(
                registry=build_simulation_workbench_registry(),
                live_authority=_live_authority,
                batch_runner=_batch_runner,
            )
            listed = source("list_sessions", principal_id=principal_id)
            created = source(
                "create_session",
                "run-usage",
                principal_id=principal_id,
                request_id=generate_id("req"),
            )
            stepped = source(
                "step",
                created["session_id"],
                principal_id=principal_id,
                ticks=step.ticks,
            )
            sought = source(
                "seek",
                created["session_id"],
                principal_id=principal_id,
                target_cursor=seek.target_cursor,
            )
            commanded = source(
                "command",
                created["session_id"],
                principal_id=principal_id,
                command=command.model_dump(),
            )
            finalized = source(
                "finalize", created["session_id"], principal_id=principal_id
            )
            batch_created = source(
                "create_batch",
                batch.model_dump(mode="json"),
                principal_id=principal_id,
            )
            print(
                {
                    "feature": "simulation-workbench",
                    "sessions_listed": len(listed),
                    "session_created": created["session_id"] is not None,
                    "stepped": stepped["operation"] == "step",
                    "sought": sought["operation"] == "seek",
                    "commanded": commanded["operation"] == "command",
                    "finalized": finalized["operation"] == "finalize",
                    "batch_created": batch_created["batch_id"] == "batch-usage",
                }
            )


if __name__ == "__main__":
    main()
