"""Shared HTTP helpers for host endpoints.

Every host endpoint speaks the envelope, propagates request ids, and parses
optional JSON object bodies the same way; these helpers keep that behavior
in one place so feature modules never import each other — and never import
``webserver.py`` (the composition root imports them, so the reverse
direction would create a cycle; this module is the acyclic seam below all
consumers).
"""

from __future__ import annotations

import json
from typing import Any

from starlette.requests import Request
from starlette.responses import JSONResponse

from app.host.envelope import new_request_id

REQUEST_ID_HEADER = "X-Request-Id"


class MalformedRequestError(Exception):
    """Raised when a request body cannot be parsed as the declared JSON.

    The webserver converts this into a ``400 MALFORMED_REQUEST`` error
    envelope, so feature endpoints can simply let it propagate.
    """


def request_id_of(request: Request) -> str:
    """Return the caller-supplied request id, or a fresh one.

    Honoring a caller's ``X-Request-Id`` lets clients correlate their own
    logs with host telemetry; otherwise an unguessable id is generated so
    every response still carries one.

    Args:
        request: The incoming Starlette request.

    Returns:
        The header value when present and non-empty, else a new request id.
    """
    supplied = request.headers.get(REQUEST_ID_HEADER)
    return supplied or new_request_id()


def envelope_response(
    request_id: str,
    payload: dict[str, Any],
    status_code: int = 200,
) -> JSONResponse:
    """Wrap an envelope payload in a JSON response carrying the request id.

    Args:
        request_id: Written both into the ``X-Request-Id`` header and (by the
            payload builders) the envelope body.
        payload: An envelope built by ``app.host.envelope``.
        status_code: HTTP status line for the response.

    Returns:
        A ``JSONResponse`` with the request-id header set.
    """
    response = JSONResponse(payload, status_code=status_code)
    response.headers[REQUEST_ID_HEADER] = request_id
    return response


async def read_json_body(request: Request) -> dict[str, Any]:
    """Parse an optional JSON object body; fail closed on malformed input.

    An absent or empty body is a valid ``{}`` (commands may take no
    arguments); anything present must be a JSON *object* — arrays and scalars
    are rejected so endpoints can index fields safely.

    Args:
        request: The incoming Starlette request.

    Returns:
        The parsed body as a dictionary; ``{}`` when the body is empty.

    Raises:
        MalformedRequestError: If the body is not valid JSON or not an
            object.
    """
    if not await request.body():
        return {}
    try:
        parsed: Any = json.loads(await request.body())
    except (json.JSONDecodeError, UnicodeDecodeError) as err:
        raise MalformedRequestError("Request body is not valid JSON") from err
    if not isinstance(parsed, dict):
        raise MalformedRequestError("Request body must be a JSON object")
    return parsed
