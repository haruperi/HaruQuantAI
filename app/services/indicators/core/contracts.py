"""Immutable calculation-relevant contracts for the Indicators domain.

Defines the frozen configuration, spec, warmup, and structural calculator
contracts shared by every official built-in indicator. These contracts carry
no cache, calendar, backend, actor, tracing, SLO, entitlement, timeout,
cancellation, or orchestration context.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal, Protocol, runtime_checkable

if TYPE_CHECKING:
    from app.services.data.contracts import MarketDataset
    from app.services.indicators.core.results import IndicatorResult


@dataclass(frozen=True, slots=True)
class IndicatorConfig:
    """Immutable, calculation-relevant batch configuration.

    Attributes:
        indicator_id: Exact lowercase official registry identifier; must
            match the called wrapper.
        parameters: Canonical key-sorted immutable parameter pairs; duplicate
            keys are invalid.
        source: Selected price source among ``open``, ``high``, ``low``, or
            ``close``; ``None`` for fixed-OHLC indicators.
        formula_version: Version of the approved mathematical convention;
            must equal the selected official spec.
        output_mode: Core output mode; only ``"values"`` is supported.
        column_conflict_policy: Output-collision policy; only ``"error"`` is
            supported.
        precision_dtype: Numerical output dtype; only ``"float64"`` is
            supported.
        availability_policy: Availability basis; only
            ``"source_available_at"`` is supported.
        quality_policy: Quality propagation policy; only
            ``"propagate_dataset"`` is supported.
        error_mode: Failure policy; only ``"raise"`` is supported.
    """

    indicator_id: str
    parameters: tuple[tuple[str, int | float | str], ...]
    source: str | None
    formula_version: str
    output_mode: Literal["values"]
    column_conflict_policy: Literal["error"]
    precision_dtype: Literal["float64"]
    availability_policy: Literal["source_available_at"]
    quality_policy: Literal["propagate_dataset"]
    error_mode: Literal["raise"]


@dataclass(frozen=True, slots=True)
class IndicatorSpec:
    """Immutable public metadata describing one official indicator.

    Attributes:
        indicator_id: Stable lowercase official registry identifier.
        name: Human-readable indicator name.
        indicator_version: Public implementation version.
        formula_version: Version of the approved mathematical convention.
        tier: Review tier; only ``"core_mvp"`` is supported.
        required_columns: Fixed OHLC columns or the ``"source"`` placeholder,
            resolved before calculation.
        parameter_schema: Frozen JSON-compatible parameter schema mapping.
        output_templates: Deterministic output-name templates in canonical
            order.
        warmup_policy: Declared warmup convention for the indicator.
            ``"none"`` marks an indicator valid from the first row (no
            warmup); ``"custom"`` marks a formula-specific warmup count
            documented in the owning README formula table rather than a
            simple multiple of ``period``.
        vectorized: Always ``True``; batch/vectorized is the only supported
            execution mode.
        multi_symbol: Always ``False``; no official calculation accepts more
            than one symbol.
        multi_timeframe: Always ``False``; multi-timeframe combination is an
            orchestrator responsibility.
        import_path: Stable dotted import path to the official callable.
        stability: Public API stability marker; only ``"stable"`` is
            supported.
        workflow_eligibility: Official workflow IDs this indicator is
            eligible for.
    """

    indicator_id: str
    name: str
    indicator_version: str
    formula_version: str
    tier: Literal["core_mvp"]
    required_columns: tuple[str, ...]
    parameter_schema: Mapping[str, object]
    output_templates: tuple[str, ...]
    warmup_policy: Literal["period", "period_plus_one", "two_period", "none", "custom"]
    vectorized: Literal[True]
    multi_symbol: Literal[False]
    multi_timeframe: Literal[False]
    import_path: str
    stability: Literal["stable"]
    workflow_eligibility: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class WarmupRequirement:
    """Exact normalized history requirement for an indicator/config.

    Describes the minimum history an indicator/config combination requires
    without fetching data.

    Attributes:
        indicator_id: Stable lowercase official registry identifier.
        formula_version: Version of the approved mathematical convention.
        minimum_observations: Minimum number of source observations required
            before any valid output is produced.
        source_timeframe: Required exact source timeframe, or ``None`` when
            any timeframe is accepted.
        required_columns: Fixed OHLC columns or the ``"source"`` placeholder.
        availability_basis: Availability basis; only
            ``"source_available_at"`` is supported.
    """

    indicator_id: str
    formula_version: str
    minimum_observations: int
    source_timeframe: str | None
    required_columns: tuple[str, ...]
    availability_basis: Literal["source_available_at"]


@runtime_checkable
class IndicatorProtocol(Protocol):
    """Minimal structural registered-calculator protocol.

    Public convenience wrappers construct their own ``IndicatorConfig`` and
    are not required to share this internal signature.
    """

    def calculate(
        self, data: MarketDataset, config: IndicatorConfig
    ) -> IndicatorResult:
        """Calculate one official indicator for a normalized dataset.

        Args:
            data: One normalized, immutable ``MarketDataset v1`` for a single
                symbol/timeframe.
            config: Complete, validated calculation configuration.

        Returns:
            The deterministic ``IndicatorResult`` for the supplied dataset.

        Raises:
            IndicatorError: On deterministic request or calculation failure
                under the approved error mode.
        """
        ...


__all__ = [
    "IndicatorConfig",
    "IndicatorProtocol",
    "IndicatorSpec",
    "WarmupRequirement",
]
