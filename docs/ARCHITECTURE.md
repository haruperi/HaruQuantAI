# HaruQuantAI Architecture Specification (Compressed)

## 1. Vision & Architecture
**Purpose:** A modular, AI-assisted quantitative trading platform prioritizing safe service boundaries, governed execution, reproducible research, and strict kill-switches. 
**Architecture:** Modular monolith with strict service-oriented boundaries.
*   **Layer 1:** UI / Conversation / Research
*   **Layer 2:** API Gateway / Auth / Tool Access Control
*   **Layer 3:** Optimization / Simulation / Analytics
*   **Layer 4:** Trading / Risk / Strategy / Indicator
*   **Layer 5:** Data / Broker Adapters / State Persistence
*   **Layer 6:** Utils (Settings, logging, event bus, security)

## 2. Actors & Core Workflows
**Actors:** 
*   *Human:* Owner, Operator, Researcher, Strategy Dev, Risk Manager, Compliance, Viewer.
*   *System:* AI Agent (bounded by policy), Service Account, Broker Adapter (external boundary).

**Core Trading Pipeline:** `Strategy (Signal)` → `Risk (Decision)` → `Trading (Order Intent)` → `Broker (Receipt)`

**Workflows:**
1.  **Research:** Load data → Explore → Versioned spec → Simulate → Governed promotion.
2.  **Paper Trade:** Signal → Risk eval → Order intent → Paper execution → Audit.
3.  **Live Trade:** Auth → Signal → Risk/Gates → Order intent → **Broker execution (only if explicitly enabled)** → Reconciliation.
4.  **AI Conversation:** Prompt → Redacted action draft → Governance approval → Backend execution.

## 3. Runtime & Environments
*   **Stack:** FastAPI/Pydantic (BE), Next.js/TS (FE), SQLite (State), MetaTrader5 (Baseline Broker).
*   **Execution Modes:** 
    *   `Research`: No broker mutation. 
    *   `Simulation`: Simulated side-effects only. 
    *   `Paper`: Demo side-effects only. 
    *   `Live`: **Disabled by default.** Requires full safety gates and explicit approval.
*   **Key Config:** `ALLOW_LIVE_MUTATIONS=false` (default), `ENVIRONMENT`, `DATABASE_URL`, `LOG_LEVEL`.
*   **Folder Structure:** `app/` (core), `agentic/` (AI runtime/policy), `data/` (SQLite/migrations), `ui/` (Next.js), `tests/`, `scripts/`, `docs/`.

## 4. Global Invariants & Non-Negotiables
*   **Strict Boundaries:** Strategies emit *Signals* (never orders). Risk intercepts *all* signals. Trading creates deterministic *Order Intents*. AI drafts *Actions* (never executes directly). Utils are shared foundation only.
*   **Fail-Closed:** Live trading fails closed by default. Missing context, stale data, or active kill-switches block execution.
*   **Traceability & Idempotency:** All cross-module/financial actions require `request_id`, `correlation_id`, and `workflow_id`. Financial paths require idempotency keys.
*   **Data Rules:** UUID4/ULID IDs, UTC timestamps, `*_json` suffixes, strict table namespaces (`core_`, `risk_`, `gov_`, `audit_`, etc.), no casual floats for prices.
*   **Security & Safety:** Validate *before* side-effects. Redact secrets in logs/errors. Retry *only* known safe transients. 

## 5. Module Contracts & I/O

| Module | Inputs | Outputs | Key Constraints & Contracts |
| :--- | :--- | :--- | :--- |
| **Data** | Feeds, broker reads, files | Normalized bars/ticks, state | Foundation layer. No business logic. |
| **Indicator** | Data, params | Indicator values | Pure functions. |
| **Strategy** | Data, indicators, lifecycle | **Signals**, metadata | Emits intent, never broker orders. |
| **Risk** | Proposals, state, policies | **Decisions**, kill-switch state | Modular engines (VaR, Margin, Drawdown). Cryptographic audit chaining. Enforces lifecycle gates (research → full-live). |
| **Trading** | Risk decisions | **Order Intents** | Owns broker routing. Enforces rate limits. Carries trace IDs. |
| **Analytics** | Logs, returns, benchmarks | Reports, scorecards | **Strictly read-only.** No side-effects. Governed by metric/schema catalogs. |
| **Simulator** | History, intents | Sim trades, metrics | **No live side-effects.** In-memory. Deterministic replay. Supports advanced orders/sizing gates. |
| **Optimization**| Data, strategy | Optimized params | Grid/Random/GA/Bayesian. Strict time-series splitting (no leakage). Atomic checkpointing. |
| **Live** | Intents, state | Executions, receipts | **11 deterministic gates.** Single-session guard. Strict reconciliation authority. |
| **Research** | Data | Insights, reports | Read-only/live. Strict leakage/bias gating. Statistical sign-off (bootstrapping/FDR). |

## 6. Interface Envelopes
**API Response (Mandatory):**
```json
{
  "status": "success|error", "message": "...", "data": {}, 
  "error": null | {"code": "...", "details": "..."},
  "metadata": {
    "request_id": "...", "correlation_id": "...", "api_version": "...", 
    "module": "...", "risk_level": "governed", "side_effects": "none",
    "execution_time_ms": 42, "created_at": "ISO-8601"
  }
}
```
**Event Bus:** `event_id`, `event_type`, `schema_version`, `source_module`, `timestamp`, `request_id`, `correlation_id`, `causation_id`, `payload_json` (redacted), `audit_level`.

## 7. Implementation Standards
*   **Validation:** Reject unknown fields for sensitive mutations. Fail-closed on missing auth, stale prices, or reconciliation mismatches.
*   **Testing:** Coverage scales with risk. Utils/Data (deterministic) → Strategy/Risk (contracts) → Sim/Live (safety-gated) → UI/Conv (redaction/drafts).
*   **Observability:** Structured JSON logs. Health monitoring (readiness, DB, clock drift). Audit trails for token logs and approvals.
*   **Utility Layer:** Standard helpers (envelopes, validators, redaction) are support infrastructure. They do not own strategy, portfolio, or trading decisions. Lazy-load optional adapters.

## 8. Pending Architecture Decisions
1. Event bus durability phases.
2. Exact API schema/versioning format.
3. Deployment topology & Worker/job model for heavy compute.
4. SQLite migration path & Retention windows for regulated artifacts.
5. AI provider interface details & Final identity provider.
6. Risk threshold signing and approval process.