"""Executable package-root Strategy diagnostics example."""

import sys
from datetime import UTC, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.services.strategy import (
    StrategyEnvironment,
    StrategyExecutionContext,
    StrategyTimingPolicy,
    export_strategy_diagnostics,
)

context = StrategyExecutionContext(
    environment=StrategyEnvironment.RESEARCH,
    decision_timestamp=datetime.now(UTC),
    timing_policy=StrategyTimingPolicy.EVENT_DRIVEN,
    seed=11,
    interface_version="v1",
    request_id="strategy-usage-diagnostics",
    workflow_id="strategy-usage-diagnostics-workflow",
    correlation_id="strategy-usage-diagnostics-correlation",
    dependency_status={"data": "ready"},
    snapshot_refs=("live-read",),
    max_diagnostic_bytes=8_192,
)
outcome = export_strategy_diagnostics(
    context,
    {
        "strategy_id": "naive-ma-trend",
        "strategy_version": "1.0.0",
        "data_source": "mt5",
        "api_key": "redacted-example-value",
    },
)

print("\nSTRATEGY DIAGNOSTICS")
print("=" * 88)
print("Status:", outcome.status)
if outcome.data is not None:
    print("Schema:", outcome.data.schema_id)
    print("Redacted paths:", outcome.data.redacted_paths)
    print("Safe details:", dict(outcome.data.safe_details))
elif outcome.error is not None:
    print("Error:", outcome.error.code, outcome.error.message)
