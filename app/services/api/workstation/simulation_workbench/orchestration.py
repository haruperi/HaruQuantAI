"""Simulation Workbench orchestration composition (FEAT-API-27).

The gateway owns no part of simulation itself. It composes the durable
catalogue (registry plus persistence), the typed live-session authority
(wired by the interactive-session tasks), and the bounded viewport rules
behind one dispatch source consumed by the routes.
"""

from __future__ import annotations

import json
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from typing import Any, cast

from app.services.api.workstation.simulation_workbench.migrations import (
    get_simulation_workbench_migration_steps,
)
from app.services.api.workstation.simulation_workbench.persistence import (
    create_simulation_session_record,
    read_simulation_batch_items,
    read_simulation_batch_record,
    read_simulation_result_record,
    read_simulation_results_page,
    read_simulation_session_record,
    read_simulation_sessions,
)
from app.services.api.workstation.simulation_workbench.registry import (
    SimulationWorkbenchRegistry,
    build_simulation_workbench_registry,
)
from app.services.api.workstation.simulation_workbench.schemas import (
    DEFAULT_PAGE_SIZE,
    DEFAULT_VIEWPORT_BEFORE,
    MAX_PAGE_SIZE,
    MAX_VIEWPORT_BEFORE,
    VIEWPORT_AFTER,
)
from app.services.simulator import (
    branch_live_simulation,
    close_live_simulation_session,
    execute_live_simulation_command,
    finalize_live_simulation_session,
    read_live_simulation_state,
    read_live_simulation_viewport,
    rearm_live_simulation_session,
    restore_live_simulation_session,
    seek_live_simulation,
    step_live_simulation,
)
from app.utils import format_utc_timestamp, generate_id, get_logger, utc_now

logger = get_logger(__name__)

type _LiveAuthority = Callable[..., object]
type _BatchRunner = Callable[..., object]


@dataclass(frozen=True, slots=True)
class _WorkbenchContext:
    """Injected composition dependencies for the dispatch handlers."""

    registry: SimulationWorkbenchRegistry
    live_authority: _LiveAuthority | None
    batch_runner: _BatchRunner | None


def _common(kwargs: dict[str, object]) -> tuple[str, str]:
    """Extract the principal and request identities from handler kwargs.

    Args:
        kwargs: Caller keyword arguments.

    Returns:
        Principal identity and canonical request identity.
    """
    principal_id = str(kwargs.pop("principal_id", ""))
    request_id = str(kwargs.pop("request_id", "") or generate_id("req"))
    return principal_id, request_id


def _create_session(
    _context: _WorkbenchContext, run_id: str, **kwargs: object
) -> object:
    """Open one practice session over a completed owned run.

    Returns:
        Created session row, or ``None`` for an unknown or foreign run.

    Raises:
        ValueError: If the run has not completed.
    """
    principal_id, request_id = _common(kwargs)
    rows = read_simulation_result_record(run_id, principal_id, request_id=request_id)
    if not rows:
        return None
    if str(rows[0]["status"]) != "completed":
        raise ValueError("SIMULATION_RUN_NOT_COMPLETED")
    durable = bool(kwargs.get("durable", False))
    session_id = generate_id("ses")
    now = format_utc_timestamp(utc_now())
    create_simulation_session_record(
        {
            "session_id": session_id,
            "principal_id": principal_id,
            "run_id": run_id,
            "mode": "practice",
            "evidence_class": "practice",
            "status": "active",
            "cursor": -1,
            "tick_count": 0,
            "completed": 0,
            "durable": 1 if durable else 0,
            "state_hash": None,
            "closed_at": None,
            "created_at": now,
            "updated_at": now,
        },
        request_id=request_id,
    )
    return read_simulation_session_record(
        session_id, principal_id, request_id=request_id
    )[0]


def _list_sessions(_context: _WorkbenchContext, **kwargs: object) -> object:
    """List the principal's live sessions.

    Returns:
        Session rows newest first.
    """
    principal_id, request_id = _common(kwargs)
    return read_simulation_sessions(principal_id, request_id=request_id)


def _get_session(
    _context: _WorkbenchContext, session_id: str, **kwargs: object
) -> object:
    """Read one owned session row.

    Returns:
        Session row, or ``None`` when unknown or foreign-owned.
    """
    principal_id, request_id = _common(kwargs)
    rows = read_simulation_session_record(
        session_id, principal_id, request_id=request_id
    )
    return rows[0] if rows else None


def _viewport(context: _WorkbenchContext, session_id: str, **kwargs: object) -> object:
    """Return one backwards-only viewport through the live authority.

    Returns:
        Bounded viewport rows from the live authority.

    Raises:
        ValueError: If the viewport would expose future rows.
        RuntimeError: If the live authority is not composed.
    """
    # The viewport is backwards-only by contract; ``after`` is frozen
    # at zero so no future row can ever be requested.
    principal_id, request_id = _common(kwargs)
    before = int(str(kwargs.get("before", DEFAULT_VIEWPORT_BEFORE)))
    after = int(str(kwargs.get("after", VIEWPORT_AFTER)))
    if after != VIEWPORT_AFTER or not 1 <= before <= MAX_VIEWPORT_BEFORE:
        raise ValueError("SIMULATION_VIEWPORT_INVALID")
    if context.live_authority is None:
        raise RuntimeError("SIMULATION_WORKBENCH_RUNTIME_UNAVAILABLE")
    return context.live_authority(
        "viewport",
        session_id,
        before=before,
        after=after,
        request_id=request_id,
        principal_id=principal_id,
    )


def _delegated(context: _WorkbenchContext, session_id: str, **kwargs: object) -> object:
    """Delegate one interactive operation to the live authority.

    Returns:
        Live-authority operation result, or ``None`` for unknown sessions.

    Raises:
        RuntimeError: If the live authority is not composed.
    """
    principal_id, request_id = _common(kwargs)
    operation = str(kwargs.pop("_operation"))
    rows = read_simulation_session_record(
        session_id, principal_id, request_id=request_id
    )
    if not rows:
        return None
    if context.live_authority is None:
        raise RuntimeError("SIMULATION_WORKBENCH_RUNTIME_UNAVAILABLE")
    return context.live_authority(
        operation,
        session_id,
        request_id=request_id,
        principal_id=principal_id,
        **kwargs,
    )


def _page_runs(_context: _WorkbenchContext, **kwargs: object) -> object:
    """Read one descending catalogue page for the principal.

    Returns:
        Catalogue rows ordered by creation descending.
    """
    principal_id, request_id = _common(kwargs)
    limit = min(int(str(kwargs.get("limit", DEFAULT_PAGE_SIZE))), MAX_PAGE_SIZE)
    offset = max(int(str(kwargs.get("offset", 0))), 0)
    return project_catalogue_rows(
        read_simulation_results_page(
            principal_id, limit=limit, offset=offset, request_id=request_id
        )
    )


def _get_run(_context: _WorkbenchContext, run_id: str, **kwargs: object) -> object:
    """Read one owned catalogue run row.

    Returns:
        Run row, or ``None`` when unknown or foreign-owned.
    """
    principal_id, request_id = _common(kwargs)
    rows = read_simulation_result_record(run_id, principal_id, request_id=request_id)
    return project_catalogue_row(rows[0]) if rows else None


def _register_run(
    context: _WorkbenchContext, values: Mapping[str, object], **kwargs: object
) -> object:
    """Register one catalogue run row identity-idempotently.

    Returns:
        True when a new row was created.
    """
    _, request_id = _common(kwargs)
    return context.registry.register_run(values, request_id=request_id)


def _complete_run(context: _WorkbenchContext, run_id: str, **kwargs: object) -> object:
    """Complete one active run after attaching its report.

    Returns:
        Updated catalogue row.

    Raises:
        SimulationWorkbenchConflictError: On guarded transition conflicts.
    """
    principal_id, request_id = _common(kwargs)
    return context.registry.complete_run(
        run_id,
        principal_id,
        request_id=request_id,
        report_json=cast("str | None", kwargs.get("report_json")),
        evidence=cast("Mapping[str, object] | None", kwargs.get("evidence")),
    )


def _create_batch(
    context: _WorkbenchContext, payload: object, **kwargs: object
) -> object:
    """Submit one bounded batch through the batch runner.

    Returns:
        Accepted batch projection.

    Raises:
        RuntimeError: If the batch runner is not composed.
    """
    principal_id, request_id = _common(kwargs)
    if context.batch_runner is None:
        raise RuntimeError("SIMULATION_WORKBENCH_RUNTIME_UNAVAILABLE")
    return context.batch_runner(
        "create_batch", payload, principal_id=principal_id, request_id=request_id
    )


def _get_batch(_context: _WorkbenchContext, batch_id: str, **kwargs: object) -> object:
    """Read one owned batch with its ordered items.

    Returns:
        Batch projection with items, or ``None`` when unknown or foreign.
    """
    principal_id, request_id = _common(kwargs)
    rows = read_simulation_batch_record(batch_id, principal_id, request_id=request_id)
    if not rows:
        return None
    items = read_simulation_batch_items(batch_id, principal_id, request_id=request_id)
    return {"batch": rows[0], "items": items}


def _stream_batch(
    context: _WorkbenchContext, batch_id: str, **kwargs: object
) -> object:
    """Open one ordered batch stream through the batch runner.

    Returns:
        Batch stream handle, or ``None`` when unknown or foreign.

    Raises:
        RuntimeError: If the batch runner is not composed.
    """
    principal_id, _ = _common(kwargs)
    if not read_simulation_batch_record(
        batch_id, principal_id, request_id=generate_id("req")
    ):
        return None
    if context.batch_runner is None:
        raise RuntimeError("SIMULATION_WORKBENCH_RUNTIME_UNAVAILABLE")
    return context.batch_runner(
        "stream_batch", batch_id, principal_id=principal_id, **kwargs
    )


def _cancel_batch(
    context: _WorkbenchContext, batch_id: str, **kwargs: object
) -> object:
    """Cancel every non-terminal item of one owned batch once.

    Returns:
        Cancellation result with cancelled item count.

    Raises:
        SimulationWorkbenchConflictError: When the batch is unknown or foreign.
    """
    principal_id, request_id = _common(kwargs)
    return context.registry.cancel_batch(batch_id, principal_id, request_id=request_id)


def _retry_failed(
    context: _WorkbenchContext, batch_id: str, **kwargs: object
) -> object:
    """Retry only the failed items of one owned batch.

    Returns:
        Retry result with retried item count.

    Raises:
        RuntimeError: If the batch runner is not composed.
        SimulationWorkbenchConflictError: When the batch is unknown or foreign.
    """
    principal_id, request_id = _common(kwargs)
    runner = context.batch_runner
    if runner is None:
        raise RuntimeError("SIMULATION_WORKBENCH_RUNTIME_UNAVAILABLE")

    def resubmit(item: Mapping[str, object]) -> str:
        return str(runner("resubmit", item, principal_id=principal_id))

    return context.registry.retry_failed_batch_items(
        batch_id, principal_id, request_id=request_id, resubmit=resubmit
    )


def _interactive(name: str) -> Callable[..., object]:
    """Build one delegating handler for a named interactive operation.

    Args:
        name: Interactive operation name.

    Returns:
        Handler delegating to the live authority with the name bound.
    """

    def handler(
        context: _WorkbenchContext, session_id: str, **kwargs: object
    ) -> object:
        """Delegate one named interactive operation.

        Returns:
            Live-authority result, or ``None`` for unknown sessions.
        """
        return _delegated(context, session_id, _operation=name, **kwargs)

    return handler


def _unwrap(response: object) -> object:
    """Return the payload of one Simulator response envelope.

    Args:
        response: Simulator ``StandardResponse`` or a raw payload.

    Returns:
        The owner payload.

    Raises:
        ValueError: If the Simulator reported a failure.
    """
    status_value = getattr(response, "status", None)
    if status_value is None:
        return response
    if str(status_value) != "success":
        error = getattr(response, "error", None)
        raise ValueError(str(getattr(error, "code", "SIMULATION_OPERATION_FAILED")))
    return getattr(response, "data", None)


def _session_is_finalized(session: object) -> bool:
    """Return whether one Simulator session projection is sealed.

    Args:
        session: Simulator-owned session projection.

    Returns:
        True when the owner marked the session finalized.
    """
    return isinstance(session, Mapping) and bool(session.get("finalized", False))


async def _run_command(session_id: str, kwargs: Mapping[str, object]) -> object:
    """Execute one manual command and return receipt plus refreshed state.

    Args:
        session_id: Owned session identity.
        kwargs: Route keyword arguments carrying the command mapping.

    Returns:
        Owner receipt evidence and refreshed session projection.
    """
    command = cast("Mapping[str, object]", kwargs.get("command", {}))
    return _unwrap(await execute_live_simulation_command(session_id, command))


def _self_contained_handlers() -> Mapping[str, Callable[..., object]]:
    """Build handlers that need no composed Simulator dependency bundle.

    Returns:
        Mapping of operation name to delegating handler.
    """
    return {
        "viewport": lambda session_id, kwargs: _unwrap(
            read_live_simulation_viewport(
                session_id,
                before=int(str(kwargs.get("before", DEFAULT_VIEWPORT_BEFORE))),
            )
        ),
        "step": lambda session_id, kwargs: _unwrap(
            step_live_simulation(session_id, int(str(kwargs.get("ticks", 1))))
        ),
        "seek": lambda session_id, kwargs: _unwrap(
            seek_live_simulation(session_id, int(str(kwargs.get("target_cursor", 0))))
        ),
        "command": _run_command,
        "close_session": lambda session_id, _kwargs: _unwrap(
            close_live_simulation_session(session_id)
        ),
        "finalize": lambda session_id, kwargs: _unwrap(
            finalize_live_simulation_session(
                session_id, request_id=str(kwargs.get("request_id", ""))
            )
        ),
        "rearm": lambda session_id, kwargs: _unwrap(
            rearm_live_simulation_session(
                session_id,
                approved=bool(kwargs.get("approved", False)),
                request_id=str(kwargs.get("request_id", "")),
            )
        ),
    }


def build_simulation_workbench_live_authority(
    dependencies: object | None,
    *,
    reproduction_runner: Callable[..., object] | None = None,
) -> _LiveAuthority:
    """Build the interactive live-session authority for the workbench routes.

    The gateway owns none of this behaviour: each operation delegates to the
    Simulator's public live-session surface and returns the owner projection
    unchanged. The one rule the gateway does enforce is that reproduction
    requires finalized evidence, because reproducing a session that is still
    moving would capture a state no one reviewed.

    Args:
        dependencies: Composed Simulator run dependency bundle.
        reproduction_runner: Callable submitting one canonical job from a
            finalized session projection.

    Returns:
        Callable dispatching one named interactive operation.
    """

    def _reproduce(session_id: str, kwargs: Mapping[str, object]) -> object:
        """Submit one canonical job reproducing a finalized session.

        Returns:
            Canonical job projection produced by the reproduction runner.

        Raises:
            ValueError: If the session is not finalized, or if no reproduction
                runner is composed.
        """
        session = _unwrap(read_live_simulation_state(session_id))
        if not _session_is_finalized(session):
            raise ValueError("SIMULATION_SESSION_NOT_FINALIZED")
        if reproduction_runner is None:
            raise ValueError("SIMULATION_REPRODUCTION_UNAVAILABLE")
        return reproduction_runner(
            session,
            request_id=str(kwargs.get("request_id", "")),
            principal_id=str(kwargs.get("principal_id", "")),
        )

    handlers: dict[str, Callable[..., object]] = dict(_self_contained_handlers())
    handlers["branch"] = lambda session_id, kwargs: _unwrap(
        branch_live_simulation(
            session_id,
            cast("Mapping[str, object]", kwargs.get("overrides", {})),
            dependencies,
            request_id=str(kwargs.get("request_id", "")),
        )
    )
    handlers["restore"] = lambda session_id, kwargs: _unwrap(
        restore_live_simulation_session(
            session_id, dependencies, request_id=str(kwargs.get("request_id", ""))
        )
    )
    handlers["reproduce"] = _reproduce
    requires_bundle = frozenset({"branch", "restore", "reproduce"})

    def authority(operation: str, session_id: str, **kwargs: object) -> object:
        """Delegate one interactive operation to the Simulator.

        Returns:
            Simulator-owned projection, or an awaitable for manual commands.

        Raises:
            RuntimeError: If a required Simulator dependency bundle is absent.
            ValueError: If the operation is unsupported.
        """
        handler = handlers.get(operation)
        if handler is None:
            raise ValueError("unsupported interactive Simulation operation")
        if operation in requires_bundle and dependencies is None:
            raise RuntimeError("SIMULATION_WORKBENCH_RUNTIME_UNAVAILABLE")
        return handler(session_id, kwargs)

    return authority


def build_simulation_workbench_source(
    *,
    registry: SimulationWorkbenchRegistry | None = None,
    live_authority: _LiveAuthority | None = None,
    batch_runner: _BatchRunner | None = None,
) -> Callable[..., object]:
    """Build the dispatch source covering every workbench operation.

    Args:
        registry: Catalogue transition registry; built on demand when absent.
        live_authority: Interactive live-session authority dispatcher; every
            interactive operation fails closed until it is composed.
        batch_runner: Canonical batch execution dispatcher; batch streaming
            and submission fail closed until it is composed.

    Returns:
        Callable dispatching one allowlisted workbench operation.
    """
    context = _WorkbenchContext(
        registry=registry
        or cast("SimulationWorkbenchRegistry", build_simulation_workbench_registry()),
        live_authority=live_authority,
        batch_runner=batch_runner,
    )
    routed: dict[str, Callable[..., object]] = {
        "create_session": _create_session,
        "list_sessions": _list_sessions,
        "get_session": _get_session,
        "viewport": _viewport,
        "delete_session": _get_session,
        "page_runs": _page_runs,
        "get_run": _get_run,
        "register_run": _register_run,
        "complete_run": _complete_run,
        "create_batch": _create_batch,
        "get_batch": _get_batch,
        "stream_batch": _stream_batch,
        "cancel_batch": _cancel_batch,
        "retry_failed": _retry_failed,
    }
    for name in (
        "step",
        "seek",
        "command",
        "branch",
        "restore",
        "rearm",
        "finalize",
        "reproduce",
        "close_session",
    ):
        routed[name] = _interactive(name)

    def dispatch(operation: str, *args: object, **kwargs: object) -> object:
        """Execute one Simulation Workbench operation.

        Returns:
            Operation result; ``None`` signals an unknown or foreign resource.

        Raises:
            RuntimeError: If an uncomposed authority is required.
            ValueError: If the operation is unsupported or input invalid.
            SimulationWorkbenchConflictError: On guarded transition conflicts.
        """
        handler = routed.get(operation)
        if handler is None:
            raise ValueError("unsupported Simulation workbench operation")
        return handler(context, *args, **kwargs)

    return dispatch


def build_simulation_workbench_source_bundle() -> Mapping[str, object]:
    """Build the default uncomposed composition source bundle.

    Returns:
        Opaque composition source consumed by the application factory;
        interactive authorities remain fail-closed until their tasks
        compose them.
    """
    logger.info("Building Simulation workbench composition source")
    return {
        "migration_steps": get_simulation_workbench_migration_steps(),
        "source": build_simulation_workbench_source(),
    }


def deserialize_json_list(value: object) -> tuple[str, ...]:
    """Decode one durable JSON text column into its contract tuple.

    The catalogue stores ``symbols`` and ``tags`` as JSON text, but
    ``RunCatalogueEntry`` publishes both as arrays. Rows must therefore be
    projected back into contract shape before they cross the boundary.

    Args:
        value: Durable JSON text, an already-decoded sequence, or ``None``.

    Returns:
        Decoded string tuple; empty when the column holds nothing usable.
    """
    if value is None:
        return ()
    if isinstance(value, str):
        try:
            decoded = json.loads(value)
        except ValueError:
            return ()
    else:
        decoded = value
    if not isinstance(decoded, list | tuple):
        return ()
    return tuple(str(item) for item in cast("Sequence[object]", decoded))


def project_catalogue_row(row: Mapping[str, object]) -> Mapping[str, object]:
    """Project one durable catalogue row into its published contract shape.

    Args:
        row: Exact durable ``api_simulation_results`` row.

    Returns:
        The same row with its JSON text columns decoded into arrays.
    """
    return {
        **row,
        "symbols": deserialize_json_list(row.get("symbols")),
        "tags": deserialize_json_list(row.get("tags")),
    }


def project_catalogue_rows(
    rows: Sequence[Mapping[str, object]],
) -> tuple[Mapping[str, object], ...]:
    """Project every durable catalogue row into published contract shape.

    Args:
        rows: Ordered durable catalogue rows.

    Returns:
        Ordered rows with their JSON text columns decoded into arrays.
    """
    return tuple(project_catalogue_row(row) for row in rows)


def serialize_tags(tags: object) -> str:
    """Serialize one bounded tag tuple for catalogue storage.

    Args:
        tags: Tag sequence or serialized tag text.

    Returns:
        Canonical JSON tag list text.
    """
    if isinstance(tags, str):
        return tags
    return json.dumps(list(cast("Any", tags)))


__all__ = (
    "build_simulation_workbench_live_authority",
    "build_simulation_workbench_source",
    "build_simulation_workbench_source_bundle",
    "deserialize_json_list",
    "project_catalogue_row",
    "project_catalogue_rows",
    "serialize_tags",
)
