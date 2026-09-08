"""Configuration tests for FEAT-WS-MANAGE_ACCOUNTS."""

from pathlib import Path

import pytest
from app.services.workspace.manage_accounts.config import (
    ManageAccountsConfig,
    from_dict,
)


def test_config_accepts_workspace_root_and_canonical_database(tmp_path: Path) -> None:
    """The compatibility key resolves only a workspace root or canonical file."""
    root = tmp_path / "workspace"
    assert from_dict({"database_path": root}).workspace_path == root
    database = root / "metadata" / "workspace.db"
    assert ManageAccountsConfig(database_path=database).workspace_path == root
    assert ManageAccountsConfig.from_dict({}).workspace_path.name == "local"


def test_config_rejects_unknown_type_and_arbitrary_database_file(
    tmp_path: Path,
) -> None:
    """Invalid configuration fails before persistence effects."""
    with pytest.raises(ValueError, match="Unknown"):
        from_dict({"unknown": True})
    with pytest.raises(TypeError, match="string or Path"):
        from_dict({"database_path": 42})
    with pytest.raises(ValueError, match="workspace root"):
        ManageAccountsConfig(database_path=tmp_path / "arbitrary.db")
