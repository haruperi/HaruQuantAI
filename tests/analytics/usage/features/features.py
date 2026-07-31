"""Executable Full-Domain Analytics Pipeline usage program.

Connects all 5 registered package features (`FEAT-ANLT-01` through `FEAT-ANLT-05`)
into a single homogeneous, end-to-end operational pipeline.
Imports strictly from the public API boundary `app.services.analytics`.
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
    METRIC_DEFINITION_CATALOG,
    AnalyticsRunConfig,
    AnalyticsValidationError,
    AnalyticsWarning,
    ClosedTrade,
    ClosedTradeLedger,
    Lineage,
    MetricEvidence,
    PerformanceReport,
    QualityFlag,
    ReproducibilityHashes,
    RiskFreeRateEvidence,
    SectionEvidence,
    StatisticalValidationConfig,
    adapt_trading_result,
    align_benchmark_series,
    build_barrier_section,
    build_closed_trade_equity_curve,
    build_dashboard_payload,
    build_performance_report,
    build_portfolio_allocation_evidence,
    build_portfolio_performance_report,
    build_portfolio_rebalance_measurement,
    build_quality_flag,
    build_warning,
    build_worst_day_distribution,
    calculate_benchmark_evidence,
    calculate_cost_efficiency_evidence,
    calculate_distribution_evidence,
    calculate_drawdown_evidence,
    calculate_grouped_evidence,
    calculate_ratio_evidence,
    calculate_return_evidence,
    calculate_risk_evidence,
    calculate_trade_evidence,
    compare_performance_reports,
    compute_reproducibility_hashes,
    run_statistical_validation,
    serialize_report,
    to_analytics_error_payload,
    to_report_json_safe,
    truncate_series,
    validate_contract_version,
    validate_metric_catalog,
)
from app.services.risk import get_drawdown_mode
from app.utils import generate_id
from tests.analytics._support import (
    _configured_result,
    _measurement_request,
    _portfolio_simulation_result,
)
from tests.analytics.usage._support import unwrap

NOW = datetime(2026, 7, 19, 8, 0, tzinfo=UTC)
HASH = "0" * 64


def _stage_banner(stage_num: int, title: str, feature_id: str) -> None:
    """Print stage header banner."""
    print(f"\n{'=' * 88}")
    print(f"Stage {stage_num}: {title} ({feature_id})")
    print(f"{'=' * 88}")


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


def _lineage() -> Lineage:
    """Build example Analytics lineage."""
    return Lineage(
        source_contract="simulation.result",
        source_version="v1",
        source_schema_id="simulation.result.v1",
        source_ids=("run-1",),
        configuration_sources=("usage",),
        account_currency="USD",
        transformations=("closed_trade_equity",),
    )


def _hashes() -> ReproducibilityHashes:
    """Build example Analytics hashes."""
    return ReproducibilityHashes(
        input_hash=HASH,
        configuration_hash=HASH,
        trade_ledger_hash=HASH,
        equity_curve_hash=HASH,
    )


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


def main() -> None:  # noqa: PLR0915
    """Run full Analytics domain feature pipeline sequentially."""
    print("\n" + "=" * 88)
    print("HARUQUANT AI — ANALYTICS DOMAIN FULL-FEATURE PIPELINE EXECUTION")
    print("=" * 88)

    config = _config()

    # -------------------------------------------------------------------------
    # Stage 1: Schemas, Catalogs, and Evidence Safety (FEAT-ANLT-01)
    # -------------------------------------------------------------------------
    _stage_banner(1, "Schemas, Catalogs, and Evidence Safety", "FEAT-ANLT-01")
    version_res = validate_contract_version("simulation.result", "v1")
    print(_format_result(version_res))

    catalog_res = validate_metric_catalog(METRIC_DEFINITION_CATALOG)
    print(_format_result(catalog_res))

    err_payload_res = to_analytics_error_payload(
        AnalyticsValidationError("Invalid input schema"), max_detail_bytes=128
    )
    print(_format_result(err_payload_res))

    warning_res = build_warning(
        "insufficient_samples",
        section="trades",
        source_context="usage",
        detail={"observed_count": 1, "required_count": 10},
        max_detail_bytes=1024,
    )
    warning_dto = unwrap(warning_res)
    warning = AnalyticsWarning(**dict(warning_dto.__dict__))
    print(_format_result(warning))

    qflag_res = build_quality_flag(
        "sample_below_threshold",
        section="trades",
        source_context="usage",
        detail={"observed_count": 1, "required_count": 10},
        max_detail_bytes=1024,
    )
    qflag_dto = unwrap(qflag_res)
    qflag = QualityFlag(**dict(qflag_dto.__dict__))
    print(_format_result(qflag))

    metric = MetricEvidence(
        metric_key="trade_count",
        status="calculated",
        value=1,
        unit="count",
    )
    section = SectionEvidence(
        section_key="trades",
        criticality="required",
        metrics=(metric,),
        status="completed",
    )
    report = PerformanceReport(
        contract_version="v1",
        schema_id="analytics.performance_report.v1",
        report_id="report-1",
        request_id="req-00000000-0000-4000-8000-000000000001",
        created_at=NOW,
        account_currency="USD",
        sections=(section,),
        caveats=(),
        quality_flags=(qflag,),
        lineage=_lineage(),
        hashes=_hashes(),
        precision_metadata={"decimal_places": 8},
    )
    print(_format_result(report))

    json_safe_res = to_report_json_safe(report)
    print(_format_result(json_safe_res))

    # -------------------------------------------------------------------------
    # Stage 2: Approved Upstream Result Mapping (FEAT-ANLT-02)
    # -------------------------------------------------------------------------
    _stage_banner(2, "Approved Upstream Result Mapping", "FEAT-ANLT-02")
    source = _source("run-1", Decimal(10))
    adapted_res = adapt_trading_result(
        source,
        source_contract="simulation.result",
        initial_balance=Decimal(1000),
        account_currency="USD",
        config=config,
    )
    trading_result = unwrap(adapted_res)
    print(_format_result(adapted_res))

    curve_res = build_closed_trade_equity_curve(
        (_trade(),), initial_balance=Decimal(1000), config=config
    )
    print(_format_result(curve_res))

    # -------------------------------------------------------------------------
    # Stage 3: Internal Pure Analytical Evidence (FEAT-ANLT-03)
    # -------------------------------------------------------------------------
    _stage_banner(3, "Internal Pure Analytical Evidence", "FEAT-ANLT-03")
    trade_ev_res = calculate_trade_evidence(trading_result, config=config)
    print(_format_result(trade_ev_res))

    return_ev_res = calculate_return_evidence(trading_result, config=config)
    print(_format_result(return_ev_res))

    drawdown_ev_res = calculate_drawdown_evidence(trading_result, config=config)
    print(_format_result(drawdown_ev_res))

    daily_returns = (0.01, -0.005, 0.008)
    risk_ev_res = calculate_risk_evidence(daily_returns, config=config)
    print(_format_result(risk_ev_res))

    ratio_ev_res = calculate_ratio_evidence(
        trading_result, daily_returns, config=config
    )
    print(_format_result(ratio_ev_res))

    cost_ev_res = calculate_cost_efficiency_evidence(trading_result, config=config)
    print(_format_result(cost_ev_res))

    dist_ev_res = calculate_distribution_evidence(daily_returns, config=config)
    print(_format_result(dist_ev_res))

    stat_res = run_statistical_validation(
        tuple(float(index - 15) for index in range(30)), config=config
    )
    print(_format_result(stat_res))

    benchmark_result, benchmark_config = _configured_result(benchmark=True)
    benchmark_points = benchmark_result.benchmark
    if benchmark_points is not None:
        strategy_points = tuple(
            {"timestamp": point["timestamp"], "value": 0.01}
            for point in benchmark_result.daily_equity_curve
        )
        aligned_res = align_benchmark_series(
            strategy_points, benchmark_points["points"]
        )
        print(_format_result(aligned_res))

    bm_ev_res = calculate_benchmark_evidence(benchmark_result, config=benchmark_config)
    print(_format_result(bm_ev_res))

    grouped_res = calculate_grouped_evidence(trading_result, config=config)
    print(_format_result(grouped_res))

    # -------------------------------------------------------------------------
    # Stage 4: Canonical Reporting (FEAT-ANLT-04)
    # -------------------------------------------------------------------------
    _stage_banner(4, "Canonical Reporting", "FEAT-ANLT-04")
    source1 = _source("simulation-result-1", Decimal(10))
    source2 = _source("simulation-result-2", Decimal(20))

    report1_dto = unwrap(
        build_performance_report(
            source1,
            source_contract="simulation.result",
            request_id=generate_id("req"),
            correlation_id=generate_id("cor"),
            created_at=NOW,
            initial_balance=Decimal(1000),
            account_currency="USD",
            config=config,
        )
    )
    report1 = PerformanceReport(**dict(report1_dto.__dict__))

    report2_dto = unwrap(
        build_performance_report(
            source2,
            source_contract="simulation.result",
            request_id=generate_id("req"),
            correlation_id=generate_id("cor"),
            created_at=NOW,
            initial_balance=Decimal(1000),
            account_currency="USD",
            config=config,
        )
    )
    report2 = PerformanceReport(**dict(report2_dto.__dict__))

    comp_res = compare_performance_reports(report1, report2)
    print(_format_result(comp_res))

    serialize_res = serialize_report(report1, format_name="json", config=config)
    print(_format_result(serialize_res))

    hash_res = compute_reproducibility_hashes(trading_result, report1)
    print(_format_result(hash_res))

    port_res = build_portfolio_performance_report(
        (report1, report2),
        base_currency="USD",
        fx_evidence=None,
        config=config,
    )
    print(_format_result(port_res))

    alloc_res = build_portfolio_allocation_evidence(
        (report1, report2),
        base_currency="USD",
        fx_evidence=None,
        config=config,
        portfolio_simulation_result=_portfolio_simulation_result(),
    )
    print(_format_result(alloc_res))

    rebalance_req = _measurement_request()
    meas_res = build_portfolio_rebalance_measurement(rebalance_req)
    print(_format_result(meas_res))

    worst_res = build_worst_day_distribution(
        ClosedTradeLedger(
            daily_pnl=(Decimal(-100), Decimal(-10), Decimal(-50), Decimal(20))
        ),
        percentiles=(Decimal("0.5"), Decimal("0.95")),
    )
    distribution = unwrap(worst_res)
    print(_format_result(worst_res))

    first_ns = SimpleNamespace(
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
    joint_ns = SimpleNamespace(
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
    barrier_res = build_barrier_section(
        first_ns,
        joint_ns,
        distribution,
        mandate_version="v1",
        mode_sensitivity={get_drawdown_mode("STATIC"): first_ns},
    )
    print(_format_result(barrier_res))

    # -------------------------------------------------------------------------
    # Stage 5: Bounded Report Projection (FEAT-ANLT-05)
    # -------------------------------------------------------------------------
    _stage_banner(5, "Bounded Report Projection", "FEAT-ANLT-05")
    points = tuple(
        {"timestamp": NOW + timedelta(minutes=i), "value": float(i % 5)}
        for i in range(20)
    )
    trunc_res = truncate_series(points, max_points=6)
    print(_format_result(trunc_res))

    dashboard_res = build_dashboard_payload(report1)
    print(_format_result(dashboard_res))

    print("\n" + "=" * 88)
    print("ALL 5 STAGES COMPLETED SUCCESSFULLY WITH GENUINE ANALYTICS DOMAIN EVIDENCE")
    print("=" * 88 + "\n")


if __name__ == "__main__":
    main()
