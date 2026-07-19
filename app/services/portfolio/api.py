"""Typed public Portfolio application boundary without presentation concerns."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Literal

from app.services.portfolio.contracts import (
    ActivePortfolioAllocation,
    PortfolioConstructionRequest,
    PortfolioConstructionResult,
    PortfolioOutcome,
    PortfolioRebalancePlan,
)
from app.services.portfolio.exceptions import PortfolioError, PortfolioErrorPayload
from app.utils import AuthContext, logger

if TYPE_CHECKING:
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
        """Validate supplied trace identity without authenticating the principal.

        Args:
            auth_context: Already authenticated Utils context.
            request_id: Optional caller-supplied request identity.
            command_request_id: Optional request identity carried by a command.
            command_workflow_id: Optional workflow identity carried by a command.
            command_correlation_id: Optional correlation identity carried by a command.

        Returns:
            Validated request and correlation identities.

        Raises:
            PortfolioError: If context type or trace identities conflict.
        """
        logger.debug("Validating Portfolio public boundary trace identities")
        if not isinstance(auth_context, AuthContext):
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
            Non-empty request and correlation text for safe error mapping.
        """
        logger.debug("Preparing fallback Portfolio error-envelope trace")
        context_request_id = getattr(auth_context, "request_id", None)
        context_correlation_id = getattr(auth_context, "correlation_id", None)
        return (
            request_id
            or (
                context_request_id if isinstance(context_request_id, str) else "unknown"
            ),
            (
                context_correlation_id
                if isinstance(context_correlation_id, str)
                else "unknown"
            ),
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
        request_id: str,
        correlation_id: str,
    ) -> PortfolioOutcome[T]:
        """Map every failure into the closed Portfolio error envelope.

        Args:
            error: Known or unexpected operation failure.
            request_id: Request trace identity.
            correlation_id: Correlation trace identity.

        Returns:
            Structured error-only Portfolio outcome.
        """
        logger.warning("Mapping Portfolio operation failure to a safe envelope")
        payload = (
            error.to_payload()
            if isinstance(error, PortfolioError)
            else PortfolioErrorPayload("PORT_INTERNAL_ERROR", "UNEXPECTED")
        )
        return PortfolioOutcome(
            ok=False,
            request_id=request_id,
            correlation_id=correlation_id,
            error=payload,
        )

    @staticmethod
    def _success[T](
        value: T,
        *,
        request_id: str,
        correlation_id: str,
        audit_event_id: str | None = None,
    ) -> PortfolioOutcome[T]:
        """Wrap one non-null success value in the public envelope.

        Args:
            value: Successful typed operation value.
            request_id: Request trace identity.
            correlation_id: Correlation trace identity.
            audit_event_id: Optional persisted audit identity.

        Returns:
            Structured success-only Portfolio outcome.
        """
        logger.debug("Wrapping successful Portfolio operation outcome")
        return PortfolioOutcome(
            ok=True,
            request_id=request_id,
            correlation_id=correlation_id,
            value=value,
            audit_event_id=audit_event_id,
        )

    def construct(
        self,
        request: PortfolioConstructionRequest,
        auth_context: AuthContext,
        request_id: str | None = None,
    ) -> PortfolioOutcome[PortfolioConstructionResult]:
        """Construct and persist one deterministic Portfolio candidate.

        Args:
            request: Validated Portfolio construction command.
            auth_context: Already authenticated Utils context.
            request_id: Optional exact request identity.

        Returns:
            Structured construction result or failure.
        """
        logger.info("Serving public Portfolio construction operation")
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
                request_id=safe_request_id,
                correlation_id=correlation_id,
            )
        except Exception as error:  # noqa: BLE001 - public exception boundary.
            return self._failure(
                error,
                request_id=safe_request_id,
                correlation_id=correlation_id,
            )

    def status(
        self,
        portfolio_id: str,
        scope: Mapping[str, str],
        auth_context: AuthContext,
        request_id: str | None = None,
    ) -> PortfolioOutcome[ActivePortfolioAllocation]:
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
        safe_request_id, correlation_id = self._fallback_trace(auth_context, request_id)
        try:
            safe_request_id, correlation_id = self._trace(auth_context, request_id)
            return self._success(
                self._active(portfolio_id, scope),
                request_id=safe_request_id,
                correlation_id=correlation_id,
            )
        except Exception as error:  # noqa: BLE001 - public exception boundary.
            return self._failure(
                error,
                request_id=safe_request_id,
                correlation_id=correlation_id,
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
    ) -> PortfolioOutcome[ActivePortfolioAllocation]:
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
                request_id=safe_request_id,
                correlation_id=correlation_id,
                audit_event_id=value.audit_ref,
            )
        except Exception as error:  # noqa: BLE001 - public exception boundary.
            return self._failure(
                error,
                request_id=safe_request_id,
                correlation_id=correlation_id,
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
    ) -> PortfolioOutcome[PortfolioRebalancePlan]:
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
                request_id=safe_request_id,
                correlation_id=correlation_id,
            )
        except Exception as error:  # noqa: BLE001 - public exception boundary.
            return self._failure(
                error,
                request_id=safe_request_id,
                correlation_id=correlation_id,
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
    ) -> PortfolioOutcome[PortfolioRebalancePlan]:
        """Submit and measure one Risk-reviewed reduce-only plan.

        Args:
            plan: Current immutable rebalance plan.
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
                request_id=safe_request_id,
                correlation_id=correlation_id,
            )
        except Exception as error:  # noqa: BLE001 - public exception boundary.
            return self._failure(
                error,
                request_id=safe_request_id,
                correlation_id=correlation_id,
            )

    def recompute_measurement(
        self,
        plan_id: str,
        *,
        trading_request_id: str,
        auth_context: AuthContext,
        request_id: str | None = None,
    ) -> PortfolioOutcome[PortfolioRebalancePlan]:
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
        safe_request_id, correlation_id = self._fallback_trace(auth_context, request_id)
        try:
            safe_request_id, correlation_id = self._trace(auth_context, request_id)
            value = self._workflows.recompute_measurement(
                plan_id,
                trading_request_id=trading_request_id,
            )
            return self._success(
                value,
                request_id=safe_request_id,
                correlation_id=correlation_id,
            )
        except Exception as error:  # noqa: BLE001 - public exception boundary.
            return self._failure(
                error,
                request_id=safe_request_id,
                correlation_id=correlation_id,
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
    ) -> PortfolioOutcome[ActivePortfolioAllocation]:
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
                request_id=safe_request_id,
                correlation_id=correlation_id,
                audit_event_id=value.audit_ref,
            )
        except Exception as error:  # noqa: BLE001 - public exception boundary.
            return self._failure(
                error,
                request_id=safe_request_id,
                correlation_id=correlation_id,
            )

    def history(
        self,
        portfolio_id: str,
        auth_context: AuthContext,
        request_id: str | None = None,
    ) -> PortfolioOutcome[tuple[ActivePortfolioAllocation, ...]]:
        """Return immutable allocation history in activation order.

        Args:
            portfolio_id: Portfolio identity.
            auth_context: Already authenticated Utils context.
            request_id: Optional exact request identity.

        Returns:
            Structured immutable history or failure.
        """
        logger.info("Serving public Portfolio history operation")
        safe_request_id, correlation_id = self._fallback_trace(auth_context, request_id)
        try:
            safe_request_id, correlation_id = self._trace(auth_context, request_id)
            return self._success(
                self._repository.history(portfolio_id),
                request_id=safe_request_id,
                correlation_id=correlation_id,
            )
        except Exception as error:  # noqa: BLE001 - public exception boundary.
            return self._failure(
                error,
                request_id=safe_request_id,
                correlation_id=correlation_id,
            )


__all__: tuple[str, ...] = ("PortfolioService",)
