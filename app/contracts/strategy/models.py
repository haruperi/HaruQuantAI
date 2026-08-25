"""Strict Pydantic v2 wire records for the ratified Strategy v1 contracts."""

from decimal import Decimal
from typing import Annotated, Literal

from pydantic import Field, StringConstraints, model_validator

# These reference records are annotation-only for readers but Pydantic
# resolves them at class-creation time, so they must remain runtime imports.
from app.contracts.catalogue.models import BrokerRef, InstrumentRef  # noqa: TC001
from app.contracts.common.models import (
    CapabilityIdentifier,
    ContentHash,
    DecimalValue,
    Direction,
    JsonObject,
    JsonValue,
    Timeframe,
    UtcTimestamp,
    Uuid7,
    ValidationIssue,
    WireModel,
)

# Inclusive upper bound of an ATM stage size in percent; stages are strictly
# positive fractions of one position, so their sum is bounded by 100 percent.
_MAX_STAGE_SIZE_PERCENT = 100

# Shared AST type literal from the ratified v1 public records intro
# (FR-STRAT-DEFINE_AST_TYPES).
type AstType = Literal[
    "BOOLEAN",
    "INTEGER",
    "DECIMAL",
    "PRICE",
    "QUANTITY",
    "PERCENTAGE",
    "DURATION",
    "TIMEFRAME",
    "INSTRUMENT",
    "ENUM",
    "SCALAR_SERIES",
    "EVENT",
    "ACTION",
]

# Constrained local string aliases reused across strategy records.
type NonEmptyStr = Annotated[str, StringConstraints(min_length=1)]
# Domain assumption: a syntactic SemVer 2.0.0 core check only; this does not
# validate build/precedence semantics.
type SemverString = Annotated[
    str,
    StringConstraints(
        pattern=r"^\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?(?:\+[0-9A-Za-z.-]+)?$"
    ),
]


def _require_present(fields: tuple[tuple[str, object], ...]) -> None:
    """Reject an operation request that omits a required field.

    Args:
        fields: ``(field name, value)`` pairs that must not be None.

    Raises:
        ValueError: Any listed field is None.
    """
    for name, value in fields:
        if value is None:
            raise ValueError("required field is missing: " + name)


def _require_absent(fields: tuple[tuple[str, object], ...]) -> None:
    """Reject an operation request that sets a forbidden field.

    Args:
        fields: ``(field name, value)`` pairs that must be None.

    Raises:
        ValueError: Any listed field is not None.
    """
    for name, value in fields:
        if value is not None:
            raise ValueError("forbidden field is set: " + name)


def _require_single_primary(charts: tuple[ChartDefinition, ...]) -> None:
    """Reject a chart collection without exactly one PRIMARY chart.

    Args:
        charts: Chart definitions that must contain exactly one chart with
            the PRIMARY role.

    Raises:
        ValueError: The collection contains zero or multiple PRIMARY charts.
    """
    primary_count = sum(chart.role == "PRIMARY" for chart in charts)
    if primary_count != 1:
        raise ValueError("charts must contain exactly one PRIMARY chart")


class NodeBinding(WireModel):
    """One typed input binding of an AST node.

    Domain assumption: exactly one of ``source_node_id`` and a ``constant``
    value supplies a port; the mutual-exclusion rule is enforced by AST
    normalization (FR-STRAT-DEFINE_AST_NODES), not by the wire shape, because
    a ``None`` constant is itself a legal JSON value.
    """

    port_name: NonEmptyStr
    source_node_id: Uuid7 | None = None
    constant: JsonValue = None


class StrategyNode(WireModel):
    """One AST node carrying identity, block reference, and typed bindings."""

    node_id: Uuid7
    kind: NonEmptyStr
    block_id: NonEmptyStr
    block_version: int = Field(ge=1)
    bindings: tuple[NodeBinding, ...] = ()
    parameters: dict[str, JsonValue] = Field(default_factory=dict)
    # Ordered only where the child order is semantic; the README marks the
    # ordering semantics, and canonical ordering is decided by normalization.
    children: tuple[Uuid7, ...] = ()
    schema_version: Literal[1] = 1


class ExpressionNode(WireModel):
    """One typed operator application over referenced operand nodes.

    Domain assumption: invalid operand connections such as series-to-boolean
    or price-to-duration require the operand types from the block catalogue,
    so they are rejected by AST validation (FR-STRAT-DEFINE_AST_TYPES) rather
    than by this wire shape.
    """

    node_id: Uuid7
    operator: NonEmptyStr
    operands: tuple[Uuid7, ...] = Field(min_length=1)
    result_type: AstType
    schema_version: Literal[1] = 1


class StrategyAst(WireModel):
    """Canonical typed abstract syntax tree of one strategy.

    Commutatively reordered AND operands hash equally; ordered action
    sequences do not (FR-STRAT-NORMALIZE_STRATEGY_AST).
    """

    nodes: tuple[StrategyNode, ...] = Field(min_length=1)
    expression_nodes: tuple[ExpressionNode, ...] = ()
    content_hash: ContentHash
    schema_version: Literal[1] = 1


class BlockDefinition(WireModel):
    """One versioned block catalogue record.

    Uniqueness ``(stable_id, version)`` and referenced-version diagnosability
    are enforced by the owning store because they span records.
    """

    block_id: NonEmptyStr
    version: int = Field(ge=1)
    category: NonEmptyStr
    input_types: tuple[AstType, ...] = ()
    output_types: tuple[AstType, ...] = ()
    parameter_schema: JsonObject
    data_capabilities: tuple[CapabilityIdentifier, ...] = ()
    supported_events: tuple[NonEmptyStr, ...] = ()
    target_capabilities: tuple[CapabilityIdentifier, ...] = ()
    status: Literal["ACTIVE", "DEPRECATED", "RETIRED"]
    content_hash: ContentHash
    schema_version: Literal[1] = 1


class ParameterDefinition(WireModel):
    """One typed parameter with its declared value domain.

    Integer 5-15 step 5 enumerates exactly 5, 10, 15; invalid or empty
    declared domains fail before search queueing
    (FR-STRAT-DEFINE_PARAMETER_DOMAINS, FR-STRAT-DEFINE_SEARCH_PARAMETERS).
    """

    name: NonEmptyStr
    value_type: AstType
    domain: Literal["FIXED", "DISCRETE", "RANGE_STEP"]
    fixed_value: JsonValue = None
    discrete_values: tuple[JsonValue, ...] = ()
    range_min: DecimalValue | None = None
    range_max: DecimalValue | None = None
    step: DecimalValue | None = None
    default_value: JsonValue = None
    is_search_eligible: bool = False
    mutation_behavior: str = ""
    optimization_visible: bool = True
    schema_version: Literal[1] = 1

    @model_validator(mode="after")
    def validate_domain(self) -> ParameterDefinition:
        """Reject a declared domain that is incomplete or inconsistent.

        Returns:
            The validated parameter definition.

        Raises:
            ValueError: The declared ``domain`` lacks its defining values,
                a RANGE_STEP interval is inverted, or the step is not
                positive.
        """
        match self.domain:
            case "FIXED":
                if self.fixed_value is None:
                    raise ValueError("FIXED domain requires fixed_value")
            case "DISCRETE":
                if not self.discrete_values:
                    raise ValueError("DISCRETE domain requires discrete_values")
            case "RANGE_STEP":
                if (
                    self.range_min is None
                    or self.range_max is None
                    or self.step is None
                ):
                    raise ValueError(
                        "RANGE_STEP domain requires range_min, range_max, and step"
                    )
                if Decimal(self.range_min) > Decimal(self.range_max):
                    raise ValueError("range_min must be <= range_max")
                if Decimal(self.step) <= 0:
                    raise ValueError("step must be > 0")
        return self


class ChartDefinition(WireModel):
    """One primary or additional chart binding of a strategy.

    Exactly one chart of a strategy carries the PRIMARY role; that
    collection-level rule is validated wherever charts are collected.
    """

    ordinal: int = Field(ge=0)
    instrument: InstrumentRef
    broker: BrokerRef | None = None
    timeframe: Timeframe
    role: Literal["PRIMARY", "ADDITIONAL"]
    warmup_bars: int = Field(default=0, ge=0)
    schema_version: Literal[1] = 1


class DirectionPolicy(WireModel):
    """Trade-direction and opposite-symmetry policy of a strategy.

    Derived short logic is stored visibly and detachable without mutating
    long logic (FR-STRAT-CONFIGURE_TRADE_DIRECTIONS).
    """

    direction: Direction
    symmetry: Literal["INDEPENDENT", "DERIVED"]
    opposite_map_version_id: Uuid7 | None = None
    schema_version: Literal[1] = 1

    @model_validator(mode="after")
    def validate_symmetry(self) -> DirectionPolicy:
        """Reject a DERIVED policy without an opposite-map version.

        Returns:
            The validated direction policy.

        Raises:
            ValueError: ``symmetry`` is DERIVED while
                ``opposite_map_version_id`` is missing.
        """
        if self.symmetry == "DERIVED" and self.opposite_map_version_id is None:
            raise ValueError("DERIVED symmetry requires opposite_map_version_id")
        return self


class VisibilityPolicy(WireModel):
    """Observable series shift declaration for one chart.

    Shift 0 exposes only the value observable at the current event;
    higher-timeframe future closes cannot influence lower timeframes
    (FR-STRAT-DEFINE_SERIES_SHIFTS).
    """

    chart_ordinal: int = Field(ge=0)
    shift: int = Field(default=0, ge=0)
    look_ahead: Literal["PROHIBITED"] = "PROHIBITED"
    schema_version: Literal[1] = 1


class StrategyRef(WireModel):
    """Reference to one strategy identity."""

    strategy_id: Uuid7
    schema_version: Literal[1] = 1


class StrategyArchitecture(WireModel):
    """One architecture style selection of a strategy.

    Signal-gated evaluation prevents conflicting entry and exit signals
    (FR-STRAT-DEFINE_STRATEGY_ARCHITECTURES).
    """

    architecture_id: Uuid7
    version: int = Field(ge=1)
    style: Literal["CLASSIC_RULES", "SIGNAL_GATED", "FUZZY_VOTING", "CUSTOM"]
    custom_template_version_id: Uuid7 | None = None
    schema_version: Literal[1] = 1

    @model_validator(mode="after")
    def validate_style(self) -> StrategyArchitecture:
        """Reject a CUSTOM architecture without a custom template version.

        Returns:
            The validated architecture.

        Raises:
            ValueError: ``style`` is CUSTOM while
                ``custom_template_version_id`` is missing.
        """
        if self.style == "CUSTOM" and self.custom_template_version_id is None:
            raise ValueError("CUSTOM style requires custom_template_version_id")
        return self


class StrategyVersion(WireModel):
    """One versioned strategy snapshot.

    Uniqueness ``(strategy_id, version)`` is enforced by the owning store
    because it spans records; committing a draft creates the immutable
    version and results from the parent stay linked
    (FR-STRAT-VERSION_STRATEGY_DRAFTS).
    """

    strategy_version_id: Uuid7
    strategy_id: Uuid7
    version: int = Field(ge=1)
    architecture: StrategyArchitecture
    ast: StrategyAst
    ast_hash: ContentHash
    charts: tuple[ChartDefinition, ...] = Field(min_length=1)
    direction: DirectionPolicy
    parent_version_id: Uuid7 | None = None
    creation_method: NonEmptyStr
    dependency_artifact_ids: tuple[Uuid7, ...] = ()
    created_at: UtcTimestamp
    content_hash: ContentHash
    schema_version: Literal[1] = 1

    @model_validator(mode="after")
    def validate_charts(self) -> StrategyVersion:
        """Reject a chart set without exactly one PRIMARY chart.

        Returns:
            The validated strategy version.

        Raises:
            ValueError: The declared charts contain zero or multiple PRIMARY
                charts.
        """
        _require_single_primary(self.charts)
        return self


class StrategyValidationReport(WireModel):
    """Complete validation findings for one strategy version.

    The response contains all findings covering structure, types, block
    versions, parameter domains, charts, instruments, sessions, data
    precision, order lifecycle, sizing, exits, and the selected code target
    (FR-STRAT-VALIDATE_STRATEGIES).
    """

    report_id: Uuid7
    strategy_version_id: Uuid7
    findings: tuple[ValidationIssue, ...] = ()
    is_valid: bool
    schema_version: Literal[1] = 1


class TemplatePlaceholder(WireModel):
    """One named substitution slot of a strategy template."""

    name: NonEmptyStr
    is_required: bool
    allowed_domains: tuple[JsonValue, ...] = ()


class TemplateSubtreeConstraint(WireModel):
    """One subtree grammar constraint applied to a template placeholder."""

    placeholder: NonEmptyStr
    cardinality_min: int = Field(ge=0)
    cardinality_max: int = Field(ge=0)
    compatible_block_ids: tuple[NonEmptyStr, ...] = ()
    complexity_limit: int = Field(ge=1)

    @model_validator(mode="after")
    def validate_cardinality(self) -> TemplateSubtreeConstraint:
        """Reject an inverted cardinality interval.

        Returns:
            The validated subtree constraint.

        Raises:
            ValueError: ``cardinality_max`` is below ``cardinality_min``.
        """
        if self.cardinality_max < self.cardinality_min:
            raise ValueError("cardinality_max must be >= cardinality_min")
        return self


class StrategyTemplate(WireModel):
    """One versioned strategy template with placeholders and constraints.

    Instantiation with missing required or out-of-domain values fails
    without creating a version; materialization is type-valid or a
    structured rejection (FR-STRAT-DEFINE_STRATEGY_TEMPLATES,
    FR-STRAT-CONSTRAIN_TEMPLATE_GRAMMAR).
    """

    template_id: Uuid7
    name: NonEmptyStr
    base_version_id: Uuid7
    placeholders: tuple[TemplatePlaceholder, ...] = ()
    subtree_constraints: tuple[TemplateSubtreeConstraint, ...] = ()
    content_hash: ContentHash
    schema_version: Literal[1] = 1


class PackageDependency(WireModel):
    """One packaged interchange dependency entry with content proof."""

    role: NonEmptyStr
    relative_path: NonEmptyStr
    media_type: NonEmptyStr
    size_bytes: int = Field(ge=0)
    sha256: ContentHash


class StrategyExchangePackage(WireModel):
    """One native `.sqxs` interchange package of a strategy version.

    Export-then-import reproduces the AST and content hash; unknown required
    roles reject import while unknown optional entries are preserved as
    namespaced attachments (FR-STRAT-EXCHANGE_NATIVE_STRATEGIES). The
    deterministic ZIP64 rules are owned by the interchange feature per
    Project section 22.3.
    """

    package_id: Uuid7
    container_schema_version: Literal[1]
    strategy_id: Uuid7
    strategy_version_id: Uuid7
    ast_hash: ContentHash
    created_at: UtcTimestamp
    dependencies: tuple[PackageDependency, ...] = ()
    settings_hash: ContentHash | None = None
    results_hash: ContentHash | None = None
    content_hash: ContentHash
    schema_version: Literal[1] = 1


class AtmStage(WireModel):
    """One partial-exit stage of an ATM exit definition.

    Sizing, protection, residual-position, collision, and state semantics
    are owned by the ATM feature per Project sections 18.6-18.7.
    """

    stage_name: NonEmptyStr
    size_percent: DecimalValue
    parameters: JsonObject

    @model_validator(mode="after")
    def validate_size_percent(self) -> AtmStage:
        """Reject a stage size outside the exclusive-zero percent interval.

        Returns:
            The validated ATM stage.

        Raises:
            ValueError: ``size_percent`` is not within (0, 100].
        """
        size = Decimal(self.size_percent)
        if size <= 0 or size > _MAX_STAGE_SIZE_PERCENT:
            raise ValueError("size_percent must be within (0, 100]")
        return self


class AtmExitDefinition(WireModel):
    """One ATM exit definition with ordered partial-exit stages."""

    atm_id: Uuid7
    stages: tuple[AtmStage, ...] = Field(min_length=1)
    content_hash: ContentHash
    schema_version: Literal[1] = 1


class PartialExitDefinition(WireModel):
    """One partial-exit rule of a strategy.

    Section 23 exit fixtures pass before enablement
    (FR-STRAT-MODEL_ATM_EXITS).
    """

    exit_id: Uuid7
    kind: Literal[
        "TARGET",
        "STOP",
        "TRAILING",
        "BREAKEVEN",
        "BARS",
        "RULE",
        "EOD",
        "FRIDAY",
    ]
    parameters: JsonObject
    residual_policy: Literal["KEEP_RESIDUAL", "CLOSE_ALL"]
    schema_version: Literal[1] = 1


class PluginNodeRef(WireModel):
    """Reference to one plugin-provided AST node type.

    A missing plugin or migration hook yields a diagnosable unavailable
    strategy, never silent node loss (FR-STRAT-IDENTIFY_PLUGIN_NODES).
    """

    # Cross-owner reference: Plugins-domain plugin stable-ID string.
    plugin_id: NonEmptyStr
    api_version: SemverString
    schema_ref: NonEmptyStr
    capabilities: tuple[CapabilityIdentifier, ...] = ()
    migration_hook: NonEmptyStr | None = None
    schema_version: Literal[1] = 1


class RandomBlockTemplate(WireModel):
    """One weighted block candidate of a random group version."""

    block_id: NonEmptyStr
    block_version: int = Field(ge=1)
    weight: DecimalValue

    @model_validator(mode="after")
    def validate_weight(self) -> RandomBlockTemplate:
        """Reject a negative block weight.

        Returns:
            The validated random block template.

        Raises:
            ValueError: ``weight`` is negative.
        """
        if Decimal(self.weight) < 0:
            raise ValueError("weight must be >= 0")
        return self


class RandomGroupVersion(WireModel):
    """One immutable versioned random group of block templates."""

    group_id: Uuid7
    version: int = Field(ge=1)
    group_type: Literal["CONDITION", "VALUE", "ACTION"]
    block_templates: tuple[RandomBlockTemplate, ...] = Field(min_length=1)
    fixed_parameters: tuple[NonEmptyStr, ...] = ()
    applicability: tuple[CapabilityIdentifier, ...] = ()
    content_hash: ContentHash
    schema_version: Literal[1] = 1


class OppositeMapVersion(WireModel):
    """One immutable versioned opposite-direction block mapping."""

    map_id: Uuid7
    version: int = Field(ge=1)
    source_block_id: NonEmptyStr
    source_relation: NonEmptyStr
    action: Literal["MAP", "PRESERVE", "REJECT"]
    target_block_id: NonEmptyStr | None = None
    target_relation: NonEmptyStr | None = None
    parameter_transform: JsonObject = Field(default_factory=dict)
    content_hash: ContentHash
    schema_version: Literal[1] = 1


class IndicatorOutputLine(WireModel):
    """One named typed output line of an indicator definition."""

    line_name: NonEmptyStr
    value_type: AstType


class IndicatorDefinition(WireModel):
    """One versioned indicator definition with typed output lines."""

    indicator_id: NonEmptyStr
    version: int = Field(ge=1)
    source: Literal["BUILTIN", "EXTERNAL"]
    output_lines: tuple[IndicatorOutputLine, ...] = Field(min_length=1)
    parameters: tuple[ParameterDefinition, ...] = ()
    content_hash: ContentHash
    schema_version: Literal[1] = 1


class TargetFragment(WireModel):
    """One isolated target-specific code fragment of an external indicator.

    Cross-owner reference: Workspace artifact store artifact ID.
    """

    target_id: NonEmptyStr
    artifact_id: Uuid7


class ExternalIndicatorDefinitionVersion(WireModel):
    """One immutable versioned external indicator definition.

    Target fragments stay isolated from canonical semantics; shift-0 and
    look-ahead sentinels follow Project section 15.4
    (FR-STRAT-ISOLATE_INDICATOR_FRAGMENTS).
    """

    definition_id: Uuid7
    version: int = Field(ge=1)
    value_kind: Literal["NUMBER", "PRICE", "PRICE_RANGE", "SIGNAL"]
    output_lines: tuple[IndicatorOutputLine, ...] = Field(min_length=1)
    parameter_schema: JsonObject
    source_platform: NonEmptyStr
    source_version: NonEmptyStr
    chart_binding_defaults: JsonObject = Field(default_factory=dict)
    warmup_bars: int = Field(default=0, ge=0)
    shift_semantics: NonEmptyStr
    target_fragments: tuple[TargetFragment, ...] = ()
    content_hash: ContentHash
    schema_version: Literal[1] = 1


class CodeTargetDescriptor(WireModel):
    """One versioned code-generation target advertisement.

    A target is advertised only from a versioned compatibility record backed
    by compiler/runtime versions, capability tests, and section 23.13 parity
    fixtures; PSEUDOCODE is a deterministic human-readable built-in target
    (FR-STRAT-REGISTER_CODE_TARGETS, FR-STRAT-DESCRIBE_EMITTER_CAPABILITIES).
    """

    target_id: NonEmptyStr
    version: int = Field(ge=1)
    supported_ast_capabilities: tuple[CapabilityIdentifier, ...] = ()
    engine_profile_id: Uuid7 | None = None
    emitter_version: NonEmptyStr
    formatter: NonEmptyStr
    compiler_adapter: NonEmptyStr | None = None
    packaging_rules: JsonObject
    unsupported_semantics: tuple[NonEmptyStr, ...] = ()
    compatibility_record_id: Uuid7 | None = None
    schema_version: Literal[1] = 1


class CodegenRequest(WireModel):
    """One deterministic code-generation job request for one target."""

    request_id: Uuid7
    strategy_version_id: Uuid7
    target_id: NonEmptyStr
    target_version: int = Field(ge=1)
    settings_hash: ContentHash
    schema_version: Literal[1] = 1


class CompilerDiagnostic(WireModel):
    """One parsed compiler diagnostic anchored to generated code."""

    severity: Literal["ERROR", "WARNING", "INFO"]
    code: NonEmptyStr
    file: NonEmptyStr
    line: int | None = Field(default=None, ge=1)
    column: int | None = Field(default=None, ge=1)
    message: NonEmptyStr
    node_id: Uuid7 | None = None


class CodegenResult(WireModel):
    """One code-generation run result with compile status and diagnostics.

    PASSED is reported only with real compiler success and an existing
    output artifact; repeated emission has an identical normalized source
    hash (FR-STRAT-GENERATE_CODE_DETERMINISTICALLY,
    FR-STRAT-VERIFY_MQL5_COMPILE).
    """

    result_id: Uuid7
    request_id: Uuid7
    source_artifact_id: Uuid7
    source_hash: ContentHash
    compile_status: Literal["PENDING", "PASSED", "FAILED", "SKIPPED"] = "PENDING"
    diagnostics: tuple[CompilerDiagnostic, ...] = ()
    manifest_id: Uuid7
    parity_report_id: Uuid7 | None = None
    schema_version: Literal[1] = 1


class CodeManifest(WireModel):
    """One embedded manifest tracing generated code to its source version."""

    manifest_id: Uuid7
    strategy_version_id: Uuid7
    generator_version: NonEmptyStr
    engine_profile_id: Uuid7 | None = None
    settings_hash: ContentHash
    content_hash: ContentHash
    schema_version: Literal[1] = 1


class DeploymentPackage(WireModel):
    """One immutable deployable package of a code-generation run.

    Uniqueness ``(codegen_run_id, package_hash)`` is enforced by the owning
    store because it spans records (FR-STRAT-PACKAGE_TARGET_CODE).
    """

    package_id: Uuid7
    codegen_result_id: Uuid7
    target_id: NonEmptyStr
    target_version: int = Field(ge=1)
    engine_profile_id: Uuid7 | None = None
    strategy_source_artifact_id: Uuid7
    strategy_binary_artifact_id: Uuid7 | None = None
    dependency_artifact_ids: tuple[Uuid7, ...] = ()
    installation_manifest: JsonObject
    checksums: dict[NonEmptyStr, ContentHash]
    validation_result_id: Uuid7 | None = None
    content_hash: ContentHash
    schema_version: Literal[1] = 1


class DefineAstRequest(WireModel):
    """Operation-discriminated canonical AST request.

    NORMALIZE requires only ``ast``; VALIDATE requires only
    ``strategy_version_id`` because the validation report is anchored to a
    stored version. Domain assumption: the operation split follows the
    record shapes; the ratified envelope lists only the operations.
    """

    request_id: Uuid7
    capability_snapshot_id: Uuid7
    operation: Literal["NORMALIZE", "VALIDATE"]
    ast: StrategyAst | None = None
    strategy_version_id: Uuid7 | None = None
    schema_version: Literal[1] = 1

    @model_validator(mode="after")
    def validate_operation_shape(self) -> DefineAstRequest:
        """Validate that request fields match the selected operation.

        Returns:
            The validated request.

        Raises:
            ValueError: Required fields are missing or forbidden fields are
                set for the selected operation.
        """
        match self.operation:
            case "NORMALIZE":
                _require_present((("ast", self.ast),))
                _require_absent((("strategy_version_id", self.strategy_version_id),))
            case "VALIDATE":
                _require_present((("strategy_version_id", self.strategy_version_id),))
                _require_absent((("ast", self.ast),))
        return self


class DefineAstSuccess(WireModel):
    """Successful canonical AST operation result."""

    request_id: Uuid7
    ast: StrategyAst | None = None
    report: StrategyValidationReport | None = None
    outcome: Literal["SUCCESS"] = "SUCCESS"
    result_version: Literal[1] = 1
    schema_version: Literal[1] = 1


class CatalogBlocksRequest(WireModel):
    """Operation-discriminated block catalogue request.

    CATALOG requires no selector; DESCRIBE requires only ``block_id`` with
    an optional ``block_version`` (latest when absent); FILTER_COMPATIBLE
    requires the schema-aware insertion point given by ``ast``,
    ``parent_node_id``, and ``port_name``.
    """

    request_id: Uuid7
    capability_snapshot_id: Uuid7
    operation: Literal["CATALOG", "DESCRIBE", "FILTER_COMPATIBLE"]
    block_id: NonEmptyStr | None = None
    block_version: int | None = Field(default=None, ge=1)
    ast: StrategyAst | None = None
    parent_node_id: Uuid7 | None = None
    port_name: NonEmptyStr | None = None
    schema_version: Literal[1] = 1

    @model_validator(mode="after")
    def validate_operation_shape(self) -> CatalogBlocksRequest:
        """Validate that request fields match the selected operation.

        Returns:
            The validated request.

        Raises:
            ValueError: Required fields are missing or forbidden fields are
                set for the selected operation.
        """
        match self.operation:
            case "CATALOG":
                _require_absent(
                    (
                        ("block_id", self.block_id),
                        ("block_version", self.block_version),
                        ("ast", self.ast),
                        ("parent_node_id", self.parent_node_id),
                        ("port_name", self.port_name),
                    )
                )
            case "DESCRIBE":
                _require_present((("block_id", self.block_id),))
                _require_absent(
                    (
                        ("ast", self.ast),
                        ("parent_node_id", self.parent_node_id),
                        ("port_name", self.port_name),
                    )
                )
            case "FILTER_COMPATIBLE":
                _require_present(
                    (
                        ("ast", self.ast),
                        ("parent_node_id", self.parent_node_id),
                        ("port_name", self.port_name),
                    )
                )
                _require_absent(
                    (
                        ("block_id", self.block_id),
                        ("block_version", self.block_version),
                    )
                )
        return self


class CatalogBlocksSuccess(WireModel):
    """Successful block catalogue operation result."""

    request_id: Uuid7
    blocks: tuple[BlockDefinition, ...] = ()
    parameters: tuple[ParameterDefinition, ...] = ()
    outcome: Literal["SUCCESS"] = "SUCCESS"
    result_version: Literal[1] = 1
    schema_version: Literal[1] = 1


class ConfigureChartsRequest(WireModel):
    """Operation-discriminated charts, direction, and visibility request.

    CONFIGURE_CHARTS requires a nonempty replacement chart set with exactly
    one PRIMARY chart; CONFIGURE_DIRECTION requires only ``direction``;
    DECLARE_SHIFT requires only ``visibility``.
    """

    request_id: Uuid7
    capability_snapshot_id: Uuid7
    operation: Literal["CONFIGURE_CHARTS", "CONFIGURE_DIRECTION", "DECLARE_SHIFT"]
    charts: tuple[ChartDefinition, ...] = ()
    direction: DirectionPolicy | None = None
    visibility: VisibilityPolicy | None = None
    schema_version: Literal[1] = 1

    @model_validator(mode="after")
    def validate_operation_shape(self) -> ConfigureChartsRequest:
        """Validate that request fields match the selected operation.

        Returns:
            The validated request.

        Raises:
            ValueError: Required fields are missing or forbidden fields are
                set for the selected operation, or CONFIGURE_CHARTS carries
                an empty chart set.
        """
        match self.operation:
            case "CONFIGURE_CHARTS":
                if not self.charts:
                    raise ValueError("CONFIGURE_CHARTS requires charts")
                _require_single_primary(self.charts)
                _require_absent(
                    (
                        ("direction", self.direction),
                        ("visibility", self.visibility),
                    )
                )
            case "CONFIGURE_DIRECTION":
                _require_present((("direction", self.direction),))
                _require_absent((("visibility", self.visibility),))
            case "DECLARE_SHIFT":
                _require_present((("visibility", self.visibility),))
                _require_absent((("direction", self.direction),))
        return self


class ConfigureChartsSuccess(WireModel):
    """Successful charts, direction, and visibility operation result."""

    request_id: Uuid7
    charts: tuple[ChartDefinition, ...] = ()
    direction: DirectionPolicy | None = None
    visibility: VisibilityPolicy | None = None
    outcome: Literal["SUCCESS"] = "SUCCESS"
    result_version: Literal[1] = 1
    schema_version: Literal[1] = 1

    @model_validator(mode="after")
    def validate_charts(self) -> ConfigureChartsSuccess:
        """Reject a nonempty returned chart set without exactly one PRIMARY.

        Returns:
            The validated success record.

        Raises:
            ValueError: A nonempty ``charts`` tuple contains zero or
                multiple PRIMARY charts.
        """
        if self.charts:
            _require_single_primary(self.charts)
        return self


class VersionStrategiesRequest(WireModel):
    """Operation-discriminated strategy versioning request.

    CREATE_DRAFT requires only the draft record ``strategy_version``;
    COMMIT_VERSION and SNAPSHOT_DRAFT require only the stored
    ``strategy_version_id``; a backtest binding commits the exact draft.
    """

    request_id: Uuid7
    capability_snapshot_id: Uuid7
    operation: Literal["CREATE_DRAFT", "COMMIT_VERSION", "SNAPSHOT_DRAFT"]
    strategy_version: StrategyVersion | None = None
    strategy_version_id: Uuid7 | None = None
    schema_version: Literal[1] = 1

    @model_validator(mode="after")
    def validate_operation_shape(self) -> VersionStrategiesRequest:
        """Validate that request fields match the selected operation.

        Returns:
            The validated request.

        Raises:
            ValueError: Required fields are missing or forbidden fields are
                set for the selected operation.
        """
        match self.operation:
            case "CREATE_DRAFT":
                _require_present((("strategy_version", self.strategy_version),))
                _require_absent((("strategy_version_id", self.strategy_version_id),))
            case "COMMIT_VERSION" | "SNAPSHOT_DRAFT":
                _require_present((("strategy_version_id", self.strategy_version_id),))
                _require_absent((("strategy_version", self.strategy_version),))
        return self


class VersionStrategiesSuccess(WireModel):
    """Successful strategy versioning operation result."""

    request_id: Uuid7
    strategy_version: StrategyVersion | None = None
    strategy_version_id: Uuid7 | None = None
    outcome: Literal["SUCCESS"] = "SUCCESS"
    result_version: Literal[1] = 1
    schema_version: Literal[1] = 1


class EditTemplatesRequest(WireModel):
    """Operation-discriminated template request.

    DEFINE_TEMPLATE requires only ``template``; INSTANTIATE requires only
    ``template_id`` with ``placeholder_values``. Visual-edit operations are
    client-side; commands flow through version-strategies.
    """

    request_id: Uuid7
    capability_snapshot_id: Uuid7
    operation: Literal["DEFINE_TEMPLATE", "INSTANTIATE"]
    template: StrategyTemplate | None = None
    template_id: Uuid7 | None = None
    placeholder_values: JsonObject | None = None
    schema_version: Literal[1] = 1

    @model_validator(mode="after")
    def validate_operation_shape(self) -> EditTemplatesRequest:
        """Validate that request fields match the selected operation.

        Returns:
            The validated request.

        Raises:
            ValueError: Required fields are missing or forbidden fields are
                set for the selected operation.
        """
        match self.operation:
            case "DEFINE_TEMPLATE":
                _require_present((("template", self.template),))
                _require_absent(
                    (
                        ("template_id", self.template_id),
                        ("placeholder_values", self.placeholder_values),
                    )
                )
            case "INSTANTIATE":
                _require_present(
                    (
                        ("template_id", self.template_id),
                        ("placeholder_values", self.placeholder_values),
                    )
                )
                _require_absent((("template", self.template),))
        return self


class EditTemplatesSuccess(WireModel):
    """Successful template operation result."""

    request_id: Uuid7
    template: StrategyTemplate | None = None
    instantiated_version_id: Uuid7 | None = None
    outcome: Literal["SUCCESS"] = "SUCCESS"
    result_version: Literal[1] = 1
    schema_version: Literal[1] = 1


class ExchangeStrategiesRequest(WireModel):
    """Operation-discriminated strategy interchange request.

    EXPORT requires only ``strategy_version_id``; IMPORT requires only
    ``package``; IMPORT_LEGACY requires only ``legacy_artifact_id`` holding
    the Workspace artifact-store reference of a legacy `.sqx` file that is
    imported only through the isolated importer plugin.
    """

    request_id: Uuid7
    capability_snapshot_id: Uuid7
    operation: Literal["EXPORT", "IMPORT", "IMPORT_LEGACY"]
    strategy_version_id: Uuid7 | None = None
    package: StrategyExchangePackage | None = None
    legacy_artifact_id: Uuid7 | None = None
    schema_version: Literal[1] = 1

    @model_validator(mode="after")
    def validate_operation_shape(self) -> ExchangeStrategiesRequest:
        """Validate that request fields match the selected operation.

        Returns:
            The validated request.

        Raises:
            ValueError: Required fields are missing or forbidden fields are
                set for the selected operation.
        """
        match self.operation:
            case "EXPORT":
                _require_present((("strategy_version_id", self.strategy_version_id),))
                _require_absent(
                    (
                        ("package", self.package),
                        ("legacy_artifact_id", self.legacy_artifact_id),
                    )
                )
            case "IMPORT":
                _require_present((("package", self.package),))
                _require_absent(
                    (
                        ("strategy_version_id", self.strategy_version_id),
                        ("legacy_artifact_id", self.legacy_artifact_id),
                    )
                )
            case "IMPORT_LEGACY":
                _require_present((("legacy_artifact_id", self.legacy_artifact_id),))
                _require_absent(
                    (
                        ("strategy_version_id", self.strategy_version_id),
                        ("package", self.package),
                    )
                )
        return self


class ExchangeStrategiesSuccess(WireModel):
    """Successful strategy interchange operation result."""

    request_id: Uuid7
    package: StrategyExchangePackage | None = None
    imported_version_id: Uuid7 | None = None
    outcome: Literal["SUCCESS"] = "SUCCESS"
    result_version: Literal[1] = 1
    schema_version: Literal[1] = 1


class DefineArchitecturesRequest(WireModel):
    """Operation-discriminated architecture and mapping request.

    DEFINE_ARCHITECTURE requires only ``architecture``; DEFINE_RANDOM_GROUP
    requires only ``random_group``; MAP_OPPOSITE requires only
    ``opposite_map``.
    """

    request_id: Uuid7
    capability_snapshot_id: Uuid7
    operation: Literal["DEFINE_ARCHITECTURE", "DEFINE_RANDOM_GROUP", "MAP_OPPOSITE"]
    architecture: StrategyArchitecture | None = None
    random_group: RandomGroupVersion | None = None
    opposite_map: OppositeMapVersion | None = None
    schema_version: Literal[1] = 1

    @model_validator(mode="after")
    def validate_operation_shape(self) -> DefineArchitecturesRequest:
        """Validate that request fields match the selected operation.

        Returns:
            The validated request.

        Raises:
            ValueError: Required fields are missing or forbidden fields are
                set for the selected operation.
        """
        match self.operation:
            case "DEFINE_ARCHITECTURE":
                _require_present((("architecture", self.architecture),))
                _require_absent(
                    (
                        ("random_group", self.random_group),
                        ("opposite_map", self.opposite_map),
                    )
                )
            case "DEFINE_RANDOM_GROUP":
                _require_present((("random_group", self.random_group),))
                _require_absent(
                    (
                        ("architecture", self.architecture),
                        ("opposite_map", self.opposite_map),
                    )
                )
            case "MAP_OPPOSITE":
                _require_present((("opposite_map", self.opposite_map),))
                _require_absent(
                    (
                        ("architecture", self.architecture),
                        ("random_group", self.random_group),
                    )
                )
        return self


class DefineArchitecturesSuccess(WireModel):
    """Successful architecture and mapping operation result."""

    request_id: Uuid7
    architecture: StrategyArchitecture | None = None
    random_group: RandomGroupVersion | None = None
    opposite_map: OppositeMapVersion | None = None
    outcome: Literal["SUCCESS"] = "SUCCESS"
    result_version: Literal[1] = 1
    schema_version: Literal[1] = 1


class DefineIndicatorsRequest(WireModel):
    """Operation-discriminated indicator request.

    DEFINE_INDICATOR requires only ``indicator``; DEFINE_EXTERNAL requires
    only ``external_definition``.
    """

    request_id: Uuid7
    capability_snapshot_id: Uuid7
    operation: Literal["DEFINE_INDICATOR", "DEFINE_EXTERNAL"]
    indicator: IndicatorDefinition | None = None
    external_definition: ExternalIndicatorDefinitionVersion | None = None
    schema_version: Literal[1] = 1

    @model_validator(mode="after")
    def validate_operation_shape(self) -> DefineIndicatorsRequest:
        """Validate that request fields match the selected operation.

        Returns:
            The validated request.

        Raises:
            ValueError: Required fields are missing or forbidden fields are
                set for the selected operation.
        """
        match self.operation:
            case "DEFINE_INDICATOR":
                _require_present((("indicator", self.indicator),))
                _require_absent((("external_definition", self.external_definition),))
            case "DEFINE_EXTERNAL":
                _require_present((("external_definition", self.external_definition),))
                _require_absent((("indicator", self.indicator),))
        return self


class DefineIndicatorsSuccess(WireModel):
    """Successful indicator operation result."""

    request_id: Uuid7
    indicator: IndicatorDefinition | None = None
    external_definition: ExternalIndicatorDefinitionVersion | None = None
    outcome: Literal["SUCCESS"] = "SUCCESS"
    result_version: Literal[1] = 1
    schema_version: Literal[1] = 1


class ModelAtmExitsRequest(WireModel):
    """Operation-discriminated ATM and partial-exit request.

    DEFINE_ATM requires only ``atm``; DEFINE_PARTIAL_EXIT requires only
    ``partial_exit``.
    """

    request_id: Uuid7
    capability_snapshot_id: Uuid7
    operation: Literal["DEFINE_ATM", "DEFINE_PARTIAL_EXIT"]
    atm: AtmExitDefinition | None = None
    partial_exit: PartialExitDefinition | None = None
    schema_version: Literal[1] = 1

    @model_validator(mode="after")
    def validate_operation_shape(self) -> ModelAtmExitsRequest:
        """Validate that request fields match the selected operation.

        Returns:
            The validated request.

        Raises:
            ValueError: Required fields are missing or forbidden fields are
                set for the selected operation.
        """
        match self.operation:
            case "DEFINE_ATM":
                _require_present((("atm", self.atm),))
                _require_absent((("partial_exit", self.partial_exit),))
            case "DEFINE_PARTIAL_EXIT":
                _require_present((("partial_exit", self.partial_exit),))
                _require_absent((("atm", self.atm),))
        return self


class ModelAtmExitsSuccess(WireModel):
    """Successful ATM and partial-exit operation result."""

    request_id: Uuid7
    atm: AtmExitDefinition | None = None
    partial_exit: PartialExitDefinition | None = None
    outcome: Literal["SUCCESS"] = "SUCCESS"
    result_version: Literal[1] = 1
    schema_version: Literal[1] = 1


class ExtendPluginNodesRequest(WireModel):
    """Plugin node registration request.

    REGISTER_PLUGIN_NODE requires only ``plugin_node``; Volume-Profile/TPO
    nodes are Experimental and gated per Project section 2.
    """

    request_id: Uuid7
    capability_snapshot_id: Uuid7
    operation: Literal["REGISTER_PLUGIN_NODE"]
    plugin_node: PluginNodeRef | None = None
    schema_version: Literal[1] = 1

    @model_validator(mode="after")
    def validate_operation_shape(self) -> ExtendPluginNodesRequest:
        """Validate that request fields match the selected operation.

        Returns:
            The validated request.

        Raises:
            ValueError: The plugin node reference is missing.
        """
        _require_present((("plugin_node", self.plugin_node),))
        return self


class ExtendPluginNodesSuccess(WireModel):
    """Successful plugin node registration result."""

    request_id: Uuid7
    plugin_node: PluginNodeRef | None = None
    outcome: Literal["SUCCESS"] = "SUCCESS"
    result_version: Literal[1] = 1
    schema_version: Literal[1] = 1


class GenerateCodeRequest(WireModel):
    """Operation-discriminated codegen core request.

    REGISTER_TARGET requires only ``target``; GENERATE requires only the
    code-generation job record ``codegen_request``.
    """

    request_id: Uuid7
    capability_snapshot_id: Uuid7
    operation: Literal["REGISTER_TARGET", "GENERATE"]
    target: CodeTargetDescriptor | None = None
    codegen_request: CodegenRequest | None = None
    schema_version: Literal[1] = 1

    @model_validator(mode="after")
    def validate_operation_shape(self) -> GenerateCodeRequest:
        """Validate that request fields match the selected operation.

        Returns:
            The validated request.

        Raises:
            ValueError: Required fields are missing or forbidden fields are
                set for the selected operation.
        """
        match self.operation:
            case "REGISTER_TARGET":
                _require_present((("target", self.target),))
                _require_absent((("codegen_request", self.codegen_request),))
            case "GENERATE":
                _require_present((("codegen_request", self.codegen_request),))
                _require_absent((("target", self.target),))
        return self


class GenerateCodeSuccess(WireModel):
    """Successful codegen core operation result.

    The field named ``request`` carries the accepted
    ``CodegenRequest`` record per the ratified success envelope.
    """

    request_id: Uuid7
    target: CodeTargetDescriptor | None = None
    request: CodegenRequest | None = None
    result: CodegenResult | None = None
    manifest: CodeManifest | None = None
    outcome: Literal["SUCCESS"] = "SUCCESS"
    result_version: Literal[1] = 1
    schema_version: Literal[1] = 1


class GenerateMql5Request(WireModel):
    """Operation-discriminated MQL5 toolchain request.

    GENERATE requires only ``codegen_request``; COMPILE, VERIFY, and
    PACKAGE require only ``result_id``; COMPARE requires only
    ``baseline_result_id`` with ``comparison_result_id``. MetaEditor is
    invoked in an isolated worker with timeout and captured output.
    """

    request_id: Uuid7
    capability_snapshot_id: Uuid7
    operation: Literal["GENERATE", "COMPILE", "VERIFY", "COMPARE", "PACKAGE"]
    codegen_request: CodegenRequest | None = None
    result_id: Uuid7 | None = None
    baseline_result_id: Uuid7 | None = None
    comparison_result_id: Uuid7 | None = None
    schema_version: Literal[1] = 1

    @model_validator(mode="after")
    def validate_operation_shape(self) -> GenerateMql5Request:
        """Validate that request fields match the selected operation.

        Returns:
            The validated request.

        Raises:
            ValueError: Required fields are missing or forbidden fields are
                set for the selected operation.
        """
        match self.operation:
            case "GENERATE":
                _require_present((("codegen_request", self.codegen_request),))
                _require_absent(
                    (
                        ("result_id", self.result_id),
                        ("baseline_result_id", self.baseline_result_id),
                        ("comparison_result_id", self.comparison_result_id),
                    )
                )
            case "COMPILE" | "VERIFY" | "PACKAGE":
                _require_present((("result_id", self.result_id),))
                _require_absent(
                    (
                        ("codegen_request", self.codegen_request),
                        ("baseline_result_id", self.baseline_result_id),
                        ("comparison_result_id", self.comparison_result_id),
                    )
                )
            case "COMPARE":
                _require_present(
                    (
                        ("baseline_result_id", self.baseline_result_id),
                        ("comparison_result_id", self.comparison_result_id),
                    )
                )
                _require_absent(
                    (
                        ("codegen_request", self.codegen_request),
                        ("result_id", self.result_id),
                    )
                )
        return self


class GenerateMql5Success(WireModel):
    """Successful MQL5 toolchain operation result."""

    request_id: Uuid7
    result: CodegenResult | None = None
    package: DeploymentPackage | None = None
    outcome: Literal["SUCCESS"] = "SUCCESS"
    result_version: Literal[1] = 1
    schema_version: Literal[1] = 1


class GenerateTargetsRequest(WireModel):
    """Operation-discriminated additional-target request.

    IMPLEMENT_TARGET requires only ``target``; VALIDATE_TARGET requires
    only ``target_id`` with an optional ``target_version``.
    """

    request_id: Uuid7
    capability_snapshot_id: Uuid7
    operation: Literal["IMPLEMENT_TARGET", "VALIDATE_TARGET"]
    target: CodeTargetDescriptor | None = None
    target_id: NonEmptyStr | None = None
    target_version: int | None = Field(default=None, ge=1)
    schema_version: Literal[1] = 1

    @model_validator(mode="after")
    def validate_operation_shape(self) -> GenerateTargetsRequest:
        """Validate that request fields match the selected operation.

        Returns:
            The validated request.

        Raises:
            ValueError: Required fields are missing or forbidden fields are
                set for the selected operation.
        """
        match self.operation:
            case "IMPLEMENT_TARGET":
                _require_present((("target", self.target),))
                _require_absent(
                    (
                        ("target_id", self.target_id),
                        ("target_version", self.target_version),
                    )
                )
            case "VALIDATE_TARGET":
                _require_present((("target_id", self.target_id),))
                _require_absent((("target", self.target),))
        return self


class GenerateTargetsSuccess(WireModel):
    """Successful additional-target operation result."""

    request_id: Uuid7
    target: CodeTargetDescriptor | None = None
    result: CodegenResult | None = None
    outcome: Literal["SUCCESS"] = "SUCCESS"
    result_version: Literal[1] = 1
    schema_version: Literal[1] = 1


# AstType, NonEmptyStr, and SemverString are PEP 695 ``type`` aliases, not
# classes, so they cannot be registered in WIRE_MODELS.
WIRE_MODELS: dict[str, type[WireModel]] = {
    "StrategyRef": StrategyRef,
    "StrategyVersion": StrategyVersion,
    "StrategyAst": StrategyAst,
    "StrategyNode": StrategyNode,
    "ExpressionNode": ExpressionNode,
    "NodeBinding": NodeBinding,
    "BlockDefinition": BlockDefinition,
    "ParameterDefinition": ParameterDefinition,
    "ChartDefinition": ChartDefinition,
    "DirectionPolicy": DirectionPolicy,
    "VisibilityPolicy": VisibilityPolicy,
    "StrategyValidationReport": StrategyValidationReport,
    "StrategyTemplate": StrategyTemplate,
    "TemplatePlaceholder": TemplatePlaceholder,
    "TemplateSubtreeConstraint": TemplateSubtreeConstraint,
    "StrategyExchangePackage": StrategyExchangePackage,
    "PackageDependency": PackageDependency,
    "AtmExitDefinition": AtmExitDefinition,
    "AtmStage": AtmStage,
    "PartialExitDefinition": PartialExitDefinition,
    "PluginNodeRef": PluginNodeRef,
    "StrategyArchitecture": StrategyArchitecture,
    "RandomGroupVersion": RandomGroupVersion,
    "RandomBlockTemplate": RandomBlockTemplate,
    "OppositeMapVersion": OppositeMapVersion,
    "IndicatorDefinition": IndicatorDefinition,
    "IndicatorOutputLine": IndicatorOutputLine,
    "ExternalIndicatorDefinitionVersion": ExternalIndicatorDefinitionVersion,
    "TargetFragment": TargetFragment,
    "CodeTargetDescriptor": CodeTargetDescriptor,
    "CodegenRequest": CodegenRequest,
    "CodegenResult": CodegenResult,
    "CompilerDiagnostic": CompilerDiagnostic,
    "CodeManifest": CodeManifest,
    "DeploymentPackage": DeploymentPackage,
    "DefineAstRequest": DefineAstRequest,
    "DefineAstSuccess": DefineAstSuccess,
    "CatalogBlocksRequest": CatalogBlocksRequest,
    "CatalogBlocksSuccess": CatalogBlocksSuccess,
    "ConfigureChartsRequest": ConfigureChartsRequest,
    "ConfigureChartsSuccess": ConfigureChartsSuccess,
    "VersionStrategiesRequest": VersionStrategiesRequest,
    "VersionStrategiesSuccess": VersionStrategiesSuccess,
    "EditTemplatesRequest": EditTemplatesRequest,
    "EditTemplatesSuccess": EditTemplatesSuccess,
    "ExchangeStrategiesRequest": ExchangeStrategiesRequest,
    "ExchangeStrategiesSuccess": ExchangeStrategiesSuccess,
    "DefineArchitecturesRequest": DefineArchitecturesRequest,
    "DefineArchitecturesSuccess": DefineArchitecturesSuccess,
    "DefineIndicatorsRequest": DefineIndicatorsRequest,
    "DefineIndicatorsSuccess": DefineIndicatorsSuccess,
    "ModelAtmExitsRequest": ModelAtmExitsRequest,
    "ModelAtmExitsSuccess": ModelAtmExitsSuccess,
    "ExtendPluginNodesRequest": ExtendPluginNodesRequest,
    "ExtendPluginNodesSuccess": ExtendPluginNodesSuccess,
    "GenerateCodeRequest": GenerateCodeRequest,
    "GenerateCodeSuccess": GenerateCodeSuccess,
    "GenerateMql5Request": GenerateMql5Request,
    "GenerateMql5Success": GenerateMql5Success,
    "GenerateTargetsRequest": GenerateTargetsRequest,
    "GenerateTargetsSuccess": GenerateTargetsSuccess,
}
