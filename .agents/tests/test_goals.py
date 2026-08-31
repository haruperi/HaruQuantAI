"""Deterministic Goal selection and state regression tests."""

from __future__ import annotations

import argparse
import importlib.util
import sys
import tomllib
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


def _load_make_goal(orc: ModuleType) -> ModuleType:
    path = orc.AGENTS_DIR / "make_goal.py"
    spec = importlib.util.spec_from_file_location("hq_make_goal_tests", path)
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


def _table_tracker(path: Path) -> Path:
    path.write_text(
        "# Table tracker\n\n"
        "| Order | Status | Type | V3 feature / atomic slice | Evidence |\n"
        "| --- | --- | --- | --- | --- |\n"
        "| P.001 | Pending | Specification Task | `SPEC-GAP-ONE` | Resolve it |\n"
        "| 1.1 | Complete | Primary | `FEAT-ONE` | Accepted |\n"
        "| 1.2 | Partial | Primary | `FEAT-TWO` | Remaining slice |\n"
        "| 16.1 | Pending | Integration | Bidirectional parity | Prove parity |\n",
        encoding="utf-8",
    )
    return path


def _unattended_policy(orc: ModuleType) -> Any:
    role = orc.RolePolicy(
        vendor="codex", brand="codex", model="gpt-5.6-sol", effort="high"
    )
    return orc.RuntimePolicy(
        schema_version=2,
        mode="delegate",
        approval_policy="unattended",
        max_iterations=6,
        roles=dict.fromkeys(("planner", "executor", "reviewer"), role),
        unattended=orc.UnattendedPolicy(
            allow_execute=True,
            allow_local_commit=True,
            allow_local_merge=True,
        ),
        recovery=orc.RecoveryPolicy(),
    )


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
    assert goal.resolve_goal_entries(_spec(selection_type="all_open"), entries) == [
        "4.1",
        "4.3",
        "5.1",
    ]


def test_current_table_tracker_selects_pending_and_partial_rows(
    orc: ModuleType, tmp_path: Path
) -> None:
    goal = _load_goal_engine(orc)
    entries = goal.parse_entries(_table_tracker(tmp_path / "tracker.md"))

    assert list(entries) == ["P.001", "1.1", "1.2", "16.1"]
    assert entries["P.001"]["is_feature"] is False
    assert entries["1.1"]["done"] is True
    assert entries["1.2"]["partial"] is True
    assert entries["1.2"]["feature"] == "FEAT-TWO"
    assert goal.resolve_goal_entries(_spec(selection_type="all_open"), entries) == [
        "P.001",
        "1.2",
        "16.1",
    ]


def test_repository_implementation_order_is_goal_parseable(
    orc: ModuleType,
) -> None:
    goal = _load_goal_engine(orc)
    tracker = orc.REPO_ROOT / "docs" / "dev" / "IMPLEMENTATION_ORDER.md"
    entries = goal.parse_entries(tracker)

    assert "P.001" in entries
    assert "16.5" in entries

    open_entries = [k for k, v in entries.items() if not goal.is_entry_complete(v)]
    if open_entries:
        selected = goal.resolve_goal_entries(_spec(selection_type="all_open"), entries)
        assert all(entry_id in entries for entry_id in selected)
        assert all(not entries[entry_id]["done"] for entry_id in selected)
        assert "P.001" not in selected
    else:
        with pytest.raises(goal.OrchestratorError, match="zero executable child Tasks"):
            goal.resolve_goal_entries(_spec(selection_type="all_open"), entries)


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


def test_child_additional_context_is_optional_and_frozen_exactly(
    orc: ModuleType, tmp_path: Path
) -> None:
    goal = _load_goal_engine(orc)
    _tracker(tmp_path / "tracker.md")

    without_context = goal.create_goal_state({"repo": tmp_path}, _spec())
    assert "child_additional_context" not in without_context

    context = "  Read the coordination plan.\nPreserve this spacing.  "
    with_context = goal.create_goal_state(
        {"repo": tmp_path}, _spec(child_additional_context=context)
    )
    assert with_context["child_additional_context"] == context
    reloaded = goal.load_goal_state({"repo": tmp_path}, with_context["goal_run_id"])
    assert reloaded["child_additional_context"] == context


@pytest.mark.parametrize("value", ["", "   ", 7, ["context"]])
def test_invalid_child_additional_context_fails_closed(
    orc: ModuleType, tmp_path: Path, value: Any
) -> None:
    goal = _load_goal_engine(orc)
    goal_file = tmp_path / "goal.toml"
    rendered = repr(value).replace("'", '"')
    goal_file.write_text(
        'goal_id = "G"\n'
        'goal_slug = "g"\n'
        'goal_name = "G"\n'
        'goal_request = "G"\n'
        'implementation_file = "tracker.md"\n'
        'selection_type = "all_open"\n'
        f"child_additional_context = {rendered}\n",
        encoding="utf-8",
    )
    with pytest.raises(goal.OrchestratorError, match="child_additional_context"):
        goal.load_goal_spec(goal_file)


def test_make_goal_renders_optional_child_context(orc: ModuleType) -> None:
    make_goal = _load_make_goal(orc)
    args = argparse.Namespace(
        entries=["4.1"],
        phase=None,
        all_open=False,
        goal_name=None,
        goal_id=None,
        goal_slug=None,
        goal_request=None,
        file="tracker.md",
        listed_order=True,
        child_additional_context="Line one.\nLine two.",
    )
    spec = make_goal._build_spec(args)
    rendered = make_goal._render(spec)

    assert tomllib.loads(rendered)["child_additional_context"] == (
        "Line one.\nLine two."
    )


@pytest.mark.parametrize("value", ["", "   ", 7])
def test_make_goal_rejects_invalid_supplied_child_context(
    orc: ModuleType, value: Any
) -> None:
    make_goal = _load_make_goal(orc)
    args = argparse.Namespace(
        entries=["4.1"],
        phase=None,
        all_open=False,
        goal_name=None,
        goal_id=None,
        goal_slug=None,
        goal_request=None,
        file="tracker.md",
        listed_order=True,
        child_additional_context=value,
    )

    with pytest.raises(ValueError, match="child_additional_context"):
        make_goal._build_spec(args)


def test_make_goal_omits_unsupplied_child_context(orc: ModuleType) -> None:
    make_goal = _load_make_goal(orc)
    args = argparse.Namespace(
        entries=["4.1"],
        phase=None,
        all_open=False,
        goal_name=None,
        goal_id=None,
        goal_slug=None,
        goal_request=None,
        file="tracker.md",
        listed_order=True,
        child_additional_context=None,
    )

    assert "child_additional_context" not in make_goal._build_spec(args)


def test_make_goal_can_render_unattended_assumption_retry(orc: ModuleType) -> None:
    make_goal = _load_make_goal(orc)
    args = argparse.Namespace(
        entries=None,
        phase=None,
        all_open=True,
        goal_name=None,
        goal_id=None,
        goal_slug=None,
        goal_request=None,
        file="tracker.md",
        listed_order=False,
        child_additional_context=None,
        continue_on_blocked=True,
    )

    spec = make_goal._build_spec(args)
    assert spec["stop_on_blocked"] is False
    assert tomllib.loads(make_goal._render(spec))["stop_on_blocked"] is False


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
        "stop_on_blocked = true\n",
        encoding="utf-8",
    )
    with pytest.raises(goal.OrchestratorError):
        goal.load_goal_spec(goal_file)


def test_goal_spec_accepts_unattended_assumption_retry_mode(
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
        "stop_on_blocked = false\n",
        encoding="utf-8",
    )
    assert goal.load_goal_spec(goal_file)["stop_on_blocked"] is False


def test_assumption_retry_mode_requires_unattended_runtime_policy(
    orc: ModuleType, tmp_path: Path
) -> None:
    goal = _load_goal_engine(orc)
    _tracker(tmp_path / "tracker.md")
    spec = _spec(stop_on_blocked=False)

    with pytest.raises(goal.OrchestratorError, match="unattended runtime policy"):
        goal.create_goal_state({"repo": tmp_path}, spec)

    state = goal.create_goal_state(
        {"repo": tmp_path, "runtime_policy": _unattended_policy(orc)}, spec
    )
    assert state["stop_on_blocked"] is False
    assert state["approval_policy"] == "unattended"
    assert state["runtime_mode"] == "delegate-headless"
    assert state["assumption_ledger"] == []


def test_unattended_child_receives_assumption_contract_and_archives_review(
    orc: ModuleType, tmp_path: Path
) -> None:
    goal = _load_goal_engine(orc)
    _tracker(tmp_path / "tracker.md")
    cfg = {
        "repo": tmp_path,
        "logs_dir": tmp_path / ".agents" / "logs",
        "runtime_policy": _unattended_policy(orc),
    }
    state = goal.create_goal_state(cfg, _spec(stop_on_blocked=False))

    task = goal._write_child_spec(cfg, state, "4.1")
    assert goal.ASSUMPTION_CONTEXT_LABEL in task["additional_context"]
    assert goal.ASSUMPTION_SECTION in task["additional_context"]

    run_id = "child-4.1"
    reviewer = cfg["logs_dir"] / run_id / "closeout" / "reviewer.md"
    reviewer.parent.mkdir(parents=True)
    reviewer.write_text(
        "## Accepted review\n\n"
        "### Assumptions for Human Review\n\n"
        "- Blocker: an owner-neutral default was unspecified.\n"
        "- Assumption: retain the documented existing default.\n"
        "- Evidence: owning README.\n"
        "- Risk: low and reversible.\n"
        "- Revisit trigger: owner changes the default.\n\n"
        "STOPPED : REVIEWER\n",
        encoding="utf-8",
    )
    goal._record_child_assumption_review(cfg, state, {"run_id": run_id}, "4.1")

    assert len(state["assumption_reviews"]) == 1
    assert len(state["assumption_ledger"]) == 1
    assert state["assumption_ledger"][0]["entry"] == "4.1"


def test_planner_blocker_gets_only_one_unattended_assumption_retry(
    orc: ModuleType, tmp_path: Path, monkeypatch: Any
) -> None:
    goal = _load_goal_engine(orc)
    _tracker(tmp_path / "tracker.md")
    cfg = {"repo": tmp_path, "runtime_policy": _unattended_policy(orc)}
    state = goal.create_goal_state(cfg, _spec(stop_on_blocked=False))
    active: dict[str, Any] = {"entry": "4.1", "run_id": "child-4.1"}
    child = {"run_id": "child-4.1", "phase": "planner_blocked"}
    resolutions: list[tuple[str, str]] = []
    monkeypatch.setattr(
        goal,
        "apply_planner_blocker_resolution",
        lambda _cfg, _child, evidence, *, source: resolutions.append(
            (evidence, source)
        ),
    )

    assert goal._apply_unattended_assumption_retry(cfg, state, active, child) is True
    assert goal._apply_unattended_assumption_retry(cfg, state, active, child) is False
    assert len(resolutions) == 1
    assert resolutions[0][1] == "GOAL_ASSUMPTION_POLICY"
    assert active["assumption_retry_used"] is True
    assert state["history"][-1]["event"] == "CHILD_ASSUMPTION_RETRY"


def test_second_running_goal_is_rejected(orc: ModuleType, tmp_path: Path) -> None:
    goal = _load_goal_engine(orc)
    _tracker(tmp_path / "tracker.md")
    cfg = {"repo": tmp_path}
    state = goal.create_goal_state(cfg, _spec())
    assert state["status"] == "RUNNING"
    with pytest.raises(goal.OrchestratorError):
        goal._ensure_no_running_goal(cfg)
