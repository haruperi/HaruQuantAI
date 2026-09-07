"""Integration test for the complete Phase 0 evidence validator."""

from __future__ import annotations

from scripts import validate_phase0


def test_phase0_evidence_is_internally_consistent() -> None:
    """Checked-in Phase 0 evidence satisfies every deterministic readiness gate."""
    assert validate_phase0.validate() == []


def _task(task_id: str, feature_id: str, *, complete: bool) -> dict[str, object]:
    """Build one minimal parsed-task fixture."""
    return {"task_id": task_id, "feature_id": feature_id, "complete": complete}


def test_progress_allows_new_completions_without_rewriting_baseline() -> None:
    """A live tracker may advance beyond the frozen Phase 0 completion set."""
    baseline = [
        _task("1.01", "FEAT-A", complete=False),
        _task("1.02", "FEAT-B", complete=True),
    ]
    live = [
        _task("1.01", "FEAT-A", complete=True),
        _task("1.02", "FEAT-B", complete=True),
    ]
    assert validate_phase0._validate_task_progress(live, baseline) == []


def test_progress_rejects_completion_regression() -> None:
    """A Phase 0-complete task cannot become open in the live tracker."""
    baseline = [_task("1.01", "FEAT-A", complete=True)]
    live = [_task("1.01", "FEAT-A", complete=False)]
    assert validate_phase0._validate_task_progress(live, baseline) == [
        "live tracker regressed completed Phase 0 tasks: 1.01"
    ]


def test_progress_rejects_identity_or_order_drift() -> None:
    """Monotonic status updates cannot reorder or replace feature identities."""
    baseline = [
        _task("1.01", "FEAT-A", complete=False),
        _task("1.02", "FEAT-B", complete=False),
    ]
    live = list(reversed(baseline))
    assert validate_phase0._validate_task_progress(live, baseline) == [
        "live task identity/order differs from the Phase 0 baseline"
    ]


def test_acceptance_reference_supports_commit_or_closeout_receipt() -> None:
    """Acceptance references are exact SHAs or deterministic receipt identities."""
    assert validate_phase0._valid_acceptance_reference("a" * 40)
    assert validate_phase0._valid_acceptance_reference(
        "task-closeout:20260907-run-1.01-01"
    )


def test_acceptance_reference_rejects_malformed_or_missing_values() -> None:
    """Receipt labels cannot masquerade as arbitrary acceptance text."""
    assert not validate_phase0._valid_acceptance_reference(None)
    assert not validate_phase0._valid_acceptance_reference("pending")
    assert not validate_phase0._valid_acceptance_reference("task-closeout:")
