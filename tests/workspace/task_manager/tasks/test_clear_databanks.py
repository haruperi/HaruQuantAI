"""Unit tests for ClearDatabanksTask coordinator.

Description:
    Validates precedence of 'all' keyword, missing bank continuation, duplicate clears,
    exact log/reason strings, MemoryError handling, and uncaught exception propagation.

Purpose:
    FEAT-TASK-EXECUTION: Validate databank clearing coordinator.

Key Capabilities:
    - FR-task-clear-databanks: Test execution branches and exception policies.
"""

from __future__ import annotations

from collections.abc import Sequence

import pytest
from app.workspace.task_manager.tasks.clear_databanks import (
    ClearBank,
    ClearDatabanksTask,
)


class FakeBank:
    """In-memory bank recording clear_records calls."""

    def __init__(self, name: str, fail_error: Exception | None = None) -> None:
        self.name = name
        self.fail_error = fail_error
        self.calls: list[tuple[bool, bool, str]] = []

    def clear_records(self, reset_view: bool, notify: bool, reason: str) -> None:
        if self.fail_error:
            raise self.fail_error
        self.calls.append((reset_view, notify, reason))


class FakeProgress:
    """In-memory progress recording call sequence."""

    def __init__(self) -> None:
        self.prefix = ""
        self.logs: list[str] = []
        self.started = False
        self.finished = False

    def set_log_prefix(self, prefix: str) -> None:
        self.prefix = prefix

    def log(self, message: str) -> None:
        self.logs.append(message)

    def start(self) -> None:
        self.started = True

    def finish(self) -> None:
        self.finished = True


class FakeProject:
    """In-memory project adapter."""

    def __init__(
        self,
        banks: Sequence[FakeBank],
        on_memory_error_callback: Exception | None = None,
    ) -> None:
        self.banks_list = list(banks)
        self.banks_map = {b.name: b for b in banks}
        self.get_bank_calls: list[str] = []
        self.memory_error_received: MemoryError | None = None
        self.on_memory_error_callback = on_memory_error_callback

    def list_banks(self) -> Sequence[ClearBank]:
        return self.banks_list

    def get_bank(self, name: str) -> ClearBank | None:
        self.get_bank_calls.append(name)
        return self.banks_map.get(name)

    def on_memory_error(self, error: MemoryError) -> None:
        self.memory_error_received = error
        if self.on_memory_error_callback:
            raise self.on_memory_error_callback


def test_all_precedence() -> None:
    """When 'all' is in names, list_banks is used and all banks are cleared once."""
    bank_a = FakeBank("A")
    bank_b = FakeBank("B")
    project = FakeProject([bank_a, bank_b])
    progress = FakeProgress()

    ClearDatabanksTask.run(
        ["Missing", "all", "A"],
        project_name="Proj1",
        task_title="Title1",
        task_log_prefix="[Prefix]",
        project=project,
        progress=progress,
    )

    # Prefix set, start and finish called
    assert progress.prefix == "[Prefix]"
    assert progress.started is True
    assert progress.finished is True

    # Logs assert start and all-cleared
    assert progress.logs == ["Clearing databanks...", "Cleared all databanks"]

    # Each bank cleared exactly once with exact all reason
    expected_reason_a = (
        "'Clear databanks task' Proj1/Title1, clear all databanks - databank Proj1/A"
    )
    expected_reason_b = (
        "'Clear databanks task' Proj1/Title1, clear all databanks - databank Proj1/B"
    )
    assert bank_a.calls == [(True, True, expected_reason_a)]
    assert bank_b.calls == [(True, True, expected_reason_b)]


def test_selected_missing_duplicate() -> None:
    """Selected banks iterate in order; missing bank logs and duplicate clears again."""
    bank_a = FakeBank("A")
    project = FakeProject([bank_a])
    progress = FakeProgress()

    ClearDatabanksTask.run(
        ["A", "Missing", "A"],
        project_name="Proj2",
        task_title="Title2",
        task_log_prefix="[P2]",
        project=project,
        progress=progress,
    )

    assert project.get_bank_calls == ["A", "Missing", "A"]
    assert progress.logs == [
        "Clearing databanks...",
        "Cleared databank 'A'",
        "Error: Databank Missing not found",
        "Cleared databank 'A'",
    ]
    assert progress.finished is True

    expected_reason = (
        "'Clear databanks task' Proj2/Title2, "
        "clear selected databanks - databank Proj2/A"
    )
    assert bank_a.calls == [
        (True, True, expected_reason),
        (True, True, expected_reason),
    ]


def test_exception_policies() -> None:
    """RuntimeError propagates without finish; MemoryError invokes handler and finishes."""
    # RuntimeError propagates with no finish
    failing_bank = FakeBank("Bad", fail_error=RuntimeError("disk full"))
    project1 = FakeProject([failing_bank])
    progress1 = FakeProgress()

    with pytest.raises(RuntimeError, match="disk full"):
        ClearDatabanksTask.run(
            ["Bad"],
            project_name="P",
            task_title="T",
            task_log_prefix="",
            project=project1,
            progress=progress1,
        )
    assert progress1.finished is False

    # MemoryError invokes handler and finishes if handler returns
    mem_bank = FakeBank("Mem", fail_error=MemoryError("out of memory"))
    project2 = FakeProject([mem_bank])
    progress2 = FakeProgress()

    ClearDatabanksTask.run(
        ["Mem"],
        project_name="P",
        task_title="T",
        task_log_prefix="",
        project=project2,
        progress=progress2,
    )
    assert project2.memory_error_received is not None
    assert progress2.finished is True
