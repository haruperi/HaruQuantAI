"""Typed UI/API request boundary models."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import fields, is_dataclass
from datetime import datetime, time, timedelta
from decimal import Decimal
from enum import StrEnum
from hashlib import blake2b
from pathlib import Path
from types import MappingProxyType
from typing import Any, Generic, Literal, Self, TypeVar, cast

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    ValidationInfo,
    field_serializer,
    field_validator,
    model_validator,
)

from app.services.api._limits import MAX_ERROR_DETAILS, MAX_ERROR_TEXT_LENGTH
from app.services.data import build_market_dataset, is_market_dataset
from app.services.research import create_research_value, is_research_value
from app.utils import get_logger, is_sensitive_key, utc_now

_MAX_VISIBLE_IDS = 200
_MAX_REFERENCE_LENGTH = 200
_MAX_TEXT_LENGTH = 2_000
_MAX_SEQUENCE_ITEMS = 64
_HASH_HEX_LENGTH = 64
_HTTP_SUCCESS_MIN = 200
_HTTP_ERROR_MIN = 400

logger = get_logger(__name__)


class ApiErrorCode(StrEnum):
    """Stable API error code family."""

    AUTHENTICATION_REQUIRED = "AUTHENTICATION_REQUIRED"
    AUTHORIZATION_DENIED = "AUTHORIZATION_DENIED"
    AUTHORIZATION_FAILED = "AUTHORIZATION_FAILED"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    VALIDATION_FAILED = "VALIDATION_FAILED"
    INTERNAL_ERROR = "INTERNAL_ERROR"
    NOT_IMPLEMENTED = "NOT_IMPLEMENTED"
    DEPENDENCY_UNAVAILABLE = "DEPENDENCY_UNAVAILABLE"
    RATE_LIMITED = "RATE_LIMITED"
    GOVERNED_REQUEST_STALE = "GOVERNED_REQUEST_STALE"
    CSRF_REQUIRED = "CSRF_REQUIRED"
    CSRF_INVALID = "CSRF_INVALID"
    IDEMPOTENCY_KEY_REQUIRED = "IDEMPOTENCY_KEY_REQUIRED"
    DUPLICATE_IDEMPOTENCY_KEY = "DUPLICATE_IDEMPOTENCY_KEY"
    IDEMPOTENCY_CONFLICT = "IDEMPOTENCY_CONFLICT"
    GOVERNANCE_REQUIRED = "GOVERNANCE_REQUIRED"
    STALE_DATA = "STALE_DATA"
    UPSTREAM_UNAVAILABLE = "UPSTREAM_UNAVAILABLE"
    UPSTREAM_TIMEOUT = "UPSTREAM_TIMEOUT"
    UPSTREAM_NON_JSON_RESPONSE = "UPSTREAM_NON_JSON_RESPONSE"
    UNSUPPORTED_MEDIA_TYPE = "UNSUPPORTED_MEDIA_TYPE"


class ApiStatus(StrEnum):
    """Response status family."""

    SUCCESS = "success"
    ERROR = "error"


class StreamEventType(StrEnum):
    """Stream event families."""

    HEARTBEAT = "heartbeat"
    PAYLOAD = "payload"
    ERROR = "error"


class RouteSideEffect(StrEnum):
    """Route side-effect classification."""

    NONE = "none"
    READ = "read"
    STREAM = "stream"
    WRITE = "write"
    GOVERNED_WRITE = "governed_write"


class RouteStability(StrEnum):
    """Route stability classification."""

    STABLE = "stable"
    EXPERIMENTAL = "experimental"
    DEPRECATED = "deprecated"


_T = TypeVar("_T")


def _validate_non_empty(value: str, field_name: str) -> str:
    """Validate a trimmed non-empty string.

    Returns:
        The validated, bounded result.

    Raises:
        ValueError: If the declared validation fails.
    """
    if not value or value != value.strip():
        msg = f"{field_name} is required and must be non-empty and trimmed"
        raise ValueError(msg)
    return value


def _validate_route(value: str, field_name: str) -> str:
    """Validate a route-style path.

    Returns:
        The validated, bounded result.

    Raises:
        ValueError: If the declared validation fails.
    """
    value = _validate_non_empty(value, field_name)
    if not value.startswith("/"):
        msg = f"{field_name} must start with '/'"
        raise ValueError(msg)
    return value


def _validate_timestamp(value: datetime, field_name: str) -> datetime:
    """Validate UTC-aware timestamp.

    Returns:
        The validated, bounded result.

    Raises:
        ValueError: If the declared validation fails.
    """
    if value.tzinfo is None or value.tzinfo.utcoffset(value) != timedelta(0):
        msg = f"{field_name} must be UTC-aware"
        raise ValueError(msg)
    return value


class _BaseApiContract(BaseModel):
    """Shared immutable contract configuration."""

    model_config = ConfigDict(extra="forbid", frozen=True)


class ApiMetadata(_BaseApiContract):
    """Metadata for one API response envelope."""

    contract_version: Literal["v1"] = "v1"
    schema_id: Literal["api.metadata.v1"] = "api.metadata.v1"
    request_id: str
    route: str
    operation: str
    trace_id: str | None = None
    side_effect: Literal["none", "read", "write", "governed_write", "stream"] = "read"
    duration_ms: float | None = None
    timestamp: datetime = Field(default_factory=utc_now)
    stale: bool = False
    stale_reason: str | None = None
    next_cursor: str | None = None
    page_size: int | None = Field(default=None, ge=0, le=200)
    idempotency_replayed: bool = False

    @field_validator("request_id", "operation")
    @classmethod
    def _validate_text_fields(cls, value: str, info: ValidationInfo) -> str:
        """Validate required non-empty metadata text.

        Returns:
            The validated, bounded result.
        """
        return _validate_non_empty(value, str(getattr(info, "field_name", "field")))

    @field_validator("route")
    @classmethod
    def _validate_route_field(cls, value: str) -> str:
        """Validate metadata route.

        Returns:
            The validated, bounded result.
        """
        return _validate_route(value, "route")

    @field_validator("timestamp")
    @classmethod
    def _validate_timestamp(cls, value: datetime) -> datetime:
        """Validate metadata timestamp.

        Returns:
            The validated, bounded result.
        """
        return _validate_timestamp(value, "timestamp")

    @model_validator(mode="after")
    def _validate_stale_reason(self) -> Self:
        """Require stale reason when stale is true.

        Returns:
            The validated, bounded result.

        Raises:
            ValueError: If the declared validation fails.
        """
        if self.stale and not self.stale_reason:
            raise ValueError("stale_reason is required")
        return self


class ApiError(_BaseApiContract):
    """Structured API error envelope."""

    code: ApiErrorCode
    message: str
    details: Mapping[str, object] = Field(default_factory=dict)
    request_id: str | None = None
    trace_id: str | None = None
    retryable: bool = False

    @field_validator("message")
    @classmethod
    def _validate_message(cls, value: str) -> str:
        """Validate API error message.

        Returns:
            The validated, bounded result.
        """
        return _validate_non_empty(value, "message")

    @field_validator("details", mode="before")
    @classmethod
    def _validate_details(cls, value: object) -> Mapping[str, object]:
        """Validate bounded error details.

        Returns:
            The validated, bounded result.

        Raises:
            TypeError: If the declared validation fails.
            ValueError: If the declared validation fails.
        """
        if not isinstance(value, Mapping):
            raise TypeError("details must be a mapping")
        if len(value) > MAX_ERROR_DETAILS:
            raise ValueError("details must be at most 16 entries")
        for key, item in value.items():
            if not isinstance(key, str):
                raise TypeError("detail keys must be strings")
            _validate_non_empty(key, "detail key")
            if is_sensitive_key(key):
                raise ValueError("reserved key is not allowed")
            if isinstance(item, str) and len(item) > MAX_ERROR_TEXT_LENGTH:
                raise ValueError("detail text exceeds maximum length")
        return value


class ApiResponse(_BaseApiContract, Generic[_T]):  # noqa: UP046
    """Canonical non-stream response envelope."""

    status: ApiStatus
    message: str
    data: _T | None = None
    error: ApiError | None = None
    metadata: ApiMetadata

    @field_validator("message")
    @classmethod
    def _validate_message(cls, value: str) -> str:
        """Validate response message.

        Returns:
            The validated, bounded result.
        """
        return _validate_non_empty(value, "message")

    @model_validator(mode="after")
    def _validate_branches(self) -> Self:
        """Validate branch exclusivity for status.

        Returns:
            The validated, bounded result.

        Raises:
            ValueError: If the declared validation fails.
        """
        if self.status == ApiStatus.SUCCESS and self.error is not None:
            raise ValueError("success response cannot include an error")
        if self.status == ApiStatus.ERROR:
            if self.error is None:
                raise ValueError("error response requires error")
            if self.data is not None:
                raise ValueError("error response requires data=None")
        return self


class StreamEvent(_BaseApiContract):
    """Streaming event envelope."""

    sequence: int
    request_id: str
    trace_id: str | None = None
    route: str
    event_type: StreamEventType
    timestamp: datetime = Field(default_factory=utc_now)
    payload: Mapping[str, object] | None = None
    error: str | None = None
    cursor: str | None = None

    @field_validator("request_id")
    @classmethod
    def _validate_request_id(cls, value: str) -> str:
        """Validate stream request id.

        Returns:
            The validated, bounded result.
        """
        return _validate_non_empty(value, "request_id")

    @field_validator("route")
    @classmethod
    def _validate_route_field(cls, value: str) -> str:
        """Validate stream route.

        Returns:
            The validated, bounded result.
        """
        return _validate_route(value, "route")

    @field_validator("sequence")
    @classmethod
    def _validate_sequence(cls, value: int) -> int:
        """Validate sequence ordering.

        Returns:
            The validated, bounded result.

        Raises:
            ValueError: If the declared validation fails.
        """
        if value < 0:
            raise ValueError("sequence must be greater than or equal to 0")
        return value

    @field_validator("timestamp")
    @classmethod
    def _validate_timestamp(cls, value: datetime) -> datetime:
        """Validate event timestamp.

        Returns:
            The validated, bounded result.
        """
        return _validate_timestamp(value, "timestamp")

    @model_validator(mode="after")
    def _validate_shape(self) -> Self:
        """Validate event shape by type.

        Returns:
            The validated, bounded result.

        Raises:
            ValueError: If the declared validation fails.
        """
        if self.event_type == StreamEventType.HEARTBEAT and self.payload is not None:
            raise ValueError("heartbeat events cannot include payload")
        if self.event_type == StreamEventType.ERROR and self.error is None:
            raise ValueError("error events require error")
        if self.event_type != StreamEventType.ERROR and self.error is not None:
            raise ValueError("only error events may include error")
        if self.event_type == StreamEventType.PAYLOAD and self.payload is None:
            raise ValueError("payload events require payload")
        return self


class HealthDependencyCheck(_BaseApiContract):
    """One bounded dependency probe result for readiness."""

    component: str
    required: bool
    healthy: bool
    checked_at: datetime = Field(default_factory=utc_now)
    reason: str | None = None

    @field_validator("component")
    @classmethod
    def _validate_component(cls, value: str) -> str:
        """Validate the dependency component name.

        Returns:
            The validated, bounded result.
        """
        return _validate_non_empty(value, "component")

    @field_validator("reason")
    @classmethod
    def _validate_reason(cls, value: str | None, info: object) -> str | None:
        """Validate optional reason details.

        Returns:
            The validated, bounded result.
        """
        field_name = str(getattr(info, "field_name", "reason"))
        if value is not None:
            return _validate_non_empty(value, field_name)
        return None

    @field_validator("checked_at")
    @classmethod
    def _validate_checked_at(cls, value: datetime) -> datetime:
        """Validate readiness check timestamp.

        Returns:
            The validated, bounded result.
        """
        return _validate_timestamp(value, "checked_at")

    @model_validator(mode="after")
    def _validate_reason_required(self) -> Self:
        """Require a reason when a probe is unhealthy.

        Returns:
            The validated, bounded result.

        Raises:
            ValueError: If the declared validation fails.
        """
        if self.healthy and self.reason is not None:
            raise ValueError("reason is invalid when healthy")
        if not self.healthy and not self.reason:
            raise ValueError("unhealthy dependency requires reason")
        return self


class Liveness(_BaseApiContract):
    """Coarse process-level liveness contract."""

    status: Literal["healthy", "degraded", "unhealthy"] = "healthy"
    checked_at: datetime = Field(default_factory=utc_now)

    @field_validator("status")
    @classmethod
    def _validate_status(cls, value: str) -> str:
        """Validate liveness status.

        Returns:
            The validated, bounded result.
        """
        return _validate_non_empty(value, "status")

    @field_validator("checked_at")
    @classmethod
    def _validate_checked_at(cls, value: datetime) -> datetime:
        """Validate liveness timestamp.

        Returns:
            The validated, bounded result.
        """
        return _validate_timestamp(value, "checked_at")


class Readiness(_BaseApiContract):
    """Bounded readiness report with required/optional dependency checks."""

    status: Literal["ready", "degraded"] = "ready"
    checked_at: datetime = Field(default_factory=utc_now)
    clock_drift_seconds: Decimal
    dependencies: tuple[HealthDependencyCheck, ...] = ()

    @field_validator("checked_at")
    @classmethod
    def _validate_checked_at(cls, value: datetime) -> datetime:
        """Validate readiness timestamp.

        Returns:
            The validated, bounded result.
        """
        return _validate_timestamp(value, "checked_at")

    @field_validator("clock_drift_seconds")
    @classmethod
    def _validate_clock_drift(cls, value: Decimal) -> Decimal:
        """Validate bounded readiness clock drift.

        Returns:
            The validated, bounded result.

        Raises:
            ValueError: If the declared validation fails.
        """
        if value.is_nan():
            raise ValueError("clock_drift_seconds must be a finite decimal")
        return value

    @model_validator(mode="after")
    def _validate_dependencies(self) -> Self:
        """Validate required versus optional readiness semantics.

        Returns:
            The validated, bounded result.

        Raises:
            ValueError: If the declared validation fails.
        """
        required_failed = [
            dependency
            for dependency in self.dependencies
            if dependency.required and not dependency.healthy
        ]
        optional_failed = [
            dependency
            for dependency in self.dependencies
            if not dependency.required and not dependency.healthy
        ]
        if required_failed:
            raise ValueError("required dependencies must be healthy")
        if self.status == "ready" and optional_failed:
            raise ValueError("degraded checks must set status='degraded'")
        if self.status == "degraded" and not optional_failed:
            raise ValueError("degraded status requires at least one optional failure")
        if len({dependency.component for dependency in self.dependencies}) != len(
            self.dependencies,
        ):
            raise ValueError("dependency components must be unique")
        return self


class RouteContract(_BaseApiContract):
    """Boundary declaration for one route."""

    route_id: str
    method: str
    path: str
    owner: str
    response_contract: str | None = None
    request_contract: str | None = None
    request_schema: str | None = None
    permission: str | None = None
    side_effect: RouteSideEffect = RouteSideEffect.READ
    stability: RouteStability = RouteStability.STABLE
    auth_required: bool = False
    governance_scope: Literal["none", "required", "optional"] = "none"
    pagination: str | None = None
    idempotency_policy: Literal["none", "required", "optional"] | None = None
    rate_limit: str | None = None
    audit_events: bool = False
    success_statuses: tuple[int, ...] = (200,)
    error_statuses: tuple[int, ...] = (422, 500)
    observability: bool = True

    @field_validator("route_id", "owner")
    @classmethod
    def _validate_text_fields(cls, value: str, info: ValidationInfo) -> str:
        """Validate non-empty route declaration fields.

        Returns:
            The validated, bounded result.
        """
        return _validate_non_empty(value, str(getattr(info, "field_name", "field")))

    @field_validator("path")
    @classmethod
    def _validate_path(cls, value: str) -> str:
        """Validate route path.

        Returns:
            The validated, bounded result.
        """
        return _validate_route(value, "path")

    @field_validator("method")
    @classmethod
    def _validate_method(cls, value: str) -> str:
        """Validate method token.

        Returns:
            The validated, bounded result.
        """
        return _validate_non_empty(value, "method").upper()

    @model_validator(mode="after")
    def _validate_side_effect_rules(self) -> Self:
        """Validate side-effect constraints.

        Returns:
            The validated, bounded result.

        Raises:
            ValueError: If the declared validation fails.
        """
        if self.pagination is not None and not self.response_contract:
            raise ValueError("pagination requires a response contract")
        if (
            self.side_effect == RouteSideEffect.GOVERNED_WRITE
            and self.governance_scope != "required"
        ):
            raise ValueError("governed_write routes must require governance")
        if self.side_effect in {RouteSideEffect.WRITE, RouteSideEffect.GOVERNED_WRITE}:
            if self.idempotency_policy is None:
                raise ValueError("write routes require an explicit retry policy")
            if not self.audit_events:
                raise ValueError("write routes require audit events")
        if (
            self.side_effect == RouteSideEffect.GOVERNED_WRITE
            and self.idempotency_policy != "required"
        ):
            raise ValueError("governed_write routes require idempotency")
        if not self.success_statuses or any(
            status < _HTTP_SUCCESS_MIN or status >= _HTTP_ERROR_MIN
            for status in self.success_statuses
        ):
            raise ValueError("success_statuses must contain successful HTTP statuses")
        if not self.error_statuses or any(
            status < _HTTP_ERROR_MIN for status in self.error_statuses
        ):
            raise ValueError("error_statuses must contain error HTTP statuses")
        return self


class GovernedRequestContext(_BaseApiContract):
    """Evidence envelope for governed writes."""

    workflow: str
    permission: str
    actor_id: str
    evidence_id: str
    approval_id: str | None = None
    idempotency_key: str | None = None
    route_id: str | None = None
    audit_reference: str | None = None
    request_id: str | None = None
    trace_id: str | None = None
    stale_after_seconds: int = 30
    generated_at: datetime = Field(default_factory=utc_now)

    @field_validator("workflow", "permission", "actor_id", "evidence_id")
    @classmethod
    def _validate_text_fields(cls, value: str, info: ValidationInfo) -> str:
        """Validate required context fields.

        Returns:
            The validated, bounded result.
        """
        return _validate_non_empty(value, str(getattr(info, "field_name", "field")))

    @field_validator("generated_at")
    @classmethod
    def _validate_generated_at(cls, value: datetime) -> datetime:
        """Validate generation timestamp.

        Returns:
            The validated, bounded result.
        """
        return _validate_timestamp(value, "generated_at")

    @field_validator("stale_after_seconds")
    @classmethod
    def _validate_stale_after(cls, value: int) -> int:
        """Validate stale timeout.

        Returns:
            The validated, bounded result.

        Raises:
            ValueError: If the declared validation fails.
        """
        if value <= 0:
            raise ValueError("stale_after_seconds must be greater than zero")
        return value

    def is_stale(self, *, now: datetime | None = None) -> bool:
        """Return whether this context is stale."""
        now = now or utc_now()
        return (now - self.generated_at).total_seconds() > self.stale_after_seconds


class SimulationSessionCreateRequest(_BaseApiContract):
    """Request to open playback over one completed Simulation run."""

    run_id: str = Field(min_length=1, max_length=200)

    @field_validator("run_id")
    @classmethod
    def _validate_run_id(cls, value: str) -> str:
        """Validate one trimmed completed-run identity.

        Returns:
            Validated run identity.
        """
        return _validate_non_empty(value, "run_id")


class SimulationRunRequest(_BaseApiContract):
    """Exact API projection of ``SimulationBacktestRequestV1``."""

    contract_version: Literal["v1"] = "v1"
    schema_id: Literal["simulation.backtest_request.v1"] = (
        "simulation.backtest_request.v1"
    )
    request_id: str
    workflow_id: str
    correlation_id: str
    strategy_id: str
    strategy_version: str
    strategy_config_ref: str
    strategy_config_hash: str
    data_ref: str
    data_version: str
    data_hash: str
    tick_generation_ref: str
    tick_generation_version: str
    tick_generation_hash: str
    execution_profile_ref: str
    execution_profile_version: str
    execution_profile_hash: str
    risk_policy_ref: str
    risk_policy_version: str
    risk_policy_hash: str
    symbol: str
    timeframe: str
    start: datetime
    end: datetime
    parameters: Mapping[str, object]
    initial_balance: Decimal
    account_currency: str
    asset_class: Literal["FX"]
    seed: int
    runtime_profile: Literal["simulation", "fast_research"]
    execution_route: Literal["sim"]
    canonical: bool
    config_hash: str


class PortfolioComponentRunRequest(_BaseApiContract):
    """One exact portfolio component and its canonical backtest request."""

    component_id: str
    capital_weight: Decimal
    risk_budget: Decimal
    risk_decision_id: str
    metrics_ref: str
    backtest_request: SimulationRunRequest


class PortfolioSimulationRunRequest(_BaseApiContract):
    """Exact API projection of ``PortfolioBacktestRequestV1``."""

    contract_version: Literal["v1"] = "v1"
    schema_id: Literal["simulation.portfolio_backtest_request.v1"] = (
        "simulation.portfolio_backtest_request.v1"
    )
    request_id: str
    workflow_id: str
    correlation_id: str
    portfolio_id: str
    construction_result_id: str
    construction_version: str
    components: tuple[PortfolioComponentRunRequest, ...]
    measurement_start: datetime
    measurement_end: datetime
    base_currency: str
    fx_evidence_ids: tuple[str, ...]
    fx_evidence_versions: tuple[str, ...]
    fx_evidence_hashes: tuple[str, ...]
    execution_profile_version: str
    risk_policy_version: str
    seed: int
    initial_balance: Decimal
    runtime_profile: Literal["simulation"]
    execution_route: Literal["sim"]
    config_hash: str


class TradingMutationRequest(_BaseApiContract):
    """Exact API projection of one governed Trading request."""

    contract_version: Literal["v1"] = "v1"
    schema_id: Literal["trading.trading_request.v1"] = "trading.trading_request.v1"
    request_id: str
    workflow_id: str
    correlation_id: str
    causation_id: str | None = None
    route: Literal["paper", "live"]
    action: str
    provider_id: str | None = None
    account_id: str
    portfolio_id: str | None = None
    strategy_id: str
    strategy_version: str
    intent_id: str
    symbol: str | None = None
    side: Literal["BUY", "SELL"] | None = None
    order_type: Literal["MARKET", "LIMIT", "STOP", "STOP_LIMIT"]
    quantity_unit: str
    quantity: Decimal | None = None
    price: Decimal | None = None
    stop_price: Decimal | None = None
    stop_loss: Decimal | None = None
    take_profit: Decimal | None = None
    time_in_force: Literal["GTC", "IOC", "FOK", "GTD", "DAY"] | None = None
    expiration: datetime | None = None
    target_broker_order_id: str | None = None
    target_broker_position_id: str | None = None
    order_id: str | None = None
    position_id: str | None = None
    expected_version: int | None = None
    risk_decision_id: str
    action_policy_verdict_id: str
    approval_token_ref: str
    eligibility_decision_id: str | None = None
    allocation_decision_id: str | None = None
    scope_level: Literal["global", "portfolio", "strategy", "symbol"] | None = None
    control_reason: str | None = None
    idempotency_key: str
    canonical_material_version: str
    system_time: datetime
    broker_time: datetime | None = None
    valid_until: datetime
    instrument_min_quantity: Decimal | None = None
    instrument_max_quantity: Decimal | None = None
    instrument_quantity_step: Decimal | None = None
    instrument_price_tick: Decimal | None = None
    redaction_applied: Literal[True] = True


class PortfolioStrategyAllocationRef(_BaseApiContract):
    """Exact API projection of one Portfolio component reference.

    Attributes:
        component_id: Portfolio-local stable component identity.
        strategy_id: Strategy-owned immutable identity.
        strategy_version: Exact Strategy version.
        registry_record_hash: Strategy registry record digest.
        eligibility_decision_id: Risk eligibility decision reference.
    """

    component_id: str
    strategy_id: str
    strategy_version: str
    registry_record_hash: str
    eligibility_decision_id: str


class PortfolioFixedWeightInput(_BaseApiContract):
    """Exact API projection of one fixed-weight component.

    Attributes:
        component_id: Referenced component identity.
        capital_weight: Target capital metadata weight.
        proposed_risk_budget_weight: Non-authoritative proposed Risk budget.
    """

    component_id: str
    capital_weight: Decimal
    proposed_risk_budget_weight: Decimal


class PortfolioEvidenceReferenceSet(_BaseApiContract):
    """Exact API projection of one Portfolio construction evidence lineage.

    Attributes:
        account_snapshot_id: Data account snapshot reference.
        account_snapshot_hash: Account snapshot digest.
        account_snapshot_as_of: Account snapshot observation time.
        market_dataset_id: Data market dataset reference.
        market_dataset_hash: Market dataset digest.
        market_dataset_as_of: Market evidence observation time.
        analytics_evidence_id: Analytics evidence reference.
        analytics_evidence_hash: Analytics evidence digest.
        analytics_evidence_as_of: Analytics evidence observation time.
        fx_evidence_ids: Ordered Data FX evidence references.
        fx_evidence_hashes: Ordered digests aligned to each FX reference.
    """

    account_snapshot_id: str
    account_snapshot_hash: str
    account_snapshot_as_of: datetime
    market_dataset_id: str
    market_dataset_hash: str
    market_dataset_as_of: datetime
    analytics_evidence_id: str
    analytics_evidence_hash: str
    analytics_evidence_as_of: datetime
    fx_evidence_ids: tuple[str, ...]
    fx_evidence_hashes: tuple[str, ...]


class PortfolioConstructRequest(_BaseApiContract):
    """Exact API projection of ``PortfolioConstructionRequest``.

    The bridge converts this boundary model into the strict Portfolio-owned
    construction request through Portfolio's package-root value factory.
    """

    contract_version: Literal["v1"] = "v1"
    schema_id: Literal["portfolio.construction_request.v1"] = (
        "portfolio.construction_request.v1"
    )
    request_id: str
    workflow_id: str
    correlation_id: str
    causation_id: str | None = None
    portfolio_id: str
    portfolio_version: str
    scope: Mapping[str, str]
    components: tuple[PortfolioStrategyAllocationRef, ...]
    method: Literal["fixed", "equal", "inverse_volatility"]
    fixed_weights: tuple[PortfolioFixedWeightInput, ...]
    evidence: PortfolioEvidenceReferenceSet
    measurement_start: datetime
    measurement_end: datetime
    base_currency: str
    runtime_profile: Literal["simulation", "paper", "live"]
    execution_route: Literal["sim", "paper", "live"]
    simulation_policy_version: str
    requested_at: datetime


class PortfolioActivationRequest(_BaseApiContract):
    """Governed Portfolio activation command.

    Activation runs the complete owner workflow chain WF-PORT-001 through
    WF-PORT-004 as one governed write: the composed Portfolio workflow handle
    constructs the candidate and its validated evidence, coordinates the
    Simulation and Risk review, and only then activates. The gateway supplies
    no evidence of its own and never decides approval.
    """

    contract_version: Literal["v1"] = "v1"
    schema_id: Literal["api.portfolio_activation_request.v1"] = (
        "api.portfolio_activation_request.v1"
    )
    construction: PortfolioConstructRequest
    simulation: PortfolioSimulationRunRequest
    approval_refs: tuple[str, ...] = ()
    approval_attestation: Mapping[str, Any] | None = None
    approval_validation: Mapping[str, Any] | None = None
    expires_at: datetime
    expected_predecessor: str | None = None
    expected_revision: int


class PortfolioRollbackRequest(_BaseApiContract):
    """Governed Portfolio rollback command.

    Rollback shares activation's evidence chain and additionally names the
    immutable prior version being rolled back to. Portfolio creates a new
    forward version; no historical version is mutated or deleted.
    """

    contract_version: Literal["v1"] = "v1"
    schema_id: Literal["api.portfolio_rollback_request.v1"] = (
        "api.portfolio_rollback_request.v1"
    )
    construction: PortfolioConstructRequest
    simulation: PortfolioSimulationRunRequest
    rollback_of_version: str
    approval_refs: tuple[str, ...] = ()
    approval_attestation: Mapping[str, Any] | None = None
    approval_validation: Mapping[str, Any] | None = None
    expires_at: datetime
    expected_predecessor: str | None = None
    expected_revision: int


class PortfolioDriftRequest(_BaseApiContract):
    """Portfolio drift-assessment request over one active allocation.

    The gateway reads the active allocation through the Portfolio public status
    operation and forwards caller-supplied observed exposures. Drift thresholds
    and the resulting judgement remain entirely Portfolio-owned.
    """

    contract_version: Literal["v1"] = "v1"
    schema_id: Literal["api.portfolio_drift_request.v1"] = (
        "api.portfolio_drift_request.v1"
    )
    scope: Mapping[str, str]
    actual_exposures: Mapping[str, Decimal]
    evidence_as_of: datetime
    risk_decision: Mapping[str, Any]
    eligibility_decisions: Mapping[str, Mapping[str, Any]]


class PortfolioRebalanceRequest(_BaseApiContract):
    """Governed Portfolio rebalance submission.

    Every evidence reference is opaque and owner-resolved. The runtime profile
    and execution route must match the deployment's composed settings, and a
    live route additionally requires ``allow_live_mutations``; the composition
    layer enforces both before Portfolio is reached.
    """

    contract_version: Literal["v1"] = "v1"
    schema_id: Literal["api.portfolio_rebalance_request.v1"] = (
        "api.portfolio_rebalance_request.v1"
    )
    plan: Mapping[str, Any]
    account_evidence_ref: str
    market_evidence_ref: str
    fx_evidence_refs: tuple[str, ...]
    runtime_profile: Literal["simulation", "paper", "live"]
    execution_route: Literal["sim", "paper", "live"]
    approval_refs: tuple[str, ...]
    approval_token_ref: str
    trading_request_id: str
    valid_until: datetime


class PortfolioMeasurementRequest(_BaseApiContract):
    """Recompute one Portfolio measurement from immutable Trading evidence."""

    contract_version: Literal["v1"] = "v1"
    schema_id: Literal["api.portfolio_measurement_request.v1"] = (
        "api.portfolio_measurement_request.v1"
    )
    plan_id: str
    trading_request_id: str


class PageContext(_BaseApiContract):
    """Frontend context before redaction."""

    route: str
    user_id: str
    page_name: str
    approved_actions: tuple[str, ...] = ()
    visible_entity_ids: tuple[str, ...] = ()

    @field_validator("route")
    @classmethod
    def _validate_route(cls, value: str) -> str:
        """Validate route value.

        Returns:
            The validated, bounded result.
        """
        return _validate_route(value, "route")

    @field_validator("user_id", "page_name")
    @classmethod
    def _validate_text_fields(cls, value: str, info: ValidationInfo) -> str:
        """Validate principal and page fields.

        Returns:
            The validated, bounded result.
        """
        return _validate_non_empty(value, str(getattr(info, "field_name", "field")))

    @field_validator("approved_actions", "visible_entity_ids", mode="before")
    @classmethod
    def _validate_tuples(
        cls,
        value: object,
        info: ValidationInfo,
    ) -> tuple[str, ...]:
        """Validate one bounded sequence of identifiers.

        Returns:
            The validated, bounded result.

        Raises:
            TypeError: If the declared validation fails.
            ValueError: If the declared validation fails.
        """
        field_name = str(getattr(info, "field_name", "field"))
        if isinstance(value, str):
            values = (value,)
        elif isinstance(value, tuple | list):
            values = tuple(value)
        else:
            msg = f"{field_name} must be a tuple of strings"
            raise TypeError(msg)
        normalized = tuple(_validate_non_empty(item, field_name) for item in values)
        if len(set(normalized)) != len(normalized):
            msg = f"{field_name} must not contain duplicates"
            raise ValueError(msg)
        if field_name == "visible_entity_ids" and len(normalized) > _MAX_VISIBLE_IDS:
            raise ValueError("visible_entity_ids exceeds maximum limit")
        return normalized

    @property
    def redacted_visible_entity_ids(self) -> tuple[str, ...]:
        """Return deterministic redacted entity identifiers."""

        def _redact(value: str) -> str:
            digest = blake2b(value.encode("utf-8"), digest_size=6).hexdigest()
            return f"redacted:{digest}"

        return tuple(_redact(value) for value in self.visible_entity_ids)


class ResearchRunRequest(BaseModel):
    """Bounded authenticated request for one advisory Research run."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    hypothesis: str
    dataset: object
    config: object

    @field_validator("hypothesis")
    @classmethod
    def _validate_hypothesis(cls, value: str) -> str:
        """Validate explicit researcher-supplied hypothesis text.

        Returns:
            The validated, bounded result.

        Raises:
            ValueError: If the declared validation fails.
        """
        logger.debug("Validating API Research hypothesis")
        if not value or value != value.strip():
            raise ValueError("hypothesis must be non-empty and trimmed")
        return value

    @field_validator("dataset", mode="before")
    @classmethod
    def _coerce_dataset(cls, value: object) -> object:
        """Validate or rebuild one Data dataset contract.

        Returns:
            The validated, bounded result.

        Raises:
            TypeError: If the declared validation fails.
        """
        if is_market_dataset(value):
            return value
        if not isinstance(value, Mapping):
            raise TypeError("dataset must be a MarketDataset or serialized mapping")
        return build_market_dataset(**value)

    @field_validator("config", mode="before")
    @classmethod
    def _coerce_config(cls, value: object) -> object:
        """Accept either domain objects or serialized JSON payloads.

        Returns:
            The validated, bounded result.

        Raises:
            TypeError: If the declared validation fails.
        """
        if is_research_value(value, "EdgeLabConfig"):
            return value
        if not isinstance(value, Mapping):
            raise TypeError("config must be EdgeLabConfig or serialized mapping")

        sessions = cast("Mapping[str, object]", value["sessions"])
        windows = cast("Mapping[str, tuple[object, object]]", sessions["windows"])

        return create_research_value(
            "EdgeLabConfig",
            cleaning=create_research_value(
                "CleaningConfig", **cast("Mapping[str, object]", value["cleaning"])
            ),
            enrichment=create_research_value(
                "EnrichmentConfig", **cast("Mapping[str, object]", value["enrichment"])
            ),
            features=create_research_value(
                "FeatureConfig", **cast("Mapping[str, object]", value["features"])
            ),
            statistics=create_research_value(
                "StatisticalConfig", **cast("Mapping[str, object]", value["statistics"])
            ),
            studies=create_research_value(
                "StudyConfig", **cast("Mapping[str, object]", value["studies"])
            ),
            sessions=create_research_value(
                "SessionConfig",
                timezone=cast("str", sessions["timezone"]),
                windows={
                    key: (
                        _coerce_time(cast("str | time", windows[key][0])),
                        _coerce_time(cast("str | time", windows[key][1])),
                    )
                    for key in windows
                },
                overlap_precedence=tuple(
                    cast("tuple[str, ...] | list[str]", sessions["overlap_precedence"])
                ),
            ),
            market_structure=create_research_value(
                "MarketStructureConfig",
                **cast("Mapping[str, object]", value["market_structure"]),
            ),
            modeling=create_research_value(
                "UnsupervisedResearchConfig",
                **cast("Mapping[str, object]", value["modeling"]),
            ),
            artifacts=create_research_value(
                "ArtifactWriteConfig",
                allowed_root=Path(str(value["artifacts"]["allowed_root"])),
                **{
                    key: value["artifacts"][key]
                    for key in value["artifacts"]
                    if key != "allowed_root"
                },
            ),
            limits=create_research_value(
                "ResearchResourceLimits",
                **cast("Mapping[str, object]", value["limits"]),
            ),
            selected_stages=tuple(
                cast("tuple[str, ...] | list[str]", value["selected_stages"])
            ),
        )

    @field_serializer("config", when_used="json")
    def _serialize_config(self, value: object) -> dict[str, object]:
        """Serialize configuration with mappingproxy-safe nested values.

        Returns:
            The validated, bounded result.
        """
        return cast("dict[str, object]", _serialize_mappingproxy(value))


class AgenticRunSubmitRequest(_BaseApiContract):
    """Bounded authenticated request to reserve one Agentic run.

    Submitting reserves a run identifier; it does **not** execute agents. The
    bridge forwards these fields to the Agentic operator surface, which refuses
    an unregistered workflow deterministically.
    """

    workflow_name: str
    objective: str
    input_refs: tuple[str, ...] = ()
    deadline_seconds: int = Field(default=1_800, gt=0, le=86_400)
    cost_budget: str | None = Field(default=None, max_length=64)

    @field_validator("workflow_name", "objective")
    @classmethod
    def _validate_text(cls, value: str) -> str:
        """Validate non-empty trimmed bounded text.

        Args:
            value: Candidate text.

        Returns:
            The validated, trimmed text.

        Raises:
            ValueError: If the text is empty, untrimmed, or oversized.
        """
        if not value or value != value.strip():
            msg = "field must be non-empty trimmed text"
            raise ValueError(msg)
        if len(value) > _MAX_TEXT_LENGTH:
            msg = "field must not exceed 2000 characters"
            raise ValueError(msg)
        return value

    @field_validator("input_refs", mode="before")
    @classmethod
    def _coerce_input_refs(cls, value: object) -> tuple[str, ...]:
        """Normalize one JSON-style evidence-reference sequence.

        Args:
            value: Candidate sequence.

        Returns:
            Tuple of trimmed non-empty references.

        Raises:
            ValueError: If any reference is blank or the tuple is oversized.
        """
        if isinstance(value, str):
            items: tuple[str, ...] = (value,)
        elif isinstance(value, tuple | list):
            items = tuple(str(item) for item in value)
        else:
            items = ()
        normalized = tuple(item for item in items if item)
        if len(normalized) != len(items):
            msg = "input_refs must not contain blank entries"
            raise ValueError(msg)
        if len(normalized) > _MAX_SEQUENCE_ITEMS:
            msg = "input_refs must not exceed 64 entries"
            raise ValueError(msg)
        return normalized


class AgenticHandoffApprovalRequest(_BaseApiContract):
    """Bounded authenticated human approval of one staged Agentic artefact."""

    artifact_hash: str
    artifact_id: str
    rationale: str

    @field_validator("artifact_hash")
    @classmethod
    def _validate_hash(cls, value: str) -> str:
        """Validate one lowercase SHA-256 artefact digest.

        Args:
            value: Candidate digest.

        Returns:
            The validated digest.

        Raises:
            ValueError: If the digest is not 64 lowercase hex characters.
        """
        if len(value) != _HASH_HEX_LENGTH or any(
            ch not in "0123456789abcdef" for ch in value
        ):
            msg = "artifact_hash must be 64 lowercase hex characters"
            raise ValueError(msg)
        return value

    @field_validator("artifact_id", "rationale")
    @classmethod
    def _validate_text(cls, value: str) -> str:
        """Validate non-empty trimmed bounded text.

        Args:
            value: Candidate text.

        Returns:
            The validated, trimmed text.

        Raises:
            ValueError: If the text is empty, untrimmed, or oversized.
        """
        if not value or value != value.strip():
            msg = "field must be non-empty trimmed text"
            raise ValueError(msg)
        if len(value) > _MAX_TEXT_LENGTH:
            msg = "field must not exceed 2000 characters"
            raise ValueError(msg)
        return value


class AgenticQuarantineRequest(_BaseApiContract):
    """Bounded authenticated request to classify, contain, and record one incident."""

    run_id: str
    kind: Literal[
        "cost",
        "data_poisoning",
        "drift",
        "injection",
        "privilege",
        "provider",
        "runaway_loop",
        "sandbox",
        "schema",
    ]
    trigger: str
    role_id: str
    preserved_evidence_refs: tuple[str, ...]
    checkpoint_ref: str

    @field_validator("run_id", "role_id", "checkpoint_ref")
    @classmethod
    def _validate_reference(cls, value: str) -> str:
        """Validate one short non-empty trimmed reference.

        Args:
            value: Candidate reference.

        Returns:
            The validated, trimmed reference.

        Raises:
            ValueError: If the reference is empty, untrimmed, or oversized.
        """
        if not value or value != value.strip():
            msg = "reference must be non-empty trimmed text"
            raise ValueError(msg)
        if len(value) > _MAX_REFERENCE_LENGTH:
            msg = "reference must not exceed 200 characters"
            raise ValueError(msg)
        return value

    @field_validator("trigger")
    @classmethod
    def _validate_trigger(cls, value: str) -> str:
        """Validate the bounded incident trigger description.

        Args:
            value: Candidate trigger text.

        Returns:
            The validated, trimmed trigger text.

        Raises:
            ValueError: If the trigger is empty, untrimmed, or oversized.
        """
        if not value or value != value.strip():
            msg = "trigger must be non-empty trimmed text"
            raise ValueError(msg)
        if len(value) > _MAX_TEXT_LENGTH:
            msg = "trigger must not exceed 2000 characters"
            raise ValueError(msg)
        return value

    @field_validator("preserved_evidence_refs", mode="before")
    @classmethod
    def _coerce_evidence(cls, value: object) -> tuple[str, ...]:
        """Normalize one non-empty JSON-style evidence-reference sequence.

        Args:
            value: Candidate sequence.

        Returns:
            Tuple of trimmed non-empty references.

        Raises:
            ValueError: If the sequence is empty, blank, or oversized.
        """
        if isinstance(value, str):
            items: tuple[str, ...] = (value,)
        elif isinstance(value, tuple | list):
            items = tuple(str(item) for item in value)
        else:
            items = ()
        normalized = tuple(item.strip() for item in items if item.strip())
        if not normalized:
            msg = "preserved_evidence_refs must name at least one reference"
            raise ValueError(msg)
        if len(normalized) != len(items):
            msg = "preserved_evidence_refs must not contain blank entries"
            raise ValueError(msg)
        if len(normalized) > _MAX_SEQUENCE_ITEMS:
            msg = "preserved_evidence_refs must not exceed 64 entries"
            raise ValueError(msg)
        return normalized


class AgenticDisableRequest(_BaseApiContract):
    """Bounded authenticated request to stop the Agentic firm and settle runs."""

    run_ids: tuple[str, ...] = ()
    policy: Literal["cancel", "drain"] = "drain"

    @field_validator("run_ids", mode="before")
    @classmethod
    def _coerce_run_ids(cls, value: object) -> tuple[str, ...]:
        """Normalize one optional JSON-style run-identifier sequence.

        Args:
            value: Candidate sequence.

        Returns:
            Tuple of trimmed non-empty run identifiers.

        Raises:
            ValueError: If any identifier is blank or the tuple is oversized.
        """
        if isinstance(value, str):
            items: tuple[str, ...] = (value,)
        elif isinstance(value, tuple | list):
            items = tuple(str(item) for item in value)
        else:
            items = ()
        normalized = tuple(item.strip() for item in items if item.strip())
        if len(normalized) != len(items):
            msg = "run_ids must not contain blank entries"
            raise ValueError(msg)
        if len(normalized) > _MAX_SEQUENCE_ITEMS:
            msg = "run_ids must not exceed 64 entries"
            raise ValueError(msg)
        return normalized


def _serialize_mappingproxy(value: object) -> object:
    """Recursively convert mapping proxies, tuples, and dataclasses to JSON-safe values.

    Returns:
        The validated, bounded result.
    """
    if is_dataclass(value):
        return {
            field.name: _serialize_mappingproxy(getattr(value, field.name))
            for field in fields(value)
        }
    if isinstance(value, MappingProxyType):
        return {key: _serialize_mappingproxy(item) for key, item in value.items()}
    if isinstance(value, Mapping):
        return {key: _serialize_mappingproxy(item) for key, item in value.items()}
    if isinstance(value, tuple | list):
        return [_serialize_mappingproxy(item) for item in value]
    return value


def _coerce_time(value: str | time) -> time:
    """Normalize one session boundary value.

    Returns:
        The validated, bounded result.
    """
    if isinstance(value, time):
        return value
    return time.fromisoformat(value)


class OptimizationParameterSweepRequest(_BaseApiContract):
    """Serialized API projection of one Optimization ``SearchRequest``.

    The bridge reconstructs the strict Optimization-owned request through the
    Optimization package-root value factory; the serialized payload is
    validated only for non-emptiness and bounded size at the API boundary.
    """

    request_id: str
    payload: Mapping[str, object]


class OptimizationWalkForwardRequest(_BaseApiContract):
    """Serialized API projection of one Optimization ``WalkForwardRequest``."""

    request_id: str
    payload: Mapping[str, object]


class OptimizationWalkForwardMatrixRequest(_BaseApiContract):
    """Serialized API projection of a bounded walk-forward matrix request."""

    request_id: str
    requests: tuple[Mapping[str, object], ...]
    max_requests: int = Field(ge=1, le=20)


class OptimizationRobustnessRequest(_BaseApiContract):
    """Serialized API projection of one Optimization robustness request.

    The Optimization robustness contract is a discriminated union of
    ``MonteCarloRequest`` and ``ExecutionStressAnalysisRequest``. The presence
    of the ``stress`` field in ``payload`` selects the stress variant; the
    bridge reconstructs the correct owner value.
    """

    request_id: str
    payload: Mapping[str, object]
    max_simulations: int = Field(default=2000, ge=1, le=10_000)


class OptimizationCompareRequest(_BaseApiContract):
    """Serialized API projection of one Optimization comparison request."""

    request_id: str
    results: tuple[Mapping[str, object], ...]


class OptimizationStabilityRequest(_BaseApiContract):
    """Serialized API projection of one parameter-stability request."""

    request_id: str
    ranked_candidates: tuple[Mapping[str, object], ...]


class OptimizationOverfitRequest(_BaseApiContract):
    """Serialized API projection of one overfit-parameter evidence request."""

    request_id: str
    in_sample: Mapping[str, float]
    out_of_sample: Mapping[str, float]
    threshold: float


class OptimizationRankRequest(_BaseApiContract):
    """Serialized API projection of one parameter-set ranking request."""

    request_id: str
    candidates: tuple[Mapping[str, object], ...]


class OptimizationRobustnessScoreRequest(_BaseApiContract):
    """Serialized API projection of one robustness-score request."""

    request_id: str
    checks: tuple[bool, ...]


class OptimizationHandoffRequest(_BaseApiContract):
    """Serialized API projection of one Optimization evidence handoff request."""

    request_id: str
    payload: Mapping[str, object]


class StrategyRegistrationRequestModel(_BaseApiContract):
    """Serialized API projection of one Strategy registration command.

    Strategy owns the registration schema and its validation policy. The gateway
    forwards the caller payload to Strategy's package-root factory unchanged and
    never supplies, defaults, or repairs a field.
    """

    contract_version: Literal["v1"] = "v1"
    schema_id: Literal["api.strategy_registration_request.v1"] = (
        "api.strategy_registration_request.v1"
    )
    payload: Mapping[str, object]


class StrategyParameterUpdateRequestModel(_BaseApiContract):
    """Serialized API projection of one Strategy parameter update command."""

    contract_version: Literal["v1"] = "v1"
    schema_id: Literal["api.strategy_parameter_update_request.v1"] = (
        "api.strategy_parameter_update_request.v1"
    )
    payload: Mapping[str, object]


class DatasetPrepareRequest(_BaseApiContract):
    """Governed dataset preparation command.

    Preparation is a two-step owner delegation: Data fetches the requested
    market dataset and then persists it. Both request shapes belong to Data; the
    gateway forwards them and stores nothing itself.
    """

    contract_version: Literal["v1"] = "v1"
    schema_id: Literal["api.dataset_prepare_request.v1"] = (
        "api.dataset_prepare_request.v1"
    )
    market_request: Mapping[str, object]
    save_request: Mapping[str, object]


class DatasetImportRequest(_BaseApiContract):
    """Governed external dataset import command.

    Data owns parsing, dialect handling, validation, and persistence, and
    authors the resulting storage manifest. The gateway forwards the caller
    payload unchanged: it never reads the source file and never selects a
    dialect on the caller's behalf.
    """

    contract_version: Literal["v1"] = "v1"
    schema_id: Literal["api.dataset_import_request.v1"] = (
        "api.dataset_import_request.v1"
    )
    payload: Mapping[str, object]


class SimulationBranchRequest(_BaseApiContract):
    """Live what-if branch command.

    The overrides are Simulator-owned request fields. The gateway forwards them
    unchanged; the Simulator validates them and refuses any override that
    cannot produce a valid request, so no branch opens on bad input.
    """

    contract_version: Literal["v1"] = "v1"
    schema_id: Literal["api.simulation_branch_request.v1"] = (
        "api.simulation_branch_request.v1"
    )
    overrides: Mapping[str, Any]


class KillSwitchCommandRequest(_BaseApiContract):
    """Operator kill-switch command projection.

    Risk remains the sole kill-switch authority. The gateway authenticates a
    human operator, requires a distinct-principal approval, and forwards the
    command; it never computes, overrides, or clears canonical safety state.
    """

    contract_version: Literal["v1"] = "v1"
    schema_id: Literal["api.kill_switch_command_request.v1"] = (
        "api.kill_switch_command_request.v1"
    )
    scope_level: str
    scope: Mapping[str, str]
    command: Mapping[str, object]
    attestation: Mapping[str, Any] | None = None


__all__ = (
    "AgenticDisableRequest",
    "AgenticHandoffApprovalRequest",
    "AgenticQuarantineRequest",
    "AgenticRunSubmitRequest",
    "ApiError",
    "ApiErrorCode",
    "ApiMetadata",
    "ApiResponse",
    "ApiStatus",
    "DatasetImportRequest",
    "DatasetPrepareRequest",
    "GovernedRequestContext",
    "HealthDependencyCheck",
    "KillSwitchCommandRequest",
    "Liveness",
    "OptimizationCompareRequest",
    "OptimizationHandoffRequest",
    "OptimizationOverfitRequest",
    "OptimizationParameterSweepRequest",
    "OptimizationRankRequest",
    "OptimizationRobustnessRequest",
    "OptimizationRobustnessScoreRequest",
    "OptimizationStabilityRequest",
    "OptimizationWalkForwardMatrixRequest",
    "OptimizationWalkForwardRequest",
    "PageContext",
    "PortfolioActivationRequest",
    "PortfolioComponentRunRequest",
    "PortfolioConstructRequest",
    "PortfolioDriftRequest",
    "PortfolioEvidenceReferenceSet",
    "PortfolioFixedWeightInput",
    "PortfolioMeasurementRequest",
    "PortfolioRebalanceRequest",
    "PortfolioRollbackRequest",
    "PortfolioSimulationRunRequest",
    "PortfolioStrategyAllocationRef",
    "Readiness",
    "ResearchRunRequest",
    "RouteContract",
    "RouteSideEffect",
    "RouteStability",
    "SimulationBranchRequest",
    "SimulationRunRequest",
    "StrategyParameterUpdateRequestModel",
    "StrategyRegistrationRequestModel",
    "StreamEvent",
    "StreamEventType",
    "TradingMutationRequest",
)
