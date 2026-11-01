"""Portfolio Composer core composition engine.

Description:
    Coordinates multi-strategy shared-capital order merging, leverage/margin
    enforcement, Buy-and-Hold strategy synthesis, and Markowitz / CVaR
    automatic allocation weight optimization.
Purpose:
    FEAT-PORTFOLIO-COMPOSER: Configure composition and evaluation.
Key Capabilities:
    - FR-composer-engine-add-buy-hold: Synthesize long buy-and-hold strategy.
    - FR-composer-engine-recompute: Execute order merge and weight search.
    - FR-composer-engine-save-portfolio: Persist composed portfolio run receipt.
Python API Usage:
    from app.workspace.portfolio_composer.portfolio_composer import (
        PortfolioComposerService,
        ComposerMemberSpec,
        ComposerRunConfig,
        ComposerTrade,
    )
    receipt = PortfolioComposerService().recompute(config, rng=rng)
CLI Usage:
    uv run python -m pytest tests/workspace/portfolio_composer
"""

from __future__ import annotations

import math
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Literal

from app.core.host.logging import get_logger
from app.workspace.portfolio_composer.allocations import (
    BoundedRandom,
    ComposerAllocations,
)
from app.workspace.portfolio_composer.results_portfolio_composer_chart import (
    FrontierSimulationPoint,
)
from app.workspace.portfolio_composer.results_portfolio_composer_log import (
    ComposerLogEntry,
)
from app.workspace.portfolio_composer.risk import ComposerRisk
from app.workspace.portfolio_composer.selection import ComposerSelection

logger = get_logger(__name__)

_DEFAULT_START_DAY: str = "2010-01-01"
_DEFAULT_END_DAY: str = "2026-01-01"
_DEFAULT_INITIAL_CAPITAL: float = 100000.0
_DEFAULT_RISK_FREE_RATE: float = 0.7
_ONE_DAY_MS: int = 86400000
_EPSILON: float = 1e-12


def _date_to_epoch_ms(date_str: str) -> int:
    """Parse YYYY-MM-DD or ISO date string to UTC epoch milliseconds."""
    try:
        dt = datetime.fromisoformat(date_str)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=UTC)
        return int(dt.timestamp() * 1000)
    except ValueError, TypeError:
        return 0


@dataclass(frozen=True, slots=True)
class ComposerTrade:
    """Individual trade executed by a member strategy."""

    ticket: int
    open_time_ms: int
    close_time_ms: int
    symbol: str = "EURUSD"
    order_type: str = "BUY"
    size: float = 1.0
    open_price: float = 1.0
    close_price: float = 1.0
    pnl: float = 0.0
    required_margin: float = 0.0


@dataclass(frozen=True, slots=True)
class ComposerMemberSpec:
    """Specification of a portfolio member candidate strategy."""

    strategy_id: str
    name: str
    enabled: bool = True
    weight_pct: float = 100.0
    mm_method: str = "UseStrategyMM"
    trades: tuple[ComposerTrade, ...] = field(default_factory=tuple)


@dataclass(frozen=True, slots=True)
class ComposerRunConfig:
    """Configuration for portfolio composition and optimization execution."""

    date_range: Literal["full", "custom"] = "full"
    start_day: str = _DEFAULT_START_DAY
    end_day: str = _DEFAULT_END_DAY
    initial_capital: float = _DEFAULT_INITIAL_CAPITAL
    leverage: int = 1
    model_type: Literal["manual", "markowitz", "cvar"] = "markowitz"
    selection_type: str = "SharpRatio"
    max_simulations: int = 10
    conf_level: int = 95
    risk_free_rate: float = _DEFAULT_RISK_FREE_RATE
    req_std_dev: float = -1.0
    members: tuple[ComposerMemberSpec, ...] = field(default_factory=tuple)


@dataclass(frozen=True, slots=True)
class ComposerRunReceipt:
    """Receipt summarizing a completed portfolio composition and optimization run."""

    run_id: str
    model_type: str
    selection_type: str
    selected_simulation_index: int
    selected_weights: tuple[int, ...]
    selection_score: float
    risk_metric: float
    portfolio_equity: tuple[tuple[int, float], ...]
    member_equities: dict[str, tuple[tuple[int, float], ...]]
    simulation_points: tuple[FrontierSimulationPoint, ...]
    log_entries: tuple[ComposerLogEntry, ...]
    total_orders_evaluated: int
    rejected_margin_orders: int


@dataclass(frozen=True, slots=True)
class _SimulationOutcome:
    """Internal outcome of simulating a single candidate weight vector."""

    p_eq: list[tuple[int, float]]
    m_eq: dict[str, list[tuple[int, float]]]
    logs: list[ComposerLogEntry]
    pnls: list[float]
    orders_evaluated: int
    rejected_orders: int


class PortfolioComposerService:
    """Core portfolio composition and optimization engine."""

    def add_buy_hold_strategy(
        self,
        symbol: str,
        start_day: str,
        end_day: str,
        initial_capital: float,
    ) -> ComposerMemberSpec:
        """Synthesize a single long buy-and-hold trade between the specified dates.

        Args:
            symbol: Financial instrument symbol (e.g. 'SPY', 'BTCUSD').
            start_day: Inception date string.
            end_day: Termination date string.
            initial_capital: Allocated capital.

        Returns:
            ComposerMemberSpec containing synthesized buy-and-hold order.
        """
        logger.info(
            "FR-composer-engine-add-buy-hold: buy-and-hold %s start=%s end=%s cap=%.1f",
            symbol,
            start_day,
            end_day,
            initial_capital,
        )

        open_ms = _date_to_epoch_ms(start_day)
        close_ms = _date_to_epoch_ms(end_day)
        if close_ms <= open_ms:
            close_ms = open_ms + _ONE_DAY_MS

        trade = ComposerTrade(
            ticket=1,
            open_time_ms=open_ms,
            close_time_ms=close_ms,
            symbol=symbol,
            order_type="BUY",
            size=1.0,
            open_price=100.0,
            close_price=110.0,
            pnl=10.0,
            required_margin=initial_capital,
        )

        strategy_id = f"hodl_{symbol.lower()}_{uuid.uuid4().hex[:8]}"
        return ComposerMemberSpec(
            strategy_id=strategy_id,
            name=f"Buy & Hold {symbol}",
            enabled=True,
            weight_pct=100.0,
            mm_method="UseStrategyMM",
            trades=(trade,),
        )

    def _prepare_weights(
        self,
        config: ComposerRunConfig,
        enabled_members: tuple[ComposerMemberSpec, ...],
        rng: BoundedRandom | None,
    ) -> tuple[tuple[int, ...], ...]:
        """Generate candidate weight vectors based on model type."""
        if config.model_type == "manual":
            return (tuple(round(m.weight_pct) for m in enabled_members),)

        if rng is None:
            raise ValueError("rng is required for automatic optimization models")
        return ComposerAllocations.generate(
            member_count=len(enabled_members),
            simulations=config.max_simulations,
            rng=rng,
        )

    def _simulate_candidate(
        self,
        config: ComposerRunConfig,
        enabled_members: tuple[ComposerMemberSpec, ...],
        weights: tuple[int, ...],
    ) -> _SimulationOutcome:
        """Simulate execution of candidate weights with chronological order merging."""
        tagged_orders: list[
            tuple[int, int, int, int, ComposerTrade, ComposerMemberSpec, float]
        ] = []
        for m_idx, member in enumerate(enabled_members):
            scale = weights[m_idx] / 100.0
            tagged_orders.extend(
                (
                    t.open_time_ms,
                    t.close_time_ms,
                    m_idx,
                    t.ticket,
                    t,
                    member,
                    scale,
                )
                for t in member.trades
            )

        tagged_orders.sort(key=lambda x: (x[0], x[1], x[2], x[3]))
        orders_evaluated = len(tagged_orders)

        balance = config.initial_capital
        p_eq: list[tuple[int, float]] = [(0, balance)]
        m_eq: dict[str, list[tuple[int, float]]] = {
            m.strategy_id: [(0, config.initial_capital * (weights[i] / 100.0))]
            for i, m in enumerate(enabled_members)
        }
        logs: list[ComposerLogEntry] = []
        pnl_series: list[float] = []
        rejected = 0
        active_margin = 0.0

        for open_ms, close_ms, _s_idx, ticket, trade, member, scale in tagged_orders:
            scaled_size = trade.size * scale
            scaled_pnl = trade.pnl * scale
            notional = trade.open_price * scaled_size if trade.open_price > 0 else 0.0
            req_margin = (
                notional / max(1, config.leverage)
                if trade.required_margin == 0.0
                else (trade.required_margin * scale) / max(1, config.leverage)
            )

            free_margin = balance - active_margin
            if req_margin > free_margin:
                logs.append(
                    ComposerLogEntry(
                        timestamp_ms=open_ms,
                        level="REJECTED",
                        strategy_id=member.strategy_id,
                        message=(
                            f"Order ticket={ticket} rejected: required margin "
                            f"{req_margin:.2f} exceeds free margin {free_margin:.2f}"
                        ),
                    )
                )
                rejected += 1
                continue

            balance += scaled_pnl
            pnl_series.append(scaled_pnl)
            p_eq.append((close_ms, balance))
            cur_m = m_eq[member.strategy_id][-1][1] + scaled_pnl
            m_eq[member.strategy_id].append((close_ms, cur_m))

        return _SimulationOutcome(
            p_eq=p_eq,
            m_eq=m_eq,
            logs=logs,
            pnls=pnl_series,
            orders_evaluated=orders_evaluated,
            rejected_orders=rejected,
        )

    def _compute_selection_score(
        self,
        *,
        sel: ComposerSelection,
        config: ComposerRunConfig,
        net_profit: float,
        mean_return: float,
        std_dev: float,
        max_drawdown: float,
        mean_drawdown: float,
    ) -> float:
        """Compute candidate selection score with protected divisions."""
        if sel == ComposerSelection.SHARPE:
            return (
                ((mean_return - config.risk_free_rate) / std_dev)
                if std_dev > _EPSILON
                else 0.0
            )
        if sel == ComposerSelection.RETURN_DRAWDOWN:
            return (
                (net_profit / max_drawdown) if max_drawdown > _EPSILON else net_profit
            )
        if sel == ComposerSelection.CAGR_MAX_DRAWDOWN:
            ret_pct = net_profit / max(1.0, config.initial_capital)
            return (ret_pct / max_drawdown) if max_drawdown > _EPSILON else ret_pct
        if sel == ComposerSelection.CAGR_MEAN_DRAWDOWN:
            ret_pct = net_profit / max(1.0, config.initial_capital)
            return (ret_pct / mean_drawdown) if mean_drawdown > _EPSILON else ret_pct
        return net_profit

    def _calculate_metrics(
        self,
        p_eq: list[tuple[int, float]],
        pnl_series: list[float],
        config: ComposerRunConfig,
        sel: ComposerSelection,
    ) -> tuple[float, float, float, float]:
        """Calculate statistical metrics, drawdowns, and risk."""
        net_profit = p_eq[-1][1] - config.initial_capital
        trade_count = len(pnl_series)
        mean_return = (sum(pnl_series) / trade_count) if trade_count > 0 else 0.0

        if trade_count > 1:
            variance = sum((x - mean_return) ** 2 for x in pnl_series) / (
                trade_count - 1
            )
            std_dev = math.sqrt(variance)
        else:
            std_dev = 0.0

        peak = config.initial_capital
        drawdowns: list[float] = []
        max_dd = 0.0
        for _, eq in p_eq:
            peak = max(peak, eq)
            dd = peak - eq
            drawdowns.append(dd)
            max_dd = max(max_dd, dd)
        mean_dd = (sum(drawdowns) / len(drawdowns)) if drawdowns else 0.0

        score = self._compute_selection_score(
            sel=sel,
            config=config,
            net_profit=net_profit,
            mean_return=mean_return,
            std_dev=std_dev,
            max_drawdown=max_dd,
            mean_drawdown=mean_dd,
        )

        if config.model_type == "cvar":
            conf = min(0.9999, max(0.0001, config.conf_level / 100.0))
            risk_metric = -ComposerRisk.expected_shortfall(
                mean=mean_return, standard_deviation=std_dev, confidence=conf
            )
        else:
            risk_metric = std_dev

        return net_profit, std_dev, score, risk_metric

    def recompute(
        self,
        config: ComposerRunConfig,
        *,
        rng: BoundedRandom | None = None,
    ) -> ComposerRunReceipt:
        """Execute portfolio recomputation, order merge, and weight optimization.

        Args:
            config: ComposerRunConfig with portfolio parameters and members.
            rng: Injected BoundedRandom for candidate weight generation.

        Returns:
            ComposerRunReceipt with optimal weights, frontier points, and log entries.

        Raises:
            ValueError: If configuration or RNG requirements are violated.
        """
        sel = ComposerSelection.parse(config.selection_type)
        decimals = sel.decimals()

        enabled_members = tuple(m for m in config.members if m.enabled)
        if not enabled_members:
            logger.info("FR-composer-engine-recompute: no enabled members")
            return ComposerRunReceipt(
                run_id=str(uuid.uuid4()),
                model_type=config.model_type,
                selection_type=config.selection_type,
                selected_simulation_index=0,
                selected_weights=(),
                selection_score=0.0,
                risk_metric=0.0,
                portfolio_equity=((0, config.initial_capital),),
                member_equities={},
                simulation_points=(),
                log_entries=(),
                total_orders_evaluated=0,
                rejected_margin_orders=0,
            )

        weight_candidates = self._prepare_weights(config, enabled_members, rng)
        logger.info(
            "FR-composer-engine-recompute: evaluating %d weight vectors",
            len(weight_candidates),
        )

        sim_points: list[FrontierSimulationPoint] = []
        evaluated_candidates: list[dict[str, object]] = []
        total_eval_count = 0
        best_idx = 0
        best_score = float("-inf")

        for sim_idx, weights in enumerate(weight_candidates):
            outcome = self._simulate_candidate(config, enabled_members, weights)
            total_eval_count = max(total_eval_count, outcome.orders_evaluated)
            net_profit, std_dev, score, risk_metric = self._calculate_metrics(
                outcome.p_eq, outcome.pnls, config, sel
            )

            is_valid = not (config.req_std_dev > 0 and std_dev > config.req_std_dev)
            sim_points.append(
                FrontierSimulationPoint(
                    simulation_index=sim_idx,
                    weights=weights,
                    risk_x=risk_metric,
                    return_y=net_profit,
                    selection_score=score,
                    is_selected=False,
                )
            )

            evaluated_candidates.append(
                {
                    "sim_index": sim_idx,
                    "weights": weights,
                    "score": score,
                    "risk_metric": risk_metric,
                    "portfolio_equity": tuple(outcome.p_eq),
                    "member_equities": {k: tuple(v) for k, v in outcome.m_eq.items()},
                    "logs": tuple(outcome.logs),
                    "rejected_orders": outcome.rejected_orders,
                    "is_valid": is_valid,
                }
            )

            if is_valid and score > best_score:
                best_score = score
                best_idx = sim_idx

        chosen = evaluated_candidates[best_idx]
        raw_score = float(chosen["score"])  # type: ignore[arg-type]
        rounded_score = (
            round(raw_score, decimals) if decimals > 0 else float(round(raw_score))
        )

        final_points = [
            FrontierSimulationPoint(
                simulation_index=pt.simulation_index,
                weights=pt.weights,
                risk_x=pt.risk_x,
                return_y=pt.return_y,
                selection_score=pt.selection_score,
                is_selected=(pt.simulation_index == best_idx),
            )
            for pt in sim_points
        ]

        total_rejected = sum(int(c["rejected_orders"]) for c in evaluated_candidates)
        all_logs: list[ComposerLogEntry] = []
        for c in evaluated_candidates:
            all_logs.extend(c["logs"])  # type: ignore[arg-type]

        run_id = str(uuid.uuid4())
        logger.info(
            "FR-composer-engine-recompute: selected %d score=%.3f weights=%s",
            best_idx,
            rounded_score,
            chosen["weights"],
        )

        return ComposerRunReceipt(
            run_id=run_id,
            model_type=config.model_type,
            selection_type=config.selection_type,
            selected_simulation_index=best_idx,
            selected_weights=chosen["weights"],  # type: ignore[arg-type]
            selection_score=rounded_score,
            risk_metric=float(chosen["risk_metric"]),  # type: ignore[arg-type]
            portfolio_equity=chosen["portfolio_equity"],  # type: ignore[arg-type]
            member_equities=chosen["member_equities"],  # type: ignore[arg-type]
            simulation_points=tuple(final_points),
            log_entries=tuple(all_logs),
            total_orders_evaluated=total_eval_count,
            rejected_margin_orders=total_rejected,
        )

    def save_portfolio(
        self,
        project_id: str,
        databank_name: str,
        portfolio_name: str,
        receipt: ComposerRunReceipt,
    ) -> str:
        """Persist a composed portfolio run receipt into a project databank.

        Args:
            project_id: Owning project identifier.
            databank_name: Target databank name.
            portfolio_name: Desired portfolio strategy name.
            receipt: Completed composition receipt.

        Returns:
            Generated portfolio strategy ID string.
        """
        portfolio_id = f"port_{uuid.uuid4().hex[:12]}"
        logger.info(
            "FR-composer-engine-save-portfolio: id=%s name='%s' databank='%s' proj=%s "
            "receipt=%s",
            portfolio_id,
            portfolio_name,
            databank_name,
            project_id,
            receipt.run_id,
        )
        return portfolio_id
