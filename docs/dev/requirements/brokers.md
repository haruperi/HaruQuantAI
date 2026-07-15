# Broker Domain — Functional Requirements

> **System:** HaruQuantAI
> **Domain:** Brokers
> **Target package:** `app/services/brokers`
> **Status:** Canonical merged draft
> **Requirement type:** Functional requirements and mandatory domain-boundary rules
> **Source basis:** Current Brokers V1 audit plus the approved decision to move broker connectivity out of Data

---

## 1. Purpose

The Brokers domain provides the system's **only direct integration boundary to real external broker and market-provider platforms**. It is a pure, thin passthrough abstraction with **zero business logic**. Every operation that requires a real provider connection—whether for market data, account information, subscriptions, or trading—must pass through this domain.

Its sole responsibility is to:

1. establish and maintain a direct provider connection;
2. authenticate an account or application;
3. translate canonical broker requests into provider-native API/SDK calls;
4. translate provider-native responses and errors into canonical broker contracts while preserving provider truth;
5. expose provider capabilities through one consistent interface;
6. return either the provider response mapped structurally into canonical DTOs or a uniform broker error.

The domain must not own any trading, risk, data-processing, orchestration, persistence, fallback-selection, approval, reconciliation, or analytical business logic.

---

## 2. Architectural Decision

The previous ownership rule is replaced.

### Previous rule

```text
Data owns broker connection lifecycle and exposes broker access to Trading.
```

### New rule

```text
Brokers owns all real broker/provider connection and protocol integration.
Data owns data acquisition workflows, normalization, validation, caching, and persistence.
Trading owns approved order orchestration, idempotency, execution policy, and reconciliation.
Risk owns approval and safety policy.
```

### Required Compile-Time Import Dependencies (Static Architecture)

The static compile-time import dependencies represent code referencing, where low-level components must not import high-level business domains (arrows represent "imports / depends on"):

```text
Data ───────→ Brokers ───────→ Utils
Trading ────→ Brokers

Strategy/Trading ──→ Risk
Trading ───────────→ Data
```

The Brokers domain may depend on Utils and third-party provider SDKs. It must not import Data, Trading, Risk, Strategy, Indicators, Simulation, Analytics, Optimization, Research, or UI/API.

### Runtime Execution Workflow (Call Stack Direction)

The dynamic runtime command-dispatch flow represents active method invocation during execution (arrows represent "calls"):

```text
Trading ──[ mutation requests ]──→ Brokers
Data ─────[ query requests ]─────→ Brokers
```

### Event and Data Flow (Event Streaming Direction)

The asynchronous event propagation flow represents data push updates (arrows represent "pushes updates to"):

```text
Brokers ──[ WebSocket events ]──→ Data / Trading (via subscriptions)
Data ─────[ normalization ]──────→ Strategy / UI (via stored files or caches)
```

---

## 3. Domain Ownership

### 3.1 Brokers owns

- Provider SDK/API integration.
- Provider protocol and transport handling.
- Connection, authentication, session, token, and subscription lifecycle.
- Provider request construction.
- Provider response decoding.
- Provider-native pagination and cursors.
- Provider error capture and canonical error mapping.
- Provider capability discovery and reporting.
- Minimal structural mapping from provider objects into canonical broker DTOs.
- Technical connection/session state required to communicate with the provider.
- Direct broker reads and direct broker mutations requested by an authorized caller.

Technical connection/session state is permitted; application business state is not. The domain must remain a faithful direct passthrough rather than an orchestration or policy layer.

### 3.2 Brokers does not own (BRK-FR-OWN-001)

The domain must remain a faithful direct passthrough rather than an orchestration or policy layer. The domain explicitly does not own:

- Market-data cleaning, quality scoring, resampling, alignment, gap filling, deduplication, or no-lookahead enforcement.
- Business-level or reusable data caching (such as historical bars, reusable market datasets, account snapshots, normalized quotes, persisted positions, cross-provider fallback data), persistence, licensing policy, source fallback, or source preference. Provider-required technical/session caches (such as access tokens, connection state, capability discovery, latest WebSocket sequence number, subscription registrations, rate-limit counters, provider-required instrument metadata, latest transport event needed for protocol operation) are permitted when bounded, instance-scoped, observable, and invalidated correctly.
- Strategy evaluation, signal generation, or trade proposal creation.
- Risk rules, position sizing policy, approval tokens, permissions, or kill-switch policy.
- Order-intent creation, execution policy, idempotency policy, rate-limit policy, retries after uncertain mutations, or reconciliation authority.
- Simulation or paper-fill emulation.
- Performance calculations, reporting, research, or optimization.
- UI/API routes, AI-tool envelopes, user messages, or presentation DTOs.
- Credential persistence, database lookup, user-account lookup, or secret-vault ownership.
- Synthetic prices, synthetic ticks, fabricated fills, fallback order IDs, assumed spreads, or invented account state.

---

## 4. Consumers and Allowed Use

| Consumer | Allowed Broker usage | Consumer-owned logic |
| --- | --- | --- |
| `Data` | Bars, ticks, quotes, order books, symbols, sessions, account-state reads when needed | Source selection, fallback sources, normalization, validation, caching, storage, datasets, account snapshots |
| `Trading` | Account reads, symbol metadata, positions, orders, deals, calculations, order mutation, subscriptions needed for execution | Risk-token enforcement, order intent, idempotency, mutation gates, timeouts, unknown-outcome handling, reconciliation, persistence |
| `Risk` | No direct broker dependency in normal workflows | Consumes trusted snapshots from Data and decisions from its own policy engine |
| `UI/API` | No direct broker dependency | Authentication, authorization, request handling, DTO presentation |
| Other domains | No direct broker dependency | Consume outputs from their owning upstream domains |

No domain may bypass Data or Trading by calling Brokers for business workflows it does not own.

---

## 5. Standardized Broker Interface

A single canonical interface, named `IBroker` conceptually and implemented in Python as the `BrokerAdapter` protocol/ABC, must define every operation that any supported broker or provider could perform. Every concrete adapter must implement the interface in its entirety, even where the underlying platform does not support a capability.

### 5.1 Initial platform support

The initial domain must support the following adapters:

**Trading-capable broker platforms**

- MetaTrader 5
- cTrader
- Binance Spot and Binance Futures

**Read-only or capability-limited provider platforms**

- Dukascopy
- Yahoo Finance

Read-only or capability-limited providers must still implement the complete interface. Trading, account, subscription, or other unavailable methods must return the standard unsupported-capability outcome. Additional providers must implement the same contract before registration.

### 5.2 Mandatory implementation rule

Each provider module must expose one adapter class implementing the canonical `BrokerAdapter` protocol.

Example logical exports:

```text
app/services/brokers/mt5.py        → MT5BrokerAdapter
app/services/brokers/ctrader.py    → CTraderBrokerAdapter
app/services/brokers/binance.py    → BinanceBrokerAdapter
app/services/brokers/dukascopy.py  → DukascopyBrokerAdapter
app/services/brokers/yahoo.py      → YahooBrokerAdapter
```

Every adapter must contain every public operation listed in Section 6.

### 5.2.1 Asynchronous operation model

The canonical adapter protocol is async-first. This is essential for non-blocking operations (such as streaming quotes or executing trades over WebSocket/gRPC interfaces) without requiring complex per-adapter multi-threading.

```python
class BrokerAdapter(ABC):
    async def connect(self, config: BrokerConnectionConfig) -> BrokerResult[None]: ...
    async def get_quote(self, symbol: str) -> BrokerResult[BrokerQuote]: ...
    async def subscribe_quotes(self, symbols: List[str],
                               handler: Callable[[BrokerQuote], Awaitable[None]]) -> BrokerResult[str]: ...
    # ...
```

A synchronous facade can satisfy consumers that prefer threading, but the core protocol must remain async. The synchronous façade must never call `asyncio.run()` when another event loop is active. Instead, a separate `SyncBrokerAdapter` must be defined that uses either:
- a dedicated background event-loop thread; or
- provider-specific blocking execution where appropriate.

**BRK-FR-ASYNC-001** – The canonical `BrokerAdapter` protocol shall expose async operations as the primary contract. Synchronous consumers shall obtain a wrapper implementing `SyncBrokerAdapter` from the registry; adapters must not block the caller’s event loop when used natively. The synchronous façade wrapper must never call `asyncio.run()` when another event loop is active.

**BRK-FR-ASYNC-002** — Async Task Cancellation. If an `asyncio.CancelledError` is raised by the caller, the adapter must attempt to cancel the in-flight provider request where the SDK supports it, log the cancellation, and propagate the `CancelledError` without corrupting adapter state.

### 5.3 Unsupported capability rule

When a provider does not support an operation:

1. the method must still exist;
2. it must not simulate or approximate the capability;
3. it must return a canonical error with code `BROKER_CAPABILITY_UNSUPPORTED`;
4. the error must identify the broker, operation, and capability;
5. the adapter feature-flag report must mark the operation as unsupported;
6. no provider SDK call may be attempted.

The canonical result-based API must return `BrokerResult` with `BROKER_CAPABILITY_UNSUPPORTED`. A strict exception façade may convert that result into `BrokerNotSupportedException` for callers that prefer exception handling. Adapters must not expose Python's generic `NotImplementedError`, leave compilation/runtime stubs, or omit the method.

---

### 5.4 Normative core interface

The following methods are the minimum recognizable broker-agnostic surface and must exist with equivalent snake_case Python names as coroutines (i.e. `async def`) on every adapter. Section 6 extends this same interface with additional direct provider operations.

| Conceptual operation | Canonical Python method | Required behavior |
| --- | --- | --- |
| `Connect(credentials)` | `connect(config)` | Establish and verify the provider session. |
| `Disconnect()` | `disconnect()` | Close the session and owned resources. |
| `IsConnected` | `is_connected()` | Return verified connection state. |
| `GetAccountInfo()` | `get_account_info()` | Return provider-supplied account information. |
| `GetSymbols()` | `get_symbols(query=None, cursor=None, limit=None)` | Return provider instruments and direct specifications. |
| `GetQuote(symbol)` | `get_quote(symbol)` | Return the latest genuine provider quote. |
| `GetOrderBook(symbol, depth)` | `get_order_book(symbol, depth=None)` | Return provider depth-of-market data. |
| `SubscribeQuotes(symbols, callback)` | `subscribe_quotes(symbols, handler)` | Stream genuine provider quote events. |
| `Unsubscribe(token)` | `unsubscribe(subscription_id)` | Remove any adapter-owned subscription. |
| `GetHistoricalBars(...)` | `get_historical_bars(...)` | Return provider OHLCV bars using provider timeframe translation only. |
| `PlaceOrder(request)` | `place_order(request)` | Submit one caller-defined order. |
| `ModifyOrder(...)` | `modify_order(request)` | Modify one existing provider order. |
| `CancelOrder(orderId)` | `cancel_order(order_id, ...)` | Cancel one existing provider order. |
| `GetOrders(filter)` | `get_orders(filter=None, ...)` | Return provider orders matching a structural filter. |
| `GetPositions(filter)` | `get_positions(filter=None, ...)` | Return current provider positions. |
| `ClosePosition(...)` | `close_position(request)` | Close or reduce one provider position. |
| `ModifyPosition(...)` | `modify_position(request)` | Modify provider-supported fields on one position. |
| `GetFeatureFlags()` | `get_feature_flags()` | Return the complete runtime feature-flag matrix. |

The public interface may expose additional direct provider primitives, but provider-specific public methods are forbidden unless they are first added to the canonical interface and implemented by all adapters.

---

## 6. Required Standard Operations

All operations below must exist on every provider adapter.

### 6.1 Connection and session

| Operation | Purpose |
| --- | --- |
| `connect(config)` | Connect and authenticate using caller-supplied configuration. |
| `disconnect()` | Close the provider session and release provider resources. |
| `reconnect()` | Re-establish the same configured provider session without changing broker identity. |
| `is_connected()` | Return the verified current provider connection state. |
| `get_connection_status()` | Return detailed transport, authentication, account, and environment state. |
| `ping()` | Perform a provider-supported liveness check. |
| `refresh_session()` | Refresh an expiring token/session when the provider supports it. |
| `get_server_time()` | Return provider server time when available (exposing clock-skew information). |
| `get_last_error()` | Return the latest provider error captured by this adapter instance (non-authoritative diagnostic use only; errors are returned directly in BrokerResult.error). |
| `connection_events()` | Return an async iterator yielding connection events: `AsyncIterator[BrokerConnectionEvent]`. |

### 6.2 Capabilities and platform metadata

| Operation | Purpose |
| --- | --- |
| `get_feature_flags()` | Return the complete feature-flag matrix for the connected provider/profile. |
| `supports(capability)` | Return whether one named capability is currently supported. |
| `get_platform_info()` | Return provider name, API/terminal version, environment, and endpoint metadata. |
| `get_permissions()` | Return provider-reported read/trade/account permissions. |
| `list_accounts()` | Return accounts visible to the authenticated provider session. |
| `select_account(account_id)` | Select the account used by subsequent calls where the provider supports account switching. |
| `get_account_info()` | Return current account identity, currency, balances, equity, margin, and status fields supplied by the provider. |
| `get_balances()` | Return provider-reported asset or currency balances. |
| `list_assets()` | Return assets/currencies known to the account or provider. |
| `get_asset_info(asset)` | Return direct provider metadata for one asset/currency. |

### 6.3 Symbols and market metadata

| Operation | Purpose |
| --- | --- |
| `get_symbols(query=None, cursor=None, limit=None)` | Return symbols directly available from the provider. |
| `get_symbol_info(symbol)` | Return provider symbol specifications and current trading flags. |
| `select_symbol(symbol, enabled=True)` | Add/remove a symbol from a provider watch list where supported. |
| `get_market_status(symbol)` | Return provider-reported open, closed, halted, or unknown state. |
| `get_trading_sessions(symbol, start=None, end=None)` | Return provider-supplied session windows where available. |
| `get_quote(symbol)` | Return the latest genuine provider bid/ask/last quote without fabricated fields. |
| `get_ticks(symbol, start=None, end=None, cursor=None, limit=None)` | Return provider historical ticks. |
| `get_historical_bars(symbol, timeframe, start=None, end=None, cursor=None, limit=None)` | Return provider historical bars/candles; timeframe mapping is provider translation only. |
| `get_order_book(symbol, depth=None)` | Return the current provider order book where supported. |
| `get_spread(symbol)` | Return the provider-reported current spread when available. |

### 6.4 Streaming and subscriptions

| Operation | Purpose |
| --- | --- |
| `subscribe_quotes(symbols, handler)` | Subscribe to provider tick/quote events. |
| `subscribe_bars(symbols, timeframe, handler)` | Subscribe to provider bar events where supported. |
| `subscribe_order_book(symbols, depth, handler)` | Subscribe to provider order-book events where supported. |
| `unsubscribe(subscription_id)` | Remove any subscription owned by the current adapter instance. |
| `list_subscriptions()` | Return subscriptions owned by the current adapter instance. |

### 6.5 Positions, orders, deals, and account activity

| Operation | Purpose |
| --- | --- |
| `get_positions(filter=None, cursor=None, limit=None)` | Return current provider positions matching a structural filter. |
| `get_position(position_id)` | Return one current provider position. |
| `get_orders(filter=None, cursor=None, limit=None)` | Return active or historical provider orders matching a structural filter. |
| `get_order(order_id)` | Return one provider order. |
| `list_order_history(start=None, end=None, symbol=None, cursor=None, limit=None)` | Return historical provider orders. |
| `list_deal_history(start=None, end=None, symbol=None, cursor=None, limit=None)` | Return fills/deals/trades reported by the provider. |
| `get_deal(deal_id)` | Return one provider deal/fill. |
| `list_account_transactions(start=None, end=None, cursor=None, limit=None)` | Return deposits, withdrawals, fees, swaps, and provider-reported account transactions where available. |

### 6.6 Direct broker mutations

| Operation | Purpose |
| --- | --- |
| `check_order(request)` | Ask the provider to validate or preview an order where supported. |
| `place_order(request)` | Submit exactly one caller-supplied order request. |
| `modify_order(request)` | Modify exactly one existing provider order. |
| `cancel_order(order_id, client_request_id=None)` | Cancel exactly one existing provider order. |
| `modify_position(request)` | Modify provider-supported position fields such as stop loss or take profit. |
| `close_position(request)` | Close or reduce exactly one provider position. |
| `replace_order(request)` | Atomically replace one order where the provider supports it. |

Bulk business operations such as `close_all_positions`, `cancel_all_orders`, portfolio liquidation, or multi-leg orchestration are intentionally excluded (adhering to Section 3.2). Calling domains may compose single-operation primitives under their own policy.

### 6.7 Provider calculations

| Operation | Purpose |
| --- | --- |
| `calculate_margin(request)` | Request provider-native expected margin. |
| `calculate_profit(request)` | Request provider-native expected profit/P&L. |
| `get_commission_estimate(request)` | Request provider-native commission/fee estimate where supported. |

The adapter must not substitute local risk, portfolio, or pricing formulas when the provider does not expose the calculation (adhering to Section 3.2).

---

## 7. Canonical Contracts

### BRK-FR-CONTRACT-001 — Standard result

Every public operation must return `BrokerResult[T]` with:

- `status`: `success` or `error`;
- `broker`: canonical provider identifier;
- `operation`: canonical operation name;
- `request_id`: caller-supplied or adapter-generated correlation identifier;
- `timestamp`: UTC completion timestamp;
- `data`: canonical response payload on success, otherwise `null`;
- `error`: canonical error on failure, otherwise `null`;
- `provider_metadata`: non-secret provider identifiers needed for diagnosis, including provider-native field names or raw identifiers where required for traceability;
- `latency_ms`: measured adapter call duration.

The canonical mapping must preserve the provider's original values. Optional redacted raw-response metadata may be attached for technical diagnosis, but raw SDK objects may never cross the boundary.

### BRK-FR-CONTRACT-002 — Standard error

`BrokerError` must include:

- `code`;
- `message`;
- `retryable`;
- `provider_code` when supplied;
- `provider_message` when supplied;
- `capability` when applicable;
- `details` containing redacted diagnostic fields only.

### BRK-FR-CONTRACT-003 — Required error codes

At minimum, the domain must support:

- `BROKER_UNKNOWN`
- `BROKER_CONFIGURATION_INVALID`
- `BROKER_AUTHENTICATION_FAILED`
- `BROKER_AUTHORIZATION_FAILED`
- `BROKER_NOT_CONNECTED`
- `BROKER_CONNECTION_FAILED`
- `BROKER_CONNECTION_LOST`
- `BROKER_TIMEOUT`
- `BROKER_RATE_LIMITED`
- `BROKER_CAPABILITY_UNSUPPORTED`
- `BROKER_SYMBOL_NOT_FOUND`
- `BROKER_ACCOUNT_NOT_FOUND`
- `BROKER_ORDER_NOT_FOUND`
- `BROKER_POSITION_NOT_FOUND`
- `BROKER_DEAL_NOT_FOUND`
- `BROKER_REQUEST_INVALID`
- `BROKER_REQUEST_REJECTED`
- `BROKER_MARKET_CLOSED`
- `BROKER_INSUFFICIENT_MARGIN`
- `BROKER_INSUFFICIENT_FUNDS`
- `BROKER_UNKNOWN_OUTCOME`
- `BROKER_PROVIDER_ERROR`
- `BROKER_RESPONSE_INVALID`
- `BROKER_SUBSCRIPTION_FAILED`
- `BROKER_MAINTENANCE_MODE`
- `BROKER_SUBSCRIPTION_RESYNC_REQUIRED`
- `BROKER_SUBSCRIPTION_NOT_FOUND`
- `BROKER_BACKPRESSURE`
- `BROKER_OPERATION_CANCELLED`
- `BROKER_DEPENDENCY_MISSING`
- `BROKER_ACCOUNT_SWITCH_IN_PROGRESS`
- `BROKER_SESSION_CHANGED`
- `BROKER_CIRCUIT_OPEN`

### BRK-FR-CONTRACT-003A — Canonical error mode and typed exception façade

Canonical adapters must use returned error results as the exclusive error mode:
1. **Canonical error mode**: All public operations in `BrokerAdapter` must return `BrokerResult[T]` on success or failure, and must never raise expected domain exceptions.
2. **Propagating exceptions**: Low-level runtime exceptions such as `asyncio.CancelledError`, `KeyboardInterrupt`, and fatal process exceptions (e.g. `SystemExit`, `OutOfMemoryError`) must propagate and must not be swallowed.
3. **Exceptions wrapper**: Callers that prefer exception handling shall consume a separate `StrictBrokerAdapter` wrapper. The wrapper wraps a canonical `BrokerAdapter` and converts any failed `BrokerResult[T]` into a typed canonical exception:
   - `BrokerException` — base canonical broker exception;
   - `BrokerConnectionException` — connection or authentication failures;
   - `BrokerNotSupportedException` — unsupported capability;
   - `BrokerTimeoutException` — provider or transport timeout;
   - `BrokerRateLimitException` — provider throttling;
   - `BrokerRequestRejectedException` — provider rejection;
   - `BrokerUnknownOutcomeException` — mutation may have reached the provider but acknowledgement is unknown;
   - `BrokerResponseInvalidException` — corrupted, NaN/Infinity, or invalid platform responses.
4. **No mixed error modes**: Concrete adapters must never unpredictably mix returned errors and raised exceptions; they must consistently return `BrokerResult[T]` for all operational failures.

The exception must preserve the canonical error code, normalized message, redacted provider code/message, broker ID, operation, and correlation ID.

### BRK-FR-CONTRACT-003B — No retry policy

The domain must not implement business retry policies. A transport library may complete protocol-mandated handshakes or a provider SDK's internal delivery sequence, but the adapter must not retry failed reads or mutations on its own. Retry, fallback, and reconciliation policy belong to the calling domain. While the domain must not implement business-level reactive retries, it must implement proactive transport-level flow control (e.g., token bucket or leaky bucket, dynamically respecting rate-limiting headers such as Binance's `X-MBX-USED-WEIGHT-1M` when provided by the platform) to respect provider rate limits and prevent IP bans. This throttling is considered transport protocol handling, not business logic.

### BRK-FR-CONTRACT-003C — Rate-Limit Queue Semantics

Where proactive transport-level throttling/flow control queueing is implemented to handle rate-limit capacity:
1. **Configurable Behavior**: Throttling queue behavior must be configurable to either block and wait in the queue, or fail fast immediately returning `BROKER_BACKPRESSURE`.
2. **Maximum Queue Wait**: When queue waiting is configured, requests must support a maximum queue wait timeout (`throttling_max_wait_sec`), returning `BROKER_BACKPRESSURE` if the request cannot be sent within the timeout.
3. **Priority Queuing**: The throttling queue must prioritize mutation operations (orders, cancellations) over read operations (symbols, quotes, historical bars).
4. **Cancellation**: In-flight requests waiting in the throttling queue must be cancellable (e.g. via `asyncio.CancelledError`), removing them from the queue and returning `BROKER_OPERATION_CANCELLED`.
5. **No Mutation Reordering**: To prevent execution anomalies, mutation operations targeting the same symbol/account must preserve FIFO ordering and must never be reordered within the queue.
6. **Provider Weight Handling**: The rate limiter must respect platform-specific endpoint weights (e.g., higher weights for order book pulls vs single quote lookups).
7. **Limiter Telemetry**: Every rate-limited result must expose canonical `retry_after_sec` (float) and rate-limit capacity metadata in the response `BrokerError` or header.

---

### BRK-FR-CONTRACT-004 — No raw SDK leakage

Provider SDK objects, protobuf messages, sockets, terminal handles, database sessions, or provider-specific exceptions must not cross the public domain boundary.

### BRK-FR-CONTRACT-005 — Canonical DTOs

All adapters must return identical canonical model types. This is **transport/schema normalization only**: canonical field names, enum mapping, explicit quantity units, decimal-compatible numbers, and timezone-aware UTC timestamps. It must not include data cleaning, resampling, enrichment, currency conversion, profit calculation, risk calculation, or any transformation that changes provider truth.

The domain must define canonical DTOs for at least:

- `BrokerConnectionConfig`
- `BrokerFeatureFlags`
- `BrokerConnectionStatus`
- `BrokerPlatformInfo`
- `BrokerPermissions`
- `BrokerAccountInfo`
- `BrokerBalance`
- `BrokerAssetInfo`
- `BrokerSymbolInfo`
- `BrokerQuote`
- `BrokerMarketStatus`
- `BrokerTradingSession`
- `BrokerTick`
- `BrokerBar`
- `BrokerOrderBook`
- `BrokerSubscription`
- `BrokerPosition`
- `BrokerOrderFilter`
- `BrokerPositionFilter`
- `BrokerOrder`
- `BrokerDeal`
- `BrokerAccountTransaction`
- `BrokerOrderRequest`
- `BrokerOrderModificationRequest`
- `BrokerOrderCancellationRequest`
- `BrokerOrderCheck`
- `BrokerOrderResult`
- `BrokerPositionModificationRequest`
- `BrokerPositionCloseRequest`
- `BrokerMarginRequest`
- `BrokerProfitRequest`
- `BrokerFeeEstimate`
- `BrokerPage[T]`
- `BrokerResult[T]`
- `BrokerError`

### BRK-FR-CONTRACT-006 — Missing provider fields

A provider field that is unavailable must be represented as `null` or an explicit `UNKNOWN` enum value. It must not be replaced with zero, a default price, a default spread, a fake identifier, or a guessed value.

### BRK-FR-CONTRACT-007 — Numeric semantics

Prices, money, quantities, fees, margin, and P&L must use exact decimal-compatible values. Binary floating-point values from SDKs must be converted without inventing precision. When converting provider-native binary floating-point values to canonical Decimals, the adapter must first serialize the value to a string (e.g., `Decimal(str(provider_float))`) to prevent binary floating-point precision artifacts. The adapter must explicitly check for, and reject or sanitize, out-of-bounds numbers (such as `NaN` or `Infinity`) received from the provider: if the field is optional/nullable, it must be mapped to `null`; if the field is mandatory for a valid canonical contract (e.g. quote price), the adapter must treat it as a corrupted payload and return `BROKER_RESPONSE_INVALID` or raise `BrokerResponseInvalidException`.

### BRK-FR-CONTRACT-008 — Quantity units

Every quantity must identify its unit or interpretation, such as lots, contracts, base units, quote units, or coins. The adapter may perform only the provider translation required to submit or decode the request.

### BRK-FR-CONTRACT-009 — Time

All canonical timestamps must be timezone-aware UTC. Provider-native timestamps and timezones may be retained in metadata for traceability. The adapter is responsible for translating provider-native server timestamps (which may use broker-specific timezones, e.g., MT5 GMT+2/3) into canonical UTC. The adapter must not assume the provider timestamp is already UTC unless explicitly verified.

### BRK-FR-CONTRACT-010 — Pagination

List/history operations must return a canonical page containing records and the provider-derived next cursor where available. The domain must not perform unbounded whole-history downloads by default.

### BRK-FR-CONTRACT-011 — Standard Order Fields

The `BrokerOrder`, `BrokerOrderRequest`, and order-related mutation DTOs must support standard fields mapping provider features cleanly:
- `reduce_only` (bool): indicates whether the order is reduce-only.
- `post_only` (bool): indicates whether the order is post-only.
- `position_side` (enum: `LONG` | `SHORT` | `FLAT`): position side for platforms supporting hedging mode.
- `hedging_mode` (enum: `HEDGING` | `NETTING`): account-level execution mode.
- `margin_mode` (enum: `CROSS` | `ISOLATED`): margin allocation mode.
- `trigger_price_type` (enum: `LAST_PRICE` | `MARK_PRICE` | `INDEX_PRICE`): trigger source for conditional/stop orders.
- `trailing_stop_activation_price` (Decimal | None) & `trailing_stop_callback_rate` (Decimal | None): parameters for trailing-stop orders.
- `execution_policy` (enum: `GTC` | `IOC` | `FOK`): time-in-force fill policy.
- `self_trade_prevention_mode` (enum: `EXPIRE_TAKER` | `EXPIRE_MAKER` | `EXPIRE_BOTH` | `NONE`).
- `close_on_trigger` (bool): forces order closure upon trigger activation.
- `quote_quantity` (Decimal | None) vs `base_quantity` (Decimal | None): distinguishes size denominated in quote or base assets.
- `contract_multiplier` (Decimal | None): unit multiplier for derivatives/futures contracts.
- `leverage` (Decimal | None): requested leverage for the execution channel.
- `product_profile` (enum: `SPOT` | `MARGIN` | `FUTURES` | `CFD` | `FOREX`): product profile of the instrument.

### BRK-FR-CONTRACT-012 — Connection Events

The `BrokerConnectionEvent` DTO returned by `connection_events()` must contain:
- `previous_state` (enum representing previous lifecycle state).
- `new_state` (enum representing new lifecycle state).
- `reason` (str | None): description of why the change occurred (e.g. transport disconnect message).
- `timestamp` (datetime timezone-aware UTC).
- `session_generation` (int): monotonically increasing counter representing the logical connection instance.
- `reconnect_attempt` (int): transport reconnect attempt counter.
- `resynchronization_requirement` (bool): indicating whether a data resync is required.

### BRK-FR-CONTRACT-013 — Bar Semantics

The `BrokerBar` DTO must specify:
- `opening_timestamp` (datetime timezone-aware UTC).
- `closing_timestamp` (datetime timezone-aware UTC).
- `is_closed` (bool): whether the bar is closed or still forming.
- `trade_volume` (Decimal): actual traded base asset volume.
- `tick_volume` (Decimal): count of price changes.
- `provider_timeframe` (str): native provider interval.
- `requested_timeframe` (str): canonical timeframe requested by the caller.
- `timezone_conversion_evidence` (str | dict): original server time and timezone details used to produce the UTC timestamp.

### BRK-FR-CONTRACT-014 — Tick Semantics

The `BrokerTick` DTO must specify:
- `provider_sequence_id` (str | int | None).
- `event_timestamp` (datetime timezone-aware UTC).
- `provider_receipt_timestamp` (datetime timezone-aware UTC).
- `bid_price`, `bid_quantity`, `ask_price`, `ask_quantity`, `last_price` (Decimal | None).
- `tick_type` (enum: `TRADE` | `QUOTE` | `BLOCK` | `UNKNOWN`).

### BRK-FR-CONTRACT-015 — Order Book Semantics

The `BrokerOrderBook` DTO must specify:
- `is_snapshot` (bool): true if this is a full depth snapshot; false if this is an incremental update.
- `first_sequence_id` (int | None).
- `last_sequence_id` (int | None).
- `checksum` (str | None): checksum of depth levels for consistency validation.
- `depth_truncation` (int | None): level of book depth returned.
- `required_resnapshot` (bool): true if connection gaps or checksum mismatches require fresh snapshots.

### BRK-FR-CONTRACT-016 — Clock Skew and Latency Metadata

`get_server_time()` must return:
- `provider_time` (datetime timezone-aware UTC).
- `local_send_time` (datetime timezone-aware UTC): local time immediately before request submission.
- `local_receive_time` (datetime timezone-aware UTC): local time immediately after response receipt.
- `estimated_clock_offset` (float): local clock offset relative to the provider, computed as:
  `((provider_time - local_send_time) + (provider_time - local_receive_time)) / 2`
- `round_trip_latency` (float): round-trip duration in milliseconds.

Adapters must not correct business timestamps silently, but must expose this metadata so consumers can assess freshness.

### BRK-FR-CONTRACT-017 — DTO and Contract Versioning

All results, DTOs, and feature flag outputs must report:
- `contract_version` (str): semantic version of the Broker domain requirements contract.
- `adapter_version` (str): version of the concrete adapter implementation.
- `provider_api_version` (str | None): API version of the underlying platform.

Backward-compatibility policy requires that any enum expansion (e.g. new order types) must fail closed or fallback to explicit safe states, and any field deprecation must support a documented transition period.

---

## 8. Capability Requirements

### BRK-FR-CAP-001

The capability catalogue must contain one canonical identifier for every operation in Section 6.

### BRK-FR-CAP-002

Each adapter must publish a complete feature-flag report containing all catalogue entries, not only supported entries.

### BRK-FR-CAP-003 — Structured Capability Record

Each capability entry must be reported as a structured capability record, containing separate dimensions for implementation status, runtime availability, access modes, and validation status:
- `implementation_status`: `IMPLEMENTED` | `NOT_IMPLEMENTED`
- `availability`: `AVAILABLE` | `UNAVAILABLE` | `DEGRADED`
- `access_mode`: `READ` | `WRITE` | `READ_WRITE`
- `requirement`: `NONE` | `AUTHENTICATION` | `CONFIGURATION` | `PERMISSION`
- `verification_status`: `TESTED_SANDBOX` | `TESTED_LIVE` | `NOT_TESTED` (satisfying the verification tracking under `BRK-FR-TEST-001`)
- `reason`: `str | None` (describing why a capability is unavailable or degraded)

### BRK-FR-CAP-004

Capability status may vary by broker, environment, account type, permissions, market, SDK version, or credentials.

### BRK-FR-CAP-005

A feature-flag report must be refreshed after connection, authentication, account selection, permission changes, or provider version changes.

### BRK-FR-CAP-006

The adapter must not claim a capability as supported unless an implementation exists and its provider response path is covered by contract tests.

### BRK-FR-CAP-007

Unsupported capability behavior must be deterministic and must not depend on catching missing provider attributes at runtime.

### BRK-FR-CAP-008

To avoid interface bloat and support modular code design, the canonical `BrokerAdapter` interface shall be composed from fine-grained, trait-based capability groups (or mixins) that adapters explicitly declare they implement:
- `MarketDataProvider` (handles quotes, bars, ticks, order books, session/market status)
- `TradeExecutionProvider` (handles place_order, modify_order, cancel_order, replace_order, get_order, close_position, etc.)
- `AccountProvider` (handles account_info, balances, list_accounts, select_account, positions, asset info)
- `CalculationProvider` (handles margin, profit, and fee calculation estimates)

The composite `BrokerAdapter` protocol inherits from these interface traits. The registry may expose these narrower interfaces to consumers that only require specific subsets (e.g., a read-only consumer depending only on `MarketDataProvider`).

---

## 9. Registry and Adapter Resolution Requirements

### BRK-FR-REG-001

The domain must provide an explicit broker registry mapping canonical broker IDs to adapter factories.

### BRK-FR-REG-002

Adapter resolution must require an explicit broker ID. Unknown broker IDs must return `BROKER_UNKNOWN`.

### BRK-FR-REG-003

The registry must never silently default an unknown or unavailable broker to MT5 or any other provider.

### BRK-FR-REG-004

The registry must not select a provider based on symbol, route, environment, data availability, fallback priority, or business policy.

### BRK-FR-REG-005

Data owns data-source selection. Trading owns execution-broker selection. Brokers only resolves the explicit provider requested by the caller.

### BRK-FR-REG-006

The registry must support independent adapter instances for different accounts, credentials, environments, and concurrent sessions.

### BRK-FR-REG-007

A global singleton must not be the only supported lifecycle because it would allow account and credential state to leak between callers.

### BRK-FR-REG-008

Optional provider SDKs must be imported lazily so unavailable SDKs do not break unrelated providers.

### BRK-FR-REG-009 — Missing SDK dependency handling

A provider whose SDK package is not installed must remain registered but return `BROKER_DEPENDENCY_MISSING` upon connection attempts. The adapter must not map a missing SDK package to `BROKER_CAPABILITY_UNSUPPORTED` or `BROKER_CONFIGURATION_INVALID` (which would imply the provider itself lacks the feature or the inputs are wrong). The error payload must provide explicit dependency metadata fields including:
- `package_name` (str)
- `required_version` (str)
- `installed_version` (str)
- `installation_extra` (str)

### BRK-FR-REG-010 — Session ownership and adapter lifetime

The application composition root is responsible for creating adapter instances, and the caller (e.g. the specific execution runner or data fetcher) owns the adapter instance lifetime. The registry behaves strictly as a factory class, not a hidden singleton manager or connection pool.

### BRK-FR-REG-011 — Dependency injection and session sharing boundaries

Consuming domains (e.g., Data and Trading) may share a single adapter instance only through explicit, deterministic dependency injection. No implicit cross-domain session sharing or hidden global pool access is permitted, which is critical for terminal-based providers and per-account rate limits.

---

## 10. Connection and Authentication Requirements

### BRK-FR-CON-001

`connect()` must validate only connection-level configuration required by the selected provider.

### BRK-FR-CON-002

Credentials and secrets must be supplied by the caller through `BrokerConnectionConfig` or an injected secret reference. The Brokers domain must not query application user tables or persist credentials.

### BRK-FR-CON-003

Secrets must remain in memory only for the active adapter lifecycle unless the provider SDK manages its own secure token store.

### BRK-FR-CON-004

Secrets, access tokens, passwords, private keys, and full account identifiers must never be logged or included in errors.

### BRK-FR-CON-005

`connect()` success must mean provider connectivity and required authentication were actually verified. Setting a local Boolean flag is insufficient.

### BRK-FR-CON-006

The connection status must distinguish transport connection, application authentication, account authentication, trading permission, and subscription readiness where applicable.

### BRK-FR-CON-007

Calling an operation requiring connection while disconnected must return `BROKER_NOT_CONNECTED`. Public operations must not silently connect unless the caller explicitly enabled an adapter-level auto-connect option.

### BRK-FR-CON-008

`disconnect()` must close network sessions, terminal handles, subscriptions, reactors/tasks, and SDK resources owned by the adapter instance.

### BRK-FR-CON-009

`disconnect()` must be idempotent.

### BRK-FR-CON-010

`reconnect()` must not change provider, environment, credentials, or account unless the caller supplies a new configuration through a separate connection operation.

### BRK-FR-CON-011

Token refresh must use only provider-supported refresh flows. Failure must leave the adapter in a clearly reported unauthenticated or disconnected state.

### BRK-FR-CON-012

The adapter must detect provider disconnect events and update connection state without waiting for a subsequent business call.

### BRK-FR-CON-013

Multiple adapter instances must not share mutable connection/account/subscription state unless the shared provider runtime explicitly requires it and isolation is maintained.

### BRK-FR-CON-014 — Account selection concurrency and session isolation

The primary architectural design requires that one adapter instance represents one immutable provider, account, and environment session. Creating a new adapter instance is the preferred method for switching accounts.

Where the adapter supports runtime account switching via `select_account()`, it must prevent race conditions and state corruption under concurrent execution by implementing:
1. **Exclusive lifecycle lock**: The adapter must use an exclusive lock during the account switch transition.
2. **In-flight request cleanup**: All in-flight calls associated with the prior account must be cancelled or completed before the account change completes.
3. Monotonically increasing session generation: The adapter must maintain an internal monotonically increasing session generation counter.
4. **Rejection of stale responses**: Responses or callbacks received from requests sent prior to the account switch must be discarded based on the session generation counter.
5. **Subscription termination**: All account-bound subscriptions must be explicitly terminated during the transition.
6. **State invalidation**: After `select_account()`, any cached account-specific state (e.g., symbol lists, position snapshots, cached feature flags) must be invalidated, and the feature-flag report must be refreshed for the new account.

### BRK-FR-CON-015

The `BrokerConnectionConfig` DTO must support tuning of timeouts and buffers, containing at a minimum:
- `request_timeout_sec` (float)
- `connect_timeout_sec` (float)
- `transport_reconnect_max_attempts` (int) (for internal transport-level reconnects only, not business retries)
- `stream_buffer_size` (int) (bounds internal subscription queues)

Each adapter must honor these configurations or document its deviation in `get_feature_flags()`. This ensures operators can tune latency and safety behavior without knowing internal SDK details.

### BRK-FR-CON-016

When a session or token refresh fails, the adapter must immediately transition to `BROKER_AUTHENTICATION_FAILED`, cancel any pending in-flight requests with an appropriate error, and emit a connection status change event.

### BRK-FR-CON-017

In-flight subscription callbacks must receive a `BROKER_CONNECTION_LOST` event before the adapter attempts reconnection (if auto-reconnect is enabled).

### BRK-FR-CON-018

After a successful reconnect+refresh, subscriptions may be transparently resumed **only if** the provider and adapter guarantee no data loss during the disconnected interval; otherwise the adapter must raise `BROKER_SUBSCRIPTION_RESYNC_REQUIRED` and let the consumer rebuild subscriptions.

### BRK-FR-CON-019

The adapter should implement a transport-level circuit breaker. If the adapter detects consecutive transport/network failures, it must immediately return `BROKER_CONNECTION_LOST` or `BROKER_TIMEOUT` on subsequent calls without waiting for network timeouts, enabling fast failure and preventing thread/connection pool exhaustion.

### BRK-FR-CON-020

The adapter must support async context manager protocols (i.e. `async with`) to ensure deterministic resource cleanup. The `__aenter__` method shall trigger `connect()` if not already connected, and `__aexit__` must guarantee `disconnect()` is called and resources are released, even if unhandled exceptions occur in the consumer domain.

### BRK-FR-CON-021

If a provider returns scheduled maintenance headers or indicates active downtime, the adapter must update `get_connection_status()` status to reflect maintenance mode preemptively and return `BROKER_MAINTENANCE_MODE` on subsequent requests.

### BRK-FR-CON-022

If a provider protocol requires periodic pings or heartbeats to keep a session (e.g. WebSocket or socket terminal connection) active, the adapter must manage this keep-alive lifecycle internally using a background async task. Consuming domains must not be required to periodically poll `ping()` to prevent connection drops.

### BRK-FR-CON-023 — Explicit Connection Lifecycle State Machine

To prevent race conditions, state corruption, or duplicate socket allocations under concurrent asynchronous execution, the adapter must implement an internal, thread-safe lifecycle state machine.
1. **Explicit States**: The state machine must support at least the following states:
   - `DISCONNECTED`: Initial state; no resources allocated.
   - `CONNECTING`: Transport socket or terminal connection is being established.
   - `CONNECTED`: Network transport is active; authentication has not yet occurred.
   - `AUTHENTICATING`: Security credentials/tokens are being verified.
   - `READY`: Authenticated, features queried, and ready for queries or mutations.
   - `DEGRADED`: Network loss, queue backpressure, or rate-limiting throttling active.
   - `RECONNECTING`: Attempting socket recovery after an unexpected disconnect.
   - `MAINTENANCE`: Preemptive or active provider downtime state.
   - `CLOSING`: Releasing subscriptions, connection threads, and socket handles.
   - `FAILED`: Terminal error state (e.g. invalid credentials or lost host).
2. **Valid State Transitions**: Only the following state transitions are permitted:
   - `DISCONNECTED` → `CONNECTING`
   - `CONNECTING` → `CONNECTED` | `FAILED` | `CLOSING`
   - `CONNECTED` → `AUTHENTICATING` | `FAILED` | `CLOSING`
   - `AUTHENTICATING` → `READY` | `FAILED` | `CLOSING`
   - `READY` → `DEGRADED` | `RECONNECTING` | `MAINTENANCE` | `CLOSING` | `FAILED`
   - `DEGRADED` → `READY` | `RECONNECTING` | `CLOSING` | `FAILED`
   - `RECONNECTING` → `READY` | `FAILED` | `CLOSING`
   - `MAINTENANCE` → `RECONNECTING` | `DISCONNECTED` | `CLOSING`
   - `CLOSING` → `DISCONNECTED`
   - `FAILED` → `CONNECTING` | `DISCONNECTED`
3. **Execution Semantics**:
   - Any mutation call attempted while the state is `CONNECTING` or `RECONNECTING` must either fail immediately with `BROKER_NOT_CONNECTED` or block deterministically up to the request timeout.
   - A transition to `FAILED` or `DISCONNECTED` must cancel all in-flight read and mutation operations immediately with the corresponding canonical error.

### BRK-FR-CON-024 — Connection recovery vs operation retries

The adapter must distinguish connection recovery from business-level or operational retries:
- **Connection recovery**: The adapter may automatically re-establish/reconnect the underlying socket/transport connection up to `transport_reconnect_max_attempts`.
- **Read operations**: The adapter must never automatically replay read operations interrupted by connection drops, unless the provider SDK guarantees the request was never transmitted.
- **Mutation operations**: The adapter must never automatically retry or replay order mutations.
- **Interrupted operations**: A reconnect attempt does not imply retrying any interrupted operations. Operations interrupted during a reconnect phase must fail immediately and return the corresponding transport/connection error.
- **Uncertain transmission**: Any mutation operation interrupted with uncertain transmission state (where the adapter cannot guarantee the provider did not receive/process the order) must return error code `BROKER_UNKNOWN_OUTCOME` to prevent duplicate execution.

### BRK-FR-CON-025 — Provider Environment Safety

To prevent catastrophic execution mismatches (e.g., executing live trades in a sandbox or demo environment):
1. **Explicit Environment Configuration**: The adapter configuration must require an explicit environment name (`LIVE` | `DEMO` | `TESTNET` | `SANDBOX`). No implicit default to `LIVE` is permitted.
2. **Connection Mismatch Protection**: Mismatch between the requested environment name and the provider endpoint URL/account details must result in a connection failure returning `BROKER_CONFIGURATION_INVALID`.
3. **Immutability**: Once `connect()` succeeds, the environment type and account fingerprint are immutable for that adapter instance. Mutation requests must not accept environment overrides; mutations operate strictly in the session's connected environment.
4. **Traceability**: All logs, errors, and returned `BrokerResult[T]` headers must contain the immutable environment tag.

### BRK-FR-CON-026 — Connection event streaming

The adapter must expose `connection_events() -> AsyncIterator[BrokerConnectionEvent]` to allow consuming domains (such as Data and Trading) to monitor connection lifecycle changes. The adapter must yield a new `BrokerConnectionEvent` DTO on every state transition of the connection lifecycle state machine.

---

## 11. Read Operation Requirements

### BRK-FR-READ-001

Each operation must perform the minimum bounded provider interaction required by the provider protocol (e.g. to support authentication refresh, symbol resolution, pagination, snapshot/sequence initialization, or protocol-mandated handshakes). Hidden business orchestration and unbounded request fan-out are forbidden.

### BRK-FR-READ-002

All read operations must strictly adhere to the out-of-scope boundaries defined in `BRK-FR-OWN-001` (Section 3.2). Specifically, the domain must not maintain business-level or reusable data caches (e.g. caching historical bars, account snapshots, or normalized quotes), must not fall back to other providers, and must not resample, synthesize, or estimate data. Provider-required technical/session caches are permitted when bounded, instance-scoped, observable, and invalidated correctly.

### BRK-FR-READ-005

Provider-native symbol aliases may be translated only through explicit adapter mappings. Symbol-discovery and canonical market identity policy belong to Data.

### BRK-FR-READ-006

An empty valid provider result must return successful empty data, distinct from connection, permission, unsupported, and provider errors.

### BRK-FR-READ-007

The adapter must preserve broker order, position, deal, and account identifiers exactly as supplied by the provider.

### BRK-FR-READ-008

Provider response truncation or page limits must be explicit in the canonical page metadata.

### BRK-FR-READ-009

Any malformed provider response must return `BROKER_RESPONSE_INVALID`; the adapter must not manufacture a success payload.

---

## 12. Mutation Requirements

### BRK-FR-MUT-001

Mutation methods perform direct provider submission only. They must not decide whether an order should be placed.

### BRK-FR-MUT-002

The caller must supply the complete canonical mutation request. Brokers may perform provider-required structural conversion only.

### BRK-FR-MUT-003

All mutation operations must strictly adhere to the out-of-scope boundaries defined in `BRK-FR-OWN-001` (Section 3.2). Specifically, the domain must not evaluate risk approval, kill-switch status, or user authorization (Trading must complete those checks before calling Brokers).

### BRK-FR-MUT-004

The adapter may validate provider-required fields and reject structurally invalid requests with `BROKER_REQUEST_INVALID`.

### BRK-FR-MUT-005

The canonical order request must support the direct provider fields needed across platforms, including symbol, side, order type, quantity and quantity unit, limit/stop price where applicable, stop loss, take profit, time in force, expiration, permitted deviation/slippage, client request/order ID, label/magic number/comment, account reference, and provider environment. Fields unavailable or irrelevant to a provider remain optional; the adapter must not infer trading intent or calculate missing values.

The adapter must transmit caller-supplied client request IDs, client order IDs, labels, magic numbers, or comments when the provider supports them.

### BRK-FR-MUT-006

The domain must not generate business idempotency keys. It may generate a transport correlation ID only when the provider requires one and the caller did not supply it. The adapter must map the caller-supplied `client_request_id` to the provider’s native idempotency/client-order-id field (e.g., Binance's `newClientOrderId`, cTrader's `ctidClientOrderId`, MT5's `Magic`/`Comment`) where supported, ensuring the caller can reconcile unknown outcomes using their own key.

### BRK-FR-MUT-007

Mutation success must be based on explicit provider acknowledgement. Local packaging, queueing, or request transmission alone is not success.

### BRK-FR-MUT-008

The adapter must not fabricate accepted order IDs, deal IDs, fills, prices, or success codes.

### BRK-FR-MUT-009

A timeout or connection loss after a mutation may have reached the provider must return `BROKER_UNKNOWN_OUTCOME`.

### BRK-FR-MUT-010

In accordance with `BRK-FR-OWN-001` (Section 3.2), the Brokers domain must not implement business retry policies for mutations. Trading owns all reconciliation and retry policy.

### BRK-FR-MUT-011

Provider rejections must be returned as `BROKER_REQUEST_REJECTED` with the redacted provider code and message.

### BRK-FR-MUT-012

Partial fills and partial closes must be represented exactly as returned by the provider.

### BRK-FR-MUT-013

A mutation method must affect only the one order or position identified in the request.

### BRK-FR-MUT-014

In accordance with `BRK-FR-OWN-001` (Section 3.2), the domain must not provide automatic bulk mutations, liquidations, averaging, or complex multi-leg strategy execution.

### BRK-FR-MUT-015

Provider-side order validation or preview must be exposed through `check_order()` and must not be represented as final order acceptance.

---

## 13. Subscription Requirements

### BRK-FR-SUB-001

Each successful subscription must return a unique adapter-scoped subscription ID.

### BRK-FR-SUB-002

Subscription callbacks/events must use canonical broker event DTOs and must not expose provider SDK message objects.

### BRK-FR-SUB-003

The adapter must report disconnect, resubscription-required, provider-error, and permission-change events to the subscriber.

### BRK-FR-SUB-004

Automatic resubscription may occur only when it cannot cause a broker mutation and the adapter reports the reconnection event. The adapter is responsible for transparently reconnecting the underlying WebSocket/transport socket. However, if the provider does not guarantee snapshot consistency upon reconnection (e.g., missed ticks during the drop), the adapter must emit `BROKER_SUBSCRIPTION_RESYNC_REQUIRED` so the caller can request a fresh snapshot.

### BRK-FR-SUB-005

Unsubscribing an unknown subscription must return a deterministic not-found result and must not affect other subscriptions.

### BRK-FR-SUB-006

`disconnect()` must terminate all subscriptions owned by that adapter instance.

### BRK-FR-SUB-007

The adapter must not persist event streams or subscription data.

### BRK-FR-SUB-008 — Bounded Event Buffer and Overflow Semantics

The adapter must implement a bounded event buffer per subscription, with a size configurable via the `stream_buffer_size` parameter in `BrokerConnectionConfig`. For market-critical streams, silently dropping the oldest event is forbidden.
When buffer overflow occurs (e.g. because a consumer falls behind):
1. **Emit Backpressure Event**: The adapter must immediately emit a `BROKER_BACKPRESSURE` event containing the lost sequence range.
2. **Degrade Lifecycle State**: The state machine must transition to `DEGRADED`.
3. **Trigger Resync**: The subscription must require the caller to trigger a full resynchronization (returning `BROKER_SUBSCRIPTION_RESYNC_REQUIRED` on subsequent reads or updates).

### BRK-FR-SUB-009 — Streaming Delivery and Callback Semantics

To ensure safety and deterministic delivery:
1. **AsyncIterator Preferred**: The primary method of consuming stream events is via an `AsyncIterator` yielding canonical events from the bounded queue, rather than executing user-supplied callbacks directly inside adapter tasks.
2. **Ordering Guarantees**: Strict FIFO (First-In, First-Out) ordering must be preserved for all events within a subscription stream.
3. **Sequence Numbers & Duplication**: All events must contain monotonically increasing sequence numbers. The adapter must utilize provider sequence numbers to filter out duplicate events.
4. **Callback Isolation**: If callbacks are utilized, any exception raised in the consumer callback must be caught and logged at `ERROR` level, ensuring it does not crash the adapter stream listener loop.
5. **Slow Callbacks & Concurrent Execution**: Stream listener tasks must not execute consumer callbacks blocking the main network thread. Callback execution for a single subscription must run sequentially to preserve ordering, while separate subscriptions can execute concurrently.
6. **Post-Unsubscribe Discarding**: Immediately upon calling `unsubscribe()`, the adapter must discard any further incoming events for that subscription, even if they were already queued.
7. **Snapshot vs Incremental Flags**: Event payloads must explicitly flag whether they represent a full snapshot or an incremental delta update (e.g., in order book or position streams).

---

## 14. Provider-Specific Requirements

### BRK-FR-PROV-001

Each provider module must contain only:

- provider SDK imports;
- provider configuration mapping;
- adapter lifecycle state;
- provider request construction;
- provider response decoding;
- provider-to-canonical DTO mapping;
- provider-to-canonical error mapping;
- capability declarations;
- provider-specific private helpers required by these operations.

### BRK-FR-PROV-002

Provider modules must strictly adhere to the out-of-scope ownership boundaries defined in `BRK-FR-OWN-001` (Section 3.2). Specifically, they must not contain cross-provider routing, source fallback, presentation logic, persistence, user database lookup, or domain orchestration.

### BRK-FR-PROV-003

Each adapter must implement every standard public operation, including unsupported methods.

### BRK-FR-PROV-004

Provider-specific extension methods must remain private unless added to the canonical contract for all adapters.

### BRK-FR-PROV-005

Provider-native constants must not become the cross-domain public contract. Canonical enums and DTOs must be used.

### BRK-FR-PROV-006

MT5 and cTrader compatibility must be achieved through canonical contracts, not by pretending one provider is the other or copying another provider's numeric constants.

### BRK-FR-PROV-007

Yahoo Finance ticks must return unsupported unless the selected Yahoo integration supplies genuine provider tick data. Synthetic ticks are forbidden in Brokers.

### BRK-FR-PROV-008

Dukascopy trading methods must return unsupported unless a genuine authenticated trading API is implemented and verified.

### BRK-FR-PROV-009 — Binance Product Profiles

Rather than using a single Binance adapter instance whose fundamental semantics and API endpoints change dynamically at runtime, the domain must define separate immutable provider profiles:
- `BINANCE_SPOT`
- `BINANCE_USD_M_FUTURES`
- `BINANCE_COIN_M_FUTURES`

An adapter instance must be initialized for one explicit profile and remain immutable. The registry must resolve these as distinct provider types. Binance account and mutation capabilities must be determined from the configured API permissions and the immutable profile type.

### BRK-FR-PROV-010

No provider adapter may advertise trading capability solely because its SDK contains an order method; authenticated permission and a tested response path are required.

---

## 15. Public Package Requirements

### BRK-FR-API-001

`app/services/brokers/__init__.py` must expose only canonical contracts, registry/factory entry points, capability identifiers, and approved adapter types.

### BRK-FR-API-002

`__init__.py` must contain no connection, provider, routing, conversion, or business logic.

### BRK-FR-API-003

The preferred domain entry points must be:

- `create_broker_adapter(broker_id, config) -> BrokerAdapter`
- `get_registered_brokers()`
- `get_broker_capability_catalogue()`

Consumers must obtain adapters through this registry/factory and must not instantiate concrete provider classes directly.

### BRK-FR-API-004

Consumers must import the public domain API rather than provider implementation files, except provider-specific integration tests.

### BRK-FR-API-005

The domain must not expose AI tools directly. Data, Trading, or UI/API may expose governed tools that call their own business workflows.

### BRK-FR-API-006

The package must expose a canonical `FakeBrokerAdapter` (or `MockBrokerAdapter`) in its test utilities. It must implement the full `BrokerAdapter` protocol, return deterministic canonical DTOs, and allow tests to inject specific errors (e.g., force a specific outcome or exception on any selected operation) to support fast, non-networked unit testing in calling domains.

---

## 16. Logging and Observability Requirements

### BRK-FR-OBS-001

The domain must log connection transitions, authentication outcomes, provider calls, provider errors, subscription transitions, and mutation acknowledgements.

### BRK-FR-OBS-002

Logs must include broker ID, operation, request/correlation ID, environment, redacted account reference, result status, provider code, and latency where applicable.

### BRK-FR-OBS-003

Logs must never include secrets or complete private account credentials.

### BRK-FR-OBS-004

Every broker interaction must be technically reconstructable using timestamp, broker/adapter name, operation, correlation ID, redacted request payload, redacted response payload or canonical error, provider references, and latency.

Normal application logs must record redacted payload summaries rather than complete bodies. Full payload capture is permitted only in an explicitly configured secure broker-audit sink with field-level secret redaction, access control, retention limits, and encryption. Secrets, tokens, private keys, and authentication material must never be captured.

### BRK-FR-OBS-005

Unknown mutation outcomes must be logged at error severity with enough provider references for Trading to reconcile.

### BRK-FR-OBS-006

The adapter internals and `BrokerResult` must support distributed tracing by propagating OpenTelemetry (or equivalent) trace contexts. The canonical `request_id` should represent or include the W3C Trace ID when available from the calling context.

---

## 17. Non-Functional Requirements

### BRK-NFR-001 — Zero business logic

The domain must contain zero business logic and must strictly adhere to the out-of-scope ownership boundaries defined in `BRK-FR-OWN-001` (Section 3.2).

### BRK-NFR-002 — Thread and concurrency safety

Each adapter must be safe for concurrent use without state corruption. Where an SDK or terminal is inherently single-threaded, the adapter must serialize provider access internally and publish its concurrency limits through `get_feature_flags()`. Calling domains must not need provider-specific synchronization logic.

### BRK-NFR-003 — Minimal overhead

Canonical marshaling, error wrapping, correlation, and technical telemetry must add minimal overhead and must not introduce unnecessary copying, calculations, or network calls.

### BRK-NFR-004 — Domain independence

The Brokers domain must compile, test, and operate independently of Data, Trading, Risk, Strategy, and every other business domain. Its public contracts must be owned locally or by the lower-level Utils/shared-kernel domain.

### BRK-NFR-005 — Extensibility

Adding a provider must require only implementing the complete canonical adapter, declaring verified feature flags, adding provider-specific tests, and registering its factory. No source changes may be required in Data, Trading, or other consumers.

### BRK-NFR-006 — Deterministic unsupported behavior

Unsupported methods must fail immediately and consistently without a provider call, approximation, synthetic substitute, or provider-type branch in consuming domains.

### BRK-NFR-007 — Performance budgets and latency observability

The adapter must minimize overhead to keep the domain viable for low-latency execution.
1. **Measurable Budgets**: Concrete DTO mapping must satisfy a p99 latency budget of < 100 microseconds under normal operation.
2. **No Event-Loop Blocking**: Under no circumstances shall DTO serialization, mapping, or local parsing block the asyncio event loop.
3. **Bounded Allocation**: DTO construction and response wrapping must use bounded copying and allocation rather than unbounded deep copies. Zero-copy is not required where it violates DTO ownership, type safety, or numeric/timezone conversions.
4. **Separated Latency telemetry**: The adapter must capture and report provider-network latency and local adapter wrapping overhead separately in `BrokerResult` metadata.

### BRK-NFR-008 — Blocking SDK isolation

Adapters wrapping blocking SDKs (e.g., MT5) must isolate provider calls in a dedicated thread executor (e.g., using `asyncio.to_thread`) and must publish this execution model in `get_feature_flags()` so consumers know not to block the main event loop.

---

## 18. Mandatory Boundary Tests

Every provider adapter must pass the same contract test suite.

### 18.1 Contract tests

- Every standard method exists.
- Method signatures match the canonical protocol.
- Success results match canonical DTOs.
- Error results match `BrokerError`.
- Unsupported methods return `BROKER_CAPABILITY_UNSUPPORTED`.
- Unsupported methods make no SDK call.
- Raw SDK objects never escape.
- Missing provider values remain `null`/`UNKNOWN`.
- Empty results are distinct from errors.
- Timestamps are UTC.
- Numeric values preserve decimal semantics.

### 18.2 Connection tests

- Real verification is required before connected state is reported.
- Authentication failure is distinct from transport failure.
- Disconnect is idempotent.
- Connection loss updates state.
- Multiple accounts/adapters remain isolated.
- Secrets are redacted from logs and errors.

### 18.3 Mutation tests

- Provider rejection is not packaged as success.
- Missing provider acknowledgement is not success.
- No fallback order or deal IDs are generated.
- Timeout after possible transmission returns `BROKER_UNKNOWN_OUTCOME`.
- Unknown-outcome mutations are not retried by Brokers.
- One mutation affects only one target.
- Partial fills remain partial.

### 18.4 Domain-boundary tests

- Brokers imports no business domain.
- Brokers performs no database access.
- Brokers performs no caching or data persistence.
- Brokers performs no risk or approval checks.
- Brokers performs no source or execution-route selection.
- Brokers generates no synthetic market data.
- Data and Trading consume the canonical broker interface rather than provider SDKs.

### 18.5 Sandbox integration tests

**BRK-FR-TEST-001**: Every adapter shall include a suite of sandbox integration tests covering all capabilities marked `SUPPORTED`. Those tests must be run as part of the CI/CD pipeline against provider test environments, sandboxes, or testnets to verify actual provider behavior before release.

---

## 19. Required Initial Capability Matrix

Implementation must maintain a tested matrix similar to the following. Values are determined from the actual SDK/API and configured account, not assumed in this document.

| Capability group | MT5 | cTrader | Binance Spot | Binance USD-M Futures | Binance Coin-M Futures | Dukascopy | Yahoo |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Connection/authentication | Declared by adapter | Declared by adapter | Declared by adapter | Declared by adapter | Declared by adapter | Declared by adapter | Declared by adapter |
| Account reads | Declared by adapter | Declared by adapter | Declared by adapter | Declared by adapter | Declared by adapter | Declared by adapter | Declared by adapter |
| Symbols/metadata | Declared by adapter | Declared by adapter | Declared by adapter | Declared by adapter | Declared by adapter | Declared by adapter | Declared by adapter |
| Bars | Declared by adapter | Declared by adapter | Declared by adapter | Declared by adapter | Declared by adapter | Declared by adapter |
| Genuine ticks | Declared by adapter | Declared by adapter | Declared by adapter | Declared by adapter | Declared by adapter | Declared by adapter | Declared by adapter |
| Streaming | Declared by adapter | Declared by adapter | Declared by adapter | Declared by adapter | Declared by adapter | Declared by adapter | Declared by adapter |
| Positions/orders/deals | Declared by adapter | Declared by adapter | Declared by adapter | Declared by adapter | Declared by adapter | Declared by adapter | Declared by adapter |
| Trading mutations | Declared by adapter | Declared by adapter | Declared by adapter | Declared by adapter | Declared by adapter | Declared by adapter | Declared by adapter |
| Margin/profit/fee calculations | Declared by adapter | Declared by adapter | Declared by adapter | Declared by adapter | Declared by adapter | Declared by adapter | Declared by adapter |

The matrix must be generated from the adapters' capability declarations and verified by tests. It must not be manually maintained in multiple places. Each capability in the matrix must also report a corresponding `Sandbox Test Status` (e.g. `TESTED_SANDBOX` or `NOT_TESTED`) to satisfy the testing verification under `BRK-FR-TEST-001`.

---

## 20. Cross-Domain Workflow Boundaries

### 20.1 Data acquisition

```text
Data selects explicit source
→ Data creates/obtains Broker adapter
→ Data calls broker read operation
→ Brokers returns direct canonical provider response
→ Data validates, normalizes, aligns, caches, persists, and exposes MarketDataset
```

Brokers ends at the direct canonical provider response. Data obtains the adapter through `create_broker_adapter()` and contains no concrete provider-class imports or broker-type branches.

### 20.2 Live or paper execution

```text
Trading receives approved RiskDecision
→ Trading validates token, kill switch, readiness, idempotency, and route policy
→ Trading creates canonical broker mutation request
→ Trading selects explicit broker/account/environment
→ Brokers sends direct provider request
→ Brokers returns direct provider acknowledgement/error
→ Trading determines execution state, reconciles, persists, and handles incidents
```

Brokers does not know whether the caller labels the workflow live or paper. It connects to the explicit provider environment/account supplied in `BrokerConnectionConfig`. Trading obtains the adapter through `create_broker_adapter()`, may inspect `get_feature_flags()` before calling an optional operation, and handles canonical unsupported outcomes without concrete provider knowledge.

### 20.3 Account-state snapshots

```text
Data or Trading requests direct account/position/order state
→ Brokers reads provider truth
→ Caller validates freshness and builds its owned snapshot/reconciliation model
```

Brokers does not persist or certify snapshot freshness beyond reporting the provider timestamp and retrieval timestamp.

---

## 21. Explicitly Forbidden Behaviours

The Brokers domain must never:

1. silently choose a different broker;
2. silently switch from live to demo or demo to live;
3. silently fall back from genuine ticks to synthetic ticks;
4. fabricate bid, ask, spread, price, fill, order ID, deal ID, balance, equity, margin, or connection status;
5. return success when only local request packaging succeeded;
6. retry a mutation whose provider outcome is unknown;
7. place orders without an explicit caller request;
8. close or cancel multiple positions/orders from one primitive call;
9. read application databases for credentials or user details;
10. persist broker data, account state, orders, or connection state;
11. enforce risk, authorization, approval-token, or kill-switch policy;
12. normalize or clean market data beyond structural provider-to-canonical field mapping;
13. maintain business-level or reusable data caches, resample, aggregate, backfill, or merge provider data (technical/session caches needed for protocol operations are permitted);
14. expose raw SDK/protobuf/terminal objects;
15. depend on Data, Trading, Risk, or any higher business domain;
16. omit a canonical interface method or expose a generic `NotImplementedError`;
17. require a consumer to branch on concrete provider type.

---

## 22. Definition of Done

The Brokers domain is complete when:

- [ ] `app/services/brokers` exists as an independent domain below Data and Trading.
- [ ] PROJECT.md and the relevant ADRs no longer assign broker connection ownership to Data.
- [ ] The public canonical `BrokerAdapter` contract is defined and versioned.
- [ ] Every provider adapter implements every standard operation.
- [ ] Unsupported operations return `BROKER_CAPABILITY_UNSUPPORTED` consistently or are converted by the strict façade into `BrokerNotSupportedException`.
- [ ] No adapter omits a canonical method or raises generic `NotImplementedError`.
- [ ] The broker registry requires an explicit provider and never defaults unknown values.
- [ ] All provider responses use identical canonical DTOs, enums, UTC timestamps, units, and decimal-compatible numeric semantics.
- [ ] Original provider values and identifiers remain traceable without leaking SDK objects.
- [ ] No raw SDK object crosses the boundary.
- [ ] No synthetic or fabricated broker truth is produced.
- [ ] No business-domain logic exists in Brokers.
- [ ] No credential persistence or database access exists in Brokers.
- [ ] Data owns normalization, caching, persistence, fallback, and datasets.
- [ ] Trading owns approved mutation workflow, idempotency, timeouts, reconciliation, and execution persistence.
- [ ] Risk remains the independent approval authority.
- [ ] All adapters pass the shared contract test suite.
- [ ] Provider-specific integration tests verify every capability marked `SUPPORTED`.
- [ ] Domain-boundary import tests prove Brokers depends only on Utils and provider libraries.
- [ ] End-to-end Data and Trading integration tests use the canonical broker interface.

---

## 23. Required Project Documentation Changes

This requirement changes the current system-level design and therefore requires:

1. Add **Brokers** to the Domain Capability Map.
2. Add **Brokers** to the Domain Registry immediately after Utils.
3. Change Data so it consumes Brokers and no longer owns broker connection lifecycle or credential-backed execution channels.
4. Change Trading so it calls Brokers directly for approved provider mutations.
5. Replace `BrokerExecutionChannel` ownership by Data with the canonical Brokers-domain contract.
6. Update compile-time dependency diagrams to include `Utils ←── Brokers ←── Data`, `Brokers ←── Trading`, `Risk ←── Strategy/Trading`, and `Data ←── Trading`.
7. Update live/paper workflows so the provider call is `Trading → Brokers → external broker`.
8. Update account/market-data workflows so the provider call is `Data → Brokers → external provider`.
9. Create an ADR superseding the previous MT5-access split and connection-ownership decision.
10. Create `app/services/brokers/README.md` as the authoritative domain document.
