"""Extended live-session authority: listing, seek, commands, and finalization.

These tests cover the interactive operations added for the Simulation
Workbench. They exercise the rules that make interactive evidence trustworthy:
seek only moves forward, a command receipt reflects what the engine actually
did, and a finalized session accepts nothing further.
"""

from __future__ import annotations

from decimal import Decimal
from types import SimpleNamespace
from typing import Any

import pytest
from app.services.simulator.errors import SimulationError
from app.services.simulator.state import live_sessions
from app.services.simulator.state.live_sessions import (
    close_live_simulation_session,
    create_live_simulation_session,
    execute_live_simulation_command,
    finalize_live_simulation_session,
    list_live_simulation_sessions,
    read_live_simulation_state,
    reset_live_simulation_sessions,
    seek_live_simulation,
    step_live_simulation,
)


class _Engine:
    """Engine stub recording the operations the command layer requested."""

    def __init__(self) -> None:
        """Start with empty execution and command records."""
        self.executed: list[int] = []
        self.cancelled: list[str] = []
        self.modified: list[tuple[str, object, object, object]] = []
        self.closed: list[tuple[str, Decimal]] = []
        self.positions: tuple[dict[str, object], ...] = ()

    def execute_tick(self, tick: Any) -> Any:
        """Record one executed tick.

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

    def cancel_pending_order(self, client_order_id: str) -> Any:
        """Cancel one resting order.

        Args:
            client_order_id: Resting order identity.

        Returns:
            Cancelled receipt stand-in carrying no fill.
        """
        self.cancelled.append(client_order_id)
        return {
            "client_order_id": client_order_id,
            "status": "cancelled",
            "filled_quantity": Decimal(0),
        }

    def modify_pending_order(
        self,
        client_order_id: str,
        *,
        price: object = None,
        stop_loss: object = None,
        take_profit: object = None,
    ) -> Any:
        """Revise one resting order.

        Args:
            client_order_id: Resting order identity.
            price: Replacement trigger price.
            stop_loss: Replacement protective stop.
            take_profit: Replacement protective target.

        Returns:
            Accepted receipt stand-in carrying no fill.
        """
        self.modified.append((client_order_id, price, stop_loss, take_profit))
        return {
            "client_order_id": client_order_id,
            "status": "accepted",
            "filled_quantity": Decimal(0),
        }

    def close_position(self, position_id: str, quantity: Decimal) -> Any:
        """Close one open position.

        Args:
            position_id: Open position identity.
            quantity: Approved closing quantity.

        Returns:
            Close evidence stand-in.
        """
        self.closed.append((position_id, quantity))
        return {"position_id": position_id, "closed_volume": quantity}

    def snapshot(self) -> Any:
        """Return a bounded virtual account projection."""
        return {
            "orders": (),
            "positions": self.positions,
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
            JSON-safe request mapping.
        """
        return {
            **self.fields,
            "data_ref": self.data_ref,
            "data_version": self.data_version,
            "data_hash": self.data_hash,
        }


def _context(engine: _Engine, tick_count: int = 5) -> Any:
    """Build one prepared-context stand-in.

    Args:
        engine: Engine stub the session should drive.
        tick_count: Number of ticks in the timeline.

    Returns:
        Object exposing the fields the session registry reads.
    """
    return SimpleNamespace(
        timeline=tuple(
            SimpleNamespace(index=index, timestamp=index) for index in range(tick_count)
        ),
        evidence=None,
        writer=None,
        ledger=None,
        profile=None,
        engine=engine,
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
def engine(monkeypatch: pytest.MonkeyPatch) -> _Engine:
    """Replace run preparation with a deterministic stub.

    Args:
        monkeypatch: Pytest patching fixture.

    Returns:
        The engine stub every session in the test will drive.
    """
    stub = _Engine()
    monkeypatch.setattr(
        live_sessions, "prepare_run_context", lambda *_a, **_k: _context(stub)
    )
    monkeypatch.setattr(live_sessions, "submit_orders_before", lambda *_a, **_k: None)
    return stub


def _open(request_id: str = "req-1") -> str:
    """Open one session and return its identity.

    Args:
        request_id: Request identity driving session derivation.

    Returns:
        The opened session identity.
    """
    state = create_live_simulation_session(
        _Request(marker=request_id), object(), request_id=request_id
    )
    return str(state["session_id"])


# --- Listing ---------------------------------------------------------------


@pytest.mark.usefixtures("engine")
def test_listing_returns_every_open_session() -> None:
    """An operator can see the sessions they can actually act on."""
    first = _open("req-1")
    second = _open("req-2")
    listed = list_live_simulation_sessions()
    assert [str(row["session_id"]) for row in listed] == [first, second]


@pytest.mark.usefixtures("engine")
def test_listing_omits_a_closed_session() -> None:
    """A released session is no longer offered as actionable."""
    first = _open("req-1")
    close_live_simulation_session(first)
    assert list_live_simulation_sessions() == ()


# --- Seek ------------------------------------------------------------------


def test_seek_advances_to_the_requested_cursor(engine: _Engine) -> None:
    """Seeking executes every tick between the cursor and the target."""
    session_id = _open()
    state = seek_live_simulation(session_id, 3)
    assert state["cursor"] == 3
    assert engine.executed == [0, 1, 2]


@pytest.mark.usefixtures("engine")
def test_seek_to_the_current_cursor_is_a_no_op() -> None:
    """A repeated seek does not re-execute ticks."""
    session_id = _open()
    seek_live_simulation(session_id, 2)
    state = seek_live_simulation(session_id, 2)
    assert state["cursor"] == 2


@pytest.mark.usefixtures("engine")
def test_seek_backwards_is_forbidden() -> None:
    """Rewinding would let hindsight leak into a later decision."""
    session_id = _open()
    step_live_simulation(session_id, 3)
    with pytest.raises(SimulationError) as failure:
        seek_live_simulation(session_id, 1)
    assert failure.value.code == "SIMULATION_SEEK_REWIND_FORBIDDEN"


@pytest.mark.usefixtures("engine")
def test_seek_beyond_the_bounded_distance_is_refused() -> None:
    """An unbounded seek would execute an unbounded amount of work."""
    session_id = _open()
    with pytest.raises(SimulationError) as failure:
        seek_live_simulation(session_id, live_sessions._MAX_SEEK_TICKS + 1)
    assert failure.value.code == "SIMULATION_SEEK_LIMIT_EXCEEDED"


@pytest.mark.usefixtures("engine")
def test_seek_beyond_the_timeline_is_refused() -> None:
    """A session cannot advance past the data it was prepared with."""
    session_id = _open()
    with pytest.raises(SimulationError) as failure:
        seek_live_simulation(session_id, 6)
    assert failure.value.code == "SIM_INVALID_CONFIG"


# --- Commands --------------------------------------------------------------


@pytest.mark.anyio
@pytest.mark.usefixtures("engine")
async def test_unknown_command_discriminator_is_refused() -> None:
    """Only the frozen command set reaches the engine."""
    session_id = _open()
    with pytest.raises(SimulationError) as failure:
        await execute_live_simulation_command(session_id, {"command": "liquidate_all"})
    assert failure.value.code == "SIM_UNSUPPORTED_OPERATION"


@pytest.mark.anyio
async def test_cancel_command_returns_a_receipt_without_a_fill(
    engine: _Engine,
) -> None:
    """Cancelling a resting order never reports a fill."""
    session_id = _open()
    result = await execute_live_simulation_command(
        session_id, {"command": "cancel_pending_order", "order_id": "order-7"}
    )
    assert engine.cancelled == ["order-7"]
    receipt = result["receipts"][0]  # type: ignore[index]
    assert receipt["status"] == "cancelled"
    assert receipt["filled_quantity"] == Decimal(0)


@pytest.mark.anyio
async def test_modify_command_forwards_only_supplied_levels(
    engine: _Engine,
) -> None:
    """A modification changes levels and reports no fill."""
    session_id = _open()
    result = await execute_live_simulation_command(
        session_id,
        {
            "command": "modify_pending_order",
            "order_id": "order-7",
            "stop_loss": "1.0800",
        },
    )
    assert engine.modified == [("order-7", None, Decimal("1.0800"), None)]
    assert result["receipts"][0]["filled_quantity"] == Decimal(0)  # type: ignore[index]


@pytest.mark.anyio
async def test_close_position_command_uses_the_supplied_volume(
    engine: _Engine,
) -> None:
    """Closing evidence comes from the engine, not from the caller."""
    session_id = _open()
    await execute_live_simulation_command(
        session_id,
        {"command": "close_position", "position_id": "pos-1", "volume": "0.10"},
    )
    assert engine.closed == [("pos-1", Decimal("0.10"))]


@pytest.mark.anyio
@pytest.mark.usefixtures("engine")
async def test_close_position_command_requires_a_position() -> None:
    """A command missing a required field fails closed."""
    session_id = _open()
    with pytest.raises(SimulationError) as failure:
        await execute_live_simulation_command(
            session_id, {"command": "close_position", "volume": "0.10"}
        )
    assert failure.value.code == "SIM_INVALID_CONFIG"


@pytest.mark.anyio
async def test_close_all_practice_exposure_closes_every_open_position(
    engine: _Engine,
) -> None:
    """The panic action closes exactly what the engine reports as open."""
    engine.positions = (
        {"position_id": "pos-1", "volume": "0.10"},
        {"position_id": "pos-2", "volume": "0.20"},
    )
    session_id = _open()
    result = await execute_live_simulation_command(
        session_id, {"command": "close_all_practice_exposure"}
    )
    assert engine.closed == [
        ("pos-1", Decimal("0.10")),
        ("pos-2", Decimal("0.20")),
    ]
    assert len(result["receipts"]) == 2  # type: ignore[arg-type]


@pytest.mark.anyio
@pytest.mark.usefixtures("engine")
async def test_command_response_carries_refreshed_session_state() -> None:
    """Every command answers with the authoritative state it produced."""
    session_id = _open()
    step_live_simulation(session_id, 2)
    result = await execute_live_simulation_command(
        session_id, {"command": "cancel_pending_order", "order_id": "order-7"}
    )
    session = result["session"]
    assert session["session_id"] == session_id  # type: ignore[index]
    assert session["cursor"] == 2  # type: ignore[index]


@pytest.mark.anyio
@pytest.mark.usefixtures("engine")
async def test_completed_session_accepts_no_command() -> None:
    """A session with no timeline left cannot act on the market."""
    session_id = _open()
    seek_live_simulation(session_id, 5)
    with pytest.raises(SimulationError) as failure:
        await execute_live_simulation_command(
            session_id, {"command": "cancel_pending_order", "order_id": "order-7"}
        )
    assert failure.value.code == "SIM_UNSUPPORTED_OPERATION"


# --- Finalization ----------------------------------------------------------


@pytest.mark.usefixtures("engine")
def test_finalization_seals_the_session_and_stays_advisory() -> None:
    """Sealing records completion without promoting advisory evidence."""
    session_id = _open()
    state = finalize_live_simulation_session(session_id, request_id="req-final")
    assert state["finalized"] is True
    assert state["advisory"] is True
    assert state["exposure_blocked"] is True
    assert state["permitted_actions"] == ("read", "reproduce", "close")


@pytest.mark.usefixtures("engine")
def test_finalized_session_rejects_further_advance() -> None:
    """A sealed journal cannot gain new ticks."""
    session_id = _open()
    finalize_live_simulation_session(session_id, request_id="req-final")
    with pytest.raises(SimulationError) as failure:
        step_live_simulation(session_id, 1)
    assert failure.value.code == "SIMULATION_SESSION_FINALIZED"


@pytest.mark.anyio
@pytest.mark.usefixtures("engine")
async def test_finalized_session_rejects_further_commands() -> None:
    """A sealed journal cannot gain new receipts."""
    session_id = _open()
    finalize_live_simulation_session(session_id, request_id="req-final")
    with pytest.raises(SimulationError) as failure:
        await execute_live_simulation_command(
            session_id, {"command": "cancel_pending_order", "order_id": "order-7"}
        )
    assert failure.value.code == "SIMULATION_SESSION_FINALIZED"


@pytest.mark.usefixtures("engine")
def test_finalizing_twice_is_refused() -> None:
    """Sealing is a one-way transition, not a repeatable write."""
    session_id = _open()
    finalize_live_simulation_session(session_id, request_id="req-final")
    with pytest.raises(SimulationError) as failure:
        finalize_live_simulation_session(session_id, request_id="req-final")
    assert failure.value.code == "SIMULATION_SESSION_FINALIZED"


@pytest.mark.usefixtures("engine")
def test_finalized_session_remains_readable() -> None:
    """Sealed evidence stays available for review and reproduction."""
    session_id = _open()
    finalize_live_simulation_session(session_id, request_id="req-final")
    state = read_live_simulation_state(session_id)
    assert state["finalized"] is True
    assert state["finalized_at"] is not None


# --- Viewport --------------------------------------------------------------


@pytest.mark.usefixtures("engine")
def test_viewport_never_returns_a_row_beyond_the_cursor() -> None:
    """A visual practice surface cannot see a bar the session has not reached."""
    session_id = _open()
    step_live_simulation(session_id, 3)
    viewport = live_sessions.read_live_simulation_viewport(session_id, before=10)
    assert viewport["cursor"] == 3
    assert viewport["after"] == 0
    assert len(viewport["rows"]) == 3  # type: ignore[arg-type]


@pytest.mark.usefixtures("engine")
def test_viewport_is_bounded_to_the_requested_row_count() -> None:
    """A viewport returns at most the rows the caller asked for."""
    session_id = _open()
    step_live_simulation(session_id, 5)
    viewport = live_sessions.read_live_simulation_viewport(session_id, before=2)
    assert len(viewport["rows"]) == 2  # type: ignore[arg-type]


@pytest.mark.usefixtures("engine")
def test_viewport_row_count_is_bounded() -> None:
    """An unbounded viewport request is refused rather than truncated silently."""
    session_id = _open()
    with pytest.raises(SimulationError) as failure:
        live_sessions.read_live_simulation_viewport(
            session_id, before=live_sessions.MAX_VIEWPORT_BEFORE + 1
        )
    assert failure.value.code == "SIM_INVALID_CONFIG"


@pytest.mark.usefixtures("engine")
def test_viewport_at_the_start_is_empty() -> None:
    """A session that has executed nothing shows no market history."""
    session_id = _open()
    viewport = live_sessions.read_live_simulation_viewport(session_id)
    assert viewport["rows"] == ()
