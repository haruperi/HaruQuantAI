"""Tests for source-bound controller validation receipts."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

MODULE_PATH = Path(__file__).resolve().parents[1] / "validation_receipts.py"
sys.path.insert(0, str(MODULE_PATH.parent))
SPEC = importlib.util.spec_from_file_location("hq_validation_receipts", MODULE_PATH)
assert SPEC
assert SPEC.loader
receipts = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = receipts
SPEC.loader.exec_module(receipts)


def _diagnostic(tmp_path: Path) -> Path:
    log = tmp_path / "step.log"
    log.write_text("passed\n", encoding="utf-8")
    report = {
        "schema_version": 1,
        "report_kind": "diagnostic-not-reusable-validation-receipt",
        "decision": {
            "requested_profile": "affected",
            "selected_families": ["documentation"],
            "changed_paths": ["changed.txt"],
            "python_test_paths": [],
            "ui_test_paths": [],
            "reasons": ["test"],
            "candidate": {"base_commit": "base", "head_commit": "head"},
        },
        "steps": [{"step_id": "one", "command": ["check"]}],
        "results": [
            {
                "step_id": "one",
                "exit_code": 0,
                "log_path": str(log),
                "log_sha256": receipts._sha_file(log),
            }
        ],
    }
    path = tmp_path / "diagnostic.json"
    path.write_text(json.dumps(report), encoding="utf-8")
    return path


def test_receipt_reuses_exact_unchanged_inputs(tmp_path: Path) -> None:
    """Controller evidence remains reusable for the exact same candidate."""
    (tmp_path / "changed.txt").write_text("same\n", encoding="utf-8")
    diagnostic = _diagnostic(tmp_path)
    receipt = tmp_path / "receipt.json"
    digest = receipts.create_validation_receipt(
        repo=tmp_path,
        diagnostic_path=diagnostic,
        receipt_path=receipt,
        worktree_sha256="tree",
        authority_sha256="authority",
    )

    value = receipts.verify_validation_receipt(
        repo=tmp_path,
        receipt_path=receipt,
        expected_receipt_sha256=digest,
        expected_worktree_sha256="tree",
        expected_authority_sha256="authority",
    )

    assert value["producer"] == "haruquant-workflow-controller"


def test_changed_input_rejects_receipt(tmp_path: Path) -> None:
    """Any relevant input change invalidates previous execution evidence."""
    changed = tmp_path / "changed.txt"
    changed.write_text("before\n", encoding="utf-8")
    diagnostic = _diagnostic(tmp_path)
    receipt = tmp_path / "receipt.json"
    digest = receipts.create_validation_receipt(
        repo=tmp_path,
        diagnostic_path=diagnostic,
        receipt_path=receipt,
        worktree_sha256="tree",
        authority_sha256="authority",
    )
    changed.write_text("after\n", encoding="utf-8")

    with pytest.raises(receipts.ValidationReceiptError, match="input changed"):
        receipts.verify_validation_receipt(
            repo=tmp_path,
            receipt_path=receipt,
            expected_receipt_sha256=digest,
            expected_worktree_sha256="tree",
            expected_authority_sha256="authority",
        )


def test_edited_or_forged_receipt_is_rejected(tmp_path: Path) -> None:
    """Agent-authored receipt bytes cannot replace controller state identity."""
    (tmp_path / "changed.txt").write_text("same\n", encoding="utf-8")
    diagnostic = _diagnostic(tmp_path)
    receipt = tmp_path / "receipt.json"
    digest = receipts.create_validation_receipt(
        repo=tmp_path,
        diagnostic_path=diagnostic,
        receipt_path=receipt,
        worktree_sha256="tree",
        authority_sha256="authority",
    )
    receipt.write_text(receipt.read_text(encoding="utf-8") + " ", encoding="utf-8")

    with pytest.raises(receipts.ValidationReceiptError, match="missing or edited"):
        receipts.verify_validation_receipt(
            repo=tmp_path,
            receipt_path=receipt,
            expected_receipt_sha256=digest,
            expected_worktree_sha256="tree",
            expected_authority_sha256="authority",
        )
