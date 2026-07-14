# Brokers — Version 1 Code Audit

## 1. Audit Scope

* **Domain:** `brokers`
* **Repository:** `haruperi/HaruQuant`
* **Repository snapshot:** commit `a39d26498e14772c571d75fa9a5f0e477a1dd912` on the default branch available to the audit
* **Package path:** `app/services/brokers`
* **Tests path:** `tests/unit/app/services/brokers`
* **Python files inspected:**
  * `app/services/brokers/__init__.py`
  * `app/services/brokers/router.py`
  * `app/services/brokers/mt5.py`
  * `app/services/brokers/ctrader.py`
  * `app/services/brokers/dukascopy.py`
  * `app/services/brokers/dukascopy_instruments.py`
  * `app/services/brokers/binance.py`
  * `app/services/brokers/yahoo.py`
* **Other package files inspected:** `app/services/brokers/README.md`
* **Broker test files identified:**
  * `test_binance.py`
  * `test_brokers_extra2.py`
  * `test_brokers_registry.py`
  * `test_ctrader.py`
  * `test_ctrader_trade.py`
  * `test_dukascopy.py`
  * `test_dukascopy_extra.py`
  * `test_mt5.py`
  * `test_router.py`
  * `test_yahoo.py`
* **Usage/example files identified:** `tests/usage/app/services/02_data.py`, `tests/usage/app/services/03_indicator.py`, `tests/usage/app/services/07_trading.py`, and broker-related scripts under `scripts/examples` and `scripts/benchmarks`.
* **Related packages searched:**
  * `app/services/data`, especially `gateway.py` and `_common.py`
  * `app/services/trading`
  * `app/services/execution`, especially `execution/live`
  * `app/services/risk/live`
  * `app/api/routes` and `app/api/session`
  * `app/services/utils/settings.py`
  * `data/database/sqlite/users.py`
  * repository tests, examples, configuration, and documentation
* **Search categories completed:** direct imports, package imports, symbol-name searches, class construction, module-method calls, dynamic module routing, lazy exports, settings references, API/live-session references, test usage, and source-adapter registration.
* **Excluded:** generated files, caches, virtual environments, unrelated packages, and Version 2 requirements.
* **Audit limitations:**
  * This is a static audit of the accessible GitHub snapshot. Broker credentials, terminals, live accounts, network endpoints, and external provider responses were not available.
  * Tests were inspected but not executed. Therefore, test collection, runtime compatibility, coverage, and provider integration success are unverified.
  * Repository-wide indexed searches were available, but a local clone and exhaustive AST/call-graph run were not available. Dynamic calls are labelled **Possibly used** where the runtime target depends on settings or string-based resolution.
  * The audit does not infer production deployment from source presence alone.

## 2. Executive Summary

The Version 1 brokers domain provides five provider clients:

1. MetaTrader 5 for terminal connection, account and trading information, market data, credentials, and order submission.
2. cTrader Open API for connection/authentication, market data, account/trading compatibility wrappers, and order submission.
3. Dukascopy for HTTP-scraped historical bars and ticks.
4. Binance for public klines and aggregate/recent trades.
5. Yahoo Finance for historical bars and synthetic ticks derived from the latest daily close.

It also provides a lazy package-export facade, a configured active-broker router, and a large Dukascopy instrument alias catalogue.

The strongest confirmed runtime value is in two areas:

* `app/services/data/gateway.py` registers all five clients and delegates broker-backed OHLCV and tick retrieval through `connect()`, `get_bars()`, and `get_ticks()`.
* MT5 is directly integrated into live execution, live sessions, dashboard routes, risk checks, and trading workflows. The broker-neutral trading facade dynamically uses either the MT5 or cTrader module through `get_broker_module()`.

The most important structural and correctness problems are:

* The active-broker router supports only MT5, cTrader, and a missing `app.services.simulator` target. Unknown values silently resolve to MT5.
* `ctrader.py` and `mt5.py` are very large files with connection, data, account, execution, normalization, compatibility, and tool responsibilities combined.
* cTrader compatibility code can create fallback prices and fallback order identifiers and then return a success-shaped result, weakening broker-truth guarantees.
* Yahoo “tick” data is synthetic rather than provider tick data.
* Binance, Yahoo, and Dukascopy `connect()` methods only mutate a local flag; they do not verify external connectivity.
* Return types, timeframe validation, error propagation, and empty-result behaviour differ substantially between providers.
* Broker-owned data tools overlap with the data domain’s gateway, cache, normalization, licensing, and response-envelope responsibilities.

The package structure and static call paths are well evidenced. Operational status is **high confidence for source structure**, **medium confidence for runtime call paths**, and **low confidence for live-provider behaviour**, because live credentials, terminals, networks, and test execution were unavailable.

```text
Module folders: 1 package root (0 nested) | Files: 8 Python (+1 README) | Public symbols: 131 unique declarations | Symbols with confirmed callers: 92 (70.2%, conservative static count) | Workflows found: 7
```

Counting notes:

* Public-symbol count includes public classes, functions, named methods, module constants, cTrader compatibility constants, and the three operational `__getattr__` delegation hooks.
* Package-level aliases in `app/services/brokers/__init__.py` are not double-counted against their underlying declarations.
* The confirmed-caller count is conservative. A symbol was credited only where a non-declaration reference was visible in internal code, another package, a registration map, or a test. Unresolved dynamic attribute calls were not automatically credited.

## 3. Actual Package Structure

```text
app.services.brokers
├── __init__.py
│   ├── __getattr__(name)
│   └── Lazy package exports
│       ├── BinanceClient, get_binance_client
│       ├── CTraderClient and seven cTrader information/result classes
│       ├── get_ctrader_client
│       ├── DukascopyClient, fetch, get_dukascopy_client
│       ├── load_dukascopy, dukascopy_data_list_symbols
│       ├── MT5Api, MT5Client
│       ├── get_mt5_api, get_mt5_client, get_mt5_credentials
│       ├── get_connected_mt5_client, load_mt5
│       ├── mt5_data_get_bars_with_credentials
│       ├── mt5_data_list_symbol_details_with_credentials
│       ├── mt5_data_list_symbols
│       ├── get_active_broker_name, get_broker_module
│       └── YahooClient, get_yahoo_client
├── router.py
│   ├── get_active_broker_name()
│   └── get_broker_module()
├── mt5.py
│   ├── MT5Api
│   │   ├── initialize(*args, **kwargs)
│   │   ├── shutdown()
│   │   ├── last_error()
│   │   ├── is_initialized()
│   │   └── __getattr__(name)
│   ├── MT5Client
│   │   ├── connect(path=None, login=None, password=None, server=None)
│   │   ├── is_connected()
│   │   ├── shutdown()
│   │   ├── get_bars(...)
│   │   ├── get_ticks(...)
│   │   ├── get_instance()
│   │   └── __getattr__(name)
│   ├── get_mt5_client()
│   ├── get_terminal_info()
│   ├── get_account_info()
│   ├── get_symbol_info(symbol)
│   ├── get_position_info(symbol=None, ticket=None)
│   ├── get_order_info(symbol=None, ticket=None)
│   ├── get_history_order_info(...)
│   ├── get_history_deal_info(...)
│   ├── trade(request)
│   ├── get_mt5_api()
│   ├── get_mt5_credentials(user_id=1, mt5_login=None)
│   ├── get_connected_mt5_client(user_id=1, mt5_login=None)
│   ├── load_mt5(...)
│   ├── mt5_data_get_bars_with_credentials(...)
│   ├── mt5_data_list_symbol_details_with_credentials(...)
│   └── mt5_data_list_symbols(pattern=None, request_id=None)
├── ctrader.py
│   ├── CTraderClient
│   │   ├── 14 MT5-compatible order/action constants
│   │   ├── connect(), disconnect()
│   │   ├── is_connected(), is_app_authenticated(), is_account_authorized()
│   │   ├── send_request(req, response_payload_type, timeout=10.0)
│   │   ├── subscribe_spots(symbol_name), unsubscribe_spots(symbol_name)
│   │   ├── last_error(), symbols_total(), symbol_info_tick(symbol_name)
│   │   ├── order_calc_margin(...), order_calc_profit(...)
│   │   ├── get_bars(...), get_ticks(...)
│   │   └── get_instance()
│   ├── CTraderTerminalInfo
│   ├── CTraderAccountInfo
│   ├── CTraderSymbolInfo
│   ├── CTraderPositionInfo
│   ├── CTraderOrderInfo
│   ├── CTraderDealInfo
│   ├── CTraderTradeResult
│   ├── get_ctrader_client()
│   ├── get_terminal_info()
│   ├── get_account_info()
│   ├── get_symbol_info(symbol)
│   ├── get_position_info(symbol=None, ticket=None)
│   ├── get_order_info(symbol=None, ticket=None)
│   ├── get_history_order_info(...)
│   ├── get_history_deal_info(...)
│   └── trade(request)
├── dukascopy.py
│   ├── TIME_UNIT_MONTH, TIME_UNIT_WEEK, TIME_UNIT_DAY
│   ├── TIME_UNIT_HOUR, TIME_UNIT_MIN, TIME_UNIT_SEC, TIME_UNIT_TICK
│   ├── 14 INTERVAL_* constants
│   ├── OFFER_SIDE_BID, OFFER_SIDE_ASK
│   ├── fetch(...)
│   ├── DukascopyClient
│   │   ├── connect(), disconnect(), is_connected()
│   │   ├── get_bars(...), get_ticks(...)
│   │   └── get_instance()
│   ├── get_dukascopy_client()
│   ├── load_dukascopy(...)
│   └── dukascopy_data_list_symbols(pattern=None, request_id=None)
├── dukascopy_instruments.py
│   └── INSTRUMENT_MAP
├── binance.py
│   ├── BinanceClient
│   │   ├── connect(), disconnect(), is_connected()
│   │   ├── get_bars(...), get_ticks(...)
│   │   └── get_instance()
│   └── get_binance_client()
└── yahoo.py
    ├── YahooClient
    │   ├── connect(), disconnect(), is_connected()
    │   ├── get_bars(...), get_ticks(...)
    │   └── get_instance()
    └── get_yahoo_client()
```

No nested module folders, package-local configuration files, scripts, or examples exist under `app/services/brokers` itself. Configuration is read from `app/services/utils/settings.py`; usage examples and tests live elsewhere.

## 4. Module and File Inventory

Files are arranged from package/selection infrastructure through provider implementations and provider metadata.

| Module | File | Responsibility | Key exports | Dependencies | Usage status | Value status |
| --- | --- | --- | --- | --- | --- | --- |
| Package facade | `__init__.py` | Lazily resolve selected public broker symbols so optional provider SDKs are imported only when used. | 30 exported aliases; `__getattr__` | **Standard:** `typing`, `importlib`.<br>**Third-party:** none directly.<br>**Local:** `app.services.utils.logger`; provider modules named in `_EXPORT_MODULES`. | Used | Supporting |
| Selection | `router.py` | Read `active_broker` and return an MT5-, cTrader-, or simulator-compatible module. | `get_active_broker_name`, `get_broker_module` | **Standard:** `types`, `importlib`.<br>**Third-party:** none.<br>**Local:** logger, settings, broker modules. | Used | Essential for broker-neutral trading; partial overall |
| MT5 provider | `mt5.py` | MT5 connection, delegation, market data, account/order/deal reads, order send, credential lookup, and data-tool wrappers. | `MT5Api`, `MT5Client`, 16 public functions | **Standard:** `datetime`, `typing`.<br>**Third-party:** `MetaTrader5`, `pandas`.<br>**Local:** `UserManager`, errors, common serialization, logger, settings, validators. | Used | Essential |
| cTrader provider | `ctrader.py` | cTrader socket lifecycle, protobuf authentication and requests, market data, compatibility objects, broker reads, and order mutation. | `CTraderClient`, seven wrapper classes, nine module functions | **Standard:** threading/time/context utilities, datetime, typing.<br>**Third-party:** `ctrader_open_api`, protobuf payload classes, Twisted reactor, `pandas`.<br>**Local:** settings, errors, logger. | Used for data; possibly used for live trading | Useful / Essential when cTrader is active |
| Dukascopy provider | `dukascopy.py` | Scrape Dukascopy freeserv data, normalize bars/ticks, expose singleton client and data-tool wrappers. | `fetch`, `DukascopyClient`, client getter, load/list tools, time/interval constants | **Standard:** `fnmatch`, JSON, random/string, generators, datetime, sleep.<br>**Third-party:** `requests`, `pandas`.<br>**Local:** `INSTRUMENT_MAP`, serializer, logger. | Used through data gateway | Useful |
| Dukascopy metadata | `dukascopy_instruments.py` | Static alias/name catalogue for Dukascopy instruments. | `INSTRUMENT_MAP` | **Standard/third-party/local:** none. | Used internally by symbol listing | Supporting |
| Binance provider | `binance.py` | Fetch Binance klines and public trades in the broker-client shape. | `BinanceClient`, `get_binance_client` | **Standard:** datetime, typing.<br>**Third-party:** `python-binance`, `pandas`.<br>**Local:** logger. | Used through data gateway | Useful |
| Yahoo provider | `yahoo.py` | Fetch Yahoo historical bars and create synthetic ticks from the latest close. | `YahooClient`, `get_yahoo_client` | **Standard:** datetime, typing.<br>**Third-party:** `yfinance`, `pandas`.<br>**Local:** logger; runtime import of data synthetic transform. | Used through data gateway | Useful for bars; questionable for ticks |
| Documentation | `README.md` | Describes provider modules and states that trade helper names are intentionally module-specific rather than flattened at package level. | None | None | Documentation-only | Supporting |

### Files with multiple unrelated responsibilities

* `mt5.py` combines terminal lifecycle, provider API delegation, market data, account/trading reads, order mutation, user credential persistence reads, output serialization, and agent/data-tool envelopes.
* `ctrader.py` combines event-loop management, socket callbacks, authentication state, synchronous request bridging, market data decoding, compatibility object modelling, account/trading reads, calculations, and order mutation.
* `dukascopy.py` combines low-level HTTP scraping, retry streaming, timestamp normalization, provider client lifecycle, market-data adaptation, symbol listing, and tool response construction.

## 5. Public Behaviour Inventory

### `app/services/brokers/__init__.py`

**File responsibility:** Lazy public facade for broker clients and selected data helpers.

| Symbol | Type | Responsibility | Inputs → Return | Side effects | Raises | Callers | Tests | Usage status | Value status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `__getattr__(name)` | Function / package hook | Resolve a name through `_EXPORT_MODULES`, import its module, cache the value in package globals, and return it. | `str` → `object` | Local state mutation; imports optional modules | `AttributeError`; provider import errors | Python package attribute resolution; package-level imports | `test_brokers_registry.py` | Used | Supporting |
| Names in `__all__` | Export aliases | Present 30 selected provider/router symbols from the package root without eager importing provider SDKs. | Attribute access → underlying class/function | Import side effect on first access | Underlying import/attribute errors | Tests and code importing `app.services.brokers.<name>` | `test_brokers_registry.py` | Used selectively | Supporting |

**Confirmed export fact:** low-level MT5/cTrader trading functions such as `trade`, `get_account_info`, and `get_position_info` are not flattened by package `__init__.py`; callers obtain them from the selected provider module.

### `app/services/brokers/router.py`

**File responsibility:** Convert settings into a provider module compatible with the trading facade.

| Symbol | Type | Responsibility | Inputs → Return | Side effects | Raises | Callers | Tests | Usage status | Value status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `get_active_broker_name()` | Function | Read `settings.active_broker`, with a legacy fallback to `app.core.config`, defaulting to `mt5`; lowercase the value. | None → `str` | Read-only configuration/import | Normally none; unusual import-time failures may propagate | `app/services/trading/trade.py` and other trading modules | `test_router.py` | Used | Essential |
| `get_broker_module()` | Function | Return `ctrader` when configured, dynamically import `app.services.simulator` for simulator, otherwise return `mt5`. | None → `ModuleType` | Dynamic import | `ModuleNotFoundError` for absent simulator | `app/services/trading/account_info.py`, `deal_info.py`, `history_order_info.py`, `order_info.py`, `position_info.py`, `symbol_info.py`, `terminal_info.py`, `trade.py` | `test_router.py` | Used | Essential but incomplete |

### `app/services/brokers/mt5.py`

**File responsibility:** Provider-native MT5 lifecycle, information, data, and order-send surface plus credential-backed wrappers.

#### Classes and methods

| Symbol | Type | Responsibility | Inputs → Return | Side effects | Raises | Callers | Tests | Usage status | Value status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `MT5Api` | Class | Thin state-tracking wrapper around the imported `MetaTrader5` package. | `mt5_module=mt5` → wrapper | Local state mutation | Underlying provider errors | `_MT5_API`, `get_mt5_api` | `test_mt5.py` | Possibly used | Questionable overlap |
| `MT5Api.initialize(*args, **kwargs)` | Method | Call provider initialization and remember success. | provider args → `bool` | External API call; local state mutation | Underlying provider errors | Direct wrapper users/tests | `test_mt5.py` | Test-confirmed / possibly runtime | Supporting |
| `MT5Api.shutdown()` | Method | Shut down provider and clear wrapper state. | None → `None` | External API call; local state mutation | Underlying provider errors | Direct wrapper users/tests | `test_mt5.py` | Test-confirmed / possibly runtime | Supporting |
| `MT5Api.last_error()` | Method | Return provider’s last error. | None → `Any` | Read-only external API call | Underlying provider errors | Direct wrapper users/tests | `test_mt5.py` | Test-confirmed / possibly runtime | Supporting |
| `MT5Api.is_initialized()` | Method | Return the wrapper’s local initialization flag. | None → `bool` | Read-only | None | Tests/direct users | `test_mt5.py` | Test-only evidence | Questionable |
| `MT5Api.__getattr__(name)` | Method | Delegate unknown attributes to the provider package. | `str` → `Any` | Read-only/provider-dependent | `AttributeError` | Dynamic callers | `test_mt5.py` | Possibly used | Supporting |
| `MT5Client` | Class | Own configured MT5 terminal/account connection and broker/data calls. | path/login/password/server/symbols/timeouts → client | Local state mutation; holds credentials | Constructor itself does not connect | Live execution, data gateway, trading, risk, API | `test_mt5.py` | Used | Essential |
| `MT5Client.connect(path=None, login=None, password=None, server=None)` | Method | Validate credentials, initialize terminal, login, select default Market Watch symbols, mark connected. | optional overrides → `bool` | External API call; broker session mutation; local state mutation | `ConfigurationError`, `ExternalServiceError`, provider exceptions wrapped | Data gateway, live routes/session/engine, direct clients | `test_mt5.py` | Used | Essential |
| `MT5Client.is_connected()` | Method | Query `mt5.terminal_info().connected`. | None → `bool` | Read-only external API call | Catches exceptions and returns `False` | Data gateway, client methods, live services | `test_mt5.py` | Used | Essential |
| `MT5Client.shutdown()` | Method | Call `mt5.shutdown()` and mark disconnected. | None → `None` | External API call; local state mutation | Exceptions are logged and suppressed | Credential-backed wrappers, live lifecycle | `test_mt5.py` | Used | Supporting |
| `MT5Client.get_bars(symbol, timeframe, count=100, start_pos=0, date_from=None, date_to=None)` | Method | Fetch MT5 rates and normalize to `Timestamp/Open/High/Low/Close/Volume/Spread`. | query → `DataFrame` | External API call; may auto-connect and select symbol | `ValueError` for unsupported timeframe; connection errors | Data gateway, `_load_mt5_impl`, explicit-credential wrapper, live bar monitor | `test_mt5.py`, data tests | Used | Essential |
| `MT5Client.get_ticks(symbol, count=100, start=None, end=None, flags=COPY_TICKS_ALL, as_dataframe=True)` | Method | Fetch MT5 tick range/recent ticks as DataFrame or records. | query → `DataFrame  or  list[dict]  or  None` | External API call; may auto-connect and select symbol | Connection/provider errors | Data gateway and benchmark/live consumers | `test_mt5.py` | Used | Essential |
| `MT5Client.get_instance()` | Class method | Create/return process-local singleton. | None → `MT5Client` | Local singleton mutation | Constructor/config errors are deferred until connect | `get_mt5_client` | `test_mt5.py` | Used | Supporting |
| `MT5Client.__getattr__(name)` | Method | Delegate provider attributes; auto-connect before delegated callable access. | `str` → `Any` | External API call possible; dynamic delegation | `AttributeError`, connection errors | Trading and live code using MT5-native methods/constants | `test_mt5.py` | Used dynamically | Essential compatibility surface |

#### Module functions

| Symbol | Type | Responsibility | Inputs → Return | Side effects | Raises | Callers | Tests | Usage status | Value status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `get_mt5_client()` | Function | Return shared `MT5Client`. | None → `MT5Client` | May create singleton | None until client construction | Data gateway, trading, execution, examples | `test_mt5.py`, registry | Used | Essential |
| `get_terminal_info()` | Function | Ensure connection and return `mt5.terminal_info()`. | None → `Any` | External API call; possible auto-connect | Connection/config/provider errors | Trading `TerminalInfo` via routed module | Trading/broker tests | Possibly used dynamically | Essential |
| `get_account_info()` | Function | Ensure connection and return account info. | None → `Any` | External API call; possible auto-connect | Connection/config/provider errors | Trading `AccountInfo` via routed module | Trading/broker tests | Possibly used dynamically | Essential |
| `get_symbol_info(symbol)` | Function | Ensure connection, select symbol, return provider symbol info. | `str` → `Any` | External API call; Market Watch mutation | Connection/provider errors | Trading `SymbolInfo` and risk/live code | Trading/broker tests | Used | Essential |
| `get_position_info(symbol=None, ticket=None)` | Function | Return all or filtered open positions. | filters → provider tuple/collection | Read-only external API call; possible auto-connect | Connection/provider errors | Trading/reconciliation/live code | Trading/broker tests | Used | Essential |
| `get_order_info(symbol=None, ticket=None)` | Function | Return all or filtered active orders. | filters → provider tuple/collection | Read-only external API call; possible auto-connect | Connection/provider errors | Trading/reconciliation code | Trading/broker tests | Used | Essential |
| `get_history_order_info(date_from=None, date_to=None, group=None, ticket=None)` | Function | Return historical orders by ticket or interval/group. | filters → provider collection | Read-only external API call; possible auto-connect | Connection/provider errors | Trading `HistoryOrderInfo` | Trading/broker tests | Possibly used dynamically | Useful |
| `get_history_deal_info(date_from=None, date_to=None, group=None, ticket=None)` | Function | Return historical deals by ticket or interval/group. | filters → provider collection | Read-only external API call; possible auto-connect | Connection/provider errors | Trading `DealInfo` | Trading/broker tests | Possibly used dynamically | Useful |
| `trade(request)` | Function | Submit `mt5.order_send`, reject `None` and non-success retcodes. | request dict → provider result | **Broker mutation**; external API call | `ExternalServiceError`, connection/config errors | `app/services/trading/trade.py` through router; execution code | Broker/trading tests | Used through dynamic broker route | Essential |
| `get_mt5_api()` | Function | Return `_MT5_API` wrapper singleton. | None → `MT5Api` | None | None | Direct wrapper users/tests | `test_mt5.py` | Possibly used | Questionable |
| `get_mt5_credentials(user_id=1, mt5_login=None)` | Function | Read stored MT5 credentials through `UserManager`. | identifiers → `dict  or  None` | **Persistence read** | Database errors | `get_connected_mt5_client` | `test_mt5.py` | Used internally | Supporting |
| `get_connected_mt5_client(user_id=1, mt5_login=None)` | Function | Build a non-singleton client from stored credentials, connect, return it or `None`. | identifiers → `MT5Client  or  None` | Persistence read; external API call; local client lifecycle | Most connection errors caught and converted to `None` | `_load_mt5_impl`, possible API/tool callers | `test_mt5.py` | Used internally / possibly external | Useful |
| `load_mt5(...)` | Function | Fetch normalized OHLCV using stored credentials and return a status/data envelope. | symbol/time/date/user/request → `dict` | Persistence read; external API call; terminal connect/shutdown | Converts broad exceptions to error dictionaries | Data/tool compatibility paths; package export | Data/broker tests | Possibly used dynamically | Useful but overlapping |
| `mt5_data_get_bars_with_credentials(...)` | Function | Connect with explicit credentials, fetch bars, return serialized status envelope. | credentials + query → `dict` | External API call; terminal connect/shutdown | Converts broad exceptions to error dictionaries | Package/tool consumers | Broker tests | Possibly used | Useful but sensitive/overlapping |
| `mt5_data_list_symbol_details_with_credentials(...)` | Function | Connect with explicit credentials and return JSON-safe symbol metadata. | credentials → `dict` | External API call; terminal connect/shutdown | Converts broad exceptions to error dictionaries | Package/tool consumers | Broker tests | Possibly used | Useful but overlapping |
| `mt5_data_list_symbols(pattern=None, request_id=None)` | Function | Call `mt5.symbols_get`, optionally glob-filter names, return status envelope. | pattern/request id → `dict` | Read-only external API call | Converts broad exceptions to error dictionary | Package/tool consumers | Broker tests | Possibly used | Useful but incomplete connection handling |

### `app/services/brokers/ctrader.py`

**File responsibility:** cTrader Open API connection/authentication, synchronous request bridge, data decoding, MT5-compatible information objects, and trade mutation.

#### Compatibility constants

| Symbol(s) | Type | Responsibility | Inputs → Return | Side effects | Raises | Callers | Tests | Usage status | Value status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `ORDER_FILLING_FOK`, `ORDER_FILLING_IOC`, `ORDER_TIME_GTC` | Class constants | Provide MT5-style filling/time values to higher-level trading code. | Constants | None | None | Trading code through active client/module | cTrader/trading tests | Possibly used dynamically | Supporting |
| `TRADE_ACTION_DEAL`, `TRADE_ACTION_PENDING`, `TRADE_ACTION_SLTP`, `TRADE_ACTION_MODIFY`, `TRADE_ACTION_REMOVE` | Class constants | Define action codes interpreted by `trade(request)`. | Constants | None | None | Trading request construction and `trade` branch logic | `test_ctrader_trade.py` | Used | Essential compatibility surface |
| `ORDER_TYPE_BUY`, `ORDER_TYPE_SELL`, `ORDER_TYPE_BUY_LIMIT`, `ORDER_TYPE_SELL_LIMIT`, `ORDER_TYPE_BUY_STOP`, `ORDER_TYPE_SELL_STOP` | Class constants | Define MT5-style order-type codes translated into cTrader protobuf fields. | Constants | None | None | Trading request construction and `trade` | `test_ctrader_trade.py` | Used | Essential compatibility surface |

#### `CTraderClient`

| Symbol | Type | Responsibility | Inputs → Return | Side effects | Raises | Callers | Tests | Usage status | Value status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `CTraderClient` | Class | Own Open API credentials, socket client, auth state, symbol/assets/ticks caches, callbacks, and request lifecycle. | credential/environment/account overrides → client | Local state mutation; holds credentials | Constructor mostly defers validation to connect | Data gateway; routed trading; tests | `test_ctrader.py`, `test_ctrader_trade.py` | Used for data; possible live trading | Essential when cTrader active |
| `connect()` | Method | Validate settings, start/connect client and reactor, authenticate app/account, fetch trader/symbol/asset state. | None → `bool` | External API call; starts background reactor thread; local state mutation | `ConfigurationError`, `ExternalServiceError` | Data gateway, `_ensure_connected`, direct callers | `test_ctrader.py` | Used | Essential |
| `disconnect()` | Method | Stop client and clear connection/auth flags. | None → `None` | External API call; local state mutation | Provider/reactor errors may be logged | Direct lifecycle callers/tests | `test_ctrader.py` | Test-confirmed / possibly runtime | Supporting |
| `is_connected()` | Method | Return socket connection state. | None → `bool` | Read-only | None | Data gateway, `_ensure_connected`, wrappers | `test_ctrader.py` | Used | Essential |
| `is_app_authenticated()` | Method | Return application-authentication flag. | None → `bool` | Read-only | None | Connect/tests | `test_ctrader.py` | Used internally | Supporting |
| `is_account_authorized()` | Method | Return account-authorization flag. | None → `bool` | Read-only | None | `_ensure_connected`, tests | `test_ctrader.py` | Used | Supporting |
| `send_request(req, response_payload_type, timeout=10.0)` | Method | Register a temporary callback, send protobuf request, block on matching payload/error, remove callback. | request/type/timeout → extracted payload | External API call; callback-list mutation; thread wait | `ExternalServiceError` for disconnected, timeout, provider error, no data | Most cTrader reads, calculations, data, subscriptions, trade | cTrader tests | Used | Essential |
| `subscribe_spots(symbol_name)` | Method | Request spot subscription and track symbol id. | symbol → `None` | External API call; local subscription mutation | Provider/request errors | `symbol_info_tick`, direct callers | `test_ctrader.py` | Used internally | Supporting |
| `unsubscribe_spots(symbol_name)` | Method | Request spot unsubscription and remove symbol id. | symbol → `None` | External API call; local subscription mutation | Errors are logged/suppressed | No confirmed non-test caller found | `test_ctrader.py` | Test-only evidence | Questionable |
| `last_error()` | Method | Return stored error string or `Success`. | None → `str` | Read-only | None | Direct compatibility callers/tests | `test_ctrader.py` | Test-confirmed / possibly runtime | Supporting |
| `symbols_total()` | Method | Return cached symbol count. | None → `int` | Read-only | None | Compatibility callers/tests | `test_ctrader.py` | Test-confirmed / possibly runtime | Useful |
| `symbol_info_tick(symbol_name)` | Method | Return bid/ask/last holder; subscribe if needed; use trendbar or hard-coded fallback when no tick exists. | symbol → tick object | External API call possible; local tick cache mutation | Most provider errors suppressed during fallback | Trading/live compatibility users | cTrader/trading tests | Possibly used dynamically | Useful but broker-truth risk |
| `order_calc_margin(action, symbol, volume, price)` | Method | Request expected margin and convert provider money units. | order inputs → `float  or  None` | Read-only external API call | Errors logged and converted to `None` | Risk/trading compatibility users | cTrader tests | Possibly used dynamically | Useful |
| `order_calc_profit(action, symbol, volume, price_open, price_close)` | Method | Fetch lot size and calculate directional profit locally. | order inputs → `float  or  None` | Read-only external API call | Errors logged and converted to `None` | Risk/trading compatibility users | cTrader tests | Possibly used dynamically | Useful |
| `get_bars(symbol, timeframe, count=100, start_pos=0, date_from=None, date_to=None)` | Method | Request/deserialize cTrader trendbars into canonical DataFrame. | query → `DataFrame` | External API call; may auto-connect | `ValueError` for unsupported timeframe; request failures generally become empty frame | Data gateway; private data compatibility loader | cTrader/data tests | Used | Essential |
| `get_ticks(symbol, count=100, start=None, end=None, as_dataframe=True)` | Method | Request BID/ASK tick streams, decode deltas, merge and normalize. | query → `DataFrame  or  list  or  None` | External API call; may auto-connect | Many request errors are logged and converted to empty data | Data gateway | cTrader/data tests | Used | Essential |
| `get_instance()` | Class method | Create/return singleton. | None → `CTraderClient` | Local singleton mutation | Constructor errors | `get_ctrader_client` | cTrader tests | Used | Supporting |

#### Compatibility information/result classes

| Symbol | Type | Responsibility | Inputs → Return | Side effects | Raises | Callers | Tests | Usage status | Value status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `CTraderTerminalInfo` | Class | Build MT5-like terminal fields from connection endpoint/environment. | connected/host/port/environment → object | Local state mutation | Attribute/type errors from inputs | `get_terminal_info` | `test_ctrader.py` | Used internally | Supporting |
| `CTraderAccountInfo` | Class | Convert trader/account payload to MT5-like fields with currency/leverage/balance defaults. | trader/client → object | Local state mutation | Attribute errors for malformed payload | `get_account_info` | `test_ctrader.py` | Used internally | Supporting |
| `CTraderSymbolInfo` | Class | Convert full/light symbol payload and tick state into MT5-like symbol fields; may fetch/fabricate price. | symbol/light symbol/client → object | External API call possible; local cache mutation | Most fallback errors suppressed | `get_symbol_info` | `test_ctrader.py` | Used internally | Supporting but truth-sensitive |
| `CTraderPositionInfo` | Class | Convert cTrader position payload into MT5-like position fields. | position/client → object | Local state mutation | Attribute errors for malformed payload | `get_position_info` | cTrader tests | Used internally | Supporting |
| `CTraderOrderInfo` | Class | Convert cTrader pending order payload into MT5-like order fields. | order/client → object | Local state mutation | Attribute errors for malformed payload | `get_order_info`, history order function | cTrader tests | Used internally | Supporting |
| `CTraderDealInfo` | Class | Convert cTrader deal payload into MT5-like deal fields. | deal/client → object | Local state mutation | Attribute errors for malformed payload | `get_history_deal_info` | cTrader tests | Used internally | Supporting |
| `CTraderTradeResult` | Class | Return MT5-like success retcode/comment and order/deal identifiers. | order id/deal id → object | Local state mutation | None | `trade` | `test_ctrader_trade.py` | Used internally | Essential compatibility result; truth-sensitive |

#### Module functions

| Symbol | Type | Responsibility | Inputs → Return | Side effects | Raises | Callers | Tests | Usage status | Value status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `get_ctrader_client()` | Function | Return singleton client. | None → `CTraderClient` | May create singleton | None until connect | Data gateway, private data loader | cTrader/data tests, registry | Used | Essential |
| `get_terminal_info()` | Function | Ensure connection and build terminal wrapper. | None → `CTraderTerminalInfo  or  None` | External API call possible | Connection/auth errors | Trading `TerminalInfo` via router | cTrader/trading tests | Possibly used dynamically | Essential |
| `get_account_info()` | Function | Ensure connection and convert cached trader info. | None → `CTraderAccountInfo  or  None` | External API call possible | Connection/auth errors | Trading `AccountInfo` via router | cTrader/trading tests | Possibly used dynamically | Essential |
| `get_symbol_info(symbol)` | Function | Request full symbol payload and build wrapper. | symbol → `CTraderSymbolInfo  or  None` | Read-only external API call | Connection errors; request errors converted to `None` | Trading `SymbolInfo` via router | cTrader/trading tests | Possibly used dynamically | Essential |
| `get_position_info(symbol=None, ticket=None)` | Function | Reconcile and filter open positions. | filters → list | Read-only external API call | Connection errors; request errors become `[]` | Trading/reconciliation via router | cTrader/trading tests | Possibly used dynamically | Essential |
| `get_order_info(symbol=None, ticket=None)` | Function | Reconcile and filter pending orders. | filters → list | Read-only external API call | Connection errors; request errors become `[]` | Trading/reconciliation via router | cTrader/trading tests | Possibly used dynamically | Essential |
| `get_history_order_info(date_from=None, date_to=None, group=None, ticket=None)` | Function | Request order history and filter by ticket/group. | filters → list | Read-only external API call | Connection errors; request errors become `[]` | Trading history facade via router | cTrader tests | Possibly used dynamically | Useful |
| `get_history_deal_info(date_from=None, date_to=None, group=None, ticket=None)` | Function | Request deal history and filter by ticket/group. | filters → list | Read-only external API call | Connection errors; request errors become `[]` | Trading deal facade via router | cTrader tests | Possibly used dynamically | Useful |
| `trade(request)` | Function | Translate MT5-style deal/pending/SLTP/modify/remove requests into cTrader protobuf mutations and return compatibility result. | request dict → `CTraderTradeResult` | **Broker mutation**; external API call | `ExternalServiceError`; key errors are wrapped | `app/services/trading/trade.py` when cTrader active | `test_ctrader_trade.py` | Possibly used dynamically | Essential when cTrader active |

**Private-but-cross-domain behaviour:** `_load_ctrader_impl(...)` is private by name but imported by `app/services/data/_common.py`. It is not counted as public, but it is a real cross-domain dependency and a boundary leak.

### `app/services/brokers/dukascopy.py`

**File responsibility:** Low-level Dukascopy HTTP data retrieval plus provider-client and data-tool adaptation.

#### Constants

| Symbol(s) | Type | Responsibility | Inputs → Return | Side effects | Raises | Callers | Tests | Usage status | Value status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `TIME_UNIT_MONTH`, `TIME_UNIT_WEEK`, `TIME_UNIT_DAY`, `TIME_UNIT_HOUR`, `TIME_UNIT_MIN`, `TIME_UNIT_SEC`, `TIME_UNIT_TICK` | Constants | Name supported time units for interval decoding and DataFrame schema selection. | Constants | None | None | `_interval_units`, resampling/schema helpers | Dukascopy tests | Used internally | Supporting |
| `INTERVAL_MONTH_1`, `INTERVAL_WEEK_1`, `INTERVAL_DAY_1`, `INTERVAL_HOUR_4`, `INTERVAL_HOUR_1`, `INTERVAL_MIN_30`, `INTERVAL_MIN_15`, `INTERVAL_MIN_10`, `INTERVAL_MIN_5`, `INTERVAL_MIN_1`, `INTERVAL_SEC_30`, `INTERVAL_SEC_10`, `INTERVAL_SEC_1`, `INTERVAL_TICK` | Constants | Construct provider interval strings and populate interval-to-unit registry. | Constants | None | None | `_interval_units`, fetch/stream/tests | Dukascopy tests | Used internally | Supporting |
| `OFFER_SIDE_BID`, `OFFER_SIDE_ASK` | Constants | Name provider side codes. | Constants | None | None | Tests/direct callers; production methods use literal `"B"` rather than the constants | Dukascopy tests | Test/direct-use evidence | Questionable |

#### Functions and client

| Symbol | Type | Responsibility | Inputs → Return | Side effects | Raises | Callers | Tests | Usage status | Value status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `fetch(instrument, interval, offer_side, start, end, max_retries=7, limit=30000)` | Function | Stream Dukascopy freeserv JSONP data, build timestamp-indexed DataFrame. | query → `DataFrame` | External HTTP API call; sleeps/retries | JSON, HTTP, interval, retry exhaustion errors | `DukascopyClient.get_bars`, `get_ticks`, direct tests | Dukascopy tests | Used | Essential internal capability |
| `DukascopyClient` | Class | Present Dukascopy data in common client shape and manage a local connection flag. | optional username/password → client | Local state mutation; holds optional credentials | None in constructor | Data gateway | Dukascopy tests | Used | Useful |
| `connect()` | Method | Set local `_connected=True`; no remote probe/authentication. | None → `bool` | Local state mutation | None | Data gateway/client methods | Dukascopy tests | Used | Supporting but weak readiness signal |
| `disconnect()` | Method | Clear local connection flag. | None → `None` | Local state mutation | None | Direct callers/tests | Dukascopy tests | Test-confirmed / possibly runtime | Supporting |
| `is_connected()` | Method | Return local connection flag. | None → `bool` | Read-only | None | Data gateway/client methods | Dukascopy tests | Used | Supporting |
| `get_bars(symbol, timeframe, count=100, start_pos=0, date_from=None, date_to=None)` | Method | Normalize six-character FX symbols, fetch bid bars, map to canonical DataFrame, assign fixed spread. | query → `DataFrame` | External HTTP API call; may auto-connect | `ValueError` for unsupported timeframe; fetch errors become empty frame | Data gateway, load wrappers | Dukascopy/data tests | Used | Useful |
| `get_ticks(symbol, count=100, start=None, end=None, as_dataframe=True)` | Method | Fetch provider tick rows and normalize bid/ask/last/volume/spread. | query → `DataFrame  or  list  or  None` | External HTTP API call; may auto-connect | Fetch errors become `None` | Data gateway | Dukascopy/data tests | Used | Useful |
| `get_instance()` | Class method | Create/return singleton. | None → client | Local singleton mutation | None | `get_dukascopy_client` | Dukascopy tests | Used | Supporting |
| `get_dukascopy_client()` | Function | Return singleton client. | None → client | May create singleton | None | Data gateway and load wrappers | Dukascopy/data tests, registry | Used | Essential integration surface |
| `load_dukascopy(...)` | Function | Fetch bars and return serialized status/data dictionary. The `cache` argument is discarded. | query → `dict` | External HTTP API call | Broad errors converted to error dictionary | Package/tool consumers | Dukascopy tests | Possibly used dynamically | Useful but overlapping |
| `dukascopy_data_list_symbols(pattern=None, request_id=None)` | Function | Return sorted keys and values from `INSTRUMENT_MAP`, optionally filtered. `request_id` is discarded. | pattern → `dict` | Read-only | None | Package/tool consumers | Dukascopy tests | Possibly used dynamically | Useful |

### `app/services/brokers/dukascopy_instruments.py`

**File responsibility:** Large static instrument alias catalogue.

| Symbol | Type | Responsibility | Inputs → Return | Side effects | Raises | Callers | Tests | Usage status | Value status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `INSTRUMENT_MAP` | Constant mapping | Map alternate/provider instrument names and support symbol discovery. | Mapping lookup | None | `KeyError` only for direct indexed access | `dukascopy_data_list_symbols`; imported by `dukascopy.py` | Dukascopy tests | Used internally | Supporting |

### `app/services/brokers/binance.py`

**File responsibility:** Binance public market data in the common broker-client shape.

| Symbol | Type | Responsibility | Inputs → Return | Side effects | Raises | Callers | Tests | Usage status | Value status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `BinanceClient` | Class | Store optional API credentials and provide klines/trades through a singleton-compatible client. | key/secret → client | Local state mutation; holds credentials | None in constructor | Data gateway | `test_binance.py` | Used | Useful |
| `connect()` | Method | Set local `_connected=True`; no remote ping/authentication. | None → `bool` | Local state mutation | None | Data gateway/client methods | `test_binance.py` | Used | Supporting but weak readiness signal |
| `disconnect()` | Method | Clear local flag. | None → `None` | Local state mutation | None | Tests/direct lifecycle users | `test_binance.py` | Test-only evidence | Supporting |
| `is_connected()` | Method | Return local flag. | None → `bool` | Read-only | None | Data gateway/client methods | `test_binance.py` | Used | Supporting |
| `get_bars(symbol, timeframe, count=100, start_pos=0, date_from=None, date_to=None)` | Method | Fetch klines, normalize compact symbol to a Binance quote suffix, return canonical DataFrame. | query → `DataFrame` | External API call; creates provider client per call | Provider/network errors propagate; unsupported timeframe silently becomes H1 | Data gateway | Binance/data tests | Used | Useful |
| `get_ticks(symbol, count=100, start=None, end=None, as_dataframe=True)` | Method | Fetch aggregate or recent trades and represent trade price as bid/ask/last with zero spread. | query → `DataFrame  or  list  or  None` | External API call; creates provider client per call | Provider/network errors propagate | Data gateway | Binance/data tests | Used | Useful |
| `get_instance()` | Class method | Create/return singleton. | None → client | Local singleton mutation | None | `get_binance_client` | `test_binance.py` | Used | Supporting |
| `get_binance_client()` | Function | Return singleton client. | None → client | May create singleton | None | Data gateway | Binance/data tests, registry | Used | Essential integration surface |

### `app/services/brokers/yahoo.py`

**File responsibility:** Yahoo historical bars and synthetic tick generation in the common broker-client shape.

| Symbol | Type | Responsibility | Inputs → Return | Side effects | Raises | Callers | Tests | Usage status | Value status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `YahooClient` | Class | Provide yfinance historical bars and locally generated ticks. | optional api key → client | Local state mutation | None in constructor | Data gateway | `test_yahoo.py` | Used | Useful for bars |
| `connect()` | Method | Set local `_connected=True`; no remote probe. | None → `bool` | Local state mutation | None | Data gateway/client methods | `test_yahoo.py` | Used | Supporting but weak readiness signal |
| `disconnect()` | Method | Clear local flag. | None → `None` | Local state mutation | None | Tests/direct lifecycle users | `test_yahoo.py` | Test-only evidence | Supporting |
| `is_connected()` | Method | Return local flag. | None → `bool` | Read-only | None | Data gateway/client methods | `test_yahoo.py` | Used | Supporting |
| `get_bars(symbol, timeframe, count=100, start_pos=0, date_from=None, date_to=None)` | Method | Call `yfinance.Ticker.history`, normalize timestamp/OHLCV, add zero spread. | query → `DataFrame` | External API call | Provider/network errors propagate; unsupported timeframe silently becomes H1 | Data gateway | Yahoo/data tests | Used | Useful |
| `get_ticks(symbol, count=100, start=None, end=None, as_dataframe=True)` | Method | Get latest daily close and call `app.services.data.transforms.generate_synthetic_ticks`; ignore `end`. | query → `DataFrame  or  list  or  None` | External API call plus synthetic data generation | Provider/transform errors propagate | Data gateway | Yahoo/data tests | Used | Questionable as provider tick capability |
| `get_instance()` | Class method | Create/return singleton. | None → client | Local singleton mutation | None | `get_yahoo_client` | `test_yahoo.py` | Used | Supporting |
| `get_yahoo_client()` | Function | Return singleton client. | None → client | May create singleton | None | Data gateway | Yahoo/data tests, registry | Used | Essential integration surface |

## 6. Actual Workflows

### `V1-WF-BROKERS-001` — Lazy Package Export Resolution

* **Scope:** Internal
* **Trigger:** A caller accesses a name such as `app.services.brokers.MT5Client`.
* **Input boundary:** Attribute name.
* **Functions and methods used:** `app.services.brokers.__getattr__` → `_EXPORT_MODULES` → `import_module` → provider symbol.
* **Files involved:** `app/services/brokers/__init__.py`, selected provider module.
* **External dependencies:** Optional provider SDK is imported only for the requested symbol.
* **Output boundary:** Underlying class/function, cached in package globals.
* **Failure behaviour:** Unknown name raises `AttributeError`; missing optional dependency or provider import error propagates.
* **Operational status:** **Working** statically; registry tests cover valid/invalid resolution.
* **Evidence:** `app/services/brokers/__init__.py::__getattr__`; `tests/unit/app/services/brokers/test_brokers_registry.py`.

```text
Package attribute access
→ __getattr__(name)
→ _EXPORT_MODULES[name]
→ import provider module
→ cache resolved object
→ return public symbol
```

### `V1-WF-BROKERS-002` — Active Trading Broker Resolution

* **Scope:** Cross-domain
* **Trigger:** Trading information or order code calls `get_broker_module()`.
* **Input boundary:** `settings.active_broker` from the utils/settings domain.
* **Functions and methods used:** `get_active_broker_name()` → `get_broker_module()`.
* **Files involved:** `app/services/brokers/router.py`, `app/services/utils/settings.py`, MT5/cTrader modules, `app/services/trading/*`.
* **External dependencies:** Selected provider SDK when its module is imported/used.
* **Output boundary:** Module exposing `get_*_info` and `trade` functions to the trading domain.
* **Failure behaviour:** `ctrader` returns cTrader; `simulator` tries to import absent `app.services.simulator`; every other value returns MT5 without validation.
* **Operational status:** **Partial**.
* **Evidence:** `router.py::get_broker_module`; `settings.py::active_broker`; imports in `app/services/trading/trade.py`, account/order/position/deal/symbol/terminal facades.

```text
Trading domain request
→ get_active_broker_name()
→ active == "ctrader" ? ctrader
→ active == "simulator" ? dynamic import app.services.simulator
→ otherwise mt5
→ trading facade invokes module function
```

### `V1-WF-BROKERS-003` — Unified Broker-Backed Market Data

* **Scope:** Cross-domain
* **Trigger:** Data gateway receives source `mt5`, `ctrader`, `dukascopy`, `binance`, or `yahoo`.
* **Input boundary:** Source, symbol, timeframe/date range or tick range, request context.
* **Functions and methods used:** data gateway registry → provider `get_*_client()` → `is_connected()` → `connect()` → `get_bars()` or `get_ticks()` → gateway normalization/validation/cache.
* **Files involved:** `app/services/data/gateway.py`; all five client modules.
* **External dependencies:** MT5 terminal, cTrader Open API, Dukascopy HTTP endpoint, Binance API, Yahoo Finance; data gateway persistence/cache/licensing.
* **Output boundary:** Canonical OHLCV/tick records returned to data consumers.
* **Failure behaviour:** Gateway circuit-breaker and provider-specific error behaviour apply. Providers differ: exceptions, empty DataFrames, `None`, or generated data.
* **Operational status:** **Working statically; live-provider execution unverified**.
* **Evidence:** `gateway.py::_mt5_client`, `_ctrader_client`, `_dukascopy_client`, `_binance_client`, `_yahoo_client`; `_BROKER_SPECS`; `ADAPTER_REGISTRY`; `BrokerAdapter.get_market_dataframe/get_tick_dataframe`.

```text
Data request
→ ADAPTER_REGISTRY[source]
→ BrokerAdapter._connect()
→ provider singleton client
→ client.get_bars() or client.get_ticks()
→ gateway canonical normalization
→ cache/validated records
→ data consumer
```

### `V1-WF-BROKERS-004` — Stored-Credential MT5 Data Load

* **Scope:** Cross-domain
* **Trigger:** `load_mt5` or a compatible tool requests MT5 OHLCV for a user/account.
* **Input boundary:** Symbol/timeframe/date/count plus `user_id` and optional login.
* **Functions and methods used:** `load_mt5` → `_load_mt5_impl` → `get_connected_mt5_client` → `get_mt5_credentials` → `UserManager` → `MT5Client.connect` → `MT5Client.get_bars` → `prepare_ohlcv_data` → serialization → shutdown.
* **Files involved:** `app/services/brokers/mt5.py`, `data/database/sqlite/users.py`, utils validators/common.
* **External dependencies:** Local user database and MT5 terminal/account.
* **Output boundary:** Dictionary containing status, metadata, and serialized bars.
* **Failure behaviour:** Missing credentials/client or empty bars returns an error result; broad exceptions are converted to an error dictionary.
* **Operational status:** **Unverified** with live credentials.
* **Evidence:** `mt5.py::get_mt5_credentials`, `get_connected_mt5_client`, `_load_mt5_impl`, `load_mt5`.

```text
Tool/data request
→ load_mt5()
→ read stored credentials
→ create MT5Client
→ connect/login
→ get_bars()
→ normalize/serialize
→ shutdown
→ status envelope
```

### `V1-WF-BROKERS-005` — MT5 Live Session Injection

* **Scope:** Cross-domain
* **Trigger:** API/live-session code creates or starts a live trading session.
* **Input boundary:** Connected `MT5Client`, session id, database manager, strategy/session configuration.
* **Functions and methods used:** MT5 client construction/connection outside or before session → `LiveTradingSession` receives client → constructs `MultiStrategyEngine(config, client=mt5_client)` → engine reads/broker operations through injected client.
* **Files involved:** `app/services/brokers/mt5.py`, `app/services/execution/live/session.py`, `engine.py`, bar/position managers, live API routes.
* **External dependencies:** MT5 terminal/account, database, engine/runtime.
* **Output boundary:** Running live engine with broker data and mutations.
* **Failure behaviour:** Client/engine initialization failures stop session startup; runtime failures update session status to error.
* **Operational status:** **Working call path; live execution unverified**.
* **Evidence:** `execution/live/session.py::LiveTradingSession.__init__/start`; direct `MT5Client` references in live engine, bar monitor, position manager, risk live code, and API routes.

```text
Live API/session request
→ obtain connected MT5Client
→ LiveTradingSession(..., mt5_client, ...)
→ MultiStrategyEngine(client=mt5_client)
→ broker reads/order operations
→ live session outcome
```

### `V1-WF-BROKERS-006` — Broker-Neutral Trade Submission and Reconciliation

* **Scope:** Cross-domain
* **Trigger:** `app.services.trading.Trade` submits a validated trading request.
* **Input boundary:** MT5-style request dictionary after trading-domain validation/readiness/idempotency.
* **Functions and methods used:** trading `Trade._send_request` → `get_active_broker_name` → `get_broker_module` → selected module `get_position_info/get_order_info` for reconciliation → selected module `trade(request)` → normalized result/persistence.
* **Files involved:** broker router, `mt5.py` or `ctrader.py`, `app/services/trading/trade.py` and trading support modules.
* **External dependencies:** Selected live broker, trading store/reconciliation/readiness services.
* **Output boundary:** Normalized trading result and local execution/order/position state.
* **Failure behaviour:** Readiness/validation/rate-limit failures block before broker call; broker timeout is treated as unknown outcome and forces reconciliation; provider exceptions become failure results.
* **Operational status:** **Working static path for MT5/cTrader; live behaviour unverified**.
* **Evidence:** `app/services/trading/trade.py::_send_request`, especially dynamic calls to `broker.get_position_info`, `broker.get_order_info`, and `broker.trade`.

```text
Trading request
→ active broker resolution
→ startup broker reconciliation
→ readiness and validation
→ broker.trade(sanitized_request)
→ result normalization
→ local execution/order/position persistence
```

### `V1-WF-BROKERS-007` — cTrader Connect, Authenticate, Request, and Translate

* **Scope:** Internal with cross-domain output
* **Trigger:** Data gateway or trading facade requests cTrader data/account/trade behaviour.
* **Input boundary:** Settings credentials/account/environment plus protobuf request inputs.
* **Functions and methods used:** `get_ctrader_client` → `connect` → socket callbacks (`_on_connected`, `_on_message`, auth handlers) → `send_request` → provider-specific method/module function → compatibility object or DataFrame/result.
* **Files involved:** `app/services/brokers/ctrader.py`, settings, caller in data/trading.
* **External dependencies:** cTrader Open API, Twisted reactor, protobuf messages.
* **Output boundary:** DataFrame, account/info wrapper, list of wrappers, or `CTraderTradeResult`.
* **Failure behaviour:** Connection/auth failures raise; many read/data functions catch errors and return empty/`None`; trade errors raise `ExternalServiceError`.
* **Operational status:** **Unverified** against a real account.
* **Evidence:** `CTraderClient.connect`, callback handlers, `send_request`, data/info/trade functions.

```text
cTrader request
→ singleton client
→ connect socket
→ application authentication
→ account authorization
→ symbol/asset/trader cache
→ send_request()
→ decode/translate response
→ data/info/trade output
```

## 7. Usage and Caller Map

| Public symbol or family | Called from | Call type | Runtime or test | Evidence |
| --- | --- | --- | --- | --- |
| Package lazy exports | Code importing `app.services.brokers.<export>` | Dynamic `__getattr__` import and cache | Runtime-capable; registry test confirmed | `__init__.py::_EXPORT_MODULES`; `test_brokers_registry.py` |
| `get_active_broker_name`, `get_broker_module` | `app/services/trading/*` | Direct import; dynamic module selection | Runtime source | `trading/trade.py`, account/order/position/deal/symbol/terminal modules |
| `MT5Client` | Live engine/session/bar monitor/position manager, risk live checks, API live/dashboard routes | Direct class import, injection, construction, type reference | Runtime source | Repository-wide `MT5Client` search; `execution/live/session.py` |
| `get_mt5_client` | Data gateway, trading, execution, symbol info, examples | Direct helper call | Runtime source | `data/gateway.py::_mt5_client`; trading/execution files |
| `MT5Client.get_bars/get_ticks` | Data `BrokerAdapter`; live monitor/benchmarks | Method call | Runtime source | `data/gateway.py::BrokerAdapter`; live files |
| MT5 information functions | Trading facades through selected module | Dynamic module attribute call | Runtime source, configuration-dependent | `trading/*`; `router.py` |
| `mt5.trade` | `app/services/trading/trade.py` selected module | Dynamic module call in executor | Runtime source, configuration-dependent | `Trade._send_request` |
| MT5 credential/data wrappers | Internal helpers, package exports, tests, possible tool registry | Direct and dynamic | Mixed / uncertain | `mt5.py`; package `__init__.py`; broker tests |
| `CTraderClient/get_ctrader_client` | Data gateway; cTrader internal wrappers | Direct helper call | Runtime source | `data/gateway.py::_ctrader_client` |
| `CTraderClient.get_bars/get_ticks` | Data gateway; private data compatibility loader | Method call | Runtime source | `BrokerAdapter`; `data/_common.py` private loader import |
| cTrader information/trade functions | Trading facades through router when active broker is `ctrader` | Dynamic module attribute call | Runtime source, configuration-dependent | `router.py`; `trading/trade.py` and facades |
| cTrader wrapper classes | cTrader module functions | Direct instantiation | Internal runtime | `get_*_info` implementations |
| `DukascopyClient/get_dukascopy_client` | Data gateway; load wrapper | Direct helper call | Runtime source | `data/gateway.py::_dukascopy_client` |
| `DukascopyClient.get_bars/get_ticks` | Data gateway, load wrapper | Method call | Runtime source | `BrokerAdapter`; `load_dukascopy` |
| `fetch` | Dukascopy client data methods; tests/direct users | Direct call | Internal runtime | `dukascopy.py::get_bars/get_ticks` |
| `INSTRUMENT_MAP` | Dukascopy symbol-list function | Direct import/read | Internal runtime | `dukascopy.py::dukascopy_data_list_symbols` |
| `BinanceClient/get_binance_client` | Data gateway | Direct helper call | Runtime source | `data/gateway.py::_binance_client` |
| `BinanceClient.get_bars/get_ticks` | Data gateway | Method call | Runtime source | `BrokerAdapter` |
| `YahooClient/get_yahoo_client` | Data gateway | Direct helper call | Runtime source | `data/gateway.py::_yahoo_client` |
| `YahooClient.get_bars/get_ticks` | Data gateway | Method call | Runtime source | `BrokerAdapter` |
| Provider `disconnect` methods | Primarily provider unit tests; no strong production shutdown map for data singletons | Direct call | Test or uncertain | Provider tests; no confirmed gateway disconnect |
| `CTraderClient.unsubscribe_spots` | Unit tests/direct API only | Direct call | Test-only evidence | `test_ctrader.py`; no production caller found |

## 8. Cross-Domain Surface

### Outbound — this domain depends on

| Depends on (domain/package) | Symbols or capabilities consumed | Where used in this domain | Evidence |
| --- | --- | --- | --- |
| Utils/settings | MT5/cTrader credentials, terminal path, environment, account id, active broker | `mt5.py`, `ctrader.py`, `router.py` | Imports and settings field access |
| Utils/errors | `ConfigurationError`, `ExternalServiceError` | MT5/cTrader connection and trade failures | Provider modules |
| Utils/logger | Structured/logging calls | Every broker module | Direct imports |
| Utils/common/validators | `bars_to_records`, `prepare_ohlcv_data` | MT5/Dukascopy tool wrappers | Direct imports |
| User database | `UserManager.get_mt5_credentials*` | `mt5.py::get_mt5_credentials` | Direct import/call |
| Data transforms | `generate_synthetic_ticks` | `YahooClient.get_ticks` | Runtime import |
| MetaTrader5 SDK/terminal | Initialize/login/info/rates/ticks/orders | `mt5.py` | Direct SDK calls |
| cTrader Open API / Twisted | Socket client, protobuf requests/responses, reactor | `ctrader.py` | Direct imports/calls |
| Requests / Dukascopy endpoint | HTTP JSONP feed | `dukascopy.py::_fetch` | `requests.get` |
| python-binance | Klines and trades | `binance.py` | `BinanceAPIClient` |
| yfinance | Historical bars/latest daily close | `yahoo.py` | `yf.Ticker.history` |
| pandas | Provider normalization | All provider data modules | Direct imports |

### Inbound — other domains depend on this domain

| Consuming domain/package | Symbols consumed from this domain | Purpose | Evidence |
| --- | --- | --- | --- |
| Data gateway | All five `get_*_client` helpers and client `connect/is_connected/get_bars/get_ticks` shape | Unified broker-backed OHLCV/tick source adapters | `app/services/data/gateway.py` broker factories, specs, registry |
| Legacy data common | Private `_load_ctrader_impl` and provider loaders | Source-specific OHLCV compatibility | `app/services/data/_common.py` imports/search |
| Trading domain | Router plus provider `get_*_info` and `trade` module functions | Broker-neutral information and order operations | `app/services/trading/*` |
| Live execution | `MT5Client`, delegated native MT5 methods | Live engine, bars, positions, session control | `app/services/execution/live/*` |
| Risk live | `MT5Client` and broker information | Safety checks and portfolio state | `app/services/risk/live/*` |
| API routes/session | `MT5Client`, provider/data helpers | Live-session creation, broker dashboard, data endpoints | `app/api/routes/*`, `app/api/session/*` |
| Simulation/optimization/research/edge callers | Broker data clients or data loaders | Data preparation and strategy workflows | Repository-wide broker import results |
| Tests/examples | Provider classes, constants, helpers, router | Unit, usage, benchmark, example coverage | Broker tests and `tests/usage`/scripts |

## 9. Duplicate and Overlapping Behaviour

| Item A | Item B | Overlap | Evidence | Risk |
| --- | --- | --- | --- | --- |
| `MT5Api` | `MT5Client.__getattr__` and module-level MT5 wrappers | Both delegate to the same `MetaTrader5` package and maintain/assume connection state. | `mt5.py::MT5Api`, `MT5Client`, `_MT5_API`, wrapper functions | Divergent connection-state concepts and unnecessary public surface |
| Five provider client classes | Each other | Repeat singleton, `connect/disconnect/is_connected/get_bars/get_ticks` patterns. | Provider class definitions | Behaviour looks uniform but semantics differ materially |
| MT5 module information/trade functions | cTrader module information/trade functions | Same MT5-shaped names for routed trading. | Both modules’ `__all__`; broker README | Useful compatibility, but inconsistent errors/types can leak through same interface |
| Broker `load_mt5/load_dukascopy` and listing tools | Data gateway/data common | Both own data retrieval, normalization, serialization, and source selection concerns. | Broker wrappers versus `app/services/data/gateway.py` | Bypassed licensing/cache/circuit-breaker/standard response behaviour |
| `_load_ctrader_impl` | Data gateway cTrader adapter | Two paths load cTrader bars. | Private function imported by data `_common`; gateway `BrokerAdapter` | Private cross-domain coupling and divergent behaviour |
| `DukascopyClient.get_bars/get_ticks` | `fetch` | Client wraps the same low-level scraper and adds normalization/error conversion. | `dukascopy.py` call chain | Large mixed file and inconsistent failure visibility |
| Yahoo tick path | Data domain synthetic transform | Yahoo adapter delegates actual tick construction to synthetic generator. | `YahooClient.get_ticks` runtime import | Provider attribution can be confused with generated data |
| cTrader tick/symbol fallbacks | Synthetic/default values inside cTrader client/wrappers | Multiple places fabricate prices when live ticks are absent. | `symbol_info_tick`, `CTraderSymbolInfo` | Fake values may appear broker-derived |

## 10. Unused or Questionable Items

| Item | Finding | Searches performed | Confidence | Evidence |
| --- | --- | --- | --- | --- |
| `CTraderClient.unsubscribe_spots` | No non-test call site found. | Symbol search, method-call search, callback/subscription inspection, tests | Medium | Defined in `ctrader.py`; test coverage exists; no production caller found |
| `MT5Api.is_initialized` | Only the wrapper’s own local flag; no confirmed production consumer found. | Symbol search, MT5 wrapper/client callers, tests | Medium | `mt5.py::MT5Api`; separate from actual `MT5Client.is_connected` |
| `get_mt5_api` / `MT5Api` | Adds a second provider wrapper beside `MT5Client`; real production value is unclear. | Import/caller searches, package exports, tests | Medium | Package export and tests; no strong runtime workflow identified |
| `OFFER_SIDE_BID`, `OFFER_SIDE_ASK` | Public constants exist, but provider methods pass literal `"B"`; ask-side production use was not found. | Constant search, fetch callers, tests | Medium | `dukascopy.py` declarations and `get_bars/get_ticks` literals |
| Provider `disconnect()` for Binance/Yahoo/Dukascopy | Gateway obtains process singletons but does not expose a confirmed shutdown workflow. | Data gateway call path, provider lifecycle search, tests | Medium | Gateway calls connect/data; tests call disconnect |
| `cache` in `load_dukascopy` and `_load_dukascopy_impl` | Argument is explicitly discarded. | Function body, call/search | High | `del cache` in both functions |
| `request_id` in `dukascopy_data_list_symbols` | Argument is explicitly discarded and not returned. | Function body | High | `del request_id` |
| `end` in `YahooClient.get_ticks` | Parameter is marked unused and synthetic generation uses count/start only. | Function signature/body | High | `end: ...  # noqa: ARG002`; no use in body |
| `start_pos` in several date-range paths | Semantics differ by provider and may be ignored when explicit dates are supplied. | Provider method comparison | Medium | Provider-specific `get_bars` bodies |
| `mt5_data_*` wrapper functions | Public/package-exported and tested, but direct production callers were not conclusively identified; dynamic tool registration remains possible. | Name/import searches, package export map, tests, API/tool searches | Medium | `mt5.py`, package `__init__`, broker tests |
| `dukascopy_data_list_symbols` aliases | Lists map keys and values, but those aliases are not resolved by `get_bars/get_ticks`; advertised names may not all be fetchable. | Map import/use search and client symbol normalization | High | Symbol list uses `INSTRUMENT_MAP`; fetch methods only split six-character FX symbols |

No item is labelled dead code. The items above are **Questionable**, **Test-only**, or **Possibly used** because dynamic consumers and external direct imports cannot be completely ruled out.

### Confidence scale

| Confidence | Meaning |
| --- | --- |
| **High** | Relevant static usage categories were completed and the finding is explicit in code. |
| **Medium** | Static searches were completed, but dynamic/direct external usage cannot be fully excluded. |
| **Low** | Evidence was incomplete or inaccessible. |

## 11. Incomplete or Disconnected Workflows

| Workflow / capability | Missing connection | Current impact | Evidence |
| --- | --- | --- | --- |
| Simulator selection | Router imports `app.services.simulator`, but no such package/module exists in the inspected tree. | Configuring `active_broker="simulator"` can fail at import time; router test may fail collection in a clean checkout. | `router.py::get_broker_module`; `test_router.py` |
| Active routing of Dukascopy/Binance/Yahoo | Router has no cases for these names and defaults every unknown value to MT5. | These providers work only through direct/data-gateway use, not the broker-neutral trading route. | `router.py`; data gateway registry |
| cTrader private data loader | Data domain imports `_load_ctrader_impl`, which is intentionally private and absent from cTrader `__all__`. | Cross-domain dependency is hidden from the public contract and may diverge from the gateway. | `ctrader.py::_load_ctrader_impl`; `data/_common.py` |
| Yahoo tick workflow | No real Yahoo tick endpoint is used. | Results are synthetic despite passing through the Yahoo source adapter. | `YahooClient.get_ticks` |
| cTrader live-price fallback | Missing live tick can result in trendbar-derived or hard-coded prices. | Readiness/risk/trading consumers may receive values not representing a current broker quote. | `symbol_info_tick`; `CTraderSymbolInfo` |
| cTrader result identity | Missing response order id can fall back to `12345`; result always uses success retcode `10009`. | A response missing expected identifiers may look successful. | `ctrader.py::trade`; `CTraderTradeResult` |
| MT5 symbol listing | `mt5_data_list_symbols` calls `mt5.symbols_get()` without `_ensure_connected()`. | A disconnected terminal can produce empty/error output unlike other MT5 helpers. | `mt5.py::mt5_data_list_symbols` |
| Broker-owned data wrappers | Direct wrappers do not pass through data gateway licensing, persistent circuit breaker, cache, or canonical tool response path. | Same source can behave differently depending on entry point. | Broker load functions versus `data/gateway.py` |

## 12. Structural Problems

| ID | Problem | Location | Impact | Evidence |
| --- | --- | --- | --- | --- |
| `V1-ISSUE-BROKERS-001` | Unknown broker names silently resolve to MT5. | `router.py::get_broker_module` | Typos or unsupported providers can unexpectedly target a live MT5 path. | Only explicit `ctrader` and `simulator` branches; unconditional MT5 fallback |
| `V1-ISSUE-BROKERS-002` | Configured simulator target is absent. | `router.py`, settings comment, `test_router.py` | Simulator routing is broken in the inspected snapshot. | Dynamic import of `app.services.simulator` without matching module |
| `V1-ISSUE-BROKERS-003` | Router selection and data-source selection are separate, inconsistent mechanisms. | `router.py` versus `data/gateway.py` | Dukascopy/Binance/Yahoo are valid data sources but cannot be selected as active trading broker; meaning of “broker” varies by caller. | Router cases versus `_BROKER_SPECS`/`ADAPTER_REGISTRY` |
| `V1-ISSUE-BROKERS-004` | Extremely large multi-responsibility provider files. | `ctrader.py`, `mt5.py`, `dukascopy.py` | High change coupling, difficult testing, and unclear public boundary. | Responsibilities enumerated in Sections 4–5 |
| `V1-ISSUE-BROKERS-005` | cTrader request correlation matches payload type only. | `CTraderClient.send_request` | Concurrent requests expecting the same payload type can potentially consume the wrong response. | Temporary callbacks compare only `payload_type == response_payload_type` |
| `V1-ISSUE-BROKERS-006` | cTrader can fabricate fallback quote prices. | `symbol_info_tick`, `CTraderSymbolInfo` | Broker truth is weakened; risk/validation may consume synthetic defaults. | Hard-coded EURUSD/XAU/other defaults after failed/no quote |
| `V1-ISSUE-BROKERS-007` | cTrader trade result can fabricate fallback order id and success shape. | `ctrader.py::trade`, `CTraderTradeResult` | Missing provider fields may be represented as successful execution. | Fallback `12345`; fixed retcode `10009` and “Request executed” |
| `V1-ISSUE-BROKERS-008` | `CTraderPositionInfo.profit` is populated from `swap`. | `ctrader.py::CTraderPositionInfo` | Position profit can be materially incorrect. | Both `profit` and `swap` read the `swap` field |
| `V1-ISSUE-BROKERS-009` | Duplicate unreachable return exists in profit calculation. | `CTraderClient.order_calc_profit` | Indicates unreviewed code and obscures implementation quality. | Consecutive identical `return float(diff * ...)` statements |
| `V1-ISSUE-BROKERS-010` | Yahoo ticks are synthetic, not provider ticks. | `YahooClient.get_ticks` | Source attribution can overstate data provenance and suitability. | Calls `generate_synthetic_ticks` after one daily close query |
| `V1-ISSUE-BROKERS-011` | Data-only clients report connected without validating the external service. | Binance/Yahoo/Dukascopy `connect` | Gateway readiness can report success before the first network call. | Methods only set `_connected=True` |
| `V1-ISSUE-BROKERS-012` | Timeframe validation is inconsistent. | Provider `get_bars` methods | Same invalid input may raise on MT5/cTrader/Dukascopy but silently become H1 on Binance/Yahoo. | Provider-specific timeframe maps |
| `V1-ISSUE-BROKERS-013` | Error and empty-result contracts are inconsistent. | All provider data/read functions | Callers must handle exceptions, empty frame, empty list, `None`, or error dictionaries for similar failures. | Public behaviour inventory |
| `V1-ISSUE-BROKERS-014` | MT5 has overlapping provider wrappers and connection state. | `MT5Api`, `_MT5_API`, `MT5Client`, module wrappers | Multiple ways to initialize/delegate can diverge and confuse callers. | `mt5.py` public surface |
| `V1-ISSUE-BROKERS-015` | Broker and data domain responsibilities overlap. | `load_mt5`, `load_dukascopy`, MT5 listing wrappers, data gateway/common | Direct entry points bypass data-domain controls and standardization. | Wrapper implementations and gateway workflow |
| `V1-ISSUE-BROKERS-016` | Private cTrader loader is consumed across domains. | `ctrader.py::_load_ctrader_impl`; `data/_common.py` | Private implementation has become an undocumented integration contract. | Repository import search |
| `V1-ISSUE-BROKERS-017` | Dukascopy instrument catalogue is not used to normalize fetch inputs. | `dukascopy_instruments.py`; `DukascopyClient.get_bars/get_ticks` | Symbol listing can advertise aliases that the fetch path does not translate. | Map used only by list function; fetch only reformats six-character pairs |
| `V1-ISSUE-BROKERS-018` | Fixed/zero spreads are inserted by several adapters. | Dukascopy bars, Binance bars/ticks, Yahoo bars | Consumers may interpret placeholder spreads as observed market costs. | `Spread=0.0002` or `0.0` assignments |
| `V1-ISSUE-BROKERS-019` | Singleton clients retain credentials and mutable connection/cache state process-wide. | All provider client classes | Tests/sessions/accounts can share stale state; multi-account isolation is unclear. | `_instance` on each client; settings-backed credentials/caches |
| `V1-ISSUE-BROKERS-020` | `mt5_data_list_symbols` does not establish a connection. | `mt5.py::mt5_data_list_symbols` | Behaviour differs from other MT5 public reads and may fail when terminal is not initialized. | Direct `mt5.symbols_get()` call |

## 13. V1 Capability Catalogue

| Capability ID | Capability | Current implementation | Workflow(s) | Usage status | Value status | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| `V1-CAP-BROKERS-001` | Lazy optional-provider exports | `__init__.py::__getattr__`, `_EXPORT_MODULES`, `__all__` | `V1-WF-BROKERS-001` | Used | Supporting | Prevents eager optional SDK imports |
| `V1-CAP-BROKERS-002` | Active trading broker selection | `router.py` | `V1-WF-BROKERS-002`, `006` | Used | Essential | MT5/cTrader only; simulator broken; unknown defaults MT5 |
| `V1-CAP-BROKERS-003` | MT5 terminal/account lifecycle | `MT5Client.connect/is_connected/shutdown` | `V1-WF-BROKERS-004`, `005`, `006` | Used | Essential | Requires terminal and credentials |
| `V1-CAP-BROKERS-004` | MT5 bars and ticks | `MT5Client.get_bars/get_ticks` | `V1-WF-BROKERS-003`, `004`, `005` | Used | Essential | Canonical DataFrame columns |
| `V1-CAP-BROKERS-005` | MT5 account/order/position/deal reads | Module `get_*_info` functions and delegated client calls | `V1-WF-BROKERS-005`, `006` | Used / dynamic | Essential | Supports trading and reconciliation |
| `V1-CAP-BROKERS-006` | MT5 order mutation | `mt5.py::trade` and delegated native methods | `V1-WF-BROKERS-005`, `006` | Used / dynamic | Essential | Checks common success retcodes |
| `V1-CAP-BROKERS-007` | Stored/explicit MT5 credential data operations | Credential helpers and `load_mt5`/`mt5_data_*` | `V1-WF-BROKERS-004` | Possibly used | Useful | Overlaps data domain |
| `V1-CAP-BROKERS-008` | cTrader connection/authentication | `CTraderClient.connect` and callbacks | `V1-WF-BROKERS-003`, `006`, `007` | Used for data; live unverified | Essential when selected | Twisted/reactor and protobuf state machine |
| `V1-CAP-BROKERS-009` | cTrader bars/ticks | `CTraderClient.get_bars/get_ticks` | `V1-WF-BROKERS-003`, `007` | Used | Essential | Error paths often return empty data |
| `V1-CAP-BROKERS-010` | cTrader MT5-compatible information objects | Seven wrapper classes and module `get_*_info` functions | `V1-WF-BROKERS-006`, `007` | Possibly used dynamically | Useful | Contains hard-coded/default fields |
| `V1-CAP-BROKERS-011` | cTrader order mutation | `ctrader.py::trade` | `V1-WF-BROKERS-006`, `007` | Possibly used dynamically | Essential when selected | Success/fallback truth issues identified |
| `V1-CAP-BROKERS-012` | Dukascopy historical/tick data | `fetch`, `DukascopyClient` | `V1-WF-BROKERS-003` | Used | Useful | HTTP scraper with retries |
| `V1-CAP-BROKERS-013` | Dukascopy instrument discovery | `INSTRUMENT_MAP`, `dukascopy_data_list_symbols` | Tool/direct workflow | Possibly used | Useful | Alias map not applied to fetch |
| `V1-CAP-BROKERS-014` | Binance klines and public-trade ticks | `BinanceClient.get_bars/get_ticks` | `V1-WF-BROKERS-003` | Used | Useful | No trading operations in this domain |
| `V1-CAP-BROKERS-015` | Yahoo historical bars | `YahooClient.get_bars` | `V1-WF-BROKERS-003` | Used | Useful | yfinance source |
| `V1-CAP-BROKERS-016` | Yahoo synthetic ticks | `YahooClient.get_ticks` + data synthetic transform | `V1-WF-BROKERS-003` | Used | Questionable | Generated, not observed Yahoo ticks |
| `V1-CAP-BROKERS-017` | Shared broker-backed data integration | Common client shape consumed by `data/gateway.py::BrokerAdapter` | `V1-WF-BROKERS-003` | Used | Essential integration surface | Actual commonality is conventional, not enforced by a broker protocol here |

## 14. Audit Conclusions

### Valuable behaviour worth preserving

* The common client shape—singleton getter, connection check, bars, and ticks—has real cross-domain value because the data gateway actively consumes it for all five providers.
* MT5 connection, normalized bars/ticks, account/order/position/deal reads, and order submission support confirmed live, trading, risk, and API call paths.
* The broker-neutral MT5/cTrader module surface allows the trading domain to call the same information and trade names after broker selection.
* cTrader authentication, request bridging, data decoding, and order translation represent substantial real implementation, even though live operation was not verifiable.
* Lazy package exports reduce eager loading of optional provider SDKs.
* Dukascopy, Binance, and Yahoo historical-data clients provide real source diversity to the data gateway.

### Behaviour that exists but is disconnected or only partially connected

* Binance, Yahoo, and Dukascopy are registered data sources but cannot be selected by the active trading-broker router.
* Simulator routing exists in settings/router/tests but the target module is absent.
* Several MT5 data-tool wrappers are exported and tested, but their production/dynamic tool callers were not conclusively confirmed.
* cTrader’s private `_load_ctrader_impl` is used outside the package rather than through a public contract.
* Provider disconnect operations have no confirmed unified shutdown workflow for data singletons.

### Likely dead weight or questionable surface

No symbol is conclusively declared dead code. The strongest questionable items are:

* the second MT5 wrapper (`MT5Api`) and its local initialization state;
* cTrader `unsubscribe_spots` without a production caller;
* ignored Dukascopy `cache` and `request_id` arguments;
* Dukascopy offer-side constants that production methods bypass with literals;
* wrappers that duplicate data-gateway behaviour without its controls.

### Duplicated responsibilities

* Provider lifecycle/data methods repeat across five clients but have different semantics.
* MT5 and cTrader duplicate the same compatibility information/trade surface.
* Broker data loaders overlap with data gateway/common responsibilities.
* MT5 exposes both `MT5Api` and `MT5Client` delegation layers.

### Important uncertainties requiring manual confirmation

* Whether live MT5 and cTrader credentials and terminals currently work with this snapshot.
* Whether cTrader’s Twisted reactor lifecycle remains stable across repeated tests/sessions and concurrent calls.
* Whether any external agent/tool registry invokes the exported MT5/Dukascopy tool wrappers by string name.
* Whether deployments ever set `active_broker=simulator`, or rely on unsupported values that currently fall through to MT5.
* Whether downstream consumers know that Yahoo ticks and some cTrader quote fallbacks are synthetic.
* Whether all aliases in `INSTRUMENT_MAP` are intended to be fetchable or only discoverable labels.
* Whether fixed/zero spread values are acceptable placeholders or are being used in risk/backtest/live decisions.

### Final validation

* Every Python file under `app/services/brokers` is represented.
* Every package-level `__all__` export was checked against an existing underlying symbol.
* Public classes, functions, named methods, and constants are inventoried; package aliases are not double-counted.
* Callers were searched across the accessible repository, including dynamic router and data-adapter registration paths.
* Production/runtime source usage is distinguished from tests and examples.
* Inbound and outbound cross-domain surfaces are summarized.
* Workflows are based on actual call paths and registration maps.
* Uncertain findings are labelled.
* No Version 2 design or requirement was invented.
* No code was changed.

## Evidence Not Accessible

* Actual broker credentials, terminals, accounts, and external provider responses.
* Runtime deployment configuration and environment variables.
* Successful execution of the test suite, coverage reports, type checks, or lint checks for this snapshot.
* Uncommitted/local-only files and external consumers outside the inspected repository.
* A complete runtime trace proving which settings-selected or string-registered paths execute in production.
