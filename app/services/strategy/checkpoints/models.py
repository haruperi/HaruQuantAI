"""Immutable bounded Strategy-local checkpoint contract."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime
from types import MappingProxyType
from typing import Literal

from pydantic import BaseModel, ConfigDict, field_serializer, field_validator

from app.services.strategy.contracts._base import JsonValue  # noqa: TC001
from app.utils import logger

_SHA256_LENGTH = 64


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


__all__ = ["StrategyCheckpoint"]
