"""Focused tests for the machine-readable workflow protocol."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parents[1] / "orchestrator.py"
SPEC = importlib.util.spec_from_file_location("hq_orchestrator", MODULE_PATH)
assert SPEC
assert SPEC.loader
orchestrator = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = orchestrator
SPEC.loader.exec_module(orchestrator)


def test_protocol_has_unique_source_handoff_pairs() -> None:
    """Every source-role/handoff pair must route deterministically."""
    protocol_path = Path(__file__).resolve().parents[1] / "protocol.toml"
    _, transitions = orchestrator._parse_protocol(protocol_path)
    keys = [(item.source_role, item.handoff) for item in transitions]
    assert len(keys) == len(set(keys))


def test_protocol_contains_task_activation() -> None:
    """Initial Planner startup is a protocol-defined artifact transition."""
    protocol_path = Path(__file__).resolve().parents[1] / "protocol.toml"
    _, transitions = orchestrator._parse_protocol(protocol_path)
    activation = orchestrator._transition_for(
        transitions, "ORCHESTRATOR", "TASK_ACTIVATED"
    )
    assert activation.target_role == "PLANNER"
    assert activation.target_template == "docs/templates/prompt/planner.md"
    assert activation.gate is None


def test_protocol_contains_owner_gates() -> None:
    """Execution and commit owner gates remain explicit."""
    protocol_path = Path(__file__).resolve().parents[1] / "protocol.toml"
    _, transitions = orchestrator._parse_protocol(protocol_path)
    execute = orchestrator._transition_for(transitions, "PLANNER", "PENDING_APPROVAL")
    commit = orchestrator._transition_for(transitions, "REVIEWER", "PENDING_COMMIT")
    assert execute.gate == "APPROVED: EXECUTE"
    assert commit.gate == "APPROVED: COMMIT"
    gates = [item.gate for item in transitions if item.gate]
    assert gates == ["APPROVED: EXECUTE", "APPROVED: COMMIT"]
    assert "CONTINUE: REVIEWER" not in protocol_path.read_text(encoding="utf-8")
