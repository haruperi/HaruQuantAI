"""Executable package-root create_trade_intent_value construction example."""

import sys
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.services.strategy import (
    build_trade_intent,
    create_strategy_decision,
    create_strategy_execution_context,
    create_trade_intent_value,
    get_strategy_environment,
    get_strategy_timing_policy,
)


def _header(title: str) -> None:
    """Print one example heading."""
    print(f"\n{'=' * 88}\n{title}\n{'=' * 88}")


def fr_str_025() -> None:
    """Demonstrate the canonical create_trade_intent_value contract."""
    _header("Demonstrate the canonical create_trade_intent_value contract.")
    assert callable(create_trade_intent_value)


def fr_str_026() -> None:
    """Demonstrate deterministic create_trade_intent_value construction."""
    _header("Demonstrate deterministic create_trade_intent_value construction.")
    assert callable(build_trade_intent)


def main() -> int:
    """Build canonical create_trade_intent_value proposals from strategy decisions.

    Returns:
        ``0`` once deterministic identity and neutrality have been shown.
    """
    fr_str_025()
    fr_str_026()
    now = datetime.now(UTC)
    context = create_strategy_execution_context(
        environment=get_strategy_environment("RESEARCH"),
        decision_timestamp=now,
        timing_policy=get_strategy_timing_policy("BAR_OPEN_PREVIOUS_CLOSE"),
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
    decision = create_strategy_decision(
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
    print("Contract:", create_trade_intent_value.__name__)
    response = build_trade_intent(decision, context, 0)
    print("Status:", response.status)
    if response.data is None:
        print("Error:", response.error)
        return 1
    intent = response.data
    reconstructed = create_trade_intent_value(**intent.model_dump())
    print("Schema:", intent.schema_id)
    print("Intent ID:", intent.intent_id)
    print("Idempotency key:", intent.idempotency_key)
    print("Sequence:", intent.strategy_sequence)
    print("Symbol / side:", intent.symbol, intent.side)
    print("Order type:", intent.order_type)
    print("Quantity hint:", intent.quantity_hint)
    print("Lineage keys:", sorted(intent.lineage))
    print("Complete proposal:", intent.model_dump(mode="json"))
    print("Public value-factory round trip:", reconstructed == intent)

    print("\n-- Deterministic identity --")
    repeat = build_trade_intent(decision, context, 0)
    stable = repeat.data is not None and repeat.data.intent_id == intent.intent_id
    print("Identical inputs reproduce the identical intent id:", stable)

    print("\n-- Neutral decisions emit no intent --")
    neutral = create_strategy_decision(
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
    neutral_response = build_trade_intent(neutral, context, 1)
    print("Status:", neutral_response.status)
    if neutral_response.error is not None:
        print("Error code:", neutral_response.error.code)
    print("\nThis remains a proposal; Risk has not approved execution.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
