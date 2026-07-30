"""Unit tests for the observability scrape route."""

from __future__ import annotations

from decimal import Decimal
from types import SimpleNamespace

import pytest
from app.services.api import create_in_process_metric_sink
from app.services.api.identity import require_auth_context
from app.services.api.routes import observability
from fastapi import FastAPI

from tests.api._support import get_json


def _context(*, permissions: tuple[str, ...] = ("ops:metrics:read",)) -> object:
    """Build one synthetic auth context for route calls."""
    return SimpleNamespace(
        principal_type="USER",
        permissions=permissions,
        request_id="req-11111111-1111-4111-8111-111111111111",
        correlation_id="cor-33333333-3333-4333-8333-333333333333",
    )


def _app(
    *,
    sink: object,
    permissions: tuple[str, ...] = ("ops:metrics:read",),
) -> FastAPI:
    """Build one focused test app with dependency overrides."""
    app = FastAPI()
    app.include_router(observability.router)
    app.dependency_overrides[require_auth_context] = lambda: _context(
        permissions=permissions,
    )
    app.dependency_overrides[observability._metrics_sink] = lambda: sink
    return app


def test_disabled_metrics_returns_not_found(monkeypatch: pytest.MonkeyPatch) -> None:
    """When metrics are disabled the endpoint exposes no scrape surface."""
    monkeypatch.setenv("METRICS_ENABLED", "false")
    sink = create_in_process_metric_sink()
    sink.record("api_metric_total", Decimal(1), labels={"service": "api"})

    status_code, body = get_json(_app(sink=sink), "/api/metrics")

    assert status_code == 404
    assert body["detail"] == "METRICS_DISABLED"


def test_scrape_requires_permission(monkeypatch: pytest.MonkeyPatch) -> None:
    """Missing scrape permission must be rejected by identity enforcement."""
    monkeypatch.setenv("METRICS_ENABLED", "true")
    sink = create_in_process_metric_sink()
    sink.record("api_metric_total", Decimal(1), labels={"service": "api"})

    status_code, body = get_json(
        _app(sink=sink, permissions=("ops:read",)),
        "/api/metrics",
    )

    assert status_code == 403
    assert body["detail"] == "AUTHORIZATION_DENIED"


def test_scrape_returns_prometheus_payload(monkeypatch: pytest.MonkeyPatch) -> None:
    """Authorized scrape returns a typed response with exposition payload."""
    monkeypatch.setenv("METRICS_ENABLED", "true")
    sink = create_in_process_metric_sink()
    sink.record("api_metric_total", Decimal(1), labels={"service": "api"})

    status_code, body = get_json(_app(sink=sink), "/api/metrics")

    assert status_code == 200
    assert body["status"] == "success"
    assert "api_metric_total" in body["data"]
    assert body["metadata"]["route"] == "/api/metrics"
