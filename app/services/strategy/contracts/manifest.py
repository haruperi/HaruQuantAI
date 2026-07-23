"""Immutable Strategy identity, capability, and resource manifest."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Literal, cast

from pydantic import (
    Field,
    field_serializer,
    field_validator,
    model_validator,
)

from app.services.strategy.contracts._base import (
    JsonValue,
    _Contract,
    _freeze_json,
    _hash,
    _text,
    _thaw_json,
)
from app.services.strategy.contracts.enums import (  # noqa: TC001
    StrategyEnvironment,
    StrategyTimingPolicy,
)
from app.utils import logger


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
