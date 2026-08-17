"""Bounded live what-if session behaviour.

These tests exercise the session registry against a stubbed prepared context,
so they assert lifecycle and lineage rules without re-running a full backtest.
Determinism of the underlying engine is covered by the existing run tests; what
matters here is that a session advances in increments, that a branch cannot
disturb its parent, and that the registry stays bounded.
"""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any

import pytest
from app.services.simulator.errors import SimulationError
from app.services.simulator.state import live_sessions
from app.services.simulator.state.live_sessions import (
    branch_live_simulation,
    close_live_simulation_session,
    create_live_simulation_session,
    read_live_simulation_state,
    reset_live_simulation_sessions,
    step_live_simulation,
)


class _Engine:
    """Engine stub recording the ticks it was asked to execute."""

    def __init__(self) -> None:
        """Start with an empty execution record."""
        self.executed: list[int] = []

    def execute_tick(self, tick: Any) -> Any:
        """Record one executed tick.

        `unwrap_simulation_response` passes a non-envelope value through
        unchanged, so returning the raw receipt tuple keeps the stub honest
        without fabricating an owner response envelope.

        Args:
            tick: Timeline tick.

        Returns:
            Empty receipt tuple.
        """
        self.executed.append(tick.index)
        return ()

    def submit_order(self, intent: Any) -> Any:
        """Accept one order intent.

        Args:
            intent: Order intent.

        Returns:
            The accepted intent.
        """
        return intent

    def snapshot(self) -> Any:
        """Return a bounded virtual account projection."""
        return {
            "orders": (),
            "positions": (),
            "pending_orders": (),
            "deals": (),
            "account": {"balance": "100000"},
        }


class _Request:
    """Backtest-request stand-in supporting the owner copy contract."""

    def __init__(self, **fields: object) -> None:
        """Record the request fields.

        Args:
            **fields: Arbitrary request fields.
        """
        self.fields = fields
        self.data_ref = str(fields.get("data_ref", "dataset-test"))
        self.data_version = str(fields.get("data_version", "revision-test"))
        self.data_hash = str(fields.get("data_hash", "a" * 64))

    def model_copy(self, *, update: dict[str, object]) -> _Request:
        """Return a new request carrying the overrides.

        Args:
            update: Field overrides.

        Returns:
            Independent overridden request.
        """
        return _Request(**{**self.fields, **update})

    def model_dump(self, **_kwargs: object) -> dict[str, object]:
        """Return the immutable dataset request material.

        Returns:
            JSON-safe request mapping used by durable-session tests.
        """
        return {
            **self.fields,
            "data_ref": self.data_ref,
            "data_version": self.data_version,
            "data_hash": self.data_hash,
        }


def _tick(index: int) -> Any:
    """Build one ordered timeline tick.

    Args:
        index: Tick position.

    Returns:
        Tick stand-in carrying a comparable timestamp.
    """
    return SimpleNamespace(index=index, timestamp=index)


def _context(tick_count: int = 5) -> Any:
    """Build one prepared-context stand-in.

    Args:
        tick_count: Number of ticks in the timeline.

    Returns:
        Object exposing the fields the session registry reads.
    """
    return SimpleNamespace(
        timeline=tuple(_tick(index) for index in range(tick_count)),
        evidence=None,
        writer=None,
        ledger=None,
        profile=None,
        engine=_Engine(),
        order_intents=(),
    )


@pytest.fixture(autouse=True)
def _clean_registry() -> Any:
    """Ensure no session leaks between tests.

    Yields:
        Control to the test with an empty registry on both sides.
    """
    reset_live_simulation_sessions()
    yield
    reset_live_simulation_sessions()


@pytest.fixture
def _prepared(monkeypatch: pytest.MonkeyPatch) -> None:
    """Replace run preparation with a deterministic stub.

    Args:
        monkeypatch: Pytest patching fixture.
    """
    monkeypatch.setattr(
        live_sessions, "prepare_run_context", lambda *_a, **_k: _context()
    )
    monkeypatch.setattr(live_sessions, "submit_orders_before", lambda *_a, **_k: None)

    monkeypatch.setattr(live_sessions, "submit_orders_before", lambda *_a, **_k: None)


@pytest.mark.usefixtures("_prepared")
def test_session_opens_before_the_first_tick() -> None:
    """A new session has executed nothing yet."""
    state = create_live_simulation_session(_Request(), object(), request_id="req-1")
    assert state["cursor"] == 0
    assert state["tick_count"] == 5
    assert state["complete"] is False
    assert state["advisory"] is True


@pytest.mark.usefixtures("_prepared")
def test_stepping_advances_in_bounded_increments() -> None:
    """Stepping moves the cursor without overshooting the timeline."""
    state = create_live_simulation_session(_Request(), object(), request_id="req-1")
    session_id = str(state["session_id"])
    assert step_live_simulation(session_id, 2)["cursor"] == 2
    assert step_live_simulation(session_id, 2)["cursor"] == 4
    final = step_live_simulation(session_id, 10)
    assert final["cursor"] == 5
    assert final["complete"] is True


@pytest.mark.usefixtures("_prepared")
def test_step_size_must_be_bounded_and_positive() -> None:
    """A non-positive or oversized step never touches the engine."""
    state = create_live_simulation_session(_Request(), object(), request_id="req-1")
    session_id = str(state["session_id"])
    with pytest.raises(SimulationError):
        step_live_simulation(session_id, 0)
    with pytest.raises(SimulationError):
        step_live_simulation(session_id, 10_001)


def test_unknown_session_fails_closed() -> None:
    """An unknown session is refused rather than silently recreated."""
    with pytest.raises(SimulationError):
        read_live_simulation_state("simlive-does-not-exist")


@pytest.mark.usefixtures("_prepared")
def test_branch_replays_to_divergence_without_touching_the_parent() -> None:
    """A branch reaches the parent's cursor on its own engine.

    This is the property the live what-if exclusion existed to protect: a
    recorded outcome must stay immutable, so the branch must not share or
    mutate the parent's engine.
    """
    parent_state = create_live_simulation_session(
        _Request(), object(), request_id="req-1"
    )
    parent_id = str(parent_state["session_id"])
    step_live_simulation(parent_id, 3)
    parent_engine = live_sessions._SESSIONS[parent_id].context.engine
    parent_executed = list(parent_engine.executed)

    branch_state = branch_live_simulation(
        parent_id, {"seed": 99}, object(), request_id="req-2"
    )
    branch_id = str(branch_state["session_id"])

    assert branch_state["branch_of"] == parent_id
    assert branch_state["divergence_index"] == 3
    assert branch_state["cursor"] == 3
    assert branch_state["run_id"] != parent_state["run_id"]
    # The parent advanced no further and kept its own engine.
    assert read_live_simulation_state(parent_id)["cursor"] == 3
    assert parent_engine.executed == parent_executed
    assert live_sessions._SESSIONS[branch_id].context.engine is not parent_engine


@pytest.mark.usefixtures("_prepared")
def test_branch_from_the_start_replays_nothing() -> None:
    """Branching before any tick produces an unadvanced branch."""
    parent = create_live_simulation_session(_Request(), object(), request_id="req-1")
    branch = branch_live_simulation(
        str(parent["session_id"]), {}, object(), request_id="req-2"
    )
    assert branch["divergence_index"] == 0
    assert branch["cursor"] == 0


@pytest.mark.usefixtures("_prepared")
def test_invalid_overrides_fail_closed() -> None:
    """Overrides that cannot build a valid request never open a branch."""
    parent = create_live_simulation_session(_Request(), object(), request_id="req-1")

    class _Rejecting:
        def model_copy(self, *, _update: dict[str, object]) -> object:
            """Reject every override.

            Args:
                _update: Requested field overrides.

            Raises:
                ValueError: Always.
            """
            raise ValueError("invalid")

    live_sessions._SESSIONS[str(parent["session_id"])].request = _Rejecting()  # type: ignore[assignment]
    with pytest.raises(SimulationError):
        branch_live_simulation(
            str(parent["session_id"]), {"bad": 1}, object(), request_id="req-2"
        )


@pytest.mark.usefixtures("_prepared")
def test_registry_capacity_is_bounded() -> None:
    """An abandoned exploration cannot pin unbounded engine memory."""
    for index in range(live_sessions._MAX_LIVE_SESSIONS):
        create_live_simulation_session(_Request(), object(), request_id=f"req-{index}")
    with pytest.raises(SimulationError):
        create_live_simulation_session(_Request(), object(), request_id="req-overflow")


@pytest.mark.usefixtures("_prepared")
def test_reopening_the_same_request_is_idempotent() -> None:
    """A retried open re-attaches to the same session, not a second engine."""
    first = create_live_simulation_session(_Request(), object(), request_id="req-1")
    step_live_simulation(str(first["session_id"]), 2)
    second = create_live_simulation_session(_Request(), object(), request_id="req-1")
    assert second["session_id"] == first["session_id"]
    assert second["cursor"] == 2
    assert len(live_sessions._SESSIONS) == 1


@pytest.mark.usefixtures("_prepared")
def test_durable_session_persists_request_and_each_cursor(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Durable practice state is checkpointed without serializing the engine."""
    created: list[dict[str, object]] = []
    updated: list[dict[str, object]] = []
    monkeypatch.setattr(live_sessions, "_store", object)
    monkeypatch.setattr(
        live_sessions,
        "create_interactive_session_record",
        lambda _store, value, **_kwargs: created.append(dict(value)),
    )

    def _update(_store: object, **values: object) -> bool:
        updated.append(values)
        return True

    monkeypatch.setattr(live_sessions, "update_interactive_session_record", _update)
    state = create_live_simulation_session(
        _Request(), object(), request_id="req-durable", durable=True
    )
    assert created[0]["request"] == {
        "data_ref": "dataset-test",
        "data_version": "revision-test",
        "data_hash": "a" * 64,
    }
    assert "engine" not in created[0]
    step_live_simulation(str(state["session_id"]), 2)
    assert updated[-1]["cursor"] == 2
    assert len(str(updated[-1]["state_hash"])) == 64


@pytest.mark.usefixtures("_prepared")
def test_closing_releases_the_session() -> None:
    """A closed session is gone and its identity is not reusable."""
    state = create_live_simulation_session(_Request(), object(), request_id="req-1")
    session_id = str(state["session_id"])
    closed = close_live_simulation_session(session_id)
    assert closed["session_id"] == session_id
    with pytest.raises(SimulationError):
        read_live_simulation_state(session_id)
