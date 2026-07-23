"""Private deterministic mechanics for concrete Strategy signal evaluators."""

from __future__ import annotations

import hashlib
import math
from collections.abc import Mapping
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import TYPE_CHECKING, Literal, cast

from app.services.data.contracts import OHLCVRecord
from app.services.strategy.contracts import StrategySignal
from app.utils import canonical_json, logger

if TYPE_CHECKING:
    from app.services.data.contracts import MarketDataset
    from app.services.indicators import IndicatorResult
    from app.services.strategy.contracts import (
        StrategyExecutionContext,
        StrategySignalEvidence,
        ValidatedStrategyConfig,
    )
    from app.services.strategy.contracts._base import JsonValue

_MIN_SERIES_VALUES = 2


class _SignalConfigError(TypeError):
    """Concrete signal configuration is absent or has an invalid type."""


class _SignalDataError(ValueError):
    """Concrete signal market or feature evidence is invalid."""


class _SignalIndicatorError(ValueError):
    """Concrete signal indicator evidence is missing or unavailable."""


@dataclass(frozen=True, slots=True)
class _SignalEvaluatorBase:
    """Immutable registry-bound identity shared by concrete evaluators."""

    strategy_id: str
    strategy_version: str
    module_path: str
    source_hash: str
    artifact_hash: str
    dependency_hash: str


def _parameter(config: ValidatedStrategyConfig, name: str) -> JsonValue:
    """Return one required normalized strategy parameter.

    Args:
        config: Validated strategy configuration.
        name: Required parameter name.

    Returns:
        The normalized JSON-compatible parameter.

    Raises:
        _SignalConfigError: If the required parameter is absent.
    """
    logger.debug("Reading concrete Strategy parameter %s", name)
    if name not in config.normalized_parameters:
        message = f"missing required parameter: {name}"
        raise _SignalConfigError(message)
    return config.normalized_parameters[name]


def _integer_parameter(config: ValidatedStrategyConfig, name: str) -> int:
    """Return one exact integer parameter.

    Args:
        config: Validated strategy configuration.
        name: Required parameter name.

    Returns:
        The exact integer value.

    Raises:
        _SignalConfigError: If the value is not an integer.
    """
    logger.debug("Reading concrete Strategy integer parameter %s", name)
    value = _parameter(config, name)
    if isinstance(value, bool) or not isinstance(value, int):
        message = f"parameter must be an integer: {name}"
        raise _SignalConfigError(message)
    return value


def _decimal_parameter(config: ValidatedStrategyConfig, name: str) -> Decimal:
    """Return one finite decimal-compatible parameter.

    Args:
        config: Validated strategy configuration.
        name: Required parameter name.

    Returns:
        The finite decimal value.

    Raises:
        _SignalConfigError: If the value is Boolean, structured, or non-finite.
    """
    logger.debug("Reading concrete Strategy decimal parameter %s", name)
    value = _parameter(config, name)
    if isinstance(value, bool) or not isinstance(value, str | int | float):
        message = f"parameter must be numeric: {name}"
        raise _SignalConfigError(message)
    try:
        resolved = Decimal(str(value))
    except InvalidOperation as error:
        message = f"parameter must be decimal-compatible: {name}"
        raise _SignalConfigError(message) from error
    if not resolved.is_finite():
        message = f"parameter must be finite: {name}"
        raise _SignalConfigError(message)
    return resolved


def _text_parameter(config: ValidatedStrategyConfig, name: str) -> str:
    """Return one non-empty text parameter.

    Args:
        config: Validated strategy configuration.
        name: Required parameter name.

    Returns:
        The stripped text value.

    Raises:
        _SignalConfigError: If the value is not non-empty text.
    """
    logger.debug("Reading concrete Strategy text parameter %s", name)
    value = _parameter(config, name)
    if not isinstance(value, str) or not value.strip():
        message = f"parameter must be non-empty text: {name}"
        raise _SignalConfigError(message)
    return value.strip()


def _bar_records(market: MarketDataset) -> tuple[OHLCVRecord, ...]:
    """Return exact canonical bars from one market dataset.

    Args:
        market: Data-owned market dataset.

    Returns:
        Ordered canonical bar records.

    Raises:
        _SignalDataError: If the dataset is not a non-empty bar dataset.
    """
    logger.debug("Reading concrete Strategy canonical bar evidence")
    if market.data_kind != "bars" or not market.records:
        raise _SignalDataError("signal evaluation requires non-empty bar data")
    if any(not isinstance(record, OHLCVRecord) for record in market.records):
        raise _SignalDataError("signal evaluation requires canonical OHLCV records")
    return cast("tuple[OHLCVRecord, ...]", market.records)


def _related_market(evidence: StrategySignalEvidence, name: str) -> MarketDataset:
    """Return one required named related market dataset.

    Args:
        evidence: Immutable signal evidence.
        name: Required related-market name.

    Returns:
        The named market dataset.

    Raises:
        _SignalDataError: If the dataset is absent.
    """
    logger.debug("Reading related concrete Strategy market %s", name)
    if name not in evidence.related_markets:
        message = f"missing related market: {name}"
        raise _SignalDataError(message)
    return evidence.related_markets[name]


def _feature_values(
    evidence: StrategySignalEvidence, name: str, minimum: int
) -> tuple[Decimal, ...]:
    """Return one complete named feature sequence.

    Args:
        evidence: Immutable signal evidence.
        name: Required feature name.
        minimum: Minimum required value count.

    Returns:
        The immutable feature sequence.

    Raises:
        _SignalDataError: If the feature is absent or too short.
    """
    logger.debug("Reading concrete Strategy feature %s", name)
    values = evidence.feature_values.get(name)
    if values is None or len(values) < minimum:
        message = f"feature requires at least {minimum} values: {name}"
        raise _SignalDataError(message)
    return values


def _indicator_values(
    indicators: tuple[IndicatorResult, ...],
    *,
    indicator_id: str,
    output_column: str,
) -> tuple[float, ...]:
    """Return one exact ready official indicator column.

    Args:
        indicators: Official indicator results.
        indicator_id: Required official indicator identity.
        output_column: Required canonical output column.

    Returns:
        Ordered finite indicator values.

    Raises:
        _SignalIndicatorError: If the result is absent, ambiguous, or empty.
    """
    logger.debug(
        "Reading concrete Strategy indicator %s column %s",
        indicator_id,
        output_column,
    )
    matches = tuple(
        result
        for result in indicators
        if result.indicator_id == indicator_id
        and output_column in result.output_columns
    )
    if len(matches) != 1:
        message = f"indicator result must resolve exactly once: {output_column}"
        raise _SignalIndicatorError(message)
    raw = tuple(float(item) for item in matches[0].values[output_column].tolist())
    if not raw:
        message = f"indicator result is empty: {output_column}"
        raise _SignalIndicatorError(message)
    return raw


def _current_previous(values: tuple[float, ...], name: str) -> tuple[Decimal, Decimal]:
    """Return the current and previous values from an ordered series.

    Args:
        values: Ordered finite values.
        name: Value name for deterministic errors.

    Returns:
        Current and previous exact decimal projections.

    Raises:
        _SignalIndicatorError: If fewer than two ready values are available.
    """
    logger.debug("Reading current and previous concrete Strategy values for %s", name)
    if len(values) < _MIN_SERIES_VALUES:
        message = f"two values are required: {name}"
        raise _SignalIndicatorError(message)
    if not math.isfinite(values[-1]) or not math.isfinite(values[-2]):
        message = f"indicator result is not ready: {name}"
        raise _SignalIndicatorError(message)
    return Decimal(str(values[-1])), Decimal(str(values[-2]))


def _current_value(values: tuple[float, ...], name: str) -> Decimal:
    """Return the current finite value from an ordered series.

    Args:
        values: Ordered indicator values.
        name: Value name for deterministic errors.

    Returns:
        Current exact decimal projection.

    Raises:
        _SignalIndicatorError: If the current value is absent or unavailable.
    """
    logger.debug("Reading current concrete Strategy value for %s", name)
    if not values or not math.isfinite(values[-1]):
        message = f"indicator result is not ready: {name}"
        raise _SignalIndicatorError(message)
    return Decimal(str(values[-1]))


def _position_tag(magic_number: int, side: str) -> str:
    """Build the recovered magic-number ownership tag convention.

    Args:
        magic_number: Recovered strategy magic number.
        side: Exact uppercase side label.

    Returns:
        Stable ownership tag expected from runtime evidence.
    """
    logger.debug("Building concrete Strategy owned-position tag")
    return f"magic:{magic_number}:{side}"


def _make_signal(
    evaluator: _SignalEvaluatorBase,
    evidence: StrategySignalEvidence,
    config: ValidatedStrategyConfig,
    context: StrategyExecutionContext,
    *,
    signal_name: str,
    side: str,
    active: bool,
    facts: Mapping[str, JsonValue] | None = None,
    lineage: Mapping[str, str] | None = None,
) -> StrategySignal:
    """Build one deterministic active or inactive concrete signal.

    Args:
        evaluator: Immutable concrete evaluator identity.
        evidence: Point-in-time signal evidence.
        config: Validated strategy configuration.
        context: Fixed evaluation context.
        signal_name: Stable recovered signal name.
        side: ``BUY`` or ``SELL``.
        active: Whether the recovered rule is active.
        facts: Optional bounded signal facts.
        lineage: Optional additional lineage references.

    Returns:
        Immutable deterministic signal contract.

    Raises:
        _SignalConfigError: If the side is unsupported.
    """
    logger.debug("Building concrete Strategy signal %s", signal_name)
    if side not in {"BUY", "SELL"}:
        raise _SignalConfigError("signal side must be BUY or SELL")
    resolved_side: Literal["BUY", "SELL"] = "BUY" if side == "BUY" else "SELL"
    bars = _bar_records(evidence.primary_market)
    timestamp = bars[-1].timestamp
    resolved_facts = dict(facts or {})
    resolved_lineage = {
        "evidence_id": evidence.evidence_id,
        "config_hash": config.config_hash,
        "workflow_id": context.workflow_id,
        **dict(lineage or {}),
    }
    material = {
        "strategy_id": evaluator.strategy_id,
        "strategy_version": evaluator.strategy_version,
        "symbol": evidence.primary_market.symbol,
        "timestamp": timestamp,
        "signal_name": signal_name,
        "side": side,
        "active": active,
        "facts": resolved_facts,
        "lineage": resolved_lineage,
    }
    signal_id = hashlib.sha256(canonical_json(material).encode("utf-8")).hexdigest()
    return StrategySignal(
        signal_id=signal_id,
        strategy_id=evaluator.strategy_id,
        strategy_version=evaluator.strategy_version,
        symbol=evidence.primary_market.symbol,
        timestamp=timestamp,
        signal_name=signal_name,
        side=resolved_side,
        active=active,
        facts=resolved_facts,
        lineage=resolved_lineage,
    )


__all__: tuple[str, ...] = ()
