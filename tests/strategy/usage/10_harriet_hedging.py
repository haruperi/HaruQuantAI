"""Run Harriet Hedging signals against real multi-timeframe MT5 data."""

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
from app.services.strategy import (
    HarrietHedgingEvaluator,
    StrategyEnvironment,
    StrategyExecutionContext,
    StrategySignalEvidence,
    StrategyTimingPolicy,
    ValidatedStrategyConfig,
)
from app.utils import canonical_json

print("\nHARRIET HEDGING — REAL MT5 EURUSD M5/H1 SIGNAL")
print("=" * 88)

try:
    lower = get_market_data(
        source_id="mt5",
        symbol="EURUSD",
        timeframe="M5",
        limit=20,
        use_cache=False,
    )
    higher = get_market_data(
        source_id="mt5",
        symbol="EURUSD",
        timeframe="H1",
        limit=20,
        use_cache=False,
    )
    metadata = get_symbol_metadata(source_id="mt5", symbol="EURUSD")
except DataError as error:
    print("Live signal evidence unavailable:", error.code)
    sys.exit(3)

if not isinstance(metadata.point, int | float):
    print("MT5 point-size evidence unavailable:", metadata.point)
    sys.exit(3)

parameters = {
    "higher_timeframe": "H1",
    "lower_timeframe": "M5",
    "pip_multiplier": "10",
    "higher_min_distance_pips": "5",
    "lower_min_distance_pips": "2",
}
config_hash = hashlib.sha256(canonical_json(parameters).encode()).hexdigest()
source_hash = hashlib.sha256(
    inspect.getsource(HarrietHedgingEvaluator).encode()
).hexdigest()
context = StrategyExecutionContext(
    environment=StrategyEnvironment.RESEARCH,
    decision_timestamp=datetime.now(UTC),
    timing_policy=StrategyTimingPolicy.BAR_OPEN_PREVIOUS_CLOSE,
    seed=3,
    interface_version="v1",
    request_id="strategy-usage-harriet",
    workflow_id="strategy-usage-harriet-workflow",
    correlation_id="strategy-usage-harriet-correlation",
    dependency_status={"data": "ready"},
    snapshot_refs=(lower.request_id, higher.request_id),
    max_diagnostic_bytes=8_192,
)
evidence = StrategySignalEvidence(
    evidence_id=hashlib.sha256(
        f"{lower.request_id}:{higher.request_id}:{lower.available_at.isoformat()}".encode()
    ).hexdigest(),
    primary_market=lower,
    related_markets={"H1": higher},
    point_size=Decimal(str(metadata.point)),
    feature_values={},
    feature_available_at={},
    feature_refs={},
    active_position_tags=(),
)
config = ValidatedStrategyConfig(
    strategy_id="harriet-hedging",
    strategy_version="1.0.0",
    config_schema_version="v1",
    normalized_parameters=parameters,
    config_hash=config_hash,
    policy_version="usage-v1",
    request_id=context.request_id,
)
evaluator = HarrietHedgingEvaluator(
    strategy_id=config.strategy_id,
    strategy_version=config.strategy_version,
    module_path="app.services.strategy.evaluators.harriet_hedging",
    source_hash=source_hash,
    artifact_hash=source_hash,
    dependency_hash=source_hash,
)
try:
    signals = evaluator.evaluate_signals(evidence, (), config, context)
except ValueError as error:
    print("Point-in-time higher timeframe evidence unavailable:", error)
    sys.exit(3)

latest = to_ohlcv_dataframe(lower).iloc[-1]
print("Evaluated lower-timeframe bar:", lower.end)
print("Close:", latest["close"])
for signal in signals:
    marker = "<-- ENTRY" if signal.active else ""
    print(f"{signal.signal_name:12} active={signal.active!s:5} {marker}")
