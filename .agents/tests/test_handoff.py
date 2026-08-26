"""Focused tests for next-agent parsing and fail-closed validation primitives."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

MODULE_PATH = Path(__file__).resolve().parents[1] / "orchestrator.py"
SPEC = importlib.util.spec_from_file_location("hq_orchestrator_handoff", MODULE_PATH)
assert SPEC
assert SPEC.loader
orchestrator = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = orchestrator
SPEC.loader.exec_module(orchestrator)


def _artifact(body: str) -> str:
    return f"""+++
prompt_schema_version = 1
run_id = "run"
task_id = "TASK"
iteration = 1
source_role = "EXECUTOR"
target_role = "REVIEWER"
handoff = "READY_FOR_REVIEW"
branch = "feature/task"
baseline_commit = "abc"
source_head = "abc"
template_path = "docs/templates/prompt/reviewer.md"
requires_owner_gate = false
owner_gate = ""
+++

{body}
"""


def test_parse_next_agent_reads_toml_front_matter(tmp_path: Path) -> None:
    """A complete artifact exposes metadata and prompt body separately."""
    path = tmp_path / "next-agent.md"
    path.write_text(_artifact("# PROMPT\n"), encoding="utf-8")
    parsed = orchestrator.parse_next_agent(path)
    assert parsed.metadata["target_role"] == "REVIEWER"
    assert parsed.body.startswith("# PROMPT")


def test_parse_next_agent_rejects_unfilled_placeholders(tmp_path: Path) -> None:
    """A role cannot hand off a partially instantiated prompt."""
    path = tmp_path / "next-agent.md"
    path.write_text(_artifact("{{unfilled}}\n"), encoding="utf-8")
    with pytest.raises(orchestrator.OrchestratorError):
        orchestrator.parse_next_agent(path)


def test_handoff_block_parses_latest_triplet() -> None:
    """Routing markers remain strict and machine-readable."""
    lines = [
        "STOPPED : EXECUTOR",
        "ACTIVATING : REVIEWER",
        "HANDOFF : READY_FOR_REVIEW",
    ]
    assert orchestrator.parse_handoff_block(lines) == {
        "stopped": "EXECUTOR",
        "activating": "REVIEWER",
        "handoff": "READY_FOR_REVIEW",
    }


def test_pending_next_agent_mutation_fails_closed(tmp_path: Path) -> None:
    """A prompt changed after validation cannot be executed."""
    path = tmp_path / "next-agent.md"
    original = _artifact("# PROMPT\n")
    path.write_text(original, encoding="utf-8")
    cfg = {"next_agent": path, "repo": tmp_path}
    state = {
        "next_agent": {
            "prompt_sha256": orchestrator._sha_text(original),
            "worktree_sha256": "unused-after-prompt-mismatch",
        }
    }

    path.write_text(original + "\nMUTATED\n", encoding="utf-8")

    with pytest.raises(
        orchestrator.OrchestratorError,
        match="next-agent.md changed after it was validated",
    ):
        orchestrator._ensure_pending_artifact_unchanged(cfg, state)
