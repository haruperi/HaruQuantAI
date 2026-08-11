"""Dataset preparation bridge composition and route boundary tests.

Symbol discovery is covered by the pagination contract suite. These tests cover
the governed dataset-preparation boundary: permission, idempotency, fail-closed
composition, and the exact two-step Data delegation.
"""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any
from uuid import uuid4

import pytest
from app.services.api.composition import data_dependencies
from app.services.api.identity import require_auth_context
from app.services.api.routes import data
from app.utils import create_auth_context, utc_now
from fastapi import FastAPI

from tests.api._support import get_json, post_json


def _key() -> str:
    """Return one fresh idempotency key.

    Durable reservations are retained for at least 24 hours, so a literal key
    would only be reservable on the first run of the suite. A unique key per
    call keeps these tests hermetic.

    Returns:
        Unique idempotency key.
    """
    return f"test-{uuid4()}"


_PAYLOAD = {
    "market_request": {"symbol": "EURUSD", "timeframe": "H1"},
    "save_request": {"destination": "datasets/eurusd-h1"},
}


def _auth(permissions: tuple[str, ...] = ("data:read", "data:write")) -> Any:
    """Build one authorized Data caller.

    Args:
        permissions: Granted backend permissions.

    Returns:
        Utils-owned authenticated context.
    """
    return create_auth_context(
        contract_version="v2",
        schema_id="utils.auth_context.v2",
        principal_id="data-operator",
        principal_type="USER",
        roles=("operator",),
        permissions=permissions,
        scopes=("data",),
        tenant_or_environment="development",
        runtime_profile="research",
        request_id="req-11111111-1111-4111-8111-111111111111",
        workflow_id="wf-22222222-2222-4222-8222-222222222222",
        correlation_id="cor-33333333-3333-4333-8333-333333333333",
        issued_at=utc_now(),
    )


def _app(source: Any, permissions: tuple[str, ...] | None = None) -> FastAPI:
    """Build one router-only application bound to a stub dispatcher.

    Args:
        source: Stub dataset dispatcher.
        permissions: Optional exact granted permissions.

    Returns:
        Configured FastAPI application.
    """
    app = FastAPI()
    app.include_router(data.router)
    app.dependency_overrides[require_auth_context] = lambda: _auth(
        permissions=permissions or ("data:read", "data:write")
    )
    app.dependency_overrides[data._dataset_source] = lambda: source
    return app


def test_capability_catalog_surfaces_all_data_features() -> None:
    """The authenticated read surface reports every Data feature exactly once."""
    status_code, body = get_json(_app(lambda *_args: None), "/api/v1/data/capabilities")

    assert status_code == 200
    capabilities = body["data"]["capabilities"]
    assert [item["feature_id"] for item in capabilities] == [
        f"FEAT-DATA-{index:02d}" for index in range(1, 15)
    ]


def test_prepare_requires_idempotency_key() -> None:
    """Preparation without an idempotency key never reaches Data."""

    def _source(operation: str, *args: object) -> object:
        raise AssertionError("source must not be called without an idempotency key")

    status_code, body = post_json(
        _app(_source), "/api/v1/data/datasets/prepare", _PAYLOAD
    )
    assert status_code == 422
    assert body["detail"] == "IDEMPOTENCY_KEY_REQUIRED"


def test_prepare_requires_write_permission() -> None:
    """Read permission alone never authorizes dataset preparation."""

    def _source(operation: str, *args: object) -> object:
        raise AssertionError("source must not be called without permission")

    status_code, _body = post_json(
        _app(_source, permissions=("data:read",)),
        "/api/v1/data/datasets/prepare",
        _PAYLOAD,
        headers={"Idempotency-Key": _key()},
    )
    assert status_code == 403


def test_prepare_delegates_both_owner_requests() -> None:
    """The route forwards the market and save payloads unchanged."""
    captured: list[tuple[str, dict[str, object], dict[str, object]]] = []

    def _source(operation: str, *args: object) -> object:
        captured.append((operation, dict(args[0]), dict(args[1])))  # type: ignore[arg-type]
        return {"status": "success"}

    status_code, _body = post_json(
        _app(_source),
        "/api/v1/data/datasets/prepare",
        _PAYLOAD,
        headers={"Idempotency-Key": _key()},
    )
    assert status_code == 200
    assert captured == [
        ("prepare", dict(_PAYLOAD["market_request"]), dict(_PAYLOAD["save_request"]))
    ]


def test_prepare_translates_unavailable_dataset_to_503() -> None:
    """An absent owner dataset becomes a bounded 503, never an invented result."""

    def _source(operation: str, *args: object) -> object:
        raise RuntimeError("DATASET_UNAVAILABLE")

    status_code, body = post_json(
        _app(_source),
        "/api/v1/data/datasets/prepare",
        _PAYLOAD,
        headers={"Idempotency-Key": _key()},
    )
    assert status_code == 503
    assert body["detail"] == "DATASET_UNAVAILABLE"


def test_replayed_key_conflicts_instead_of_repeating_the_write() -> None:
    """A second identical governed request never re-executes the owner call.

    Preparation has no owner read-back that could reproduce the original
    manifest, so the replay is reported as a bounded 409 rather than silently
    duplicating a governed write or inventing a response.
    """
    calls: list[str] = []

    def _source(operation: str, *args: object) -> object:
        calls.append(operation)
        return {"status": "success"}

    app = _app(_source)
    key = _key()
    first, _first_body = post_json(
        app,
        "/api/v1/data/datasets/prepare",
        _PAYLOAD,
        headers={"Idempotency-Key": key},
    )
    second, second_body = post_json(
        app,
        "/api/v1/data/datasets/prepare",
        _PAYLOAD,
        headers={"Idempotency-Key": key},
    )
    assert first == 200
    assert second == 409
    assert second_body["detail"] == "IDEMPOTENCY_CONFLICT"
    assert calls == ["prepare"]


# --- External import (NFR-API-014) --------------------------------------------


def test_import_requires_idempotency_key() -> None:
    """An import without an idempotency key never reaches Data."""

    def _source(operation: str, *args: object) -> object:
        raise AssertionError("source must not be called without an idempotency key")

    status_code, body = post_json(
        _app(_source), "/api/v1/data/imports", {"payload": {"path": "a.csv"}}
    )
    assert status_code == 422
    assert body["detail"] == "IDEMPOTENCY_KEY_REQUIRED"


def test_import_requires_write_permission() -> None:
    """Read permission alone never authorizes an import."""

    def _source(operation: str, *args: object) -> object:
        raise AssertionError("source must not be called without permission")

    status_code, _body = post_json(
        _app(_source, permissions=("data:read",)),
        "/api/v1/data/imports",
        {"payload": {"path": "a.csv"}},
        headers={"Idempotency-Key": _key()},
    )
    assert status_code == 403


def test_import_forwards_payload_unchanged() -> None:
    """Data owns parsing and dialects; the payload passes through untouched."""
    captured: list[tuple[str, dict[str, object]]] = []

    def _source(operation: str, *args: object) -> object:
        captured.append((operation, dict(args[0])))  # type: ignore[arg-type]
        return {"status": "success"}

    payload = {"path": "prices.csv", "dialect": "mt5-export"}
    status_code, _body = post_json(
        _app(_source),
        "/api/v1/data/imports",
        {"payload": payload},
        headers={"Idempotency-Key": _key()},
    )
    assert status_code == 200
    assert captured == [("import", payload)]


def test_dialects_read_delegates_to_owner_truth() -> None:
    """The gateway keeps no dialect list; it asks Data every time."""
    captured: list[str] = []

    def _source(operation: str, *args: object) -> object:
        captured.append(operation)
        return {"csv": "comma separated"}

    status_code, _body = get_json(_app(_source), "/api/v1/data/imports/dialects")
    assert status_code == 200
    assert captured == ["dialects"]


def test_import_source_delegates_to_data(monkeypatch: pytest.MonkeyPatch) -> None:
    """The dispatcher builds the owner request and imports exactly once."""
    calls: list[str] = []
    monkeypatch.setattr(
        data_dependencies,
        "build_external_import_request",
        lambda **kw: calls.append("build") or kw,
    )
    monkeypatch.setattr(
        data_dependencies,
        "import_external_dataset",
        lambda request: calls.append("import") or request,
    )
    source = data_dependencies.build_dataset_source()
    result = source("import", {"path": "a.csv"})
    assert calls == ["build", "import"]
    assert result == {"path": "a.csv"}


def test_source_rejects_unknown_operation() -> None:
    """Only the registered preparation operation is dispatchable."""
    source = data_dependencies.build_dataset_source()
    with pytest.raises(ValueError, match="unsupported Data operation"):
        source("delete", {}, {})


def test_source_fails_closed_when_owner_returns_no_dataset(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A Data response without a dataset never reaches the storage boundary."""
    monkeypatch.setattr(
        data_dependencies, "build_market_data_request", lambda **_kw: object()
    )
    monkeypatch.setattr(
        data_dependencies, "fetch_market_dataset", lambda _request: object()
    )
    source = data_dependencies.build_dataset_source()
    with pytest.raises(RuntimeError, match="DATASET_UNAVAILABLE"):
        source("prepare", {"symbol": "EURUSD"}, {"destination": "x"})


def test_source_delegates_fetch_then_save(monkeypatch: pytest.MonkeyPatch) -> None:
    """Preparation fetches once, then persists the returned owner dataset."""
    calls: list[str] = []

    class _Response:
        data = "dataset-value"

    monkeypatch.setattr(
        data_dependencies,
        "build_market_data_request",
        lambda **kw: calls.append("market") or kw,
    )
    monkeypatch.setattr(
        data_dependencies,
        "fetch_market_dataset",
        lambda _request: calls.append("fetch") or _Response(),
    )
    monkeypatch.setattr(
        data_dependencies,
        "build_dataset_save_request",
        lambda **kw: calls.append("save-request") or kw,
    )
    monkeypatch.setattr(
        data_dependencies,
        "save_dataset",
        lambda request: calls.append("save") or request,
    )
    source = data_dependencies.build_dataset_source()
    result = source("prepare", {"symbol": "EURUSD"}, {"destination": "x"})
    assert calls == ["market", "fetch", "save-request", "save"]
    assert result["dataset"] == "dataset-value"  # type: ignore[index]


def _markets_app() -> FastAPI:
    """Build one router-only application for the markets route.

    The markets handler requires only ``data:read`` and delegates to Data's
    directory builder, so no dataset-source stub is needed.

    Returns:
        Configured FastAPI application.
    """
    app = FastAPI()
    app.include_router(data.router)
    app.dependency_overrides[require_auth_context] = lambda: _auth(
        permissions=("data:read",)
    )
    return app


def test_markets_requires_read_permission() -> None:
    """The markets route refuses callers without data:read permission."""
    app = FastAPI()
    app.include_router(data.router)
    app.dependency_overrides[require_auth_context] = lambda: _auth(permissions=())
    status_code, _body = get_json(app, "/api/v1/data/markets")
    assert status_code == 403


def test_markets_delegates_once_with_resolved_source(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The markets route resolves the runtime broker and delegates once to Data."""
    from fastapi.testclient import TestClient

    captured: dict[str, str | None] = {}

    def _fake_resolve(
        override: str | None = None, *, request_id: str | None = None
    ) -> str:
        captured["override"] = override
        return "mt5"

    def _fake_directory(request: object) -> object:
        captured["source_id"] = request.source_id
        captured["limit"] = request.limit
        return SimpleNamespace(
            status="success",
            data={
                "source_id": "mt5",
                "rows": [],
                "limit": 25,
                "next_cursor": None,
                "revision": "rev-1",
                "generated_at": "2026-08-10T12:00:00Z",
                "request_id": "req-1",
            },
            message="ok",
            error=None,
            metadata={},
        )

    monkeypatch.setattr(data, "resolve_runtime_source_id", _fake_resolve)
    monkeypatch.setattr(data, "list_market_directory", _fake_directory)

    client = TestClient(_markets_app(), raise_server_exceptions=True)
    response = client.get("/api/v1/data/markets?limit=25")

    assert response.status_code == 200
    body = response.json()
    assert body["data"]["source_id"] == "mt5"
    assert captured["override"] is None
    assert captured["source_id"] == "mt5"
    assert captured["limit"] == 25


def test_markets_forwards_explicit_source_id(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """An explicit source_id query parameter overrides runtime-broker resolution."""
    from fastapi.testclient import TestClient

    captured: dict[str, str | None] = {}

    def _fake_resolve(
        override: str | None = None, *, request_id: str | None = None
    ) -> str:
        captured["override"] = override
        return override or ""

    monkeypatch.setattr(data, "resolve_runtime_source_id", _fake_resolve)
    monkeypatch.setattr(
        data,
        "list_market_directory",
        lambda _request: SimpleNamespace(
            status="success",
            data={},
            message="ok",
            error=None,
            metadata={},
        ),
    )

    client = TestClient(_markets_app(), raise_server_exceptions=True)
    response = client.get("/api/v1/data/markets?source_id=binance_spot")
    assert response.status_code == 200
    assert captured["override"] == "binance_spot"
