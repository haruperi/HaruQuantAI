"""Unit tests for synchronous effect scope.

Traces to: P5-T01, Gate G5
"""

from __future__ import annotations

from collections.abc import Generator
from contextlib import contextmanager

import pytest
from app.kernel.effects import EffectScope
from app.kernel.errors import LifecycleError


def test_reverse_order_disposal() -> None:
    """Verify registered callbacks execute in exact reverse registration order."""
    calls: list[int] = []
    scope = EffectScope()
    scope.callback(lambda: calls.append(1))
    scope.callback(lambda: calls.append(2))
    scope.callback(lambda: calls.append(3))

    assert scope.closed is False
    scope.close()
    assert scope.closed is True
    assert calls == [3, 2, 1]


def test_context_manager_entry_and_exit() -> None:
    """Verify context managers entered in scope are exited on close."""
    events: list[str] = []

    @contextmanager
    def _sample_cm(name: str) -> Generator[str]:
        events.append(f"enter_{name}")
        try:
            yield name
        finally:
            events.append(f"exit_{name}")

    scope = EffectScope()
    res1 = scope.enter_context(_sample_cm("A"))
    res2 = scope.enter_context(_sample_cm("B"))

    assert res1 == "A"
    assert res2 == "B"
    assert events == ["enter_A", "enter_B"]

    scope.close()
    assert events == ["enter_A", "enter_B", "exit_B", "exit_A"]


def test_double_close_is_idempotent() -> None:
    """Verify closing an already closed scope is safe and idempotent."""
    calls: list[int] = []
    scope = EffectScope()
    scope.callback(lambda: calls.append(1))

    scope.close()
    assert calls == [1]
    scope.close()
    assert calls == [1]


def test_register_after_close_raises_lifecycle_error() -> None:
    """Verify registering callback or context manager on closed scope raises LifecycleError."""
    scope = EffectScope()
    scope.close()

    with pytest.raises(LifecycleError, match="effect scope is closed"):
        scope.callback(lambda: None)

    @contextmanager
    def _cm() -> Generator[None]:
        yield

    with pytest.raises(LifecycleError, match="effect scope is closed"):
        scope.enter_context(_cm())


def test_can_dispose_refusal_leaves_scope_open() -> None:
    """Verify refusal predicate raises LifecycleError without closing scope or executing disposers."""
    calls: list[int] = []
    allow_dispose = False

    scope = EffectScope(can_dispose=lambda: allow_dispose)
    scope.callback(lambda: calls.append(1))

    with pytest.raises(LifecycleError, match="effect scope refused disposal"):
        scope.close()

    assert scope.closed is False
    assert calls == []

    allow_dispose = True
    scope.close()
    assert scope.closed is True
    assert calls == [1]


def test_all_failures_attempted_and_aggregated() -> None:
    """Verify all disposers execute even when some fail, and exceptions are aggregated."""
    calls: list[str] = []

    def _fail_1() -> None:
        calls.append("f1")
        raise RuntimeError("boom_1")

    def _ok() -> None:
        calls.append("ok")

    def _fail_2() -> None:
        calls.append("f2")
        raise ValueError("boom_2")

    scope = EffectScope()
    scope.callback(_fail_1)
    scope.callback(_ok)
    scope.callback(_fail_2)

    with pytest.raises(
        LifecycleError, match="effect scope cleanup failed: 2 disposer\\(s\\)"
    ) as exc_info:
        scope.close()

    assert scope.closed is True
    assert calls == ["f2", "ok", "f1"]
    assert len(exc_info.value.failures) == 2  # type: ignore[attr-defined]
    assert isinstance(exc_info.value.failures[0], ValueError)  # type: ignore[attr-defined]
    assert isinstance(exc_info.value.failures[1], RuntimeError)  # type: ignore[attr-defined]
