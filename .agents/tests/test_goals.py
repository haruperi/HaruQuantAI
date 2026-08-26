"""Deterministic Goal selection and state regression tests."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest


def _load_goal_engine(orc: ModuleType) -> ModuleType:
    path = orc.AGENTS_DIR / "goal_engine.py"
    spec = importlib.util.spec_from_file_location("hq_goal_engine_tests", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _tracker(path: Path) -> Path:
    path.write_text(
        "# Tracker\n\n"
        "#### 4.1 [ ] `FEAT-ONE` First\n"
        "1. [ ] FR-ONE-001 first requirement\n\n"
        "#### 4.2 [X] `FEAT-TWO` Second\n"
        "1. [X] FR-TWO-001 second requirement\n\n"
        "#### 4.3 [ ] `FEAT-THREE` Third\n"
        "1. [ ] FR-THREE-001 third requirement\n\n"
        "#### 5.1 [ ] `FEAT-FOUR` Fourth\n"
        "1. [ ] FR-FOUR-001 fourth requirement\n",
        encoding="utf-8",
    )
    return path


def _spec(**overrides: Any) -> dict[str, Any]:
    spec: dict[str, Any] = {
        "goal_id": "GOAL-TEST",
        "goal_slug": "test-goal",
        "goal_name": "Test Goal",
        "goal_request": "Test deterministic Goal selection.",
        "implementation_file": "tracker.md",
        "selection_type": "phase",
        "selection": "4",
        "execution_order": "tracker",
        "skip_completed": True,
        "stop_on_blocked": True,
    }
    spec.update(overrides)
    return spec


def test_phase_selection_skips_completed(orc: ModuleType, tmp_path: Path) -> None:
    goal = _load_goal_engine(orc)
    entries = goal.parse_entries(_tracker(tmp_path / "tracker.md"))
    assert goal.resolve_goal_entries(_spec(), entries) == ["4.1", "4.3"]


def test_explicit_entries_can_preserve_listed_order(
    orc: ModuleType, tmp_path: Path
) -> None:
    goal = _load_goal_engine(orc)
    entries = goal.parse_entries(_tracker(tmp_path / "tracker.md"))
    spec = _spec(
        selection_type="entries",
        entries=["5.1", "4.1"],
        execution_order="listed",
    )
    assert goal.resolve_goal_entries(spec, entries) == ["5.1", "4.1"]


def test_explicit_entries_tracker_order_is_deterministic(
    orc: ModuleType, tmp_path: Path
) -> None:
    goal = _load_goal_engine(orc)
    entries = goal.parse_entries(_tracker(tmp_path / "tracker.md"))
    spec = _spec(
        selection_type="entries",
        entries=["5.1", "4.1"],
        execution_order="tracker",
    )
    assert goal.resolve_goal_entries(spec, entries) == ["4.1", "5.1"]


def test_all_open_selects_every_incomplete_entry(
    orc: ModuleType, tmp_path: Path
) -> None:
    goal = _load_goal_engine(orc)
    entries = goal.parse_entries(_tracker(tmp_path / "tracker.md"))
    assert goal.resolve_goal_entries(
        _spec(selection_type="all_open"), entries
    ) == ["4.1", "4.3", "5.1"]


def test_unknown_explicit_entry_fails_closed(orc: ModuleType, tmp_path: Path) -> None:
    goal = _load_goal_engine(orc)
    entries = goal.parse_entries(_tracker(tmp_path / "tracker.md"))
    with pytest.raises(goal.OrchestratorError):
        goal.resolve_goal_entries(
            _spec(selection_type="entries", entries=["99.9"]), entries
        )


def test_zero_child_goal_fails_closed(orc: ModuleType, tmp_path: Path) -> None:
    goal = _load_goal_engine(orc)
    entries = goal.parse_entries(_tracker(tmp_path / "tracker.md"))
    with pytest.raises(goal.OrchestratorError):
        goal.resolve_goal_entries(
            _spec(selection_type="entries", entries=["4.2"]), entries
        )


def test_goal_scope_is_frozen_at_activation(orc: ModuleType, tmp_path: Path) -> None:
    goal = _load_goal_engine(orc)
    tracker = _tracker(tmp_path / "tracker.md")
    cfg = {"repo": tmp_path}
    state = goal.create_goal_state(cfg, _spec())
    assert state["resolved_entries"] == ["4.1", "4.3"]
    tracker.write_text(
        tracker.read_text(encoding="utf-8")
        + "\n#### 4.4 [ ] `FEAT-FIVE` Fifth\n1. [ ] FR-FIVE-001 fifth\n",
        encoding="utf-8",
    )
    reloaded = goal.load_goal_state(cfg, state["goal_run_id"])
    assert reloaded["resolved_entries"] == ["4.1", "4.3"]


def test_goal_state_never_contains_role_session_ids(
    orc: ModuleType, tmp_path: Path
) -> None:
    goal = _load_goal_engine(orc)
    _tracker(tmp_path / "tracker.md")
    state = goal.create_goal_state({"repo": tmp_path}, _spec())
    serialized = goal.json.dumps(state)
    assert "role_sessions" not in serialized
    assert "session_id" not in serialized


def test_duplicate_entries_in_goal_toml_are_rejected(
    orc: ModuleType, tmp_path: Path
) -> None:
    goal = _load_goal_engine(orc)
    goal_file = tmp_path / "goal.toml"
    goal_file.write_text(
        'goal_id = "G"\n'
        'goal_slug = "g"\n'
        'goal_name = "G"\n'
        'goal_request = "G"\n'
        'implementation_file = "tracker.md"\n'
        'selection_type = "entries"\n'
        'entries = ["4.1", "4.1"]\n'
        'stop_on_blocked = true\n',
        encoding="utf-8",
    )
    with pytest.raises(goal.OrchestratorError):
        goal.load_goal_spec(goal_file)


def test_goal_v1_rejects_automatic_child_skipping(
    orc: ModuleType, tmp_path: Path
) -> None:
    goal = _load_goal_engine(orc)
    goal_file = tmp_path / "goal.toml"
    goal_file.write_text(
        'goal_id = "G"\n'
        'goal_slug = "g"\n'
        'goal_name = "G"\n'
        'goal_request = "G"\n'
        'implementation_file = "tracker.md"\n'
        'selection_type = "all_open"\n'
        'stop_on_blocked = false\n',
        encoding="utf-8",
    )
    with pytest.raises(goal.OrchestratorError):
        goal.load_goal_spec(goal_file)


def test_second_running_goal_is_rejected(orc: ModuleType, tmp_path: Path) -> None:
    goal = _load_goal_engine(orc)
    _tracker(tmp_path / "tracker.md")
    cfg = {"repo": tmp_path}
    state = goal.create_goal_state(cfg, _spec())
    assert state["status"] == "RUNNING"
    with pytest.raises(goal.OrchestratorError):
        goal._ensure_no_running_goal(cfg)
