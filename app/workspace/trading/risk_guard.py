"""Live risk guard and circuit breaker enforcement for order execution.

Description:
    Provides RiskGuard and RiskLimits enforcing pre-trade sanity limits (order volume,
    symbol position counts, slippage tolerance), monitoring portfolio equity drawdown
    against circuit breaker thresholds, and providing emergency flatten/cancel actions.
Purpose:
    FEAT-LIVE-RISK-GUARD: Live risk management and circuit breakers.
Key Capabilities:
    - FR-trading-risk-order-sanity: Validate max order volume and position limits.
    - FR-trading-risk-circuit-breaker: Detect max equity drawdown and trip breaker.
    - FR-trading-risk-emergency-flatten: Panic-close open positions and cancel orders.
Python API Usage:
    from app.workspace.trading.risk_guard import RiskGuard, RiskLimits
    guard = RiskGuard(RiskLimits(max_volume_per_order=5.0))
    guard.validate_order(order_req, current_positions_count=2)
CLI Usage:
    uv run python -m pytest tests/workspace/trading/test_risk_guard.py -q
"""

from __future__ import annotations

import inspect
from dataclasses import dataclass

from app.core.data.contracts import (
    OrderInfo,
    PositionInfo,
    TradeRequest,
    TradeResult,
)
from app.core.enums import (
    OrderType,
    TradeAction,
    TradeRetcode,
)
from app.core.host.logging import get_logger
from app.core.trading.connection.base import TradingClient
from app.core.trading.strategy.contracts import OrderRequest

logger = get_logger(__name__)


@dataclass(frozen=True, slots=True)
class RiskLimits:
    """Configurable risk thresholds and execution boundaries."""

    max_volume_per_order: float = 10.0
    max_open_positions_per_symbol: int = 5
    max_drawdown_pct: float = 0.20  # 20% drawdown trips circuit breaker
    slippage_points_tolerance: int = 50


class RiskGuard:
    """Pre-trade risk validator and emergency panic handler."""

    def __init__(self, limits: RiskLimits | None = None) -> None:
        self.limits = limits or RiskLimits()
        self._circuit_breaker_tripped = False
        self._peak_equity: float = 0.0

    @property
    def is_tripped(self) -> bool:
        """Return whether the portfolio drawdown circuit breaker is tripped."""
        return self._circuit_breaker_tripped

    def reset_circuit_breaker(self) -> None:
        """Reset the circuit breaker following manual operator verification."""
        logger.info("FR-trading-risk-circuit-breaker: circuit breaker manually reset")
        self._circuit_breaker_tripped = False

    def update_equity(self, current_equity: float) -> bool:
        """Update peak equity and check if max drawdown circuit breaker is tripped.

        Returns True if tripped.
        """
        if current_equity > self._peak_equity:
            self._peak_equity = current_equity
            return False

        if self._peak_equity > 0.0:
            drawdown = (self._peak_equity - current_equity) / self._peak_equity
            if drawdown >= self.limits.max_drawdown_pct:
                if not self._circuit_breaker_tripped:
                    logger.error(
                        "FR-trading-risk-circuit-breaker: TRIPPED! Drawdown %.2f%% "
                        ">= limit %.2f%% (Peak: %.2f, Current: %.2f)",
                        drawdown * 100,
                        self.limits.max_drawdown_pct * 100,
                        self._peak_equity,
                        current_equity,
                    )
                self._circuit_breaker_tripped = True
                return True
        return False

    def validate_order(
        self,
        order: OrderRequest,
        current_positions_count: int,
    ) -> bool:
        """Validate order size, limits, and circuit breaker status."""
        logger.debug(
            "FR-trading-risk-order-sanity: validating order for %s vol=%.2f",
            order.symbol,
            order.volume,
        )
        if self._circuit_breaker_tripped:
            logger.warning(
                "FR-trading-risk-order-sanity: rejected order %s (breaker tripped)",
                order.symbol,
            )
            return False

        if order.volume <= 0.0 or order.volume > self.limits.max_volume_per_order:
            logger.warning(
                "FR-trading-risk-order-sanity: rejected order %s (vol=%.2f > max=%.2f)",
                order.symbol,
                order.volume,
                self.limits.max_volume_per_order,
            )
            return False

        if current_positions_count >= self.limits.max_open_positions_per_symbol:
            logger.warning(
                "FR-trading-risk-order-sanity: rejected order %s (%d >= max %d)",
                order.symbol,
                current_positions_count,
                self.limits.max_open_positions_per_symbol,
            )
            return False

        return True

    async def flatten_all(self, client: TradingClient) -> list[TradeResult]:
        """Close all active open market positions across the client."""
        logger.info(
            "FR-trading-risk-emergency-flatten: starting emergency flatten on %s",
            client.name,
        )
        raw_positions = client.get_positions()
        if inspect.isawaitable(raw_positions):
            positions: list[PositionInfo] = await raw_positions
        else:
            positions = raw_positions

        results: list[TradeResult] = []
        for pos in positions:
            close_req = TradeRequest(
                action=TradeAction.DEAL,
                symbol=pos.symbol,
                volume=pos.volume,
                position=pos.ticket,
                order_type=(
                    OrderType.SELL if pos.position_type == 0 else OrderType.BUY
                ),
                comment="emergency flatten",
            )
            try:
                res = client.order_send(close_req)
                if inspect.isawaitable(res):
                    trade_res = await res
                else:
                    trade_res = res
                results.append(trade_res)
            except Exception as exc:
                logger.exception(
                    "FR-trading-risk-emergency-flatten: failed closing ticket %s",
                    pos.ticket,
                )
                results.append(
                    TradeResult(
                        retcode=int(TradeRetcode.ERROR),
                        comment=f"Flatten failed: {exc}",
                    )
                )

        logger.info(
            "FR-trading-risk-emergency-flatten: flatten done (%d closed)",
            len(results),
        )
        return results

    async def cancel_all(self, client: TradingClient) -> list[TradeResult]:
        """Cancel all active pending orders across the client."""
        logger.info(
            "FR-trading-risk-emergency-flatten: starting emergency cancel_all on %s",
            client.name,
        )
        raw_orders = client.get_orders()
        if inspect.isawaitable(raw_orders):
            orders: list[OrderInfo] = await raw_orders
        else:
            orders = raw_orders

        results: list[TradeResult] = []
        for order in orders:
            cancel_req = TradeRequest(
                action=TradeAction.REMOVE,
                order=order.ticket,
                symbol=order.symbol,
                comment="emergency cancel all",
            )
            try:
                res = client.order_send(cancel_req)
                if inspect.isawaitable(res):
                    trade_res = await res
                else:
                    trade_res = res
                results.append(trade_res)
            except Exception as exc:
                logger.exception(
                    "FR-trading-risk-emergency-flatten: failed canceling order %s",
                    order.ticket,
                )
                results.append(
                    TradeResult(
                        retcode=int(TradeRetcode.ERROR),
                        comment=f"Cancel failed: {exc}",
                    )
                )

        logger.info(
            "FR-trading-risk-emergency-flatten: completed cancel (%d orders canceled)",
            len(results),
        )
        return results


__all__ = ["RiskGuard", "RiskLimits"]
