"""Receiver-owned governed Strategy mutation commands."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime
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
    _text,
    _thaw_json,
    _utc,
)
from app.services.strategy.contracts.enums import StrategyLifecycleStatus  # noqa: TC001
from app.services.strategy.contracts.manifest import StrategyManifest  # noqa: TC001
from app.services.strategy.contracts.references import (  # noqa: TC001
    StrategyConfig,
    StrategyRef,
)
from app.utils import logger


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
