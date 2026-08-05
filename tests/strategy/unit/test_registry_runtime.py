"""Tests for Strategy runtime registry."""

from app.services.strategy.registry.runtime import (
    build_development_strategy_validation_policy,
)


def test_build_development_strategy_validation_policy_returns_valid_policy() -> None:
    """Verify runtime builds a valid development policy."""
    policy = build_development_strategy_validation_policy()
    assert policy.policy_version == "strategy-development-v1"
    assert "app.services.strategy" in policy.approved_module_roots
