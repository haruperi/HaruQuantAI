"""Risk package-root state read tests."""

import pytest
from app.services.risk.audit import runtime


def test_kill_switch_and_decision_reads_delegate_to_owner_store(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Public reads use only the Risk-owned state adapter."""
    store = object()
    calls: list[tuple[str, tuple[object, ...]]] = []
    monkeypatch.setattr(runtime, "build_risk_state_store", lambda: store)

    def execute(_store: object, operation: str, *args: object) -> object:
        calls.append((operation, args))
        return ("decision",) if operation == "list_decisions" else "state"

    monkeypatch.setattr(runtime, "execute_risk_state_store_operation", execute)
    assert runtime.get_kill_switch_state("global", {}) == "state"
    assert runtime.list_risk_decisions(10) == ("decision",)
    assert calls == [
        ("load_kill_switch", ("global", {})),
        ("list_decisions", (10,)),
    ]


def test_decision_write_delegates_canonical_value(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The package-root write accepts only the canonical decision contract."""

    class _Decision:
        """Test stand-in for the already-validated contract."""

    decision = _Decision()
    store = object()
    calls: list[tuple[object, str, object]] = []
    monkeypatch.setattr(runtime, "RiskDecisionPackage", _Decision)
    monkeypatch.setattr(runtime, "build_risk_state_store", lambda: store)
    monkeypatch.setattr(
        runtime,
        "execute_risk_state_store_operation",
        lambda value, operation, payload: calls.append((value, operation, payload)),
    )
    runtime.persist_risk_decision(decision)
    assert calls == [(store, "save_decision", decision)]
    with pytest.raises(TypeError, match="RiskDecisionPackage"):
        runtime.persist_risk_decision(object())
