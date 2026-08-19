"""Executable Analytics workbench usage example.

Demonstrates FEAT-ANLT-11 building the finite owner-produced workbench
payload over one validated performance report and one canonical Simulation
result, including unavailable-section truth and explicit truncation.
"""

from __future__ import annotations

import sys
from decimal import Decimal
from pathlib import Path
from typing import Any

# Add repository root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.services.analytics import (
    build_analytics_workbench_payload,
    build_performance_report,
    deserialize_analytics_performance_report,
    serialize_report,
)
from app.utils import generate_id
from tests.analytics._support import NOW, _configured, _source_with_profit, unwrap


def _feature_header(title: str) -> None:
    """Print the feature header banner."""
    print(f"\n{'=' * 88}\n{title}\n{'=' * 88}")


def _header(title: str) -> None:
    """Print one example heading."""
    print(f"\n{'=' * 88}\n{title}\n{'=' * 88}")


def _format_result(obj: Any) -> str:
    """Dynamically format the output result type name and field/key signature."""
    cls = type(obj)
    type_name = cls.__name__
    if hasattr(cls, "model_fields"):
        keys = ", ".join(cls.model_fields.keys())
        return f"SUCCESS: Output Result -> {type_name}({keys}) : {type_name}"
    if isinstance(obj, dict):
        keys = ", ".join(obj.keys())
        return f"SUCCESS: Output Result -> dict({keys}) : dict"
    if hasattr(obj, "__dict__"):
        keys = ", ".join(vars(obj).keys())
        return f"SUCCESS: Output Result -> {type_name}({keys}) : {type_name}"
    return f"SUCCESS: Output Result -> {type_name} : {type_name}"


_SIMULATION_RESULT: dict[str, object] = {
    "contract_version": "v1",
    "schema_id": "simulation.result.v1",
    "run_id": "run-usage-workbench",
    "status": "completed",
}


def _report() -> Any:
    """Build one validated report from bounded two-trade evidence."""
    source = _source_with_profit(Decimal(25))
    trades = source["closed_trades"]
    first = trades[0]  # type: ignore[index]
    second = {**first, "ticket": "ticket-2", "profit": Decimal(-5)}
    source["closed_trades"] = (first, second)
    return unwrap(
        build_performance_report(
            source,
            source_contract="simulation.result",
            request_id=generate_id("req"),
            correlation_id=generate_id("cor"),
            created_at=NOW,
            initial_balance=Decimal(1000),
            account_currency="USD",
            config=_configured(),
        )
    )


def build_payload() -> None:
    """Demonstrate the complete finite workbench projection."""
    _header("Projection - Build Analytics Workbench Payload")
    payload = unwrap(build_analytics_workbench_payload(_report(), _SIMULATION_RESULT))
    print(_format_result(payload))
    print(
        f"Data -> schema_id='{payload.schema_id}', report_id='{payload.report_id}', "
        f"summary_items={payload.summary.sample_count}, "
        f"equity_points={payload.equity_curve.sample_count}"
    )


def unavailable_truth() -> None:
    """Demonstrate unavailable sections never substitute zero.

    Report-owned presentation series (drawdown, monthly returns) are now
    completed from owner evidence; ledger-owned workbench sections remain
    unavailable with their exact reason because ``_SIMULATION_RESULT`` carries
    no ``closed_trades`` ledger here.
    """
    _header("Truth - Unavailable Sections Never Substitute Zero")
    payload = unwrap(build_analytics_workbench_payload(_report(), _SIMULATION_RESULT))
    print(
        f"Data -> drawdown_curve='{payload.drawdown_curve.status}' "
        f"reason='{payload.drawdown_curve.reason}', "
        f"monthly_returns='{payload.monthly_returns.status}' "
        f"reason='{payload.monthly_returns.reason}', "
        f"period_tables='{payload.period_tables.status}' "
        f"reason='{payload.period_tables.reason}'"
    )


def report_deserialization() -> None:
    """Demonstrate the strict report deserializer over a serialized report."""
    _header("Deserialization - Canonical Report Round Trip")
    report = _report()
    artifact = unwrap(
        serialize_report(report, format_name="json", config=_configured())
    )
    rebuilt = unwrap(deserialize_analytics_performance_report(artifact))
    print(
        f"Data -> report_id='{rebuilt.report_id}', "
        f"schema_id='{rebuilt.schema_id}', "
        f"section_keys={[s.section_key for s in rebuilt.sections]}"
    )


def explicit_truncation() -> None:
    """Demonstrate bounded section retention with visible truncation."""
    _header("Bounds - Explicit Section Truncation")
    payload = unwrap(
        build_analytics_workbench_payload(_report(), _SIMULATION_RESULT, max_points=1)
    )
    print(
        f"Data -> equity_curve truncated={payload.equity_curve.truncated}, "
        f"sample_count={payload.equity_curve.sample_count}, "
        f"total_count={payload.equity_curve.total_count}, "
        f"truncation_rows={len(payload.truncation)}"
    )


def fr_anlt_079() -> None:
    """
    FR-ANLT-079: Stage 3 — Expose the finite Analytics workbench projection.

    The system shall project one validated PerformanceReport and canonical
    Simulation result into the bounded non-binding workbench payload with
    stable sections, preserved source contexts, exact unavailability
    reasons, and explicit truncation evidence, without persistence or
    recalculation outside Analytics.
    """
    build_payload()
    unavailable_truth()
    report_deserialization()
    payload = unwrap(build_analytics_workbench_payload(_report(), _SIMULATION_RESULT))
    print(_format_result(payload))
    print(
        f"Data -> section_count={len(payload.__dataclass_fields__)}, non_binding={payload.non_binding}"
    )


def main() -> None:
    """Run all feature examples in sequential module flow order."""
    _feature_header(
        "FEATURE: FEAT-ANLT-11 — workbench/ — Finite Workbench Projection\n\n"
        "Purpose: Project one validated PerformanceReport and canonical "
        "Simulation result into 17 bounded, non-binding workbench sections "
        "with exact unavailability reasons and explicit truncation.\n\n"
        "Module flow:\n"
        "-> Stage 1: Validated report and canonical Simulation result inputs\n"
        "-> Stage 2: Owner-only projection with preserved source contexts\n"
        "-> Stage 3: Unavailable-section truth and explicit bounds"
    )
    fr_anlt_079()
    explicit_truncation()


if __name__ == "__main__":
    main()
