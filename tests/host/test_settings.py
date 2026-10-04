"""Unit tests for host configuration settings container and dot-access interface."""

from __future__ import annotations

from pathlib import Path

import pytest
from app.host.persistance import SettingsStore
from app.host.settings import HostSettings, _SettingsNode, settings


def test_settings_node_primitives_and_dict_access() -> None:
    """Verify _SettingsNode provides dot and dict access for nested structures."""
    raw_data = {
        "theme": "dark",
        "nested": {"key": "value", "count": 10},
        "QQE.RSIPeriod": 14,
        "items": [{"name": "item1"}, {"name": "item2"}],
    }
    node = _SettingsNode(raw_data)

    # Dot-access
    assert node.theme == "dark"
    assert node.nested.key == "value"
    assert node.nested.count == 10
    assert node.QQE_RSIPeriod == 14
    assert node.items[0].name == "item1"
    assert node.items[1].name == "item2"

    # Dict-access
    assert node["theme"] == "dark"
    assert node["nested"]["key"] == "value"
    assert node["QQE.RSIPeriod"] == 14
    assert node["QQE_RSIPeriod"] == 14

    # .get() access
    assert node.get("theme") == "dark"
    assert node.get("QQE.RSIPeriod") == 14
    assert node.get("missing", "fallback") == "fallback"

    # Contains, len, iter, as_dict, repr
    assert "theme" in node
    assert "QQE.RSIPeriod" in node
    assert "QQE_RSIPeriod" in node
    assert "nonexistent" not in node
    assert len(node) == 4
    assert list(iter(node)) == ["theme", "nested", "QQE.RSIPeriod", "items"]
    assert node.as_dict() == raw_data
    assert "_SettingsNode" in repr(node)

    # Error handling
    with pytest.raises(AttributeError, match="Setting attribute 'unknown' not found"):
        _ = node.unknown

    with pytest.raises(KeyError, match="Setting key 'unknown' not found"):
        _ = node["unknown"]


def test_settings_node_primitive_wrap() -> None:
    """Verify _SettingsNode wraps primitive value safely."""
    node = _SettingsNode(123)
    assert node.value == 123
    assert node["value"] == 123
    assert node.get("value") == 123


def test_host_settings_missing_db(tmp_path: Path) -> None:
    """Verify HostSettings handles missing database file gracefully."""
    missing_path = tmp_path / "does_not_exist.db"
    s = HostSettings(db_path=missing_path)

    assert s.db_path == missing_path
    assert len(s) == 0
    assert s.get("anything") is None
    assert s.get("anything", 999) == 999
    assert "anything" not in s
    assert s.as_dict() == {}
    assert "HostSettings" in repr(s)

    with pytest.raises(AttributeError, match="HostSettings has no setting or scope"):
        _ = s.missing

    with pytest.raises(KeyError, match="HostSettings has no setting or scope"):
        _ = s["missing"]


def test_host_settings_seeded_db(tmp_path: Path) -> None:
    """Verify HostSettings loads seeded database records with dot-access."""
    db_file = tmp_path / "seeded.db"
    store = SettingsStore(db_file)
    store.initialize()

    # Seed application settings
    store.update_settings(
        scope="application",
        values={
            "app.general": {"theme": "dark", "language": "en", "zoom": 1},
            "config.agents": {
                "active_provider": "gemini",
                "gemini": {"model": "gemini-3.6-flash"},
            },
        },
    )

    # Seed host settings
    store.update_settings(
        scope="host",
        values={"bound_port": 8080},
    )

    s = HostSettings(db_path=db_file)

    # Top-level dot-access
    assert s.app_general.theme == "dark"
    assert s.app_general.language == "en"
    assert s.app_general.zoom == 1
    assert s.config_agents.active_provider == "gemini"
    assert s.config_agents.gemini.model == "gemini-3.6-flash"
    assert s.bound_port == 8080

    # Scoped namespace dot-access
    assert s.application.app_general.theme == "dark"
    assert s.host.bound_port == 8080

    # Dict-style access
    assert s["app_general"]["theme"] == "dark"
    assert s.get("app.general")["theme"] == "dark"
    assert s.get("bound_port") == 8080
    assert s.get("missing", "default") == "default"

    # Iteration and items
    items = dict(s.items())
    assert "app_general" in items
    assert "config_agents" in items
    assert "bound_port" in items
    assert list(iter(s)) == list(items.keys())

    # as_dict returns raw dicts
    data_dict = s.as_dict()
    assert data_dict["app_general"] == {
        "theme": "dark",
        "language": "en",
        "zoom": 1,
    }


def test_host_settings_update_and_reload(tmp_path: Path) -> None:
    """Verify update() persists to database and refreshes memory."""
    db_file = tmp_path / "update.db"
    store = SettingsStore(db_file)
    store.initialize()

    store.update_settings(
        scope="application",
        values={"user.access": {"username": "admin", "roles": ["operator"]}},
    )

    s = HostSettings(db_path=db_file)
    assert s.user_access.username == "admin"
    assert s.user_access.roles == ["operator"]

    # Perform update via HostSettings
    s.update(
        scope="application",
        values={"user.access": {"username": "superuser", "roles": ["admin"]}},
    )
    assert s.user_access.username == "superuser"
    assert s.user_access.roles == ["admin"]


def test_global_settings_singleton() -> None:
    """Verify default global settings singleton is instantiated."""
    assert settings.db_path.name == "haruquantai.db"
    assert isinstance(settings, HostSettings)
