"""Supported Optimization state API."""

from app.services.optimization.state.artifacts import (
    build_optimization_artifact_path,
)
from app.services.optimization.state.contracts import (
    OPTIMIZATION_SCHEMA_VERSION,
    OptimizationCheckpoint,
    OptimizationPersistenceReceipt,
    OptimizationStateStore,
)
from app.services.optimization.state.migrations import get_optimization_migrations
from app.services.optimization.state.persistence import persist_optimization_result
from app.services.optimization.state.stores import (
    load_search_checkpoint,
    save_search_checkpoint,
)

__all__ = [
    "OPTIMIZATION_SCHEMA_VERSION",
    "OptimizationCheckpoint",
    "OptimizationPersistenceReceipt",
    "OptimizationStateStore",
    "build_optimization_artifact_path",
    "get_optimization_migrations",
    "load_search_checkpoint",
    "persist_optimization_result",
    "save_search_checkpoint",
]
