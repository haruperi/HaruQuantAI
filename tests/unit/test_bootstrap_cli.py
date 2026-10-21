"""Verify host bootstrap, lifecycle, settings wiring and CLI dispatch.

Description:
    Exercise startup, route registration, settings HTTP writes and shutdown using
    isolated temporary databases, including rollback and telemetry draining.
Purpose:
    FEAT-HOST-BOOT: Verify application lifecycle and settings transport wiring.
Key Capabilities:
    - FR-HOST-BOOT-STAGE-PROGRESSION: Assert ordered initialization and teardown.
      Associated: test_seven_stage_progression_and_reverse_lifo_teardown().
      Logging: assert structured stage events and durable telemetry results.
    - FR-HOST-BOOT-PERSISTENCE-STAGE: Verify real settings writes and conflicts.
      Associated: test_bootstrapped_settings_http_writes_and_telemetry_shutdown().
      Logging: verify telemetry sinks and post-shutdown engine state.
Python API Usage:
    pytest.main(["tests/unit/test_bootstrap_cli.py", "--no-cov"])
CLI Usage:
    uv run pytest tests/unit/test_bootstrap_cli.py --no-cov
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import app.host.bootstrap
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
    AppHost,
)
from app.host.bootstrap import (
    main as bootstrap_main,
)
from app.host.persistence import HostPersistence
from app.host.response import StandardError
from app.main import (
    create_app,
    resolve_main_config,
    run_server,
)
from app.main import (
    main as main_entrypoint,
)
from fastapi import APIRouter, FastAPI
from fastapi.testclient import TestClient


@pytest.fixture(autouse=True)
def _isolate_default_db(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Redirect HostPersistence.DEFAULT_DB_PATH to an isolated temporary SQLite file."""
    db_file = tmp_path / "database" / "haruquantai.db"
    monkeypatch.setattr(HostPersistence, "DEFAULT_DB_PATH", db_file)
    return db_file


def _seed_orphan_running_job(job_id: str = "job-orphan-boot") -> None:
    """Insert a RUNNING job row directly via persistence to test boot recovery."""
    HostPersistence.create_record(
        "host_jobs",
        {
            "job_id": job_id,
            "owner": "test",
            "kind": "backtest",
            "status": "RUNNING",
            "progress": 42.0,
            "message": "In flight before crash",
            "attempt_id": 1,
            "submitted_at_utc": "2026-10-14T10:00:00+00:00",
            "started_at_utc": "2026-10-14T10:00:01+00:00",
        },
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

    runtime = AppHost(data_dir=tmp_path, use_process_pool=False)
    app = create_app(runtime=runtime)
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
            json={
                "expected_revision": revision,
                "changes": {"app.general": {"header_custom_text": "test"}},
            },
        )
        assert saved.status_code == 200, saved.text
        assert saved.json()["data"]["revision"] == revision + 1
        assert (
            client.put(
                "/api/v1/settings",
                json={
                    "expected_revision": revision,
                    "changes": {"app.general": {"header_custom_text": "stale"}},
                },
            ).status_code
            == 409
        )
        assert any(
            row["key"] == "app_general"
            for row in HostPersistence.read_records("host_settings")
        )
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

    runtime = AppHost(data_dir=tmp_path, use_process_pool=False)
    reset = Mock()
    stopped = Mock(side_effect=RuntimeError("one cleanup failed"))

    def fail_discovery():
        assert runtime.session_manager is not None
        assert runtime.job_manager is not None
        monkeypatch.setattr(runtime.session_manager, "reset", reset)
        monkeypatch.setattr(runtime.job_manager, "shutdown", stopped)
        raise RuntimeError("discovery initialization failed")

    monkeypatch.setattr(runtime, "_init_discovery", fail_discovery)
    runtime.startup()
    runtime.initialize_db()
    with pytest.raises(RuntimeError, match="discovery initialization failed"):
        runtime.register_modules()
    stopped.assert_called_once_with(wait=True, cancel_futures=True)
    reset.assert_called_once()
    assert AppHost.Stage.SERVICES in runtime.teardown_stages
    assert runtime.state == AppHost.State.FAILED
    assert not telemetry._BOOTSTRAPPED


# ============================================================================
# 1. 7-Stage Bootstrap State Machine & LIFO Teardown Tests
# ============================================================================


def test_seven_stage_progression_and_reverse_lifo_teardown(tmp_path: Path) -> None:
    """Verify exact 7-stage startup progression, orphan recovery, and LIFO stop."""
    data_dir = tmp_path / "data"
    plugins_dir = data_dir / "plugins"

    _seed_orphan_running_job("job-orphan-01")
    _write_sample_plugin(plugins_dir)

    runtime = AppHost(
        data_dir=data_dir,
        plugins_dir=plugins_dir,
        headless=True,
        debug=True,
        use_process_pool=False,
    )

    # Pre-boot state
    assert str(runtime.state) == AppHost.State.UNINITIALIZED.value
    assert runtime._is_ready() is False
    runtime.shutdown()
    assert str(runtime.state) == AppHost.State.STOPPED.value

    # Execute 5-method workflow progression
    app = runtime.startup()
    assert isinstance(app, FastAPI)
    assert runtime.initialize_db() is True
    runtime.register_modules()
    ev = runtime.broadcast_event("system", "host.ready")
    assert ev.channel == "system"

    assert str(runtime.state) == AppHost.State.READY.value
    assert runtime._is_ready() is True
    assert tuple(runtime.completed_stages) == AppHost.ORDERED_STAGES
    assert runtime.active_stage == AppHost.Stage.READY

    # Verify Stage 5 reconciled the orphan RUNNING job -> INTERRUPTED
    reconciled_rows = HostPersistence.read_records(
        "host_jobs", {"job_id": "job-orphan-01"}, limit=1
    )
    assert len(reconciled_rows) == 1
    assert reconciled_rows[0]["status"] == "INTERRUPTED"
    assert "job-orphan-01" in runtime._details["services"]["reconciled_orphan_jobs"]
    assert runtime._details["services"]["plugins_enabled"] >= 1

    # Execute reverse-order LIFO teardown
    runtime.shutdown()
    assert str(runtime.state) == AppHost.State.STOPPED.value
    assert runtime._is_ready() is False
    assert tuple(runtime.teardown_stages) == tuple(reversed(AppHost.ORDERED_STAGES))

    # Calling shutdown() again while STOPPED is idempotent
    runtime.shutdown()
    assert str(runtime.state) == AppHost.State.STOPPED.value


def test_bootstrap_failure_triggers_reverse_rollback(tmp_path: Path) -> None:
    """Verify mid-boot failure rolls back only acquired stages in LIFO order."""
    # 1. Invalid port fails in Stage 1 (CONFIGURING) before stage acquisition
    rt_bad = AppHost(data_dir=tmp_path / "bad_port", port=70000)
    with pytest.raises(ValueError, match="Invalid host port"):
        rt_bad.startup()
    assert rt_bad.state == AppHost.State.FAILED
    assert rt_bad.teardown_stages == []

    # 2. Failure injected via stage hook at Stage 5 (SERVICES) rolls back 5..1
    hook_order: list[str] = []

    def _fail_on_services(rt: AppHost) -> None:
        hook_order.append(f"hook:{rt.active_stage}")
        rt._acquired_stack.append(
            rt._acquired_stack[-1].__class__(
                stage=AppHost.Stage.SERVICES,
                check_key="services",
                cleanup=lambda: (_ for _ in ()).throw(RuntimeError("cleanup boom")),
            )
        )
        raise RuntimeError("Simulated service initialization failure")

    rt_mid = AppHost(
        data_dir=tmp_path / "mid_fail",
        headless=True,
        use_process_pool=False,
        stage_hooks={AppHost.Stage.SERVICES: _fail_on_services},
    )
    rt_mid.startup()
    rt_mid.initialize_db()
    with pytest.raises(RuntimeError, match="Simulated service initialization"):
        rt_mid.register_modules()

    assert rt_mid.state == AppHost.State.FAILED
    assert AppHost.Stage.CONFIGURING in rt_mid.teardown_stages
    assert AppHost.Stage.PERSISTENCE in rt_mid.teardown_stages
    assert rt_mid.teardown_stages[-1] == AppHost.Stage.CONFIGURING


def test_five_method_lifecycle_and_reconcile(tmp_path: Path) -> None:
    """Verify 5-method AppHost lifecycle execution, database reconcile, and bootstrap main."""
    rt = AppHost(
        data_dir=tmp_path / "flow_test",
        headless=True,
        use_process_pool=False,
    )
    rt.startup()
    rt.initialize_db()
    rt.register_modules()
    rt.broadcast_event("system", "host.ready")
    assert rt._is_ready() is True
    assert str(rt.state) == AppHost.State.READY.value
    rt.shutdown()
    assert str(rt.state) == AppHost.State.STOPPED.value

    # Database reconciliation helper
    _seed_orphan_running_job("job-rec-99")
    rep = AppHost._reconcile_database()
    assert rep["status"] == "reconciled"
    assert "job-rec-99" in rep["reconciled_orphan_jobs"]

    # bootstrap.py main() demonstration
    assert bootstrap_main(["--check-only"]) == 0


# ============================================================================
# 2. UI / FastAPI + Uvicorn Entrypoint Tests (app/main.py)
# ============================================================================


def test_main_ui_server_lifespan_and_uvicorn_modes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Verify app/main.py config resolution, FastAPI 7-stage lifespan, and Uvicorn."""
    data_dir = tmp_path / "main_ui_data"
    plugins_dir = data_dir / "plugins"
    _write_sample_plugin(plugins_dir)

    class _MockSettings:
        def get(self, section: str, key: str, default: Any = None) -> Any:
            mapping = {
                ("app_general", "host"): "127.0.0.1",
                ("app_general", "backend_port"): 8123,
                ("config_troubleshooting", "debug_level_active"): True,
                ("app_general", "data_dir"): str(data_dir),
                ("app_general", "plugins_dir"): str(plugins_dir),
                ("app_security", "require_auth"): False,
            }
            return mapping.get((section, key), default)

    cfg, args = resolve_main_config([], settings_source=_MockSettings())
    assert cfg.host == "127.0.0.1"
    assert cfg.port == 8123
    assert cfg.debug is True
    assert cfg.headless is False
    assert args.reload is False

    extra = APIRouter()

    @extra.get("/ui-custom-ping")
    def _custom_ping() -> dict[str, bool]:
        return {"pong": True}

    runtime = AppHost(config=cfg, extra_routers=[extra])
    app = create_app(config=cfg, runtime=runtime)

    # Entering TestClient context runs FastAPI lifespan -> 5-method orchestration
    with TestClient(app) as client:
        assert runtime._is_ready() is True
        assert tuple(runtime.completed_stages) == AppHost.ORDERED_STAGES

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
        assert r_disc.json()["report"]["enabled_count"] >= 1

        r_extra = client.get("/ui-custom-ping")
        assert r_extra.status_code == 200

    # Exiting TestClient context runs FastAPI lifespan -> reverse LIFO teardown
    assert runtime.state == AppHost.State.STOPPED
    assert tuple(runtime.teardown_stages) == tuple(reversed(AppHost.ORDERED_STAGES))

    # Test run_server() in production mode and --reload mode with fake uvicorn runner
    calls: list[dict[str, Any]] = []

    def _fake_uvicorn_run(target: Any, **kwargs: Any) -> None:
        calls.append({"target": target, **kwargs})

    rc_prod = run_server(
        [],
        settings_source=_MockSettings(),
        uvicorn_runner=_fake_uvicorn_run,
    )
    assert rc_prod == 0
    assert len(calls) == 1
    assert calls[0]["port"] == 8123

    rc_reload = run_server(
        ["--reload"],
        settings_source=_MockSettings(),
        uvicorn_runner=_fake_uvicorn_run,
    )
    assert rc_reload == 0
    assert len(calls) == 2
    assert calls[1]["target"] == "app.main:create_app"
    assert calls[1]["reload"] is True
    assert calls[1]["factory"] is True

    # Default create_app() and main entrypoint
    default_app = create_app(config=cfg)
    assert default_app.title == cfg.title
    default_app.state.runtime.shutdown()

    monkeypatch.setattr("uvicorn.run", _fake_uvicorn_run)
    assert main_entrypoint(["--reload"]) == 0
    assert len(calls) == 3
    assert calls[2]["reload"] is True


# ============================================================================
# 3. Headless CLI Entrypoint Tests (app/cli.py)
# ============================================================================


def test_headless_cli_commands_and_7_stage_bootstrap(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Verify app/cli.py executes 7-stage bootstrap and dispatches all commands."""
    monkeypatch.chdir(tmp_path)
    data_dir = tmp_path / "cli_data"
    plugins_dir = data_dir / "plugins"
    _seed_orphan_running_job("job-cli-orphan")
    _write_sample_plugin(plugins_dir)

    base_args = [
        "--data-dir",
        str(data_dir),
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
    assert json.loads(out_pl)["data"]["enabled_count"] >= 1

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

    rt = AppHost(data_dir=data_dir, headless=True, use_process_pool=False)
    rt.startup()
    rt.initialize_db()
    rt.register_modules()
    rt.broadcast_event("system", "host.ready")
    try:
        runner = HeadlessCliRunner(rt)
        with pytest.raises(ValueError, match="Unsupported CLI command"):
            runner.execute("nonexistent-cmd")
    finally:
        rt.shutdown()

    # 8. CLI main() with and without --data-dir
    assert cli_main(["status", "--json"]) == 0
    assert cli_main(["status", "--json", *base_args]) == 0


def test_app_host_blueprint_methods_and_single_export(tmp_path: Path) -> None:
    """Verify __all__ == ['AppHost'] and AppHost exposes exactly five public methods."""
    assert app.host.bootstrap.__all__ == ["AppHost"]

    # Assert that the ONLY public methods on AppHost are the five canonical methods
    public_methods = [
        name
        for name in dir(AppHost)
        if not name.startswith("_")
        and callable(getattr(AppHost, name))
        and not isinstance(getattr(AppHost, name), type)
    ]
    assert sorted(public_methods) == [
        "broadcast_event",
        "initialize_db",
        "register_modules",
        "shutdown",
        "startup",
    ]

    host = AppHost(
        data_dir=tmp_path,
        headless=True,
        use_process_pool=False,
    )

    # 1. Test private _write_lock context manager
    with host._write_lock():
        locked = True
    assert locked is True

    # 2. Test startup
    app_instance = host.startup()
    assert isinstance(app_instance, FastAPI)

    # 3. Test initialize_db
    assert host.initialize_db() is True

    # 4. Test register_modules
    host.register_modules()
    assert host.job_manager is not None
    assert host.job_manager.max_workers >= 1

    # 5. Test broadcast_event
    ev = host.broadcast_event(
        channel="test-channel",
        event_type="test.event",
        payload={"msg": "ping"},
    )
    assert ev.channel == "test-channel"
    assert ev.event_type == "test.event"
    assert ev.payload == {"msg": "ping"}

    # Broadcast host.ready advances to READY
    ev_ready = host.broadcast_event("system", "host.ready")
    assert ev_ready.channel == "system"
    assert str(host.state) == AppHost.State.READY.value
    assert len(host.completed_stages) == 7

    # 6. Test shutdown
    host.shutdown()
    assert str(host.state) == AppHost.State.STOPPED.value
    assert len(host.teardown_stages) == 7


def test_app_host_create_app_and_routes(tmp_path: Path) -> None:
    """Verify AppHost 5-method workflow mounts routes and returns security headers."""
    host = AppHost(
        data_dir=tmp_path,
        headless=False,
        use_process_pool=False,
    )
    app_instance = host.startup()
    host.initialize_db()
    host.register_modules(app_instance)
    host.broadcast_event("system", "host.ready")
    assert app_instance.state.runtime is host

    with TestClient(app_instance) as client:
        resp_status = client.get("/status")
        assert resp_status.status_code == 200
        assert resp_status.json()["status"] == "success"
        assert resp_status.headers["x-content-type-options"] == "nosniff"
        assert resp_status.headers["x-frame-options"] == "DENY"
        assert resp_status.headers["referrer-policy"] == "no-referrer"

        resp_specs = client.get("/specs")
        assert resp_specs.status_code == 200
        assert resp_specs.json()["status"] == "success"

        resp_constants = client.get("/constants")
        assert resp_constants.status_code == 200
        assert resp_constants.json()["status"] == "success"

    host.shutdown()


class _DummyModel:
    def to_dict(self) -> dict[str, Any]:
        return {"id": "test"}


class _DummyDataSub:
    def list_datasets(self) -> list[Any]:
        return [_DummyModel()]

    def view(self) -> list[Any]:
        return [{"symbol": "EURUSD"}]

    def get_baskets_overview(self) -> list[Any]:
        return [_DummyModel()]

    def list_brokers(self) -> list[Any]:
        return [_DummyModel()]

    def list_providers(self) -> list[Any]:
        return [_DummyModel()]

    def list_logs(self, limit: int = 50) -> list[Any]:
        return [_DummyModel()]


class _DummyInstrumentsCLI:
    @staticmethod
    def format_instruments_table(items: Any) -> str:
        return "table"

    @staticmethod
    def dispatch(args: Any, target: Any) -> dict[str, Any]:
        return {"status": "dispatched", "args": args}


class _DummySessionsCLI:
    @staticmethod
    def format_sessions_table(items: Any) -> str:
        return "table"

    @staticmethod
    def dispatch(args: Any, target: Any) -> dict[str, Any]:
        return {"status": "dispatched", "args": args}


def test_headless_cli_data_and_workspace_commands(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Verify app/cli.py data manager commands, flags, and runner error handling."""
    monkeypatch.chdir(tmp_path)
    data_dir = tmp_path / "cli_data"

    base_args = [
        "--data-dir",
        str(data_dir),
    ]

    # 1. Test live data home command
    code_home, out_home = run_cli(["data", "--action", "home", "--json", *base_args])
    assert code_home == 0
    assert json.loads(out_home)["data"]["action"] == "home"

    # 2. Test HeadlessCliRunner against mock DataManagerWorkspace sub-catalogs
    host = AppHost(data_dir=data_dir, headless=True, use_process_pool=False)
    host.startup()
    host.initialize_db()
    host.register_modules()
    host.broadcast_event("system", "host.ready")
    try:
        assert host.data_manager is not None
        host.data_manager.data = _DummyDataSub()  # type: ignore[attr-defined]
        host.data_manager.instruments = _DummyDataSub()  # type: ignore[attr-defined]
        host.data_manager.sessions = _DummyDataSub()  # type: ignore[attr-defined]
        host.data_manager.baskets = _DummyDataSub()  # type: ignore[attr-defined]
        host.data_manager.broker = _DummyDataSub()  # type: ignore[attr-defined]
        host.data_manager.connections = _DummyDataSub()  # type: ignore[attr-defined]
        host.data_manager.log = _DummyDataSub()  # type: ignore[attr-defined]

        import app.workspace.data_manager as dm_pkg

        monkeypatch.setattr(
            dm_pkg, "InstrumentsCLI", _DummyInstrumentsCLI, raising=False
        )
        monkeypatch.setattr(dm_pkg, "SessionsCLI", _DummySessionsCLI, raising=False)

        runner = HeadlessCliRunner(host)
        for sub in (
            "home",
            "datasets",
            "instruments",
            "sessions",
            "baskets",
            "brokers",
            "providers",
            "logs",
        ):
            res = runner._cmd_data(sub)
            assert res["command"] == "data"
            assert res["action"] in (sub, "home")

        with pytest.raises(ValueError, match="Unsupported data action"):
            runner._cmd_data("invalid_action")

        res_inst = runner._cmd_instrument("view")
        assert res_inst["status"] == "dispatched"
        res_inst2 = runner._cmd_instrument("view=1")
        assert res_inst2["status"] == "dispatched"
        res_inst_empty = runner._cmd_instrument("")
        assert res_inst_empty["status"] == "dispatched"

        res_sess = runner._cmd_sessions("view")
        assert res_sess["status"] == "dispatched"
        res_sess2 = runner._cmd_sessions("view=1")
        assert res_sess2["status"] == "dispatched"
        res_sess_empty = runner._cmd_sessions("")
        assert res_sess_empty["status"] == "dispatched"
    finally:
        host.shutdown()

    # 3. Test instrument and sessions without monkeypatched CLI classes (returns CLI_EXECUTION_ERROR)
    monkeypatch.delattr(dm_pkg, "InstrumentsCLI", raising=False)
    monkeypatch.delattr(dm_pkg, "SessionsCLI", raising=False)

    code_inst, out_inst = run_cli(
        ["instrument", "--action", "view", "--json", *base_args]
    )
    assert code_inst == 1
    assert "InstrumentsCLI is not available" in out_inst

    code_sess, out_sess = run_cli(
        ["sessions", "--action", "view", "--json", *base_args]
    )
    assert code_sess == 1
    assert "SessionsCLI is not available" in out_sess

    # 4. Test format_cli_output rendered branch
    assert (
        format_cli_output(
            {"command": "test", "rendered": "custom_render"}, as_json=False
        )
        == "custom_render"
    )

    # 5. Test invalid data action via run_cli (triggers run_cli error handling)
    code_bad_data, out_bad_data = run_cli(
        ["data", "--action", "invalid_sub", "--json", *base_args]
    )
    assert code_bad_data == 1
    parsed_err = json.loads(out_bad_data)
    assert parsed_err["status"] == "error"
    assert parsed_err["error"]["code"] == "CLI_EXECUTION_ERROR"
    assert "Unsupported data action" in parsed_err["error"]["message"]

    # 7. Test cli main with data directory present
    (tmp_path / "data").mkdir(parents=True, exist_ok=True)
    assert cli_main(["status", "--json"]) == 0


def test_headless_cli_runner_uninitialized_guards(tmp_path: Path) -> None:
    """Verify HeadlessCliRunner raises RuntimeError if required subsystems are None."""
    host = AppHost(data_dir=tmp_path, headless=True, use_process_pool=False)
    runner = HeadlessCliRunner(host)

    with pytest.raises(RuntimeError, match="ResourceMonitor is not initialized"):
        runner._cmd_health()

    with pytest.raises(RuntimeError, match="ResourceMonitor is not initialized"):
        runner._cmd_resources()

    with pytest.raises(RuntimeError, match="JobManager is not initialized"):
        runner._cmd_jobs("list")

    with pytest.raises(RuntimeError, match="PluginLifecycleManager is not initialized"):
        runner._cmd_plugins("list")

    with pytest.raises(RuntimeError, match="DataManagerWorkspace is not initialized"):
        runner._cmd_data("home")

    with pytest.raises(RuntimeError, match="DataManagerWorkspace is not initialized"):
        runner._cmd_instrument("view")

    with pytest.raises(RuntimeError, match="DataManagerWorkspace is not initialized"):
        runner._cmd_sessions("view")


def test_app_host_broadcast_event_ready_failure_rollback(tmp_path: Path) -> None:
    """Verify broadcast_event('system', 'host.ready') catches failure and rolls back."""
    host = AppHost(data_dir=tmp_path, headless=True, use_process_pool=False)
    host.startup()
    host.initialize_db()
    # Deliberately skip host.register_modules(), so SERVICES and ROUTES are incomplete

    with pytest.raises(
        RuntimeError, match="Cannot enter Stage READY; incomplete stage checks"
    ):
        host.broadcast_event("system", "host.ready")

    assert str(host.state) == AppHost.State.FAILED.value
    assert len(host.teardown_stages) > 0


def test_home_composition_http_and_cli(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Use the same Home objects for CLI and mounted host routes."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("HARUQUANTAI_RELEASE_FEED_URL", raising=False)
    host = AppHost(data_dir=tmp_path / "data", use_process_pool=False)
    try:
        host.startup()
        host.initialize_db()
        host.register_modules()
        assert host.home is not None and host.home_about is not None
        runner = HeadlessCliRunner(host)
        for command in ("home", "about", "updates", "diagnostics"):
            result = runner.execute(command)
            assert result["command"] == command
            assert json.loads(result["rendered"])
        assert host.app is not None
        with TestClient(host.app) as client:
            assert client.get("/api/v1/home").json()["data"]["recent_projects"] == []
            assert (
                client.get("/api/v2/home/about").json()["data"]["license"]["state"]
                == "unavailable"
            )
            assert client.get("/home/updates").json()["data"]["state"] == "unavailable"
    finally:
        host.shutdown()


def test_home_release_environment_configuration(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Compose the explicit release URL without making a network request."""
    monkeypatch.setenv(
        "HARUQUANTAI_RELEASE_FEED_URL", "https://example.invalid/releases"
    )
    config, _ = resolve_main_config(
        [],
        settings_source=type(
            "Source", (), {"get": lambda self, scope, key, default=None: default}
        )(),
    )
    assert config.home_release_feed_url == "https://example.invalid/releases"
