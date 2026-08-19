"""Durable HTTP idempotency reservation and terminal replay records."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Awaitable, Callable
from datetime import datetime, timedelta
from typing import Literal

from fastapi import HTTPException, status
from pydantic import BaseModel, ConfigDict

from app.services.api.identity.errors import IdentityError
from app.services.api.identity.persistence import (
    create_idempotency_record,
    delete_idempotency_record,
    finalize_idempotency_record,
    read_idempotency_record,
)
from app.services.api.widgets.settings.limits import (
    HTTP_IDEMPOTENCY_RETENTION_SECONDS,
)
from app.utils import canonical_json, get_logger, utc_now

logger = get_logger(__name__)

_MAX_TERMINAL_RESPONSE_BYTES = 1_000_000


class IdempotencyDecision(BaseModel):
    """Outcome of a durable idempotency reservation check."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    state: Literal["reserved", "replay"]
    response_json: str | None = None
    status_code: int | None = None


def _scope_key(principal_id: str, method: str, route: str, key: str) -> str:
    """Build the canonical idempotency scope digest.

    Returns:
        SHA-256 scope digest.
    """
    material = canonical_json(
        {
            "principal_id": principal_id,
            "method": method.upper(),
            "route": route,
            "key": key,
        }
    )
    return hashlib.sha256(material.encode("utf-8")).hexdigest()


def reserve_idempotency_key(
    *,
    principal_id: str,
    method: str,
    route: str,
    key: str,
    request_material: object,
    request_id: str,
    now: datetime | None = None,
) -> IdempotencyDecision:
    """Reserve a scoped key or return an identical terminal replay.

    Args:
        principal_id: Authenticated caller identity.
        method: Canonical HTTP method.
        route: Canonical route path.
        key: Caller-supplied idempotency key.
        request_material: Canonical validated request material.
        request_id: Operation request identifier.
        now: Injectable UTC instant.

    Returns:
        Reservation or replay decision.

    Raises:
        IdentityError: If the key conflicts or storage is unavailable.
    """
    logger.info("Checking one durable HTTP idempotency key")
    if not all((principal_id, method, route, key)):
        raise IdentityError("IDEMPOTENCY_KEY_REQUIRED")
    current = now or utc_now()
    scope_key = _scope_key(principal_id, method, route, key)
    request_hash = hashlib.sha256(
        canonical_json(request_material).encode("utf-8")
    ).hexdigest()
    rows = read_idempotency_record(scope_key, request_id=request_id)
    if rows:
        row = rows[0]
        if datetime.fromisoformat(str(row["expires_at"])) <= current:
            delete_idempotency_record(scope_key, request_id=request_id)
        elif str(row["request_hash"]) != request_hash:
            raise IdentityError("IDEMPOTENCY_CONFLICT")
        elif row["response_json"] is not None and row["status_code"] is not None:
            return IdempotencyDecision(
                state="replay",
                response_json=str(row["response_json"]),
                status_code=int(str(row["status_code"])),
            )
        else:
            raise IdentityError("DUPLICATE_IDEMPOTENCY_KEY")
    expires_at = current + timedelta(seconds=HTTP_IDEMPOTENCY_RETENTION_SECONDS)
    create_idempotency_record(
        scope_key=scope_key,
        request_hash=request_hash,
        created_at=current.isoformat(),
        expires_at=expires_at.isoformat(),
        request_id=request_id,
    )
    return IdempotencyDecision(state="reserved")


def finalize_idempotency_key(
    *,
    principal_id: str,
    method: str,
    route: str,
    key: str,
    response_json: str,
    status_code: int,
    request_id: str,
) -> None:
    """Persist a terminal replay-safe response for one reserved key.

    Args:
        principal_id: Authenticated caller identity.
        method: Canonical HTTP method.
        route: Canonical route path.
        key: Caller-supplied idempotency key.
        response_json: Bounded canonical terminal response.
        status_code: Terminal HTTP status.
        request_id: Operation request identifier.

    Raises:
        IdentityError: If the reservation is absent or persistence fails.
    """
    if len(response_json.encode("utf-8")) > _MAX_TERMINAL_RESPONSE_BYTES:
        raise IdentityError("IDEMPOTENCY_RESPONSE_TOO_LARGE")
    affected_rows = finalize_idempotency_record(
        scope_key=_scope_key(principal_id, method, route, key),
        response_json=response_json,
        status_code=status_code,
        request_id=request_id,
    )
    if affected_rows != 1:
        raise IdentityError("IDEMPOTENCY_RESERVATION_MISSING")


def run_idempotent_write(
    *,
    principal_id: str,
    method: str,
    route: str,
    key: str,
    request_material: object,
    request_id: str,
    operation: Callable[[], object],
    replay: Callable[[], object] | None = None,
) -> object:
    """Reserve one governed write, execute it once, and record its outcome.

    This is the single reserve-execute-finalize cycle shared by every governed
    route, so no route re-implements durable HTTP idempotency. A replayed key
    never re-executes ``operation``: the caller-supplied ``replay`` reader
    returns owner-authored truth instead, and when no reader is supplied the
    replay is reported to the caller rather than silently repeated.

    Finalization failure is logged but never rolls back an owner-completed
    write, because the owning domain has already recorded the effect and the
    gateway is not that effect's authority.

    Args:
        principal_id: Authenticated caller identity.
        method: Canonical HTTP method.
        route: Canonical route path.
        key: Caller-supplied idempotency key.
        request_material: Canonical request body used for the request hash.
        request_id: Operation request identifier.
        operation: Zero-argument callable performing the governed write once.
        replay: Optional zero-argument reader returning owner truth for a
            previously completed identical request.

    Returns:
        Result of the executed operation, or the replayed owner-authored value.

    Raises:
        IdentityError: If the key is a duplicate in flight or conflicts with a
            different request body.
        HTTPException: 409 when a terminal replay exists but the route supplies
            no owner read-back able to reproduce the original result.
    """
    replayed = _reserve_or_replay(
        principal_id=principal_id,
        method=method,
        route=route,
        key=key,
        request_material=request_material,
        request_id=request_id,
        replay=replay,
    )
    if replayed is not _RESERVED:
        return replayed

    result = operation()
    _finalize_quietly(
        principal_id=principal_id,
        method=method,
        route=route,
        key=key,
        request_id=request_id,
    )
    return result


async def run_idempotent_write_async(
    *,
    principal_id: str,
    method: str,
    route: str,
    key: str,
    request_material: object,
    request_id: str,
    operation: Callable[[], Awaitable[object]],
    replay: Callable[[], object] | None = None,
) -> object:
    """Asynchronous sibling of :func:`run_idempotent_write`.

    Trading mutations are the asynchronous governed writes at this boundary.
    Reservation happens before the awaited call and finalization after it, so a
    concurrent duplicate is rejected while the first request is still in flight
    rather than after it completes.

    Args:
        principal_id: Authenticated caller identity.
        method: Canonical HTTP method.
        route: Canonical route path.
        key: Caller-supplied idempotency key.
        request_material: Canonical request body used for the request hash.
        request_id: Operation request identifier.
        operation: Zero-argument awaitable performing the governed write once.
        replay: Optional zero-argument reader returning owner truth for a
            previously completed identical request.

    Returns:
        Result of the awaited operation, or the replayed owner-authored value.

    Raises:
        IdentityError: If the key is a duplicate in flight or conflicts with a
            different request body.
        HTTPException: 409 when a terminal replay exists but the route supplies
            no owner read-back able to reproduce the original result.
    """
    replayed = _reserve_or_replay(
        principal_id=principal_id,
        method=method,
        route=route,
        key=key,
        request_material=request_material,
        request_id=request_id,
        replay=replay,
    )
    if replayed is not _RESERVED:
        return replayed

    result = await operation()
    _finalize_quietly(
        principal_id=principal_id,
        method=method,
        route=route,
        key=key,
        request_id=request_id,
    )
    return result


_RESERVED = object()


def _reserve_or_replay(
    *,
    principal_id: str,
    method: str,
    route: str,
    key: str,
    request_material: object,
    request_id: str,
    replay: Callable[[], object] | None,
) -> object:
    """Reserve one key, or resolve an identical terminal replay.

    Args:
        principal_id: Authenticated caller identity.
        method: Canonical HTTP method.
        route: Canonical route path.
        key: Caller-supplied idempotency key.
        request_material: Canonical request body used for the request hash.
        request_id: Operation request identifier.
        replay: Optional owner read-back for a completed identical request.

    Returns:
        The sentinel ``_RESERVED`` when the caller should execute the write, or
        the replayed owner-authored value.

    Raises:
        HTTPException: 409 when a terminal replay exists but no read-back does.
    """
    decision = reserve_idempotency_key(
        principal_id=principal_id,
        method=method,
        route=route,
        key=key,
        request_material=request_material,
        request_id=request_id,
    )
    if decision.state != "replay":
        return _RESERVED
    if replay is None:
        # A terminal record exists for this exact key and body, but this route
        # has no owner read-back that could reproduce the original result.
        # Re-running the write would duplicate a governed effect, and inventing
        # a response would be worse, so the caller gets a bounded deterministic
        # conflict instead of a server error.
        logger.warning("Replayed governed key has no owner read-back: %s", route)
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="IDEMPOTENCY_CONFLICT",
        )
    return replay()


def _finalize_quietly(
    *,
    principal_id: str,
    method: str,
    route: str,
    key: str,
    request_id: str,
) -> None:
    """Record a terminal replay marker without rolling back a completed write.

    Args:
        principal_id: Authenticated caller identity.
        method: Canonical HTTP method.
        route: Canonical route path.
        key: Caller-supplied idempotency key.
        request_id: Operation request identifier.
    """
    try:
        finalize_idempotency_key(
            principal_id=principal_id,
            method=method,
            route=route,
            key=key,
            response_json=json.dumps({"request_id": request_id}, sort_keys=True),
            status_code=200,
            request_id=request_id,
        )
    except IdentityError:
        logger.exception(
            "Idempotency finalization failed after a completed governed write: %s",
            route,
        )


__all__ = (
    "IdempotencyDecision",
    "finalize_idempotency_key",
    "reserve_idempotency_key",
    "run_idempotent_write",
    "run_idempotent_write_async",
)
