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
    build_trade_intent,
)

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
    lineage={
        "strategy_id": "naive-ma-trend",
        "strategy_version": "1.0.0",
        "config_hash": "0" * 64,
    },
)
outcome = build_trade_intent(decision, context, 0)

print("\nTRADE INTENT PROPOSAL")
print("=" * 88)
print("Status:", outcome.status)
if outcome.data is not None:
    print("Intent ID:", outcome.data.intent_id)
    print("Symbol / side:", outcome.data.symbol, outcome.data.side)
    print("Quantity hint:", outcome.data.quantity_hint)
    print("This remains a proposal; Risk has not approved execution.")
elif outcome.error is not None:
    print("Error:", outcome.error.code, outcome.error.message)
