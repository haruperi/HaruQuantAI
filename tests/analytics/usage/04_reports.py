"""Executable Analytics reports usage example.

Demonstrates performance report building, comparison, hashing, and serialization.
"""

import sys
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

# Add repository root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.services.analytics import (
    AnalyticsRunConfig,
    ClosedTrade,
    PerformanceReport,
    PortfolioAllocationEvidence,
    PortfolioPerformanceReport,
    PortfolioRebalanceMeasurementEvidence,
    PortfolioRebalanceMeasurementRequest,
    RiskFreeRateEvidence,
    StatisticalValidationConfig,
    adapt_trading_result,
    build_performance_report,
    build_portfolio_allocation_evidence,
    build_portfolio_performance_report,
    build_portfolio_rebalance_measurement,
    compare_performance_reports,
    compute_reproducibility_hashes,
    serialize_report,
)
from app.utils import generate_id
from tests.analytics._support import (
    _measurement_request,
    _portfolio_simulation_result,
)
from tests.analytics.usage._support import unwrap

NOW = datetime(2026, 7, 19, 8, 0, tzinfo=UTC)


def _header(title: str) -> None:
    """Print one example heading."""
    print(f"\n{'=' * 88}\n{title}\n{'=' * 88}")


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


def example_reports() -> None:
    """Demonstrate Analytics reporting capabilities."""
    _header("Demonstrate Analytics reporting capabilities.")
    print("Analytics Example 4: Performance Report Building and Comparison")

    config = _config()
    trade1 = _trade(Decimal(10))
    trade2 = _trade(Decimal(20))

    source1 = {
        "contract_version": "v1",
        "schema_id": "simulation.result.v1",
        "source_id": "simulation-result-1",
        "phase": "backtest",
        "window_start": NOW,
        "window_end": NOW + timedelta(days=1),
        "strategy_id": "strategy-1",
        "strategy_version": "v1",
        "symbols": ("EURUSD",),
        "timeframe": "M1",
        "closed_trades": (dict(trade1.__dict__),),
        "quality_metadata": {},
        "source_metadata": {},
    }

    source2 = {
        "contract_version": "v1",
        "schema_id": "simulation.result.v1",
        "source_id": "simulation-result-2",
        "phase": "backtest",
        "window_start": NOW,
        "window_end": NOW + timedelta(days=1),
        "strategy_id": "strategy-1",
        "strategy_version": "v1",
        "symbols": ("EURUSD",),
        "timeframe": "M1",
        "closed_trades": (dict(trade2.__dict__),),
        "quality_metadata": {},
        "source_metadata": {},
    }

    # 1. Build performance reports
    report1 = unwrap(
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
    report1 = PerformanceReport(**dict(report1.__dict__))
    print(f"Report 1 ID: {report1.report_id}, sections count: {len(report1.sections)}")

    report2 = unwrap(
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
    print(f"Report 2 ID: {report2.report_id}, sections count: {len(report2.sections)}")

    # 2. Compare reports
    comparison = unwrap(compare_performance_reports(report1, report2))
    print(
        f"Report comparison section: {comparison.section_key}, "
        f"status: {comparison.status}"
    )

    # 3. Serialize report
    serialized_json = unwrap(
        serialize_report(report1, format_name="json", config=config)
    )
    print(f"Serialized report JSON length: {len(serialized_json)} chars")

    result = unwrap(
        adapt_trading_result(
            source1,
            source_contract="simulation.result",
            initial_balance=Decimal(1000),
            account_currency="USD",
            config=config,
        )
    )
    hashes = unwrap(compute_reproducibility_hashes(result, report1))
    print(f"Report reproducibility hash present: {hashes.report_hash is not None}")
    portfolio = unwrap(
        build_portfolio_performance_report(
            (report1, report2),
            base_currency="USD",
            fx_evidence=None,
            config=config,
        )
    )
    portfolio = PortfolioPerformanceReport(**dict(portfolio.__dict__))
    print(f"Portfolio report ID: {portfolio.report_id}")
    allocation = unwrap(
        build_portfolio_allocation_evidence(
            (report1, report2),
            base_currency="USD",
            fx_evidence=None,
            config=config,
            portfolio_simulation_result=_portfolio_simulation_result(),
        )
    )
    allocation = PortfolioAllocationEvidence(**dict(allocation.__dict__))
    print(f"Allocation evidence ID: {allocation.evidence_id}")
    request = _measurement_request()
    request = PortfolioRebalanceMeasurementRequest(**dict(request.__dict__))
    measurement = unwrap(build_portfolio_rebalance_measurement(request))
    measurement = PortfolioRebalanceMeasurementEvidence(**dict(measurement.__dict__))
    print(f"Rebalance measurement ID: {measurement.evidence_id}")


def fr_anlt_039() -> None:
    """FR-ANLT-039.

    The system shall compute deterministic SHA-256 input, config, ledger, equity,
    optional benchmark, and report hashes from canonical JSON while excluding
    documented nondeterministic fields.
    """
    _header(
        "FR-ANLT-039. The system shall compute deterministic SHA-256 input, config, ledger, equity, optional benchmark, and report hashes from canonical JSON while excluding documented nondeterministic fields."
    )
    example_reports()


def fr_anlt_040() -> None:
    """FR-ANLT-040.

    The system shall serialize a validated report as canonical JSON or one minimal
    approved human-readable representation without file writes or placeholder
    formatters, enforcing the injected response bound before returning.
    """
    _header(
        "FR-ANLT-040. The system shall serialize a validated report as canonical JSON or one minimal approved human-readable representation without file writes or placeholder formatters, enforcing the injected response bound before returning."
    )
    example_reports()


def fr_anlt_041() -> None:
    """FR-ANLT-041.

    The system shall aggregate actual compatible component evidence only after
    schema, base-currency, caller-supplied FX, and component-bound validation;
    missing conversion blocks affected aggregation.
    """
    _header(
        "FR-ANLT-041. The system shall aggregate actual compatible component evidence only after schema, base-currency, caller-supplied FX, and component-bound validation; missing conversion blocks affected aggregation."
    )
    example_reports()


def fr_anlt_042() -> None:
    """FR-ANLT-042.

    The system shall compare schema- and pairing-compatible reports using actual
    common cataloged metrics, preserving omissions and caveats without mutating
    either report.
    """
    _header(
        "FR-ANLT-042. The system shall compare schema- and pairing-compatible reports using actual common cataloged metrics, preserving omissions and caveats without mutating either report."
    )
    example_reports()


def fr_anlt_043() -> None:
    """FR-ANLT-043.

    The system shall build `PerformanceReport v1` from approved producer-neutral
    ledger evidence, required request/correlation IDs, caller-supplied UTC
    creation time, initial balance/account currency, injected
    bounded/statistical/risk-free configuration, optional Data-owned benchmark
    evidence, required and optional cataloged sections, deterministic
    warnings/flags, lineage, precision metadata, finite validation, and hashes.
    The public boundary logs start, validation failure, unexpected failure, and
    success with safe request/correlation IDs. `quality_flags` is drawn from the
    Evidence Catalog and is empty only when the report is a complete, clean
    measurement. The builder emits `required_section_failed` once per failed
    required section, `diagnostic_partial_report` exactly once in diagnostic mode,
    `sample_below_threshold` below the statistical minimum, and
    `intratrade_exposure_unobserved` on every report.
    """
    _header(
        "FR-ANLT-043. The system shall build `PerformanceReport v1` from approved producer-neutral ledger evidence, required request/correlation IDs, caller-supplied UTC creation time, initial balance/account currency, injected bounded/statistical/risk-free configuration, optional Data-owned benchmark evidence, required and optional cataloged sections, deterministic warnings/flags, lineage, precision metadata, finite validation, and hashes. The public boundary logs start, validation failure, unexpected failure, and success with safe request/correlation IDs. `quality_flags` is drawn from the Evidence Catalog and is empty only when the report is a complete, clean measurement. The builder emits `required_section_failed` once per failed required section, `diagnostic_partial_report` exactly once in diagnostic mode, `sample_below_threshold` below the statistical minimum, and `intratrade_exposure_unobserved` on every report."
    )
    example_reports()


def fr_anlt_048() -> None:
    """FR-ANLT-048.

    The system shall project validated component `PerformanceReport` evidence and
    required Simulation `FR-SIM-033` `PortfolioSimulationResult` evidence into
    `PortfolioAllocationEvidence v1` after exact component/source schema,
    component-result pairing, measurement-window, base-currency, fresh Data-owned
    `FXConversionEvidence`, finite-value, aligned-return, and injected
    component/response-bound validation. Dependence contains only cataloged
    pairwise `component_return_correlation`; concentration contains only cataloged
    `capital_concentration_hhi` calculated from converted actual starting equity.
    Missing, short, unaligned, or constant dependence inputs fail the complete
    projection. It shall emit no partial cross-domain evidence, recommend no
    weight, approve no portfolio, set no risk budget, and infer no missing value.
    """
    _header(
        "FR-ANLT-048. The system shall project validated component `PerformanceReport` evidence and required Simulation `FR-SIM-033` `PortfolioSimulationResult` evidence into `PortfolioAllocationEvidence v1` after exact component/source schema, component-result pairing, measurement-window, base-currency, fresh Data-owned `FXConversionEvidence`, finite-value, aligned-return, and injected component/response-bound validation. Dependence contains only cataloged pairwise `component_return_correlation`; concentration contains only cataloged `capital_concentration_hhi` calculated from converted actual starting equity. Missing, short, unaligned, or constant dependence inputs fail the complete projection. It shall emit no partial cross-domain evidence, recommend no weight, approve no portfolio, set no risk budget, and infer no missing value."
    )
    example_reports()


def fr_anlt_052() -> None:
    """FR-ANLT-052.

    The system shall receive `PortfolioRebalanceMeasurementRequest v1`, require
    exact plan/version/hash and Trading request/reference/hash bindings, accept
    only redacted reconciled-success `execute_portfolio_rebalance` facts with
    ordered successful action outcomes, verify the execution digest, and
    deterministically publish non-binding `PortfolioRebalanceMeasurementEvidence
    v1` without invoking or changing execution.
    """
    _header(
        "FR-ANLT-052. The system shall receive `PortfolioRebalanceMeasurementRequest v1`, require exact plan/version/hash and Trading request/reference/hash bindings, accept only redacted reconciled-success `execute_portfolio_rebalance` facts with ordered successful action outcomes, verify the execution digest, and deterministically publish non-binding `PortfolioRebalanceMeasurementEvidence v1` without invoking or changing execution."
    )
    example_reports()


def main() -> None:
    """Run the bounded demonstration shared by every reporting requirement."""
    example_reports()


if __name__ == "__main__":
    main()
