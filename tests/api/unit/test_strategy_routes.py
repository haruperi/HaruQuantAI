"""Authenticated Strategy catalogue route tests."""

from typing import Any

import pytest
from app.services.api.identity import require_auth_context
from app.services.api.widgets.strategies import routes as strategies
from app.services.api.widgets.strategies.routes import router
from app.utils import create_auth_context, utc_now
from fastapi import FastAPI

from tests.api._support import get_json


def _auth() -> object:
    """Build one authorized Strategy reader."""
    return create_auth_context(
        contract_version="v2",
        schema_id="utils.auth_context.v2",
        principal_id="strategy-reader",
        principal_type="USER",
        roles=("researcher",),
        permissions=("strategy:read",),
        scopes=("strategy",),
        tenant_or_environment="development",
        runtime_profile="research",
        request_id="req-11111111-1111-4111-8111-111111111111",
        workflow_id="wf-22222222-2222-4222-8222-222222222222",
        correlation_id="cor-33333333-3333-4333-8333-333333333333",
        issued_at=utc_now(),
    )


def _app() -> FastAPI:
    """Build one authenticated Strategy read application."""
    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[require_auth_context] = _auth
    return app


def test_strategy_catalogue_reads_delegate_to_owner(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Catalogue and filtered version reads preserve owner delegation."""
    calls: list[str | None] = []

    def versions(strategy_id: str | None = None) -> tuple[dict[str, Any], ...]:
        calls.append(strategy_id)
        return ({"strategy_id": strategy_id or "all"},)

    monkeypatch.setattr(strategies, "list_strategy_versions", versions)
    catalogue_status, catalogue = get_json(_app(), "/api/v1/strategies")
    version_status, version = get_json(_app(), "/api/v1/strategies/alpha/versions")

    assert (catalogue_status, catalogue) == (200, [{"strategy_id": "all"}])
    assert (version_status, version) == (200, [{"strategy_id": "alpha"}])
    assert calls == [None, "alpha"]
