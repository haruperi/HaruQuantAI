"""Run Decomposing Trade signals against real MT5 market data."""

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
from app.services.indicators import IndicatorError, rsi
from app.services.strategy import (
    DecomposingTradeEvaluator,
    StrategyEnvironment,
    StrategyExecutionContext,
    StrategySignalEvidence,
    StrategyTimingPolicy,
    ValidatedStrategyConfig,
)
from app.utils import canonical_json

print("\nDECOMPOSING TRADE — REAL MT5 EURUSD M5 SIGNAL")
print("=" * 88)

try:
    market = get_market_data(
        source_id="mt5",
        symbol="EURUSD",
        timeframe="M5",
        limit=100,
        use_cache=False,
    )
    metadata = get_symbol_metadata(source_id="mt5", symbol="EURUSD")
    indicator = rsi(market, period=14)
except (DataError, IndicatorError) as error:
    print("Live signal evidence unavailable:", error)
    sys.exit(3)

if not isinstance(metadata.point, int | float):
    print("MT5 point-size evidence unavailable:", metadata.point)
    sys.exit(3)

parameters = {"rsi_period": 14, "oversold": "30", "overbought": "70"}
config_hash = hashlib.sha256(canonical_json(parameters).encode()).hexdigest()
source_hash = hashlib.sha256(
    inspect.getsource(DecomposingTradeEvaluator).encode()
).hexdigest()
context = StrategyExecutionContext(
    environment=StrategyEnvironment.RESEARCH,
    decision_timestamp=datetime.now(UTC),
    timing_policy=StrategyTimingPolicy.BAR_OPEN_PREVIOUS_CLOSE,
    seed=2,
    interface_version="v1",
    request_id="strategy-usage-decomposing",
    workflow_id="strategy-usage-decomposing-workflow",
    correlation_id="strategy-usage-decomposing-correlation",
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
    strategy_id="decomposing-trade",
    strategy_version="1.0.0",
    config_schema_version="v1",
    normalized_parameters=parameters,
    config_hash=config_hash,
    policy_version="usage-v1",
    request_id=context.request_id,
)
evaluator = DecomposingTradeEvaluator(
    strategy_id=config.strategy_id,
    strategy_version=config.strategy_version,
    module_path="app.services.strategy.evaluators.decomposing_trade",
    source_hash=source_hash,
    artifact_hash=source_hash,
    dependency_hash=source_hash,
)
signals = evaluator.evaluate_signals(evidence, (indicator,), config, context)
latest = to_ohlcv_dataframe(market).iloc[-1]

print("Evaluated bar:", market.end)
print("Close:", latest["close"], "RSI:", signals[0].facts["rsi"])
for signal in signals:
    marker = "<-- ENTRY" if signal.active and "ENTRY" in signal.signal_name else ""
    print(f"{signal.signal_name:12} active={signal.active!s:5} {marker}")
