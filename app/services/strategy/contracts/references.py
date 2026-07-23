"""Strategy reference and configuration contracts before and after validation."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Literal, cast

from pydantic import (
    field_serializer,
    field_validator,
    model_validator,
)

from app.services.strategy.contracts._base import (
    JsonValue,
    _contains_executable_marker,
    _Contract,
    _freeze_json,
    _hash,
    _text,
    _thaw_json,
)
from app.services.strategy.contracts.enums import (  # noqa: TC001
    StrategyEnvironment,
    StrategyLifecycleStatus,
)
from app.services.strategy.contracts.manifest import StrategyManifest  # noqa: TC001
from app.services.strategy.contracts.policy import (
    StrategyValidationPolicy,  # noqa: TC001
)
from app.utils import logger


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
