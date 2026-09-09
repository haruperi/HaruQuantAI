"""Tests for the frozen strategy-ready milestone derivation."""

from __future__ import annotations

import importlib.util
from pathlib import Path

MODULE_PATH = (
    Path(__file__).resolve().parents[2]
    / "scripts"
    / "derive_strategy_ready_milestone.py"
)
SPEC = importlib.util.spec_from_file_location(
    "derive_strategy_ready_milestone", MODULE_PATH
)
assert SPEC
assert SPEC.loader
milestone = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(milestone)


def test_frozen_closure_and_goal_are_honest() -> None:
    evidence, goal = milestone.derive()
    assert evidence["closure_count"] == 58
    assert evidence["accepted_count"] == 13
    assert evidence["remaining_count"] == 45
    assert evidence["full_v3_scope_preserved"] is True
    assert "DORMANT" in evidence["delivery_status"]
    assert "parallelism = 1" in goal
    assert 'entries = ["1.18"' in goal


def test_frozen_seed_capabilities_are_present() -> None:
    evidence, _goal = milestone.derive()
    assert evidence["seed_tasks"] == ["2.19", "3.14", "4.20", "4.23", "4.24", "4.25"]
    assert set(evidence["seed_tasks"]).issubset(evidence["closure"])
