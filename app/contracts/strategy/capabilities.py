"""Strategy domain capability keys."""

from typing import TYPE_CHECKING

from app.kernel.capability import CapabilityKey

if TYPE_CHECKING:
    from app.contracts.strategy.ports import (
        CatalogBlocksCapability,
        ConfigureChartsCapability,
        DefineArchitecturesCapability,
        DefineAstCapability,
        DefineIndicatorsCapability,
        EditTemplatesCapability,
        ExchangeStrategiesCapability,
        ExtendPluginNodesCapability,
        GenerateCodeCapability,
        GenerateMql5Capability,
        GenerateTargetsCapability,
        ModelAtmExitsCapability,
        VersionStrategiesCapability,
    )

DEFINE_AST_CAPABILITY: CapabilityKey[DefineAstCapability] = CapabilityKey(
    name="strategy.define-ast",
    major=1,
)

CATALOG_BLOCKS_CAPABILITY: CapabilityKey[CatalogBlocksCapability] = CapabilityKey(
    name="strategy.catalog-blocks",
    major=1,
)

CONFIGURE_CHARTS_CAPABILITY: CapabilityKey[ConfigureChartsCapability] = CapabilityKey(
    name="strategy.configure-charts",
    major=1,
)

VERSION_STRATEGIES_CAPABILITY: CapabilityKey[VersionStrategiesCapability] = (
    CapabilityKey(
        name="strategy.version-strategies",
        major=1,
    )
)

EDIT_TEMPLATES_CAPABILITY: CapabilityKey[EditTemplatesCapability] = CapabilityKey(
    name="strategy.edit-templates",
    major=1,
)

EXCHANGE_STRATEGIES_CAPABILITY: CapabilityKey[ExchangeStrategiesCapability] = (
    CapabilityKey(
        name="strategy.exchange-strategies",
        major=1,
    )
)

DEFINE_ARCHITECTURES_CAPABILITY: CapabilityKey[DefineArchitecturesCapability] = (
    CapabilityKey(
        name="strategy.define-architectures",
        major=1,
    )
)

DEFINE_INDICATORS_CAPABILITY: CapabilityKey[DefineIndicatorsCapability] = CapabilityKey(
    name="strategy.define-indicators",
    major=1,
)

MODEL_ATM_EXITS_CAPABILITY: CapabilityKey[ModelAtmExitsCapability] = CapabilityKey(
    name="strategy.model-atm-exits",
    major=1,
)

EXTEND_PLUGIN_NODES_CAPABILITY: CapabilityKey[ExtendPluginNodesCapability] = (
    CapabilityKey(
        name="strategy.extend-plugin-nodes",
        major=1,
    )
)

GENERATE_CODE_CAPABILITY: CapabilityKey[GenerateCodeCapability] = CapabilityKey(
    name="strategy.generate-code",
    major=1,
)

GENERATE_MQL5_CAPABILITY: CapabilityKey[GenerateMql5Capability] = CapabilityKey(
    name="strategy.generate-mql5",
    major=1,
)

GENERATE_TARGETS_CAPABILITY: CapabilityKey[GenerateTargetsCapability] = CapabilityKey(
    name="strategy.generate-targets",
    major=1,
)
