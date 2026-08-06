"""Unit tests for registry/listing.py branch coverage floor."""

from unittest.mock import patch

from app.services.strategy import (
    get_strategy_definition,
    list_strategy_configs,
    list_strategy_versions,
    resolve_strategy_config,
)


def test_get_strategy_definition_not_found() -> None:
    """Verify get_strategy_definition returns NOT_FOUND when definition is absent."""
    with patch(
        "app.services.strategy.registry.listing.read_strategy_definitions",
        return_value=(),
    ):
        res = get_strategy_definition("nonexistent-id")
        assert res.status == "error"
        assert res.error is not None
        assert res.error.code == "STRATEGY_NOT_FOUND"


def test_list_strategy_versions_query_failure() -> None:
    """Verify list_strategy_versions query failure maps to INTERNAL_ERROR."""
    with patch(
        "app.services.strategy.registry.listing.read_strategy_versions",
        side_effect=ValueError("db query failed"),
    ):
        res = list_strategy_versions(strategy_id="test-id")
        assert res.status == "error"
        assert res.error is not None
        assert res.error.code == "STRATEGY_INTERNAL_ERROR"


def test_list_strategy_configs_empty() -> None:
    """Verify list_strategy_configs returns empty tuple when no configs found."""
    with patch(
        "app.services.strategy.registry.listing.read_strategy_configs",
        return_value=(),
    ):
        res = list_strategy_configs("test-id", "1.0.0")
        assert res.status == "success"
        assert res.data == ()


def test_resolve_strategy_config_not_found() -> None:
    """Verify resolve_strategy_config returns NOT_FOUND when config is absent."""
    with patch(
        "app.services.strategy.registry.listing.read_strategy_config_record",
        return_value=(),
    ):
        res = resolve_strategy_config("nonexistent-cfg-id")
        assert res.status == "error"
        assert res.error is not None
        assert res.error.code == "STRATEGY_NOT_FOUND"
