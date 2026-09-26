"""Framework-independent builders for the application API envelope.

HTTP adapters and UI/CLI transports use api_version, request_id, and status with
either data or an error body. These helpers build fresh Python mappings without
serializing or sending them; the caller ensures payloads are JSON-compatible
and error text is safe to expose. Framework middleware and static-file responses
are outside this envelope contract.

Immutable issue/error records support structured validation details when callers
supply them. No server, request context, or logging configuration is created here.
"""

from __future__ import annotations

import secrets
import time
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

API_VERSION = "1.0"


@dataclass(frozen=True)
class ValidationIssue:
    """A single structured validation problem tied to a payload location.

    Attributes:
        path: JSON-Pointer-like location of the problem (for example
            ``$.nodes`` for documents, or the offending field name).
        code: Stable machine-readable problem code (for example ``required``,
            ``invalid``, ``too_large``).
        message: Human-readable explanation safe to show to a user.
    """

    path: str
    code: str
    message: str

    def to_json(self) -> dict[str, str]:
        """Return the wire representation of this issue.

        Returns:
            A fresh ``{"path", "code", "message"}`` object.
        """
        return {"path": self.path, "code": self.code, "message": self.message}


@dataclass(frozen=True)
class ErrorBody:
    """The error half of the envelope, mirroring the UI ``ApiClientError``.

    Attributes:
        code: Stable machine-readable error code (for example ``NOT_FOUND``,
            ``UNAUTHORIZED``, ``MALFORMED_REQUEST``).
        message: Human-readable error text safe to display.
        issues: Optional structured validation detail; empty when the error
            is not tied to specific payload locations.
    """

    code: str
    message: str
    issues: tuple[ValidationIssue, ...] = ()

    def to_json(self) -> dict[str, Any]:
        """Return the wire representation of this error body.

        Returns:
            A fresh object with ``code``, ``message``, and a list of
            serialized :class:`ValidationIssue` entries.
        """
        payload: dict[str, Any] = {
            "code": self.code,
            "message": self.message,
            "issues": [issue.to_json() for issue in self.issues],
        }
        return payload


def new_request_id() -> str:
    """Generate a timestamped diagnostic request identifier.

    Uses wall-clock nanoseconds and random entropy to reduce collisions. It is a
    correlation label, not an authentication token or a uniqueness guarantee.

    Returns:
        req-<timestamp-nanos>-<hex> with four random bytes encoded as hex.
    """
    return f"req-{time.time_ns()}-{secrets.token_hex(4)}"


def success_payload(request_id: str, data: Any) -> dict[str, Any]:
    """Build a success envelope body carrying ``data``.

    Args:
        request_id: The request id echoed into the envelope.
        data: Any JSON-serializable payload to return to the caller.

    Returns:
        The envelope object with ``status: "success"``.
    """
    return {
        "api_version": API_VERSION,
        "request_id": request_id,
        "status": "success",
        "data": data,
    }


def error_payload(
    request_id: str,
    code: str,
    message: str,
    issues: Sequence[ValidationIssue] = (),
) -> dict[str, Any]:
    """Build an error envelope body carrying a structured error.

    Args:
        request_id: The request id echoed into the envelope.
        code: Stable machine-readable error code.
        message: Human-readable error text safe to display.
        issues: Optional structured validation detail.

    Returns:
        The envelope object with ``status: "error"``.
    """
    body = ErrorBody(code=code, message=message, issues=tuple(issues))
    return {
        "api_version": API_VERSION,
        "request_id": request_id,
        "status": "error",
        "error": body.to_json(),
    }
