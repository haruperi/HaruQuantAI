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
from typing import Generic, Literal, Self, TypeVar, cast

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
        if self.auth_required and not self.permission:
            raise ValueError("authenticated routes require a permission")
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


__all__ = (
    "ApiError",
    "ApiErrorCode",
    "ApiMetadata",
    "ApiResponse",
    "ApiStatus",
    "GovernedRequestContext",
    "HealthDependencyCheck",
    "Liveness",
    "PageContext",
    "Readiness",
    "ResearchRunRequest",
    "RouteContract",
    "RouteSideEffect",
    "RouteStability",
    "StreamEvent",
    "StreamEventType",
)
