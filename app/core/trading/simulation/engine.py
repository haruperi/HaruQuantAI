"""Historical order matching, partial closes, and pending expiry.

Description:
    Apply strategy intentions to isolated simulation positions and trade records.
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

import math
from dataclasses import dataclass
from itertools import count
from typing import TYPE_CHECKING

from app.core.data.contracts import MarketBar
from app.core.enums import (
    OrderState,
    OrderType,
    PositionType,
)
from app.core.host.logging import get_logger
from app.core.lib.errors import DomainError
from app.core.trading.backtest.contracts import (
    BacktestSettings,
    EquityPoint,
    MaeMfeRecord,
    SameBarExecutionRule,
    TradeRecord,
)
from app.core.trading.connection.contracts import OrderInfo, PositionInfo

if TYPE_CHECKING:
    from app.core.trading.strategy.contracts import (
        CloseRequest,
        OrderModification,
        OrderRequest,
        StrategyEffects,
    )

logger = get_logger(__name__)


@dataclass(slots=True)
class PositionState:
    """Active open position tracked during historical simulation."""

    ticket: int
    symbol: str
    direction: int  # 1 for Long/Buy, -1 for Short/Sell
    volume: float
    open_time: int
    open_price: float
    sl: float = 0.0
    tp: float = 0.0
    magic: int = 0
    comment: str = ""
    commission_paid: float = 0.0
    slippage_incurred: float = 0.0
    mae_price: float = 0.0
    mfe_price: float = 0.0


@dataclass(slots=True)
class PendingOrderState:
    """Pending limit or stop order waiting for price trigger."""

    ticket: int
    symbol: str
    direction: int
    order_type: OrderType
    volume: float
    price: float
    sl: float = 0.0
    tp: float = 0.0
    magic: int = 0
    comment: str = ""
    expires_at: int = 0


class SimulationEngine:
    """Historical bar matching engine implementing broker execution semantics."""

    def __init__(
        self,
        settings: BacktestSettings | None = None,
        symbol: str = "",
    ) -> None:
        self.settings = settings or BacktestSettings()
        self.symbol: str = symbol
        self.balance: float = float(self.settings.initial_capital)
        self.peak_equity: float = float(self.settings.initial_capital)

        self.positions: dict[int, PositionState] = {}
        self.pending_orders: dict[int, PendingOrderState] = {}
        self.completed_trades: list[TradeRecord] = []
        self.mae_mfe_records: list[MaeMfeRecord] = []
        self.equity_curve: list[EquityPoint] = []

        self._ticket_gen = count(1)

    def _next_ticket(self) -> int:
        return next(self._ticket_gen)

    def process_pre_bar(self, bar: MarketBar, symbol: str | None = None) -> None:
        """Evaluate pending stop and limit orders at bar Open with gap fill detection."""
        open_price = float(bar.open)
        bar_time = int(bar.time)
        target_symbol = symbol or self.symbol

        for ticket, order in list(self.pending_orders.items()):
            if order.expires_at and order.expires_at <= bar.time:
                del self.pending_orders[ticket]
                continue
            if target_symbol and order.symbol and order.symbol != target_symbol:
                continue

            triggered = False
            fill_price = order.price
            slippage = self.settings.slippage_points

            if order.order_type == OrderType.BUY_LIMIT:
                if open_price <= order.price:
                    triggered = True
                    # Gap down: opened lower than limit price
                    fill_price = min(order.price, open_price) + slippage

            elif order.order_type == OrderType.SELL_LIMIT:
                if open_price >= order.price:
                    triggered = True
                    # Gap up: opened higher than limit price
                    fill_price = max(order.price, open_price) - slippage

            elif order.order_type == OrderType.BUY_STOP:
                if open_price >= order.price:
                    triggered = True
                    # Gap up: opened higher than stop trigger
                    fill_price = max(order.price, open_price) + slippage

            elif order.order_type == OrderType.SELL_STOP:
                if open_price <= order.price:
                    triggered = True
                    # Gap down: opened lower than stop trigger
                    fill_price = min(order.price, open_price) - slippage

            if triggered:
                del self.pending_orders[ticket]
                self._open_position(
                    symbol=order.symbol or target_symbol,
                    direction=order.direction,
                    volume=order.volume,
                    open_price=fill_price,
                    open_time=bar_time,
                    sl=order.sl,
                    tp=order.tp,
                    magic=order.magic,
                    comment=order.comment,
                    slippage=slippage,
                )

    def process_intra_bar(self, bar: MarketBar, symbol: str | None = None) -> None:
        """Evaluate intra-bar pending order triggers, update MAE/MFE, and check SL/TP."""
        high = float(bar.high)
        low = float(bar.low)
        bar_time = int(bar.time)
        slippage = self.settings.slippage_points
        target_symbol = symbol or self.symbol

        # 1. Intra-bar pending orders (triggers within [low, high] that did not trigger at open)
        for ticket, order in list(self.pending_orders.items()):
            if order.expires_at and order.expires_at <= bar.time:
                del self.pending_orders[ticket]
                continue
            if target_symbol and order.symbol and order.symbol != target_symbol:
                continue

            triggered = False
            fill_price = order.price

            if order.order_type == OrderType.BUY_LIMIT and low <= order.price:
                triggered = True
                fill_price = order.price + slippage
            elif order.order_type == OrderType.SELL_LIMIT and high >= order.price:
                triggered = True
                fill_price = order.price - slippage
            elif order.order_type == OrderType.BUY_STOP and high >= order.price:
                triggered = True
                fill_price = order.price + slippage
            elif order.order_type == OrderType.SELL_STOP and low <= order.price:
                triggered = True
                fill_price = order.price - slippage

            if triggered:
                del self.pending_orders[ticket]
                self._open_position(
                    symbol=order.symbol or target_symbol,
                    direction=order.direction,
                    volume=order.volume,
                    open_price=fill_price,
                    open_time=bar_time,
                    sl=order.sl,
                    tp=order.tp,
                    magic=order.magic,
                    comment=order.comment,
                    slippage=slippage,
                )

        # 2. Update MAE and MFE on all currently open positions
        for pos in self.positions.values():
            if target_symbol and pos.symbol and pos.symbol != target_symbol:
                continue
            if pos.direction == 1:
                # Long position: adverse is lower low, favorable is higher high
                pos.mae_price = low if pos.mae_price == 0.0 else min(pos.mae_price, low)
                pos.mfe_price = (
                    high if pos.mfe_price == 0.0 else max(pos.mfe_price, high)
                )
            else:
                # Short position: adverse is higher high, favorable is lower low
                pos.mae_price = (
                    high if pos.mae_price == 0.0 else max(pos.mae_price, high)
                )
                pos.mfe_price = low if pos.mfe_price == 0.0 else min(pos.mfe_price, low)

        # 3. Evaluate Stop Loss and Take Profit
        for pos in list(self.positions.values()):
            if target_symbol and pos.symbol and pos.symbol != target_symbol:
                continue

            open_price = float(bar.open)

            if pos.direction == 1:  # Long
                sl_hit = pos.sl > 0.0 and low <= pos.sl
                tp_hit = pos.tp > 0.0 and high >= pos.tp

                if sl_hit and tp_hit:
                    # Same-bar conflict tie-breaking
                    if (
                        self.settings.same_bar_sl_tp_rule
                        == SameBarExecutionRule.WORST_CASE
                    ):
                        sl_exec = (
                            min(open_price, pos.sl) if open_price < pos.sl else pos.sl
                        )
                        self._close_position(
                            pos, sl_exec - slippage, bar_time, "SL", slippage
                        )
                    else:
                        tp_exec = (
                            max(open_price, pos.tp) if open_price > pos.tp else pos.tp
                        )
                        self._close_position(
                            pos, tp_exec - slippage, bar_time, "TP", slippage
                        )
                elif sl_hit:
                    sl_exec = min(open_price, pos.sl) if open_price < pos.sl else pos.sl
                    self._close_position(
                        pos, sl_exec - slippage, bar_time, "SL", slippage
                    )
                elif tp_hit:
                    tp_exec = max(open_price, pos.tp) if open_price > pos.tp else pos.tp
                    self._close_position(
                        pos, tp_exec - slippage, bar_time, "TP", slippage
                    )

            else:  # Short
                sl_hit = pos.sl > 0.0 and high >= pos.sl
                tp_hit = pos.tp > 0.0 and low <= pos.tp

                if sl_hit and tp_hit:
                    if (
                        self.settings.same_bar_sl_tp_rule
                        == SameBarExecutionRule.WORST_CASE
                    ):
                        sl_exec = (
                            max(open_price, pos.sl) if open_price > pos.sl else pos.sl
                        )
                        self._close_position(
                            pos, sl_exec + slippage, bar_time, "SL", slippage
                        )
                    else:
                        tp_exec = (
                            min(open_price, pos.tp) if open_price < pos.tp else pos.tp
                        )
                        self._close_position(
                            pos, tp_exec + slippage, bar_time, "TP", slippage
                        )
                elif sl_hit:
                    sl_exec = max(open_price, pos.sl) if open_price > pos.sl else pos.sl
                    self._close_position(
                        pos, sl_exec + slippage, bar_time, "SL", slippage
                    )
                elif tp_hit:
                    tp_exec = min(open_price, pos.tp) if open_price < pos.tp else pos.tp
                    self._close_position(
                        pos, tp_exec + slippage, bar_time, "TP", slippage
                    )

    def apply_effects(
        self,
        effects: StrategyEffects,
        bar: MarketBar,
        symbol: str | None = None,
    ) -> None:
        """Apply orders, modifications, cancellations, and closes emitted on bar close."""
        bar_close = float(bar.close)
        bar_time = int(bar.time)
        slippage = self.settings.slippage_points
        target_symbol = symbol or self.symbol

        # 1. Close requests
        for close_req in effects.positions_to_close:
            self._handle_close_request(
                close_req, target_symbol, bar_close, bar_time, slippage
            )

        # 2. Orders to cancel
        for cancel_id in effects.orders_to_cancel:
            try:
                ticket = int(cancel_id)
                self.pending_orders.pop(ticket, None)
            except ValueError:
                for t, o in list(self.pending_orders.items()):
                    if o.comment == cancel_id:
                        del self.pending_orders[t]

        # 3. Orders to modify
        for mod in effects.orders_to_modify:
            self._handle_order_modification(mod)

        # 4. Orders to open
        for order_req in effects.orders_to_open:
            self._handle_order_request(
                order_req, bar_close, bar_time, slippage, target_symbol
            )

    def _handle_close_request(
        self,
        req: CloseRequest,
        symbol: str,
        bar_close: float,
        bar_time: int,
        slippage: float,
    ) -> None:
        matched: list[PositionState] = []
        if req.ticket:
            try:
                t = int(req.ticket)
                if t in self.positions:
                    matched.append(self.positions[t])
            except ValueError:
                pass
        else:
            matched.extend(
                p for p in self.positions.values() if not symbol or p.symbol == symbol
            )

        for pos in matched:
            reason = req.comment or "SIGNAL"
            if pos.direction == 1:
                exec_price = bar_close - slippage
            else:
                exec_price = bar_close + slippage
            if req.volume is not None and (
                not math.isfinite(req.volume) or req.volume <= 0
            ):
                raise DomainError(
                    code="INVALID_CLOSE_VOLUME",
                    message="Close quantity must be finite and positive",
                )
            if req.volume is not None and 0 < req.volume < pos.volume:
                from dataclasses import replace

                fraction = req.volume / pos.volume
                partial = replace(
                    pos,
                    volume=req.volume,
                    commission_paid=pos.commission_paid * fraction,
                    slippage_incurred=pos.slippage_incurred * fraction,
                )
                remainder = replace(
                    pos,
                    volume=pos.volume - req.volume,
                    commission_paid=pos.commission_paid * (1 - fraction),
                    slippage_incurred=pos.slippage_incurred * (1 - fraction),
                )
                self._close_position(partial, exec_price, bar_time, reason, slippage)
                self.positions[pos.ticket] = remainder
            else:
                self._close_position(pos, exec_price, bar_time, reason, slippage)

    def _handle_order_modification(self, mod: OrderModification) -> None:
        try:
            t = int(mod.ticket)
        except ValueError:
            return

        if t in self.positions:
            pos = self.positions[t]
            if mod.sl is not None:
                pos.sl = mod.sl
            if mod.tp is not None:
                pos.tp = mod.tp

        if t in self.pending_orders:
            po = self.pending_orders[t]
            if mod.price is not None:
                po.price = mod.price
            if mod.sl is not None:
                po.sl = mod.sl
            if mod.tp is not None:
                po.tp = mod.tp

    def _handle_order_request(
        self,
        req: OrderRequest,
        bar_close: float,
        bar_time: int,
        slippage: float,
        target_symbol: str = "",
    ) -> None:
        sym = req.symbol or target_symbol or self.symbol
        if req.order_type in (OrderType.BUY, OrderType.SELL):
            # Market order executed immediately on bar close
            is_buy = req.order_type == OrderType.BUY or req.direction == 1
            direction = 1 if is_buy else -1
            exec_price = bar_close + slippage if is_buy else bar_close - slippage

            self._open_position(
                symbol=sym,
                direction=direction,
                volume=req.volume,
                open_price=exec_price,
                open_time=bar_time,
                sl=req.sl,
                tp=req.tp,
                magic=req.magic,
                comment=req.comment,
                slippage=slippage,
            )
        else:
            # Pending stop or limit order
            order_price = req.price if req.price > 0.0 else bar_close
            ticket = self._next_ticket()
            self.pending_orders[ticket] = PendingOrderState(
                ticket=ticket,
                symbol=sym,
                direction=req.direction,
                order_type=req.order_type,
                volume=req.volume,
                price=order_price,
                sl=req.sl,
                tp=req.tp,
                magic=req.magic,
                comment=req.comment,
                expires_at=int(req.atm_rules.get("expires_at", 0)),
            )

    def _open_position(
        self,
        symbol: str,
        direction: int,
        volume: float,
        open_price: float,
        open_time: int,
        sl: float,
        tp: float,
        magic: int,
        comment: str,
        slippage: float,
    ) -> PositionState:
        ticket = self._next_ticket()
        comm = self.settings.commission_per_order
        self.balance -= comm

        pos = PositionState(
            ticket=ticket,
            symbol=symbol,
            direction=direction,
            volume=volume,
            open_time=open_time,
            open_price=open_price,
            sl=sl,
            tp=tp,
            magic=magic,
            comment=comment,
            commission_paid=comm,
            slippage_incurred=slippage,
            mae_price=open_price,
            mfe_price=open_price,
        )
        self.positions[ticket] = pos
        return pos

    def _close_position(
        self,
        pos: PositionState,
        close_price: float,
        close_time: int,
        reason: str,
        slippage: float,
    ) -> TradeRecord:
        exit_comm = self.settings.commission_per_order
        total_comm = pos.commission_paid + exit_comm

        if pos.direction == 1:
            gross_pnl = (
                (close_price - pos.open_price) * pos.volume * self.settings.point_value
            )
            mae_points = max(0.0, pos.open_price - pos.mae_price)
            mfe_points = max(0.0, pos.mfe_price - pos.open_price)
            mae_pnl = -mae_points * pos.volume * self.settings.point_value
            mfe_pnl = mfe_points * pos.volume * self.settings.point_value
        else:
            gross_pnl = (
                (pos.open_price - close_price) * pos.volume * self.settings.point_value
            )
            mae_points = max(0.0, pos.mae_price - pos.open_price)
            mfe_points = max(0.0, pos.open_price - pos.mfe_price)
            mae_pnl = -mae_points * pos.volume * self.settings.point_value
            mfe_pnl = mfe_points * pos.volume * self.settings.point_value

        net_pnl = gross_pnl - total_comm
        # Pos was already charged commission_paid at open, so deduct only exit_comm from balance
        self.balance += gross_pnl - exit_comm

        trade = TradeRecord(
            ticket=pos.ticket,
            symbol=pos.symbol,
            direction=pos.direction,
            volume=pos.volume,
            open_time=pos.open_time,
            open_price=pos.open_price,
            close_time=close_time,
            close_price=close_price,
            sl=pos.sl,
            tp=pos.tp,
            commission=total_comm,
            slippage=pos.slippage_incurred + slippage,
            pnl=gross_pnl,
            net_pnl=net_pnl,
            close_reason=reason,
            magic=pos.magic,
            comment=pos.comment,
        )

        mae_mfe = MaeMfeRecord(
            ticket=pos.ticket,
            mae_price=pos.mae_price,
            mae_points=mae_points,
            mae_pnl=mae_pnl,
            mfe_price=pos.mfe_price,
            mfe_points=mfe_points,
            mfe_pnl=mfe_pnl,
        )

        self.positions.pop(pos.ticket, None)
        self.completed_trades.append(trade)
        self.mae_mfe_records.append(mae_mfe)
        return trade

    def record_equity(self, bar: MarketBar, symbol: str | None = None) -> None:
        """Mark open positions to market and record equity point at bar close."""
        close_price = float(bar.close)
        floating_pnl = 0.0
        target_symbol = symbol or self.symbol

        for pos in self.positions.values():
            if target_symbol and pos.symbol and pos.symbol != target_symbol:
                continue
            if pos.direction == 1:
                floating_pnl += (
                    (close_price - pos.open_price)
                    * pos.volume
                    * self.settings.point_value
                )
            else:
                floating_pnl += (
                    (pos.open_price - close_price)
                    * pos.volume
                    * self.settings.point_value
                )

        current_equity = self.balance + floating_pnl
        self.peak_equity = max(self.peak_equity, current_equity)

        drawdown = max(0.0, self.peak_equity - current_equity)
        drawdown_pct = (
            (drawdown / self.peak_equity * 100.0) if self.peak_equity > 0.0 else 0.0
        )

        self.equity_curve.append(
            EquityPoint(
                timestamp=int(bar.time),
                equity=current_equity,
                balance=self.balance,
                drawdown=drawdown,
                drawdown_pct=drawdown_pct,
            )
        )

    def close_all_open_positions(self, last_bar: MarketBar) -> None:
        """Force-close any positions remaining open at end of backtest."""
        close_price = float(last_bar.close)
        bar_time = int(last_bar.time)
        slippage = self.settings.slippage_points

        for pos in list(self.positions.values()):
            exec_price = (
                close_price - slippage if pos.direction == 1 else close_price + slippage
            )
            self._close_position(pos, exec_price, bar_time, "END_OF_DATA", slippage)

    def get_open_position_infos(self) -> tuple[PositionInfo, ...]:
        """Convert in-memory positions to domain PositionInfo snapshots."""
        infos: list[PositionInfo] = []
        for p in self.positions.values():
            pos_type = PositionType.BUY if p.direction == 1 else PositionType.SELL
            infos.append(
                PositionInfo(
                    ticket=p.ticket,
                    symbol=p.symbol,
                    position_type=pos_type,
                    volume=p.volume,
                    price_open=p.open_price,
                    price_current=p.open_price,
                    sl=p.sl,
                    tp=p.tp,
                    magic=p.magic,
                    comment=p.comment,
                    time=p.open_time,
                )
            )
        return tuple(infos)

    def get_pending_order_infos(self) -> tuple[OrderInfo, ...]:
        """Convert in-memory pending orders to domain OrderInfo snapshots."""
        infos: list[OrderInfo] = []
        for o in self.pending_orders.values():
            infos.append(
                OrderInfo(
                    ticket=o.ticket,
                    symbol=o.symbol,
                    order_type=o.order_type,
                    state=OrderState.PLACED,
                    volume_initial=o.volume,
                    volume_current=o.volume,
                    price_open=o.price,
                    sl=o.sl,
                    tp=o.tp,
                    magic=o.magic,
                    comment=o.comment,
                    time_expiration=o.expires_at,
                )
            )
        return tuple(infos)

    def compute_metrics(self) -> dict[str, float]:
        """Calculate summary performance statistics from completed trades and equity curve."""
        trades = self.completed_trades
        trades_count = len(trades)
        net_profit = sum(t.net_pnl for t in trades)
        gross_profit = sum(t.net_pnl for t in trades if t.net_pnl > 0.0)
        gross_loss = sum(t.net_pnl for t in trades if t.net_pnl < 0.0)
        winning_trades = sum(1 for t in trades if t.net_pnl > 0.0)
        losing_trades = sum(1 for t in trades if t.net_pnl < 0.0)

        if gross_loss < 0.0:
            profit_factor = gross_profit / abs(gross_loss)
        elif gross_profit > 0.0:
            profit_factor = gross_profit
        else:
            profit_factor = 0.0

        win_rate = (winning_trades / trades_count) if trades_count > 0 else 0.0
        max_dd = max((pt.drawdown for pt in self.equity_curve), default=0.0)
        max_dd_pct = max((pt.drawdown_pct for pt in self.equity_curve), default=0.0)

        sharpe_ratio = self._calculate_sharpe()

        return {
            "net_profit": net_profit,
            "gross_profit": gross_profit,
            "gross_loss": gross_loss,
            "profit_factor": profit_factor,
            "win_rate": win_rate,
            "trades_count": float(trades_count),
            "winning_trades": float(winning_trades),
            "losing_trades": float(losing_trades),
            "max_drawdown": max_dd,
            "max_drawdown_pct": max_dd_pct,
            "sharpe_ratio": sharpe_ratio,
            "final_balance": self.balance,
            "final_equity": self.balance,
        }

    def _calculate_sharpe(self) -> float:
        """Calculate annualized Sharpe ratio from daily equity curve or trade returns."""
        if len(self.equity_curve) < 2:
            return 0.0

        returns: list[float] = []
        for i in range(1, len(self.equity_curve)):
            prev = self.equity_curve[i - 1].equity
            curr = self.equity_curve[i].equity
            if prev > 0.0:
                returns.append((curr - prev) / prev)

        if not returns or len(returns) < 2:
            return 0.0

        mean_ret = sum(returns) / len(returns)
        variance = sum((r - mean_ret) ** 2 for r in returns) / (len(returns) - 1)
        std_ret = math.sqrt(variance)

        if std_ret < 1e-12:
            return 0.0

        # Standard daily root-factor approximation: sqrt(252)
        return (mean_ret / std_ret) * math.sqrt(252)


__all__ = ["PendingOrderState", "PositionState", "SimulationEngine"]
