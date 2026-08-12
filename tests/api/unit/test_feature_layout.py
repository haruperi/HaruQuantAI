"""Structural guarantees for focused API feature ownership."""

from pathlib import Path

_API_ROOT = Path(__file__).parents[3] / "app" / "services" / "api"
_WORKSTATION_ROOT = _API_ROOT / "workstation"
_REMOVED_HORIZONTAL_FOLDERS = {"migrations", "persistence", "routes", "streams"}
_REMOVED_ROOT_FILES = {"_limits.py", "_settings.py"}
_WORKSTATION_FEATURES = {
    "agentic",
    "dashboards",
    "data",
    "event_delivery",
    "indicators",
    "markets",
    "operational",
    "operator",
    "optimization",
    "portfolio",
    "research",
    "risk",
    "settings",
    "simulation",
    "strategies",
    "trading",
    "watchlists",
}
_STANDARD_FILES = {
    "README.md",
    "__init__.py",
    "orchestration.py",
    "routes.py",
    "schemas.py",
}


def test_horizontal_api_folders_are_absent() -> None:
    """Verify retired root implementation folders cannot regain ownership."""
    present = {path.name for path in _API_ROOT.iterdir() if path.is_dir()}
    assert not (_REMOVED_HORIZONTAL_FOLDERS & present)


def test_api_root_behavior_files_are_absent() -> None:
    """Verify bootstrap configuration and limits remain Settings-owned."""
    present = {path.name for path in _API_ROOT.iterdir() if path.is_file()}
    assert not (_REMOVED_ROOT_FILES & present)
    settings = _WORKSTATION_ROOT / "settings"
    assert (settings / "bootstrap.py").is_file()
    assert (settings / "limits.py").is_file()


def test_every_workstation_feature_has_the_standard_surface() -> None:
    """Verify each registered page/widget feature is independently traceable."""
    present = {
        path.name
        for path in _WORKSTATION_ROOT.iterdir()
        if path.is_dir() and path.name != "__pycache__"
    }
    assert present == _WORKSTATION_FEATURES
    for feature in present:
        files = {path.name for path in (_WORKSTATION_ROOT / feature).iterdir()}
        assert files >= _STANDARD_FILES
