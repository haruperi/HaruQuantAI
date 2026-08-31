"""Strict common scalar aliases and reusable wire records."""

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator

Uuid7 = Annotated[
    str,
    StringConstraints(
        pattern=r"^[0-9a-f]{8}-[0-9a-f]{4}-7[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$"
    ),
]
UtcTimestamp = Annotated[
    str,
    StringConstraints(pattern=r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{6}Z$"),
]
DecimalValue = Annotated[
    str,
    StringConstraints(pattern=r"^-?(?:0|[1-9]\d*)(?:\.\d*[1-9])?$"),
]
CurrencyCode = Annotated[str, StringConstraints(pattern=r"^[A-Z]{3}$")]
ContentHash = Annotated[str, StringConstraints(pattern=r"^[0-9a-f]{64}$")]
CapabilityIdentifier = Annotated[
    str, StringConstraints(pattern=r"^[a-z][a-z0-9.-]*@[1-9]\d*$")
]
FeatureIdentifier = Annotated[str, StringConstraints(pattern=r"^FEAT-[A-Z0-9_-]+$")]

type JsonValue = (
    bool | int | float | str | list[JsonValue] | dict[str, JsonValue] | None
)
type JsonObject = dict[str, JsonValue]

# Closed core enum literals from Shared Contracts §4.3. Domain owners reference
# these instead of redeclaring equivalent literal unions.
type Direction = Literal["LONG", "SHORT", "BOTH"]
type Side = Literal["BUY", "SELL"]
type OrderType = Literal["MARKET", "STOP", "LIMIT", "STOP_LIMIT"]
type TimeInForce = Literal["GTC", "DAY", "IOC", "FOK"]
type Precision = Literal[
    "SELECTED_TIMEFRAME",
    "M1_SIMULATION",
    "REAL_TICK_CUSTOM_SPREAD",
    "REAL_TICK_RECORDED_SPREAD",
]
type Segment = Literal["FULL", "IS", "VALIDATION", "OOS", "NO_TRADE"]
type PlUnit = Literal["MONEY", "PERCENT", "PIPS"]
type Rounding = Literal["DOWN", "UP", "HALF_UP", "HALF_EVEN", "TOWARD_ZERO"]
type ResultState = Literal["STAGED", "VALIDATING", "COMMITTED", "REJECTED", "CORRUPT"]
type JobState = Literal[
    "QUEUED",
    "LEASED",
    "RUNNING",
    "PAUSING",
    "PAUSED",
    "RESUMING",
    "STOPPING",
    "STOPPED",
    "COMPLETED",
    "FAILED",
    "CANCELLED",
]
type FeatureState = Literal[
    "DISCOVERED",
    "DISABLED",
    "MISSING",
    "BLOCKED",
    "PREPARING",
    "ACTIVE",
    "QUIESCING",
    "STOPPING",
    "STOPPED",
    "FAILED_IMPORT",
    "FAILED_CONFIG",
    "FAILED_START",
    "FAILED_RUNTIME",
]
type OrderState = Literal[
    "CREATED",
    "ACCEPTED",
    "REJECTED",
    "PENDING",
    "PARTIALLY_FILLED",
    "FILLED",
    "CANCELLED",
    "EXPIRED",
]
type TradingModeValue = Literal["PAPER", "DEMO", "LIVE"]
type TradingSessionStateValue = Literal[
    "CREATED",
    "STARTING",
    "ACTIVE",
    "DEGRADED",
    "STOPPING",
    "STOPPED",
    "ARCHIVED",
]
type TradingOperationStateValue = Literal[
    "PLANNED",
    "ADMITTED",
    "DISPATCHING",
    "ACCEPTED",
    "REJECTED",
    "UNKNOWN",
    "RECONCILING",
    "PARTIALLY_FILLED",
    "FILLED",
    "CANCELLED",
    "CLOSED",
    "FAILED",
]
type RuntimeRiskDecision = Literal[
    "APPROVE",
    "WARN",
    "NEEDS_APPROVAL",
    "NEEDS_MORE_EVIDENCE",
    "REJECT",
    "BLOCK",
    "ERROR",
]


class WireModel(BaseModel):
    """Base configuration shared by public wire records."""

    model_config = ConfigDict(frozen=True, extra="forbid")


class Money(WireModel):
    """Currency-qualified canonical decimal amount."""

    amount: DecimalValue
    currency: CurrencyCode


class Timeframe(WireModel):
    """Positive multiple of a supported market-time unit."""

    unit: Literal["MINUTE", "DAY", "WEEK", "MONTH"]
    multiple: int = Field(ge=1)


class SeriesPointKey(WireModel):
    """Stable ordering key for one time-series observation."""

    timestamp: UtcTimestamp
    sequence: int = Field(ge=0)


class ValidationIssue(WireModel):
    """Machine-readable validation issue."""

    path: tuple[str, ...]
    code: Annotated[str, StringConstraints(pattern=r"^[A-Z][A-Z0-9_]*$")]
    message: Annotated[str, StringConstraints(min_length=1)]
    context: JsonObject = Field(default_factory=dict)


class ProblemDetails(WireModel):
    """Stable application failure envelope."""

    type: Annotated[str, StringConstraints(pattern=r"^(?:urn:|https?://).+")]
    title: Annotated[str, StringConstraints(min_length=1)]
    status: int = Field(ge=400, le=599)
    code: Annotated[str, StringConstraints(pattern=r"^[A-Z][A-Z0-9_]*$")]
    detail: Annotated[str, StringConstraints(min_length=1)]
    request_id: Uuid7
    errors: tuple[ValidationIssue, ...] = ()
    capability_key: CapabilityIdentifier | None = None
    required_version: int | None = Field(default=None, ge=1)
    feature_state: str | None = None
    affected_object_id: Uuid7 | None = None
    missing_dependencies: tuple[CapabilityIdentifier, ...] = ()
    available_alternatives: tuple[CapabilityIdentifier, ...] = ()
    schema_version: Literal[1] = 1


class CapabilityProviderSnapshot(WireModel):
    """Pinned provider identity and configuration evidence."""

    capability_key: CapabilityIdentifier
    provider_feature_id: FeatureIdentifier
    generation: int = Field(ge=1)
    implementation_hash: ContentHash
    configuration_hash: ContentHash


class CapabilitySnapshot(WireModel):
    """Immutable ordered provider snapshot."""

    snapshot_id: Uuid7
    created_at: UtcTimestamp
    providers: tuple[CapabilityProviderSnapshot, ...] = Field(min_length=1)
    snapshot_hash: ContentHash
    causal_request_id: Uuid7 | None = None
    schema_version: Literal[1] = 1

    @model_validator(mode="after")
    def validate_provider_order(self) -> CapabilitySnapshot:
        """Reject duplicate or non-canonical provider ordering.

        Returns:
            The validated snapshot.

        Raises:
            ValueError: Providers are duplicated or not canonically ordered.
        """
        keys = tuple(provider.capability_key for provider in self.providers)
        if keys != tuple(sorted(keys)) or len(keys) != len(set(keys)):
            raise ValueError("providers must be unique and sorted by capability key")
        return self


WIRE_MODELS: dict[str, type[WireModel]] = {
    "Money": Money,
    "Timeframe": Timeframe,
    "SeriesPointKey": SeriesPointKey,
    "ValidationIssue": ValidationIssue,
    "ProblemDetails": ProblemDetails,
    "CapabilityProviderSnapshot": CapabilityProviderSnapshot,
    "CapabilitySnapshot": CapabilitySnapshot,
}
