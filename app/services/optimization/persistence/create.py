"""Relational store construction and Optimization result creation."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any, cast

from app.services.data import (
    build_statement_plan,
    build_transaction_request,
    execute_transaction,
)
from app.services.optimization.contracts import OptimizationError
from app.services.optimization.persistence.read import read_checkpoint, read_result
from app.services.optimization.persistence.update import upsert_checkpoint
from app.services.optimization.state.contracts import (
    OptimizationCheckpoint,
    OptimizationPersistenceReceipt,
)
from app.utils import canonical_json, generate_id, get_logger

logger = get_logger(__name__)

if TYPE_CHECKING:
    from app.services.optimization.evidence import OptimizationResult


class _RelationalOptimizationStore:
    """Internal Data-backed implementation of the Optimization state port."""

    def __init__(self, request_id: str, correlation_id: str) -> None:
        self._request_id = request_id
        self._correlation_id = correlation_id

    def save_checkpoint(
        self, checkpoint: OptimizationCheckpoint
    ) -> OptimizationPersistenceReceipt:
        """Atomically save one checkpoint and return durable confirmation.

        Returns:
            Exact durable persistence receipt.
        """
        upsert_checkpoint(
            checkpoint,
            request_id=self._request_id,
            correlation_id=self._correlation_id,
        )
        return OptimizationPersistenceReceipt(
            search_id=checkpoint.search_id,
            reproducibility_hash=checkpoint.reproducibility_hash,
            stored_at=datetime.now(UTC),
            durable=True,
        )

    def load_checkpoint(self, search_id: str) -> OptimizationCheckpoint | None:
        """Load one checkpoint through the bounded relational read.

        Returns:
            Persisted checkpoint or ``None``.
        """
        return read_checkpoint(search_id, self._request_id)

    def save_result(
        self,
        result: OptimizationResult,
        ranked_candidates: tuple[Mapping[str, object], ...],
    ) -> OptimizationPersistenceReceipt:
        """Atomically insert one immutable Optimization result.

        Returns:
            Exact durable persistence receipt.

        Raises:
            OptimizationError: If Data rejects or conflicts with the insert.
        """
        logger.info("Creating Optimization result relationally")
        stored_at = datetime.now(UTC)
        statement = """INSERT INTO optimization_results (
            search_id, schema_version, reproducibility_hash, result_json,
            ranked_candidates_json, stored_at, request_id, correlation_id, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)"""
        parameters = (
            result.search_id,
            result.contract_version,
            result.reproducibility_hash,
            canonical_json(result.model_dump(mode="json"), max_items=None),
            canonical_json(ranked_candidates, max_items=None),
            stored_at.isoformat(),
            self._request_id,
            self._correlation_id,
            stored_at.isoformat(),
        )
        response = execute_transaction(
            build_transaction_request(
                plan=build_statement_plan(
                    statements=(statement,),
                    parameter_sets=(cast("tuple[Any, ...]", parameters),),
                    max_rows=1,
                ),
                request_id=self._request_id,
            )
        )
        if response.status != "success" or response.data is None:
            raise OptimizationError("OPT_PERSISTENCE_FAILED", "RESULT_WRITE_FAILED")
        if cast("Any", response.data).affected_rows != 1:
            raise OptimizationError("OPT_STATE_CONFLICT", "RESULT_ALREADY_EXISTS")
        return OptimizationPersistenceReceipt(
            search_id=result.search_id,
            reproducibility_hash=result.reproducibility_hash,
            stored_at=stored_at,
            durable=True,
        )

    def load_result(self, search_id: str) -> OptimizationResult | None:
        """Load one result through the bounded relational read.

        Returns:
            Persisted result or ``None``.
        """
        return read_result(search_id, self._request_id)


def create_optimization_state_store(
    *, request_id: str | None = None, correlation_id: str | None = None
) -> object:
    """Create an opaque Data-backed Optimization state store.

    Args:
        request_id: Optional caller trace identifier.
        correlation_id: Optional cross-operation trace identifier.

    Returns:
        Opaque store satisfying the internal Optimization state protocol.
    """
    logger.info("Creating Data-backed Optimization state store")
    return _RelationalOptimizationStore(
        request_id or generate_id("req"),
        correlation_id or generate_id("cor"),
    )


__all__ = ["create_optimization_state_store"]
