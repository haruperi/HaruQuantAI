"""Configuration tests for FEAT-WS-MANAGE_ACCOUNTS."""

from pathlib import Path

import pytest
from app.services.workspace.manage_accounts.config import (
    ManageAccountsConfig,
    from_dict,
)


def test_config_accepts_canonical_database(tmp_path: Path) -> None:
    """The configuration resolves only a database directory or canonical haruquantai.db file."""
    root = tmp_path / "database"
    assert from_dict({"database_path": root}).workspace_path == root
    database = root / "haruquantai.db"
    assert ManageAccountsConfig(database_path=database).workspace_path == database
    assert (
        ManageAccountsConfig(database_path=Path("haruquantai.db")).workspace_path.name
        == "haruquantai.db"
    )
    assert ManageAccountsConfig.from_dict({}).workspace_path.name == "haruquantai.db"


def test_config_rejects_unknown_type_and_arbitrary_database_file(
    tmp_path: Path,
) -> None:
    """Invalid configuration fails before persistence effects."""
    with pytest.raises(ValueError, match="Unknown"):
        from_dict({"unknown": True})
    with pytest.raises(TypeError, match="string or Path"):
        from_dict({"database_path": 42})
    with pytest.raises(ValueError, match=r"haruquantai\.db"):
        ManageAccountsConfig(database_path=tmp_path / "arbitrary.db")
