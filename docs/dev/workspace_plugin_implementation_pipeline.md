# Workspace and plugin implementation pipeline

Status: normative standard, authored under approved ownership-removal-correction
plan v1, phase A, 2026-09-27. Runtime enforcement and migration remain pending.
Authority: [AGENTS.md](../../AGENTS.md) owns workflow/verification;
[ARCHITECTURE.md](../ARCHITECTURE.md) owns structural contracts;
[PROJECT.md](../PROJECT.md) owns product scope. This document owns build procedure;
the [independent audit](workspace_plugin_implementation_audit.md) owns acceptance.
No pipeline step authorizes source edits outside an approved exact-path plan.

## 1. Delivery units and metadata authority

A workspace pair is one workflow owner; a plugin pair is one concept attached to
exactly one workspace. A logical package includes backend, optional UI, all owned
tests, examples, fixtures and package assets even when located in separate roots.
Published/user-created resources are never package assets. Directory existence is
not registration, availability or implementation evidence.

Use local `package.json` documents satisfying [package.schema.json](schemas/package.schema.json).
Keep one authoritative package document in the backend root when present, otherwise
the UI root. Paths are repository/installation relative, exact files, not globs.
The normalized inventory is generated, never edited as a central plugin list.
The manifest owns pairing/path ownership and entry locations. The backend's literal
PLUGIN owns executable semantic metadata and references the same stable identity.
No second parameter/bounds schema is permitted in packaging or UI metadata.

`ui_only`, `headless` and `paired` explicitly declare counterpart presence. An absent
counterpart declared by mode differs from an incomplete installed pair. UI-only
plugins describe presentation attachment without claiming a backend provider.
Semantic descriptors own backend slots/requirements; a UI-only contribution's
entry owns presentation slots. The composer checks identity/attachment agreement.
README prose explains metadata; it is not another machine-readable registry.

Semantic plugin declaration: namespaced ID, implementation version, host contract
compatibility, owner workspace, slot/version, typed input/output ports, schema with
defaults/constraints/bounds/units, numerical/warm-up/missing-data/error policy,
authorized host requirements and deterministic entrypoint. One concrete Python
file contains the concept's calculation, schema, metadata and lowering. Universal
metamodels are allowed. Initializers are empty or docstring-only.

## 2. Common controls before either track

1. Record source fingerprint, current Git status, relevant READMEs and authority
   conflicts. Inspect actual tracked source, import graph, assets, styles, tests
   and installed capabilities; old walkthroughs cannot qualify different source.
2. Identify every owned path, counterpart, dependency, host service, shared resource
   schema and affected consumer. Resource schema access cannot require producer code.
3. Create the [implementation plan](../templates/implementation-plan.md), including
   explicit write/move/removal paths, contracts, isolated verification and residuals.
   Obtain the AGENTS.md owner approval before source changes.
4. Preserve unrelated work and existing UI behavior. Reapprove material contract,
   ownership, dependency, destructive-target or architectural expansions.

## 3. Workspace track W

| Step                | Required deliverable                                                                                             | Failure blocks   |
| ------------------- | ---------------------------------------------------------------------------------------------------------------- | ---------------- |
| W1 Ownership        | Local package document, one pair, local state, schemas and precise tests/assets                                  | Coding admission |
| W2 Slots            | Typed versioned slots, cardinality and explicit zero-plugin behavior; no list of concrete children               | Composition      |
| W3 Host services    | Scoped log/job/reservation/resource interfaces; no raw SQL, peer objects or global registry                      | Activation       |
| W4 Implementation   | Workspace-local workflow; immutable resource input/output; local view state; discovered UI entry                 | Candidate        |
| W5 Failure handling | Empty workspace, missing capability, partial activation cleanup, bounded cancellation                            | Candidate        |
| W6 Qualification    | Focused tests, wire/schema checks, resource producer-removal reads, workspace cascade and UI regression evidence | Release          |

Workspace preparation cannot require a named plugin. A specific operation may need
an attached capability and must explain its absence without preventing unrelated
operations. Workspaces cannot import sibling workspaces or sibling plugin logic.
The owner may invoke its children through host-bound typed slots; children do not
call their owner implementation or each other. No cross-workspace executor API.

## 4. Plugin track P

| Step             | Required deliverable                                                                               | Failure blocks   |
| ---------------- | -------------------------------------------------------------------------------------------------- | ---------------- |
| P1 Ownership     | One owner ID; exact paired code/test/assets; no overlap                                            | Coding admission |
| P2 Attachment    | Slot ID/version and compatible owner, typed contracts, explicit host capabilities                  | Activation       |
| P3 Concept       | One cohesive Python concept file, deterministic offline example and schema tests                   | Candidate        |
| P4 UI            | Generic schema renderer or local reviewed UI extension; no copied backend algorithms               | Candidate        |
| P5 Isolation     | No sibling stores/imports/services; owner absent/incompatible means no execution                   | Candidate        |
| P6 Qualification | Focused behavior/boundary tests, actual removal, unaffected sibling operations, retained artifacts | Release          |

UI-only prototypes must be labeled; no placeholder Python implementation is created
to imply a working provider. New functionality follows its own approved plan even
when a package already exists. Provider expansion follows host/Data Manager cohort
qualification, not merely completion of the documentation tracks.

## 5. Discovery and attachment lifecycle

The following are required contract records, not claims of existing runtime APIs:

| Record             | Required fields and constraints                                                                                                    |
| ------------------ | ---------------------------------------------------------------------------------------------------------------------------------- |
| Workspace slot     | Stable slot ID, contract version, input/output schema references, cardinality, allowed presentation vocabulary, empty-state policy |
| Plugin attachment  | Exclusive owner ID, slot ID, exact supported contract version, local entrypoint and authorized host-service requirements           |
| Binding            | Immutable owner/plugin identities, accepted contract version and scoped invocation handle; only owning composition receives it     |
| Availability       | Package ID, lifecycle state, affected operation, machine-readable reason and safe diagnostic; no hidden provider substitution      |
| Job request        | Owner-scoped task identity, immutable inputs, finite deadline/resource budget and cancellation policy                              |
| Resource reference | Resource ID, schema ID/version, revision, digest, media type and immutable producer provenance                                     |

Initial attachment requires exact contract-version agreement; future compatibility
ranges require independently tested rules. Cardinality conflicts fail closed for
the affected slot. Required operation inputs are distinguished from optional child
presence so workspace startup can succeed without a concrete plugin. Diagnostics
must distinguish missing_owner, incompatible_slot, missing_capability,
ambiguous_identity, incomplete_pair and activation_failed. Contract metadata never
grants authorization by itself. Wire/schema generation cannot centralize plugin
semantic definitions outside their owner.

Inspect metadata without executing contributions. Resolve exclusive ownership and
validate path containment, identity, versions, routes and slot cardinality before
importing trusted entrypoints. Prepare host services and workspace context, attach
valid children, then publish complete operations. No imported registration effects.
Child failures are attributed and cleaned up locally; unrelated startup continues.
Duplicate identities/ambiguous providers fail closed. Unsupported backend execution
does not turn an implemented read-only UI into fabricated success.

Frontend build discovers declared local entries, then lazily composes them by
owner/slot. Host navigation and types cannot enumerate domain implementations.
Backend runtime state gates commands. Missing/disabled owners hide child UI; stale
links and saved references have explicit unavailable states. Rebuild and restart
are required for initial removal guarantees; no runtime hot replacement promise.

## 6. Host services and resource boundary

Host owns logging, jobs/deadlines/cancellation, admission and hardware reservations,
authorization, generic custody, transactions and transport. A task's quantitative
body remains in its owner. Jobs/reservations release on completion, cancellation,
failure and shutdown; every effect has explicit lifecycle ownership.

Resources carry ID, schema ID/version, immutable revision, digest, media type and
producer provenance. Collections have versioned membership. Host performs bounded
authorized publication/list/read without producer imports. Publication is atomic or
recoverable, with explicit concurrent revision handling. Declarative schema snapshots
and content survive uninstall. Shared resources cannot contain executable dispatch
that calls a removed producer to read them. Unknown semantics can remain exportable
as bytes while interpretation/execution is unavailable. Retained settings/private
data also survive uninstall; permission to read still requires authority.

No package receives raw global registry, database connection or ambient filesystem
access. Host persistence adapters may reside in app/persistence. No plugin ad-hoc
SQL. Production schema changes require a distinct approved migration/recovery plan;
all qualification uses isolated temporary stores, never active databases.

## 7. Package removal procedure

1. Verify the stopped installation and current validated inventory. Compute the
   target's exact ownership set plus all children for a workspace. Never cascade
   through capability references to another workspace or through resource links.
2. Reject overlapping/unowned/protected paths, traversal, links/junction escapes,
   stale inventories and uncertain active owners. A missing pair is a diagnostic,
   not authority to guess cleanup targets. Discovery performs no deletion.
3. Use journaled reversible moves within the verified installation boundary.
   Abort/recover partial application explicitly. Apply authority excludes data roots,
   published content, lineage, databases, secrets and unrelated configuration.
4. Rebuild UI and restart backend. Verify removed routes/activation/contributions,
   unaffected operations, missing-capability errors and retained resource reads.
5. Reinstall under compatible identity to verify preserved data can be recognized.
   Data purge, workspace reassignment and live replacement are separate operations.

Deleting one folder manually does not delete its separate counterpart. The complete
package operation implements cascade semantics; cold absence still needs tests.

## 8. Candidate and release verification

Use explicit focused pytest paths with `--no-cov` during iteration. At candidate:
`uv run python scripts/ci_check.py`, `uv run python scripts/architecture_check.py`,
`npm --prefix app/ui run typecheck`, `npm --prefix app/ui run test`, and
`npm --prefix app/ui run build`, plus scoped real-host browser tests and the full
removal matrix defined by the audit. These existing commands alone do not yet
enforce the new standard. Future release/removal commands require approved source
implementation and must be documented with evidence before being called available.

The generic removal harness lives outside removable owners. Every shipping package
is discovered into the required test matrix; manifests cannot opt out by declaring
themselves incomplete. Reports use [removal-qualification.schema.json](schemas/removal-qualification.schema.json)
and bind exact source/config/lockfile/inventory digests and tool versions. Freshness
must be recomputed by CI, not trusted from a report's own assertions. Exclude generated
evidence from its own source hash, but include all executable source/config/inputs.

Missing, failed, skipped or stale required checks block release. Cohort reports
cannot qualify a larger shipping artifact. Do not remove existing screens/tests or
hide unqualified packages from discovery to claim success. Runtime isolation does
not imply hostile-code containment. Remote required-status enforcement needs actual
configuration evidence, not merely a checked-in workflow.

## 9. Handoff

Complete the independent audit and [walkthrough](../templates/walkthrough.md),
including exact commands/results, residuals, git status and proposed commit message.
Do not commit/merge/push or rewrite history without the owner's separate authority.

## 10. Quick Reference: How to Add, Create, or Remove Packages

### 10.1 Creating a new workspace

1. **Directory Structure**: Create `app/workspace/<Name>/` (backend) and/or `app/ui/app/workspace/<Name>/` (frontend).
2. **Authoritative Manifest (`package.json`)**:
   - Define `id: "workspace.<name>"`, `kind: "workspace"`, `version`, `host_contract`, `mode`, and `slots` (the extension points this workspace provides for plugins).
   - Explicitly list all `owned_paths` (`source`, `tests`, `assets`, `metadata`) matching exact files.
3. **UI Contribution & Slot Discovery**:
   - In the frontend component, discover child plugins dynamically using `useAttachments('<slot_id>')` from `app/ui/app/host/composition.tsx`.
   - Never statically import concrete plugins.
4. **Zero-Plugin Behavior**:
   - Implement explicit fallback UI/logic when zero child plugins are installed.

### 10.2 Creating a new plugin

1. **Directory Structure**: Create `app/plugins/<concept>/<Name>/` and/or `app/ui/app/plugins/<concept>/<Name>/`.
2. **Authoritative Manifest (`package.json`)**:
   - Define `id: "plugin.<workspace>.<name>"`, `kind: "plugin"`, `owner_workspace_id: "workspace.<owner>"`.
   - Specify `attachment`: `{ "slot_id": "<slot_name>", "contract_version": "1.0.0" }`.
   - Explicitly declare all `owned_paths` matching exact files.
3. **Cohesive Python Concept File (for backend plugins)**:
   - Calculation, parameter schema, defaults, bounds, inputs/outputs, and lowering stay together in one cohesive file.
4. **Zero Cross-Owner Imports**:
   - The plugin must not import sibling plugins or its owner workspace directly.

### 10.3 Removing a package

1. **Planning**: Use `plan_removal()` in `app/host/removal.py` to compute the exact closure (all owned files for the plugin, or the workspace plus all its child plugins). Persistent user data and settings are never touched.
2. **Application**: `apply_removal()` performs a journaled move into temporary storage under an installation lease.
3. **Survivor Invariant**: All remaining code must compile, pass tests, and run without runtime errors or missing-import crashes. Uninstalled plugins gracefully disclose missing capabilities.
4. **Restoration**: `restore_removal()` reverses the journal and verifies that the package inventory fingerprint is identical to baseline.

### 10.4 The Three-Tier Verification Cadence

Verification is structured into three tiers to balance rapid developer iteration with rigorous release-grade isolation guarantees:

| Tier | Name | Target Runtime | When to Run | Scope & Commands |
| :--- | :--- | :--- | :--- | :--- |
| **Tier 1** | **Focused Verification** | 1–5 seconds | Continuous inner loop during edits | Change-scoped tests with `--no-cov` to verify local behavior without whole-suite overhead:<br>• `uv run pytest <path/to/test.py> -k <test_name> --no-cov`<br>• `npm --prefix app/ui run test <path/to/test.ts>` |
| **Tier 2** | **Candidate Qualification** | ~45–60 seconds | Pre-commit, end of task, before walkthrough review | Fast static & whole-suite integrity (zero lint errors, type safety, 100% test pass, >=80% coverage):<br>1. `uv run python scripts/package_inventory.py`<br>2. `node scripts/ui_architecture_check.cjs`<br>3. `uv run python scripts/ci_check.py`<br>4. `npm --prefix app/ui run typecheck`<br>5. `npm --prefix app/ui run test`<br>6. `npm --prefix app/ui run build` |
| **Tier 3** | **Milestone Release Qualification** | ~60–75 minutes | Milestone releases, PR merges, or package lifecycle changes | Full combinatorial isolation matrix (all package removal cascades, fresh restarts, survivor checks, and Playwright E2E browser tests):<br>• `uv run python scripts/release_check.py --report .agents/logs/<timestamp>_<task>/release.json` |

> [!NOTE]
> **Why Tier 3 is not run for everyday edits:**
> `release_check.py` exhaustively uninstalls and restores every package in isolation (68+ scenarios across all workspaces and plugins), running full Python compilation, UI typechecks, Vitest suites, Vite builds, and Playwright headless browser checks for every single survivor permutation. It is designed as an automated release gate and CI milestone qualification, not an inner-loop pre-commit hook. Routine development relies on Tier 1 and Tier 2.
