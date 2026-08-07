"""Fail-closed branch evidence for Portfolio relational persistence."""

import json
from datetime import UTC, datetime
from decimal import Decimal
from types import SimpleNamespace
from typing import Any, cast

import pytest
from app.services.portfolio import create_portfolio_value
from app.services.portfolio.persistence import create, read, update
from app.services.portfolio.state import runtime

_NOW = datetime(2026, 8, 4, tzinfo=UTC)


def _result(affected_rows: int, rows: tuple[dict[str, object], ...] = ()) -> object:
    """Build one minimal transaction result."""
    return SimpleNamespace(affected_rows=affected_rows, rows=rows)


def _store(*, decoded: object | None = None) -> object:
    """Build a codec-backed private persistence handle."""
    return create.create_portfolio_runtime_store(
        {
            kind: (
                lambda value: json.dumps(value, default=str),
                lambda value, restored=decoded: (
                    json.loads(value) if restored is None else restored
                ),
            )
            for kind in ("allocation", "construction", "outbox", "plan")
        }
    )


def _model(**overrides: object) -> object:
    """Build a field-bearing persistence value."""
    values: dict[str, object] = {
        "activated_at": _NOW,
        "allocation_id": "allocation-one",
        "allocation_version": "v1",
        "canonical_hash": "a" * 64,
        "correlation_id": "cor-33333333-3333-4333-8333-333333333333",
        "created_at": _NOW,
        "idempotency_key": "idempotency-one",
        "plan_id": "plan-one",
        "plan_version": "v1",
        "portfolio_id": "portfolio-one",
        "portfolio_version": "v1",
        "request_id": "req-11111111-1111-4111-8111-111111111111",
        "result_id": "result-one",
        "scope": {"environment": "simulation"},
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def test_store_and_field_guards_fail_closed() -> None:
    """Reject unknown codecs, handles, and malformed model fields."""
    store = cast("Any", _store())
    assert store.decode("outbox", store.encode("outbox", {"ok": True})) == {"ok": True}
    with pytest.raises(ValueError, match="unsupported"):
        store.encode("unknown", object())
    with pytest.raises(ValueError, match="unsupported"):
        store.decode("unknown", "{}")
    with pytest.raises(TypeError, match="invalid Portfolio persistence store"):
        create._require_store(object())
    with pytest.raises(TypeError, match="lacks missing"):
        create._field(object(), "missing")
    with pytest.raises(TypeError, match="must be text"):
        create._text_field(SimpleNamespace(value=""), "value")
    with pytest.raises(TypeError, match="must be datetime"):
        create._time_field(SimpleNamespace(value="now"), "value")
    with pytest.raises(TypeError, match="must be a mapping"):
        create._mapping_field(SimpleNamespace(value=()), "value")


def test_transaction_and_outbox_guards(monkeypatch: pytest.MonkeyPatch) -> None:
    """Reject failed Data responses and incomplete audit evidence."""
    monkeypatch.setattr(
        create,
        "execute_transaction",
        lambda _request: SimpleNamespace(status="error", data=None),
    )
    with pytest.raises(ValueError, match="transaction failed"):
        create._execute(("SELECT 1",), ((),))
    for value in (object(), {"audit": []}, {"audit": {}}):
        with pytest.raises(TypeError):
            create._outbox_event_type(value)
    assert create._outbox_event_type({"audit": {"action": "portfolio.saved"}}) == (
        "portfolio.saved"
    )
    assert create._outbox_event_type({"event_type": "portfolio.saved"}) == (
        "portfolio.saved"
    )


def test_create_and_update_validate_transition_evidence(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Reject inconsistent keys, sequences, and revisions before writing."""
    store = _store()
    with pytest.raises(ValueError, match="construction persistence identity"):
        create.create_construction_record(
            store,
            state_key="wrong",
            state_value=_model(),
            event_key="event-one",
            event_sequence=0,
            event_value={"event": "portfolio.constructed"},
        )
    with pytest.raises(ValueError, match="sequence must be positive"):
        create.create_plan_record(
            store,
            state_value=_model(),
            event_key="event-one",
            event_sequence=0,
            event_value={"event": "portfolio.planned"},
        )
    with pytest.raises(ValueError, match="transition evidence is invalid"):
        update.update_active_allocation_record(
            store,
            state_value=_model(),
            expected_revision=-1,
            event_key="event-one",
            event_sequence=0,
            event_value={"event": "portfolio.activated"},
        )
    monkeypatch.setattr(update, "_execute", lambda *_args, **_kwargs: _result(3))
    assert not update.update_active_allocation_record(
        store,
        state_value=_model(),
        expected_revision=0,
        event_key="event-one",
        event_sequence=1,
        event_value={"event": "portfolio.activated"},
    )


def test_read_and_runtime_guards(monkeypatch: pytest.MonkeyPatch) -> None:
    """Reject malformed stored revisions and invalid opaque operations."""
    monkeypatch.setattr(
        read,
        "_execute",
        lambda *_args, **_kwargs: _result(
            0,
            ({"allocation_json": "{}", "revision": "bad"},),
        ),
    )
    with pytest.raises(TypeError, match="revision is malformed"):
        read.read_active_allocation_record(_store(decoded={}), "portfolio", "scope")
    with pytest.raises(TypeError, match="validated model"):
        runtime._encode_model(object())
    with pytest.raises(TypeError, match="must be a mapping"):
        runtime._encode_mapping(object())
    with pytest.raises(TypeError, match="payload must be an object"):
        runtime._decode_model(cast("Any", object), "[]")
    with pytest.raises(TypeError, match="invalid Portfolio state-store"):
        runtime.execute_portfolio_state_store_operation(object(), "load_history")
    state_store = runtime.build_portfolio_state_store()
    with pytest.raises(ValueError, match="unsupported"):
        runtime.execute_portfolio_state_store_operation(state_store, "unknown")


def test_runtime_codec_shape_and_union_guards() -> None:
    """Exercise strict restoration for malformed and compatible stored shapes."""
    with pytest.raises(TypeError, match="nested Portfolio"):
        runtime._coerce_model_field(cast("Any", object), [])
    with pytest.raises(TypeError, match="tuple must be"):
        runtime._coerce_sequence((str,), {})
    with pytest.raises(TypeError, match="mapping must be"):
        runtime._coerce_mapping((str, str), [])
    with pytest.raises(TypeError, match="datetime must be"):
        runtime._coerce_field(datetime, 1)
    with pytest.raises(TypeError, match="decimal is malformed"):
        runtime._coerce_field(Decimal, True)
    assert runtime._coerce_sequence((Decimal,), ["1.25"]) == (Decimal("1.25"),)
    assert runtime._coerce_mapping((str, Decimal), {"weight": "0.5"}) == {
        "weight": Decimal("0.5")
    }
    assert runtime._coerce_union((type(None), Decimal), "2.5") == Decimal("2.5")
    assert runtime._coerce_union((datetime,), object()).__class__ is object


def test_definition_runtime_conflict_and_commit_guards(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Definition state replays idempotently and all conflicts fail closed."""
    definition = create_portfolio_value(
        "PortfolioDefinition",
        portfolio_id="portfolio-one",
        portfolio_version="v1",
        scope={"environment": "simulation"},
        definition={"objective": "balanced"},
        canonical_hash="a" * 64,
        request_id="req-11111111-1111-4111-8111-111111111111",
        workflow_id="wf-22222222-2222-4222-8222-222222222222",
        correlation_id="cor-33333333-3333-4333-8333-333333333333",
        created_at=_NOW,
    )
    state_store = cast("Any", runtime.build_portfolio_state_store())
    monkeypatch.setattr(runtime, "read_definition_record", lambda *_args: definition)
    assert state_store.save_definition(definition, {"event": "saved"}) == definition

    monkeypatch.setattr(runtime, "read_definition_record", lambda *_args: object())
    with pytest.raises(ValueError, match="immutable definition conflicts"):
        state_store.save_definition(definition, {"event": "saved"})

    monkeypatch.setattr(runtime, "read_definition_record", lambda *_args: None)
    monkeypatch.setattr(
        runtime, "create_definition_record", lambda *_args, **_kw: False
    )
    with pytest.raises(ValueError, match="transaction was not confirmed"):
        state_store.save_definition(definition, {"event": "saved"})
