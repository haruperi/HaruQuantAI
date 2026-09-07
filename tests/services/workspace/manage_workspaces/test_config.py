"""Strict configuration tests for FEAT-WS-MANAGE_WORKSPACES."""

import pytest
from app.services.workspace.manage_workspaces.config import (
    ManageWorkspacesConfig,
    from_dict,
)
from app.services.workspace.manage_workspaces.manifest import SPEC


def test_config_defaults_and_manifest_parity() -> None:
    config = from_dict(None)
    assert config == ManageWorkspacesConfig()
    assert SPEC.config_keys == frozenset(
        {
            "auto_migrate",
            "busy_timeout_seconds",
            "staged_grace_period_seconds",
            "max_manifest_files",
            "max_backup_bytes",
        }
    )


@pytest.mark.parametrize(
    ("value", "error"),
    [
        ({"unknown": True}, ValueError),
        ({"auto_migrate": 1}, TypeError),
        ({"busy_timeout_seconds": float("inf")}, ValueError),
        ({"staged_grace_period_seconds": -1}, ValueError),
        ({"max_manifest_files": 0}, ValueError),
        ({"max_backup_bytes": True}, TypeError),
    ],
)
def test_config_rejects_unknown_wrong_type_and_unbounded_values(
    value: dict[str, object], error: type[Exception]
) -> None:
    with pytest.raises(error):
        from_dict(value)
