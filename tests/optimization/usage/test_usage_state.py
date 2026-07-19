"""Runnable usage evidence for Optimization durable state requirements."""

from pathlib import Path

from app.services.optimization.evidence import build_optimization_evidence
from app.services.optimization.state import (
    OptimizationStateStore,
    build_optimization_artifact_path,
    get_optimization_migrations,
    load_search_checkpoint,
    persist_optimization_result,
    save_search_checkpoint,
)
from tests.optimization.unit.test_evidence_contracts import evidence_request
from tests.optimization.unit.test_state_contracts import (
    MemoryOptimizationStore,
    checkpoint,
)


def test_usage_state_store() -> None:
    """Inject a store that satisfies the owned-state port."""
    assert isinstance(MemoryOptimizationStore(), OptimizationStateStore)


def test_usage_checkpoint_contract() -> None:
    """Construct immutable checkpoint evidence."""
    assert checkpoint().completed_candidate_position == 2


def test_usage_checkpoint_round_trip() -> None:
    """Save and recover an exact checkpoint identity."""
    store = MemoryOptimizationStore()
    value = checkpoint()
    save_search_checkpoint(value, store)
    assert (
        load_search_checkpoint(
            search_id=value.search_id,
            reproducibility_hash=value.reproducibility_hash,
            store=store,
        )
        == value
    )


def test_usage_persist_result() -> None:
    """Persist result and ranked evidence atomically."""
    result = build_optimization_evidence(evidence_request())
    assert persist_optimization_result(result, MemoryOptimizationStore()).durable


def test_usage_artifact_path(tmp_path: Path) -> None:
    """Build a deterministic artifact location without writing it."""
    assert (
        build_optimization_artifact_path(
            artifact_root=tmp_path,
            kind="checkpoints",
            search_id="search-one",
            reproducibility_hash="a" * 64,
        ).suffix
        == ".json"
    )


def test_usage_migrations() -> None:
    """Supply owned additive definitions to Data infrastructure."""
    assert get_optimization_migrations()[0].domain == "optimization"
