"""Executable package-root Strategy diagnostics example."""

import sys
from datetime import UTC, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.services.strategy import (
    StrategyDiagnostics,
    StrategyEnvironment,
    StrategyErrorCode,
    StrategyExecutionContext,
    StrategyTimingPolicy,
    export_strategy_diagnostics,
)


def main() -> int:
    """Export bounded redacted diagnostics and show the accepted code catalogue.

    Returns:
        ``0`` when diagnostics export and bound enforcement both behave.
    """
    print("\nSTRATEGY DIAGNOSTICS")
    print("=" * 88)
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
    print("Status:", outcome.status)
    if outcome.data is None:
        print("Error:", outcome.error)
        return 1
    diagnostics: StrategyDiagnostics = outcome.data
    print("Schema:", diagnostics.schema_id)
    print("Contract version:", diagnostics.contract_version)
    print("Status field:", diagnostics.status)
    print("Strategy:", diagnostics.strategy_id, diagnostics.strategy_version)
    print("Request / correlation:", diagnostics.request_id, diagnostics.correlation_id)
    print("Dependency health:", dict(diagnostics.dependency_health))
    print("Payload bytes:", diagnostics.payload_bytes)
    print("Redacted paths:", diagnostics.redacted_paths)
    print("Safe details:", dict(diagnostics.safe_details))
    print("Secret value never appears above.")

    print("\n-- Bound enforcement --")
    bounded_context = context.model_copy(update={"max_diagnostic_bytes": 1})
    bounded = export_strategy_diagnostics(bounded_context, {"note": "x" * 512})
    print("Status:", bounded.status)
    if bounded.error is not None:
        print("Error code:", bounded.error.code)

    print("\n-- Accepted error catalogue --")
    print("Total accepted codes:", len(tuple(StrategyErrorCode)))
    for code in (
        StrategyErrorCode.INVALID_CONFIG,
        StrategyErrorCode.LOOKAHEAD_DETECTED,
        StrategyErrorCode.ARBITRARY_CODE_REJECTED,
        StrategyErrorCode.RESOURCE_LIMIT_EXCEEDED,
    ):
        print(" ", code.value)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
