#!/usr/bin/env python3
"""Reusable Task-run API layered over the existing HaruQuantAI Task engine."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
from workflow_engine import *


def create_task_state(
    task: dict[str, Any],
    baseline: str,
    *,
    run_id: str | None = None,
) -> dict[str, Any]:
    """Create the canonical initial state for one atomic Task workflow run."""
    missing = [key for key in TASK_REQUIRED if not task.get(key)]
    if missing:
        raise OrchestratorError(f"Missing task fields: {missing}")
    task_slug = str(task["task_slug"])
    if not SLUG_RE.fullmatch(task_slug):
        raise OrchestratorError("task_slug must be lowercase filesystem-safe text.")
    if run_id is None:
        stamp = dt.datetime.now(tz=dt.UTC).strftime("%Y%m%d-%H%M%S")
        run_id = f"{stamp}-{task_slug}"
    return {
        "run_id": run_id,
        "task": task,
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


def prepare_task_run(
    cfg: dict[str, Any],
    task: dict[str, Any],
    *,
    run_id: str | None = None,
) -> dict[str, Any]:
    """Pass the clean-main entry gate, create Task state, and persist it."""
    baseline = _entry_gate(cfg)
    state = create_task_state(task, baseline, run_id=run_id)
    _save_state(cfg, state)
    return state


def resume_task_run(
    cfg: dict[str, Any],
    state: dict[str, Any],
    *,
    auto_approve: bool = False,
    approved: bool = False,
    reject_feedback: str | None = None,
    commit_approved: bool = False,
    commit_reject_feedback: str | None = None,
) -> dict[str, Any]:
    """Run the existing Task state machine without changing its semantics."""
    return router(
        cfg,
        state,
        auto_approve=auto_approve,
        approved=approved,
        reject_feedback=reject_feedback,
        commit_approved=commit_approved,
        commit_reject_feedback=commit_reject_feedback,
    )


def apply_planner_blocker_resolution(
    cfg: dict[str, Any], state: dict[str, Any], evidence: str
) -> None:
    """Record owner evidence that resolves the active Planner blocker."""
    if state.get("phase") != "planner_blocked":
        raise OrchestratorError(
            "Planner blocker resolution is valid only while the Task is planner_blocked."
        )
    if not evidence.strip():
        raise OrchestratorError("Planner blocker resolution evidence must not be empty.")
    state["blocker_resolution"] = {
        "evidence": evidence.strip(),
        "resolved_at": dt.datetime.now(tz=dt.UTC).isoformat(timespec="seconds"),
    }
    _save_state(cfg, state)


__all__ = [name for name in globals() if not name.startswith("__")]
