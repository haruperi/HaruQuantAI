# Domain Implementation Audit

> **Purpose:** Persistent, read-only procedure for determining whether one
> domain was built according to the authoritative
> [`Feature Implementation Pipeline`](feature_implementation_pipeline.md) within
> a generic modular monolith architecture.
>
> **Reciprocity rule:** This audit and the pipeline use the same closed `FIP-*`
> control catalogue. An audit-only requirement or an unaudited build
> requirement is a documentation defect. Change both files together.

An audit verifies evidence; it does not implement fixes, update evidence,
rewrite documentation, migrate databases, or change Git state. Findings that
require repository mutation proceed through the applicable task or quick-fix
workflow after separate authorization.

## 1. Audit Invocation

Instantiate these values before beginning:

```text
DOMAIN_NAME: <human-readable name>
DOMAIN_ID: <D-XXX>
DOMAIN_SLUG: <domain>
DOMAIN_NUMBER: <NN>
FEATURE_PREFIX: <PREFIX>
OWNING_REGISTRY: app/services/<domain>/README.md
PRODUCTION_PACKAGE: app/services/<domain>/
PUBLIC_CONTRACT: app/contracts/<domain>.py
PERSISTENCE_OWNER: app/services/persistence/<domain>.py
OWNED_TESTS: tests/services/<domain>/
CONSOLIDATED_EXAMPLE: tests/examples/<NN>_<domain>.py
WORKFLOW_TESTS: tests/system/integration/
FEATURE_EVIDENCE: docs/dev/evidence/features/FEAT-<PREFIX>-*/acceptance.json
AUDITED_REVISION: <full Git SHA>
```

A missing expected path is audit evidence, not permission to create it. A
missing persistence module may be conformant only when every feature in the
domain is truthfully stateless.

## 2. Authority and Safety

Apply authority in this order:

1. `AGENTS.md`.
2. `docs/PROJECT.md`.
3. `docs/ARCHITECTURE.md`.
4. The owning domain README.
5. Public contracts and executable, source-bound evidence.
6. This procedure and the feature implementation pipeline.

Report real conflicts rather than silently selecting a convenient rule.

During the audit:

- Do not modify source, documentation, tests, evidence, databases, or Git state.
- Never clear, migrate, reset, truncate, overwrite, or otherwise mutate the
  active workspace database.
- Run database checks only against isolated temporary databases.
- Do not invoke external providers, credentialed services, destructive operations,
  or remote publication.
- Use bounded explicit test paths. Never run bare or unfiltered pytest.
- Reuse a valid source-bound receipt instead of repeating its exact commands.
- Do not infer coverage, browser, provider, performance, soak, or release results.
- Treat README status, checklists, filenames, test names, and acceptance
  manifests as claims until independently reconciled.
- Record the exact revision, command, exit code, and evidence limitation for
  every dynamic conclusion.

## 3. Verdict Model

Each control receives exactly one verdict:

| Verdict | Meaning |
| --- | --- |
| `PASS` | Fully conformant at the audited revision; sufficient exact evidence is recorded. |
| `PARTIAL` | Some obligations pass, but bounded deviations remain; each deviation and remediation is recorded. |
| `FAIL` | One or more mandatory obligations are non-conformant; exact evidence and remediation are recorded. |
| `INCONCLUSIVE` | Available static or runtime evidence cannot establish the result; the missing evidence and resolution owner are recorded. |
| `N/A` | The responsibility demonstrably does not apply; feature-specific rationale is recorded. |

Do not collapse `PARTIAL` or `INCONCLUSIVE` into `PASS`. A passing unit test
cannot close an integration, coverage, UI, provider, workflow, performance, or
release obligation.

For every control record:

1. Control ID and title.
2. Verdict.
3. Requirements assessed.
4. Exact evidence: paths, symbols, line references, commands, exit codes,
   receipts, and manifest fields.
5. Deviation.
6. Required remediation and owning layer.
7. Evidence limitation or `N/A` rationale.

## 4. Reciprocal Audit Controls

The controls below mirror Section 4 of the feature implementation pipeline.
Assess every control independently.

### `FIP-01 REG` — Feature registry reconciliation

Reconcile every README-registered feature identity with exactly one cohesive
`app/services/<domain>/<feature>.py` module. Verify the module's `SPEC`, registry
factory, owned test path, consolidated example function, and acceptance evidence
path all identify the same feature. Exclude only README files, pure
initializers, the dedicated persistence module, and explicitly documented
support exceptions. Fail unregistered production features, registered features
without modules, feature subpackages, split ownership, duplicate owners, or
shadow implementations.

### `FIP-02 REQ` — Requirements and status reconciliation

Enumerate every feature status, FR, local NFR, applicable shared NFR, acceptance
ID, workflow contribution, catalogue/source binding, and open decision from the
owning README. Trace each to public operations, implementation symbols,
acceptance oracles, and executable evidence. A `Completed` declaration without
the complete chain is not conformant. Report missing, partial, excluded,
contradictory, stale, or unmapped obligations explicitly.

### `FIP-03 INIT` — Initializer purity

Parse every applicable `__init__.py`. It must be empty or docstring-only, with
no `__all__`, imports, re-exports, registration, I/O, task creation, logging
configuration, compatibility shims, or runtime code. The package root is not a
public API boundary.

### `FIP-04 MOD` — Single-module ownership

Verify one flat, cohesive feature module owns each backend feature. Reject
feature implementation folders, functionality split across alternative owners,
undocumented helper modules, or shared support acting as a feature registry.
Any support exception must satisfy the documented consumer-count or explicit
architecture exception and preserve one semantic owner.

### `FIP-05 SPEC` — Specification and configuration parity

For every feature compare module `SPEC`, feature class attributes, capability
major versions, required/optional dependencies, conflicts, state, strict
configuration keys/defaults, registry identity, and README declarations.
Unknown settings, silently ignored keys, implicit providers, undeclared
capabilities, or version shadowing fail this control.

### `FIP-06 IMPORT` — Import and collaboration boundaries

Inspect production features, examples, gateways, workflow code, and integration
tests for sibling or cross-domain feature implementation imports. Collaboration
must use public contracts, typed requests/events, and `FeatureContext`-resolved
capabilities. Private service symbols and UI/Interfaces implementation imports
across business boundaries are non-conformant.

### `FIP-07 CONTRACT-PURITY` — Public contract purity

Verify the domain contract contains only public DTOs, protocols, events, errors,
and versioned capability keys. It must not import removable services, perform
I/O, create runtime effects, execute persistence, or hide business
orchestration. Reconcile generated schemas when applicable and verify breaking
changes use an explicit new capability major.

### `FIP-08 USE` — Consolidated usage evidence

Verify one `example_<NN>_<feature_slug>()` function exists per completed backend
feature in `tests/examples/<NN>_<domain>.py`. Run the consolidated example when
safe. It must be realistic, offline, deterministic, bounded, secret-safe,
truthful about illustrative/unavailable/refused/partial outcomes, and clean up
resources. It must not duplicate production logic or claim provider, browser,
or release qualification. Do not require an arbitrary number of print
statements; require meaningful bounded output demonstrating the result.

### `FIP-09 WF` — Workflow coverage

Identify every active `WF-*` to which the domain contributes. Reconcile its lead
owner, participants, handoffs, failure/cancellation/recovery states, final
oracle, and independently owned system evidence. Do not count a domain-local
reading sequence as a canonical workflow. A local feature test cannot establish
cross-domain workflow acceptance, and a `PARTIAL` workflow cannot be reported
complete.

### `FIP-10 TEST` — Feature-owned tests

For each feature inspect `tests/services/<domain>/<feature_slug>/` and any
documented compatible test owner. Assess applicable happy path, invalid input,
boundary, authorization, computational, required/optional dependency, lifecycle,
cleanup, failure, cancellation, idempotency, replay, stale identity, removal,
and acceptance-ID traceability. Run only bounded explicit paths with `--no-cov`
during focused audit validation and record exact results.

### `FIP-11 INTEG` — Independent integration evidence

Locate independently owned evidence for contract-provider compatibility,
composition and registration, affected consumers, Interfaces, UI, persistence,
workflows, physical removal, and qualified providers as applicable. Evidence
belongs with its real owner; do not require a legacy
`tests/<domain>/integration/` directory. Offline mocks do not establish real
provider or end-to-end qualification.

### `FIP-12 COV` — Coverage

Verify a current source-bound report covers the audited domain and revision and
meets the configured floor (minimum 80%), including line and branch measurement
where required. Confirm feature modules are not omitted and exclusions are justified.
A repository aggregate must not conceal an unmeasured feature. Coverage is a
floor, not semantic proof. If evidence is unavailable, report `INCONCLUSIVE`; if
the actual gate failed, report `FAIL`.

### `FIP-13 HYG` — Code and repository hygiene

Verify explicit typing, Google-style docstrings with only applicable sections,
standard-library -> third-party -> local import order, Ruff formatting/lint, and
the absence of bare or silently swallowed exceptions, application/library
prints, literal credentials, sensitive payloads, import-time effects, and
service logging configuration. Public operations must match the public
Protocol; internal helpers and internal helper classes begin with `_`. Verify
every documented validation command names a real script at the audited
revision.

### `FIP-14 PERSIST` — Persistence and migration integrity

For each stateful feature, verify schema, parameterized SQL, and transactions are
owned by `app/services/persistence/<domain>.py`. Feature modules must not execute
ad-hoc SQL or receive unrestricted raw connections. Verify authoritative
migration manifests, immutable applied checksums, ledger verification, write
locks, transactional execution, retention/purge policy, and isolated temporary
test databases. Persistence must not absorb feature policy or authorization. A
stateless feature may be `N/A` only when `SPEC`, contract, README, and
implementation agree.

### `FIP-15 SCHEMA` — Declared-to-implemented state reconciliation

Compare README and `SPEC` state declarations, contracts, persistence schema,
migration manifests, safe applied-ledger evidence, and acceptance manifests.
Every durable namespace, schema version, table, and record type needs one
semantic owner. Record every divergence rather than normalizing it during the audit.

### `FIP-16 REACH` — Durable record reachability

Trace every domain-owned table or durable record from schema/migration through a
focused persistence operation and production feature operation to an authorized
consumer or documented retained-evidence purpose. Fail orphan tables, dead CRUD
builders, records reachable only from tests, write-only state without retention
purpose, direct cross-domain writes, or business state accidentally owned by
Interfaces or UI.

### `FIP-17 CONTRACT` — Producer-consumer compatibility

Verify public contracts are documented, domain-owned, versioned, implemented by
the registered provider, consumed through declared capabilities, compatible
with generated schemas, and exercised by producer-consumer tests. Absence,
incompatibility, and major-version mismatch must produce explicit unavailable or
blocked outcomes without fallback.

### `FIP-18 LIFE` — Lifecycle, dependency loss, and removability

Verify effects are lifecycle-owned, background work uses `FeatureContext.spawn`,
partial startup unwinds all resources, and teardown is idempotent. Required
dependency loss must block only dependent behavior; optional loss must disable
only affected operations. Provider replacement must not retain stale generation
state. Physical removal must preserve unrelated startup, capabilities, retained
user data, and external evidence without selecting a substitute provider.

### `FIP-19 LOG` — Structured logging and redaction

Where operational logging is warranted, verify
`logger = get_logger(__name__)` is used at public boundaries, state transitions,
external interactions, side effects, decisions, retries, and failures. Reject
global logging configuration and exposure of secrets, personal data, full
sensitive payloads, workspace paths, fencing/session tokens, account or
sensitive domain data, and unbounded raw exceptions. Pure helpers need not log.

### `FIP-20 SAFE` — Fail-closed authority and safety

Verify absent, stale, non-finite, incompatible, or uncertain inputs fail closed.
Preserve workspace, account, dataset, provider, environment, revision,
authorization, resource-admission, receiver, and execution boundaries.
Confirm no feature grants itself unauthorized authority, triggers unauthenticated
remote or destructive action, silently relaxes constraints, or substitutes
identity, provider, data, result, or policy.

### `FIP-21 COMP` — Computational and numerical integrity

Verify explicit unit conversions, defined unavailable/error results, checked
boundary arithmetic, deterministic seeded stochastic paths, reproducibility,
finite admitted search/simulation, exact identity and lineage, and truthful
distinctions between aggregation and recomputation. Reject fabricated or invented
results or undocumented formula substitutions.

### `FIP-22 PERF` — Performance and resource discipline

Verify work, memory, cardinality, concurrency, queues, retries, waits, and
outputs are bounded. Every performance or latency claim needs a measured,
revision-bound workload and environment; targets are not measurements. Unit
tests should isolate real network/database I/O and sleeps when they exceed
roughly 100 ms. Missing benchmark or soak evidence cannot pass a declared
budget.

### `FIP-23 DOCS` — Documentation reconciliation

Reconcile `AGENTS.md`, `docs/PROJECT.md`, `docs/ARCHITECTURE.md`, the owning
README, contracts, module `SPEC`, strict configuration, persistence, tests,
examples, decisions, source fingerprints, and acceptance evidence. Reject stale
counts, resolved open decisions, contradictory statuses, nonexistent commands,
and unsupported provider, remote, or system-completion claims. A changelog is
mandatory only when current repository authority makes it applicable.

### `FIP-24 IFACE` — Interfaces reachability

For intended external operations, verify an owned Interfaces feature performs
authentication/authorization before dispatch, translates wire DTOs to public
contracts, invokes declared capabilities, and preserves owner results.
Interfaces must not implement domain formulas, workflows, raw SQL, or business
state. Check bounded transport, version compatibility, idempotency, pagination,
and truthful denied/unavailable/conflict/stale/partial outcomes. `N/A` requires
explicit owner and acceptance-manifest justification.

### `FIP-25 UI` — UI reachability and truthfulness

For intended interactive operations, trace UI -> Interfaces -> public contract ->
provider. Verify the UI does not import or duplicate domain implementation and
truthfully represents loading, unavailable, denied, stale, partial, invalid, and
success states with correct units, provenance, and authority labels. Inspect
applicable browser, accessibility, cleanup, and interaction evidence. Component
presence or a README claim alone does not pass. `N/A` requires explicit
feature-specific justification.

### `FIP-26 EVID` — Source-bound acceptance evidence

Inspect every `docs/dev/evidence/features/<FEAT-ID>/acceptance.json`. Cross-check
feature and requirement identities, source/README hashes, tested revision,
paths/symbols, capability/config/persistence mappings, fixtures, environment,
commands and exit codes, coverage, usage, lifecycle/removal, qualification,
workflow disposition, and independent Contract, Provider, Composition,
Interfaces, UI, and End-to-end stages. The manifest is a claim container, not
proof by itself. Reject fabricated/self-referential identities, credentials,
private raw data, stale evidence, unjustified `NOT_APPLICABLE`, or optional
operations represented as qualified without evidence.

For each implementation task affecting the audited domain, also inspect its
task documentation. Verify that the Implementation Plan and Walkthrough are
present, follow-up iterations append to those files, and source-bound receipts/
fingerprints match the claimed candidate. Confirm the
history was committed with the implementation. Raw `*.log` streams, native session
handles, credentials, private payloads, and absolute workspace paths must not
be tracked; their bounded receipts may retain hash references.

## 5. Required Report

### 5.1 Executive summary

State:

- Domain and audited revision.
- Overall conclusion.
- Counts of `PASS`, `PARTIAL`, `FAIL`, `INCONCLUSIVE`, and `N/A`.
- Highest-risk deviations.
- Whether the domain may truthfully retain its documented completion state.
- Whether any result is limited by unavailable CI, browser, provider,
  performance, remote, or release evidence.

### 5.2 Control results

| # | Control | Verdict | Short evidence | Deviation | Remediation |
| ---: | --- | --- | --- | --- | --- |
| 1 | `FIP-01 REG` |  |  |  |  |
| 2 | `FIP-02 REQ` |  |  |  |  |
| 3 | `FIP-03 INIT` |  |  |  |  |
| 4 | `FIP-04 MOD` |  |  |  |  |
| 5 | `FIP-05 SPEC` |  |  |  |  |
| 6 | `FIP-06 IMPORT` |  |  |  |  |
| 7 | `FIP-07 CONTRACT-PURITY` |  |  |  |  |
| 8 | `FIP-08 USE` |  |  |  |  |
| 9 | `FIP-09 WF` |  |  |  |  |
| 10 | `FIP-10 TEST` |  |  |  |  |
| 11 | `FIP-11 INTEG` |  |  |  |  |
| 12 | `FIP-12 COV` |  |  |  |  |
| 13 | `FIP-13 HYG` |  |  |  |  |
| 14 | `FIP-14 PERSIST` |  |  |  |  |
| 15 | `FIP-15 SCHEMA` |  |  |  |  |
| 16 | `FIP-16 REACH` |  |  |  |  |
| 17 | `FIP-17 CONTRACT` |  |  |  |  |
| 18 | `FIP-18 LIFE` |  |  |  |  |
| 19 | `FIP-19 LOG` |  |  |  |  |
| 20 | `FIP-20 SAFE` |  |  |  |  |
| 21 | `FIP-21 COMP` |  |  |  |  |
| 22 | `FIP-22 PERF` |  |  |  |  |
| 23 | `FIP-23 DOCS` |  |  |  |  |
| 24 | `FIP-24 IFACE` |  |  |  |  |
| 25 | `FIP-25 UI` |  |  |  |  |
| 26 | `FIP-26 EVID` |  |  |  |  |

Follow the table with one detailed subsection per control using the mandatory
fields in Section 3.

### 5.3 Feature reconciliation matrix

| Feature ID | Module and `SPEC` | Capability | Registry | Tests | Example | Evidence | Verdict |
| --- | --- | --- | --- | --- | --- | --- | --- |

### 5.4 Requirement traceability matrix

| Requirement ID | Contract operation | Implementation symbol | Acceptance oracle | Executable evidence | Verdict |
| --- | --- | --- | --- | --- | --- |

Include every FR, local NFR, applicable shared NFR, workflow acceptance ID, and
any unmapped or unsupported claim.

### 5.5 Persistence reachability matrix

| Durable record | Schema/migration | Persistence operation | Production operation | Consumer/retention purpose | Verdict |
| --- | --- | --- | --- | --- | --- |

Use `N/A` only when the audited domain is demonstrably stateless.

### 5.6 Command ledger

| Command | Purpose | Exit code | Result | Evidence limitation |
| --- | --- | ---: | --- | --- |

### 5.7 Remediation plan

Order remediation by:

1. Safety, authority, secrets, or destructive-data violations.
2. Data integrity, persistence, and computational correctness.
3. Contract, lifecycle, ownership, and architecture violations.
4. Missing executable acceptance and integration evidence.
5. Tests, coverage, performance, and resource controls.
6. Documentation-only drift.

Identify which findings require a formal implementation task and which are bounded
documentation corrections. Do not implement either during the audit.

## 6. Audit Completion Gate

Before issuing the report, verify:

- All 26 controls have one verdict.
- The `FIP-*` control-ID set exactly equals the pipeline control-ID set.
- Every `PASS` cites sufficient exact evidence.
- Every `PARTIAL` and `FAIL` records deviation and remediation.
- Every `INCONCLUSIVE` records the missing evidence and resolution owner.
- Every `N/A` has a feature-specific rationale.
- No declaration is used as its own proof.
- No unsafe, external, destructive, or active-database action occurred.
- The report distinguishes local evidence from CI, remote, browser,
  provider, performance, soak, and release evidence.

Only then is the audit complete. Completion of the audit does not itself change
the domain's implementation or acceptance state.
