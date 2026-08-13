"""Authenticated Indicators route unit tests."""

from __future__ import annotations

from types import SimpleNamespace

from app.services.api.identity import require_auth_context
from app.services.api.workstation.indicators import (
    orchestration as indicator_orchestration,
)
from app.services.api.workstation.indicators import routes as indicator_routes
from app.services.api.workstation.indicators.routes import router
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
    assert body["metadata"]["schema_id"] == "api.metadata.v1"
    assert body["metadata"]["route"] == "/api/v1/indicators"
    assert body["metadata"]["operation"] == "api.indicators.list"


def test_get_indicator_capabilities_authenticated() -> None:
    """GET /api/v1/indicators/capabilities returns all 64 capability records."""
    status_code, body = get_json(
        _app(authenticated=True), "/api/v1/indicators/capabilities"
    )
    assert status_code == 200
    assert isinstance(body, dict)
    assert body["status"] == "success"
    assert len(body["data"]) == 64
    assert body["metadata"]["schema_id"] == "api.metadata.v1"
    assert body["metadata"]["operation"] == "api.indicators.capabilities"


def test_get_indicator_spec_authenticated() -> None:
    """GET /api/v1/indicators/sma returns standard response with SMA spec."""
    status_code, body = get_json(_app(authenticated=True), "/api/v1/indicators/sma")
    assert status_code == 200
    assert isinstance(body, dict)
    assert body["status"] == "success"
    assert body["data"]["indicator_id"] == "sma"
    assert body["metadata"]["schema_id"] == "api.metadata.v1"
    assert body["metadata"]["route"] == "/api/v1/indicators/{indicator_id}"
    assert body["metadata"]["operation"] == "api.indicators.get_spec"


def test_indicators_routes_unauthenticated() -> None:
    """Unauthenticated requests to indicators routes fail closed with 401."""
    status_code, body = get_json(_app(authenticated=False), "/api/v1/indicators")
    assert status_code == 401
    assert isinstance(body, dict)
    assert body["detail"] == "AUTHENTICATION_REQUIRED"


def test_indicator_series_route_forwards_validated_query(monkeypatch) -> None:
    """The chart-series route forwards one bounded EMA read."""
    captured: dict[str, object] = {}

    def _fake_orchestrate(**kwargs: object) -> object:
        captured.update(kwargs)
        return {"status": "success", "data": {"indicator_id": "ema"}}

    monkeypatch.setattr(
        indicator_routes, "orchestrate_indicator_series", _fake_orchestrate
    )
    status_code, body = get_json(
        _app(),
        "/api/v1/indicators/ema/series",
        query_string="symbol=EURUSD&timeframe=M15&period=20&limit=100",
    )

    assert status_code == 200
    assert body["data"]["indicator_id"] == "ema"
    assert captured["indicator_id"] == "ema"
    assert captured["symbol"] == "EURUSD"
    assert captured["timeframe"] == "M15"
    assert captured["period"] == 20
    assert captured["source"] == "close"
    assert captured["limit"] == 100
    assert captured["start"] is None
    assert captured["end"] is None


def test_indicator_series_route_rejects_unsupported_indicator() -> None:
    """An indicator outside the initial EMA/RSI manifest fails closed."""
    status_code, _body = get_json(
        _app(),
        "/api/v1/indicators/macd/series",
        query_string="symbol=EURUSD",
    )
    assert status_code == 422


def test_indicator_orchestration_fetches_uncached_data_and_delegates(
    monkeypatch,
) -> None:
    """EMA receives the exact uncached Data-owned dataset."""
    dataset = object()
    indicator_response = SimpleNamespace(status="success", data=object(), error=None)
    captured: dict[str, object] = {}

    def _resolve_source(source_id: str | None, *, request_id: str) -> str:
        assert source_id is None
        assert request_id == "req-test"
        return "mt5"

    monkeypatch.setattr(
        indicator_orchestration, "resolve_runtime_source_id", _resolve_source
    )

    def _build_request(**kwargs: object) -> object:
        captured.update(kwargs)
        return object()

    monkeypatch.setattr(
        indicator_orchestration, "build_market_data_request", _build_request
    )
    monkeypatch.setattr(
        indicator_orchestration,
        "get_market_data",
        lambda _request: SimpleNamespace(status="success", data=dataset),
    )

    def _ema(owner_dataset: object, *, period: int, source: str) -> object:
        assert owner_dataset is dataset
        assert period == 20
        assert source == "close"
        return indicator_response

    monkeypatch.setattr(indicator_orchestration, "ema", _ema)
    monkeypatch.setattr(
        indicator_orchestration,
        "build_indicator_series_response",
        lambda response, **kwargs: {"response": response, **kwargs},
    )

    result = indicator_orchestration.orchestrate_indicator_series(
        indicator_id="ema",
        symbol="EURUSD",
        timeframe="H1",
        period=20,
        source="close",
        limit=100,
        start=None,
        end=None,
        source_id=None,
        request_id="req-test",
    )

    assert captured["use_cache"] is False
    assert captured["data_kind"] == "bars"
    assert result["response"] is indicator_response
