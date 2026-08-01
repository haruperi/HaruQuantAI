"""Authoritative secret-free Strategy development validation policy."""

from app.services.strategy.contracts.factories import (
    create_strategy_validation_policy,
)


def build_development_strategy_validation_policy() -> object:
    """Build the bounded host policy used by the development API process.

    Returns:
        Validated immutable Strategy validation policy.
    """
    return create_strategy_validation_policy(
        policy_version="strategy-development-v1",
        approved_module_roots=("app.services.strategy",),
        max_config_payload_bytes=65_536,
        max_config_nesting_depth=12,
        max_config_string_length=4_096,
        max_config_collection_items=1_000,
    )


__all__ = ("build_development_strategy_validation_policy",)
