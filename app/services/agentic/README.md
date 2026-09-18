# Agentic

> **Package:** `app/services/agentic/`
> **Status:** `Missing`
> **Last updated:** `2026-09-18`
> **Domain ID:** `D-AGENTIC`

This README is the domain's single source of truth for its boundary, feature and FR registry,
domain-local workflows, semantic contract ownership, persisted-state model, acceptance evidence,
and deletion behavior. Reference-product evidence is a requirement source, never implementation
evidence.

`PROJECT.md` owns system scope and cross-domain behavior. `ARCHITECTURE.md` owns universal
structure and runtime constraints. `AGENTS.md` owns contributor workflow. The
[Feature Implementation Pipeline](../../../docs/dev/feature_implementation_pipeline.md) owns the
complete single-file feature delivery checklist.

## Code-aligned implementation convention

Backend features use the simplified modular-monolith layout:

```text
app/services/agentic/
|-- README.md
|-- __init__.py
|-- providers.py
|-- context.py
|-- tools.py
|-- approvals.py
`-- audit.py

app/contracts/agentic.py
app/services/persistence/agentic.py
tests/services/agentic/<feature>/
tests/examples/17_agentic.py
```

Each feature module is one cohesive physical removal unit. It contains typed configuration,
service behavior, lifecycle wiring, immutable `SPEC`, and a zero-argument factory. Registration
is explicit in `app/registry.py`; import-time discovery and ambient singletons are forbidden.
Cross-boundary DTOs, protocols, events, errors, and capability keys live in
`app/contracts/agentic.py`. Features resolve dependencies through `FeatureContext` and
never import sibling implementations.

All schema, parameterized SQL, and transactions for this domain live in
`app/services/persistence/agentic.py`. A feature may be stateless, but it never accepts an
unrestricted database connection. Every completed feature contributes a deterministic, offline,
secret-safe example to `tests/examples/17_agentic.py`.

---

## 1. Purpose and boundary

### Purpose

Own optional model-provider adapters, bounded tools, context/evidence assembly, structured outputs, budgets, approvals, and auditability while remaining non-authoritative for quantitative and live decisions.

### Owns

- Model profiles, provider-neutral requests/responses, token/cost budgets, cancellation, and redaction.
- Allowlisted typed tools, evidence/context manifests, structured-output validation, approvals, and audit records.
- Advisory explanations and proposals that deterministic domains validate.

### Does not own

- Metric, strategy, simulation, risk, or trading authority.
- Credential exposure, arbitrary code/shell/database access, or self-granted permissions.

### Shared contracts


The public boundary is `app/contracts/agentic.py`; private implementation imports are forbidden.

| Status | Capability or event | Protocol / DTO symbol | Version | Purpose |
| --- | --- | --- | --- | --- |
| Missing | `agentic.providers@1` | `ModelProviderRegistry` | `1` | Model profiles, requests, budgets, and health |
| Missing | `agentic.context@1` | `ContextAssembler` | `1` | Evidence-bounded context manifests |
| Missing | `agentic.tools@1` | `AgentToolRegistry` | `1` | Allowlisted typed read/mutation tools |
| Missing | `agentic.approvals@1` | `ApprovalService` | `1` | Explicit scoped mutation approvals |
| Missing | `agentic.audit@1` | `AgentAuditService` | `1` | Prompts/evidence/tool/outcome provenance |

### Persisted-state ownership


Semantic state remains feature-owned although storage mechanics are centralized.

| Status | Namespace | Owning feature | Driver | Retention | Public read boundary |
| --- | --- | --- | --- | --- | --- |
| Missing | `agentic.v1` | `FEAT-AGENTIC-PROVIDERS` and registry peers | `sqlite` | Explicit reference-safe policy | `agentic.providers@1` |

---

## 2. Feature registry and dependency direction


| Feature | Delivered value | Owner module | Provides | Required capabilities | Status |
| --- | --- | --- | --- | --- | --- |
| `FEAT-AGENTIC-PROVIDERS` | Model profiles, requests, budgets, and health | `app/services/agentic/providers.py` | `agentic.providers@1` | None | Missing |
| `FEAT-AGENTIC-CONTEXT` | Evidence-bounded context manifests | `app/services/agentic/context.py` | `agentic.context@1` | `persistence.artifacts@1` | Missing |
| `FEAT-AGENTIC-TOOLS` | Allowlisted typed read/mutation tools | `app/services/agentic/tools.py` | `agentic.tools@1` | `gateway.authorization@1` | Missing |
| `FEAT-AGENTIC-APPROVALS` | Explicit scoped mutation approvals | `app/services/agentic/approvals.py` | `agentic.approvals@1` | `workspace.jobs@1` | Missing |
| `FEAT-AGENTIC-AUDIT` | Prompts/evidence/tool/outcome provenance | `app/services/agentic/audit.py` | `agentic.audit@1` | `persistence.artifacts@1` | Missing |

Dependencies use versioned public contracts. Removing a contribution withdraws only its capability;
required consumers become attributed `BLOCKED`, optional operations return unavailable, and
retained state is not purged.

---

## 3. Domain workflows


### `WF-AGENTIC-PROPOSE` — Produce and optionally apply a validated proposal

- **Lead owner:** `FEAT-AGENTIC-CONTEXT`
- **Participants:** Context/evidence, provider, schema validator, tool registry, approval, target capability, audit.
- **Input boundary:** User goal, allowed sources/tools, privacy class, output schema, token/cost/time budget.
- **Output boundary:** Cited structured proposal; optional approved tool receipt; complete audit manifest.
- **Failure boundary:** Missing evidence/schema/budget/approval fails closed; provider text is never directly executed.
- **Acceptance:** `ATW-AGENTIC-PROPOSE-001`

---

## 4. Feature specifications


This representative card applies to every registry entry; exact algorithms and states are in Section 9.

### `providers.py` — `FEAT-AGENTIC-PROVIDERS`

> **Feature ID:** `FEAT-AGENTIC-PROVIDERS`
> **Status:** `Missing`
> **Owner module:** `app/services/agentic/providers.py`

#### Purpose

Provide model profiles, requests, budgets, and health without absorbing another feature's responsibility.

#### Capability declarations

- **Provides:** `agentic.providers@1`
- **Requires:** None
- **Optional / operation-gated:** absence is explicit; no silent substitution.

#### Configuration and limits

Configuration is immutable, typed, versioned, and bounded. Reference sample values are not defaults.

| Status | Setting | Type / unit | Default | Validation and failure |
| --- | --- | --- | --- | --- |
| Missing | `schema_version` | positive integer | `1` | Reject incompatible versions |
| Missing | `operation_timeout_s` | finite seconds | operation-specific | Positive and bounded |
| Missing | `resource_limit` | positive integer | deployment-specific | Reject unbounded/nonpositive |

#### Runtime effects and cleanup

| Effect | Acquisition | Cleanup / failure behavior |
| --- | --- | --- |
| Capability/contribution | Managed feature scope | Withdraw with scope |
| Task/subscription/resource | Managed lifecycle API | Reverse-order close; failed start unwinds |
| Durable mutation | Focused persistence/API protocol | Roll back; partial output remains unpublished |

#### Persistent state

- **Domain persistence module:** `app/services/persistence/agentic.py`
- **Namespace:** `agentic.v1`
- **Schema version:** `1` initially; forward migration only
- **Retention and purge:** explicit and reference-safe; removal never implicitly purges.

#### Single-file structure and symbols

| Status | Owner | Responsibility | Symbols |
| --- | --- | --- | --- |
| Missing | `providers.py` | Model profiles, requests, budgets, and health; configuration, service, lifecycle, immutable specification, factory/contribution | `ModelProviderRegistry` |
| Missing | `context.py` | Evidence-bounded context manifests; configuration, service, lifecycle, immutable specification, factory/contribution | `ContextAssembler` |
| Missing | `tools.py` | Allowlisted typed read/mutation tools; configuration, service, lifecycle, immutable specification, factory/contribution | `AgentToolRegistry` |
| Missing | `approvals.py` | Explicit scoped mutation approvals; configuration, service, lifecycle, immutable specification, factory/contribution | `ApprovalService` |
| Missing | `audit.py` | Prompts/evidence/tool/outcome provenance; configuration, service, lifecycle, immutable specification, factory/contribution | `AgentAuditService` |
| Missing | `tests/examples/17_agentic.py` | Offline primary-purpose evidence | one named scenario per completed feature |

#### Functional requirements

| Status | Requirement ID | Observable behavior | Evidence |
| --- | --- | --- | --- |
| Missing | `FR-AGENTIC-001` | Outputs validate against a deterministic schema before use. | Malformed-output tests |
| Missing | `FR-AGENTIC-002` | Tool authority is allowlisted, scoped, expiring, and no broader than user approval. | Policy tests |
| Missing | `FR-AGENTIC-003` | Quantitative values link to deterministic artifacts/calculators, not model assertion. | Provenance tests |
| Missing | `FR-AGENTIC-004` | Secrets/private data are minimized and redacted across provider, logs, and audit. | Adversarial privacy tests |

#### Removal behavior

Withdraw the capability and managed effects while retaining schema-readable artifacts. Dependent
operations return attributed unavailable; reinstall requires schema/version compatibility.

---

## 5. Domain-wide requirements and invariants

| Status | Requirement ID | Rule | Verification |
| --- | --- | --- | --- |
| Missing | `ARCH-001` | `__init__.py` is docstring-only. | `scripts/architecture_check.py` |
| Missing | `ARCH-002` | Tasks and resources are managed through `FeatureContext`. | Lifecycle tests |
| Missing | `ARCH-003` | Logging uses `app.kernel.logging`; no service configures handlers. | Architecture/logging tests |
| Missing | `ARCH-004` | Public contracts live in `app/contracts/agentic.py`. | Import/contract checks |
| Missing | `ARCH-005` | Feature modules never import sibling implementations. | Import checks |
| Missing | `ARCH-006` | SQL/schema operations live in `app/services/persistence/agentic.py`. | Architecture/schema checks |

---

## 6. Decisions and open evidence


| Status | Decision ID | Decision or missing evidence | Scope | Required closure |
| --- | --- | --- | --- | --- |
| Accepted | `DEC-AGENTIC-001` | Agentic output is advisory; deterministic domains and approvals remain authoritative. | Safety | SYS-014 |
| Open | `DEC-AGENTIC-002` | Providers, models, retention, residency, and budget defaults are unselected. | Integration | Owner decision and provider review |

Evidence IDs resolve through `docs/PROJECT.md`. Unknowns remain explicit; installed names and
sample values are not runtime proof.

---

## 7. Tests and definition of done

```text
tests/services/agentic/<feature>/
|-- test_config.py
|-- test_<feature>.py
|-- test_lifecycle.py
|-- test_removal.py
`-- test_persistence.py       # when applicable

tests/examples/17_agentic.py
```

Editing uses explicit affected paths with `--no-cov`; the full candidate gate remains
`uv run python scripts/ci_check.py`.

- [ ] Stable feature and requirement IDs have one owner.
- [ ] Public contracts and exact `FeatureSpec` dependencies exist.
- [ ] Registration is explicit; imports have no runtime effects.
- [ ] Happy, invalid, boundary, unavailable, lifecycle, persistence, and removal tests pass.
- [ ] Numerical or stateful behavior has deterministic golden/fault fixtures.
- [ ] One offline usage example exists per completed feature.
- [ ] Domain status reflects repository evidence, not reference-product evidence.
- [ ] Architecture and full qualification gates pass.

---

## 8. Change process

1. Update this README and identify the exact feature/requirement scope.
2. Update `app/contracts/agentic.py` first when the public boundary changes.
3. Implement one cohesive owner module and immutable `SPEC`.
4. Change `app/services/persistence/agentic.py` only for database mechanics.
5. Update explicit registry, consolidated examples, and focused tests.
6. Verify feature removal and affected consumers.
7. Run the repository-prescribed candidate gate and record actual results.

---

## 9. Normative domain specification

A model profile declares provider/model/version, endpoint class, data-retention/residency policy, timeouts, retries, context/output limits, cost metadata, and supported structured/tool modes. Context manifests list exact artifact IDs, excerpts/hashes, truncation and retrieval policy. Tools expose typed inputs/outputs, side-effect class, required capability and approval. Read-only is default. Mutations require a displayed diff/summary, target, scope, expiry and idempotency key; live trading is outside agentic authority. Treat model/provider text as untrusted data. No shell, arbitrary SQL, raw filesystem, credential, or dynamic-code tool. Record prompt/template version, evidence IDs, model profile, validated output hash, tool calls, approvals, and outcomes subject to privacy policy.
