"""Backend lifecycle and launcher checks without binding a network port."""

from pathlib import Path
from unittest.mock import Mock

import pytest
from app import main as backend
from fastapi.testclient import TestClient


def test_lifespan_initializes_and_cleans_services(monkeypatch):
    settings = Mock()
    monkeypatch.setattr(backend, "SettingsManager", Mock(return_value=settings))
    gateway = Mock()
    application = backend.create_app(gateway)
    settings.reload.assert_not_called()
    with TestClient(application) as client:
        settings.reload.assert_called_once_with()
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
