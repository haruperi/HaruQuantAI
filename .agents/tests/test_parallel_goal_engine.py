"""Parallel Goal scheduling and lane-state tests."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from types import ModuleType

import pytest


def _load() -> ModuleType:
    root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(root))
    path = root / "parallel_goal_engine.py"
    spec = importlib.util.spec_from_file_location("hq_parallel_goal_tests", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _schedule(path: Path) -> None:
    path.write_text(
        json.dumps(
            {
                "dag_properties": {"is_acyclic": True},
                "phases": [{"tasks": ["1.01", "1.02", "1.03"]}],
                "schedule_constraints": [
                    {"task": "1.02", "predecessor": "1.01"},
                    {"task": "1.03", "predecessor": "1.01"},
                ],
            }
        ),
        encoding="utf-8",
    )


def test_readiness_uses_schedule_constraints(tmp_path: Path) -> None:
    parallel = _load()
    schedule = tmp_path / "schedule.json"
    _schedule(schedule)
    predecessors, digest = parallel.load_schedule(schedule)
    assert len(digest) == 64
    assert parallel.ready_entries(
        selected=["1.01", "1.02", "1.03"],
        completed={"1.01"},
        active={"1.02"},
        predecessors=predecessors,
    ) == ["1.03"]


def test_parallel_operation_requires_explicit_lane(tmp_path: Path) -> None:
    parallel = _load()
    schedule = tmp_path / "schedule.json"
    _schedule(schedule)
    state = parallel.create_parallel_state(
        {"active_child": None},
        lanes=["codex", "gemini", "zcode"],
        schedule_path=schedule,
    )
    with pytest.raises(parallel.ParallelGoalError, match="--lane"):
        parallel.require_lane(state, None)


def test_two_lane_state_uses_only_requested_lanes(tmp_path: Path) -> None:
    parallel = _load()
    schedule = tmp_path / "schedule.json"
    _schedule(schedule)
    state = parallel.create_parallel_state(
        {"active_child": None}, lanes=["codex", "gemini"], schedule_path=schedule
    )
    assert state["parallelism"] == 2
    assert state["lane_names"] == ["codex", "gemini"]
    assert parallel.is_parallel_state(state)
