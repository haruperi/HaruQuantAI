# Broker execution backends

The public trading API lives in app/services/trading/. Strategies compose
Trading(backend) and await the same Trade, AccountInfo, SymbolInfo, OrderInfo,
HistoryOrderInfo, PositionInfo, DealInfo and TerminalInfo methods for either live
MT5 or local simulation. Backend-specific behavior stays here.

## Ownership and layout

```text
app/services/include/
  __init__.py          # Public re-exports for contracts, enums, temporal helpers
  contracts.py         # Consolidated domain data contracts
  enums.py             # Canonical trading enumerations

app/services/brokers/
  base.py              # BaseBrokerBackend template lifecycle, session cleanup, read_history
  capabilities.py      # ProviderCapabilities, HistoryRequest, HistoryPage, ProviderHealth
  registry.py          # Centralized BrokerRegistry, lease tracking, alias normalization
  _http.py             # Bounded HTTP transport, retries, redacted logging, connection pooling
  _file_history.py     # Partition matching, delimited text parsing, local parquet/bar loaders
  _native_history.py   # HST, FXT, StrategyQuant DAT binary codecs and bi5 decompression
  _simulation_api.py   # Private method handlers/per-object state for simulation
  metatrader.py        # Native Bridge and MT5Backend adapter
  simulator.py         # Local model and async execution adapter
  ctrader.py           # Spotware cTrader Open API Protobuf/TLS backend and unified dispatch
  dukascopy.py         # Dukascopy CDN market data broker
  darwinex.py          # Darwinex tick & bar market data broker
  crypto.py            # Cryptocurrency market data broker (Binance, Bitfinex, Coinbase, Poloniex)
  files.py             # Local filesystem market data broker (CSV, Parquet, HST, FXT)
  yahoo.py             # Yahoo Finance market data broker
  tick_downloader.py   # Historical tick downloader broker
  sq_equity.py         # StrategyQuant US Equities daily bundled broker
  sq_futures.py        # StrategyQuant Continuous Futures minute/daily bundled broker

app/host/persistence/
  mt5bridge_journal.py # Dedicated journal connection/CRUD
  schema.py            # Isolated journal DDL and compatibility checks

scripts/
  generate_token.py
  mql5/Experts/PythonBridge.mq5
```

The brokers package provides unified broker abstractions across execution backends and
market data providers. Shared foundation modules (`base.py`, `_http.py`, `_file_history.py`,
`_native_history.py`) eliminate boilerplate across provider adapters:
- `BaseBrokerBackend` automatically manages HTTP session lifecycles in `close_sync()`
  and provides a default `read_history()` template validating requests, token cancellation,
  and dispatching to `fetch_bars` / `fetch_ticks`.
- `_file_history.load_local_partition_bars` and `load_local_partition_ticks` unify
  multi-partition file discovery, decoding, date filtering, and deduplication across file-based
  providers (`files.py`, `sq_equity.py`, `sq_futures.py`).
- `BrokerRegistry` centralizes alias normalization via `normalize_provider_id` and
  guarantees safe idempotent resource disposal across synchronous and asynchronous callers.

TradingBackend is the async lifecycle/operation capability. BrokerBackend is a
synchronous internal snapshot-model ABC for simulator implementations;
MT5 does not pretend to implement that model or locally recalculate broker data.

## Live MT5

```python
import os
from app.services.brokers.metatrader import MT5Backend
from app.services.trading import Trading

token = os.environ["MT5_BRIDGE_TOKEN"]
backend = MT5Backend(auth_token=token)
trading = Trading(backend)
# async with trading: ... await trading.account.Balance()
```

Python listens on loopback 127.0.0.1:8765; the EA connects to it. Generate the shared
secret from the repository root with uv run python scripts/generate_token.py.
Provide MT5_BRIDGE_TOKEN to your calling code and set the same EA InpAuthToken.
Copy scripts/mql5/Experts/PythonBridge.mq5 into the terminal's MQL5/Experts folder,
compile in MetaEditor and attach one EA to one chart. Configure InpBridgeHost and
InpBridgePort and allow loopback sockets in Expert Advisors options as required.
Never embed credentials in examples or operation logs.

Authentication does not authorize trading. The bridge starts disarmed. Explicit
arming is required for marked live mutations, with distinct owner authorization
for actual live execution. Immediate CTrade return booleans do not prove a fill.
Timeout/connection uncertainty produces UNCERTAIN receipts and disarms trading;
reconcile orders/deals/positions before retrying. Events may span multiple trade
transactions and are not proof of a complete lifecycle.

Host persistence owns the MT5 journal in `data/database/haruquantai.db`, resolved
from the project location independently of the working directory. MT5 controls
its lifecycle. Startup creates missing `mt5_commands` and `mt5_events` tables
and `idx_mt5_events_request`/`idx_mt5_events_command` indexes; incompatible shapes
are rejected. Existing application tables and data are preserved. No legacy
journal fallback or migration is provided. Explicit `journal_path` arguments
remain available for isolated stores and tests.
Frames are newline-delimited UTF-8 JSON, version 1, with a 1 MiB payload limit.
Integer tags preserve full ticket/magic precision, and reserved string prefixes
are escaped. Native times remain seconds or milliseconds without implicit timezone
conversion. Codec logs exclude message contents and secrets.

## Simulation and future backends

SimulationBackend implements the same async execution boundary over the existing
local MT5-semantics model. Register SymbolSpec records and feed ticks explicitly.
Only caller-supplied tick/clock changes advance simulated time. Selection/trade
configuration is keyed by object ID; receipts are in-memory and do not open SQL.
Explicit simulated arming permits local mutations without authorizing live trades.

See ../include/README.md for named-property support and explicit unsupported numeric
property/native-request-correlation and queued-trade behavior. Local events are simulation events;
text formatting is model-specific. Future brokers implement the async capability
and map supported operations into this vocabulary, rejecting unavailable features.

## cTrader Open API (`CTraderBackend`)

```python
from app.services.brokers.ctrader import CTraderBackend
from app.services.trading import Trading

backend = CTraderBackend(
    client_id="...",
    client_secret="...",
    access_token="...",
    account_id=1234567,
    environment="demo",
)
trading = Trading(backend)
# async with backend: account = await trading.account.AccountInfo()
```

`CTraderBackend` connects to Spotware Open API via length-prefixed Protocol Buffers
over TLS (`live.ctraderapi.com:5035` or demo). It maps Spotware Open API payloads
into canonical `Trading` properties, symbols, depth of market, trendbars, positions,
and order execution checks. When protobuf modules are absent, it gracefully raises
`BridgeError("cTrader Open API protobuf modules not available", code="MODULE_NOT_FOUND")`.

Authentication first authorizes the application, then fetches the accounts allowed
by the access token, validates the configured account/environment, and finally
authorizes that account. `account_id` must be the API `ctidTraderAccountId`, not
the `traderLogin` shown in the cTrader UI. A login-number match raises
`CTRADER_ACCOUNT_ID_IS_LOGIN` with the correct API ID. No account is selected
implicitly. The account's `isLive` must match `environment` and the gateway.

Configuration precedence is explicit constructor arguments, `CTRADER_*`
environment variables, `settings.config_ctrader`, then defaults. Omitted
`environment` and `gateway_port` now respect settings. Defaults are `demo` and
5035; a configured host that contradicts the environment is rejected. Configure
both `environment="live"` and `gateway_host="live.ctraderapi.com"` for live, or
both demo values for demo. An explicitly configured gateway is preserved.

A rejected or expired access token triggers at most one protobuf token refresh
and account-list retry. If no usable refresh token exists, startup raises
`CTRADER_REAUTHORIZE_REQUIRED`; obtain fresh account consent/tokens through the
[cTrader authentication flow](https://help.ctrader.com/open-api/account-authentication/).
Refreshing invalidates the old access and refresh tokens. When the entire
credential set came from host settings, the rotated pair is saved atomically
through the host settings API with revision checks. For explicit or environment
credentials, the caller must securely store `backend.client.access_token` and
`backend.client.refresh_token` after rotation; do not log them. A host persistence
conflict stops startup with `CTRADER_TOKEN_PERSIST_FAILED`, retaining the new pair
on the client for secure recovery. No broker code runs SQL or migrates settings.

The usage example defaults `ALLOW_LIVE_TRADING=False`, keeping external mutation
examples disabled. Authentication/configuration failures expose safe error codes;
server descriptions and token contents are excluded from auth diagnostics.

### Historical downloads

cTrader historical bars and ticks support explicit date ranges through
`Trading.get_historical_bars` and `Trading.get_ticks`. The backend resolves the
broker symbol ID, forwards inclusive date bounds in milliseconds, normalizes
`M1`/`PERIOD_M1` timeframes, and rejects unsupported timeframes. Caller limits
are enforced without silently truncating data. Position, latest and date/count
modes currently raise `UNSUPPORTED_OPERATION`; supply both range boundaries.

Requests are paced below five historical requests per second, with bounded
pagination (64 pages per stream) and caller limits up to 10,000 records. Bars
use one-day windows; ticks use windows no longer than one week. Incomplete or
nonprogressing pages fail explicitly. Bid/ask tick timestamps and prices are
both decoded from signed deltas after the first absolute sample. Overlapping
page boundaries are deduplicated and returned records are chronological.
Tick flags identify the updated side; the other side is carried forward only
from prior observations within the requested range. Zero denotes an unobserved
side. Historical candles carry spread=0 because the API does not supply it.

Historical downloads now use actual server data. Live SymbolSnapshot/spot quote
metadata, order book and some trading calculations remain legacy placeholder
implementations; completing the read-only example does not certify those
capabilities or authorize trading.

## Focused verification

```powershell
uv run pytest tests/unit/services/test_trading_api.py tests/unit/services/test_trading_backend_parity.py tests/unit/services/test_trading_simulator.py tests/unit/services/test_metatrader_bridge_protocol.py tests/unit/services/test_broker_contracts.py tests/unit/services/test_mt5bridge_journal.py --no-cov
uv run mypy --strict --follow-imports=silent app/services/include app/services/brokers/base.py app/services/brokers/metatrader.py app/services/brokers/simulator.py app/services/brokers/_simulation_api.py
```

Checks use isolated stores and local/native-fixture execution. Compile and validate
the EA separately in the installed terminal. Focused checks are not live-execution
certification or evidence of global 80% branch coverage.


Native deal-ticket selection loads the requested deal with `HistoryDealSelect`
before reading properties; history-order and deal index selection rebuild the
native history list first. After updating `PythonBridge.mq5`, compile it in
MetaEditor and replace/reload the EA attached to the chart.

The example reports successful buy dispatch before checking ownership. Failures
such as `DEAL_HISTORY_SELECTION_FAILED`, `DEAL_POSITION_ID_UNAVAILABLE` and
`POSITION_OWNERSHIP_UNCONFIRMED` stop execution and disarm the bridge. Rejected
or unconfirmed buys include their numeric retcode. Arbitrary exception messages
remain redacted. There is no repeated buy or close-by-symbol fallback. A failure
after a successful buy can leave its position open: inspect and reconcile that
position before rerunning the examples.


## Historical data capability and named usage examples

`scripts/examples/brokers.py` provides the seventeen legacy named async examples
plus historical-bars and tick-data functions. The operation bodies use only the
shared Trading facade; shutdown runs after both history-data functions.
The write walkthrough now includes SL/TP modification, a partial position close
and pending-order modification. It opens twice the configured partial VOLUME,
then closes that amount in two stages, verifying owned tickets at every step.

Trading adds read-only `get_historical_bars`/`get_ticks` helpers through internal
`MarketData` dispatch, without adding a ninth trading class. MT5 executes CopyRates
and bounded CopyTicks; simulation reads explicitly seeded immutable records.
Requests use aware UTC date bounds, chronological MarketBar/MarketTick DTOs,
inclusive seconds/milliseconds and a 1..1000 record cap. Native timeframe is
explicit; CURRENT and native-special tick epoch zero are rejected. Excess rows,
unavailable history and malformed payloads fail explicitly. Narrow date intervals
instead of assuming an oversized request returns a complete truncated result.

Recompile/reload the updated bridge EA to enable the new commands. Native copy
can wait for terminal synchronization; requests have an explicit 60-second deadline
and no automatic retry. No trading arming is needed for these read helpers, and
no database schema changes are introduced. See trading/README.md for the nineteen
functions, shared signatures, date settings and simulation seed ownership.


## Optional historical-read selectors

The same two functions route according to their arguments; no additional public
scenario functions are needed:

```python
# Bars from a date, moving forward through time.
bars = await trading.get_historical_bars(symbol, timeframe, date_from=start, count=100)
# Bars by native index: zero is the current, potentially unfinished bar.
bars = await trading.get_historical_bars(symbol, timeframe, start_pos=10, count=100)
# Inclusive date range (existing positional dates also work).
bars = await trading.get_historical_bars(
    symbol, timeframe, date_from=start, date_to=end
)
# Latest bars; a date alone runs through the current UTC instant.
bars = await trading.get_historical_bars(symbol, timeframe, count=100)
bars = await trading.get_historical_bars(symbol, timeframe, date_from=start)
# Index alone returns indices start_pos through zero (chronologically).
bars = await trading.get_historical_bars(symbol, timeframe, start_pos=10)

# Ticks from a date/count, date range, latest count or date through now.
ticks = await trading.get_ticks(symbol, date_from=start, count=100)
ticks = await trading.get_ticks(symbol, date_from=start, date_to=end)
ticks = await trading.get_ticks(symbol, count=100)
ticks = await trading.get_ticks(symbol, date_from=start)
```

All rows return oldest-first. Bar index/count follows native indexing toward
older bars; date/count moves forward for both bars and ticks. Forward bar counting
is intentional: the EA uses date-to-index selection, since native CopyRates'
date/count overload counts older bars. Ticks sharing a millisecond remain distinct.

No selector/count defaults to the latest `limit` rows (1000). Explicit count asks
for up to that many available records; fewer rows near available/current history
can be valid. Date-only endpoints use one captured current UTC instant, not a
future end-of-day. Simulation also filters out seeded records after its model
clock without advancing time. Capacity remains 1000 for testing, implemented in
our code; oversized date/position ranges fail rather than silently truncate.

Reject date_from combined with start_pos, date_to without date_from, explicit
date_to combined with count, booleans/non-integer count/index, nonpositive counts
and negative/out-of-native-range indices. Existing deadlines, DTO validation,
frame limits and absence of automatic retries/saving remain unchanged.

Example functions 18 and 19 demonstrate the selectors directly. Recompile/reload
the updated EA before using the extended wire routes; deployed files are not
updated by editing repository source.


## Quiet EA reconnection logs

The attached EA continues retrying while the Python listener is unavailable,
including after an example script shuts down its connection. Error 5272 means the
socket could not connect; repeated retries are expected when no listener is running.

`InpVerboseReconnectLogs = false` is the default. The Experts tab reports the first
socket-creation/connection failure and changed error codes, suppressing identical
repeated failures. Successful connection resets the reported-error state, so a
later outage is reported once. Set the input to `true` for per-attempt diagnostics.
The timer/reconnect interval and socket timeout remain unchanged; quiet logging
does not stop monitoring or reconnection. Startup token/lock diagnostics remain.
The existing connected message describes TCP/hello-send success, not completed
authentication. Recompile/reload the updated EA to use the new input.

## Stage 2C: Dynamic Market Data Providers (`slot: "data.provider"`)

Stage 2C introduces typed market data provider plugins discoverable under slot
`data.provider` coordinated through `BrokerRegistry`. It bridges historical data
acquisition across local file archives, binary codecs, remote HTTP feeds, and
active trading broker instances without duplicating or mutating broker state.

### Registered Data Providers

1. `dukascopy`: Dukascopy Bank SA historical tick and bar provider (BI5 binary codec & CDN feeds).
2. `darwinex`: Darwinex tick archives (gzipped / custom binary `.dat` feeds).
3. `metatrader`: MetaTrader 5 Bridge historical data provider (delegating to active `MT5Backend` or local HST/FXT archives).
4. `sq_equity`: StrategyQuant US Equities bundled D1 daily historical data provider.
5. `sq_futures`: StrategyQuant Continuous Futures bundled M1 and D1 historical data provider.
6. `crypto`: Cryptocurrency Spot and USD-M Futures candle provider (Binance, Bitfinex, Coinbase, Poloniex).
7. `files`: Local filesystem market data broker supporting CSV, Parquet, MT4 HST, and FXT historical files.
8. `yahoo`: Yahoo Finance public market data and symbol metadata provider (v8 chart API).
9. `tick_downloader`: High-precision tick and trade volume historical data downloader plugin.

### Typed Contracts and Invariants

- **Capability Descriptor**: `ProviderCapabilities` declares supported timeframes, modes (`bars`, `ticks`), auth requirements, and rate limits.
- **Request / Response Models**: `HistoryRequest` enforces strict date bounds and count validation; `HistoryPage` encapsulates typed records, cursor, and provenance metadata.
- **Cancellation**: Cooperative, thread-safe cancellation via `CancellationToken`.
- **Health Probing**: Every provider exposes `check_health() -> ProviderHealth` verifying reachability, filesystem accessibility, or credentials.
- **Strict Real-Data Policy**: Production download paths never synthesize synthetic mock records. Unavailable history fails explicitly with typed `ProviderError` subtypes (`ProviderNotFoundError`, `ProviderValidationError`, `ProviderUnsupportedError`, `ProviderRateLimitError`, `ProviderTimeoutError`).
- **Resource Management**: Registry leases (`with registry.lease(name) as broker:`) coordinate concurrent access and orderly lifecycle release (`close_sync` / `close`).
