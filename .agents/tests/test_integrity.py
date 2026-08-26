"""Integrity regression tests for workflow artifacts and approval gates."""

from __future__ import annotations

import hashlib
from pathlib import Path
from types import ModuleType

import pytest


def test_approval_chain_uses_pre_gate_bytes(orc: ModuleType, repo: Path) -> None:
    journal = repo / ".agents/task/planner.md"
    plan = "## Dry Run 1\nplan\n"
    digest = hashlib.sha256(plan.encode()).hexdigest()
    journal.write_bytes(
        (
            plan
            + "### Owner Gate — Dry Run 1\n\n"
            + "APPROVED: EXECUTE\nTask ID: FEAT-DEMO\nDry Run: 1\n"
            + f"Plan SHA-256: {digest}\nMain baseline: abc\n"
            + "Task branch: feature/feat-demo-demo\n"
        ).encode()
    )
    orc._verify_approval_chain(
        journal, 1, "FEAT-DEMO", "abc", "feature/feat-demo-demo", digest
    )


def test_duplicate_owner_gate_fails_closed(orc: ModuleType, repo: Path) -> None:
    journal = repo / ".agents/task/planner.md"
    marker = "### Owner Gate — Dry Run 1\n"
    journal.write_text("plan\n" + marker + marker, encoding="utf-8")
    with pytest.raises(orc.OrchestratorError):
        orc._verify_approval_chain(journal, 1, "T", "B", "branch", "bad")


def test_reviewer_prompt_contains_no_claim_payload(repo: Path) -> None:
    text = (repo / "docs/templates/prompt/reviewer.md").read_text(encoding="utf-8")
    assert "{{handoff_facts}}" not in text
    assert text.index("Stage A") < text.index("Stage B") < text.index("Stage C")
