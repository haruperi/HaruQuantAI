"""Persistence integration evidence for the built-in Strategy catalogue."""

from pathlib import Path

from app.services.strategy import (
    bootstrap_builtin_strategies,
    build_development_strategy_validation_policy,
    list_strategy_definitions,
    list_strategy_versions,
)
from app.services.strategy.contracts.responses import unwrap_strategy_response

from tests.strategy.unit.test_catalog import storage_context
from tests.strategy.unit.test_models import make_auth


def test_bootstrap_builtin_strategies_idempotency(tmp_path: Path) -> None:
    """Verify repeated bootstrap preserves seven immutable built-in versions."""
    auth = make_auth(permissions=("strategy:register", "strategy:parameter_update"))
    policy = build_development_strategy_validation_policy()
    with storage_context(tmp_path):
        first = unwrap_strategy_response(
            bootstrap_builtin_strategies(auth, policy), operation="bootstrap1"
        )
        retry = unwrap_strategy_response(
            bootstrap_builtin_strategies(auth, policy), operation="bootstrap2"
        )
        definitions = unwrap_strategy_response(
            list_strategy_definitions(), operation="list_defs"
        )
        versions = unwrap_strategy_response(
            list_strategy_versions(), operation="list_vers"
        )
    assert first["registered_strategies"] == 7
    assert retry["registered_strategies"] == 7
    assert len(definitions) == 7
    assert len(versions) == 7
