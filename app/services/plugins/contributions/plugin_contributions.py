"""Plugin contribution registration and contract testing.

Purpose:
    Register typed plugin contribution capabilities across all supported plugin
    types and execute contract tests before stable enablement per §21.4.

Key capabilities:
    * Register contribution descriptors for BLOCK, INDICATOR, METRIC, FILTER,
      FITNESS, RESEARCH_METHOD, DATA_CONNECTOR, PROJECT_TASK, SOURCE_EMITTER,
      and RESULT_PANEL.
    * Enforce that contributions match declared manifest plugin types and limits.
    * Run type-specific contract tests validating interface contracts and schemas.
    * Query registered contributions by type or unique identifier.
    * Unregister contributions transactionally upon plugin withdrawal.

Python API usage:
    service = RegisterContributionsService()
    result = service.register_contributions(manifest, contributions)

CLI usage:
    uv run python -m app.services.plugins.contributions.plugin_contributions
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.contracts.plugins.errors import (
    PluginContractTestError,
    PluginContributionError,
)
from app.contracts.plugins.models import (
    ContributionRegistrationResult,
    ContributionTestResult,
    PluginContributionDescriptor,
    PluginManifest,
    PluginType,
)
from app.services.plugins.contributions.config import PluginContributionsConfig

if TYPE_CHECKING:
    from app.kernel.events import EventBus


def _test_block_contract(
    contribution: PluginContributionDescriptor,
    implementation: object | None,
) -> tuple[bool, str, list[str]]:
    """Test BLOCK plugin contract.

    Args:
        contribution: Descriptor to evaluate.
        implementation: Optional implementation object.

    Returns:
        Tuple of (passed, details message, list of error strings).
    """
    errors: list[str] = []
    if not contribution.name:
        errors.append("BLOCK contribution requires non-empty name")
    if implementation is not None and not callable(
        getattr(implementation, "evaluate", implementation)
    ):
        errors.append("BLOCK implementation must be callable or provide 'evaluate'")
    passed = len(errors) == 0
    details = "BLOCK contract test passed" if passed else "BLOCK validation failed"
    return passed, details, errors


def _test_indicator_contract(
    contribution: PluginContributionDescriptor,
    implementation: object | None,
) -> tuple[bool, str, list[str]]:
    """Test INDICATOR plugin contract.

    Args:
        contribution: Descriptor to evaluate.
        implementation: Optional implementation object.

    Returns:
        Tuple of (passed, details message, list of error strings).
    """
    errors: list[str] = []
    if not contribution.name:
        errors.append("INDICATOR contribution requires non-empty name")
    if implementation is not None and not callable(
        getattr(implementation, "calculate", implementation)
    ):
        errors.append(
            "INDICATOR implementation must be callable or provide 'calculate'"
        )
    passed = len(errors) == 0
    details = (
        "INDICATOR contract test passed" if passed else "INDICATOR validation failed"
    )
    return passed, details, errors


def _test_metric_contract(
    contribution: PluginContributionDescriptor,
    implementation: object | None,
) -> tuple[bool, str, list[str]]:
    """Test METRIC plugin contract.

    Args:
        contribution: Descriptor to evaluate.
        implementation: Optional implementation object.

    Returns:
        Tuple of (passed, details message, list of error strings).
    """
    errors: list[str] = []
    if not contribution.name:
        errors.append("METRIC contribution requires non-empty name")
    if implementation is not None and not callable(
        getattr(implementation, "compute", implementation)
    ):
        errors.append("METRIC implementation must be callable or provide 'compute'")
    passed = len(errors) == 0
    details = "METRIC contract test passed" if passed else "METRIC validation failed"
    return passed, details, errors


def _test_filter_contract(
    contribution: PluginContributionDescriptor,
    implementation: object | None,
) -> tuple[bool, str, list[str]]:
    """Test FILTER plugin contract.

    Args:
        contribution: Descriptor to evaluate.
        implementation: Optional implementation object.

    Returns:
        Tuple of (passed, details message, list of error strings).
    """
    errors: list[str] = []
    if not contribution.name:
        errors.append("FILTER contribution requires non-empty name")
    if implementation is not None and not callable(
        getattr(implementation, "filter", implementation)
    ):
        errors.append("FILTER implementation must be callable or provide 'filter'")
    passed = len(errors) == 0
    details = "FILTER contract test passed" if passed else "FILTER validation failed"
    return passed, details, errors


def _test_generic_contract(
    contribution: PluginContributionDescriptor,
    _implementation: object | None,
) -> tuple[bool, str, list[str]]:
    """Test generic plugin contribution types.

    Args:
        contribution: Descriptor to evaluate.
        _implementation: Optional implementation object.

    Returns:
        Tuple of (passed, details message, list of error strings).
    """
    errors: list[str] = []
    if not contribution.name:
        errors.append(f"{contribution.plugin_type} requires non-empty name")
    if not contribution.contribution_id:
        errors.append(f"{contribution.plugin_type} requires valid contribution_id")
    passed = len(errors) == 0
    details = (
        f"{contribution.plugin_type} contract test passed"
        if passed
        else f"{contribution.plugin_type} validation failed"
    )
    return passed, details, errors


def _run_type_contract_test(
    contribution: PluginContributionDescriptor,
    implementation: object | None,
) -> ContributionTestResult:
    """Dispatch contract verification based on contribution PluginType.

    Args:
        contribution: The contribution descriptor.
        implementation: Optional implementation object.

    Returns:
        ContributionTestResult describing the outcome.
    """
    ptype = contribution.plugin_type
    if ptype == PluginType.BLOCK:
        passed, details, errors = _test_block_contract(contribution, implementation)
    elif ptype == PluginType.INDICATOR:
        passed, details, errors = _test_indicator_contract(contribution, implementation)
    elif ptype == PluginType.METRIC:
        passed, details, errors = _test_metric_contract(contribution, implementation)
    elif ptype == PluginType.FILTER:
        passed, details, errors = _test_filter_contract(contribution, implementation)
    else:
        passed, details, errors = _test_generic_contract(contribution, implementation)

    return ContributionTestResult(
        contribution_id=contribution.contribution_id,
        plugin_type=ptype,
        passed=passed,
        details=details,
        errors=tuple(errors),
    )


class RegisterContributionsService:
    """Service providing typed plugin contribution registration and testing."""

    def __init__(
        self,
        config: PluginContributionsConfig | None = None,
        event_bus: EventBus | None = None,
    ) -> None:
        """Initialize the service.

        Args:
            config: Optional configuration limits.
            event_bus: Optional kernel event bus for notification publication.
        """
        self._config = config or PluginContributionsConfig()
        self._event_bus = event_bus
        self._contributions: dict[str, PluginContributionDescriptor] = {}
        self._by_plugin: dict[str, set[str]] = {}
        self._by_type: dict[PluginType, set[str]] = {
            ptype: set() for ptype in PluginType
        }

    def register_contributions(
        self,
        manifest: PluginManifest,
        contributions: tuple[PluginContributionDescriptor, ...],
        implementations: dict[str, object] | None = None,
    ) -> ContributionRegistrationResult:
        """Register typed contributions declared by a plugin manifest.

        Args:
            manifest: Validated plugin manifest.
            contributions: Descriptors of contributions to register.
            implementations: Optional mapping of contribution_id to implementation.

        Returns:
            ContributionRegistrationResult with registration status.

        Raises:
            PluginContributionError: If validation or boundary rules fail.
            PluginContractTestError: If strict contract verification fails.
        """
        self._validate_registration_preconditions(manifest, contributions)

        impl_map = implementations or {}
        test_results: list[ContributionTestResult] = []
        all_errors: list[str] = []

        for contrib in contributions:
            impl = impl_map.get(contrib.contribution_id)
            test_res = self.run_contract_test(contrib, impl)
            test_results.append(test_res)

            if not test_res.passed:
                all_errors.extend(test_res.errors)
                if self._config.strict_contract_tests:
                    joined = "; ".join(test_res.errors)
                    msg = (
                        f"Contribution '{contrib.contribution_id}' failed contract "
                        f"test: {joined}"
                    )
                    raise PluginContractTestError(msg)

        if all_errors:
            return ContributionRegistrationResult(
                plugin_id=manifest.id,
                contributions=(),
                test_results=tuple(test_results),
                is_successful=False,
                errors=tuple(all_errors),
            )

        self._store_contributions(manifest.id, contributions)

        return ContributionRegistrationResult(
            plugin_id=manifest.id,
            contributions=contributions,
            test_results=tuple(test_results),
            is_successful=True,
            errors=(),
        )

    def _validate_registration_preconditions(
        self,
        manifest: PluginManifest,
        contributions: tuple[PluginContributionDescriptor, ...],
    ) -> None:
        """Validate manifest and contribution limits before registration.

        Args:
            manifest: The plugin manifest.
            contributions: Descriptors to validate.

        Raises:
            PluginContributionError: If preconditions are violated.
        """
        if not manifest.id:
            msg = "Manifest must have a non-empty plugin ID"
            raise PluginContributionError(msg)

        if len(contributions) > self._config.max_contributions_per_plugin:
            msg = (
                f"Plugin declares {len(contributions)} contributions, exceeding "
                f"maximum limit of {self._config.max_contributions_per_plugin}"
            )
            raise PluginContributionError(msg)

        for contrib in contributions:
            if contrib.plugin_id != manifest.id:
                msg = (
                    f"Contribution plugin_id '{contrib.plugin_id}' does not match "
                    f"manifest id '{manifest.id}'"
                )
                raise PluginContributionError(msg)

            if contrib.plugin_type not in manifest.types:
                msg = (
                    f"Contribution type '{contrib.plugin_type}' is not declared "
                    f"in plugin manifest types: {[t.value for t in manifest.types]}"
                )
                raise PluginContributionError(msg)

            if not contrib.contribution_id:
                msg = "Contribution ID cannot be empty"
                raise PluginContributionError(msg)

    def _store_contributions(
        self,
        plugin_id: str,
        contributions: tuple[PluginContributionDescriptor, ...],
    ) -> None:
        """Commit validated contribution descriptors to memory store.

        Args:
            plugin_id: Identifier of the owning plugin.
            contributions: Validated descriptors to record.
        """
        plugin_set = self._by_plugin.setdefault(plugin_id, set())
        for contrib in contributions:
            cid = contrib.contribution_id
            self._contributions[cid] = contrib
            plugin_set.add(cid)
            self._by_type[contrib.plugin_type].add(cid)

    def unregister_contributions(self, plugin_id: str) -> int:
        """Unregister all contributions associated with a plugin ID.

        Args:
            plugin_id: Identifier of the plugin to withdraw.

        Returns:
            Count of removed contribution descriptors.
        """
        cids = self._by_plugin.pop(plugin_id, set())
        for cid in cids:
            contrib = self._contributions.pop(cid, None)
            if contrib is not None:
                self._by_type[contrib.plugin_type].discard(cid)
        return len(cids)

    def get_contributions(
        self, plugin_type: PluginType | None = None
    ) -> tuple[PluginContributionDescriptor, ...]:
        """Query currently registered plugin contributions.

        Args:
            plugin_type: Optional filter by PluginType.

        Returns:
            Tuple of active contribution descriptors matching criteria.
        """
        if plugin_type is not None:
            cids = self._by_type.get(plugin_type, set())
            return tuple(
                self._contributions[cid]
                for cid in sorted(cids)
                if cid in self._contributions
            )

        return tuple(self._contributions[cid] for cid in sorted(self._contributions))

    def get_contribution(
        self, contribution_id: str
    ) -> PluginContributionDescriptor | None:
        """Retrieve a registered contribution by its ID.

        Args:
            contribution_id: Unique contribution identifier.

        Returns:
            PluginContributionDescriptor if found, or None.
        """
        return self._contributions.get(contribution_id)

    def run_contract_test(
        self,
        contribution: PluginContributionDescriptor,
        implementation: object | None = None,
    ) -> ContributionTestResult:
        """Execute type-specific contract tests against a contribution.

        Args:
            contribution: Contribution descriptor to test.
            implementation: Optional concrete implementation object or mock.

        Returns:
            ContributionTestResult indicating whether contract rules were satisfied.
        """
        return _run_type_contract_test(contribution, implementation)


def fr_plug_register_plugin_contributions(
    manifest: PluginManifest,
    contributions: tuple[PluginContributionDescriptor, ...],
    config: PluginContributionsConfig | None = None,
    implementations: dict[str, object] | None = None,
) -> ContributionRegistrationResult:
    """Requirement implementation trace for FR-PLUG-REGISTER_PLUGIN_CONTRIBUTIONS.

    Args:
        manifest: Validated plugin manifest.
        contributions: Tuple of contribution descriptors.
        config: Optional configuration limits.
        implementations: Optional implementations map.

    Returns:
        ContributionRegistrationResult outcome.
    """
    service = RegisterContributionsService(config=config)
    return service.register_contributions(
        manifest, contributions, implementations=implementations
    )


def _run_usage_example() -> None:
    """Execute the bounded public usage demonstration and verification harness.

    Raises:
        RuntimeError: If verification assertion fails.
    """
    print("=== Demonstrating FR-PLUG-REGISTER_PLUGIN_CONTRIBUTIONS Usage ===")
    service = RegisterContributionsService()

    manifest = PluginManifest(
        id="com.haruquantai.sample.analytics",
        version="1.0.0",
        api_range=">=1.0.0,<2.0.0",
        types=(PluginType.INDICATOR, PluginType.METRIC, PluginType.FILTER),
    )

    indicator_desc = PluginContributionDescriptor(
        plugin_id=manifest.id,
        plugin_type=PluginType.INDICATOR,
        contribution_id="com.haruquantai.sample.analytics.rsi",
        name="Relative Strength Index",
        description="Calculates standard 14-period RSI.",
    )

    metric_desc = PluginContributionDescriptor(
        plugin_id=manifest.id,
        plugin_type=PluginType.METRIC,
        contribution_id="com.haruquantai.sample.analytics.sharpe",
        name="Sharpe Ratio Extension",
        description="Computes risk-adjusted returns metric.",
    )

    class MockRSI:
        def calculate(self, series: list[float]) -> list[float]:
            return [50.0] * len(series)

    class MockSharpe:
        def compute(self, returns: list[float]) -> float:
            return sum(returns) / max(len(returns), 1)

    implementations = {
        indicator_desc.contribution_id: MockRSI(),
        metric_desc.contribution_id: MockSharpe(),
    }

    result = service.register_contributions(
        manifest=manifest,
        contributions=(indicator_desc, metric_desc),
        implementations=implementations,
    )

    if not result.is_successful:
        msg = f"Registration failed unexpectedly: {result.errors}"
        raise RuntimeError(msg)

    print(
        f"1. Successfully registered {len(result.contributions)} contributions for "
        f"{manifest.id}"
    )

    indicators = service.get_contributions(PluginType.INDICATOR)
    print(f"2. Active INDICATOR contributions: {[c.name for c in indicators]}")

    metrics = service.get_contributions(PluginType.METRIC)
    print(f"3. Active METRIC contributions: {[c.name for c in metrics]}")

    removed = service.unregister_contributions(manifest.id)
    print(f"4. Successfully unregistered {removed} contributions for {manifest.id}")
    print("=== Usage demonstration completed successfully ===")


if __name__ == "__main__":
    _run_usage_example()
