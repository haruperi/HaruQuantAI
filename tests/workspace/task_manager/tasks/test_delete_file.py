"""Unit tests for DeleteFileTask coordinator.

Description:
    Validates success workflow ordering, missing and deletion-denied error handling,
    adapter exception isolation, and progress start exception propagation.

Purpose:
    FEAT-TASK-EXECUTION: Validate file deletion coordinator.

Key Capabilities:
    - FR-task-delete-file: Test execution ordering, error formatting, and catch-and-finish policies.
"""

from __future__ import annotations

import logging
from pathlib import PurePath

import pytest
from app.workspace.task_manager.tasks.delete_file import (
    DeleteFileTask,
)


class FakeFileOperations:
    """In-memory file operations adapter recording to a shared call list."""

    def __init__(
        self,
        calls: list[str],
        exists_result: bool = True,
        delete_result: bool = True,
        exists_error: Exception | None = None,
    ) -> None:
        self.calls = calls
        self.exists_result = exists_result
        self.delete_result = delete_result
        self.exists_error = exists_error

    def exists(self, path: str) -> bool:
        self.calls.append("exists")
        if self.exists_error:
            raise self.exists_error
        return self.exists_result

    def delete(self, path: str) -> bool:
        self.calls.append("delete")
        return self.delete_result

    def basename(self, path: str) -> str:
        return PurePath(path).name


class FakeProgress:
    """In-memory progress adapter recording to a shared call list."""

    def __init__(
        self,
        calls: list[str],
        start_error: Exception | None = None,
    ) -> None:
        self.calls = calls
        self.logs: list[str] = []
        self.start_error = start_error

    def set_log_prefix(self, prefix: str) -> None:
        self.calls.append("prefix")

    def log(self, message: str) -> None:
        self.calls.append("log")
        self.logs.append(message)

    def start(self) -> None:
        self.calls.append("start")
        if self.start_error:
            raise self.start_error

    def finish(self) -> None:
        self.calls.append("finish")


def test_success() -> None:
    """Successful deletion verifies exact call order, log message, and finish call."""
    calls: list[str] = []
    files = FakeFileOperations(calls, exists_result=True, delete_result=True)
    progress = FakeProgress(calls)

    result = DeleteFileTask.run(
        "p/a.txt",
        task_log_prefix="[P] ",
        files=files,
        progress=progress,
    )

    assert result.message == "File 'a.txt' deleted."
    assert calls == [
        "prefix",
        "log",
        "start",
        "exists",
        "delete",
        "log",
        "finish",
    ]
    assert progress.logs == ["Deleting file...", "File 'a.txt' deleted."]


def test_missing_and_denied() -> None:
    """Missing file and delete failure log their errors and finish without outward raise."""
    # Missing file
    calls_missing: list[str] = []
    files_missing = FakeFileOperations(calls_missing, exists_result=False)
    progress_missing = FakeProgress(calls_missing)
    res_missing = DeleteFileTask.run(
        "p/a.txt",
        task_log_prefix="[P] ",
        files=files_missing,
        progress=progress_missing,
    )
    assert res_missing.message == "File 'a.txt' not found."
    assert "delete" not in calls_missing
    assert progress_missing.logs == ["Deleting file...", "File 'a.txt' not found."]
    assert calls_missing[-1] == "finish"

    # Exists true, delete false
    calls_denied: list[str] = []
    files_denied = FakeFileOperations(
        calls_denied, exists_result=True, delete_result=False
    )
    progress_denied = FakeProgress(calls_denied)
    res_denied = DeleteFileTask.run(
        "p/a.txt",
        task_log_prefix="[P] ",
        files=files_denied,
        progress=progress_denied,
    )
    assert res_denied.message == "File 'a.txt' cannot be deleted."
    assert "delete" in calls_denied
    assert progress_denied.logs == [
        "Deleting file...",
        "File 'a.txt' cannot be deleted.",
    ]
    assert calls_denied[-1] == "finish"


def test_adapter_exception(caplog: pytest.LogCaptureFixture) -> None:
    """Adapter exception is logged with cause, returns message, and finishes; start error propagates."""
    with caplog.at_level(logging.ERROR):
        calls: list[str] = []
        files = FakeFileOperations(calls, exists_error=RuntimeError("disk unavailable"))
        progress = FakeProgress(calls)

        outcome = DeleteFileTask.run(
            "p/a.txt",
            task_log_prefix="",
            files=files,
            progress=progress,
        )
        assert outcome.message == "disk unavailable"
        assert calls[-1] == "finish"
        assert any(
            "Error while loading strategies. Exc." in record.message
            for record in caplog.records
        )

    # Progress start failure propagates without file operations
    calls_fail: list[str] = []
    progress_fail = FakeProgress(calls_fail, start_error=RuntimeError("start failed"))
    files_untouched = FakeFileOperations(calls_fail)
    with pytest.raises(RuntimeError, match="start failed"):
        DeleteFileTask.run(
            "p/a.txt",
            task_log_prefix="",
            files=files_untouched,
            progress=progress_fail,
        )
    assert "exists" not in calls_fail
    assert "delete" not in calls_fail
