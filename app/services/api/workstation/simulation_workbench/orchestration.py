"""Simulation Workbench orchestration composition (FEAT-API-27).

The gateway owns no part of simulation itself. It composes the durable
catalogue (registry plus persistence), the typed live-session authority
(wired by the interactive-session tasks), and the bounded viewport rules
behind one dispatch source consumed by the routes.
"""

from __future__ import annotations

import json
from collections.abc import Callable, Mapping
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
    return read_simulation_results_page(
        principal_id, limit=limit, offset=offset, request_id=request_id
    )


def _get_run(_context: _WorkbenchContext, run_id: str, **kwargs: object) -> object:
    """Read one owned catalogue run row.

    Returns:
        Run row, or ``None`` when unknown or foreign-owned.
    """
    principal_id, request_id = _common(kwargs)
    rows = read_simulation_result_record(run_id, principal_id, request_id=request_id)
    return rows[0] if rows else None


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
    "build_simulation_workbench_source",
    "build_simulation_workbench_source_bundle",
    "serialize_tags",
)
