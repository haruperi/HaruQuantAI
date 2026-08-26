"""Task-run identifier validation regression tests."""

from __future__ import annotations

import sys
from types import ModuleType
from typing import Any

import pytest


def _task() -> dict[str, Any]:
    return {
        "task_kind": "feature",
        "task_id": "FEAT-DEMO",
        "task_slug": "demo",
        "task_name": "Demo",
        "task_request": "Exercise Task API run-id validation.",
    }


@pytest.mark.parametrize(
    "run_id",
    [
        "../escape",
        r"..\escape",
        "../../outside",
        r"C:\outside",
        "/absolute/path",
        "a/b",
        r"a\b",
        ".",
        "..",
        "-leading-dash",
    ],
)
def test_create_task_state_rejects_unsafe_run_ids(
    orc: ModuleType, run_id: str
) -> None:
    with pytest.raises(orc.OrchestratorError, match="run_id"):
        orc.create_task_state(_task(), "baseline", run_id=run_id)


@pytest.mark.parametrize(
    "run_id",
    [
        "run-1",
        "RUN_2.test",
        "20260826-182203-123456-ui-phase-1.8-manage-data",
    ],
)
def test_create_task_state_accepts_filesystem_safe_run_ids(
    orc: ModuleType, run_id: str
) -> None:
    state = orc.create_task_state(_task(), "baseline", run_id=run_id)
    assert state["run_id"] == run_id


def test_prepare_task_run_rejects_unsafe_id_before_persistence(
    orc: ModuleType, monkeypatch: pytest.MonkeyPatch
) -> None:
    task_api = sys.modules[orc.prepare_task_run.__module__]
    monkeypatch.setattr(task_api, "_entry_gate", lambda _cfg: "baseline")
    monkeypatch.setattr(
        task_api,
        "_save_state",
        lambda *_args, **_kwargs: pytest.fail("unsafe run_id reached persistence"),
    )

    with pytest.raises(orc.OrchestratorError, match="run_id"):
        orc.prepare_task_run({}, _task(), run_id="../escape")
