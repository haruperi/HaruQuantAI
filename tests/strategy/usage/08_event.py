"""Executable stateful event-hook example against real MT5 evidence."""

import hashlib
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.services.data import get_market_data
from app.services.data.contracts import DataError
from app.services.strategy import (
    EventStrategyEvaluator,
    StrategyDecision,
    StrategyEnvironment,
    StrategyEvent,
    StrategyExecutionContext,
    StrategyLifecycleStatus,
    StrategyManifest,
    StrategyTimingPolicy,
    StrategyValidationPolicy,
    ValidatedStrategyConfig,
    ValidatedStrategyRef,
    run_event_strategy_hook,
)
from app.utils import canonical_json

_UNAVAILABLE = 3
_HASH = "e" * 64
_REQUEST = "strategy-usage-event"
_WORKFLOW = "strategy-usage-event-workflow"
_CORRELATION = "strategy-usage-event-correlation"
_STRATEGY = "usage-event-strategy"
_HOOKS = ("on_init", "on_bar", "on_tick", "on_fill", "on_stop")


class BarCountingEvaluator:
    """Minimal declared-hook evaluator that counts observed closed bars."""

    def __init__(self, source_hash: str) -> None:
        """Bind the evaluator to its immutable registry identity.

        Args:
            source_hash: Approved source, artifact, and dependency hash.
        """
        self.strategy_id = _STRATEGY
        self.strategy_version = "1.0.0"
        self.module_path = "app.services.strategy.evaluators.naive_ma_trend"
        self.source_hash = source_hash
        self.artifact_hash = source_hash
        self.dependency_hash = source_hash
        self.supported_hooks = _HOOKS

    def evaluate_event(self, event, config, context, local_state, account_snapshot):
        """Return one neutral decision carrying an incremented candidate state.

        Args:
            event: Typed receiver-owned event.
            config: Validated immutable configuration.
            context: Fixed deterministic evaluation context.
            local_state: Prior bounded strategy-local state.
            account_snapshot: Optional Data-owned account snapshot.

        Returns:
            One neutral decision whose candidate local state counts the bar.
        """
        del config, account_snapshot
        seen = int((local_state or {}).get("bars_seen", 0)) + 1
        decision = StrategyDecision(
            decision_id=f"usage-event-{event.sequence}",
            sequence=0,
            action="NEUTRAL",
            valid_from=context.decision_timestamp,
            expires_at=context.decision_timestamp + timedelta(minutes=5),
            allow_partial_fills=False,
            rationale_refs=("usage-event-observation",),
            diagnostic_facts={"bars_seen": seen},
            candidate_local_state={"bars_seen": seen},
            lineage={
                "strategy_id": self.strategy_id,
                "strategy_version": self.strategy_version,
                "config_hash": _HASH,
            },
        )
        return (decision,)


def main() -> int:
    """Invoke one declared typed hook against a real closed bar.

    Returns:
        ``0`` on success, or ``3`` when real MT5 evidence is unavailable.
    """
    print("\nSTATEFUL STRATEGY EVENT HOOK — REAL MT5 EURUSD M5")
    print("=" * 88)
    try:
        market = get_market_data(
            source_id="mt5",
            symbol="EURUSD",
            timeframe="M5",
            limit=2,
            use_cache=False,
        )
    except DataError as error:
        print("Live MT5 data unavailable:", error.code)
        return _UNAVAILABLE

    bar = market.records[-1]
    source_checksum = hashlib.sha256(
        canonical_json(market.model_dump(mode="json")).encode()
    ).hexdigest()
    event = StrategyEvent(
        event_type="BAR_CLOSED",
        hook="on_bar",
        occurred_at=bar.timestamp,
        sequence=market.record_count - 1,
        source_owner="data",
        source_contract_version=market.contract_version,
        source_schema_id=market.schema_id,
        source_snapshot_ref=market.request_id,
        source_checksum=source_checksum,
        source_as_of=bar.timestamp,
        facts={"symbol": market.symbol, "timeframe": market.timeframe or ""},
        request_id=_REQUEST,
        workflow_id=_WORKFLOW,
        correlation_id=_CORRELATION,
    )
    print("Event:", event.event_type, event.hook)
    print("Occurred at:", event.occurred_at)
    print("Close:", bar.close)

    evaluator: EventStrategyEvaluator = BarCountingEvaluator(_HASH)
    policy = StrategyValidationPolicy(
        policy_version="usage-v1",
        approved_module_roots=("app.services.strategy.evaluators",),
        max_config_payload_bytes=4_096,
        max_config_nesting_depth=8,
        max_config_string_length=128,
        max_config_collection_items=64,
    )
    context = StrategyExecutionContext(
        environment=StrategyEnvironment.RESEARCH,
        decision_timestamp=datetime.now(UTC),
        timing_policy=StrategyTimingPolicy.EVENT_DRIVEN,
        seed=17,
        interface_version="v1",
        request_id=_REQUEST,
        workflow_id=_WORKFLOW,
        correlation_id=_CORRELATION,
        dependency_status={"data": "ready"},
        snapshot_refs=(market.request_id,),
        max_diagnostic_bytes=8_192,
    )
    manifest = StrategyManifest(
        strategy_id=_STRATEGY,
        strategy_version="1.0.0",
        module_path=evaluator.module_path,
        owner_ref="strategy-usage",
        interface_version="v1",
        config_schema_version="v1",
        config_schema={"type": "object"},
        required_data=("EURUSD:M5",),
        required_indicators=(),
        timing_policy=StrategyTimingPolicy.EVENT_DRIVEN,
        permitted_environments=(StrategyEnvironment.RESEARCH,),
        source_hash=_HASH,
        artifact_hash=_HASH,
        dependency_hash=_HASH,
        provenance_refs=(market.request_id,),
        supported_hooks=_HOOKS,
        requires_account_snapshot=False,
        max_batch_records=1_000,
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
        normalized_parameters={"observe": True},
        config_hash=_HASH,
        policy_version=policy.policy_version,
        request_id=_REQUEST,
    )

    print("\n-- Declared hook invocation --")
    outcome = run_event_strategy_hook(
        ref, config, event, context, evaluator, {"bars_seen": 0}
    )
    if outcome.data is None:
        print("Event hook failed:", outcome.error)
        return _UNAVAILABLE
    result = outcome.data
    print("Decisions:", len(result.decisions))
    print("Intents (neutral emits none):", len(result.intents))
    print("Committed local state:", dict(result.local_state_update or {}))

    print("\n-- Undeclared hook fails closed --")
    undeclared = event.model_copy(update={"hook": "on_unknown"})
    rejected = run_event_strategy_hook(
        ref, config, undeclared, context, evaluator, {"bars_seen": 0}
    )
    print("Status:", rejected.status)
    if rejected.error is not None:
        print("Error code:", rejected.error.code)
    print("\nLocal state commits only after the complete result validates.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
