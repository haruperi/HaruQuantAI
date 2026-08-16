"""Portfolio bridge composition and route boundary tests.

The conversion and fail-closed behaviour of the Portfolio bridge is verified
directly against the source dispatcher (mirroring the Simulation/Trading
owner-dependency composition tests). The HTTP boundary guards (permission and
idempotency enforcement) are verified against the helper functions and through
the canonical application's route catalogue.
"""

from __future__ import annotations

from datetime import UTC, datetime
from types import SimpleNamespace
from typing import Any, ClassVar
from uuid import uuid4

import pytest
from app.services.api import build_api_settings
from app.services.api.identity import require_auth_context
from app.services.api.workstation.portfolio import (
    orchestration as portfolio_dependencies,
)
from app.services.api.workstation.portfolio import routes as portfolio
from app.services.api.workstation.portfolio.schemas import (
    PortfolioConstructRequest,
    PortfolioDefinitionRequest,
)
from app.utils import create_auth_context, utc_now
from fastapi import FastAPI, HTTPException

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
    """Only registered Portfolio operations are dispatchable."""
    source = portfolio_dependencies.build_portfolio_source(object())
    with pytest.raises(ValueError, match="unsupported Portfolio operation"):
        source("liquidate")


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


def test_definition_source_injects_authenticated_trace(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Definition registration derives trace identity from authenticated context."""
    captured: dict[str, object] = {}
    definition = object()
    monkeypatch.setattr(
        portfolio_dependencies,
        "create_portfolio_value",
        lambda _contract, **values: captured.update(values) or definition,
    )
    monkeypatch.setattr(
        portfolio_dependencies,
        "register_portfolio_definition",
        lambda handle, value, auth: (handle, value, auth),
    )
    auth = _auth()
    boundary = PortfolioDefinitionRequest(
        portfolio_id="port-1",
        portfolio_version="v1",
        scope={"environment": "simulation"},
        definition={"objective": "balanced"},
        canonical_hash="a" * 64,
    )
    result = portfolio_dependencies.build_portfolio_source("handle")(
        "register_definition", boundary, auth
    )
    assert result == ("handle", definition, auth)
    assert captured["request_id"] == auth.request_id
    assert captured["workflow_id"] == auth.workflow_id
    assert captured["correlation_id"] == auth.correlation_id


def test_definition_read_delegates_exact_identity(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Definition reads delegate exact immutable identity."""
    expected = object()
    monkeypatch.setattr(
        portfolio_dependencies,
        "get_portfolio_definition",
        lambda handle, portfolio_id, version, auth: (
            handle,
            portfolio_id,
            version,
            auth,
            expected,
        ),
    )
    auth = _auth()
    result = portfolio_dependencies.build_portfolio_source("handle")(
        "definition", "port-1", "v1", auth
    )
    assert result == ("handle", "port-1", "v1", auth, expected)


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


# --- Governed allocation lifecycle (FR-API-056) ---------------------------------


_LIFECYCLE_PERMISSIONS = (
    "portfolio:read",
    "portfolio:write",
    "portfolio:activate",
    "portfolio:rebalance",
)


def _activation_payload() -> dict[str, Any]:
    """Build one bounded secret-free activation request payload.

    Returns:
        JSON-compatible activation request body.
    """
    construction = _construction_model().model_dump(mode="json")
    return {
        "construction": construction,
        "simulation": {
            "request_id": "req-aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa",
            "workflow_id": "wf-bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb",
            "correlation_id": "cor-cccccccc-cccc-4ccc-8ccc-cccccccccccc",
            "portfolio_id": "port-1",
            "construction_result_id": "res-1",
            "construction_version": "v1",
            "components": [],
            "measurement_start": "2026-01-01T00:00:00Z",
            "measurement_end": "2026-06-01T00:00:00Z",
            "base_currency": "USD",
            "fx_evidence_ids": ["fx-1"],
            "fx_evidence_versions": ["1"],
            "fx_evidence_hashes": ["e" * 64],
            "execution_profile_version": "exec-1",
            "risk_policy_version": "risk-1",
            "seed": 7,
            "initial_balance": "100000",
            "runtime_profile": "simulation",
            "execution_route": "sim",
            "config_hash": "f" * 64,
        },
        "approval_refs": ["appr-1"],
        "expires_at": "2026-07-01T00:00:00Z",
        "expected_predecessor": None,
        "expected_revision": 0,
    }


def _lifecycle_app(
    source: Any,
    permissions: tuple[str, ...] | None = None,
    settings: Any = None,
) -> FastAPI:
    """Build one router-only application bound to a stub dispatcher.

    Args:
        source: Stub Portfolio operation dispatcher.
        permissions: Optional exact granted permissions.
        settings: Optional composed settings. Defaults to the safe development
            profile, under which no live route is configured.

    Returns:
        Configured FastAPI application.
    """
    app = FastAPI()
    app.include_router(portfolio.router)
    app.dependency_overrides[require_auth_context] = lambda: _auth(
        permissions=permissions or _LIFECYCLE_PERMISSIONS
    )
    app.dependency_overrides[portfolio._portfolio_source] = lambda: source
    app.state.api_settings = settings or build_api_settings()
    return app


def _rebalance_payload(route: str, profile: str) -> dict[str, Any]:
    """Build one complete rebalance request body.

    Args:
        route: Execution route named by the request.
        profile: Runtime profile named by the request.

    Returns:
        Rebalance request payload.
    """
    return {
        "plan": {"plan_id": "plan-1"},
        "account_evidence_ref": "acc-1",
        "market_evidence_ref": "mkt-1",
        "fx_evidence_refs": ["fx-1"],
        "runtime_profile": profile,
        "execution_route": route,
        "approval_refs": ["appr-1"],
        "approval_token_ref": "tok-1",
        "trading_request_id": "treq-1",
        "valid_until": "2026-07-01T00:00:00Z",
    }


def test_activate_requires_idempotency_key() -> None:
    """A governed activation without an idempotency key never delegates."""

    def _source(operation: str, *args: object) -> object:
        raise AssertionError("source must not be called without an idempotency key")

    status_code, body = post_json(
        _lifecycle_app(_source),
        "/api/v1/portfolio/port-1/activate",
        _activation_payload(),
    )
    assert status_code == 422
    assert body["detail"] == "IDEMPOTENCY_KEY_REQUIRED"


def test_activate_requires_activate_permission() -> None:
    """Write permission alone never authorizes an activation."""

    def _source(operation: str, *args: object) -> object:
        raise AssertionError("source must not be called without permission")

    status_code, _body = post_json(
        _lifecycle_app(_source, permissions=("portfolio:read", "portfolio:write")),
        "/api/v1/portfolio/port-1/activate",
        _activation_payload(),
        headers={"Idempotency-Key": _key()},
    )
    assert status_code == 403


def test_activate_rejects_portfolio_identity_mismatch() -> None:
    """A path and body that disagree on identity fail closed before delegation."""

    def _source(operation: str, *args: object) -> object:
        raise AssertionError("source must not be called on identity mismatch")

    status_code, body = post_json(
        _lifecycle_app(_source),
        "/api/v1/portfolio/other-portfolio/activate",
        _activation_payload(),
        headers={"Idempotency-Key": _key()},
    )
    assert status_code == 422
    assert body["detail"] == "PORTFOLIO_IDENTITY_MISMATCH"


def test_activate_delegates_once_with_idempotency_key() -> None:
    """An authorized activation delegates exactly once carrying its key."""
    captured: list[tuple[str, str]] = []

    def _source(operation: str, *args: object) -> object:
        captured.append((operation, str(args[2])))
        return {"status": "success"}

    key = _key()
    status_code, _body = post_json(
        _lifecycle_app(_source),
        "/api/v1/portfolio/port-1/activate",
        _activation_payload(),
        headers={"Idempotency-Key": key},
    )
    assert status_code == 200
    assert captured == [("activate", key)]


def test_rollback_delegates_with_target_version() -> None:
    """Rollback carries the immutable prior version to the owner boundary."""
    captured: list[tuple[str, str]] = []

    def _source(operation: str, *args: object) -> object:
        captured.append((operation, str(args[0].rollback_of_version)))
        return {"status": "success"}

    payload = _activation_payload() | {"rollback_of_version": "v0"}
    status_code, _body = post_json(
        _lifecycle_app(_source),
        "/api/v1/portfolio/port-1/rollback",
        payload,
        headers={"Idempotency-Key": _key()},
    )
    assert status_code == 200
    assert captured == [("rollback", "v0")]


def test_rebalance_forwards_the_configured_live_route() -> None:
    """A live-configured deployment forwards a live rebalance unchanged.

    Demo and live differ only by broker credentials, so the boundary must not
    reshape or refuse a live request once the deployment is configured for it.
    """
    captured: list[tuple[str, str, str]] = []

    def _source(operation: str, *args: object) -> object:
        req = args[0]
        captured.append((operation, str(req.runtime_profile), str(req.execution_route)))
        return {"status": "success"}

    status_code, _body = post_json(
        _lifecycle_app(
            _source,
            settings=build_api_settings(
                runtime_profile="live",
                execution_route="live",
                allow_live_mutations=True,
            ),
        ),
        "/api/v1/portfolio/rebalance",
        _rebalance_payload("live", "live"),
        headers={"Idempotency-Key": _key()},
    )
    assert status_code == 200
    assert captured == [("rebalance", "live", "live")]


def test_rebalance_refuses_a_route_the_deployment_is_not_configured_for() -> None:
    """A research deployment never relays a live rebalance, even if asked.

    This is the same gate `routes/trading.py` applies. Without it the two
    governed capital paths would disagree: Trading would refuse the request
    while Portfolio forwarded it.
    """

    def _source(operation: str, *args: object) -> object:
        raise AssertionError("source must not be called for an unconfigured route")

    status_code, body = post_json(
        _lifecycle_app(_source),
        "/api/v1/portfolio/rebalance",
        _rebalance_payload("live", "live"),
        headers={"Idempotency-Key": _key()},
    )
    assert status_code == 503
    assert body["detail"] == "EXECUTION_ROUTE_NOT_CONFIGURED"


def test_rebalance_refuses_live_without_explicit_enablement() -> None:
    """Being configured for live is not the same as being enabled for it.

    `build_api_settings` refuses to construct this combination, so the flag is
    checked independently of the route match rather than being inferred from
    it. Mirrors `tests/api/unit/test_trading_routes.py`, which stubs the same
    otherwise-unconstructible state to cover the same defensive branch.
    """

    def _source(operation: str, *args: object) -> object:
        raise AssertionError("source must not be called with live mutations disabled")

    settings = SimpleNamespace(
        execution_route="live",
        runtime_profile="live",
        allow_live_mutations=False,
    )
    status_code, body = post_json(
        _lifecycle_app(_source, settings=settings),
        "/api/v1/portfolio/rebalance",
        _rebalance_payload("live", "live"),
        headers={"Idempotency-Key": _key()},
    )
    assert status_code == 403
    assert body["detail"] == "LIVE_MUTATIONS_DISABLED"


def test_drift_requires_read_permission_and_delegates() -> None:
    """Drift assessment authorizes first, then delegates the path identity."""
    captured: list[tuple[str, str]] = []

    def _source(operation: str, *args: object) -> object:
        captured.append((operation, str(args[0])))
        return {"status": "success"}

    payload = {
        "scope": {"tenant": "dev"},
        "actual_exposures": {"comp-1": "0.5"},
        "evidence_as_of": "2026-06-02T00:00:00Z",
        "risk_decision": {"decision_id": "dec-1"},
        "eligibility_decisions": {"comp-1": {"decision_id": "elig-1"}},
    }
    status_code, _body = post_json(
        _lifecycle_app(_source), "/api/v1/portfolio/port-1/drift", payload
    )
    assert status_code == 200
    assert captured == [("drift", "port-1")]


def test_recompute_delegates_plan_and_trading_evidence() -> None:
    """Measurement recomputation forwards only owner-issued identifiers."""
    captured: list[tuple[str, str, str]] = []

    def _source(operation: str, *args: object) -> object:
        boundary = args[0]
        captured.append(
            (operation, boundary.plan_id, boundary.trading_request_id)  # type: ignore[attr-defined]
        )
        return {"status": "success"}

    status_code, _body = post_json(
        _lifecycle_app(_source),
        "/api/v1/portfolio/measurement/recompute",
        {"plan_id": "plan-1", "trading_request_id": "treq-1"},
        headers={"Idempotency-Key": _key()},
    )
    assert status_code == 200
    assert captured == [("recompute", "plan-1", "treq-1")]


def test_lifecycle_operations_fail_closed_without_dependencies() -> None:
    """Every governed lifecycle operation fails closed with no composition."""
    source = portfolio_dependencies.build_portfolio_source(None)
    for operation in ("activate", "rollback", "drift", "rebalance", "recompute"):
        with pytest.raises(RuntimeError, match="PORTFOLIO_RUNTIME_UNAVAILABLE"):
            source(operation, object(), _auth(), "key-1")


def test_activation_requires_composed_workflow_handle() -> None:
    """A service handle without its workflow handle cannot activate."""
    source = portfolio_dependencies.build_portfolio_source("service-only")
    with pytest.raises(RuntimeError, match="PORTFOLIO_RUNTIME_UNAVAILABLE"):
        source("activate", object(), _auth(), "key-1")


def test_activation_chain_constructs_reviews_then_activates(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Activation runs construct, coordinate_review, then activate, in order."""
    calls: list[str] = []
    monkeypatch.setattr(
        portfolio_dependencies, "create_portfolio_value", lambda _name, **_v: "request"
    )
    monkeypatch.setattr(
        portfolio_dependencies, "create_simulation_value", lambda _name, **_v: "sim"
    )

    def _handle_operation(_handle: object, operation: str, *args: object, **kw: object):
        calls.append(operation)
        if operation == "construct":
            return ("candidate", "evidence")
        return "review"

    monkeypatch.setattr(
        portfolio_dependencies,
        "execute_portfolio_handle_operation",
        _handle_operation,
    )
    captured: dict[str, object] = {}
    monkeypatch.setattr(
        portfolio_dependencies,
        "activate_portfolio",
        lambda _service, candidate, evidence, review, **kw: (
            captured.update(
                candidate=candidate, evidence=evidence, review=review, kw=kw
            )
            or "allocation"
        ),
    )

    class _Boundary:
        construction: ClassVar[dict[str, object]] = {}
        simulation: ClassVar[dict[str, object]] = {}
        approval_refs = ("appr-1",)
        approval_attestation = None
        approval_validation = None
        expires_at = datetime(2026, 7, 1, tzinfo=UTC)
        expected_predecessor = None
        expected_revision = 0

    source = portfolio_dependencies.build_portfolio_source(
        {"service": "svc", "workflows": "wf"}
    )
    result = source("activate", _Boundary(), _auth(), "key-1")
    assert calls == ["construct", "coordinate_review"]
    assert result == "allocation"
    assert captured["candidate"] == "candidate"
    assert captured["evidence"] == "evidence"
    assert captured["review"] == "review"
    assert captured["kw"]["idempotency_key"] == "key-1"  # type: ignore[index]


def test_rollback_chain_forwards_target_version(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Rollback reaches the owner boundary carrying its prior version."""
    monkeypatch.setattr(
        portfolio_dependencies, "create_portfolio_value", lambda _n, **_v: "request"
    )
    monkeypatch.setattr(
        portfolio_dependencies, "create_simulation_value", lambda _n, **_v: "sim"
    )
    monkeypatch.setattr(
        portfolio_dependencies,
        "execute_portfolio_handle_operation",
        lambda _h, op, *_a, **_k: (
            ("candidate", "evidence") if op == "construct" else "review"
        ),
    )
    captured: dict[str, object] = {}
    monkeypatch.setattr(
        portfolio_dependencies,
        "rollback_portfolio",
        lambda *_a, **kw: captured.update(kw) or "rolled-back",
    )

    class _Boundary:
        construction: ClassVar[dict[str, object]] = {}
        simulation: ClassVar[dict[str, object]] = {}
        rollback_of_version = "v0"
        approval_refs = ()
        approval_attestation = None
        approval_validation = None
        expires_at = datetime(2026, 7, 1, tzinfo=UTC)
        expected_predecessor = "v1"
        expected_revision = 3

    source = portfolio_dependencies.build_portfolio_source(
        {"service": "svc", "workflows": "wf"}
    )
    assert source("rollback", _Boundary(), _auth(), "key-2") == "rolled-back"
    assert captured["rollback_of_version"] == "v0"
    assert captured["expected_revision"] == 3


def test_drift_fails_closed_when_allocation_is_absent(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """No active allocation means no drift judgement is fabricated."""
    monkeypatch.setattr(
        portfolio_dependencies, "get_portfolio_status", lambda *_a: object()
    )

    class _Boundary:
        scope: ClassVar[dict[str, str]] = {"tenant": "dev"}

    source = portfolio_dependencies.build_portfolio_source(
        {"service": "svc", "workflows": "wf"}
    )
    with pytest.raises(RuntimeError, match="PORTFOLIO_ALLOCATION_UNAVAILABLE"):
        source("drift", "port-1", _Boundary(), _auth())


def test_recompute_forwards_only_owner_identifiers(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Measurement recomputation passes exactly the two owner identifiers."""
    captured: dict[str, object] = {}
    monkeypatch.setattr(
        portfolio_dependencies,
        "recompute_portfolio_measurement",
        lambda _service, plan_id, **kw: (
            captured.update(plan_id=plan_id, **kw) or "measurement"
        ),
    )

    class _Boundary:
        plan_id = "plan-1"
        trading_request_id = "treq-1"

    source = portfolio_dependencies.build_portfolio_source(
        {"service": "svc", "workflows": "wf"}
    )
    assert source("recompute", _Boundary(), _auth()) == "measurement"
    assert captured["plan_id"] == "plan-1"
    assert captured["trading_request_id"] == "treq-1"


def test_risk_value_returns_none_without_payload() -> None:
    """An absent governance payload is never replaced by a gateway default."""
    assert portfolio_dependencies._risk_value("approval_attestation", None) is None


def test_resolve_handles_accepts_bundle_and_bare_handle() -> None:
    """Composition accepts both the paired bundle and a legacy bare handle."""
    service, workflows = portfolio_dependencies._resolve_handles(
        {"service": "svc", "workflows": "wf"}
    )
    assert (service, workflows) == ("svc", "wf")
    bare_service, bare_workflows = portfolio_dependencies._resolve_handles("svc")
    assert (bare_service, bare_workflows) == ("svc", None)
