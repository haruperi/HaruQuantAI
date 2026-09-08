"""Exact-path lease tests for parallel Goal children."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType

import pytest


def _load() -> ModuleType:
    path = Path(__file__).resolve().parents[1] / "path_leases.py"
    spec = importlib.util.spec_from_file_location("hq_path_leases_tests", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_exact_leases_conflict_and_release() -> None:
    leases = _load()
    first = leases.LeaseRequest.build(
        task_run_id="one",
        lane="codex",
        exclusive_paths=["app/a.py"],
        deferred_paths=["docs/shared.md"],
    )
    table = leases.acquire_leases({}, first)
    with pytest.raises(leases.PathLeaseError, match="conflict"):
        leases.acquire_leases(
            table,
            leases.LeaseRequest.build(
                task_run_id="two",
                lane="gemini",
                exclusive_paths=["app/a.py"],
            ),
        )
    assert leases.release_leases(table, "one") == {}


@pytest.mark.parametrize("path", ["", "../x", "/x", "C:/x", ".git/config"])
def test_unsafe_lease_paths_fail(path: str) -> None:
    leases = _load()
    with pytest.raises(leases.PathLeaseError):
        leases.normalize_paths([path])


def test_exclusive_and_deferred_sets_must_be_disjoint() -> None:
    leases = _load()
    with pytest.raises(leases.PathLeaseError, match="both"):
        leases.LeaseRequest.build(
            task_run_id="one",
            lane="codex",
            exclusive_paths=["same.txt"],
            deferred_paths=["same.txt"],
        )
