"""Tests for conservative DT-09 delivery batches."""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest


def _packet(feature: str, task: str, *, paths: list[str] | None = None) -> dict:
    return {
        "identity": {"feature_id": feature, "task_id": task, "baseline_commit": "abc"},
        "status": "EXECUTOR_READY",
        "unresolved_decisions": [],
        "risk": {"tier": "STANDARD"},
        "authorized_write_paths": paths or [f"app/{feature.lower()}"],
        "dependencies": {"schedule_constraints": []},
    }


def test_preparation_keeps_feature_authority_separate() -> None:
    batches = __import__("delivery_batch")
    result = batches.prepare_batch(
        batch_id="batch-1",
        baseline="abc",
        packets=[_packet("FEAT-A", "1.1"), _packet("FEAT-B", "1.2")],
    )
    assert result["status"] == "PREPARED"
    assert result["feature_ids"] == ["FEAT-A", "FEAT-B"]
    assert result["independent_task_acceptance_required"] is True


@pytest.mark.parametrize("count", [1, 4])
def test_preparation_requires_two_or_three_members(count: int) -> None:
    batches = __import__("delivery_batch")
    with pytest.raises(batches.DeliveryBatchError, match="two or three"):
        batches.prepare_batch(
            batch_id="bad",
            baseline="abc",
            packets=[_packet(f"F-{n}", str(n)) for n in range(count)],
        )


def test_preparation_rejects_critical_and_path_collision() -> None:
    batches = __import__("delivery_batch")
    critical = _packet("FEAT-A", "1.1")
    critical["risk"]["tier"] = "CRITICAL"
    with pytest.raises(batches.DeliveryBatchError, match="Critical"):
        batches.prepare_batch(
            batch_id="bad", baseline="abc", packets=[critical, _packet("FEAT-B", "1.2")]
        )
    with pytest.raises(batches.DeliveryBatchError, match="collision"):
        batches.prepare_batch(
            batch_id="bad",
            baseline="abc",
            packets=[
                _packet("FEAT-A", "1.1", paths=["same"]),
                _packet("FEAT-B", "1.2", paths=["same"]),
            ],
        )


def test_preparation_rejects_internal_unaccepted_predecessor() -> None:
    batches = __import__("delivery_batch")
    dependent = _packet("FEAT-B", "1.2")
    dependent["dependencies"]["schedule_constraints"] = [{"predecessor": "1.1"}]
    with pytest.raises(batches.DeliveryBatchError, match="unaccepted member"):
        batches.prepare_batch(
            batch_id="bad",
            baseline="abc",
            packets=[_packet("FEAT-A", "1.1"), dependent],
        )


def test_qualification_requires_each_acceptance_and_receipt(tmp_path: Path) -> None:
    batches = __import__("delivery_batch")
    prepared = batches.prepare_batch(
        batch_id="batch-1",
        baseline="abc",
        packets=[_packet("FEAT-A", "1.1"), _packet("FEAT-B", "1.2")],
    )
    receipt = tmp_path / "receipt.json"
    receipt.write_text(json.dumps({"candidate": "def"}), encoding="utf-8")
    result = batches.qualify_batch(
        prepared,
        accepted_children=[
            {
                "feature_id": "FEAT-A",
                "status": "ACCEPTED",
                "task_commit": "a",
                "merge_commit": "ma",
            },
            {
                "feature_id": "FEAT-B",
                "status": "ACCEPTED",
                "task_commit": "b",
                "merge_commit": "mb",
            },
        ],
        candidate="def",
        validation_receipt=receipt,
    )
    assert result["status"] == "PUSH_READY"
    assert result["push_performed"] is False


def test_combined_gate_runs_once_and_requires_passing_report(tmp_path: Path) -> None:
    batches = __import__("delivery_batch")
    calls: list[list[str]] = []

    def run(command: list[str], **_kwargs: object) -> SimpleNamespace:
        calls.append(command)
        report = Path(command[command.index("--report") + 1])
        report.parent.mkdir(parents=True, exist_ok=True)
        report.write_text(
            json.dumps(
                {
                    "explain_only": False,
                    "results": [{"step_id": "full", "exit_code": 0}],
                }
            ),
            encoding="utf-8",
        )
        return SimpleNamespace(returncode=0)

    def receipt_builder(**kwargs: object) -> str:
        receipt = Path(str(kwargs["receipt_path"]))
        receipt.write_text(
            '{"receipt_kind":"controller-validation-receipt"}', encoding="utf-8"
        )
        return "digest"

    report, elapsed = batches.run_combined_gate(
        tmp_path,
        {"batch_id": "b"},
        output_dir=tmp_path / "evidence",
        runner=run,
        receipt_builder=receipt_builder,
        fingerprint=lambda _repo: "candidate",
    )
    assert len(calls) == 1
    assert "full" in calls[0]
    assert report.is_file()
    assert elapsed >= 0
