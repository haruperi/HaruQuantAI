"""Immutable deterministic Strategy replay-manifest contract."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, field_validator

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


__all__ = ["StrategyReplayManifest"]
