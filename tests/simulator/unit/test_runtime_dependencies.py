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
