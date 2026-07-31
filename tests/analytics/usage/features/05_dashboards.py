"""Executable Analytics dashboards usage example.

Demonstrates FEAT-ANLT-05 building bounded DashboardPayload presentation projections and series truncation.
"""

from __future__ import annotations

import sys
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

# Add repository root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.services.analytics import (
    AnalyticsRunConfig,
    ClosedTrade,
    DashboardPayload,
    RiskFreeRateEvidence,
    StatisticalValidationConfig,
    build_dashboard_payload,
    build_performance_report,
    truncate_series,
)
from app.utils import generate_id
from tests.analytics.usage._support import unwrap

NOW = datetime(2026, 7, 19, tzinfo=UTC)


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
        return f"Output Result -> {type_name}({keys}) : {type_name}"
    if isinstance(obj, dict):
        keys = ", ".join(obj.keys())
        return f"Output Result -> dict({keys}) : dict"
    if hasattr(obj, "__dict__"):
        keys = ", ".join(vars(obj).keys())
        return f"Output Result -> {type_name}({keys}) : {type_name}"
    return f"Output Result -> {type_name} : {type_name}"


def _config() -> AnalyticsRunConfig:
    """Build usage configuration."""
    return AnalyticsRunConfig(
        max_warning_detail_bytes=1024,
        max_trades=100,
        max_equity_points=100,
        max_benchmark_points=100,
        max_statistical_observations=100,
        max_bootstrap_iterations=100,
        max_permutation_iterations=100,
        max_portfolio_components=10,
        max_response_bytes=100_000,
        risk_free_rate=RiskFreeRateEvidence(
            rate=Decimal("0.02"),
            unit="annual_decimal",
            source="usage-fixture",
            as_of=NOW,
        ),
        statistics=StatisticalValidationConfig(
            seed=1,
            bootstrap_iterations=10,
            permutation_iterations=10,
            confidence=0.95,
            alpha=0.05,
        ),
    )


def _trade() -> ClosedTrade:
    """Build a closed trade fixture."""
    return ClosedTrade(
        ticket="ticket-1",
        symbol="EURUSD",
        type="BUY",
        volume=Decimal(1),
        entry_time=NOW,
        entry_price=Decimal("1.10"),
        stop_loss=Decimal("1.09"),
        take_profit=Decimal("1.12"),
        exit_time=NOW,
        exit_price=Decimal("1.11"),
        comment="closed",
        commission=Decimal(-1),
        swap=Decimal(0),
        profit=Decimal(10),
        magic="strategy-1",
        mae=Decimal(-2),
        mfe=Decimal(12),
    )


def fr_anlt_045() -> None:
    """FR-ANLT-045: Stage 3 — Truncate series while preserving key extrema and endpoints."""
    _header("Stage 3: Series Truncation - Truncate Series (FR-ANLT-045)")
    points = tuple(
        {"timestamp": NOW + timedelta(minutes=i), "value": float(i % 5)}
        for i in range(20)
    )
    truncation_response = truncate_series(points, max_points=6)
    selected = unwrap(truncation_response)
    metadata = truncation_response.metadata.extensions["truncation"]
    print(_format_result(truncation_response))
    print(
        f"Data -> original_points={len(points)}, truncated_points={len(selected)}, is_truncated={metadata['truncated']}"
    )


def fr_anlt_046() -> None:
    """FR-ANLT-046: Stage 3 — Project PerformanceReport into bounded DashboardPayload v1."""
    _header("Stage 3: Dashboard Projection - Build Dashboard Payload (FR-ANLT-046)")
    config = _config()
    trade = _trade()
    source = {
        "contract_version": "v1",
        "schema_id": "simulation.result.v1",
        "source_id": "sim-run-1",
        "phase": "backtest",
        "window_start": NOW,
        "window_end": NOW,
        "strategy_id": "strategy-1",
        "strategy_version": "v1",
        "symbols": ("EURUSD",),
        "timeframe": "M1",
        "closed_trades": (dict(trade.__dict__),),
        "quality_metadata": {},
        "source_metadata": {},
    }
    report = unwrap(
        build_performance_report(
            source,
            source_contract="simulation.result",
            request_id=generate_id("req"),
            correlation_id=generate_id("cor"),
            created_at=NOW,
            initial_balance=Decimal(1000),
            account_currency="USD",
            config=config,
        )
    )
    payload_resp = build_dashboard_payload(report)
    payload_dto = unwrap(payload_resp)
    payload = DashboardPayload(**dict(payload_dto.__dict__))
    print(_format_result(payload_resp))
    print(f"Data -> schema_id='{payload.schema_id}', non_binding={payload.non_binding}")


def main() -> None:
    """Run all feature examples in sequential module flow order."""
    _feature_header(
        "FEATURE: FEAT-ANLT-05 — dashboards/ — Bounded Report Projection\n\n"
        "Purpose: Project validated PerformanceReport evidence into bounded DashboardPayload payloads and perform deterministic series truncation.\n\n"
        "Module flow:\n"
        "-> Stage 1: PerformanceReport input mapping and truncation parameter binding\n"
        "-> Stage 2: Endpoint/extrema preservation and bounding validation\n"
        "-> Stage 3: DashboardPayload v1 projection construction and truncation metadata generation"
    )

    # Stage 3: Series truncation & Dashboard payload projection
    fr_anlt_045()
    fr_anlt_046()


if __name__ == "__main__":
    main()
