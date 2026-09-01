"""Atomic hash-bound boundary for concrete Strategy signal evaluators."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import UTC
from typing import TYPE_CHECKING, Any

from app.composition.logging import get_logger
from app.contracts.common.models import get_standard_response_type
from app.kernel.serialization import canonical_json
from app.services.indicators import get_indicator_result_values, join_indicator_result
from app.services.strategy.contracts import StrategySignal
from app.services.strategy.contracts.outcomes import failure, success
from app.services.strategy.contracts.responses import (
    StrategyOperationError,
    guard_strategy_boundary,
    unwrap_evaluator_result,
)
from app.services.strategy.diagnostics.errors import StrategyErrorCode
from app.services.strategy.signals._mechanics import (
    _bar_records,
    _SignalConfigError,
    _SignalDataError,
    _SignalIndicatorError,
)

logger = get_logger(__name__)
_STANDARD_RESPONSE_TYPE = get_standard_response_type()

if TYPE_CHECKING:
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
    indicators: tuple[Any, ...],
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
            joined = join_indicator_result(indicator, evidence.primary_market)
            if (
                isinstance(joined, _STANDARD_RESPONSE_TYPE)
                and getattr(joined, "status", None) == "error"
            ):
                error = getattr(joined, "error", None)
                upstream_code = (
                    getattr(error, "code", "INVALID_RESPONSE")
                    if error is not None
                    else "INVALID_RESPONSE"
                )
                failure(
                    StrategyErrorCode.INDICATOR_MODULE_ERROR,
                    "concrete signal indicator join failed",
                    details={"upstream_code": upstream_code},
                    request_id=context.request_id,
                    correlation_id=context.correlation_id,
                )
            available = get_indicator_result_values(indicator)["available_at"]
            if any(
                item.to_pydatetime() > context.decision_timestamp for item in available
            ):
                failure(
                    StrategyErrorCode.LOOKAHEAD_DETECTED,
                    "concrete signal indicator contains future evidence",
                    request_id=context.request_id,
                    correlation_id=context.correlation_id,
                )
    except TypeError, ValueError, KeyError:
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
    indicators: tuple[Any, ...],
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
    except Exception as error:
        logger.exception("Concrete Strategy evaluator failed: %s", type(error).__name__)
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


@guard_strategy_boundary
def record_strategy_signals(
    config_id: str,
    signals: tuple[StrategySignal, ...],
    *,
    intents: tuple[Any, ...] = (),
    request_id: str,
    correlation_id: str,
) -> tuple[Mapping[str, Any], ...]:
    """Atomically persist genuine evaluator Strategy signal output records.

    Args:
        config_id: Strategy configuration record identifier.
        signals: Bounded tuple of StrategySignal output contracts.
        intents: Optional tuple of TradeIntent contracts.
        request_id: Tracing request identifier.
        correlation_id: Tracing correlation identifier.

    Returns:
        Tuple of persisted signal record mappings.
    """
    from app.services.strategy.persistence import create_strategy_signal_records

    logger.info("Recording %d strategy signals for config %s", len(signals), config_id)
    records = []
    for idx, sig in enumerate(signals):
        intent_id = (
            intents[idx].intent_id
            if idx < len(intents) and hasattr(intents[idx], "intent_id")
            else None
        )
        rec = {
            "signal_id": sig.signal_id,
            "config_id": config_id,
            "strategy_id": sig.strategy_id,
            "strategy_version": sig.strategy_version,
            "sequence": idx,
            "symbol": sig.symbol,
            "signal_name": sig.signal_name,
            "side": sig.side,
            "active": sig.active,
            "signal_timestamp": sig.timestamp.isoformat()
            if hasattr(sig.timestamp, "isoformat")
            else str(sig.timestamp),
            "signal_json": sig.model_dump_json(),
            "lineage_json": canonical_json(sig.lineage)
            if hasattr(sig, "lineage")
            else "{}",
            "facts_json": canonical_json(sig.facts) if hasattr(sig, "facts") else "{}",
            "intent_id": intent_id,
            "publication_status": "generated",
            "risk_submission_ref": None,
            "request_id": request_id,
            "correlation_id": correlation_id,
            "created_at": context_now_iso(),
            "updated_at": context_now_iso(),
        }
        records.append(rec)
    rec_tuple = tuple(records)
    create_strategy_signal_records(rec_tuple, request_id)
    return rec_tuple


@guard_strategy_boundary
def list_strategy_signals(
    config_id: str,
    *,
    publication_status: str | None = None,
) -> tuple[Mapping[str, Any], ...]:
    """List bounded durable Strategy signal evidence.

    Args:
        config_id: Configuration record identifier.
        publication_status: Optional publication status filter.

    Returns:
        Tuple of signal record mappings.
    """
    from app.kernel.identity import generate_id
    from app.services.strategy.persistence import read_strategy_signals

    logger.info("Listing strategy signals for %s", config_id)
    request_id = generate_id("req")
    rows = read_strategy_signals(config_id, request_id)
    if publication_status:
        rows = tuple(
            r for r in rows if r.get("publication_status") == publication_status
        )
    return rows


@guard_strategy_boundary
def mark_strategy_signal_submitted(
    signal_id: str,
    *,
    expected_status: str = "generated",
    risk_submission_ref: str,
    request_id: str,
    correlation_id: str,
) -> Mapping[str, Any]:
    """Mark successful handoff to Risk without storing a Risk decision.

    Args:
        signal_id: Signal record identifier.
        expected_status: Expected current status.
        risk_submission_ref: Opaque risk submission reference string.
        request_id: Tracing request identifier.
        correlation_id: Tracing correlation identifier.

    Returns:
        Updated signal reference mapping.
    """
    from app.services.strategy.persistence import (
        update_strategy_signal_publication_record,
    )

    logger.info("Marking strategy signal %s as submitted", signal_id)
    success_sub = update_strategy_signal_publication_record(
        signal_id=signal_id,
        expected_status=expected_status,
        new_status="submitted",
        risk_submission_ref=risk_submission_ref,
        request_id=request_id,
    )
    if not success_sub:
        failure(
            StrategyErrorCode.INTERNAL_ERROR,
            f"Failed to mark signal {signal_id} as submitted",
            request_id=request_id,
            correlation_id=correlation_id,
        )
    return {
        "signal_id": signal_id,
        "publication_status": "submitted",
        "risk_submission_ref": risk_submission_ref,
    }


@guard_strategy_boundary
def evaluate_and_record_strategy_signals(
    ref: ValidatedStrategyRef,
    config: ValidatedStrategyConfig,
    config_id: str,
    evidence: StrategySignalEvidence,
    indicators: tuple[Any, ...],
    context: StrategyExecutionContext,
    evaluator: SignalEvaluator,
) -> tuple[StrategySignal, ...]:
    """Evaluate and atomically record exact genuine signals.

    Args:
        ref: Validated exact strategy reference.
        config: Validated strategy configuration.
        config_id: Configuration record identifier.
        evidence: Point-in-time signal evidence.
        indicators: Calculated indicators.
        context: Execution context.
        evaluator: Signal evaluator.

    Returns:
        Tuple of emitted signals.
    """
    from app.services.strategy.contracts.responses import unwrap_strategy_response

    logger.info(
        "Evaluating and recording strategy signals for %s", ref.manifest.strategy_id
    )
    signals = unwrap_strategy_response(
        evaluate_strategy_signals(
            ref, config, evidence, indicators, context, evaluator
        ),
        operation="strategy.signals.evaluate_strategy_signals",
    )
    if signals:
        record_strategy_signals(
            config_id=config_id,
            signals=signals,
            request_id=context.request_id,
            correlation_id=context.correlation_id,
        )
    return signals


def context_now_iso() -> str:
    """Return ISO format string for current UTC timestamp."""
    from datetime import datetime

    return datetime.now(UTC).isoformat()


__all__ = [
    "evaluate_and_record_strategy_signals",
    "evaluate_strategy_signals",
    "list_strategy_signals",
    "mark_strategy_signal_submitted",
    "record_strategy_signals",
]
