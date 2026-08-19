"""Composed interactive live-session authority for the Simulation Workbench.

The gateway owns no simulation behaviour, so these tests prove delegation
rather than simulation: each operation reaches the matching Simulator function
with the caller's inputs, and reproduction refuses to run until the owner
reports the session as finalized.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import pytest
from app.services.api.workstation.simulation_workbench import orchestration
from app.services.api.workstation.simulation_workbench.orchestration import (
    build_simulation_workbench_live_authority,
)


class _Response:
    """Simulator response envelope stand-in."""

    def __init__(self, data: object, *, status: str = "success") -> None:
        """Record the envelope payload.

        Args:
            data: Owner payload.
            status: Envelope status.
        """
        self.status = status
        self.data = data
        self.error = _Error("SIM_UNSUPPORTED_OPERATION")


class _Error:
    """Simulator error stand-in."""

    def __init__(self, code: str) -> None:
        """Record the failure code.

        Args:
            code: Owner error code.
        """
        self.code = code


@pytest.fixture
def calls(monkeypatch: pytest.MonkeyPatch) -> dict[str, Any]:
    """Replace every delegated Simulator operation with a recorder.

    Args:
        monkeypatch: Pytest patching fixture.

    Returns:
        Mapping recording the arguments each delegated operation received.
    """
    recorded: dict[str, Any] = {}

    def _record(name: str, payload: object) -> Any:
        def _handler(*args: object, **kwargs: object) -> object:
            recorded[name] = (args, kwargs)
            return _Response(payload)

        return _handler

    monkeypatch.setattr(
        orchestration,
        "read_live_simulation_viewport",
        _record("viewport", {"cursor": 3, "rows": ()}),
    )
    monkeypatch.setattr(
        orchestration, "step_live_simulation", _record("step", {"cursor": 4})
    )
    monkeypatch.setattr(
        orchestration, "seek_live_simulation", _record("seek", {"cursor": 9})
    )
    monkeypatch.setattr(
        orchestration,
        "close_live_simulation_session",
        _record("close", {"session_id": "s-1"}),
    )
    monkeypatch.setattr(
        orchestration,
        "finalize_live_simulation_session",
        _record("finalize", {"finalized": True}),
    )
    monkeypatch.setattr(
        orchestration,
        "rearm_live_simulation_session",
        _record("rearm", {"recovery_state": "running"}),
    )
    monkeypatch.setattr(
        orchestration,
        "branch_live_simulation",
        _record("branch", {"session_id": "s-2"}),
    )
    monkeypatch.setattr(
        orchestration,
        "restore_live_simulation_session",
        _record("restore", {"recovery_state": "recovery_blocked"}),
    )
    return recorded


def test_viewport_forwards_the_bounded_row_count(calls: dict[str, Any]) -> None:
    """The gateway passes the caller's bound to the Simulator unchanged."""
    authority = build_simulation_workbench_live_authority(object())
    result = authority("viewport", "s-1", before=120)
    assert calls["viewport"][1]["before"] == 120
    assert result == {"cursor": 3, "rows": ()}


def test_seek_forwards_the_absolute_target(calls: dict[str, Any]) -> None:
    """Seek delegates the absolute cursor rather than a relative delta."""
    authority = build_simulation_workbench_live_authority(object())
    authority("seek", "s-1", target_cursor=9)
    assert calls["seek"][0] == ("s-1", 9)


def test_step_forwards_the_tick_count(calls: dict[str, Any]) -> None:
    """Stepping delegates the requested bounded tick count."""
    authority = build_simulation_workbench_live_authority(object())
    authority("step", "s-1", ticks=25)
    assert calls["step"][0] == ("s-1", 25)


def test_rearm_forwards_the_explicit_approval(calls: dict[str, Any]) -> None:
    """Rearm stays an explicit operator decision, never an implied one."""
    authority = build_simulation_workbench_live_authority(object())
    authority("rearm", "s-1", approved=True, request_id="req-1")
    assert calls["rearm"][1]["approved"] is True


@pytest.mark.usefixtures("calls")
def test_unsupported_operation_is_refused() -> None:
    """Only the composed interactive operations are reachable."""
    authority = build_simulation_workbench_live_authority(object())
    with pytest.raises(ValueError, match="unsupported interactive"):
        authority("liquidate", "s-1")


@pytest.mark.usefixtures("calls")
def test_branch_requires_a_composed_dependency_bundle() -> None:
    """An operation needing the Simulator bundle fails closed without it."""
    authority = build_simulation_workbench_live_authority(None)
    with pytest.raises(RuntimeError, match="SIMULATION_WORKBENCH_RUNTIME_UNAVAILABLE"):
        authority("branch", "s-1", overrides={}, request_id="req-1")


@pytest.mark.usefixtures("calls")
def test_self_contained_operations_need_no_bundle() -> None:
    """Reading a viewport does not require a composed run bundle."""
    authority = build_simulation_workbench_live_authority(None)
    assert authority("viewport", "s-1", before=10) == {"cursor": 3, "rows": ()}


def test_owner_failure_surfaces_the_owner_code(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A Simulator failure is reported, never smoothed into a success."""
    monkeypatch.setattr(
        orchestration,
        "step_live_simulation",
        lambda *_a, **_k: _Response(None, status="error"),
    )
    authority = build_simulation_workbench_live_authority(object())
    with pytest.raises(ValueError, match="SIM_UNSUPPORTED_OPERATION"):
        authority("step", "s-1", ticks=1)


# --- Reproduction ----------------------------------------------------------


def _with_session(
    monkeypatch: pytest.MonkeyPatch, session: Mapping[str, object]
) -> None:
    """Bind one Simulator session projection to the authority.

    Args:
        monkeypatch: Pytest patching fixture.
        session: Session projection the Simulator should report.
    """
    monkeypatch.setattr(
        orchestration,
        "read_live_simulation_state",
        lambda *_a, **_k: _Response(session),
    )


def test_reproduction_refuses_an_unfinalized_session(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Reproducing a moving session would capture a state nobody reviewed."""
    _with_session(monkeypatch, {"session_id": "s-1", "finalized": False})
    submitted: list[object] = []
    authority = build_simulation_workbench_live_authority(
        object(), reproduction_runner=lambda *a, **_k: submitted.append(a)
    )
    with pytest.raises(ValueError, match="SIMULATION_SESSION_NOT_FINALIZED"):
        authority("reproduce", "s-1", request_id="req-1", principal_id="user-1")
    assert submitted == []


def test_reproduction_creates_a_distinct_canonical_job(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A finalized session reproduces into its own canonical job."""
    session = {"session_id": "s-1", "run_id": "advisory-1", "finalized": True}
    _with_session(monkeypatch, session)
    submitted: list[tuple[object, dict[str, object]]] = []

    def _runner(projection: object, **kwargs: object) -> object:
        submitted.append((projection, dict(kwargs)))
        return {"job_id": "canonical-77"}

    authority = build_simulation_workbench_live_authority(
        object(), reproduction_runner=_runner
    )
    result = authority("reproduce", "s-1", request_id="req-1", principal_id="user-1")

    assert result == {"job_id": "canonical-77"}
    assert submitted[0][0] == session
    assert submitted[0][1]["principal_id"] == "user-1"


def test_reproduction_without_a_composed_runner_fails_closed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Reproduction cannot silently succeed without a canonical submitter."""
    _with_session(monkeypatch, {"session_id": "s-1", "finalized": True})
    authority = build_simulation_workbench_live_authority(object())
    with pytest.raises(ValueError, match="SIMULATION_REPRODUCTION_UNAVAILABLE"):
        authority("reproduce", "s-1", request_id="req-1", principal_id="user-1")


@pytest.mark.anyio
async def test_command_returns_an_awaitable_resolving_to_owner_evidence(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Manual commands stay asynchronous all the way to the Simulator."""
    recorded: dict[str, object] = {}

    async def _execute(session_id: str, command: Mapping[str, object]) -> object:
        recorded["session_id"] = session_id
        recorded["command"] = dict(command)
        return _Response({"receipts": (), "session": {"session_id": session_id}})

    monkeypatch.setattr(orchestration, "execute_live_simulation_command", _execute)
    authority = build_simulation_workbench_live_authority(object())
    result = await authority(
        "command", "s-1", command={"command": "close_all_practice_exposure"}
    )
    assert recorded["session_id"] == "s-1"
    assert result["session"]["session_id"] == "s-1"  # type: ignore[index]
