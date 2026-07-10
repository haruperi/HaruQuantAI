# HaruQuantAI Architecture & Product Truth (Dense Reference)

## Core System Axioms & Rules

* **Architectural Philosophy**: Ambiguity = hard failure. System fails closed by default. If safety or context cannot be proven, block execution.
* **Sequence Controls**: Strategies emit **Signals/Proposals**, *never* direct broker orders. **Risk** intercepts all proposals *before* Trading execution. **Trading** converts approved proposals into deterministic **Order Intents** and owns live-route runtime gates, broker dispatch, reconciliation, monitoring, and emergency controls.
* **Data Integrity & Privacy**: Zero secret leakage permitted across logs, errors, events, notifications, metrics, or chat. Strict UTC-first time policy (`Z` suffix). Plaintext keys or payloads must be redacted case-insensitively using denylist-first matching.
* **Build & Dependency Order**: Utils → Data → Indicator → Strategy → Risk → Analytics → Trading → Simulation → Optimization → UI/API Gateway → Research → Conversation.
* **AI Agent Constraints**: AI Agents can only execute approved, read-only tool plans via explicit allowlists; they can *never* directly execute governed, broker-affecting, or live mutation actions. Conversation layer only generates un-executed **Action Drafts**.

---

## System Workflows & Actors

* **Actors**: Owner/Admin (Policy/Config), Operator (Run/Monitor), Researcher (Data/Hypothesis), Strategy Dev (Build/Test), Risk Manager (Thresholds/Kill Switch), Compliance Approver (Recovery/Governance), Read-only Viewer, Service Account (Internal), AI Agent (Scoped Tools), Broker Adapter (External Data/Boundary).
* **Workflow Paths**:
  * *Research → Strategy*: Raw Data → Hypothesis → Spec Versioning → Sim → Governance Path.
  * *Signal → Paper*: Market State → Indicators → Signal → Risk Evaluation → Order Intent → Paper Receipt → Audit.
  * *Signal → Live*: Auth Principal → Signal → Multi-Gate Risk Validation → Idempotent Order Intent → Broker Readiness → Real Submission (if enabled) → Reconciliation/Audit.
  * *Action Draft*: Chat Request → Redacted Draft → Governance Route → Separate Backend Execution.

---

## 12-Module Technical Registry

> **Status**: This registry describes the target module map for HaruQuantAI. As of this writing the repository is a fresh scaffold (`app/` package, tooling only) — modules below are being built out incrementally per [docs/CHANGELOG.md](CHANGELOG.md).

### 1. Utils

* **Inputs**: Raw logs, event payloads, alerts, metrics.
* **Outputs**: Formatted JSON/colorized logs, Prometheus metrics, routed notifications, standard envelopes.
* **Owns**: Structured logging (JSON for prod, colorized human-readable for dev), UTC time/timezone formatting, standard tool response envelopes, error mapping (`HaruQuantError`), prefixed IDs (UUID4/ULID), safe path normalization, canonical JSON serialization, in-process Event Bus (deterministic, ordered per event type), alert/notification routing (Email, Telegram, Desktop), Prometheus health metrics.
* **Boundaries**: Strictly stateless and business-decision free. *Does not own* strategy logic, broker operations, risk rules, or persistence.
* **Key Limits**: Idempotency keys use TTL/eviction tracking. Queue full returns immediate `BACKPRESSURE_EXCEEDED` or `QUEUE_FULL` (fail-fast for critical workflows).

### 2. Data

* **Inputs**: Feeds, broker reads, files.
* **Outputs**: Normalized bars/ticks, state.
* **Owns**: Historical data, real-time feeds, provider alias mappings, SQLite storage/migrations, read-only broker/account state adapters (MT5 isolated behind facade).
* **Boundaries**: Foundation layer. No business logic. *Does not own* strategy logic, backtesting engines, or allocation formulas. Never leaks raw DataFrames, sockets, or db sessions across tool boundaries.
* **Key Limits**: Backfills maxed at 10,000 records or 1 calendar day per chunk. Commits checkpoints per chunk ID. Exclusive path-scoped locks for storage writes; returns `CONCURRENT_WRITE_LOCKED` on conflict. Multi-timeframe alignment defaults to no-lookahead.

### 3. Indicator

* **Inputs**: Data, params.
* **Outputs**: Indicator values.
* **Owns**: Pure deterministic formula library (EMA, SMA, ADX, ATR, ADR, RSI, etc.), parameter validation, indicator registry/capability matrix.
* **Boundaries**: Pure functions. Free of calculation-path I/O. *Does not own* broker calls, order state, strategy lifecycle, or external caching.
* **Key Limits**: Inputs must be normalized and non-empty. No-lookahead execution enforced via explicit `available_at` metadata fields.

### 4. Strategy

* **Inputs**: Data, indicators, lifecycle.
* **Outputs**: Signals, metadata.
* **Owns**: Strategy registry/versions, parameter schemas, state checkpoints, generation of canonical signals and `TradeIntent` payloads.
* **Boundaries**: Emits intent, never broker orders. *Does not own* risk enforcement, order routing, official fills, account sizing, or data normalization.
* **Key Limits**: Neutral signals emit no action. Lookahead or clock-drift violations cause atomic batch execution failure. Uses read-only execution state snapshots.

### 5. Risk (The Master Gate)

* **Inputs**: Proposals, state, policies.
* **Outputs**: Decisions, kill-switch state.
* **Owns**: Proposals intercept, safety limits, portfolio exposure, drawdown tracking, risk kill-switch state, validation of approval tokens, scenario analysis.
* **Boundaries**: Modular engines (VaR, Margin, Drawdown). Cryptographic audit chaining. Enforces lifecycle gates (research → full-live). *Does not own* data ingestion, strategy code, broker submission, or broad account state truth.
* **Key Limits**: Live trading requires active broker state validation; missing thresholds fail closed. Payloads capped at 1 MiB, max nesting depth 10, max list length 10,000. Public Pydantic V2 models use strict `decimal.Decimal` handling, `allow_inf_nan=False`, and `ROUND_HALF_EVEN`.

### 6. Analytics

* **Inputs**: Trades results, Logs, returns, benchmarks.
* **Outputs**: Reports, scorecards.
* **Owns**: Performance schemas, metric kernels, report builders, dashboard payloads, caveat/warning metadata. Non-binding advisory evidence only.
* **Boundaries**: Strictly read-only. No side-effects. Governed by metric/schema catalogs. *Does not own* live state mutation, broker execution, strategy promotion, or arbitrary local file loading.
* **Key Limits**: Monetary math utilizes `Decimal`; ratios use `float64` with documented tolerance. `Infinity` fields trigger structured validation errors. Fails closed on missing FX conversions.

### 7. Trading

* **Inputs**: Risk decisions.
* **Outputs**: Order Intents.
* **Owns**: Order intent formulation, client order IDs, route-aware request packing (`sim` vs `live`), simulator state mutation (for `route="sim"` only), live-route runtime orchestration, gate decisions, broker dispatch post-clearance, incident logging, monitoring, and reconciliation authority.
* **Boundaries**: Owns broker routing and live-route runtime middleware. Enforces rate limits. Carries trace IDs. *Does not own* signal creation, risk policy drafting, or broker secret resolution.
* **Key Limits**: Live actions require approved risk tokens and volume constraints. Precise decimal usage (minimum 28 digits, 8-decimal quantization). Idempotency material uses UTF-8 canonical JSON hashed via SHA-256. Broker operation timeout = 10s; check timeout = 5s.

### 8. Simulation

* **Inputs**: History, intents.
* **Outputs**: Sim trades, metrics.
* **Owns**: Backtest runtime, tick-based execution replay, simulated fills/journals, artifact manifests, execution reports.
* **Boundaries**: No live side-effects. In-memory. Deterministic replay. Supports advanced orders/sizing gates. *Does not own* live broker channels, live adapter code, or arbitrary Python strategy string execution.
* **Key Limits**: Initial balance must be positive. Rejects raw arbitrary code inputs — requires vetted registry references. Controlled boundaries return `SIM_*` error structures.

### 9. Optimization

* **Inputs**: Data, strategy.
* **Outputs**: Optimized params.
* **Owns**: Parameter sweeps, walk-forward routines, overfit/robustness diagnostics, reproducibility hashes, search metadata (`places_trade=False`).
* **Boundaries**: Grid/Random/GA/Bayesian. Strict time-series splitting (no leakage). Atomic checkpointing. *Does not own* live execution, automatic promotion, or database migrations.
* **Key Limits**: Parameter ranges must be explicitly bounded. Omitted `dry_run` flags default to `True`. Optimization ties resolve deterministically via trade count and candidate hash. Oversized payloads rejected instantly via `OPT_PAYLOAD_TOO_LARGE`.

### 10. UI / API Gateway

* **Inputs**: HTTP requests, WebSocket connections, client payloads.
* **Outputs**: HTTP responses, WebSocket broadcasts, views/DTOs.
* **Owns**: FastAPI routes, HTTP/WebSocket wrappers, frontend views, client stores, preflight write safeguards, auth/authz enforcement, DTO translations.
* **Boundaries**: Pure presentation/delegation layer. Contains *zero* domain or calculation logic inline. Enforces auth/authz.
* **Key Limits**: List endpoints require pagination (cursor-based default 50, max 200). 30-second endpoint timeouts apply. Preflight warnings expire after 30 seconds.

### 11. Research

* **Inputs**: Data.
* **Outputs**: Insights, reports.
* **Owns**: Sandboxed analysis, feature engineering tools, leakage validation, null-model/edge discovery wrappers, advisory reports.
* **Boundaries**: Read-only/live. Strict leakage/bias gating. Statistical sign-off (bootstrapping/FDR). Advisory only. *Does not own* live mutations, risk decisions, or roadmap code selection.
* **Key Limits**: Re-exported analytics mirror upstream definitions. Non-deterministic routines require seed injection and output logs. Persistent files store SHA-256 configuration hashes. `CleaningConfig` explicitly forbids implicit or hidden data filling/dropping.

### 12. Conversation (The AI Interface)

* **Inputs**: User messages, tool execution responses, context parameters.
* **Outputs**: Redacted response streams, action drafts, summarized threads, prompt payloads.
* **Owns**: Chat threads, redacted interaction streams, memory summarization, pinned facts, prompt assembly, action draft templates.
* **Boundaries**: Read-only workspace. Pre-persistence redaction. Context isolation. *Does not own* trade execution, risk management, or identity creation.
* **Key Limits**: Safe context tracking requires matching `(user_id, thread_id, request_id)` parameters for idempotent turns. Action drafts require schema validation prior to database storage. Prompt inclusion of tool data requires explicit permission metadata. Redaction occurs *prior* to thread persistence. Component limits (retention policies, prompt budgets) are strictly configuration-injected.

---

## Technical Error & Rounding Matrices

### Approved Error-Code Registry Additions

* `INVALID_AUTH_CONTEXT`, `AUTHORIZATION_FAILED`
* `INVALID_EVENT`, `EVENT_PUBLISH_FAILED`, `EVENT_HANDLER_FAILED`, `EVENT_DEAD_LETTER_FAILED`
* `QUEUE_FULL`, `BACKPRESSURE_EXCEEDED`
* `NOTIFICATION_FAILED`, `NOTIFICATION_SUPPRESSED`, `NOTIFICATION_THROTTLED`
* `OBSERVABILITY_ERROR`, `METRICS_EXPORT_FAILED`, `CLOCK_DRIFT_DETECTED`
* `CIRCUIT_OPEN`, `SECRET_VERSION_CONFLICT`
