"""Unit tests for provider removability and safety evidence enforcer.

Traces to: P16-T03, Gate G16
"""

from __future__ import annotations

from pathlib import Path

from scripts.architecture.enforce_provider_evidence import (
    check_provider_evidence,
    run_evidence_check,
)

_REPO_ROOT = Path(__file__).resolve().parents[2]
_MATRIX_PATH = (
    _REPO_ROOT
    / "docs"
    / "dev"
    / "plugin-decoupling"
    / "audit"
    / "removability_matrix.json"
)


def test_missing_config_matrix_evidence_detected(tmp_path: Path) -> None:
    """Verify missing config disable matrix test triggers violation."""
    violations = check_provider_evidence({"providers": []}, tmp_path)
    assert any(
        v.code == "DELETION_EVIDENCE_MISSING"
        and "test_config_disable_matrix.py" in v.path
        for v in violations
    )


def test_missing_physical_deletion_evidence_detected(tmp_path: Path) -> None:
    """Verify missing physical deletion matrix test triggers violation."""
    violations = check_provider_evidence({"providers": []}, tmp_path)
    assert any(
        v.code == "DELETION_EVIDENCE_MISSING"
        and "test_physical_deletion_matrix.py" in v.path
        for v in violations
    )


def test_current_evidence_tree_passes() -> None:
    """Verify all required removability and safety evidence exists in current tree."""
    violations = run_evidence_check(_REPO_ROOT, _MATRIX_PATH)
    assert not violations, f"Evidence violations: {[v.format() for v in violations]}"
