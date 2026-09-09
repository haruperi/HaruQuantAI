"""Integrity regression tests for workflow artifacts and approval gates."""

from __future__ import annotations

import hashlib
import subprocess
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

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


def test_run_preauthorization_records_truthful_fingerprints(
    orc: ModuleType, repo: Path
) -> None:
    journal = repo / ".agents/task/planner.md"
    plan = "## Dry Run 1\nplan\n"
    digest = hashlib.sha256(plan.encode()).hexdigest()
    policy_hash = "a" * 64
    scope_hash = "b" * 64
    journal.write_bytes(
        (
            plan
            + "### Owner Gate — Dry Run 1\n\n"
            + "Gate: APPROVED: EXECUTE\n"
            + "Authorization source: RUN_PREAUTHORIZATION\n"
            + "Task ID: FEAT-DEMO\nDry Run: 1\n"
            + f"Plan SHA-256: {digest}\nMain baseline: abc\n"
            + "Task branch: feature/feat-demo-demo\n"
            + f"Runtime policy SHA-256: {policy_hash}\n"
            + f"Frozen scope SHA-256: {scope_hash}\n"
        ).encode()
    )

    orc._verify_approval_chain(
        journal,
        1,
        "FEAT-DEMO",
        "abc",
        "feature/feat-demo-demo",
        digest,
        authorization_source="RUN_PREAUTHORIZATION",
        runtime_policy_fingerprint=policy_hash,
        scope_fingerprint=scope_hash,
    )


def test_reviewer_prompt_contains_no_claim_payload(repo: Path) -> None:
    text = (repo / "docs/templates/prompt/reviewer.md").read_text(encoding="utf-8")
    assert "{{handoff_facts}}" not in text
    assert text.index("Stage A") < text.index("Stage B") < text.index("Stage C")


def _agent_cfg(repo: Path, code: str, retries: int) -> dict[str, Any]:
    return {
        "repo": repo,
        "logs_dir": repo / ".agents/logs",
        "retries": retries,
        "timeout": 10,
        "stream": False,
        "heartbeat": 0,
        "roles": {
            "planner": {
                "command": [sys.executable, "-c", code],
                "prompt_delivery": "stdin",
            }
        },
    }


def test_failed_mutating_process_suppresses_retry(orc: ModuleType, repo: Path) -> None:
    counter = repo.parent / f"{repo.name}-mutating-count.txt"
    code = (
        "from pathlib import Path; "
        f"c=Path({str(counter)!r}); "
        "n=int(c.read_text())+1 if c.exists() else 1; c.write_text(str(n)); "
        "Path('surprise.txt').write_text('bad'); raise SystemExit(1)"
    )
    with pytest.raises(orc.OrchestratorError, match="automatic retry suppressed"):
        orc.run_agent(_agent_cfg(repo, code, 2), "PLANNER", "prompt", "mutating")
    assert counter.read_text(encoding="utf-8") == "1"


def test_failed_nonmutating_process_may_retry(orc: ModuleType, repo: Path) -> None:
    counter = repo.parent / f"{repo.name}-clean-count.txt"
    code = (
        "from pathlib import Path; "
        f"c=Path({str(counter)!r}); "
        "n=int(c.read_text())+1 if c.exists() else 1; c.write_text(str(n)); "
        "raise SystemExit(1 if n == 1 else 0)"
    )
    orc.run_agent(_agent_cfg(repo, code, 1), "PLANNER", "prompt", "clean")
    assert counter.read_text(encoding="utf-8") == "2"


def test_stale_canonical_template_rejected(
    orc: ModuleType,
    cfg: dict[str, Any],
    state: dict[str, Any],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    orc._activate_task(cfg, state)
    planner_template = cfg["templates"]["planner"]
    planner_template.write_text("changed template\n", encoding="utf-8")
    monkeypatch.setattr(
        orc,
        "run_agent",
        lambda *_args, **_kwargs: pytest.fail("stale prompt was invoked"),
    )
    with pytest.raises(orc.OrchestratorError, match="Canonical template changed"):
        orc._invoke_pending(cfg, state, "PLANNER")


def test_staging_or_normalizing_coordination_bytes_changes_fingerprint(
    orc: ModuleType,
    repo: Path,
) -> None:
    """CRLF staging cannot preserve an approval fingerprint silently."""
    attributes = repo / ".gitattributes"
    attributes.write_text(".agents/task/*.md text eol=lf\n", encoding="utf-8")
    subprocess.run(["git", "config", "core.autocrlf", "true"], cwd=repo, check=True)
    subprocess.run(["git", "add", ".gitattributes"], cwd=repo, check=True)
    subprocess.run(
        ["git", "commit", "--no-verify", "-m", "attributes"],
        cwd=repo,
        check=True,
        capture_output=True,
    )
    planner = repo / ".agents/task/planner.md"
    planner.write_bytes(b"approved\r\n")
    before_stage = orc._worktree_fingerprint(repo)

    subprocess.run(["git", "add", ".agents/task/planner.md"], cwd=repo, check=True)
    after_stage = orc._worktree_fingerprint(repo)

    assert after_stage != before_stage
    assert (
        subprocess.run(
            ["git", "show", ":.agents/task/planner.md"],
            cwd=repo,
            check=True,
            capture_output=True,
        ).stdout
        == b"approved\n"
    )


def test_product_change_invalidates_validated_role_artifact(
    orc: ModuleType,
    cfg: dict[str, Any],
    state: dict[str, Any],
    repo: Path,
) -> None:
    """A product mutation after prompt validation fails before role execution."""
    orc._activate_task(cfg, state)
    (repo / "product.py").write_text("changed = True\n", encoding="utf-8")

    with pytest.raises(orc.OrchestratorError, match="Working tree changed"):
        orc._ensure_pending_artifact_unchanged(cfg, state)
