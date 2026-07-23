"""Atomic typed-hook event-driven Strategy evaluation."""

from __future__ import annotations

import hashlib
from collections.abc import Mapping
from typing import TYPE_CHECKING, Protocol, runtime_checkable

from app.services.strategy.contracts.execution import (
    StrategyDecision,
    StrategyEvent,
    StrategyExecutionContext,
    StrategyExecutionResult,
)
from app.services.strategy.contracts.outcomes import (
    StrategyOutcome,
    failure,
    propagate_failure,
    success,
)
from app.services.strategy.contracts.references import (  # noqa: TC001
    ValidatedStrategyConfig,
    ValidatedStrategyRef,
)
from app.services.strategy.diagnostics import (
    StrategyErrorCode,
    export_strategy_diagnostics,
)
from app.services.strategy.intents import TradeIntent, build_trade_intent
from app.services.strategy.replay import create_strategy_replay_manifest
from app.utils import canonical_digest, canonical_json, logger

if TYPE_CHECKING:
    from app.services.data.evidence.account_contracts import AccountStateSnapshot
    from app.services.strategy.contracts._base import JsonValue


@runtime_checkable
class EventStrategyEvaluator(Protocol):
    """Injected hash-bound typed event evaluator structural contract."""

    strategy_id: str
    strategy_version: str
    module_path: str
    source_hash: str
    artifact_hash: str
    dependency_hash: str
    supported_hooks: tuple[str, ...]

    def evaluate_event(
        self,
        event: StrategyEvent,
        config: ValidatedStrategyConfig,
        context: StrategyExecutionContext,
        local_state: Mapping[str, JsonValue] | None,
        account_snapshot: AccountStateSnapshot | None,
    ) -> tuple[StrategyDecision, ...]:
        """Evaluate one typed immutable event without external access.

        Args:
            event: Receiver-owned event evidence.
            config: Validated immutable configuration.
            context: Fixed deterministic evaluation context.
            local_state: Optional validated Strategy-local state.
            account_snapshot: Optional immutable Data-owned account evidence.

        Raises:
            NotImplementedError: Protocol declaration has no implementation.
        """
        logger.debug("Invoking injected event Strategy evaluator")
        del event, config, context, local_state, account_snapshot
        raise NotImplementedError


def run_event_strategy_hook(  # noqa: C901, PLR0911
    ref: ValidatedStrategyRef,
    config: ValidatedStrategyConfig,
    event: StrategyEvent,
    context: StrategyExecutionContext,
    evaluator: EventStrategyEvaluator,
    local_state: Mapping[str, JsonValue] | None = None,
    account_snapshot: AccountStateSnapshot | None = None,
) -> StrategyOutcome[StrategyExecutionResult]:
    """Validate and atomically invoke one declared typed event hook.

    Args:
        ref: Validated exact strategy reference.
        config: Validated exact configuration.
        event: Receiver-owned immutable external evidence.
        context: Fixed-clock execution context.
        evaluator: Injected evaluator bound to registry identity and hashes.
        local_state: Optional validated Strategy-local prior state.
        account_snapshot: Optional immutable account-state evidence.

    Returns:
        One atomic event execution result or deterministic failure.
    """
    logger.info("Running event Strategy hook %s", event.hook)
    readiness = _validate_event_readiness(
        ref, config, event, context, evaluator, local_state, account_snapshot
    )
    if readiness is not None:
        return readiness
    try:
        decisions = evaluator.evaluate_event(
            event, config, context, local_state, account_snapshot
        )
    except Exception as error:  # noqa: BLE001 - evaluator trust boundary.
        logger.error("Event Strategy evaluator failed: %s", type(error).__name__)
        return failure(
            StrategyErrorCode.INTERNAL_ERROR,
            "strategy evaluator failed",
            request_id=context.request_id,
            correlation_id=context.correlation_id,
        )
    if len(decisions) > ref.manifest.max_batch_records:
        return failure(
            StrategyErrorCode.RESOURCE_LIMIT_EXCEEDED,
            "event decision batch exceeds the approved resource budget",
            request_id=context.request_id,
            correlation_id=context.correlation_id,
        )
    intents_outcome = _build_event_intents(decisions, context)
    if intents_outcome.status == "error" or intents_outcome.data is None:
        return propagate_failure(intents_outcome)
    intents = intents_outcome.data
    if len({intent.idempotency_key for intent in intents}) != len(intents):
        return failure(
            StrategyErrorCode.DUPLICATE_INTENT,
            "event hook produced duplicate intents",
            request_id=context.request_id,
            correlation_id=context.correlation_id,
        )
    local_updates = tuple(
        item.candidate_local_state
        for item in decisions
        if item.candidate_local_state is not None
    )
    if len(local_updates) > 1:
        return failure(
            StrategyErrorCode.CHECKPOINT_INVALID,
            "event hook produced multiple local-state candidates",
            request_id=context.request_id,
            correlation_id=context.correlation_id,
        )
    candidate = local_updates[0] if local_updates else None
    if candidate is not None and len(canonical_json(candidate).encode("utf-8")) > (
        ref.manifest.max_local_state_bytes
    ):
        return failure(
            StrategyErrorCode.RESOURCE_LIMIT_EXCEEDED,
            "local-state candidate exceeds the approved resource budget",
            request_id=context.request_id,
            correlation_id=context.correlation_id,
        )
    indicator_hash = hashlib.sha256(
        canonical_json(
            {
                "source_owner": event.source_owner,
                "source_schema_id": event.source_schema_id,
                "source_contract_version": event.source_contract_version,
            }
        ).encode("utf-8")
    ).hexdigest()
    replay = create_strategy_replay_manifest(
        ref,
        config,
        context,
        event.source_checksum,
        indicator_hash,
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
            "data_checksum": event.source_checksum,
            "event_type": event.event_type,
            "event_sequence": event.sequence,
            "decision_count": len(decisions),
            "intent_count": len(intents),
        },
    )
    if diagnostics.status == "error" or diagnostics.data is None:
        return propagate_failure(diagnostics)
    material = {
        "event": event.model_dump(mode="json"),
        "decisions": tuple(item.model_dump(mode="json") for item in decisions),
        "intents": tuple(item.model_dump(mode="json") for item in intents),
        "replay_manifest": replay.data.model_dump(mode="json"),
        "local_state_update": candidate,
    }
    try:
        result_hash = canonical_digest(material)
    except (TypeError, ValueError):
        logger.error("Event Strategy result digest failed")
        return failure(
            StrategyErrorCode.INTERNAL_ERROR,
            "strategy result digest failed",
            request_id=context.request_id,
            correlation_id=context.correlation_id,
        )
    return success(
        StrategyExecutionResult(
            decisions=decisions,
            intents=intents,
            diagnostics=diagnostics.data,
            replay_manifest=replay.data,
            local_state_update=candidate,
            result_hash=result_hash,
        )
    )


def _validate_event_readiness(  # noqa: PLR0911
    ref: ValidatedStrategyRef,
    config: ValidatedStrategyConfig,
    event: StrategyEvent,
    context: StrategyExecutionContext,
    evaluator: EventStrategyEvaluator,
    local_state: Mapping[str, JsonValue] | None,
    account_snapshot: AccountStateSnapshot | None,
) -> StrategyOutcome[StrategyExecutionResult] | None:
    """Validate all event evidence before evaluator invocation.

    Args:
        ref: Validated strategy reference.
        config: Validated configuration.
        event: Receiver-owned event evidence.
        context: Fixed-clock context.
        evaluator: Injected event evaluator.
        local_state: Optional prior local state.
        account_snapshot: Optional account evidence.

    Returns:
        ``None`` when ready, otherwise deterministic failed outcome.
    """
    logger.debug("Validating event Strategy readiness")
    if not isinstance(evaluator, EventStrategyEvaluator) or not _identity_matches(
        ref, evaluator
    ):
        return failure(
            StrategyErrorCode.ARTIFACT_HASH_MISMATCH,
            "event evaluator identity does not match the registry reference",
            request_id=context.request_id,
            correlation_id=context.correlation_id,
        )
    if event.hook not in ref.manifest.supported_hooks or event.hook not in (
        evaluator.supported_hooks
    ):
        return failure(
            StrategyErrorCode.UNSUPPORTED_TIMING_POLICY,
            "event hook is not declared by the manifest and evaluator",
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
            "event execution identity does not match validated contracts",
            request_id=context.request_id,
            correlation_id=context.correlation_id,
        )
    if event.occurred_at > context.decision_timestamp or event.source_as_of > (
        context.decision_timestamp
    ):
        return failure(
            StrategyErrorCode.LOOKAHEAD_DETECTED,
            "event evidence is unavailable at the fixed decision clock",
            request_id=context.request_id,
            correlation_id=context.correlation_id,
        )
    last_sequence = context.dependency_status.get("last_event_sequence")
    if isinstance(last_sequence, int) and event.sequence <= last_sequence:
        return failure(
            StrategyErrorCode.DUPLICATE_INTENT,
            "event sequence is duplicated or out of order",
            request_id=context.request_id,
            correlation_id=context.correlation_id,
        )
    if local_state is not None and len(canonical_json(local_state).encode("utf-8")) > (
        ref.manifest.max_local_state_bytes
    ):
        return failure(
            StrategyErrorCode.RESOURCE_LIMIT_EXCEEDED,
            "prior local state exceeds the approved resource budget",
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
    ref: ValidatedStrategyRef,
    evaluator: EventStrategyEvaluator,
) -> bool:
    """Return whether event evaluator identity exactly matches the registry.

    Args:
        ref: Validated registry reference.
        evaluator: Injected event evaluator.

    Returns:
        Whether all immutable identity and hash fields match.
    """
    logger.debug("Checking event evaluator hash binding")
    manifest = ref.manifest
    return (
        evaluator.strategy_id == manifest.strategy_id
        and evaluator.strategy_version == manifest.strategy_version
        and evaluator.module_path == manifest.module_path
        and evaluator.source_hash == manifest.source_hash
        and evaluator.artifact_hash == manifest.artifact_hash
        and evaluator.dependency_hash == manifest.dependency_hash
    )


def _build_event_intents(
    decisions: tuple[StrategyDecision, ...],
    context: StrategyExecutionContext,
) -> StrategyOutcome[tuple[TradeIntent, ...]]:
    """Build event proposal intents atomically.

    Args:
        decisions: Ordered evaluator decisions.
        context: Fixed-clock context.

    Returns:
        Complete ordered intent tuple or first deterministic failure.
    """
    logger.debug("Building atomic event Strategy intent batch")
    sequences = tuple(item.sequence for item in decisions)
    if sequences != tuple(sorted(sequences)) or len(set(sequences)) != len(sequences):
        return failure(
            StrategyErrorCode.INVALID_CONFIG,
            "event decisions are not deterministically ordered",
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


__all__ = ["EventStrategyEvaluator", "run_event_strategy_hook"]
