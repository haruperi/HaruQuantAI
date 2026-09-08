"""Reviewed-draft integration queue tests."""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path
from types import ModuleType

import pytest


def _git(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args], cwd=repo, check=True, capture_output=True, text=True
    )
    return result.stdout.strip()


def _load() -> ModuleType:
    path = Path(__file__).resolve().parents[1] / "integration_queue.py"
    spec = importlib.util.spec_from_file_location("hq_integration_queue_tests", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_queue_orders_criticality_then_task_id() -> None:
    integration = _load()
    items = [
        integration.QueueItem("2.10", "c", "zcode", 1),
        integration.QueueItem("1.11", "b", "gemini", 2),
        integration.QueueItem("1.08", "a", "codex", 2),
    ]
    assert [item.entry for item in integration.order_queue(items)] == [
        "1.08",
        "1.11",
        "2.10",
    ]


def test_integration_lock_rejects_second_owner(tmp_path: Path) -> None:
    integration = _load()
    path = tmp_path / "integration.lock"
    with integration.IntegrationLock(path, "one"):
        with pytest.raises(integration.IntegrationError, match="already held"):
            with integration.IntegrationLock(path, "two"):
                pass
    assert not path.exists()


def test_refresh_overlap_detects_changed_draft_path(repo: Path) -> None:
    integration = _load()
    baseline = _git(repo, "rev-parse", "HEAD")
    (repo / "demo.txt").write_text("main changed", encoding="utf-8")
    _git(repo, "add", "demo.txt")
    _git(repo, "commit", "--no-verify", "-m", "move main")
    head = _git(repo, "rev-parse", "HEAD")
    assert integration.refresh_overlap(
        repo,
        draft_baseline=baseline,
        integration_baseline=head,
        draft_paths={"demo.txt", "other.txt"},
    ) == {"demo.txt"}
