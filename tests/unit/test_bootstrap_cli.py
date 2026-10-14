"""Unit and lifecycle integration tests for Stage 1G Bootstrap, Main, and CLI."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any

import pytest
from app.cli import (
    HeadlessCliRunner,
    format_cli_output,
    run_cli,
)
from app.cli import (
    main as cli_main,
)
from app.host.bootstrap import (
    ORDERED_BOOT_STAGES,
    BootstrapConfig,
    HostRuntime,
    LifespanStage,
    ReadinessState,
    bootstrap_context,
    create_bootstrap_app,
    reconcile_database,
)
from app.host.bootstrap import (
    main as bootstrap_main,
)
from app.host.persistence.create import create_schema, get_connection
from app.host.persistence.read import get_host_job
from app.host.persistence.update import save_host_job
from app.host.response import StandardError
from app.main import (
    create_app,
    resolve_main_config,
    run_server,
)
from app.main import (
    main as main_entrypoint,
)
from fastapi import APIRouter
from fastapi.testclient import TestClient


def _seed_orphan_running_job(db_path: Path, job_id: str = "job-orphan-boot") -> None:
    """Insert a RUNNING job row directly via persistence to test boot recovery."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = get_connection(db_path)
    try:
        create_schema(conn)
    finally:
        conn.close()

    save_host_job(
        job_id,
        owner="test",
        kind="backtest",
        status="RUNNING",
        progress=42.0,
        message="In flight before crash",
        attempt_id=1,
        submitted_at_utc="2026-10-14T10:00:00+00:00",
        started_at_utc="2026-10-14T10:00:01+00:00",
        conn=db_path,
    )


def _write_sample_plugin(plugins_dir: Path) -> None:
    """Create a valid sample plugin in plugins_dir for Stage 5 discovery tests."""
    p_dir = plugins_dir / "data_source" / "demo_feed"
    p_dir.mkdir(parents=True, exist_ok=True)
    manifest = {
        "id": "demo-feed",
        "name": "Demo Feed Provider",
        "version": "1.0.0",
        "slot": "data.provider",
        "entry_point": "adapter:DemoFeedPlugin",
        "capabilities": ["bars"],
    }
    (p_dir / "plugin.json").write_text(json.dumps(manifest), encoding="utf-8")
    (p_dir / "adapter.py").write_text(
        "class DemoFeedPlugin:\n"
        "    def __init__(self, context=None):\n"
        "        self.context = context\n",
        encoding="utf-8",
    )


def test_bootstrapped_settings_http_writes_and_telemetry_shutdown(
    tmp_path: Path,
) -> None:
    import app.host.logging as telemetry
    from app.host.persistence.read import list_host_settings

    config = BootstrapConfig(data_dir=tmp_path, use_process_pool=False)
    runtime = HostRuntime(config)
    app = create_bootstrap_app(runtime=runtime)
    with TestClient(app) as client:
        telemetry.flush_logs()
        with client.websocket_connect("/api/v1/ws?channels=logs") as websocket:
            websocket.send_json({"action": "ping"})
            while websocket.receive_json()["event_type"] != "pong":
                pass
            telemetry.flush_logs()
            cursor = runtime.event_bus.current_cursor
            telemetry.get_logger("audit.live").warning("live console audit marker")
            telemetry.flush_logs()
            for _ in range(100):
                streamed = websocket.receive_json()
                assert streamed["channel"] == "logs"
                if "live console audit marker" in streamed["payload"]["message"]:
                    break
            else:
                pytest.fail("Live log marker did not reach WebSocket subscriber")
            replay = client.get(
                f"/api/v1/events?channels=logs&since_cursor={cursor}&limit=1"
            )
            assert "live console audit marker" in replay.text
            websocket.send_json({"action": "close"})
        revision = client.get("/api/v1/settings").json()["data"]["revision"]
        saved = client.put(
            "/api/v1/settings",
            json={"revision": revision, "settings": {"audit": {"theme": "dark"}}},
        )
        assert saved.status_code == 200, saved.text
        assert saved.json()["data"]["revision"] == revision + 1
        assert (
            client.put(
                "/api/v1/settings",
                json={"revision": revision, "settings": {"audit": {"theme": "stale"}}},
            ).status_code
            == 409
        )
        conn = get_connection(config.resolved_db_path)
        try:
            assert any(row["key"] == "theme" for row in list_host_settings(conn=conn))
        finally:
            conn.close()
        engine = telemetry._GLOBAL_ENGINE
        assert engine is not None
    assert telemetry._GLOBAL_ENGINE is None
    assert not telemetry._BOOTSTRAPPED
    assert all(
        handler.stream is None
        for handler in engine.downstream_handlers
        if isinstance(handler, telemetry.WindowsSafeRotatingFileHandler)
    )


def test_partial_service_initialization_releases_acquired_resources(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from unittest.mock import Mock

    import app.host.logging as telemetry

    runtime = HostRuntime(BootstrapConfig(data_dir=tmp_path, use_process_pool=False))
    reset = Mock()
    stopped = Mock(side_effect=RuntimeError("one cleanup failed"))

    def fail_discovery():
        assert runtime.session_manager is not None
        assert runtime.job_manager is not None
        monkeypatch.setattr(runtime.session_manager, "reset", reset)
        monkeypatch.setattr(runtime.job_manager, "shutdown", stopped)
        raise RuntimeError("discovery initialization failed")

    monkeypatch.setattr(runtime, "init_discovery", fail_discovery)
    with pytest.raises(RuntimeError, match="discovery initialization failed"):
        runtime.start_sync()
    stopped.assert_called_once_with(wait=True, cancel_futures=True)
    reset.assert_called_once()
    assert LifespanStage.SERVICES in runtime.teardown_stages
    assert runtime.state == ReadinessState.FAILED
    assert not telemetry._BOOTSTRAPPED


# ============================================================================
# 1. 7-Stage Bootstrap State Machine & LIFO Teardown Tests
# ============================================================================


def test_seven_stage_progression_and_reverse_lifo_teardown(tmp_path: Path) -> None:
    """Verify exact 7-stage startup progression, orphan recovery, and LIFO stop."""
    data_dir = tmp_path / "data"
    db_path = data_dir / "database" / "haruquantai.db"
    plugins_dir = data_dir / "plugins"

    _seed_orphan_running_job(db_path, "job-orphan-01")
    _write_sample_plugin(plugins_dir)

    cfg = BootstrapConfig(
        data_dir=data_dir,
        db_path=db_path,
        plugins_dir=plugins_dir,
        headless=True,
        debug=True,
        use_process_pool=False,
    )
    runtime = HostRuntime(config=cfg)

    # Pre-boot state
    pre_snap = runtime.get_readiness()
    assert pre_snap.state == ReadinessState.UNINITIALIZED
    assert pre_snap.is_ready is False
    assert runtime.stop_sync().state == ReadinessState.STOPPED

    # Execute 7-stage startup
    ready_snap = runtime.start_sync()
    assert ready_snap.state == ReadinessState.READY
    assert ready_snap.is_ready is True
    assert tuple(ready_snap.completed_stages) == ORDERED_BOOT_STAGES
    assert tuple(runtime.completed_stages) == ORDERED_BOOT_STAGES
    assert runtime.active_stage == LifespanStage.READY
    assert all(ready_snap.checks.values())

    # Calling start() again while READY is idempotent
    again_snap = runtime.start_sync()
    assert again_snap.host_instance_id == ready_snap.host_instance_id

    # Verify Stage 5 reconciled the orphan RUNNING job -> INTERRUPTED
    reconciled_row = get_host_job("job-orphan-01", conn=db_path)
    assert reconciled_row is not None
    assert reconciled_row["status"] == "INTERRUPTED"
    assert "job-orphan-01" in ready_snap.details["services"]["reconciled_orphan_jobs"]
    assert ready_snap.details["services"]["plugins_enabled"] == 1

    # Execute reverse-order LIFO teardown
    stop_snap = runtime.stop_sync()
    assert stop_snap.state == ReadinessState.STOPPED
    assert stop_snap.is_ready is False
    assert tuple(runtime.teardown_stages) == tuple(reversed(ORDERED_BOOT_STAGES))

    # Calling stop() again while STOPPED is idempotent
    assert runtime.stop_sync().state == ReadinessState.STOPPED


def test_bootstrap_failure_triggers_reverse_rollback(tmp_path: Path) -> None:
    """Verify mid-boot failure rolls back only acquired stages in LIFO order."""
    # 1. Invalid port fails in Stage 1 (CONFIGURING) before stage acquisition
    bad_cfg = BootstrapConfig(data_dir=tmp_path / "bad_port", port=70000)
    rt_bad = HostRuntime(config=bad_cfg)
    with pytest.raises(ValueError, match="Invalid host port"):
        rt_bad.start_sync()
    assert rt_bad.state == ReadinessState.FAILED
    assert rt_bad.teardown_stages == []

    # 2. Failure injected via stage hook at Stage 5 (SERVICES) rolls back 5..1
    hook_order: list[str] = []

    async def _fail_on_services(rt: HostRuntime) -> None:
        hook_order.append(f"hook:{rt.active_stage}")
        # Register a custom cleanup that raises to verify exception isolation
        rt._acquired_stack.append(
            rt._acquired_stack[-1].__class__(
                stage=LifespanStage.SERVICES,
                check_key="services",
                cleanup=lambda: (_ for _ in ()).throw(RuntimeError("cleanup boom")),
            )
        )
        raise RuntimeError("Simulated service initialization failure")

    cfg_mid = BootstrapConfig(
        data_dir=tmp_path / "mid_fail",
        headless=True,
        use_process_pool=False,
    )
    rt_mid = HostRuntime(
        config=cfg_mid,
        stage_hooks={LifespanStage.SERVICES: _fail_on_services},
    )
    with pytest.raises(RuntimeError, match="Simulated service initialization"):
        rt_mid.start_sync()

    assert rt_mid.state == ReadinessState.FAILED
    # Stages 1..4 completed before Stage 5 failed; rollback released SERVICES..CONFIGURING
    assert LifespanStage.CONFIGURING in rt_mid.teardown_stages
    assert LifespanStage.PERSISTENCE in rt_mid.teardown_stages
    assert rt_mid.teardown_stages[-1] == LifespanStage.CONFIGURING


def test_sync_and_async_bootstrap_context_and_reconcile(tmp_path: Path) -> None:
    """Verify both sync and async bootstrap_context managers and CLI main."""
    cfg = BootstrapConfig(
        data_dir=tmp_path / "ctx_test",
        headless=True,
        use_process_pool=False,
    )

    with bootstrap_context(cfg) as rt_sync:
        assert rt_sync.is_ready() is True
    assert rt_sync.state == ReadinessState.STOPPED

    async def _run_async_ctx() -> None:
        async with bootstrap_context(cfg) as rt_async:
            assert rt_async.is_ready() is True
            snap_dict = rt_async.get_readiness().to_dict()
            assert snap_dict["state"] == "READY"
        assert rt_async.state == ReadinessState.STOPPED

    asyncio.run(_run_async_ctx())

    # Database reconciliation helper
    db_file = tmp_path / "reconcile_only" / "haruquantai.db"
    _seed_orphan_running_job(db_file, "job-rec-99")
    rep = reconcile_database(db_file)
    assert rep["status"] == "reconciled"
    assert "job-rec-99" in rep["reconciled_orphan_jobs"]

    # bootstrap.py main() demonstration
    assert bootstrap_main(["--check-only"]) == 0


# ============================================================================
# 2. UI / FastAPI + Uvicorn Entrypoint Tests (app/main.py)
# ============================================================================


def test_main_ui_server_lifespan_and_uvicorn_modes(tmp_path: Path) -> None:
    """Verify app/main.py config resolution, FastAPI 7-stage lifespan, and Uvicorn."""
    data_dir = tmp_path / "main_ui_data"
    plugins_dir = data_dir / "plugins"
    _write_sample_plugin(plugins_dir)

    cfg, args = resolve_main_config(
        [
            "--host",
            "127.0.0.1",
            "--port",
            "8123",
            "--debug",
            "--data-dir",
            str(data_dir),
            "--plugins-dir",
            str(plugins_dir),
        ]
    )
    assert cfg.host == "127.0.0.1"
    assert cfg.port == 8123
    assert cfg.debug is True
    assert cfg.headless is False
    assert args.reload is False

    extra = APIRouter()

    @extra.get("/ui-custom-ping")
    def _custom_ping() -> dict[str, bool]:
        return {"pong": True}

    runtime = HostRuntime(config=cfg, extra_routers=[extra])
    app = create_bootstrap_app(config=cfg, runtime=runtime)

    # Entering TestClient context runs FastAPI lifespan -> 7-stage HostRuntime.start()
    with TestClient(app) as client:
        assert runtime.is_ready() is True
        assert tuple(runtime.completed_stages) == ORDERED_BOOT_STAGES

        r_status = client.get("/api/v1/status")
        assert r_status.status_code == 200
        assert r_status.json()["data"]["is_ready"] is True

        r_set = client.get("/api/v1/settings")
        assert r_set.status_code == 200
        assert "revision" in r_set.json()["data"]

        r_diag = client.get("/api/v1/diagnostics")
        assert r_diag.status_code == 200
        assert "worker_capacity" in r_diag.json()["data"]

        r_jobs = client.get("/api/v1/jobs")
        assert r_jobs.status_code == 200
        assert "jobs" in r_jobs.json()["data"]

        r_disc = client.get("/api/v1/discovery/plugins")
        assert r_disc.status_code == 200
        assert r_disc.json()["report"]["enabled_count"] == 1

        r_extra = client.get("/ui-custom-ping")
        assert r_extra.status_code == 200

    # Exiting TestClient context runs FastAPI lifespan -> reverse LIFO teardown
    assert runtime.state == ReadinessState.STOPPED
    assert tuple(runtime.teardown_stages) == tuple(reversed(ORDERED_BOOT_STAGES))

    # Test run_server() in production mode and --reload mode with fake uvicorn runner
    calls: list[dict[str, Any]] = []

    def _fake_uvicorn_run(target: Any, **kwargs: Any) -> None:
        calls.append({"target": target, **kwargs})

    rc_prod = run_server(
        ["--host", "127.0.0.1", "--port", "8010", "--data-dir", str(data_dir)],
        uvicorn_runner=_fake_uvicorn_run,
    )
    assert rc_prod == 0
    assert len(calls) == 1
    assert calls[0]["port"] == 8010

    rc_reload = run_server(
        [
            "--host",
            "127.0.0.1",
            "--port",
            "8011",
            "--reload",
            "--data-dir",
            str(data_dir),
        ],
        uvicorn_runner=_fake_uvicorn_run,
    )
    assert rc_reload == 0
    assert len(calls) == 2
    assert calls[1]["target"] == "app.main:create_app"
    assert calls[1]["reload"] is True
    assert calls[1]["factory"] is True

    # Default create_app() and main(["--check-only"])
    default_app = create_app(config=cfg)
    assert default_app.title == cfg.title
    assert main_entrypoint(["--check-only"]) == 0


# ============================================================================
# 3. Headless CLI Entrypoint Tests (app/cli.py)
# ============================================================================


def test_headless_cli_commands_and_7_stage_bootstrap(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Verify app/cli.py executes 7-stage bootstrap and dispatches all commands."""
    monkeypatch.chdir(tmp_path)
    data_dir = tmp_path / "cli_data"
    db_path = data_dir / "database" / "haruquantai.db"
    plugins_dir = data_dir / "plugins"
    _seed_orphan_running_job(db_path, "job-cli-orphan")
    _write_sample_plugin(plugins_dir)

    base_args = [
        "--data-dir",
        str(data_dir),
        "--db-path",
        str(db_path),
        "--plugins-dir",
        str(plugins_dir),
    ]

    # 1. status (--json)
    code_st, out_st = run_cli(["status", "--json", *base_args])
    assert code_st == 0
    parsed_st = json.loads(out_st)
    assert parsed_st["status"] == "success"
    assert parsed_st["data"]["stages_completed"] == 7
    assert parsed_st["data"]["readiness"]["headless"] is True

    # 2. health (text mode)
    code_hl, out_hl = run_cli(["health", *base_args])
    assert code_hl == 0
    assert "Command: health" in out_hl

    # 3. resources (--json)
    code_res, out_res = run_cli(["resources", "--json", *base_args])
    assert code_res == 0
    assert json.loads(out_res)["data"]["allocated_workers"] >= 1

    # 4. jobs list & jobs reconcile
    code_jl, out_jl = run_cli(["jobs", "--action", "list", "--json", *base_args])
    assert code_jl == 0
    jobs_payload = json.loads(out_jl)["data"]
    assert jobs_payload["count"] >= 1
    assert jobs_payload["jobs"][0]["status"] == "INTERRUPTED"

    code_jr, _ = run_cli(["jobs", "--action", "reconcile", "--json", *base_args])
    assert code_jr == 0

    # 5. plugins list & plugins slots
    code_pl, out_pl = run_cli(["plugins", "--action", "list", "--json", *base_args])
    assert code_pl == 0
    assert json.loads(out_pl)["data"]["enabled_count"] == 1

    code_ps, out_ps = run_cli(["plugins", "--action", "slots", "--json", *base_args])
    assert code_ps == 0
    assert json.loads(out_ps)["data"]["count"] >= 4

    # 6. settings & reconcile
    code_set, _ = run_cli(["settings", "--json", *base_args])
    assert code_set == 0

    code_rec, out_rec = run_cli(["reconcile", "--json", *base_args])
    assert code_rec == 0
    assert json.loads(out_rec)["data"]["status"] == "reconciled"

    # 7. Error formatting & unknown command in HeadlessCliRunner
    err_obj = StandardError(code="TEST_ERR", message="Something failed")
    assert "ERROR [TEST_ERR]" in format_cli_output(None, as_json=False, error=err_obj)
    err_json = json.loads(format_cli_output(None, as_json=True, error=err_obj))
    assert err_json["status"] == "error"

    cfg = BootstrapConfig(data_dir=data_dir, headless=True, use_process_pool=False)
    with bootstrap_context(cfg) as rt:
        runner = HeadlessCliRunner(rt)
        with pytest.raises(ValueError, match="Unsupported CLI command"):
            runner.execute("nonexistent-cmd")

    # 8. CLI main() with and without --data-dir
    assert cli_main(["status", "--json"]) == 0
    assert cli_main(["status", "--json", *base_args]) == 0

    # 8. Standalone cli.py main()
    assert cli_main(["status", "--json"]) == 0
