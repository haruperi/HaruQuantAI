"""Immutable canonical Analytics input, evidence, and output contracts."""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from datetime import datetime, timedelta
from decimal import Decimal
from types import MappingProxyType
from typing import Literal

from pydantic import ConfigDict
from pydantic.dataclasses import dataclass

from app.services.analytics.contracts.catalogs import EVIDENCE_CATALOG
from app.services.analytics.contracts.errors import AnalyticsValidationError
from app.utils import logger

ANALYTICS_SCHEMA_VERSION = "v1"
_SHA256_LENGTH = 64


def _require_cataloged_code(
    code: str,
    severity: str,
    *,
    namespace: str,
) -> Mapping[str, object]:
    """Validate one evidence code and severity against the Evidence Catalog.

    Args:
        code: Candidate warning or quality-flag code.
        severity: Candidate severity for that code.
        namespace: Catalog namespace, ``warnings`` or ``quality_flags``.

    Returns:
        The authoritative catalog definition for the code.

    Raises:
        AnalyticsValidationError: If the code is uncataloged or the severity
            conflicts with the cataloged severity.
    """
    logger.debug("Validating Analytics evidence code against the catalog")
    definition = EVIDENCE_CATALOG[namespace].get(code)
    if definition is None:
        message = f"uncataloged {namespace} code: {code}"
        raise AnalyticsValidationError(message)
    if severity != definition["severity"]:
        message = f"severity conflicts with the catalog for code: {code}"
        raise AnalyticsValidationError(message)
    return definition


def _require_text(value: str, field_name: str) -> str:
    """Validate required trimmed text.

    Args:
        value: Candidate text.
        field_name: Field name used in failures.

    Returns:
        Validated text.

    Raises:
        AnalyticsValidationError: If the value is blank or untrimmed.
    """
    logger.debug("Validating Analytics text field")
    if not value or value != value.strip():
        message = f"{field_name} must be non-empty trimmed text"
        raise AnalyticsValidationError(message)
    return value


def _require_utc(value: datetime, field_name: str) -> datetime:
    """Validate an aware UTC timestamp.

    Args:
        value: Candidate timestamp.
        field_name: Field name used in failures.

    Returns:
        Validated UTC timestamp.

    Raises:
        AnalyticsValidationError: If the timestamp is not aware UTC.
    """
    logger.debug("Validating Analytics UTC timestamp")
    if value.tzinfo is None or value.utcoffset() != timedelta(0):
        message = f"{field_name} must be aware UTC"
        raise AnalyticsValidationError(message)
    return value


def _require_decimal(value: object, field_name: str) -> Decimal:
    """Validate one exact finite Decimal.

    Args:
        value: Candidate value.
        field_name: Field name used in failures.

    Returns:
        Validated finite Decimal.

    Raises:
        AnalyticsValidationError: If the value is not an exact finite Decimal.
    """
    logger.debug("Validating Analytics Decimal field")
    if not isinstance(value, Decimal) or not value.is_finite():
        message = f"{field_name} must be a finite Decimal"
        raise AnalyticsValidationError(message)
    return value


def _validate_finite_scalar(value: object, path: str) -> bool:
    """Validate a scalar and report whether it was recognized.

    Args:
        value: Candidate scalar.
        path: Diagnostic path.

    Returns:
        Whether the value is a supported scalar.

    Raises:
        AnalyticsValidationError: If a recognized number is non-finite.
    """
    logger.debug("Validating finite Analytics scalar evidence")
    if value is None or isinstance(value, (str, bool, int, datetime)):
        return True
    if isinstance(value, Decimal):
        if not value.is_finite():
            message = f"{path} contains a non-finite Decimal"
            raise AnalyticsValidationError(message)
        return True
    if isinstance(value, float):
        if not math.isfinite(value):
            message = f"{path} contains a non-finite float"
            raise AnalyticsValidationError(message)
        return True
    return False


def _validate_finite(value: object, path: str = "value") -> None:
    """Recursively validate finite report evidence.

    Args:
        value: Candidate nested evidence.
        path: Diagnostic path.

    Raises:
        AnalyticsValidationError: If an unsupported or non-finite value is found.
    """
    logger.debug("Validating finite Analytics evidence")
    if _validate_finite_scalar(value, path):
        return
    if isinstance(value, Mapping):
        for key, item in value.items():
            if not isinstance(key, str):
                message = f"{path} contains a non-string key"
                raise AnalyticsValidationError(message)
            _validate_finite(item, f"{path}.{key}")
        return
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for index, item in enumerate(value):
            _validate_finite(item, f"{path}[{index}]")
        return
    message = f"{path} contains unsupported evidence"
    raise AnalyticsValidationError(message)


def _freeze_mapping(value: Mapping[str, object]) -> Mapping[str, object]:
    """Return an immutable shallow mapping copy.

    Args:
        value: Source mapping.

    Returns:
        Immutable mapping copy.
    """
    logger.debug("Freezing Analytics mapping evidence")
    _validate_finite(value)
    return MappingProxyType(dict(value))


@dataclass(config=ConfigDict(frozen=True, extra="forbid"))
class AnalyticsWarning:
    """Bounded catalog-backed Analytics warning evidence."""

    code: str
    severity: str
    affected_section: str
    source_context: str
    detail: Mapping[str, object]

    def __post_init__(self) -> None:
        """Validate warning identity and detail.

        Raises:
            AnalyticsValidationError: If the code is uncataloged or the
                severity conflicts with the cataloged severity.
        """
        logger.debug("Validating Analytics warning contract")
        for name in ("code", "severity", "affected_section", "source_context"):
            _require_text(getattr(self, name), name)
        _require_cataloged_code(self.code, self.severity, namespace="warnings")
        object.__setattr__(self, "detail", _freeze_mapping(self.detail))


@dataclass(config=ConfigDict(frozen=True, extra="forbid"))
class QualityFlag:
    """Non-governing quality evidence with explicit blocker semantics."""

    code: str
    severity: str
    blocker: bool
    affected_sections: tuple[str, ...]
    source_context: str
    detail: Mapping[str, object]

    def __post_init__(self) -> None:
        """Validate quality-flag evidence.

        Raises:
            AnalyticsValidationError: If required evidence is missing, the code
                is uncataloged, or the severity or blocker semantics conflict
                with the Evidence Catalog.
        """
        logger.debug("Validating Analytics quality flag contract")
        _require_text(self.code, "code")
        _require_text(self.severity, "severity")
        _require_text(self.source_context, "source_context")
        if not self.affected_sections:
            raise AnalyticsValidationError("affected_sections must not be empty")
        for section in self.affected_sections:
            _require_text(section, "affected_section")
        definition = _require_cataloged_code(
            self.code, self.severity, namespace="quality_flags"
        )
        if self.blocker != definition["blocker"]:
            message = f"blocker conflicts with the catalog for code: {self.code}"
            raise AnalyticsValidationError(message)
        object.__setattr__(self, "detail", _freeze_mapping(self.detail))


@dataclass(config=ConfigDict(frozen=True, extra="forbid"))
class Lineage:
    """Bounded source, version, currency, and transformation lineage."""

    source_contract: str
    source_version: str
    source_schema_id: str
    source_ids: tuple[str, ...]
    configuration_sources: tuple[str, ...]
    account_currency: str
    transformations: tuple[str, ...]

    def __post_init__(self) -> None:
        """Validate required lineage values.

        Raises:
            AnalyticsValidationError: If required lineage is missing.
        """
        logger.debug("Validating Analytics lineage contract")
        for name in (
            "source_contract",
            "source_version",
            "source_schema_id",
            "account_currency",
        ):
            _require_text(getattr(self, name), name)
        if not self.source_ids:
            raise AnalyticsValidationError("source_ids must not be empty")
        for item in (
            *self.source_ids,
            *self.configuration_sources,
            *self.transformations,
        ):
            _require_text(item, "lineage item")


@dataclass(config=ConfigDict(frozen=True, extra="forbid"))
class ReproducibilityHashes:
    """SHA-256 identities for reproducible Analytics evidence."""

    input_hash: str
    configuration_hash: str
    trade_ledger_hash: str
    equity_curve_hash: str
    benchmark_hash: str | None = None
    report_hash: str | None = None

    def __post_init__(self) -> None:
        """Validate every supplied SHA-256 digest.

        Raises:
            AnalyticsValidationError: If a digest is malformed.
        """
        logger.debug("Validating Analytics reproducibility hashes")
        for value in (
            self.input_hash,
            self.configuration_hash,
            self.trade_ledger_hash,
            self.equity_curve_hash,
            self.benchmark_hash,
            self.report_hash,
        ):
            if value is None:
                continue
            if len(value) != _SHA256_LENGTH or any(
                character not in "0123456789abcdef" for character in value
            ):
                raise AnalyticsValidationError("hash must be lowercase SHA-256")


@dataclass(config=ConfigDict(frozen=True, extra="forbid"))
class RiskFreeRateEvidence:
    """Caller-supplied source-backed annual risk-free rate."""

    rate: Decimal
    unit: Literal["annual_decimal"]
    source: str
    as_of: datetime

    def __post_init__(self) -> None:
        """Validate risk-free-rate source, unit, and value."""
        logger.debug("Validating Analytics risk-free-rate evidence")
        _require_decimal(self.rate, "rate")
        _require_text(self.source, "source")
        _require_utc(self.as_of, "as_of")


@dataclass(config=ConfigDict(frozen=True, extra="forbid"))
class StatisticalValidationConfig:
    """Deterministic statistical-validation invocation settings."""

    seed: int
    bootstrap_iterations: int
    permutation_iterations: int
    confidence: float
    alpha: float

    def __post_init__(self) -> None:
        """Validate statistical settings.

        Raises:
            AnalyticsValidationError: If an iteration or probability is invalid.
        """
        logger.debug("Validating Analytics statistical configuration")
        if self.bootstrap_iterations <= 0 or self.permutation_iterations <= 0:
            raise AnalyticsValidationError("statistical iterations must be positive")
        if not 0.0 < self.confidence < 1.0 or not 0.0 < self.alpha < 1.0:
            raise AnalyticsValidationError(
                "confidence and alpha must be between zero and one"
            )


@dataclass(config=ConfigDict(frozen=True, extra="forbid"))
class AnalyticsRunConfig:
    """Required fail-closed Analytics limits and calculation settings."""

    max_warning_detail_bytes: int
    max_trades: int
    max_equity_points: int
    max_benchmark_points: int
    max_statistical_observations: int
    max_bootstrap_iterations: int
    max_permutation_iterations: int
    max_portfolio_components: int
    max_response_bytes: int
    risk_free_rate: RiskFreeRateEvidence | None
    statistics: StatisticalValidationConfig

    def __post_init__(self) -> None:
        """Validate required bounds and configured iteration ceilings.

        Raises:
            AnalyticsValidationError: If a bound is invalid or exceeded.
        """
        logger.debug("Validating Analytics runtime configuration")
        bounds = (
            self.max_warning_detail_bytes,
            self.max_trades,
            self.max_equity_points,
            self.max_benchmark_points,
            self.max_statistical_observations,
            self.max_bootstrap_iterations,
            self.max_permutation_iterations,
            self.max_portfolio_components,
            self.max_response_bytes,
        )
        if any(value <= 0 for value in bounds):
            raise AnalyticsValidationError("every Analytics bound must be positive")
        if self.statistics.bootstrap_iterations > self.max_bootstrap_iterations:
            raise AnalyticsValidationError(
                "bootstrap iterations exceed configured bound"
            )
        if self.statistics.permutation_iterations > self.max_permutation_iterations:
            raise AnalyticsValidationError(
                "permutation iterations exceed configured bound"
            )


@dataclass(config=ConfigDict(frozen=True, extra="forbid"))
class ClosedTrade:
    """One immutable closed trade in the Analytics-owned ledger schema."""

    ticket: str
    symbol: str
    type: Literal["BUY", "SELL"]
    volume: Decimal
    entry_time: datetime
    entry_price: Decimal
    stop_loss: Decimal | None
    take_profit: Decimal | None
    exit_time: datetime
    exit_price: Decimal
    comment: str
    commission: Decimal
    swap: Decimal
    profit: Decimal
    magic: str
    mae: Decimal | None
    mfe: Decimal | None

    def __post_init__(self) -> None:
        """Validate exact closed-trade semantics.

        Raises:
            AnalyticsValidationError: If identity, numeric, or time evidence fails.
        """
        logger.debug("Validating Analytics closed trade")
        for name in ("ticket", "symbol", "comment", "magic"):
            _require_text(getattr(self, name), name)
        for name in (
            "volume",
            "entry_price",
            "exit_price",
            "commission",
            "swap",
            "profit",
        ):
            _require_decimal(getattr(self, name), name)
        for name in ("stop_loss", "take_profit", "mae", "mfe"):
            value = getattr(self, name)
            if value is not None:
                _require_decimal(value, name)
        self._validate_numeric_semantics()
        _require_utc(self.entry_time, "entry_time")
        _require_utc(self.exit_time, "exit_time")
        if self.exit_time < self.entry_time:
            raise AnalyticsValidationError("exit_time precedes entry_time")

    def _validate_numeric_semantics(self) -> None:
        """Validate positive prices and signed excursion semantics.

        Raises:
            AnalyticsValidationError: If numeric trade semantics are invalid.
        """
        logger.debug("Validating Analytics closed-trade numeric semantics")
        if self.volume <= 0 or self.entry_price <= 0 or self.exit_price <= 0:
            raise AnalyticsValidationError(
                "volume and entry/exit prices must be positive"
            )
        if self.stop_loss is not None and self.stop_loss <= 0:
            raise AnalyticsValidationError("stop_loss must be positive when supplied")
        if self.take_profit is not None and self.take_profit <= 0:
            raise AnalyticsValidationError("take_profit must be positive when supplied")
        if self.mae is not None and self.mae > 0:
            raise AnalyticsValidationError("mae must be non-positive")
        if self.mfe is not None and self.mfe < 0:
            raise AnalyticsValidationError("mfe must be non-negative")

    @property
    def net_trade_pnl(self) -> Decimal:
        """Return gross profit plus signed commission and swap.

        Returns:
            Exact net trade profit or loss.
        """
        logger.debug("Calculating Analytics net trade PnL")
        return self.profit + self.commission + self.swap


@dataclass(config=ConfigDict(frozen=True, extra="forbid", arbitrary_types_allowed=True))
class TradingResult:
    """Canonical producer-neutral Analytics calculation input."""

    contract_version: Literal["v1"]
    schema_id: Literal["analytics.trading_result.v1"]
    source_contract: str
    source_contract_version: str
    source_schema_id: str
    source_id: str
    phase: str
    window_start: datetime
    window_end: datetime
    account_currency: str
    initial_balance: Decimal
    strategy_id: str
    strategy_version: str
    symbols: tuple[str, ...]
    timeframe: str
    trades: tuple[ClosedTrade, ...]
    equity_curve: tuple[Mapping[str, object], ...]
    daily_equity_curve: tuple[Mapping[str, object], ...]
    curve_basis: Literal["closed_trade"]
    benchmark: Mapping[str, object] | None
    fx_evidence: Mapping[str, object] | None
    quality_metadata: Mapping[str, object]
    source_metadata: Mapping[str, object]
    lineage: Lineage

    def __post_init__(self) -> None:
        """Validate canonical Analytics input invariants.

        Raises:
            AnalyticsValidationError: If required canonical evidence is invalid.
        """
        logger.debug("Validating Analytics trading result")
        for name in (
            "source_contract",
            "source_contract_version",
            "source_schema_id",
            "source_id",
            "phase",
            "account_currency",
            "strategy_id",
            "strategy_version",
            "timeframe",
        ):
            _require_text(getattr(self, name), name)
        _require_utc(self.window_start, "window_start")
        _require_utc(self.window_end, "window_end")
        if self.window_end < self.window_start:
            raise AnalyticsValidationError("result window is unordered")
        _require_decimal(self.initial_balance, "initial_balance")
        if self.initial_balance <= 0:
            raise AnalyticsValidationError("initial_balance must be positive")
        if not self.trades or not self.symbols:
            raise AnalyticsValidationError("trades and symbols must not be empty")
        object.__setattr__(
            self, "quality_metadata", _freeze_mapping(self.quality_metadata)
        )
        object.__setattr__(
            self, "source_metadata", _freeze_mapping(self.source_metadata)
        )
        if self.benchmark is not None:
            object.__setattr__(self, "benchmark", _freeze_mapping(self.benchmark))
        if self.fx_evidence is not None:
            object.__setattr__(self, "fx_evidence", _freeze_mapping(self.fx_evidence))


@dataclass(config=ConfigDict(frozen=True, extra="forbid", arbitrary_types_allowed=True))
class MetricEvidence:
    """Finite calculated, undefined, or skipped metric evidence."""

    metric_key: str
    status: Literal["calculated", "undefined", "skipped"]
    value: object
    unit: str
    confidence: Mapping[str, object] | None = None
    warnings: tuple[AnalyticsWarning, ...] = ()
    source_context: str = "all"

    def __post_init__(self) -> None:
        """Validate metric status, value, and source context.

        Raises:
            AnalyticsValidationError: If status and evidence conflict.
        """
        logger.debug("Validating Analytics metric evidence")
        _require_text(self.metric_key, "metric_key")
        _require_text(self.unit, "unit")
        _require_text(self.source_context, "source_context")
        if self.status == "calculated" and self.value is None:
            raise AnalyticsValidationError("calculated metric requires a value")
        if self.status != "calculated" and self.value is not None:
            raise AnalyticsValidationError(
                "undefined or skipped metric value must be None"
            )
        _validate_finite(self.value)
        if self.confidence is not None:
            object.__setattr__(self, "confidence", _freeze_mapping(self.confidence))


@dataclass(config=ConfigDict(frozen=True, extra="forbid"))
class SectionEvidence:
    """Ordered evidence for one report section."""

    section_key: str
    criticality: Literal["required", "optional"]
    metrics: tuple[MetricEvidence, ...]
    status: Literal["completed", "degraded", "skipped", "failed"]
    warnings: tuple[AnalyticsWarning, ...] = ()
    reason: str | None = None

    def __post_init__(self) -> None:
        """Validate section status and included evidence.

        Raises:
            AnalyticsValidationError: If status and section evidence conflict.
        """
        logger.debug("Validating Analytics section evidence")
        _require_text(self.section_key, "section_key")
        if self.status in {"skipped", "failed"} and not self.reason:
            raise AnalyticsValidationError(
                "skipped or failed section requires a reason"
            )
        if self.status in {"completed", "degraded"} and not self.metrics:
            raise AnalyticsValidationError(
                "completed or degraded section requires metrics"
            )


@dataclass(config=ConfigDict(frozen=True, extra="forbid", arbitrary_types_allowed=True))
class PerformanceReport:
    """Analytics-owned non-binding cross-domain performance report v1."""

    contract_version: Literal["v1"]
    schema_id: Literal["analytics.performance_report.v1"]
    report_id: str
    request_id: str
    created_at: datetime
    account_currency: str
    sections: tuple[SectionEvidence, ...]
    caveats: tuple[AnalyticsWarning, ...]
    quality_flags: tuple[QualityFlag, ...]
    lineage: Lineage
    hashes: ReproducibilityHashes
    precision_metadata: Mapping[str, object]
    non_binding: Literal[True] = True

    def __post_init__(self) -> None:
        """Validate report identity, ordering, and finite metadata.

        Raises:
            AnalyticsValidationError: If the report is incomplete or unsafe.
        """
        logger.debug("Validating Analytics performance report")
        for name in ("report_id", "request_id", "account_currency"):
            _require_text(getattr(self, name), name)
        _require_utc(self.created_at, "created_at")
        if not self.sections:
            raise AnalyticsValidationError("report sections must not be empty")
        object.__setattr__(
            self, "precision_metadata", _freeze_mapping(self.precision_metadata)
        )


@dataclass(config=ConfigDict(frozen=True, extra="forbid"))
class PortfolioPerformanceReport:
    """Analytics-internal currency-safe portfolio performance report."""

    schema_id: Literal["analytics.portfolio_performance_report.v1"]
    report_id: str
    component_report_ids: tuple[str, ...]
    measurement_start: datetime
    measurement_end: datetime
    base_currency: str
    sections: tuple[SectionEvidence, ...]
    caveats: tuple[AnalyticsWarning, ...]
    quality_flags: tuple[QualityFlag, ...]
    fx_lineage: Lineage
    hashes: ReproducibilityHashes
    non_binding: Literal[True] = True

    def __post_init__(self) -> None:
        """Validate portfolio aggregation evidence.

        Raises:
            AnalyticsValidationError: If portfolio evidence is incomplete.
        """
        logger.debug("Validating Analytics portfolio report")
        _require_text(self.report_id, "report_id")
        _require_text(self.base_currency, "base_currency")
        _require_utc(self.measurement_start, "measurement_start")
        _require_utc(self.measurement_end, "measurement_end")
        if self.measurement_end < self.measurement_start:
            raise AnalyticsValidationError("portfolio measurement window is unordered")
        if not self.component_report_ids or not self.sections:
            raise AnalyticsValidationError("portfolio report is incomplete")


@dataclass(config=ConfigDict(frozen=True, extra="forbid", arbitrary_types_allowed=True))
class DashboardPayload:
    """Bounded non-binding dashboard projection contract v1."""

    contract_version: Literal["v1"]
    schema_id: Literal["analytics.dashboard_payload.v1"]
    payload_id: str
    report_id: str
    generated_at: datetime
    sections: tuple[Mapping[str, object], ...]
    warnings: tuple[AnalyticsWarning, ...]
    quality_flags: tuple[QualityFlag, ...]
    units: Mapping[str, str]
    truncation_metadata: tuple[Mapping[str, object], ...]
    non_binding: Literal[True] = True

    def __post_init__(self) -> None:
        """Validate dashboard identity and finite payload values."""
        logger.debug("Validating Analytics dashboard payload")
        _require_text(self.payload_id, "payload_id")
        _require_text(self.report_id, "report_id")
        _require_utc(self.generated_at, "generated_at")
        _validate_finite(self.sections)
        _validate_finite(self.units)
        _validate_finite(self.truncation_metadata)


@dataclass(config=ConfigDict(frozen=True, extra="forbid", arbitrary_types_allowed=True))
class PortfolioAllocationEvidence:
    """Non-binding portfolio allocation evidence contract v1."""

    contract_version: Literal["v1"]
    schema_id: Literal["analytics.portfolio_allocation_evidence.v1"]
    evidence_id: str
    allocation_reference: str
    result_references: tuple[str, ...]
    measurement_start: datetime
    measurement_end: datetime
    base_currency: str
    component_metrics: tuple[Mapping[str, object], ...]
    aggregate_metrics: tuple[MetricEvidence, ...]
    dependence_evidence: SectionEvidence
    concentration_evidence: SectionEvidence
    caveats: tuple[AnalyticsWarning, ...]
    fx_lineage: Lineage
    non_binding: Literal[True] = True

    def __post_init__(self) -> None:
        """Validate allocation evidence identity, window, and finite values.

        Raises:
            AnalyticsValidationError: If allocation evidence is incomplete.
        """
        logger.debug("Validating Analytics portfolio allocation evidence")
        _require_text(self.evidence_id, "evidence_id")
        _require_text(self.allocation_reference, "allocation_reference")
        _require_text(self.base_currency, "base_currency")
        _require_utc(self.measurement_start, "measurement_start")
        _require_utc(self.measurement_end, "measurement_end")
        if self.measurement_end < self.measurement_start:
            raise AnalyticsValidationError("allocation measurement window is unordered")
        if not self.result_references or not self.component_metrics:
            raise AnalyticsValidationError("allocation evidence is incomplete")
        _validate_finite(self.component_metrics)


__all__ = [
    "ANALYTICS_SCHEMA_VERSION",
    "AnalyticsRunConfig",
    "AnalyticsWarning",
    "ClosedTrade",
    "DashboardPayload",
    "Lineage",
    "MetricEvidence",
    "PerformanceReport",
    "PortfolioAllocationEvidence",
    "PortfolioPerformanceReport",
    "QualityFlag",
    "ReproducibilityHashes",
    "RiskFreeRateEvidence",
    "SectionEvidence",
    "StatisticalValidationConfig",
    "TradingResult",
]
