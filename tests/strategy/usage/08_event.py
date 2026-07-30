"""Executable stateful event-hook example against real MT5 evidence."""

import hashlib
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.services.data import get_market_data, to_ohlcv_dataframe
from app.services.strategy import (
    create_strategy_decision,
    create_strategy_event,
    create_strategy_execution_context,
    create_strategy_manifest,
    create_strategy_validation_policy,
    create_validated_strategy_config,
    create_validated_strategy_ref,
    get_strategy_environment,
    get_strategy_lifecycle_status,
    get_strategy_timing_policy,
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


def _header(title: str) -> None:
    """Print one example heading."""
    print(f"\n{'=' * 88}\n{title}\n{'=' * 88}")


def fr_str_033() -> None:
    """Demonstrate atomic typed event evaluation."""
    _header("Demonstrate atomic typed event evaluation.")
    assert callable(run_event_strategy_hook)


def fr_str_037() -> None:
    """Demonstrate the hash-bound event evaluator contract."""
    _header("Demonstrate the hash-bound event evaluator contract.")
    assert callable(run_event_strategy_hook)


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
        decision = create_strategy_decision(
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
    fr_str_033()
    fr_str_037()
    print("\nSTATEFUL STRATEGY EVENT HOOK — REAL MT5 EURUSD M5")
    try:
        request_end = datetime.now(UTC) - timedelta(hours=2)
        market_response = get_market_data(
            source_id="mt5",
            symbol="EURUSD",
            timeframe="M5",
            start=request_end - timedelta(days=1),
            end=request_end,
            limit=2,
            use_cache=False,
            quality_failure_behavior="warn",
        )
    except Exception as error:  # noqa: BLE001 - bounded standalone evidence path.
        print("Live MT5 data unavailable:", type(error).__name__)
        return _UNAVAILABLE
    if market_response.status != "success" or market_response.data is None:
        print("Live MT5 data unavailable:", market_response.error)
        return _UNAVAILABLE
    market = market_response.data
    frame_response = to_ohlcv_dataframe(market)
    if frame_response.data is None:
        print("MT5 frame projection failed:", frame_response.error)
        return 1
    print(frame_response.data.to_string())

    bar = market.records[-1]
    source_checksum = hashlib.sha256(
        canonical_json(market.model_dump(mode="json")).encode()
    ).hexdigest()
    event = create_strategy_event(
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

    evaluator: Any = BarCountingEvaluator(_HASH)
    policy = create_strategy_validation_policy(
        policy_version="usage-v1",
        approved_module_roots=("app.services.strategy.evaluators",),
        max_config_payload_bytes=4_096,
        max_config_nesting_depth=8,
        max_config_string_length=128,
        max_config_collection_items=64,
    )
    context = create_strategy_execution_context(
        environment=get_strategy_environment("RESEARCH"),
        decision_timestamp=market.available_at + timedelta(seconds=1),
        timing_policy=get_strategy_timing_policy("EVENT_DRIVEN"),
        seed=17,
        interface_version="v1",
        request_id=_REQUEST,
        workflow_id=_WORKFLOW,
        correlation_id=_CORRELATION,
        dependency_status={"data": "ready"},
        snapshot_refs=(market.request_id,),
        max_diagnostic_bytes=8_192,
    )
    manifest = create_strategy_manifest(
        strategy_id=_STRATEGY,
        strategy_version="1.0.0",
        module_path=evaluator.module_path,
        owner_ref="strategy-usage",
        interface_version="v1",
        config_schema_version="v1",
        config_schema={"type": "object"},
        required_data=("EURUSD:M5",),
        required_indicators=(),
        timing_policy=get_strategy_timing_policy("EVENT_DRIVEN"),
        permitted_environments=(get_strategy_environment("RESEARCH"),),
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
    ref = create_validated_strategy_ref(
        manifest=manifest,
        lifecycle_status=get_strategy_lifecycle_status("APPROVED"),
        environment=get_strategy_environment("RESEARCH"),
        policy_version=policy.policy_version,
        validation_policy=policy,
        registry_record_hash=_HASH,
        request_id=_REQUEST,
        correlation_id=_CORRELATION,
    )
    config = create_validated_strategy_config(
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
        return 1
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
    if (
        rejected.error is None
        or rejected.error.code != "STRATEGY_UNSUPPORTED_TIMING_POLICY"
    ):
        print("Undeclared hook did not fail closed as expected.")
        return 1
    print("\nLocal state commits only after the complete result validates.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
