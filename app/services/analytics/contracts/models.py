"""Analytics schema versioning and contracts support models.

This module defines the versioned dataclasses representing the inputs, reports,
warnings, quality flags, and envelopes used by the Analytics service.
It performs no I/O, network calls, database mutations, broker calls, or trading
side effects.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any, Literal

from app.utils.errors import ValidationError

# Define types for schema version status and capability metadata
SchemaCompatibility = Literal[
    "accepted",
    "deprecated",
    "legacy_adapted",
    "rejected",
    "unsupported_future",
]

SchemaCompatibilityMatrix = Mapping[str, SchemaCompatibility]

CapabilityStability = Literal[
    "stable",
    "approved_experimental",
    "deprecated",
    "internal_support_only",
]

MetricRole = Literal[
    "calculated_fact",
    "diagnostic_estimate",
    "warning_evidence",
    "scorecard_input",
    "non_binding_review_context",
]


@dataclass(frozen=True, slots=True)
class Lineage:
    """Lineage and provenance metadata for traceability.

    Attributes:
        run_id: Unique identification of the execution run.
        strategy_id: Identifier of the strategy being evaluated.
        dataset_hash: Hex hash of the input dataset.
        cost_model: Description or name of the cost/slippage model.
        fill_model: Description or name of the fill/execution model.
        risk_policy_version: Version string of the active risk policy.
        journal_reference: Identifier referencing the trade journal.
        source_metadata: Raw key-value mappings of upstream origin details.
    """

    run_id: str | None = None
    strategy_id: str | None = None
    dataset_hash: str | None = None
    cost_model: str | None = None
    fill_model: str | None = None
    risk_policy_version: str | None = None
    journal_reference: str | None = None
    source_metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class BenchmarkData:
    """Benchmark price and return data for comparison.

    Attributes:
        symbol: The ticker symbol of the benchmark instrument.
        prices: Bounded float prices representing close ticks/bars.
        returns: Calculated chronological float return series.
        timestamps: ISO-8601 timestamps corresponding to points.
        metadata: Trailing dictionary of provider parameters.
    """

    symbol: str
    prices: tuple[float, ...] = ()
    returns: tuple[float, ...] = ()
    timestamps: tuple[str, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class TradingResult:
    """Versioned canonical trading result input contract.

    Attributes:
        schema_version: Semantic version of the result input schema.
        result_id: Unique result identifier.
        environment: Execution phase/environment (backtest, paper, live, etc.).
        account_base_currency: ISO-4217 currency code of the account.
        trades: Tuple of chronological closed trade record dictionaries.
        equity_curve: Chronological list of equity points.
        benchmark: Optional benchmark comparison data descriptor.
        lineage: Detail trace tracking upstream run contexts.
    """

    schema_version: str
    result_id: str
    environment: str
    account_base_currency: str
    trades: tuple[dict[str, Any], ...]
    equity_curve: tuple[dict[str, Any], ...]
    benchmark: BenchmarkData | None = None
    lineage: Lineage = field(default_factory=Lineage)


@dataclass(frozen=True, slots=True)
class ReproducibilityHashes:
    """Hashes of inputs, config, and report for validation and audit.

    Attributes:
        input_hash: Hash computed from canonical TradingResult.
        config_hash: Hash computed from canonical AnalyticsConfig.
        report_hash: Hash computed from report sections.
    """

    input_hash: str | None = None
    config_hash: str | None = None
    report_hash: str | None = None


@dataclass(frozen=True, slots=True)
class AnalyticsWarning:
    """Warning object emitted during analytics compilation.

    Attributes:
        code: Warning code identifying the constraint violated.
        severity: Severity (informational/warning/major/critical/blocker).
        affected_section: Key name of the report section affected.
        source_context: Optional text explaining why this was triggered.
        detail: Mapped dictionary of raw values that triggered the issue.
    """

    code: str
    severity: str
    affected_section: str
    source_context: str | None = None
    detail: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class QualityFlag:
    """Quality flag object emitted during strategy quality scorecard evaluation.

    Attributes:
        code: Quality scorecard flag code.
        severity: Severity level (informational/warning/major/critical/blocker).
        affected_section: Report section context target.
        source_context: Text detail identifying source metrics.
        detail: Key-value metadata of values.
    """

    code: str
    severity: str
    affected_section: str
    source_context: str | None = None
    detail: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class AnalyticsReport:
    """Versioned canonical analytics report contract.

    Attributes:
        schema_version: Semantic version of the report schema.
        report_id: Unique report execution ID.
        report_status: Completeness state ("completed" or "partial").
        sections: Standard dictionary containing computed metrics.
        warnings: Ordered warnings collected during report execution.
        quality_flags: Strategy scorecard quality flags.
        lineage: Full trace lineage referencing inputs.
        hashes: Cryptographic reproducibility hashes.
    """

    schema_version: str
    report_id: str
    report_status: str
    sections: dict[str, Any]
    warnings: tuple[AnalyticsWarning, ...] = ()
    quality_flags: tuple[QualityFlag, ...] = ()
    lineage: Lineage = field(default_factory=Lineage)
    hashes: ReproducibilityHashes = field(default_factory=ReproducibilityHashes)


@dataclass(frozen=True, slots=True)
class PortfolioAnalyticsReport:
    """Versioned portfolio analytics report contract.

    Attributes:
        schema_version: Semantic version of the portfolio report schema.
        portfolio_run_id: Traceable portfolio runtime identification.
        account_base_currency: Normalized account base currency code.
        component_count: Number of strategies or components aggregated.
        aggregate_metrics: Mapping of aggregated metrics.
        warnings: Ordered warnings across all portfolio components.
        lineage: full lineage detail mapping components.
    """

    schema_version: str
    portfolio_run_id: str
    account_base_currency: str
    component_count: int
    aggregate_metrics: dict[str, Any]
    warnings: tuple[AnalyticsWarning, ...] = ()
    lineage: Lineage = field(default_factory=Lineage)


@dataclass(frozen=True, slots=True)
class TruncationMetadata:
    """Metadata describing details of series downsampling.

    Attributes:
        truncated: True if downsampling actually happened.
        original_point_count: Number of points before truncation.
        returned_point_count: Number of points returned in charts.
        truncation_method: Name of the downsampling algorithm.
        truncation_reason: Context description for the downsampling.
    """

    truncated: bool = False
    original_point_count: int = 0
    returned_point_count: int = 0
    truncation_method: str | None = None
    truncation_reason: str | None = None


@dataclass(frozen=True, slots=True)
class DashboardPayload:
    """Versioned dashboard payload contract.

    Attributes:
        schema_version: Semantic version of the dashboard schema.
        charts: Chart-friendly datasets projected from report.
        tables: Tabular summaries projected from report.
        truncation: Indication whether downsampling occurred.
    """

    schema_version: str
    charts: dict[str, Any] = field(default_factory=dict)
    tables: dict[str, Any] = field(default_factory=dict)
    truncation: TruncationMetadata = field(default_factory=TruncationMetadata)


@dataclass(frozen=True, slots=True)
class ErrorPayload:
    """Sanitized standard error payload inside envelopes.

    Attributes:
        code: Normalized string error code.
        message: Safe human-readable error description.
        details: Mapped key-value diagnostics.
    """

    code: str
    message: str
    details: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class ToolEnvelope:
    """Standard success/error envelope wrapper.

    Attributes:
        schema_version: Envelope structure version.
        status: State classification ("success" or "error").
        message: Safe workflow summary message.
        data: Bounded dictionary payload containing results.
        error: Safe error payload detail when failed.
        metadata: Bounded transaction metadata tracing details.
    """

    schema_version: str
    status: Literal["success", "error"]
    message: str
    data: Any | None = None
    error: ErrorPayload | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class MetricDefinition:
    """Approved definition for a metric exposed by analytics.

    Attributes:
        name: Stable metric name matching the catalog key.
        formula: Human-readable formula string.
        units: Metric units (e.g. "percent", "ratio", "currency").
        required_inputs: Required input field names.
        optional_inputs: Optional input field names.
        accepted_aliases: Accepted source-field aliases.
        return_scale: Scale label (e.g. "fraction", "percent").
        annualization_basis: Annualisation basis or None.
        sample_convention: "sample" or "population" convention.
        minimum_sample_size: Minimum sample size before the metric is reliable.
        undefined_behavior: How undefined values must be represented.
        golden_fixture: Expected fixture behaviour for regression tests.
        role: How the metric may be used by reports and scorecards.
        confidence: Confidence label for derived or proxy metrics.
    """

    name: str
    formula: str
    units: str
    required_inputs: tuple[str, ...]
    optional_inputs: tuple[str, ...] = ()
    accepted_aliases: tuple[str, ...] = ()
    return_scale: str = "scalar"
    annualization_basis: str | None = None
    sample_convention: str = "sample"
    minimum_sample_size: int = 1
    undefined_behavior: str = "return None and emit warning metadata"
    golden_fixture: str = "covered by analytics unit tests"
    role: MetricRole = "calculated_fact"
    confidence: Literal["normal", "degraded"] = "normal"


@dataclass(frozen=True, slots=True)
class ToolDefinition:
    """Public analytics tool catalog entry.

    Attributes:
        name: Stable public tool name.
        input_schema: Human-readable input schema summary.
        output_schema: Human-readable output schema summary.
        errors: Stable error codes used by the tool.
        side_effects: Side-effect summary.
        stability: Stability classification.
        agent_api_safe: Whether the tool is safe for agent/API use.
        tests: Test files or usage scripts covering the tool.
    """

    name: str
    input_schema: str
    output_schema: str
    errors: tuple[str, ...]
    side_effects: str
    stability: CapabilityStability
    agent_api_safe: bool
    tests: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class AnalyticsConfig:
    """Deterministic analytics configuration.

    Attributes:
        annualization_periods: Period count used for annualised ratios.
        breakeven_epsilon: Absolute PnL tolerance for breakeven classification.
        monetary_precision_mode: Monetary precision mode used in reports.
        derived_ratio_tolerance: Deterministic tolerance for float ratios.
        max_dashboard_points: Maximum points returned in dashboard series.
        risk_free_rate: Annual risk-free rate used in Sharpe / Sortino.
        min_sample_size: Minimum trades for reliable metric calculation.
    """

    annualization_periods: int = 252
    breakeven_epsilon: float = 1e-9
    monetary_precision_mode: str = "float64_with_tolerance"
    derived_ratio_tolerance: float = 1e-9
    max_dashboard_points: int = 500
    risk_free_rate: float = 0.0
    min_sample_size: int = 30
    metadata: dict[str, Any] = field(default_factory=dict)


# MetricConfig is the approved alias for AnalyticsConfig
MetricConfig = AnalyticsConfig


@dataclass(frozen=True, slots=True)
class MetricResult[T]:
    """Unified wrapper around a single metric calculation outcome.

    Attributes:
        value: The calculated metric value (or None if undefined).
        confidence: Confidence level of the metric ("normal" or "degraded").
        warnings: Warnings emitted specifically for this metric.
    """

    value: T | None
    confidence: Literal["normal", "degraded"] = "normal"
    warnings: tuple[dict[str, Any], ...] = ()


def validate_schema_version(
    version: str,
    matrix: SchemaCompatibilityMatrix,
) -> SchemaCompatibility:
    """Validate a schema version against a compatibility matrix.

    Args:
        version: The schema version string to validate.
        matrix: The mapping of supported schema versions to their status.

    Returns:
        The compatibility status of the validated version.

    Raises:
        ValidationError: If the schema version is explicitly rejected, is an
            unsupported future version, or is not defined in the matrix and
            cannot be resolved to a legacy_adapted version using major.minor.
    """
    status = matrix.get(version)
    if status is not None:
        if status == "rejected":
            msg = f"Schema version {version!r} is explicitly rejected."
            raise ValidationError(msg)
        if status == "unsupported_future":
            msg = (
                f"Schema version {version!r} is a future version "
                "not yet supported by this engine."
            )
            raise ValidationError(msg)
        return status

    # Fallback to check prefix matching (major.minor check)
    for k in matrix:
        if "." in k:
            prefix = k.rsplit(".", 1)[0]
            if version.startswith(prefix):
                return "legacy_adapted"

    msg = (
        f"Unsupported schema version: {version!r}. "
        "Check SCHEMA_COMPATIBILITY_MATRIX for accepted versions."
    )
    raise ValidationError(msg)


@dataclass(frozen=True, slots=True)
class ExplainabilityOutput:
    """Explainability output container (ANL-NFR-280).

    Attributes:
        explained_pnl: Explained PnL component.
        unexplained_pnl: Unexplained PnL component.
        explained_variance_percentage: Explained variance percentage.
        sample_count: Sample count.
        driver_stability: Driver stability metric.
    """

    explained_pnl: float | None = None
    unexplained_pnl: float | None = None
    explained_variance_percentage: float | None = None
    sample_count: int | None = None
    driver_stability: str | None = None


@dataclass(frozen=True, slots=True)
class PrecisionPolicy:
    """Precision policy configurations for rounding and formatting (ANL-NFR-086).

    Attributes:
        monetary_precision_mode: Mode name (e.g. "float64_with_tolerance").
        derived_ratio_tolerance: Decimal precision/tolerance threshold.
    """

    monetary_precision_mode: str = "float64_with_tolerance"
    derived_ratio_tolerance: float = 1e-9


