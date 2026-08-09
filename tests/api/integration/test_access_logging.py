"""Integration evidence for canonical API access-log routing."""

from __future__ import annotations

from pathlib import Path
from typing import cast

import pytest
from app.services.api import (
    build_request_context_middleware,
    build_route_contract,
    build_route_contract_registry,
    build_secret_redaction_middleware,
)
from app.utils import configure_logging, flush_logging, shutdown_logging
from fastapi import FastAPI
from fastapi.testclient import TestClient
from starlette.types import ASGIApp


def test_api_request_reaches_general_and_access_logs(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Route one secret-safe API request to app and access logs only."""
    monkeypatch.setenv("LOG_DIRECTORY", str(tmp_path))
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")
    monkeypatch.setenv("LOG_RENDER", "json")
    monkeypatch.setenv("LOG_ENQUEUE", "false")
    monkeypatch.setenv("LOG_COLORIZE", "false")
    shutdown_logging()
    configure_logging()

    app = FastAPI()

    @app.get("/api/logging/access")
    async def access_demo() -> dict[str, str]:
        """Return one bounded response for access-routing verification."""
        return {"status": "ok"}

    contract = build_route_contract(
        route_id="api.logging.access",
        method="GET",
        path="/api/logging/access",
        owner="api",
    )
    wrapped = build_request_context_middleware(
        app,
        route_contract_registry=build_route_contract_registry((contract,)),
    )
    wrapped = build_secret_redaction_middleware(cast("ASGIApp", wrapped))
    try:
        response = TestClient(cast("ASGIApp", wrapped)).get(
            "/api/logging/access",
            headers={
                "authorization": "Bearer must-not-be-logged",
                "cookie": "hq_session=must-not-be-logged",
            },
        )
        assert response.status_code == 200
        flush_logging()
    finally:
        shutdown_logging()

    app_log = (tmp_path / "app.log").read_text(encoding="utf-8")
    access_log = (tmp_path / "access.log").read_text(encoding="utf-8")
    debug_log = (tmp_path / "debug.log").read_text(encoding="utf-8")
    errors_log = (tmp_path / "errors.log").read_text(encoding="utf-8")
    for content in (app_log, access_log):
        assert "api.request_telemetry" in content
        assert '"route":"/api/logging/access"' in content
        assert "must-not-be-logged" not in content
    assert "api.request_telemetry" not in debug_log
    assert "api.request_telemetry" not in errors_log
