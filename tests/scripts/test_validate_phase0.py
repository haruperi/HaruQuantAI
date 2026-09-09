"""Integration test for the complete Phase 0 evidence validator."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts import validate_phase0


def test_phase0_evidence_is_internally_consistent() -> None:
    """Checked-in Phase 0 evidence satisfies every deterministic readiness gate."""
    assert validate_phase0.validate() == []


def test_strategy_ready_projection_is_part_of_phase_validation() -> None:
    """The frozen milestone cannot silently drift from its schedule."""
    errors = validate_phase0.validate()
    assert not [error for error in errors if "strategy-ready" in error]


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


def _accepted_task(
    evidence_path: Path,
    task_id: str,
    feature_id: str,
    *,
    acceptance_commit: str,
    baseline_commit: str,
) -> dict[str, object]:
    """Write one accepted manifest and return its parsed-task identity."""
    evidence_path.write_text(
        json.dumps(
            {
                "feature_id": feature_id,
                "task_id": task_id,
                "status": "ACCEPTED",
                "acceptance_commit": acceptance_commit,
                "baseline_commit": baseline_commit,
            }
        ),
        encoding="utf-8",
    )
    return {
        "feature_id": feature_id,
        "task_id": task_id,
        "evidence_path": evidence_path.name,
    }


def test_accepted_provider_commit_may_precede_later_listed_consumer(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Git-proved accepted delivery may supersede static tracker ordering."""
    provider_commit = "a" * 40
    consumer_baseline = "b" * 40
    provider = _accepted_task(
        tmp_path / "provider.json",
        "1.09",
        "FEAT-PROVIDER",
        acceptance_commit=provider_commit,
        baseline_commit="c" * 40,
    )
    consumer = _accepted_task(
        tmp_path / "consumer.json",
        "1.04",
        "FEAT-CONSUMER",
        acceptance_commit="task-closeout:consumer",
        baseline_commit=consumer_baseline,
    )
    monkeypatch.setattr(validate_phase0, "REPO", tmp_path)
    monkeypatch.setattr(
        validate_phase0,
        "_git_is_ancestor",
        lambda ancestor, descendant: (
            (ancestor, descendant) == (provider_commit, consumer_baseline)
        ),
    )

    assert validate_phase0._accepted_provider_precedes_consumer(provider, consumer)


@pytest.mark.parametrize(
    ("provider_status", "provider_commit", "is_ancestor"),
    [
        ("PENDING", "a" * 40, True),
        ("ACCEPTED", "task-closeout:provider", True),
        ("ACCEPTED", "a" * 40, False),
    ],
)
def test_later_provider_requires_exact_commit_and_proved_ancestry(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    provider_status: str,
    provider_commit: str,
    is_ancestor: bool,
) -> None:
    """Incomplete, receipt-only, or non-ancestral evidence fails closed."""
    provider = _accepted_task(
        tmp_path / "provider.json",
        "1.09",
        "FEAT-PROVIDER",
        acceptance_commit=provider_commit,
        baseline_commit="c" * 40,
    )
    payload = json.loads((tmp_path / "provider.json").read_text(encoding="utf-8"))
    payload["status"] = provider_status
    (tmp_path / "provider.json").write_text(json.dumps(payload), encoding="utf-8")
    consumer = _accepted_task(
        tmp_path / "consumer.json",
        "1.04",
        "FEAT-CONSUMER",
        acceptance_commit="task-closeout:consumer",
        baseline_commit="b" * 40,
    )
    monkeypatch.setattr(validate_phase0, "REPO", tmp_path)
    monkeypatch.setattr(
        validate_phase0, "_git_is_ancestor", lambda _ancestor, _descendant: is_ancestor
    )

    assert not validate_phase0._accepted_provider_precedes_consumer(provider, consumer)
