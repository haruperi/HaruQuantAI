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
        gateway.read_records.assert_called_once_with("datamgr_datasets", offset=0)
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
    from app.host.events import EventBus

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
