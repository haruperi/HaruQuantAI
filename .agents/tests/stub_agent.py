#!/usr/bin/env python3
"""Deterministic stub agents for the artifact-driven orchestrator self-test."""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
import tomllib
from pathlib import Path
from typing import Any

POINTER_RE = re.compile(r"instructions in (.*?) exactly")
ITER_RE = re.compile(
    r"(?:Iteration|Dry-run/report number|Approved dry-run number)\s*:\s*`?(\d+)"
)


def _git(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=repo,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr)
    return result.stdout.strip()


def _parse_front_matter(text: str) -> dict[str, Any]:
    if not text.startswith("+++\n"):
        return {}
    marker = text.find("\n+++\n", 4)
    if marker < 0:
        return {}
    return tomllib.loads(text[4:marker])


def _iteration(prompt: str) -> int:
    meta = _parse_front_matter(prompt)
    if meta.get("iteration"):
        return int(meta["iteration"])
    match = ITER_RE.search(prompt)
    return int(match.group(1)) if match else 1


def _append(path: Path, text: str) -> None:
    with path.open("a", encoding="utf-8") as handle:
        handle.write(text)


def _meta(
    *,
    run_id: str,
    task_id: str,
    iteration: int,
    source_role: str,
    target_role: str,
    handoff: str,
    branch: str,
    baseline: str,
    head: str,
    template: str,
    gate: str = "",
    allowed_write_paths: tuple[str, ...] = (),
) -> str:
    required = "true" if gate else "false"
    allowed = ""
    if allowed_write_paths:
        rendered = ", ".join(f'"{path}"' for path in allowed_write_paths)
        allowed = f"allowed_write_paths = [{rendered}]\n"
    return (
        "+++\n"
        "prompt_schema_version = 1\n"
        f'run_id = "{run_id}"\n'
        f'task_id = "{task_id}"\n'
        f"iteration = {iteration}\n"
        f'source_role = "{source_role}"\n'
        f'target_role = "{target_role}"\n'
        f'handoff = "{handoff}"\n'
        f'branch = "{branch}"\n'
        f'baseline_commit = "{baseline}"\n'
        f'source_head = "{head}"\n'
        f'template_path = "{template}"\n'
        f"requires_owner_gate = {required}\n"
        f'owner_gate = "{gate}"\n'
        f"{allowed}"
        "+++\n\n"
    )


def _planner_body(iteration: int) -> str:
    return f"""# PROMPT

## 1. Role
Act as the HaruQuantAI **Planner** defined by `AGENTS.md`.

## 2. Context
Iteration: `{iteration}`

## 5. Authority and Boundaries
Plan only; do not implement.

## 8. Output Format
STOPPED : PLANNER
ACTIVATING : EXECUTOR
HANDOFF : PENDING_APPROVAL
"""


def _executor_body(iteration: int) -> str:
    return f"""# PROMPT

## 1. Role
Act as the HaruQuantAI **Executor** defined by `AGENTS.md`.

## 2. Context
Approved dry-run number: `{iteration}`

## 5. Authority and Boundaries
Implement only approved scope.

## 8. Output Format
STOPPED : EXECUTOR
ACTIVATING : REVIEWER
HANDOFF : READY_FOR_REVIEW
"""


def _reviewer_body(iteration: int) -> str:
    return f"""# PROMPT

## 1. Role
Act as the HaruQuantAI **Reviewer** defined by `AGENTS.md`.

## 2. Context
Dry-run/report number: `{iteration}`

## 3. Instruction / Task
Stage A — Independent reconstruction
Stage B — Independent verification
Stage C — Dry-run, report, and code reconciliation

## 5. Authority and Boundaries
Never repair implementation.
"""


def _closeout_body(iteration: int) -> str:
    return f"""# PROMPT

## 1. Role
Act as the HaruQuantAI **Reviewer performing authorized close-out**.

## 2. Context
Review number: `{iteration}`

## 3. Instruction / Task
Perform the ff-only merge after exact authorization.

## 8. Output Format
HANDOFF : ACCEPTED
"""


def _write_next(
    repo: Path,
    *,
    source: str,
    target: str,
    handoff: str,
    iteration: int,
    template: str,
    body: str,
    gate: str = "",
    allowed_write_paths: tuple[str, ...] = (),
) -> None:
    branch = _git(repo, "branch", "--show-current")
    baseline = _git(repo, "rev-parse", "main")
    head = _git(repo, "rev-parse", "HEAD")
    raw = (
        _meta(
            run_id="self-test",
            task_id="FEAT-DEMO",
            iteration=iteration,
            source_role=source,
            target_role=target,
            handoff=handoff,
            branch=branch,
            baseline=baseline,
            head=head,
            template=template,
            gate=gate,
            allowed_write_paths=allowed_write_paths,
        )
        + body
    )
    (repo / ".agents/task/next-agent.md").write_text(raw, encoding="utf-8")


def _planner(repo: Path, iteration: int) -> None:
    if _git(repo, "branch", "--show-current") == "main":
        _git(repo, "checkout", "-b", "feature/feat-demo-demo")
    journal = repo / ".agents/task/planner.md"
    _append(
        journal,
        f"\n## Dry Run {iteration}\n"
        "1. TASK TO DO: stub\n2. Files read: stub\n3. Files to create or edit: demo.txt\n"
        "4. Dependencies: None\n5. Blockers: None\n6. Scope boundaries: demo only\n"
        "7. Validation commands: stub\n8. Rollback: restore demo.txt\n"
        "ALLOWED_WRITE_PATHS:\n- demo.txt\nEND_ALLOWED_WRITE_PATHS:\n"
        "STOPPED : PLANNER\nACTIVATING : EXECUTOR\nHANDOFF : PENDING_APPROVAL\n",
    )
    _write_next(
        repo,
        source="PLANNER",
        target="EXECUTOR",
        handoff="PENDING_APPROVAL",
        iteration=iteration,
        template="docs/templates/prompt/executor.md",
        body=_executor_body(iteration),
        gate="APPROVED: EXECUTE",
        allowed_write_paths=("demo.txt",),
    )


def _executor(repo: Path, iteration: int) -> None:
    journal = repo / ".agents/task/executor.md"
    demo = repo / "demo.txt"
    demo.write_text(f"implemented iteration {iteration}\n", encoding="utf-8")
    if iteration == 1:
        _append(
            journal,
            "\n## Report 1\nBLOCKED: simulated upstream contract.\n"
            "STOPPED : EXECUTOR\nACTIVATING : PLANNER\nHANDOFF : BLOCKED\n",
        )
        _write_next(
            repo,
            source="EXECUTOR",
            target="PLANNER",
            handoff="BLOCKED",
            iteration=2,
            template="docs/templates/prompt/planner.md",
            body=_planner_body(2),
        )
        return
    _append(
        journal,
        f"\n## Report {iteration}\nREADY.\n"
        "STOPPED : EXECUTOR\nACTIVATING : REVIEWER\nHANDOFF : READY_FOR_REVIEW\n",
    )
    _write_next(
        repo,
        source="EXECUTOR",
        target="REVIEWER",
        handoff="READY_FOR_REVIEW",
        iteration=iteration,
        template="docs/templates/prompt/reviewer.md",
        body=_reviewer_body(iteration),
    )


def _reviewer(repo: Path, iteration: int, incoming: dict[str, Any]) -> None:
    if incoming.get("handoff") == "PENDING_COMMIT":
        _closeout(repo, iteration)
        return
    journal = repo / ".agents/task/reviewer.md"
    if iteration == 2:
        _append(
            journal,
            "\n## Review 2\nCHANGES REQUESTED.\n"
            "STOPPED : REVIEWER\nACTIVATING : PLANNER\nHANDOFF : CHANGES_REQUESTED\n",
        )
        _write_next(
            repo,
            source="REVIEWER",
            target="PLANNER",
            handoff="CHANGES_REQUESTED",
            iteration=3,
            template="docs/templates/prompt/planner.md",
            body=_planner_body(3),
        )
        return
    _append(
        journal,
        f"\n## Review {iteration}\nIndependent verification passed.\n"
        "STOPPED : REVIEWER\nACTIVATING : REVIEWER\nHANDOFF : PENDING_COMMIT\n",
    )
    _write_next(
        repo,
        source="REVIEWER",
        target="REVIEWER",
        handoff="PENDING_COMMIT",
        iteration=iteration,
        template="docs/templates/prompt/reviewer-closeout.md",
        body=_closeout_body(iteration),
        gate="APPROVED: COMMIT",
    )


def _closeout(repo: Path, iteration: int) -> None:
    reviewer = repo / ".agents/task/reviewer.md"
    _append(
        reviewer, f"\n### Commit Authorization — Review {iteration}\nAPPROVED: COMMIT\n"
    )
    branch = _git(repo, "branch", "--show-current")
    _git(repo, "add", "demo.txt")
    _git(repo, "commit", "--no-verify", "-m", "self-test task")
    for name in ("planner.md", "executor.md", "reviewer.md", "next-agent.md"):
        (repo / ".agents/task" / name).write_bytes(b"")
    if _git(repo, "status", "--porcelain"):
        raise RuntimeError("Self-test task branch is dirty after coordination cleanup.")
    _git(repo, "checkout", "main")
    _git(repo, "merge", "--ff-only", branch)
    _git(repo, "branch", "-d", branch)
    print("STOPPED : REVIEWER\nACTIVATING : NONE\nHANDOFF : ACCEPTED")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--role", choices=("planner", "executor", "reviewer"), required=True
    )
    parser.add_argument("--repo", required=True)
    parser.add_argument("pointer", nargs="?", default="")
    args = parser.parse_args()
    match = POINTER_RE.search(args.pointer)
    if not match:
        print("missing prompt pointer", file=sys.stderr)
        return 3
    prompt = Path(match.group(1).strip()).read_text(encoding="utf-8")
    incoming = _parse_front_matter(prompt)
    iteration = _iteration(prompt)
    repo = Path(args.repo)
    if args.role == "planner":
        _planner(repo, iteration)
    elif args.role == "executor":
        _executor(repo, iteration)
    else:
        _reviewer(repo, iteration, incoming)
    return 0


if __name__ == "__main__":
    sys.exit(main())
