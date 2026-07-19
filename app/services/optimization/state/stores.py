"""Validated invocation of injected Optimization-owned state operations."""

from __future__ import annotations

from app.services.optimization.errors import OptimizationError
from app.services.optimization.state.contracts import (
    OPTIMIZATION_SCHEMA_VERSION,
    OptimizationCheckpoint,
    OptimizationPersistenceReceipt,
    OptimizationStateStore,
)
from app.utils import logger


def _validate_receipt(
    receipt: OptimizationPersistenceReceipt,
    *,
    search_id: str,
    reproducibility_hash: str,
) -> OptimizationPersistenceReceipt:
    """Validate exact receipt identity after an injected write.

    Args:
        receipt: Store-issued durable receipt.
        search_id: Expected search identity.
        reproducibility_hash: Expected evidence identity.

    Returns:
        Exact matching receipt.

    Raises:
        OptimizationError: If store confirmation is contradictory.
    """
    logger.debug("Validating Optimization store receipt identity")
    if (
        receipt.schema_version != OPTIMIZATION_SCHEMA_VERSION
        or receipt.search_id != search_id
        or receipt.reproducibility_hash != reproducibility_hash
        or not receipt.durable
    ):
        raise OptimizationError("OPT_STATE_CONFLICT", "RECEIPT_IDENTITY_MISMATCH")
    return receipt


def save_search_checkpoint(
    checkpoint: OptimizationCheckpoint,
    store: OptimizationStateStore,
) -> OptimizationPersistenceReceipt:
    """Atomically save one completed-candidate checkpoint.

    Args:
        checkpoint: Validated checkpoint evidence.
        store: Injected Optimization state port.

    Returns:
        Exact durable store receipt.

    Raises:
        OptimizationError: If the store fails or contradicts identity.
    """
    logger.info("Saving atomic Optimization search checkpoint")
    try:
        receipt = store.save_checkpoint(checkpoint)
    except Exception as exc:
        raise OptimizationError(
            "OPT_PERSISTENCE_FAILED", "CHECKPOINT_WRITE_FAILED"
        ) from exc
    return _validate_receipt(
        receipt,
        search_id=checkpoint.search_id,
        reproducibility_hash=checkpoint.reproducibility_hash,
    )


def load_search_checkpoint(
    *,
    search_id: str,
    reproducibility_hash: str,
    store: OptimizationStateStore,
) -> OptimizationCheckpoint | None:
    """Recover only an exact compatible Optimization checkpoint.

    Args:
        search_id: Expected canonical search identity.
        reproducibility_hash: Expected canonical evidence identity.
        store: Injected Optimization state port.

    Returns:
        Exact checkpoint or None when no checkpoint exists.

    Raises:
        OptimizationError: If loaded state is stale, conflicting, or unavailable.
    """
    logger.info("Loading exact Optimization search checkpoint")
    try:
        checkpoint = store.load_checkpoint(search_id)
    except Exception as exc:
        raise OptimizationError(
            "OPT_PERSISTENCE_FAILED", "CHECKPOINT_READ_FAILED"
        ) from exc
    if checkpoint is None:
        return None
    if (
        checkpoint.schema_version != OPTIMIZATION_SCHEMA_VERSION
        or checkpoint.search_id != search_id
        or checkpoint.reproducibility_hash != reproducibility_hash
    ):
        raise OptimizationError("OPT_STATE_CONFLICT", "CHECKPOINT_IDENTITY_MISMATCH")
    return checkpoint


__all__ = ["load_search_checkpoint", "save_search_checkpoint"]
