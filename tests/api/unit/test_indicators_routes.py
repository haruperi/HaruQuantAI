"""Authenticated Indicators route unit tests."""

from __future__ import annotations

from app.services.api.identity import require_auth_context
from app.services.api.routes.indicators import router
from fastapi import FastAPI

from tests.api._support import get_json
from tests.strategy.unit.test_models import make_auth


def _app(*, authenticated: bool = True) -> FastAPI:
    """Build an isolated FastAPI app for Indicators route tests."""
    app = FastAPI()
    app.include_router(router)
    if authenticated:
        auth = make_auth().model_copy(
            update={"permissions": ("indicators:read",)},
        )
        app.dependency_overrides[require_auth_context] = lambda: auth
    return app


def test_list_indicator_catalogue_authenticated() -> None:
    """GET /api/v1/indicators returns all 64 registered specs."""
    status_code, body = get_json(_app(authenticated=True), "/api/v1/indicators")
    assert status_code == 200
    assert isinstance(body, dict)
    assert body["status"] == "success"
    assert len(body["data"]) == 64


def test_get_indicator_capabilities_authenticated() -> None:
    """GET /api/v1/indicators/capabilities returns all 64 capability records."""
    status_code, body = get_json(
        _app(authenticated=True), "/api/v1/indicators/capabilities"
    )
    assert status_code == 200
    assert isinstance(body, dict)
    assert body["status"] == "success"
    assert len(body["data"]) == 64


def test_get_indicator_spec_authenticated() -> None:
    """GET /api/v1/indicators/sma returns standard response with SMA spec."""
    status_code, body = get_json(_app(authenticated=True), "/api/v1/indicators/sma")
    assert status_code == 200
    assert isinstance(body, dict)
    assert body["status"] == "success"
    assert body["data"]["indicator_id"] == "sma"


def test_indicators_routes_unauthenticated() -> None:
    """Unauthenticated requests to indicators routes fail closed with 401."""
    status_code, body = get_json(_app(authenticated=False), "/api/v1/indicators")
    assert status_code == 401
    assert isinstance(body, dict)
    assert body["detail"] == "AUTHENTICATION_REQUIRED"
