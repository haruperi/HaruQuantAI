"""Immutable public contracts for the Strategy domain."""

from __future__ import annotations

import math
from collections.abc import Mapping
from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from types import MappingProxyType
from typing import Literal, cast

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_serializer,
    field_validator,
    model_validator,
)

from app.services.data.contracts import MarketDataset  # noqa: TC001
from app.utils import logger

_MAX_TEXT_LENGTH = 512
_SHA256_LENGTH = 64

type JsonScalar = str | int | float | bool | None
type JsonValue = JsonScalar | tuple["JsonValue", ...] | Mapping[str, "JsonValue"]


def _utc(value: datetime) -> datetime:
    """Validate that a timestamp is timezone-aware UTC.

    Args:
        value: Timestamp to validate.

    Returns:
        The validated timestamp.

    Raises:
        ValueError: If the timestamp is naive or not UTC.
    """
    logger.debug("Validating a Strategy UTC timestamp")
    offset = value.utcoffset()
    if value.tzinfo is None or offset is None:
        raise ValueError("timestamp must be timezone-aware UTC")
    if offset.total_seconds() != 0:
        raise ValueError("timestamp must use UTC")
    return value


def _text(value: str) -> str:
    """Validate a required bounded text value.

    Args:
        value: Text to validate.

    Returns:
        Stripped text.

    Raises:
        ValueError: If the text is blank or oversized.
    """
    logger.debug("Validating Strategy text")
    cleaned = value.strip()
    if not cleaned or len(cleaned) > _MAX_TEXT_LENGTH:
        raise ValueError("text must contain 1..512 characters")
    return cleaned


def _hash(value: str) -> str:
    """Validate one lowercase SHA-256 digest.

    Args:
        value: Digest to validate.

    Returns:
        The validated digest.

    Raises:
        ValueError: If the digest is malformed.
    """
    logger.debug("Validating a Strategy SHA-256 digest")
    if len(value) != _SHA256_LENGTH or any(
        character not in "0123456789abcdef" for character in value
    ):
        raise ValueError("hash must be a lowercase 64-character SHA-256 digest")
    return value


def _finite_decimal(value: Decimal | None) -> Decimal | None:
    """Validate an optional finite decimal value.

    Args:
        value: Optional decimal value.

    Returns:
        The finite decimal or ``None``.

    Raises:
        ValueError: If the decimal is non-finite.
    """
    logger.debug("Validating a finite Strategy decimal")
    if value is not None and not value.is_finite():
        raise ValueError("decimal values must be finite")
    return value


def _freeze_json(value: object) -> JsonValue:
    """Recursively freeze JSON-compatible values.

    Args:
        value: Candidate JSON-compatible value.

    Returns:
        An immutable JSON-compatible value.

    Raises:
        ValueError: If an unsupported or non-finite value is supplied.
    """
    logger.debug("Freezing Strategy JSON material")
    if isinstance(value, Mapping):
        return MappingProxyType(
            {_text(str(key)): _freeze_json(item) for key, item in value.items()}
        )
    if isinstance(value, (list, tuple)):
        return tuple(_freeze_json(item) for item in value)
    if value is None or isinstance(value, (str, int, bool)):
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError("JSON numbers must be finite")
        return value
    raise ValueError("value must be JSON-compatible")


def _thaw_json(value: JsonValue) -> JsonScalar | list[object] | dict[str, object]:
    """Convert frozen JSON material to ordinary JSON containers.

    Args:
        value: Frozen value.

    Returns:
        JSON-serializable material.
    """
    logger.debug("Serializing Strategy JSON material")
    if isinstance(value, Mapping):
        return {str(key): _thaw_json(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_thaw_json(item) for item in value]
    return value


def _contains_executable_marker(value: JsonValue) -> bool:
    """Return whether JSON text contains an executable payload marker.

    Args:
        value: JSON-compatible value.

    Returns:
        Whether executable-looking content is present recursively.
    """
    logger.debug("Scanning Strategy JSON for executable markers")
    if isinstance(value, str):
        lowered = value.casefold()
        return any(
            marker in lowered
            for marker in ("import ", "exec(", "eval(", "__", "file://")
        )
    if isinstance(value, Mapping):
        return any(_contains_executable_marker(item) for item in value.values())
    if isinstance(value, tuple):
        return any(_contains_executable_marker(item) for item in value)
    return False


class _Contract(BaseModel):
    """Strict immutable base for Strategy contracts."""

    model_config = ConfigDict(frozen=True, extra="forbid", arbitrary_types_allowed=True)


class StrategyEnvironment(StrEnum):
    """Approved Strategy execution environments."""

    RESEARCH = "RESEARCH"
    SIMULATION = "SIMULATION"
    PAPER = "PAPER"
    LIVE = "LIVE"


class StrategyTimingPolicy(StrEnum):
    """Supported evidence timing policies."""

    BAR_OPEN_PREVIOUS_CLOSE = "BAR_OPEN_PREVIOUS_CLOSE"
    EVENT_DRIVEN = "EVENT_DRIVEN"


class StrategyLifecycleStatus(StrEnum):
    """Immutable version lifecycle states."""

    DRAFT = "DRAFT"
    APPROVED = "APPROVED"
    DEPRECATED = "DEPRECATED"
    REVOKED = "REVOKED"


class StrategyValidationPolicy(_Contract):
    """Explicit host-owned module and configuration validation policy."""

    contract_version: Literal["v1"] = "v1"
    schema_id: Literal["strategy.validation_policy.v1"] = (
        "strategy.validation_policy.v1"
    )
    policy_version: str
    approved_module_roots: tuple[str, ...]
    max_config_payload_bytes: int = Field(gt=0)
    max_config_nesting_depth: int = Field(gt=0)
    max_config_string_length: int = Field(gt=0)
    max_config_collection_items: int = Field(gt=0)

    @field_validator("policy_version")
    @classmethod
    def _validate_policy_version(cls, value: str) -> str:
        """Validate the policy version.

        Args:
            value: Version text.

        Returns:
            Validated text.
        """
        logger.debug("Validating Strategy policy version")
        return _text(value)

    @field_validator("approved_module_roots")
    @classmethod
    def _validate_roots(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        """Validate approved module roots.

        Args:
            value: Approved roots.

        Returns:
            Validated unique roots.

        Raises:
            ValueError: If roots are empty, duplicated, or malformed.
        """
        logger.debug("Validating approved Strategy module roots")
        roots = tuple(_text(root).rstrip(".") for root in value)
        if not roots or len(set(roots)) != len(roots):
            raise ValueError("approved_module_roots must be non-empty and unique")
        return roots


class StrategyManifest(_Contract):
    """Immutable identity, capability, and resource manifest."""

    contract_version: Literal["v1"] = "v1"
    schema_id: Literal["strategy.manifest.v1"] = "strategy.manifest.v1"
    strategy_id: str
    strategy_version: str
    module_path: str
    owner_ref: str
    interface_version: str
    config_schema_version: str
    config_schema: Mapping[str, JsonValue]
    required_data: tuple[str, ...]
    required_indicators: tuple[str, ...]
    timing_policy: StrategyTimingPolicy
    permitted_environments: tuple[StrategyEnvironment, ...]
    concurrency_model: Literal["SYNC_BLOCKING"] = "SYNC_BLOCKING"
    source_hash: str
    artifact_hash: str
    dependency_hash: str
    provenance_refs: tuple[str, ...]
    supported_hooks: tuple[str, ...]
    requires_account_snapshot: bool
    max_batch_records: int = Field(gt=0)
    max_diagnostic_bytes: int = Field(gt=0)
    max_checkpoint_bytes: int = Field(gt=0)
    max_local_state_bytes: int = Field(gt=0)
    decision_timeout_seconds: int = Field(gt=0)

    @field_validator(
        "strategy_id",
        "strategy_version",
        "module_path",
        "owner_ref",
        "interface_version",
        "config_schema_version",
    )
    @classmethod
    def _validate_text_fields(cls, value: str) -> str:
        """Validate required manifest text.

        Args:
            value: Text to validate.

        Returns:
            Validated text.
        """
        logger.debug("Validating Strategy manifest text")
        return _text(value)

    @field_validator("source_hash", "artifact_hash", "dependency_hash")
    @classmethod
    def _validate_hash_fields(cls, value: str) -> str:
        """Validate manifest hashes.

        Args:
            value: Hash to validate.

        Returns:
            Validated hash.
        """
        logger.debug("Validating Strategy manifest hash")
        return _hash(value)

    @field_validator("config_schema", mode="after")
    @classmethod
    def _freeze_schema(cls, value: Mapping[str, JsonValue]) -> Mapping[str, JsonValue]:
        """Validate manifest schema JSON.

        Args:
            value: Schema mapping.

        Returns:
            Validated mapping.

        Raises:
            ValueError: If executable-looking content is present.
        """
        logger.debug("Freezing Strategy manifest schema")
        return cast("Mapping[str, JsonValue]", _freeze_json(value))

    @model_validator(mode="after")
    def _validate_manifest(self) -> StrategyManifest:
        """Validate manifest uniqueness and capability declarations.

        Returns:
            The validated manifest.

        Raises:
            ValueError: If a required sequence is empty or duplicated.
        """
        logger.debug("Validating Strategy manifest relationships")
        if not self.permitted_environments:
            raise ValueError("permitted_environments must not be empty")
        module_parts = self.module_path.split(".")
        if not all(part.isidentifier() for part in module_parts):
            raise ValueError("module_path must be a dotted Python identifier")
        for values in (
            self.required_data,
            self.required_indicators,
            self.permitted_environments,
            self.provenance_refs,
            self.supported_hooks,
        ):
            if len(values) != len(set(values)):
                raise ValueError("manifest sequence values must be unique")
        if not self.provenance_refs:
            raise ValueError("provenance_refs must not be empty")
        return self

    @field_serializer("config_schema", when_used="json")
    def _serialize_schema(self, value: Mapping[str, JsonValue]) -> dict[str, object]:
        """Serialize frozen config schema.

        Args:
            value: Frozen schema.

        Returns:
            JSON-compatible schema.
        """
        logger.debug("Serializing Strategy manifest schema")
        return cast("dict[str, object]", _thaw_json(value))


class StrategyRef(_Contract):
    """Caller reference to one exact or constrained strategy version."""

    contract_version: Literal["v1"] = "v1"
    schema_id: Literal["strategy.ref.v1"] = "strategy.ref.v1"
    strategy_id: str
    exact_version: str | None = None
    version_constraint: str | None = None
    environment: StrategyEnvironment
    request_id: str
    correlation_id: str

    @field_validator("strategy_id", "request_id", "correlation_id")
    @classmethod
    def _validate_ref_text(cls, value: str) -> str:
        """Validate reference text.

        Args:
            value: Text to validate.

        Returns:
            Validated text.
        """
        logger.debug("Validating Strategy reference text")
        return _text(value)

    @model_validator(mode="after")
    def _validate_selector(self) -> StrategyRef:
        """Require exactly one version selector.

        Returns:
            The validated reference.

        Raises:
            ValueError: If selector cardinality is not one.
        """
        logger.debug("Validating Strategy version selector")
        if (self.exact_version is None) == (self.version_constraint is None):
            raise ValueError("exactly one version selector is required")
        return self


class StrategyConfig(_Contract):
    """Unvalidated caller-supplied strategy parameters."""

    contract_version: Literal["v1"] = "v1"
    schema_id: Literal["strategy.config.v1"] = "strategy.config.v1"
    strategy_id: str
    strategy_version: str
    config_schema_version: str
    parameters: Mapping[str, JsonValue]
    request_id: str

    @field_validator(
        "strategy_id", "strategy_version", "config_schema_version", "request_id"
    )
    @classmethod
    def _validate_config_text(cls, value: str) -> str:
        """Validate configuration identity text.

        Args:
            value: Text to validate.

        Returns:
            Validated text.
        """
        logger.debug("Validating Strategy configuration text")
        return _text(value)

    @field_validator("parameters", mode="after")
    @classmethod
    def _freeze_parameters(
        cls, value: Mapping[str, JsonValue]
    ) -> Mapping[str, JsonValue]:
        """Validate configuration JSON.

        Args:
            value: Parameter mapping.

        Returns:
            Validated mapping.

        Raises:
            ValueError: If executable-looking content is present.
        """
        logger.debug("Freezing Strategy configuration parameters")
        frozen = cast("Mapping[str, JsonValue]", _freeze_json(value))
        if _contains_executable_marker(frozen):
            raise ValueError("configuration cannot contain executable content")
        return frozen

    @field_serializer("parameters", when_used="json")
    def _serialize_parameters(
        self, value: Mapping[str, JsonValue]
    ) -> dict[str, object]:
        """Serialize configuration parameters.

        Args:
            value: Frozen parameters.

        Returns:
            JSON-compatible parameters.
        """
        logger.debug("Serializing Strategy configuration parameters")
        return cast("dict[str, object]", _thaw_json(value))


class ValidatedStrategyRef(_Contract):
    """Exactly resolved approved immutable strategy reference."""

    contract_version: Literal["v1"] = "v1"
    schema_id: Literal["strategy.validated_ref.v1"] = "strategy.validated_ref.v1"
    manifest: StrategyManifest
    lifecycle_status: StrategyLifecycleStatus
    environment: StrategyEnvironment
    policy_version: str
    validation_policy: StrategyValidationPolicy
    registry_record_hash: str
    request_id: str
    correlation_id: str

    @field_validator("policy_version", "request_id", "correlation_id")
    @classmethod
    def _validate_validated_ref_text(cls, value: str) -> str:
        """Validate resolved-reference text.

        Args:
            value: Text to validate.

        Returns:
            Validated text.
        """
        logger.debug("Validating resolved Strategy reference text")
        return _text(value)

    @field_validator("registry_record_hash")
    @classmethod
    def _validate_registry_hash(cls, value: str) -> str:
        """Validate the registry record hash.

        Args:
            value: Hash to validate.

        Returns:
            Validated hash.
        """
        logger.debug("Validating Strategy registry hash")
        return _hash(value)


class ValidatedStrategyConfig(_Contract):
    """Normalized schema-validated immutable strategy configuration."""

    contract_version: Literal["v1"] = "v1"
    schema_id: Literal["strategy.validated_config.v1"] = "strategy.validated_config.v1"
    strategy_id: str
    strategy_version: str
    config_schema_version: str
    normalized_parameters: Mapping[str, JsonValue]
    config_hash: str
    policy_version: str
    request_id: str

    @field_validator(
        "strategy_id",
        "strategy_version",
        "config_schema_version",
        "policy_version",
        "request_id",
    )
    @classmethod
    def _validate_validated_config_text(cls, value: str) -> str:
        """Validate normalized configuration identity.

        Args:
            value: Text to validate.

        Returns:
            Validated text.
        """
        logger.debug("Validating normalized Strategy configuration text")
        return _text(value)

    @field_validator("config_hash")
    @classmethod
    def _validate_config_hash(cls, value: str) -> str:
        """Validate the canonical configuration hash.

        Args:
            value: Hash to validate.

        Returns:
            Validated hash.
        """
        logger.debug("Validating Strategy configuration hash")
        return _hash(value)

    @field_validator("normalized_parameters", mode="after")
    @classmethod
    def _freeze_normalized(
        cls, value: Mapping[str, JsonValue]
    ) -> Mapping[str, JsonValue]:
        """Freeze normalized parameters.

        Args:
            value: Parameter mapping.

        Returns:
            Validated mapping.
        """
        logger.debug("Freezing normalized Strategy parameters")
        return cast("Mapping[str, JsonValue]", _freeze_json(value))

    @field_serializer("normalized_parameters", when_used="json")
    def _serialize_normalized(
        self, value: Mapping[str, JsonValue]
    ) -> dict[str, object]:
        """Serialize normalized parameters.

        Args:
            value: Frozen parameters.

        Returns:
            JSON-compatible parameters.
        """
        logger.debug("Serializing normalized Strategy parameters")
        return cast("dict[str, object]", _thaw_json(value))


class StrategyRegistrationRequest(_Contract):
    """Command to register one immutable strategy version."""

    contract_version: Literal["v1"] = "v1"
    schema_id: Literal["strategy.registration_request.v1"] = (
        "strategy.registration_request.v1"
    )
    command_id: str
    strategy_id: str
    strategy_version: str
    module_path: str
    manifest: StrategyManifest
    config_schema: Mapping[str, JsonValue]
    source_hash: str
    artifact_hash: str
    dependency_hash: str
    provenance_refs: tuple[str, ...]
    principal_id: str
    reason: str
    lifecycle_status: StrategyLifecycleStatus
    authorization_ref: str
    requested_at: datetime
    request_id: str
    correlation_id: str

    @field_validator(
        "command_id",
        "strategy_id",
        "strategy_version",
        "module_path",
        "principal_id",
        "reason",
        "authorization_ref",
        "request_id",
        "correlation_id",
    )
    @classmethod
    def _validate_registration_text(cls, value: str) -> str:
        """Validate registration command text.

        Args:
            value: Text to validate.

        Returns:
            Validated text.
        """
        logger.debug("Validating Strategy registration text")
        return _text(value)

    @field_validator("requested_at")
    @classmethod
    def _validate_registration_time(cls, value: datetime) -> datetime:
        """Validate registration time.

        Args:
            value: Timestamp to validate.

        Returns:
            Validated timestamp.
        """
        logger.debug("Validating Strategy registration time")
        return _utc(value)

    @model_validator(mode="after")
    def _validate_registration_identity(self) -> StrategyRegistrationRequest:
        """Require request identity to match its immutable manifest.

        Returns:
            The validated registration request.

        Raises:
            ValueError: If duplicated receiver fields disagree.
        """
        logger.debug("Validating Strategy registration identity")
        if (
            self.strategy_id != self.manifest.strategy_id
            or self.strategy_version != self.manifest.strategy_version
            or self.module_path != self.manifest.module_path
            or self.config_schema != self.manifest.config_schema
            or self.source_hash != self.manifest.source_hash
            or self.artifact_hash != self.manifest.artifact_hash
            or self.dependency_hash != self.manifest.dependency_hash
            or self.provenance_refs != self.manifest.provenance_refs
        ):
            raise ValueError("registration fields must match the manifest")
        return self


class StrategyParameterUpdateRequest(_Contract):
    """Command to register one immutable parameter version."""

    contract_version: Literal["v1"] = "v1"
    schema_id: Literal["strategy.parameter_update_request.v1"] = (
        "strategy.parameter_update_request.v1"
    )
    command_id: str
    strategy_id: str
    strategy_version: str
    parameters: Mapping[str, JsonValue]
    optimization_result_ref: str | None = None
    expected_config_hash: str | None = None
    principal_id: str
    reason: str
    ref: StrategyRef
    config: StrategyConfig
    authorization_ref: str
    requested_at: datetime
    request_id: str
    correlation_id: str

    @field_validator(
        "command_id",
        "strategy_id",
        "strategy_version",
        "principal_id",
        "reason",
        "authorization_ref",
        "request_id",
        "correlation_id",
    )
    @classmethod
    def _validate_update_text(cls, value: str) -> str:
        """Validate update command text.

        Args:
            value: Text to validate.

        Returns:
            Validated text.
        """
        logger.debug("Validating Strategy parameter update text")
        return _text(value)

    @field_validator("requested_at")
    @classmethod
    def _validate_update_time(cls, value: datetime) -> datetime:
        """Validate update time.

        Args:
            value: Timestamp to validate.

        Returns:
            Validated timestamp.
        """
        logger.debug("Validating Strategy parameter update time")
        return _utc(value)

    @field_validator("parameters", mode="after")
    @classmethod
    def _freeze_update_parameters(
        cls, value: Mapping[str, JsonValue]
    ) -> Mapping[str, JsonValue]:
        """Freeze declarative parameter-update values.

        Args:
            value: Proposed parameter mapping.

        Returns:
            Immutable validated mapping.

        Raises:
            ValueError: If executable-looking content is present.
        """
        logger.debug("Freezing Strategy parameter update values")
        frozen = cast("Mapping[str, JsonValue]", _freeze_json(value))
        if _contains_executable_marker(frozen):
            raise ValueError("parameter update cannot contain executable content")
        return frozen

    @field_serializer("parameters", when_used="json")
    def _serialize_update_parameters(
        self, value: Mapping[str, JsonValue]
    ) -> dict[str, object]:
        """Serialize immutable parameter-update values.

        Args:
            value: Immutable parameters.

        Returns:
            Ordinary JSON mapping.
        """
        logger.debug("Serializing Strategy parameter update values")
        return cast("dict[str, object]", _thaw_json(value))

    @model_validator(mode="after")
    def _validate_update_identity(self) -> StrategyParameterUpdateRequest:
        """Require an exact selector and matching receiver fields.

        Returns:
            The validated parameter-update request.

        Raises:
            ValueError: If identities disagree or selector is constrained.
        """
        logger.debug("Validating Strategy parameter update identity")
        if (
            self.ref.exact_version is None
            or self.strategy_id != self.ref.strategy_id
            or self.strategy_version != self.ref.exact_version
            or self.strategy_id != self.config.strategy_id
            or self.strategy_version != self.config.strategy_version
            or self.parameters != self.config.parameters
        ):
            raise ValueError("parameter update requires one matching exact version")
        return self


class StrategyExecutionContext(_Contract):
    """Immutable deterministic evaluation context."""

    contract_version: Literal["v1"] = "v1"
    schema_id: Literal["strategy.execution_context.v1"] = (
        "strategy.execution_context.v1"
    )
    environment: StrategyEnvironment
    decision_timestamp: datetime
    timing_policy: StrategyTimingPolicy
    seed: int
    interface_version: str
    request_id: str
    workflow_id: str
    correlation_id: str
    dependency_status: Mapping[str, JsonValue]
    snapshot_refs: tuple[str, ...]
    max_diagnostic_bytes: int = Field(gt=0)

    @field_validator("interface_version", "request_id", "workflow_id", "correlation_id")
    @classmethod
    def _validate_context_text(cls, value: str) -> str:
        """Validate context text.

        Args:
            value: Text to validate.

        Returns:
            Validated text.
        """
        logger.debug("Validating Strategy execution context text")
        return _text(value)

    @field_validator("decision_timestamp")
    @classmethod
    def _validate_context_time(cls, value: datetime) -> datetime:
        """Validate decision time.

        Args:
            value: Timestamp to validate.

        Returns:
            Validated timestamp.
        """
        logger.debug("Validating Strategy decision timestamp")
        return _utc(value)

    @field_validator("dependency_status", mode="after")
    @classmethod
    def _freeze_dependency_status(
        cls, value: Mapping[str, JsonValue]
    ) -> Mapping[str, JsonValue]:
        """Freeze dependency status evidence.

        Args:
            value: Dependency evidence.

        Returns:
            Validated evidence.
        """
        logger.debug("Freezing Strategy dependency status")
        return cast("Mapping[str, JsonValue]", _freeze_json(value))

    @field_serializer("dependency_status", when_used="json")
    def _serialize_dependency_status(
        self, value: Mapping[str, JsonValue]
    ) -> dict[str, object]:
        """Serialize immutable dependency evidence.

        Args:
            value: Immutable dependency evidence.

        Returns:
            Ordinary JSON mapping.
        """
        logger.debug("Serializing Strategy dependency status")
        thawed = _thaw_json(value)
        return cast("dict[str, object]", thawed)


class StrategyEvent(_Contract):
    """Receiver-owned immutable external event evidence."""

    contract_version: Literal["v1"] = "v1"
    schema_id: Literal["strategy.event.v1"] = "strategy.event.v1"
    event_type: str
    hook: str
    occurred_at: datetime
    sequence: int = Field(ge=0)
    source_owner: str
    source_contract_version: str
    source_schema_id: str
    source_snapshot_ref: str
    source_checksum: str
    source_as_of: datetime
    facts: Mapping[str, JsonValue]
    request_id: str
    workflow_id: str
    correlation_id: str

    @field_validator(
        "event_type",
        "hook",
        "source_owner",
        "source_contract_version",
        "source_schema_id",
        "source_snapshot_ref",
        "request_id",
        "workflow_id",
        "correlation_id",
    )
    @classmethod
    def _validate_event_text(cls, value: str) -> str:
        """Validate event evidence text.

        Args:
            value: Text to validate.

        Returns:
            Validated text.
        """
        logger.debug("Validating Strategy event text")
        return _text(value)

    @field_validator("source_checksum")
    @classmethod
    def _validate_event_checksum(cls, value: str) -> str:
        """Validate source checksum.

        Args:
            value: Hash to validate.

        Returns:
            Validated hash.
        """
        logger.debug("Validating Strategy event checksum")
        return _hash(value)

    @field_validator("occurred_at", "source_as_of")
    @classmethod
    def _validate_event_time(cls, value: datetime) -> datetime:
        """Validate event evidence time.

        Args:
            value: Timestamp to validate.

        Returns:
            Validated timestamp.
        """
        logger.debug("Validating Strategy event timestamp")
        return _utc(value)

    @field_validator("facts", mode="after")
    @classmethod
    def _freeze_event_facts(
        cls, value: Mapping[str, JsonValue]
    ) -> Mapping[str, JsonValue]:
        """Freeze bounded event facts.

        Args:
            value: Fact mapping.

        Returns:
            Validated facts.
        """
        logger.debug("Freezing Strategy event facts")
        return cast("Mapping[str, JsonValue]", _freeze_json(value))

    @field_serializer("facts", when_used="json")
    def _serialize_event_facts(
        self, value: Mapping[str, JsonValue]
    ) -> dict[str, object]:
        """Serialize immutable event facts.

        Args:
            value: Immutable event facts.

        Returns:
            Ordinary JSON mapping.
        """
        logger.debug("Serializing Strategy event facts")
        return cast("dict[str, object]", _thaw_json(value))


def _validate_strategy_order_shape(
    order_type: Literal["MARKET", "LIMIT", "STOP", "STOP_LIMIT"] | None,
    limit_price: Decimal | None,
    stop_price: Decimal | None,
) -> None:
    """Validate explicit Strategy execution-instruction shape.

    Args:
        order_type: Optional proposal order type.
        limit_price: Optional limit entry price.
        stop_price: Optional stop entry price.

    Raises:
        ValueError: If prices are invalid or conflict with the order type.
    """
    logger.debug("Validating Strategy decision order shape")
    required_prices = {
        "MARKET": (False, False),
        "LIMIT": (True, False),
        "STOP": (False, True),
        "STOP_LIMIT": (True, True),
    }
    if order_type is not None:
        limit_required, stop_required = required_prices[order_type]
        if (limit_price is not None) != limit_required:
            raise ValueError("limit_price conflicts with order_type")
        if (stop_price is not None) != stop_required:
            raise ValueError("stop_price conflicts with order_type")
    for price in (limit_price, stop_price):
        if price is not None and (not price.is_finite() or price <= 0):
            raise ValueError("entry prices must be finite and positive")


class StrategyDecision(_Contract):
    """Neutral or actionable evaluator decision."""

    contract_version: Literal["v1"] = "v1"
    schema_id: Literal["strategy.decision.v1"] = "strategy.decision.v1"
    decision_id: str
    sequence: int = Field(ge=0)
    action: Literal["NEUTRAL", "PROPOSE"]
    symbol: str | None = None
    side: Literal["BUY", "SELL"] | None = None
    intent_type: (
        Literal["OPEN", "CLOSE", "REDUCE", "INCREASE", "MODIFY", "CANCEL"] | None
    ) = None
    order_type: Literal["MARKET", "LIMIT", "STOP", "STOP_LIMIT"] | None = None
    limit_price: Decimal | None = None
    stop_price: Decimal | None = None
    time_in_force: Literal["GTC", "IOC", "FOK", "GTD", "DAY"] | None = None
    requested_sizing_mode: str | None = None
    quantity_hint: Decimal | None = None
    notional_hint: Decimal | None = None
    valid_from: datetime
    expires_at: datetime
    parent_intent_id: str | None = None
    stop_loss: Decimal | None = None
    take_profit: Decimal | None = None
    allow_partial_fills: bool
    min_fill_size: Decimal | None = None
    rationale_ref: str | None = None
    lineage: Mapping[str, str]
    rationale_refs: tuple[str, ...]
    diagnostic_facts: Mapping[str, JsonValue]
    candidate_local_state: Mapping[str, JsonValue] | None = None

    @field_validator("diagnostic_facts", "candidate_local_state", mode="after")
    @classmethod
    def _freeze_decision_json(
        cls, value: Mapping[str, JsonValue] | None
    ) -> Mapping[str, JsonValue] | None:
        """Freeze decision-owned JSON mappings.

        Args:
            value: Optional JSON mapping.

        Returns:
            Optional immutable mapping.
        """
        logger.debug("Freezing Strategy decision JSON material")
        if value is None:
            return None
        return cast("Mapping[str, JsonValue]", _freeze_json(value))

    @field_validator("lineage", mode="after")
    @classmethod
    def _freeze_decision_lineage(cls, value: Mapping[str, str]) -> Mapping[str, str]:
        """Freeze decision lineage.

        Args:
            value: Decision lineage.

        Returns:
            Immutable lineage mapping.
        """
        logger.debug("Freezing Strategy decision lineage")
        return MappingProxyType(dict(value))

    @field_validator("decision_id")
    @classmethod
    def _validate_decision_id(cls, value: str) -> str:
        """Validate decision identity.

        Args:
            value: Identity text.

        Returns:
            Validated text.
        """
        logger.debug("Validating Strategy decision identity")
        return _text(value)

    @field_validator("valid_from", "expires_at")
    @classmethod
    def _validate_decision_time(cls, value: datetime) -> datetime:
        """Validate decision time.

        Args:
            value: Timestamp to validate.

        Returns:
            Validated timestamp.
        """
        logger.debug("Validating Strategy decision timestamp")
        return _utc(value)

    @model_validator(mode="after")
    def _validate_decision(self) -> StrategyDecision:
        """Validate neutral and proposal invariants.

        Returns:
            The validated decision.

        Raises:
            ValueError: If decision fields conflict.
        """
        logger.debug("Validating Strategy decision relationships")
        if self.expires_at <= self.valid_from:
            raise ValueError("expires_at must follow valid_from")
        action_fields = (
            self.symbol,
            self.side,
            self.intent_type,
            self.order_type,
            self.limit_price,
            self.stop_price,
            self.time_in_force,
            self.quantity_hint,
            self.notional_hint,
        )
        if self.action == "NEUTRAL" and any(item is not None for item in action_fields):
            raise ValueError("neutral decisions cannot contain proposal fields")
        if self.action == "PROPOSE" and (
            self.symbol is None
            or self.side is None
            or self.intent_type is None
            or self.order_type is None
        ):
            raise ValueError(
                "proposal decisions require symbol, side, intent type, and order type"
            )
        _validate_strategy_order_shape(
            self.order_type,
            self.limit_price,
            self.stop_price,
        )
        if self.quantity_hint is not None and self.quantity_hint <= 0:
            raise ValueError("quantity_hint must be positive")
        if self.notional_hint is not None and self.notional_hint <= 0:
            raise ValueError("notional_hint must be positive")
        if self.min_fill_size is not None and (
            not self.allow_partial_fills or self.min_fill_size <= 0
        ):
            raise ValueError("min_fill_size requires allowed partial fills")
        return self

    @field_serializer("diagnostic_facts", "candidate_local_state", when_used="json")
    def _serialize_decision_json(
        self, value: Mapping[str, JsonValue] | None
    ) -> dict[str, object] | None:
        """Serialize immutable decision JSON mappings.

        Args:
            value: Optional immutable mapping.

        Returns:
            Optional ordinary JSON mapping.
        """
        logger.debug("Serializing Strategy decision JSON material")
        if value is None:
            return None
        return cast("dict[str, object]", _thaw_json(value))

    @field_serializer("lineage", when_used="json")
    def _serialize_decision_lineage(self, value: Mapping[str, str]) -> dict[str, str]:
        """Serialize immutable decision lineage.

        Args:
            value: Immutable lineage.

        Returns:
            Ordinary JSON mapping.
        """
        logger.debug("Serializing Strategy decision lineage")
        return dict(value)


class StrategySignal(_Contract):
    """Immutable deterministic output from one concrete signal evaluator."""

    contract_version: Literal["v1"] = "v1"
    schema_id: Literal["strategy.signal.v1"] = "strategy.signal.v1"
    signal_id: str
    strategy_id: str
    strategy_version: str
    symbol: str
    timestamp: datetime
    signal_name: str
    side: Literal["BUY", "SELL"] | None
    active: bool
    lineage: Mapping[str, str]
    facts: Mapping[str, JsonValue]

    @field_validator("signal_id")
    @classmethod
    def _validate_signal_id(cls, value: str) -> str:
        """Validate deterministic signal identity.

        Args:
            value: Signal SHA-256 identity.

        Returns:
            Validated lowercase digest.
        """
        logger.debug("Validating concrete Strategy signal identity")
        return _hash(value)

    @field_validator("strategy_id", "strategy_version", "symbol", "signal_name")
    @classmethod
    def _validate_signal_text(cls, value: str) -> str:
        """Validate required signal text.

        Args:
            value: Text to validate.

        Returns:
            Validated bounded text.
        """
        logger.debug("Validating concrete Strategy signal text")
        return _text(value)

    @field_validator("timestamp")
    @classmethod
    def _validate_signal_time(cls, value: datetime) -> datetime:
        """Validate the point-in-time signal timestamp.

        Args:
            value: Signal timestamp.

        Returns:
            Validated aware UTC timestamp.
        """
        logger.debug("Validating concrete Strategy signal timestamp")
        return _utc(value)

    @field_validator("lineage", mode="after")
    @classmethod
    def _freeze_signal_lineage(cls, value: Mapping[str, str]) -> Mapping[str, str]:
        """Freeze signal lineage references.

        Args:
            value: Lineage mapping.

        Returns:
            Immutable validated lineage.
        """
        logger.debug("Freezing concrete Strategy signal lineage")
        return MappingProxyType(
            {_text(key): _text(item) for key, item in value.items()}
        )

    @field_validator("facts", mode="after")
    @classmethod
    def _freeze_signal_facts(
        cls, value: Mapping[str, JsonValue]
    ) -> Mapping[str, JsonValue]:
        """Freeze JSON-compatible signal facts.

        Args:
            value: Signal fact mapping.

        Returns:
            Immutable signal facts.
        """
        logger.debug("Freezing concrete Strategy signal facts")
        return cast("Mapping[str, JsonValue]", _freeze_json(value))

    @field_serializer("lineage", when_used="json")
    def _serialize_signal_lineage(self, value: Mapping[str, str]) -> dict[str, str]:
        """Serialize immutable signal lineage.

        Args:
            value: Immutable lineage mapping.

        Returns:
            Ordinary lineage mapping.
        """
        logger.debug("Serializing concrete Strategy signal lineage")
        return dict(value)

    @field_serializer("facts", when_used="json")
    def _serialize_signal_facts(
        self, value: Mapping[str, JsonValue]
    ) -> dict[str, object]:
        """Serialize immutable signal facts.

        Args:
            value: Immutable signal fact mapping.

        Returns:
            JSON-compatible fact mapping.
        """
        logger.debug("Serializing concrete Strategy signal facts")
        return cast("dict[str, object]", _thaw_json(value))


class StrategySignalEvidence(_Contract):
    """Immutable point-in-time evidence for concrete signal evaluation."""

    contract_version: Literal["v1"] = "v1"
    schema_id: Literal["strategy.signal_evidence.v1"] = "strategy.signal_evidence.v1"
    evidence_id: str
    primary_market: MarketDataset
    related_markets: Mapping[str, MarketDataset]
    point_size: Decimal
    feature_values: Mapping[str, tuple[Decimal, ...]]
    feature_available_at: Mapping[str, datetime]
    feature_refs: Mapping[str, str]
    active_position_tags: tuple[str, ...]

    @field_validator("evidence_id")
    @classmethod
    def _validate_evidence_id(cls, value: str) -> str:
        """Validate signal evidence identity.

        Args:
            value: Evidence identifier.

        Returns:
            Validated bounded identifier.
        """
        logger.debug("Validating concrete Strategy signal evidence identity")
        return _text(value)

    @field_validator("point_size")
    @classmethod
    def _validate_point_size(cls, value: Decimal) -> Decimal:
        """Validate explicit positive point-size evidence.

        Args:
            value: Market point size.

        Returns:
            Validated positive finite point size.

        Raises:
            ValueError: If the point size is non-finite or non-positive.
        """
        logger.debug("Validating concrete Strategy point-size evidence")
        validated = _finite_decimal(value)
        if validated is None or validated <= 0:
            raise ValueError("point_size must be positive")
        return validated

    @field_validator("related_markets", mode="after")
    @classmethod
    def _freeze_related_markets(
        cls, value: Mapping[str, MarketDataset]
    ) -> Mapping[str, MarketDataset]:
        """Freeze named related market datasets.

        Args:
            value: Named point-in-time market datasets.

        Returns:
            Immutable related market mapping.
        """
        logger.debug("Freezing related concrete Strategy market evidence")
        return MappingProxyType({_text(key): item for key, item in value.items()})

    @field_validator("feature_values", mode="after")
    @classmethod
    def _freeze_feature_values(
        cls, value: Mapping[str, tuple[Decimal, ...]]
    ) -> Mapping[str, tuple[Decimal, ...]]:
        """Validate and freeze named feature values.

        Args:
            value: Named decimal feature sequences.

        Returns:
            Immutable validated feature values.

        Raises:
            ValueError: If a feature value is non-finite.
        """
        logger.debug("Freezing concrete Strategy feature values")
        frozen: dict[str, tuple[Decimal, ...]] = {}
        for key, items in value.items():
            validated_items: list[Decimal] = []
            for item in items:
                validated = _finite_decimal(item)
                if validated is None:
                    raise ValueError("feature values must be finite")
                validated_items.append(validated)
            frozen[_text(key)] = tuple(validated_items)
        return MappingProxyType(frozen)

    @field_validator("feature_available_at", mode="after")
    @classmethod
    def _freeze_feature_times(
        cls, value: Mapping[str, datetime]
    ) -> Mapping[str, datetime]:
        """Validate and freeze feature availability timestamps.

        Args:
            value: Named feature availability timestamps.

        Returns:
            Immutable UTC timestamp mapping.
        """
        logger.debug("Freezing concrete Strategy feature availability")
        return MappingProxyType({_text(key): _utc(item) for key, item in value.items()})

    @field_validator("feature_refs", mode="after")
    @classmethod
    def _freeze_feature_refs(cls, value: Mapping[str, str]) -> Mapping[str, str]:
        """Validate and freeze feature provenance references.

        Args:
            value: Named feature provenance references.

        Returns:
            Immutable validated reference mapping.
        """
        logger.debug("Freezing concrete Strategy feature references")
        return MappingProxyType(
            {_text(key): _text(item) for key, item in value.items()}
        )

    @field_validator("active_position_tags")
    @classmethod
    def _validate_position_tags(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        """Validate immutable active position ownership tags.

        Args:
            value: Position tags supplied by the runtime owner.

        Returns:
            Validated unique tags.

        Raises:
            ValueError: If position tags are duplicated.
        """
        logger.debug("Validating concrete Strategy active position tags")
        validated = tuple(_text(item) for item in value)
        if len(set(validated)) != len(validated):
            raise ValueError("active_position_tags must be unique")
        return validated

    @model_validator(mode="after")
    def _validate_feature_completeness(self) -> StrategySignalEvidence:
        """Require values, availability, and provenance for every feature.

        Returns:
            Validated complete signal evidence.

        Raises:
            ValueError: If feature evidence keys disagree.
        """
        logger.debug("Validating concrete Strategy feature completeness")
        keys = set(self.feature_values)
        if keys != set(self.feature_available_at) or keys != set(self.feature_refs):
            raise ValueError("feature evidence values, times, and refs must align")
        return self

    @field_serializer("related_markets", when_used="json")
    def _serialize_related_markets(
        self, value: Mapping[str, MarketDataset]
    ) -> dict[str, MarketDataset]:
        """Serialize named related markets.

        Args:
            value: Immutable related markets.

        Returns:
            Ordinary related-market mapping.
        """
        logger.debug("Serializing related concrete Strategy market evidence")
        return dict(value)

    @field_serializer("feature_values", when_used="json")
    def _serialize_feature_values(
        self, value: Mapping[str, tuple[Decimal, ...]]
    ) -> dict[str, tuple[Decimal, ...]]:
        """Serialize named feature values.

        Args:
            value: Immutable feature values.

        Returns:
            Ordinary feature-value mapping.
        """
        logger.debug("Serializing concrete Strategy feature values")
        return dict(value)

    @field_serializer("feature_available_at", when_used="json")
    def _serialize_feature_times(
        self, value: Mapping[str, datetime]
    ) -> dict[str, datetime]:
        """Serialize feature availability timestamps.

        Args:
            value: Immutable feature timestamps.

        Returns:
            Ordinary feature timestamp mapping.
        """
        logger.debug("Serializing concrete Strategy feature availability")
        return dict(value)

    @field_serializer("feature_refs", when_used="json")
    def _serialize_feature_refs(self, value: Mapping[str, str]) -> dict[str, str]:
        """Serialize feature provenance references.

        Args:
            value: Immutable feature references.

        Returns:
            Ordinary feature reference mapping.
        """
        logger.debug("Serializing concrete Strategy feature references")
        return dict(value)


class StrategyExecutionResult(_Contract):
    """Atomic ordered evaluation output."""

    contract_version: Literal["v1"] = "v1"
    schema_id: Literal["strategy.execution_result.v1"] = "strategy.execution_result.v1"
    decisions: tuple[StrategyDecision, ...]
    intents: tuple[object, ...]
    diagnostics: object
    replay_manifest: object
    local_state_update: Mapping[str, JsonValue] | None = None
    result_hash: str

    @field_validator("result_hash")
    @classmethod
    def _validate_result_hash(cls, value: str) -> str:
        """Validate the result hash.

        Args:
            value: Hash to validate.

        Returns:
            Validated hash.
        """
        logger.debug("Validating Strategy execution result hash")
        return _hash(value)

    @model_validator(mode="after")
    def _validate_atomic_result(self) -> StrategyExecutionResult:
        """Validate deterministic ordering and atomicity.

        Returns:
            The validated result.

        Raises:
            ValueError: If decision ordering or batch correspondence is invalid.
        """
        logger.debug("Validating atomic Strategy execution result")
        sequences = tuple(decision.sequence for decision in self.decisions)
        if sequences != tuple(sorted(sequences)) or len(set(sequences)) != len(
            sequences
        ):
            raise ValueError("decisions must have unique ascending sequence numbers")
        proposal_count = sum(
            decision.action == "PROPOSE" for decision in self.decisions
        )
        if proposal_count != len(self.intents):
            raise ValueError("every proposal must produce exactly one intent")
        return self

    @field_serializer("local_state_update", when_used="json")
    def _serialize_local_state_update(
        self, value: Mapping[str, JsonValue] | None
    ) -> dict[str, object] | None:
        """Serialize optional immutable result local state.

        Args:
            value: Optional local state.

        Returns:
            Optional ordinary JSON mapping.
        """
        logger.debug("Serializing Strategy result local state")
        if value is None:
            return None
        return cast("dict[str, object]", _thaw_json(value))


__all__ = [
    "JsonValue",
    "StrategyConfig",
    "StrategyDecision",
    "StrategyEnvironment",
    "StrategyEvent",
    "StrategyExecutionContext",
    "StrategyExecutionResult",
    "StrategyLifecycleStatus",
    "StrategyManifest",
    "StrategyParameterUpdateRequest",
    "StrategyRef",
    "StrategyRegistrationRequest",
    "StrategySignal",
    "StrategySignalEvidence",
    "StrategyTimingPolicy",
    "StrategyValidationPolicy",
    "ValidatedStrategyConfig",
    "ValidatedStrategyRef",
]
