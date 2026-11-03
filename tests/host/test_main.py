"""Backend lifecycle, launcher, and open-stream shutdown checks."""

import asyncio
import socket
from contextlib import closing
from pathlib import Path
from unittest.mock import Mock

import httpx
import pytest
import uvicorn
from app import main as backend
from fastapi.testclient import TestClient


def test_lifespan_initializes_and_cleans_services(monkeypatch):
    settings = Mock()
    monkeypatch.setattr(backend, "SettingsManager", Mock(return_value=settings))
    gateway = Mock()
    gateway.read_records.return_value = {"success": True, "data": {"records": []}}
    application = backend.create_app(gateway)
    settings.reload.assert_not_called()
    with TestClient(application) as client:
        settings.reload.assert_called_once_with()
        gateway.read_records.assert_any_call("host_jobs", limit=1000)
        gateway.read_records.assert_any_call("datamgr_datasets", offset=0)
        assert application.state.persistence is gateway
        assert application.state.settings is settings
        assert application.state.sessions.persistence is gateway
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}
    assert not hasattr(application.state, "sessions")


def test_startup_rejects_unavailable_settings(monkeypatch):
    settings = Mock()
    settings.reload.side_effect = RuntimeError("settings unavailable")
    monkeypatch.setattr(backend, "SettingsManager", Mock(return_value=settings))
    application = backend.create_app(Mock())
    with (
        pytest.raises(RuntimeError, match="settings unavailable"),
        TestClient(application),
    ):
        pytest.fail("Startup must fail before accepting requests")
    assert not hasattr(application.state, "sessions")


@pytest.mark.parametrize("port", [8000, 0, 65536, True, "8000"])
@pytest.mark.parametrize("reload", [False, True])
def test_launcher_uses_validated_stored_settings(monkeypatch, port, reload):
    settings = Mock()
    settings.get.side_effect = ["127.0.0.1", port]
    monkeypatch.setattr(backend, "SettingsManager", Mock(return_value=settings))
    run = Mock()
    shutdown = Mock()
    monkeypatch.setattr(backend.uvicorn, "run", run)
    monkeypatch.setattr(backend, "shutdown_logging", shutdown)
    if port == 8000:
        backend.main(["--reload"] if reload else [])
        run.assert_called_once_with(
            "app.main:app",
            host="127.0.0.1",
            port=8000,
            log_config=None,
            timeout_graceful_shutdown=5,
            reload=reload,
            reload_dirs=[str(Path(backend.__file__).resolve().parent)]
            if reload
            else None,
        )
    else:
        with pytest.raises(ValueError, match=r"host\.port"):
            backend.main([])
        run.assert_not_called()
    shutdown.assert_called_once_with()


def test_shutdown_finishes_with_open_event_stream(monkeypatch):
    """An idle SSE client must not prevent shutdown or service cleanup."""
    from app.core.host import transport
    from app.core.host.events import EventBus

    settings = Mock()
    monkeypatch.setattr(backend, "SettingsManager", Mock(return_value=settings))
    monkeypatch.setattr(transport, "_require", Mock())
    bus = EventBus()
    unsubscribe = Mock(wraps=bus.unsubscribe)
    monkeypatch.setattr(bus, "unsubscribe", unsubscribe)
    monkeypatch.setattr(transport, "get_global_event_bus", lambda: bus)
    gateway = Mock()
    gateway.read_records.return_value = {"success": True, "data": {"records": []}}
    application = backend.create_app(gateway)

    async def exercise():
        with closing(socket.socket()) as listener:
            listener.bind(("127.0.0.1", 0))
            port = listener.getsockname()[1]
            server = uvicorn.Server(
                uvicorn.Config(
                    application,
                    log_config=None,
                    timeout_graceful_shutdown=backend._GRACEFUL_SHUTDOWN_SECONDS,
                )
            )
            task = asyncio.create_task(server.serve(sockets=[listener]))
            try:
                async with asyncio.timeout(10):
                    while not server.started:
                        if task.done():
                            await task
                            pytest.fail("Server stopped before startup")
                        await asyncio.sleep(0.01)
                async with httpx.AsyncClient(trust_env=False) as client:
                    async with client.stream(
                        "GET", f"http://127.0.0.1:{port}/api/v1/events?channels=system"
                    ) as response:
                        assert response.status_code == 200
                        assert response.headers["content-type"].startswith(
                            "text/event-stream"
                        )
                        assert not task.done()
                        server.should_exit = True
                        await asyncio.wait_for(asyncio.shield(task), timeout=8)
                unsubscribe.assert_called_once()
                assert not hasattr(application.state, "sessions")
                assert not server.server_state.connections
            finally:
                if not task.done():
                    server.force_exit = True
                    task.cancel()
                await asyncio.gather(task, return_exceptions=True)

    asyncio.run(exercise())


def test_lifespan_cancels_and_closes_basket_jobs(monkeypatch):
    monkeypatch.setattr(backend, "SettingsManager", Mock(return_value=Mock()))
    gateway = Mock()
    gateway.read_records.return_value = {"success": True, "data": {"records": []}}
    application = backend.create_app(gateway)
    manager = Mock()
    with TestClient(application):
        application.state.basket_jobs = manager
    manager.shutdown.assert_called_once_with(wait=True, cancel_futures=True)
    assert not hasattr(application.state, "basket_jobs")


def test_home_uses_host_capabilities(monkeypatch, tmp_path):
    """Home shares the loaded settings, catalog and job persistence authority."""
    from app.core.host.persistence import HostPersistence

    settings = Mock()
    monkeypatch.setattr(backend, "SettingsManager", Mock(return_value=settings))
    gateway = HostPersistence(tmp_path / "host.db")
    application = backend.create_app(gateway)
    with TestClient(application):
        home = application.state.home_service
        assert home._persistence is gateway
        assert home._settings_manager is settings
        assert home._data_catalog is application.state.data_catalog
        assert home._job_manager is application.state.job_manager
    assert not hasattr(application.state, "home_service")
    assert not hasattr(application.state, "job_manager")


def test_catalog_startup_failure_releases_workers(monkeypatch):
    """A failure after worker creation must still release the worker pool."""
    monkeypatch.setattr(backend, "SettingsManager", Mock(return_value=Mock()))
    jobs = Mock()
    monkeypatch.setattr(backend, "JobManager", Mock(return_value=jobs))
    monkeypatch.setattr(
        backend,
        "recover_catalog_publications",
        Mock(side_effect=RuntimeError("catalog unavailable")),
    )
    application = backend.create_app(Mock())
    with (
        pytest.raises(RuntimeError, match="catalog unavailable"),
        TestClient(application),
    ):
        pytest.fail("Startup must fail before accepting requests")
    jobs.shutdown.assert_called_once_with(wait=True, cancel_futures=True)
    for name in ("job_manager", "persistence", "settings", "data_catalog", "data_logs"):
        assert not hasattr(application.state, name)


def test_lifespan_invokes_diagnostics_and_directory_inspection(monkeypatch):
    settings = Mock()
    monkeypatch.setattr(backend, "SettingsManager", Mock(return_value=settings))
    mock_conf_log = Mock()
    mock_emit_diag = Mock()
    mock_inspect_dirs = Mock()
    monkeypatch.setattr(backend, "configure_logging_from_settings", mock_conf_log)
    monkeypatch.setattr(backend, "emit_startup_diagnostics", mock_emit_diag)
    monkeypatch.setattr(backend, "inspect_workspace_directories", mock_inspect_dirs)
    gateway = Mock()
    gateway.read_records.return_value = {"success": True, "data": {"records": []}}
    application = backend.create_app(gateway)
    with TestClient(application):
        mock_conf_log.assert_called_once_with(settings)
        mock_emit_diag.assert_called_once_with(app_version="1.0.0", settings=settings)
        mock_inspect_dirs.assert_called_once_with(settings)


def test_main_invokes_startup_diagnostics(monkeypatch):
    settings = Mock()
    settings.get.side_effect = ["127.0.0.1", 8000]
    monkeypatch.setattr(backend, "SettingsManager", Mock(return_value=settings))
    mock_conf_log = Mock()
    mock_emit_diag = Mock()
    mock_inspect_dirs = Mock()
    monkeypatch.setattr(backend, "configure_logging_from_settings", mock_conf_log)
    monkeypatch.setattr(backend, "emit_startup_diagnostics", mock_emit_diag)
    monkeypatch.setattr(backend, "inspect_workspace_directories", mock_inspect_dirs)
    monkeypatch.setattr(backend.uvicorn, "run", Mock())
    monkeypatch.setattr(backend, "shutdown_logging", Mock())

    backend.main([])
    mock_conf_log.assert_called_once_with(settings)
    mock_emit_diag.assert_called_once_with(app_version="1.0.0", settings=settings)
    mock_inspect_dirs.assert_called_once_with(settings)


def test_main_cli_host_and_port_overrides(monkeypatch):
    settings = Mock()
    settings.get.side_effect = ["127.0.0.1", 8000]
    monkeypatch.setattr(backend, "SettingsManager", Mock(return_value=settings))
    mock_run = Mock()
    monkeypatch.setattr(backend.uvicorn, "run", mock_run)
    monkeypatch.setattr(backend, "shutdown_logging", Mock())
    monkeypatch.setattr(backend, "_run_startup_diagnostics", Mock())

    backend.main(["--host", "0.0.0.0", "--port", "9090", "--reload"])
    mock_run.assert_called_once()
    _, kwargs = mock_run.call_args
    assert kwargs["host"] == "0.0.0.0"
    assert kwargs["port"] == 9090
    assert kwargs["reload"] is True


def test_main_invalid_host_and_port(monkeypatch):
    settings = Mock()
    settings.get.side_effect = ["", 8000]
    monkeypatch.setattr(backend, "SettingsManager", Mock(return_value=settings))
    monkeypatch.setattr(backend, "shutdown_logging", Mock())

    with pytest.raises(ValueError, match=r"host\.host must be a non-empty string"):
        backend.main([])

    settings2 = Mock()
    settings2.get.side_effect = ["127.0.0.1", 70000]
    monkeypatch.setattr(backend, "SettingsManager", Mock(return_value=settings2))
    with pytest.raises(
        ValueError, match=r"host\.port must be an integer between 1 and 65535"
    ):
        backend.main([])


def test_install_web_build_and_spa_routing(monkeypatch, tmp_path):
    dist_dir = tmp_path / "dist"
    dist_dir.mkdir()
    index_file = dist_dir / "index.html"
    index_file.write_text(
        "<!doctype html><html><body>App</body></html>", encoding="utf-8"
    )
    assets_dir = dist_dir / "assets"
    assets_dir.mkdir()
    bundle_file = assets_dir / "bundle.js"
    bundle_file.write_text("console.log('hi');", encoding="utf-8")
    css_file = assets_dir / "style.css"
    css_file.write_text("body { color: red; }", encoding="utf-8")
    other_file = dist_dir / "robots.txt"
    other_file.write_text("User-agent: *", encoding="utf-8")

    settings = Mock()
    settings.get_scope.return_value = {"username": "admin"}
    monkeypatch.setattr(backend, "SettingsManager", Mock(return_value=settings))
    gateway = Mock()
    gateway.read_records.return_value = {"success": True, "data": {"records": []}}
    app = backend.create_app(gateway, web_build_dir=dist_dir)

    with TestClient(app) as client:
        # GET index
        resp = client.get("/")
        assert resp.status_code == 200
        assert "text/html" in resp.headers["content-type"]
        assert "App" in resp.text

        # HEAD index
        head_resp = client.head("/")
        assert head_resp.status_code == 200
        assert head_resp.text == ""

        # GET asset JS
        js_resp = client.get("/assets/bundle.js")
        assert js_resp.status_code == 200
        assert "javascript" in js_resp.headers["content-type"]
        assert "immutable" in js_resp.headers.get("cache-control", "")

        # GET asset CSS
        css_resp = client.get("/assets/style.css")
        assert css_resp.status_code == 200
        assert "text/css" in css_resp.headers["content-type"]

        # GET other file
        txt_resp = client.get("/robots.txt")
        assert txt_resp.status_code == 200

        # SPA client fallback
        spa_resp = client.get("/workspace/overview")
        assert spa_resp.status_code == 200
        assert "App" in spa_resp.text

        # Reserved API path 404
        api_resp = client.get("/api/v1/nonexistent")
        assert api_resp.status_code == 404

        # Missing asset 404
        missing_asset = client.get("/assets/missing.js")
        assert missing_asset.status_code == 404

        # Directory traversal attempt
        trav_resp = client.get("/../outside.txt")
        assert trav_resp.status_code in (400, 404)


def test_install_web_build_missing_index(monkeypatch, tmp_path):
    empty_dist = tmp_path / "empty_dist"
    empty_dist.mkdir()
    settings = Mock()
    monkeypatch.setattr(backend, "SettingsManager", Mock(return_value=settings))
    gateway = Mock()
    gateway.read_records.return_value = {"success": True, "data": {"records": []}}
    app = backend.create_app(gateway, web_build_dir=empty_dist)

    with TestClient(app) as client:
        resp = client.get("/")
        assert resp.status_code == 503
        assert resp.json() == {"detail": "Web build unavailable"}


def test_teardown_mt5_and_scopes_for(monkeypatch):
    settings = Mock()
    settings.get_scope.return_value = {"username": "admin"}
    monkeypatch.setattr(backend, "SettingsManager", Mock(return_value=settings))
    gateway = Mock()
    gateway.read_records.return_value = {"success": True, "data": {"records": []}}
    application = backend.create_app(gateway)

    async def mock_mt5_close():
        pass

    mt5_mock = Mock()
    mt5_mock.close = mock_mt5_close

    with TestClient(application):
        application.state.data_mt5 = mt5_mock
        application.state.code_editor_compilation = Mock()

        # Check scope resolver
        sessions = application.state.sessions
        assert sessions._scope_resolver("admin") == ("*:*",)
        assert sessions._scope_resolver("other_user") == ()

    assert not hasattr(application.state, "data_mt5")
    assert not hasattr(application.state, "code_editor_compilation")
