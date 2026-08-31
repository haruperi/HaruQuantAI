"""Unit tests for the HaruQuantAI CLI entry point (app.main)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from app.main import build_parser, run


def test_build_parser_defaults() -> None:
    """Verify default parser settings match configuration."""
    parser = build_parser()
    args = parser.parse_args([])

    assert args.host == "127.0.0.1"
    assert args.port == 8000
    assert args.reload is True  # In dev environment
    assert args.workers == 1
    assert args.log_level == "info"


def test_build_parser_custom_args() -> None:
    """Verify custom CLI options parse correctly."""
    parser = build_parser()
    args = parser.parse_args(
        [
            "--host",
            "127.0.0.2",
            "--port",
            "9000",
            "--no-reload",
            "--workers",
            "4",
            "--log-level",
            "debug",
        ]
    )

    assert args.host == "127.0.0.2"
    assert args.port == 9000
    assert args.reload is False
    assert args.workers == 4
    assert args.log_level == "debug"


@patch("app.main.uvicorn.run")
def test_run_with_reload(mock_uvicorn_run: MagicMock) -> None:
    """Verify uvicorn.run is called with reload enabled."""
    run(["--host", "127.0.0.1", "--port", "8000", "--reload"])

    mock_uvicorn_run.assert_called_once_with(
        "app.services.api.composition.application:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        log_level="info",
    )


@patch("app.main.uvicorn.run")
def test_run_without_reload(mock_uvicorn_run: MagicMock) -> None:
    """Verify uvicorn.run is called with workers when reload is disabled."""
    run(["--host", "127.0.0.2", "--port", "8080", "--no-reload", "--workers", "2"])

    mock_uvicorn_run.assert_called_once_with(
        "app.services.api.composition.application:app",
        host="127.0.0.2",
        port=8080,
        reload=False,
        workers=2,
        log_level="info",
    )
