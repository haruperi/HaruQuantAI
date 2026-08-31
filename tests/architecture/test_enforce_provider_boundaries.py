"""Unit tests for provider architecture boundary enforcement.

Traces to: P16-T01, Gate G16
"""

from __future__ import annotations

from pathlib import Path

from scripts.architecture.enforce_provider_boundaries import (
    check_file_ast,
    run_boundary_check,
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


def test_kernel_business_import_violation(tmp_path: Path) -> None:
    """Verify kernel file importing business domain triggers violation."""
    file_path = tmp_path / "app" / "kernel" / "bad.py"
    file_path.parent.mkdir(parents=True)
    file_path.write_text("import app.services.data\n", encoding="utf-8")

    violations = check_file_ast(file_path, tmp_path, set())
    assert len(violations) == 1
    assert violations[0].code == "KERNEL_BUSINESS_IMPORT"
    assert violations[0].target == "app.services.data"


def test_spec_provider_import_violation(tmp_path: Path) -> None:
    """Verify contract spec importing concrete provider triggers violation."""
    file_path = tmp_path / "app" / "contracts" / "bad.py"
    file_path.parent.mkdir(parents=True)
    file_path.write_text(
        "from app.services.data.providers import something\n", encoding="utf-8"
    )

    violations = check_file_ast(file_path, tmp_path, set())
    assert len(violations) == 1
    assert violations[0].code == "SPEC_PROVIDER_IMPORT"


def test_dynamic_import_not_allowlisted(tmp_path: Path) -> None:
    """Verify unallowlisted dynamic import triggers violation."""
    file_path = tmp_path / "app" / "services" / "data" / "bad.py"
    file_path.parent.mkdir(parents=True)
    file_path.write_text(
        "import importlib\nimportlib.import_module('unapproved_pkg')\n",
        encoding="utf-8",
    )

    violations = check_file_ast(file_path, tmp_path, {"approved_pkg"})
    assert len(violations) == 1
    assert violations[0].code == "DYNAMIC_IMPORT_NOT_ALLOWLISTED"
    assert violations[0].target == "unapproved_pkg"


def test_current_tree_has_zero_violations() -> None:
    """Verify current codebase has zero architecture boundary violations."""
    violations = run_boundary_check(_REPO_ROOT, _MATRIX_PATH)
    assert not violations, (
        f"Boundary violations found: {[v.format() for v in violations]}"
    )
