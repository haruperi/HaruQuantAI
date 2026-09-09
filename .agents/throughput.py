#!/usr/bin/env python3
"""Canonical throughput summaries for accepted Task and Goal evidence."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import itertools
import json
import statistics
from pathlib import Path
from typing import Any, Final, cast

SUMMARY_SCHEMA_VERSION: Final[int] = 1
STAGE_PHASES: Final[dict[str, frozenset[str]]] = {
    "planning": frozenset({"planner", "task_activation", "task_branch_created"}),
    "execution": frozenset({"executor", "executor_handoff_correction_materialized"}),
    "review": frozenset({"reviewer", "reviewer_handoff_correction_materialized"}),
    "closeout": frozenset({"closeout"}),
}


class ThroughputError(RuntimeError):
    """Raised when timing or adoption evidence is malformed."""


def _instant(value: str) -> dt.datetime:
    """Parse one UTC history timestamp."""
    try:
        parsed = dt.datetime.fromisoformat(value)
    except ValueError as exc:
        raise ThroughputError(f"Invalid history timestamp: {value!r}") from exc
    if parsed.tzinfo is None:
        raise ThroughputError("History timestamps must include a UTC offset.")
    return parsed


def stage_durations(history: list[dict[str, Any]]) -> dict[str, float]:
    """Derive nonoverlapping stage time from consecutive controller events."""
    totals = dict.fromkeys(STAGE_PHASES, 0.0)
    ordered = [item for item in history if item.get("time") and item.get("phase")]
    has_explicit_roles = any(
        item.get("phase") in {"ide_role_completed", "headless_role_completed"}
        for item in ordered
    )
    for current, following in itertools.pairwise(ordered):
        elapsed = max(
            0.0,
            (
                _instant(str(following["time"])) - _instant(str(current["time"]))
            ).total_seconds(),
        )
        phase = str(current["phase"])
        if phase in {"ide_role_completed", "headless_role_completed"}:
            role_stage = {
                "PLANNER": "planning",
                "EXECUTOR": "execution",
                "REVIEWER": "review",
            }.get(str(current.get("role", "")))
            if role_stage:
                totals[role_stage] += float(current.get("duration_seconds", elapsed))
                continue
        for stage, phases in STAGE_PHASES.items():
            if phase in phases:
                if has_explicit_roles and phase in {"planner", "executor", "reviewer"}:
                    break
                totals[stage] += float(current.get("duration_seconds", elapsed))
                break
    return totals


def build_task_summary(state: dict[str, Any]) -> dict[str, Any]:
    """Build the stable DT-10 summary without inventing unavailable usage data."""
    raw_task = state.get("task")
    task = cast("dict[str, Any]", raw_task) if isinstance(raw_task, dict) else {}
    raw_packet = state.get("task_packet")
    packet = cast("dict[str, Any]", raw_packet) if isinstance(raw_packet, dict) else {}
    raw_risk = packet.get("risk")
    risk = cast("dict[str, Any]", raw_risk) if isinstance(raw_risk, dict) else {}
    raw_history = state.get("history")
    history = (
        cast("list[dict[str, Any]]", raw_history)
        if isinstance(raw_history, list)
        else []
    )
    durations = stage_durations(history)
    paths = [str(value) for value in state.get("approved_write_paths", [])]
    pilot_classes = [
        "UI_INTERACTION"
        if any(path.startswith("app/ui/") for path in paths)
        else "ORDINARY_SERVICE"
    ]
    if str(risk.get("tier") or state.get("risk_tier")) == "CRITICAL":
        pilot_classes.append("CRITICAL")
    correction_events = [
        item
        for item in history
        if "correction" in str(item.get("phase", "")).lower()
        or str(item.get("handoff", "")) in {"BLOCKED", "CHANGES_REQUESTED"}
    ]
    command_wall = sum(
        float(item.get("duration_seconds", 0.0))
        for item in state.get("validation_commands", [])
        if isinstance(item, dict)
    )
    integration = state.get("integration_validation")
    if isinstance(integration, dict):
        report_path = Path(str(integration.get("report_path", "")))
        if report_path.is_file():
            report = json.loads(report_path.read_text(encoding="utf-8"))
            command_wall += sum(
                float(item.get("duration_seconds", 0.0))
                for item in report.get("results", [])
                if isinstance(item, dict)
            )
    return {
        "schema_version": SUMMARY_SCHEMA_VERSION,
        "task_or_batch_id": str(state.get("run_id", "")),
        "feature_ids": [str(task.get("task_id", ""))] if task.get("task_id") else [],
        "risk_tier": str(risk.get("tier") or state.get("risk_tier") or "UNKNOWN"),
        "pilot_classes": pilot_classes,
        "parallelism": int(state.get("parallelism", 1)),
        "comparable_scope": state.get("comparable_scope"),
        "accepted_throughput_per_hour": state.get("accepted_throughput_per_hour"),
        "baseline": state.get("baseline"),
        "candidate": state.get("accepted_head") or state.get("reviewed_head"),
        "planning_elapsed": durations["planning"],
        "execution_elapsed": durations["execution"],
        "review_elapsed": durations["review"],
        "closeout_elapsed": durations["closeout"],
        "command_wall_time": command_wall,
        "integration_wait": float(state.get("integration_wait_seconds", 0.0)),
        "correction_count": len(correction_events),
        "correction_causes": [
            str(item.get("handoff") or item.get("phase")) for item in correction_events
        ],
        "acceptance_result": state.get("status"),
        "escaped_regression_or_reopen": bool(
            state.get("escaped_regression_or_reopen", False)
        ),
        "provider_reported_usage_if_available": state.get("provider_reported_usage"),
        "allowance_before": state.get("allowance_before"),
        "allowance_after": state.get("allowance_after"),
        "other_concurrent_usage_known": state.get("other_concurrent_usage_known"),
    }


def write_summary(path: Path, summary: dict[str, Any]) -> str:
    """Write canonical summary bytes and return their digest."""
    raw = json.dumps(summary, indent=2, sort_keys=True) + "\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(raw, encoding="utf-8", newline="\n")
    return hashlib.sha256(raw.encode()).hexdigest()


def adoption_decision(summaries: list[dict[str, Any]]) -> dict[str, Any]:
    """Return a conservative lane recommendation from ten accepted outcomes."""
    accepted = [
        item for item in summaries if item.get("acceptance_result") == "ACCEPTED"
    ]
    if len(accepted) < 10:
        return {
            "decision": "INSUFFICIENT_EVIDENCE",
            "accepted_results": len(accepted),
            "required_results": 10,
        }
    classes = {
        str(value) for item in accepted[-10:] for value in item.get("pilot_classes", [])
    }
    required_classes = {"UI_INTERACTION", "ORDINARY_SERVICE", "CRITICAL"}
    if not required_classes.issubset(classes):
        return {
            "decision": "INSUFFICIENT_EVIDENCE",
            "accepted_results": 10,
            "missing_pilot_classes": sorted(required_classes - classes),
        }
    if any(item.get("escaped_regression_or_reopen") for item in accepted[-10:]):
        return {"decision": "KEEP_SEQUENTIAL", "reason": "escaped regression or reopen"}
    window = accepted[-10:]
    comparable = [
        item
        for item in window
        if item.get("comparable_scope") is True
        and isinstance(item.get("accepted_throughput_per_hour"), int | float)
    ]
    modes = {int(item.get("parallelism", 1)) for item in comparable}
    if len(comparable) != 10 or 1 not in modes or not modes.intersection({2, 3}):
        return {
            "decision": "INSUFFICIENT_EVIDENCE",
            "accepted_results": 10,
            "reason": "Comparable sequential and parallel throughput is required.",
        }
    medians = {
        mode: statistics.median(
            float(item["accepted_throughput_per_hour"])
            for item in comparable
            if int(item.get("parallelism", 1)) == mode
        )
        for mode in modes
    }
    candidates = [mode for mode in (3, 2) if medians.get(mode, 0.0) > medians[1]]
    decision = f"ADOPT_{candidates[0]}" if candidates else "KEEP_SEQUENTIAL"
    return {"decision": decision, "accepted_results": 10, "median_throughput": medians}


def load_recent_summaries(root: Path, limit: int = 10) -> list[dict[str, Any]]:
    """Load the newest bounded run summaries."""
    if limit < 1 or limit > 100:
        raise ThroughputError("Summary limit must be between 1 and 100.")
    paths = sorted(root.glob("*/throughput-summary.json"), reverse=True)[:limit]
    return [json.loads(path.read_text(encoding="utf-8")) for path in paths]


def main() -> int:
    """Write one compact bounded adoption report.

    Returns:
        Zero after writing a diagnostic recommendation.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runs-dir", type=Path, default=Path(".agents/runs"))
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--limit", type=int, default=10)
    args = parser.parse_args()
    summaries = load_recent_summaries(args.runs_dir, args.limit)
    report = {
        "schema_version": SUMMARY_SCHEMA_VERSION,
        "result_count": len(summaries),
        "summaries": summaries,
        "adoption": adoption_decision(summaries),
    }
    write_summary(args.report, report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
