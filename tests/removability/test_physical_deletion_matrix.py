"""Unit tests for physical provider deletion runner and guardrails.

Traces to: P11-T02, Gate G11
"""

from __future__ import annotations

from pathlib import Path

import pytest
from scripts.architecture.provider_deletion_matrix import (
    execute_deletion_test,
    setup_isolated_tree,
    validate_delete_target,
)

_REPO_ROOT = Path(__file__).resolve().parents[2]


def test_reject_source_target() -> None:
    """Verify target validation refuses to operate on source repository root."""
    with pytest.raises(ValueError, match="Refusing to operate on real repository root"):
        validate_delete_target(
            _REPO_ROOT,
            _REPO_ROOT,
            _REPO_ROOT / "app" / "services" / "data",
        )


def test_reject_escaped_path(tmp_path: Path) -> None:
    """Verify target validation refuses paths escaping isolated copy."""
    isolated = tmp_path / "isolated"
    isolated.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()

    with pytest.raises(ValueError, match="escapes isolated root"):
        validate_delete_target(_REPO_ROOT, isolated, outside)


def test_reject_non_app_path(tmp_path: Path) -> None:
    """Verify target validation refuses paths not inside app/ directory."""
    isolated = tmp_path / "isolated"
    tests_dir = isolated / "tests"
    tests_dir.mkdir(parents=True)

    with pytest.raises(ValueError, match="not inside isolated app/ directory"):
        validate_delete_target(_REPO_ROOT, isolated, tests_dir)


def test_delete_pilot_fresh_modules(tmp_path: Path) -> None:
    """Verify physical deletion of pilot provider succeeds in fresh isolated process."""
    isolated = tmp_path / "isolated"
    setup_isolated_tree(_REPO_ROOT, isolated)

    res = execute_deletion_test(
        repo_root=_REPO_ROOT,
        isolated_root=isolated,
        provider_id="indicator.rsi.default",
        reinstall=False,
    )
    assert res["passed"] is True, f"Deletion failed: {res.get('stderr')}"
    assert res["stage"] == "deletion"
