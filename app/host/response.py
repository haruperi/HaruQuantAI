# ruff: noqa: INP001
"""Canonical result envelope and error taxonomy for bounded host operations.

Description:
    Provides the standardized, immutable response envelope (`StandardResponse[T]`),
    structured error taxonomy (`StandardError`), execution metadata
    (`ResponseMetadata`), and HTTP/CLI dictionary builder (`ApiResponse`) across
    the HaruQuantAI host subsystem. Enforces structural invariants, automatic UTC
    timestamps, and structured telemetry logging for every public operation.

Purpose:
    FEAT-HOST-RESPONSE: Canonical REST, WebSocket, and CLI response and error
    envelope across the repository.

Key Capabilities:
    - FR-HOST-RESPONSE-SUCCESS-ENVELOPE: Success envelopes (StandardResponse, ok).
    - FR-HOST-RESPONSE-ERROR-ENVELOPE: Error taxonomy & envelopes (failure, error).
    - FR-HOST-RESPONSE-SERIALIZATION: Serialize envelopes to dicts (to_dict).

Python API Usage:
    from app.host.response import (
        ApiResponse,
        ResponseMetadata,
        StandardError,
        StandardResponse,
    )

    resp = StandardResponse.success(data={"symbol": "EURUSD"}, request_id="req-1")
    payload = ApiResponse.ok(data={"symbol": "EURUSD"}, request_id="req-1")

CLI Usage:
    uv run python -m app.host.response --verify --json
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass, field, is_dataclass
from datetime import UTC, datetime
from typing import Any, Final, Literal

from app.host.logging import get_logger

__all__ = [
    "ApiResponse",
    "ApiResponseCLI",
    "ResponseMetadata",
    "StandardError",
    "StandardResponse",
]

logger = get_logger(__name__)

FR_SUCCESS_ENVELOPE: Final[str] = "FR-HOST-RESPONSE-SUCCESS-ENVELOPE"
FR_ERROR_ENVELOPE: Final[str] = "FR-HOST-RESPONSE-ERROR-ENVELOPE"
FR_SERIALIZATION: Final[str] = "FR-HOST-RESPONSE-SERIALIZATION"
_MIN_HTTP_STATUS: Final[int] = 100
_MAX_HTTP_STATUS: Final[int] = 599
_RETRYABLE_STATUS_CODES: Final[frozenset[int]] = frozenset({408, 429, 502, 503, 504})


def _now_utc_iso() -> str:
    """Return the current UTC timestamp formatted as an ISO 8601 string."""
    return datetime.now(UTC).isoformat()


def _serialize_payload(val: Any) -> Any:
    """Recursively convert dataclass instances in payloads to dictionaries."""
    if is_dataclass(val) and not isinstance(val, type):
        return asdict(val)
    if isinstance(val, dict):
        return {k: _serialize_payload(v) for k, v in val.items()}
    if isinstance(val, (list, tuple)):
        return [_serialize_payload(item) for item in val]
    return val


@dataclass(frozen=True, slots=True)
class StandardError:
    """Structured operation failure representation.

    Attributes:
        code: Machine-readable error code identifier.
        message: Bounded human-readable error summary.
        details: Optional structured dictionary containing error context.
        retryable: Indicates whether the failed operation may be retried safely.
    """

    code: str
    message: str
    details: dict[str, Any] | None = None
    retryable: bool = False

    def __post_init__(self) -> None:
        """Validate error field invariants.

        Raises:
            ValueError: If code or message is empty or whitespace-only.
        """
        if not self.code or not self.code.strip():
            raise ValueError("Error code must be a non-empty string.")
        if not self.message or not self.message.strip():
            raise ValueError("Error message must be a non-empty string.")


@dataclass(frozen=True, slots=True)
class ResponseMetadata:
    """Required execution, side-effect, and extension metadata.

    Attributes:
        timestamp_utc: ISO 8601 UTC timestamp of response creation.
        duration_ms: Elapsed execution time in milliseconds, if measured.
        request_id: Optional correlation or request identifier.
        side_effects: Indicates whether the operation induced state mutations.
        extensions: Arbitrary structured auxiliary metadata mapping.
    """

    timestamp_utc: str
    duration_ms: float | None = None
    request_id: str | None = None
    side_effects: bool = False
    extensions: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate metadata invariants.

        Raises:
            ValueError: If duration_ms is negative or timestamp_utc is empty.
        """
        if not self.timestamp_utc or not self.timestamp_utc.strip():
            raise ValueError("timestamp_utc must be a non-empty string.")
        if self.duration_ms is not None and self.duration_ms < 0:
            raise ValueError(f"duration_ms cannot be negative, got {self.duration_ms}.")


@dataclass(frozen=True, slots=True)
class StandardResponse[T]:
    """Canonical immutable result envelope of one bounded public operation.

    Attributes:
        status: Function-level completion status ('success' or 'error').
        message: Bounded human-readable summary.
        data: Raw successful function result payload.
        error: Structured operation failure when status is 'error'.
        metadata: Execution, side-effect, and extension metadata.
    """

    status: Literal["success", "error"]
    message: str
    data: T | None
    error: StandardError | None
    metadata: ResponseMetadata

    def __post_init__(self) -> None:
        """Validate structural invariants of the response envelope.

        Raises:
            ValueError: If status is unrecognized or conflicts with error presence.
            TypeError: If error is not a StandardError instance when status is error.
        """
        if self.status not in ("success", "error"):
            raise ValueError(
                f"Invalid status '{self.status}'; must be 'success' or 'error'."
            )
        if self.status == "success":
            if self.error is not None:
                raise ValueError("Success response must not contain an error.")
        else:
            if self.error is None:
                raise ValueError(
                    "Error response must contain a StandardError instance."
                )
            if not isinstance(self.error, StandardError):
                raise TypeError(
                    "Error must be an instance of StandardError, got "
                    f"{type(self.error).__name__}."
                )

    @property
    def is_success(self) -> bool:
        """Return True if the operation completed successfully."""
        return self.status == "success"

    @property
    def is_error(self) -> bool:
        """Return True if the operation failed with an error."""
        return self.status == "error"

    def __bool__(self) -> bool:
        """Allow direct boolean evaluation: `if response: ...`."""
        return self.is_success

    def unwrap(self) -> T:
        """Return data if successful, otherwise raise RuntimeError."""
        if not self.is_success:
            err_msg = self.error.message if self.error else self.message
            err_code = self.error.code if self.error else "UNKNOWN_ERROR"
            raise RuntimeError(f"Operation failed [{err_code}]: {err_msg}")
        return self.data  # type: ignore[return-value]

    @property
    def error_code(self) -> str | None:
        """Return the error code if an error is attached, else None."""
        return self.error.code if self.error is not None else None

    @property
    def request_id(self) -> str | None:
        """Return the correlation or request identifier if set in metadata."""
        return self.metadata.request_id

    @classmethod
    def success[V](
        cls,
        data: V | None = None,
        message: str = "Operation completed successfully.",
        *,
        request_id: str | None = None,
        duration_ms: float | None = None,
        side_effects: bool = False,
        extensions: Mapping[str, Any] | None = None,
        timestamp_utc: str | None = None,
    ) -> StandardResponse[V]:
        """Construct a validated immutable success response envelope."""
        resolved_ts = timestamp_utc if timestamp_utc is not None else _now_utc_iso()
        resolved_ext: dict[str, Any] = (
            dict(extensions) if extensions is not None else {}
        )
        metadata = ResponseMetadata(
            timestamp_utc=resolved_ts,
            duration_ms=duration_ms,
            request_id=request_id,
            side_effects=side_effects,
            extensions=resolved_ext,
        )
        logger.info(
            "%s: StandardResponse.success emitted (msg=%s duration_ms=%s req_id=%s)",
            FR_SUCCESS_ENVELOPE,
            message,
            duration_ms,
            request_id,
            extra={
                "fr_id": FR_SUCCESS_ENVELOPE,
                "requirement": FR_SUCCESS_ENVELOPE,
            },
        )
        return StandardResponse(
            status="success",
            message=message,
            data=data,
            error=None,
            metadata=metadata,
        )

    @classmethod
    def failure[V = None](
        cls,
        message: str,
        error: StandardError,
        *,
        data: V | None = None,
        request_id: str | None = None,
        duration_ms: float | None = None,
        side_effects: bool = False,
        extensions: Mapping[str, Any] | None = None,
        timestamp_utc: str | None = None,
    ) -> StandardResponse[V]:
        """Construct a validated immutable failure response envelope."""
        resolved_ts = timestamp_utc if timestamp_utc is not None else _now_utc_iso()
        resolved_ext: dict[str, Any] = (
            dict(extensions) if extensions is not None else {}
        )
        metadata = ResponseMetadata(
            timestamp_utc=resolved_ts,
            duration_ms=duration_ms,
            request_id=request_id,
            side_effects=side_effects,
            extensions=resolved_ext,
        )
        logger.warning(
            "%s: StandardResponse.failure emitted (code=%s message=%s request_id=%s)",
            FR_ERROR_ENVELOPE,
            error.code,
            message,
            request_id,
            extra={
                "fr_id": FR_ERROR_ENVELOPE,
                "requirement": FR_ERROR_ENVELOPE,
            },
        )
        return StandardResponse(
            status="error",
            message=message,
            data=data,
            error=error,
            metadata=metadata,
        )

    def to_dict(self) -> dict[str, Any]:
        """Serialize the response envelope to a JSON-compatible dictionary."""
        logger.debug(
            "%s: StandardResponse.to_dict serialized (status=%s)",
            FR_SERIALIZATION,
            self.status,
            extra={
                "fr_id": FR_SERIALIZATION,
                "requirement": FR_SERIALIZATION,
            },
        )
        result: dict[str, Any] = {
            "status": self.status,
            "message": self.message,
            "data": _serialize_payload(self.data),
            "error": asdict(self.error) if self.error is not None else None,
            "metadata": asdict(self.metadata),
        }
        if self.metadata.request_id is not None:
            result["request_id"] = self.metadata.request_id
        return result


class ApiResponse:
    """HTTP, WebSocket, and CLI dictionary factory backed by StandardResponse."""

    @classmethod
    def ok(
        cls,
        data: Any = None,
        *,
        meta: Mapping[str, Any] | None = None,
        request_id: str | None = None,
    ) -> dict[str, Any]:
        """Construct a validated success dictionary envelope for HTTP/CLI responses."""
        meta_dict: dict[str, Any] = dict(meta) if meta is not None else {}
        message = str(
            meta_dict.pop("message", "Operation completed successfully.")
            or "Operation completed successfully."
        )
        raw_dur = meta_dict.pop("duration_ms", None)
        duration_ms = float(raw_dur) if raw_dur is not None else None
        side_effects = bool(meta_dict.pop("side_effects", False))
        raw_ts = meta_dict.pop("timestamp_utc", None)
        timestamp_utc = str(raw_ts) if raw_ts is not None else None
        resolved_req_id = request_id or (
            str(meta_dict.pop("request_id"))
            if meta_dict.get("request_id") is not None
            else None
        )
        envelope = StandardResponse.success(
            data=data,
            message=message,
            request_id=resolved_req_id,
            duration_ms=duration_ms,
            side_effects=side_effects,
            extensions=meta_dict,
            timestamp_utc=timestamp_utc,
        )
        return envelope.to_dict()

    @classmethod
    def error(
        cls,
        code: str,
        message: str,
        *,
        details: Mapping[str, Any] | None = None,
        status_code: int = 400,
        request_id: str | None = None,
    ) -> dict[str, Any]:
        """Construct a validated error dictionary envelope for HTTP/CLI responses."""
        if status_code < _MIN_HTTP_STATUS or status_code > _MAX_HTTP_STATUS:
            raise ValueError(
                f"Invalid HTTP status_code {status_code}; must be in 100..599."
            )
        details_dict: dict[str, Any] | None = (
            dict(details) if details is not None else None
        )
        std_err = StandardError(
            code=code,
            message=message,
            details=details_dict,
            retryable=status_code in _RETRYABLE_STATUS_CODES,
        )
        envelope: StandardResponse[None] = StandardResponse.failure(
            message=message,
            error=std_err,
            request_id=request_id,
            extensions={"status_code": status_code},
        )
        result = envelope.to_dict()
        result["status_code"] = status_code
        return result


class ApiResponseCLI:
    """CLI verification runner for FEAT-HOST-RESPONSE envelopes."""

    @staticmethod
    def build_parser() -> argparse.ArgumentParser:
        """Build the argument parser for `python -m app.host.response`."""
        parser = argparse.ArgumentParser(
            prog="python -m app.host.response",
            description="Verify HaruQuantAI response and error envelopes.",
        )
        parser.add_argument(
            "--verify",
            action="store_true",
            help="Run self-verification of StandardResponse and ApiResponse.",
        )
        parser.add_argument(
            "--json",
            action="store_true",
            help="Emit verification report as formatted JSON.",
        )
        return parser

    @classmethod
    def run(cls, argv: Sequence[str] | None = None) -> int:
        """Execute CLI verification of response and error envelopes."""
        parser = cls.build_parser()
        args = parser.parse_args(list(argv) if argv is not None else None)
        ok_env = StandardResponse.success(
            data={"service": "host.response", "verified": True},
            request_id="req-cli-verify",
            duration_ms=0.5,
        )
        err_env: StandardResponse[None] = StandardResponse.failure(
            message="Simulated validation check",
            error=StandardError(code="VERIFY_ERR", message="Simulated failure"),
            request_id="req-cli-verify",
        )
        ok_dict = ApiResponse.ok(
            data=ok_env.unwrap(),
            meta={"verified": bool(args.verify)},
            request_id="req-cli-verify",
        )
        err_dict = ApiResponse.error(
            code="VERIFY_ERR",
            message="Simulated failure",
            details={"check": "error_envelope"},
            status_code=422,
            request_id="req-cli-verify",
        )
        report: dict[str, Any] = {
            "status": "verified",
            "ok_envelope_status": ok_dict["status"],
            "error_envelope_status": err_dict["status"],
            "error_status_code": err_dict["status_code"],
            "failure_is_error": err_env.is_error,
        }
        sys.stdout.write(
            (json.dumps(report, indent=2) if args.json else str(report)) + "\n"
        )
        return 0


def main(argv: Sequence[str] | None = None) -> int:
    """Entrypoint for `python -m app.host.response`."""
    return ApiResponseCLI.run(argv)


if __name__ == "__main__":
    raise SystemExit(main())
