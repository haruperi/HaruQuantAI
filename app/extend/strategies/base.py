# ruff: noqa: N802
"""Base execution contracts, market data structures, and Strategy abstraction.

Description:
    Provides domain contracts and runtime interfaces conforming to StrategyQuant's
    SQ.Internal.Strategy and com.strategyquant.tradinglib specifications. Includes
    DataSeries, ChartData, MarketData, ILiveOrder, OrderBuilder, Trader,
    Indicators, UpdateEventTypes, OrderTypes, OrderCloseTypes, and Strategy.

Purpose:
    FEAT-STRATEGIES: StrategyQuant donor-faithful strategy execution framework.

Key Capabilities:
    - FR-STRAT-BASE: Strategy lifecycle hooks (Initialize, OnBarUpdate, Deinitialize).
    - FR-STRAT-MARKETDATA: Multi-chart data structures with time/price access.
    - FR-STRAT-TRADER: Order dispatch, management, and account metrics.
    - FR-STRAT-INDICATORS: Built-in indicator adapters (CCI, ATR).

Python API Usage:
    from app.extend.strategies.base import Strategy, UpdateEventTypes

CLI Usage:
    uv run pytest tests/extend/test_strategies_catalog.py --no-cov
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence
from dataclasses import dataclass
from enum import IntEnum
from typing import Any, cast, overload

from app.core.host.logging import get_logger

logger = get_logger(__name__)


class UpdateEventTypes(IntEnum):
    """Bar/tick update event types matching StrategyQuant UpdateEventTypes."""

    BarTick = 0
    BarOpen = 1
    BarClose = 2


class OrderTypes(IntEnum):
    """Order type enumeration matching StrategyQuant OrderTypes constants."""

    Buy = 1
    Sell = 2
    BuyLimit = 3
    SellLimit = 4
    BuyStop = 5
    SellStop = 6


class OrderCloseTypes(IntEnum):
    """Order close reason enumeration matching StrategyQuant OrderCloseTypes."""

    Normal = 0
    Reversed = 1
    Deleted = 2
    Manual = 3
    SL = 4
    PT = 5
    EndOfDay = 6


class DataSeries:
    """Historical data series providing StrategyQuant shift-based lookup."""

    def __init__(self, values: Sequence[float] | None = None) -> None:
        """Initialize data series with chronological values (oldest to newest)."""
        self._values: list[float] = [float(v) for v in (values or [])]

    def get(self, shift: int = 0, default: float = 0.0) -> float:
        """Retrieve value at specified bar shift (0 = current/most recent)."""
        idx = len(self._values) - 1 - shift
        if 0 <= idx < len(self._values):
            return self._values[idx]
        return default

    def __getitem__(self, shift: int) -> float:
        """Index access by bar shift."""
        return self.get(shift)

    def __len__(self) -> int:
        """Return total number of bars in series."""
        return len(self._values)

    def append(self, val: float) -> None:
        """Append newest value to series."""
        self._values.append(float(val))

    def to_list(self) -> list[float]:
        """Return raw internal list copy."""
        return list(self._values)


class IndicatorResult:
    """Wrapper holding an indicator output DataSeries."""

    def __init__(self, values: Sequence[float]) -> None:
        self.Value: DataSeries = DataSeries(values)


class ChartData:
    """Representation of an instrument chart and its price/time streams."""

    def __init__(  # noqa: PLR0917
        self,
        symbol: str = "EURUSD",
        timeframe: str = "H1",
        connection: str = "Default",
        opens: Sequence[float] | None = None,
        highs: Sequence[float] | None = None,
        lows: Sequence[float] | None = None,
        closes: Sequence[float] | None = None,
        volumes: Sequence[float] | None = None,
        times: Sequence[float] | None = None,
    ) -> None:
        self.Symbol: str = symbol
        self.Timeframe: str = timeframe
        self.Connection: str = connection
        self.EventType: int = UpdateEventTypes.BarOpen
        self._updated: bool = False

        self._opens = opens if opens is not None else [1.0, 1.05, 1.1]
        self._highs = highs if highs is not None else [1.02, 1.07, 1.12]
        self._lows = lows if lows is not None else [0.99, 1.04, 1.09]
        self._closes = closes if closes is not None else [1.01, 1.06, 1.11]
        self._volumes = volumes if volumes is not None else [100.0, 150.0, 200.0]
        self._times = (
            times
            if times is not None
            else [1514764800000.0, 1514768400000.0, 1514772000000.0]
        )

        self.Open: DataSeries = DataSeries(self._opens)
        self.High: DataSeries = DataSeries(self._highs)
        self.Low: DataSeries = DataSeries(self._lows)
        self.Close: DataSeries = DataSeries(self._closes)
        self.Volume: DataSeries = DataSeries(self._volumes)
        self.Time_series: DataSeries = DataSeries(self._times)

    def Open_val(self, shift: int = 0) -> float:
        """Return open price at shift."""
        return self.Open.get(shift)

    def High_val(self, shift: int = 0) -> float:
        """Return high price at shift."""
        return self.High.get(shift)

    def Low_val(self, shift: int = 0) -> float:
        """Return low price at shift."""
        return self.Low.get(shift)

    def Close_val(self, shift: int = 0) -> float:
        """Return close price at shift."""
        return self.Close.get(shift)

    def Volume_val(self, shift: int = 0) -> float:
        """Return volume at shift."""
        return self.Volume.get(shift)

    def Time(self, shift: int = 0) -> int:
        """Return epoch timestamp in milliseconds at shift."""
        return int(self.Time_series.get(shift))

    def Ask(self) -> float:
        """Return current ask price."""
        return self.Close.get(0) + 0.0001

    def Bid(self) -> float:
        """Return current bid price."""
        return self.Close.get(0)

    def isUpdated(self) -> bool:
        """Return whether this chart received an update in the current event."""
        return self._updated

    def set_updated(self, updated: bool) -> None:
        """Set chart updated flag."""
        self._updated = updated


class MarketDataManager:
    """Manages multi-chart datasets for strategy execution."""

    def __init__(self, default_chart: ChartData | None = None) -> None:
        self._charts: list[ChartData] = [default_chart or ChartData()]

    def Chart(self, index: int = 0) -> ChartData:
        """Return ChartData at given index, creating default if necessary."""
        while len(self._charts) <= index:
            self._charts.append(
                ChartData(
                    symbol=f"XSymbol_0_{len(self._charts)}",
                    timeframe="H1",
                    connection="Default",
                )
            )
        return self._charts[index]

    def addChart(
        self,
        arg1: str,
        arg2: str | None = None,
        arg3: str | None = None,
    ) -> ChartData:
        """Add new chart with flexible signatures matching StrategyQuant API."""
        if arg2 is None and arg3 is None:
            timeframe = arg1
            chart = ChartData(timeframe=timeframe)
        elif arg3 is None:
            symbol = arg1
            timeframe = arg2 or "H1"
            chart = ChartData(symbol=symbol, timeframe=timeframe)
        else:
            connection = arg1
            symbol = arg2 or "Symbol"
            timeframe = arg3
            chart = ChartData(connection=connection, symbol=symbol, timeframe=timeframe)
        self._charts.append(chart)
        return chart

    def get_charts_count(self) -> int:
        """Return total number of charts."""
        return len(self._charts)


@dataclass
class ITradingEvent:
    """Payload representing a strategy trading execution event."""

    event_type: str = "OrderFilled"
    order: ILiveOrder | None = None
    message: str = ""
    timestamp: int = 0


class ITradingEventListener:
    """Protocol for receiving asynchronous strategy trading events."""

    def OnEvent(self, event: ITradingEvent) -> None:
        """Handle global trading event."""

    def OnTradingEvent(self, event: ITradingEvent) -> None:
        """Handle order-specific async event."""


class ILiveOrder:
    """Represents an active or historical trade/order in strategy execution."""

    def __init__(  # noqa: PLR0917
        self,
        symbol: str,
        order_type: int,
        size: float = 1.0,
        price: float = 0.0,
        magic_number: int = 0,
        comment: str = "",
        sl: float = 0.0,
        pt: float = 0.0,
    ) -> None:
        self._symbol: str = symbol
        self._order_type: int = order_type
        self._size: float = size
        self._open_price: float = price
        self._close_price: float = 0.0
        self._magic_number: int = magic_number
        self._comment: str = comment
        self._sl: float = sl
        self._pt: float = pt
        self._bars_in_trade: int = 0
        self._is_closed: bool = False
        self._close_type: int = OrderCloseTypes.Normal
        self._is_successful: bool = True
        self._is_pending: bool = order_type in (
            OrderTypes.BuyLimit,
            OrderTypes.SellLimit,
            OrderTypes.BuyStop,
            OrderTypes.SellStop,
        )

    def is_active(self) -> bool:
        """Return whether order is currently active and not closed."""
        return not self._is_closed

    def getMagicNumber(self) -> int:
        """Return order magic number."""
        return self._magic_number

    def getOrderType(self) -> int:
        """Return order type (Buy, Sell, etc.)."""
        return self._order_type

    def getOpenPrice(self) -> float:
        """Return order execution/entry price."""
        return self._open_price

    def getClosePrice(self) -> float:
        """Return order close price."""
        return self._close_price

    def getBarsInTrade(self) -> int:
        """Return duration of trade in completed bars."""
        return self._bars_in_trade

    def increment_bars(self) -> None:
        """Increment bars in trade counter."""
        self._bars_in_trade += 1

    def setSL(self, sl: float) -> ILiveOrder:
        """Update stop loss price."""
        self._sl = sl
        return self

    def setPT(self, pt: float) -> ILiveOrder:
        """Update profit target price."""
        self._pt = pt
        return self

    def Send(self) -> ILiveOrder:
        """Confirm modification / re-send."""
        logger.info(
            "FR-STRAT-ORDER-MOD: order %s updated SL=%s PT=%s",
            self._magic_number,
            self._sl,
            self._pt,
        )
        return self

    def Close(self, close_type: int = OrderCloseTypes.Normal) -> None:
        """Close order with specified reason code."""
        self._is_closed = True
        self._close_type = close_type
        logger.info(
            "FR-STRAT-ORDER-CLOSE: order %s closed via code %s",
            self._magic_number,
            close_type,
        )

    def CloseAsync(self, listener: ITradingEventListener | None = None) -> None:
        """Asynchronously close order and notify listener."""
        self.Close(OrderCloseTypes.Normal)
        if listener is not None:
            listener.OnTradingEvent(
                ITradingEvent(event_type="OrderClosed", order=self, message="Closed")
            )

    def isSuccessful(self) -> bool:
        """Return whether order fill was successful."""
        return self._is_successful

    def isPendingOrder(self) -> bool:
        """Return whether order is pending entry."""
        return self._is_pending


class OrderBuilder:
    """Fluent order parameters builder matching StrategyQuant Trader.Buy().Send()."""

    def __init__(
        self,
        trader: Trader,
        symbol: str,
        order_type: int,
        size: float = 1.0,
        price: float = 0.0,
    ) -> None:
        self._trader: Trader = trader
        self._symbol: str = symbol
        self._order_type: int = order_type
        self._size: float = size
        self._price: float = price
        self._magic_number: int = 0
        self._comment: str = ""
        self._sl: float = 0.0
        self._pt: float = 0.0
        self._expiration: float = 0.0
        self._max_slippage: float = 0.0

    def setSize(self, size: float) -> OrderBuilder:
        """Set order lot size."""
        self._size = size
        return self

    def setMagicNumber(self, magic: int) -> OrderBuilder:
        """Set order magic number."""
        self._magic_number = magic
        return self

    def setComment(self, comment: str) -> OrderBuilder:
        """Set order comment."""
        self._comment = comment
        return self

    def setSL(self, sl: float) -> OrderBuilder:
        """Set stop loss price."""
        self._sl = sl
        return self

    def setPT(self, pt: float) -> OrderBuilder:
        """Set profit target price."""
        self._pt = pt
        return self

    def setExpiration(self, expiration: float) -> OrderBuilder:
        """Set order expiration timestamp."""
        self._expiration = expiration
        return self

    def setMaxSlippage(self, slippage: float) -> OrderBuilder:
        """Set max slippage."""
        self._max_slippage = slippage
        return self

    def Send(self) -> ILiveOrder:
        """Submit and register order synchronously."""
        order = ILiveOrder(
            symbol=self._symbol,
            order_type=self._order_type,
            size=self._size,
            price=self._price or 1.1000,
            magic_number=self._magic_number,
            comment=self._comment,
            sl=self._sl,
            pt=self._pt,
        )
        self._trader.register_order(order)
        logger.info(
            "FR-STRAT-ORDER-SEND: order type=%s symbol=%s size=%s magic=%s",
            self._order_type,
            self._symbol,
            self._size,
            self._magic_number,
        )
        return order

    def SendAsync(self, listener: ITradingEventListener | None = None) -> ILiveOrder:
        """Submit order asynchronously and notify listener."""
        order = self.Send()
        if listener is not None:
            listener.OnTradingEvent(
                ITradingEvent(event_type="OrderSent", order=order, message="Sent")
            )
        return order


class Trader:
    """Trading bridge for StrategyQuant order routing and account introspection."""

    def __init__(self, balance: float = 10000.0, equity: float = 10000.0) -> None:
        self._balance: float = balance
        self._equity: float = equity
        self._open_orders: list[ILiveOrder] = []
        self._history_orders: list[ILiveOrder] = []

    def register_order(self, order: ILiveOrder) -> None:
        """Register newly created order."""
        self._open_orders.append(order)

    def Buy(self, symbol: str) -> OrderBuilder:
        """Initiate Buy market order builder."""
        return OrderBuilder(self, symbol, OrderTypes.Buy)

    def Sell(self, symbol: str) -> OrderBuilder:
        """Initiate Sell market order builder."""
        return OrderBuilder(self, symbol, OrderTypes.Sell)

    def BuyLimit(self, symbol: str, price: float) -> OrderBuilder:
        """Initiate BuyLimit order builder."""
        return OrderBuilder(self, symbol, OrderTypes.BuyLimit, price=price)

    def SellLimit(self, symbol: str, price: float) -> OrderBuilder:
        """Initiate SellLimit order builder."""
        return OrderBuilder(self, symbol, OrderTypes.SellLimit, price=price)

    def BuyStop(self, symbol: str, price: float) -> OrderBuilder:
        """Initiate BuyStop order builder."""
        return OrderBuilder(self, symbol, OrderTypes.BuyStop, price=price)

    def SellStop(self, symbol: str, price: float) -> OrderBuilder:
        """Initiate SellStop order builder."""
        return OrderBuilder(self, symbol, OrderTypes.SellStop, price=price)

    def Open(self, order_type: int, symbol: str, size: float = 1.0) -> OrderBuilder:
        """Initiate generic order builder with specified type and size."""
        return OrderBuilder(self, symbol, order_type, size=size)

    def getOpenOrdersCount(self, is_live: bool = True) -> int:
        """Return count of active non-closed orders."""
        _ = is_live
        return len([o for o in self._open_orders if o.is_active()])

    def getOpenOrder(self, index: int, is_live: bool = True) -> ILiveOrder:
        """Return active order at index."""
        _ = is_live
        active = [o for o in self._open_orders if o.is_active()]
        return active[index]

    def getAccountBalance(self) -> float:
        """Return simulated account cash balance."""
        return self._balance

    def setAccountBalance(self, balance: float) -> None:
        """Update account cash balance."""
        self._balance = balance

    def getAccountEquity(self) -> float:
        """Return simulated account equity."""
        return self._equity

    def setAccountEquity(self, equity: float) -> None:
        """Update account equity."""
        self._equity = equity

    def GetHistoryTrades(self) -> list[ILiveOrder]:
        """Return list of closed historical trades."""
        return list(self._history_orders)


class Indicators:
    """Built-in technical indicator calculations conforming to SQ indicator library."""

    def __init__(self, strategy: Strategy | None = None) -> None:
        self.strategy: Strategy | None = strategy
        self.Engine: int = 1

    def destroy(self) -> None:
        """Clean up cached indicator states."""

    def getIndicatorsCache(self) -> dict[str, Any]:
        """Return cached calculation states."""
        return {}

    def CCI(
        self, series: DataSeries | Sequence[float], period: int = 20
    ) -> IndicatorResult:
        """Calculate Commodity Channel Index on data series."""
        vals = series.to_list() if isinstance(series, DataSeries) else list(series)
        n = len(vals)
        if n < period or period <= 0:
            return IndicatorResult([0.0] * max(n, 1))

        output: list[float] = []
        for i in range(n):
            if i + 1 < period:
                output.append(0.0)
                continue
            window = vals[i + 1 - period : i + 1]
            sma = sum(window) / period
            mean_dev = sum(abs(x - sma) for x in window) / period
            if mean_dev == 0.0:
                output.append(0.0)
            else:
                output.append((vals[i] - sma) / (0.015 * mean_dev))
        return IndicatorResult(output)

    def ATR(self, chart_data: ChartData, period: int = 14) -> IndicatorResult:
        """Calculate Average True Range on chart data."""
        highs = chart_data.High.to_list()
        lows = chart_data.Low.to_list()
        closes = chart_data.Close.to_list()
        n = min(len(highs), len(lows), len(closes))
        if n == 0 or period <= 0:
            return IndicatorResult([0.0])

        tr_values: list[float] = []
        for i in range(n):
            if i == 0:
                tr_values.append(highs[i] - lows[i])
            else:
                tr = max(
                    highs[i] - lows[i],
                    abs(highs[i] - closes[i - 1]),
                    abs(lows[i] - closes[i - 1]),
                )
                tr_values.append(tr)

        output: list[float] = []
        for i in range(n):
            if i + 1 < period:
                output.append(tr_values[i])
            else:
                window = tr_values[i + 1 - period : i + 1]
                output.append(sum(window) / period)
        return IndicatorResult(output)


class StrategyLogger:
    """Strategy logger matching StrategyQuant Log facade."""

    @staticmethod
    def debug(msg: str) -> None:
        """Output debug log message."""
        logger.debug("FR-STRAT-LOG: %s", msg)

    @staticmethod
    def info(msg: str) -> None:
        """Output informational log message."""
        logger.info("FR-STRAT-LOG: %s", msg)

    @staticmethod
    def warn(msg: str) -> None:
        """Output warning log message."""
        logger.warning("FR-STRAT-LOG: %s", msg)

    @staticmethod
    def error(msg: str) -> None:
        """Output error log message."""
        logger.error("FR-STRAT-LOG: %s", msg)


Log = StrategyLogger


class Parameter[T]:
    """Descriptor identifying configurable strategy parameter attributes."""

    def __init__(self, default: T) -> None:
        self.default: T = default
        self.name: str = ""

    def __set_name__(self, owner: type[Any], name: str) -> None:
        """Bind descriptor to attribute name on owning class."""
        self.name = name

    @overload
    def __get__(self, instance: None, owner: type[Any]) -> Parameter[T]: ...

    @overload
    def __get__(self, instance: object, owner: type[Any]) -> T: ...

    def __get__(self, instance: object | None, owner: type[Any]) -> Parameter[T] | T:
        """Retrieve parameter value from instance dictionary."""
        if instance is None:
            return self
        return cast("T", instance.__dict__.get(self.name, self.default))

    def __set__(self, instance: object, value: T) -> None:
        """Assign parameter value into instance dictionary."""
        instance.__dict__[self.name] = value


class Strategy(ABC):
    """Abstract base class for all StrategyQuant-compatible strategy snippets."""

    def __init__(
        self,
        market_data: MarketDataManager | None = None,
        trader: Trader | None = None,
    ) -> None:
        """Initialize strategy with default runtime contexts and data structures."""
        self.MarketData: MarketDataManager = market_data or MarketDataManager()
        self.Trader: Trader = trader or Trader()
        self.Indicators: Indicators = Indicators(self)
        self.Symbol: str = "EURUSD"
        self.UpdateEventType: int = UpdateEventTypes.BarOpen
        self.UpdatedChart: int = 0
        self.MultipleChartsUpdated: bool = False
        self._stopped: bool = False

        # Direct access to primary chart series
        chart0 = self.MarketData.Chart(0)
        self.Open: DataSeries = chart0.Open
        self.High: DataSeries = chart0.High
        self.Low: DataSeries = chart0.Low
        self.Close: DataSeries = chart0.Close
        self.Volume: DataSeries = chart0.Volume
        self.Time: DataSeries = chart0.Time_series

        # Daily series simulations for multi-timeframe access
        self.OpenD: DataSeries = DataSeries([1.08, 1.085, 1.09])
        self.HighD: DataSeries = DataSeries([1.095, 1.098, 1.10])
        self.LowD: DataSeries = DataSeries([1.075, 1.08, 1.082])
        self.CloseD: DataSeries = DataSeries([1.084, 1.089, 1.095])

        logger.info("FR-STRAT-INIT: strategy %s instantiated", self.__class__.__name__)

    @abstractmethod
    def Initialize(self) -> None:
        """Strategy lifecycle initialization callback."""

    @abstractmethod
    def OnBarUpdate(self) -> None:
        """Per-bar or per-tick evaluation callback."""

    def Deinitialize(self) -> None:
        """Strategy lifecycle termination callback."""
        logger.info(
            "FR-STRAT-DEINIT: default deinit called on %s",
            self.__class__.__name__,
        )

    def setUpdateEventType(self, event_type: int) -> None:
        """Set event frequency trigger (BarTick, BarOpen, BarClose)."""
        self.UpdateEventType = event_type

    def getEventType(self) -> int:
        """Return configured event type."""
        return self.UpdateEventType

    def StopStrategy(self) -> None:
        """Halt strategy execution loop."""
        self._stopped = True
        logger.info(
            "FR-STRAT-STOP: strategy %s requested halt", self.__class__.__name__
        )

    def is_stopped(self) -> bool:
        """Check if strategy has been stopped."""
        return self._stopped

    def Bars(self) -> int:
        """Return total bar count of primary chart."""
        return len(self.MarketData.Chart(0).Open)

    def TimeCurrent(self) -> int:
        """Return current market timestamp in milliseconds."""
        return self.MarketData.Chart(0).Time(0)

    def Ask(self) -> float:
        """Return primary chart current ask price."""
        return self.MarketData.Chart(0).Ask()

    def Bid(self) -> float:
        """Return primary chart current bid price."""
        return self.MarketData.Chart(0).Bid()

    def Open_price(self, chart_or_shift: int = 0, shift: int | None = None) -> float:
        """Flexible accessor matching Java Open(shift) and Open(chart, shift)."""
        if shift is None:
            return self.MarketData.Chart(0).Open.get(chart_or_shift)
        return self.MarketData.Chart(chart_or_shift).Open.get(shift)

    def High_price(self, chart_or_shift: int = 0, shift: int | None = None) -> float:
        """Flexible accessor matching Java High(shift) and High(chart, shift)."""
        if shift is None:
            return self.MarketData.Chart(0).High.get(chart_or_shift)
        return self.MarketData.Chart(chart_or_shift).High.get(shift)

    def Low_price(self, chart_or_shift: int = 0, shift: int | None = None) -> float:
        """Flexible accessor matching Java Low(shift) and Low(chart, shift)."""
        if shift is None:
            return self.MarketData.Chart(0).Low.get(chart_or_shift)
        return self.MarketData.Chart(chart_or_shift).Low.get(shift)

    def Close_price(self, chart_or_shift: int = 0, shift: int | None = None) -> float:
        """Flexible accessor matching Java Close(shift) and Close(chart, shift)."""
        if shift is None:
            return self.MarketData.Chart(0).Close.get(chart_or_shift)
        return self.MarketData.Chart(chart_or_shift).Close.get(shift)

    def Volume_val(self, chart_or_shift: int = 0, shift: int | None = None) -> float:
        """Flexible accessor matching Java Volume(shift) and Volume(chart, shift)."""
        if shift is None:
            return self.MarketData.Chart(0).Volume.get(chart_or_shift)
        return self.MarketData.Chart(chart_or_shift).Volume.get(shift)

    def getATRValue(
        self, chart_data: ChartData, atr_period: int, shift: int = 0
    ) -> float:
        """Compute ATR on specified chart and return value at shift."""
        return self.Indicators.ATR(chart_data, atr_period).Value.get(shift)
