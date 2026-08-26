"""Shared test fixtures for the .agents workflow test suite."""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

_ORCHESTRATOR_PATH = Path(__file__).resolve().parents[1] / "orchestrator.py"
_REPO_ROOT = Path(__file__).resolve().parents[2]


def load_orchestrator(tag: str = "hq_orch") -> ModuleType:
    """Load the orchestrator module under a unique name."""
    spec = importlib.util.spec_from_file_location(tag, _ORCHESTRATOR_PATH)
    assert spec
    assert spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def git(repo: Path, *args: str) -> str:
    """Run a git command in *repo* and return stripped stdout."""
    result = subprocess.run(
        ["git", *args],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    return result.stdout.strip()


def git_ok(repo: Path, *args: str) -> str:
    """Run a git command; return stdout on success or empty string."""
    result = subprocess.run(
        ["git", *args],
        cwd=repo,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    return result.stdout.strip() if result.returncode == 0 else ""


def scaffold_repo(tmp_path: Path) -> Path:
    """Create a minimal git repo with .agents/task workspace."""
    (tmp_path / ".agents" / "task").mkdir(parents=True)
    (tmp_path / "docs" / "templates" / "prompt").mkdir(parents=True)
    for name in ("planner.md", "executor.md", "reviewer.md", "next-agent.md"):
        (tmp_path / ".agents" / "task" / name).write_bytes(b"")
    for tpl in ("planner.md", "executor.md", "reviewer.md", "reviewer-closeout.md"):
        dst = tmp_path / "docs" / "templates" / "prompt" / tpl
        dst.write_text(
            (_REPO_ROOT / "docs" / "templates" / "prompt" / tpl).read_text(
                encoding="utf-8"
            ),
            encoding="utf-8",
        )
    git(tmp_path, "init", "-b", "main")
    git(tmp_path, "config", "user.email", "test@example.invalid")
    git(tmp_path, "config", "user.name", "Test")
    git(tmp_path, "add", ".")
    git(tmp_path, "commit", "-m", "baseline")
    return tmp_path


def build_cfg(orc: ModuleType, repo: Path) -> dict[str, Any]:
    """Build a minimal orchestrator config dict for *repo*."""
    protocol_path = _REPO_ROOT / ".agents" / "protocol.toml"
    protocol, transitions = orc._parse_protocol(protocol_path)
    return {
        "repo": repo,
        "main_branch": "main",
        "max_iterations": 10,
        "protocol": protocol,
        "transitions": transitions,
        "journals": {
            "planner": repo / ".agents" / "task" / "planner.md",
            "executor": repo / ".agents" / "task" / "executor.md",
            "reviewer": repo / ".agents" / "task" / "reviewer.md",
        },
        "next_agent": repo / ".agents" / "task" / "next-agent.md",
        "templates": {
            "planner": repo / "docs" / "templates" / "prompt" / "planner.md",
            "executor": repo / "docs" / "templates" / "prompt" / "executor.md",
            "reviewer": repo / "docs" / "templates" / "prompt" / "reviewer.md",
        },
        "runs_dir": repo / ".agents" / "runs",
        "logs_dir": repo / ".agents" / "logs",
    }


def build_state(
    *,
    run_id: str = "test-run",
    task_id: str = "FEAT-DEMO",
    task_slug: str = "demo",
    baseline: str = "",
) -> dict[str, Any]:
    """Build a minimal run-state dict."""
    return {
        "run_id": run_id,
        "task": {
            "task_kind": "feature",
            "task_id": task_id,
            "task_slug": task_slug,
            "task_name": "Demo Task",
            "task_request": "Implement demo feature.",
            "additional_context": "None",
            "exclusions": "None",
            "owner_execution_notes": "None",
            "review_focus": "None",
            "implementation_file": "",
            "implementation_entry": "",
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


@pytest.fixture
def orc() -> ModuleType:
    """Provide a freshly loaded orchestrator module."""
    return load_orchestrator("hq_orch_conftest")


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    """Provide a scaffolded temporary repository."""
    return scaffold_repo(tmp_path)


@pytest.fixture
def cfg(orc: ModuleType, repo: Path) -> dict[str, Any]:
    """Provide a minimal orchestrator config backed by *repo*."""
    return build_cfg(orc, repo)


@pytest.fixture
def state(repo: Path) -> dict[str, Any]:
    """Provide a minimal run-state backed by *repo*."""
    baseline = git(repo, "rev-parse", "HEAD")
    return build_state(baseline=baseline)
