# HaruquantAI — Spatiotemporal Composability Refactor Plan

> **Version:** `v2` (merged)
> **Status:** `Proposed` — no code written
> **Audited question:** can a domain or feature be absent, disabled, fail activation, be replaced, or be removed at runtime such that the app *loses that capability* rather than *breaks*?

---

## 0. Definition of success

The refactor succeeds when a removable unit can disappear and:

- the kernel still starts;
- unaffected capabilities remain operational;
- direct **and transitive** consumers become explicitly inactive;
- affected runtime profiles become unready where necessary;
- unsafe operations fail closed, with **no silent fallback provider selected**;
- reversible effects are released completely;
- durable and irreversible effects are preserved and reconciled, never auto-compensated;
- reinstalling a compatible provider **reactivates** its consumers;
- the failure surfaces as a structured `CAPABILITY_UNAVAILABLE` carrying a precise reason and the dependency chain.

**The plan does not begin by rewriting imports.** Imports change only after contracts, resolver, lifecycle, and rules exist.

---

## 0.1 What changed in v2

| Area | v1 | v2 |
|---|---|---|
| Baseline | none | **Phase 0**: golden financial fixtures captured before any change |
| Removal unit | feature folder | **provider** (a feature may have several; bundles declared explicitly) |
| Contracts | Protocols inside the kernel | separate importable **`app/capabilities/`** spec tree |
| Effect classes | binary revertible/irreversible | **three-way**: reversible ephemeral / durable compensatable / irreversible external |
| Error model | 3 codes | 1 family + **reason codes** + `dependency_chain` evidence |
| Lifecycle | activate/dispose | explicit **component state machine** + drain + shadow activation |
| Replacement | out of scope | **provider generations**, atomic lease switch, run-pinned graphs |
| Profiles | mentioned | **first-class**: `research`/`simulation`/`demo`/`live` readiness policy |
| Injection | `ctx.inject()` everywhere | **construction-time typed injection**; service-locator lookups banned in hot paths |
| Audit | static graph + shadow | **five graphs**: static, runtime, state, configuration, frontend |
| Deletion test | config-disable in CI | config-disable CI **plus** fresh-process physical-deletion proof **plus reinstall** |
| Test placement | all feature-local | feature-local **plus** system-level removability tests kept outside the provider |
| Utils split | late (W11) | **early**, right after the pure pilot |
| Pilot | whole `indicators` domain | **RSI + Williams %R** first, then the domain |
| HMR | binary out-of-scope | **three tiers**; Tier 1 (config reconciliation) is in scope |
| Governance | 12 decisions, all up front | **staged**: 5 lock at G1, the rest at the gate that needs them |

Retained from v1 unchanged: the migration-ledger blocker, removability tiers, existing-asset leverage, stop conditions, risk register.

---

## 0.2 What is rejected from the original brainstorm

**"Change the import from domain root to feature root" — rejected.** It multiplies the public contract surface ~15×, and a static import is an unconditional hard requirement by construction. Consumers import *capability specifications*, never providers. Domain roots survive only as **temporary** compatibility façades with a sunset date, and internal code may not use them.

**Function-only exports — amended, not relaxed wholesale.** Feature packages may export protocols/ABCs, frozen dataclasses, Pydantic models, enums, immutable constants, factories, pure functions, diagnostics. They may **not** export active singletons, DB connections, mutable registries, broker sessions, module-level clients, or provider objects for consumers to construct.

**FR tests inside production modules via `if __name__ == "__main__":` — rejected.** Replaced by the layout in D-12.

---

## 0.3 Existing assets that shorten this

- `app/services/brokers/capabilities/` + `conformance/` — "one capability, N interchangeable implementations, proven by a conformance suite" already exists for one domain. The kernel generalises it upward.
- `app/services/portfolio/__init__.py` — lazy `_EXPORTS` + `__getattr__` is the façade mechanism, already working.
- `app/services/api/composition/` — an explicit wiring layer already exists.
- `app/runtime.py` — `validate_runtime_configuration(runtime_profile, execution_route)` is already the profile gate; profile readiness extends it rather than replacing it.

**Counter-example, verified:** `app/utils/__init__.py` is a **fully eager** barrel — `from app.utils import get_logger` currently pulls in `notifications`, `security`, `serialization`, and everything else. An optional utility can take down unrelated consumers today. This is why the Utils split moves early.

---

# Part I — Foundation

## Phase 0 — Protected baseline

**Goal:** an authoritative snapshot proving later phases did not change financial behaviour.

- [ ] Record commit; create refactor branch.
- [ ] Full `pytest`, `ruff check`, `ruff format --check`, strict `mypy`, coverage recorded.
- [ ] Frontend build + Vitest + Playwright recorded.
- [ ] Inventory: public package exports, API routes and contracts, applied migrations and schema checksums, runtime-profile startup/readiness behaviour.
- [ ] Inventory live resources: provider connections, background tasks, threads, sockets, timers, subscriptions, shutdown behaviour.
- [ ] **Capture golden output fixtures** for deterministic calculations: indicators, analytics, risk, strategy signals, simulation, portfolio valuation, order-request construction.
- [ ] Fresh-process application-import smoke test.
- [ ] Deletion-test harness scaffolded, expectations **not yet enforced**.

**Gate G0:** verification suite passes; deterministic outputs captured; baseline recreatable from a clean checkout.
`test(architecture): capture pre-composability baseline`

---

## Phase 1 — Governing rules and decisions

**Goal:** amend repository policy *before* implementation. The agent must never be asked to follow rules that contradict the target architecture.

### 1.1 Architectural units

| Unit | Meaning |
|---|---|
| Kernel | Protected, business-neutral runtime that discovers, resolves, and manages components |
| Capability specification | Stable versioned contract for a service that may be provided |
| Provider | Concrete implementation of one or more capabilities — **the runtime removal unit** |
| Component | One activated provider generation + its configuration + its owned effects |
| Feature | Product capability owned by a domain; may comprise several providers |
| Domain | Ownership namespace, not necessarily one runtime component |
| Profile | `research` \| `simulation` \| `demo` \| `live` readiness policy |
| Composition root | The only layer permitted to select providers and assemble components |
| Effect scope | Lifecycle owner of tasks, listeners, sockets, routes, locks |

> **Removability unit:** a *provider* is removable. A domain is removable when none of its providers is a protected kernel dependency. A folder containing multiple independently removable behaviours must be split into provider folders **or explicitly declared an atomic bundle**.

**Granularity guard (v2 addition):** default to bundling at the natural family level and split to individual providers **only on demonstrated need** — a consumer that wants one without the other, or differing dependencies. `indicators` alone would otherwise generate 50–150 provider folders. The RSI/Williams pilot proves splitting *works*; it does not mandate splitting everything.

### 1.2 Decisions to lock

**Governance is staged, not monolithic.** Only the five **G1** decisions change repository policy and therefore block all code; the rest are locked at the gate of the phase that first needs them. Deciding everything up front is over-specification — you would be committing to a resolution-timing or error-model choice before the audit has told you what the graph actually looks like.

| # | Decision | Lock by | Recommendation |
|---|---|---|---|
| D-09 | Migration/schema | **G1** | Append-only + tombstones + **uninstall ≠ purge** (§Phase 8). *Amends AGENTS.md §5 — the hard blocker.* |
| D-10 | Access mechanism | **G1** | Consumers import capability specs; providers injected at construction. **No repeated `registry.get(...)` in business code.** *Amends AGENTS.md §1; this is the "don't rewrite imports first" spine.* |
| D-12 | Test/example placement | **G1** | §1.4. *Amends AGENTS.md §2.* |
| D-01 | Kernel membership | **G1** | `app/kernel/` = machinery only: identifiers, manifests, discovery, registry, resolver, profiles, states, errors, health, diagnostics. Contracts live in `app/capabilities/`, not the kernel. |
| — | Export-surface amendment | **G1** | Per §0.2. *Amends AGENTS.md §1.* |
| D-02 | Capability naming + version | G3 | `domain.capability.vN` (e.g. `indicator.rsi.v1`, `risk.order_authorization.v2`). `requires` carries a version range. |
| D-03 | Cardinality | G3 | `exactly_one` \| `zero_or_one` \| `one_of_several` \| `many`. Brokers are `one_of_several`; indicators are `many`. |
| D-05 | Resolution timing | G4 | Resolve at **activation**. `api` synthesises call-time unavailability at its own boundary so external clients keep a stable surface. |
| D-04 | `on_missing` policy | G4 | Per `requires` entry: `fail_closed` \| `degrade` \| `skip`. **Default `fail_closed`.** |
| D-07 | Effect classes | G5 | Three-way (§1.3). |
| D-08 | Quiesce protocol | G5 | `can_dispose()`; *quiesce → drain → dispose in reverse registration order*. Refusal is a structured error, never a forced teardown. |
| D-06 | Error model | G7 | One family `CAPABILITY_UNAVAILABLE` + reason code + evidence (§7). |
| D-11 | Registry direction | Phase 16 | Manifest is source of truth; README `### Feature Registry` tables are generated. |
| D-13 | HMR | Phase 17 | Tier 1 in scope; Tiers 2–3 deferred. |

The recommendations for later-gate decisions are stated now as **defaults, not commitments** — carry them as working assumptions, and let Phases 2–5 falsify them. A decision that survives the audit unchanged costs nothing; one that was locked prematurely costs a rewrite.

### 1.2.1 Resolved by the owner, 2026-08-20

These seven were resolved ahead of their gates because the Phase 3–5 work orders could not be written without them. They are commitments, not defaults.

| Ref | Question | Resolution |
|---|---|---|
| R-01 | Capability contract shape | **Hybrid.** `typing.Protocol` for effectful capabilities (brokers, streams, persistence, anything owning a scope); frozen dataclass of callables for pure ones (indicators, calculations). The split follows the §1.3 effect classes. |
| R-02 | Concurrency model | **Sync core, async edge.** The kernel, resolver, registry, and lifecycle are synchronous. An async adapter layer wraps only streaming, broker transport, and API capabilities. Rationale: MetaTrader5 is a blocking C extension and cannot be made async; twelve domains are pure sync. *This supersedes the `AsyncExitStack` wording formerly in Phase 5.* |
| R-03 | Governance of new top-level packages | `app/kernel/`, `app/capabilities/`, and `app/composition/` are **non-feature infrastructure**: no `FEAT-*` IDs, no Feature Registry section, no numbered usage programs. Declared as an `AGENTS.md` §1 exception extending "Reconciliation Exclusions". |
| R-04 | Capability spec layout | `app/capabilities/<domain>/<capability>/vN.py` — e.g. `app/capabilities/indicator/rsi/v1.py`. Domain-owned specs were rejected: importing `app.services.data.capabilities` would execute a 60 KB domain `__init__.py`, defeating "importable with zero providers". |
| R-05 | Manifest format | `manifest.toml` per provider folder, parsed with stdlib `tomllib`. Discovery must not import implementation code, which rules out a Python manifest. No new dependency. |
| R-06 | Composition root location | New top-level `app/composition/`. Not `app/services/api/composition/` — the API domain is Tier B and must itself be removable. Not `app/kernel/` — provider-selection policy must not live inside business-neutral machinery. |
| R-07 | Approval granularity | One `APPROVED: EXECUTE` per **phase**; mechanical steps inside a phase are pre-authorised in that phase's dry run. |

### 1.3 Effect classes

| Class | Examples | Removal treatment |
|---|---|---|
| Reversible ephemeral | task, timer, listener, socket, HTTP client, route contribution | dispose automatically |
| Durable compensatable | cache registration, provisional record, lock lease | transaction, compensation, tombstone, or release |
| Irreversible external | filled order, sent message, external publication | preserve evidence, stop new actions, reconcile |

> **Safety rule:** disposal must never place a compensating trade automatically. Any financially compensating action is an explicit governed operation, never a lifecycle side effect.

### 1.4 Test and example placement

```text
provider/
├── manifest.toml
├── plugin.py            # setup/factory — no import-time effects
├── implementation.py
├── example.py           # executable usage evidence + conformance proof
├── README.md
├── __main__.py          # optional diagnostics
└── tests/
    ├── test_contract.py
    ├── test_unit.py
    ├── test_lifecycle.py
    └── test_removability.py
```

**System-level tests stay outside the provider:**

```text
tests/architecture/     tests/composition/     tests/removability/
```

> **Why this matters:** deleting the provider must not delete the only tests proving the *rest of the application* survives without it. v1 got this wrong.

`tests/{domain}/usage/` is retired.

### 1.5 Profile readiness

| Profile | Missing-capability behaviour |
|---|---|
| Research | Missing optional research tool deactivates that tool; missing authoritative data capability makes the affected workflow unready |
| Simulation | Missing simulator, selected strategy dependencies, risk controls, or historical data makes the run unavailable |
| Demo | Missing broker transport, Risk, Trading, reconciliation, idempotency, audit, or kill-switch makes demo execution unavailable |
| Live | **Any** missing safety or execution capability makes the profile unready and blocks all mutations |

### 1.6 AGENTS.md amendments required before Phase 2

| Rule | Blocks | Amendment |
|---|---|---|
| §1 Function-Only Public API Surface | Protocols, DTOs, models at the boundary | permit per §0.2 |
| §1 Package-Root Export Gate | — *(keep; it is load-bearing)* | restate root as **transitional** façade; internal use prohibited |
| §1 No Deep Cross-Domain Imports | — *(keep)* | extend: cross-domain consumers import **capability specs**, not providers |
| §1 Three-Feature Shared-Support Threshold | no stability axis | kernel/spec-eligible = stable + tiny + versioned; convenience-shared belongs to an owner |
| §2 Usage Evidence | `tests/{domain}/usage/` location | relocate per §1.4 |
| §2 Quality (`print` ban) | feature `example.py` | extend the standalone-script exception |
| §4 Feature Registry Authority | generated registries | manifest is source; README is published output |
| §4 Decision Hygiene | this document | carve out implementation plans (already implied by §4's "implementation-plan checklist item") |
| **§5 Immutable Historical Steps** | **feature deletion** | **add tombstone + uninstall≠purge rules (D-09)** |

> **The single most important present-tense finding.** As written today, deleting a feature that owns `migrations/` does not degrade the app — a checksum/ledger mismatch **blocks all database access**. **Twelve of the fifteen packages own a `migrations/` folder** (all except `api`, `ui`, `utils`). There is almost no removal path that does not hit this rule.

**Operational note (repo-specific):** AGENTS.md §1 requires a dry run plus a standalone `APPROVED: EXECUTE` per change. At ~17 phases this is a lot of gates. **Batch the approval unit at the phase level**, not the file level, and pre-authorise the mechanical steps inside a phase in the dry run — otherwise this plan dies of process before it dies of scope.

**Gate G1:** the five G1 decisions resolved and the corresponding `AGENTS.md`, `docs/ARCHITECTURE.md`, `docs/PROJECT.md` amendments merged. No implementation before this. Later-gate decisions remain open by design.
`docs(architecture): define spatiotemporal composition rules`

---

## Phase 2 — Five-graph audit

The migration order is *generated* here, not assumed.

| Graph | Extract |
|---|---|
| **Static Python** | absolute/relative imports, `TYPE_CHECKING` imports, `importlib`/`find_spec`, string module paths, package-root re-exports, deferred `_EXPORTS` maps, function-local imports, decorator registrations |
| **Runtime composition** | FastAPI router mounting, provider registries, event subscribers, scheduled jobs, background tasks, callbacks/DI, broker & data subscriptions, startup/shutdown hooks, workers and subprocesses |
| **State** | migration ordering, table ownership, foreign keys, shared writers, schema IDs, **serialized Python class paths**, caches, persisted registries, idempotency and audit dependencies |
| **Configuration** | module paths in config, provider names, profile settings, feature flags, env assumptions, secret references, static allowlists |
| **Frontend** | TS imports, dynamic imports, Next.js routes, navigation registrations, widget registries, generated API clients, feature stores, page-level backend assumptions |

> **Why five.** Config and state are real coupling channels invisible to imports. A persisted record holding a Python class path is a deletability blocker that no import graph will ever show you.

> **Calibration.** The AST scan **overstates** current coupling wherever lazy `__getattr__` barrels exist (`portfolio`, and per Phase 0 inventory others) — `TYPE_CHECKING` imports cost nothing at runtime. Weight fan-in/fan-out by *resolved runtime symbol*, not import-statement count. Conversely `app/utils` is fully eager and its true fan-in is worse than it looks.

**Required outputs:** domain removability matrix, feature/provider removability matrix, dependency-edge matrix (type, capability version, required/optional, cardinality, profile scope, lifecycle scope, security criticality), cycle report separating legitimate event flows from hard code cycles.

**Exit gate G2:** every domain and registered feature classified as one of — protected kernel candidate / stable capability spec / required profile provider / optional provider / composition-only module / compatibility façade / historical migration artifact / invalid coupling requiring refactor. Unexplained dynamic imports must be zero or explicitly allowlisted.
`build(architecture): add dependency and removability audit`

---

## Phase 3 — Capability specification layer

`app/capabilities/<capability>/vN.py` — importable with **zero providers installed**.

**May contain:** identifier, API version, protocol/ABC, immutable requests and responses, semantic errors, compatibility rules, event specifications, conformance helpers.
**May not contain:** implementation, provider selection, DB/broker/network access, imports of `app.services.*` or `app.agentic.*`, registration side effects.

Group specs by domain prefix to avoid a flat directory of 200+ entries.

**Gate G3:** a consumer imports a capability protocol without importing or requiring any provider. Architecture test enforces the import ban.
`feat(capabilities): add versioned provider-neutral specifications`

---

## Phase 4 — Protected microkernel

```text
app/kernel/{identifiers,manifests,discovery,registry,resolver,profiles,states,errors,health,diagnostics}.py
```

**Does:** read and validate manifests; discover providers *without importing implementation code*; maintain inventories; resolve requirements; detect ambiguity and version incompatibility; compute dependency chains and profile readiness; expose component state; normalise errors; emit bounded diagnostics.

**Does not:** know RSI formulas or broker APIs; place trades; evaluate risk; touch domain databases; import `app.services.*` or `app.agentic.*`.

**Resolver:** validate manifests → build graph → reject duplicate IDs, incompatible versions, unresolved hard cycles → apply explicit configuration → deterministic priority only where configuration permits → **never use import order as provider selection** → resolve transitive unavailability → return a complete resolution report *before* activation.

**Gate G4:** in a copied tree with `app/services/` absent, `import app.kernel` succeeds and reports *no business providers* rather than raising `ImportError`.
`feat(kernel): add capability discovery and resolution`

---

## Phase 5 — Lifecycle and effect ownership

**Component states:** `DISCOVERED → DISABLED → RESOLVING → WAITING_FOR_DEPENDENCY → STARTING → ACTIVE → DEGRADED → DRAINING → STOPPING → STOPPED`, plus terminal `FAILED`, `FAILED_CLEANUP`, `QUARANTINED`, `VERSION_INCOMPATIBLE`.

**Activation scope** owns: tasks and task groups, timers, listeners, event and broker subscriptions, network clients, sockets, DB sessions, locks and leases, temp files, subprocesses, thread workers, metric collectors, route contributions. Per **R-02** the scope is **synchronous**: implement on `contextlib.ExitStack` plus explicit disposer registration. The async edge (streaming, broker transport, API) wraps a sync scope in an `AsyncExitStack` adapter; async never leaks into the kernel or into a pure domain.

**Activate:** validate config → resolve deps → allocate isolated scope → construct → start resources → readiness probes → publish capabilities → `ACTIVE`.
**Deactivate:** `DRAINING` → stop new leases → deactivate dependents in reverse dependency order → drain or cancel per policy → remove capability bindings → dispose effects in reverse registration order → verify no owned resource remains → `STOPPED` or `FAILED_CLEANUP`.

**Required tests:** successful activation; failure before allocation; failure after *partial* allocation; idempotent double shutdown; reverse-order cleanup; timed-out cleanup; task cancellation; listener cleanup; socket/client cleanup; consumer deactivation on upstream loss; no admission while draining.

**Gate G5:** a test provider owning tasks, listeners, timers, and a mock client returns all resource counts to zero after deactivation. Full `pytest` with per-test scopes shows zero `ResourceWarning`/`RuntimeWarning` leaks — retiring the standing AGENTS.md §2 concern.
`feat(kernel): add component lifecycle and effect scopes`

---

## Phase 6 — Composition, injection, generations

**Anti-service-locator rule.** Business code must not repeatedly call `registry.get("capability.name")`. The resolver selects; the composition root activates; **typed dependencies are injected at provider construction**; the active component holds direct typed references. Replacement creates a **new generation** rather than mutating the old instance.

Each active provider carries: provider ID, provider version, capability contract versions, generation ID, configuration digest, dependency-generation IDs, activation timestamp, effect-scope identity.

**Transactional replacement:** discover candidate → validate manifest/config → start in isolated **shadow scope** → readiness + contract checks → reject without touching the incumbent on failure → **atomic lease switch** → old generation `DRAINING` → finish or cancel in-flight → dispose → preserve rollback evidence.

**Scope levels:** process, runtime profile, broker account, execution session, simulation run, strategy instance, request.

> **Reproducibility rule:** a simulation run **pins its full provider-generation set**. Indicator or risk implementations must not change halfway through a run.

**Gate G6:** a consumer survives successful provider replacement without retaining a stale instance.
`feat(composition): add injected provider generations`

---

## Phase 7 — Capability errors, health, profile readiness

**Family:** `CAPABILITY_UNAVAILABLE`.
**Reason codes:** `NOT_INSTALLED`, `DISABLED`, `VERSION_INCOMPATIBLE`, `DEPENDENCY_UNAVAILABLE`, `PROVIDER_AMBIGUOUS`, `CONFIG_INVALID`, `ACTIVATION_FAILED`, `UNHEALTHY`, `DRAINING`, `LOST_DURING_OPERATION`, `PROFILE_REQUIREMENT_UNSATISFIED`, `POLICY_BLOCKED`, `CLEANUP_FAILED`.

```json
{
  "code": "CAPABILITY_UNAVAILABLE",
  "reason_code": "DEPENDENCY_UNAVAILABLE",
  "capability": "research.profile.v1",
  "consumer": "optimization.search.v1",
  "provider_id": null,
  "provider_state": "NOT_INSTALLED",
  "profile": "research",
  "dependency_chain": ["optimization.search.v1", "research.profile.v1", "analytics.performance.v2"],
  "retryable": false
}
```

**Six distinct status concepts, never collapsed:** process liveness · kernel readiness · capability availability · provider health · profile readiness · operation authorization. An active API process may honestly report `live` unready.

**Live safety rule.** Absence of any required safety capability must block new mutation, prevent fallback to a less restrictive provider, keep position and reconciliation authority intact, preserve audit evidence, and report the exact missing requirement.

> **Authorization rule.** Risk publishes authorization as an **explicit positive capability**. Trading must never infer authorization from an absent error or a missing response. Absence-of-denial is not consent.

**Gate G7:** all service, API, CLI, and agent-tool boundaries normalise missing-capability behaviour into this one family.
`feat(kernel): add profile readiness and capability errors`

---

## Phase 8 — Provider state and migration lifecycle

**Rules:**

- installing a provider may apply **additive** migrations;
- disabling a provider does **not** drop its tables;
- removing provider code does **not** erase its data;
- historical migrations needed to verify an existing database remain available as **tombstones** keyed by capability ID; the ledger tolerates "applied, owner absent" without blocking database access;
- **data purge is a separate explicit operator action** requiring authorization;
- reinstallation validates schema compatibility;
- provider records carry **stable schema IDs, never Python implementation class paths**;
- unknown historical records are preserved or quarantined;
- cross-feature foreign keys are minimised;
- a provider does not run migrations merely because its module was imported.

**Manifest additions for stateful providers:** state-schema ID, state-schema version, migration manifest, compatible prior versions, downgrade policy, uninstall retention policy, purge authorization requirement.

Feature owns its migration definitions; a domain aggregator collects manifests **without owning or rewriting them**. `data` retains shared execution, locking, checksum, and ledger infrastructure.

**Required test cycle:** install → migrate → disable → restart without provider → verify kernel and unaffected profiles → **reinstall compatible provider → verify preserved state** → reject incompatible schema → prove uninstall does not drop data → prove purge requires explicit authority.

**Gate G8:** a stateful provider can be absent while its historical database evidence remains valid and startup-safe.
`feat(composition): define provider state retention and migrations`

---

# Part II — Pilots

No broad migration begins before G0–G8.

## Phase 9 — Pure pilot: RSI and Williams %R

**Verified structure today:** `app/services/indicators/momentum/` contains `rsi.py` (6.3 KB) and `williams_r.py` (6.2 KB) — two independently removable behaviours in one folder. Exactly the case §1.1 requires splitting or declaring atomic.

**Target:**

```text
app/services/indicators/
├── rsi_default/           { manifest.toml, plugin.py, implementation.py, example.py, README.md, tests/ }
├── williams_r_default/    { same }
└── momentum/              { README.md, __init__.py }   # organizational namespace only
```

Per provider: create `indicator.rsi.v1` spec · preserve the exact formula and deterministic outputs · manifest · implementation behind a factory · declare closed-bar and input-schema requirements · remove import-time registration · contract tests · **output-parity tests against Phase 0 fixtures** · absence tests · replacement tests · `example.py` · temporary domain-root compatibility export.

**Cross-feature proof.** A test consumer requiring RSI but not Williams %R: deleting Williams must not affect it; deleting RSI must deactivate it; **reinstalling RSI must reactivate it**; the domain and unrelated indicators stay available.

**Gate G9:** physical deletion of either provider folder in a fresh copied tree does not prevent kernel or app import, does not break the other indicator, produces correct capability status, and alters no unrelated output.
`refactor(indicators): make RSI an independently removable provider`

---

## Phase 10 — Effectful pilot: Notifications, then one Data stream

**Pilot A — Notifications.** Chosen because it owns clients, templates, sessions, and external delivery *without* trading authority. And because `app/utils/__init__.py` is eager today, so this pilot simultaneously fixes a live fragility.

Extract true kernel primitives from `app.utils` · keep notifications outside the kernel · define notification capability specs · provider manifests per transport · move clients into activation scopes · record sent notifications as **irreversible** effects · dispose clients and queues on deactivation · prove `app/runtime.py` profile validation imports with Notifications absent · **prove no silent transport fallback** · absence and replacement tests.

**Pilot B — one Data stream.** Select one bounded live or simulated stream provider. Track subscription, task, buffer, and connection ownership. Test draining while consumers hold active leases; upstream broker-reader disappearance; reconnection as a **new generation**; **no duplicate events after replacement**.

**Gate G10:** both the pure and the effectful models are proven before broad migration.

---

## Phase 11 — Deletion, reinstall, and enforcement CI

Three complementary proofs — the fast one gates every merge, the slow one runs periodically.

1. **Config-disable matrix (fast, every merge).** For each optional provider: disable in loader config, boot, assert startup succeeds, capability reports `CAPABILITY_UNAVAILABLE` with the right reason code, dependents behave per `on_missing`.
2. **Fresh-process physical deletion (slow, nightly).** Copy the tree, delete the provider folder, **new interpreter**, import kernel → import app → resolve profiles → call the affected capability → verify transitive consumers → run unaffected tests → **verify no stale `sys.modules` entry masks the deletion** → verify packaging, `mypy`, and frontend build.
3. **Reinstall cycle.** Remove → restart → reinstall → assert consumers reactivate and state is preserved (Phase 8).

**Inverse assertion.** For providers marked *required* (kernel, `risk.kill_switch`, live safety set): disabling must **fail closed and refuse to boot**. Fail-closed is tested as deliberately as degradation.

> Config-disable is only equivalent to deletion **if the loader is the sole activation path** — which is why the import-time-side-effect lint (Phase 16) is a precondition, and why proof #2 exists at all.

**Gate G11:** all three green and required to merge.

---

# Part III — Cross-domain waves

Exact topological order comes from Phase 2. Expected sequence below. A detected cycle is broken through contracts, events, or ownership correction — cyclic domains are not migrated as one coupled block.

| # | Layer | Intra-domain sequence | Tier |
|---|---|---|---|
| 12.1 | **Utils separation** | kernel primitives → shared response/error contracts → time, identity, serialization, units, validation, security → settings/config as scoped providers → idempotency, state machine → logging beyond bootstrap → notifications, progress last. **Do not move all of Utils into the kernel.** | mixed |
| 12.2 | **Data foundation** | connection/locking/transaction/ledger → dataset & event specs → historical storage/retrieval → normalization & timestamp alignment → resampling & closed-bar projection → lineage & persistence → provider-backed acquisition | C |
| 12.3 | **Brokers read path** | neutral specs → broker identity & venue metadata → symbol metadata → read-only account/market data → connection & session lifecycle → snapshot gateways → adapters (MT5, cTrader, Binance, Dukascopy, Yahoo). **Mutation capabilities stay out of composition until Risk and Trading migrate.** | B |
| 12.4 | **Data live path** | broker stream adapter → Data-owned normalization → event sequencing → freshness & gap detection → persistence & fan-out → replacement & reconnection | B |
| 12.5 | **Indicators (remainder)** | common input/result specs → leaf pure indicators → structure & patterns → composite market-speed → regime providers (consume other indicators) → snapshots & catalogue. Composites migrate **after** their leaves. | A |
| 12.6 | **Analytics** | evidence & metric contracts → leaf calculators → grouped calculations → comparison/benchmark → reports → dashboards → journal & behavioral evidence → persistent evidence → workbench | A |
| 12.7 | **Strategy** | identity & version specs → parameter/config contracts → feature-capability declarations → signal evaluation → state & checkpoints → persistence → lifecycle & promotion → orchestration. Strategies **declare** indicator/data capabilities rather than import implementations. | B |
| 12.8 | **Portfolio — reads** | position & holding specs → FX and valuation → exposure projections → margin views → performance & reconciliation views. Read-only; no execution authority. | B |
| 12.9 | **Risk** | evidence & policy specs → pure limit calculations → exposure & correlation → account/portfolio projections → policy evaluation → drawdown & loss controls → news/weekend/overnight restrictions → **kill switch** → **authorization capability** → durable Risk state → profile-readiness integration | C (kill switch), B |
| 12.10 | **Portfolio — actions** | allocation proposals → rebalance proposals → lifecycle transitions → Risk-review requests → persistent evidence. Portfolio emits proposals; it does not import Trading execution. | B |
| 12.11 | **Trading contracts & state** | trade intent → order request → fill & lifetime policies → position & order state → execution session → idempotency records → reconciliation records → audit events | B |
| 12.12 | **Trading — route-neutral evaluation** | intent validation → strategy-lineage validation → risk-authorization requirement → preflight → evaluation cycle → deterministic timeouts. **No broker mutation yet.** | B |
| 12.13 | **Simulator** | clock → event queue → historical replay → simulated broker → simulated fills & account state → Strategy integration → Risk integration → Trading evaluation integration → artifacts & lineage → reproduction → workbench & batching. A run **pins its full capability graph**. | A |
| 12.14 | **Broker mutation** | order translation → provider preflight → demo transport → live transport → cancel/close/modify → connection-loss classification → unknown-outcome handling. Providers do not grant themselves permission. | B |
| 12.15 | **Trading demo/live composition** | compose evaluation → require Risk authorization → idempotency → audit append → reconciliation → kill switch → broker mutation → bind credentials by profile → start demo → start live **only after all safety gates pass** | B |
| 12.16 | **Research** | dataset & leakage protections → pure features → statistics → seasonality → market structure → studies & null baselines → profile/report projections → experiment & run persistence → drift evidence → fundamental/sentiment evidence → orchestration | A |
| 12.17 | **Optimization** | search-space contract → objective contract → trial contract → sampler providers → simulator objective adapter → robustness & stability → trial persistence → orchestration → workbench. Removing one sampler removes one algorithm, not the domain. | A |
| 12.18 | **Agentic** | immutable contracts → mandate & role manifests → model-runtime capability → permission & authorization enforcement → context & memory → deterministic tool adapters → agent providers → deliberation & workflow → artifact lifecycle → API orchestration. **Never imports concrete Trading, Risk, Broker, Data, or Research implementations.** | A |
| 12.19 | **API** | keep identity, security middleware, core health, error normalization always available → move discovery/resolution into the kernel → route-contribution capability → provider/source contributions → stable dispatch layer → activate routes only for resolved providers → structured unavailable responses where route contracts require → rebuild routers **by generation** → expose capability & readiness projections → retain compatibility routes → remove hardcoded optional-domain inventories and static optional-router imports | B |
| 12.20 | **UI** | typed capability/readiness client → capability store → shell independent of optional workspaces → navigation as declared contributions → optional pages/widgets as dynamic modules → explicit unavailable/disabled/loading/stale/unhealthy states → prevent calls to unavailable capabilities → deep links resolve to structured unavailable view → profile-readiness presentation → build variants with feature modules absent | B |
| 12.21 | **Cutover** | remove internal compatibility imports; enforce the deletion matrix | — |

**Route-table warning (12.19).** Do not repeatedly mutate one FastAPI route table in arbitrary order. Use generation-scoped sub-applications, mounted routers rebuilt during controlled replacement, **or** stable dispatch routes whose provider target switches atomically.

**Cycle-breaking notes.** Portfolio splits into reads (12.8) and actions (12.10) specifically to break the Risk↔Portfolio cycle. Broker mutation is deliberately deferred to 12.14 so execution authority never precedes Risk authorization.

### Removability tiers

- **Tier C — required by construction:** `app/kernel`, `app/capabilities`, Data core (persistence, market data), `risk.kill_switch` and the live safety set. Deleting these *should* fail closed. Asserted by CI's inverse matrix.
- **Tier B — optional with declared degradation:** Portfolio, Brokers (≥1 implementation required, any specific one optional), Trading (absent ⇒ research-only build), Strategy sub-features, API/UI widgets.
- **Tier A — freely removable:** Research, Optimization, Analytics, Agentic, Simulator, individual indicators, individual brokers, Notifications, optional Data sources.

Effort concentrates on A and B. **No effort is spent making Tier C optional.**

### `app/ui` is a second runtime

Next.js/TypeScript with its own `package.json`, Vitest, Playwright. Kernel, resolver, and effect scopes are Python-only and stop at the API boundary. The resolver exposes the active capability graph over HTTP (`api/health/` or `observability/`); widgets declare the capability they need and render degraded states rather than handling 5xx. Deletion CI extends to the UI via the existing Playwright config — this also discharges the AGENTS.md §1 `FEAT-UI-*` unavailable-state evidence requirement.

---

# Part IV — Repeatable per-provider migration procedure

Every provider in every domain follows the same ten steps.

| Step | Actions |
|---|---|
| **A — Removal boundary** | confirm the folder is one removable provider · split category folders holding independent providers · declare atomic bundles explicitly · assign stable provider ID · assign provided capabilities and versions |
| **B — Classify code** | implementation · capability spec · domain-local shared support · historical migrations · compatibility exports · import-time side effects · runtime resources · all consumers |
| **C — Extract contracts** | move neutral protocols/schemas to `app/capabilities/` · keep implementation-specific models inside the provider · version · compatibility rules · standard errors · required vs optional deps |
| **D — Manifest** | ID, version, entry point, capabilities provided, required, optional, scope & profile permissions, lifecycle & reload policy, effect classes, config schema, state-schema version |
| **E — Remove hidden construction** | eliminate import-time registration, module-level clients, module-level mutable state · add explicit factory · typed injection · config via activation context · register all resources with the effect scope |
| **F — Migrate consumers** | concrete imports → capability-spec imports · constructor calls → injected deps · remove service-locator lookups from hot paths · declare transitive requirements · **preserve exact financial semantics** · add missing-capability behaviour · add profile-impact evidence |
| **G — Compatibility façade** | retain temporary domain-root wrappers resolving the active capability · return structured unavailability when absent · **prohibit internal use** · remove only after all external callers migrate |
| **H — Verify** | contract conformance · unit · **deterministic output parity vs Phase 0** · lifecycle · partial-startup cleanup · absence · upstream-loss · replacement · resource-leak · profile readiness · `example.py` · fresh-process deletion |
| **I — Ownership records** | Feature Registry (generated) · public API docs · capability dependencies · profile impact · migration/state ownership · removal behaviour · usage and test evidence |
| **J — Deletion proof** | per Phase 11 proof #2, in a copied tree |

### Feature ordering within a domain

leaf providers → shared support → hub providers, with effect-heavy providers last within each tier.

---

# Part V — Shared-support policy

1. **Stable cross-domain contracts** live in `app/capabilities/<capability>/vN.py` and must outlive any individual provider.
2. **Domain-local support** is permitted only when ≥3 independent features consume it, it owns one coherent capability, it contains no orchestration, it is not a second implementation location, and deleting one feature does not delete it.
3. **One- or two-consumer support** stays inside an explicit owner feature; the other consumer depends on that owner's capability.
4. **Category folders** (`momentum`, `trend`, `volatility`) may be organizational namespaces only.
5. **Composite features** declare capability dependencies, not files — e.g. `market_speed.composite.v1` requires `momentum.acceleration.v1`, `volatility.expansion.v1`, `volume.acceleration.v1`. Removing one leaf deactivates the composite, not the leaves.
6. **Events** use versioned contracts and must not hide a synchronous mandatory dependency.
7. **Migrations** stay feature-owned; domain aggregation collects manifests without importing implementations.

> **The pattern to notice:** `contracts/ + persistence/ + migrations/` recurs in nearly every domain, and `_shared/` in two more. This is one structural problem repeated ten times, not ten problems. Solve ownership once in the pilot and the rest is mechanical. It is also exactly the case the original brainstorm flagged — "deleting a generic contract folder breaks everything."

**Named hard cases:** `data` (`_shared/`, `contracts/`, `persistence/`, `migrations/` — four horizontals, the largest blocker) · `risk/kill_switch/` (non-disableable; the resolver is a new bypass surface for AGENTS.md §3 and must be closed explicitly) · `trading` (`state/`, `session_registry/`, `live/`, `protective_orders/` — irreversible effects) · `strategy/registry/` (an existing in-domain registry that must be **reconciled** with the global resolver, not run alongside it) · `brokers` (`canonical_contracts/`, `capabilities/`, `conformance/` — already near-target; generalise upward) · `research/data/` (name collides with the `data` domain; rename during step A) · `utils` (`notifications/`, `security/`, `state_machine/`, `random_streams/`, `progress/` — universal by convenience, not stability).

---

# Part VI — Enforcement

## Phase 16 — Executable architecture constraints

- [ ] Kernel may not import business domains.
- [ ] Capability specs may not import providers.
- [ ] Cross-domain modules may not import concrete providers.
- [ ] Dynamic imports only in approved loader modules.
- [ ] **Provider import may not start I/O** (the precondition that makes config-disable honest).
- [ ] Every provider folder has a valid manifest.
- [ ] Every provided capability has a stable specification.
- [ ] Every required capability resolves or produces an explicit inactive state.
- [ ] Hard dependency cycles forbidden; cycles only through optional/reactive deps.
- [ ] Provider selection cannot depend on import order.
- [ ] Demo/live require their complete safety sets.
- [ ] Every effectful provider has lifecycle tests.
- [ ] Every removable provider has a fresh-process deletion test.
- [ ] Every UI capability has unavailable-state evidence.
- [ ] Removability matrices regenerated in CI.

**Legacy cleanup order:** stop adding new domain-root internal imports → migrate internal consumers → deprecate large `_EXPORTS` maps → retain external wrappers → collect usage references → remove obsolete wrappers → remove hardcoded inventories → make checks mandatory.

`ci(architecture): enforce capability and removability boundaries`

---

## Phase 17 — Controlled runtime replacement

HMR is **not** a prerequisite for removability. It is the final optional capability.

| Tier | Scope | Requirements |
|---|---|---|
| **1 — Config reconciliation** *(in scope)* | validate new config → compute affected providers → deactivate in reverse dependency order → reactivate in dependency order → rollback on candidate failure | reuses Phase 5 + 6 machinery; also what the deletion CI already needs |
| **2 — Logical in-process replacement** *(deferred)* | pure providers, stateless indicators, bounded analytics calculators, safely restartable internal services | shadow activation, readiness proof, atomic lease switch, generation pinning, draining, rollback |
| **3 — Process-isolated replacement** *(deferred)* | broker connections, live market streams, live execution, long-running workers, model runtimes, native-extension providers | new process → health check → switch authority → drain old → terminate |

**Live policy:** in-process source-code HMR stays disabled for live Trading and Brokers unless a later verified safety case explicitly authorises it. Process-isolated replacement is the safer default — and the right answer for MT5's native dependency.

---

# Definition of done

- [ ] Kernel imports no business provider.
- [ ] Every cross-domain dependency is a versioned capability.
- [ ] Every independently removable behaviour has its own provider unit, or is a declared atomic bundle.
- [ ] Every provider has a static manifest.
- [ ] Every required dependency resolves before activation.
- [ ] Every reversible effect is lifecycle-owned.
- [ ] Every durable or irreversible effect has a reconciliation policy, and none is auto-compensated.
- [ ] Missing optional capabilities deactivate only their consumers.
- [ ] Missing profile-critical capabilities make the profile unready.
- [ ] Demo and live fail closed without Risk and the complete safety set.
- [ ] Absence, activation failure, health failure, and dependency failure are distinguishable.
- [ ] Provider replacement is generational and transactional.
- [ ] Stateful provider removal preserves historical data; purge is separately authorised.
- [ ] Examples live with features; system-level removability tests live outside them.
- [ ] Backend and frontend both tolerate capability absence.
- [ ] Every removable provider passes a fresh-process deletion **and reinstall** test.
- [ ] Removability matrices are generated and enforced in CI.
- [ ] **All Phase 0 deterministic financial outputs are unchanged**, unless a separately approved behaviour change documents otherwise.

---

# Risk register

| Risk | Mitigation |
|---|---|
| Migration ledger blocks DB access on first removal | D-09 amended into AGENTS.md §5 at G1, before code; verified at Phase 8 and again at 12.2 |
| Silent financial behaviour change during refactor | Phase 0 golden fixtures + output-parity tests in step H of every provider |
| Coupling moves into capability strings and becomes unverifiable | manifest + architecture lints exist at Phase 16, and the audit's five graphs are regenerated in CI |
| Config-disable masks a real import coupling | fresh-process deletion proof with `sys.modules` verification (Phase 11 #2) |
| Silent degradation of a risk check | `on_missing` defaults `fail_closed`; Risk publishes explicit positive authorization; kill switch non-disableable with inverse CI assertion |
| Disposal triggers a compensating trade | explicit rule in §1.3; irreversible effects preserve evidence and reconcile only |
| Persisted class paths break on provider deletion | stable schema IDs (Phase 8); surfaced by the state graph (Phase 2) |
| Provider explosion (50–150 folders in Indicators alone) | granularity guard in §1.1: bundle by default, split on demonstrated need |
| Two registries running at once | `strategy/registry/` reconciled with the resolver at 12.7 |
| **Death by approval gate** | batch `APPROVED: EXECUTE` at phase level; pre-authorise mechanical steps in the dry run |
| **Plan never finishes** | reduced-scope fallback below |

# Stop conditions

Halt and re-plan if:

- the kernel exceeds ~600 lines — it is absorbing capabilities;
- the RSI/Williams pilot requires changes to the kernel or resolver API — the model is wrong, and finding out at an indicator is far cheaper than at Trading;
- a Tier-A provider cannot be made removable without touching more than two other domains — its tier is misclassified;
- deletion CI runtime exceeds what can gate every merge — shrink the matrix, keep the gate;
- Phase 2's cycle report shows a hard cycle that cannot be broken by contract extraction — fix ownership before proceeding, do not migrate the cycle as a block.

# Reduced-scope fallback

If the full plan proves too large to finish, this ordered subset delivers most of the value and is independently coherent:

1. **Phase 0** — golden fixtures. Cheap, and permanently useful regardless of what follows.
2. **Phase 1 §1.6** — the AGENTS.md §5 tombstone amendment. Removes the single hard blocker; valuable even with zero other changes.
3. **Phase 10 Pilot A** — make `app/utils/__init__.py` lazy and lift Notifications out. Fixes a live fragility today, no kernel required.
4. **Phase 11 proof #1** — config-disable CI over whatever is already optional. Turns removability from an aspiration into a measurement.

Everything beyond that is the full model. These four are the ones worth doing even if the rest never happens.
