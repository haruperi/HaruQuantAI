"""Deterministic TradeIntent construction from Strategy decisions."""

import hashlib

from app.services.strategy.contracts.execution import (  # noqa: TC001
    StrategyDecision,
    StrategyExecutionContext,
)
from app.services.strategy.contracts.outcomes import StrategyOutcome, failure, success
from app.services.strategy.diagnostics.errors import StrategyErrorCode
from app.services.strategy.intents.intent import TradeIntent
from app.utils import canonical_json, logger


def build_trade_intent(
    decision: StrategyDecision,
    context: StrategyExecutionContext,
    sequence: int,
) -> StrategyOutcome[TradeIntent]:
    """Build one deterministic canonical intent from a proposal decision.

    Args:
        decision: Validated proposal decision.
        context: Exact deterministic evaluation context.
        sequence: Monotonic strategy-instance sequence.

    Returns:
        A canonical TradeIntent or deterministic validation failure.
    """
    logger.info("Building TradeIntent for decision %s", decision.decision_id)
    if decision.action != "PROPOSE":
        return failure(
            StrategyErrorCode.INVALID_CONFIG,
            "neutral decisions cannot produce trade intents",
            request_id=context.request_id,
            correlation_id=context.correlation_id,
        )
    if (
        decision.side is None
        or decision.intent_type is None
        or decision.order_type is None
    ):
        return failure(
            StrategyErrorCode.SCHEMA_VALIDATION_FAILED,
            "proposal decision is missing side, intent type, or order type",
            request_id=context.request_id,
            correlation_id=context.correlation_id,
        )
    if sequence < 0 or sequence != decision.sequence:
        return failure(
            StrategyErrorCode.INVALID_CONFIG,
            "intent sequence must equal the decision sequence",
            request_id=context.request_id,
            correlation_id=context.correlation_id,
        )
    if decision.valid_from > context.decision_timestamp:
        return failure(
            StrategyErrorCode.LOOKAHEAD_DETECTED,
            "decision evidence is not available at the fixed clock",
            request_id=context.request_id,
            correlation_id=context.correlation_id,
        )
    material = {
        "decision": decision.model_dump(mode="json"),
        "context": context.model_dump(mode="json"),
        "sequence": sequence,
    }
    digest = hashlib.sha256(canonical_json(material).encode("utf-8")).hexdigest()
    try:
        intent = TradeIntent(
            intent_id=f"intent-{digest}",
            decision_id=decision.decision_id,
            idempotency_key=digest,
            strategy_id=str(decision.lineage["strategy_id"]),
            strategy_version=str(decision.lineage["strategy_version"]),
            strategy_sequence=sequence,
            symbol=str(decision.symbol),
            side=decision.side,
            intent_type=decision.intent_type,
            order_type=decision.order_type,
            limit_price=decision.limit_price,
            stop_price=decision.stop_price,
            time_in_force=decision.time_in_force,
            requested_sizing_mode=decision.requested_sizing_mode,
            quantity_hint=decision.quantity_hint,
            notional_hint=decision.notional_hint,
            signal_timestamp=decision.valid_from,
            decision_timestamp=context.decision_timestamp,
            parent_intent_id=decision.parent_intent_id,
            stop_loss=decision.stop_loss,
            take_profit=decision.take_profit,
            expiration=decision.expires_at,
            allow_partial_fills=decision.allow_partial_fills,
            min_fill_size=decision.min_fill_size,
            rationale_ref=decision.rationale_ref,
            lineage=decision.lineage,
        )
    except (KeyError, ValueError):
        logger.warning("TradeIntent construction rejected invalid proposal fields")
        return failure(
            StrategyErrorCode.SCHEMA_VALIDATION_FAILED,
            "proposal fields do not form a valid TradeIntent",
            request_id=context.request_id,
            correlation_id=context.correlation_id,
        )
    return success(intent)


__all__ = ["build_trade_intent"]
