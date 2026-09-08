"""Unit tests for RegisterContributionsService logic."""

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
from app.services.plugins.register_contributions.config import (
    PluginContributionsConfig,
)
from app.services.plugins.register_contributions.register_contributions import (
    RegisterContributionsService,
    fr_plug_register_plugin_contributions,
    fr_trc_plug_register_contributions_001,
    fr_trc_plug_register_contributions_002,
)


@pytest.fixture
def service() -> RegisterContributionsService:
    """Fixture providing a default RegisterContributionsService instance."""
    return RegisterContributionsService()


@pytest.fixture
def sample_manifest() -> PluginManifest:
    """Fixture providing a valid plugin manifest declaring all types."""
    return PluginManifest(
        id="com.haruquantai.example.alltypes",
        version="1.0.0",
        api_range=">=1.0.0,<2.0.0",
        types=tuple(PluginType),
    )


class MockAllTypesCallable:
    """Mock implementation implementing protocols for all 10 plugin types."""

    def evaluate(self, *_args: object) -> bool:
        return True

    def calculate(self, *_args: object) -> list[float]:
        return [1.0]

    def compute(self, *_args: object) -> float:
        return 1.0

    def filter(self, *_args: object) -> bool:
        return True

    def score(self, *_args: object) -> float:
        return 0.9

    def execute(self, *_args: object) -> dict[str, object]:
        return {}

    def fetch(self, *_args: object) -> list[object]:
        return []

    def run(self, *_args: object) -> None:
        pass

    def emit(self, *_args: object) -> None:
        pass

    def render(self, *_args: object) -> str:
        return "<div></div>"


def test_register_all_10_plugin_types(
    service: RegisterContributionsService,
    sample_manifest: PluginManifest,
) -> None:
    """Verify that all 10 supported PluginType enum members can be registered."""
    descriptors: list[PluginContributionDescriptor] = []
    implementations: dict[str, object] = {}
    mock_impl = MockAllTypesCallable()

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
        manifest=sample_manifest,
        contributions=tuple(descriptors),
        implementations=implementations,
    )

    assert result.is_successful is True
    assert len(result.contributions) == 10
    assert len(result.test_results) == 10
    assert all(tr.passed for tr in result.test_results)
    assert len(service.get_contributions()) == 10


def test_contract_test_failure_strict(
    sample_manifest: PluginManifest,
) -> None:
    """Verify strict contract testing raises PluginContractTestError."""
    service = RegisterContributionsService(
        config=PluginContributionsConfig(strict_contract_tests=True)
    )
    desc = PluginContributionDescriptor(
        plugin_id=sample_manifest.id,
        plugin_type=PluginType.BLOCK,
        contribution_id=f"{sample_manifest.id}.invalid_block",
        name="Invalid Block",
    )

    class BadImpl:
        pass

    with pytest.raises(PluginContractTestError, match="failed contract test"):
        service.register_contributions(
            manifest=sample_manifest,
            contributions=(desc,),
            implementations={desc.contribution_id: BadImpl()},
        )


def test_contract_test_failure_non_strict(
    sample_manifest: PluginManifest,
) -> None:
    """Verify non-strict mode records failures without raising."""
    service = RegisterContributionsService(
        config=PluginContributionsConfig(strict_contract_tests=False)
    )
    desc = PluginContributionDescriptor(
        plugin_id=sample_manifest.id,
        plugin_type=PluginType.INDICATOR,
        contribution_id=f"{sample_manifest.id}.invalid_indicator",
        name="Invalid Indicator",
    )

    class BadIndicator:
        pass

    result = service.register_contributions(
        manifest=sample_manifest,
        contributions=(desc,),
        implementations={desc.contribution_id: BadIndicator()},
    )

    assert result.is_successful is False
    assert len(result.errors) > 0
    assert len(service.get_contributions()) == 0


def test_validation_preconditions(
    service: RegisterContributionsService,
) -> None:
    """Verify boundary checks on manifest and contributions."""
    empty_manifest = PluginManifest(id="", version="1.0.0", api_range=">=1.0.0")
    with pytest.raises(
        PluginContributionError, match="Manifest must have a non-empty plugin ID"
    ):
        service.register_contributions(empty_manifest, ())

    # Exceeding max limits
    limited_service = RegisterContributionsService(
        config=PluginContributionsConfig(max_contributions_per_plugin=2)
    )
    manifest = PluginManifest(
        id="com.example.limited",
        version="1.0.0",
        api_range=">=1.0.0",
        types=(PluginType.BLOCK,),
    )
    c1 = PluginContributionDescriptor(
        plugin_id=manifest.id,
        plugin_type=PluginType.BLOCK,
        contribution_id="c1",
        name="C1",
    )
    c2 = PluginContributionDescriptor(
        plugin_id=manifest.id,
        plugin_type=PluginType.BLOCK,
        contribution_id="c2",
        name="C2",
    )
    c3 = PluginContributionDescriptor(
        plugin_id=manifest.id,
        plugin_type=PluginType.BLOCK,
        contribution_id="c3",
        name="C3",
    )
    with pytest.raises(PluginContributionError, match="exceeding maximum limit"):
        limited_service.register_contributions(manifest, (c1, c2, c3))

    # Mismatched plugin ID
    c_mismatch = PluginContributionDescriptor(
        plugin_id="other.plugin",
        plugin_type=PluginType.BLOCK,
        contribution_id="c_other",
        name="Other",
    )
    with pytest.raises(PluginContributionError, match="does not match manifest id"):
        service.register_contributions(manifest, (c_mismatch,))

    # Undeclared plugin type
    c_undeclared = PluginContributionDescriptor(
        plugin_id=manifest.id,
        plugin_type=PluginType.INDICATOR,
        contribution_id="c_ind",
        name="Ind",
    )
    with pytest.raises(
        PluginContributionError, match="is not declared in plugin manifest types"
    ):
        service.register_contributions(manifest, (c_undeclared,))


def test_trace_functions(
    sample_manifest: PluginManifest,
) -> None:
    """Verify trace functions for requirement bindings."""
    c = PluginContributionDescriptor(
        plugin_id=sample_manifest.id,
        plugin_type=PluginType.DATA_CONNECTOR,
        contribution_id=f"{sample_manifest.id}.feed",
        name="Market Feed",
    )
    service = RegisterContributionsService()

    res = fr_trc_plug_register_contributions_001(sample_manifest, (c,), service=service)
    assert res.is_successful is True

    items = fr_trc_plug_register_contributions_002(
        service, plugin_type=PluginType.DATA_CONNECTOR
    )
    assert len(items) == 1
    assert items[0].contribution_id == c.contribution_id

    res_legacy = fr_plug_register_plugin_contributions(sample_manifest, (c,))
    assert res_legacy.is_successful is True


def test_disposer_properties_and_edge_cases(
    service: RegisterContributionsService,
    sample_manifest: PluginManifest,
) -> None:
    """Verify disposer properties, repeated disposal idempotency, and nonexistent generation."""
    c = PluginContributionDescriptor(
        plugin_id=sample_manifest.id,
        plugin_type=PluginType.INDICATOR,
        contribution_id=f"{sample_manifest.id}.rsi_edge",
        name="RSI Edge",
    )
    result = service.register_contributions(sample_manifest, (c,))
    assert result.disposer is not None
    disposer = result.disposer
    assert disposer.plugin_id == sample_manifest.id
    assert disposer.generation == 1
    assert disposer.is_disposed is False

    # First disposal
    removed = disposer()
    assert removed == 1
    assert disposer.is_disposed is True

    # Second disposal returns 0 idempotently
    assert disposer.dispose() == 0
    assert disposer() == 0

    # Nonexistent generation returns 0
    assert service.dispose_generation("nonexistent", 999) == 0
    assert service.unregister_contributions("nonexistent") == 0
    assert service.get_contribution("nonexistent") is None


def test_extended_validation_and_branch_coverage(
    sample_manifest: PluginManifest,
) -> None:
    """Verify empty id, duplicate id in request, and limit exhaustion."""
    service = RegisterContributionsService(
        config=PluginContributionsConfig(max_contributions_per_plugin=2)
    )

    # Empty contribution ID
    c_empty_id = PluginContributionDescriptor(
        plugin_id=sample_manifest.id,
        plugin_type=PluginType.INDICATOR,
        contribution_id="",
        name="Empty ID",
    )
    with pytest.raises(
        PluginContributionError, match="Contribution ID cannot be empty"
    ):
        service.register_contributions(sample_manifest, (c_empty_id,))

    # Duplicate contribution ID in the same request
    c_dup = PluginContributionDescriptor(
        plugin_id=sample_manifest.id,
        plugin_type=PluginType.INDICATOR,
        contribution_id="dup.id",
        name="Dup 1",
    )
    c_dup_same = PluginContributionDescriptor(
        plugin_id=sample_manifest.id,
        plugin_type=PluginType.INDICATOR,
        contribution_id="dup.id",
        name="Dup 2",
    )
    with pytest.raises(
        PluginContributionError,
        match=r"Duplicate contribution ID 'dup\.id' in registration request",
    ):
        service.register_contributions(sample_manifest, (c_dup, c_dup_same))

    # Exceeding maximum limit
    c1 = PluginContributionDescriptor(
        plugin_id=sample_manifest.id,
        plugin_type=PluginType.INDICATOR,
        contribution_id="c1",
        name="C1",
    )
    c2 = PluginContributionDescriptor(
        plugin_id=sample_manifest.id,
        plugin_type=PluginType.INDICATOR,
        contribution_id="c2",
        name="C2",
    )
    c3 = PluginContributionDescriptor(
        plugin_id=sample_manifest.id,
        plugin_type=PluginType.INDICATOR,
        contribution_id="c3",
        name="C3",
    )
    with pytest.raises(PluginContributionError, match="exceeding maximum limit"):
        service.register_contributions(sample_manifest, (c1, c2, c3))


def test_usage_demonstration_scenario() -> None:
    """Verify that _usage.py scenarios execute successfully and cover demonstration code."""
    from app.services.plugins.register_contributions._usage import (
        MockBeta,
        MockRSI,
        MockSharpe,
        _run_usage_example,
    )

    # Cover mock compute/calculate calls
    rsi = MockRSI()
    assert rsi.calculate([1.0, 2.0]) == [50.0, 50.0]
    sharpe = MockSharpe()
    assert sharpe.compute([0.1, 0.2]) == 1.85
    assert sharpe.compute([]) == 0.0
    beta = MockBeta()
    assert beta.compute([0.1]) == 1.05
    assert beta.compute([]) == 0.0

    _run_usage_example()
