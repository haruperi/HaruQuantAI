"""Standalone usage evidence for FEAT-UTIL-15."""

from app.utils import (
    create_progress_snapshot,
    make_progress_callback,
)


def main() -> None:
    """Demonstrate progress tracking and step callbacks."""
    updates: list[dict[str, object]] = []
    callback = make_progress_callback(
        total=10, description="Processing work", on_update=updates.append
    )

    for _ in range(10):
        callback(1)

    final_snapshot = create_progress_snapshot(
        completed=10, total=10, description="Processing work"
    )
    assert final_snapshot["is_complete"] is True
    assert len(updates) == 10
    print("SUCCESS: FEAT-UTIL-15 progress tracking completed")
    print(f"Data -> final_snapshot={final_snapshot}")


if __name__ == "__main__":
    main()
