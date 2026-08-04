"""Durable HTTP idempotency reservation and terminal replay records."""

from __future__ import annotations

import hashlib
from datetime import datetime, timedelta
from typing import Literal

from pydantic import BaseModel, ConfigDict

from app.services.api._limits import HTTP_IDEMPOTENCY_RETENTION_SECONDS
from app.services.api.identity.errors import IdentityError
from app.services.api.persistence import (
    create_idempotency_record,
    delete_idempotency_record,
    finalize_idempotency_record,
    read_idempotency_record,
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


__all__ = (
    "IdempotencyDecision",
    "finalize_idempotency_key",
    "reserve_idempotency_key",
)
