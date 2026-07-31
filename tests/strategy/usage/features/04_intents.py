"""Executable package-root create_trade_intent_value construction example."""

import sys
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.services.strategy import (
    build_trade_intent,
    create_strategy_decision,
    create_strategy_execution_context,
    create_trade_intent_value,
    get_strategy_environment,
    get_strategy_timing_policy,
)


def _feature_header(title: str) -> None:
    """Print the feature header banner."""
    print(f"\n\n{'=' * 88}\n{title}\n{'=' * 88}")


def _header(title: str) -> None:
    """Print one example heading."""
    print(f"\n{'=' * 88}\n{title}\n{'=' * 88}")


def _format_result(obj: Any) -> str:
    """Dynamically format the output result type name and field/key signature."""
    cls = type(obj)
    type_name = cls.__name__
    if hasattr(cls, "model_fields"):
        keys = ", ".join(cls.model_fields.keys())
        return f"Output Result -> {type_name}({keys}) : {type_name}"
    if isinstance(obj, dict):
        keys = ", ".join(obj.keys())
        return f"Output Result -> dict({keys}) : dict"
    if hasattr(obj, "__dict__"):
        keys = ", ".join(vars(obj).keys())
        return f"Output Result -> {type_name}({keys}) : {type_name}"
    return f"Output Result -> {type_name} : {type_name}"


def fr_str_025() -> None:
    """FR-STR-025: Stage 1 — Canonical TradeIntent contract creation."""
    _header("Stage 1: TradeIntent Contract Creation (FR-STR-025)")
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
        lineage={
            "strategy_id": "naive-ma-trend",
            "strategy_version": "1.0.0",
            "config_hash": "0" * 64,
        },
    )
    resp = build_trade_intent(decision, context, 0)
    if resp.data is None:
        raise RuntimeError("Failed to build TradeIntent")
    result = create_trade_intent_value(**resp.data.model_dump())
    print(_format_result(result))
    print(
        f"Data -> intent_id='{result.intent_id}', symbol='{result.symbol}', side='{result.side}'"
    )


def fr_str_026() -> None:
    """FR-STR-026: Stage 2 & 3 — Deterministic TradeIntent construction from decision."""
    _header("Stage 2 & 3: Deterministic TradeIntent Construction (FR-STR-026)")
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
        lineage={
            "strategy_id": "naive-ma-trend",
            "strategy_version": "1.0.0",
            "config_hash": "0" * 64,
        },
    )
    result = build_trade_intent(decision, context, 0)
    print(_format_result(result))
    if result.data is None:
        raise RuntimeError("TradeIntent construction failed")
    intent = result.data
    print(
        f"Data -> status='{result.status}', intent_id='{intent.intent_id}', idempotency_key='{intent.idempotency_key}'"
    )


def main() -> None:
    """Run all feature examples in sequential module flow order."""
    _feature_header(
        "FEATURE: FEAT-STR-04 — intents/ — Canonical TradeIntent Proposals\n\n"
        "Purpose: Construct canonical TradeIntent proposals with deterministic identity, sequence, and lineage for Risk evaluation.\n\n"
        "Module flow:\n"
        "-> StrategyDecision metadata\n"
        "-> Identity, sequence & lineage derivation\n"
        "-> Canonical TradeIntent proposal"
    )

    # 1. Stage 1: TradeIntent contract creation
    fr_str_025()

    # 2. Stage 2 & 3: Deterministic TradeIntent construction from decision
    fr_str_026()


if __name__ == "__main__":
    main()
