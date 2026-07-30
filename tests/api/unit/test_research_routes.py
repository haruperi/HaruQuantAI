"""Authenticated Research route tests."""

from pathlib import Path

from app.services.api import build_research_run_request
from app.services.api.identity import require_auth_context
from app.services.api.routes.research import router
from fastapi import FastAPI

from tests.api._support import post_json
from tests.research._support import make_dataset, make_edge_lab_config
from tests.strategy.unit.test_models import make_auth


def _app(*, authenticated: bool) -> FastAPI:
    """Build an isolated API application.

    Args:
        authenticated: Whether to inject a valid human principal.

    Returns:
        Configured FastAPI application.
    """
    app = FastAPI()
    app.include_router(router)
    if authenticated:
        auth = make_auth().model_copy(
            update={"permissions": ("research:run",)},
        )
        app.dependency_overrides[require_auth_context] = lambda: auth
    return app


def test_only_registered_report_crosses_boundary(tmp_path: Path) -> None:
    """Verify authenticated Research route returns a standard response."""
    request = build_research_run_request(
        hypothesis="Returns persist over one research bar.",
        dataset=make_dataset(),
        config=make_edge_lab_config(tmp_path),
    )

    status_code, body = post_json(
        _app(authenticated=True),
        "/api/research/run",
        request.model_dump(mode="json"),
    )

    assert status_code == 200, body
    assert set(body) == {"status", "message", "data", "error", "metadata"}
    assert body["status"] == "success"
    assert body["error"] is None
    assert body["data"]["schema_id"] == "research.report.v1"
    assert body["data"]["hypothesis"] == request.hypothesis
    assert body["data"]["advisory_only"] is True
    assert body["metadata"]["name"] == "research.run_edge_lab_profile"


def test_research_route_fails_closed_without_authentication(tmp_path: Path) -> None:
    """Verify missing authentication prevents Research delegation."""
    request = build_research_run_request(
        hypothesis="Returns persist over one research bar.",
        dataset=make_dataset(),
        config=make_edge_lab_config(tmp_path),
    )

    status_code, body = post_json(
        _app(authenticated=False),
        "/api/research/run",
        request.model_dump(mode="json"),
    )

    assert status_code == 401
    assert body["detail"] == "AUTHENTICATION_REQUIRED"
