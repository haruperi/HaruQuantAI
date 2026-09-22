# Workspace and Plugin Implementation Audit

> **Purpose:** Independently assess a workspace (Track W) or a concrete
> non-workspace plugin (Track P) against its approved delivery scope.
> **Reciprocal standard:** [Workspace and Plugin Implementation Pipeline](workspace_plugin_implementation_pipeline.md).
> **Authority:** [AGENTS.md](../../AGENTS.md), [PROJECT.md](../PROJECT.md),
> [ARCHITECTURE.md](../ARCHITECTURE.md), and the applicable family README.

An audit reports what the inspected evidence proves. It does not implement fixes,
change product status, rewrite ledgers, ratify missing contracts or authorize Git
operations. Source and operational state remain read-only. If an audit report is
requested as a file, write only the declared report output; remediation requires
its own approved implementation plan. A completed audit is not a compliant unit.

This audit and the pipeline use exactly the same closed control catalogue. Track W
assesses WP-C01-C13 plus WP-W01-W08; Track P assesses WP-C01-C13 plus WP-P01-P10.
Mixed tasks produce separate per-unit findings. A workspace pass cannot establish
a child algorithm's correctness, and a plugin pass cannot establish UI integration.

## 1. Audit invocation and boundaries

Complete before collecting evidence. Placeholders below must be replaced with
actual approved paths/identities, or recorded as missing evidence.

```text
TRACK: W | P
UNIT_REF: <stable ID and exact version>
DECLARED_SCOPE: <commands/operations/consumers actually claimed>
DEFERRED_SCOPE: <explicit exclusions and unavailable operations>
PRODUCTION_FILE: <one owning plugin file>
FAMILY_README: <owning family policy/index>
REQUIREMENTS_AND_DECISIONS: <registered references or gaps>
PUBLIC_CONTRACTS: <shared types and allowed host contract symbols>
UI_AND_CONSUMERS: <actual callers, renderers and gateways, or justified N/A>
STATE_AND_EFFECT_OWNERS: <run-local/durable/resource owners or justified N/A>
OBSERVABLE_FLOWS: <event worksheet, emitter/correlation/sink and evidence>
PLAN_AND_APPROVAL: <task path, iteration and approval evidence>
TESTS_AND_USAGE: <exact existing test/example paths>
EVIDENCE_INPUTS: <receipts/manifests/schemas to reconcile>
AUDITED_REVISION: <full SHA and candidate source fingerprints>
AUDIT_DATE_UTC: <actual timestamp>
REPORT_OUTPUT: <authorized path or conversation-only>
```

Missing paths or contracts are findings, not permission to create them. Resolve
whether a requested screen is a workspace, informational shell or host tool before
applying the wrong track. For a family audit, enumerate its concrete units and
give each the appropriate track; do not hide a failed unit in an aggregate pass.

### Evidence and operational safety

1. Inspect working-tree state, authority, scope, contracts and existing receipts
   before choosing dynamic checks. Report conflicts with exact sources.
2. Reuse current source-bound results where sufficient. A prior result for different
   code or configuration does not prove the current candidate.
3. Run only explicit, bounded relevant tests/examples. Use temporary plugin trees,
   isolated stores and offline fixtures. Do not remove production plugins, mutate
   active databases, call credentialed providers or trigger external mutations.
4. Do not change source, tests, status, schemas or evidence to make a check pass.
   Record failure and remediation ownership. No commits, branches, pushes or
   history rewrites are authorized by audit work.
5. Record actual commands, exit codes, timestamps, artifacts and limitations.
   Unit fixtures do not establish browser, provider, performance or release results.
6. Keep logical roots/repository-relative paths in retained evidence. Exclude
   secrets, raw sensitive payloads, personal data and machine-specific paths.
7. An unavailable test environment yields missing evidence, not a fabricated pass.
   A failed test may require diagnosis before attributing its cause to the unit.

## 2. Verdict model and completion rules

| Verdict | Meaning |
|---|---|
| PASS | Sufficient exact evidence proves the full applicable obligation at the audited source revision. |
| PARTIAL | Some required elements are proven, but the declared scope has explicit incomplete or contradictory elements. |
| FAIL | Evidence demonstrates a mandatory violation or absent required implementation. |
| INCONCLUSIVE | Available evidence cannot establish conformity; identify missing evidence and how to obtain it. |
| N/A | The responsibility demonstrably does not apply to this unit; give a specific rationale and supporting evidence. |

Give each applicable-set control exactly one verdict. N/A is not a substitute for
an unimplemented required feature. Deferred scope is not automatically a failure,
but the unit must truthfully declare and enforce that boundary. An unexecuted
test is not a pass. Some numerical/lowering/state controls can be N/A for kinds
that make no such claims; identity, ownership and delivery gates still apply.

For every control record: ID/title, scoped requirements, verdict, exact evidence,
deviation, remediation and owner, evidence limitation, and any N/A rationale.
PARTIAL or INCONCLUSIVE must never be collapsed into PASS. A full-compliance claim
requires all applicable obligations proved; report bounded delivery separately
from full product capability and independently verified donor parity.

## 3. Track W: workspace audit sequence

1. **Establish scope:** reconcile invocation, approved plan, family index and
   workspace descriptor. Classify commands as local, functional, deferred or
   unavailable. Identify source conflicts and undeclared promises (C01-C02, W01).
2. **Inspect ownership and construction:** locate one declaration file; inspect
   imports, initializers and pure factory; enumerate view/renderer ownership.
   Distinguish descriptive commands from executable operations (C03-C05, W03).
3. **Trace supported commands:** follow each action from actual UI through the
   client/gateway to admitted exact operations and real response fields. Compare
   authorization and availability with declared dependencies (C06, C09, W02, W04).
4. **Check presentation and transport:** inspect schema projection, unavailable
   states, loading, errors, results, provenance, persistence boundaries, cancellation
   and resource limits (C07, W05-W06). No fabricated progress or metrics. Verify
   command/request flow events and inspectable correlated outcomes under C13.
5. **Exercise isolation safely:** use temporary catalog roots for add/disable/remove
   and shared-child cases. Include the unrelated-kind/deferred-command regression
   (C08, W04, W07). No active-tree mutation.
6. **Validate real reachability:** inspect/run focused tests, supported offline
   usage and appropriate real UI/gateway/browser evidence (C10, W08). Distinguish
   metadata discovery, graph evaluation and complete product workflows.
7. **Reconcile and report:** evaluate all C+W controls; verify source-bound evidence,
   candidate qualification, status wording and walkthrough (C11-C12). Identify
   residual unavailable scope without implementing fixes.

## 4. Track P: concrete plugin audit sequence

1. **Establish concept and scope:** reconcile family, stable version, approved
   requirements, operations and consumers (C01-C02, C09, P01).
2. **Inspect one-file ownership:** check schema/config/behavior/metadata/lowering
   locality, initializer/factory purity and allowed imports (C03, P01-P02).
3. **Reconcile contracts:** inspect immutable inputs/outputs, schema constraints,
   operation bindings, algebra placement, canonical wire and version behavior
   (C04-C06, P02-P03).
4. **Verify behavior independently:** inspect or reproduce applicable goldens,
   numerical/error policies, determinism, mutable-state isolation and resource
   boundaries (C07, P04-P07). Do not generate the oracle from the implementation.
   Reconcile host-boundary observation and effectful retry/failure events under C13.
5. **Trace each consumer:** verify actual optimization, lowering/export and generic
   UI/schema consumers where claimed (C09, P08-P09). Record missing integrations.
6. **Prove independence and usability:** run scoped temporary removal/unsupported
   dependency checks and deterministic offline usage (C08, C10, P10).
7. **Reconcile and report:** evaluate all C+P controls; verify evidence freshness,
   qualification and bounded completion claims (C11-C12). Do not require building
   a new workspace solely to finish a plugin audit.

## 5. Common control procedures

### WP-C01 — Authority and approved scope

**Inspect:** authorities, owning README, plan iteration, approval, allowed writes,
requirements, non-goals and actual diff. Record authority conflicts before drawing
completion conclusions.

**Pass evidence:** the implemented candidate matches the explicitly approved scope;
material deviations have recorded approval. Current paths/APIs are distinguished
from target requirements. **Failure:** unapproved new contracts/dependencies,
silent scope expansion, unrelated overwrites, or invented authority. Applies to all
units; an audit-only task evaluates existing authorization without creating it.

### WP-C02 — Identity, version and ownership

**Inspect:** PluginRef/PluginSpec, owning file/family, catalog entry, README index,
test/example identity and migration policy. Distinguish implementation, metamodel,
capability, graph/wire and artifact versions.

**Pass evidence:** one canonical globally unambiguous identity has one owner;
version changes and unsupported states are explicit and claims match that unit.
**Failure:** duplicate/shadow identities, conflicting owners, compatible versions
masking breaking changes, or unsupported status claims. Applies to all units.

### WP-C03 — Locality and import purity

**Inspect:** all concept-specific definitions, imports/accesses and initializers;
include aliases, transitive imports, annotations, decorators, bases and defaults.
Exercise import and factory separately where safe. Check that importing approved
host contracts does not require optional provider packages or start providers.

**Pass evidence:** one cohesive declaration/behavior owner, no duplicated schemas,
pure initialization and permitted symbols only. **Failure:** sibling/private host
access, hidden registration/I/O/environment reads/tasks/global mutation, split
plugin contracts, or business logic in shared vocabulary. Applies to all units.

### WP-C04 — Discovery and admission

**Inspect:** configured family roots, pre-import exclusions, ordering/bounds,
snapshot validation/publication, duplicate-ID behavior, selection and admission.
Use isolated invalid/duplicate candidates when dynamic proof is needed.

**Pass evidence:** deterministic bounded discovery without runtime concrete lists;
invalid refresh preserves a valid snapshot, initial failure reports unavailable,
and installation is distinct from enablement/authorization. **Failure:** import-all
scans, silent collision/fallback or effect activation on install. Record approved
transitional topology exceptions as deviations, not no-central-edit proof.

### WP-C05 — Immutable contracts and wire

**Inspect:** actual public signatures/descriptors and generated wire projections;
try nested mutable aliases, invalid values and round trips. Check exact versions,
explicit missing encodings and unsupported-document retention.

**Pass evidence:** immutable typed values and canonical serialization conform
across actual consumers; generated clients match the owner. **Failure:** copied
mutable dictionaries presented as immutable, NaN JSON, silently dropped unknown
fields, invented fields or incompatible clients. Apply supported document controls
to each relevant interface; no nonexistent interface is required merely for audit.

### WP-C06 — Capabilities, effects and security

**Inspect:** declared required/optional bindings, operation permissions/effects,
call sites, provider boundaries, defaults, redaction and secret-bearing artifacts.
Trace who authorizes each action.

**Pass evidence:** only explicitly permitted typed collaboration; optional absence
affects the relevant operation; no ambient authority, private provider bypass or
unauthorized external mutation. **Failure:** live registry access, hidden clients,
embedded credentials, self-granted authority or silent substitution. A pure unit
still demonstrates purity; absence of effects does not waive import controls.

### WP-C07 — State, persistence and resources

**Inspect:** run-local versus durable state, host storage/resource contracts,
record schemas/reachability/retention and actual producer/consumer paths. For
resource users, inspect bounds, retries, cleanup, failed/cancelled acquisition,
drain order and valid bindings during cleanup.

**Pass evidence:** one authorized durable owner and bounded owned resources, with
isolated test stores and supported failure/cleanup results. **Failure:** ad-hoc
plugin SQL, orphan durable records, UI-owned durable truth, leaked consumers,
unbounded retries or active-data mutation. A stateless unit may justify N/A only
for absent state/resource sub-obligations; never force a fake lifecycle.

### WP-C08 — Orthogonality and removal

**Inspect:** safe temporary add/change/disable/physical-removal evidence, peers,
referencing documents and admitted dependency identities.

**Pass evidence:** unrelated results and entry/dependency fingerprints remain
stable despite whole-catalog membership changes; unknown references survive
losslessly as unavailable; admitted runs retain exact dependencies or fail.
**Failure:** central runtime edits, peer breakage, silent rebinding, data loss,
or a test that only checks coexistence while claiming physical removal. Never
delete a production plugin or active record to perform this audit.

### WP-C09 — Requirements and consumer traceability

**Inspect:** every scoped requirement, command/operation, workflow contribution,
consumer and supported target. Trace owner symbols, actual contracts, entry
points, output/failure semantics and independent acceptance oracles.

**Pass evidence:** complete scope-to-implementation-to-evidence mappings, with
missing registered IDs explicitly identified rather than fabricated. **Failure:**
unreachable operations, reading order presented as a workflow, unit-only evidence
claimed as end-to-end, or a caller recomputing owner semantics. N/A requires proof
that a particular consumer is not part of the declared scope.

### WP-C10 — Tests, usage and coverage

**Inspect:** focused test content, actual executed results, deterministic bounded
offline example, integration ownership and revision-bound branch coverage.
Check happy, invalid, boundary, failure and applicable lifecycle/resource cases.

**Pass evidence:** meaningful oracles, actual consumer integration and configured
coverage floor without omitted changed source. **Failure:** tests mirroring code,
untested changed behavior concealed by aggregate coverage, example reimplementing
logic, or unsafe/live fixtures. Missing runnable/coverage evidence is INCONCLUSIVE
unless other evidence proves violation; a known failed gate is not a pass.

### WP-C11 — Evidence and documentation

**Inspect:** fingerprints, tested revision/candidate, timestamps, commands, exits,
fixtures, limitations, plan/walkthrough and README/status reconciliation. For donor
claims inspect atomicity, schema, provenance, mappings and historical links.

**Pass evidence:** source-bound, reproducible and truthful claims; schemas live
with their implementation; clean-room records and retained history conform.
**Failure:** stale or self-referential proof, absolute machine paths, secrets,
unsupported parity, invented IDs or rewritten material findings. Do not mutate a
ledger during audit. Missing donor use makes donor-only subchecks N/A, not all
acceptance evidence obligations.

### WP-C12 — Qualification and delivery gates

**Inspect:** reciprocal audit, actual architecture/CI and applicable UI checks,
walkthrough, deviations, working-tree scope and approval boundaries. Compare
commands with existing scripts, not an outdated checklist.

**Pass evidence:** all applicable candidate gates have exact results, unresolved
limits are retained and commit authorization remains with the owner. **Failure:**
missing required qualification claimed as complete, hidden failures, unaudited
scope or unauthorized Git mutations. An implementation audit may record a pending
walkthrough/gate as incomplete; it cannot authorize that gate itself.

### WP-C13 — Operational logging and flow tracing

**Inspect:** the plan's flow-event worksheet, import ordering, emitters, public
telemetry contracts, subscriptions, actual observers/sinks and their lifecycle.
Trace operation boundaries, state transitions, meaningful decisions, retries,
external interactions, side effects and failures appropriate to the scoped unit.
Pure plugin internals may be silent; identify their invoking host as the boundary
observation owner instead of requiring a logger in every calculation.

Compare actual fields and propagation with declared request/run/job/operation
correlation. Validate externally supplied IDs; do not use sensitive identities or
session tokens. Check stable names, appropriate levels, safe error codes, elapsed
duration and causally consistent outcomes. Distinguish request timeout from the
eventual execution outcome; an event stream need not promise crash-proof terminal
delivery or a total ordering across concurrent flows.

Use isolated capturing observers and synthetic sentinel secrets to verify applicable
successful, rejected, failed, retried and cancelled paths; inspect both normal
events and observer-failure diagnostics for leaks. Verify field/volume bounds,
absence of hot-loop noise, correct correlation and supported subscription cleanup.
Inject an observer exception and check the declared result isolation and diagnostic
reporting. A truncated exception is not necessarily redacted. Do not send real
secrets or production payloads through a test observer.

Check delivery guarantees independently: capture proves emission, not persistence,
retention, timestamping, cross-process tracing or nonblocking subscriber behavior.
If those are claimed, require actual sink/retention/process/latency evidence.
Inspect drop/overflow reporting where supported; missing support is a named gap,
not an invented pass. Ordinary diagnostic loss and mandatory durable audit records
must not be conflated. Do not recursively log failures into a failing observer.

**Pass evidence:** each required scoped flow is inspectable through its declared
supported path with safe correlation and verified boundaries, levels, redaction,
noise limits, failure policy and lifecycle. The pipeline's import discipline and
host-owned configuration are followed. **Failure:** no event owner, missing required
flow evidence, module-owned handlers/global logging, fake async bridges in synchronous
plugins, silent observer failures, fabricated sink guarantees, sensitive values or
unbounded event traffic. Missing accessible evidence is INCONCLUSIVE; demonstrated
absence of required instrumentation is FAIL or PARTIAL according to scoped coverage.

For a declaration-only workspace or pure plugin, internal logging subchecks may
be N/A with evidence that no operational side effects occur there. The actual
host execution path and the limits of any claimed flow visibility must still be
assessed. Avoid claiming full operational observability from a pure-factory test.

## 6. Workspace control procedures

### WP-W01 — Command and workflow scope

**Inspect:** the command matrix against descriptor, visible controls and supported
workflows. Each row needs actual inputs, outputs, binding, availability and oracle.
Separate local edits, graph evaluation and complete product workflows.

**Pass evidence:** no visible or documented action promises an unbacked capability;
deferred scope is explicit. **Failure:** metadata treated as implementation,
unspecified data inputs, hidden non-goals or graph evaluation called a trading
backtest. Applies to every workspace, including a bounded declarative slice.

### WP-W02 — Operation and host binding

**Inspect:** a supported action through UI/client/host admission to exact plugin
references and operation IDs or actual generic host contracts. Compare request
and result fields with the active code.

**Pass evidence:** real compatible dispatch without child imports, quantitative
logic in views or an ad-hoc backend workspace switch. **Failure:** invented endpoint,
field, operation, central concrete dispatch or frontend authorization. For local
editing-only commands, verify the honest local boundary; do not require network I/O.

### WP-W03 — Workspace descriptor and views

**Inspect:** PluginContribution, WorkspaceSpec, commands, accepted kinds and view
references; discover the workspace and inspect pure construction. Trace the actual
renderer/installed extension for each claimed view.

**Pass evidence:** one immutable owning declaration and approved UI ownership;
opening/declaring it does not implicitly start services. **Failure:** duplicate
metadata, a route string asserted to implement a renderer, private host construction
or an unnecessary lifecycle. A declaration-only scope must not claim UI delivery.

### WP-W04 — Exact command availability

**Inspect:** availability/denial reasons and backend admission. In a temporary test
catalog add an unrelated optimizer or cross-check while a command remains deferred.
Also inspect missing, disabled and incompatible exact dependencies.

**Pass evidence:** deferred commands remain unavailable and supported operations
depend on actual admitted bindings; reasons identify the missing support.
**Failure:** any-entry-of-kind enables a command, a disabled control substitutes
for authorization, or errors silently select an alternative operation.

### WP-W05 — Schema-driven truthful UI

**Inspect:** parameter controls against backend schema and output rendering against
actual response values, units, missing/error states and provenance. Identify mock
data, formulas, local storage and schema copies.

**Pass evidence:** presentation reflects backend truth within approved renderers;
draft state is distinct from durable state. **Failure:** duplicated algorithms,
fabricated metrics/trades, unsupported timestamps, hidden stale results or frontend
policy copies. Schema projection is assessed only for claimed controls; novel
renderers need their own reviewed implementation and evidence.

### WP-W06 — Execution and transport states

**Inspect:** loading/error/completion/progress/cancellation flows, request budgets,
timeouts, component cleanup and late-result handling against the real transport.
Exercise applicable bounded timeout/failure cases.

**Pass evidence:** truthful indeterminate state when no progress exists; cooperative
cancellation is described/tested at supported boundaries, with eventual completion
for bounded test operations. **Failure:** timer-generated progress, browser abort
claimed as server termination, hard-preemption promises or nonexistent job feeds.
Local-only views justify N/A for absent transport responsibilities.

### WP-W07 — Shared children and independence

**Inspect:** two workspaces selecting a real supported child, followed by isolated
disable/removal of one workspace. Check peer catalog access, graph execution,
shared services, user documents and unavailable references.

**Pass evidence:** peer behavior and dependencies remain valid; discovery and graph
execution are independently demonstrated. **Failure:** uninstalling shared plugins,
stopping shared providers, editing peers for removal or destroying drafts/documents.
Use tmp_path or equivalent isolated roots, never the active production tree.

### WP-W08 — Supported workflow integration

**Inspect:** each claimed supported workflow's UI action, real client/gateway path,
input, output/error and offline usage. Review component tests separately from
applicable browser, accessibility and actual integration evidence.

**Pass evidence:** independently checkable final observations prove the approved
workflow; unsupported commands remain honest. **Failure:** only helper tests,
mock-backed demonstration claimed as live integration, absent real entry-point
coverage or product completion inferred from a declaration. Record unavailable
browser/provider environments as evidence limits, not successful checks.

## 7. Concrete plugin control procedures

### WP-P01 — Cohesive concept and operations

**Inspect:** owning module and repository-wide copies of its behavior/config/schema/
metadata/lowering. Match every advertised OperationSpec to a real implementation
and pure contribution factory.

**Pass evidence:** one concept, one file, one semantic owner; implemented behavior
matches declared operations. **Failure:** split plugin-specific contracts/helpers,
shadow formulas, placeholders advertised as operational, or algorithms moved to
host/workspace/shared vocabulary. Applies to numerical and non-numerical plugins.

### WP-P02 — Parameter and search policy

**Inspect:** typed defaults, validity constraints, units, cross-field rules, optimizer
eligibility/bounds/scale/step and presentation hints. Exercise invalid and boundary
values through actual validation and relevant consumers.

**Pass evidence:** schema and behavior agree; validity and search spaces are distinct
and owned locally, without silent coercion. **Failure:** ignored settings, duplicated
optimizer ranges, undocumented defaults or UI-only constraints. A parameterless
operation can justify absent parameter subchecks with its real contract.

### WP-P03 — Ports and algebra

**Inspect:** typed ports, units/alignment, exact node references, graph versions,
connections, cycle/resource checks, unsupported references and canonical round trips.

**Pass evidence:** consumers use the same document semantics, invalid edges fail,
and recurrence remains explicit node state. **Failure:** implicit coercion, parallel
strategy interpreters, central comparison enums or lossy unknown nodes. N/A is
appropriate only if the plugin makes no algebra/node contribution or claim.

### WP-P04 — Numerical and error semantics

**Inspect:** independent specification and tests for parameter-derived warm-up,
seeding, flat/monotonic inputs, gap recovery, invalid periods, insufficient data,
non-finite values, zero division, ordering/timezones, precision and rounding.

**Pass evidence:** all applicable numerical and failure policies are explicit and
verified, including changed bound parameters. **Failure:** formula-name assumptions,
fixed warm-up metadata contradicting actual parameters or unexplained substitutions.
For non-numerical kinds justify numerical N/A; generic error semantics still apply.

### WP-P05 — Determinism and run isolation

**Inspect:** frozen inputs and descriptors, mutable aliases, seeds, persistent hashes,
accumulators and concurrent independent executions. Compare repeated equivalent runs.

**Pass evidence:** supported reproducibility is source/data/version/seed-bound and
run state is isolated; live input acquisition is frozen before comparison.
**Failure:** shared mutable buffers, leaked accumulators, ambient randomness or
Python hash used as durable identity. Do not demand identical elapsed durations
or external live responses as proof of deterministic quantitative output.

### WP-P06 — Operation effects and resources

**Inspect:** per-operation capabilities, effects, permissions, required/optional
absence, budgets, retries/rates and host-owned leases/cleanup. Distinguish pure
construction from effectful execution.

**Pass evidence:** actual bindings enforce declared effects and limits; relevant
failure/cancellation/startup/cleanup integration evidence exists. **Failure:** raw
connections/clients, plugin-owned host lifecycle, leaked resources, unbounded work
or optional absence blocking unrelated operations. Pure operations prove absence
of effects and justify N/A for unnecessary resource lifecycle subchecks.

### WP-P07 — Independent behavioral oracles

**Inspect:** hand-derived/reference goldens and their provenance; invalid, boundary
and degenerate cases; scalar/accelerated equivalence where both paths exist.
Reproduce a bounded selection when existing source-bound evidence is insufficient.

**Pass evidence:** expected observations are independent of the implementation and
cover the claimed semantics. **Failure:** snapshots generated by the same algorithm
as sole proof, asserted parity without comparison or tests only mirroring code.
Non-numerical plugins require appropriate independent behavior oracles, not N/A
for correctness as a whole.

### WP-P08 — Optimization and export compatibility

**Inspect:** declared search bounds and actual optimization consumers; advertised
lowering targets, node-owned IR contributions and generic exporter emission.
Compare execution and target semantics, including missing data/state policies.

**Pass evidence:** each claimed consumer/target works with semantic parity and
unsupported combinations fail explicitly. **Failure:** nonempty text presented as
parity, duplicated formulas, changed semantics or fabricated optimization results.
N/A requires no optimization/export claim; a missing advertised lowering is FAIL.

### WP-P09 — Generic consumer reflection

**Inspect:** actual UI/generator/simulator/optimizer/export consumers against canonical
plugin metadata and exact identity. Where supported, add a test plugin within the
existing vocabulary without changing engines, schema types or frontend source.

**Pass evidence:** generic consumers project one schema and behavior contract;
new universal vocabulary is explicitly scoped rather than silently patched.
**Failure:** hard-coded plugin-specific forms/branches, parallel parameter truth or
claimed reflection proved only by backend construction. Mark unclaimed consumer
subchecks N/A with rationale.

### WP-P10 — Usage and unsupported dependencies

**Inspect:** primary-purpose deterministic offline usage, resource cleanup, version
pinning and isolated missing/removed/incompatible dependency cases. Trace execution
through supported public composition boundaries rather than example-local formulas.

**Pass evidence:** realistic bounded outputs, preserved unknown documents and
attributed unavailability with no silent substitution. **Failure:** fabricated
example output, rewritten algorithms, active-data mutation, implicit fallback or
unsupported-version execution. Usage evidence does not establish remote/provider
or release qualification and does not require creating an unrelated workspace.

## 8. Required audit report

### 8.1 Answer-first assessment

State the unit/reference, track, exact source revision/candidate, audited scope,
overall recommendation and counts of PASS/PARTIAL/FAIL/INCONCLUSIVE/N/A. Name the
highest-impact deviations and whether the unit can truthfully retain its declared
completion scope. Separate an audit completion claim from implementation acceptance.

### 8.2 Control results and detailed findings

Create one row for every control in the applicable set. W has 21 controls; P has
23. Report mixed units separately, rather than averaging their results.

| Control | Verdict | Requirement/scope | Exact evidence | Deviation | Remediation owner | Limitation/N/A rationale |
|---|---|---|---|---|---|---|
| `<ID>` | `<verdict>` | `<mapping>` | `<path:symbol, receipt, command>` | `<finding>` | `<owning layer>` | `<reason>` |

Follow with detailed findings sufficient to reproduce each material conclusion.
Distinguish static observation, executed verification and inference. A file name,
test name, README status or metadata declaration alone is not a passing oracle.

### 8.3 Unit and requirement reconciliation

| Unit/version | Production owner | Descriptor | Family index | Tests/example | Candidate evidence | Verdict |
|---|---|---|---|---|---|---|
| `<ref>` | `<file>` | `<symbol>` | `<README>` | `<paths>` | `<source-bound receipt>` | `<verdict>` |

| Requirement/command/operation | Producer contract | Consumer/entry point | Acceptance oracle | Executable evidence | Verdict |
|---|---|---|---|---|---|
| `<ID or explicit gap>` | `<actual interface>` | `<actual caller>` | `<expected observation>` | `<receipt>` | `<verdict>` |

For workspaces include every command and its supported/deferred state. For
plugins include every declared operation and claimed target. Include shared
workflow obligations without manufacturing new requirement identifiers.

### 8.4 State and effect reachability, when applicable

| State/resource | Schema/contract owner | Authorized producer | Consumer/retention purpose | Cleanup/bounds | Evidence/verdict |
|---|---|---|---|---|---|
| `<record or resource>` | `<host contract>` | `<operation>` | `<actual use>` | `<policy>` | `<receipt>` |

Explain genuine stateless/non-effectful N/A. Never infer persistence correctness
from CRUD existence or test-only record access. Assess migrations only when the
declared host capability and task scope actually use them.

### 8.5 Command ledger

| Exact command | Purpose | Execution time | Exit code | Observed result | Source/environment limitation |
|---|---|---|---|---|---|
| `<command actually run>` | `<control>` | `<timestamp>` | `<code>` | `<observation>` | `<limit>` |

List checks not run separately with reasons and the evidence needed. Reused
receipts name their original source revision/time; do not present reuse as a new run.

### 8.6 Remediation and completion recommendation

Prioritize authority/security/data-integrity violations, computational errors,
contract/ownership/lifecycle defects, missing integration evidence, and then
documentation drift. Identify the owning layer, exact control, proposed action,
validation oracle and approval needed for each remediation. Do not implement it.

The report closes only after checking:

- Every applicable control has one verdict and sufficient cited evidence or gap.
- Every PASS proves the complete obligation; PARTIAL/FAIL name remediation;
  INCONCLUSIVE names missing evidence; every N/A has unit-specific justification.
- Source fingerprints, revision, commands and scopes agree; history is preserved.
- Pipeline canonical IDs and audit procedure IDs match exactly, without duplicates.
- No unsupported UI/provider/performance/release/parity claim was inferred.
- Source, production data and Git state were not mutated during the audit.
- The report says whether implementation may be called complete for its precise
  scope; finishing the audit does not itself change family or product status.

## 9. Maintaining reciprocity

For standards changes, verify the pipeline and audit contain exactly C01-C13,
W01-W08 and P01-P10 with identical titles and semantics. Check the pipeline's
prior PIP-control crosswalk for retained obligations. Historical FIP/PIP reports
retain their original meaning; do not rewrite them using these new verdicts.

Walk through a bounded declarative workspace and a concrete numerical plugin.
Confirm each delivery step has an audit route and that the audit introduces no
new build obligation. Validate links and actual commands. ID equality is a
necessary structural check, not proof of semantic reciprocity or code correctness.
