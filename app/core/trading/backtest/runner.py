"""Backtest runner orchestrating historical bar iteration and rule evaluation."""

from __future__ import annotations

from dataclasses import replace

import numpy as np

from app.core.trading.backtest.contracts import (
    EquityPoint,
    RunResult,
    RunSpec,
)
from app.core.trading.blocks.series import BarData
from app.core.trading.simulation.engine import SimulationEngine
from app.core.trading.strategy.contracts import (
    BarUpdateEvent,
    StrategyContext,
)
from app.core.trading.strategy.runtime import StrategyRuntime


class BacktestRunner:
    """Historical backtest runner evaluating strategy rules across market bars."""

    def __init__(self, runtime: StrategyRuntime | None = None) -> None:
        self.runtime = runtime or StrategyRuntime()

    def run(self, spec: RunSpec) -> RunResult:
        """Run backtest across chronological sequence of market bars.

        Orchestrates:
        1. Pre-bar checks: pending stop/limit orders evaluated at bar Open.
        2. Intra-bar checks: evaluated against High/Low (SL/TP tie-breaking).
        3. On-bar close: triggers StrategyRuntime.evaluate() with BarUpdateEvent.
        4. Applies returned StrategyEffects (orders, modifications, closes).
        5. Tracks equity curve, trade records, and MAE/MFE excursions.
        """
        strategy = spec.strategy
        if not spec.bars:
            return RunResult(
                strategy_id=strategy.strategy_id,
                trades=(),
                equity_curve=(),
                metrics={
                    "net_profit": 0.0,
                    "gross_profit": 0.0,
                    "gross_loss": 0.0,
                    "profit_factor": 0.0,
                    "win_rate": 0.0,
                    "trades_count": 0.0,
                    "winning_trades": 0.0,
                    "losing_trades": 0.0,
                    "max_drawdown": 0.0,
                    "max_drawdown_pct": 0.0,
                    "sharpe_ratio": 0.0,
                    "final_balance": spec.settings.initial_capital,
                    "final_equity": spec.settings.initial_capital,
                },
                mae_mfe=(),
            )

        symbol = spec.symbol
        timeframe = spec.timeframe
        engine = SimulationEngine(spec.settings, symbol=symbol)

        # Pre-allocate numpy arrays for fast zero-copy BarData slicing
        opens = np.array([float(b.open) for b in spec.bars], dtype=np.float64)
        highs = np.array([float(b.high) for b in spec.bars], dtype=np.float64)
        lows = np.array([float(b.low) for b in spec.bars], dtype=np.float64)
        closes = np.array([float(b.close) for b in spec.bars], dtype=np.float64)
        volumes = np.array([float(b.tick_volume) for b in spec.bars], dtype=np.float64)
        timestamps = np.array([int(b.time) for b in spec.bars], dtype=np.int64)

        variables = {v.name: v.default_value for v in strategy.variables}

        for i, bar in enumerate(spec.bars):
            # 1. Pre-bar checks: evaluate pending orders against bar Open (gap fill)
            engine.process_pre_bar(bar)

            # 2. Intra-bar checks: stop/limit triggers and SL/TP against High/Low
            engine.process_intra_bar(bar)

            # 3. Incremental BarData view up to current bar
            raw_bar_data = BarData.from_arrays(
                open=opens[: i + 1],
                high=highs[: i + 1],
                low=lows[: i + 1],
                close=closes[: i + 1],
                volume=volumes[: i + 1],
                timestamps=timestamps[: i + 1],
            )
            bar_data = replace(raw_bar_data, symbol=symbol, timeframe=str(timeframe))

            # 4. Strategy context snapshot
            context = StrategyContext(
                bars=bar_data,
                bars_by_symbol={symbol: bar_data},
                positions=engine.get_open_position_infos(),
                orders=engine.get_pending_order_infos(),
                account_balance=engine.balance,
                variables=variables,
            )

            # 5. On-bar close: pure evaluation of strategy rules
            event = BarUpdateEvent(
                symbol=symbol,
                timeframe=timeframe,
                bar=bar,
                is_bar_close=True,
            )
            effects = self.runtime.evaluate(strategy, context, event)

            # 6. Apply returned strategy effects
            engine.apply_effects(effects, bar)

            # 7. Record equity curve point
            engine.record_equity(bar)

        # End of backtest: close any positions remaining open on last bar
        if spec.bars and engine.positions:
            engine.close_all_open_positions(spec.bars[-1])
            if engine.equity_curve:
                last_pt = engine.equity_curve[-1]
                dd = max(0.0, engine.peak_equity - engine.balance)
                dd_pct = (
                    (dd / engine.peak_equity * 100.0)
                    if engine.peak_equity > 0.0
                    else 0.0
                )
                engine.equity_curve[-1] = EquityPoint(
                    timestamp=last_pt.timestamp,
                    equity=engine.balance,
                    balance=engine.balance,
                    drawdown=dd,
                    drawdown_pct=dd_pct,
                )

        metrics = engine.compute_metrics()

        return RunResult(
            strategy_id=strategy.strategy_id,
            trades=tuple(engine.completed_trades),
            equity_curve=tuple(engine.equity_curve),
            metrics=metrics,
            mae_mfe=tuple(engine.mae_mfe_records),
        )


__all__ = ["BacktestRunner"]
