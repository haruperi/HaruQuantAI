# HaruQuantAI System Architecture (Dense Reference)

## System Overview & Tech Stack

* **Architectural Pattern**: Modular monolith with service-oriented module boundaries. Aligns research, simulation, paper, and live environments while preventing any bypass of system controllers.
* **Production Stack Baseline**:
  * *Backend*: Python 3.14, managed with `uv`. FastAPI, Pydantic, Uvicorn (introduced once the API Gateway module lands).
  * *Frontend*: Next.js, React, TypeScript, Tailwind CSS, Radix UI (introduced once the UI module lands).
  * *Persistence*: SQLite (launch baseline); SQL migrations tracked under `data/database/migrations/`.
  * *Data Science*: `pandas`, `numpy`, `scipy`, `scikit-learn`, `numba`, approved `pyarrow`/`fastparquet`.
  * *Broker Gate*: MetaTrader5 (MT5).
  * *Quality Gate*: `ruff` (lint + format), `mypy` (static types), `pytest` (tests/coverage), `pre-commit` (enforced hook chain).

* **Runtime Execution Modes**:
  * `Research`: Data and feature exploration. Zero live broker mutations.
  * `Simulation`: Historical backtests via the core trading path. Simulated side effects.
  * `Paper`: Live paths executed against demo infrastructure. Paper side effects.
  * `Live`: Real capital transaction. Disabled by default; mandates all functional safety gates. Explicit toggle: `ALLOW_LIVE_MUTATIONS=false`.

---

## Current Implementation State

> This section tracks reality; the rest of this document describes the target architecture. Update it as modules land — see [docs/CHANGELOG.md](CHANGELOG.md) for history.

* Project scaffolded with `uv` (Python 3.14, `pyproject.toml`, `uv.lock`).
* Tooling configured: `ruff` (full rule set), `mypy`, `pytest`, `pre-commit` (hygiene checks, ruff, ruff-format, detect-secrets, mypy).
* Code present: `app/` package with implemented service modules under `app/services/`, including Trading as the surviving live-route runtime and broker-dispatch owner.
* The retired Live service has been folded into `app/services/trading/`; live execution remains a runtime route/mode, not a standalone service package.
* No `api/` or `ui/` application packages yet.

---

## Folder Topology & Dependency Flow

### Workspace Directory Layout (Target)

* `api/`: FastAPI apps, routes, middleware, auth, WS/session layers, API composition.
* `app/`: Core domain modules (utils, data, indicator, strategy, risk, analytics, trading, simulation, optimization, research, conversation). Live-route execution is owned by Trading.
* `agentic/`: Agent runtimes, explicit tool permission states, workflow schemas, provider configs.
* `data/`: SQLite databases, migration tracking, cache/log dumps, market/research assets.
* `ui/`: Next.js frontend application environment.
* `tests/`: Unit, integration, usage, and system contract test suites.
* `scripts/`: DB initialization, migration runners, validation tools, operational utilities.
* `docs/`: Documented project truth.

### Module Boundary Pipeline

Dependencies flow strictly downward; reverse routing or bypass loops are prohibited:

```
Conversation / Research / UI
        |
        v
API Gateway / Auth / Access Control
        |
        v
Optimization / Simulation / Analytics
        |
        v
Trading / Risk / Strategy / Indicator
        |
        v
Data / Broker Adapters / State Repositories
        |
        v
Utils (Shared Infrastructure Foundations)
```

---

## Technical Contracts & Envelopes

### Public Registry & Module File Framework (`app/utils/`)

* **Public Registry Rule**: Handled strictly via `app/utils/__init__.py` using explicit public exposure lists (`__all__`). No fallback imports, shims, or duplicate modules are permitted.
* **Submodule Footprint**: `logger`, `standard`, `errors`, `identity`, `normalization`, `paths`, `dataframe_tools`, `data_quality`, `schema_validation`, `security`, `settings`, `auth`, `event_bus`, `error_routing`, `notifications`, `observability`.

### Standard AI Tool Response Contract

Every official utility or domain tool exposed to AI layers must return five root fields:

```json
{
  "status": "success | error",
  "message": "Human-readable execution outcome description.",
  "data": {},
  "error": null,
  "metadata": {
    "tool_name": "string",
    "tool_version": "string",
    "tool_category": "string",
    "tool_risk_level": "string",
    "request_id": "string",
    "execution_ms": "float (monotonic timer rounded to 3 decimals)",
    "read_only": "boolean",
    "writes_file": "boolean",
    "modifies_database": "boolean",
    "places_trade": "boolean",
    "requires_network": "boolean"
  }
}
```

### Core Event Bus Envelope

```json
{
  "event_id": "TEXT (Traceable string-safe UUID4/ULID)",
  "event_type": "TEXT",
  "schema_version": "TEXT",
  "source_module": "TEXT",
  "timestamp": "TEXT (UTC ISO string with 'Z')",
  "request_id": "TEXT",
  "correlation_id": "TEXT",
  "causation_id": "TEXT",
  "payload_json": "TEXT (Redacted payload mapping)",
  "audit_level": "TEXT"
}
```

### Shared Authentication Context

```json
{
  "principal_id": "TEXT",
  "principal_type": "USER | SERVICE_ACCOUNT | AGENT",
  "roles": "ARRAY[TEXT]",
  "permissions": "ARRAY[TEXT]",
  "scopes": "ARRAY[TEXT]",
  "tenant_or_environment": "TEXT",
  "request_id": "TEXT",
  "workflow_id": "TEXT",
  "correlation_id": "TEXT"
}
```

---

## Data Models & Schema Management

* **Data Layout Conventions**: Core cross-module database tracking identifiers must use `TEXT` format. SQLite boolean fields enforce strict `0` or `1` constraints. JSON text structures map to an explicit `*_json` suffix name.
* **Precision Standard**: Structural or broker-critical price, size, volume, and balance mathematics must bypass standard floating-point operations. Requires `decimal.Decimal` parsing to ensure transaction immutability.
* **Table Namespace Prefixes**: System storage isolates data types using specific table identifiers: `core_`, `risk_`, `gov_`, `audit_`, `research_`, `ref_`, `ai_chat_`, and `agent_`.
* **Migration Invariance**: Database tracking updates via additive structure migrations. Modifying applied structural migrations is prohibited without an explicit baseline reset approval.

---

## System Control Policies

### Validation Strategy

* Enforce absolute schema checking prior to triggering downstream system side effects.
* Fail closed immediately if tracking context data is missing or corrupted during risk checks, live trade execution, or security evaluation.
* Enforce exact field parsing for sensitive updates; reject unknown or unmapped properties.

### Error & Automatic Retry Paradigm

* Every error object crossing module borders must remain structured, fully trace-tagged, and redacted.
* **Blind Retry Ban**: Automated retries apply only to verified transient transport anomalies. Unknown broker state responses block automated processing; execution loops freeze until state validation completes.
* **Fail-Closed Baseline**: System stops operations instantly if it encounters active kill switches, validation failures, token expiration, or structural mismatch flags.

### Core Security Mandates

* Plaintext application passwords, live API keys, provider access configurations, and cryptographic seeds are classified as system secrets.
* Redact sensitive patterns from execution dumps, trace events, log lines, and metrics payloads case-insensitively before persistence.
* AI modules can evaluate patterns or generate action draft states; they are blocked from direct interaction execution.

---

## Deployment Configuration Reference

| Target Group | Explicit Key Identifiers |
| --- | --- |
| **Application Environment** | `APP_NAME`, `ENVIRONMENT`, `API_HOST`, `API_PORT`, `UI_ORIGIN` |
| **System Persistence** | `DATABASE_URL`, `DATA_DIR`, `ARTIFACT_DIR`, `DATA_CACHE_PATH` |
| **Operational Protection** | `ALLOW_LIVE_MUTATIONS` (Defaults to `false`), `PROFILE` |
| **System Observability** | `LOG_LEVEL`, `LOG_RENDER`, `EVENT_BUS_BACKEND`, `METRICS_ENABLED`, `METRICS_PORT` |
| **Broker Integration (MT5)** | `MT5_ENABLED`, `MT5_LOGIN`, `MT5_PASSWORD`, `MT5_SERVER`, `MT5_TERMINAL_PATH` |
| **Email Service Routes** | `NOTIFICATION_EMAIL_ENABLED`, SMTP host/port/user/password/from/to records |
| **Telegram Alert Gate** | `NOTIFICATION_TELEGRAM_ENABLED`, `NOTIFICATION_TELEGRAM_BOT_TOKEN`, `NOTIFICATION_TELEGRAM_CHAT_IDS` |
| **AI Layer Interfaces** | `HARUQUANTAI_CHAT_ENABLED`, provider type, model spec target, API key, base URL |

---

## Core System Quality Gates

CI runners validate module engineering standards via targeted verification commands:

```bash
# Linting & Formatting Check
uv run ruff check .
uv run ruff format --check .

# Static Type Verification
uv run mypy .

# Unit Testing & Coverage Gates
uv run pytest --cov=app --cov-fail-under=80
```
