"""Single BlockRegistry projection and semantic block resolution for HSL 1.0.

Description:
    Adapts the core BlockRegistry (app/core/trading/blocks/registry.py) as the
    sole authoritative source of indicator and function blocks for AlgoWizard,
    projecting registered BlockDescriptors alongside HSL 1.0 semantic language
    primitives without maintaining a duplicate static JSON indicator catalog.

Purpose:
    FEAT-WIZARD-BLOCK-LIBRARY: Bridges HSL 1.0 semantic identifiers
    (e.g. indicator.rsi, comparison.crosses_above, order.enter_market) to live
    BlockRegistry snapshots, parameter bounds, and static return types.

Key Capabilities:
    - FR-wizard-registry-projection: Reads BlockRegistry.snapshot() directly and
      lazily seeds canonical indicators when the default registry is empty.
    - FR-wizard-semantic-id-mapping: Maps HSL semantic IDs (indicator.rsi <->
      indicator.momentum.rsi / rsi) and language primitives deterministically.
    - FR-wizard-parameter-bounds-extraction: Extracts min/max/default/required
      parameter bounds from BlockSpec.parameter_search_space and JSON schemas.

Python API Usage:
    from app.workspace.algo_wizard.library import WizardBlockLibrary

    library = WizardBlockLibrary()
    entry = library.require("indicator.rsi")

CLI Usage:
    python -c "from app.workspace.algo_wizard import library; print(1)"
"""

from __future__ import annotations

from collections.abc import Mapping
from importlib import import_module
from typing import Any

from app.core.host.logging import get_logger
from app.core.lib.errors import DomainError
from app.core.trading.blocks.composition import composition_manifest
from app.core.trading.blocks.metadata import ExecutionKind, PortType
from app.core.trading.blocks.registry import (
    BlockDescriptor,
    BlockRegistry,
    block_registry,
)
from app.workspace.algo_wizard.catalogue_models import (
    CatalogueParameterBounds,
    HSLBlockCatalogueEntry,
    SemanticNodeFamily,
    StaticReturnType,
)
from app.workspace.algo_wizard.value_models import ScalarLiteral, ScalarValueType

logger = get_logger(__name__)

_SEMANTIC_INDICATOR_ALIASES: dict[str, tuple[str, ...]] = {
    "indicator.highest": (
        "indicator.volatility.highest_in_range",
        "indicator.price_action.highest_lowest",
        "highest_in_range",
        "highest",
    ),
    "indicator.lowest": (
        "indicator.volatility.lowest_in_range",
        "indicator.price_action.highest_lowest",
        "lowest_in_range",
        "lowest",
    ),
    "indicator.donchian": (
        "indicator.trend.donchian_channel",
        "donchian_channel",
        "donchian",
    ),
}


def _map_schema_param_type(raw_type: str) -> ScalarValueType:
    """Convert JSON schema or search-space type strings to ScalarValueType."""
    lower = raw_type.strip().lower()
    if lower in {"int", "integer"}:
        return "int"
    if lower in {"bool", "boolean"}:
        return "bool"
    if lower in {"str", "string"}:
        return "str"
    return "float"


def _extract_parameter_bounds(
    descriptor: BlockDescriptor,
) -> tuple[CatalogueParameterBounds, ...]:
    """Extract parameter bounds from BlockSpec search space and JSON schema."""
    search_space = descriptor.spec.parameter_search_space
    schema_props = descriptor.parameter_schema.get("properties", {})
    required_set = set(descriptor.parameter_schema.get("required", ()))

    param_names: list[str] = []
    for key in search_space:
        if key not in param_names:
            param_names.append(str(key))
    if isinstance(schema_props, Mapping):
        for key in schema_props:
            if key not in param_names:
                param_names.append(str(key))

    bounds: list[CatalogueParameterBounds] = []
    for name in param_names:
        sp_entry = search_space.get(name) if isinstance(search_space, Mapping) else None
        prop_entry = (
            schema_props.get(name) if isinstance(schema_props, Mapping) else None
        )
        sp_map = sp_entry if isinstance(sp_entry, Mapping) else {}
        prop_map = prop_entry if isinstance(prop_entry, Mapping) else {}

        raw_type = str(sp_map.get("type") or prop_map.get("type") or "float")
        param_type = _map_schema_param_type(raw_type)

        default_val = sp_map.get("default", prop_map.get("default"))
        scalar_default: ScalarLiteral | None = (
            default_val if isinstance(default_val, (bool, int, float, str)) else None
        )

        min_raw = sp_map.get(
            "min",
            sp_map.get(
                "minimum",
                prop_map.get("minimum", prop_map.get("exclusiveMinimum")),
            ),
        )
        max_raw = sp_map.get(
            "max",
            sp_map.get(
                "maximum",
                prop_map.get("maximum", prop_map.get("exclusiveMaximum")),
            ),
        )
        min_val: int | float | None = (
            min_raw
            if isinstance(min_raw, (int, float)) and not isinstance(min_raw, bool)
            else None
        )
        max_val: int | float | None = (
            max_raw
            if isinstance(max_raw, (int, float)) and not isinstance(max_raw, bool)
            else None
        )

        is_req = bool(
            sp_map.get("required", name in required_set and scalar_default is None)
        )
        desc = str(prop_map.get("description") or sp_map.get("description") or "")

        bounds.append(
            CatalogueParameterBounds(
                name=name,
                param_type=param_type,
                default=scalar_default,
                min_value=min_val,
                max_value=max_val,
                required=is_req,
                description=desc,
            )
        )
    return tuple(bounds)


def _infer_family_and_return_type(
    descriptor: BlockDescriptor,
) -> tuple[SemanticNodeFamily, StaticReturnType]:
    """Map BlockDescriptor execution kind and outputs to HSL family and return type."""
    kind = descriptor.spec.execution_kind
    if kind == ExecutionKind.CONDITION:
        return "CONDITION", "bool"
    if kind in {ExecutionKind.ACTION, ExecutionKind.ORDER}:
        return "ACTION", "void"

    if descriptor.spec.outputs:
        first_port = descriptor.spec.outputs[0].port_type
        if first_port in {PortType.BOOLEAN, PortType.BOOLEAN_SERIES}:
            return "EXPRESSION", "bool"
        if first_port == PortType.STRING:
            return "EXPRESSION", "str"
    return "EXPRESSION", "float"


def _canonical_semantic_id(
    registry_id: str, category: str
) -> tuple[str, tuple[str, ...]]:
    """Derive the canonical HSL semantic ID and aliases for a registered block."""
    cleaned = registry_id.strip().lower()
    parts = cleaned.split(".")
    tail = parts[-1]

    aliases: list[str] = [cleaned, tail]
    if cleaned.startswith("indicator.") or category in {
        "indicators",
        "momentum",
        "trend",
        "volatility",
        "volume",
        "price_action",
        "regime",
    }:
        semantic_id = f"indicator.{tail}"
        if semantic_id not in aliases:
            aliases.insert(0, semantic_id)
        return semantic_id, tuple(dict.fromkeys(aliases))

    return cleaned, tuple(dict.fromkeys(aliases))


def _builtin_hsl_primitives() -> tuple[HSLBlockCatalogueEntry, ...]:
    """Return built-in HSL 1.0 language primitive catalogue descriptors."""
    entries: list[HSLBlockCatalogueEntry] = []

    comparisons = (
        ("comparison.greater_than", "Greater Than (>)"),
        ("comparison.greater_or_equal", "Greater Than or Equal (>=)"),
        ("comparison.less_than", "Less Than (<)"),
        ("comparison.less_or_equal", "Less Than or Equal (<=)"),
        ("comparison.equal", "Equal (==)"),
        ("comparison.not_equal", "Not Equal (!=)"),
        ("comparison.crosses_above", "Crosses Above"),
        ("comparison.crosses_below", "Crosses Below"),
    )
    for sem_id, label in comparisons:
        short = sem_id.split(".")[-1]
        entries.append(
            HSLBlockCatalogueEntry(
                semantic_id=sem_id,
                registry_id=sem_id,
                name=label,
                category="comparison",
                family="CONDITION",
                return_type="bool",
                description=f"HSL 1.0 {label} relational/crossing condition.",
                aliases=(sem_id, short),
            )
        )

    math_ops = (
        ("math.add", "Add (+)"),
        ("math.subtract", "Subtract (-)"),
        ("math.multiply", "Multiply (*)"),
        ("math.divide", "Divide (/)"),
        ("math.min", "Minimum"),
        ("math.max", "Maximum"),
        ("math.abs", "Absolute Value"),
    )
    for sem_id, label in math_ops:
        short = sem_id.split(".")[-1]
        entries.append(
            HSLBlockCatalogueEntry(
                semantic_id=sem_id,
                registry_id=sem_id,
                name=label,
                category="math",
                family="EXPRESSION",
                return_type="float",
                description=f"HSL 1.0 {label} arithmetic expression.",
                aliases=(sem_id, short),
            )
        )

    market_fields = (
        ("market.open", "Bar Open Price"),
        ("market.high", "Bar High Price"),
        ("market.low", "Bar Low Price"),
        ("market.close", "Bar Close Price"),
        ("market.volume", "Bar Volume"),
    )
    for sem_id, label in market_fields:
        short = sem_id.split(".")[-1]
        entries.append(
            HSLBlockCatalogueEntry(
                semantic_id=sem_id,
                registry_id=sem_id,
                name=label,
                category="market",
                family="VALUE",
                return_type="float",
                description=f"HSL 1.0 {label} series value.",
                aliases=(sem_id, short),
            )
        )

    states = (
        ("position.is_flat", "Position Is Flat"),
        ("position.is_long", "Position Is Long"),
        ("position.is_short", "Position Is Short"),
        ("session.is_open", "Session Is Open"),
    )
    for sem_id, label in states:
        entries.append(
            HSLBlockCatalogueEntry(
                semantic_id=sem_id,
                registry_id=sem_id,
                name=label,
                category="state",
                family="CONDITION",
                return_type="bool",
                description=f"HSL 1.0 {label} state predicate.",
                aliases=(sem_id,),
            )
        )

    orders_and_setup = (
        ("order.enter_market", "Enter At Market", "order", "ACTION", "void"),
        ("order.enter_stop", "Enter Stop Pending", "order", "ACTION", "void"),
        ("order.enter_limit", "Enter Limit Pending", "order", "ACTION", "void"),
        ("order.exit_position", "Exit Position", "order", "ACTION", "void"),
        ("stop_loss.none", "No Stop Loss", "stop_loss", "EXPRESSION", "float"),
        (
            "stop_loss.fixed_pips",
            "Fixed Pips Stop Loss",
            "stop_loss",
            "EXPRESSION",
            "float",
        ),
        (
            "stop_loss.fixed_points",
            "Fixed Points Stop Loss",
            "stop_loss",
            "EXPRESSION",
            "float",
        ),
        ("stop_loss.atr", "ATR Stop Loss", "stop_loss", "EXPRESSION", "float"),
        (
            "stop_loss.percent",
            "Percentage Stop Loss",
            "stop_loss",
            "EXPRESSION",
            "float",
        ),
        (
            "stop_loss.expression",
            "Expression Stop Loss",
            "stop_loss",
            "EXPRESSION",
            "float",
        ),
        ("take_profit.none", "No Take Profit", "take_profit", "EXPRESSION", "float"),
        (
            "take_profit.fixed_pips",
            "Fixed Pips Take Profit",
            "take_profit",
            "EXPRESSION",
            "float",
        ),
        ("take_profit.atr", "ATR Take Profit", "take_profit", "EXPRESSION", "float"),
        (
            "take_profit.risk_multiple",
            "Risk Multiple Take Profit",
            "take_profit",
            "EXPRESSION",
            "float",
        ),
        (
            "take_profit.expression",
            "Expression Take Profit",
            "take_profit",
            "EXPRESSION",
            "float",
        ),
        (
            "position_size.fixed_size",
            "Fixed Lot Size",
            "position_size",
            "EXPRESSION",
            "float",
        ),
        (
            "position_size.fixed_cash",
            "Fixed Cash Notional",
            "position_size",
            "EXPRESSION",
            "float",
        ),
        (
            "position_size.percent_equity",
            "Percent of Equity",
            "position_size",
            "EXPRESSION",
            "float",
        ),
        (
            "position_size.risk_percent",
            "Percent Risk Per Trade",
            "position_size",
            "EXPRESSION",
            "float",
        ),
    )
    for sem_id, label, cat, fam, ret in orders_and_setup:
        entries.append(
            HSLBlockCatalogueEntry(
                semantic_id=sem_id,
                registry_id=sem_id,
                name=label,
                category=cat,
                family=fam,  # type: ignore[arg-type]
                return_type=ret,  # type: ignore[arg-type]
                description=f"HSL 1.0 {label} building block.",
                aliases=(sem_id, sem_id.split(".")[-1]),
            )
        )

    return tuple(entries)


_BUILTIN_PRIMITIVES: tuple[HSLBlockCatalogueEntry, ...] = _builtin_hsl_primitives()


def _seed_default_indicators_if_empty(registry: BlockRegistry) -> None:
    """Populate the default BlockRegistry from composition_manifest when empty."""
    manifest = composition_manifest()
    calculations = manifest.get("calculations", {})
    if not isinstance(calculations, Mapping):
        return
    registered_count = 0
    for block_id, info in calculations.items():
        if not isinstance(info, Mapping) or registry.get(str(block_id)) is not None:
            continue
        mod_name = str(info.get("module") or "")
        cls_name = str(info.get("class") or "")
        if not mod_name or not cls_name:
            continue
        cls_obj: Any = getattr(import_module(mod_name), cls_name)
        registry.register_block(cls_obj, source_file=mod_name, overwrite=True)
        registered_count += 1
    logger.info(
        "Seeded %d canonical indicators into default BlockRegistry",
        registered_count,
    )


class WizardBlockLibrary:
    """Single-source-of-truth block adapter projecting BlockRegistry snapshots."""

    def __init__(
        self,
        registry: BlockRegistry | None = None,
        *,
        seed_defaults: bool | None = None,
    ) -> None:
        self._registry: BlockRegistry = (
            registry if registry is not None else block_registry
        )
        should_seed = seed_defaults if seed_defaults is not None else (registry is None)
        if should_seed:
            _seed_default_indicators_if_empty(self._registry)

    @property
    def registry(self) -> BlockRegistry:
        """Return the underlying authoritative BlockRegistry."""
        return self._registry

    @property
    def revision(self) -> str:
        """Return the current BlockRegistry snapshot revision."""
        return self._registry.snapshot().revision

    def _project_descriptor(
        self,
        descriptor: BlockDescriptor,
        extra_aliases: tuple[str, ...] = (),
    ) -> HSLBlockCatalogueEntry:
        """Convert a BlockDescriptor from BlockRegistry into HSLBlockCatalogueEntry."""
        spec = descriptor.spec
        sem_id, base_aliases = _canonical_semantic_id(spec.id, spec.category)
        all_aliases = tuple(dict.fromkeys((*base_aliases, *extra_aliases)))
        family, return_type = _infer_family_and_return_type(descriptor)
        outputs = tuple(out.name for out in spec.outputs) if spec.outputs else ("main",)
        if "main" not in outputs:
            outputs = ("main", *outputs)

        return HSLBlockCatalogueEntry(
            semantic_id=sem_id,
            registry_id=spec.id,
            name=spec.name or sem_id,
            category=spec.category or "indicators",
            family=family,
            return_type=return_type,
            description=spec.description,
            parameters=_extract_parameter_bounds(descriptor),
            outputs=outputs,
            required_inputs=tuple(spec.required_market_inputs),
            aliases=all_aliases,
            is_causal=spec.is_causal,
        )

    def _build_index(
        self,
    ) -> tuple[dict[str, HSLBlockCatalogueEntry], list[HSLBlockCatalogueEntry]]:
        """Build lookup map and ordered list from the current BlockRegistry snapshot."""
        snapshot = self._registry.snapshot()
        by_key: dict[str, HSLBlockCatalogueEntry] = {}
        ordered: list[HSLBlockCatalogueEntry] = []

        for prim in _BUILTIN_PRIMITIVES:
            ordered.append(prim)
            by_key[prim.semantic_id.lower()] = prim
            for alias in prim.aliases:
                by_key.setdefault(alias.lower(), prim)

        for desc in snapshot:
            entry = self._project_descriptor(desc)
            ordered.append(entry)
            by_key[entry.semantic_id.lower()] = entry
            by_key[entry.registry_id.lower()] = entry
            for alias in entry.aliases:
                by_key[alias.lower()] = entry

        for canonical_alias, targets in _SEMANTIC_INDICATOR_ALIASES.items():
            if canonical_alias not in by_key:
                for candidate in targets:
                    if candidate.lower() in by_key:
                        matched = by_key[candidate.lower()]
                        aliased_entry = matched.model_copy(
                            update={
                                "semantic_id": canonical_alias,
                                "aliases": tuple(
                                    dict.fromkeys(
                                        (
                                            canonical_alias,
                                            canonical_alias.split(".")[-1],
                                            *matched.aliases,
                                        )
                                    )
                                ),
                            }
                        )
                        by_key[canonical_alias] = aliased_entry
                        by_key[canonical_alias.split(".")[-1]] = aliased_entry
                        ordered.append(aliased_entry)
                        break

        return by_key, ordered

    def resolve(self, identifier: str) -> HSLBlockCatalogueEntry | None:
        """Resolve a semantic ID, registry ID, or alias to a catalogue entry."""
        key = identifier.strip().lower()
        if not key:
            return None
        by_key, _ = self._build_index()
        resolved = by_key.get(key)
        if resolved is None and not key.startswith("indicator."):
            resolved = by_key.get(f"indicator.{key}")
        return resolved

    def require(self, identifier: str) -> HSLBlockCatalogueEntry:
        """Resolve a block identifier or raise DomainError(WIZARD_UNKNOWN_BLOCK_ID)."""
        entry = self.resolve(identifier)
        if entry is None:
            logger.warning("Unknown block identifier requested: %s", identifier)
            raise DomainError(
                code="WIZARD_UNKNOWN_BLOCK_ID",
                message=f"Block '{identifier}' is not registered in BlockRegistry.",
                details={"block_id": identifier},
            )
        return entry

    def list_entries(
        self,
        *,
        category: str | None = None,
        family: SemanticNodeFamily | None = None,
    ) -> tuple[HSLBlockCatalogueEntry, ...]:
        """Return catalogue entries matching optional category and family filters."""
        _, ordered = self._build_index()
        deduped: dict[str, HSLBlockCatalogueEntry] = {}
        for item in ordered:
            deduped[item.semantic_id] = item

        cat_filter = category.strip().lower() if category else None
        filtered = [
            item
            for item in deduped.values()
            if (cat_filter is None or item.category.lower() == cat_filter)
            and (family is None or item.family == family)
        ]
        filtered.sort(key=lambda item: (item.family, item.semantic_id))
        logger.debug(
            "Listed %d HSL block catalogue entries (category=%s, family=%s)",
            len(filtered),
            category,
            family,
        )
        return tuple(filtered)
