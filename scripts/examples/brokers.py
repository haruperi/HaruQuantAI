"""Twenty-one named async trading examples with a switchable broker.

Description:
    Adapt the legacy seventeen-function trading walkthrough to the shared Trading
    facade, then add historical bars, ticks, and order book. Backend-specific setup
    stays in create_backend; ExampleContext owns only this run's trade identities and
    state. Shutdown runs last and on errors. Explicit live writes can leave open
    resources when outcomes are uncertain; never retry or close an unknown position.

Purpose:
    FEAT-TRADING-USAGE: Demonstrate the same API on MT5 and seeded simulation.

Key Capabilities:
    - FR-TRADING-USAGE-EXAMPLES: Execute twenty-one named functions and field previews.
      Associated: `example_01_connect()` through `example_21_shutdown()`
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


from app.services.brokers.base import BridgeError
from app.services.brokers.ctrader import CTraderBackend
from app.services.brokers.metatrader import MT5Backend
from app.services.brokers.simulator import SimulationBackend
from app.services.include.contracts import (
    SymbolInfo,
    TerminalInfo,
    TradeRequest,
)
from app.services.trading import (
    MarginMode,
    OrderFilling,
    OrderType,
    ReceiptStatus,
    TradeAction,
    Trading,
    TradingBackend,
)
from app.services.utils import format_timestamp
from app.workspace.data_manager import (
    MarketBar,
    MarketTick,
    Timeframe,
)
from app.workspace.data_manager.history import (
    bars_to_dataframe,
    get_historical_bars,
    get_ticks,
    ticks_to_dataframe,
)

BROKER: Literal["simulator", "mt5", "ctrader"] = "ctrader"
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


def create_backend(name: str | None = None) -> TradingBackend:
    """Select and seed the provider; example bodies use only Trading."""
    selected = BROKER if name is None else name
    print("FR-TRADING-USAGE-LIFECYCLE: selecting backend")
    if selected == "simulator":
        backend = SimulationBackend()
        backend.add_symbol(SymbolInfo(name=SYMBOL))
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
    if selected == "mt5":
        token = os.environ.get(
            "MT5_BRIDGE_TOKEN", "P8H5yPraTVSz4vkuaMVgWN8qcfeXUswuxIV70QES0Co"
        )
        return MT5Backend(auth_token=token)
    if selected == "ctrader":
        return CTraderBackend()
    raise ValueError("BROKER must be simulator, mt5, or ctrader")


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
    connected_info = await ctx.trading.terminal.TerminalInfo()
    command_id = ctx.trading.terminal.last_command_id
    receipt = ctx.trading.receipt(command_id) if command_id is not None else None
    receipt_connected = (
        receipt.value.connected
        if receipt is not None and isinstance(receipt.value, TerminalInfo)
        else receipt.value.get("connected")
        if receipt is not None and isinstance(receipt.value, dict)
        else None
    )
    if (
        not isinstance(connected_info, TerminalInfo)
        or receipt is None
        or receipt.status != ReceiptStatus.RESOLVED
        or receipt.command_id != command_id
        or receipt.object_id != ctx.trading.terminal.object_id
        or receipt.class_name != "TerminalInfo"
        or receipt.method_name != "TerminalInfo"
        or receipt_connected is not True
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
    if not connected_info.connected:
        ctx.trading.disarm()
        raise ExampleError("Terminal responded but is disconnected from its broker")
    print(f"Terminal connected : {connected_info.connected}")
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
    info = await terminal.TerminalInfo()
    print(f"Name: {info.name}")
    print(f"Company: {info.company}")
    print(f"Build: {info.build}")
    print(f"Language: {info.language}")
    print(f"Connected: {info.connected}")
    print(f"Trade allowed: {info.trade_allowed}")
    print(f"DLLs allowed: {info.dlls_allowed}")
    print(f"Trade API disabled: {info.tradeapi_disabled}")
    print(f"Notifications enabled: {info.notifications_enabled}")
    print(f"MQID: {info.mqid}")
    print(f"Ping last: {info.ping_last}")
    print(f"Community balance: {info.community_balance}")
    print(f"Retransmission: {info.retransmission}")
    print(f"Path: {info.path}")
    print(f"Data path: {info.data_path}")
    print(f"Common data path: {info.common_data_path}")


async def example_03_account(ctx: ExampleContext) -> None:
    """Demonstrate printing account information using AccountInfo."""
    _header("Account Information")
    account = ctx.trading.account
    info = await account.AccountInfo()
    print(f"Login: {info.login}")
    print(f"Trade mode: {info.trade_mode}")
    print(f"Leverage: {info.leverage}")
    print(f"Limit orders: {info.limit_orders}")
    print(f"Margin SO mode: {info.stopout_mode}")
    print(f"Trade allowed: {info.trade_allowed}")
    print(f"Trade expert: {info.trade_expert}")
    print(f"Margin mode: {info.margin_mode}")
    print(f"Currency digits: {info.currency_digits}")
    print(f"FIFO close: {info.fifo_close}")
    print(f"Balance: {info.balance}")
    print(f"Credit: {info.credit}")
    print(f"Profit: {info.profit}")
    print(f"Equity: {info.equity}")
    print(f"Margin: {info.margin}")
    print(f"Free margin: {info.free_margin}")
    print(f"Margin level: {info.margin_level}")
    print(f"Margin SO call: {info.margin_call}")
    print(f"Margin SO SO: {info.margin_stop_out}")
    print(f"Margin initial: {info.margin_initial}")
    print(f"Margin maintenance: {info.margin_maintenance}")
    print(f"Assets: {info.assets}")
    print(f"Liabilities: {info.liabilities}")
    print(f"Commission blocked: {info.commission_blocked}")
    print(f"Name: {info.name}")
    print(f"Server: {info.server}")
    print(f"Currency: {info.currency}")
    print(f"Company: {info.company}")


async def example_04_symbol(ctx: ExampleContext) -> None:
    """Demonstrate printing symbol specification information using SymbolInfo."""
    _header("Symbol Information")
    symbol = ctx.trading.symbol

    total = await symbol.SymbolsTotal(False)
    selected = await symbol.SymbolsTotal(True)
    print(f"Symbols total (server): {total}")
    print(f"Symbols total (watchlist): {selected}")

    all_symbols = await symbol.SymbolsGet()
    ru_symbols = await symbol.SymbolsGet("*RU*")
    no_majors = await symbol.SymbolsGet("*,!*USD*,!*EUR*,!*JPY*,!*GBP*")
    print(f"Symbols get (all count): {len(all_symbols)}")
    print(f"Symbols get (*RU*): {ru_symbols}")
    print(f"Symbols get (no USD/EUR/JPY/GBP): {no_majors[:10]}")

    selected_ok = await symbol.SymbolSelect(SYMBOL, True)
    print(f"Symbol select ({SYMBOL}, True): {selected_ok}")

    last_tick = await symbol.SymbolInfoTick(SYMBOL)
    print(f"Symbol info tick: {last_tick}")

    if (
        not await symbol.Name(SYMBOL)
        or not await symbol.Select(True)
        or not await symbol.RefreshRates()
    ):
        ctx.trading.disarm()
        raise ExampleError("Configured symbol or quote is unavailable")
    info = await symbol.SymbolInfo()
    print(f"Name: {info.name}")
    print(f"Digits: {info.digits}")
    print(f"Point: {info.point}")
    print(f"Tick size: {info.trade_tick_size}")
    print(f"Bid: {info.bid}")
    print(f"Ask: {info.ask}")
    print(f"Last: {info.last}")
    print(f"Spread: {info.spread}")
    print(f"Trade mode: {info.trade_mode_description}")
    print(f"Contract size: {info.trade_contract_size}")
    print(f"Min lot: {info.volume_min}")
    print(f"Max lot: {info.volume_max}")
    print(f"Lot step: {info.volume_step}")
    print(f"Swap mode: {info.swap_mode}")
    print(f"Swap long: {info.swap_long}")
    print(f"Swap short: {info.swap_short}")


async def example_05_historical_bars(ctx: ExampleContext) -> None:
    """Demonstrate bars by date range converted to a DataFrame."""
    _header("Historical Bars")
    backend = ctx.trading.backend
    bars = await get_historical_bars(
        backend, SYMBOL, TIMEFRAME, DATE_FROM, DATE_TO, limit=DATA_LIMIT
    )
    print(f"Range count: {len(bars)}")
    print(f"Range sample: {bars[:PREVIEW_LIMIT]}")
    bars_df = bars_to_dataframe(bars)
    print("Historical Bars DataFrame:")
    print(bars_df.head())


async def example_06_tick_data(ctx: ExampleContext) -> None:
    """Demonstrate ticks by date range converted to a DataFrame."""
    _header("Historical Ticks")
    backend = ctx.trading.backend
    ticks = await get_ticks(backend, SYMBOL, TICK_DATE_FROM, DATE_TO, limit=DATA_LIMIT)
    print(f"Range count: {len(ticks)}")
    print(f"Range sample: {ticks[:PREVIEW_LIMIT]}")
    ticks_df = ticks_to_dataframe(ticks)
    print("Historical Ticks DataFrame:")
    print(ticks_df.head())


async def example_07_order_book(ctx: ExampleContext) -> None:
    """Demonstrate subscribing to, fetching, and releasing Market Depth entries."""
    _header("Order Book")
    symbol = ctx.trading.symbol
    add_ok = await symbol.MarketBookAdd(SYMBOL)
    print(f"MarketBookAdd({SYMBOL}): {add_ok}")

    book = await symbol.MarketBookGet(SYMBOL)
    print(f"MarketBookGet count: {len(book)}")
    for i, entry in enumerate(book[:PREVIEW_LIMIT]):
        print(
            f"  [{i}] {entry.type.name} "
            f"price={entry.price} volume={entry.volume} volume_real={entry.volume_real}"
        )
        print(f"      dict: {entry._asdict()}")

    release_ok = await symbol.MarketBookRelease(SYMBOL)
    print(f"MarketBookRelease({SYMBOL}): {release_ok}")


async def example_08_order_check(ctx: ExampleContext) -> None:
    """Demonstrate validating an order before sending using Trade OrderCheck."""
    _header("Order Check")
    trading = ctx.trading
    symbol = SYMBOL
    await trading.symbol.Name(symbol)
    await trading.symbol.RefreshRates()
    sym_info = await trading.symbol.SymbolInfo()
    ask = float(sym_info.ask)
    await trading.trade.SetExpertMagicNumber(ctx.magic)
    await trading.trade.SetDeviationInPoints(20)
    await trading.trade.SetTypeFillingBySymbol(symbol)

    fill_flags = sym_info.trade_fill_flags
    if fill_flags & 1:
        filling = OrderFilling.FOK
    elif fill_flags & 2:
        filling = OrderFilling.IOC
    else:
        filling = OrderFilling.RETURN

    req = TradeRequest(
        action=TradeAction.DEAL,
        symbol=symbol,
        volume=VOLUME,
        order_type=OrderType.BUY,
        price=ask,
        deviation=20,
        magic=ctx.magic,
        type_filling=filling,
    )
    chk_res = await trading.trade.OrderCheck(req)
    print(f"OrderCheck result: retcode={chk_res.retcode} ({chk_res.comment})")
    print(f"  Margin required: {chk_res.margin:.2f}")
    print(f"  Margin free: {chk_res.margin_free:.2f}")


async def example_09_open_position(ctx: ExampleContext) -> None:
    """Demonstrate opening a buy position using Trade."""
    _header("Open Position")
    if not ctx.allow_writes:
        print("Live writes disabled; skipping open position")
        return
    trading = ctx.trading
    account_info = await trading.account.AccountInfo()
    if ctx.position_ticket or int(account_info.margin_mode) != int(
        MarginMode.RETAIL_HEDGING
    ):
        ctx.trading.disarm()
        raise ExampleError("A new hedging position is required for this example")
    sym_info = await trading.symbol.SymbolInfo()
    minimum = float(sym_info.volume_min)
    maximum = float(sym_info.volume_max)
    step = float(sym_info.volume_step)
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
    req = TradeRequest(
        action=TradeAction.DEAL,
        symbol=SYMBOL,
        volume=2 * VOLUME,
        order_type=OrderType.BUY,
        price=float((await trading.symbol.SymbolInfo()).ask),
        deviation=20,
        magic=ctx.magic,
    )
    result = await trading.trade.OrderSend(req)
    retcode = result.retcode
    print(f"Buy dispatch retcode={retcode}")
    if retcode != 10009:
        ctx.trading.disarm()
        raise ExampleError("Buy not confirmed; check trade outcome before rerunning")
    deal = result.deal
    if not deal or not await trading.deal.Ticket(deal):
        ctx.trading.disarm()
        raise ExampleError("Buy deal history could not be selected")
    deal_info = await trading.deal.DealInfo()
    ctx.position_id = deal_info.position_id
    if not ctx.position_id:
        ctx.trading.disarm()
        raise ExampleError("Buy deal position identifier is unavailable")
    for ticket in (result.order, ctx.position_id):
        if ticket and await trading.position.SelectByTicket(ticket):
            pos_info = await trading.position.PositionInfo()
            if (
                pos_info.identifier == ctx.position_id
                and pos_info.magic == ctx.magic
                and pos_info.symbol == SYMBOL
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
    sym_info = await ctx.trading.symbol.SymbolInfo()
    ask = float(sym_info.ask)
    point = float(sym_info.point)
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


async def example_11_position(ctx: ExampleContext) -> None:
    """Demonstrate inspecting open positions using PositionInfo."""
    _header("Position Information")
    position = ctx.trading.position
    total = await position.PositionsTotal()
    print(f"Total open positions (PositionsTotal): {total}")

    by_symbol = await position.PositionsGet(symbol=SYMBOL)
    print(f"Positions by symbol '{SYMBOL}': {len(by_symbol)}")

    by_group = await position.PositionsGet(group="*USD*")
    print(f"Positions by group '*USD*': {len(by_group)}")

    if ctx.position_ticket:
        by_ticket = await position.PositionsGet(ticket=ctx.position_ticket)
        print(f"Positions by ticket {ctx.position_ticket}: {len(by_ticket)}")

    all_positions = await position.PositionsGet()
    print(f"All positions (PositionsGet): {len(all_positions)}")
    found = False
    for index in range(PREVIEW_LIMIT):
        if not await position.SelectByIndex(index):
            break
        found = True
        pos = await position.PositionInfo()
        print(f"Position [{index}]:")
        print(f"  Symbol: {pos.symbol}")
        print(f"  Type: {pos.type_description}")
        print(f"  Volume: {pos.volume}")
        print(f"  Open price: {pos.price_open}")
        print(f"  Current price: {pos.price_current}")
        print(f"  SL: {pos.sl}")
        print(f"  TP: {pos.tp}")
        print(f"  Profit: {pos.profit}")
        print(f"  Swap: {pos.swap}")
    if not found:
        print("No open positions")


async def example_12_modify_position(ctx: ExampleContext) -> None:
    """Demonstrate modifying the owned position's SL/TP using Trade."""
    _header("Modify Position")
    if not ctx.allow_writes:
        print("Live writes disabled; skipping modify position")
        return
    pos, symbol, trade = ctx.trading.position, ctx.trading.symbol, ctx.trading.trade
    if not ctx.position_ticket or not await pos.SelectByTicket(ctx.position_ticket):
        ctx.trading.disarm()
        raise ExampleError("Position ownership must be confirmed before modification")
    pos_info = await pos.PositionInfo()
    if (
        pos_info.identifier != ctx.position_id
        or pos_info.magic != ctx.magic
        or pos_info.symbol != SYMBOL
    ):
        ctx.trading.disarm()
        raise ExampleError("Position ownership must be confirmed before modification")
    await symbol.RefreshRates()
    sym_info = await symbol.SymbolInfo()
    distance = max(
        1000,
        sym_info.trade_stops_level + 20,
        sym_info.trade_freeze_level + 20,
    ) * float(sym_info.point)
    bid, digits = float(sym_info.bid), sym_info.digits
    sl, tp = round(bid - distance, digits), round(bid + distance, digits)
    req = TradeRequest(
        action=TradeAction.SLTP,
        position=ctx.position_ticket,
        symbol=SYMBOL,
        sl=sl,
        tp=tp,
        magic=ctx.magic,
    )
    result = await trade.OrderSend(req)
    retcode = result.retcode
    print(f"Position modify dispatch retcode={retcode}")
    if retcode != 10009 or not await pos.SelectByTicket(ctx.position_ticket):
        ctx.trading.disarm()
        raise ExampleError("Position modification not confirmed; inspect trade outcome")
    pos_info = await pos.PositionInfo()
    if not math.isclose(pos_info.sl, sl) or not math.isclose(pos_info.tp, tp):
        ctx.trading.disarm()
        raise ExampleError("Position modification not confirmed; inspect trade outcome")
    print(f"Modified owned position SL={sl}, TP={tp}")


async def example_13_close_partial_position(ctx: ExampleContext) -> None:
    """Demonstrate partially closing the owned position using Trade."""
    _header("Close Partial Position")
    if not ctx.allow_writes:
        print("Live writes disabled; skipping partial close")
        return
    pos, trade, symbol = (
        ctx.trading.position,
        ctx.trading.trade,
        ctx.trading.symbol,
    )
    if not ctx.position_ticket or not await pos.SelectByTicket(ctx.position_ticket):
        ctx.trading.disarm()
        raise ExampleError("Position ownership must be confirmed before partial close")
    pos_info = await pos.PositionInfo()
    if (
        pos_info.identifier != ctx.position_id
        or pos_info.magic != ctx.magic
        or pos_info.symbol != SYMBOL
    ):
        ctx.trading.disarm()
        raise ExampleError("Position ownership must be confirmed before partial close")
    before = pos_info.volume
    req = TradeRequest(
        action=TradeAction.DEAL,
        position=ctx.position_ticket,
        symbol=SYMBOL,
        volume=VOLUME,
        order_type=OrderType.SELL,
        price=float((await symbol.SymbolInfo()).bid),
        deviation=20,
        magic=ctx.magic,
    )
    result = await trade.OrderSend(req)
    retcode = result.retcode
    print(f"Partial close dispatch retcode={retcode}")
    if retcode != 10009 or not await pos.SelectByTicket(ctx.position_ticket):
        ctx.trading.disarm()
        raise ExampleError("Partial close not confirmed; inspect trade outcome")
    pos_info = await pos.PositionInfo()
    remaining = pos_info.volume
    if remaining <= 0 or not math.isclose(remaining, before - VOLUME):
        ctx.trading.disarm()
        raise ExampleError("Partial-close remaining volume did not match")
    print(f"Partial close successful; remaining volume: {remaining}")


async def example_14_close_position(ctx: ExampleContext) -> None:
    """Demonstrate fully closing the remaining owned position using Trade."""
    _header("Close Position")
    if not ctx.allow_writes:
        print("Live writes disabled; skipping close position")
        return
    pos, trade, symbol = (
        ctx.trading.position,
        ctx.trading.trade,
        ctx.trading.symbol,
    )
    if not ctx.position_ticket or not await pos.SelectByTicket(ctx.position_ticket):
        ctx.trading.disarm()
        raise ExampleError("Position ownership must be confirmed before closing")
    pos_info = await pos.PositionInfo()
    if (
        pos_info.identifier != ctx.position_id
        or pos_info.magic != ctx.magic
        or pos_info.symbol != SYMBOL
    ):
        ctx.trading.disarm()
        raise ExampleError("Position ownership must be confirmed before closing")
    req = TradeRequest(
        action=TradeAction.DEAL,
        position=ctx.position_ticket,
        symbol=SYMBOL,
        volume=pos_info.volume,
        order_type=OrderType.SELL,
        price=float((await symbol.SymbolInfo()).bid),
        deviation=20,
        magic=ctx.magic,
    )
    result = await trade.OrderSend(req)
    retcode = result.retcode
    print(f"Position close dispatch retcode={retcode}")
    if retcode != 10009 or await pos.SelectByTicket(ctx.position_ticket):
        ctx.trading.disarm()
        raise ExampleError("Position close not confirmed; inspect trade outcome")
    ctx.position_ticket = 0
    print("Closed remaining owned position")


async def example_15_pending_orders(ctx: ExampleContext) -> None:
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
    sym_info = await symbol.SymbolInfo()
    distance = max(
        1000,
        sym_info.trade_stops_level + 20,
        sym_info.trade_freeze_level + 20,
    ) * float(sym_info.point)
    ctx.pending_price = round(float(sym_info.bid) - distance, sym_info.digits)
    req = TradeRequest(
        action=TradeAction.PENDING,
        symbol=SYMBOL,
        volume=VOLUME,
        order_type=OrderType.BUY_LIMIT,
        price=ctx.pending_price,
        magic=ctx.magic,
    )
    result = await trade.OrderSend(req)
    retcode = result.retcode
    print(f"BuyLimit dispatch retcode={retcode}")
    if retcode not in (10008, 10009):
        ctx.trading.disarm()
        raise ExampleError("Pending order not confirmed; inspect trade outcome")
    ctx.pending_ticket = result.order
    if not ctx.pending_ticket or not await order.Select(ctx.pending_ticket):
        ctx.trading.disarm()
        raise ExampleError("Pending order ownership could not be confirmed")
    ord_info = await order.OrderInfo()
    if ord_info.magic != ctx.magic or ord_info.symbol != SYMBOL:
        ctx.trading.disarm()
        raise ExampleError("Pending order ownership could not be confirmed")
    print(f"Placed owned pending order at price: {ctx.pending_price}; volume: {VOLUME}")


async def example_16_order(ctx: ExampleContext) -> None:
    """Demonstrate inspecting pending orders using OrderInfo."""
    _header("Order Information")
    order = ctx.trading.order
    total = await order.OrdersTotal()
    print(f"Total active orders (OrdersTotal): {total}")

    by_symbol = await order.OrdersGet(symbol=SYMBOL)
    print(f"Orders by symbol '{SYMBOL}': {len(by_symbol)}")

    by_group = await order.OrdersGet(group="*USD*")
    print(f"Orders by group '*USD*': {len(by_group)}")

    if ctx.pending_ticket:
        by_ticket = await order.OrdersGet(ticket=ctx.pending_ticket)
        print(f"Orders by ticket {ctx.pending_ticket}: {len(by_ticket)}")

    all_orders = await order.OrdersGet()
    print(f"All orders (OrdersGet): {len(all_orders)}")
    found = False
    for index in range(PREVIEW_LIMIT):
        if not await order.SelectByIndex(index):
            break
        found = True
        ord_info = await order.OrderInfo()
        print(f"Order [{index}]:")
        print(f"  Symbol: {ord_info.symbol}")
        print(f"  Type: {ord_info.type_description}")
        print(f"  Volume: {ord_info.volume_current}")
        print(f"  Price: {ord_info.price_open}")
        print(f"  SL: {ord_info.sl}")
        print(f"  TP: {ord_info.tp}")
    if not found:
        print("No pending orders")


async def example_17_modify_pending_orders(ctx: ExampleContext) -> None:
    """Demonstrate modifying the owned pending order using Trade."""
    _header("Modify Pending Order")
    if not ctx.allow_writes:
        print("Live writes disabled; skipping modify pending order")
        return
    order, symbol, trade = ctx.trading.order, ctx.trading.symbol, ctx.trading.trade
    if not ctx.pending_ticket or not await order.Select(ctx.pending_ticket):
        ctx.trading.disarm()
        raise ExampleError("Order ownership must be confirmed before modification")
    ord_info = await order.OrderInfo()
    if ord_info.magic != ctx.magic or ord_info.symbol != SYMBOL:
        ctx.trading.disarm()
        raise ExampleError("Order ownership must be confirmed before modification")
    await symbol.RefreshRates()
    sym_info = await symbol.SymbolInfo()
    distance = max(
        1000,
        sym_info.trade_stops_level + 20,
        sym_info.trade_freeze_level + 20,
    ) * float(sym_info.point)
    price = round(ctx.pending_price - distance, sym_info.digits)
    req = TradeRequest(
        action=TradeAction.MODIFY,
        order=ctx.pending_ticket,
        price=price,
        magic=ctx.magic,
    )
    result = await trade.OrderSend(req)
    retcode = result.retcode
    print(f"Order modify dispatch retcode={retcode}")
    if retcode != 10009 or not await order.Select(ctx.pending_ticket):
        ctx.trading.disarm()
        raise ExampleError("Order modification not confirmed; inspect trade outcome")
    ord_info = await order.OrderInfo()
    if not math.isclose(ord_info.price_open, price):
        ctx.trading.disarm()
        raise ExampleError("Order modification not confirmed; inspect trade outcome")
    ctx.pending_price = price
    print(f"Modified owned pending order price: {price}")


async def example_18_delete_pending_orders(ctx: ExampleContext) -> None:
    """Demonstrate cancelling the owned pending order using Trade."""
    _header("Cancel Pending Order")
    if not ctx.allow_writes:
        print("Live writes disabled; skipping delete pending order")
        return
    order, trade = ctx.trading.order, ctx.trading.trade
    if not ctx.pending_ticket or not await order.Select(ctx.pending_ticket):
        ctx.trading.disarm()
        raise ExampleError("Order ownership must be confirmed before cancellation")
    ord_info = await order.OrderInfo()
    if ord_info.magic != ctx.magic or ord_info.symbol != SYMBOL:
        ctx.trading.disarm()
        raise ExampleError("Order ownership must be confirmed before cancellation")
    req = TradeRequest(
        action=TradeAction.REMOVE,
        order=ctx.pending_ticket,
        magic=ctx.magic,
    )
    result = await trade.OrderSend(req)
    retcode = result.retcode
    print(f"Order delete dispatch retcode={retcode}")
    if retcode != 10009 or await order.Select(ctx.pending_ticket):
        ctx.trading.disarm()
        raise ExampleError("Order cancellation not confirmed; inspect trade outcome")
    ctx.pending_ticket = 0
    print("Deleted owned pending order")


async def example_19_history_order(ctx: ExampleContext) -> None:
    """Demonstrate inspecting historical orders using HistoryOrderInfo."""
    _header("History Order Information")
    order = ctx.trading.history_order
    now = datetime.now(UTC)
    interval_start = now - timedelta(days=7)
    total = await order.HistoryOrdersTotal(interval_start, now)
    print(f"Total history orders (HistoryOrdersTotal): {total}")

    by_symbol = await order.HistoryOrdersGet(symbol=SYMBOL)
    print(f"History orders by symbol '{SYMBOL}': {len(by_symbol)}")

    by_group = await order.HistoryOrdersGet(group="*USD*")
    print(f"History orders by group '*USD*': {len(by_group)}")

    if ctx.pending_ticket:
        by_ticket = await order.HistoryOrdersGet(ticket=ctx.pending_ticket)
        print(f"History orders by ticket {ctx.pending_ticket}: {len(by_ticket)}")

    if ctx.position_id:
        by_pos = await order.HistoryOrdersGet(position=ctx.position_id)
        print(f"History orders by position {ctx.position_id}: {len(by_pos)}")

    all_history = await order.HistoryOrdersGet()
    print(f"All history orders (HistoryOrdersGet): {len(all_history)}")
    found = False
    for index in range(PREVIEW_LIMIT):
        if not await order.SelectByIndex(index):
            break
        found = True
        h_order = await order.HistoryOrderInfo()
        print(f"History Order [{index}]:")
        print(f"  Symbol: {h_order.symbol}")
        print(f"  Type: {h_order.type_description}")
        print(f"  State: {h_order.state_description}")
        print(f"  Volume: {h_order.volume_initial}")
        print(f"  Price: {h_order.price_open}")
        print(f"  Done time: {format_timestamp(h_order.time_done)}")
    if not found:
        print("No history orders")


async def example_20_history_deal(ctx: ExampleContext) -> None:
    """Demonstrate inspecting historical deals using DealInfo."""
    _header("Deal Information")
    deal = ctx.trading.deal
    now = datetime.now(UTC)
    interval_start = now - timedelta(days=7)
    total = await deal.HistoryDealsTotal(interval_start, now)
    print(f"Total history deals (HistoryDealsTotal): {total}")

    by_symbol = await deal.HistoryDealsGet(symbol=SYMBOL)
    print(f"History deals by symbol '{SYMBOL}': {len(by_symbol)}")

    by_group = await deal.HistoryDealsGet(group="*USD*")
    print(f"History deals by group '*USD*': {len(by_group)}")

    if ctx.position_id:
        by_pos = await deal.HistoryDealsGet(position=ctx.position_id)
        print(f"History deals by position {ctx.position_id}: {len(by_pos)}")

    all_deals = await deal.HistoryDealsGet()
    print(f"All history deals (HistoryDealsGet): {len(all_deals)}")
    found = False
    for index in range(PREVIEW_LIMIT):
        if not await deal.SelectByIndex(index):
            break
        found = True
        d_info = await deal.DealInfo()
        print(f"Deal [{index}]:")
        print(f"  Symbol: {d_info.symbol}")
        print(f"  Type: {d_info.type_description}")
        print(f"  Entry: {d_info.entry_description}")
        print(f"  Volume: {d_info.volume}")
        print(f"  Price: {d_info.price}")
        print(f"  Profit: {d_info.profit}")
        print(f"  Commission: {d_info.commission}")
        print(f"  Swap: {d_info.swap}")
    if not found:
        print("No history deals")


async def example_21_shutdown(ctx: ExampleContext) -> None:
    """Demonstrate shutting down the broker connection."""
    _header("Shutdown")
    if not ctx.closed:
        ctx.closed = True
        ctx.trading.disarm()
        await ctx.trading.close()
        print("Broker connection closed successfully")


example_17_shutdown = example_21_shutdown
example_19_shutdown = example_21_shutdown
example_20_shutdown = example_21_shutdown


EXAMPLES: tuple[Callable[[ExampleContext], Awaitable[None]], ...] = (
    example_01_connect,
    example_02_terminal,
    example_03_account,
    example_04_symbol,
    example_05_historical_bars,
    example_06_tick_data,
    example_07_order_book,
    example_08_order_check,
    example_09_open_position,
    example_10_calc_profit_margin,
    example_11_position,
    example_12_modify_position,
    example_13_close_partial_position,
    example_14_close_position,
    example_15_pending_orders,
    example_16_order,
    example_17_modify_pending_orders,
    example_18_delete_pending_orders,
    example_19_history_order,
    example_20_history_deal,
)


async def run_examples(
    backend: TradingBackend, *, allow_writes: bool = False
) -> list[ExampleResult]:
    """Run the demonstrations and always shut down last."""
    ctx = ExampleContext(Trading(backend), allow_writes=allow_writes)
    try:
        for i, example in enumerate(EXAMPLES):
            if i >= 8:
                await asyncio.sleep(2)
            await example(ctx)
    finally:
        await example_21_shutdown(ctx)
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
            print(f"Example failed: {error}")
            return 1
        except BridgeError as error:
            code = (
                error.code
                if error.code
                in {
                    "SYMBOL_NOT_FOUND",
                    "AUTH_FAILED",
                    "CONNECT_FAILED",
                    "MODULE_NOT_FOUND",
                    "CTRADER_CONFIG_INVALID",
                    "CTRADER_ENVIRONMENT_MISMATCH",
                    "CTRADER_REAUTHORIZE_REQUIRED",
                    "CTRADER_TOKEN_PERSIST_FAILED",
                    "CTRADER_ACCOUNT_ID_IS_LOGIN",
                    "CTRADER_ACCOUNT_NOT_AUTHORIZED",
                    "CH_ACCESS_TOKEN_INVALID",
                    "OA_AUTH_TOKEN_EXPIRED",
                    "CH_CLIENT_AUTH_FAILURE",
                    "ACCOUNT_NOT_AUTHORIZED",
                    "CH_CTID_TRADER_ACCOUNT_NOT_FOUND",
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
            print(f"Example failed: {code}")
            return 1
        except Exception as error:
            print(f"Example failed: {type(error).__name__}")
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
