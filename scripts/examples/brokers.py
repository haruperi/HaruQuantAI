"""Nineteen named async trading examples with a switchable broker.

Description:
    Adapt the legacy seventeen-function trading walkthrough to the shared Trading
    facade, then add historical bars and ticks. Backend-specific setup stays in
    create_backend; ExampleContext owns only this run's trade identities and state.
    Shutdown runs last and on errors. Explicit live writes can leave open resources
    when outcomes are uncertain; never retry or close an unknown position.

Purpose:
    FEAT-TRADING-USAGE: Demonstrate the same API on MT5 and seeded simulation.

Key Capabilities:
    - FR-TRADING-USAGE-EXAMPLES: Execute nineteen named functions and field previews.
      Associated: `example_01_connect()` through `example_19_tick_data()`
      Logging: INFO number/title/status and labelled values, no credentials,
        identity/path/comment/request dumps or arbitrary exception messages.
    - FR-TRADING-USAGE-LIFECYCLE: Select providers and close exactly once.
      Associated: `create_backend()`, `run_examples()`, `main()`
      Logging: DEBUG/INFO setup, ERROR static explanation or safe exception type.

Python API Usage:
    backend = create_backend("simulator")
    results = await run_examples(backend, allow_writes=True)
    # Individual functions also accept an explicit ExampleContext(Trading(backend)).

CLI Usage:
    uv run python -m scripts.examples.brokers
    Select BROKER; MT5 requires MT5_BRIDGE_TOKEN and a compiled, attached bridge EA.
"""

from __future__ import annotations

import asyncio
import math
import os
import sys
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from pathlib import Path
from secrets import randbits
from tempfile import TemporaryDirectory
from typing import Any, Literal

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))


from app.services.brokers.contracts import (
    BridgeError,
    MarginMode,
    MarketBar,
    MarketTick,
    OrderTime,
    OrderType,
    ReceiptStatus,
    SymbolSpec,
    Timeframe,
    TradingBackend,
)
from app.services.brokers.metatrader import MT5Backend
from app.services.brokers.simulator import SimulationBackend
from app.services.trading import Trading
from app.services.utils import format_timestamp

BROKER: Literal["simulator", "mt5"] = "mt5"
ALLOW_LIVE_TRADING = True
SYMBOL = "EURUSD"
VOLUME = 0.01  # Partial-close volume; the example buy opens twice this amount.
CONNECT_TIMEOUT = 60.0
TIMEFRAME = Timeframe.PERIOD_M1
DATE_TO = datetime.now(UTC).replace(second=0, microsecond=0)
DATE_FROM = DATE_TO - timedelta(minutes=5)
TICK_DATE_FROM = DATE_TO - timedelta(seconds=10)
DATA_LIMIT = 1000
PREVIEW_LIMIT = 5


class ExampleError(RuntimeError):
    """A static explanation from an example, safe to display without a traceback."""


@dataclass(frozen=True)
class ExampleResult:
    """One function outcome for the runner's completion summary."""

    number: int
    title: str
    status: Literal["passed", "skipped"]
    summary: str


@dataclass
class ExampleContext:
    """Share the connection and this run's owned tickets between examples."""

    trading: Trading
    allow_writes: bool = False
    results: list[ExampleResult] = field(default_factory=list)
    magic: int = field(default_factory=lambda: randbits(48))
    position_ticket: int = 0
    position_id: int = 0
    pending_ticket: int = 0
    pending_price: float = 0.0
    closed: bool = False


def create_backend(name: str = BROKER) -> TradingBackend:
    """Select and seed the provider; example bodies use only Trading."""
    print("FR-TRADING-USAGE-LIFECYCLE: selecting backend")
    if name == "simulator":
        backend = SimulationBackend()
        backend.add_symbol(SymbolSpec(name=SYMBOL))
        backend.feed_tick(SYMBOL, bid=1.1, ask=1.1002, time=DATE_TO)
        base = int(DATE_FROM.timestamp())
        backend.seed_bar_history(
            SYMBOL,
            TIMEFRAME,
            [
                MarketBar(base + i * 60, 1.1, 1.1005, 1.0995, 1.1002, 10, 20, 0)
                for i in range(3)
            ],
        )
        stamp = int(TICK_DATE_FROM.timestamp() * 1000)
        backend.seed_tick_history(
            SYMBOL,
            [
                MarketTick(stamp + offset, 1.1, 1.1002, 0.0, 0, 6, 0.0)
                for offset in (0, 123, 456)
            ],
        )
        return backend
    if name == "mt5":
        token = os.environ.get("MT5_BRIDGE_TOKEN")
        if not token:
            raise ValueError("MT5_BRIDGE_TOKEN is required for mt5")
        return MT5Backend(auth_token=token)
    raise ValueError("BROKER must be simulator or mt5")


def _report(
    ctx: ExampleContext, number: int, title: str, value: Any, *, skipped: bool = False
) -> None:
    summary = str(value)
    ctx.results.append(
        ExampleResult(number, title, "skipped" if skipped else "passed", summary)
    )
    print(
        f"Example {number:02d}/19 - {title} - {'skipped' if skipped else 'passed'}: {summary}"
    )


def _header(title: str) -> None:
    """Print a header for the example output."""
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)


async def example_01_connect(ctx: ExampleContext) -> None:
    """Verify backend readiness, then show an observed terminal probe and receipt.

    MT5 readiness validates the EA hello/token; the resolved read proves a return
    path through the bridge. Simulation supplies local readiness/probe evidence.
    Terminal connectivity measures its broker connection at the probe's instant.
    """
    _header("Connect to Broker")
    await ctx.trading.start()
    print(f"Waiting for backend readiness; timeout={CONNECT_TIMEOUT} seconds")
    await ctx.trading.wait_connected(timeout=CONNECT_TIMEOUT)
    connected = await ctx.trading.terminal.IsConnected()
    command_id = ctx.trading.terminal.last_command_id
    receipt = ctx.trading.receipt(command_id) if command_id is not None else None
    if (
        type(connected) is not bool
        or receipt is None
        or receipt.status != ReceiptStatus.RESOLVED
        or receipt.command_id != command_id
        or receipt.object_id != ctx.trading.terminal.object_id
        or receipt.class_name != "TerminalInfo"
        or receipt.method_name != "IsConnected"
        or receipt.value is not connected
        or receipt.error is not None
        or receipt.sent_at is None
        or receipt.acknowledged_at is None
        or receipt.resolved_at is None
        or not all(
            isinstance(stamp, (int, float))
            and not isinstance(stamp, bool)
            and math.isfinite(stamp)
            for stamp in (receipt.sent_at, receipt.acknowledged_at, receipt.resolved_at)
        )
    ):
        ctx.trading.disarm()
        raise ExampleError(
            "Connection probe has missing or mismatched response evidence"
        )
    if not connected:
        ctx.trading.disarm()
        raise ExampleError("Terminal responded but is disconnected from its broker")
    print(f"Terminal connected : {connected}")
    print(f"Probe : {receipt.class_name}.{receipt.method_name}")
    print(f"Command ID : {receipt.command_id}")
    print(f"Receipt status : {receipt.status.value}")
    print(f"Sent at : {format_timestamp(receipt.sent_at)}")
    print(f"Acknowledged at : {format_timestamp(receipt.acknowledged_at)}")
    print(f"Resolved at : {format_timestamp(receipt.resolved_at)}")


async def example_02_terminal(ctx: ExampleContext) -> None:
    """Demonstrate printing terminal information using TerminalInfo."""
    _header("Terminal Information")
    terminal = ctx.trading.terminal
    print(f"Name: {await terminal.Name()}")
    print(f"Company: {await terminal.Company()}")
    print(f"Build: {await terminal.Build()}")
    print(f"Language: {await terminal.Language()}")
    print(f"Connected: {await terminal.IsConnected()}")
    print(f"Trade allowed: {await terminal.IsTradeAllowed()}")
    print(f"DLLs allowed: {await terminal.IsDLLsAllowed()}")
    print(f"Trade API disabled: {await terminal.TradeAPIDisabled()}")
    print(f"Notifications enabled: {await terminal.NotificationsEnabled()}")
    print(f"MQID: {await terminal.MQID()}")
    print(f"Ping last: {await terminal.PingLast()}")
    print(f"Community balance: {await terminal.CommunityBalance()}")
    print(f"Retransmission: {await terminal.Retransmission()}")
    print(f"Path: {await terminal.Path()}")
    print(f"Data path: {await terminal.DataPath()}")
    print(f"Common data path: {await terminal.CommonDataPath()}")


async def example_03_account(ctx: ExampleContext) -> None:
    """Demonstrate printing account information using AccountInfo."""
    _header("Account Information")
    account = ctx.trading.account
    print(f"Currency: {await account.Currency()}")
    print(f"Leverage: {await account.Leverage()}")
    print(f"Trade mode: {await account.TradeModeDescription()}")
    print(f"Margin mode: {await account.MarginModeDescription()}")
    print(f"Trade allowed: {await account.TradeAllowed()}")
    print(f"Expert allowed: {await account.TradeExpert()}")
    print(f"Balance: {await account.Balance()}")
    print(f"Credit: {await account.Credit()}")
    print(f"Profit: {await account.Profit()}")
    print(f"Equity: {await account.Equity()}")
    print(f"Margin: {await account.Margin()}")
    print(f"Free margin: {await account.FreeMargin()}")
    print(f"Margin level: {await account.MarginLevel()}")


async def example_04_symbol(ctx: ExampleContext) -> None:
    """Demonstrate printing symbol specification information using SymbolInfo."""
    _header("Symbol Information")
    symbol = ctx.trading.symbol
    if (
        not await symbol.Name(SYMBOL)
        or not await symbol.Select(True)
        or not await symbol.RefreshRates()
    ):
        ctx.trading.disarm()
        raise ExampleError("Configured symbol or quote is unavailable")
    print(f"Name: {await symbol.Name()}")
    print(f"Digits: {await symbol.Digits()}")
    print(f"Point: {await symbol.Point()}")
    print(f"Tick size: {await symbol.TickSize()}")
    print(f"Bid: {await symbol.Bid()}")
    print(f"Ask: {await symbol.Ask()}")
    print(f"Last: {await symbol.Last()}")
    print(f"Spread: {await symbol.Spread()}")
    print(f"Trade mode: {await symbol.TradeModeDescription()}")
    print(f"Contract size: {await symbol.ContractSize()}")
    print(f"Min lot: {await symbol.LotsMin()}")
    print(f"Max lot: {await symbol.LotsMax()}")
    print(f"Lot step: {await symbol.LotsStep()}")
    print(f"Swap mode: {await symbol.SwapMode()}")
    print(f"Swap long: {await symbol.SwapLong()}")
    print(f"Swap short: {await symbol.SwapShort()}")


async def example_05_position(ctx: ExampleContext) -> None:
    """Demonstrate printing an open-position preview using PositionInfo."""
    _header("Position Information")
    position = ctx.trading.position
    found = False
    for index in range(PREVIEW_LIMIT):
        if not await position.SelectByIndex(index):
            break
        found = True
        print(f"Position [{index}]:")
        print(f"  Symbol: {await position.Symbol()}")
        print(f"  Type: {await position.TypeDescription()}")
        print(f"  Volume: {await position.Volume()}")
        print(f"  Open price: {await position.PriceOpen()}")
        print(f"  Current price: {await position.PriceCurrent()}")
        print(f"  SL: {await position.StopLoss()}")
        print(f"  TP: {await position.TakeProfit()}")
        print(f"  Profit: {await position.Profit()}")
        print(f"  Swap: {await position.Swap()}")
    if not found:
        print("No open positions")


async def example_06_order(ctx: ExampleContext) -> None:
    """Demonstrate printing a pending-order preview using OrderInfo."""
    _header("Order Information")
    order = ctx.trading.order
    found = False
    for index in range(PREVIEW_LIMIT):
        if not await order.SelectByIndex(index):
            break
        found = True
        print(f"Order [{index}]:")
        print(f"  Symbol: {await order.Symbol()}")
        print(f"  Type: {await order.TypeDescription()}")
        print(f"  Volume: {await order.VolumeCurrent()}")
        print(f"  Price: {await order.PriceOpen()}")
        print(f"  SL: {await order.StopLoss()}")
        print(f"  TP: {await order.TakeProfit()}")
    if not found:
        print("No pending orders")


async def example_07_history_order(ctx: ExampleContext) -> None:
    """Demonstrate printing historical orders using HistoryOrderInfo."""
    _header("History Order Information")
    order = ctx.trading.history_order
    found = False
    for index in range(PREVIEW_LIMIT):
        if not await order.SelectByIndex(index):
            break
        found = True
        print(f"History Order [{index}]:")
        print(f"  Symbol: {await order.Symbol()}")
        print(f"  Type: {await order.TypeDescription()}")
        print(f"  State: {await order.StateDescription()}")
        print(f"  Volume: {await order.VolumeInitial()}")
        print(f"  Price: {await order.PriceOpen()}")
        print(f"  Done time: {format_timestamp(await order.TimeDone())}")
    if not found:
        print("No history orders")


async def example_08_history_deal(ctx: ExampleContext) -> None:
    """Demonstrate printing historical deals using DealInfo."""
    _header("Deal Information")
    deal = ctx.trading.deal
    found = False
    for index in range(PREVIEW_LIMIT):
        if not await deal.SelectByIndex(index):
            break
        found = True
        print(f"Deal [{index}]:")
        print(f"  Symbol: {await deal.Symbol()}")
        print(f"  Type: {await deal.TypeDescription()}")
        print(f"  Entry: {await deal.EntryDescription()}")
        print(f"  Volume: {await deal.Volume()}")
        print(f"  Price: {await deal.Price()}")
        print(f"  Profit: {await deal.Profit()}")
        print(f"  Commission: {await deal.Commission()}")
        print(f"  Swap: {await deal.Swap()}")
    if not found:
        print("No history deals")


async def example_09_open_position(ctx: ExampleContext) -> None:
    """Demonstrate opening a buy position using Trade."""
    _header("Open Position")
    if not ctx.allow_writes:
        print("Live writes disabled; skipping open position")
        return
    trading = ctx.trading
    if ctx.position_ticket or int(await trading.account.MarginMode()) != int(
        MarginMode.RETAIL_HEDGING
    ):
        ctx.trading.disarm()
        raise ExampleError("A new hedging position is required for this example")
    minimum = float(await trading.symbol.LotsMin())
    maximum = float(await trading.symbol.LotsMax())
    step = float(await trading.symbol.LotsStep())
    if (
        not math.isfinite(VOLUME)
        or step <= 0
        or VOLUME < minimum
        or 2 * VOLUME > maximum
        or not math.isclose(VOLUME / step, round(VOLUME / step))
    ):
        ctx.trading.disarm()
        raise ExampleError(
            "VOLUME must allow two valid lots for the partial-close example"
        )
    await trading.trade.SetExpertMagicNumber(ctx.magic)
    await trading.trade.SetDeviationInPoints(20)
    if not await trading.trade.SetTypeFillingBySymbol(SYMBOL):
        ctx.trading.disarm()
        raise ExampleError("Symbol filling policy is unavailable")
    trading.arm()
    sent = await trading.trade.Buy(2 * VOLUME, SYMBOL)
    retcode = int(await trading.trade.ResultRetcode())
    print(f"Buy dispatch: {sent}; retcode={retcode}")
    if not sent or retcode != 10009:
        ctx.trading.disarm()
        raise ExampleError("Buy not confirmed; check trade outcome before rerunning")
    result = await trading.trade.Result()
    deal = int(result.get("deal", 0))
    if not deal or not await trading.deal.Ticket(deal):
        ctx.trading.disarm()
        raise ExampleError("Buy deal history could not be selected")
    ctx.position_id = int(await trading.deal.PositionId())
    if not ctx.position_id:
        ctx.trading.disarm()
        raise ExampleError("Buy deal position identifier is unavailable")
    for ticket in (int(result.get("order", 0)), ctx.position_id):
        if ticket and await trading.position.SelectByTicket(ticket):
            if (
                int(await trading.position.Identifier()) == ctx.position_id
                and int(await trading.position.Magic()) == ctx.magic
                and await trading.position.Symbol() == SYMBOL
            ):
                ctx.position_ticket = ticket
                break
    if not ctx.position_ticket:
        ctx.trading.disarm()
        raise ExampleError("Buy position ownership could not be confirmed")
    print(f"Opened owned position with volume: {2 * VOLUME}; retcode={retcode}")


async def example_10_calc_profit_margin(ctx: ExampleContext) -> None:
    """Demonstrate calculating expected profit and required margin using AccountInfo."""
    _header("Calculate Profit and Margin")
    ask = float(await ctx.trading.symbol.Ask())
    point = float(await ctx.trading.symbol.Point())
    account = ctx.trading.account
    print(
        f"Margin: {await account.MarginCheck(SYMBOL, OrderType.BUY, 2 * VOLUME, ask)}"
    )
    print(
        "Profit: "
        f"{await account.OrderProfitCheck(SYMBOL, OrderType.BUY, 2 * VOLUME, ask, ask + 100 * point)}"
    )
    print(
        f"Free margin check: {await account.FreeMarginCheck(SYMBOL, OrderType.BUY, 2 * VOLUME, ask)}"
    )


async def example_11_modify_position(ctx: ExampleContext) -> None:
    """Demonstrate modifying the owned position's SL/TP using Trade."""
    _header("Modify Position")
    if not ctx.allow_writes:
        print("Live writes disabled; skipping modify position")
        return
    pos, symbol, trade = ctx.trading.position, ctx.trading.symbol, ctx.trading.trade
    if (
        not ctx.position_ticket
        or not await pos.SelectByTicket(ctx.position_ticket)
        or int(await pos.Identifier()) != ctx.position_id
        or int(await pos.Magic()) != ctx.magic
        or await pos.Symbol() != SYMBOL
    ):
        ctx.trading.disarm()
        raise ExampleError("Position ownership must be confirmed before modification")
    await symbol.RefreshRates()
    distance = max(
        1000, int(await symbol.StopsLevel()) + 20, int(await symbol.FreezeLevel()) + 20
    ) * float(await symbol.Point())
    bid, digits = float(await symbol.Bid()), int(await symbol.Digits())
    sl, tp = round(bid - distance, digits), round(bid + distance, digits)
    sent = await trade.PositionModify(ctx.position_ticket, sl, tp)
    retcode = int(await trade.ResultRetcode())
    print(f"Position modify dispatch: {sent}; retcode={retcode}")
    if (
        not sent
        or retcode != 10009
        or not await pos.SelectByTicket(ctx.position_ticket)
        or not math.isclose(float(await pos.StopLoss()), sl)
        or not math.isclose(float(await pos.TakeProfit()), tp)
    ):
        ctx.trading.disarm()
        raise ExampleError("Position modification not confirmed; inspect trade outcome")
    print(f"Modified owned position SL={sl}, TP={tp}")


async def example_12_close_partial_position(ctx: ExampleContext) -> None:
    """Demonstrate partially closing the owned position using Trade."""
    _header("Close Partial Position")
    if not ctx.allow_writes:
        print("Live writes disabled; skipping partial close")
        return
    pos, trade = ctx.trading.position, ctx.trading.trade
    if (
        not ctx.position_ticket
        or not await pos.SelectByTicket(ctx.position_ticket)
        or int(await pos.Identifier()) != ctx.position_id
        or int(await pos.Magic()) != ctx.magic
        or await pos.Symbol() != SYMBOL
    ):
        ctx.trading.disarm()
        raise ExampleError("Position ownership must be confirmed before partial close")
    before = float(await pos.Volume())
    sent = await trade.PositionClosePartial(ctx.position_ticket, VOLUME)
    retcode = int(await trade.ResultRetcode())
    print(f"Partial close dispatch: {sent}; retcode={retcode}")
    if (
        not sent
        or retcode != 10009
        or not await pos.SelectByTicket(ctx.position_ticket)
    ):
        ctx.trading.disarm()
        raise ExampleError("Partial close not confirmed; inspect trade outcome")
    remaining = float(await pos.Volume())
    if remaining <= 0 or not math.isclose(remaining, before - VOLUME):
        ctx.trading.disarm()
        raise ExampleError("Partial-close remaining volume did not match")
    print(f"Partial close successful; remaining volume: {remaining}")


async def example_13_close_position(ctx: ExampleContext) -> None:
    """Demonstrate fully closing the remaining owned position using Trade."""
    _header("Close Position")
    if not ctx.allow_writes:
        print("Live writes disabled; skipping close position")
        return
    pos, trade = ctx.trading.position, ctx.trading.trade
    if (
        not ctx.position_ticket
        or not await pos.SelectByTicket(ctx.position_ticket)
        or int(await pos.Identifier()) != ctx.position_id
        or int(await pos.Magic()) != ctx.magic
        or await pos.Symbol() != SYMBOL
    ):
        ctx.trading.disarm()
        raise ExampleError("Position ownership must be confirmed before closing")
    sent = await trade.PositionClose(ctx.position_ticket)
    retcode = int(await trade.ResultRetcode())
    print(f"Position close dispatch: {sent}; retcode={retcode}")
    if not sent or retcode != 10009 or await pos.SelectByTicket(ctx.position_ticket):
        ctx.trading.disarm()
        raise ExampleError("Position close not confirmed; inspect trade outcome")
    ctx.position_ticket = 0
    print("Closed remaining owned position")


async def example_14_pending_orders(ctx: ExampleContext) -> None:
    """Demonstrate placing a BuyLimit pending order using Trade."""
    _header("Place Pending Order")
    if not ctx.allow_writes:
        print("Live writes disabled; skipping place pending order")
        return
    if ctx.pending_ticket:
        ctx.trading.disarm()
        raise ExampleError("This example already owns a pending order")
    symbol, trade, order = ctx.trading.symbol, ctx.trading.trade, ctx.trading.order
    await symbol.RefreshRates()
    distance = max(
        1000, int(await symbol.StopsLevel()) + 20, int(await symbol.FreezeLevel()) + 20
    ) * float(await symbol.Point())
    ctx.pending_price = round(
        float(await symbol.Bid()) - distance, int(await symbol.Digits())
    )
    sent = await trade.BuyLimit(VOLUME, ctx.pending_price, SYMBOL)
    retcode = int(await trade.ResultRetcode())
    print(f"BuyLimit dispatch: {sent}; retcode={retcode}")
    if not sent or retcode not in (10008, 10009):
        ctx.trading.disarm()
        raise ExampleError("Pending order not confirmed; inspect trade outcome")
    ctx.pending_ticket = int(await trade.ResultOrder())
    if (
        not ctx.pending_ticket
        or not await order.Select(ctx.pending_ticket)
        or int(await order.Magic()) != ctx.magic
        or await order.Symbol() != SYMBOL
    ):
        ctx.trading.disarm()
        raise ExampleError("Pending order ownership could not be confirmed")
    print(f"Placed owned pending order at price: {ctx.pending_price}; volume: {VOLUME}")


async def example_15_modify_pending_orders(ctx: ExampleContext) -> None:
    """Demonstrate modifying the owned pending order using Trade."""
    _header("Modify Pending Order")
    if not ctx.allow_writes:
        print("Live writes disabled; skipping modify pending order")
        return
    order, symbol, trade = ctx.trading.order, ctx.trading.symbol, ctx.trading.trade
    if (
        not ctx.pending_ticket
        or not await order.Select(ctx.pending_ticket)
        or int(await order.Magic()) != ctx.magic
        or await order.Symbol() != SYMBOL
    ):
        ctx.trading.disarm()
        raise ExampleError("Order ownership must be confirmed before modification")
    await symbol.RefreshRates()
    distance = max(
        1000, int(await symbol.StopsLevel()) + 20, int(await symbol.FreezeLevel()) + 20
    ) * float(await symbol.Point())
    price = round(ctx.pending_price - distance, int(await symbol.Digits()))
    sent = await trade.OrderModify(
        ctx.pending_ticket, price, 0.0, 0.0, OrderTime.GTC, 0
    )
    retcode = int(await trade.ResultRetcode())
    print(f"Order modify dispatch: {sent}; retcode={retcode}")
    if (
        not sent
        or retcode != 10009
        or not await order.Select(ctx.pending_ticket)
        or not math.isclose(float(await order.PriceOpen()), price)
    ):
        ctx.trading.disarm()
        raise ExampleError("Order modification not confirmed; inspect trade outcome")
    ctx.pending_price = price
    print(f"Modified owned pending order price: {price}")


async def example_16_delete_pending_orders(ctx: ExampleContext) -> None:
    """Demonstrate cancelling the owned pending order using Trade."""
    _header("Cancel Pending Order")
    if not ctx.allow_writes:
        print("Live writes disabled; skipping delete pending order")
        return
    order, trade = ctx.trading.order, ctx.trading.trade
    if (
        not ctx.pending_ticket
        or not await order.Select(ctx.pending_ticket)
        or int(await order.Magic()) != ctx.magic
        or await order.Symbol() != SYMBOL
    ):
        ctx.trading.disarm()
        raise ExampleError("Order ownership must be confirmed before cancellation")
    sent = await trade.OrderDelete(ctx.pending_ticket)
    retcode = int(await trade.ResultRetcode())
    print(f"Order delete dispatch: {sent}; retcode={retcode}")
    if not sent or retcode != 10009 or await order.Select(ctx.pending_ticket):
        ctx.trading.disarm()
        raise ExampleError("Order cancellation not confirmed; inspect trade outcome")
    ctx.pending_ticket = 0
    print("Deleted owned pending order")


async def example_17_shutdown(ctx: ExampleContext) -> None:
    """Demonstrate shutting down the broker connection."""
    _header("Shutdown")
    if not ctx.closed:
        ctx.closed = True
        ctx.trading.disarm()
        await ctx.trading.close()
        print("Broker connection closed successfully")


async def example_18_historical_bars(ctx: ExampleContext) -> None:
    """Demonstrate bars by date range, forward date/count, index/count and defaults."""
    _header("Historical Bars")
    trading = ctx.trading
    bars = await trading.get_historical_bars(
        SYMBOL, TIMEFRAME, DATE_FROM, DATE_TO, limit=DATA_LIMIT
    )
    from_date = await trading.get_historical_bars(
        SYMBOL, TIMEFRAME, date_from=DATE_FROM, count=3
    )
    from_index = await trading.get_historical_bars(
        SYMBOL, TIMEFRAME, start_pos=1, count=2
    )
    latest = await trading.get_historical_bars(SYMBOL, TIMEFRAME, count=3)
    until_now = await trading.get_historical_bars(
        SYMBOL, TIMEFRAME, date_from=DATE_FROM
    )
    through_current = await trading.get_historical_bars(SYMBOL, TIMEFRAME, start_pos=2)
    print(f"Range count: {len(bars)}")
    print(f"Range sample: {bars[:PREVIEW_LIMIT]}")
    print(f"Date/count: {from_date[:PREVIEW_LIMIT]}")
    print(f"Index/count: {from_index[:PREVIEW_LIMIT]}")
    print(f"Latest: {latest[:PREVIEW_LIMIT]}")
    print(f"Date until now count: {len(until_now)}")
    print(f"Index through current: {through_current[:PREVIEW_LIMIT]}")


async def example_19_tick_data(ctx: ExampleContext) -> None:
    """Demonstrate ticks by date range, forward date/count and latest count."""
    _header("Historical Ticks")
    trading = ctx.trading
    ticks = await trading.get_ticks(SYMBOL, TICK_DATE_FROM, DATE_TO, limit=DATA_LIMIT)
    from_date = await trading.get_ticks(SYMBOL, date_from=TICK_DATE_FROM, count=3)
    latest = await trading.get_ticks(SYMBOL, count=3)
    until_now = await trading.get_ticks(SYMBOL, date_from=TICK_DATE_FROM)
    print(f"Range count: {len(ticks)}")
    print(f"Range sample: {ticks[:PREVIEW_LIMIT]}")
    print(f"Date/count: {from_date[:PREVIEW_LIMIT]}")
    print(f"Latest: {latest[:PREVIEW_LIMIT]}")
    print(f"Date until now count: {len(until_now)}")


EXAMPLES: tuple[Callable[[ExampleContext], Awaitable[None]], ...] = (
    example_01_connect,
    example_02_terminal,
    # example_03_account,
    # example_04_symbol,
    # example_05_position,
    # example_06_order,
    # example_07_history_order,
    # example_08_history_deal,
    # example_09_open_position,
    # example_10_calc_profit_margin,
    # example_11_modify_position,
    # example_12_close_partial_position,
    # example_13_close_position,
    # example_14_pending_orders,
    # example_15_modify_pending_orders,
    # example_16_delete_pending_orders,
    # example_18_historical_bars,
    # example_19_tick_data,
)


async def run_examples(
    backend: TradingBackend, *, allow_writes: bool = False
) -> list[ExampleResult]:
    """Run the demonstrations and always shut down last."""
    ctx = ExampleContext(Trading(backend), allow_writes=allow_writes)
    try:
        for example in EXAMPLES:
            await example(ctx)
    finally:
        await example_17_shutdown(ctx)
    print("\nExamples completed successfully.")
    return ctx.results


def main() -> int:
    """Configure CLI logging and run the selected provider."""
    with TemporaryDirectory(prefix="trading-examples-"):
        try:
            asyncio.run(
                run_examples(
                    create_backend(BROKER),
                    allow_writes=BROKER == "simulator" or ALLOW_LIVE_TRADING,
                )
            )
        except ExampleError as error:
            print("Example failed: %s", error)
            return 1
        except BridgeError as error:
            code = (
                error.code
                if error.code
                in {
                    "DATA_NOT_READY",
                    "DATA_LIMIT_EXCEEDED",
                    "INVALID_MARKET_DATA",
                    "UNSUPPORTED_TIMEFRAME",
                    "BAD_REQUEST",
                    "COMMAND_TIMEOUT",
                    "CONNECTION_LOST",
                    "NOT_CONNECTED",
                    "UNSUPPORTED_OPERATION",
                }
                else "BRIDGE_ERROR"
            )
            print("Example failed: %s", code)
            return 1
        except Exception as error:
            print("Example failed: %s", type(error).__name__)
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
