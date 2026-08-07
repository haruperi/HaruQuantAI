"""Tests for explicit Simulation runtime composition."""

from pathlib import Path

import pytest
from app.services.simulator import build_simulation_run_dependencies


class _StateStore:
    """Minimal structural Simulation persistence port for composition tests."""

    def append_journal(self, *_: object) -> object:
        """Accept a journal append."""
        return None

    def flush_journal(self, *_: object) -> object:
        """Accept a journal flush."""
        return None

    def finalize_journal(self, *_: object) -> object:
        """Accept a journal finalization."""
        return None

    def load_run(self, *_: object) -> object:
        """Return no prior run."""
        return None

    def record_idempotency(self, *_: object, **__: object) -> object:
        """Accept one idempotency state change."""
        return None


def _ports() -> dict[str, object]:
    """Return the exact inert public-owner port set."""
    names = (
        "audit",
        "market_data",
        "tick_series",
        "indicators",
        "strategy",
        "risk",
        "order_intents",
        "execution_profile",
        "symbol_specification",
        "cost_model",
        "fx_evidence",
    )
    return {name: (lambda *args: args) for name in names}


def test_build_runtime_dependencies_requires_exact_ports(tmp_path: Path) -> None:
    """Construction accepts a complete graph and rejects missing owner ports."""
    dependencies = build_simulation_run_dependencies(
        state_store=_StateStore(),
        artifact_root=tmp_path,
        fast_research_enabled=False,
        ports=_ports(),
    )
    assert dependencies.artifact_root == tmp_path
    incomplete = _ports()
    incomplete.pop("risk")
    with pytest.raises(ValueError, match="canonical Simulation dependency set"):
        build_simulation_run_dependencies(
            state_store=_StateStore(),
            artifact_root=tmp_path,
            fast_research_enabled=False,
            ports=incomplete,
        )


def test_runtime_dependency_adapter_delegates_every_port(tmp_path: Path) -> None:
    """Every receiver-owned adapter method delegates to its named port."""
    calls: list[tuple[str, tuple[object, ...]]] = []
    ports = {
        name: (lambda *args, _name=name: calls.append((_name, args)) or _name)
        for name in _ports()
    }
    dependencies = build_simulation_run_dependencies(
        state_store=_StateStore(),
        artifact_root=tmp_path,
        fast_research_enabled=True,
        ports=ports,
    )

    assert dependencies.persist_audit_event("event") == "audit"
    assert dependencies.load_market_data("request") == "market_data"
    assert dependencies.generate_tick_series("dataset", "request") == "tick_series"
    assert dependencies.calculate_indicators("dataset", "request") == "indicators"
    assert (
        dependencies.evaluate_strategy("dataset", ("indicator",), "request")
        == "strategy"
    )
    assert dependencies.review_risk(("intent",), "request") == "risk"
    assert dependencies.build_order_intents(("decision",), "request") == "order_intents"
    assert dependencies.resolve_execution_profile("request") == "execution_profile"
    assert (
        dependencies.resolve_symbol_specification("request") == "symbol_specification"
    )
    assert dependencies.resolve_cost_model("request") == "cost_model"
    assert dependencies.resolve_fx_evidence(("fx-id",)) == "fx_evidence"
    assert len(calls) == 11


def test_runtime_dependencies_reject_invalid_store_and_port(tmp_path: Path) -> None:
    """Invalid state stores and non-callable ports fail before construction."""
    with pytest.raises(TypeError, match="state_store"):
        build_simulation_run_dependencies(
            state_store=object(),
            artifact_root=tmp_path,
            fast_research_enabled=False,
            ports=_ports(),
        )
    ports = _ports()
    ports["risk"] = object()
    with pytest.raises(ValueError, match="must be callable"):
        build_simulation_run_dependencies(
            state_store=_StateStore(),
            artifact_root=tmp_path,
            fast_research_enabled=False,
            ports=ports,
        )
