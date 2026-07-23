"""Workflow integration for producer-neutral Analytics adaptation."""

# ruff: noqa: INP001

from datetime import UTC, datetime
from decimal import Decimal

from app.services.analytics.adapters.results import (
    adapt_trading_result,
    build_closed_trade_equity_curve,
)
from app.services.analytics.contracts import (
    AnalyticsRunConfig,
    ClosedTrade,
    StatisticalValidationConfig,
)
from app.utils import logger

NOW = datetime(2026, 7, 19, tzinfo=UTC)


def _config() -> AnalyticsRunConfig:
    """Build complete usage configuration."""
    logger.debug("Building Analytics adapter usage configuration")
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
        risk_free_rate=None,
        statistics=StatisticalValidationConfig(
            seed=1,
            bootstrap_iterations=10,
            permutation_iterations=10,
            confidence=0.95,
            alpha=0.05,
        ),
    )


def _trade() -> ClosedTrade:
    """Build one usage closed trade."""
    logger.debug("Building Analytics adapter usage trade")
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


def _results_build_equity_curve() -> None:
    """Build both documented closed-trade curves."""
    logger.debug("Running Analytics equity-curve usage")
    curve, daily = build_closed_trade_equity_curve(
        (_trade(),), initial_balance=Decimal(1000), config=_config()
    )
    assert curve[0]["curve_basis"] == "closed_trade"
    assert len(daily) == 1


def _results_adapt_trading_result() -> None:
    """Adapt a producer-neutral Simulation ledger projection."""
    logger.debug("Running Analytics result-adapter usage")
    trade = _trade()
    source = {
        "contract_version": "v1",
        "schema_id": "simulation.result.v1",
        "source_id": "run-1",
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
    result = adapt_trading_result(
        source,
        source_contract="simulation.result",
        initial_balance=Decimal(1000),
        account_currency="USD",
        config=_config(),
    )
    assert result.schema_id == "analytics.trading_result.v1"


def test_approved_sources_map_without_field_loss() -> None:
    """The canonical adapter workflow produces both result and curve evidence."""
    logger.debug("Running Analytics adapter workflow integration")
    _results_build_equity_curve()
    _results_adapt_trading_result()
