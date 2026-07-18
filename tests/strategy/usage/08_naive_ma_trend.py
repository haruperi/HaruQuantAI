"""Run Naive MA Trend signals against real MT5 market data."""

import hashlib
import inspect
import sys
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.services.data import (
    get_market_data,
    get_symbol_metadata,
    to_ohlcv_dataframe,
)
from app.services.data.contracts import DataError
from app.services.indicators import IndicatorError, sma
from app.services.strategy import (
    NaiveMATrendEvaluator,
    StrategyEnvironment,
    StrategyExecutionContext,
    StrategyLifecycleStatus,
    StrategyManifest,
    StrategySignalEvidence,
    StrategyTimingPolicy,
    StrategyValidationPolicy,
    ValidatedStrategyConfig,
    ValidatedStrategyRef,
    evaluate_strategy_signals,
)
from app.utils import canonical_json

print("\nNAIVE MA TREND — REAL MT5 EURUSD M5 SIGNAL")
print("=" * 88)

try:
    market = get_market_data(
        source_id="mt5",
        symbol="EURUSD",
        timeframe="M5",
        limit=300,
        use_cache=False,
    )
    metadata = get_symbol_metadata(source_id="mt5", symbol="EURUSD")
    indicators = (
        sma(market, period=20),
        sma(market, period=50),
        sma(market, period=200),
    )
except (DataError, IndicatorError) as error:
    print("Live signal evidence unavailable:", error)
    sys.exit(3)

if not isinstance(metadata.point, int | float):
    print("MT5 point-size evidence unavailable:", metadata.point)
    sys.exit(3)

parameters = {
    "fast_ma_period": 20,
    "slow_ma_period": 50,
    "filter_ma_period": 200,
}
config_hash = hashlib.sha256(canonical_json(parameters).encode()).hexdigest()
source_hash = hashlib.sha256(
    inspect.getsource(NaiveMATrendEvaluator).encode()
).hexdigest()
context = StrategyExecutionContext(
    environment=StrategyEnvironment.RESEARCH,
    decision_timestamp=datetime.now(UTC),
    timing_policy=StrategyTimingPolicy.BAR_OPEN_PREVIOUS_CLOSE,
    seed=1,
    interface_version="v1",
    request_id="strategy-usage-naive-ma",
    workflow_id="strategy-usage-naive-ma-workflow",
    correlation_id="strategy-usage-naive-ma-correlation",
    dependency_status={"data": "ready", "indicators": "ready"},
    snapshot_refs=(market.request_id,),
    max_diagnostic_bytes=8_192,
)
evidence = StrategySignalEvidence(
    evidence_id=hashlib.sha256(
        f"{market.request_id}:{market.available_at.isoformat()}".encode()
    ).hexdigest(),
    primary_market=market,
    related_markets={},
    point_size=Decimal(str(metadata.point)),
    feature_values={},
    feature_available_at={},
    feature_refs={},
    active_position_tags=(),
)
config = ValidatedStrategyConfig(
    strategy_id="naive-ma-trend",
    strategy_version="1.0.0",
    config_schema_version="v1",
    normalized_parameters=parameters,
    config_hash=config_hash,
    policy_version="usage-v1",
    request_id=context.request_id,
)
evaluator = NaiveMATrendEvaluator(
    strategy_id=config.strategy_id,
    strategy_version=config.strategy_version,
    module_path="app.services.strategy.evaluators.naive_ma_trend",
    source_hash=source_hash,
    artifact_hash=source_hash,
    dependency_hash=source_hash,
)
policy = StrategyValidationPolicy(
    policy_version="usage-v1",
    approved_module_roots=("app.services.strategy.evaluators",),
    max_config_payload_bytes=4_096,
    max_config_nesting_depth=8,
    max_config_string_length=128,
    max_config_collection_items=64,
)
manifest = StrategyManifest(
    strategy_id=config.strategy_id,
    strategy_version=config.strategy_version,
    module_path=evaluator.module_path,
    owner_ref="strategy-usage",
    interface_version="v1",
    config_schema_version=config.config_schema_version,
    config_schema={"type": "object"},
    required_data=("EURUSD:M5",),
    required_indicators=("sma",),
    timing_policy=context.timing_policy,
    permitted_environments=(context.environment,),
    source_hash=source_hash,
    artifact_hash=source_hash,
    dependency_hash=source_hash,
    provenance_refs=(market.request_id,),
    supported_hooks=(),
    requires_account_snapshot=False,
    max_batch_records=10,
    max_diagnostic_bytes=context.max_diagnostic_bytes,
    max_checkpoint_bytes=8_192,
    max_local_state_bytes=8_192,
    decision_timeout_seconds=5,
)
ref = ValidatedStrategyRef(
    manifest=manifest,
    lifecycle_status=StrategyLifecycleStatus.APPROVED,
    environment=context.environment,
    policy_version=policy.policy_version,
    validation_policy=policy,
    registry_record_hash=config_hash,
    request_id=context.request_id,
    correlation_id=context.correlation_id,
)
outcome = evaluate_strategy_signals(
    ref,
    config,
    evidence,
    indicators,
    context,
    evaluator,
)
if outcome.status == "error" or outcome.data is None:
    print("Signal evaluation failed:", outcome.error)
    sys.exit(1)

signals = outcome.data
latest = to_ohlcv_dataframe(market).iloc[-1]

print("Evaluated bar:", market.end)
print("Close:", latest["close"])
for signal in signals:
    marker = "<-- ENTRY" if signal.active and "ENTRY" in signal.signal_name else ""
    print(f"{signal.signal_name:12} active={signal.active!s:5} {marker}")
