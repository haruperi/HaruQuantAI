"""Canonical reproduction of finalized practice sessions (FEAT-API-27).

Reproducing a session means executing its exact immutable request through
the deterministic canonical engine a second time — nothing about the
advisory practice run is replayed or trusted. The gateway supplies only the
provenance link back to the session it reproduced; every number in the
resulting evidence is produced by the Simulator from scratch.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import cast

from app.utils import get_logger

logger = get_logger(__name__)


def _session_identity(session: object) -> str:
    """Return the session identity carried by one owner projection.

    Args:
        session: Simulator-owned live-session projection.

    Returns:
        Canonical session identity.

    Raises:
        ValueError: If the projection carries no session identity.
    """
    if isinstance(session, Mapping):
        session_id = session.get("session_id")
    else:
        session_id = getattr(session, "session_id", None)
    if not session_id:
        raise ValueError("SIMULATION_SESSION_NOT_FOUND")
    return str(session_id)


def build_reproduction_runner(
    run_source: Callable[..., object],
    *,
    session_request_reader: Callable[[str], Mapping[str, object] | None] | None = None,
    provenance: Callable[[str, Mapping[str, object]], None] | None = None,
) -> Callable[..., object]:
    """Build the runner submitting one canonical job from a finalized session.

    Args:
        run_source: Composed Simulator run dispatcher accepting ``submit``.
        session_request_reader: Callable returning the durable session's
            immutable canonical request; the Simulator reader is used when
            absent.
        provenance: Callable recording the gateway-owned origin of the
            submitted job so its catalogue row records the source session.

    Returns:
        Callable accepting one finalized session projection and returning the
        canonical job projection reproducing it.
    """

    def read_request(session_id: str) -> Mapping[str, object] | None:
        """Read one durable session's immutable canonical request.

        Args:
            session_id: Canonical session identity.

        Returns:
            Immutable canonical request mapping, or ``None`` when the durable
            record or its request is absent.
        """
        if session_request_reader is not None:
            return session_request_reader(session_id)
        from app.services.simulator import read_live_simulation_request

        response = read_live_simulation_request(session_id)
        return cast("Mapping[str, object] | None", getattr(response, "data", response))

    def reproduce(session: object, **kwargs: object) -> object:
        """Submit one canonical job reproducing a finalized session.

        Args:
            session: Finalized Simulator-owned live-session projection.
            **kwargs: Principal and request identities from the route.

        Returns:
            Compact canonical job projection for the reproducing run.

        Raises:
            ValueError: If the session holds no durable immutable request.
        """
        from app.services.api.widgets.simulator.schemas import SimulatorRunRequest

        session_id = _session_identity(session)
        principal_id = str(kwargs.get("principal_id", ""))
        request = read_request(session_id)
        if not request:
            raise ValueError("SIMULATION_SESSION_NOT_REPRODUCIBLE")
        submitted = SimulatorRunRequest.model_validate(
            {
                "symbol": request["symbol"],
                "timeframe": request["timeframe"],
                "strategy_id": request["strategy_id"],
                "start": request["start"],
                "end": request["end"],
                "parameters": dict(
                    cast("Mapping[str, str]", request.get("parameters", {}))
                ),
                "initial_balance": request["initial_balance"],
                "account_currency": request["account_currency"],
                "seed": request["seed"],
            }
        )
        snapshot = cast(
            "Mapping[str, object]",
            run_source("submit", submitted, principal_id=principal_id),
        )
        if provenance is not None:
            provenance(
                str(snapshot.get("job_id", "")),
                {"origin_kind": "reproduction", "session_id": session_id},
            )
        logger.info("Reproducing finalized Simulation session %s", session_id)
        return snapshot

    return reproduce


__all__ = ("build_reproduction_runner",)
