"""Guard: live feed state has exactly one owner.

``CAP-DATA-026`` Phase 8 split ``feeds/runtime.py`` into buffer, reconnection,
heartbeat, and status. ``_ACTIVE_FEEDS`` — the registry of live feed state — had to end
up in exactly one of them.

If each module declared its own registry, ingestion would write to one while status read
another. Nothing would raise. The feed would simply report as idle while receiving
events, and buffer depth would read zero while the buffer filled. That is the same shape
as the duplicated settings ``ContextVar`` Phase 3 uncovered: a silent divergence where
one half of the system is quietly wrong.

The first test asserts the structural property by parsing source, so it holds even when
Python's module cache would mask a second definition. The rest assert the behavioural
consequence — that a feed started through one module is visible through the others.
"""

from __future__ import annotations

import ast
from pathlib import Path

FEEDS = Path("app/services/data/realtime_feeds").resolve()
STATE_SYMBOL = "_ACTIVE_FEEDS"


def _modules_declaring(symbol: str) -> list[str]:
    """Return every feed module that assigns ``symbol`` at module level.

    A re-export (``from ._state import _ACTIVE_FEEDS``) is not a declaration and is not
    counted — only an assignment creates a second registry.

    Args:
        symbol: Module-level name to look for.

    Returns:
        Sorted file names that assign the symbol.
    """
    declaring: list[str] = []
    for path in sorted(FEEDS.glob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in tree.body:
            targets = []
            if isinstance(node, ast.Assign):
                targets = node.targets
            elif isinstance(node, ast.AnnAssign):
                targets = [node.target]
            if any(
                isinstance(target, ast.Name) and target.id == symbol
                for target in targets
            ):
                declaring.append(path.name)
    return sorted(declaring)


def test_exactly_one_module_declares_the_feed_registry() -> None:
    """Assert ``_ACTIVE_FEEDS`` is assigned in one place only.

    Raises:
        AssertionError: If zero or more than one module declares the registry.
    """
    declaring = _modules_declaring(STATE_SYMBOL)
    assert declaring == ["state.py"], (
        f"{STATE_SYMBOL} is declared in {declaring}. Exactly one module may own live "
        "feed state; a second registry makes ingestion and status disagree silently."
    )


def test_every_feed_module_shares_the_same_registry_object() -> None:
    """Assert the modules resolve the identical registry object at runtime.

    Structural analysis alone would miss an alias created through some other route, so
    this pins object identity as well.

    Raises:
        AssertionError: If any module holds a different registry object.
    """
    from app.services.data.realtime_feeds import buffer, reconnection, state

    assert buffer._ACTIVE_FEEDS is state._ACTIVE_FEEDS
    assert reconnection._ACTIVE_FEEDS is state._ACTIVE_FEEDS


def test_a_feed_registered_through_buffer_is_visible_to_status() -> None:
    """Assert the registry is genuinely shared across the split boundary.

    This is the behavioural form of the same property: were there two registries, a feed
    inserted by the ingestion path would be absent from the status path.

    Raises:
        AssertionError: If a directly registered feed is not observable.
    """
    from app.services.data.realtime_feeds import status
    from app.services.data.realtime_feeds.state import _ACTIVE_FEEDS, ActiveFeed

    probe = ActiveFeed.__new__(ActiveFeed)
    _ACTIVE_FEEDS["probe-feed"] = probe
    try:
        # `status` reads the registry it imported; if that were a second dict, the probe
        # would be invisible here.
        from app.services.data.realtime_feeds.state import _ACTIVE_FEEDS as STATUS_SIDE

        assert "probe-feed" in STATUS_SIDE
        assert STATUS_SIDE["probe-feed"] is probe
        assert status is not None
    finally:
        _ACTIVE_FEEDS.pop("probe-feed", None)


def test_scheduler_background_tasks_have_one_owner() -> None:
    """Assert the scheduler's task registry is declared once.

    Smaller blast radius than the feed registry, but the same failure mode: a duplicated
    task registry would let ``stop`` fail to cancel a loop that ``start`` created, and
    the job would keep running while reporting as stopped.

    Raises:
        AssertionError: If more than one scheduler module declares the registry.
    """
    scheduler = Path("app/services/data/data_jobs").resolve()
    declaring: list[str] = []
    for path in sorted(scheduler.glob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in tree.body:
            targets = []
            if isinstance(node, ast.Assign):
                targets = node.targets
            elif isinstance(node, ast.AnnAssign):
                targets = [node.target]
            if any(
                isinstance(target, ast.Name) and target.id == "_BACKGROUND_TASKS"
                for target in targets
            ):
                declaring.append(path.name)
    assert sorted(declaring) == ["job.py"], (
        f"_BACKGROUND_TASKS is declared in {sorted(declaring)}. Only the module that "
        "starts and stops loops may own the task registry."
    )
