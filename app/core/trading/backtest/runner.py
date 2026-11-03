"""Historical execution through the shared strategy runtime.

Description:
    Supply causal event snapshots and retain actual simulation results.
Purpose:
    FEAT-WIZARD-HSL-LANGUAGE: Consistent, explicit strategy execution boundaries.
Key Capabilities:
    - FR-shared-hsl-execution: Hosts log decisions; focused tests verify effects.
Python API Usage:
    Import the typed contracts and services from this module.
CLI Usage:
    uv run pytest tests/core/trading tests/workspace/algo_wizard --no-cov
"""

from __future__ import annotations

from dataclasses import replace
from typing import Any

import numpy as np

from app.core.lib.errors import DomainError
from app.core.trading.backtest.contracts import (
    EquityPoint,
    PrecisionMode,
    RunResult,
    RunSpec,
)
from app.core.trading.blocks.series import BarData
from app.core.trading.simulation.engine import SimulationEngine
from app.core.trading.strategy.contracts import (
    BarUpdateEvent,
    LifecycleEvent,
    StrategyContext,
    StrategyEffects,
)
from app.core.trading.strategy.runtime import StrategyRuntime


def _validate_hsl(spec: RunSpec) -> None:
    """Require a historical stream capable of executing the requested document."""
    strategy = spec.strategy
    from app.core.trading.strategy.hsl.documents import parse_hsl_document

    document = parse_hsl_document(strategy.hsl_json or "")
    if spec.settings.precision_mode != PrecisionMode.OHLC:
        raise DomainError(
            code="HSL_BACKTEST_PRECISION_UNSUPPORTED",
            message="HSL historical host currently requires OHLC bars",
        )
    if document.strategy.timeframe.primary in ("MN1", "CURRENT"):
        raise DomainError(
            code="HSL_UNSUPPORTED_TIMEFRAME",
            message="Calendar-based execution requires an explicit event stream",
        )
    if any(
        current.time <= previous.time
        for previous, current in zip(spec.bars, spec.bars[1:], strict=False)
    ):
        raise DomainError(
            code="HSL_INVALID_FEED",
            message="Historical bars must have strictly increasing timestamps",
        )
    supported = {"on_start", "on_stop", "on_bar_open", "on_bar_close"}
    if any(
        rule.enabled and rule.event.type not in supported
        for rule in document.strategy.rules
    ):
        raise DomainError(
            code="HSL_BACKTEST_EVENT_UNSUPPORTED",
            message="Bar backtests cannot supply this lifecycle event",
        )
    if (
        spec.symbol != document.strategy.universe.symbols[0]
        or str(spec.timeframe) != document.strategy.timeframe.primary
    ):
        raise DomainError(
            code="HSL_BACKTEST_CONTEXT_MISMATCH",
            message="Backtest stream must match the primary HSL context",
        )


def _empty_result(spec: RunSpec) -> RunResult:
    """Return an empty result without inventing trades or market data."""
    strategy = spec.strategy
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


def _settle(engine: SimulationEngine, spec: RunSpec) -> None:
    """Close remaining positions and mark the final balance."""
    if spec.bars and engine.positions:
        closing_bar = spec.bars[-1]
        if spec.strategy.hsl_json:
            closing_bar = replace(
                closing_bar, time=closing_bar.time + spec.timeframe.to_seconds()
            )
        engine.close_all_open_positions(closing_bar)
        if engine.equity_curve:
            last_pt = engine.equity_curve[-1]
            dd = max(0.0, engine.peak_equity - engine.balance)
            dd_pct = (
                dd / engine.peak_equity * 100.0 if engine.peak_equity > 0.0 else 0.0
            )
            engine.equity_curve[-1] = EquityPoint(
                timestamp=last_pt.timestamp,
                equity=engine.balance,
                balance=engine.balance,
                drawdown=dd,
                drawdown_pct=dd_pct,
            )


def _entries_today(spec: RunSpec, engine: SimulationEngine, event: Any) -> int | None:
    """Count actual filled tickets once, including partially closed positions."""
    if not spec.strategy.hsl_json:
        return None
    from datetime import UTC, datetime
    from zoneinfo import ZoneInfo

    from app.core.trading.strategy.hsl.documents import parse_hsl_document
    from app.core.trading.strategy.hsl.expressions import event_time

    document = parse_hsl_document(spec.strategy.hsl_json)
    if document.strategy.trading_options.max_trades_per_day is None:
        return None
    timezone = ZoneInfo(document.strategy.trading_options.timezone)
    day = datetime.fromtimestamp(event_time(event), UTC).astimezone(timezone).date()
    entries = {str(trade.ticket): trade.open_time for trade in engine.completed_trades}
    entries.update(
        {
            str(position.ticket): position.open_time
            for position in engine.positions.values()
        }
    )
    return sum(
        datetime.fromtimestamp(timestamp, UTC).astimezone(timezone).date() == day
        for timestamp in entries.values()
    )


def _merge_effects(effects: tuple[StrategyEffects, ...]) -> StrategyEffects:
    """Retain all event intentions while exposing one trace record per bar."""
    return StrategyEffects(
        orders_to_open=tuple(
            request for item in effects for request in item.orders_to_open
        ),
        orders_to_cancel=tuple(
            request for item in effects for request in item.orders_to_cancel
        ),
        orders_to_modify=tuple(
            request for item in effects for request in item.orders_to_modify
        ),
        positions_to_close=tuple(
            request for item in effects for request in item.positions_to_close
        ),
        state_updates=effects[-1].state_updates,
        alerts=tuple(request for item in effects for request in item.alerts),
    )


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
        if strategy.hsl_json:
            _validate_hsl(spec)
        if not spec.bars:
            return _empty_result(spec)
        symbol = spec.symbol
        timeframe = spec.timeframe
        engine = SimulationEngine(spec.settings, symbol=symbol)
        opens = np.array([float(b.open) for b in spec.bars], dtype=np.float64)
        highs = np.array([float(b.high) for b in spec.bars], dtype=np.float64)
        lows = np.array([float(b.low) for b in spec.bars], dtype=np.float64)
        closes = np.array([float(b.close) for b in spec.bars], dtype=np.float64)
        volumes = np.array([float(b.tick_volume) for b in spec.bars], dtype=np.float64)
        timestamps = np.array([int(b.time) for b in spec.bars], dtype=np.int64)
        variables = {v.name: v.default_value for v in strategy.variables}
        state: dict[str, Any] = {}
        effects_log: list[StrategyEffects] = []

        def execute(event: Any, data: BarData, price_bar: Any) -> StrategyEffects:
            nonlocal state
            positions = engine.get_open_position_infos()
            for position in positions:
                position.price_current = price_bar.close
                direction = 1 if position.position_type == 0 else -1
                position.profit = (
                    (price_bar.close - position.price_open)
                    * direction
                    * position.volume
                    * spec.settings.point_value
                )
            context = StrategyContext(
                bars=data,
                bars_by_symbol={symbol: data},
                positions=positions,
                orders=engine.get_pending_order_infos(),
                account_balance=engine.balance,
                variables=variables,
                bars_by_context={
                    (symbol, str(timeframe)): data,
                    **spec.additional_bars,
                },
                bar_close_times=spec.bar_close_times,
                economics={symbol: spec.settings.economics}
                if spec.settings.economics
                else {},
                account_equity=engine.balance
                + sum(position.profit for position in positions),
                state=state,
                entries_today=_entries_today(spec, engine, event),
            )
            effects = self.runtime.evaluate(strategy, context, event)
            if strategy.hsl_json:
                from app.core.trading.strategy.hsl.expressions import event_time

                price_bar = replace(price_bar, time=event_time(event))
            engine.apply_effects(effects, price_bar)
            state = dict(effects.state_updates)
            return effects

        for i, bar in enumerate(spec.bars):
            engine.process_pre_bar(bar)
            raw = BarData.from_arrays(
                open=opens[: i + 1],
                high=highs[: i + 1],
                low=lows[: i + 1],
                close=closes[: i + 1],
                volume=volumes[: i + 1],
                timestamps=timestamps[: i + 1],
            )
            data = replace(raw, symbol=symbol, timeframe=str(timeframe))
            opened = replace(
                bar,
                high=bar.open,
                low=bar.open,
                close=bar.open,
                tick_volume=0,
                real_volume=0,
            )
            prefix: list[StrategyEffects] = []
            if strategy.hsl_json is not None:
                if i == 0:
                    prefix.append(
                        execute(
                            LifecycleEvent(
                                "on_start", symbol, bar.time, str(timeframe)
                            ),
                            data,
                            opened,
                        )
                    )
                prefix.append(
                    execute(
                        BarUpdateEvent(symbol, timeframe, opened, False), data, opened
                    )
                )
            engine.process_intra_bar(bar)
            effects = execute(BarUpdateEvent(symbol, timeframe, bar, True), data, bar)
            effects = _merge_effects((*prefix, effects))
            effects_log.append(effects)
            engine.record_equity(bar)
        if strategy.hsl_json is not None:
            last = spec.bars[-1]
            stopped = execute(
                LifecycleEvent(
                    "on_stop",
                    symbol,
                    last.time + timeframe.to_seconds(),
                    str(timeframe),
                ),
                data,
                last,
            )
            effects_log[-1] = _merge_effects((effects_log[-1], stopped))

        _settle(engine, spec)
        metrics = engine.compute_metrics()
        return RunResult(
            strategy_id=strategy.strategy_id,
            trades=tuple(engine.completed_trades),
            equity_curve=tuple(engine.equity_curve),
            metrics=metrics,
            mae_mfe=tuple(engine.mae_mfe_records),
            effects=tuple(effects_log),
        )


__all__ = ["BacktestRunner"]
