#!/usr/bin/env python3
"""Scripted stub agents for orchestrator.py self-test.

Simulates the three roles' journal behavior without any real agent CLI.
Scenario: iteration 1 the Executor BLOCKS; iteration 2 implements the
blocker resolution but the Reviewer requests changes; iteration 3 the
Reviewer pauses at PENDING_COMMIT, the owner authorizes the commit, and the
close-out invocation accepts. The iteration number is parsed from the prompt
file that the orchestrator's "file" prompt delivery points at.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

POINTER_RE = re.compile(r"instructions in (.*?) exactly")
FINAL_ACCEPTED_ITERATION = 3
ITER_PATTERNS = {
    "planner": [
        re.compile(r"Iteration number\s*:\s*`?(\d+)"),
        re.compile(r"Approved dry-run number\s*:\s*`?(\d+)"),
    ],
    "executor": [re.compile(r"Approved dry-run number\s*:\s*`?(\d+)")],
    "reviewer": [
        re.compile(r"Dry-run number to review\s*:\s*`?(\d+)"),
        re.compile(r"Review number\s*:\s*`?(\d+)"),  # close-out template
    ],
}


def append(journal: Path, text: str) -> None:
    """Append text to a journal, preserving newline separation."""
    existing = journal.read_text(encoding="utf-8") if journal.exists() else ""
    if existing and not existing.endswith("\n"):
        existing += "\n"
    journal.write_text(existing + text, encoding="utf-8")


def _planner_behavior(journal: Path, mode: str, iteration: int) -> None:
    """Write the scripted Planner journal entry for this invocation."""
    if mode == "approval":
        append(
            journal,
            (
                f"\n### Approval Record - Dry Run {iteration}\n"
                f"`APPROVED: EXECUTE` (approved dry-run {iteration})\n"
                "NEXT AGENT NOTES : approval recorded; executor must "
                "verify the baseline\n"
                "STOPPED : PLANNER\nACTIVATING : EXECUTOR\n"
                "HANDOFF : APPROVED_EXECUTE\n"
            ),
        )
    else:
        append(
            journal,
            (
                f"\n## Dry Run {iteration}\n(eight-part dry run body)\n"
                f"NEXT AGENT NOTES : dry run {iteration} appended; cite "
                "the main baseline\n"
                "STOPPED : PLANNER\nACTIVATING : PLANNER\n"
                "HANDOFF : PENDING_APPROVAL\n"
            ),
        )


def _executor_behavior(journal: Path, iteration: int) -> None:
    """Write the scripted Executor journal entry for this invocation."""
    if iteration == 1:
        append(
            journal,
            (
                f"\n## Report {iteration}\n(blocked: missing upstream dependency)\n"
                "NEXT AGENT NOTES : blocked on upstream contract; scope only "
                "the blocker fix\n"
                "STOPPED : EXECUTOR\nACTIVATING : PLANNER\n"
                "HANDOFF : BLOCKED\n"
            ),
        )
    else:
        append(
            journal,
            (
                f"\n## Report {iteration}\n(files changed; evidence)\n"
                f"NEXT AGENT NOTES : Report {iteration} evidence table lists "
                "every changed file\n"
                "STOPPED : EXECUTOR\nACTIVATING : REVIEWER\n"
                "HANDOFF : READY_FOR_REVIEW\n"
            ),
        )


def _reviewer_behavior(journal: Path, mode: str, iteration: int) -> None:
    """Write the scripted Reviewer journal entry for this invocation."""
    if mode == "commit":
        append(
            journal,
            (
                f"\n### Commit Authorization - Review {iteration}\n"
                f"`APPROVED: COMMIT`\n"
                "(close-out: journals emptied, commit, ff-only merge, "
                "branch deleted)\n"
                "STOPPED : REVIEWER\nACTIVATING : NONE\nHANDOFF : ACCEPTED\n"
            ),
        )
        print("STOPPED : REVIEWER\nACTIVATING : NONE\nHANDOFF : ACCEPTED")
        return
    verdict = (
        "CHANGES_REQUESTED"
        if iteration < FINAL_ACCEPTED_ITERATION
        else "PENDING_COMMIT"
    )
    activating = "PLANNER" if verdict == "CHANGES_REQUESTED" else "REVIEWER"
    notes = (
        "NEXT AGENT NOTES : fix contract parity before continuing the original scope\n"
        if verdict == "CHANGES_REQUESTED"
        else "NEXT AGENT NOTES : verification passed; awaiting commit authorization\n"
    )
    append(
        journal,
        (
            f"\n## Review {iteration}\n(evidence)\n{notes}"
            f"STOPPED : REVIEWER\nACTIVATING : {activating}\n"
            f"HANDOFF : {verdict}\n"
        ),
    )


def _find_iteration(prompt: str, role: str) -> int | None:
    """Return the iteration number parsed from the prompt for the role."""
    for pattern in ITER_PATTERNS[role]:
        it_match = pattern.search(prompt)
        if it_match:
            return int(it_match.group(1))
    return None


def main() -> int:
    """Run the stub agent for the requested role and iteration.

    Returns:
        Exit code for the stub process: 0 on success, 3 when the prompt does not
        contain a parseable iteration field.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--role", required=True, choices=("planner", "executor", "reviewer")
    )
    parser.add_argument("--journal", required=True)
    parser.add_argument("--mode", default="initial")  # initial | approval | commit
    parser.add_argument("pointer", nargs="?", default="")
    args = parser.parse_args()

    journal = Path(args.journal)
    match = POINTER_RE.search(args.pointer)
    if not match:
        print("stub: no prompt pointer found in argv", file=sys.stderr)
        return 3
    prompt = Path(match.group(1).strip()).read_text(encoding="utf-8")
    iteration = _find_iteration(prompt, args.role)
    if iteration is None:
        print(
            f"stub: no iteration field in prompt for role {args.role}",
            file=sys.stderr,
        )
        return 3

    if args.role == "planner":
        _planner_behavior(journal, args.mode, iteration)
    elif args.role == "executor":
        _executor_behavior(journal, iteration)
    else:
        _reviewer_behavior(journal, args.mode, iteration)

    print(f"stub {args.role} mode={args.mode} iteration={iteration} -> journal updated")
    return 0


if __name__ == "__main__":
    sys.exit(main())
