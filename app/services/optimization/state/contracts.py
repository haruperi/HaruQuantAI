"""Immutable contracts and injected port for Optimization-owned state."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime
from typing import Protocol, runtime_checkable

from pydantic import BaseModel, ConfigDict, model_validator

from app.services.optimization.evidence import OptimizationResult  # noqa: TC001
from app.utils import canonical_json, logger

OPTIMIZATION_SCHEMA_VERSION = "v1"
_SHA256_HEX_LENGTH = 64


class OptimizationCheckpoint(BaseModel):
    """Immutable completed-candidate checkpoint evidence."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: str = OPTIMIZATION_SCHEMA_VERSION
    search_id: str
    reproducibility_hash: str
    completed_candidate_position: int
    rng_state: Mapping[str, object] | None = None
    evidence_references: tuple[str, ...] = ()
    created_at: datetime

    @model_validator(mode="after")
    def _validate_checkpoint(self) -> OptimizationCheckpoint:
        """Validate checkpoint version, identity, position, and UTC time.

        Returns:
            Validated Optimization checkpoint.

        Raises:
            ValueError: If checkpoint evidence is malformed or incompatible.
        """
        logger.debug("Validating Optimization checkpoint evidence")
        if self.schema_version != OPTIMIZATION_SCHEMA_VERSION:
            raise ValueError("checkpoint schema version is incompatible")
        if not self.search_id.startswith("search-"):
            raise ValueError("checkpoint search identity is invalid")
        if len(self.reproducibility_hash) != _SHA256_HEX_LENGTH:
            raise ValueError("checkpoint reproducibility hash is malformed")
        if self.completed_candidate_position < 0:
            raise ValueError("checkpoint candidate position cannot be negative")
        offset = self.created_at.utcoffset()
        if (
            self.created_at.tzinfo is None
            or offset is None
            or offset.total_seconds() != 0
        ):
            raise ValueError("checkpoint timestamp must be UTC")
        if any(not value.strip() for value in self.evidence_references):
            raise ValueError("checkpoint evidence references cannot be blank")
        try:
            canonical_json(self.model_dump(mode="json"), max_items=None)
        except (TypeError, ValueError) as exc:
            raise ValueError("checkpoint must be JSON-safe") from exc
        return self


class OptimizationPersistenceReceipt(BaseModel):
    """Confirmed atomic durable-write receipt."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: str = OPTIMIZATION_SCHEMA_VERSION
    search_id: str
    reproducibility_hash: str
    stored_at: datetime
    durable: bool

    @model_validator(mode="after")
    def _validate_receipt(self) -> OptimizationPersistenceReceipt:
        """Validate durable receipt identity and UTC confirmation.

        Returns:
            Validated persistence receipt.

        Raises:
            ValueError: If receipt cannot prove durable success.
        """
        logger.debug("Validating Optimization persistence receipt")
        offset = self.stored_at.utcoffset()
        if (
            self.schema_version != OPTIMIZATION_SCHEMA_VERSION
            or not self.search_id.startswith("search-")
            or len(self.reproducibility_hash) != _SHA256_HEX_LENGTH
            or self.stored_at.tzinfo is None
            or offset is None
            or offset.total_seconds() != 0
            or not self.durable
        ):
            raise ValueError("persistence receipt does not prove durable success")
        return self


@runtime_checkable
class OptimizationStateStore(Protocol):
    """Injected port limited to Optimization-owned atomic state operations."""

    def save_checkpoint(
        self, checkpoint: OptimizationCheckpoint
    ) -> OptimizationPersistenceReceipt:
        """Atomically save one checkpoint and return durable confirmation."""
        logger.debug(
            "Declaring Optimization checkpoint store operation for %s",
            checkpoint.search_id,
        )
        raise NotImplementedError

    def load_checkpoint(self, search_id: str) -> OptimizationCheckpoint | None:
        """Load the latest Optimization checkpoint for one search."""
        logger.debug("Declaring Optimization checkpoint load for %s", search_id)
        raise NotImplementedError

    def save_result(
        self,
        result: OptimizationResult,
        ranked_candidates: tuple[Mapping[str, object], ...],
    ) -> OptimizationPersistenceReceipt:
        """Atomically save a result and its ranked-candidate evidence."""
        logger.debug(
            "Declaring Optimization result store operation for %s with %s candidates",
            result.search_id,
            len(ranked_candidates),
        )
        raise NotImplementedError


__all__ = [
    "OPTIMIZATION_SCHEMA_VERSION",
    "OptimizationCheckpoint",
    "OptimizationPersistenceReceipt",
    "OptimizationStateStore",
]
