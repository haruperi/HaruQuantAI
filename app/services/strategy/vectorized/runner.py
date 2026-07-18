"""Atomic no-lookahead vectorized Strategy evaluation."""

from __future__ import annotations

import hashlib
from dataclasses import asdict
from typing import Protocol, runtime_checkable

from app.services.data.contracts import (  # noqa: TC001
    AccountStateSnapshot,
    MarketDataset,
)
from app.services.indicators import IndicatorResult  # noqa: TC001
from app.services.strategy.contracts.models import (
    StrategyDecision,
    StrategyExecutionContext,
    StrategyExecutionResult,
    ValidatedStrategyConfig,
    ValidatedStrategyRef,
)
from app.services.strategy.contracts.outcomes import (
    StrategyOutcome,
    failure,
    propagate_failure,
    success,
)
from app.services.strategy.diagnostics import (
    StrategyErrorCode,
    export_strategy_diagnostics,
)
from app.services.strategy.intents import TradeIntent, build_trade_intent
from app.services.strategy.replay import create_strategy_replay_manifest
from app.utils import canonical_json, logger


@runtime_checkable
class VectorizedStrategyEvaluator(Protocol):
    """Injected hash-bound vectorized evaluator structural contract."""

    strategy_id: str
    strategy_version: str
    module_path: str
    source_hash: str
    artifact_hash: str
    dependency_hash: str

    def evaluate_vectorized(
        self,
        market: MarketDataset,
        indicators: tuple[IndicatorResult, ...],
        config: ValidatedStrategyConfig,
        context: StrategyExecutionContext,
        account_snapshot: AccountStateSnapshot | None,
    ) -> tuple[StrategyDecision, ...]:
        """Evaluate normalized evidence without external access.

        Args:
            market: Exact normalized Data dataset.
            indicators: Exact ordered precomputed indicator results.
            config: Validated immutable configuration.
            context: Fixed deterministic evaluation context.
            account_snapshot: Optional immutable Data-owned account evidence.

        Raises:
            NotImplementedError: Protocol declaration has no implementation.
        """
        logger.debug("Invoking injected vectorized Strategy evaluator")
        del market, indicators, config, context, account_snapshot
        raise NotImplementedError


def run_vectorized_strategy_signals(  # noqa: PLR0911
    ref: ValidatedStrategyRef,
    config: ValidatedStrategyConfig,
    market: MarketDataset,
    indicators: tuple[IndicatorResult, ...],
    context: StrategyExecutionContext,
    evaluator: VectorizedStrategyEvaluator,
    account_snapshot: AccountStateSnapshot | None = None,
) -> StrategyOutcome[StrategyExecutionResult]:
    """Validate and atomically run one vectorized evaluator.

    Args:
        ref: Validated exact strategy reference.
        config: Validated exact configuration.
        market: Normalized immutable market data.
        indicators: Ordered precomputed indicator results.
        context: Fixed-clock execution context.
        evaluator: Injected evaluator bound to registry identity and hashes.
        account_snapshot: Optional immutable account-state evidence.

    Returns:
        One atomic execution result or deterministic failure with no intents.
    """
    logger.info("Running vectorized Strategy evaluation")
    readiness = _validate_readiness(
        ref, config, market, indicators, context, evaluator, account_snapshot
    )
    if readiness is not None:
        return readiness
    try:
        decisions = evaluator.evaluate_vectorized(
            market, indicators, config, context, account_snapshot
        )
    except Exception as error:  # noqa: BLE001 - evaluator trust boundary.
        logger.error("Vectorized Strategy evaluator failed: %s", type(error).__name__)
        return failure(
            StrategyErrorCode.INTERNAL_ERROR,
            "strategy evaluator failed",
            request_id=context.request_id,
            correlation_id=context.correlation_id,
        )
    if len(decisions) > ref.manifest.max_batch_records:
        return failure(
            StrategyErrorCode.RESOURCE_LIMIT_EXCEEDED,
            "decision batch exceeds the approved resource budget",
            request_id=context.request_id,
            correlation_id=context.correlation_id,
        )
    if any(
        decision.valid_from > context.decision_timestamp
        or decision.expires_at <= context.decision_timestamp
        for decision in decisions
    ):
        return failure(
            StrategyErrorCode.LOOKAHEAD_DETECTED,
            "decision batch contains unavailable or expired evidence",
            request_id=context.request_id,
            correlation_id=context.correlation_id,
        )
    intents_outcome = _build_intents(decisions, context)
    if intents_outcome.status == "error" or intents_outcome.data is None:
        return propagate_failure(intents_outcome)
    intents = intents_outcome.data
    if len({intent.idempotency_key for intent in intents}) != len(intents):
        return failure(
            StrategyErrorCode.DUPLICATE_INTENT,
            "decision batch produced duplicate intents",
            request_id=context.request_id,
            correlation_id=context.correlation_id,
        )
    data_checksum = hashlib.sha256(
        canonical_json(market.model_dump(mode="json")).encode("utf-8")
    ).hexdigest()
    indicator_hash = hashlib.sha256(
        canonical_json(tuple(asdict(item.manifest) for item in indicators)).encode(
            "utf-8"
        )
    ).hexdigest()
    replay = create_strategy_replay_manifest(
        ref, config, context, data_checksum, indicator_hash
    )
    if replay.status == "error" or replay.data is None:
        return propagate_failure(replay)
    diagnostics = export_strategy_diagnostics(
        context,
        {
            "status": "PROPOSED" if intents else "NEUTRAL",
            "strategy_id": ref.manifest.strategy_id,
            "strategy_version": ref.manifest.strategy_version,
            "config_hash": config.config_hash,
            "data_checksum": data_checksum,
            "decision_count": len(decisions),
            "intent_count": len(intents),
        },
    )
    if diagnostics.status == "error" or diagnostics.data is None:
        return propagate_failure(diagnostics)
    local_updates = tuple(
        decision.candidate_local_state
        for decision in decisions
        if decision.candidate_local_state is not None
    )
    if len(local_updates) > 1:
        return failure(
            StrategyErrorCode.CHECKPOINT_INVALID,
            "decision batch contains multiple local-state candidates",
            request_id=context.request_id,
            correlation_id=context.correlation_id,
        )
    result_material = {
        "decisions": tuple(item.model_dump(mode="json") for item in decisions),
        "intents": tuple(item.model_dump(mode="json") for item in intents),
        "replay_manifest": replay.data.model_dump(mode="json"),
        "local_state_update": local_updates[0] if local_updates else None,
    }
    result_hash = hashlib.sha256(
        canonical_json(result_material).encode("utf-8")
    ).hexdigest()
    return success(
        StrategyExecutionResult(
            decisions=decisions,
            intents=intents,
            diagnostics=diagnostics.data,
            replay_manifest=replay.data,
            local_state_update=local_updates[0] if local_updates else None,
            result_hash=result_hash,
        )
    )


def _validate_readiness(  # noqa: PLR0911
    ref: ValidatedStrategyRef,
    config: ValidatedStrategyConfig,
    market: MarketDataset,
    indicators: tuple[IndicatorResult, ...],
    context: StrategyExecutionContext,
    evaluator: VectorizedStrategyEvaluator,
    account_snapshot: AccountStateSnapshot | None,
) -> StrategyOutcome[StrategyExecutionResult] | None:
    """Validate all vectorized evidence before evaluator invocation.

    Args:
        ref: Validated strategy reference.
        config: Validated configuration.
        market: Normalized market dataset.
        indicators: Ordered indicator results.
        context: Fixed-clock context.
        evaluator: Injected evaluator.
        account_snapshot: Optional account evidence.

    Returns:
        ``None`` when ready, otherwise a deterministic failed outcome.
    """
    logger.debug("Validating vectorized Strategy readiness")
    if not isinstance(evaluator, VectorizedStrategyEvaluator) or not _identity_matches(
        ref, evaluator
    ):
        return failure(
            StrategyErrorCode.ARTIFACT_HASH_MISMATCH,
            "evaluator identity does not match the validated registry reference",
            request_id=context.request_id,
            correlation_id=context.correlation_id,
        )
    if (
        config.strategy_id != ref.manifest.strategy_id
        or config.strategy_version != ref.manifest.strategy_version
        or context.environment != ref.environment
        or context.timing_policy != ref.manifest.timing_policy
    ):
        return failure(
            StrategyErrorCode.INVALID_CONFIG,
            "execution identity does not match validated contracts",
            request_id=context.request_id,
            correlation_id=context.correlation_id,
        )
    if market.data_kind != "bars" or not market.records:
        return failure(
            StrategyErrorCode.MISSING_REQUIRED_DATA,
            "vectorized evaluation requires non-empty normalized bars",
            request_id=context.request_id,
            correlation_id=context.correlation_id,
        )
    if market.record_count > ref.manifest.max_batch_records:
        return failure(
            StrategyErrorCode.RESOURCE_LIMIT_EXCEEDED,
            "market batch exceeds the approved resource budget",
            request_id=context.request_id,
            correlation_id=context.correlation_id,
        )
    if market.available_at > context.decision_timestamp or any(
        record.available_at > context.decision_timestamp for record in market.records
    ):
        return failure(
            StrategyErrorCode.LOOKAHEAD_DETECTED,
            "market evidence is unavailable at the fixed decision clock",
            request_id=context.request_id,
            correlation_id=context.correlation_id,
        )
    actual_indicators = tuple(item.indicator_id for item in indicators)
    if actual_indicators != ref.manifest.required_indicators:
        return failure(
            StrategyErrorCode.INDICATOR_NOT_READY,
            "ordered required indicators are incomplete",
            request_id=context.request_id,
            correlation_id=context.correlation_id,
        )
    if any(not _indicator_ready(item, context) for item in indicators):
        return failure(
            StrategyErrorCode.LOOKAHEAD_DETECTED,
            "indicator evidence is unavailable at the fixed decision clock",
            request_id=context.request_id,
            correlation_id=context.correlation_id,
        )
    if ref.manifest.requires_account_snapshot and account_snapshot is None:
        return failure(
            StrategyErrorCode.MISSING_REQUIRED_DATA,
            "strategy requires account-state evidence",
            request_id=context.request_id,
            correlation_id=context.correlation_id,
        )
    if account_snapshot is not None and not (
        account_snapshot.snapshot_at
        <= context.decision_timestamp
        < account_snapshot.expires_at
    ):
        return failure(
            StrategyErrorCode.STALE_DATA,
            "account-state evidence is stale or from the future",
            request_id=context.request_id,
            correlation_id=context.correlation_id,
        )
    return None


def _identity_matches(
    ref: ValidatedStrategyRef, evaluator: VectorizedStrategyEvaluator
) -> bool:
    """Return whether evaluator identity exactly matches the registry.

    Args:
        ref: Validated registry reference.
        evaluator: Injected evaluator.

    Returns:
        Whether all immutable identity and hash fields match.
    """
    logger.debug("Checking vectorized evaluator hash binding")
    manifest = ref.manifest
    return (
        evaluator.strategy_id == manifest.strategy_id
        and evaluator.strategy_version == manifest.strategy_version
        and evaluator.module_path == manifest.module_path
        and evaluator.source_hash == manifest.source_hash
        and evaluator.artifact_hash == manifest.artifact_hash
        and evaluator.dependency_hash == manifest.dependency_hash
    )


def _indicator_ready(
    indicator: IndicatorResult, context: StrategyExecutionContext
) -> bool:
    """Return whether one indicator is causal at the decision clock.

    Args:
        indicator: Precomputed indicator result.
        context: Fixed-clock context.

    Returns:
        Whether every availability timestamp is causal.
    """
    logger.debug("Checking Strategy indicator readiness")
    if indicator.errors or "available_at" not in indicator.values.columns:
        return False
    return all(
        timestamp.to_pydatetime() <= context.decision_timestamp
        for timestamp in indicator.values["available_at"].tolist()
    )


def _build_intents(
    decisions: tuple[StrategyDecision, ...],
    context: StrategyExecutionContext,
) -> StrategyOutcome[tuple[TradeIntent, ...]]:
    """Build all proposal intents atomically.

    Args:
        decisions: Ordered evaluator decisions.
        context: Fixed-clock context.

    Returns:
        Complete ordered intent tuple or first deterministic failure.
    """
    logger.debug("Building atomic vectorized Strategy intent batch")
    if tuple(item.sequence for item in decisions) != tuple(
        sorted(item.sequence for item in decisions)
    ):
        return failure(
            StrategyErrorCode.INVALID_CONFIG,
            "decisions are not deterministically ordered",
            request_id=context.request_id,
            correlation_id=context.correlation_id,
        )
    intents: list[TradeIntent] = []
    for decision in decisions:
        if decision.action == "NEUTRAL":
            continue
        outcome = build_trade_intent(decision, context, decision.sequence)
        if outcome.status == "error" or outcome.data is None:
            return propagate_failure(outcome)
        intents.append(outcome.data)
    return success(tuple(intents))


__all__ = ["VectorizedStrategyEvaluator", "run_vectorized_strategy_signals"]
