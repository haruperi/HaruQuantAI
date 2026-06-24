## Phase 1.5 Core Domain Contracts

### Goal

Define canonical cross-domain models and protocol contracts before Data, Indicators, Strategies, Risk, Trading, Simulation, Analytics, Optimization, Live, UI/API, Research, and Conversation implement incompatible duplicates.

Task inventory: 73 checkbox tasks (73 checked, 0 unchecked).

### Dependency Files and Functionality


Required functionality:

- Canonical data, signal, risk, execution, portfolio, analytics, optimization, live, and audit contracts.
- Protocol interfaces for providers and governed service boundaries.
- Serialization, versioning, hashing, and compatibility rules.
- Contract tests shared by every later phase.


### Functionality to Implement

Tasks are grouped by domain functionality. Each requirement is now part of its corresponding functional contract.

#### Canonical base contracts

- [x] Create `app/contracts/` as the canonical model boundary shared by all domain phases, with a side-effect-free public registry in `app/contracts/__init__.py` that never imports broker SDKs, database clients, UI frameworks, LLM clients, or optional provider packages.
  - `app/contracts/` created as the canonical model boundary
  - Side-effect-free public registry in `app/contracts/__init__.py`
  - Contract modules do not import broker SDKs, database clients, UI frameworks, LLM clients, or optional provider packages
- [x] Define a common contract base carrying `schema_version`, `created_at`, optional `request_id`, optional `workflow_id`, and optional `correlation_id` where applicable, with deterministic serialization helpers, deterministic contract hashing (for reproducibility, caching, audit records, and evidence packs), compatibility rules based on major/minor schema versions, and validation helpers that return deterministic errors through the Utils error model.
  - Common contract base with the listed identity/versioning fields
  - Deterministic serialization helpers using JSON-safe values
  - Deterministic contract hashing
  - Compatibility rules based on major/minor schema versions
  - Validation helpers returning deterministic errors through the Utils error model
- [x] Ensure all canonical contracts are typed, documented, and safe to import in test, CLI, API, and agent runtimes.
- [x] Treat canonical contracts as stabilization-stage during the first three approved sprint packs after Phase 1.5, accepting owner-approved additive changes without forcing broad downstream rewrites. (Links to the stabilization review rule under Contract Governance below.)
- [x] Give every canonical contract that crosses service or provider boundaries a JSON-safe `metadata: dict[str, Any]` escape hatch for broker-specific, provider-specific, phase-specific, or experimental fields not yet stable enough to become first-class contract fields, namespaced by owning adapter/provider/phase/feature area to prevent collisions and accidental promotion of ambiguous keys, while preserving deterministic serialization, hashing policy, redaction policy, and schema-version compatibility behavior.
  - Metadata escape hatch on boundary-crossing contracts
  - Metadata namespaced by owning adapter/provider/phase/feature area
  - Metadata preserves serialization, hashing, redaction, and compatibility behavior

#### Market data contracts

- [x] Define `Symbol` with canonical symbol, broker symbol, asset class, quote currency, base currency, precision, lot/tick metadata, and provider metadata where applicable.
- [x] Define `Timeframe` with deterministic parsing, canonical names, duration metadata, and unsupported-timeframe validation.
- [x] Define `Bar` with timestamp, open, high, low, close, optional volume, optional spread, symbol, timeframe, and source metadata.
- [x] Define `Tick` with timestamp, bid, ask, last, volume, symbol, and source metadata.
- [x] Define `Spread` with bid, ask, spread points, spread price, timestamp, symbol, and source metadata.
- [x] Define `DataSlice` for bounded batches of bars, ticks, or records with source, retrieval, transformation, and quality metadata.
- [x] Define canonical market-data error codes for unavailable symbols, unsupported timeframes, stale data, provider errors, and malformed payloads.
- [x] Define raw-provider-data lineage fields: provider, provider_request_id, retrieved_at, normalized_at, transformation_hash, and source_hash.

#### Indicator and strategy contracts

- [x] Define `IndicatorResult` with name, version, parameters, warmup period, input hash, output metadata, and deterministic result serialization.
- [x] Define `StrategyInput` with market data references, indicator references, portfolio context, configuration, and timestamp boundaries.
- [x] Define `StrategySignal` as the only allowed strategy-to-risk output contract, including strategy ID, strategy version, parameter hash, symbol, side, confidence, validity window, reason, evidence references, and source data hash, and ensure strategy contracts cannot represent broker-specific order placement directly.
  - `StrategySignal` is the only allowed strategy-to-risk output contract
  - Includes strategy ID, strategy version, parameter hash, symbol, side, confidence, validity window, reason, evidence references, source data hash
  - Strategy contracts cannot represent broker-specific order placement directly
- [x] Define strategy contract validation that rejects signals with missing symbol, invalid side, expired validity window, missing evidence where required, or broker-specific mutation fields.

#### Risk and execution contracts

- [x] Define `RiskDecision` as the only allowed risk-to-execution approval or rejection contract.
- [x] Define `RiskRejection` with deterministic code, severity, reason, violated limit, evidence, and remediation metadata.
- [x] Define `PositionSizingResult` with requested size, approved size, sizing method, constraints applied, and risk contribution.
- [x] Define `OrderIntent` as the canonical post-risk pre-execution request.
- [x] Define `TradeRequest` as the canonical execution-layer request after all required risk and approval gates pass.
- [x] Define `TradeResult` with accepted, rejected, pending, partially filled, filled, cancelled, expired, failed, and reconciled states.
- [x] Define `ExecutionReport` and `Fill` contracts with broker-neutral execution status, fill price, quantity, commission, slippage, latency, provider IDs, and timestamps.
- [x] Define `BrokerCapabilities` for supported order types, fill policies, asset classes, time-in-force options, margin mode, hedging/netting mode, and provider limits.
- [x] Define provider protocols `MarketDataProvider`, `ExecutionProvider`, `AccountProvider`, `PositionProvider`, `OrderProvider`, `SymbolInfoProvider`, and `BrokerErrorMapper`, ensuring they return canonical contracts and never expose raw broker SDK objects outside integration boundaries.
- [x] Route broker-specific reconciliation data through canonical contract `metadata` rather than first-class fields until repeated cross-provider use justifies promotion: `TradeResult`, `ExecutionReport`, and `Fill` metadata support provider reconciliation references, broker ticket aliases, venue execution hints, and diagnostic adapter fields without changing service-layer callers.
  - Broker-specific reconciliation fields use canonical contract `metadata` until promotion is justified
  - `TradeResult`/`ExecutionReport`/`Fill` metadata supports reconciliation references, ticket aliases, venue hints, and diagnostic adapter fields

#### Portfolio, simulation, analytics, optimization, live, and audit contracts

- [x] Define `AccountSnapshot` with equity, balance, margin, free margin, currency, leverage, timestamp, and provider metadata.
- [x] Define `Position` with symbol, side, quantity, average price, unrealized PnL, realized PnL, margin, provider IDs, and timestamps.
- [x] Define `PortfolioSnapshot` with account, positions, pending exposure, risk budget, correlation metadata, and freshness metadata.
- [x] Define `BacktestConfig` with dataset references, strategy references, cost model, fill model, calendar, split policy, and reproducibility seed.
- [x] Define `BacktestResult` with run ID, config hash, journal reference, equity curve reference, metrics reference, and evidence metadata.
- [x] Define `OptimizationCandidate` with strategy, parameters, score, robustness metrics, validation splits, overfitting checks, and evidence references.
- [x] Define `LiveSessionState` with environment mode, provider status, risk status, kill-switch state, reconciliation status, and operator approval status.
- [x] Define `AuditEvent` with event ID, event type, severity, actor, subject, action, evidence, redacted payload hash, and timestamp metadata.
- [x] Define `KillSwitchState` and `RiskAuditEvent` contracts shared by Risk, Trading, Live, UI/API, and Conversation.
- [x] Define `ExecutionJournal` and `TradeStore` protocol contracts for persisted orders, positions, executions, fills, idempotency keys, and reconciliation records.

#### Contract governance

- [x] Require domain modules to import canonical contracts rather than redefining cross-domain models.
- [x] Require raw broker SDK objects, raw exchange payloads, and UI DTOs to be adapted into canonical contracts before crossing service boundaries, with API DTOs allowed to wrap canonical contracts but never replace domain contracts.
- [x] Require conversation memory to store summaries and references, not raw sensitive canonical payloads.
- [x] Require a compatibility review before changing public contract names, fields, schema versions, or serialization behavior.
- [x] Define a stabilization review rule for the first three sprint packs: metadata fields that become repeated, required, or cross-domain are reviewed for promotion into first-class contract fields with migration notes. (Links to the stabilization-stage rule under Canonical Base Contracts above.)
- [x] Prohibit metadata from containing raw broker SDK objects, raw exchange payloads, credentials, unredacted account identifiers, or opaque objects that cannot serialize deterministically.
- [x] Require downstream phases to tolerate unknown metadata keys by preserving or safely ignoring them unless a documented validation policy rejects the namespace.
- [x] Add usage examples showing the Data -> Indicator -> StrategySignal -> RiskDecision -> OrderIntent -> ExecutionProvider -> TradeResult -> Analytics flow.
- [x] Add contract tests proving canonical contracts serialize deterministically and validate malformed inputs consistently.
- [x] Add tests proving provider protocols can be implemented by simulator, MT5, cTrader, Binance, and paper/shadow adapters without changing service-layer callers.


### Unit Tests Required

```text
tests/unit/app/contracts/
```

Test coverage:

- [x] Write tests verifying every contract imports without optional provider dependencies installed.
- [x] Write tests verifying deterministic serialization, hashing, equality where applicable, and schema-version compatibility.
- [x] Write tests verifying invalid required fields, unsupported states, invalid timestamps, invalid symbols, invalid sides, and malformed provider metadata fail deterministically.
- [x] Write tests verifying provider protocols can be satisfied by fake adapters for market data, execution, account, position, order, and symbol info.
- [x] Write tests verifying strategy contracts cannot encode direct broker mutation requests.
- [x] Write tests verifying risk and execution contracts preserve correlation, request, workflow, idempotency, and audit identifiers.
- [x] Write tests verifying namespaced metadata survives serialization, hashing, copying, and provider round-trips without exposing raw provider payloads.

### Usage Examples Required

```text
tests/usage/01_5_core_contracts.py
```

Usage examples must show:

- [x] Build an example demonstrating canonical Bar and DataSlice construction from provider-like data.
- [x] Build an example demonstrating IndicatorResult and StrategySignal creation with reproducibility metadata.
- [x] Build an example demonstrating RiskDecision approving or rejecting an OrderIntent.
- [x] Build an example demonstrating simulator and live providers sharing the same ExecutionProvider protocol.
- [x] Build an example demonstrating TradeResult, ExecutionReport, Fill, PortfolioSnapshot, and BacktestResult serialization.
- [x] Build an example demonstrating using metadata for a broker-specific reconciliation field and later reading it without changing the canonical service flow.

### Acceptance Checklist

- Done criterion: All Phase 1.5 checkbox tasks are implemented or explicitly deferred with a documented reason.
- Done criterion: Later phases must depend on these contracts instead of duplicating cross-domain models.
- Done criterion: Contract tests and usage examples pass before Phase 2 implementation begins.
