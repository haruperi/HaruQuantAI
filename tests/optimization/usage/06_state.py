"""Executable Optimization state usage example.

Demonstrates durable state store interface, search checkpointing, result persistence,
and artifact location generation.
"""

import sys
from pathlib import Path

# Add repository root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

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


def example_state() -> None:
    """Demonstrate optimization state persistence and checkpointing."""
    print("=" * 80)
    print("Optimization Example 6: Durable State and Checkpoints")
    print("=" * 80)

    # 1. Memory state store initialization
    store = MemoryOptimizationStore()
    print(
        f"Memory store satisfies OptimizationStateStore: {isinstance(store, OptimizationStateStore)}"
    )

    # 2. Checkpoint save and load
    ckpt = checkpoint()
    print(
        f"Original checkpoint completed candidate position: {ckpt.completed_candidate_position}"
    )
    save_search_checkpoint(ckpt, store)
    loaded_ckpt = load_search_checkpoint(
        search_id=ckpt.search_id,
        reproducibility_hash=ckpt.reproducibility_hash,
        store=store,
    )
    print(f"Loaded checkpoint search_id match: {loaded_ckpt == ckpt}")

    # 3. Persist optimization result
    ev_req = evidence_request()
    opt_evidence = build_optimization_evidence(ev_req)
    persist_res = persist_optimization_result(opt_evidence, store)
    print(f"Persisted optimization result durable flag: {persist_res.durable}")

    # 4. Artifact path construction
    artifact_path = build_optimization_artifact_path(
        artifact_root=Path("tmp/artifacts"),
        kind="checkpoints",
        search_id="search-one",
        reproducibility_hash="a" * 64,
    )
    print(f"Constructed artifact path extension: {artifact_path.suffix}")

    # 5. Migrations
    migrations = get_optimization_migrations()
    print(f"Optimization domain migrations count: {len(migrations)}")


def main() -> None:
    """Run Optimization state usage example."""
    example_state()


if __name__ == "__main__":
    main()
