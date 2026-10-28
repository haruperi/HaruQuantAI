"""Structural runtime boundary; blocks never import workspace or broker modules."""

# ruff: noqa: N802 -- matches the existing raw trading API
from __future__ import annotations

import asyncio
from datetime import datetime
from typing import Any, Protocol

from app.include.contracts import (
    AccountInfo,
    DealInfo,
    OrderInfo,
    PositionInfo,
    SymbolInfo,
    TradeCheckResult,
    TradeRequest,
    TradeResult,
)
from app.include.enums import OrderType


class PositionSource(Protocol):
    """Raw position snapshots."""

    async def PositionsGet(self, *args: Any, **kwargs: Any) -> list[PositionInfo]:
        """Fetch current positions."""


class OrderSource(Protocol):
    """Raw working order snapshots."""

    async def OrdersGet(self, *args: Any, **kwargs: Any) -> list[OrderInfo]:
        """Fetch working orders."""


class AccountSource(Protocol):
    """Account snapshots and broker profit calculations."""

    async def AccountInfo(self, *args: Any) -> AccountInfo:
        """Fetch account state."""

    async def OrderProfitCheck(self, *args: Any) -> Any:
        """Value a concrete position at a supplied price."""


class SymbolSource(Protocol):
    """Instrument execution specifications."""

    async def SymbolInfo(self, *args: Any) -> SymbolInfo:
        """Fetch an instrument specification."""


class DealSource(Protocol):
    """Raw executions; unsupported history must raise."""

    async def HistoryDealsGet(self, *args: Any, **kwargs: Any) -> list[DealInfo]:
        """Fetch execution history."""


class OrderExecution(Protocol):
    """Execution primitives, with no best/worst or scope-selection policy."""

    @property
    def operation_lock(self) -> asyncio.Lock:
        """Serialize strategy workflows sharing this executor."""

    async def prepare_entry_request(
        self,
        symbol: str,
        direction: int,
        volume: float,
        buy_type: OrderType,
        *,
        price: float,
        sl: float,
        tp: float,
        magic: int | None,
        comment: str,
        expiration: datetime | None,
    ) -> TradeRequest:
        """Validate and normalize one concrete entry request."""

    async def OrderCheck(
        self,
        request: TradeRequest | dict[str, Any],
        result: TradeCheckResult | None = None,
    ) -> TradeCheckResult:
        """Check one concrete request without sending it."""

    async def send_checked(self, request: TradeRequest) -> TradeResult:
        """Check and submit a concrete request."""

    async def close(
        self, position: PositionInfo, volume: float | None = None
    ) -> TradeResult:
        """Close one specified position snapshot."""

    async def cancel(self, order: OrderInfo) -> TradeResult:
        """Cancel one specified working order."""

    async def modify_protection(
        self,
        item: PositionInfo | OrderInfo,
        *,
        sl: float | None = None,
        tp: float | None = None,
    ) -> TradeResult:
        """Modify one specified position or pending order."""


class TradingRuntime(Protocol):
    """Injected raw data and execution capabilities shared by live and simulation."""

    @property
    def position(self) -> PositionSource:
        """Position access."""

    @property
    def order(self) -> OrderSource:
        """Pending-order access."""

    @property
    def account(self) -> AccountSource:
        """Account access."""

    @property
    def symbol(self) -> SymbolSource:
        """Instrument access."""

    @property
    def deal(self) -> DealSource:
        """History access."""

    @property
    def trade(self) -> OrderExecution:
        """Concrete execution access."""
