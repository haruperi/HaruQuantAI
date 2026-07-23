"""Executable Optimization scoring usage example.

Demonstrates objective names, candidate scoring, deflated Sharpe calculation,
candidate ranking, Pareto candidate selection, and overfit assessment.
"""

import sys
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

# Add repository root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.services.analytics.contracts import (
    AnalyticsRunConfig,
    ClosedTrade,
    RiskFreeRateEvidence,
    StatisticalValidationConfig,
)
from app.services.analytics.reports.builder import build_performance_report
from app.services.optimization.scoring import (
    CandidateScore,
    ObjectiveName,
    assess_overfit_evidence,
    calculate_candidate_score,
    calculate_deflated_sharpe,
    count_nominal_trials,
    rank_candidates,
    select_pareto_candidates,
)
from app.utils import generate_id

NOW = datetime(2026, 7, 19, tzinfo=UTC)


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


def _score(value: float = 1.0) -> CandidateScore:
    """Build a CandidateScore fixture."""
    return CandidateScore(
        candidate_hash="a" * 64,
        objective="sharpe_ratio",
        direction="maximize",
        value=value,
        available=True,
        trade_count=40,
        metrics={"sharpe_ratio": value},
    )


def example_scoring() -> None:
    """Demonstrate candidate scoring, ranking, and overfit assessment."""
    print("=" * 80)
    print("Optimization Example 2: Candidate Scoring and Pareto Selection")
    print("=" * 80)

    # 1. Objective Enum
    print(f"Canonical Sharpe objective name: {ObjectiveName.SHARPE_RATIO.value}")

    # 2. Score candidate from Analytics report
    trade = ClosedTrade(
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
    report = build_performance_report(
        source,
        source_contract="simulation.result",
        request_id=generate_id("req"),
        initial_balance=Decimal(1000),
        account_currency="USD",
        config=_config(),
    )
    score_res = calculate_candidate_score(
        report,
        candidate_hash="a" * 64,
        objective=ObjectiveName.NET_PNL,
        enabled_objectives=frozenset({ObjectiveName.NET_PNL}),
    )
    print(
        f"Calculated candidate score: objective={score_res.objective}, value={score_res.value}"
    )

    # 3. Deflated Sharpe ratio calculation
    dsr = calculate_deflated_sharpe(
        sharpe=1.0,
        variance=0.2,
        skewness=0.0,
        kurtosis=3.0,
        sample_count=100,
        nominal_trials=10,
    )
    print(f"Calculated Deflated Sharpe Ratio: {dsr}")

    # 4. Count trials and rank candidates
    trials = count_nominal_trials(("a" * 64, "b" * 64))
    print(f"Nominal trials count: {trials}")

    ranked = rank_candidates((_score(1.5), _score(1.0)))
    print(f"Ranked top candidate value: {ranked[0].value}")

    # 5. Pareto candidate selection
    pareto_indices = select_pareto_candidates(
        ({"net_pnl": 1.0}, {"net_pnl": 2.0}), ("net_pnl",)
    )
    print(f"Pareto optimal candidate indices: {pareto_indices}")

    # 6. Overfit assessment
    overfit_diag = assess_overfit_evidence(
        in_sample=_score(1.5),
        out_of_sample=_score(1.0),
        nominal_trials=2,
        deflated_sharpe=0.7,
        minimum_trade_count=30,
    )
    print(f"Overfit trade count adequate: {overfit_diag['trade_count_adequate']}")


def main() -> None:
    """Run Optimization scoring usage example."""
    example_scoring()


if __name__ == "__main__":
    main()
