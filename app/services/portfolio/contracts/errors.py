"""Internal Portfolio domain errors and boundary-safe payloads."""

from __future__ import annotations

import time
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Final, Literal, cast

from app.composition.logging import get_logger
from app.contracts.common.models import build_response_metadata, success_response
from app.kernel.errors import validate_error_catalog
from app.kernel.identity import generate_id

type StandardResponse[T] = object
RiskLevel = Literal["none", "low", "medium", "high", "critical"]


class HaruQuantError(Exception):
    """Local safe error base for Portfolio exceptions."""

    def __init__(self, code: str, detail: str = "UNSPECIFIED") -> None:
        """Initialize safe Portfolio error.

        Args:
            code: Canonical domain error code string.
            detail: Contextual detail message.
        """
        self.code = code
        self.detail = detail
        super().__init__(f"{code}:{detail}")


@dataclass(frozen=True, slots=True)
class ErrorDefinition:
    """Immutable domain-owned error catalogue entry."""

    code: str
    domain: str
    description: str
    category: str
    severity: Literal["info", "warning", "error", "critical"]
    retryable: bool
    operator_action: str


logger = get_logger(__name__)

_PORTFOLIO_ERROR_DEFINITIONS: tuple[ErrorDefinition, ...] = (
    ErrorDefinition(
        code="PORT_APPROVAL_REQUIRED",
        domain="portfolio",
        description="Portfolio approval is required",
        category="POLICY",
        severity="warning",
        retryable=False,
        operator_action="Obtain the required approval",
    ),
    ErrorDefinition(
        code="PORT_AUDIT_PENDING",
        domain="portfolio",
        description="Portfolio audit evidence is pending",
        category="INTEGRITY",
        severity="critical",
        retryable=False,
        operator_action="Resolve the audit persistence failure",
    ),
    ErrorDefinition(
        code="PORT_CONFIG_INVALID",
        domain="portfolio",
        description="Portfolio configuration is invalid",
        category="PERMANENT",
        severity="error",
        retryable=False,
        operator_action="Correct the Portfolio configuration",
    ),
    ErrorDefinition(
        code="PORT_CONSTRUCTION_FAILED",
        domain="portfolio",
        description="Portfolio construction failed",
        category="PERMANENT",
        severity="error",
        retryable=False,
        operator_action="Correct the construction inputs and evidence",
    ),
    ErrorDefinition(
        code="PORT_DEPENDENCY_FAILED",
        domain="portfolio",
        description="A Portfolio dependency failed",
        category="TRANSIENT",
        severity="error",
        retryable=False,
        operator_action="Verify the dependent domain outcome",
    ),
    ErrorDefinition(
        code="PORT_ELIGIBILITY_INVALID",
        domain="portfolio",
        description="Portfolio strategy eligibility is invalid",
        category="POLICY",
        severity="error",
        retryable=False,
        operator_action="Obtain a current approving eligibility decision",
    ),
    ErrorDefinition(
        code="PORT_EVIDENCE_INVALID",
        domain="portfolio",
        description="Portfolio evidence is invalid",
        category="DATA_STALE",
        severity="error",
        retryable=False,
        operator_action="Refresh and validate the required evidence",
    ),
    ErrorDefinition(
        code="PORT_FX_EVIDENCE_INVALID",
        domain="portfolio",
        description="Portfolio FX evidence is invalid",
        category="DATA_STALE",
        severity="error",
        retryable=False,
        operator_action="Provide current verified FX evidence",
    ),
    ErrorDefinition(
        code="PORT_IDEMPOTENCY_CONFLICT",
        domain="portfolio",
        description="Portfolio idempotency material conflicts",
        category="INTEGRITY",
        severity="error",
        retryable=False,
        operator_action="Use a new idempotency key or matching material",
    ),
    ErrorDefinition(
        code="PORT_INTERNAL_ERROR",
        domain="portfolio",
        description="Portfolio operation failed unexpectedly",
        category="UNKNOWN_STATE",
        severity="critical",
        retryable=False,
        operator_action="Inspect redacted Portfolio diagnostics",
    ),
    ErrorDefinition(
        code="PORT_INVALID_INPUT",
        domain="portfolio",
        description="Portfolio input is invalid",
        category="PERMANENT",
        severity="warning",
        retryable=False,
        operator_action="Correct the supplied Portfolio input",
    ),
    ErrorDefinition(
        code="PORT_KILL_SWITCH_ACTIVE",
        domain="portfolio",
        description="Portfolio operation is blocked by an active kill switch",
        category="POLICY",
        severity="critical",
        retryable=False,
        operator_action="Resolve the applicable Risk kill switch",
    ),
    ErrorDefinition(
        code="PORT_MEASUREMENT_FAILED",
        domain="portfolio",
        description="Portfolio measurement failed",
        category="DATA_STALE",
        severity="error",
        retryable=False,
        operator_action="Verify immutable Trading measurement evidence",
    ),
    ErrorDefinition(
        code="PORT_METHOD_UNSUPPORTED",
        domain="portfolio",
        description="Portfolio construction method is unsupported",
        category="PERMANENT",
        severity="warning",
        retryable=False,
        operator_action="Select an approved construction method",
    ),
    ErrorDefinition(
        code="PORT_NOT_FOUND",
        domain="portfolio",
        description="Portfolio state was not found",
        category="UNKNOWN_STATE",
        severity="warning",
        retryable=False,
        operator_action="Verify the Portfolio identity and version",
    ),
    ErrorDefinition(
        code="PORT_PERSISTENCE_FAILED",
        domain="portfolio",
        description="Portfolio persistence failed",
        category="INTEGRITY",
        severity="critical",
        retryable=False,
        operator_action="Verify Portfolio state storage and audit integrity",
    ),
    ErrorDefinition(
        code="PORT_REBALANCE_BLOCKED",
        domain="portfolio",
        description="Portfolio rebalance is blocked",
        category="POLICY",
        severity="warning",
        retryable=False,
        operator_action="Resolve the rebalance block reason",
    ),
    ErrorDefinition(
        code="PORT_REFERENCE_CHANGED",
        domain="portfolio",
        description="Portfolio reference changed during the operation",
        category="INTEGRITY",
        severity="warning",
        retryable=False,
        operator_action="Refresh Portfolio state before retrying",
    ),
    ErrorDefinition(
        code="PORT_RISK_AUTHORIZATION_INVALID",
        domain="portfolio",
        description="Portfolio Risk authorization is invalid",
        category="POLICY",
        severity="critical",
        retryable=False,
        operator_action="Obtain a current approving Risk decision",
    ),
    ErrorDefinition(
        code="PORT_SIMULATION_INVALID",
        domain="portfolio",
        description="Portfolio simulation validation is invalid",
        category="DATA_STALE",
        severity="error",
        retryable=False,
        operator_action="Resolve the Simulation validation conflict",
    ),
    ErrorDefinition(
        code="PORT_UNCERTAIN_OUTCOME",
        domain="portfolio",
        description="Portfolio execution outcome is uncertain",
        category="UNKNOWN_STATE",
        severity="critical",
        retryable=False,
        operator_action="Reconcile Trading state before any further action",
    ),
    ErrorDefinition(
        code="PORT_UNSAFE_OBJECT",
        domain="portfolio",
        description="Portfolio received an unsafe object",
        category="PERMANENT",
        severity="critical",
        retryable=False,
        operator_action="Supply the documented typed contract",
    ),
    ErrorDefinition(
        code="PORT_VERSION_CONFLICT",
        domain="portfolio",
        description="Portfolio version conflicts with current state",
        category="INTEGRITY",
        severity="warning",
        retryable=False,
        operator_action="Refresh the current Portfolio version",
    ),
    ErrorDefinition(
        code="PORT_WEIGHT_INVALID",
        domain="portfolio",
        description="Portfolio weight is invalid",
        category="PERMANENT",
        severity="warning",
        retryable=False,
        operator_action="Correct the Portfolio weight inputs",
    ),
)

PORTFOLIO_ERROR_CATALOG: Final = validate_error_catalog(
    cast(
        "Any",
        MappingProxyType(
            {definition.code: definition for definition in _PORTFOLIO_ERROR_DEFINITIONS}
        ),
    )
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
        if self.code not in PORTFOLIO_ERROR_CATALOG:
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
        if code not in PORTFOLIO_ERROR_CATALOG:
            raise ValueError("Portfolio error code is not registered")
        super().__init__(code, detail)

    def to_payload(self) -> StandardResponse[PortfolioErrorPayload]:
        """Return the boundary-safe error payload in a standard response.

        Returns:
            Successful standard response containing the immutable error payload.
        """
        logger.debug("Converting Portfolio error to payload")
        start_time = time.perf_counter_ns()
        metadata = build_response_metadata(
            name="portfolio.exceptions.portfolio_error.to_payload",
            domain="portfolio",
            risk_level="none",
            request_id=generate_id("req"),
            start_time=start_time,
            read_only=True,
            writes_file=False,
            modifies_database=False,
            places_trade=False,
            requires_network=False,
        )
        return success_response(
            PortfolioErrorPayload(code=self.code, detail=self.detail),
            message="Portfolio error payload created",
            metadata=metadata,
        )


__all__: tuple[str, ...] = (
    "PORTFOLIO_ERROR_CATALOG",
    "PortfolioError",
    "PortfolioErrorPayload",
)
