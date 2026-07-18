"""Executable examples of the package-root Strategy contracts."""

import sys
from datetime import UTC, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.services.strategy import (
    StrategyConfig,
    StrategyEnvironment,
    StrategyExecutionContext,
    StrategyLifecycleStatus,
    StrategyOutcome,
    StrategyRef,
    StrategyTimingPolicy,
    StrategyValidationPolicy,
)

now = datetime.now(UTC)
request_id = "strategy-usage-contracts"
correlation_id = "strategy-usage-contracts-correlation"

print("\nSTRATEGY CONTRACTS")
print("=" * 88)

reference = StrategyRef(
    strategy_id="naive-ma-trend",
    exact_version="1.0.0",
    environment=StrategyEnvironment.RESEARCH,
    request_id=request_id,
    correlation_id=correlation_id,
)
config = StrategyConfig(
    strategy_id=reference.strategy_id,
    strategy_version=reference.exact_version or "1.0.0",
    config_schema_version="v1",
    parameters={
        "fast_ma_period": 20,
        "slow_ma_period": 50,
        "filter_ma_period": 200,
    },
    request_id=request_id,
)
policy = StrategyValidationPolicy(
    policy_version="research-v1",
    approved_module_roots=("app.services.strategy.evaluators",),
    max_config_payload_bytes=16_384,
    max_config_nesting_depth=8,
    max_config_string_length=512,
    max_config_collection_items=128,
)
context = StrategyExecutionContext(
    environment=StrategyEnvironment.RESEARCH,
    decision_timestamp=now,
    timing_policy=StrategyTimingPolicy.BAR_OPEN_PREVIOUS_CLOSE,
    seed=7,
    interface_version="v1",
    request_id=request_id,
    workflow_id="strategy-usage-contracts-workflow",
    correlation_id=correlation_id,
    dependency_status={"data": "ready", "indicators": "ready"},
    snapshot_refs=("live-market-read",),
    max_diagnostic_bytes=16_384,
)
outcome = StrategyOutcome[StrategyConfig](status="success", data=config)

print("Reference:", reference.model_dump(mode="json"))
print("Configuration:", config.model_dump(mode="json"))
print("Policy version:", policy.policy_version)
print("Context timing:", context.timing_policy.value)
print("Lifecycle value:", StrategyLifecycleStatus.APPROVED.value)
print("Outcome status:", outcome.status)
