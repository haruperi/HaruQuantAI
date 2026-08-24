"""Unit tests for FEAT-PLUG-REGISTER_CONTRIBUTIONS (Plugin Contributions)."""

from __future__ import annotations

import pytest

from app.contracts.plugins.errors import (
    PluginContractTestError,
    PluginContributionError,
)
from app.contracts.plugins.models import (
    PluginContributionDescriptor,
    PluginManifest,
    PluginType,
)
from app.services.plugins.contributions.config import PluginContributionsConfig
from app.services.plugins.contributions.plugin_contributions import (
    RegisterContributionsService,
    fr_plug_register_plugin_contributions,
)


@pytest.fixture
def service() -> RegisterContributionsService:
    """Fixture providing a default RegisterContributionsService instance."""
    return RegisterContributionsService()


@pytest.fixture
def sample_manifest() -> PluginManifest:
    """Fixture providing a valid plugin manifest declaring multiple types."""
    return PluginManifest(
        id="com.haruquantai.example.quantpack",
        version="1.0.0",
        api_range=">=1.0.0,<2.0.0",
        types=tuple(PluginType),
    )


def test_plug_register_plugin_contributions(
    service: RegisterContributionsService,
    sample_manifest: PluginManifest,
) -> None:
    """Test FR-PLUG-REGISTER_PLUGIN_CONTRIBUTIONS: Register typed contributions."""
    c1 = PluginContributionDescriptor(
        plugin_id=sample_manifest.id,
        plugin_type=PluginType.INDICATOR,
        contribution_id="com.haruquantai.example.quantpack.sma",
        name="Simple Moving Average",
        description="Calculates SMA.",
    )
    c2 = PluginContributionDescriptor(
        plugin_id=sample_manifest.id,
        plugin_type=PluginType.METRIC,
        contribution_id="com.haruquantai.example.quantpack.drawdown",
        name="Max Drawdown",
        description="Calculates max drawdown.",
    )

    class MockSMA:
        def calculate(self, data: list[float]) -> list[float]:
            return data

    class MockDrawdown:
        def compute(self, data: list[float]) -> float:
            return min(data) if data else 0.12

    implementations = {
        c1.contribution_id: MockSMA(),
        c2.contribution_id: MockDrawdown(),
    }

    result = service.register_contributions(
        sample_manifest,
        (c1, c2),
        implementations=implementations,
    )

    assert result.is_successful is True
    assert len(result.contributions) == 2
    assert len(result.test_results) == 2
    assert all(tr.passed for tr in result.test_results)

    indicators = service.get_contributions(PluginType.INDICATOR)
    assert len(indicators) == 1
    assert indicators[0].contribution_id == c1.contribution_id

    metrics = service.get_contributions(PluginType.METRIC)
    assert len(metrics) == 1
    assert metrics[0].contribution_id == c2.contribution_id


def test_register_all_10_plugin_types(
    service: RegisterContributionsService,
    sample_manifest: PluginManifest,
) -> None:
    """Verify that all 10 supported PluginType enum members can be registered."""
    descriptors: list[PluginContributionDescriptor] = []
    implementations: dict[str, object] = {}

    class MockCallable:
        def __call__(self) -> None:
            pass

        def evaluate(self) -> None:
            pass

        def calculate(self) -> None:
            pass

        def compute(self) -> None:
            pass

        def filter(self) -> None:
            pass

    mock_impl = MockCallable()

    for ptype in PluginType:
        cid = f"{sample_manifest.id}.{ptype.value.lower()}"
        desc = PluginContributionDescriptor(
            plugin_id=sample_manifest.id,
            plugin_type=ptype,
            contribution_id=cid,
            name=f"Test {ptype.value}",
        )
        descriptors.append(desc)
        implementations[cid] = mock_impl

    result = service.register_contributions(
        sample_manifest,
        tuple(descriptors),
        implementations=implementations,
    )

    assert result.is_successful is True
    assert len(result.contributions) == 10
    assert len(service.get_contributions()) == 10


def test_registration_mismatched_plugin_id(
    service: RegisterContributionsService,
    sample_manifest: PluginManifest,
) -> None:
    """Verify error when contribution declares a different plugin_id."""
    desc = PluginContributionDescriptor(
        plugin_id="com.other.plugin",
        plugin_type=PluginType.BLOCK,
        contribution_id="com.other.plugin.block1",
        name="Block",
    )
    with pytest.raises(PluginContributionError, match=r"does not match manifest id"):
        service.register_contributions(sample_manifest, (desc,))


def test_registration_undeclared_plugin_type(
    service: RegisterContributionsService,
) -> None:
    """Verify error when contribution type is not declared in manifest.types."""
    manifest = PluginManifest(
        id="com.test.limited",
        version="1.0.0",
        api_range=">=1.0.0",
        types=(PluginType.INDICATOR,),  # only INDICATOR declared
    )
    desc = PluginContributionDescriptor(
        plugin_id=manifest.id,
        plugin_type=PluginType.METRIC,  # undeclared METRIC
        contribution_id=f"{manifest.id}.metric1",
        name="Metric",
    )
    with pytest.raises(
        PluginContributionError, match=r"is not declared in plugin manifest"
    ):
        service.register_contributions(manifest, (desc,))


def test_registration_exceeding_max_limit(
    sample_manifest: PluginManifest,
) -> None:
    """Verify enforcement of maximum contributions per plugin limit."""
    config = PluginContributionsConfig(max_contributions_per_plugin=2)
    service = RegisterContributionsService(config=config)

    descs = tuple(
        PluginContributionDescriptor(
            plugin_id=sample_manifest.id,
            plugin_type=PluginType.INDICATOR,
            contribution_id=f"{sample_manifest.id}.ind_{i}",
            name=f"Ind {i}",
        )
        for i in range(3)
    )

    with pytest.raises(PluginContributionError, match=r"exceeding maximum limit of 2"):
        service.register_contributions(sample_manifest, descs)


def test_strict_contract_test_failure(
    service: RegisterContributionsService,
    sample_manifest: PluginManifest,
) -> None:
    """Verify that strict contract testing raises PluginContractTestError on invalid contribution."""
    desc = PluginContributionDescriptor(
        plugin_id=sample_manifest.id,
        plugin_type=PluginType.INDICATOR,
        contribution_id=f"{sample_manifest.id}.bad_indicator",
        name="",  # Empty name fails contract test
    )

    with pytest.raises(PluginContractTestError, match=r"failed contract test"):
        service.register_contributions(sample_manifest, (desc,))


def test_non_strict_contract_test_failure(
    sample_manifest: PluginManifest,
) -> None:
    """Verify that non-strict mode returns is_successful=False instead of raising."""
    config = PluginContributionsConfig(strict_contract_tests=False)
    service = RegisterContributionsService(config=config)

    desc = PluginContributionDescriptor(
        plugin_id=sample_manifest.id,
        plugin_type=PluginType.INDICATOR,
        contribution_id=f"{sample_manifest.id}.bad_indicator",
        name="",  # Empty name fails
    )

    result = service.register_contributions(sample_manifest, (desc,))
    assert result.is_successful is False
    assert len(result.errors) > 0
    assert len(service.get_contributions()) == 0


def test_get_contributions_and_single_lookup(
    service: RegisterContributionsService,
    sample_manifest: PluginManifest,
) -> None:
    """Verify querying contributions by filter and looking up single contribution."""
    c1 = PluginContributionDescriptor(
        plugin_id=sample_manifest.id,
        plugin_type=PluginType.BLOCK,
        contribution_id=f"{sample_manifest.id}.block_a",
        name="Block A",
    )
    c2 = PluginContributionDescriptor(
        plugin_id=sample_manifest.id,
        plugin_type=PluginType.FILTER,
        contribution_id=f"{sample_manifest.id}.filter_b",
        name="Filter B",
    )

    service.register_contributions(sample_manifest, (c1, c2))

    # Single lookup
    fetched = service.get_contribution(c1.contribution_id)
    assert fetched is not None
    assert fetched.name == "Block A"

    missing = service.get_contribution("non.existent.id")
    assert missing is None

    # Filtered lookup
    blocks = service.get_contributions(PluginType.BLOCK)
    assert len(blocks) == 1
    assert blocks[0].contribution_id == c1.contribution_id

    indicators = service.get_contributions(PluginType.INDICATOR)
    assert len(indicators) == 0


def test_unregister_contributions(
    service: RegisterContributionsService,
    sample_manifest: PluginManifest,
) -> None:
    """Verify unregistering all contributions belonging to a plugin ID."""
    c1 = PluginContributionDescriptor(
        plugin_id=sample_manifest.id,
        plugin_type=PluginType.BLOCK,
        contribution_id=f"{sample_manifest.id}.b1",
        name="B1",
    )
    c2 = PluginContributionDescriptor(
        plugin_id=sample_manifest.id,
        plugin_type=PluginType.FITNESS,
        contribution_id=f"{sample_manifest.id}.f1",
        name="F1",
    )

    service.register_contributions(sample_manifest, (c1, c2))
    assert len(service.get_contributions()) == 2

    removed = service.unregister_contributions(sample_manifest.id)
    assert removed == 2
    assert len(service.get_contributions()) == 0
    assert service.get_contribution(c1.contribution_id) is None


def test_fr_trace_function(
    sample_manifest: PluginManifest,
) -> None:
    """Verify fr_plug_register_plugin_contributions requirement trace function."""
    c1 = PluginContributionDescriptor(
        plugin_id=sample_manifest.id,
        plugin_type=PluginType.DATA_CONNECTOR,
        contribution_id=f"{sample_manifest.id}.binance",
        name="Binance Connector",
    )

    result = fr_plug_register_plugin_contributions(sample_manifest, (c1,))
    assert result.is_successful is True
    assert len(result.contributions) == 1
    assert result.contributions[0].contribution_id == c1.contribution_id
