"""Immutable Strategy replay manifest and checkpoint contracts."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime
from types import MappingProxyType
from typing import Literal

from pydantic import BaseModel, ConfigDict, field_serializer, field_validator

from app.services.strategy.contracts.models import JsonValue  # noqa: TC001
from app.utils import logger

_SHA256_LENGTH = 64


class StrategyReplayManifest(BaseModel):
    """Exact hash-linked identity required to reproduce an evaluation."""

    model_config = ConfigDict(frozen=True, extra="forbid")
    contract_version: Literal["v1"] = "v1"
    schema_id: Literal["strategy.replay_manifest.v1"] = "strategy.replay_manifest.v1"
    strategy_id: str
    strategy_version: str
    interface_version: str
    config_hash: str
    data_checksum: str
    indicator_manifest_hash: str
    simulation_config_hash: str | None
    source_hash: str
    artifact_hash: str
    dependency_hash: str
    seed: int
    timing_policy: str
    decision_timestamp: datetime
    request_id: str
    workflow_id: str
    correlation_id: str
    manifest_hash: str

    @field_validator(
        "config_hash",
        "data_checksum",
        "indicator_manifest_hash",
        "source_hash",
        "artifact_hash",
        "dependency_hash",
        "manifest_hash",
    )
    @classmethod
    def _validate_hash(cls, value: str) -> str:
        """Validate one replay SHA-256 hash.

        Args:
            value: Hash to validate.

        Returns:
            Validated hash.

        Raises:
            ValueError: If the hash is malformed.
        """
        logger.debug("Validating Strategy replay hash")
        if len(value) != _SHA256_LENGTH or any(
            character not in "0123456789abcdef" for character in value
        ):
            raise ValueError("replay hashes must be lowercase SHA-256 digests")
        return value


class StrategyCheckpoint(BaseModel):
    """Bounded redacted Strategy-local recovery state."""

    model_config = ConfigDict(frozen=True, extra="forbid")
    contract_version: Literal["v1"] = "v1"
    schema_id: Literal["strategy.checkpoint.v1"] = "strategy.checkpoint.v1"
    checkpoint_id: str
    strategy_id: str
    strategy_version: str
    config_hash: str
    state_schema_version: Literal["v1"] = "v1"
    state: Mapping[str, JsonValue]
    state_checksum: str
    authorization_ref: str
    created_at: datetime
    request_id: str
    payload_bytes: int
    redacted_paths: tuple[str, ...]

    @field_validator("state", mode="after")
    @classmethod
    def _freeze_state(cls, value: Mapping[str, JsonValue]) -> Mapping[str, JsonValue]:
        """Freeze checkpoint state.

        Args:
            value: Validated local state.

        Returns:
            Immutable state mapping.
        """
        logger.debug("Freezing Strategy checkpoint state")
        return MappingProxyType(dict(value))

    @field_serializer("state", when_used="json")
    def _serialize_state(self, value: Mapping[str, JsonValue]) -> dict[str, JsonValue]:
        """Serialize checkpoint state.

        Args:
            value: Immutable state mapping.

        Returns:
            Ordinary JSON mapping.
        """
        logger.debug("Serializing Strategy checkpoint state")
        return dict(value)


__all__ = ["StrategyCheckpoint", "StrategyReplayManifest"]
