"""Portfolio bridge composition and route boundary tests.

The conversion and fail-closed behaviour of the Portfolio bridge is verified
directly against the source dispatcher (mirroring the Simulation/Trading
owner-dependency composition tests). The HTTP boundary guards (permission and
idempotency enforcement) are verified against the helper functions and through
the canonical application's route catalogue.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import pytest
from app.services.api.composition import portfolio_dependencies
from app.services.api.contracts import PortfolioConstructRequest
from app.services.api.identity import require_auth_context
from app.services.api.routes import portfolio
from app.utils import create_auth_context, utc_now
from fastapi import FastAPI, HTTPException

from tests.api._support import get_json


def _auth(permissions: tuple[str, ...] = ("portfolio:read", "portfolio:write")) -> Any:
    """Build one authorized Portfolio caller.

    Args:
        permissions: Granted backend permissions.

    Returns:
        Utils-owned authenticated context.
    """
    return create_auth_context(
        contract_version="v2",
        schema_id="utils.auth_context.v2",
        principal_id="portfolio-operator",
        principal_type="USER",
        roles=("operator",),
        permissions=permissions,
        scopes=("portfolio",),
        tenant_or_environment="development",
        runtime_profile="research",
        request_id="req-11111111-1111-4111-8111-111111111111",
        workflow_id="wf-22222222-2222-4222-8222-222222222222",
        correlation_id="cor-33333333-3333-4333-8333-333333333333",
        issued_at=utc_now(),
    )


def _construction_model() -> PortfolioConstructRequest:
    """Build one bounded secret-free Portfolio construction request model.

    Returns:
        Validated API construction request.
    """
    window_start = datetime(2026, 1, 1, tzinfo=UTC)
    window_end = datetime(2026, 6, 1, tzinfo=UTC)
    return PortfolioConstructRequest.model_validate(
        {
            "request_id": "req-aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa",
            "workflow_id": "wf-bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb",
            "correlation_id": "cor-cccccccc-cccc-4ccc-8ccc-cccccccccccc",
            "portfolio_id": "port-1",
            "portfolio_version": "v1",
            "scope": {"tenant": "dev"},
            "components": [
                {
                    "component_id": "comp-1",
                    "strategy_id": "strat-1",
                    "strategy_version": "1.0.0",
                    "registry_record_hash": "a" * 64,
                    "eligibility_decision_id": "elig-1",
                }
            ],
            "method": "fixed",
            "fixed_weights": [
                {
                    "component_id": "comp-1",
                    "capital_weight": "1",
                    "proposed_risk_budget_weight": "1",
                }
            ],
            "evidence": {
                "account_snapshot_id": "acc-1",
                "account_snapshot_hash": "b" * 64,
                "account_snapshot_as_of": window_start,
                "market_dataset_id": "mkt-1",
                "market_dataset_hash": "c" * 64,
                "market_dataset_as_of": window_start,
                "analytics_evidence_id": "anl-1",
                "analytics_evidence_hash": "d" * 64,
                "analytics_evidence_as_of": window_start,
                "fx_evidence_ids": ["fx-1"],
                "fx_evidence_hashes": ["e" * 64],
            },
            "measurement_start": window_start,
            "measurement_end": window_end,
            "base_currency": "USD",
            "runtime_profile": "simulation",
            "execution_route": "sim",
            "simulation_policy_version": "pol-1",
            "requested_at": datetime(2026, 6, 2, tzinfo=UTC),
        }
    )


def test_construct_source_converts_and_delegates(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The bridge converts the API DTO into the strict Portfolio request."""
    converted = object()
    expected = object()
    contracts: list[str] = []
    monkeypatch.setattr(
        portfolio_dependencies,
        "create_portfolio_value",
        lambda contract, **_values: contracts.append(contract) or converted,
    )
    monkeypatch.setattr(
        portfolio_dependencies,
        "construct_portfolio",
        lambda handle, request, auth: (handle, request, auth, expected),
    )
    source = portfolio_dependencies.build_portfolio_source("handle")
    auth = _auth()
    result = source("construct", _construction_model(), auth)
    assert contracts == ["PortfolioConstructionRequest"]
    assert result == ("handle", converted, auth, expected)


def test_construct_source_normalizes_lists_to_tuples(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Strict Portfolio tuple fields receive tuples, not JSON lists."""
    captured: dict[str, object] = {}

    def fake_value(contract: str, **values: object) -> object:
        captured.update(values)
        return object()

    monkeypatch.setattr(portfolio_dependencies, "create_portfolio_value", fake_value)
    monkeypatch.setattr(
        portfolio_dependencies,
        "construct_portfolio",
        lambda *_args: object(),
    )
    source = portfolio_dependencies.build_portfolio_source("handle")
    source("construct", _construction_model(), _auth())
    components = captured["components"]
    fixed_weights = captured["fixed_weights"]
    fx_ids = captured["evidence"]["fx_evidence_ids"]  # type: ignore[index]
    assert isinstance(components, tuple)
    assert isinstance(fixed_weights, tuple)
    assert isinstance(fx_ids, tuple)


def test_source_fails_closed_without_dependencies() -> None:
    """A missing Portfolio bundle never triggers speculative execution."""
    source = portfolio_dependencies.build_portfolio_source(None)
    with pytest.raises(RuntimeError, match="PORTFOLIO_RUNTIME_UNAVAILABLE"):
        source("construct", _construction_model(), _auth())
    with pytest.raises(RuntimeError, match="PORTFOLIO_RUNTIME_UNAVAILABLE"):
        source("status", "port-1", {"tenant": "dev"}, _auth())
    with pytest.raises(RuntimeError, match="PORTFOLIO_RUNTIME_UNAVAILABLE"):
        source("history", "port-1", _auth())


def test_source_rejects_unknown_operation() -> None:
    """Only the three registered operations are dispatchable."""
    source = portfolio_dependencies.build_portfolio_source(object())
    with pytest.raises(ValueError, match="unsupported Portfolio operation"):
        source("activate")


def test_status_and_history_delegate_to_owner(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Read operations delegate exact identifiers to Portfolio functions."""
    status_expected = object()
    history_expected = object()
    monkeypatch.setattr(
        portfolio_dependencies,
        "get_portfolio_status",
        lambda _handle, portfolio_id, scope, _auth: (
            portfolio_id,
            scope,
            status_expected,
        ),
    )
    monkeypatch.setattr(
        portfolio_dependencies,
        "get_portfolio_history",
        lambda _handle, portfolio_id, _auth: (portfolio_id, history_expected),
    )
    source = portfolio_dependencies.build_portfolio_source("handle")
    auth = _auth()
    assert source("status", "port-1", {"tenant": "dev"}, auth) == (
        "port-1",
        {"tenant": "dev"},
        status_expected,
    )
    assert source("history", "port-1", auth) == ("port-1", history_expected)


def test_require_idempotency_rejects_blank_and_oversized() -> None:
    """The idempotency helper rejects missing, blank, and oversized keys."""
    with pytest.raises(HTTPException) as blank:
        portfolio._require_idempotency(None)
    assert blank.value.status_code == 422
    assert blank.value.detail == "IDEMPOTENCY_KEY_REQUIRED"
    with pytest.raises(HTTPException) as whitespace:
        portfolio._require_idempotency("   ")
    assert whitespace.value.status_code == 422
    with pytest.raises(HTTPException) as oversized:
        portfolio._require_idempotency(
            "x" * (portfolio._MAX_IDEMPOTENCY_KEY_LENGTH + 1)
        )
    assert oversized.value.status_code == 422
    assert portfolio._require_idempotency("key-1") == "key-1"


def test_status_read_delegates_exact_scope() -> None:
    """The status read derives scope only from authenticated query parameters."""
    captured: list[tuple[str, str, dict[str, str]]] = []

    def _source(operation: str, *args: object) -> object:
        captured.append((operation, str(args[0]), dict(args[1])))  # type: ignore[arg-type]
        return {"status": "success", "portfolio_id": "port-1"}

    app = FastAPI()
    app.include_router(portfolio.router)
    app.dependency_overrides[require_auth_context] = _auth
    app.dependency_overrides[portfolio._portfolio_source] = lambda: _source
    status_code, _body = get_json(
        app,
        "/api/v1/portfolio/port-1/status",
        query_string="scope_key=tenant&scope_value=dev",
    )
    assert status_code == 200
    assert captured == [("status", "port-1", {"tenant": "dev"})]


def test_status_requires_read_permission() -> None:
    """A caller without read permission is rejected before delegation."""

    def _source(operation: str, *args: object) -> object:
        raise AssertionError("source must not be called without permission")

    app = FastAPI()
    app.include_router(portfolio.router)
    app.dependency_overrides[require_auth_context] = lambda: _auth(
        permissions=("portfolio:write",)
    )
    app.dependency_overrides[portfolio._portfolio_source] = lambda: _source
    status_code, _body = get_json(
        app,
        "/api/v1/portfolio/port-1/status",
        query_string="scope_key=tenant&scope_value=dev",
    )
    assert status_code == 403


def test_history_read_delegates_portfolio_id() -> None:
    """The history read delegates the path portfolio identifier once."""
    captured: list[str] = []

    def _source(operation: str, *args: object) -> object:
        captured.append(str(args[0]))
        return {"status": "success", "allocations": []}

    app = FastAPI()
    app.include_router(portfolio.router)
    app.dependency_overrides[require_auth_context] = _auth
    app.dependency_overrides[portfolio._portfolio_source] = lambda: _source
    status_code, _body = get_json(app, "/api/v1/portfolio/port-1/history")
    assert status_code == 200
    assert captured == ["port-1"]
