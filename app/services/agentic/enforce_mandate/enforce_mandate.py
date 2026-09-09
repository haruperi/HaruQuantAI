"""Production domain logic for Mandate Enforcement."""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from app.composition.logging import get_logger
from app.contracts.agentic.mandate import (
    SYSTEM_PROHIBITED_AUTHORITIES,
    BudgetEnvelope,
    CheckMandateScopeRequest,
    FirmMandate,
    InspectMandateRequest,
    MandateAccepted,
    MandateRefused,
    MandateRequest,
    MandateResponse,
    MandateScopeDecision,
    MandateView,
    ValidateMandateRequest,
    compute_mandate_digest,
)

if TYPE_CHECKING:
    from app.contracts.workspace.administer_settings import AdministerSettingsCapability
    from app.contracts.workspace.manage_accounts import ManageAccountsCapability

_LOGGER = get_logger("agentic.enforce_mandate")


class EnforceMandateService:
    """Stateless, fail-closed Mandate Enforcement service."""

    def __init__(
        self,
        accounts_port: ManageAccountsCapability | None = None,
        settings_port: AdministerSettingsCapability | None = None,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        """Initialize mandate enforcement service with required ports.

        Args:
            accounts_port: Capability for account/session verification.
            settings_port: Capability for system settings administration.
            clock: Injected clock returning current UTC datetime.
        """
        self._accounts_port = accounts_port
        self._settings_port = settings_port
        self._clock = clock or (lambda: datetime.now(UTC))
        self._closed = False

    def close(self) -> None:
        """Close the service and release references."""
        self._closed = True
        self._accounts_port = None
        self._settings_port = None
        _LOGGER.debug("EnforceMandateService closed")

    def _verify_preconditions(self, now: datetime) -> MandateRefused | None:
        """Verify service state and required dependencies.

        Args:
            now: Current timestamp.

        Returns:
            MandateRefused if preconditions fail, else None.
        """
        if self._closed:
            return MandateRefused(
                outcome="UNAVAILABLE",
                reason_codes=("SERVICE_CLOSED",),
                checked_at=now,
            )
        if self._accounts_port is None or self._settings_port is None:
            return MandateRefused(
                outcome="UNAVAILABLE",
                reason_codes=("DEPENDENCY_UNAVAILABLE",),
                checked_at=now,
            )
        return None

    def _verify_integrity_and_interval(
        self, mandate: FirmMandate, now: datetime
    ) -> MandateRefused | None:
        """Validate mandate digest and temporal validity.

        Args:
            mandate: Firm mandate to check.
            now: Current timestamp.

        Returns:
            MandateRefused if validation fails, else None.
        """
        expected_digest = compute_mandate_digest(mandate)
        if mandate.integrity_digest != expected_digest:
            _LOGGER.warning(
                "Mandate %s integrity check failed: expected %s, got %s",
                mandate.mandate_id,
                expected_digest,
                mandate.integrity_digest,
            )
            return MandateRefused(
                outcome="INVALID",
                reason_codes=("INTEGRITY_DIGEST_MISMATCH",),
                checked_at=now,
            )

        if now < mandate.effective_at:
            return MandateRefused(
                outcome="REFUSED",
                reason_codes=("MANDATE_FUTURE",),
                checked_at=now,
            )

        if now >= mandate.expires_at:
            return MandateRefused(
                outcome="REFUSED",
                reason_codes=("MANDATE_EXPIRED",),
                checked_at=now,
            )

        return None

    async def enforce_mandate(self, request: MandateRequest) -> MandateResponse:
        """Evaluate one mandate validation, scope check, or inspection operation.

        Args:
            request: Validated mandate request.

        Returns:
            MandateAccepted, MandateScopeDecision, MandateRefused, or MandateView.
        """
        now = self._clock()

        precond_err = self._verify_preconditions(now)
        if precond_err is not None:
            return precond_err

        mandate = request.mandate
        valid_err = self._verify_integrity_and_interval(mandate, now)
        if valid_err is not None:
            return valid_err

        if isinstance(request, ValidateMandateRequest):
            return self._handle_validate(mandate, now)
        if isinstance(request, InspectMandateRequest):
            return MandateView(mandate=mandate, checked_at=now)
        return await self._handle_check_scope(request, mandate, now)

    def _handle_validate(self, mandate: FirmMandate, now: datetime) -> MandateAccepted:
        """Handle pure validation of mandate.

        Args:
            mandate: Validated firm mandate.
            now: Current timestamp.

        Returns:
            MandateAccepted outcome.
        """
        effective_limits: dict[str, object] = {
            "environments": mandate.environments,
            "enabled_features": mandate.enabled_features,
            "enabled_roles": mandate.enabled_roles,
            "account_scopes": mandate.account_scopes,
            "asset_scopes": mandate.asset_scopes,
            "budgets": mandate.budgets.model_dump(),
        }
        return MandateAccepted(
            outcome="ACCEPTED",
            mandate_ref=mandate.mandate_id,
            effective_limits=effective_limits,
            integrity_digest=mandate.integrity_digest,
            checked_at=now,
        )

    async def _fetch_system_settings(
        self, now: datetime
    ) -> tuple[dict[str, str] | None, MandateRefused | None]:
        """Fetch active system settings from the settings port.

        Args:
            now: Current timestamp.

        Returns:
            Tuple of (settings_dict, refusal_error).
        """
        try:
            from app.contracts.workspace.models import AdministerSettingsRequest

            req_id = "00000000-0000-7000-8000-000000000001"
            snap_id = "00000000-0000-7000-8000-000000000002"
            settings_res = await self._settings_port.administer_settings(  # type: ignore[union-attr]
                AdministerSettingsRequest(
                    request_id=req_id,
                    capability_snapshot_id=snap_id,
                    operation="READ_SYSTEM",
                )
            )
            settings: dict[str, str] = {}
            if hasattr(settings_res, "system") and settings_res.system is not None:
                settings = settings_res.system.settings
            return settings, None
        except Exception:
            _LOGGER.exception("Failed to query settings provider")
            return None, MandateRefused(
                outcome="UNAVAILABLE",
                reason_codes=("SETTINGS_PROVIDER_ERROR",),
                checked_at=now,
            )

    @staticmethod
    def _resolve_effective_dimensions(
        mandate: FirmMandate,
        system_settings: dict[str, str],
    ) -> tuple[set[str], set[str], set[str]]:
        """Narrow environment, role, and feature sets with system restrictions.

        Args:
            mandate: Firm mandate.
            system_settings: System settings map.

        Returns:
            Tuple of (allowed_envs, allowed_roles, allowed_features).
        """
        allowed_envs = set(mandate.environments)
        system_env = system_settings.get("environment") or system_settings.get(
            "allowed_environments"
        )
        if system_env:
            system_env_set = {e.strip() for e in system_env.split(",") if e.strip()}
            allowed_envs = allowed_envs & system_env_set

        allowed_roles = set(mandate.enabled_roles)
        system_roles = system_settings.get("allowed_roles")
        if system_roles:
            system_roles_set = {r.strip() for r in system_roles.split(",") if r.strip()}
            allowed_roles = allowed_roles & system_roles_set

        allowed_features = set(mandate.enabled_features)
        system_features = system_settings.get("allowed_features")
        if system_features:
            system_features_set = {
                f.strip() for f in system_features.split(",") if f.strip()
            }
            allowed_features = allowed_features & system_features_set

        return allowed_envs, allowed_roles, allowed_features

    @staticmethod
    def _check_requested_dimensions(
        request: CheckMandateScopeRequest,
        mandate: FirmMandate,
        allowed_envs: set[str],
        allowed_roles: set[str],
        allowed_features: set[str],
    ) -> list[str]:
        """Evaluate requested dimensions against effective scopes.

        Args:
            request: Scope check request.
            mandate: Firm mandate.
            allowed_envs: Narrowed environments.
            allowed_roles: Narrowed roles.
            allowed_features: Narrowed features.

        Returns:
            List of reason codes.
        """
        reasons: list[str] = []

        req_feat = request.requested_feature
        if req_feat is not None and req_feat not in allowed_features:
            code = (
                "FEATURE_NARROWED_BY_SYSTEM"
                if req_feat in mandate.enabled_features
                else "FEATURE_OUT_OF_MANDATE_SCOPE"
            )
            reasons.append(code)

        req_role = request.requested_role
        if req_role is not None and req_role not in allowed_roles:
            code = (
                "ROLE_NARROWED_BY_SYSTEM"
                if req_role in mandate.enabled_roles
                else "ROLE_OUT_OF_MANDATE_SCOPE"
            )
            reasons.append(code)

        req_env = request.requested_environment
        if req_env is not None and req_env not in allowed_envs:
            code = (
                "ENVIRONMENT_NARROWED_BY_SYSTEM"
                if req_env in mandate.environments
                else "ENVIRONMENT_OUT_OF_MANDATE_SCOPE"
            )
            reasons.append(code)

        if request.requested_account is not None:
            if request.requested_account not in mandate.account_scopes:
                reasons.append("ACCOUNT_OUT_OF_MANDATE_SCOPE")
            elif (
                request.auth_account is None
                or request.auth_account != request.requested_account
            ):
                reasons.append("ACCOUNT_NOT_AUTHENTICATED")

        if (
            request.requested_asset is not None
            and request.requested_asset not in mandate.asset_scopes
        ):
            reasons.append("ASSET_OUT_OF_MANDATE_SCOPE")

        return reasons

    def _resolve_effective_scope(
        self,
        request: CheckMandateScopeRequest,
        mandate: FirmMandate,
        system_settings: dict[str, str],
    ) -> tuple[list[str], dict[str, object]]:
        """Compute scope intersections and check permissions.

        Args:
            request: Scope check request.
            mandate: Firm mandate.
            system_settings: Active system settings.

        Returns:
            Tuple of (reason_codes, effective_limits_dict).
        """
        allowed_envs, allowed_roles, allowed_features = (
            self._resolve_effective_dimensions(mandate, system_settings)
        )
        reasons = self._check_requested_dimensions(
            request, mandate, allowed_envs, allowed_roles, allowed_features
        )

        limits: dict[str, object] = {
            "environments": tuple(sorted(allowed_envs)),
            "enabled_roles": tuple(sorted(allowed_roles)),
            "enabled_features": tuple(sorted(allowed_features)),
        }
        return reasons, limits

    def _resolve_effective_budget(
        self,
        requested_budget: BudgetEnvelope | None,
        parent_budget: BudgetEnvelope | None,
        mandate_budget: BudgetEnvelope,
    ) -> tuple[list[str], dict[str, object]]:
        """Check budget against mandate ceiling and parent unspent budget.

        Args:
            requested_budget: Optional requested budget.
            parent_budget: Optional parent remaining budget.
            mandate_budget: Mandate budget ceiling.

        Returns:
            Tuple of (budget_reason_codes, budget_limits_dict).
        """
        eff_in = min(
            mandate_budget.max_input_tokens,
            parent_budget.max_input_tokens
            if parent_budget
            else mandate_budget.max_input_tokens,
        )
        eff_out = min(
            mandate_budget.max_output_tokens,
            parent_budget.max_output_tokens
            if parent_budget
            else mandate_budget.max_output_tokens,
        )
        eff_model = min(
            mandate_budget.max_model_calls,
            parent_budget.max_model_calls
            if parent_budget
            else mandate_budget.max_model_calls,
        )
        eff_tool = min(
            mandate_budget.max_tool_calls,
            parent_budget.max_tool_calls
            if parent_budget
            else mandate_budget.max_tool_calls,
        )
        eff_cost = min(
            mandate_budget.max_cost,
            parent_budget.max_cost if parent_budget else mandate_budget.max_cost,
        )

        limits: dict[str, object] = {
            "effective_input_tokens": eff_in,
            "effective_output_tokens": eff_out,
            "effective_model_calls": eff_model,
            "effective_tool_calls": eff_tool,
            "effective_cost": eff_cost,
        }

        reasons: list[str] = []
        if requested_budget is not None:
            if requested_budget.max_input_tokens > eff_in:
                reasons.append("BUDGET_INPUT_TOKENS_EXCEEDED")
            if requested_budget.max_output_tokens > eff_out:
                reasons.append("BUDGET_OUTPUT_TOKENS_EXCEEDED")
            if requested_budget.max_model_calls > eff_model:
                reasons.append("BUDGET_MODEL_CALLS_EXCEEDED")
            if requested_budget.max_tool_calls > eff_tool:
                reasons.append("BUDGET_TOOL_CALLS_EXCEEDED")
            if requested_budget.max_cost > eff_cost:
                reasons.append("BUDGET_COST_EXCEEDED")

        return reasons, limits

    async def _handle_check_scope(
        self,
        request: CheckMandateScopeRequest,
        mandate: FirmMandate,
        now: datetime,
    ) -> MandateScopeDecision | MandateRefused:
        """Handle scope and boundary verification against mandate and system.

        Args:
            request: Scope check request.
            mandate: Validated firm mandate.
            now: Current timestamp.

        Returns:
            MandateScopeDecision or MandateRefused outcome.
        """
        prohibited_requested = set(request.prohibited_authority_requested)
        violating_authorities = (
            prohibited_requested & SYSTEM_PROHIBITED_AUTHORITIES
        ) | (prohibited_requested & set(mandate.prohibited_authority))
        if violating_authorities:
            _LOGGER.warning(
                "Attempt to grant prohibited authority: %s",
                sorted(violating_authorities),
            )
            return MandateScopeDecision(
                outcome="DENIED",
                reason_codes=("PROHIBITED_AUTHORITY_REQUESTED",),
                checked_at=now,
            )

        settings, settings_err = await self._fetch_system_settings(now)
        if settings_err is not None or settings is None:
            return (
                settings_err
                if settings_err is not None
                else MandateRefused(
                    outcome="UNAVAILABLE",
                    reason_codes=("SETTINGS_PROVIDER_ERROR",),
                    checked_at=now,
                )
            )

        scope_reasons, scope_limits = self._resolve_effective_scope(
            request, mandate, settings
        )
        budget_reasons, budget_limits = self._resolve_effective_budget(
            request.requested_budget, request.parent_budget, mandate.budgets
        )

        all_reasons = tuple(scope_reasons + budget_reasons)
        all_limits = {**scope_limits, **budget_limits}

        return MandateScopeDecision(
            outcome="DENIED" if all_reasons else "ALLOWED",
            requested_feature=request.requested_feature,
            requested_role=request.requested_role,
            requested_environment=request.requested_environment,
            requested_account=request.requested_account,
            requested_asset=request.requested_asset,
            requested_budget=request.requested_budget,
            reason_codes=all_reasons,
            effective_limits=all_limits,
            checked_at=now,
        )


__all__ = ["EnforceMandateService"]
