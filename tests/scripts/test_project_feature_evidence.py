"""Tests for reviewed current-evidence projection."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts import project_feature_evidence as projector


def _packet() -> dict[str, object]:
    return {
        "identity": {"task_id": "1.99", "feature_id": "FEAT-DEMO"},
        "requirements": [{"requirement_id": "FR-DEMO-001"}],
        "local_nfrs": [{"requirement_id": "NFR-DEMO-001"}],
    }


def _draft() -> dict[str, object]:
    return {
        "feature_id": "FEAT-DEMO",
        "task_id": "1.99",
        "status": "IN_PROGRESS",
        "owner_specification": "app/services/demo/README.md",
        "baseline_commit": "b" * 40,
        "acceptance_commit": "task-closeout:pending",
        "requirements": [
            {
                "id": "FR-DEMO-001",
                "status": "PASS",
                "evidence_target": "tests/demo.py::test_behavior",
            },
            {
                "id": "NFR-DEMO-001",
                "status": "PASS",
                "evidence_target": "tests/demo.py::test_lifecycle",
            },
        ],
        "commands": [{"command": "pytest selected", "exit_code": 0}],
        "catalogue_entries": [],
        "stages": {
            name: {"status": "PASS", "evidence": "explicit evidence"}
            for name in (
                "contract",
                "provider",
                "composition",
                "interfaces",
                "ui",
                "end_to_end",
            )
        },
        "review": {"reviewer_verdict": "PENDING", "reviewer_notes": "pending"},
    }


def _receipt() -> dict[str, object]:
    return {
        "receipt_kind": "controller-validation-receipt",
        "producer": "haruquant-workflow-controller",
        "results": [{"step_id": "selected", "exit_code": 0}],
    }


def test_current_projection_inventory_excludes_pinned_snapshots() -> None:
    """The mutable projector can never publish Phase-0 source snapshots."""
    payloads = projector.current_projection_payloads()

    assert tuple(payloads) == projector.CURRENT_PROJECTION_PATHS
    assert all("/source/" not in path for path in payloads)
    assert "docs/dev/evidence/baseline-manifest.json" not in payloads


def test_failed_requirement_cannot_be_projected_as_accepted() -> None:
    """Explicit failed evidence prevents deterministic completion."""
    draft = _draft()
    draft["requirements"][0]["status"] = "FAIL"  # type: ignore[index]

    with pytest.raises(projector.ProjectionError, match="lacks passing"):
        projector._final_acceptance(
            _packet(),
            draft,
            "STOPPED : REVIEWER\nHANDOFF : PENDING_COMMIT\n",
            _receipt(),
            run_id="run-demo",
            receipt_sha256="a" * 64,
        )


def test_projection_requires_actual_reviewer_handoff() -> None:
    """Passing commands alone cannot manufacture Reviewer approval."""
    with pytest.raises(projector.ProjectionError, match="PENDING_COMMIT"):
        projector._final_acceptance(
            _packet(),
            _draft(),
            "HANDOFF : READY_FOR_REVIEW\n",
            _receipt(),
            run_id="run-demo",
            receipt_sha256="a" * 64,
        )


def test_empty_command_evidence_cannot_finalize_acceptance() -> None:
    """A passing receipt does not excuse an empty feature acceptance record."""
    draft = _draft()
    draft["commands"] = []

    with pytest.raises(projector.ProjectionError, match="commands"):
        projector._final_acceptance(
            _packet(),
            draft,
            "STOPPED : REVIEWER\nHANDOFF : PENDING_COMMIT\n",
            _receipt(),
            run_id="run-demo",
            receipt_sha256="a" * 64,
        )


def test_apply_is_exact_and_idempotent(tmp_path: Path) -> None:
    """Applying identical reviewed output twice changes no bytes."""
    outputs = {
        "docs/a.json": b'{"stable": true}\n',
        "docs/nested/b.txt": b"same\n",
    }

    projector.apply_outputs(outputs, repo=tmp_path)
    first = {path: (tmp_path / path).read_bytes() for path in outputs}
    projector.apply_outputs(outputs, repo=tmp_path)

    assert projector.check_outputs(outputs, repo=tmp_path) == []
    assert {path: (tmp_path / path).read_bytes() for path in outputs} == first


def test_final_projection_updates_only_exact_task_card(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A reviewed request updates its exact acceptance and tracker card."""
    plan = tmp_path / "docs/dev/Phased_Feature_Implementation_Plan.md"
    acceptance = tmp_path / "docs/dev/evidence/features/FEAT-DEMO/acceptance.json"
    packet = tmp_path / "packet.json"
    reviewer = tmp_path / "reviewer.md"
    receipt = tmp_path / "receipt.json"
    plan.parent.mkdir(parents=True)
    acceptance.parent.mkdir(parents=True)
    plan.write_text(
        "### - [ ] Task 1.99 — FEAT-DEMO — Demo\n"
        "**Status:** `NOT_STARTED`\n"
        "**Accepted commit:** Not recorded — this is a plan.\n",
        encoding="utf-8",
    )
    for path, value in (
        (packet, _packet()),
        (acceptance, _draft()),
        (receipt, _receipt()),
    ):
        path.write_text(json.dumps(value), encoding="utf-8")
    reviewer.write_text(
        "STOPPED : REVIEWER\nHANDOFF : PENDING_COMMIT\n", encoding="utf-8"
    )
    monkeypatch.setattr(
        projector,
        "current_projection_payloads",
        lambda **_kwargs: {"docs/dev/evidence/feature-baseline.json": b"{}\n"},
    )

    outputs = projector.build_feature_projection(
        packet_path=packet,
        acceptance_path=acceptance,
        reviewer_journal_path=reviewer,
        validation_receipt_path=receipt,
        run_id="run-demo",
        repo=tmp_path,
    )

    final = json.loads(outputs[acceptance.relative_to(tmp_path).as_posix()])
    updated_plan = outputs[plan.relative_to(tmp_path).as_posix()].decode()
    assert final["status"] == "ACCEPTED"
    assert final["review"]["reviewer_verdict"] == "APPROVED"
    assert "### - [x] Task 1.99" in updated_plan
    assert "**Status:** `COMPLETE`" in updated_plan
