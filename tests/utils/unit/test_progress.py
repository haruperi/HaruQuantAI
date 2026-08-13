"""Unit tests for app.utils.progress."""

import pytest
from app.utils.progress import (
    create_progress_snapshot,
    make_progress_callback,
)


def test_create_progress_snapshot_computes_percentage_and_completion() -> None:
    """Snapshot computes accurate rounded percentage and complete flag."""
    snapshot = create_progress_snapshot(
        completed=25, total=100, description="Loading bars"
    )
    assert snapshot["completed"] == 25
    assert snapshot["total"] == 100
    assert snapshot["percent"] == 25.0
    assert snapshot["description"] == "Loading bars"
    assert snapshot["status"] == "processing"
    assert snapshot["is_complete"] is False

    finished = create_progress_snapshot(completed=100, total=100, description="Done")
    assert finished["percent"] == 100.0
    assert finished["is_complete"] is True


def test_create_progress_snapshot_rejects_invalid_bounds() -> None:
    """Invalid completed or total values raise ValueError."""
    with pytest.raises(ValueError, match="completed cannot be negative"):
        create_progress_snapshot(completed=-1, total=10)

    with pytest.raises(ValueError, match="total must be positive"):
        create_progress_snapshot(completed=0, total=0)


def test_make_progress_callback_updates_step_counter() -> None:
    """Progress callback steps through progress iterations and invokes listener."""
    updates: list[dict[str, object]] = []

    callback = make_progress_callback(
        total=4,
        description="Fetching pages",
        on_update=updates.append,
    )

    s1 = callback(1)
    assert s1["completed"] == 1
    assert s1["percent"] == 25.0
    assert s1["is_complete"] is False

    s2 = callback(3)
    assert s2["completed"] == 4
    assert s2["percent"] == 100.0
    assert s2["status"] == "completed"
    assert s2["is_complete"] is True

    assert len(updates) == 2
