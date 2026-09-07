"""Strict configuration tests for FEAT-WS-EXECUTE_PERSISTENCE."""

import pytest
from app.services.workspace.execute_persistence.config import (
    ExecutePersistenceConfig,
    from_dict,
)
from app.services.workspace.execute_persistence.manifest import SPEC


def test_config_defaults_and_manifest_parity() -> None:
    config = from_dict(None)
    assert config == ExecutePersistenceConfig()
    assert SPEC.config_keys == frozenset(
        {
            "busy_timeout_seconds",
            "max_export_limit",
            "max_statements_per_tx",
        }
    )


@pytest.mark.parametrize(
    ("value", "error"),
    [
        ({"unknown_key": 123}, ValueError),
        ({"busy_timeout_seconds": "not-a-number"}, TypeError),
        ({"busy_timeout_seconds": True}, TypeError),
        ({"busy_timeout_seconds": 0.05}, ValueError),
        ({"busy_timeout_seconds": 120.0}, ValueError),
        ({"max_export_limit": "string"}, TypeError),
        ({"max_export_limit": 0}, ValueError),
        ({"max_export_limit": 20_000}, ValueError),
        ({"max_statements_per_tx": "string"}, TypeError),
        ({"max_statements_per_tx": 0}, ValueError),
        ({"max_statements_per_tx": 2_000}, ValueError),
    ],
)
def test_config_rejects_unknown_wrong_type_and_unbounded_values(
    value: dict[str, object], error: type[Exception]
) -> None:
    with pytest.raises(error):
        from_dict(value)
