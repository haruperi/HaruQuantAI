"""Executable Analytics adapters usage example.

Demonstrates FEAT-ANLT-02 result adapter canonicalization and closed-trade equity curve construction.
"""

from __future__ import annotations

import sys
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

# Add repository root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.services.analytics import (
    AnalyticsRunConfig,
    ClosedTrade,
    StatisticalValidationConfig,
    TradingResult,
    adapt_trading_result,
    build_closed_trade_equity_curve,
)
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
    """Build usage configuration for analytics adapters."""
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
    """Build one closed trade for adapter demonstration."""
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


def fr_anlt_050() -> None:
    """FR-ANLT-050: Stage 3 — Derive closed-trade equity curve and daily resample."""
    _header("Stage 3: Equity Curve Construction - Build Equity Curve (FR-ANLT-050)")
    trade = _trade()
    config = _config()
    curve_resp = build_closed_trade_equity_curve(
        (trade,), initial_balance=Decimal(1000), config=config
    )
    curve, daily = unwrap(curve_resp)
    print(_format_result(curve_resp))
    print(
        f"Data -> curve_points={len(curve)}, daily_points={len(daily)}, basis='{curve[0]['curve_basis']}'"
    )


def fr_anlt_027() -> None:
    """FR-ANLT-027: Stage 2 — Map approved upstream result into TradingResult contract."""
    _header("Stage 2: Result Adaptation - Adapt Upstream Result (FR-ANLT-027)")
    trade = _trade()
    config = _config()
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
    result_resp = adapt_trading_result(
        source,
        source_contract="simulation.result",
        initial_balance=Decimal(1000),
        account_currency="USD",
        config=config,
    )
    result = unwrap(result_resp)
    reconstructed = TradingResult(**dict(result.__dict__))
    print(_format_result(result_resp))
    print(
        f"Data -> contract_version='{result.contract_version}', trade_count={len(reconstructed.trades)}"
    )


def main() -> None:
    """Run all feature examples in sequential module flow order."""
    _feature_header(
        "FEATURE: FEAT-ANLT-02 — adapters/ — Approved Upstream Result Mapping\n\n"
        "Purpose: Adapt upstream simulation and trading closed-trade ledgers into canonical TradingResult models and build closed-trade equity curves.\n\n"
        "Module flow:\n"
        "-> Stage 1: Input source result mapping and ledger extraction\n"
        "-> Stage 2: Fail-closed schema mapping, upstream contract adaptation, and validation\n"
        "-> Stage 3: Closed-trade equity curve derivation, daily resampling, and TradingResult payload construction"
    )

    # Stage 2: Result adaptation & Fail-closed mapping
    fr_anlt_027()

    # Stage 3: Equity curve derivation & Payload construction
    fr_anlt_050()


if __name__ == "__main__":
    main()
