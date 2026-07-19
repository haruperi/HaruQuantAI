"""Runnable usage evidence for every public Analytics metric requirement."""

from dataclasses import replace
from datetime import UTC, datetime
from decimal import Decimal

from app.services.analytics.adapters.results import adapt_trading_result
from app.services.analytics.contracts import (
    AnalyticsRunConfig,
    RiskFreeRateEvidence,
    TradingResult,
)
from app.services.analytics.metrics.benchmarks import (
    align_benchmark_series,
    calculate_benchmark_evidence,
)
from app.services.analytics.metrics.cost_efficiency import (
    calculate_cost_efficiency_evidence,
)
from app.services.analytics.metrics.distributions import (
    calculate_distribution_evidence,
)
from app.services.analytics.metrics.drawdowns import calculate_drawdown_evidence
from app.services.analytics.metrics.groups import calculate_grouped_evidence
from app.services.analytics.metrics.ratios import calculate_ratio_evidence
from app.services.analytics.metrics.returns import calculate_return_evidence
from app.services.analytics.metrics.risk import calculate_risk_evidence
from app.services.analytics.metrics.statistics import run_statistical_validation
from app.services.analytics.metrics.trades import calculate_trade_evidence
from app.utils import logger
from tests.analytics.unit.test_results_adapter import _config, _source

NOW = datetime(2026, 7, 19, tzinfo=UTC)


def _configured_result(
    *, benchmark: bool = False
) -> tuple[TradingResult, AnalyticsRunConfig]:
    """Build a canonical result and fully source-backed metric configuration.

    Args:
        benchmark: Whether to include aligned benchmark evidence.

    Returns:
        Canonical result and Analytics run configuration.
    """
    logger.debug("Building Analytics metric usage evidence")
    config = replace(
        _config(),
        risk_free_rate=RiskFreeRateEvidence(
            rate=Decimal("0.02"),
            unit="annual_decimal",
            source="usage-fixture",
            as_of=NOW,
        ),
    )
    benchmark_evidence = (
        {"currency": "USD", "points": ({"timestamp": NOW, "value": 0.01},)}
        if benchmark
        else None
    )
    result = adapt_trading_result(
        _source(),
        source_contract="simulation.result",
        initial_balance=Decimal(1000),
        account_currency="USD",
        config=config,
        benchmark=benchmark_evidence,
    )
    return result, config


def test_usage_trades_calculate_trade_evidence() -> None:
    """Calculate cataloged closed-trade evidence."""
    logger.info("Running Analytics trade-evidence usage")
    result, _ = _configured_result()
    assert calculate_trade_evidence(result, config=_config()).section_key == "trades"


def test_usage_returns_calculate_return_evidence() -> None:
    """Calculate exact PnL and daily return evidence."""
    logger.info("Running Analytics return-evidence usage")
    result, _ = _configured_result()
    assert (
        calculate_return_evidence(result, config=_config()).section_key
        == "equity_returns"
    )


def test_usage_drawdowns_calculate_drawdown_evidence() -> None:
    """Calculate closed-trade drawdown evidence."""
    logger.info("Running Analytics drawdown-evidence usage")
    result, _ = _configured_result()
    assert (
        calculate_drawdown_evidence(result, config=_config()).section_key == "drawdown"
    )


def test_usage_risk_calculate_risk_evidence() -> None:
    """Calculate volatility and historical tail evidence."""
    logger.info("Running Analytics risk-evidence usage")
    assert calculate_risk_evidence(
        tuple(index / 1000 for index in range(30)), config=_config()
    ).metrics


def test_usage_ratios_calculate_ratio_evidence() -> None:
    """Calculate approved core ratios with risk-free evidence."""
    logger.info("Running Analytics ratio-evidence usage")
    result, config = _configured_result()
    assert calculate_ratio_evidence(result, (0.01, -0.01), config=config).metrics


def test_usage_benchmarks_align_series() -> None:
    """Align strategy and benchmark values on UTC timestamps."""
    logger.info("Running Analytics benchmark-alignment usage")
    point = ({"timestamp": NOW, "value": 0.01},)
    assert align_benchmark_series(point, point) == ((0.01,), (0.01,))


def test_usage_benchmarks_calculate_evidence() -> None:
    """Calculate explicit zero-variance benchmark evidence."""
    logger.info("Running Analytics benchmark-evidence usage")
    result, config = _configured_result(benchmark=True)
    assert calculate_benchmark_evidence(result, config=config).metrics


def test_usage_distributions_calculate_evidence() -> None:
    """Calculate the canonical distribution evidence set."""
    logger.info("Running Analytics distribution-evidence usage")
    assert calculate_distribution_evidence(
        (1.0, 2.0, 3.0, 4.0), config=_config()
    ).metrics


def test_usage_statistics_run_validation() -> None:
    """Run bounded, seeded statistical validation."""
    logger.info("Running Analytics statistical-validation usage")
    _, config = _configured_result()
    values = tuple(float(index) for index in range(30))
    assert run_statistical_validation(values, config=config).metrics


def test_usage_cost_efficiency_calculate_evidence() -> None:
    """Calculate signed costs, excursions, duration, and efficiency."""
    logger.info("Running Analytics cost-efficiency usage")
    result, _ = _configured_result()
    assert calculate_cost_efficiency_evidence(result, config=_config()).metrics


def test_usage_groups_calculate_grouped_evidence() -> None:
    """Calculate every approved metric group in stable order."""
    logger.info("Running Analytics grouped-evidence usage")
    result, config = _configured_result()
    assert len(calculate_grouped_evidence(result, config=config)) == 10
