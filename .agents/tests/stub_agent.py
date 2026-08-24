#!/usr/bin/env python3
"""Scripted stub agents for orchestrator.py self-test.

Simulates the three roles' journal behavior without any real agent CLI.
Scenario: iteration 1 the Executor BLOCKS; iteration 2 implements the
blocker resolution but the Reviewer requests changes; iteration 3 is
accepted. The iteration number is parsed from the prompt file that the
orchestrator's "file" prompt delivery points at.
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
    "reviewer": [re.compile(r"Dry-run number to review\s*:\s*`?(\d+)")],
}


def append(journal: Path, text: str) -> None:
    """Append text to a journal, preserving newline separation."""
    existing = journal.read_text(encoding="utf-8") if journal.exists() else ""
    if existing and not existing.endswith("\n"):
        existing += "\n"
    journal.write_text(existing + text, encoding="utf-8")


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
    parser.add_argument("--mode", default="initial")  # initial | approval
    parser.add_argument("pointer", nargs="?", default="")
    args = parser.parse_args()

    journal = Path(args.journal)
    match = POINTER_RE.search(args.pointer)
    if not match:
        print("stub: no prompt pointer found in argv", file=sys.stderr)
        return 3
    prompt = Path(match.group(1).strip()).read_text(encoding="utf-8")
    iteration = None
    for pattern in ITER_PATTERNS[args.role]:
        it_match = pattern.search(prompt)
        if it_match:
            iteration = int(it_match.group(1))
            break
    if iteration is None:
        print(
            f"stub: no iteration field in prompt for role {args.role}",
            file=sys.stderr,
        )
        return 3

    if args.role == "planner":
        if args.mode == "approval":
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
    elif args.role == "executor":
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
    else:  # reviewer
        verdict = (
            "CHANGES_REQUESTED" if iteration < FINAL_ACCEPTED_ITERATION else "ACCEPTED"
        )
        closeout = (
            "\n(close-out: journals emptied, commit, ff-only merge, branch deleted)"
            if verdict == "ACCEPTED"
            else ""
        )
        activating = "PLANNER" if verdict == "CHANGES_REQUESTED" else "NONE"
        notes = (
            "NEXT AGENT NOTES : fix contract parity before continuing the "
            "original scope\n"
            if verdict == "CHANGES_REQUESTED"
            else ""
        )
        append(
            journal,
            (
                f"\n## Review {iteration}\n(evidence){closeout}\n{notes}"
                f"STOPPED : REVIEWER\nACTIVATING : {activating}\n"
                f"HANDOFF : {verdict}\n"
            ),
        )

    print(f"stub {args.role} mode={args.mode} iteration={iteration} -> journal updated")
    return 0


if __name__ == "__main__":
    sys.exit(main())
