"""Plugin contribution registration, exact generation tracking, and contract testing.

Purpose:
    Register typed plugin contribution capabilities across all supported plugin
    types, track exact owner-scoped generations, return disposer handles, enforce
    duplicate/conflict rejection, and execute contract tests before stable
    enablement per FR-TRC-PLUG-REGISTER_CONTRIBUTIONS-001 and 002.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.composition.logging import get_logger
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
from app.services.plugins.register_contributions.config import (
    PluginContributionsConfig,
)

if TYPE_CHECKING:
    from app.kernel.events import EventBus

logger = get_logger(__name__)


class ContributionDisposer:
    """Disposer handle that unregisters a specific generation of contributions."""

    def __init__(
        self,
        service: RegisterContributionsService,
        plugin_id: str,
        generation: int,
    ) -> None:
        """Initialize the disposer handle.

        Args:
            service: Owning RegisterContributionsService instance.
            plugin_id: Identifier of the owning plugin.
            generation: Specific registration generation to remove.
        """
        self._service = service
        self._plugin_id = plugin_id
        self._generation = generation
        self._disposed = False

    @property
    def plugin_id(self) -> str:
        """Return the plugin identifier bound to this disposer."""
        return self._plugin_id

    @property
    def generation(self) -> int:
        """Return the generation number bound to this disposer."""
        return self._generation

    @property
    def is_disposed(self) -> bool:
        """Return True if this disposer has already executed."""
        return self._disposed

    def __call__(self) -> int:
        """Dispose the bound generation when invoked as a callable.

        Returns:
            Count of removed contribution descriptors.
        """
        return self.dispose()

    def dispose(self) -> int:
        """Dispose the bound generation.

        Returns:
            Count of removed contribution descriptors.
        """
        if self._disposed:
            return 0
        self._disposed = True
        return self._service.dispose_generation(self._plugin_id, self._generation)


def _test_block_contract(
    contribution: PluginContributionDescriptor,
    implementation: object | None,
) -> tuple[bool, str, list[str]]:
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


def _test_fitness_contract(
    contribution: PluginContributionDescriptor,
    implementation: object | None,
) -> tuple[bool, str, list[str]]:
    errors: list[str] = []
    if not contribution.name:
        errors.append("FITNESS contribution requires non-empty name")
    if implementation is not None and not callable(
        getattr(implementation, "score", implementation)
    ):
        errors.append("FITNESS implementation must be callable or provide 'score'")
    passed = len(errors) == 0
    details = "FITNESS contract test passed" if passed else "FITNESS validation failed"
    return passed, details, errors


def _test_research_method_contract(
    contribution: PluginContributionDescriptor,
    implementation: object | None,
) -> tuple[bool, str, list[str]]:
    errors: list[str] = []
    if not contribution.name:
        errors.append("RESEARCH_METHOD contribution requires non-empty name")
    if implementation is not None and not callable(
        getattr(implementation, "execute", implementation)
    ):
        errors.append(
            "RESEARCH_METHOD implementation must be callable or provide 'execute'"
        )
    passed = len(errors) == 0
    details = (
        "RESEARCH_METHOD contract test passed"
        if passed
        else "RESEARCH_METHOD validation failed"
    )
    return passed, details, errors


def _test_data_connector_contract(
    contribution: PluginContributionDescriptor,
    implementation: object | None,
) -> tuple[bool, str, list[str]]:
    errors: list[str] = []
    if not contribution.name:
        errors.append("DATA_CONNECTOR contribution requires non-empty name")
    if implementation is not None and not callable(
        getattr(implementation, "fetch", implementation)
    ):
        errors.append(
            "DATA_CONNECTOR implementation must be callable or provide 'fetch'"
        )
    passed = len(errors) == 0
    details = (
        "DATA_CONNECTOR contract test passed"
        if passed
        else "DATA_CONNECTOR validation failed"
    )
    return passed, details, errors


def _test_project_task_contract(
    contribution: PluginContributionDescriptor,
    implementation: object | None,
) -> tuple[bool, str, list[str]]:
    errors: list[str] = []
    if not contribution.name:
        errors.append("PROJECT_TASK contribution requires non-empty name")
    if implementation is not None and not callable(
        getattr(implementation, "run", implementation)
    ):
        errors.append("PROJECT_TASK implementation must be callable or provide 'run'")
    passed = len(errors) == 0
    details = (
        "PROJECT_TASK contract test passed"
        if passed
        else "PROJECT_TASK validation failed"
    )
    return passed, details, errors


def _test_source_emitter_contract(
    contribution: PluginContributionDescriptor,
    implementation: object | None,
) -> tuple[bool, str, list[str]]:
    errors: list[str] = []
    if not contribution.name:
        errors.append("SOURCE_EMITTER contribution requires non-empty name")
    if implementation is not None and not callable(
        getattr(implementation, "emit", implementation)
    ):
        errors.append(
            "SOURCE_EMITTER implementation must be callable or provide 'emit'"
        )
    passed = len(errors) == 0
    details = (
        "SOURCE_EMITTER contract test passed"
        if passed
        else "SOURCE_EMITTER validation failed"
    )
    return passed, details, errors


def _test_result_panel_contract(
    contribution: PluginContributionDescriptor,
    implementation: object | None,
) -> tuple[bool, str, list[str]]:
    errors: list[str] = []
    if not contribution.name:
        errors.append("RESULT_PANEL contribution requires non-empty name")
    if implementation is not None and not callable(
        getattr(implementation, "render", implementation)
    ):
        errors.append(
            "RESULT_PANEL implementation must be callable or provide 'render'"
        )
    passed = len(errors) == 0
    details = (
        "RESULT_PANEL contract test passed"
        if passed
        else "RESULT_PANEL validation failed"
    )
    return passed, details, errors


def _test_generic_contract(
    contribution: PluginContributionDescriptor,
    _implementation: object | None,
) -> tuple[bool, str, list[str]]:
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


_CONTRACT_TEST_DISPATCH = {
    PluginType.BLOCK: _test_block_contract,
    PluginType.INDICATOR: _test_indicator_contract,
    PluginType.METRIC: _test_metric_contract,
    PluginType.FILTER: _test_filter_contract,
    PluginType.FITNESS: _test_fitness_contract,
    PluginType.RESEARCH_METHOD: _test_research_method_contract,
    PluginType.DATA_CONNECTOR: _test_data_connector_contract,
    PluginType.PROJECT_TASK: _test_project_task_contract,
    PluginType.SOURCE_EMITTER: _test_source_emitter_contract,
    PluginType.RESULT_PANEL: _test_result_panel_contract,
}


def _run_type_contract_test(
    contribution: PluginContributionDescriptor,
    implementation: object | None,
) -> ContributionTestResult:
    ptype = contribution.plugin_type
    test_fn = _CONTRACT_TEST_DISPATCH.get(ptype, _test_generic_contract)
    passed, details, errors = test_fn(contribution, implementation)

    return ContributionTestResult(
        contribution_id=contribution.contribution_id,
        plugin_type=ptype,
        passed=passed,
        details=details,
        errors=tuple(errors),
    )


class RegisterContributionsService:
    """Service providing typed plugin contribution tracking and disposal."""

    def __init__(
        self,
        config: PluginContributionsConfig | None = None,
        event_bus: EventBus | None = None,
    ) -> None:
        """Initialize the service.

        Args:
            config: Optional configuration limits.
            event_bus: Optional kernel event bus.
        """
        self._config = config or PluginContributionsConfig()
        self._event_bus = event_bus
        self._contributions: dict[str, PluginContributionDescriptor] = {}
        self._by_plugin: dict[str, set[str]] = {}
        self._by_plugin_generation: dict[tuple[str, int], set[str]] = {}
        self._by_type: dict[PluginType, set[str]] = {
            ptype: set() for ptype in PluginType
        }
        self._generations: dict[str, int] = {}

    def register_contributions(
        self,
        manifest: PluginManifest,
        contributions: tuple[PluginContributionDescriptor, ...],
        implementations: dict[str, object] | None = None,
    ) -> ContributionRegistrationResult:
        """Register typed contributions declared by a plugin manifest.

        Enforces exact ID/version/generation tracking, rejects duplicate or
        conflicting IDs, executes contract tests, and returns a disposer handle.

        Args:
            manifest: Validated plugin manifest.
            contributions: Descriptors of contributions to register.
            implementations: Optional mapping of contribution_id to implementation.

        Returns:
            ContributionRegistrationResult containing recorded descriptors,
            generation number, and disposer handle.

        Raises:
            PluginContributionError: If boundary, duplicate, or conflict rules fail.
            PluginContractTestError: If strict contract verification fails.
        """
        self._validate_registration_preconditions(manifest, contributions)

        # Monotonically increment generation for this plugin
        current_gen = self._generations.get(manifest.id, 0) + 1
        self._generations[manifest.id] = current_gen

        # Ensure descriptors carry exact version and generation
        versioned_contributions: list[PluginContributionDescriptor] = []
        for c in contributions:
            versioned = PluginContributionDescriptor(
                plugin_id=c.plugin_id,
                plugin_type=c.plugin_type,
                contribution_id=c.contribution_id,
                name=c.name,
                description=c.description,
                schema_ref=c.schema_ref,
                metadata=dict(c.metadata),
                version=manifest.version,
                generation=current_gen,
            )
            versioned_contributions.append(versioned)

        impl_map = implementations or {}
        test_results: list[ContributionTestResult] = []
        all_errors: list[str] = []

        for contrib in versioned_contributions:
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
                    logger.warning(
                        "Contribution contract test failed under strict policy",
                        contribution_id=contrib.contribution_id,
                        plugin_id=manifest.id,
                        errors=test_res.errors,
                        event="plugins.register_contributions.contract_test_failed",
                    )
                    raise PluginContractTestError(msg)

        if all_errors:
            logger.warning(
                "Contribution registration failed with contract errors",
                plugin_id=manifest.id,
                errors=all_errors,
                event="plugins.register_contributions.registration_failed",
            )
            return ContributionRegistrationResult(
                plugin_id=manifest.id,
                contributions=(),
                test_results=tuple(test_results),
                is_successful=False,
                errors=tuple(all_errors),
                generation=current_gen,
                disposer=None,
            )

        recorded_tuple = tuple(versioned_contributions)
        self._store_contributions(manifest.id, current_gen, recorded_tuple)
        disposer = ContributionDisposer(self, manifest.id, current_gen)

        logger.info(
            "Registered plugin contributions generation",
            plugin_id=manifest.id,
            generation=current_gen,
            count=len(recorded_tuple),
            event="plugins.register_contributions.generation_registered",
        )

        return ContributionRegistrationResult(
            plugin_id=manifest.id,
            contributions=recorded_tuple,
            test_results=tuple(test_results),
            is_successful=True,
            errors=(),
            generation=current_gen,
            disposer=disposer,
        )

    def _validate_registration_preconditions(
        self,
        manifest: PluginManifest,
        contributions: tuple[PluginContributionDescriptor, ...],
    ) -> None:
        if not manifest.id:
            msg = "Manifest must have a non-empty plugin ID"
            raise PluginContributionError(msg)

        if len(contributions) > self._config.max_contributions_per_plugin:
            msg = (
                f"Plugin declares {len(contributions)} contributions, exceeding "
                f"maximum limit of {self._config.max_contributions_per_plugin}"
            )
            raise PluginContributionError(msg)

        seen_in_request: set[str] = set()
        for contrib in contributions:
            if not contrib.contribution_id:
                msg = "Contribution ID cannot be empty"
                raise PluginContributionError(msg)

            if contrib.contribution_id in seen_in_request:
                msg = (
                    f"Duplicate contribution ID '{contrib.contribution_id}' in "
                    f"registration request"
                )
                logger.warning(
                    "Duplicate contribution ID in registration request rejected",
                    contribution_id=contrib.contribution_id,
                    plugin_id=manifest.id,
                    event="plugins.register_contributions.duplicate_in_request",
                )
                raise PluginContributionError(msg)
            seen_in_request.add(contrib.contribution_id)

            # Enforce rejection of duplicate/conflicting active registration
            if contrib.contribution_id in self._contributions:
                existing = self._contributions[contrib.contribution_id]
                msg = (
                    f"Conflicting contribution registration: ID "
                    f"'{contrib.contribution_id}' is already registered by "
                    f"plugin '{existing.plugin_id}' (generation "
                    f"{existing.generation})"
                )
                logger.warning(
                    "Conflicting contribution registration rejected",
                    contribution_id=contrib.contribution_id,
                    existing_plugin_id=existing.plugin_id,
                    existing_generation=existing.generation,
                    requested_plugin_id=manifest.id,
                    event="plugins.register_contributions.conflict_rejected",
                )
                raise PluginContributionError(msg)

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

    def _store_contributions(
        self,
        plugin_id: str,
        generation: int,
        contributions: tuple[PluginContributionDescriptor, ...],
    ) -> None:
        plugin_set = self._by_plugin.setdefault(plugin_id, set())
        gen_set = self._by_plugin_generation.setdefault((plugin_id, generation), set())

        for contrib in contributions:
            cid = contrib.contribution_id
            self._contributions[cid] = contrib
            plugin_set.add(cid)
            gen_set.add(cid)
            self._by_type[contrib.plugin_type].add(cid)

    def dispose_generation(self, plugin_id: str, generation: int) -> int:
        """Dispose only contributions belonging to a specific generation of a plugin.

        Removes only its own generation, not all matching names or later generations.

        Args:
            plugin_id: Identifier of the owning plugin.
            generation: Specific registration generation to remove.

        Returns:
            Count of removed contribution descriptors.
        """
        cids = self._by_plugin_generation.pop((plugin_id, generation), set())
        if not cids:
            return 0

        plugin_set = self._by_plugin.get(plugin_id, set())
        for cid in cids:
            contrib = self._contributions.pop(cid, None)
            plugin_set.discard(cid)
            if contrib is not None:
                self._by_type[contrib.plugin_type].discard(cid)

        if not plugin_set and plugin_id in self._by_plugin:
            self._by_plugin.pop(plugin_id, None)

        logger.info(
            "Disposed plugin contributions generation",
            plugin_id=plugin_id,
            generation=generation,
            count=len(cids),
            event="plugins.register_contributions.generation_disposed",
        )
        return len(cids)

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

        # Clear all generation keys for this plugin
        to_delete = [k for k in self._by_plugin_generation if k[0] == plugin_id]
        for k in to_delete:
            self._by_plugin_generation.pop(k, None)

        logger.info(
            "Unregistered all contributions for plugin",
            plugin_id=plugin_id,
            count=len(cids),
            event="plugins.register_contributions.plugin_unregistered",
        )
        return len(cids)

    def get_contributions(
        self, plugin_type: PluginType | None = None
    ) -> tuple[PluginContributionDescriptor, ...]:
        """Query currently registered plugin contributions in deterministic order.

        Args:
            plugin_type: Optional filter by PluginType.

        Returns:
            Tuple of active contribution descriptors deterministically sorted
            by contribution_id.
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
        """Retrieve an active registered contribution by its ID.

        Args:
            contribution_id: Unique contribution identifier.

        Returns:
            PluginContributionDescriptor if active, or None.
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


def fr_trc_plug_register_contributions_001(
    manifest: PluginManifest,
    contributions: tuple[PluginContributionDescriptor, ...],
    service: RegisterContributionsService | None = None,
    implementations: dict[str, object] | None = None,
) -> ContributionRegistrationResult:
    """Trace implementation for FR-TRC-PLUG-REGISTER_CONTRIBUTIONS-001.

    Register immutable owner-scoped contributions with exact ID/version/generation
    and return a disposer handle. Rejects duplicate/conflicting registrations.

    Returns:
        ContributionRegistrationResult with registration status and disposer handle.
    """
    svc = service or RegisterContributionsService()
    return svc.register_contributions(
        manifest, contributions, implementations=implementations
    )


def fr_trc_plug_register_contributions_002(
    service: RegisterContributionsService,
    plugin_type: PluginType | None = None,
) -> tuple[PluginContributionDescriptor, ...]:
    """Trace implementation for FR-TRC-PLUG-REGISTER_CONTRIBUTIONS-002.

    Expose compatible contributions deterministically and withdraw them on
    removal/replacement without stale global state.

    Returns:
        Tuple of registered contribution descriptors in deterministic order.
    """
    return service.get_contributions(plugin_type=plugin_type)


def fr_plug_register_plugin_contributions(
    manifest: PluginManifest,
    contributions: tuple[PluginContributionDescriptor, ...],
    config: PluginContributionsConfig | None = None,
    implementations: dict[str, object] | None = None,
) -> ContributionRegistrationResult:
    """Legacy requirement trace alias.

    Returns:
        ContributionRegistrationResult outcome.
    """
    svc = RegisterContributionsService(config=config)
    return svc.register_contributions(
        manifest, contributions, implementations=implementations
    )
