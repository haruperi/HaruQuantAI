# Canonical Trading and Data Libraries (`app/services/libs`)

This package provides the strategy-facing implementation of the MQL5-shaped
trading classes and historical data retrieval:
- `app.services.libs.trading`: Defines `Trade`, `AccountInfo`, `SymbolInfo`, `OrderInfo`, `HistoryOrderInfo`, `PositionInfo`, `DealInfo`, `TerminalInfo`, and the master `Trading` facade.
- `app.services.libs.data`: Stateless asynchronous historical bars and ticks reading (`get_historical_bars`, `get_ticks`) and boundary validation (`validate_rows`, `validate_request`).

```text
strategy -> Trading facade -> eight async classes -> TradingBackend capability
                                                     |                    |
                                                 MT5Backend        SimulationBackend
                                                     |                    |
                                              authenticated Bridge   local model/handlers
                                                     |
                                            native MT5 C* objects
```

## Calling Code

```python
from app.services.libs.trading import Trading
from app.services.brokers.contracts import TradeRequest, TradeAction, OrderType


async def run(backend):
    async with Trading(backend) as trading:
        await trading.wait_connected(timeout=60)
        account = await trading.account.AccountInfo()
        symbol = await trading.symbol.SymbolInfo("EURUSD")
        req = TradeRequest(
            action=TradeAction.DEAL,
            symbol="EURUSD",
            volume=0.01,
            order_type=OrderType.BUY,
            price=symbol.ask,
        )
        result = await trading.trade.OrderSend(req)
        return account.balance, result.retcode
```

## Architecture

- The 8 proxy classes (`AccountInfo`, `DealInfo`, `HistoryOrderInfo`, `OrderInfo`, `PositionInfo`, `SymbolInfo`, `TerminalInfo`, `Trade`) inherit from `TradingClass` (`BaseTradingClass`), using per-object locks and proxy IDs.
- Atomic snapshot queries (`AccountInfo()`, `TerminalInfo()`, `SymbolInfo()`, `PositionInfo()`, `OrderInfo()`, `HistoryOrderInfo()`, `DealInfo()`) return strongly typed dataclasses from `app.services.brokers.contracts`.
- Order operations are consolidated into canonical `OrderSend(req)` and `OrderCheck(req)` primitives.
- Historical market data helpers in `data.py` provide bounded, validated bar and tick retrieval over any `TradingBackend`.
