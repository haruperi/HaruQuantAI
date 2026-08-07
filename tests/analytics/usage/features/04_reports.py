"""Executable Analytics reports usage example.

Demonstrates FEAT-ANLT-04 performance report building, comparison, hashing, serialization,
portfolio allocation evidence, and barrier report sections.
"""

from __future__ import annotations

import sys
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace
from typing import Any

# Add repository root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.services.analytics import (
    AnalyticsRunConfig,
    ClosedTrade,
    ClosedTradeLedger,
    RiskFreeRateEvidence,
    StatisticalValidationConfig,
    adapt_trading_result,
    build_barrier_section,
    build_performance_report,
    build_portfolio_allocation_evidence,
    build_portfolio_performance_report,
    build_portfolio_rebalance_measurement,
    build_worst_day_distribution,
    compare_performance_reports,
    compute_reproducibility_hashes,
    get_analytics_value_field,
    serialize_report,
)
from app.services.risk import get_drawdown_mode
from app.utils import generate_id
from tests.analytics._support import (
    _measurement_request,
    _portfolio_simulation_result,
)
from tests.analytics.usage._support import unwrap

NOW = datetime(2026, 7, 19, 8, 0, tzinfo=UTC)


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


def _trade(profit: Decimal = Decimal(10)) -> ClosedTrade:
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
        profit=profit,
        magic="strategy-1",
        mae=Decimal(-2),
        mfe=Decimal(12),
    )


def _source(source_id: str, profit: Decimal = Decimal(10)) -> dict[str, object]:
    """Build source mapping for report builders."""
    trade = _trade(profit)
    return {
        "contract_version": "v1",
        "schema_id": "simulation.result.v1",
        "source_id": source_id,
        "phase": "backtest",
        "window_start": NOW,
        "window_end": NOW + timedelta(days=1),
        "strategy_id": "strategy-1",
        "strategy_version": "v1",
        "symbols": ("EURUSD",),
        "timeframe": "M1",
        "closed_trades": (dict(trade.__dict__),),
        "quality_metadata": {},
        "source_metadata": {},
    }


def fr_anlt_043() -> None:
    """FR-ANLT-043: Stage 3 — Build PerformanceReport v1 from approved ledger evidence."""
    _header("Stage 3: Report Building - Build PerformanceReport (FR-ANLT-043)")
    source = _source("simulation-result-1", Decimal(10))
    report_resp = build_performance_report(
        source,
        source_contract="simulation.result",
        request_id=generate_id("req"),
        correlation_id=generate_id("cor"),
        created_at=NOW,
        initial_balance=Decimal(1000),
        account_currency="USD",
        config=_config(),
    )
    report = unwrap(report_resp)
    print(_format_result(report_resp))
    print(
        f"Data -> report_id='{report.report_id}', sections_count={len(report.sections)}"
    )


def fr_anlt_042() -> None:
    """FR-ANLT-042: Stage 3 — Compare compatible PerformanceReport instances."""
    _header("Stage 3: Report Comparison - Compare PerformanceReports (FR-ANLT-042)")
    config = _config()
    report1 = unwrap(
        build_performance_report(
            _source("simulation-result-1", Decimal(10)),
            source_contract="simulation.result",
            request_id=generate_id("req"),
            correlation_id=generate_id("cor"),
            created_at=NOW,
            initial_balance=Decimal(1000),
            account_currency="USD",
            config=config,
        )
    )
    report2 = unwrap(
        build_performance_report(
            _source("simulation-result-2", Decimal(20)),
            source_contract="simulation.result",
            request_id=generate_id("req"),
            correlation_id=generate_id("cor"),
            created_at=NOW,
            initial_balance=Decimal(1000),
            account_currency="USD",
            config=config,
        )
    )
    comp_resp = compare_performance_reports(report1, report2)
    comparison = unwrap(comp_resp)
    print(_format_result(comp_resp))
    print(
        f"Data -> section_key='{comparison.section_key}', status='{comparison.status}'"
    )


def fr_anlt_040() -> None:
    """FR-ANLT-040: Stage 3 — Serialize report as canonical JSON or human-readable text."""
    _header("Stage 3: Serialization - Serialize Report (FR-ANLT-040)")
    config = _config()
    report = unwrap(
        build_performance_report(
            _source("simulation-result-1", Decimal(10)),
            source_contract="simulation.result",
            request_id=generate_id("req"),
            correlation_id=generate_id("cor"),
            created_at=NOW,
            initial_balance=Decimal(1000),
            account_currency="USD",
            config=config,
        )
    )
    ser_resp = serialize_report(report, format_name="json", config=config)
    serialized_json = unwrap(ser_resp)
    print(_format_result(ser_resp))
    print(f"Data -> json_length={len(serialized_json)}")


def fr_anlt_039() -> None:
    """FR-ANLT-039: Stage 3 — Compute deterministic SHA-256 reproducibility hashes."""
    _header("Stage 3: Reproducibility - Compute Hashes (FR-ANLT-039)")
    config = _config()
    source = _source("simulation-result-1", Decimal(10))
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
    result = unwrap(
        adapt_trading_result(
            source,
            source_contract="simulation.result",
            initial_balance=Decimal(1000),
            account_currency="USD",
            config=config,
        )
    )
    hash_resp = compute_reproducibility_hashes(result, report)
    hashes = unwrap(hash_resp)
    print(_format_result(hash_resp))
    print(f"Data -> report_hash_present={hashes.report_hash is not None}")


def fr_anlt_041() -> None:
    """FR-ANLT-041: Stage 3 — Aggregate portfolio performance report evidence."""
    _header("Stage 3: Portfolio Report - Build Portfolio Report (FR-ANLT-041)")
    config = _config()
    report1 = unwrap(
        build_performance_report(
            _source("simulation-result-1", Decimal(10)),
            source_contract="simulation.result",
            request_id=generate_id("req"),
            correlation_id=generate_id("cor"),
            created_at=NOW,
            initial_balance=Decimal(1000),
            account_currency="USD",
            config=config,
        )
    )
    report2 = unwrap(
        build_performance_report(
            _source("simulation-result-2", Decimal(20)),
            source_contract="simulation.result",
            request_id=generate_id("req"),
            correlation_id=generate_id("cor"),
            created_at=NOW,
            initial_balance=Decimal(1000),
            account_currency="USD",
            config=config,
        )
    )
    port_resp = build_portfolio_performance_report(
        (report1, report2),
        base_currency="USD",
        fx_evidence=None,
        config=config,
    )
    portfolio = unwrap(port_resp)
    print(_format_result(port_resp))
    print(f"Data -> portfolio_report_id='{portfolio.report_id}'")


def fr_anlt_048() -> None:
    """FR-ANLT-048: Stage 3 — Project component evidence into PortfolioAllocationEvidence v1."""
    _header("Stage 3: Allocation Evidence - Build Allocation Evidence (FR-ANLT-048)")
    config = _config()
    report1 = unwrap(
        build_performance_report(
            _source("simulation-result-1", Decimal(10)),
            source_contract="simulation.result",
            request_id=generate_id("req"),
            correlation_id=generate_id("cor"),
            created_at=NOW,
            initial_balance=Decimal(1000),
            account_currency="USD",
            config=config,
        )
    )
    report2 = unwrap(
        build_performance_report(
            _source("simulation-result-2", Decimal(20)),
            source_contract="simulation.result",
            request_id=generate_id("req"),
            correlation_id=generate_id("cor"),
            created_at=NOW,
            initial_balance=Decimal(1000),
            account_currency="USD",
            config=config,
        )
    )
    alloc_resp = build_portfolio_allocation_evidence(
        (report1, report2),
        base_currency="USD",
        fx_evidence=None,
        config=config,
        portfolio_simulation_result=_portfolio_simulation_result(),
    )
    allocation = unwrap(alloc_resp)
    print(_format_result(alloc_resp))
    print(f"Data -> allocation_evidence_id='{allocation.evidence_id}'")


def fr_anlt_052() -> None:
    """FR-ANLT-052: Stage 3 — Receive rebalance measurement request and publish evidence."""
    _header(
        "Stage 3: Rebalance Measurement - Build Rebalance Measurement (FR-ANLT-052)"
    )
    request = _measurement_request()
    meas_resp = build_portfolio_rebalance_measurement(request)
    measurement = unwrap(meas_resp)
    print(_format_result(meas_resp))
    print(f"Data -> rebalance_evidence_id='{measurement.evidence_id}'")


def fr_anlt_053() -> None:
    """FR-ANLT-053: Stage 3 — Build worst-single-day percentile distribution."""
    _header(
        "Stage 3: Worst Day Distribution - Build Worst Day Distribution (FR-ANLT-053)"
    )
    worst_resp = build_worst_day_distribution(
        ClosedTradeLedger(
            daily_pnl=(Decimal(-100), Decimal(-10), Decimal(-50), Decimal(20))
        ),
        percentiles=(Decimal("0.5"), Decimal("0.95")),
    )
    distribution = unwrap(worst_resp)
    print(_format_result(worst_resp))
    print(
        f"Data -> percentiles={dict(get_analytics_value_field(distribution, 'percentiles'))}"
    )


def fr_anlt_054() -> None:
    """FR-ANLT-054: Stage 3 — Build non-fabricating barrier report section."""
    _header("Stage 3: Barrier Section - Build Barrier Section (FR-ANLT-054)")
    first = SimpleNamespace(
        mandate_version="v1",
        mode=get_drawdown_mode("STATIC"),
        paths=10,
        seed=7,
        probability_target=Decimal("0.5"),
        probability_daily_breach=Decimal("0.1"),
        probability_drawdown_breach=Decimal("0.1"),
        probability_expired=Decimal("0.3"),
        median_termination_day=Decimal(3),
    )
    joint = SimpleNamespace(
        paths=10,
        seed=7,
        account_ids=("account-1", "account-2"),
        surviving_accounts_distribution={
            0: Decimal("0.2"),
            1: Decimal("0.3"),
            2: Decimal("0.5"),
        },
        probability_none_survive=Decimal("0.2"),
        measured_correlation={"account-1:account-2": Decimal("0.8")},
    )
    worst = unwrap(
        build_worst_day_distribution(
            ClosedTradeLedger(daily_pnl=(Decimal(-100), Decimal(-10))),
            percentiles=(Decimal("0.95"),),
        )
    )
    section_resp = build_barrier_section(
        first,
        joint,
        worst,
        mandate_version="v1",
        mode_sensitivity={get_drawdown_mode("STATIC"): first},
    )
    section = unwrap(section_resp)
    print(_format_result(section_resp))
    print(f"Data -> barrier_status='{get_analytics_value_field(section, 'status')}'")


def main() -> None:
    """Run all feature examples in sequential module flow order."""
    _feature_header(
        "FEATURE: FEAT-ANLT-04 — reports/ — Canonical Reporting\n\n"
        "Purpose: Build versioned PerformanceReports, compare reports, compute reproducibility hashes, serialize reports, and publish portfolio allocation evidence.\n\n"
        "Module flow:\n"
        "-> Stage 1: Input source mapping, ledger preparation, and configuration binding\n"
        "-> Stage 2: Section criticality checking, warning/quality-flag aggregation, and hash computation\n"
        "-> Stage 3: Immutable PerformanceReport v1 envelope construction, comparison, serialization, and portfolio allocation evidence projection"
    )

    # Stage 3: Report building, comparison, hashing, serialization & projections
    fr_anlt_043()
    fr_anlt_042()
    fr_anlt_040()
    fr_anlt_039()
    fr_anlt_041()
    fr_anlt_048()
    fr_anlt_052()
    fr_anlt_053()
    fr_anlt_054()


if __name__ == "__main__":
    main()
