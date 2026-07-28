"""Typed public Portfolio application boundary without UI concerns."""

from __future__ import annotations

import time
from collections.abc import Mapping
from datetime import datetime
from decimal import Decimal
from types import MappingProxyType
from typing import TYPE_CHECKING, Any, Literal

from app.services.portfolio.exceptions import (
    PORTFOLIO_ERROR_CATALOG,
    PortfolioError,
)
from app.utils import (
    build_response_metadata,
    error_response,
    generate_id,
    get_logger,
    success_response,
    validate_id,
)

type AuthContext = Any
type JsonValue = Any
type ResponseMetadata = Any
type StandardResponse[T] = Any
RiskLevel = Literal["none", "low", "medium", "high", "critical"]

logger = get_logger(__name__)

if TYPE_CHECKING:
    from app.services.portfolio.contracts import (
        ActivePortfolioAllocation,
        PortfolioConstructionRequest,
        PortfolioConstructionResult,
        PortfolioRebalancePlan,
    )
    from app.services.portfolio.evidence import ValidatedConstructionEvidence
    from app.services.portfolio.orchestration import (
        PortfolioReviewResult,
        PortfolioWorkflowService,
    )
    from app.services.portfolio.state import PortfolioRepository
    from app.services.risk import (
        AllocationRiskDecision,
        ApprovalAttestation,
        ApprovalValidationResult,
        StrategyOperationalEligibilityDecision,
    )


_OPERATION_FACTS = MappingProxyType(
    {
        "portfolio.api.service.construct": (
            "medium",
            False,
            True,
            False,
            True,
        ),
        "portfolio.api.service.status": ("low", True, False, False, False),
        "portfolio.api.service.activate": (
            "critical",
            False,
            True,
            False,
            True,
        ),
        "portfolio.api.service.assess_drift": (
            "high",
            False,
            True,
            False,
            True,
        ),
        "portfolio.api.service.submit_rebalance": (
            "critical",
            False,
            True,
            True,
            True,
        ),
        "portfolio.api.service.recompute_measurement": (
            "high",
            False,
            True,
            False,
            True,
        ),
        "portfolio.api.service.rollback": (
            "critical",
            False,
            True,
            False,
            True,
        ),
        "portfolio.api.service.history": ("low", True, False, False, False),
    }
)


class PortfolioService:
    """Expose structured Portfolio operations to the external UI/API layer."""

    def __init__(
        self,
        workflows: PortfolioWorkflowService,
        repository: PortfolioRepository,
    ) -> None:
        """Initialize the public boundary from application-layer services.

        Args:
            workflows: Complete Portfolio workflow coordinator.
            repository: Portfolio-owned read repository.
        """
        logger.info("Initializing public Portfolio service")
        self._workflows = workflows
        self._repository = repository

    @staticmethod
    def _trace(
        auth_context: AuthContext,
        request_id: str | None,
        *,
        command_request_id: str | None = None,
        command_workflow_id: str | None = None,
        command_correlation_id: str | None = None,
    ) -> tuple[str, str]:
        """Validate trace identity without authenticating the principal.

        Args:
            auth_context: Already authenticated Utils context.
            request_id: Optional caller-supplied request identity.
            command_request_id: Optional request identity carried by a command.
            command_workflow_id: Optional workflow identity carried by command.
            command_correlation_id: Optional correlation identity carried by
                command.

        Returns:
            Validated request and correlation identities.

        Raises:
            PortfolioError: If context type or trace identities conflict.
        """
        logger.debug("Validating Portfolio public boundary trace identities")
        if not all(
            hasattr(auth_context, field)
            for field in ("request_id", "workflow_id", "correlation_id")
        ):
            raise PortfolioError("PORT_INVALID_INPUT", "AUTH_CONTEXT")
        observed_request_id = request_id or auth_context.request_id
        if (
            observed_request_id != auth_context.request_id
            or (
                command_request_id is not None
                and command_request_id != observed_request_id
            )
            or (
                command_workflow_id is not None
                and command_workflow_id != auth_context.workflow_id
            )
            or (
                command_correlation_id is not None
                and command_correlation_id != auth_context.correlation_id
            )
        ):
            raise PortfolioError("PORT_INVALID_INPUT", "TRACE_MISMATCH")
        return observed_request_id, auth_context.correlation_id

    @staticmethod
    def _fallback_trace(
        auth_context: object,
        request_id: str | None,
    ) -> tuple[str, str]:
        """Return safe trace text for an error envelope before validation.

        Args:
            auth_context: Candidate authenticated context.
            request_id: Optional caller-supplied request identity.

        Returns:
            Canonical request and correlation identities for safe error mapping.
        """
        logger.debug("Preparing fallback Portfolio error-envelope trace")
        context_request_id = getattr(auth_context, "request_id", None)
        context_correlation_id = getattr(auth_context, "correlation_id", None)

        def canonical_or_generated(value: object, prefix: Literal["req", "cor"]) -> str:
            """Return a valid trace ID without retaining malformed input."""
            if isinstance(value, str):
                try:
                    return validate_id(value, expected_prefix=prefix)
                except Exception:
                    pass
            return generate_id(prefix)

        return (
            canonical_or_generated(request_id or context_request_id, "req"),
            canonical_or_generated(context_correlation_id, "cor"),
        )

    def _active(
        self,
        portfolio_id: str,
        scope: Mapping[str, str],
    ) -> ActivePortfolioAllocation:
        """Return one active allocation or raise a known not-found error.

        Args:
            portfolio_id: Portfolio identity.
            scope: Exact governed scope.

        Returns:
            Current active allocation.

        Raises:
            PortfolioError: If no active allocation exists.
        """
        logger.debug("Requiring an active Portfolio allocation")
        active = self._repository.active(portfolio_id, scope)
        if active is None:
            raise PortfolioError("PORT_NOT_FOUND", "ACTIVE_ALLOCATION")
        return active[0]

    @staticmethod
    def _failure[T](
        error: Exception,
        *,
        operation: str,
        request_id: str,
        correlation_id: str,
        start_time: int,
    ) -> StandardResponse[T]:
        """Map every failure into the closed Portfolio error envelope.

        Args:
            error: Known or unexpected operation failure.
            operation: Qualified Portfolio operation name.
            request_id: Request trace identity.
            correlation_id: Correlation trace identity.
            start_time: Monotonic operation start time.

        Returns:
            Structured Portfolio error response.
        """
        logger.warning("Mapping Portfolio operation failure to a safe envelope")
        code = (
            error.code if isinstance(error, PortfolioError) else "PORT_INTERNAL_ERROR"
        )
        details: dict[str, JsonValue] = {
            "detail": (
                error.detail if isinstance(error, PortfolioError) else "UNEXPECTED"
            ),
        }
        if not isinstance(error, PortfolioError):
            details["failure_type"] = type(error).__name__
        metadata = PortfolioService._metadata(
            operation=operation,
            request_id=request_id,
            correlation_id=correlation_id,
            start_time=start_time,
        )
        return error_response(
            code=code,
            details=details,
            message=PORTFOLIO_ERROR_CATALOG[code].description,
            metadata=metadata,
            catalog=PORTFOLIO_ERROR_CATALOG,
        )

    @staticmethod
    def _metadata(
        *,
        operation: str,
        request_id: str,
        correlation_id: str,
        start_time: int,
        extensions: Mapping[str, JsonValue] | None = None,
    ) -> ResponseMetadata:
        """Build metadata for one Portfolio public operation.

        Returns:
            Validated standard response metadata.
        """
        risk_level, read_only, modifies_database, places_trade, requires_network = (
            _OPERATION_FACTS[operation]
        )
        return build_response_metadata(
            name=operation,
            domain="portfolio",
            risk_level=risk_level,
            request_id=request_id,
            correlation_id=correlation_id,
            start_time=start_time,
            read_only=read_only,
            writes_file=False,
            modifies_database=modifies_database,
            places_trade=places_trade,
            requires_network=requires_network,
            extensions=extensions,
        )

    @staticmethod
    def _success[T](
        value: T | None,
        *,
        operation: str,
        request_id: str,
        correlation_id: str,
        start_time: int,
        audit_event_id: str | None = None,
    ) -> StandardResponse[T]:
        """Wrap one non-null success value in the public envelope.

        Args:
            value: Successful typed operation value.
            operation: Qualified Portfolio operation name.
            request_id: Request trace identity.
            correlation_id: Correlation trace identity.
            start_time: Monotonic operation start time.
            audit_event_id: Optional persisted audit identity.

        Returns:
            Structured Portfolio success response.
        """
        logger.debug("Wrapping successful Portfolio operation outcome")
        extensions: dict[str, JsonValue] = {}
        if audit_event_id is not None:
            extensions["audit_event_id"] = audit_event_id
        return success_response(
            value,
            message="Portfolio operation completed successfully",
            metadata=PortfolioService._metadata(
                operation=operation,
                request_id=request_id,
                correlation_id=correlation_id,
                start_time=start_time,
                extensions=extensions,
            ),
        )

    def construct(
        self,
        request: PortfolioConstructionRequest,
        auth_context: AuthContext,
        request_id: str | None = None,
    ) -> StandardResponse[PortfolioConstructionResult]:
        """Construct and persist one deterministic Portfolio candidate.

        Args:
            request: Validated Portfolio construction command.
            auth_context: Already authenticated Utils context.
            request_id: Optional exact request identity.

        Returns:
            Structured construction result or failure.
        """
        logger.info("Serving public Portfolio construction operation")
        start_time = time.perf_counter_ns()
        safe_request_id, correlation_id = self._fallback_trace(auth_context, request_id)
        try:
            safe_request_id, correlation_id = self._trace(
                auth_context,
                request_id,
                command_request_id=request.request_id,
                command_workflow_id=request.workflow_id,
                command_correlation_id=request.correlation_id,
            )
            result, _evidence = self._workflows.construct(request)
            return self._success(
                result,
                operation="portfolio.api.service.construct",
                request_id=safe_request_id,
                correlation_id=correlation_id,
                start_time=start_time,
            )
        # pylint: disable-next=broad-exception-caught
        except Exception as error:  # noqa: BLE001 - public exception boundary.
            return self._failure(
                error,
                operation="portfolio.api.service.construct",
                request_id=safe_request_id,
                correlation_id=correlation_id,
                start_time=start_time,
            )

    def status(
        self,
        portfolio_id: str,
        scope: Mapping[str, str],
        auth_context: AuthContext,
        request_id: str | None = None,
    ) -> StandardResponse[ActivePortfolioAllocation]:
        """Return the exact active allocation for one Portfolio scope.

        Args:
            portfolio_id: Portfolio identity.
            scope: Exact governed scope.
            auth_context: Already authenticated Utils context.
            request_id: Optional exact request identity.

        Returns:
            Structured active allocation or failure.
        """
        logger.info("Serving public Portfolio status operation")
        start_time = time.perf_counter_ns()
        safe_request_id, correlation_id = self._fallback_trace(auth_context, request_id)
        try:
            safe_request_id, correlation_id = self._trace(auth_context, request_id)
            return self._success(
                self._active(portfolio_id, scope),
                operation="portfolio.api.service.status",
                request_id=safe_request_id,
                correlation_id=correlation_id,
                start_time=start_time,
            )
        # pylint: disable-next=broad-exception-caught
        except Exception as error:  # noqa: BLE001 - public exception boundary.
            return self._failure(
                error,
                operation="portfolio.api.service.status",
                request_id=safe_request_id,
                correlation_id=correlation_id,
                start_time=start_time,
            )

    def activate(
        self,
        candidate: PortfolioConstructionResult,
        evidence: ValidatedConstructionEvidence,
        review: PortfolioReviewResult,
        *,
        approval_attestation: ApprovalAttestation | None,
        approval_validation: ApprovalValidationResult | None,
        expires_at: datetime,
        idempotency_key: str,
        expected_predecessor: str | None,
        expected_revision: int,
        auth_context: AuthContext,
        request_id: str | None = None,
    ) -> StandardResponse[ActivePortfolioAllocation]:
        """Activate a fully reviewed Portfolio allocation version.

        Args:
            candidate: Complete construction candidate.
            evidence: Validated construction evidence.
            review: Current Simulation and Risk review results.
            approval_attestation: Conditional human approval evidence.
            approval_validation: Conditional Risk approval validation.
            expires_at: Explicit UTC allocation expiry.
            idempotency_key: Deterministic activation identity.
            expected_predecessor: Caller-observed predecessor version.
            expected_revision: Caller-observed active-scope revision.
            auth_context: Already authenticated Utils context.
            request_id: Optional exact request identity.

        Returns:
            Structured active allocation or failure.
        """
        logger.info("Serving public Portfolio activation operation")
        start_time = time.perf_counter_ns()
        safe_request_id, correlation_id = self._fallback_trace(auth_context, request_id)
        try:
            safe_request_id, correlation_id = self._trace(
                auth_context,
                request_id,
                command_request_id=candidate.request_id,
                command_workflow_id=candidate.workflow_id,
                command_correlation_id=candidate.correlation_id,
            )
            value = self._workflows.activate(
                candidate,
                evidence,
                review,
                approval_attestation=approval_attestation,
                approval_validation=approval_validation,
                expires_at=expires_at,
                idempotency_key=idempotency_key,
                expected_predecessor=expected_predecessor,
                expected_revision=expected_revision,
            )
            return self._success(
                value,
                operation="portfolio.api.service.activate",
                request_id=safe_request_id,
                correlation_id=correlation_id,
                start_time=start_time,
                audit_event_id=value.audit_ref,
            )
        # pylint: disable-next=broad-exception-caught
        except Exception as error:  # noqa: BLE001 - public exception boundary.
            return self._failure(
                error,
                operation="portfolio.api.service.activate",
                request_id=safe_request_id,
                correlation_id=correlation_id,
                start_time=start_time,
            )

    def assess_drift(
        self,
        allocation: ActivePortfolioAllocation,
        *,
        actual_exposures: Mapping[str, Decimal],
        evidence_as_of: datetime,
        risk_decision: AllocationRiskDecision,
        eligibility_decisions: Mapping[str, StrategyOperationalEligibilityDecision],
        auth_context: AuthContext,
        request_id: str | None = None,
    ) -> StandardResponse[PortfolioRebalancePlan]:
        """Assess actual exposure drift against an active target.

        Args:
            allocation: Current active allocation.
            actual_exposures: Exact component Risk-budget exposures.
            evidence_as_of: UTC account/FX evidence time.
            risk_decision: Current authoritative Risk allocation decision.
            eligibility_decisions: Component-keyed current eligibility.
            auth_context: Already authenticated Utils context.
            request_id: Optional exact request identity.

        Returns:
            Structured immutable rebalance plan or failure.
        """
        logger.info("Serving public Portfolio drift operation")
        start_time = time.perf_counter_ns()
        safe_request_id, correlation_id = self._fallback_trace(auth_context, request_id)
        try:
            safe_request_id, correlation_id = self._trace(auth_context, request_id)
            value = self._workflows.assess_drift(
                allocation,
                actual_exposures=actual_exposures,
                evidence_as_of=evidence_as_of,
                risk_decision=risk_decision,
                eligibility_decisions=eligibility_decisions,
                request_id=safe_request_id,
                workflow_id=auth_context.workflow_id,
                correlation_id=correlation_id,
            )
            return self._success(
                value,
                operation="portfolio.api.service.assess_drift",
                request_id=safe_request_id,
                correlation_id=correlation_id,
                start_time=start_time,
            )
        # pylint: disable-next=broad-exception-caught
        except Exception as error:  # noqa: BLE001 - public exception boundary.
            return self._failure(
                error,
                operation="portfolio.api.service.assess_drift",
                request_id=safe_request_id,
                correlation_id=correlation_id,
                start_time=start_time,
            )

    async def submit_rebalance(
        self,
        plan: PortfolioRebalancePlan,
        *,
        account_evidence_ref: str,
        market_evidence_ref: str,
        fx_evidence_refs: tuple[str, ...],
        runtime_profile: Literal["simulation", "paper", "live"],
        execution_route: Literal["sim", "paper", "live"],
        approval_refs: tuple[str, ...],
        approval_token_ref: str,
        trading_request_id: str,
        valid_until: datetime,
        auth_context: AuthContext,
        request_id: str | None = None,
    ) -> StandardResponse[PortfolioRebalancePlan]:
        """Submit and measure one Risk-reviewed reduce-only plan.

        Args:
            plan: Current immutable reduce-only plan.
            account_evidence_ref: Current Data account evidence reference.
            market_evidence_ref: Current Data market evidence reference.
            fx_evidence_refs: Ordered Data FX evidence references.
            runtime_profile: Explicit execution profile.
            execution_route: Compatible Trading route.
            approval_refs: Ordered owner-provided approval references.
            approval_token_ref: Opaque Risk approval token reference.
            trading_request_id: Unique Trading request identity.
            valid_until: Explicit execution authorization expiry.
            auth_context: Already authenticated Utils context.
            request_id: Optional exact request identity.

        Returns:
            Structured measured or executed-but-unmeasured plan, or failure.
        """
        logger.info("Serving public Portfolio rebalance submission")
        start_time = time.perf_counter_ns()
        safe_request_id, correlation_id = self._fallback_trace(auth_context, request_id)
        try:
            safe_request_id, correlation_id = self._trace(
                auth_context,
                request_id,
                command_request_id=plan.request_id,
                command_workflow_id=plan.workflow_id,
                command_correlation_id=plan.correlation_id,
            )
            value = await self._workflows.submit_rebalance(
                plan,
                account_evidence_ref=account_evidence_ref,
                market_evidence_ref=market_evidence_ref,
                fx_evidence_refs=fx_evidence_refs,
                runtime_profile=runtime_profile,
                execution_route=execution_route,
                approval_refs=approval_refs,
                approval_token_ref=approval_token_ref,
                trading_request_id=trading_request_id,
                valid_until=valid_until,
            )
            return self._success(
                value,
                operation="portfolio.api.service.submit_rebalance",
                request_id=safe_request_id,
                correlation_id=correlation_id,
                start_time=start_time,
            )
        # pylint: disable-next=broad-exception-caught
        except Exception as error:  # noqa: BLE001 - public exception boundary.
            return self._failure(
                error,
                operation="portfolio.api.service.submit_rebalance",
                request_id=safe_request_id,
                correlation_id=correlation_id,
                start_time=start_time,
            )

    def recompute_measurement(
        self,
        plan_id: str,
        *,
        trading_request_id: str,
        auth_context: AuthContext,
        request_id: str | None = None,
    ) -> StandardResponse[PortfolioRebalancePlan]:
        """Recompute read-only Analytics evidence from immutable Trading facts.

        Args:
            plan_id: Executed-but-unmeasured plan identity.
            trading_request_id: Original Trading request identity.
            auth_context: Already authenticated Utils context.
            request_id: Optional exact request identity.

        Returns:
            Structured measured or unchanged plan, or failure.
        """
        logger.info("Serving public Portfolio measurement recomputation")
        start_time = time.perf_counter_ns()
        safe_request_id, correlation_id = self._fallback_trace(auth_context, request_id)
        try:
            safe_request_id, correlation_id = self._trace(auth_context, request_id)
            value = self._workflows.recompute_measurement(
                plan_id,
                trading_request_id=trading_request_id,
            )
            return self._success(
                value,
                operation="portfolio.api.service.recompute_measurement",
                request_id=safe_request_id,
                correlation_id=correlation_id,
                start_time=start_time,
            )
        # pylint: disable-next=broad-exception-caught
        except Exception as error:  # noqa: BLE001 - public exception boundary.
            return self._failure(
                error,
                operation="portfolio.api.service.recompute_measurement",
                request_id=safe_request_id,
                correlation_id=correlation_id,
                start_time=start_time,
            )

    def rollback(
        self,
        candidate: PortfolioConstructionResult,
        evidence: ValidatedConstructionEvidence,
        review: PortfolioReviewResult,
        *,
        rollback_of_version: str,
        approval_attestation: ApprovalAttestation | None,
        approval_validation: ApprovalValidationResult | None,
        expires_at: datetime,
        idempotency_key: str,
        expected_predecessor: str | None,
        expected_revision: int,
        auth_context: AuthContext,
        request_id: str | None = None,
    ) -> StandardResponse[ActivePortfolioAllocation]:
        """Create a new governed version reproducing historical allocation.

        Args:
            candidate: New construction candidate with historical weights.
            evidence: Validated evidence for the new candidate.
            review: Current Simulation and Risk review results.
            rollback_of_version: Historical allocation version selected.
            approval_attestation: Conditional human approval evidence.
            approval_validation: Conditional Risk approval validation.
            expires_at: Explicit UTC allocation expiry.
            idempotency_key: Deterministic activation identity.
            expected_predecessor: Caller-observed active version.
            expected_revision: Caller-observed active-scope revision.
            auth_context: Already authenticated Utils context.
            request_id: Optional exact request identity.

        Returns:
            Structured new active allocation or failure.
        """
        logger.info("Serving public Portfolio rollback operation")
        start_time = time.perf_counter_ns()
        safe_request_id, correlation_id = self._fallback_trace(auth_context, request_id)
        try:
            safe_request_id, correlation_id = self._trace(
                auth_context,
                request_id,
                command_request_id=candidate.request_id,
                command_workflow_id=candidate.workflow_id,
                command_correlation_id=candidate.correlation_id,
            )
            value = self._workflows.rollback(
                candidate,
                evidence,
                review,
                rollback_of_version=rollback_of_version,
                approval_attestation=approval_attestation,
                approval_validation=approval_validation,
                expires_at=expires_at,
                idempotency_key=idempotency_key,
                expected_predecessor=expected_predecessor,
                expected_revision=expected_revision,
            )
            return self._success(
                value,
                operation="portfolio.api.service.rollback",
                request_id=safe_request_id,
                correlation_id=correlation_id,
                start_time=start_time,
                audit_event_id=value.audit_ref,
            )
        # pylint: disable-next=broad-exception-caught
        except Exception as error:  # noqa: BLE001 - public exception boundary.
            return self._failure(
                error,
                operation="portfolio.api.service.rollback",
                request_id=safe_request_id,
                correlation_id=correlation_id,
                start_time=start_time,
            )

    def history(
        self,
        portfolio_id: str,
        auth_context: AuthContext,
        request_id: str | None = None,
    ) -> StandardResponse[tuple[ActivePortfolioAllocation, ...]]:
        """Return immutable allocation history in activation order.

        Args:
            portfolio_id: Portfolio identity.
            auth_context: Already authenticated Utils context.
            request_id: Optional exact request identity.

        Returns:
            Structured immutable history or failure.
        """
        logger.info("Serving public Portfolio history operation")
        start_time = time.perf_counter_ns()
        safe_request_id, correlation_id = self._fallback_trace(auth_context, request_id)
        try:
            safe_request_id, correlation_id = self._trace(auth_context, request_id)
            return self._success(
                self._repository.history(portfolio_id),
                operation="portfolio.api.service.history",
                request_id=safe_request_id,
                correlation_id=correlation_id,
                start_time=start_time,
            )
        # pylint: disable-next=broad-exception-caught
        except Exception as error:  # noqa: BLE001 - public exception boundary.
            return self._failure(
                error,
                operation="portfolio.api.service.history",
                request_id=safe_request_id,
                correlation_id=correlation_id,
                start_time=start_time,
            )


__all__: tuple[str, ...] = ("PortfolioService",)
