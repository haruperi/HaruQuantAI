"""Agentic bridge composition and route boundary tests.

The conversion and fail-closed behaviour of the Agentic bridge is verified
directly against the source dispatcher (mirroring the Simulation/Trading/
Portfolio owner-dependency composition tests). The HTTP boundary guards
(permission and idempotency enforcement) are verified against the helper
functions and through a minimal FastAPI application's route catalogue.
"""

from __future__ import annotations

from typing import Any

import pytest
from app.services.api.identity import require_auth_context
from app.services.api.workstation.agentic import orchestration as agentic_dependencies
from app.services.api.workstation.agentic import routes as agentic
from app.services.api.workstation.agentic.schemas import (
    AgenticDisableRequest,
    AgenticHandoffApprovalRequest,
    AgenticQuarantineRequest,
    AgenticRunSubmitRequest,
)
from app.utils import create_auth_context, utc_now
from fastapi import FastAPI, HTTPException

from tests.api._support import get_json, post_json

_PERMS = (
    "agentic:submit",
    "agentic:read_run",
    "agentic:cancel_run",
    "agentic:read_audit",
    "agentic:approve_promotion",
    "agentic:operate",
)


def _auth(permissions: tuple[str, ...] = _PERMS) -> Any:
    """Build one authorized Agentic caller.

    Args:
        permissions: Granted backend permissions.

    Returns:
        Utils-owned authenticated context.
    """
    return create_auth_context(
        contract_version="v2",
        schema_id="utils.auth_context.v2",
        principal_id="agentic-operator",
        principal_type="USER",
        roles=("operator",),
        permissions=permissions,
        scopes=("agentic",),
        tenant_or_environment="development",
        runtime_profile="research",
        request_id="req-11111111-1111-4111-8111-111111111111",
        workflow_id="wf-22222222-2222-4222-8222-222222222222",
        correlation_id="cor-33333333-3333-4333-8333-333333333333",
        issued_at=utc_now(),
    )


def _submit_request() -> AgenticRunSubmitRequest:
    """Build one bounded secret-free Agentic run submit request.

    Returns:
        Validated API submit request.
    """
    return AgenticRunSubmitRequest.model_validate(
        {
            "workflow_name": "edge-lab",
            "objective": "Assess momentum on EURUSD.",
            "input_refs": ["ref-eurusd-1"],
            "deadline_seconds": 1800,
            "cost_budget": "1.00",
        }
    )


def test_source_fails_closed_without_dependencies() -> None:
    """A missing Agentic bundle never triggers speculative execution."""
    source = agentic_dependencies.build_agentic_source(None)
    with pytest.raises(RuntimeError, match="AGENTIC_RUNTIME_UNAVAILABLE"):
        source("inspect", _auth(), "run-1", None)
    with pytest.raises(RuntimeError, match="AGENTIC_RUNTIME_UNAVAILABLE"):
        source("submit", _auth(), "edge-lab", "obj", (), "key-1", 1800, None, None)
    with pytest.raises(RuntimeError, match="AGENTIC_RUNTIME_UNAVAILABLE"):
        source("disable", _auth(), (), "drain", None)


def test_source_rejects_unknown_operation() -> None:
    """Only the eight registered operations are dispatchable."""
    source = agentic_dependencies.build_agentic_source(object())
    with pytest.raises(ValueError, match="unsupported Agentic operation"):
        source("activate", _auth(), None)


def test_submit_delegates_exact_arguments(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Submit forwards workflow, objective, refs, key, and budget once."""
    captured: dict[str, object] = {}

    def fake_submit(deps, auth, **kwargs):  # type: ignore[no-untyped-def]
        captured.update(kwargs)
        captured["deps"] = deps
        captured["auth"] = auth
        return object()

    monkeypatch.setattr(agentic_dependencies, "submit_firm_request", fake_submit)
    deps = object()
    source = agentic_dependencies.build_agentic_source(deps)
    auth = _auth()
    source(
        "submit",
        auth,
        "edge-lab",
        "Assess momentum.",
        ("ref-1",),
        "key-1",
        1800,
        "1.00",
        None,
    )
    assert captured["workflow_name"] == "edge-lab"
    assert captured["objective"] == "Assess momentum."
    assert captured["input_refs"] == ("ref-1",)
    assert captured["idempotency_key"] == "key-1"
    assert captured["deadline_seconds"] == 1800
    assert captured["at_time"] is None
    assert captured["deps"] is deps
    assert captured["auth"] is auth


def test_submit_normalizes_list_input_refs(monkeypatch: pytest.MonkeyPatch) -> None:
    """JSON-style evidence lists become tuples for the strict Agentic contract."""
    captured: dict[str, object] = {}

    def fake_submit(deps, auth, **kwargs):  # type: ignore[no-untyped-def]
        captured.update(kwargs)
        return object()

    monkeypatch.setattr(agentic_dependencies, "submit_firm_request", fake_submit)
    source = agentic_dependencies.build_agentic_source(object())
    source(
        "submit",
        _auth(),
        "edge-lab",
        "obj",
        ["ref-1", "ref-2"],
        "key-1",
        1800,
        None,
        None,
    )
    assert captured["input_refs"] == ("ref-1", "ref-2")
    assert captured["cost_budget"] is None


def test_inspect_cancel_audit_delegate_run_id(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Inspect, cancel, and audit delegate the exact run identifier once."""
    inspected: list[str] = []
    cancelled: list[str] = []
    audited: list[tuple[str, str]] = []
    monkeypatch.setattr(
        agentic_dependencies,
        "get_firm_run",
        lambda _deps, _auth, run_id, **_: inspected.append(run_id) or object(),
    )
    monkeypatch.setattr(
        agentic_dependencies,
        "cancel_firm_run",
        lambda _deps, _auth, run_id, **_: (cancelled.append(run_id)) or object(),
    )
    monkeypatch.setattr(
        agentic_dependencies,
        "get_firm_audit",
        lambda _deps, _auth, *, task_id, run_id, **_: (
            audited.append((task_id, run_id)) or object()
        ),
    )
    source = agentic_dependencies.build_agentic_source(object())
    auth = _auth()
    source("inspect", auth, "run-9", None)
    source("cancel", auth, "run-9", "OPERATOR_CANCELLED", None)
    source("audit", auth, "task-1", "run-9", None)
    assert inspected == ["run-9"]
    assert cancelled == ["run-9"]
    assert audited == [("task-1", "run-9")]


def test_approve_quarantine_disable_delegate_exact_fields(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Approve, quarantine, and disable forward their exact operator fields."""
    approve: dict[str, object] = {}
    quarantine: dict[str, object] = {}
    disable: dict[str, object] = {}
    monkeypatch.setattr(
        agentic_dependencies,
        "approve_agentic_handoff",
        lambda _deps, _auth, **kw: approve.update(kw) or object(),
    )
    monkeypatch.setattr(
        agentic_dependencies,
        "quarantine_firm_agent",
        lambda _deps, _auth, **kw: quarantine.update(kw) or object(),
    )
    monkeypatch.setattr(
        agentic_dependencies,
        "disable_agentic",
        lambda _deps, _auth, **kw: disable.update(kw) or object(),
    )
    source = agentic_dependencies.build_agentic_source(object())
    auth = _auth()
    source(
        "approve",
        auth,
        "a" * 64,
        "artifact-1",
        "Promoted after review.",
        None,
    )
    source(
        "quarantine",
        auth,
        "run-1",
        "drift",
        "Observed behaviour drift.",
        "role-quant",
        ("ev-1",),
        "checkpoint-1",
        None,
    )
    source("disable", auth, ("run-1", "run-2"), "cancel", None)
    assert approve == {
        "artifact_hash": "a" * 64,
        "artifact_id": "artifact-1",
        "rationale": "Promoted after review.",
        "at_time": None,
    }
    assert quarantine["kind"] == "drift"
    assert quarantine["role_id"] == "role-quant"
    assert quarantine["preserved_evidence_refs"] == ("ev-1",)
    assert disable["run_ids"] == ("run-1", "run-2")
    assert disable["policy"] == "cancel"


def test_require_idempotency_rejects_blank_and_oversized() -> None:
    """The idempotency helper rejects missing, blank, and oversized keys."""
    with pytest.raises(HTTPException) as blank:
        agentic._require_idempotency(None)
    assert blank.value.status_code == 422
    assert blank.value.detail == "IDEMPOTENCY_KEY_REQUIRED"
    with pytest.raises(HTTPException) as whitespace:
        agentic._require_idempotency("   ")
    assert whitespace.value.status_code == 422
    with pytest.raises(HTTPException) as oversized:
        agentic._require_idempotency("x" * (agentic._MAX_IDEMPOTENCY_KEY_LENGTH + 1))
    assert oversized.value.status_code == 422
    assert agentic._require_idempotency("key-1") == "key-1"


def _app_with_source(source: Any) -> FastAPI:
    """Build one minimal FastAPI app with the Agentic router and source.

    Args:
        source: Agentic dispatcher callable.

    Returns:
        FastAPI application bound to the test auth and source.
    """
    app = FastAPI()
    app.include_router(agentic.router)
    app.dependency_overrides[require_auth_context] = _auth
    app.dependency_overrides[agentic._agentic_source] = lambda: source
    return app


def test_submit_route_requires_permission() -> None:
    """A caller without the submit permission is rejected before delegation."""
    captured: list[str] = []

    def _source(operation: str, *args: object) -> object:
        captured.append(operation)
        return {"status": "ok"}

    app = _app_with_source(_source)
    app.dependency_overrides[require_auth_context] = lambda: _auth(
        permissions=("agentic:read_run",)
    )
    status_code, _body = post_json(
        app,
        "/api/v1/agentic/runs",
        {
            "workflow_name": "edge-lab",
            "objective": "obj",
            "input_refs": ["ref-1"],
        },
    )
    assert status_code == 403
    assert captured == []


def test_submit_route_requires_idempotency_key() -> None:
    """Submit without an idempotency key is rejected before delegation."""
    captured: list[str] = []

    def _source(operation: str, *args: object) -> object:
        captured.append(operation)
        return {"status": "ok"}

    app = _app_with_source(_source)
    status_code, _body = post_json(
        app,
        "/api/v1/agentic/runs",
        {"workflow_name": "edge-lab", "objective": "obj"},
    )
    assert status_code == 422
    assert captured == []


def test_inspect_route_delegates_run_id() -> None:
    """An authorized inspect read delegates the run identifier once."""
    captured: list[str] = []

    def _source(operation: str, *args: object) -> object:
        captured.append(str(args[1]))
        return {"status": "ok"}

    app = _app_with_source(_source)
    status_code, _body = get_json(app, "/api/v1/agentic/runs/run-9")
    assert status_code == 200
    assert captured == ["run-9"]


def test_route_fails_closed_with_503() -> None:
    """A missing Agentic bundle yields HTTP 503 rather than a crash."""

    def _source(operation: str, *args: object) -> object:
        raise RuntimeError("AGENTIC_RUNTIME_UNAVAILABLE")

    app = _app_with_source(_source)
    status_code, _body = get_json(app, "/api/v1/agentic/runs/run-9")
    assert status_code == 503


def test_dto_validators_reject_invalid_payloads() -> None:
    """Boundary DTOs reject blank, oversized, and malformed fields."""
    with pytest.raises(ValueError, match="non-empty trimmed text"):
        AgenticRunSubmitRequest.model_validate(
            {"workflow_name": " edge-lab ", "objective": "obj"}
        )
    with pytest.raises(ValueError, match="2000 characters"):
        AgenticRunSubmitRequest.model_validate(
            {"workflow_name": "edge-lab", "objective": "x" * 2001}
        )
    with pytest.raises(ValueError, match="lowercase hex characters"):
        AgenticHandoffApprovalRequest.model_validate(
            {"artifact_hash": "tooshort", "artifact_id": "a-1", "rationale": "ok"}
        )
    with pytest.raises(ValueError, match="at least one reference"):
        AgenticQuarantineRequest.model_validate(
            {
                "run_id": "run-1",
                "kind": "drift",
                "trigger": "t",
                "role_id": "role-1",
                "preserved_evidence_refs": [],
                "checkpoint_ref": "cp-1",
            }
        )
    # Valid payloads round-trip.
    assert AgenticDisableRequest.model_validate({"run_ids": []}).policy == "drain"
