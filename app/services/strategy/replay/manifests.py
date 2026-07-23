"""Deterministic Strategy replay-manifest construction."""

import hashlib

from app.services.strategy.contracts.execution import (
    StrategyExecutionContext,  # noqa: TC001
)
from app.services.strategy.contracts.outcomes import StrategyOutcome, failure, success
from app.services.strategy.contracts.references import (  # noqa: TC001
    ValidatedStrategyConfig,
    ValidatedStrategyRef,
)
from app.services.strategy.diagnostics.errors import StrategyErrorCode
from app.services.strategy.replay.models import StrategyReplayManifest
from app.utils import canonical_json, logger

_SHA256_LENGTH = 64


def create_strategy_replay_manifest(
    ref: ValidatedStrategyRef,
    config: ValidatedStrategyConfig,
    context: StrategyExecutionContext,
    data_checksum: str,
    indicator_manifest_hash: str,
    simulation_config_hash: str | None = None,
) -> StrategyOutcome[StrategyReplayManifest]:
    """Create an exact deterministic replay identity.

    Args:
        ref: Validated exact strategy reference.
        config: Validated normalized configuration.
        context: Fixed-clock evaluation context.
        data_checksum: Exact Data dataset checksum.
        indicator_manifest_hash: Canonical hash of ordered indicator manifests.
        simulation_config_hash: Optional Simulation-owned configuration hash.

    Returns:
        A deterministic replay manifest or hash/identity failure.
    """
    logger.info("Creating Strategy replay manifest")
    hashes: tuple[str, ...] = (data_checksum, indicator_manifest_hash)
    if simulation_config_hash is not None:
        hashes += (simulation_config_hash,)
    if any(not _valid_hash(value) for value in hashes):
        return failure(
            StrategyErrorCode.ARTIFACT_HASH_MISMATCH,
            "replay inputs contain an invalid hash",
            request_id=context.request_id,
            correlation_id=context.correlation_id,
        )
    if (
        config.strategy_id != ref.manifest.strategy_id
        or config.strategy_version != ref.manifest.strategy_version
        or context.interface_version != ref.manifest.interface_version
        or context.environment != ref.environment
        or context.timing_policy != ref.manifest.timing_policy
    ):
        return failure(
            StrategyErrorCode.DEPENDENCY_HASH_MISMATCH,
            "replay identity does not match the validated strategy",
            request_id=context.request_id,
            correlation_id=context.correlation_id,
        )
    material = {
        "strategy_id": ref.manifest.strategy_id,
        "strategy_version": ref.manifest.strategy_version,
        "interface_version": context.interface_version,
        "config_hash": config.config_hash,
        "data_checksum": data_checksum,
        "indicator_manifest_hash": indicator_manifest_hash,
        "simulation_config_hash": simulation_config_hash,
        "source_hash": ref.manifest.source_hash,
        "artifact_hash": ref.manifest.artifact_hash,
        "dependency_hash": ref.manifest.dependency_hash,
        "seed": context.seed,
        "timing_policy": context.timing_policy,
        "decision_timestamp": context.decision_timestamp,
        "request_id": context.request_id,
        "workflow_id": context.workflow_id,
        "correlation_id": context.correlation_id,
    }
    manifest_hash = hashlib.sha256(canonical_json(material).encode("utf-8")).hexdigest()
    return success(
        StrategyReplayManifest(
            strategy_id=ref.manifest.strategy_id,
            strategy_version=ref.manifest.strategy_version,
            interface_version=context.interface_version,
            config_hash=config.config_hash,
            data_checksum=data_checksum,
            indicator_manifest_hash=indicator_manifest_hash,
            simulation_config_hash=simulation_config_hash,
            source_hash=ref.manifest.source_hash,
            artifact_hash=ref.manifest.artifact_hash,
            dependency_hash=ref.manifest.dependency_hash,
            seed=context.seed,
            timing_policy=context.timing_policy,
            decision_timestamp=context.decision_timestamp,
            request_id=context.request_id,
            workflow_id=context.workflow_id,
            correlation_id=context.correlation_id,
            manifest_hash=manifest_hash,
        )
    )


def _valid_hash(value: str) -> bool:
    """Return whether text is a lowercase SHA-256 digest.

    Args:
        value: Candidate digest.

    Returns:
        Whether the digest is valid.
    """
    logger.debug("Checking Strategy replay input hash")
    return len(value) == _SHA256_LENGTH and all(
        character in "0123456789abcdef" for character in value
    )


__all__ = ["create_strategy_replay_manifest"]
