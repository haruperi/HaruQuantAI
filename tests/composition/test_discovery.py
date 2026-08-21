"""Tests for manual and entry-point feature discovery."""

from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

from app.composition.discovery import FeatureDiscoverer
from app.contracts.system.clock import SYSTEM_CLOCK
from app.kernel.feature import Feature, FeatureSpec

if TYPE_CHECKING:
    from app.kernel.context import FeatureContext


class MockFeature:
    spec = FeatureSpec(
        "FEAT-SYS-PROVIDE_CLOCK",
        "system",
        provides=frozenset({SYSTEM_CLOCK}),
    )

    async def mount(self, _context: FeatureContext, _config: object) -> None:
        return None


class SecondMockFeature:
    spec = FeatureSpec(
        "FEAT-SYS-PROVIDE_CLOCK_SECOND",
        "system",
        provides=frozenset(),
    )

    async def mount(self, _context: FeatureContext, _config: object) -> None:
        return None


class InvalidSpecFeature:
    spec = FeatureSpec("   ", "system", provides=frozenset())

    async def mount(self, _context: FeatureContext, _config: object) -> None:
        return None


def test_discover_manual_instance_and_factory() -> None:
    """Manual factories are keyed by their returned FeatureSpec ID."""
    with patch("importlib.metadata.entry_points", return_value=[]):
        discoverer = FeatureDiscoverer()
        discoverer.register_feature(MockFeature())
        discoverer.register_feature(SecondMockFeature)
        result = discoverer.discover()
    assert set(result.discovered) == {
        "FEAT-SYS-PROVIDE_CLOCK",
        "FEAT-SYS-PROVIDE_CLOCK_SECOND",
    }
    assert not result.failed_specs
    assert not result.failed_imports


def test_duplicate_feature_id_is_rejected_without_overwrite() -> None:
    """Duplicate IDs are diagnostic failures rather than silent overwrites."""
    with patch("importlib.metadata.entry_points", return_value=[]):
        discoverer = FeatureDiscoverer()
        first = MockFeature()
        second = MockFeature()
        discoverer.register_feature(first, feature_id="first")
        discoverer.register_feature(second, feature_id="second")
        result = discoverer.discover()
    assert result.discovered["FEAT-SYS-PROVIDE_CLOCK"] is first
    assert "second" in result.failed_specs
    assert "Duplicate feature ID" in result.failed_specs["second"]


def test_invalid_spec_records_failed_specs() -> None:
    """Invalid feature specifications are categorized without crashing discovery."""
    with patch("importlib.metadata.entry_points", return_value=[]):
        discoverer = FeatureDiscoverer()
        discoverer.register_feature(InvalidSpecFeature())
        result = discoverer.discover()
    assert not result.discovered
    assert len(result.failed_specs) == 1


def test_entry_point_success() -> None:
    """Valid entry points are loaded under the runtime feature ID."""
    entry_point = MagicMock()
    entry_point.name = "mock-feature"
    entry_point.load.return_value = MockFeature
    with patch("importlib.metadata.entry_points", return_value=[entry_point]):
        result = FeatureDiscoverer().discover()
    assert "FEAT-SYS-PROVIDE_CLOCK" in result.discovered
    assert not result.missing_targets


def test_entry_point_missing_module_is_categorized() -> None:
    """Missing feature targets are distinct from missing third-party packages."""
    entry_point = MagicMock()
    entry_point.name = "absent-feature"
    entry_point.value = "app.services.absent.feature:create_feature"
    entry_point.load.side_effect = ModuleNotFoundError(
        "No module named 'app.services.absent'",
        name="app.services.absent",
    )
    with patch("importlib.metadata.entry_points", return_value=[entry_point]):
        result = FeatureDiscoverer().discover()
    assert "absent-feature" in result.missing_targets


def test_entry_point_missing_dependency_is_categorized() -> None:
    """A feature's missing package dependency is reported separately."""
    entry_point = MagicMock()
    entry_point.name = "mt5-feature"
    entry_point.value = "app.services.broker.mt5:create_feature"
    entry_point.load.side_effect = ModuleNotFoundError(
        "No module named 'MetaTrader5'",
        name="MetaTrader5",
    )
    with patch("importlib.metadata.entry_points", return_value=[entry_point]):
        result = FeatureDiscoverer().discover()
    assert (
        "Feature dependency 'MetaTrader5' missing"
        in result.failed_imports["mt5-feature"]
    )


def test_entry_point_invalid_object_is_rejected() -> None:
    """Loaded objects must satisfy the Feature protocol."""
    entry_point = MagicMock()
    entry_point.name = "invalid-feature"
    entry_point.load.return_value = object
    with patch("importlib.metadata.entry_points", return_value=[entry_point]):
        result = FeatureDiscoverer().discover()
    assert "does not satisfy Feature protocol" in result.failed_specs["invalid-feature"]


def test_manual_factory_error_is_categorized() -> None:
    """Manual factory failures are diagnostic import failures."""

    def broken_factory() -> Feature:
        raise RuntimeError("Factory init error")

    with patch("importlib.metadata.entry_points", return_value=[]):
        discoverer = FeatureDiscoverer()
        discoverer.register_feature(broken_factory, feature_id="broken-feat")
        result = discoverer.discover()
    assert "Factory init error" in result.failed_imports["broken-feat"]
