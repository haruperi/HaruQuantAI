# Brokers Service

Broker adapters own external trading and broker-backed market-data
connections.

## Modules

- `mt5.py`: MetaTrader 5 client lifecycle, account helpers, trade bridge,
  and MT5-backed market-data loading/listing tools.
- `ctrader.py`: cTrader Open API client lifecycle, account/trade helpers,
  and cTrader-backed market-data loading/listing tools.
- `dukascopy.py`: Dukascopy feed client and Dukascopy-backed market-data
  loading/listing tools.
- `dukascopy_instruments.py`: Dukascopy instrument alias map.
- `router.py`: Active broker resolution helpers.
- `binance.py` and `yahoo.py`: Additional broker/feed adapters.

## Exports

`__init__.py` re-exports the public broker clients, factory functions, and
data wrappers lazily (via `__getattr__` and `_EXPORT_MODULES`) so optional
provider SDKs load only when used. The cTrader and MT5 result wrappers
(`MT5Api`, `CTraderTerminalInfo`, `CTraderAccountInfo`, `CTraderSymbolInfo`,
`CTraderPositionInfo`, `CTraderOrderInfo`, `CTraderDealInfo`,
`CTraderTradeResult`) are exported by name.

Eight broker-specific trade helpers are defined in **both** `mt5.py` and
`ctrader.py` (`trade`, `get_account_info`, `get_terminal_info`,
`get_symbol_info`, `get_position_info`, `get_order_info`,
`get_history_order_info`, `get_history_deal_info`). Because the lazy export
map can bind each name only once, these are intentionally **not** flattened to
the package top level; import them from the specific broker submodule (e.g.
`from app.services.brokers.mt5 import trade`) or resolve the active broker via
`router.get_broker_module()`.

## Boundary

`app/services/data` owns local file sources, normalization, caching,
transforms, generated data, and scheduler state. Broker terminal/feed
connections live here so runtime code has one ownership point for external
broker state.
