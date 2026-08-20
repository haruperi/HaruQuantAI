"""Unit tests for generated README feature registry verifier.

Traces to: P16-T04, Gate G16
"""

from __future__ import annotations

from pathlib import Path

from scripts.architecture.generate_feature_registries import (
    check_or_write_registries,
)

_REPO_ROOT = Path(__file__).resolve().parents[2]


def test_readme_registries_pass_check() -> None:
    """Verify all current domain package READMEs satisfy registry checks."""
    exit_code = check_or_write_registries(_REPO_ROOT, write=False)
    assert exit_code == 0


def test_stale_detection_on_tampered_readme(tmp_path: Path) -> None:
    """Verify check detects malformed / duplicate registry sections."""
    app_dir = tmp_path / "app" / "services" / "test_dom"
    app_dir.mkdir(parents=True)
    readme = app_dir / "README.md"
    readme.write_text(
        "### Feature Registry\none\n### Feature Registry\ntwo\n",
        encoding="utf-8",
    )

    exit_code = check_or_write_registries(tmp_path, write=False)
    assert exit_code == 1
