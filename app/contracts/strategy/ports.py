"""Public capability protocols (ports) for Strategy capabilities."""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    from app.contracts.strategy.errors import StrategyFailure
    from app.contracts.strategy.models import (
        CatalogBlocksRequest,
        CatalogBlocksSuccess,
        ConfigureChartsRequest,
        ConfigureChartsSuccess,
        DefineArchitecturesRequest,
        DefineArchitecturesSuccess,
        DefineAstRequest,
        DefineAstSuccess,
        DefineIndicatorsRequest,
        DefineIndicatorsSuccess,
        EditTemplatesRequest,
        EditTemplatesSuccess,
        ExchangeStrategiesRequest,
        ExchangeStrategiesSuccess,
        ExtendPluginNodesRequest,
        ExtendPluginNodesSuccess,
        GenerateCodeRequest,
        GenerateCodeSuccess,
        GenerateMql5Request,
        GenerateMql5Success,
        GenerateTargetsRequest,
        GenerateTargetsSuccess,
        ModelAtmExitsRequest,
        ModelAtmExitsSuccess,
        VersionStrategiesRequest,
        VersionStrategiesSuccess,
    )


@runtime_checkable
class DefineAstCapability(Protocol):
    """Capability protocol for canonical typed AST operations."""

    async def define_ast(
        self,
        request: DefineAstRequest,
    ) -> DefineAstSuccess | StrategyFailure:
        """Normalize and validate canonical strategy ASTs.

        Args:
            request: Operation-discriminated canonical AST request.

        Returns:
            The normalized AST or the full validation report on success,
            otherwise a structured strategy failure.
        """
        ...


@runtime_checkable
class CatalogBlocksCapability(Protocol):
    """Capability protocol for block and parameter catalogue operations."""

    async def catalog_blocks(
        self,
        request: CatalogBlocksRequest,
    ) -> CatalogBlocksSuccess | StrategyFailure:
        """Catalog, describe, and compatibility-filter block definitions.

        Args:
            request: Operation-discriminated block catalogue request.

        Returns:
            The matching block definitions and parameter definitions on
            success, otherwise a structured strategy failure.
        """
        ...


@runtime_checkable
class ConfigureChartsCapability(Protocol):
    """Capability protocol for charts, direction, and visibility operations."""

    async def configure_charts(
        self,
        request: ConfigureChartsRequest,
    ) -> ConfigureChartsSuccess | StrategyFailure:
        """Bind charts, trade direction, and observable series shifts.

        Args:
            request: Operation-discriminated charts, direction, and
                visibility request.

        Returns:
            The chart set, direction policy, or visibility policy on
            success, otherwise a structured strategy failure.
        """
        ...


@runtime_checkable
class VersionStrategiesCapability(Protocol):
    """Capability protocol for strategy versioning operations."""

    async def version_strategies(
        self,
        request: VersionStrategiesRequest,
    ) -> VersionStrategiesSuccess | StrategyFailure:
        """Create drafts and commit or snapshot immutable strategy versions.

        Args:
            request: Operation-discriminated strategy versioning request.

        Returns:
            The draft or committed strategy version on success, otherwise a
            structured strategy failure.
        """
        ...


@runtime_checkable
class EditTemplatesCapability(Protocol):
    """Capability protocol for strategy template operations."""

    async def edit_templates(
        self,
        request: EditTemplatesRequest,
    ) -> EditTemplatesSuccess | StrategyFailure:
        """Define strategy templates and instantiate them into versions.

        Args:
            request: Operation-discriminated template request.

        Returns:
            The defined template or the instantiated version identity on
            success, otherwise a structured strategy failure.
        """
        ...


@runtime_checkable
class ExchangeStrategiesCapability(Protocol):
    """Capability protocol for strategy interchange operations."""

    async def exchange_strategies(
        self,
        request: ExchangeStrategiesRequest,
    ) -> ExchangeStrategiesSuccess | StrategyFailure:
        """Export and import native and legacy strategy packages.

        Args:
            request: Operation-discriminated strategy interchange request.

        Returns:
            The exported package or the imported version identity on
            success, otherwise a structured strategy failure.
        """
        ...


@runtime_checkable
class DefineArchitecturesCapability(Protocol):
    """Capability protocol for architecture and random group operations."""

    async def define_architectures(
        self,
        request: DefineArchitecturesRequest,
    ) -> DefineArchitecturesSuccess | StrategyFailure:
        """Define architectures, random groups, and opposite mappings.

        Args:
            request: Operation-discriminated architecture and mapping
                request.

        Returns:
            The architecture, random group, or opposite map on success,
            otherwise a structured strategy failure.
        """
        ...


@runtime_checkable
class DefineIndicatorsCapability(Protocol):
    """Capability protocol for indicator definition operations."""

    async def define_indicators(
        self,
        request: DefineIndicatorsRequest,
    ) -> DefineIndicatorsSuccess | StrategyFailure:
        """Define builtin and external indicator definitions.

        Args:
            request: Operation-discriminated indicator request.

        Returns:
            The indicator or external indicator definition on success,
            otherwise a structured strategy failure.
        """
        ...


@runtime_checkable
class ModelAtmExitsCapability(Protocol):
    """Capability protocol for ATM and partial-exit operations."""

    async def model_atm_exits(
        self,
        request: ModelAtmExitsRequest,
    ) -> ModelAtmExitsSuccess | StrategyFailure:
        """Define ATM exits and partial-exit rules.

        Args:
            request: Operation-discriminated ATM and partial-exit request.

        Returns:
            The ATM definition or partial-exit definition on success,
            otherwise a structured strategy failure.
        """
        ...


@runtime_checkable
class ExtendPluginNodesCapability(Protocol):
    """Capability protocol for plugin node registration."""

    async def extend_plugin_nodes(
        self,
        request: ExtendPluginNodesRequest,
    ) -> ExtendPluginNodesSuccess | StrategyFailure:
        """Register plugin-provided AST node types.

        Args:
            request: Plugin node registration request.

        Returns:
            The registered plugin node reference on success, otherwise a
            structured strategy failure.
        """
        ...


@runtime_checkable
class GenerateCodeCapability(Protocol):
    """Capability protocol for codegen core operations."""

    async def generate_code(
        self,
        request: GenerateCodeRequest,
    ) -> GenerateCodeSuccess | StrategyFailure:
        """Register code targets and generate deterministic code.

        Args:
            request: Operation-discriminated codegen core request.

        Returns:
            The target descriptor, accepted request, result, or manifest on
            success, otherwise a structured strategy failure.
        """
        ...


@runtime_checkable
class GenerateMql5Capability(Protocol):
    """Capability protocol for MQL5 toolchain operations."""

    async def generate_mql5(
        self,
        request: GenerateMql5Request,
    ) -> GenerateMql5Success | StrategyFailure:
        """Generate, compile, verify, compare, and package MQL5 code.

        Args:
            request: Operation-discriminated MQL5 toolchain request.

        Returns:
            The code generation result or deployment package on success,
            otherwise a structured strategy failure.
        """
        ...


@runtime_checkable
class GenerateTargetsCapability(Protocol):
    """Capability protocol for additional code target operations."""

    async def generate_targets(
        self,
        request: GenerateTargetsRequest,
    ) -> GenerateTargetsSuccess | StrategyFailure:
        """Implement and validate additional code targets.

        Args:
            request: Operation-discriminated additional-target request.

        Returns:
            The target descriptor or code generation result on success,
            otherwise a structured strategy failure.
        """
        ...
