# HaruQuantAI architecture

> **Authority:** This document owns spatial and runtime constraints.
> [PROJECT.md](PROJECT.md) owns product scope and target outcomes;
> [AGENTS.md](../AGENTS.md) owns development workflow and verification commands;
> the owning package README owns local contracts and implementation status.
> Donor observations are indexed in the
> [clean-room ledger](dev/evidence/reimplementation.json). Donor informs;
> specification owns.

## 1. The Five Laws of Spatial Composability

These are **HaruQuantAI decisions**, binding on backend and frontend. They are
not claims about SQX's internal correctness or packaging.

### SC-01 — Locality of behavior

One quantitative concept has one cohesive spatial home. A concrete backend
plugin keeps its calculation, configuration, parameter schema, defaults,
bounds, outputs, compatibility, lowering hooks, and presentation metadata in
one cohesive Python file. Its manifest, README, tests, and optional UI
counterpart live in that plugin's pair of folders. A workspace owns its
workflow and contracts within one backend/frontend pair of directories.
Universal metamodels and UI primitives may be shared; concept-specific
contracts and formulas may not be moved into a global catalog or components
folder merely for convenience.

**Review test:** Trace one concept from configuration to output and removal.
Its behavior must be understandable and removable without searching unrelated
workspaces for fragments of its implementation.

### SC-02 — Orthogonality

Adding, disabling, upgrading, or removing one pair cannot require edits to
another pair, either host, or a central plugin list. A failed or missing
contribution blocks only its declared dependents. Retained artifacts remain
inspectable with an explicit unavailable placeholder rather than disappearing
or acquiring a different meaning.

**Review test:** Remove a plugin from an isolated installation. Unrelated
catalog entries, routes, tests, results, and UI surfaces must still work;
documents that reference it must report the missing dependency.

### SC-03 — Explicit typed capability slots

Pairs collaborate through declared, versioned capabilities and immutable
documents. Requirements, provided outputs, authorization, compatibility, and
failure meanings are explicit. Runtime behavior cannot reach through a
registry, global variable, private sibling import, UI fixture, ambient file
path, or import-time side effect to obtain another pair's implementation.
Missing or ambiguous providers fail closed at the affected operation.

**Review test:** From a consumer's public declaration alone, identify every
external capability it requires and the result it receives when that
capability is absent.

### SC-04 — Hierarchical and algebraic composition

Complex work is composed from typed smaller units: plugins contribute
primitives; strategies and analytical pipelines bind them as immutable,
versioned trees or graphs; workspaces arrange operations over those
documents; projects compose finite tasks. Editors, generators, simulators,
result viewers, and exporters refer to the same semantic document and pinned
plugin versions. A UI label or serialized node cannot redefine execution
meaning.

**Review test:** The same reviewed document and bindings must be usable by
the editor, execution plan, and exporter, or a typed incompatibility must
identify why an operation cannot proceed.

### SC-05 — Schema-driven self-description

A pair describes its identity, compatibility, inputs/outputs, parameters,
constraints, optimization bounds, capability slots, and presentation needs in
machine-readable metadata owned by that pair. The host builds a catalog by
discovery; a UI consumes the catalog within a bounded renderer vocabulary.
Neither host keeps a hand-maintained list of quantitative concepts. Metadata
may select a known interaction; it cannot execute arbitrary UI or backend
behavior. A genuinely new interaction model requires a reviewed UI extension.

**Review test:** Add a compatible concept and confirm its catalog, settings,
validation, and generic presentation appear without edits to host source or
another pair.

The laws operate together. Self-description without locality creates a
central schema dump; locality without typed slots creates hidden imports;
composition without pinned identities changes old results when a plugin
changes.

## 2. Spatial map and ownership

The repository is a set of backend/frontend counterparts around one host pair:

~~~text
Backend                                  Frontend
app/host/            <- host pair ->     app/ui/src/app/
  lifecycle, sessions, catalog,            transport, session, router,
  envelope, commands, events,              shell store and views
  telemetry, shell settings                (no quantitative domain names)
  (no quantitative domain names)

app/workspace/<Domain>/  <- pair ->       app/ui/src/workspace/<Domain>/
  workflow, handlers, schema               view, client, local fixtures

app/plugins/<X>/         <- pair ->       app/ui/src/plugins/<X>/
  one cohesive concept file,               concept presentation or interaction
  manifest, local tests                    owned with that plugin

app/kernel/                              app/ui/src/components/
  standard-library-only, neutral           universal presentation primitives
~~~

The exact directory spelling of a new pair is established by its approved
owner README and plan. The pairing is an ownership rule, not a requirement
that every backend concept have a custom UI. A headless plugin may use a
generic schema renderer. A UI-only view must state which backend truth, if
any, it presents. Shared files are allowed only for universal mechanisms;
they cannot become a second home for a concrete concept.

The word **workspace** means an interactive workflow owner in HaruQuantAI.
A **plugin** contributes a narrower capability to one or more workspaces.
SQX calls some large application surfaces plugins and also has function-like
snippets; the installed extension manual makes that scale distinction
([SQX144-EV-000023](dev/evidence/reimplementation.json)). Our workspace
classification is a normative packaging decision, not a claim that SQX uses
this folder model.

| Owner | May own | Must not own |
| --- | --- | --- |
| Backend host | Shared envelope, auth/session boundary, command mediation, event hub, catalog and route composition, lifecycle, telemetry, shell settings | A named quantitative workspace, plugin algorithm, strategy meaning, or another owner's durable record |
| UI host | Navigation shell, universal transport and errors, session state, catalog cache, local view state, generic bounded renderers | Backend formulas, plugin-specific schemas, durable research truth, or special-case imports for each new plugin |
| Workspace pair | One user workflow, its public commands and local state, its UI client and presentation | The private code or records of plugins and sibling workspaces |
| Plugin pair | One quantitative or presentation contribution, its typed schema, behavior and tests | A sibling plugin's implementation, host lifecycle, or undeclared external authority |
| Kernel and UI primitives | Business-neutral metamodel/runtime primitives and presentation primitives respectively | Product registries, concept-specific policy, persistence, or provider adapters |

## 3. Dependency and transport direction

The host composes pairs from validated declarations at startup. A pair may
import universal backend metamodels or frontend primitives and its own files.
It cannot import a sibling's private implementation. A plugin cannot import
workspace implementation. A workspace calls another owner's public
capability through an injected typed slot or the host transport; no package
may locate another by scanning paths during an operation. Python package
initializers are empty or docstring-only, and imports perform no I/O,
registration, thread creation, or global mutation.

A backend/frontend pair shares a **wire contract**, never an in-process
module. The backend owner defines domain requests, responses, events, and
stable failures. The host pair defines only the envelope, error shape,
request ID, authentication, and transport conventions. The UI client adapts
the owner's versioned wire schema; UI presentation types do not become a
parallel backend schema. A breaking change needs a new version or explicit
migration and producer/consumer compatibility evidence.

The current host scans the configured workspace/plugin roots for
manifest.json at startup. A valid manifest declares identity, kind,
route base, version, capabilities, and optionally a route module. The
catalog returned by a running host is the same startup snapshot used to
mount routes and marks a manifest-only entry as unmounted. New files require
restart; malformed or conflicting declarations produce issues. This is
**implemented host behavior**, documented in
[app/host/README.md](../app/host/README.md). It is not yet a complete
runtime capability resolver or hot-swap system.

The current React shell still uses static workspace route imports and
several direct prototype imports. It does not yet achieve SC-02/SC-05 for
arbitrary frontend plugin additions. Migrating those routes and contribution
surfaces requires a separately approved plan, a bounded UI extension model,
and proof that existing navigation and accessibility remain correct.
Prototype shortcuts are not architecture precedents.

## 4. Composition model

A workspace declares the operations it offers and the typed plugin slots it
accepts. A plugin declares what it provides and requires. The composition
root validates unique identity, version compatibility, declared
dependencies, route ownership, authority, and resource limits before
publishing a usable capability. A missing optional plugin disables its
operation; a missing required plugin blocks that workspace operation with an
attributed reason. No provider substitution is inferred from a similar
name or output shape.

A strategy or analytical document contains typed nodes and ports with stable
IDs, parameter values, plugin identities and versions, and explicit units,
data alignment, clock, missing-data, warm-up, and numerical policies.
Validation precedes execution. An unknown node can remain in a read-only
document but cannot be executed or silently converted. Builder may generate
such documents; AlgoWizard may edit them; simulation evaluates qualified
plans; Results reads immutable outputs; exporters lower supported semantics.
Each operation owns its effect, while the shared document preserves meaning.

Project automation is a separate composition layer. A project references
tasks, databanks, artifacts, conditions, and finite budgets; tasks consume
and produce typed references. A loop requires an explicit termination or
resource bound. Installed SQX project archives show a task reference and
multiple databank declarations
([SQX144-EV-000021](dev/evidence/reimplementation.json),
[SQX144-EV-000022](dev/evidence/reimplementation.json)), and SQX official
documentation describes source/target databanks and conditional task flow
([Custom Projects main concepts](https://strategyquant.com/doc/strategyquant/custom-projects-main-concepts/)).
Those are donor observations. HaruQuantAI's document format, transaction
semantics, and scheduler are not derived by copying SQX's archive.

The installed SQX modules also show scoped contributions to a cross-check,
a Results tab, and a Data Manager source
([SQX144-EV-000018](dev/evidence/reimplementation.json),
[SQX144-EV-000019](dev/evidence/reimplementation.json),
[SQX144-EV-000020](dev/evidence/reimplementation.json)).
HaruQuantAI may use those extension *families* while applying its own typed
capability and removal rules. For example, adding a data-source plugin must
not edit Data Manager source or grant the plugin filesystem/network access
outside a declared host capability.

## 5. Schema and UI reflection boundary

The pair's schema is the single source for parameter names, types, defaults,
units, constraints, optimization bounds, compatibility and presentation hints.
Validation is backend authoritative. Generated wire schemas or clients may
project that meaning; manually copied UI validators cannot redefine it.
Forms, parameter tables, port diagrams, and common result charts are rendered
from a bounded vocabulary. Unsupported metadata yields a visible
incompatibility or an explicit extension requirement.

A host catalog entry means **discovered**, not necessarily installed,
enabled, authorized, mounted, compatible, or operational. These states remain
distinct. The catalog reports the current startup mount truth. Workspace
availability additionally depends on its declared capability and authority
checks. UI caches can be invalidated by events but must re-read owner truth;
an event is a notification, not a complete durable record.

A new plugin can bring its own UI counterpart when interaction exceeds the
generic vocabulary. That counterpart may use host transport and universal
components, but must stay inside the plugin's folder and public contracts.
The current UI's hard-coded catalogs and fixtures are transitional and must
not be used as evidence for runtime plugin discovery.

## 6. State, artifacts, and determinism

Every durable state or artifact family has one semantic owner. The host may
provide bounded storage, file exchange, sessions, and settings mechanics
without acquiring the meaning of a strategy, project, dataset, result, or
portfolio. Plugins never execute ad-hoc SQL against another owner or take a
raw shared connection. Persistence schema, migration, transaction and
retention need a ratified host capability; no such general quantitative
persistence service is implied by the shell settings store. Host-owned global
settings use scoped `(scope, key)` records in the `host_settings` table in
`data/database/haruquantai.db`, with transactional field updates, conditional
writes, credential-field redaction, and post-commit change events. The host does
not read `data/user/settings.json`. Feature-owned app presets use JSON in
`data/presets/` when their owning features are implemented; this directory is
not an alternate settings store. Other database tables remain with their
declared owners.

A project is a saved flow/configuration; a workspace is a user interaction
surface; a databank is a named collection or view of references. Strategy,
run, result and portfolio identities remain separate. Changing a view,
filter, or databank membership must not rewrite a result. Published bytes and
metadata need explicit hashes, versions, custody, and recovery rules.
Failed or partial outputs remain distinguishable from accepted complete
outputs. Removed-plugin documents retain their original references and
unavailable placeholders.

Decision-grade runs pin strategy, data, plugin/version, parameters, costs,
execution method, numerical policy, sample, seed, and relevant resource
configuration. Ordering, time zones, units, market sessions, missingness,
warm-up, ties, overflow, and precision require explicit owner policy.
Comparisons use the same declared basis or explain incompatibility.
Historical results never imply profitability or live readiness. Detailed
algorithms and tolerances belong to the concrete owning plugin/workspace and
must be independently verified, including against donor outputs if parity is
ever claimed.

## 7. Security, lifecycle, and external effects

The host mediates authentication, bounded commands, sandboxed file exchange,
and external integrations. A plugin receives only the capabilities it
declares and is authorized to use. Secrets stay out of schemas, events,
logs, research artifacts, and browser storage. Network and broker adapters
need bounded timeouts, retries, rate policy, redaction, and lifecycle
ownership. Unknown external write outcomes are reconciled before retrying.

Mounting is staged: validate metadata and compatibility, construct a
candidate, then publish only a complete accepted contribution. Disable,
failure, and removal withdraw capability, dispose owned resources, and
preserve historical records under retention policy. Replacement must either
preserve compatible identities or report a migration requirement. The
current host provides startup mount and process lifecycle, not these full
plugin replacement guarantees; future implementations must prove them.
Live trading remains disabled by default and needs distinct risk and
execution authority beyond ordinary plugin admission.

## 8. Architecture acceptance

A new pair is accepted only when its owning README registers purpose,
contract, capability slots, versions, requirements, failure behavior, status,
and evidence. Concrete plugins also follow the one-file rule and include
schema, bounds, missing-data and numerical policy, focused tests,
orthogonality/removal tests, and a deterministic offline usage example.
Owner-specific requirements may be added but may not weaken the Five Laws.

Verification must exercise:

- import direction and no import-time effects;
- manifest, schema, wire, producer/consumer, and compatibility behavior;
- addition, cold absence, disable/re-enable, removal, and retained-document
  readability;
- deterministic output, boundary values, missing data, error and recovery;
- honest UI states and no duplicated backend calculations;
- resource cleanup, bounded external effects, and authorization; and
- actual end-to-end results for any claimed donor compatibility.

Coverage, a passing linter, or a similar screen is not semantic proof. Use
the commands and owner gates in AGENTS.md. The absent workspace/plugin
pipeline and audit documents named there are a tracked documentation gap;
until approved and present, this document and AGENTS.md provide the
applicable structural and workflow rules. Do not infer a missing file's
contents or implement a pair without an approved plan.
