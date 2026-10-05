"""Canonical result envelope and error taxonomy for bounded host operations.

Description:
    Provides a standardized, immutable response envelope and structured error
    taxonomy for bounded public operations across the HaruQuantAI host subsystem.
    In quantitative trading and distributed execution architectures, ad-hoc
    return values, unhandled exceptions, and inconsistent response schemas lead to
    silent failures, difficult debugging, and fragile API boundaries. This module
    eliminates those failure modes by enforcing a canonical envelope structure
    (`StandardResponse[T]`) paired with structured error classifications
    (`StandardError`) and execution metadata (`ResponseMetadata`). Externally,
    this envelope serves as the standard boundary contract across host lifecycle
    services, RPC handlers, CLI orchestration, and workspace domain clients.
    Internally, the factory constructors (`success()` and `error()`) enforce
    structural invariants, automate UTC timestamp generation, and guarantee
    observable, structured telemetry logging for all operations.

Purpose:
    FEAT-HOST-RESPONSE: Bounded Public Operation Response Envelope.
    Provides canonical execution result wrappers, structured error reporting,
    and telemetry metadata across all public host subsystem interfaces.

Capabilities:
    - FR-HOST-RESPONSE-SUCCESS-ENVELOPE: Success Envelope Instantiation
      Associated: `[StandardResponse.success()]`
      Logging: Emits INFO log with operation summary, duration, and request
      correlation ID upon successful envelope creation.
    - FR-HOST-RESPONSE-ERROR-ENVELOPE: Error Envelope Instantiation
      Associated: `[StandardResponse.failure()]`
      Logging: Emits WARNING log with machine-readable error code, message,
      and correlation ID upon failure envelope creation.
    - FR-HOST-RESPONSE-SERIALIZATION: Dictionary & JSON Transformation
      Associated: `[StandardResponse.to_dict()]`
      Logging: Emits DEBUG log with status when serializing envelope to dict.

Python API Usage:
    ```python
    from app.host.response import ResponseMetadata, StandardError, StandardResponse

    # Create a successful response with payload and execution duration
    success_resp = StandardResponse.success(
        data={"symbol": "EURUSD", "ask": 1.0850, "bid": 1.0848},
        message="Market tick retrieved successfully.",
        duration_ms=4.2,
        request_id="req-12345",
    )
    assert success_resp.is_success
    print(success_resp.to_dict())

    # Create an error response with structured failure context
    err = StandardError(
        code="FEED_DISCONNECTED",
        message="Dukascopy price feed connection lost.",
        details={"reconnect_attempts": 3},
        retryable=True,
    )
    error_resp = StandardResponse.failure(
        message="Failed to retrieve market tick.",
        error=err,
        request_id="req-12346",
    )
    assert error_resp.is_error
    ```

CLI Usage:
    Validate response envelope integrity and functional tests via pytest:
    ```bash
    uv run pytest tests/host/test_response.py --no-cov
    ```
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from typing import Any, Literal

from app.host.logging import get_logger

__all__ = [
    "ResponseMetadata",
    "StandardError",
    "StandardResponse",
]

logger = get_logger(__name__)


def _now_utc_iso() -> str:
    """Return the current UTC timestamp formatted as an ISO 8601 string."""
    return datetime.now(UTC).isoformat()


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
    """Canonical result of one bounded public operation.

    The successful raw payload is stored directly in ``data``.

    Attributes:
        status: Function-level completion status.
        message: Bounded human-readable summary.
        data: Raw successful function result.
        error: Structured operation failure.
        metadata: Required execution, side-effect, and extension metadata.
    """

    status: Literal["success", "error"]
    message: str
    data: T | None
    error: StandardError | None
    metadata: ResponseMetadata

    def __post_init__(self) -> None:
        """Validate structural invariants of the standard response envelope.

        Raises:
            ValueError: If status is unrecognized, or if status conflicts with
                error payload presence.
            TypeError: If error is not a StandardError instance when status is
                error.
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
        """Allow direct boolean evaluation: `if response: ...`"""
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

    @classmethod
    def success[V](
        cls,
        data: V | None = None,
        message: str = "Operation completed successfully.",
        *,
        request_id: str | None = None,
        duration_ms: float | None = None,
        side_effects: bool = False,
        extensions: dict[str, Any] | None = None,
        timestamp_utc: str | None = None,
    ) -> StandardResponse[V]:
        """Construct a successful standard response envelope.

        Args:
            data: Raw successful function result payload.
            message: Bounded human-readable completion summary.
            request_id: Optional correlation or request identifier.
            duration_ms: Optional execution duration in milliseconds.
            side_effects: Whether this operation caused state mutations.
            extensions: Optional dictionary of auxiliary metadata.
            timestamp_utc: Optional ISO 8601 UTC timestamp; defaults to current time.

        Returns:
            A frozen StandardResponse instance with status 'success'.
        """
        resolved_ts = timestamp_utc if timestamp_utc is not None else _now_utc_iso()
        resolved_ext = dict(extensions) if extensions is not None else {}
        metadata = ResponseMetadata(
            timestamp_utc=resolved_ts,
            duration_ms=duration_ms,
            request_id=request_id,
            side_effects=side_effects,
            extensions=resolved_ext,
        )
        logger.info(
            "StandardResponse.success emitted: message=%s duration_ms=%s request_id=%s",
            message,
            duration_ms,
            request_id,
            extra={"requirement": "FR-HOST-RESPONSE-SUCCESS-ENVELOPE"},
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
        extensions: dict[str, Any] | None = None,
        timestamp_utc: str | None = None,
    ) -> StandardResponse[V]:
        """Construct an error standard response envelope.

        Args:
            message: Bounded human-readable failure summary.
            error: Structured StandardError operation failure details.
            data: Optional degraded or partial result payload.
            request_id: Optional correlation or request identifier.
            duration_ms: Optional execution duration in milliseconds.
            side_effects: Whether this operation caused state mutations before failing.
            extensions: Optional dictionary of auxiliary metadata.
            timestamp_utc: Optional ISO 8601 UTC timestamp; defaults to current time.

        Returns:
            A frozen StandardResponse instance with status 'error'.
        """
        resolved_ts = timestamp_utc if timestamp_utc is not None else _now_utc_iso()
        resolved_ext = dict(extensions) if extensions is not None else {}
        metadata = ResponseMetadata(
            timestamp_utc=resolved_ts,
            duration_ms=duration_ms,
            request_id=request_id,
            side_effects=side_effects,
            extensions=resolved_ext,
        )
        logger.warning(
            "StandardResponse.failure emitted: code=%s message=%s request_id=%s",
            error.code,
            message,
            request_id,
            extra={"requirement": "FR-HOST-RESPONSE-ERROR-ENVELOPE"},
        )
        return StandardResponse(
            status="error",
            message=message,
            data=data,
            error=error,
            metadata=metadata,
        )

    def to_dict(self) -> dict[str, Any]:
        """Serialize the standard response envelope to a dictionary.

        Returns:
            A plain dictionary representation suitable for JSON encoding.
        """
        logger.debug(
            "StandardResponse.to_dict serialized: status=%s",
            self.status,
            extra={"requirement": "FR-HOST-RESPONSE-SERIALIZATION"},
        )
        return asdict(self)
