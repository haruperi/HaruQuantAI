"""Unit tests for Strategy built-in catalogue and hash provenance."""

import hashlib
from pathlib import Path

from app.services.strategy import (
    bootstrap_builtin_strategies,
    build_development_strategy_validation_policy,
    list_builtin_strategy_descriptors,
    list_strategy_definitions,
    list_strategy_versions,
)
from app.services.strategy.contracts.responses import unwrap_strategy_response
from app.services.strategy.registry.catalogue import _BUILTIN_DESCRIPTORS

from tests.strategy.unit.test_catalog import storage_context
from tests.strategy.unit.test_models import make_auth


def test_builtin_catalogue_has_exact_seven_descriptors() -> None:
    """Verify built-in catalogue contains exactly seven registered descriptors.

    Args:
        None.

    Returns:
        None.
    """
    res = unwrap_strategy_response(
        list_builtin_strategy_descriptors(),
        operation="list_builtin_strategy_descriptors",
    )
    assert len(res) == 7
    keys = tuple(desc["evaluator_key"] for desc in res)
    assert keys == (
        "naive_ma_trend",
        "decomposing_trade",
        "harriet_hedging",
        "market_structure",
        "random_walk",
        "sqx_breakout_atr_trailing",
        "white_fairy",
    )


def test_builtin_evaluator_source_hashes_match_files() -> None:
    """Verify SHA-256 source hashes match actual file bytes on disk.

    Args:
        None.

    Returns:
        None.
    """
    for desc in _BUILTIN_DESCRIPTORS:
        rel_path = desc.module_path.replace(".", "/") + ".py"
        file_path = Path(rel_path)
        assert file_path.exists(), f"Evaluator file {rel_path} does not exist"
        content = file_path.read_bytes()
        expected_hash = hashlib.sha256(content).hexdigest()
        assert desc.source_hash == expected_hash, (
            f"Source hash drift detected for {desc.evaluator_key}: "
            f"expected {expected_hash}, got {desc.source_hash}"
        )


def test_builtin_dependency_hash_matches_uv_lock() -> None:
    """Verify SHA-256 dependency hash matches repository uv.lock.

    Args:
        None.

    Returns:
        None.
    """
    lock_path = Path("uv.lock")
    assert lock_path.exists(), "uv.lock file missing"
    expected_lock_hash = hashlib.sha256(lock_path.read_bytes()).hexdigest()
    for desc in _BUILTIN_DESCRIPTORS:
        assert desc.dependency_hash == expected_lock_hash, (
            f"Dependency hash mismatch for {desc.evaluator_key}"
        )


def test_bootstrap_builtin_strategies_idempotency(tmp_path: Path) -> None:
    """Verify bootstrap_builtin_strategies creates definitions, versions, and configs cleanly.

    Args:
        tmp_path: Temporary directory fixture for isolated SQLite storage.

    Returns:
        None.
    """
    auth = make_auth(permissions=("strategy:register", "strategy:parameter_update"))
    policy = build_development_strategy_validation_policy()
    with storage_context(tmp_path):
        res1 = unwrap_strategy_response(
            bootstrap_builtin_strategies(auth, policy),
            operation="bootstrap1",
        )
        assert res1["registered_strategies"] == 7

        res2 = unwrap_strategy_response(
            bootstrap_builtin_strategies(auth, policy),
            operation="bootstrap2",
        )
        assert res2["registered_strategies"] == 7

        defs = unwrap_strategy_response(
            list_strategy_definitions(), operation="list_defs"
        )
        vers = unwrap_strategy_response(list_strategy_versions(), operation="list_vers")
        assert len(defs) == 7
        assert len(vers) == 7
