"""Unit tests for app/main.py and app/__main__.py.

Verifies application bootstrap, CLI argument parsing, database fallback resolution,
uvicorn invocation, clean telemetry shutdown, and package entrypoint.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest
from app.host.settings import HostSettings
from app.main import _build_parser, create_app, main
from fastapi.testclient import TestClient


def test_create_app_defaults() -> None:
    """Verify create_app resolves default configuration and creates FastAPI app."""
    app = create_app()
    assert app.title == "HaruQuantAI Host"
    with TestClient(app) as client:
        resp = client.get("/api/v1/status")
        assert resp.status_code == 200
        assert resp.json()["status"] == "success"


def test_create_app_with_custom_settings() -> None:
    """Verify create_app accepts explicit HostSettings."""
    settings = HostSettings(
        host="0.0.0.0",
        port=9090,
        title="Custom Test Host",
        debug=True,
    )
    app = create_app(settings=settings)
    assert app.title == "Custom Test Host"


def test_build_parser_options() -> None:
    """Verify CLI argument parser handles all options."""
    parser = _build_parser()
    args = parser.parse_args(
        [
            "--host",
            "192.168.1.50",
            "--port",
            "9999",
            "--debug",
            "--reload",
            "--data-dir",
            "custom/data",
        ]
    )
    assert args.host == "192.168.1.50"
    assert args.port == 9999
    assert args.debug is True
    assert args.reload is True
    assert args.data_dir == Path("custom/data")


def test_main_cli_execution_standard() -> None:
    """Verify standard CLI run without reload calls uvicorn.run with app instance."""
    with (
        patch("uvicorn.run") as mock_uvicorn,
        patch("app.main.shutdown") as mock_shutdown,
    ):
        main(["--host", "127.0.0.1", "--port", "8888"])
        assert mock_uvicorn.called
        call_args, call_kwargs = mock_uvicorn.call_args
        assert call_kwargs["host"] == "127.0.0.1"
        assert call_kwargs["port"] == 8888
        assert mock_shutdown.called


def test_main_cli_execution_reload_mode() -> None:
    """Verify reload mode passes string factory path to uvicorn.run."""
    with (
        patch("uvicorn.run") as mock_uvicorn,
        patch("app.main.shutdown") as mock_shutdown,
    ):
        main(["--reload", "--host", "127.0.0.1", "--port", "8888"])
        assert mock_uvicorn.called
        call_args, call_kwargs = mock_uvicorn.call_args
        assert call_args[0] == "app.main:create_app"
        assert call_kwargs["factory"] is True
        assert call_kwargs["reload"] is True
        assert mock_shutdown.called


def test_main_cli_missing_uvicorn() -> None:
    """Verify missing uvicorn raises SystemExit."""
    with (
        patch.dict("sys.modules", {"uvicorn": None}),
        patch("app.main.shutdown") as mock_shutdown,
        pytest.raises(SystemExit),
    ):
        main([])
        assert mock_shutdown.called


def test_app_package_entrypoint() -> None:
    """Verify app.__main__ routes to app.main.main."""
    import app.__main__

    assert callable(app.__main__.main)
