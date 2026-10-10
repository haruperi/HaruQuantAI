"""Unit tests for app/host/bootstrap.py.

Verifies lifespan stages, reverse-order shutdown, readiness assessment,
FastAPI shell application composition, and non-silent FR log emissions.
"""

from __future__ import annotations

import asyncio
import logging
import sqlite3
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest
from app.host.bootstrap import (
    HostRuntime,
    HostSettings,
    LifespanStage,
    ReadinessState,
    create_host_app,
    create_recovery_router,
    reconcile_database,
)
from app.host.bootstrap import (
    main as bootstrap_main,
)
from app.host.persistence import DatabaseManager, IncompatibleSchemaError, SettingsStore
from app.host.session import hash_password
from app.host.settings import HostSettings as AppSettings
from fastapi import FastAPI
from fastapi.testclient import TestClient


@pytest.fixture(autouse=True)
def isolated_default_store(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Resolve pre-existing default-path fixtures to a temporary host store."""
    from app.host import persistence
    from app.host.settings import HostSettings

    path = tmp_path / "default-host.db"
    monkeypatch.setattr(persistence, "DEFAULT_DATABASE_PATH", path)
    settings = HostSettings(path)
    settings.update(
        {
            "app.general": {"host": "127.0.0.1", "backend_port": 8000},
            "config.troubleshooting": {"debug_level_active": False},
            "workspace_paths": {"data_dir": str(tmp_path / "data")},
        }
    )
    monkeypatch.setattr("app.host.bootstrap.default_host_settings", settings)
    monkeypatch.setattr("app.main.default_host_settings", settings)


def test_bootstrap_normal_startup_and_stop(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Verify normal startup sequence through all lifespan stages and teardown."""

    async def _test() -> None:
        caplog.set_level(logging.INFO)
        settings = HostSettings(title="Test Host", version="2.1.0")
        runtime = HostRuntime(settings)

        assert runtime.get_state() == ReadinessState.NOT_STARTED
        assert not runtime.is_ready()

        snapshot = await runtime.start()

        assert snapshot.state == ReadinessState.READY
        assert snapshot.is_ready
        assert runtime.is_ready()
        assert runtime.active_stage == LifespanStage.READY
        assert LifespanStage.CONFIGURING in snapshot.completed_stages
        assert LifespanStage.ROUTES in snapshot.completed_stages

        # Verify FR-HOST-BOOT-LIFECYCLE-STAGES log and numbered stage progression
        stage_logs = [
            r.message
            for r in caplog.records
            if "FR-HOST-BOOT-LIFECYCLE-STAGES" in r.message
        ]
        assert len(stage_logs) > 0
        assert any("[1/6] Stage CONFIGURING" in m for m in stage_logs)
        assert any("[2/6] Stage PATHS" in m for m in stage_logs)
        assert any("[3/6] Stage LOGGING" in m for m in stage_logs)
        assert any("[4/6] Stage DISCOVERY" in m for m in stage_logs)
        assert any("[5/6] Stage SERVICES" in m for m in stage_logs)
        assert any("Substage 1/4" in m for m in stage_logs)
        assert any("Substage 2/4" in m for m in stage_logs)
        assert any("Substage 3/4" in m for m in stage_logs)
        assert any("Substage 4/4" in m for m in stage_logs)
        assert any("[6/6] Stage ROUTES" in m for m in stage_logs)
        assert any("[READY]" in m for m in stage_logs)

        # Stop and verify reverse shutdown
        await runtime.stop()
        assert runtime.get_state() == ReadinessState.STOPPED
        assert not runtime.is_ready()

        shutdown_logs = [
            r.message
            for r in caplog.records
            if "FR-HOST-BOOT-REVERSE-SHUTDOWN" in r.message
        ]
        assert len(shutdown_logs) > 0

    asyncio.run(_test())


def test_bootstrap_safe_repeated_stop(caplog: pytest.LogCaptureFixture) -> None:
    """Verify calling stop() repeatedly is idempotent and safe."""

    async def _test() -> None:
        caplog.set_level(logging.INFO)
        runtime = HostRuntime()

        # Repeated stop before starting
        await runtime.stop()
        assert runtime.get_state() == ReadinessState.NOT_STARTED

        # Start and stop
        await runtime.start()
        assert runtime.get_state() == ReadinessState.READY
        await runtime.stop()
        assert runtime.get_state() == ReadinessState.STOPPED

        # Second stop call
        await runtime.stop()
        assert runtime.get_state() == ReadinessState.STOPPED

        no_op_logs = [
            r.message for r in caplog.records if "Repeated stop requested" in r.message
        ]
        assert len(no_op_logs) >= 1

    asyncio.run(_test())


def test_bootstrap_startup_failure_reverse_rollback(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Verify acquired stages are rolled back in reverse order upon failure."""

    async def _test() -> None:
        caplog.set_level(logging.INFO)
        runtime = HostRuntime()

        cleanup_order: list[str] = []

        async def async_cleanup_discovery() -> None:
            cleanup_order.append("discovery")

        def sync_cleanup_paths() -> None:
            cleanup_order.append("paths")

        original_advance = runtime._advance_stage

        async def advance_with_hooks(
            stage: LifespanStage, check_key: str, cleanup: Any | None = None
        ) -> None:
            if stage == LifespanStage.PATHS:
                await original_advance(stage, check_key, cleanup=sync_cleanup_paths)
            elif stage == LifespanStage.DISCOVERY:
                await original_advance(
                    stage, check_key, cleanup=async_cleanup_discovery
                )
            elif stage == LifespanStage.SERVICES:
                raise RuntimeError("Injected services stage failure")
            else:
                await original_advance(stage, check_key, cleanup=cleanup)

        with (
            patch.object(runtime, "_advance_stage", side_effect=advance_with_hooks),
            pytest.raises(RuntimeError, match="Injected services stage failure"),
        ):
            await runtime.start()

        assert runtime.get_state() == ReadinessState.FAILED
        assert runtime.active_stage == LifespanStage.FAILED
        assert not runtime.is_ready()

        # Discovery acquired after paths, so rollback must release discovery first
        assert cleanup_order == ["discovery", "paths"]

        # Verify FR logs emitted for failure and rollback
        rollback_logs = [
            r.message
            for r in caplog.records
            if "FR-HOST-BOOT-REVERSE-SHUTDOWN" in r.message
        ]
        assert len(rollback_logs) > 0

    asyncio.run(_test())


def test_readiness_snapshot_behavior(caplog: pytest.LogCaptureFixture) -> None:
    """Verify readiness snapshot reflects operational state and non-silent logs."""

    async def _test() -> None:
        caplog.set_level(logging.DEBUG)
        runtime = HostRuntime()

        # Not ready initially
        unready = runtime.get_readiness()
        assert not unready.is_ready
        assert unready.state == ReadinessState.NOT_STARTED

        warning_logs = [
            r.message
            for r in caplog.records
            if "FR-HOST-BOOT-READINESS-ASSESSMENT" in r.message
            and "Host is not ready" in r.message
        ]
        assert len(warning_logs) >= 1

        # Ready after start
        await runtime.start()
        ready = runtime.get_readiness()
        assert ready.is_ready
        assert ready.state == ReadinessState.READY
        assert ready.uptime_seconds >= 0.0

        debug_logs = [
            r.message
            for r in caplog.records
            if "FR-HOST-BOOT-READINESS-ASSESSMENT" in r.message
            and "Host is ready" in r.message
        ]
        assert len(debug_logs) >= 1

        await runtime.stop()

    asyncio.run(_test())


def test_fastapi_shell_endpoints_and_lifespan(
    caplog: pytest.LogCaptureFixture,
    tmp_path: Path,
) -> None:
    """Verify FastAPI composition and shell endpoints via TestClient."""
    caplog.set_level(logging.INFO)
    db_file = tmp_path / "test_bootstrap_settings.db"
    store = SettingsStore(db_file)
    store.initialize()
    conn = sqlite3.connect(db_file)
    conn.execute(
        """
        INSERT INTO host_settings (scope, key, value_json, schema_version, updated_at_utc)
        VALUES
            ('application', 'app_general', '{"theme":"dark","zoom":1.0}', 1, '2026-10-07T00:00:00Z')
        """
    )
    conn.commit()
    conn.close()
    app_config = AppSettings(db_file, auto_load=True)

    settings = HostSettings(
        title="Test Shell", version="2.1.0", reference_cohort="SQX145 Dev 1"
    )
    app_config.update(
        {
            "user_access": {
                "username": "operator",
                "password_hash": hash_password("test-password"),
            }
        }
    )
    runtime = HostRuntime(settings)
    app = create_host_app(settings, runtime=runtime, configuration=app_config)

    comp_logs = [
        r.message for r in caplog.records if "FR-HOST-BOOT-APP-COMPOSITION" in r.message
    ]
    assert len(comp_logs) >= 1

    with TestClient(app) as client:
        login = client.post("/api/v1/auth/login", json={"password": "test-password"})
        assert login.status_code == 200
        client.headers["Authorization"] = "Bearer " + login.json()["data"]["token"]
        # App is in lifespan: runtime should be ready
        assert runtime.is_ready()

        # 1. /status
        resp = client.get("/api/v1/status")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "success"
        assert data["data"]["is_ready"] is True
        assert data["data"]["version"] == "2.1.0"
        assert data["data"]["reference_cohort"] == "SQX145 Dev 1"
        for detected, expected in ((12, 12), (None, 1), (0, 1)):
            with patch("app.host.bootstrap.os.cpu_count", return_value=detected):
                assert (
                    client.get("/api/v1/status").json()["data"]["cpu_count"] == expected
                )

        # 2. /readiness
        resp_ready = client.get("/api/v1/readiness")
        assert resp_ready.status_code == 200
        ready_data = resp_ready.json()
        assert ready_data["status"] == "success"
        assert ready_data["data"]["is_ready"] is True

        # 3. /app-loaded
        assert not runtime.is_app_loaded()
        resp_loaded = client.post("/api/v1/app-loaded")
        assert resp_loaded.status_code == 200
        assert resp_loaded.json()["data"]["acknowledged"] is True
        assert runtime.is_app_loaded()

        # 4. /about
        resp_about = client.get("/api/v1/about")
        assert resp_about.status_code == 200
        about_data = resp_about.json()["data"]
        assert about_data["application"] == "HaruQuantAI"
        assert "Clean-room" in about_data["disposition"]

        # 5. /settings (GET and PUT)
        resp_settings = client.get("/api/v1/settings")
        assert resp_settings.status_code == 200
        settings_data = resp_settings.json()["data"]
        assert settings_data["revision"] == 2
        assert settings_data["values"]["app.general"]["theme"] == "dark"

        update_resp = client.put(
            "/api/v1/settings",
            json={
                "expected_revision": 2,
                "changes": {
                    "app.general": {"theme": "light", "zoom": 1.1},
                },
            },
        )
        assert update_resp.status_code == 200
        updated_data = update_resp.json()["data"]
        assert updated_data["revision"] == 3
        assert updated_data["values"]["app.general"]["theme"] == "light"
        assert updated_data["values"]["app.general"]["zoom"] == 1.1

        # 6. /auth/login
        resp_login = client.post(
            "/api/v1/auth/login", json={"password": "test-password"}
        )
        assert resp_login.status_code == 200
        assert "token" in resp_login.json()["data"]

    # Outside TestClient lifespan: runtime should have stopped cleanly
    assert runtime.get_state() == ReadinessState.STOPPED


def test_fastapi_readiness_returns_503_when_unready() -> None:
    """Verify /readiness returns HTTP 503 when host runtime is unready."""
    settings = HostSettings()
    runtime = HostRuntime(settings)
    app = create_host_app(settings, runtime=runtime)

    client = TestClient(app, raise_server_exceptions=False)
    # Without entering lifespan context, runtime is NOT_STARTED
    resp = client.get("/api/v1/readiness")
    assert resp.status_code == 503
    data = resp.json()
    assert data["status"] == "error"
    assert data["data"]["is_ready"] is False


def test_bootstrap_start_when_already_ready(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Verify calling start() when already ready is safe and returns snapshot."""

    async def _test() -> None:
        caplog.set_level(logging.INFO)
        runtime = HostRuntime()
        await runtime.start()
        assert runtime.get_state() == ReadinessState.READY

        # Calling start again
        snapshot = await runtime.start()
        assert snapshot.is_ready
        assert runtime.get_state() == ReadinessState.READY

        already_ready_logs = [
            r.message
            for r in caplog.records
            if "Host runtime is already ready" in r.message
        ]
        assert len(already_ready_logs) >= 1
        await runtime.stop()

    asyncio.run(_test())


def test_bootstrap_rollback_with_cleanup_exception(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Verify cleanup callback errors during rollback are caught and logged."""

    async def _test() -> None:
        caplog.set_level(logging.INFO)
        runtime = HostRuntime()

        def broken_cleanup() -> None:
            raise ValueError("Cleanup exploded")

        original_advance = runtime._advance_stage

        async def advance_with_broken_cleanup(
            stage: LifespanStage, check_key: str, cleanup: Any | None = None
        ) -> None:
            if stage == LifespanStage.PATHS:
                await original_advance(stage, check_key, cleanup=broken_cleanup)
            elif stage == LifespanStage.LOGGING:
                raise RuntimeError("Trigger rollback")
            else:
                await original_advance(stage, check_key, cleanup=cleanup)

        with (
            patch.object(
                runtime, "_advance_stage", side_effect=advance_with_broken_cleanup
            ),
            pytest.raises(RuntimeError, match="Trigger rollback"),
        ):
            await runtime.start()

        assert runtime.get_state() == ReadinessState.FAILED
        error_logs = [
            r.message for r in caplog.records if "Error releasing stage" in r.message
        ]
        assert len(error_logs) >= 1

    asyncio.run(_test())


def test_bootstrap_state_property() -> None:
    """Verify state property returns current state."""
    runtime = HostRuntime()
    assert runtime.state == ReadinessState.NOT_STARTED


def test_cors_and_transport_middleware() -> None:
    """Verify CORS headers and TransportMiddleware timing/request headers."""
    settings = HostSettings()
    runtime = HostRuntime(settings)
    app = create_host_app(settings, runtime=runtime)

    with TestClient(app) as client:
        resp = client.get(
            "/api/v1/status",
            headers={"Origin": "http://127.0.0.1:3000"},
        )
        assert resp.status_code == 200
        assert (
            resp.headers.get("access-control-allow-origin") == "http://127.0.0.1:3000"
        )
        assert "x-request-id" in resp.headers
        assert "x-response-time-ms" in resp.headers


def test_mounted_capability_routers(tmp_path: Path) -> None:
    """Verify diagnostics, debugconsole, persistence, and jobs routers are mounted."""
    db_file = tmp_path / "test_mounted_routers.db"
    store = SettingsStore(db_file)
    store.initialize()
    app_config = AppSettings(db_file, auto_load=True)

    settings = HostSettings()
    runtime = HostRuntime(settings)
    app = create_host_app(settings, runtime=runtime, configuration=app_config)

    with TestClient(app) as client:
        diag_resp = client.get("/api/v1/diagnostics/system")
        assert diag_resp.status_code == 200

        dbg_resp = client.get("/api/v1/debugconsole/categories")
        assert dbg_resp.status_code == 200

        pers_resp = client.get("/api/v1/persistence/status")
        assert pers_resp.status_code == 200

        jobs_resp = client.get("/api/v1/jobs/capacity")
        assert jobs_resp.status_code == 200


def test_bootstrap_cli_main() -> None:
    """Verify bootstrap.main parses CLI flags and invokes uvicorn with settings."""
    from app.host.bootstrap import main as bootstrap_main

    with (
        patch("uvicorn.run") as mock_uvicorn,
        patch("app.host.bootstrap.shutdown") as mock_shutdown,
    ):
        bootstrap_main(["--host", "127.0.0.1", "--port", "7777", "--debug"])
        assert mock_uvicorn.called
        call_args, call_kwargs = mock_uvicorn.call_args
        assert call_kwargs["host"] == "127.0.0.1"
        assert call_kwargs["port"] == 7777
        assert call_kwargs["timeout_graceful_shutdown"] == 2
        assert mock_shutdown.called


def test_recovery_router_uses_injected_workflow() -> None:
    """Recovery HTTP calls its bootstrap workflow and preserves the envelope."""
    calls: list[bool] = []

    def recover() -> dict[str, Any]:
        calls.append(True)
        return {"status": "reconciled", "pruned_expired_leases": 2}

    app = FastAPI()
    app.include_router(create_recovery_router(recover))
    with TestClient(app) as client:
        response = client.post(
            "/persistence/recovery/reconcile", headers={"x-request-id": "recovery-test"}
        )
    assert response.status_code == 200
    assert response.json()["data"] == {
        "status": "reconciled",
        "pruned_expired_leases": 2,
    }
    assert calls == [True]


def test_recovery_cli_bypasses_server_and_closes_database(tmp_path: Path) -> None:
    """Recovery uses only the requested store and releases it on success."""
    path = tmp_path / "recovery-cli.db"
    with (
        patch(
            "app.host.bootstrap.DatabaseManager", wraps=DatabaseManager
        ) as constructor,
        patch.object(DatabaseManager, "close", autospec=True) as close,
        patch("app.host.bootstrap.create_host_app") as create_app,
        patch("app.host.bootstrap.default_host_settings") as global_settings,
    ):
        assert bootstrap_main(["--reconcile", "--db", str(path)]) == 0
        constructor.assert_called_once_with(path)
        close.assert_called_once()
        create_app.assert_not_called()
        assert not global_settings.mock_calls
    assert path.exists()


@pytest.mark.parametrize("outcome, expected", [("incomplete", 1), ("exception", 2)])
def test_recovery_cli_failure_closes_database(
    tmp_path: Path, outcome: str, expected: int
) -> None:
    """Recovery failures return a process code and always release ownership."""
    with (
        patch.object(DatabaseManager, "close", autospec=True) as close,
        patch.object(HostRuntime, "reconcile_persistence") as recover,
    ):
        if outcome == "exception":
            recover.side_effect = IncompatibleSchemaError("invalid schema")
        else:
            recover.return_value = {"status": outcome, "pruned_expired_leases": 0}
        assert reconcile_database(tmp_path / "failed-recovery.db") == expected
        close.assert_called_once()


def test_password_login_shared_session_integration(tmp_path: Path) -> None:
    """Real host login shares authority across settings, SSE, me and revocation."""
    from app.host.session import AuthenticationError
    from app.host.transport import get_event_bus

    settings = HostSettings(
        tmp_path / "integrated-login.db", data_dir=tmp_path / "data"
    )
    settings.update(
        {
            "application": {"app_general": {"theme": "dark"}},
            "user_access": {
                "username": "configured-user",
                "password_hash": hash_password("test-password"),
            },
        }
    )
    runtime = HostRuntime(settings)
    app = create_host_app(settings, runtime=runtime, configuration=settings)
    with TestClient(app) as client:
        assert client.post("/api/v1/auth/login", json={}).status_code == 401
        assert (
            client.post("/api/v1/auth/login", json={"password": "wrong"}).status_code
            == 401
        )
        assert client.post("/api/v1/app-loaded").status_code == 401
        assert not runtime.is_app_loaded()
        assert client.get("/api/v1/settings").status_code == 401
        login = client.post("/api/v1/auth/login", json={"password": "test-password"})
        assert login.status_code == 200
        token = login.json()["data"]["token"]
        headers = {"Authorization": f"Bearer {token}"}
        assert login.json()["data"]["username"] == "configured-user"
        assert login.json()["data"]["host_instance_id"] == runtime.host_instance_id
        assert client.get("/api/v1/sessions/me", headers=headers).status_code == 200
        snapshot = client.get("/api/v1/settings", headers=headers)
        assert snapshot.status_code == 200
        assert "user_access" not in snapshot.json()["data"]["values"]
        assert "password_hash" not in snapshot.text
        assert (
            client.put(
                "/api/v1/settings",
                headers=headers,
                json={
                    "expected_revision": 1,
                    "changes": {"user_access": {"username": "other"}},
                },
            ).status_code
            == 422
        )
        cursor = get_event_bus().current_cursor
        saved = client.put(
            "/api/v1/settings",
            headers=headers,
            json={
                "expected_revision": snapshot.json()["data"]["revision"],
                "changes": {"app.general": {"theme": "light"}},
            },
        )
        assert saved.status_code == 200
        notification = client.get(
            f"/api/v1/events?channels=settings.changed&since_cursor={cursor}&limit=1",
            headers=headers,
        )
        assert notification.status_code == 200
        frame = next(
            line[6:]
            for line in notification.text.splitlines()
            if line.startswith("data: ")
        )
        import json

        assert json.loads(frame)["payload"] == {
            "revision": saved.json()["data"]["revision"]
        }
        assert "password_hash" not in notification.text
        assert client.post("/api/v1/app-loaded", headers=headers).status_code == 200
        get_event_bus().publish("login.probe", "ping", {"ready": True})
        stream = client.get(
            "/api/v1/events?channels=login.probe&since_cursor=0&limit=1",
            headers=headers,
        )
        assert stream.status_code == 200 and "login.probe" in stream.text
        assert (
            client.get(
                "/api/v1/events?limit=1",
                headers={"Authorization": "Bearer bootstrap-token-fake"},
            ).status_code
            == 401
        )
        assert (
            client.post("/api/v1/sessions/revoke", headers=headers).status_code == 200
        )
        assert client.get("/api/v1/settings", headers=headers).status_code == 401
        assert client.get("/api/v1/sessions/me", headers=headers).status_code == 401
        assert (
            client.post(
                "/api/v1/sessions/login",
                json={"password": "test-password", "role": "system"},
            ).status_code
            == 401
        )
        fresh = client.post("/api/v1/login", json={"password": "test-password"}).json()[
            "data"
        ]["token"]
    with pytest.raises(AuthenticationError):
        runtime.session_manager.verify_session(fresh)
    import warnings

    with warnings.catch_warnings(record=True) as captured:
        warnings.simplefilter("always")
        schema = app.openapi()
    assert "post" in schema["paths"]["/api/v1/auth/login"]
    assert not any(
        "Duplicate Operation ID" in str(warning.message) for warning in captured
    )
