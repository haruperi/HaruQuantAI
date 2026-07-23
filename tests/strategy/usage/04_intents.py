"""Executable package-root TradeIntent construction example."""

import sys
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.services.strategy import (
    StrategyDecision,
    StrategyEnvironment,
    StrategyExecutionContext,
    StrategyTimingPolicy,
    TradeIntent,
    build_trade_intent,
)


def main() -> int:
    """Build canonical TradeIntent proposals from strategy decisions.

    Returns:
        ``0`` once deterministic identity and neutrality have been shown.
    """
    now = datetime.now(UTC)
    context = StrategyExecutionContext(
        environment=StrategyEnvironment.RESEARCH,
        decision_timestamp=now,
        timing_policy=StrategyTimingPolicy.BAR_OPEN_PREVIOUS_CLOSE,
        seed=19,
        interface_version="v1",
        request_id="strategy-usage-intent",
        workflow_id="strategy-usage-intent-workflow",
        correlation_id="strategy-usage-intent-correlation",
        dependency_status={"data": "ready"},
        snapshot_refs=("live-market-read",),
        max_diagnostic_bytes=8_192,
    )
    lineage = {
        "strategy_id": "naive-ma-trend",
        "strategy_version": "1.0.0",
        "config_hash": "0" * 64,
    }
    decision = StrategyDecision(
        decision_id="visible-entry-example",
        sequence=0,
        action="PROPOSE",
        symbol="EURUSD",
        side="BUY",
        intent_type="OPEN",
        order_type="MARKET",
        requested_sizing_mode="quantity",
        quantity_hint=Decimal("0.01"),
        valid_from=now,
        expires_at=now + timedelta(minutes=5),
        allow_partial_fills=False,
        rationale_refs=("real-signal-required-before-use",),
        diagnostic_facts={"example": "proposal construction only"},
        lineage=lineage,
    )

    print("\nTRADE INTENT PROPOSAL")
    print("=" * 88)
    print("Contract:", TradeIntent.__name__)
    outcome = build_trade_intent(decision, context, 0)
    print("Status:", outcome.status)
    if outcome.data is None:
        print("Error:", outcome.error)
        return 1
    intent = outcome.data
    print("Schema:", intent.schema_id)
    print("Intent ID:", intent.intent_id)
    print("Idempotency key:", intent.idempotency_key)
    print("Sequence:", intent.strategy_sequence)
    print("Symbol / side:", intent.symbol, intent.side)
    print("Order type:", intent.order_type)
    print("Quantity hint:", intent.quantity_hint)
    print("Lineage keys:", sorted(intent.lineage))

    print("\n-- Deterministic identity --")
    repeat = build_trade_intent(decision, context, 0)
    stable = repeat.data is not None and repeat.data.intent_id == intent.intent_id
    print("Identical inputs reproduce the identical intent id:", stable)

    print("\n-- Neutral decisions emit no intent --")
    neutral = StrategyDecision(
        decision_id="neutral-example",
        sequence=1,
        action="NEUTRAL",
        valid_from=now,
        expires_at=now + timedelta(minutes=5),
        allow_partial_fills=False,
        rationale_refs=("no-signal",),
        diagnostic_facts={},
        lineage=lineage,
    )
    neutral_outcome = build_trade_intent(neutral, context, 1)
    print("Status:", neutral_outcome.status)
    if neutral_outcome.error is not None:
        print("Error code:", neutral_outcome.error.code)
    print("\nThis remains a proposal; Risk has not approved execution.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
