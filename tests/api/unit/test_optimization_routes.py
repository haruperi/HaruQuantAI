"""Optimization bridge composition and route boundary tests.

The conversion and fail-closed behaviour of the Optimization bridge is
verified directly against the source dispatcher (mirroring the
Simulation/Portfolio/Trading owner-dependency composition tests). The HTTP
boundary guards (permission and idempotency enforcement) are verified against
the helper functions and through the canonical application's route catalogue.
"""

from __future__ import annotations

from typing import Any

import pytest
from app.contracts.common.models import create_auth_context
from app.kernel.time import utc_now
from app.services.api.identity import require_auth_context
from app.services.api.widgets.optimization import (
    orchestration as optimization_dependencies,
)
from app.services.api.widgets.optimization import routes as optimization
from fastapi import FastAPI, HTTPException

from tests.api._support import get_json


def _auth(
    permissions: tuple[str, ...] = ("optimization:read", "optimization:run"),
) -> Any:
    """Build one authorized Optimization caller.

    Args:
        permissions: Granted backend permissions.

    Returns:
        Utils-owned authenticated context.
    """
    return create_auth_context(
        contract_version="v2",
        schema_id="utils.auth_context.v2",
        principal_id="optimization-operator",
        principal_type="USER",
        roles=("operator",),
        permissions=permissions,
        scopes=("optimization",),
        tenant_or_environment="development",
        runtime_profile="research",
        request_id="req-11111111-1111-4111-8111-111111111111",
        workflow_id="wf-22222222-2222-4222-8222-222222222222",
        correlation_id="cor-33333333-3333-4333-8333-333333333333",
        issued_at=utc_now(),
    )


def test_source_fails_closed_without_dependencies() -> None:
    """A missing Optimization bundle never triggers speculative execution."""
    source = optimization_dependencies.build_optimization_source(None)
    with pytest.raises(RuntimeError, match="OPTIMIZATION_RUNTIME_UNAVAILABLE"):
        source("parameter-sweep", {"k": 1})
    with pytest.raises(RuntimeError, match="OPTIMIZATION_RUNTIME_UNAVAILABLE"):
        source("compare", ())
    with pytest.raises(RuntimeError, match="OPTIMIZATION_RUNTIME_UNAVAILABLE"):
        source("read", "search-1", "a" * 64)


def test_source_rejects_unknown_operation() -> None:
    """Only the registered Optimization operations are dispatchable."""
    source = optimization_dependencies.build_optimization_source(
        {"adapter": object(), "auth_context": _auth(), "state_store": object()}
    )
    with pytest.raises(ValueError, match="unsupported Optimization operation"):
        source("forecast")


def test_parameter_sweep_converts_payload_and_delegates(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The bridge reconstructs the strict owner request and delegates once."""
    converted = object()
    captured: dict[str, object] = {}

    def fake_value(name: str, /, **fields: object) -> object:
        captured["name"] = name
        captured["fields"] = fields
        return converted

    monkeypatch.setattr(
        optimization_dependencies, "create_optimization_value", fake_value
    )
    delegated: list[object] = []

    def fake_run(request: object, adapter: object) -> object:
        delegated.append((request, adapter))
        return {"status": "success"}

    monkeypatch.setattr(optimization_dependencies, "run_parameter_sweep", fake_run)
    bundle = {"adapter": "the-adapter", "auth_context": _auth(), "state_store": None}
    source = optimization_dependencies.build_optimization_source(bundle)

    class _Payload:
        def model_dump(self, **_: object) -> dict[str, object]:
            """Return one bounded payload for the bridge."""
            return {"request_id": "req-1", "symbol": "EURUSD"}

    result = source("parameter-sweep", _Payload())
    assert result == {"status": "success"}
    assert captured["name"] == "SearchRequest"
    assert captured["fields"] == {"request_id": "req-1", "symbol": "EURUSD"}
    assert delegated == [(converted, "the-adapter")]


def test_robustness_selects_stress_variant_when_stress_present(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The presence of the ``stress`` field selects the stress request variant."""
    built: list[str] = []

    def fake_value(name: str, /, **_fields: object) -> object:
        built.append(name)
        return object()

    monkeypatch.setattr(
        optimization_dependencies, "create_optimization_value", fake_value
    )
    monkeypatch.setattr(
        optimization_dependencies,
        "run_robustness_analysis",
        lambda *_a, **_k: {"status": "success"},
    )
    bundle = {"adapter": object(), "auth_context": _auth(), "state_store": None}
    source = optimization_dependencies.build_optimization_source(bundle)
    source(
        "robustness",
        {"outcomes": [1], "stress": {"kind": "commission", "value": "0.1"}},
        100,
    )
    assert built == ["ExecutionStressAnalysisRequest"]

    built.clear()
    source("robustness", {"outcomes": [1], "method": "shuffle_trades"}, 100)
    assert built == ["MonteCarloRequest"]


def test_read_route_fails_closed_without_state_store(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A composed bundle without a state store fails the read route closed."""
    bundle = {"adapter": object(), "auth_context": _auth(), "state_store": None}
    source = optimization_dependencies.build_optimization_source(bundle)
    with pytest.raises(RuntimeError, match="OPTIMIZATION_RESULTS_UNAVAILABLE"):
        source("read", "search-1", "a" * 64)


def test_read_route_delegates_to_store(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The read route delegates the exact identity to the public read function."""
    captured: dict[str, object] = {}

    def fake_load(
        *, search_id: str, reproducibility_hash: str, store: object
    ) -> object:
        captured["search_id"] = search_id
        captured["reproducibility_hash"] = reproducibility_hash
        captured["store"] = store
        return {"status": "success", "search_id": search_id}

    monkeypatch.setattr(
        optimization_dependencies, "load_optimization_result", fake_load
    )
    store = object()
    bundle = {"adapter": object(), "auth_context": _auth(), "state_store": store}
    source = optimization_dependencies.build_optimization_source(bundle)
    result = source("read", "search-1", "b" * 64)
    assert result == {"status": "success", "search_id": "search-1"}
    assert captured == {
        "search_id": "search-1",
        "reproducibility_hash": "b" * 64,
        "store": store,
    }


def test_read_operation_returns_none_propagates(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A missing result resolves to ``None`` so the route can map it to 404."""
    monkeypatch.setattr(
        optimization_dependencies,
        "load_optimization_result",
        lambda **_k: None,
    )
    bundle = {"adapter": object(), "auth_context": _auth(), "state_store": object()}
    source = optimization_dependencies.build_optimization_source(bundle)
    assert source("read", "search-1", "c" * 64) is None


def test_require_idempotency_rejects_blank_and_oversized() -> None:
    """The idempotency helper rejects missing, blank, and oversized keys."""
    with pytest.raises(HTTPException) as blank:
        optimization._require_idempotency(None)
    assert blank.value.status_code == 422
    assert blank.value.detail == "IDEMPOTENCY_KEY_REQUIRED"
    with pytest.raises(HTTPException) as whitespace:
        optimization._require_idempotency("   ")
    assert whitespace.value.status_code == 422
    with pytest.raises(HTTPException) as oversized:
        optimization._require_idempotency(
            "x" * (optimization._MAX_IDEMPOTENCY_KEY_LENGTH + 1)
        )
    assert oversized.value.status_code == 422
    assert optimization._require_idempotency("key-1") == "key-1"


def _app_with_source(source_value: object) -> FastAPI:
    """Build a minimal app exposing the Optimization router.

    Args:
        source_value: Source dispatcher or value to inject.

    Returns:
        FastAPI application with the Optimization router and overridden deps.
    """
    app = FastAPI()
    app.include_router(optimization.router)
    app.dependency_overrides[require_auth_context] = _auth
    app.dependency_overrides[optimization._optimization_source] = lambda: source_value
    return app


def test_read_operations_delegate_through_source(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Each read operation delegates its transformed inputs exactly once.

    The POST read operations reconstruct no owner value; the bridge forwards
    the validated inputs straight to the matching Optimization function. This
    mirrors how the Simulation/Portfolio bridges verify one-delegation at the
    source dispatcher level rather than through HTTP body parsing.
    """
    calls: dict[str, tuple[object, ...]] = {}
    kwargs: dict[str, dict[str, object]] = {}

    def _record(name: str) -> object:
        def _impl(*args: object, **kw: object) -> object:
            calls[name] = args
            kwargs[name] = kw
            return {"status": "success", "operation": name}

        return _impl

    monkeypatch.setattr(
        optimization_dependencies, "compare_optimization_runs", _record("compare")
    )
    monkeypatch.setattr(
        optimization_dependencies,
        "calculate_parameter_stability",
        _record("stability"),
    )
    monkeypatch.setattr(
        optimization_dependencies,
        "detect_overfit_parameters",
        _record("overfit"),
    )
    monkeypatch.setattr(
        optimization_dependencies, "rank_parameter_sets", _record("rank")
    )
    monkeypatch.setattr(
        optimization_dependencies,
        "calculate_robustness_score",
        _record("robustness-score"),
    )
    bundle = {"adapter": object(), "auth_context": _auth(), "state_store": None}
    source = optimization_dependencies.build_optimization_source(bundle)

    source("compare", ({"search_id": "search-1"},))
    assert calls["compare"] == (({"search_id": "search-1"},),)

    source("stability", ({"executable_parameters": {"p": 1}},))
    assert calls["stability"] == (({"executable_parameters": {"p": 1}},),)

    source("overfit", {"a": 1.0}, {"a": 0.5}, 0.2)
    assert calls["overfit"] == ({"a": 1.0}, {"a": 0.5})
    assert kwargs["overfit"] == {"threshold": 0.2}

    source("rank", ({"candidate_hash": "h"},))
    assert calls["rank"] == (({"candidate_hash": "h"},),)

    source("robustness-score", (True, False, True))
    assert calls["robustness-score"] == ((True, False, True),)


def test_handoff_reconstructs_evidence_request(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The handoff operation rebuilds the strict owner request before delegating."""
    converted = object()
    captured: dict[str, object] = {}

    def fake_value(name: str, /, **fields: object) -> object:
        captured["name"] = name
        captured["fields"] = fields
        return converted

    monkeypatch.setattr(
        optimization_dependencies, "create_optimization_value", fake_value
    )
    delegated: list[object] = []

    def fake_build(request: object) -> object:
        delegated.append(request)
        return {"status": "success"}

    monkeypatch.setattr(
        optimization_dependencies, "build_optimization_handoff", fake_build
    )
    bundle = {"adapter": object(), "auth_context": _auth(), "state_store": None}
    source = optimization_dependencies.build_optimization_source(bundle)

    class _Payload:
        def model_dump(self, **_: object) -> dict[str, object]:
            """Return one bounded handoff payload for the bridge."""
            return {"search_id": "search-1"}

    source("handoff", _Payload())
    assert captured["name"] == "EvidenceAssemblyRequest"
    assert captured["fields"] == {"search_id": "search-1"}
    assert delegated == [converted]


def test_result_read_route_delegates_identity() -> None:
    """The result read delegates the path id and reproducibility hash."""
    captured: list[object] = []

    def _source(operation: str, *args: object) -> object:
        captured.append((operation, args))
        return {"status": "success", "search_id": args[0]}

    app = _app_with_source(_source)
    status_code, _body = get_json(
        app,
        "/api/v1/optimization/results/search-1",
        query_string="reproducibility_hash=" + "a" * 64,
    )
    assert status_code == 200
    assert captured == [("read", ("search-1", "a" * 64))]


def test_result_read_route_requires_read_permission() -> None:
    """A caller without read permission is rejected before delegation."""

    def _source(operation: str, *args: object) -> object:
        raise AssertionError("source must not be called without permission")

    app = FastAPI()
    app.include_router(optimization.router)
    app.dependency_overrides[require_auth_context] = lambda: _auth(
        permissions=("optimization:run",)
    )
    app.dependency_overrides[optimization._optimization_source] = lambda: _source
    status_code, _body = get_json(
        app,
        "/api/v1/optimization/results/search-1",
        query_string="reproducibility_hash=" + "a" * 64,
    )
    assert status_code == 403


def test_result_read_route_returns_404_when_absent() -> None:
    """A missing persisted result maps to a deterministic 404."""

    def _source(operation: str, *args: object) -> object:
        return None

    app = _app_with_source(_source)
    status_code, _body = get_json(
        app,
        "/api/v1/optimization/results/search-1",
        query_string="reproducibility_hash=" + "a" * 64,
    )
    assert status_code == 404
