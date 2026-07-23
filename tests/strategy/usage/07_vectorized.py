"""Executable vectorized Strategy evaluation against real MT5 evidence."""

import sys
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.services.data import get_market_data
from app.services.data.contracts import DataError
from app.services.strategy import (
    StrategyDecision,
    StrategyEnvironment,
    StrategyExecutionContext,
    StrategyLifecycleStatus,
    StrategyManifest,
    StrategyTimingPolicy,
    StrategyValidationPolicy,
    ValidatedStrategyConfig,
    ValidatedStrategyRef,
    VectorizedStrategyEvaluator,
    run_vectorized_strategy_signals,
)

_UNAVAILABLE = 3
_HASH = "f" * 64
_REQUEST = "strategy-usage-vectorized"
_WORKFLOW = "strategy-usage-vectorized-workflow"
_CORRELATION = "strategy-usage-vectorized-correlation"
_STRATEGY = "usage-vectorized-strategy"
_MODULE = "app.services.strategy.evaluators.naive_ma_trend"


class LastBarProposalEvaluator:
    """Minimal hash-bound evaluator proposing one entry on the last closed bar."""

    strategy_id = _STRATEGY
    strategy_version = "1.0.0"
    module_path = _MODULE
    source_hash = _HASH
    artifact_hash = _HASH
    dependency_hash = _HASH

    def evaluate_vectorized(
        self, market, indicators, config, context, account_snapshot
    ):
        """Propose one bounded advisory entry from the last completed bar.

        Args:
            market: Exact normalized Data dataset.
            indicators: Ordered precomputed indicator results.
            config: Validated immutable configuration.
            context: Fixed deterministic evaluation context.
            account_snapshot: Optional Data-owned account snapshot.

        Returns:
            One proposal decision derived from the last completed bar.
        """
        del indicators, config, account_snapshot
        bar = market.records[-1]
        return (
            StrategyDecision(
                decision_id=f"usage-vectorized-{bar.timestamp.isoformat()}",
                sequence=0,
                action="PROPOSE",
                symbol=market.symbol,
                side="BUY",
                intent_type="OPEN",
                order_type="MARKET",
                requested_sizing_mode="quantity",
                quantity_hint=Decimal("0.01"),
                valid_from=context.decision_timestamp,
                expires_at=context.decision_timestamp + timedelta(minutes=5),
                allow_partial_fills=False,
                rationale_refs=("usage-vectorized-observation",),
                diagnostic_facts={"close": str(bar.close)},
                lineage={
                    "strategy_id": self.strategy_id,
                    "strategy_version": self.strategy_version,
                    "config_hash": _HASH,
                },
            ),
        )


def main() -> int:
    """Run one atomic no-lookahead vectorized evaluation on real MT5 bars.

    Returns:
        ``0`` on success, or ``3`` when real MT5 evidence is unavailable.
    """
    print("\nVECTORIZED STRATEGY EVALUATION — REAL MT5 EURUSD M5")
    print("=" * 88)
    try:
        market = get_market_data(
            source_id="mt5",
            symbol="EURUSD",
            timeframe="M5",
            limit=300,
            use_cache=False,
        )
    except DataError as error:
        print("Live MT5 data unavailable:", error.code)
        return _UNAVAILABLE

    print("Source: MT5")
    print("Bars:", market.record_count)
    print("Latest completed bar:", market.records[-1].timestamp)

    policy = StrategyValidationPolicy(
        policy_version="usage-v1",
        approved_module_roots=("app.services.strategy.evaluators",),
        max_config_payload_bytes=4_096,
        max_config_nesting_depth=8,
        max_config_string_length=128,
        max_config_collection_items=64,
    )
    timing = StrategyTimingPolicy.BAR_OPEN_PREVIOUS_CLOSE
    context = StrategyExecutionContext(
        environment=StrategyEnvironment.RESEARCH,
        decision_timestamp=datetime.now(UTC),
        timing_policy=timing,
        seed=23,
        interface_version="v1",
        request_id=_REQUEST,
        workflow_id=_WORKFLOW,
        correlation_id=_CORRELATION,
        dependency_status={"data": "ready", "indicators": "ready"},
        snapshot_refs=(market.request_id,),
        max_diagnostic_bytes=8_192,
    )
    manifest = StrategyManifest(
        strategy_id=_STRATEGY,
        strategy_version="1.0.0",
        module_path=_MODULE,
        owner_ref="strategy-usage",
        interface_version="v1",
        config_schema_version="v1",
        config_schema={"type": "object"},
        required_data=("EURUSD:M5",),
        required_indicators=(),
        timing_policy=timing,
        permitted_environments=(StrategyEnvironment.RESEARCH,),
        source_hash=_HASH,
        artifact_hash=_HASH,
        dependency_hash=_HASH,
        provenance_refs=(market.request_id,),
        supported_hooks=(),
        requires_account_snapshot=False,
        max_batch_records=10_000,
        max_diagnostic_bytes=8_192,
        max_checkpoint_bytes=8_192,
        max_local_state_bytes=8_192,
        decision_timeout_seconds=5,
    )
    ref = ValidatedStrategyRef(
        manifest=manifest,
        lifecycle_status=StrategyLifecycleStatus.APPROVED,
        environment=StrategyEnvironment.RESEARCH,
        policy_version=policy.policy_version,
        validation_policy=policy,
        registry_record_hash=_HASH,
        request_id=_REQUEST,
        correlation_id=_CORRELATION,
    )
    config = ValidatedStrategyConfig(
        strategy_id=_STRATEGY,
        strategy_version="1.0.0",
        config_schema_version="v1",
        normalized_parameters={"lookback": 1},
        config_hash=_HASH,
        policy_version=policy.policy_version,
        request_id=_REQUEST,
    )
    evaluator: VectorizedStrategyEvaluator = LastBarProposalEvaluator()

    print("\n-- Atomic ordered intent batch --")
    outcome = run_vectorized_strategy_signals(
        ref, config, market, (), context, evaluator
    )
    if outcome.data is None:
        print("Vectorized evaluation failed:", outcome.error)
        return _UNAVAILABLE
    result = outcome.data
    print("Decisions:", len(result.decisions))
    print("Intents:", len(result.intents))
    for intent in result.intents:
        print(
            f"  seq={intent.strategy_sequence} {intent.symbol} {intent.side} "
            f"{intent.order_type} id={intent.intent_id[:16]}"
        )
    print("Replay manifest hash:", result.replay_manifest.manifest_hash)

    print("\n-- Hash binding fails closed --")
    unbound = LastBarProposalEvaluator()
    unbound.artifact_hash = "0" * 64
    rejected = run_vectorized_strategy_signals(
        ref, config, market, (), context, unbound
    )
    print("Status:", rejected.status)
    if rejected.error is not None:
        print("Error code:", rejected.error.code)
    print("\nIntents are proposals only; Risk has approved nothing.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
