"""Deterministic progress tracking models and callbacks.

Provides normalized status dictionaries, progress counters, and
callbacks for domain workflows and SSE API progress streams.
"""

from collections.abc import Callable
from typing import Any


def create_progress_snapshot(
    completed: int,
    total: int,
    *,
    description: str = "Processing…",
    status: str = "processing",
) -> dict[str, Any]:
    """Build a normalized progress status dictionary.

    Args:
        completed: Number of completed items/steps.
        total: Total expected items/steps.
        description: Human-readable step description.
        status: Operation status ('processing', 'completed', etc.).

    Returns:
        Structured progress snapshot payload.

    Raises:
        ValueError: If bounds are invalid.
    """
    if completed < 0:
        raise ValueError("completed cannot be negative")
    if total <= 0:
        raise ValueError("total must be positive")

    bounded_completed = min(completed, total)
    percent = round((bounded_completed / total) * 100.0, 2)

    return {
        "completed": bounded_completed,
        "total": total,
        "percent": percent,
        "description": description,
        "status": status,
        "is_complete": bounded_completed >= total or status == "completed",
    }


def make_progress_callback(
    total: int,
    description: str = "Processing…",
    on_update: Callable[[dict[str, Any]], None] | None = None,
) -> Callable[[int], dict[str, Any]]:
    """Return a progress callback function for iterative loops.

    Args:
        total: Total items/steps in loop.
        description: Description of the work.
        on_update: Optional listener callback invoked on each step.

    Returns:
        Step update function returning current progress snapshot.
    """
    current = 0

    def step(count: int = 1) -> dict[str, Any]:
        """Advance progress step counter and return updated snapshot.

        Args:
            count: Number of steps completed in this iteration.

        Returns:
            Updated progress snapshot dictionary.
        """
        nonlocal current
        current += count
        status_name = "completed" if current >= total else "processing"
        snapshot = create_progress_snapshot(
            completed=current,
            total=total,
            description=description,
            status=status_name,
        )
        if on_update is not None:
            on_update(snapshot)
        return snapshot

    return step
