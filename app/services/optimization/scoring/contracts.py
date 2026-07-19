"""Typed objective and candidate-score evidence."""

from __future__ import annotations

import math
from collections.abc import Mapping
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, field_validator, model_validator

from app.utils import logger


class ObjectiveName(StrEnum):
    """Analytics-owned metric keys approved as Optimization objectives."""

    NET_PNL = "net_pnl"
    PROFIT_FACTOR = "profit_factor"
    SHARPE_RATIO = "sharpe_ratio"
    SORTINO_RATIO = "sortino_ratio"
    CALMAR_RATIO = "calmar_ratio"
    MAX_DRAWDOWN = "max_drawdown"


class ObjectiveDirection(StrEnum):
    """Explicit objective ranking direction."""

    MAXIMIZE = "maximize"
    MINIMIZE = "minimize"


OBJECTIVE_DIRECTIONS: Mapping[ObjectiveName, ObjectiveDirection] = {
    ObjectiveName.NET_PNL: ObjectiveDirection.MAXIMIZE,
    ObjectiveName.PROFIT_FACTOR: ObjectiveDirection.MAXIMIZE,
    ObjectiveName.SHARPE_RATIO: ObjectiveDirection.MAXIMIZE,
    ObjectiveName.SORTINO_RATIO: ObjectiveDirection.MAXIMIZE,
    ObjectiveName.CALMAR_RATIO: ObjectiveDirection.MAXIMIZE,
    ObjectiveName.MAX_DRAWDOWN: ObjectiveDirection.MINIMIZE,
}
_SHA256_HEX_LENGTH = 64


class CandidateScore(BaseModel):
    """One objective score projected from Analytics evidence."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    candidate_hash: str
    objective: ObjectiveName
    direction: ObjectiveDirection
    value: float | None
    available: bool
    trade_count: int | None
    metrics: Mapping[str, float | None]
    caveats: tuple[str, ...] = ()

    @field_validator("candidate_hash")
    @classmethod
    def _validate_hash(cls, value: str) -> str:
        """Validate candidate identity.

        Args:
            value: Candidate hash.

        Returns:
            Validated lowercase SHA-256 hash.

        Raises:
            ValueError: If the hash is malformed.
        """
        logger.debug("Validating Optimization candidate score hash")
        if len(value) != _SHA256_HEX_LENGTH or any(
            character not in "0123456789abcdef" for character in value
        ):
            raise ValueError("candidate_hash must be a lowercase SHA-256 digest")
        return value

    @field_validator("value")
    @classmethod
    def _validate_value(cls, value: float | None) -> float | None:
        """Reject non-finite objective values.

        Args:
            value: Optional objective value.

        Returns:
            Finite value or None.

        Raises:
            ValueError: If the value is non-finite.
        """
        logger.debug("Validating Optimization candidate score value")
        if value is not None and not math.isfinite(value):
            raise ValueError("candidate score must be finite")
        return value

    @model_validator(mode="after")
    def _validate_consistency(self) -> CandidateScore:
        """Validate availability and direction relationships.

        Returns:
            Validated candidate score.

        Raises:
            ValueError: If score evidence is contradictory.
        """
        logger.debug("Validating Optimization candidate score consistency")
        if self.available != (self.value is not None):
            raise ValueError("score availability must match value presence")
        if self.direction is not OBJECTIVE_DIRECTIONS[self.objective]:
            raise ValueError("objective direction does not match the catalog")
        if self.trade_count is not None and self.trade_count < 0:
            raise ValueError("trade_count cannot be negative")
        if any(
            value is not None and not math.isfinite(value)
            for value in self.metrics.values()
        ):
            raise ValueError("metric evidence must be finite")
        return self


__all__ = [
    "OBJECTIVE_DIRECTIONS",
    "CandidateScore",
    "ObjectiveDirection",
    "ObjectiveName",
]
