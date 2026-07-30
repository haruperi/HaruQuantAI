"""Executable package-root Strategy diagnostics example."""

import sys
from datetime import UTC, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.services.strategy import (
    create_strategy_diagnostics,
    create_strategy_execution_context,
    export_strategy_diagnostics,
    get_strategy_environment,
    get_strategy_error_catalog,
    get_strategy_error_code,
    get_strategy_timing_policy,
)


def _header(title: str) -> None:
    """Print one example heading."""
    print(f"\n{'=' * 88}\n{title}\n{'=' * 88}")


def fr_str_018() -> None:
    """Demonstrate the accepted Strategy error catalogue."""
    _header("Demonstrate the accepted Strategy error catalogue.")
    assert get_strategy_error_code("STRATEGY_INVALID_CONFIG").value == (
        "STRATEGY_INVALID_CONFIG"
    )
    assert "STRATEGY_INVALID_CONFIG" in get_strategy_error_catalog()


def fr_str_019() -> None:
    """Demonstrate the bounded diagnostic exporter."""
    _header("Demonstrate the bounded diagnostic exporter.")
    assert callable(export_strategy_diagnostics)


def fr_str_034() -> None:
    """Demonstrate the immutable diagnostic contract."""
    _header("Demonstrate the immutable diagnostic contract.")
    assert callable(create_strategy_diagnostics)


def main() -> int:
    """Export bounded redacted diagnostics and show the accepted code catalogue.

    Returns:
        ``0`` when diagnostics export and bound enforcement both behave.
    """
    fr_str_018()
    fr_str_019()
    fr_str_034()
    print("\nSTRATEGY DIAGNOSTICS")
    context = create_strategy_execution_context(
        environment=get_strategy_environment("RESEARCH"),
        decision_timestamp=datetime.now(UTC),
        timing_policy=get_strategy_timing_policy("EVENT_DRIVEN"),
        seed=11,
        interface_version="v1",
        request_id="req-aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa",
        workflow_id="strategy-usage-diagnostics-workflow",
        correlation_id="cor-bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb",
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
    diagnostics = outcome.data
    reconstructed = create_strategy_diagnostics(**diagnostics.model_dump())
    print("Schema:", diagnostics.schema_id)
    print("Contract version:", diagnostics.contract_version)
    print("Status field:", diagnostics.status)
    print("Strategy:", diagnostics.strategy_id, diagnostics.strategy_version)
    print("Request / correlation:", diagnostics.request_id, diagnostics.correlation_id)
    print("Dependency health:", dict(diagnostics.dependency_health))
    print("Payload bytes:", diagnostics.payload_bytes)
    print("Redacted paths:", diagnostics.redacted_paths)
    print("Safe details:", dict(diagnostics.safe_details))
    print("Public value-factory round trip:", reconstructed == diagnostics)
    print("Secret value never appears above.")

    print("\n-- Bound enforcement --")
    bounded_context = context.model_copy(update={"max_diagnostic_bytes": 1})
    bounded = export_strategy_diagnostics(bounded_context, {"note": "x" * 512})
    print("Status:", bounded.status)
    if bounded.error is not None:
        print("Error code:", bounded.error.code)

    print("\n-- Accepted error catalogue --")
    catalogue = get_strategy_error_catalog()
    print("Total accepted codes:", len(catalogue))
    for code in (
        get_strategy_error_code("STRATEGY_INVALID_CONFIG"),
        get_strategy_error_code("STRATEGY_LOOKAHEAD_DETECTED"),
        get_strategy_error_code("STRATEGY_ARBITRARY_CODE_REJECTED"),
        get_strategy_error_code("STRATEGY_RESOURCE_LIMIT_EXCEEDED"),
    ):
        print(" ", code.value)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
