"""Tests for Optimization checkpoint store coordination."""

# ruff: noqa: INP001

import pytest
from app.services.optimization.errors import OptimizationError
from app.services.optimization.state import (
    load_search_checkpoint,
    save_search_checkpoint,
)
from tests.optimization.unit.test_state_contracts import (
    MemoryOptimizationStore,
    checkpoint,
)


def test_checkpoint_recovery_requires_exact_hash() -> None:
    """Recovery fails closed when requested identity differs from stored state."""
    store = MemoryOptimizationStore()
    save_search_checkpoint(checkpoint(), store)
    assert (
        load_search_checkpoint(
            search_id="search-one",
            reproducibility_hash="a" * 64,
            store=store,
        )
        == checkpoint()
    )
    with pytest.raises(OptimizationError) as captured:
        load_search_checkpoint(
            search_id="search-one",
            reproducibility_hash="b" * 64,
            store=store,
        )
    assert captured.value.code == "OPT_STATE_CONFLICT"
