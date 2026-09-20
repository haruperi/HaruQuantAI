"""Tests for schema-bound repository evidence secret filters."""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path
from types import ModuleType
from typing import cast


def _load_secret_filters() -> ModuleType:
    """Load the standalone hook without turning scripts into a package."""
    script_path = (
        Path(__file__).resolve().parents[2] / "scripts" / "detect_secrets_filters.py"
    )
    module_name = "_detect_secrets_filters_under_test"
    spec = importlib.util.spec_from_file_location(module_name, script_path)
    if spec is None or spec.loader is None:
        msg = f"Unable to load secret filters from {script_path}"
        raise RuntimeError(msg)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


_IsValidRepositoryEvidence = Callable[[str, str, str], bool]
is_valid_repository_evidence = cast(
    "_IsValidRepositoryEvidence",
    _load_secret_filters().is_valid_repository_evidence,
)


def test_reimplementation_commit_requires_real_repository_commit() -> None:
    """Allow a real ledger commit identity and reject an invented hash."""
    commit = subprocess.check_output(
        ["git", "rev-parse", "HEAD"],
        text=True,
    ).strip()
    path = "docs/dev/evidence/reimplementation.json"

    assert is_valid_repository_evidence(
        path,
        f'    "repository_commit": "{commit}",',
        commit,
    )
    fake_commit = "f" * 40
    assert not is_valid_repository_evidence(
        path,
        f'    "repository_commit": "{fake_commit}",',
        fake_commit,
    )


def test_reimplementation_fingerprint_requires_schema_bound_value() -> None:
    """Allow only an exact SHA-256 value field in the canonical ledger."""
    fingerprint = "a" * 64
    path = "docs/dev/evidence/reimplementation.json"

    assert is_valid_repository_evidence(
        path,
        f'    "value": "{fingerprint}"',
        fingerprint,
    )
    assert not is_valid_repository_evidence(
        "docs/PROJECT.md",
        f'    "value": "{fingerprint}"',
        fingerprint,
    )
    assert not is_valid_repository_evidence(
        path,
        f'    "token": "{fingerprint}"',
        fingerprint,
    )
