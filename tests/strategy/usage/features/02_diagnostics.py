"""Executable package-root Strategy diagnostics example."""

import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.services.strategy import (
    create_strategy_diagnostics,
    create_strategy_execution_context,
    export_strategy_diagnostics,
    get_strategy_environment,
    get_strategy_error_catalog,
    get_strategy_error_code,
    get_strategy_timing_policy,
)


def _feature_header(title: str) -> None:
    """Print the feature header banner."""
    print(f"\n\n{'=' * 88}\n{title}\n{'=' * 88}")


def _header(title: str) -> None:
    """Print one example heading."""
    print(f"\n{'=' * 88}\n{title}\n{'=' * 88}")


def _format_result(obj: Any) -> str:
    """Dynamically format the output result type name and field/key signature."""
    cls = type(obj)
    type_name = cls.__name__
    if hasattr(cls, "model_fields"):
        keys = ", ".join(cls.model_fields.keys())
        return f"Output Result -> {type_name}({keys}) : {type_name}"
    if isinstance(obj, dict):
        keys = ", ".join(obj.keys())
        return f"Output Result -> dict({keys}) : dict"
    if hasattr(obj, "__dict__"):
        keys = ", ".join(vars(obj).keys())
        return f"Output Result -> {type_name}({keys}) : {type_name}"
    return f"Output Result -> {type_name} : {type_name}"


def fr_str_018() -> None:
    """FR-STR-018: Stage 1 — Accepted error catalogue."""
    _header("Stage 1: Accepted Error Catalogue (FR-STR-018)")
    result = get_strategy_error_catalog()
    sample_code = get_strategy_error_code("STRATEGY_INVALID_CONFIG")
    print(_format_result(result))
    print(
        f"Data -> total_accepted_codes={len(result)}, sample_code='{sample_code.value}'"
    )


def fr_str_019() -> None:
    """FR-STR-019: Stage 2 — Export bounded redacted diagnostics."""
    _header("Stage 2: Export Bounded Redacted Diagnostics (FR-STR-019)")
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
    result = export_strategy_diagnostics(
        context,
        {
            "strategy_id": "naive-ma-trend",
            "strategy_version": "1.0.0",
            "data_source": "mt5",
            "api_key": "redacted-example-value",  # pragma: allowlist secret
        },
    )
    print(_format_result(result))
    print(
        f"Data -> status='{result.status}', has_diagnostics={result.data is not None}"
    )


def fr_str_034() -> None:
    """FR-STR-034: Stage 3 — Structured diagnostics contract."""
    _header("Stage 3: Structured Diagnostics Contract (FR-STR-034)")
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
        },
    )
    if outcome.data is None:
        raise RuntimeError("Diagnostics export failed")
    result = create_strategy_diagnostics(**outcome.data.model_dump())
    print(_format_result(result))
    print(
        f"Data -> schema_id='{result.schema_id}', strategy_id='{result.strategy_id}', payload_bytes={result.payload_bytes}"
    )


def main() -> None:
    """Run all feature examples in sequential module flow order."""
    _feature_header(
        "FEATURE: FEAT-STR-02 — diagnostics/ — Deterministic Safe Diagnostics\n\n"
        "Purpose: Maintain the reduced accepted error catalogue and export bounded, redacted diagnostics.\n\n"
        "Module flow:\n"
        "-> Context + diagnostic facts\n"
        "-> Recursive redaction & payload bound checks\n"
        "-> Redacted StrategyDiagnostics export"
    )

    # 1. Stage 1: Accepted error catalogue
    fr_str_018()

    # 2. Stage 2: Export bounded redacted diagnostics
    fr_str_019()

    # 3. Stage 3: Structured diagnostics contract
    fr_str_034()


if __name__ == "__main__":
    main()
