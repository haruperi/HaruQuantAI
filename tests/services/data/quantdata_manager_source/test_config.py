"""Unit tests for QuantDataManager Source configuration."""

from pathlib import Path

from app.services.data.quantdata_manager_source.config import QuantDataManagerConfig


def test_config_defaults() -> None:
    """Verify default configuration values."""
    cfg = QuantDataManagerConfig()
    assert cfg.allowed_root is None
    assert cfg.database_path is None
    assert cfg.auto_migrate is True
    assert cfg.get_allowed_root_path() is None
    assert cfg.get_database_path() is None


def test_config_path_validation(tmp_path: Path) -> None:
    """Verify path containment check."""
    cfg = QuantDataManagerConfig(
        allowed_root=tmp_path, database_path=tmp_path / "test.db"
    )
    assert cfg.get_allowed_root_path() == tmp_path.resolve()
    assert cfg.get_database_path() == (tmp_path / "test.db").resolve()

    inside_file = tmp_path / "user" / "data" / "History" / "EURUSD_M1.dat"
    assert cfg.is_path_allowed(inside_file) is True

    outside_file = tmp_path.parent / "escape.dat"
    assert cfg.is_path_allowed(outside_file) is False

    # No root configured
    empty_cfg = QuantDataManagerConfig()
    assert empty_cfg.is_path_allowed(inside_file) is False
