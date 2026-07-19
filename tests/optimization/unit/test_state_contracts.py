"""Tests for Optimization state contracts and port."""

# ruff: noqa: INP001

from collections.abc import Mapping
from datetime import UTC, datetime

from app.services.optimization.evidence import OptimizationResult
from app.services.optimization.state import (
    OptimizationCheckpoint,
    OptimizationPersistenceReceipt,
    OptimizationStateStore,
)


def checkpoint(**overrides: object) -> OptimizationCheckpoint:
    """Build a valid immutable checkpoint."""
    payload: dict[str, object] = {
        "search_id": "search-one",
        "reproducibility_hash": "a" * 64,
        "completed_candidate_position": 2,
        "rng_state": {"seed": 7},
        "evidence_references": ("candidate-2",),
        "created_at": datetime(2025, 1, 1, tzinfo=UTC),
    }
    payload.update(overrides)
    return OptimizationCheckpoint.model_validate(payload)


def receipt(
    *, search_id: str = "search-one", reproducibility_hash: str = "a" * 64
) -> OptimizationPersistenceReceipt:
    """Build a durable exact persistence receipt."""
    return OptimizationPersistenceReceipt(
        search_id=search_id,
        reproducibility_hash=reproducibility_hash,
        stored_at=datetime(2025, 1, 1, tzinfo=UTC),
        durable=True,
    )


class MemoryOptimizationStore:
    """Deterministic in-memory implementation of the injected test port."""

    def __init__(self) -> None:
        """Initialize empty Optimization-owned records."""
        self.checkpoints: dict[str, OptimizationCheckpoint] = {}
        self.results: dict[str, OptimizationResult] = {}

    def save_checkpoint(
        self, value: OptimizationCheckpoint
    ) -> OptimizationPersistenceReceipt:
        """Store one checkpoint atomically for tests."""
        self.checkpoints[value.search_id] = value
        return receipt(
            search_id=value.search_id,
            reproducibility_hash=value.reproducibility_hash,
        )

    def load_checkpoint(self, search_id: str) -> OptimizationCheckpoint | None:
        """Load one checkpoint for tests."""
        return self.checkpoints.get(search_id)

    def save_result(
        self,
        result: OptimizationResult,
        ranked_candidates: tuple[Mapping[str, object], ...],
    ) -> OptimizationPersistenceReceipt:
        """Store one result and paired ranked evidence for tests."""
        assert ranked_candidates == result.ranked_candidates
        self.results[result.search_id] = result
        return receipt(
            search_id=result.search_id,
            reproducibility_hash=result.reproducibility_hash,
        )


def test_store_port_exposes_only_owned_state() -> None:
    """The injected protocol has only three Optimization-owned operations."""
    methods = {
        name
        for name, value in OptimizationStateStore.__dict__.items()
        if callable(value) and not name.startswith("_")
    }
    assert methods == {"save_checkpoint", "load_checkpoint", "save_result"}


def test_checkpoint_requires_reproducibility_identity() -> None:
    """Checkpoint identity includes exact search and reproducibility values."""
    value = checkpoint()
    assert value.search_id == "search-one"
    assert value.reproducibility_hash == "a" * 64
