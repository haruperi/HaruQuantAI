"""Executable Optimization state usage example.

Demonstrates FEAT-OPT-06 durable state store interface, search checkpointing, result persistence, artifact location generation, and migrations.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

# Add repository root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.services.optimization import (
    build_optimization_artifact_path,
    build_optimization_evidence,
    get_optimization_migrations,
    load_search_checkpoint,
    persist_optimization_result,
    save_search_checkpoint,
)
from tests.optimization.usage._support import (
    SqliteOptimizationStore,
    checkpoint,
    evidence_request,
)


def _feature_header(title: str) -> None:
    """Print the feature header banner."""
    print(f"\n{'=' * 88}\n{title}\n{'=' * 88}")


def _header(title: str) -> None:
    """Print one example heading."""
    print(f"\n{'=' * 88}\n{title}\n{'=' * 88}")


def _format_result(obj: Any) -> str:
    """Dynamically format the output result type name and field/key signature."""
    cls = type(obj)
    type_name = cls.__name__
    if hasattr(cls, "model_fields"):
        keys = ", ".join(cls.model_fields.keys())
        return f"Output Result -> {type_name}({keys}) : {type_name}"
    if isinstance(obj, dict):
        keys = ", ".join(obj.keys())
        return f"Output Result -> dict({keys}) : dict"
    if hasattr(obj, "__dict__"):
        keys = ", ".join(vars(obj).keys())
        return f"Output Result -> {type_name}({keys}) : {type_name}"
    return f"Output Result -> {type_name} : {type_name}"


def fr_opt_050() -> None:
    """FR-OPT-050: Stage 1 — State Store Port Definition.

    The system shall define an injected store port limited to Optimization-owned checkpoint/result reads and atomic writes.
    """
    _header("Stage 1: State Store Port - Initialize Store Interface (FR-OPT-050)")
    store = SqliteOptimizationStore()
    print(_format_result(store))
    print(f"Data -> store_path='{store.path}'")


def fr_opt_051() -> None:
    """FR-OPT-051: Stage 2 — Checkpoint Evidence Structure.

    The system shall define immutable checkpoint evidence with search ID, reproducibility hash, and position.
    """
    _header("Stage 2: Checkpoint Structure - Define Checkpoint Evidence (FR-OPT-051)")
    ckpt = checkpoint()
    print(_format_result(ckpt))
    print(
        f"Data -> search_id='{ckpt.search_id}', candidate_position={ckpt.completed_candidate_position}"
    )


def fr_opt_052() -> None:
    """FR-OPT-052: Stage 3 — Atomic Checkpoint Save & Load.

    The system shall atomically save each completed-candidate checkpoint and recover exact matches.
    """
    _header(
        "Stage 3: Checkpoint Operations - Save & Load Search Checkpoint (FR-OPT-052)"
    )
    store = SqliteOptimizationStore()
    ckpt = checkpoint()
    save_search_checkpoint(ckpt, store)
    loaded_ckpt = load_search_checkpoint(
        search_id=ckpt.search_id,
        reproducibility_hash=ckpt.reproducibility_hash,
        store=store,
    )
    print(_format_result(loaded_ckpt))
    print(
        f"Data -> loaded_search_id='{loaded_ckpt.search_id}', loaded_position={loaded_ckpt.completed_candidate_position}"
    )


def fr_opt_053() -> None:
    """FR-OPT-053: Stage 3 — Result Persistence.

    The system shall atomically persist one canonical OptimizationResult v1 with ranked-candidate evidence.
    """
    _header("Stage 3: Result Persistence - Persist Optimization Result (FR-OPT-053)")
    store = SqliteOptimizationStore()
    ev_req = evidence_request()
    opt_evidence = build_optimization_evidence(ev_req)
    persist_res = persist_optimization_result(opt_evidence, store)
    print(_format_result(persist_res))
    print(f"Data -> durable={persist_res.durable}")


def fr_opt_054() -> None:
    """FR-OPT-054: Stage 3 — Artifact Path Construction.

    The system shall build artifact locations beneath approved roots from search and reproducibility identifiers.
    """
    _header("Stage 3: Artifact Pathing - Build Artifact Location (FR-OPT-054)")
    artifact_path = build_optimization_artifact_path(
        artifact_root=Path("tmp/artifacts"),
        kind="checkpoints",
        search_id="search-one",
        reproducibility_hash="a" * 64,
    )
    print(_format_result(artifact_path))
    print(f"Data -> artifact_suffix='{artifact_path.suffix}'")


def fr_opt_055() -> None:
    """FR-OPT-055: Stage 2 — Migration Definitions.

    The system shall expose ordered additive Optimization migration definitions for results and checkpoints.
    """
    _header(
        "Stage 2: Migration Declarations - Get Optimization Migrations (FR-OPT-055)"
    )
    migrations = get_optimization_migrations()
    print(_format_result(migrations))
    print(f"Data -> migration_count={len(migrations)}")


def main() -> None:
    """Run all feature examples in sequential module flow order."""
    _feature_header(
        "FEATURE: FEAT-OPT-06 — state/ — Optimization-Owned Durable State\n\n"
        "Purpose: Manage Optimization state store contracts, search checkpointing, result persistence, artifact path generation, and migration definitions.\n\n"
        "Module flow:\n"
        "-> Stage 1: State store port interface initialization\n"
        "-> Stage 2: Checkpoint contract definition and migration declaration inspection\n"
        "-> Stage 3: Atomic search checkpoint save/load, result persistence, and artifact path generation"
    )

    # Stage 1: Store Port
    fr_opt_050()

    # Stage 2: Contracts & Migrations
    fr_opt_051()
    fr_opt_055()

    # Stage 3: Persistence & Pathing
    fr_opt_052()
    fr_opt_053()
    fr_opt_054()


if __name__ == "__main__":
    main()
