## Phase 7 Trading Service

### Goal

The Trader service layer provides the dedicated trading boundary for HaruQuantAI.

The module exposes a unified trading interface supporting MT5, cTrader, and Simulator providers through `app/routes/brokers.py`.

The Trader services own broker-compatible trading operations, validation, execution readiness checks, reconciliation support, and trading state retrieval while maintaining MQL5-compatible behavior where applicable.

Task inventory: 91 checkbox tasks (75 checked, 16 unchecked).

### Dependency Files and Functionality


Required functionality:

- Pre-trade risk governor limits check and sizing calculations are available.
- Analytics trade logging and equity reporting formats are accessible.
- Central errors, standard response wrapper, and trace identifiers exist.


### Functionality to Implement

Tasks are grouped by domain functionality. Each requirement is now part of its corresponding functional contract.

#### Live Order Executor and Broker Integration

- [ ] Implement core order-lifecycle operations: submit market orders, submit pending orders, modify pending orders, cancel pending orders, and close positions fully or partially.
  - Submit market orders.
  - Submit pending orders.
  - Modify pending orders.
  - Cancel pending orders.
  - Close positions fully or partially. *Pending: `Trade.position_close` supports full close only; no partial close volume parameter is implemented.*
- [ ] Implement kill-switch trading-halt behavior.
  - Kill-Switch Behavior**: Under active kill-switch status, block all new trade requests, cancel all active pending orders immediately, and support a configurable option to flatten all open positions.
- [ ] Align order types, trade request fields, and fill policies with MQL5 trade contracts.
  - Align order types precisely: Market, Limit, and Stop orders.
  - Align trade request field naming to mirror MQL5 `MqlTradeRequest` structure.
  - Implement fill policies (Fill or Kill, Immediate or Cancel, Return) mirroring MQL5's `CTrade` and `OrderSend` contracts.
- [ ] Propagate correlation, trace, and request IDs across all trading requests, responses, and events.
  - Correlation IDs**: All requests, responses, and events must propagate structural correlation, trace, and request IDs.
- [ ] Implement shutdown order-stop behavior.
  - Stop accepting new trade requests immediately.
  - Cancel any locally tracked pending orders that have not been acknowledged by the broker. *Pending: `TradeStore` has no active order delete/acknowledgement lifecycle API.*

#### Input Parameter Validation Helpers

- [ ] Modify stop-loss/take-profit levels and return execution/fill details in the result envelope.
  - Modify stop-loss and take-profit levels.
  - Return execution/fill details (filled volume, average price, remaining volume) in the result envelope.
- [ ] Validate trade requests against symbols, volumes, prices, SL/TP geometry, margin, expiration, broker constraints, malicious payloads, and slippage tolerance.
  - Validate symbols.
  - Validate trade volumes.
  - Validate prices.
  - Validate stop-loss and take-profit geometry.
  - Validate margin requirements.
  - Validate order requests against malicious payloads and out-of-bound arguments.
  - Validate expiration values. *Pending: pending-order expiration is passed through without dedicated validation.*
  - Validate broker constraints.
  - Validate slippage against a configurable tolerance, rejecting/warning if exceeded.
- [ ] Retrieve and cache the account dealing mode, and validate dealing-mode compatibility for modification/closure requests.
  - Retrieve account dealing mode (Netting vs. Hedging) and cache it. *Pending: `AccountInfo.margin_mode()` retrieves the mode, but no cache/lifecycle invalidation is implemented.*
  - Dealing Mode Check**: Validate that position modification and closure requests are compatible with the cached account dealing mode (Netting vs. Hedging). *Pending: `ValidationService.validate_dealing_mode_compatibility` is present but does not enforce compatibility rules.*
- [ ] Retrieve symbol information.
- [ ] Validate market session eligibility for the requested trading action.
  - Market Session Check**: Validate that the requested action is allowed during current active market sessions (e.g., prevent new positions during weekend rollover, even if connected).
- [ ] Normalize prices, volumes, and SL/TP to broker-specific decimal precision and volume-step rules before routing.
  - Decimal & Precision Normalization**: Ensure that all financial values (price, volume, SL/TP) are parsed into high-precision decimal objects and rounded/truncated according to the broker's specific digits and volume step parameters before routing.
- [ ] Aggregate execution-readiness checks: broker connectivity, market availability, account permissions/readiness, margin availability, and rate-limit health.
  - Validate broker connectivity.
  - Validate market availability.
  - Validate account permissions.
  - Validate account readiness.
  - Validate margin availability.
  - Aggregate readiness checks before execution.
  - Verify rate limit health as part of the execution readiness checks.
- [ ] Compute idempotency keys from a defined hash of request attributes.
  - Idempotency Key Scope**: Compute idempotency keys using a hash of specific request attributes: `(account_id, symbol, action_type, volume, price, slippage, timestamp_window)`.
- [ ] Fail closed on invalid readiness conditions, active kill-switch status, or a blocked startup reconciliation gate.
  - Fail-Closed**: Trading operations shall fail closed on invalid readiness conditions, active kill-switch status, or if the startup reconciliation gate is blocked.
- [ ] Serialize trading requests within the same (account, symbol) scope to prevent interleaved state modification.
  - Serialized Execution**: Trading requests within the same `(account, symbol)` scope must be executed sequentially (e.g., serialized via an async lock or queue) to prevent interleaved state modification.
- [ ] Strictly type, sanitize, and validate all broker-bound parameters before leaving the trading boundary.
  - Parameter Sanitization**: All broker-bound parameters must be strictly typed, sanitized, and validated before leaving the trading boundary.
- [ ] Add contract tests validating the broker adapter interface against actual broker API behaviors.
  - Contract Tests**: Validate the broker adapter interface against actual broker API behaviors to catch breaking upstream changes. *Pending: focused unit tests mock broker behavior; no provider contract test suite exercises actual adapter API behavior.*

#### Trade Reporting and Trade Journal Sinks

- [ ] Return partial fill details directly to the Strategy/Risk caller rather than auto-chasing, with configurable behavior support.
  - Partial Fill Strategy**: Return partial fill details directly to the Strategy/Risk caller rather than auto-chasing, with configurable behavior support.
- [ ] Generate trading reports including validation warnings.
  - Generate trading reports.
  - Include validation warnings.
- [ ] Alerting Rules**:
- [ ] Propagate trace context through broker calls and redact secrets/credentials/tokens from logs and telemetry.
  - Telemetry**: Propagate trace context through broker calls if supported by the provider SDK.
  - Redaction**: Secrets, credentials, and API tokens must be redacted and never leaked to logs, error messages, or telemetry.

#### Position and Order Reconciliation Engine

- [ ] Retrieve account, position, pending-order, historical-order, historical-deal, and terminal information for reconciliation.
  - Retrieve account information.
  - Retrieve position information.
  - Retrieve pending order information.
  - Retrieve historical order information.
  - Retrieve historical deal information.
  - Retrieve terminal information.
- [ ] Detect missing and mismatched records and include reconciliation summaries.
  - Detect missing records.
  - Detect mismatched records.
  - Include reconciliation summaries.
- [ ] Run reconciliation on startup, on unknown-outcome errors, and on a configurable schedule; block trading until the initial pass succeeds.
  - Run scheduled reconciliation at configurable intervals (e.g., every N minutes). *Pending: reconciliation is invoked on startup/unknown outcome paths, but no scheduler integration exists.*
  - Trigger reconciliation on startup and immediately following any "unknown outcome" broker error.
  - Support a flag that blocks trading execution until the initial reconciliation pass completes successfully.
  - Startup Reconciliation Gate**: Trading execution must be blocked at startup until the initial reconciliation pass completes successfully.
- [ ] Prevent unsafe retries after unknown-outcome errors and enforce explicit broker-call timeouts that trigger forced reconciliation.
  - Prevent unsafe retries after "unknown outcome" errors.
  - Explicit Timeout Definition**: Synchronous broker calls must enforce explicit timeout thresholds (e.g., 5 seconds). Any request exceeding this threshold must be classified as an Unknown Outcome, disable automatic retries, and trigger forced reconciliation.
- [ ] Trigger a P1 critical alert when reconciliation drift exceeds configured monetary or percentage-of-equity thresholds.
  - Trigger a P1 critical alert if reconciliation drift exceeds a configurable monetary amount or a percentage of account equity.
- [ ] Add chaos-engineering tests for broker disconnections and delayed adapter responses.
  - Chaos Engineering**: Inject random broker disconnections and delayed adapter responses during E2E testing to verify circuit breaker and reconciliation resilience. *Pending: no E2E chaos test suite exists for trader broker disconnections or delayed responses.*

#### Order Rate Throttling and Risk Pre-Check Gates

- [ ] Configure and enforce per-provider rate limiting on all outbound broker calls, with utilization warnings.
  - Verify that the provider rate-limiting threshold has not been exceeded.
  - Configure and enforce a per-provider rate limiter (token bucket algorithm) for each broker instance.
  - Apply rate limits to all outbound API calls to prevent bans or IP blocking.
  - Trigger warning logs and flags if rate limit capacity utilization exceeds 80% for more than 5 consecutive minutes.
- [ ] Implement a graceful shutdown sequence allowing in-flight requests to resolve within a configurable timeout window.
  - Shutdown Sequence**: When the service is shutting down or redeploying, it must:
  - Allow in-flight requests to resolve within a configurable timeout window.

#### Persistent Trade Journal and Order Store

- [ ] Implement idempotency key generation, duplicate detection/rejection, TTL/lifecycle enforcement, and collision protection.
  - Generate deterministic request identifiers.
  - Detect duplicate requests using idempotency records.
  - Reject conflicting duplicate requests. *Pending: duplicate keys are blocked/cached, but conflicting payload comparison for the same explicit request ID is not implemented.*
  - Enforce TTL (Time-To-Live) and lifecycle stages on idempotency keys.
  - Handle concurrency collisions with "already in progress" responses to avoid race conditions.
  - Collision Protection**: Attempts to submit duplicate request IDs before the original is finalized must be rejected immediately.
- [ ] Compare internal `TradeStore` state against broker state.
- [ ] Track trader metrics: latency, failure rates, reconciliation drift, rate-limit utilization, and idempotency hits.
  - Metrics**: Track latency, failure rates, reconciliation drift, rate limit utilization, and idempotency hits. *Pending: services expose some status fields/logs, but no unified trader metrics collector exists.*
- [ ] Flush final reconciliation state and idempotency logs to the `TradeStore` on shutdown.
- [ ] Add E2E reconciliation/idempotency recovery tests for network drops and unknown outcomes.
  - E2E Reconciliation & Idempotency Testing**: Implement specific test suites that inject network drops, simulate unknown outcomes, and verify correct recovery, deduplication, and reconciliation. *Pending: no E2E network-drop/unknown-outcome recovery suite exists.*

#### Domain Exception Handling and Error Routing

- [ ] Classify and map broker errors to standard internal/MQL5-retcode-compatible codes, with retry-with-backoff for idempotent operations and circuit breakers around broker adapters.
  - Map error codes to standard codes that match MQL5 retcode behaviors (e.g., `TRADE_RETCODE_REQUOTE`, `TRADE_RETCODE_PRICE_OFF`).
  - Error Classification**: Errors must be classified into transient vs. permanent types, mapped from broker-specific codes to a common internal set.
  - Retry Policy**: Idempotent operations shall use a retry policy with exponential backoff and randomized jitter.
  - Circuit Breaker**: Connections to broker adapters must be protected by circuit breakers to prevent cascading failures. *Pending: data service has circuit-breaker utilities, but trader broker execution is not protected by a broker circuit breaker.*

#### Trading Service Operations and Compliance Manual

- [ ] Simulator Integration**: Maintain high-fidelity integration tests using the local simulator adapter for deterministic regression validation. *Pending: simulator routing has unit coverage, but no high-fidelity trader simulator integration test is present.*


### Hardening Amendments

#### Broker routing and execution provider boundary

Requirements:

- [ ] Move broker routing ownership out of `app/routes/` and into a service or integration boundary such as `app/services/brokers/router.py` or `app/integrations/brokers/`.
- [ ] Ensure API routes call governed services and never own broker resolution, execution decisions, risk decisions, or adapter selection policy.
- [ ] Adopt Phase 1.5 contracts for `BrokerCapabilities`, `ExecutionProvider`, `AccountProvider`, `PositionProvider`, `OrderProvider`, `SymbolInfoProvider`, `BrokerErrorMapper`, `TradeStore`, and `ExecutionJournal`.
- [ ] Ensure MT5, cTrader, Binance, simulator, paper, and shadow providers implement the same execution provider boundary where applicable. *Pending: Phase 1.5 protocols exist, but these adapters are not all conformed to a shared execution provider boundary.*
- [ ] Ensure broker-specific errors map to deterministic internal execution error codes before leaving the integration boundary.
- [ ] Ensure raw broker order IDs are stored as provider metadata and never replace canonical trade, order, execution, fill, or idempotency IDs. *Pending: `TradeStore` currently keys orders/executions by raw broker tickets.*
- [ ] Add tests proving the same service-layer caller can place a simulated, paper, or live-routed request by changing provider configuration only. *Pending: tests cover mt5/simulator resolver behavior, but not paper/live-routed execution parity by configuration only.*

### Unit Tests Required

```text

tests/unit/app/services/trader/

```

Test coverage:

- Cover every requirement in this phase with normal, edge, invalid-input, fail-closed, logging, schema, and regression tests as applicable.
- Preserve the project gate of at least 80% coverage for each affected file and package.
- Verify standard envelopes, deterministic error codes, import behavior, and ownership boundaries.

### Usage Examples Required

```text

tests/usage/app/services/07_trading.py

```

Usage examples must show:

- `example_01_order_intent_creation`: Demonstrate deterministic order-intent creation from approved risk decisions.
- `example_02_order_validation`: Demonstrate symbol, price, volume, stop, freeze-level, and MQL5 compatibility validation.
- `example_03_idempotency_and_store`: Demonstrate idempotency keys, request packaging, duplicate handling, and store persistence.
- `example_04_simulator_route`: Demonstrate paper/simulation route behavior without live broker mutation.
- `example_05_reconciliation`: Demonstrate order, position, and receipt reconciliation plus mismatch reporting.
- `example_06_rate_limits_and_shutdown`: Demonstrate throttling, ordered queues, graceful shutdown, and recoverable errors.
- `example_07_execution_quality_reporting`: Demonstrate fill quality, slippage, partial-fill metadata, and structured receipts.
- `example_08_live_boundary`: Demonstrate that live mutation is blocked unless Live phase gates approve it.
- The single usage file must be runnable as a script and organize separate examples as focused functions.
- Examples must extensively cover the phase's official public capabilities, important edge cases, fail-closed paths, and standard envelope fields where applicable.

### Documentation and Logging Requirements

- Every created or changed Python module must have a file-level docstring describing purpose, exports, and side effects.
- Every public function/class must have a Google-style docstring with args, returns, and raised or structured errors.
- Log calls, validation failures, success, exception paths, and governed/fail-closed decisions with redacted metadata only.
- Update module README or active docs when architecture, API, data models, security, testing, or observability meaning changes.

### Acceptance Checklist

- Done criterion: All 84 checkbox tasks are implemented or explicitly deferred with a documented reason.
- Done criterion: Scope stayed within this phase and approved dependency surfaces.
- Done criterion: Public exports match the phase registry rules and do not expose unapproved helpers.
- Done criterion: Standard envelopes, metadata, request IDs, error codes, logging, and redaction rules are satisfied where applicable.
- Done criterion: Unit tests, usage examples, static typing, linting, formatting, and coverage gates pass.
- Done criterion: Active docs and changelog are updated for any implemented project meaning changes.
- Done criterion: Rollback path and implementation report are recorded before handoff.

### Commit Message

```text

feat(trading-service): implement trader service layer and order validation



- Integrate TradeStore for order, deal, and position persistence

- Build stop, freeze, pegged, stop-limit, and trailing stop order validators

- Setup Startup Reconciliation Gate and position state synchronizer

- Support netting/hedging compatibility and MQL5 execution model mapping

```
