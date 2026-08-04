"""Fail-closed branch evidence for Risk relational persistence adapters."""

import json
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from typing import Any, cast

import pytest
from app.services.risk import create_risk_approval_token
from app.services.risk.approvals import runtime as approval_runtime
from app.services.risk.audit import runtime as audit_runtime
from app.services.risk.persistence import create, read, update

_NOW = datetime(2026, 8, 3, tzinfo=UTC)


def _result(affected_rows: int, rows: tuple[dict[str, object], ...] = ()) -> object:
    """Build one minimal Data transaction result."""
    return SimpleNamespace(affected_rows=affected_rows, rows=rows)


def _store(*, decoded: object | None = None) -> object:
    """Build a codec-backed private persistence handle."""
    return create.create_risk_runtime_store(
        {
            kind: (
                lambda value: json.dumps(value, default=str),
                lambda value, restored=decoded: (
                    json.loads(value) if restored is None else restored
                ),
            )
            for kind in (
                "allocation",
                "approval-state",
                "audit",
                "decision",
                "eligibility",
                "kill-switch",
            )
        }
    )


def _token(*, expires_at: datetime | None = None) -> object:
    """Build one valid approval token."""
    return create_risk_approval_token(
        token_id="token-one",
        decision_id="decision-one",
        config_hash="a" * 64,
        action="trade",
        scope={"account_id": "account-one"},
        approver_id="risk-governor",
        issued_at=_NOW,
        expires_at=expires_at or _NOW + timedelta(minutes=5),
        nonce="nonce-one",
        signature="signature-one",
        request_id="req-11111111-1111-4111-8111-111111111111",
        workflow_id="wf-22222222-2222-4222-8222-222222222222",
        correlation_id="cor-33333333-3333-4333-8333-333333333333",
    )


def _model(**overrides: object) -> object:
    """Build a field-bearing persistence value."""
    values: dict[str, object] = {
        "active": True,
        "config_hash": "a" * 64,
        "correlation_id": "cor-33333333-3333-4333-8333-333333333333",
        "decision_id": "decision-one",
        "event_type": "risk.test",
        "evidence_refs": {"market": "market-one"},
        "expires_at": _NOW + timedelta(minutes=5),
        "issued_at": _NOW,
        "occurred_at": _NOW,
        "portfolio_id": "portfolio-one",
        "predecessor_version": None,
        "previous_hash": "0" * 64,
        "record_hash": "b" * 64,
        "request_id": "req-11111111-1111-4111-8111-111111111111",
        "reviewed_version": "v1",
        "scope": {},
        "scope_level": "global",
        "sequence": 0,
        "state": "active",
        "strategy_id": "strategy-one",
        "strategy_version": "v1",
        "updated_at": _NOW,
        "version": 1,
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def test_store_codecs_and_field_guards_fail_closed() -> None:
    """Reject unknown codecs, handles, and malformed model fields."""
    store = _store()
    private = cast("Any", store)
    assert private.decode("audit", private.encode("audit", {"ok": True})) == {
        "ok": True
    }
    with pytest.raises(ValueError, match="unsupported"):
        private.encode("unknown", object())
    with pytest.raises(ValueError, match="unsupported"):
        private.decode("unknown", "{}")
    with pytest.raises(TypeError, match="invalid Risk persistence store"):
        create._require_store(object())
    with pytest.raises(TypeError, match="lacks missing"):
        create._field(object(), "missing")
    with pytest.raises(TypeError, match="must be text"):
        create._text_field(SimpleNamespace(value=""), "value")
    with pytest.raises(TypeError, match="must be datetime"):
        create._time_field(SimpleNamespace(value="now"), "value")
    with pytest.raises(TypeError, match="must be a mapping"):
        create._mapping_field(SimpleNamespace(value=()), "value")


def test_execute_and_approval_payload_guards(monkeypatch: pytest.MonkeyPatch) -> None:
    """Reject failed Data responses and malformed approval payloads."""
    monkeypatch.setattr(
        create,
        "execute_transaction",
        lambda _request: SimpleNamespace(status="error", data=None),
    )
    with pytest.raises(ValueError, match="transaction failed"):
        create._execute(("SELECT 1",), ((),))
    for value in (object(), {}, {"approval_json": "[]"}):
        with pytest.raises(TypeError):
            create._approval_token(value)


def test_create_operations_report_conflicts(monkeypatch: pytest.MonkeyPatch) -> None:
    """Map zero-row relational writes to deterministic conflicts."""
    monkeypatch.setattr(create, "_execute", lambda *_args, **_kwargs: _result(0))
    store = _store()
    token = cast("Any", _token())
    state = approval_runtime._state(token)
    state["approval_json"] = token.model_dump_json()
    assert not create.create_approval_state_record(
        store,
        state_key=token.token_id,
        state_value=state,
        index_key=token.token_id,
        index_sequence=1,
        index_value={"approval_id": token.token_id},
    )
    with pytest.raises(ValueError, match="identity is inconsistent"):
        create.create_approval_state_record(
            store,
            state_key="wrong",
            state_value=state,
            index_key="wrong",
            index_sequence=0,
            index_value={},
        )
    bad_scope = dict(state)
    bad_scope["approval_json"] = json.dumps(
        {**json.loads(token.model_dump_json()), "scope": []}
    )
    with pytest.raises(TypeError, match="scope"):
        create.create_approval_state_record(
            store,
            state_key=token.token_id,
            state_value=bad_scope,
            index_key=token.token_id,
            index_sequence=1,
            index_value={},
        )
    model = _model()
    with pytest.raises(ValueError, match="sequence"):
        create.create_audit_record(
            store, record_id="audit-one", sequence=2, value=model
        )
    for operation, message in (
        (
            lambda: create.create_audit_record(
                store, record_id="audit-one", sequence=1, value=model
            ),
            "not appended",
        ),
        (
            lambda: create.create_decision_record(
                store, decision_id="decision-one", value=model
            ),
            "identity conflict",
        ),
        (
            lambda: create.create_eligibility_record(store, "eligibility-one", model),
            "identity conflict",
        ),
        (
            lambda: create.create_allocation_review_record(
                store, "allocation-one", model
            ),
            "identity conflict",
        ),
        (
            lambda: create.create_active_allocation_record(
                store, "portfolio-one", model
            ),
            "could not be created",
        ),
    ):
        with pytest.raises(ValueError, match=message):
            operation()


def test_read_operations_cover_empty_and_malformed_rows(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Return absence consistently and reject malformed approval state."""
    store = _store()
    monkeypatch.setattr(read, "_execute", lambda *_args, **_kwargs: _result(0))
    assert read.read_approval_state_record(store, "missing") is None
    assert read.read_approval_state_record_with_revision(store, "missing") is None
    assert read.read_audit_record(store, "missing") is None
    assert read.read_decision_record(store, "missing") is None
    assert read.read_active_allocation_record(store, "missing") is None
    assert read.read_active_allocation_record_with_revision(store, "missing") is None
    assert read.read_kill_switch_record(store, "missing") is None
    assert read.read_approval_index_records(store) == ()
    assert read.read_audit_records(store) == ()
    with pytest.raises(ValueError, match="positive"):
        read.read_decision_records(store, 0)
    monkeypatch.setattr(
        read,
        "_execute",
        lambda *_args, **_kwargs: _result(
            0, ({"payload_json": "[]", "updated_at": "v1"},)
        ),
    )
    with pytest.raises(TypeError, match="malformed"):
        read.read_approval_state_record_with_revision(_store(decoded=[]), "token")


def test_update_guards_and_conflicts(monkeypatch: pytest.MonkeyPatch) -> None:
    """Exercise approval, allocation, and compound-transition guards."""
    issued = _token()
    approval_json = cast("Any", issued).model_dump_json()
    for value in (
        object(),
        {},
        {"approval_json": "[]"},
        {"approval_json": approval_json, "reservation_id": 1},
        {"approval_json": approval_json, "revoked_at": 1},
        {"approval_json": approval_json, "consumed": True},
    ):
        with pytest.raises(TypeError):
            update._approval_update(value)
    revoked = {"approval_json": approval_json, "revoked_at": _NOW.isoformat()}
    consumed = {
        "approval_json": approval_json,
        "consumed": True,
        "consumed_at": _NOW.isoformat(),
        "reservation_id": "reservation-one",
    }
    assert update._approval_update(revoked)[0] == "revoked"
    assert update._approval_update(consumed)[0] == "consumed"
    assert update._approval_update({"approval_json": approval_json})[0] == "issued"
    monkeypatch.setattr(update, "_execute", lambda *_args, **_kwargs: _result(0))
    with pytest.raises(ValueError, match="revision conflict"):
        update.update_approval_state_record(
            _store(), key="token-one", value=consumed, expected_revision="old"
        )
    monkeypatch.setattr(update, "_execute", lambda *_args, **_kwargs: _result(3))
    with pytest.raises(ValueError, match="allocation revision"):
        update.update_active_allocation_record(
            _store(),
            key="portfolio-one",
            value=_model(),
            expected_revision="decision-old",
        )
    with pytest.raises(TypeError, match="sequence is malformed"):
        update.update_kill_switch_with_audit(
            _store(),
            state_key="state-one",
            state_value=_model(version="1"),
            expected_revision=0,
            audit_key="audit-one",
            audit_sequence=1,
            audit_value=_model(),
        )
    with pytest.raises(ValueError, match="sequence is inconsistent"):
        update.update_kill_switch_with_audit(
            _store(),
            state_key="state-one",
            state_value=_model(),
            expected_revision=0,
            audit_key="audit-one",
            audit_sequence=2,
            audit_value=_model(),
        )
    monkeypatch.setattr(update, "_execute", lambda *_args, **_kwargs: _result(1))
    assert not update.update_kill_switch_with_audit(
        _store(),
        state_key="state-one",
        state_value=_model(),
        expected_revision=0,
        audit_key="audit-one",
        audit_sequence=1,
        audit_value=_model(),
    )


def test_approval_runtime_classifies_and_guards_lifecycle(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Classify every approval consumption state and guarded update failure."""
    token = cast("Any", _token())
    state = approval_runtime._state(token)
    monkeypatch.setattr(
        approval_runtime, "create_risk_runtime_store", lambda _codecs: {}
    )
    adapter = cast("Any", approval_runtime.build_risk_approval_state_store())
    with pytest.raises(TypeError, match="must be a mapping"):
        approval_runtime._encode(object())
    with pytest.raises(TypeError, match="malformed"):
        approval_runtime._approval({})
    monkeypatch.setattr(
        approval_runtime, "read_approval_state_record", lambda _store, _key: state
    )
    assert adapter.save_issued(token, timeout_seconds=None) == "already_saved"
    monkeypatch.setattr(
        approval_runtime, "read_approval_state_record", lambda _store, _key: {}
    )
    assert adapter.save_issued(token, timeout_seconds=None) == "conflict"
    monkeypatch.setattr(
        approval_runtime, "read_approval_state_record", lambda _store, _key: None
    )
    monkeypatch.setattr(
        approval_runtime, "read_approval_index_records", lambda _store: ()
    )
    monkeypatch.setattr(
        approval_runtime,
        "create_approval_state_record",
        lambda *_args, **_kwargs: False,
    )
    assert adapter.save_issued(token, timeout_seconds=None) == "conflict"

    def consume(stored: object) -> str:
        monkeypatch.setattr(
            approval_runtime,
            "read_approval_state_record_with_revision",
            lambda _store, _key: stored,
        )
        return adapter.consume_if_active(
            token.token_id,
            expected_signature=token.signature,
            reservation_id="reservation-one",
            workflow_id=token.workflow_id,
            action=token.action,
            scope=token.scope,
            now=_NOW + timedelta(seconds=1),
            timeout_seconds=None,
        )

    assert consume(None) == "missing"
    assert consume(({**state, "revoked_at": _NOW.isoformat()}, "v1")) == "revoked"
    assert consume(({**state, "consumed": True}, "v1")) == "already_consumed"
    expired = cast("Any", _token(expires_at=_NOW + timedelta(milliseconds=1)))
    assert consume((approval_runtime._state(expired), "v1")) == "expired"
    monkeypatch.setattr(
        approval_runtime,
        "read_approval_state_record_with_revision",
        lambda _store, _key: (state, "v1"),
    )
    assert (
        adapter.consume_if_active(
            token.token_id,
            expected_signature="wrong",
            reservation_id="reservation-one",
            workflow_id=token.workflow_id,
            action=token.action,
            scope=token.scope,
            now=_NOW + timedelta(seconds=1),
            timeout_seconds=None,
        )
        == "conflict"
    )
    monkeypatch.setattr(
        approval_runtime,
        "update_approval_state_record",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(ValueError("stale")),
    )
    assert consume((state, "v1")) == "conflict"


def test_approval_revocation_skips_ineligible_and_stale_rows(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Revoke only active intersecting approvals under the CAS guard."""
    token = cast("Any", _token())
    state = approval_runtime._state(token)
    monkeypatch.setattr(
        approval_runtime, "create_risk_runtime_store", lambda _codecs: {}
    )
    adapter = cast("Any", approval_runtime.build_risk_approval_state_store())
    monkeypatch.setattr(
        approval_runtime,
        "read_approval_index_records",
        lambda _store: ({"approval_id": 1}, {"approval_id": token.token_id}),
    )
    monkeypatch.setattr(
        approval_runtime,
        "read_approval_state_record_with_revision",
        lambda _store, _key: (state, "v1"),
    )
    monkeypatch.setattr(
        approval_runtime,
        "update_approval_state_record",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(ValueError("stale")),
    )
    assert (
        adapter.revoke_intersecting(
            token.scope,
            reason="operator",
            revoked_at=_NOW,
            timeout_seconds=None,
        )
        == 0
    )
    monkeypatch.setattr(
        approval_runtime,
        "read_approval_state_record_with_revision",
        lambda _store, _key: None,
    )
    assert not adapter._revoke_one(token.token_id, token.scope, "operator", _NOW)
    monkeypatch.setattr(
        approval_runtime,
        "read_approval_state_record_with_revision",
        lambda _store, _key: ({**state, "consumed": True}, "v1"),
    )
    assert not adapter._revoke_one(token.token_id, token.scope, "operator", _NOW)


def test_audit_runtime_rejects_invalid_handles_and_values() -> None:
    """Protect the function-only audit state boundary."""
    with pytest.raises(TypeError, match="validated model"):
        audit_runtime._encode(object())
    with pytest.raises(TypeError, match="invalid Risk state-store"):
        audit_runtime.execute_risk_state_store_operation(object(), "read_all")
    store = audit_runtime.build_risk_state_store()
    with pytest.raises(ValueError, match="unsupported"):
        audit_runtime.execute_risk_state_store_operation(store, "unknown")
