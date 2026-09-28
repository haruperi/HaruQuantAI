# Workspace and plugin implementation audit

Status: normative acceptance standard, 2026-09-27; enforcement implementation is
pending. Governed by [AGENTS.md](../../AGENTS.md) and
[ARCHITECTURE.md](../ARCHITECTURE.md). Audit against these controls independently of
the [build pipeline](workspace_plugin_implementation_pipeline.md); following steps
or reporting coverage does not establish semantic correctness.

## 1. Scope and evidence

Record exact candidate source/config/lockfile and inventory digests, tool versions,
approved plan version, tested shipping set, isolated storage location, commands,
exit codes and evidence files. Distinguish current behavior from target contracts.
Each control receives PASS, FAIL, BLOCKED or NOT_APPLICABLE with rationale and a
specific evidence reference. Missing/skipped checks are BLOCKED, never PASS.
NOT_APPLICABLE needs a contract-based reason, cannot waive removal/core controls,
and is prohibited for required release checks. Reports are validated both
structurally and semantically; report booleans do not prove execution.

## 2. Required controls

| ID | Inspect and exercise | Failure criterion |
| --- | --- | --- |
| O01 | Every shipping source, test, fixture, example and asset has one declared owner; paired files and modes agree | Orphan, overlap, missing pair, undeclared shipping file |
| O02 | Plugin has exactly one workspace and compatible slot/version | Multi-owner, invalid owner, ambiguous or unsupported attachment |
| B01 | Resolve Python/TS imports, aliases, re-exports, dynamic loads, CSS/asset refs and test/config edges | Peer business implementation reachable, or host imports concrete domains |
| B02 | Inspect host stores/services and neutral UI modules | Domain algorithms/state hidden in universal modules |
| B03 | Run import-time and negative graph fixtures | I/O/registration/tasks/environment reads at import; checker misses known violation |
| C01 | Validate metadata before loading factories; inject scoped services/bindings | Invalid/orphan code executes; ambient registry/SQL/path access |
| C02 | Empty host/workspace, duplicate/incompatible slots, partial init and cleanup failures | Unrelated startup fails or resources leak |
| H01 | Job ownership, admission, timeout/cancel/shutdown and hardware reservation release | Unbounded effects or plugin-owned global scheduler |
| R01 | Publish/read/revision/authorization/checksum and recovery tests | Lost/torn publication, silent overwrite, unauthorized access |
| R02 | Remove producer, restart and independently read saved bytes/schema/lineage | Read depends on producer code or uninstall changes stored content |
| R03 | Unknown executable/schema references | Silent substitution, fabricated success, data erased instead of unavailable |
| U01 | Existing routes/layout/dialogs/accessibility; removed UI after rebuild | Missing unrelated UI or changed preserved interaction |
| U02 | Schema projection and UI-only modes | Duplicate backend semantics or false provider availability |
| X01 | Dry-run ownership closure, stopped check, protected/link/stale paths, recovery | Wrong removal target or unjournaled partial operation |
| X02 | Per-plugin removal with siblings retained | Surviving build/test collection/operation fails |
| X03 | Workspace cascade and all-children-absent | Orphan activation or remaining workspace/host failure |
| X04 | Missing pair, cold absence, disable/re-enable, reinstall | Unattributed failure or lost preserved identity/data |
| Q01 | Candidate commands, branch coverage, real-host browser smoke | Required check fails/skips, tests deleted to mask failure |
| Q02 | Fresh exhaustive release report; negative CI controls | Unqualified shipping package, stale report accepted, gate bypass |

One-file concept locality, deterministic offline examples, numerical/boundary/error
tests and typed public signatures are mandatory for executable plugins. UI-only
packages cannot claim these algorithms; their presentation/removal controls still
apply. Kernel standard-library and empty/docstring-only initializer checks remain.

## 3. Mandatory matrix

| Case | Required observation |
| --- | --- |
| Intact baseline | Candidate backend checks, UI typecheck/unit/build and real-host smoke pass |
| Each plugin removed as a complete package | Backend never activates it; UI rebuild excludes it; remaining tests and sibling operations work |
| Each workspace removed with all owned plugins | No children activated/rendered; other workspace operations work |
| All children removed from each workspace | Workspace opens, reads retained resources and explains unavailable operations |
| All optional workspaces removed | Host authenticates/starts and renders an empty shell without a named Home dependency |
| Missing/incompatible owner or incomplete pair | Explicit diagnostic and no child execution; unrelated owners continue |
| Failed child activation/cleanup | Failure attributed; reservations/jobs cleaned up; unrelated owners run |
| Disable/re-enable and compatible reinstall | Correct visibility and capability transitions; retained identities/data recognized |
| Producer removed with saved resources | Independent authorized consumer reads unchanged bytes/revisions/schema/provenance; rerun reports absent algorithm |
| Unsafe/stale/active removal | Apply refuses; no data/peer mutation; partial journal recovery verified |

Each actual removal rebuilds frontend, runs surviving test collection/tests, starts
a fresh backend against isolated data, and exercises unaffected behavior in a real
browser/transport. Do not substitute a mocked catalog snapshot for these checks.
Capture resources before and compare digest, revision, membership and provenance
after. Test both ready and absent capabilities. Include original plugin tests in
baseline; remove only that package's owned tests during its uninstall case.

Use disposable materializations confined to verified temp roots. Never follow shared
data junctions, copy credentials or operate on the user's active database. Do not
mutate shared dependency installations. Run shell path containment checks before
recursive moves/deletion. Generic harness and unaffected assertions survive every
case; owner-specific browser tests have explicit ownership, not filename guessing.

## 4. Release decision

The shipping set comes from the built artifact/inventory, not a curated subset of
passing packages. For each package, compute required cases and compare with actual
report outcomes. Reject duplicate/missing cases, unmatched fingerprints, nonzero
exits, skipped requirements and unqualified shipping files. Include negative tests
that introduce an orphan, forbidden peer edge, stale digest and failed removal case;
the release command must fail for each. Artifact creation must not be treated as
release qualification. Exhaustive checks must not recursively invoke themselves.

PASS means the tested candidate/set met all applicable controls. A cohort PASS is
not full-app PASS. BLOCKED lists exact missing evidence/migrations. A report cannot
waive failures because discovery works or coverage exceeds 80%. CI workflow checks
and remote branch protection are separate facts; verify each before claiming both.

## 5. Audit record and follow-through

Use the [report schema](schemas/removal-qualification.schema.json) for machine
evidence and the [walkthrough template](../templates/walkthrough.md) for the human
decision. State limitations (trusted extensions, rebuild/restart boundary, producer
absence versus executable absence), deviations and residual risks. No approval to
commit, publish, migrate live data or expand providers follows automatically.
