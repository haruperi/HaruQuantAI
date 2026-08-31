"""Focused tests for task activation and initial Planner artifact materialization."""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

MODULE_PATH = Path(__file__).resolve().parents[1] / "orchestrator.py"
SPEC = importlib.util.spec_from_file_location("hq_orchestrator_activation", MODULE_PATH)
assert SPEC
assert SPEC.loader
orchestrator = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = orchestrator
SPEC.loader.exec_module(orchestrator)


def _git(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    return result.stdout.strip()


def _activation_fixture(tmp_path: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    (tmp_path / ".agents/task").mkdir(parents=True)
    (tmp_path / "docs/templates/prompt").mkdir(parents=True)
    for name in ("planner.md", "executor.md", "reviewer.md", "next-agent.md"):
        (tmp_path / ".agents/task" / name).write_bytes(b"")

    source_root = Path(__file__).resolve().parents[2]
    planner_template = tmp_path / "docs/templates/prompt/planner.md"
    planner_template.write_text(
        (source_root / "docs/templates/prompt/planner.md").read_text(encoding="utf-8"),
        encoding="utf-8",
    )

    _git(tmp_path, "init", "-b", "main")
    _git(tmp_path, "config", "user.email", "test@example.invalid")
    _git(tmp_path, "config", "user.name", "Test")
    _git(tmp_path, "add", ".")
    _git(tmp_path, "commit", "--no-verify", "-m", "baseline")

    protocol_path = source_root / ".agents/protocol.toml"
    protocol, transitions = orchestrator._parse_protocol(protocol_path)
    cfg = {
        "repo": tmp_path,
        "main_branch": "main",
        "protocol": protocol,
        "transitions": transitions,
        "journals": {
            "planner": tmp_path / ".agents/task/planner.md",
            "executor": tmp_path / ".agents/task/executor.md",
            "reviewer": tmp_path / ".agents/task/reviewer.md",
        },
        "next_agent": tmp_path / ".agents/task/next-agent.md",
        "templates": {"planner": planner_template},
        "runs_dir": tmp_path / ".agents/runs",
    }
    baseline = orchestrator._entry_gate(cfg)
    state = {
        "run_id": "activation-test",
        "task": {
            "task_kind": "feature",
            "task_id": "FEAT-DEMO",
            "task_slug": "demo",
            "task_name": "Demo",
            "task_request": "Test artifact-driven activation.",
        },
        "baseline": baseline,
        "branch": None,
        "iteration": 1,
        "phase": "task_activation",
        "status": "RUNNING",
        "owner_feedback": "",
        "correction_context": "None",
        "blockers": [],
        "history": [],
        "next_agent": None,
    }
    return cfg, state


def test_activation_creates_branch_then_planner_artifact(tmp_path: Path) -> None:
    """Initial Planner is materialized only after deterministic branch creation."""
    cfg, state = _activation_fixture(tmp_path)

    orchestrator._activate_task(cfg, state)

    assert _git(tmp_path, "branch", "--show-current") == "feature/feat-demo-demo"
    assert _git(tmp_path, "rev-parse", "HEAD") == state["baseline"]
    artifact = orchestrator.parse_next_agent(cfg["next_agent"])
    assert artifact.metadata["source_role"] == "ORCHESTRATOR"
    assert artifact.metadata["target_role"] == "PLANNER"
    assert artifact.metadata["handoff"] == "TASK_ACTIVATED"
    assert artifact.metadata["branch"] == "feature/feat-demo-demo"
    assert artifact.metadata["baseline_commit"] == state["baseline"]
    assert artifact.metadata["source_head"] == state["baseline"]
    assert artifact.metadata["template_path"] == "docs/templates/prompt/planner.md"
    assert artifact.metadata["requires_owner_gate"] is False
    assert state["phase"] == "planner"
    assert state["next_agent"]["prompt_sha256"] == orchestrator._sha_text(artifact.raw)


def test_activation_fails_before_branch_creation_for_empty_component(
    tmp_path: Path,
) -> None:
    """Unusable task metadata fails closed before a role can be invoked."""
    cfg, state = _activation_fixture(tmp_path)
    state["task"]["task_id"] = "///"

    with pytest.raises(orchestrator.OrchestratorError, match="branch component"):
        orchestrator._activate_task(cfg, state)

    assert _git(tmp_path, "branch", "--show-current") == "main"
    assert cfg["next_agent"].stat().st_size == 0


def test_non_feature_tasks_use_task_prefix() -> None:
    """Non-feature branch derivation remains deterministic."""
    branch = orchestrator._derive_task_branch(
        {"task_kind": "docs", "task_id": "DOCS-42", "task_slug": "workflow"}
    )
    assert branch == "task/docs-42-workflow"


def test_initial_planner_mutation_fails_before_invocation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The initial Planner cannot run after its validated artifact changes."""
    cfg, state = _activation_fixture(tmp_path)
    orchestrator._activate_task(cfg, state)
    cfg["next_agent"].write_text(
        cfg["next_agent"].read_text(encoding="utf-8") + "\nMUTATED\n",
        encoding="utf-8",
    )
    called = False

    def _unexpected_run_agent(*_args: object, **_kwargs: object) -> tuple[str, Path]:
        nonlocal called
        called = True
        raise AssertionError("run_agent must not be reached")

    runtime_module = sys.modules[orchestrator._invoke_pending.__module__]
    monkeypatch.setattr(runtime_module, "run_agent", _unexpected_run_agent)

    with pytest.raises(
        orchestrator.OrchestratorError, match="changed after it was validated"
    ):
        orchestrator._invoke_pending(cfg, state, "PLANNER")
    assert called is False
