"""Tests for stable DT-10 throughput summaries."""

from __future__ import annotations


def test_stage_durations_are_nonoverlapping() -> None:
    throughput = __import__("throughput")
    history = [
        {"time": "2026-09-09T00:00:00+00:00", "phase": "planner"},
        {"time": "2026-09-09T00:00:02+00:00", "phase": "executor"},
        {"time": "2026-09-09T00:00:05+00:00", "phase": "reviewer"},
        {"time": "2026-09-09T00:00:09+00:00", "phase": "closeout"},
        {"time": "2026-09-09T00:00:10+00:00", "phase": "done"},
    ]
    assert throughput.stage_durations(history) == {
        "planning": 2.0,
        "execution": 3.0,
        "review": 4.0,
        "closeout": 1.0,
    }


def test_usage_fields_remain_nullable() -> None:
    throughput = __import__("throughput")
    summary = throughput.build_task_summary(
        {
            "run_id": "r",
            "task": {"task_id": "FEAT-A"},
            "history": [],
            "status": "ACCEPTED",
        }
    )
    assert summary["provider_reported_usage_if_available"] is None
    assert summary["allowance_before"] is None
    assert summary["allowance_after"] is None


def test_adoption_requires_ten_accepted_results() -> None:
    throughput = __import__("throughput")
    assert (
        throughput.adoption_decision([{"acceptance_result": "ACCEPTED"}] * 9)[
            "decision"
        ]
        == "INSUFFICIENT_EVIDENCE"
    )
    results = [
        {
            "acceptance_result": "ACCEPTED",
            "parallelism": 1 if index < 5 else 2,
            "pilot_classes": ["UI_INTERACTION", "ORDINARY_SERVICE", "CRITICAL"],
            "comparable_scope": True,
            "accepted_throughput_per_hour": 2.0 if index < 5 else 3.0,
        }
        for index in range(10)
    ]
    assert throughput.adoption_decision(results)["decision"] == "ADOPT_2"


def test_regression_forces_sequential_decision() -> None:
    throughput = __import__("throughput")
    results = [
        {
            "acceptance_result": "ACCEPTED",
            "parallelism": 3,
            "escaped_regression_or_reopen": index == 9,
            "pilot_classes": ["UI_INTERACTION", "ORDINARY_SERVICE", "CRITICAL"],
        }
        for index in range(10)
    ]
    assert throughput.adoption_decision(results)["decision"] == "KEEP_SEQUENTIAL"
