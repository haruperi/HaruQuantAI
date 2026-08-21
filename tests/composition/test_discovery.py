"""Tests for feature discovery via manual registration and entry points."""

from unittest.mock import MagicMock, patch

from app.composition.discovery import FeatureDiscoverer
from app.contracts.system.clock import SYSTEM_CLOCK
from app.kernel.context import FeatureContext
from app.kernel.feature import Feature, FeatureSpec


class MockFeature:
    spec = FeatureSpec(
        feature_id="FEAT-SYS-PROVIDE_CLOCK",
        domain="system",
        provides=frozenset({SYSTEM_CLOCK}),
    )

    async def mount(self, _context: FeatureContext, _config: object) -> None:
        pass


class InvalidSpecFeature:
    spec = FeatureSpec(
        feature_id="   ",  # Invalid empty ID
        domain="system",
        provides=frozenset(),
    )

    async def mount(self, _context: FeatureContext, _config: object) -> None:
        pass


def test_discover_manual_features() -> None:
    """Test discovering manually registered feature instances and factories."""
    with patch("importlib.metadata.entry_points", return_value=[]):
        discoverer = FeatureDiscoverer()
        discoverer.register_feature(MockFeature())
        discoverer.register_feature(MockFeature)

        result = discoverer.discover()
        assert "FEAT-SYS-PROVIDE_CLOCK" in result.discovered
        assert len(result.failed_specs) == 0
        assert len(result.failed_imports) == 0
        assert FeatureContext is not None


def test_discover_invalid_spec_feature() -> None:
    """Test discovering feature with invalid spec records failed_specs."""
    with patch("importlib.metadata.entry_points", return_value=[]):
        discoverer = FeatureDiscoverer()
        discoverer.register_feature(InvalidSpecFeature())

        result = discoverer.discover()
        assert len(result.discovered) == 0
        assert len(result.failed_specs) == 1


def test_discover_entry_points_success() -> None:
    """Test discovering features through entry points."""
    mock_ep = MagicMock()
    mock_ep.name = "mock-feature"
    mock_ep.load.return_value = MockFeature

    with patch("importlib.metadata.entry_points", return_value=[mock_ep]):
        discoverer = FeatureDiscoverer()
        result = discoverer.discover()

        assert "FEAT-SYS-PROVIDE_CLOCK" in result.discovered
        assert len(result.missing_targets) == 0


def test_discover_entry_points_missing_module() -> None:
    """Test entry point targeting missing module records missing_targets."""
    mock_ep = MagicMock()
    mock_ep.name = "absent-feature"
    mock_ep.value = "app.services.absent.feature:create_feature"
    mock_ep.load.side_effect = ModuleNotFoundError(
        "No module named 'app.services.absent'", name="app.services.absent"
    )

    with patch("importlib.metadata.entry_points", return_value=[mock_ep]):
        discoverer = FeatureDiscoverer()
        result = discoverer.discover()

        assert "absent-feature" in result.missing_targets
        assert "is missing" in result.missing_targets["absent-feature"]


def test_discover_entry_points_missing_third_party() -> None:
    """Test entry point with missing external dependency records failed_imports."""
    mock_ep = MagicMock()
    mock_ep.name = "mt5-feature"
    mock_ep.value = "app.services.broker.mt5:create_feature"
    mock_ep.load.side_effect = ModuleNotFoundError(
        "No module named 'MetaTrader5'", name="MetaTrader5"
    )

    with patch("importlib.metadata.entry_points", return_value=[mock_ep]):
        discoverer = FeatureDiscoverer()
        result = discoverer.discover()

        assert "mt5-feature" in result.failed_imports
        assert (
            "Feature dependency 'MetaTrader5' missing"
            in result.failed_imports["mt5-feature"]
        )


def test_discover_entry_points_invalid_object() -> None:
    """Test entry point returning object without Feature protocol."""
    mock_ep = MagicMock()
    mock_ep.name = "invalid-feature"
    mock_ep.load.return_value = object

    with patch("importlib.metadata.entry_points", return_value=[mock_ep]):
        discoverer = FeatureDiscoverer()
        result = discoverer.discover()

        assert "invalid-feature" in result.failed_specs
        assert (
            "does not satisfy Feature protocol"
            in result.failed_specs["invalid-feature"]
        )


def test_discover_manual_factory_error() -> None:
    """Test manual factory raising exception records in failed_imports."""

    def broken_factory() -> Feature:
        msg = "Factory init error"
        raise RuntimeError(msg)

    with patch("importlib.metadata.entry_points", return_value=[]):
        discoverer = FeatureDiscoverer()
        discoverer.register_feature(broken_factory, feature_id="broken-feat")
        result = discoverer.discover()
        assert "broken-feat" in result.failed_imports
        assert "Factory init error" in result.failed_imports["broken-feat"]
