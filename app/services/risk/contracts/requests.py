"""Strict Risk-owned request contracts."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, field_validator, model_validator

from app.services.strategy import TradeIntent  # noqa: TC001
from app.utils import logger


def _utc(value: datetime) -> datetime:
    """Require aware UTC time.

    Args:
        value: Time to validate.

    Returns:
        Validated time.

    Raises:
        ValueError: If time is not aware UTC.
    """
    logger.debug("Validating Risk request UTC timestamp")
    if value.tzinfo is None or value.utcoffset() != timedelta(0):
        raise ValueError("timestamp must be aware UTC")
    return value


def _text(value: str) -> str:
    """Validate required request text.

    Args:
        value: Text to validate.

    Returns:
        Validated text.

    Raises:
        ValueError: If text is blank or untrimmed.
    """
    logger.debug("Validating Risk request text")
    if not value or value != value.strip():
        raise ValueError("value must be non-empty trimmed text")
    return value


class _RequestModel(BaseModel):
    """Private strict immutable request base."""

    model_config = ConfigDict(
        strict=True,
        extra="forbid",
        frozen=True,
        allow_inf_nan=False,
    )


class ProposedTrade(_RequestModel):
    """Risk-owned receiver request embedding one exact Strategy intent."""

    contract_version: Literal["v1"] = "v1"
    schema_id: Literal["risk.proposed_trade.v1"] = "risk.proposed_trade.v1"
    intent: TradeIntent
    account_id: str
    portfolio_id: str | None
    requested_size: Decimal
    current_price: Decimal
    stop_distance: Decimal | None
    market_as_of: datetime
    expires_at: datetime
    risk_profile: Literal["research", "simulation", "paper", "live"]
    evidence_refs: Mapping[str, str]
    provenance: Mapping[str, str]
    request_id: str
    workflow_id: str
    correlation_id: str

    @field_validator("account_id", "request_id", "workflow_id", "correlation_id")
    @classmethod
    def _validate_text(cls, value: str) -> str:
        """Validate proposal identity text.

        Args:
            value: Text to validate.

        Returns:
            Validated text.
        """
        logger.debug("Validating ProposedTrade identity")
        return _text(value)

    @field_validator("market_as_of", "expires_at")
    @classmethod
    def _validate_time(cls, value: datetime) -> datetime:
        """Validate proposal time.

        Args:
            value: Time to validate.

        Returns:
            Validated time.
        """
        logger.debug("Validating ProposedTrade timestamp")
        return _utc(value)

    @model_validator(mode="after")
    def _validate_proposal(self) -> ProposedTrade:
        """Validate proposal relationships and stop evidence.

        Returns:
            Validated proposal.

        Raises:
            ValueError: If proposal evidence conflicts.
        """
        logger.debug("Validating ProposedTrade relationships")
        if self.requested_size <= 0 or self.current_price <= 0:
            raise ValueError("requested size and current price must be positive")
        if self.expires_at <= self.market_as_of:
            raise ValueError("expires_at must follow market_as_of")
        if self.intent.intent_type in {"OPEN", "INCREASE"} and (
            self.stop_distance is None or self.stop_distance <= 0
        ):
            raise ValueError("risk-increasing proposal requires stop distance")
        if (
            self.intent.quantity_hint is not None
            and self.intent.quantity_hint != self.requested_size
        ):
            raise ValueError("requested size conflicts with embedded intent")
        if not self.evidence_refs or not self.provenance:
            raise ValueError("proposal requires evidence and provenance")
        return self


class PositionSizingRequest(_RequestModel):
    """Complete evidence for one supported sizing method."""

    method: Literal[
        "fixed_lot",
        "fixed_risk",
        "milestone",
        "fractional_kelly",
        "volatility",
        "fixed_fractional",
    ]
    requested_size: Decimal | None
    fixed_lot: Decimal | None
    risk_amount: Decimal | None
    risk_fraction: Decimal | None
    stop_distance: Decimal | None
    unit_value: Decimal | None
    milestone_multiplier: Decimal | None
    win_rate: Decimal | None
    payoff_ratio: Decimal | None
    trade_count: int | None
    volatility_multiplier: Decimal | None
    asset_volatility: Decimal | None
    broker_min_size: Decimal
    broker_max_size: Decimal
    broker_size_step: Decimal
    evidence_refs: Mapping[str, str]
    request_id: str

    @model_validator(mode="after")
    def _validate_method(self) -> PositionSizingRequest:
        """Validate method-specific sizing evidence.

        Returns:
            Validated request.

        Raises:
            ValueError: If required method evidence is absent.
        """
        logger.debug("Validating sizing method evidence")
        if min(self.broker_min_size, self.broker_max_size, self.broker_size_step) <= 0:
            raise ValueError("broker size constraints must be positive")
        if self.broker_min_size > self.broker_max_size:
            raise ValueError("broker minimum exceeds maximum")
        required: dict[str, tuple[object | None, ...]] = {
            "fixed_lot": (self.fixed_lot,),
            "fixed_risk": (self.risk_amount, self.stop_distance, self.unit_value),
            "milestone": (self.fixed_lot, self.milestone_multiplier),
            "fractional_kelly": (
                self.win_rate,
                self.payoff_ratio,
                self.trade_count,
                self.stop_distance,
                self.unit_value,
            ),
            "volatility": (
                self.risk_fraction,
                self.volatility_multiplier,
                self.asset_volatility,
                self.unit_value,
            ),
            "fixed_fractional": (
                self.risk_fraction,
                self.stop_distance,
                self.unit_value,
            ),
        }
        if any(item is None for item in required[self.method]):
            raise ValueError("sizing method evidence is incomplete")
        positive = (
            self.fixed_lot,
            self.risk_amount,
            self.risk_fraction,
            self.stop_distance,
            self.unit_value,
            self.milestone_multiplier,
            self.payoff_ratio,
            self.volatility_multiplier,
            self.asset_volatility,
        )
        if any(item is not None and item <= 0 for item in positive):
            raise ValueError("sizing evidence must be positive")
        if self.win_rate is not None and not Decimal(0) <= self.win_rate <= Decimal(1):
            raise ValueError("win rate must be between zero and one")
        if self.trade_count is not None and self.trade_count < 0:
            raise ValueError("trade count must be non-negative")
        return self


class AllocationReviewRequest(_RequestModel):
    """Self-contained Risk projection of an allocation or rebalance."""

    contract_version: Literal["v1"] = "v1"
    schema_id: Literal["risk.allocation_review_request.v1"] = (
        "risk.allocation_review_request.v1"
    )
    projection_kind: Literal["construction", "rebalance"]
    portfolio_id: str
    portfolio_version: str
    result_id: str | None
    plan_id: str | None
    ordered_components: tuple[Mapping[str, str], ...]
    eligibility_decision_refs: tuple[str, ...]
    account_evidence_ref: str
    market_evidence_ref: str
    fx_evidence_refs: tuple[str, ...]
    evidence_hashes: Mapping[str, str]
    runtime_profile: Literal["simulation", "paper", "live"]
    execution_route: Literal["sim", "paper", "live"]
    approval_refs: tuple[str, ...]
    requested_at: datetime
    request_id: str
    workflow_id: str
    correlation_id: str

    @model_validator(mode="after")
    def _validate_projection(self) -> AllocationReviewRequest:
        """Validate self-contained allocation identity.

        Returns:
            Validated request.

        Raises:
            ValueError: If the projection is incomplete or incompatible.
        """
        logger.debug("Validating allocation review projection")
        _utc(self.requested_at)
        expected_route = {
            "simulation": "sim",
            "paper": "paper",
            "live": "live",
        }[self.runtime_profile]
        if self.execution_route != expected_route:
            raise ValueError("profile and route are incompatible")
        if not self.ordered_components or not self.evidence_hashes:
            raise ValueError("allocation projection is not self-contained")
        if self.projection_kind == "construction" and self.result_id is None:
            raise ValueError("construction requires result_id")
        if self.projection_kind == "rebalance" and self.plan_id is None:
            raise ValueError("rebalance requires plan_id")
        return self


class AllocationBudgetActivationRequest(_RequestModel):
    """Exact request to activate one approved Risk budget projection."""

    contract_version: Literal["v1"] = "v1"
    schema_id: Literal["risk.allocation_budget_activation_request.v1"] = (
        "risk.allocation_budget_activation_request.v1"
    )
    portfolio_id: str
    allocation_version: str
    decision_id: str
    scope: Mapping[str, str]
    effective_at: datetime
    predecessor_version: str | None
    request_id: str
    workflow_id: str
    correlation_id: str

    @model_validator(mode="after")
    def _validate_activation(self) -> AllocationBudgetActivationRequest:
        """Validate budget activation bindings.

        Returns:
            Validated request.

        Raises:
            ValueError: If a binding or time is invalid.
        """
        logger.debug("Validating allocation budget activation request")
        _utc(self.effective_at)
        if not self.scope:
            raise ValueError("activation scope is required")
        return self


class StrategyOperationalEligibilityRequest(_RequestModel):
    """Request operational eligibility for one exact registered strategy."""

    contract_version: Literal["v1"] = "v1"
    schema_id: Literal["risk.strategy_operational_eligibility_request.v1"] = (
        "risk.strategy_operational_eligibility_request.v1"
    )
    strategy_id: str
    strategy_version: str
    runtime_profile: Literal["simulation", "paper", "live"]
    execution_route: Literal["sim", "paper", "live"]
    policy_version: str
    registration_ref: str
    evidence_refs: Mapping[str, str]
    approval_refs: tuple[str, ...]
    requested_scope: Mapping[str, str]
    requested_at: datetime
    request_id: str
    workflow_id: str
    correlation_id: str

    @model_validator(mode="after")
    def _validate_request(self) -> StrategyOperationalEligibilityRequest:
        """Validate exact strategy and runtime bindings.

        Returns:
            Validated request.

        Raises:
            ValueError: If identity, scope, or route is incompatible.
        """
        logger.debug("Validating strategy operational eligibility request")
        _utc(self.requested_at)
        expected = {"simulation": "sim", "paper": "paper", "live": "live"}
        if self.execution_route != expected[self.runtime_profile]:
            raise ValueError("profile and route are incompatible")
        if not self.evidence_refs or not self.requested_scope:
            raise ValueError("eligibility evidence and scope are required")
        return self


class ApprovalAttestation(_RequestModel):
    """Authenticated human approval evidence without execution authority."""

    contract_version: Literal["v1"] = "v1"
    schema_id: Literal["risk.approval_attestation.v1"] = "risk.approval_attestation.v1"
    attestation_id: str
    principal_id: str
    action: str
    scope: Mapping[str, str]
    policy_ref: str
    policy_version: str
    issued_at: datetime
    expires_at: datetime
    request_id: str
    workflow_id: str
    correlation_id: str

    @model_validator(mode="after")
    def _validate_attestation(self) -> ApprovalAttestation:
        """Validate attestation scope and lifetime.

        Returns:
            Validated attestation.

        Raises:
            ValueError: If scope or lifetime is invalid.
        """
        logger.debug("Validating approval attestation")
        _utc(self.issued_at)
        _utc(self.expires_at)
        if self.expires_at <= self.issued_at or not self.scope:
            raise ValueError("attestation requires valid scope and expiry")
        return self


class ScenarioDefinition(_RequestModel):
    """Bounded deterministic advisory scenario definition."""

    scenario_id: str
    shocks: Mapping[str, Decimal]
    randomized: bool
    seed: int | None
    assumptions: tuple[str, ...]

    @model_validator(mode="after")
    def _validate_scenario(self) -> ScenarioDefinition:
        """Validate deterministic scenario evidence.

        Returns:
            Validated scenario.

        Raises:
            ValueError: If shocks are invalid or randomness is unseeded.
        """
        logger.debug("Validating scenario definition")
        if not self.shocks:
            raise ValueError("scenario shocks are required")
        if any(not value.is_finite() for value in self.shocks.values()):
            raise ValueError("scenario shocks must be finite")
        if self.randomized and self.seed is None:
            raise ValueError("randomized scenario requires seed")
        return self


class KillSwitchCommand(_RequestModel):
    """Authorized request to activate or clear canonical kill-switch state."""

    contract_version: Literal["v1"] = "v1"
    schema_id: Literal["risk.kill_switch_command.v1"] = "risk.kill_switch_command.v1"
    action: Literal["activate", "clear"]
    scope_level: Literal["global", "portfolio", "strategy", "symbol"]
    portfolio_id: str | None
    strategy_id: str | None
    symbol: str | None
    reason: str
    requested_at: datetime
    request_id: str
    workflow_id: str
    correlation_id: str

    @model_validator(mode="after")
    def _validate_command(self) -> KillSwitchCommand:
        """Validate exact scope identifiers and reason.

        Returns:
            Validated command.

        Raises:
            ValueError: If scope identifiers conflict.
        """
        logger.debug("Validating kill-switch command")
        _utc(self.requested_at)
        _text(self.reason)
        required = {
            "global": (),
            "portfolio": (self.portfolio_id,),
            "strategy": (self.strategy_id,),
            "symbol": (self.symbol,),
        }[self.scope_level]
        if any(value is None for value in required):
            raise ValueError("kill-switch scope identifier is missing")
        return self


__all__ = [
    "AllocationBudgetActivationRequest",
    "AllocationReviewRequest",
    "ApprovalAttestation",
    "KillSwitchCommand",
    "PositionSizingRequest",
    "ProposedTrade",
    "ScenarioDefinition",
    "StrategyOperationalEligibilityRequest",
]
