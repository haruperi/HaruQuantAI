"""Structured Portfolio domain errors and boundary-safe payloads."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

from app.utils import HaruQuantError, logger

PORTFOLIO_ERROR_CODES: Final[frozenset[str]] = frozenset(
    {
        "PORT_APPROVAL_REQUIRED",
        "PORT_AUDIT_PENDING",
        "PORT_CONFIG_INVALID",
        "PORT_CONSTRUCTION_FAILED",
        "PORT_DEPENDENCY_FAILED",
        "PORT_ELIGIBILITY_INVALID",
        "PORT_EVIDENCE_INVALID",
        "PORT_FX_EVIDENCE_INVALID",
        "PORT_IDEMPOTENCY_CONFLICT",
        "PORT_INTERNAL_ERROR",
        "PORT_INVALID_INPUT",
        "PORT_KILL_SWITCH_ACTIVE",
        "PORT_MEASUREMENT_FAILED",
        "PORT_METHOD_UNSUPPORTED",
        "PORT_NOT_FOUND",
        "PORT_PERSISTENCE_FAILED",
        "PORT_REBALANCE_BLOCKED",
        "PORT_REFERENCE_CHANGED",
        "PORT_RISK_AUTHORIZATION_INVALID",
        "PORT_SIMULATION_INVALID",
        "PORT_UNCERTAIN_OUTCOME",
        "PORT_UNSAFE_OBJECT",
        "PORT_VERSION_CONFLICT",
        "PORT_WEIGHT_INVALID",
    }
)


@dataclass(frozen=True, slots=True)
class PortfolioErrorPayload:
    """Boundary-safe Portfolio failure evidence.

    Attributes:
        code: Closed Portfolio error code.
        detail: Uppercase symbolic safe detail.
    """

    code: str
    detail: str

    def __post_init__(self) -> None:
        """Validate the payload against the closed catalog.

        Raises:
            ValueError: If the error code is not registered.
        """
        logger.debug("Validating Portfolio error payload")
        if self.code not in PORTFOLIO_ERROR_CODES:
            raise ValueError("Portfolio error code is not registered")


class PortfolioError(HaruQuantError):
    """Known fail-closed Portfolio domain error."""

    def __init__(self, code: str, detail: str = "UNSPECIFIED") -> None:
        """Initialize one cataloged Portfolio error.

        Args:
            code: Closed Portfolio error code.
            detail: Uppercase symbolic boundary-safe detail.

        Raises:
            ValueError: If the code is not registered or tokens are malformed.
        """
        logger.debug("Initializing Portfolio error")
        if code not in PORTFOLIO_ERROR_CODES:
            raise ValueError("Portfolio error code is not registered")
        super().__init__(code, detail)

    def to_payload(self) -> PortfolioErrorPayload:
        """Return the boundary-safe error payload.

        Returns:
            Immutable error payload.
        """
        logger.debug("Converting Portfolio error to payload")
        return PortfolioErrorPayload(code=self.code, detail=self.detail)


__all__: tuple[str, ...] = (
    "PORTFOLIO_ERROR_CODES",
    "PortfolioError",
    "PortfolioErrorPayload",
)
