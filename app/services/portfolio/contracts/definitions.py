"""Immutable Portfolio definition contracts."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class PortfolioDefinition(BaseModel):
    """One immutable, versioned Portfolio definition.

    Attributes:
        portfolio_id: Stable Portfolio identity.
        portfolio_version: Immutable definition version.
        scope: Exact governed scope.
        definition: Bounded Portfolio configuration material.
        canonical_hash: Caller-provided canonical material digest.
        request_id: Request trace identity.
        workflow_id: Workflow trace identity.
        correlation_id: Correlation trace identity.
        created_at: UTC creation time.
    """

    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    contract_version: Literal["v1"] = "v1"
    schema_id: Literal["portfolio.definition.v1"] = "portfolio.definition.v1"
    portfolio_id: str = Field(min_length=1, max_length=200)
    portfolio_version: str = Field(min_length=1, max_length=100)
    scope: dict[str, str]
    definition: dict[str, Any]
    canonical_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    request_id: str = Field(min_length=1, max_length=200)
    workflow_id: str = Field(min_length=1, max_length=200)
    correlation_id: str = Field(min_length=1, max_length=200)
    created_at: datetime

    @field_validator("scope", "definition", mode="after")
    @classmethod
    def _require_mapping(cls, value: dict[str, Any]) -> dict[str, Any]:
        """Require one non-empty validated mapping.

        Args:
            value: Validated mapping.

        Returns:
            Validated mapping.

        Raises:
            ValueError: If the mapping is empty.
        """
        if not value:
            raise ValueError("Portfolio definition mappings must not be empty")
        return value

    @field_validator("created_at")
    @classmethod
    def _require_utc(cls, value: datetime) -> datetime:
        """Require an aware UTC creation time.

        Args:
            value: Candidate timestamp.

        Returns:
            Valid UTC timestamp.

        Raises:
            ValueError: If the timestamp is not UTC.
        """
        offset = value.utcoffset()
        if offset is None or offset.total_seconds() != 0:
            raise ValueError("Portfolio definition created_at must be UTC")
        return value


__all__ = ("PortfolioDefinition",)
