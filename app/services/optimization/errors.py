"""Controlled errors for the Optimization domain."""

from __future__ import annotations

from collections.abc import Mapping
from types import MappingProxyType

from app.utils import HaruQuantError, logger, redact_mapping_value

OPTIMIZATION_ERROR_CODES = frozenset(
    {
        "OPT_ADAPTER_INCOMPATIBLE",
        "OPT_CONSTRAINT_INVALID",
        "OPT_EVIDENCE_INCOMPLETE",
        "OPT_EXECUTION_FAILED",
        "OPT_INTERNAL_ERROR",
        "OPT_INVALID_REQUEST",
        "OPT_LEAKAGE_DETECTED",
        "OPT_LIMIT_EXCEEDED",
        "OPT_PERSISTENCE_FAILED",
        "OPT_STATE_CONFLICT",
    }
)


class OptimizationError(HaruQuantError):
    """Fail-closed Optimization error with redacted JSON-safe details."""

    def __init__(
        self,
        code: str,
        detail: str = "UNSPECIFIED",
        *,
        safe_details: Mapping[str, object] | None = None,
    ) -> None:
        """Initialize a controlled Optimization error.

        Args:
            code: Cataloged Optimization error code.
            detail: Uppercase symbolic safe detail.
            safe_details: Optional detail mapping redacted at construction.

        Raises:
            TypeError: If redaction does not return a mapping.
            ValueError: If the error code or detail is invalid.
        """
        logger.debug("Creating OptimizationError with code %s", code)
        if code not in OPTIMIZATION_ERROR_CODES:
            raise ValueError("Optimization error code is not cataloged")
        super().__init__(code, detail)
        redacted = redact_mapping_value(safe_details or {}).value
        if not isinstance(redacted, Mapping):
            raise TypeError("Optimization error details must be a mapping")
        self.safe_details = MappingProxyType(dict(redacted))

    def to_payload(self) -> dict[str, object]:
        """Return the controlled JSON-safe public payload.

        Returns:
            Stable error code, symbolic detail, and redacted details.
        """
        logger.info("Building Optimization error payload")
        return {
            "code": self.code,
            "detail": self.detail,
            "details": dict(self.safe_details),
        }


__all__ = ["OptimizationError"]
