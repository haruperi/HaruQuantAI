"""Role mutation-authority regression tests."""

from __future__ import annotations

from pathlib import Path
from types import ModuleType

import pytest


def test_snapshot_detects_change_to_already_dirty_file(
    orc: ModuleType, repo: Path
) -> None:
    path = repo / "dirty.txt"
    path.write_text("first", encoding="utf-8")
    before = orc.capture_repository_snapshot(repo)
    path.write_text("second", encoding="utf-8")
    delta = orc.compute_snapshot_delta(before, orc.capture_repository_snapshot(repo))
    assert delta["modified"] == {"dirty.txt"}


def test_executor_rejects_unapproved_path(orc: ModuleType) -> None:
    delta = {"created": {"surprise.py"}, "modified": set(), "deleted": set()}
    with pytest.raises(orc.OrchestratorError, match="unauthorized"):
        orc.validate_role_mutations(
            "EXECUTOR", delta, approved_write_paths={"approved.py"}
        )


@pytest.mark.parametrize(
    "path", ["../escape", "/absolute", "C:/absolute", ".git/config"]
)
def test_path_authority_rejects_unsafe_paths(orc: ModuleType, path: str) -> None:
    with pytest.raises(orc.OrchestratorError):
        orc._normalize_path_list([path])
