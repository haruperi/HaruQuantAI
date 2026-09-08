"""Focused business logic for immutable Agentic mandate enforcement."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Callable

from app.contracts.agentic.mandate import (
    BudgetEnvelope, CheckMandateScopeRequest, InspectMandateRequest, MandateAccepted,
    MandateOutcome, MandateRequest, MandateResult, MandateScopeDecision,
    ValidateMandateRequest, mandate_digest,
)

ABSOLUTE_FORBIDDEN_AUTHORITY = frozenset({
    "broker_credentials", "order_construction", "order_execution", "risk_approval",
    "kill_switch_clear", "live_deployment", "receiver_authority", "receiver_bypass",
})


def _min_budget(*budgets: BudgetEnvelope) -> BudgetEnvelope:
    deadlines = [item.deadline_at for item in budgets if item.deadline_at is not None]
    return BudgetEnvelope(
        max_input_tokens=min(item.max_input_tokens for item in budgets),
        max_output_tokens=min(item.max_output_tokens for item in budgets),
        max_model_calls=min(item.max_model_calls for item in budgets),
        max_tool_calls=min(item.max_tool_calls for item in budgets),
        max_cost=min(item.max_cost for item in budgets),
        deadline_at=min(deadlines) if deadlines else None,
    )


def _budget_within(requested: BudgetEnvelope, ceiling: BudgetEnvelope) -> bool:
    return (
        requested.max_input_tokens <= ceiling.max_input_tokens
        and requested.max_output_tokens <= ceiling.max_output_tokens
        and requested.max_model_calls <= ceiling.max_model_calls
        and requested.max_tool_calls <= ceiling.max_tool_calls
        and requested.max_cost <= ceiling.max_cost
        and (ceiling.deadline_at is None or (requested.deadline_at is not None and requested.deadline_at <= ceiling.deadline_at))
    )


class MandateService:
    """Stateless fail-closed mandate evaluator."""

    def __init__(self, accounts: object, settings: object, *, clock: Callable[[], datetime] | None = None) -> None:
        self._accounts = accounts
        self._settings = settings
        self._clock = clock or (lambda: datetime.now(timezone.utc))
        self._closed = False

    async def enforce_mandate(self, request: MandateRequest) -> MandateResult:
        if self._closed:
            raise RuntimeError("enforce-mandate service is closed")
        checked_at = self._clock()
        mandate = request.mandate
        invalid = self._invalid_reason(mandate, checked_at)
        if invalid is not None:
            return self._invalid_result(request, checked_at, invalid)
        if isinstance(request, InspectMandateRequest):
            return mandate
        if isinstance(request, ValidateMandateRequest):
            return MandateAccepted(MandateOutcome.ACCEPTED, f"{mandate.mandate_id}:{mandate.version}", mandate.budgets, mandate.integrity_digest, checked_at)
        if not isinstance(request, CheckMandateScopeRequest):
            raise TypeError("unsupported mandate request")
        reasons: list[str] = []
        for value, allowed, code in (
            (request.feature_id, mandate.enabled_features, "FEATURE_NOT_ENABLED"),
            (request.role_id, mandate.enabled_roles, "ROLE_NOT_ENABLED"),
            (request.environment, mandate.environments, "ENVIRONMENT_NOT_ALLOWED"),
            (request.account_id, mandate.account_scopes, "ACCOUNT_NOT_ALLOWED"),
            (request.asset_id, mandate.asset_scopes, "ASSET_NOT_ALLOWED"),
        ):
            if value not in allowed:
                reasons.append(code)
        ceilings = [mandate.budgets]
        if request.parent_remaining_budget is not None:
            ceilings.append(request.parent_remaining_budget)
        effective = _min_budget(*ceilings)
        if not _budget_within(request.requested_budget, effective):
            reasons.append("BUDGET_EXCEEDED")
        return MandateScopeDecision(
            MandateOutcome.ALLOWED if not reasons else MandateOutcome.DENIED,
            request.feature_id, request.role_id, request.environment, request.account_id,
            request.asset_id, request.requested_budget, tuple(reasons),
            effective if not reasons else None, checked_at,
        )

    def _invalid_reason(self, mandate: object, checked_at: datetime) -> str | None:
        if mandate_digest(mandate) != mandate.integrity_digest:
            return "MANDATE_INTEGRITY_INVALID"
        if checked_at < mandate.effective_at:
            return "MANDATE_NOT_EFFECTIVE"
        if checked_at >= mandate.expires_at:
            return "MANDATE_EXPIRED"
        if ABSOLUTE_FORBIDDEN_AUTHORITY.intersection(mandate.enabled_features):
            return "MANDATE_AUTHORITY_ESCALATION"
        return None

    def _invalid_result(self, request: MandateRequest, checked_at: datetime, code: str) -> MandateResult:
        if isinstance(request, CheckMandateScopeRequest):
            return MandateScopeDecision(
                MandateOutcome.INVALID, request.feature_id, request.role_id, request.environment,
                request.account_id, request.asset_id, request.requested_budget, (code,), None, checked_at,
            )
        return MandateAccepted(
            MandateOutcome.INVALID, f"{request.mandate.mandate_id}:{request.mandate.version}",
            request.mandate.budgets, request.mandate.integrity_digest, checked_at,
        )

    def close(self) -> None:
        """Fail closed after scope teardown."""
        self._closed = True
