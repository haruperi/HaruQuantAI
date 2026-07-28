"""Atomic hash-bound boundary for concrete Strategy signal evaluators."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from app.services.indicators import IndicatorError
from app.services.strategy.contracts import StrategySignal
from app.services.strategy.contracts.outcomes import failure, success
from app.services.strategy.contracts.responses import (
    StrategyOperationError,
    guard_strategy_boundary,
    unwrap_evaluator_result,
)
from app.services.strategy.diagnostics import StrategyErrorCode
from app.services.strategy.signals._mechanics import (
    _bar_records,
    _SignalConfigError,
    _SignalDataError,
    _SignalIndicatorError,
)
from app.utils import get_logger

type StandardResponse[T] = Any

logger = get_logger(__name__)

if TYPE_CHECKING:
    from app.services.indicators import IndicatorResult
    from app.services.strategy.contracts import (
        StrategyExecutionContext,
        StrategySignalEvidence,
        ValidatedStrategyConfig,
        ValidatedStrategyRef,
    )
    from app.services.strategy.signals.protocol import SignalEvaluator


def _validate_identity(
    ref: ValidatedStrategyRef,
    config: ValidatedStrategyConfig,
    evaluator: SignalEvaluator,
    context: StrategyExecutionContext,
) -> None:
    """Validate evaluator, registry, and configuration identity.

    Args:
        ref: Exact validated registry reference.
        config: Exact validated configuration.
        evaluator: Concrete evaluator identity.
        context: Fixed trace context.

    """
    logger.debug("Validating concrete Strategy evaluator identity")
    manifest = ref.manifest
    if (
        evaluator.strategy_id != manifest.strategy_id
        or evaluator.strategy_version != manifest.strategy_version
        or evaluator.module_path != manifest.module_path
    ):
        failure(
            StrategyErrorCode.UNAPPROVED_MODULE,
            "concrete signal evaluator identity does not match registry",
            request_id=context.request_id,
            correlation_id=context.correlation_id,
        )
    if (
        evaluator.source_hash != manifest.source_hash
        or evaluator.artifact_hash != manifest.artifact_hash
    ):
        failure(
            StrategyErrorCode.ARTIFACT_HASH_MISMATCH,
            "concrete signal evaluator artifact identity does not match registry",
            request_id=context.request_id,
            correlation_id=context.correlation_id,
        )
    if evaluator.dependency_hash != manifest.dependency_hash:
        failure(
            StrategyErrorCode.DEPENDENCY_HASH_MISMATCH,
            "concrete signal evaluator dependency identity does not match registry",
            request_id=context.request_id,
            correlation_id=context.correlation_id,
        )
    if (
        config.strategy_id != manifest.strategy_id
        or config.strategy_version != manifest.strategy_version
    ):
        failure(
            StrategyErrorCode.INVALID_CONFIG,
            "concrete signal configuration identity does not match registry",
            request_id=context.request_id,
            correlation_id=context.correlation_id,
        )


def _validate_evidence(
    evidence: StrategySignalEvidence,
    indicators: tuple[IndicatorResult, ...],
    context: StrategyExecutionContext,
) -> None:
    """Validate point-in-time market, feature, and indicator evidence.

    Args:
        evidence: Concrete signal evidence.
        indicators: Official indicator results.
        context: Fixed evaluation context.

    """
    logger.debug("Validating concrete Strategy point-in-time evidence")
    try:
        primary_bars = _bar_records(evidence.primary_market)
    except _SignalDataError:
        failure(
            StrategyErrorCode.DATA_NOT_READY,
            "concrete signal primary market is not ready",
            request_id=context.request_id,
            correlation_id=context.correlation_id,
        )
    signal_time = primary_bars[-1].available_at
    if (
        primary_bars[-1].timestamp > context.decision_timestamp
        or signal_time > context.decision_timestamp
        or evidence.primary_market.available_at > context.decision_timestamp
    ):
        failure(
            StrategyErrorCode.LOOKAHEAD_DETECTED,
            "concrete signal primary market contains future evidence",
            request_id=context.request_id,
            correlation_id=context.correlation_id,
        )
    try:
        related_future = any(
            any(record.available_at > signal_time for record in _bar_records(market))
            for market in evidence.related_markets.values()
        )
    except _SignalDataError:
        failure(
            StrategyErrorCode.DATA_NOT_READY,
            "concrete signal related market is not ready",
            request_id=context.request_id,
            correlation_id=context.correlation_id,
        )
    feature_future = any(
        available_at > signal_time
        for available_at in evidence.feature_available_at.values()
    )
    if related_future or feature_future:
        failure(
            StrategyErrorCode.LOOKAHEAD_DETECTED,
            "concrete signal related evidence was unavailable at signal time",
            request_id=context.request_id,
            correlation_id=context.correlation_id,
        )
    try:
        for indicator in indicators:
            joined = indicator.join_to(evidence.primary_market)
            if isinstance(joined, StandardResponse) and joined.status == "error":
                upstream_code = (
                    joined.error.code
                    if joined.error is not None
                    else "INVALID_RESPONSE"
                )
                failure(
                    StrategyErrorCode.INDICATOR_MODULE_ERROR,
                    "concrete signal indicator join failed",
                    details={"upstream_code": upstream_code},
                    request_id=context.request_id,
                    correlation_id=context.correlation_id,
                )
            available = indicator.values_only["available_at"]
            if any(
                item.to_pydatetime() > context.decision_timestamp for item in available
            ):
                failure(
                    StrategyErrorCode.LOOKAHEAD_DETECTED,
                    "concrete signal indicator contains future evidence",
                    request_id=context.request_id,
                    correlation_id=context.correlation_id,
                )
    except IndicatorError:
        failure(
            StrategyErrorCode.INDICATOR_MODULE_ERROR,
            "concrete signal indicator does not match primary market evidence",
            request_id=context.request_id,
            correlation_id=context.correlation_id,
        )


def _validate_signals(
    signals: tuple[StrategySignal, ...],
    ref: ValidatedStrategyRef,
    evidence: StrategySignalEvidence,
    context: StrategyExecutionContext,
) -> None:
    """Validate atomic concrete evaluator output identity and ordering.

    Args:
        signals: Evaluator-produced signals.
        ref: Exact validated registry reference.
        evidence: Exact signal evidence.
        context: Fixed evaluation context.

    """
    logger.debug("Validating concrete Strategy signal output")
    if not signals or len(signals) > ref.manifest.max_batch_records:
        failure(
            StrategyErrorCode.RESOURCE_LIMIT_EXCEEDED,
            "concrete signal batch is empty or exceeds its approved bound",
            request_id=context.request_id,
            correlation_id=context.correlation_id,
        )
    identities = tuple(signal.signal_id for signal in signals)
    names = tuple(signal.signal_name for signal in signals)
    if len(set(identities)) != len(identities) or len(set(names)) != len(names):
        failure(
            StrategyErrorCode.DUPLICATE_INTENT,
            "concrete signal batch contains duplicate identities or names",
            request_id=context.request_id,
            correlation_id=context.correlation_id,
        )
    manifest = ref.manifest
    if any(
        signal.strategy_id != manifest.strategy_id
        or signal.strategy_version != manifest.strategy_version
        or signal.symbol != evidence.primary_market.symbol
        or signal.timestamp > context.decision_timestamp
        for signal in signals
    ):
        failure(
            StrategyErrorCode.SCHEMA_VALIDATION_FAILED,
            "concrete signal output identity does not match its evaluation",
            request_id=context.request_id,
            correlation_id=context.correlation_id,
        )


@guard_strategy_boundary
def evaluate_strategy_signals(
    ref: ValidatedStrategyRef,
    config: ValidatedStrategyConfig,
    evidence: StrategySignalEvidence,
    indicators: tuple[IndicatorResult, ...],
    context: StrategyExecutionContext,
    evaluator: SignalEvaluator,
) -> tuple[StrategySignal, ...]:
    """Atomically execute one registry-bound concrete signal evaluator.

    Args:
        ref: Exact validated immutable strategy reference.
        config: Exact validated immutable strategy configuration.
        evidence: Point-in-time market, feature, and ownership evidence.
        indicators: Official precomputed indicator results.
        context: Fixed deterministic evaluation context.
        evaluator: Concrete hash-bound signal evaluator.

    Returns:
        Ordered concrete signals or one structured deterministic failure.

    Raises:
        StrategyOperationError: If an evaluator or nested boundary fails.
    """
    logger.info("Evaluating concrete Strategy signals for %s", ref.manifest.strategy_id)
    _validate_identity(ref, config, evaluator, context)
    _validate_evidence(evidence, indicators, context)
    try:
        signals = unwrap_evaluator_result(
            evaluator.evaluate_signals(evidence, indicators, config, context),
            operation="strategy.signals.evaluate_signals",
        )
    except StrategyOperationError:
        raise
    except _SignalConfigError:
        return failure(
            StrategyErrorCode.INVALID_CONFIG,
            "concrete signal configuration is invalid",
            request_id=context.request_id,
            correlation_id=context.correlation_id,
        )
    except _SignalDataError:
        return failure(
            StrategyErrorCode.DATA_NOT_READY,
            "concrete signal evidence is not ready",
            request_id=context.request_id,
            correlation_id=context.correlation_id,
        )
    except _SignalIndicatorError:
        return failure(
            StrategyErrorCode.INDICATOR_NOT_READY,
            "concrete signal indicator evidence is not ready",
            request_id=context.request_id,
            correlation_id=context.correlation_id,
        )
    except Exception as error:  # noqa: BLE001 - injected evaluator is untrusted.
        logger.error("Concrete Strategy evaluator failed: %s", type(error).__name__)
        return failure(
            StrategyErrorCode.INTERNAL_ERROR,
            "concrete signal evaluator failed",
            request_id=context.request_id,
            correlation_id=context.correlation_id,
        )
    if not isinstance(signals, tuple) or any(
        not isinstance(signal, StrategySignal) for signal in signals
    ):
        return failure(
            StrategyErrorCode.SCHEMA_VALIDATION_FAILED,
            "concrete signal evaluator returned an invalid output contract",
            request_id=context.request_id,
            correlation_id=context.correlation_id,
        )
    _validate_signals(signals, ref, evidence, context)
    return success(signals)


__all__ = ["evaluate_strategy_signals"]
