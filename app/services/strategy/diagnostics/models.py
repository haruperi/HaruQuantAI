"""Immutable bounded Strategy diagnostics contract."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime
from types import MappingProxyType
from typing import Literal

from pydantic import BaseModel, ConfigDict, field_serializer, field_validator

from app.services.strategy.contracts.models import JsonValue  # noqa: TC001
from app.utils import logger


class StrategyDiagnostics(BaseModel):
    """Versioned safe diagnostic evidence for one evaluation."""

    model_config = ConfigDict(frozen=True, extra="forbid")
    contract_version: Literal["v1"] = "v1"
    schema_id: Literal["strategy.diagnostics.v1"] = "strategy.diagnostics.v1"
    status: Literal["READY", "NEUTRAL", "PROPOSED", "FAILED"]
    strategy_id: str
    strategy_version: str
    config_hash: str | None
    data_checksum: str | None
    request_id: str
    workflow_id: str
    correlation_id: str
    decision_timestamp: datetime
    error_code: str | None
    safe_details: Mapping[str, JsonValue]
    dependency_health: Mapping[str, JsonValue]
    metrics: Mapping[str, JsonValue]
    redacted_paths: tuple[str, ...]
    truncated_paths: tuple[str, ...]
    payload_bytes: int

    @field_validator("safe_details", "dependency_health", "metrics", mode="after")
    @classmethod
    def _freeze_mappings(
        cls, value: Mapping[str, JsonValue]
    ) -> Mapping[str, JsonValue]:
        """Freeze diagnostic mappings.

        Args:
            value: Validated diagnostic mapping.

        Returns:
            An immutable shallow mapping whose nested values are already
            contract-validated JSON values.
        """
        logger.debug("Freezing Strategy diagnostic mapping")
        return MappingProxyType(dict(value))

    @field_serializer("safe_details", "dependency_health", "metrics", when_used="json")
    def _serialize_mappings(
        self, value: Mapping[str, JsonValue]
    ) -> dict[str, JsonValue]:
        """Serialize one immutable diagnostic mapping.

        Args:
            value: Immutable mapping.

        Returns:
            An ordinary JSON mapping.
        """
        logger.debug("Serializing Strategy diagnostic mapping")
        return dict(value)


__all__ = ["StrategyDiagnostics"]
