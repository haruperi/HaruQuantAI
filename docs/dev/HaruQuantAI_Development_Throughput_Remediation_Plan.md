# HaruQuantAI V3 — Development Throughput Remediation Plan

**Date:** 9 September 2026
**Status:** ACTIVE — IMPLEMENTATION DEPLOYED; EFFECTIVENESS NOT YET DEMONSTRATED. DT-01 through DT-11 are committed through `d64ea9a3`. Sections 8 through 10 are being finalized in the current uncommitted documentation/testing-policy change. The post-DT-06 representative-feature pilot is 0/3, no canonical DT-10 accepted-run summaries currently exist, the five live aggregate evidence projections report drift, and DT-03 remote publication/repository protection remain pending explicit owner authorization. Remediation self-tests do not satisfy those outstanding outcomes.
**Repository baseline checked:** `a32a46ad5c3407bdb7b68bf8dc270d327b6e7625` on remote `main`.
**Repository location:** `docs/dev/HaruQuantAI_Development_Throughput_Remediation_Plan.md`
**Basis:** The three supplied agent analyses, supplemented by targeted read-only repository checks and official tool documentation. Source references appear in §12.

## 1. Decision and objective

Keep HaruQuantAI V3, its focused feature architecture, and the complete registered product scope. Change the delivery process around that architecture. Do not restart the product, defer all tests, remove lifecycle guarantees, or make `git push --no-verify` the development policy.

The target is **more correctly accepted functionality per working hour and per unit of allowance**, not merely more generated code. The four-to-eight-hour ambition remains a throughput objective to evaluate, not a supported promise that the entire remaining acceptance contract will be finished within that time.

This plan attacks four different costs separately:

| Cost | Intervention |
|---|---|
| Repeated broad validation | Fast default tests; change-aware routing; one comprehensive integration qualification per candidate/batch. |
| Repeated reasoning and handoffs | Prepared task packets; risk-tiered planning; direct bounded corrections; deterministic administrative close-out. |
| Repetitive authoring | Reuse existing implementations; generate structural boilerplate and evidence projections; shared conformance harnesses. |
| Sequential delivery | Small coherent batches, then bounded existing parallel lanes with isolated writes and one integrator. |

**Preserve:** feature identities, owning requirements, public contracts, strict typing, applicable coverage floors, numerical correctness, authorization and account isolation, persistence safety, lifecycle/removal behavior, independent review, owner authorization, and honest distinction between component evidence and real-provider qualification.

**Do not add:** another orchestrator, a new general-purpose agent framework, a separate project-management database, a dashboard, or a second source of feature status. Extend existing scripts and records.

## 2. What the evidence establishes—and what it does not

| Finding | Evidence and interpretation |
|---|---|
| Python coverage and HTML reporting are default pytest options. | Verified in `pyproject.toml`. A focused command requires an override today. [R2] |
| A UI-only change can trigger full Python validation on push. | Verified: the pytest hook matches `app/`, ignores filenames, and runs whole-app coverage; mypy is also broadly triggered. [R1] |
| Ordinary checked-in pre-commit hooks do not run pytest. | Verified: formatting, lint, hygiene and secret scanning are pre-commit; pytest/mypy are pre-push. Local IDE or hook behavior still needs local inspection. [R1] |
| Complete validation always includes workflow-controller checks. | Verified in `scripts/ci_check.py`; its nested `uv run` also lacks a lock-preservation option. [R3] |
| The checked-in CI workflow does not run the UI's npm checks. | Verified in `.github/workflows/ci.yml`; UI typecheck, test and build scripts exist separately. [R4, R5] |
| Remote `main` reports no enabled branch protection. | The branch response at inspection reports `protected: false` and required checks off. Do not assume CI is an enforced acceptance gate. [R9] |
| Small corrections currently return through Planner. | Verified in `AGENTS.md`. Owner gates and reviewed-byte identity are intentional protections, not things to silently bypass. [R6] |
| The plan requires whole-feature scope and extensive evidence. | Verified in the plan's execution contract and Definition of Done. Feature count is not a uniform effort measure. [R7] |
| Evidence-generation tooling already exists. | `scripts/generate_phase0_evidence.py` parses the ratified plan/register and has pinned historical references. Reuse appropriate parsing/validation; do not rewrite historical Phase 0 truth. [R8] |
| Task 1.16 reportedly suffered five iterations, genuine UI defects and administrative failures. | Reported by the supplied local-agent analyses. These local logs and exact timings were not independently re-executed here. [S1] |

The following claims are **not** planning assumptions: “75% was the AI debating,” a guaranteed 5–10-minute duration for every feature, a guaranteed allowance reduction, or an architectural proof that any particular completion time is impossible. The supplied analyses do not establish those conclusions. Their counts of requirements also use differing descriptions; this plan does not combine them into a new metric.

Use Agent 1's useful suggestions about hooks, batching and automation; retain Agents 2 and 3's distinctions about real defects, risk, test selection and integration enforcement. Do not adopt blanket Quick-Fix-on-main, a universal one-to-two-test limit, or status generation from file existence.

## 3. Rollout structure

These are **eleven top-level work orders within four remediation change sets**. Until an explicitly reviewed workflow amendment replaces the current atomic Task contract, each independently reviewable work order follows the workflow required by `AGENTS.md`. DT-01, DT-02 and DT-03 were delivered separately. The owner subsequently authorized DT-04, DT-05 and DT-06 as one Change Set B delivery, while requiring their internal checkpoints to remain ordered and measurable. Workflow/approval changes themselves receive strong review.

| Change set | Work orders | Exit condition |
|---|---|---|
| A — Stop avoidable waiting | DT-01 through DT-03 | Mechanical regressions covered; fast test defaults; verified local integration protection before hook relaxation; remote enforcement handled separately. |
| B — Stop repeated reasoning | DT-04 through DT-06 | Risk-tiered packets, bounded direct corrections, trustworthy validation records and deterministic close-out. |
| C — Stop repetitive authoring | DT-07 and DT-08 | Evidence projection and one useful scaffolding/conformance path demonstrated without false acceptance. |
| D — Increase useful delivery throughput | DT-09 through DT-11 | Conservative batching and bounded parallel lanes validated using accepted outcomes; a strategy-ready milestone is frozen and measured separately from full V3 completion. |

Implement A before spending effort on a universal scaffolder or parallel scheduling improvements. Production development can resume on the improved path after A and B; completing every optional automation is not a new prerequisite for working on strategies.

### Dependency order

```text
DT-01 → DT-02 (combined DT-02A + DT-02B) → DT-03 → DT-04 → DT-05 → DT-06 → POST-DT-06 PILOT

POST-DT-06 PILOT → DT-07 → DT-08 (optional evidence/scaffolding path)
POST-DT-06 PILOT → DT-09 → DT-10 (optional batching/parallelism path)
POST-DT-06 PILOT → DT-11         (strategy-ready milestone path)
```

The owner authorized DT-02A and DT-02B as one combined DT-02 delivery, DT-04 through DT-06 as one combined Change Set B delivery, and DT-07 with DT-08 as one combined Change Set C delivery on 9 September 2026. The owner explicitly advanced Change Set C before the post-DT-06 product-feature pilot; this changes delivery order only and does not waive or satisfy that pilot. Implementation still establishes and measures each internal checkpoint before enabling the next so incremental behavior remains observable. DT-08 is not a prerequisite for DT-09. DT-11 depends on the post-DT-06 pilot, not on completing optional scaffolding or parallelism. Defer later automation whose measured benefit is weak. All change sets must preserve previously passing safeguards.

Implementation record: DT-01 was committed as `5faf73fe`; combined DT-02A/DT-02B was committed as `6420d7e8`; DT-03 was committed as `311e6dce`; combined DT-04/DT-05/DT-06 was committed as `82661187`; combined DT-07/DT-08 was committed as `a2575997`; and combined DT-09/DT-10/DT-11 was committed as `d64ea9a3`. DT-03 selects the local-first acceptance model defined below. A local Task may become `ACCEPTED` only after controller-enforced integration validation of its frozen reviewed state and exact merge lineage. Publishing remains separately authorized, and the remote `acceptance` result confirms rather than retroactively grants local Task acceptance.

## 4. Change set A — Stop avoidable waiting

### DT-01 — Capture a bounded baseline and fix recurring mechanical failures

**Primary paths:** existing `.agents/` controller and tests; `.pre-commit-config.yaml`; `.github/.secrets.baseline`; new scoped `.gitattributes`; existing runtime logs. Inspect the local ignored run configuration, Git hooks and run records without publishing credentials or private logs.

**Actions**

1. Record local HEAD, upstream HEAD, ahead/behind state, active workflow state, dirty paths, Python/Node versions and actual hook configuration. The checked repository targets Python 3.14; do not substitute older project-memory settings. Preserve active work and user changes. No reset, automatic stash, force-push or recreation of an active task.
2. Extract available stage/command timings from Task 1.16 and other existing accepted-run records. Record unknown values as unknown; do not rerun historical product tasks merely to manufacture a baseline.
3. Reproduce the reported administrative problems with small controller/Git fixtures: legitimate commit-hash secret-scanner findings, omitted generated paths, staged/unstaged normalization and approval fingerprint drift.
4. Resolve a verified scanner false positive without requiring every feature Task to edit `.github/.secrets.baseline`. Prefer a schema-aware, field-specific treatment for `baseline_commit` combined with deterministic verification that the value resolves to a real repository commit. An equivalent design is acceptable only when it avoids per-feature shared-baseline churn and retains the same narrow security boundary. Do not exclude the evidence directory, disable a detector globally, or allow every 40-character hexadecimal value everywhere. Keep ordinary new-secret detection effective.
5. Define UTF-8/LF writing for coordination documents and deterministic JSON. Add attributes for the precise relevant paths, starting with `.agents/task/*.md` and `.agents/*.toml`; do not renormalize the entire repository. Normalize an inactive/new document before approval, not by silently changing approved bytes afterward.
6. Run mutating formatting and generation **before** freezing the reviewed candidate. After approval, use check-only validation. A product edit or unexplained byte change still invalidates the appropriate approval; retry logic must not simply ignore mismatches.
7. Make the generator's complete output inventory available before execution, so known generated paths are not discovered as unauthorized writes during close-out.

**Acceptance**

- A legitimate schema-valid `baseline_commit` that resolves to a repository commit can complete normal close-out without disabling secret scanning and without a per-feature `.github/.secrets.baseline` modification.
- Synthetic secret-detection regression cases remain detectable; no actual credential is used as a fixture.
- An arbitrary hexadecimal value in any unapproved field remains subject to secret detection.
- A Windows-style staged/unstaged normalization fixture cannot silently change the approved tree.
- Changing product code after approval still blocks acceptance.
- Known generated outputs are listed before the executor starts.
- Local branch divergence is reported before an expensive delivery attempt, without modifying user work.

**Rollback:** Revert only the focused fix that regresses behavior. Preserve run evidence; never recover by weakening byte identity or deleting tests.

### DT-02 — Make normal validation fast and comprehensive validation explicit

**Primary paths:** `pyproject.toml`, `scripts/ci_check.py`, tests for the validation router. Add at most one small routing helper if needed; retain `ci_check.py` as the public entry point.

DT-02A and DT-02B are delivered as one owner-authorized change set. DT-02A remains the first internal implementation and measurement checkpoint; DT-02B then adds bounded advanced impact routing without a separate commit or approval cycle. The combined delivery does not waive either stage's acceptance criteria.

#### DT-02A — Fast defaults and explicit validation profiles

**Actions**

Remove these four entries from `[tool.pytest.ini_options].addopts`:

```toml
"--cov=app",
"--cov-report=term-missing",
"--cov-report=html",
"--cov-fail-under=80",
```

Retain import mode, strict configuration/markers, reporting, warning policy and cache configuration. Retain `[tool.coverage.run]` branch coverage, `[tool.coverage.report] fail_under = 80`, and any stronger owner-specific coverage obligation. Coverage becomes opt-in, not optional at its required boundary. [R2, W1]

Introduce these **proposed** profiles; they are new interfaces to implement, not existing commands:

| Profile | Meaning |
|---|---|
| `affected` | Explicit changed scope, owner/consumer tests, relevant static/contract checks; no global coverage or default full build. |
| `python` | Comprehensive Python/product checks, strict mypy, architectural/documentation checks and full applicable coverage. |
| `ui` | UI typecheck, Vitest and production build; applicable browser qualification remains separately required. |
| `workflow` | Workflow-controller tests, self-test and applicable lint/type checks. |
| `integration` | Select the necessary comprehensive profiles for the candidate against its integration base. |
| `full` | All applicable profiles, including workflow and UI; conservative default when no profile is supplied. |

In DT-02A, implement the explicit profiles with straightforward conservative UI, Python, workflow, documentation and mixed-scope routing. Existing no-argument invocation remains conservative. A simple path-to-profile mapping is sufficient for this stage; unknown, shared or mixed scope widens to `full`.

#### DT-02B — Advanced candidate and dependency-aware routing

After measuring DT-02A, add `--base`, `--head`, `--explain` and `--report` only when their expected benefit justifies the added implementation and maintenance cost. The two refs must resolve to commits. `--explain` outputs selected commands and routing reasons without executing them.

Use the merge-base-to-candidate delta for committed changes, including deletions, renames and both names of renamed paths. During local development, union staged, unstaged and relevant untracked paths. For integration acceptance, require a clean materialized candidate and include changes introduced while combining it with the current base. A missing base, unknown path, incomplete ownership mapping or inconclusive dependency relationship widens validation rather than returning a misleading empty selection.

**Initial routing policy**

| Change | Iterative checks | Integration checks |
|---|---|---|
| UI presentation and local UI behavior | Selected UI tests and relevant type/contract checks | Full UI checks and applicable browser regression; no unrelated Python suite. |
| Python feature internals | Owner tests plus affected public consumers | Comprehensive Python profile. |
| Shared public contracts, generation, composition, kernel, cross-stack boundary | Relevant consumers, including UI consumers | Python and UI profiles; expand to full when impact is uncertain. |
| Workflow controller, role prompts, approval rules | Focused workflow tests and self-test | Workflow profile plus every product profile affected by the change. |
| Dependency locks, root tool configuration, validation/CI or routing code | All affected tooling checks | Full profile by default. |
| Pure prose or generated status projection | Syntax/schema, links/bindings and deterministic projection checks | Relevant documentation/evidence checks; no automatic product test rerun solely for nonsemantic bookkeeping. |
| Ambiguous or mixed scope | Union of all applicable checks | Conservative full profile. |

A capability dependency graph alone is not a complete test-impact graph. Include public import/contract consumers, integration fixtures, `conftest.py` scope, generators and UI/API consumers. Do not build a speculative whole-program dependency engine: begin with conservative domain routing and existing bindings.

Use locked dependencies for the runner and all nested commands. `uv run --locked` errors rather than silently rewriting an outdated lock; this distinction is documented by uv. Do not change dependencies merely to perform validation. [W4]

Deduplicate identical command invocations within a profile combination. Remove the standalone provider-disable matrix invocation only after confirming it is collected and covered in the relevant comprehensive run; otherwise keep one explicit `--no-cov` invocation. Do not accidentally drop the matrix.

**DT-02A acceptance**

- Focused default pytest produces no coverage report and does not alter coverage artifacts.
- Comprehensive Python validation retains the coverage floor and fails on test failure or inadequate required coverage.
- UI-only routing selects no unrelated Python test/mypy run; unknown impact never silently selects nothing.
- The full profile executes every required family once, including UI and workflow checks.
- Dependency files are unchanged by validation.

**DT-02B acceptance**

- Explain-mode routing tests cover UI-only, Python-only, contracts, root fixtures, lock changes, workflow changes, mixed changes, deleted/renamed files, untracked files and unknown scope.
- Candidate selection uses the exact resolved base/head identities and invalidates stale results.
- Public-contract and dependency-aware routing includes known consumers without pretending to be a complete whole-program dependency engine.
- Measurement shows that DT-02B improves accepted throughput or diagnostic clarity enough to justify retaining it; otherwise DT-02A remains the supported path.

### DT-03 — Establish local acceptance protection, then add remote enforcement

**Primary paths:** `.github/workflows/ci.yml`, `.pre-commit-config.yaml`, `scripts/ci_check.py`, `.agents/` close-out/integration behavior, `AGENTS.md`, `.agents/PROCEDURE.md`, and repository protection settings.

**Governing model selected:** local-first acceptance with remote confirmation. The checked-in controller gate is authoritative for local Task acceptance. The CI job named `acceptance` qualifies an explicitly published candidate. Local commit/merge permissions never authorize a push, pull-request merge, branch-protection mutation or other remote administration. Until those remote settings are separately authorized, configured and verified, the local gate remains mandatory and the plan must report remote enforcement as pending.

**Target flow**

```text
Task/batch candidate branch
  → independent review and scoped tests
  → explicit commit/publish authorization
  → required integration checks against current main
  → authorized merge
  → ACCEPTED
```

**Actions**

1. Establish one local integration-candidate gate using the DT-02 profiles and locked environments. It must evaluate every profile required by the classifier, including the applicable UI `typecheck`, `test` and `build` commands, and fail on a missing, failed or unexpectedly skipped prerequisite. Use the repository's package lock; do not update packages as part of validation setup.
2. Keep applicable real-provider/browser checks at their existing required phase/operation gates. Mocked Vitest success is not browser or provider qualification.
3. Repair actual baseline failures exposed by the local checks in bounded changes. Do not change floors, blanket-ignore errors or declare the baseline green because selected checks passed.
4. Prove that the local integration-candidate gate rejects a deliberately failing or stale candidate. This local replacement permits the first hook-speed improvements without waiting for repository-administration work.
5. Once the local replacement gate is proven, keep pre-commit formatting, lint, hygiene and secret detection. Replace the broad pre-push full-suite hooks with lightweight scope/consistency checks. Focused behavioral tests run during execution; comprehensive suites run at the local integration-candidate boundary rather than on every push.
6. As a separate repository-administration step within DT-03, make CI invoke the same integration profiles and install the locked UI dependencies needed for the existing UI commands.
7. Add one stable final remote status named `acceptance`; it must always report and must reject missing, failed or unexpectedly skipped prerequisite profiles. Workflow-level path filtering must not prevent this required status from reporting. [W3]
8. Configure and verify required checks/PR protection only with the owner's explicit repository-administration authority. An unavailable permission is a remote-enforcement blocker, not permission to assume protection exists and not a blocker to retaining the proven local integration gate.
9. Amend acceptance semantics only after choosing and documenting the governing model: local-first acceptance with remote confirmation, or PR-first acceptance enforced remotely. Preserve `APPROVED: EXECUTE` and `APPROVED: COMMIT`, or the existing legitimately frozen equivalents. Existing local commit/merge permissions do **not** authorize publishing or remote merging; any remote-action permission must be explicit and default off.
10. Never remove the existing broad protection before the local replacement is operational. After remote enforcement is proven, measure whether the local comprehensive gate can be reduced further without creating an acceptance gap.

**Acceptance**

- A deliberately failing candidate cannot be accepted or merged through the selected governed path.
- A newly pushed untested candidate is not marked complete.
- A UI-only candidate runs UI validation without unrelated Python coverage.
- A Python-changing batch receives comprehensive Python coverage before acceptance.
- A stale local or remote successful check does not approve a different candidate/base combination.
- Fast local checks preserve secret detection and do not start full pytest or HTML coverage.
- Remote-action authorization cannot be inferred from local-only permission.
- The first local speed gains do not depend on GitHub-administration access; when remote enforcement is unavailable, the proven local integration gate remains authoritative under the documented local-first model.

**Rollback:** Keep or restore the conservative local integration gate until remote enforcement is healthy. Never solve a broken CI migration with routine `--no-verify` or administrative bypass.

## 5. Change set B — Stop repeated reasoning

### DT-04 — Classify failures and introduce bounded direct correction

**Primary paths:** `AGENTS.md`, `.agents/protocol.toml`, `.agents/orchestrator.py`, the actual controller transition/validation modules, canonical role/close-out prompts, `.agents/PROCEDURE.md`, controller tests.

**Decided routing**

| Finding | Route | Boundary |
|---|---|---|
| `IMPLEMENTATION_FIX` | Reviewer → Executor → Reviewer | Expected behavior, ownership and authorized scope are unchanged. |
| `DESIGN_CHANGE` | Reviewer/Executor → Planner | Requires a new contract, scope, requirement interpretation, security decision or architectural choice. |
| `ADMINISTRATIVE_RETRY` | Deterministic controller repair/retry | Exact allowlisted operation over unchanged reviewed inputs; no product-policy decision. |
| `ENVIRONMENT_FAILURE` | Preserve state; bounded environment recovery | No product replan solely because a process, runner or dependency installation failed. |

Allow at most two direct implementation-correction rounds before targeted Planner escalation. Allow at most one automatic retry of the same administrative/environment operation. Persistent failure must stop with a concrete diagnosis, not produce another indistinguishable loop.

Every reasoning invocation still receives a valid standalone handoff. A correction references the current approved task packet and exact failing expectation; it does not recreate all prior analysis. Administrative repair cannot edit product source, contracts, approved requirements or security policies. Secret-baseline policy changes are not a permanently self-authorized administrative action.

**Acceptance:** Tests cover each route, retry bounds, preserved work, stale approval rejection, scope-change escalation and refusal of an administrative attempt to change production code.

### DT-05 — Prepare compact task packets and use risk-tiered planning

**Primary paths:** existing plan/register/evidence parsing utilities, one new bounded task-packet generator, `docs/templates/prompt/`, `AGENTS.md`, relevant controller config/schema/tests. Generated packets belong in runtime task/run storage, not a second canonical plan.

**Required packet contents**

- Task and feature IDs; source commit; exact source locations/hashes; current baseline and authorized write footprint, including generated outputs.
- Complete owning FR/NFR obligations, applicable shared NFRs and catalogue obligations; no truncation to satisfy a token budget.
- Exact public contracts and dependencies; actual accepted predecessor evidence; existing provider/test/usage paths and aliases.
- Requirement-specific expected behavior, failure cases, numerical examples when applicable, lifecycle/cleanup obligations and qualification boundaries.
- One compatible accepted implementation example when available; explicit reuse decision; relevant generation/template instructions.
- Test selections, validation profiles, expected evidence, risk tier and remaining unresolved decisions.

Extraction is deterministic where sources are structured. Engineering choices are made once by Planner when genuinely unresolved, then frozen. A packet with a missing contract, ambiguous oracle or unbound required path is not executor-ready. A packet is an index and bounded extract of authority, not permission to ignore that authority. The reviewer can check original source spans directly.

**Risk tiers**

| Tier | Examples | Workflow |
|---|---|---|
| Routine | Nonsemantic prose, an isolated presentation adjustment, deterministic mechanical generation | Prepared packet → Executor → focused independent review. No fresh exploratory planning when nothing needs deciding. |
| Standard | A well-specified bounded service or UI interaction using stable contracts | Prepared packet → Executor → independent review; Planner only for an unresolved decision. |
| Critical | Authorization/session scope, cross-account or cross-workspace operations, trading/risk, numerical correctness, persistence/recovery, resource ownership/concurrency, external providers and network integrations, destructive actions, workflow approval/validation policy | Targeted explicit planning/risk analysis → Executor → stronger independent/adversarial review. |

Risk follows behavior, not file type or change size. A manifest that changes mandatory dependencies is not low-risk metadata; a session-access widget is not merely presentation; a shared DTO changes a contract. Ambiguous classification selects the stronger tier.

Keep the full policy available but reduce root `AGENTS.md` to binding invariants and precise routing. Do not replace a large file with a list of links that still forces every role to load everything. Load only the relevant role/transport/risk instructions, while retaining all applicable rules.

Reuse task-local context during a bounded correction. Do not carry hundreds of tasks through one ever-growing session, or reset a role mid-correction without a complete current packet and state handoff. Do not attribute specific token costs to an unobserved provider implementation.

**Acceptance:** A normal prepared task begins without a new exploratory Planner invocation; a contract ambiguity blocks rather than being invented; a stale source fingerprint invalidates the packet; critical classifications retain stronger review; no requirement disappears from extraction.

### DT-06 — Reuse trustworthy validation and make close-out deterministic

**Primary paths:** `scripts/ci_check.py`, existing run evidence/logging, `.agents/` controller and close-out path, role prompts and tests.

The runner, not the LLM, records commands, working directories, exit codes and durations. Store full logs outside the conversation and return bounded summaries plus log references. Reviewers still independently judge behavior, verify source/oracles and run selected adversarial checks. An executor's statement that tests passed is not a validation receipt.

A reusable receipt records the candidate/base identity; source/input manifest; validation policy and runner identity; contract/test/config/lock hashes; command/arguments/working directory; relevant environment and fixture/seed identities; timestamps/duration/exit code; and log/report hashes. A hash is integrity metadata, not proof of trusted origin: consume controller/CI-produced records from a known channel, not agent-authored JSON masquerading as a test result.

Start with conservative exact-input reuse **within the same candidate**. Do not build cross-commit cache reuse or a signing service in the first version. Changes to tests, contracts, fixtures, environment, runner, policy or relevant source invalidate the receipt. Runtime logs/receipts cannot self-reference their own hashes; define their exact nonsemantic exclusion boundary. Do not broadly exclude documentation or evidence that affects requirements or acceptance.

Move deterministic path checks, formatting verification, receipt validation, authorized commit/merge mechanics, journal archival and final receipt creation into the existing controller. Review conclusions remain authored by the reviewer. No controller decision invents an approval, interprets an unresolved requirement or grants an operation privilege.

Retain the existing self-reference avoidance: committed evidence pins the tested tree/parent and report hashes; final accepted commit is written in close-out evidence after creation. Do not manufacture an empty implementation commit to record its own hash. [R7]

**Acceptance:** Valid same-input results can be reused across a handoff; changing an input rejects them; forged/edited records are not accepted; a reviewer-selected new check runs; close-out needs no LLM invocation when no engineering decision remains; actual byte drift still blocks acceptance.

### Change Set B implementation record — 9 September 2026

- **DT-04:** The controller now distinguishes `IMPLEMENTATION_FIX`, `DESIGN_CHANGE`, `ADMINISTRATIVE_RETRY`, and `ENVIRONMENT_FAILURE`. Unchanged-scope Reviewer findings return directly to Executor for no more than two rounds; design changes and exhausted corrections return to Planner; unchanged-input administrative/environment work receives at most one retry. Allowlisted administrative paths exclude production, contracts, policies, journals, and the secret baseline. A one-correction path uses five reasoning turns (`P/E/R/E/R`) instead of the former six (`P/E/R/P/E/R`), a 16.7% reduction; two corrections use seven instead of nine, a 22.2% reduction. No elapsed-time or allowance saving is claimed before the pilot.
- **DT-05:** Task activation now generates a schema-v1 runtime packet and validates every recorded source hash. An executor-ready Routine/Standard packet may proceed to the existing execute gate without Planner; Critical, blocked, ambiguous, or stale packets retain Planner. The real Task 1.18 packet was generated in 26.6 ms and was 20,454 JSON bytes. It conservatively classified `FEAT-ORCH-MANAGE_JOBS` as Critical, retained four FRs, one local NFR, 39 shared NFRs, ten pinned source locations, fourteen authorized write paths, its declared commit message, and zero invented resolutions. Root `AGENTS.md` was reduced from 33,708 to 26,289 measured characters (22.0%) by retaining binding invariants there and routing operational detail to `.agents/PROCEDURE.md` and `.agents/GOALS.md`.
- **DT-06:** The integration runner stores complete command logs outside prompts and issues a controller-owned exact-input receipt. Product-byte, authority, policy/config/test/lock, diagnostic, result, or log drift invalidates reuse. Reviewer uses the receipt plus selected adversarial checks; the comprehensive integration profile is not repeated merely because review began. Authorized close-out is deterministic controller code that restricts staging to packet paths, creates the declared Task commit and explicit no-ff merge, verifies lineage, clears coordination only after commit success, and invokes no reasoning role. Receipt tests prove same-candidate handoff reuse and reject altered inputs/logs/records; close-out tests prove exact-path commit/merge/cleanup and fail before staging on an unauthorized path.
- **Regression checkpoint:** The workflow/controller and `ci_check` regression suite passed 259 tests after the final documentation-contract correction. The orchestrator self-test also passed end to end. This is implementation evidence, not the post-DT-06 product-throughput pilot and not proof of a universal feature-time reduction.

### Post-DT-06 pilot and continuation gate

Before implementing optional evidence/scaffolding/batching/parallelism work, exercise the remediated A+B path on three newly accepted representative features:

1. one UI interaction or presentation feature;
2. one ordinary stateless service feature;
3. one critical stateful, security-sensitive, concurrency or numerical feature.

Task 1.18 (`FEAT-ORCH-MANAGE_JOBS`) may serve only as the critical stateful/concurrency sample. Its persistent shared jobs and attempts, restart survival, authoritative lifecycle and resource-coordination behavior classify it as Critical under DT-05. It must not be treated as the routine Quick-Fix/direct-execution benchmark or used to justify weakening the critical workflow.

Compare each feature only with reasonably similar historical work. Record planning, execution, validation, review, close-out, correction causes, accepted outcome and available allowance observations. Decide explicitly whether DT-07 through DT-10 are justified, need revision or should be deferred. DT-11 may proceed from this checkpoint because it defines the product milestone needed to return attention to strategy development.

**Acceptance:** The three features are genuinely accepted rather than replayed historical work; administrative replanning is zero for repaired cases; no required safeguard or evidence mapping is lost; and the continuation decision cites measured results instead of assumed speedups. The ten-feature sample in DT-10 remains a later confirmation sample, not the first effectiveness measurement.

## 6. Change set C — Stop repetitive authoring

### DT-07 — Project evidence deterministically without inventing completion

**Primary paths:** `scripts/generate_phase0_evidence.py` for reusable parsing/validation only, the existing live evidence update path, `docs/dev/evidence/` schemas/bindings/tests, controller integration.

Inspect and reuse the existing live updater before adding another command. Preserve pinned historical Phase 0 source snapshots. Where there is no reusable live projection operation, add a small dedicated current-progress operation rather than rerunning historical generation indiscriminately.

Inputs are authoritative feature metadata, explicit requirement-to-check mappings, controller-produced validation records and reviewed acceptance decisions. Outputs are the existing feature acceptance record and current contract/path/usage/requirement/progress projections. The model supplies only new engineering mappings/findings—not repetitive JSON synchronization.

The operation must support output-path discovery, a preview, check-only validation and application of an exact reviewed projection. Outputs must be stable and idempotent. Validate all new records before replacing existing ones. Preserve existing aliases, statuses and the distinction between implemented adapters and `OPERATION_NOT_QUALIFIED` real-provider behavior.

Do not scan files, see a function or test name and declare its requirement passed. Do not delete failure evidence, upgrade unavailable operations to qualified, rewrite historical accepted facts, or treat copied examples as successful execution. Generate projections during the accepted delivery cycle, not only at the end of the phase.

Only the integrator writes shared aggregate ledgers during parallel work. Workers provide feature-local draft mappings/results. Integration regenerates and validates aggregate projections before final candidate qualification.

**Acceptance:** A repeated run changes no bytes; missing/failed evidence prevents completion; historical Phase 0 snapshots remain unchanged; an unavailable real provider remains unqualified; a changed binding cannot silently orphan a requirement; generated-path inventory is complete.

**Implementation checkpoint (9 September 2026):** `scripts/project_feature_evidence.py` now owns only the five live aggregate projections and exact reviewed feature/tracker finalization; `scripts/generate_phase0_evidence.py` preserves the three pinned Phase-0 outputs in write mode. The controller projects only after a real Reviewer `PENDING_COMMIT` and a source-bound passing validation receipt, records a derived pre/post-candidate receipt, extends authority only with packet-declared projection paths, and reuses the parent product validation rather than rerunning it for deterministic bookkeeping. Failed or missing requirement evidence, a stale Reviewer handoff, output-scope expansion, edited derived bytes, or a changed parent receipt fails closed. The DT-07 focused checkpoint passed **23 tests in 18.50 seconds (19.09 seconds wall clock)**; live projection `--apply --current-only` followed by `--check-all` changed no further bytes, and the Phase-0 generator check passed while preserving pinned snapshots.

### DT-08 — Reuse code, scaffold structural files and share conformance tests

**Primary paths:** canonical feature templates under `docs/templates/`, a small proposed scaffolding command under `scripts/`, existing feature tests/conformance infrastructure and usage examples.

Start with **one** recurring stateless backend feature shape based on a compatible accepted V3 implementation. Generate only the agreed structural shell: README, immutable manifest, strict configuration, lifecycle entry point, necessary contract placeholders, offline `_usage.py` shell and registration/evidence draft. Do not automatically invent business defaults, durable state or authorization policy.

Generate or propose the exact `pyproject.toml` feature entry-point registration when the feature shape requires one. Because `pyproject.toml` is a shared composition file, only the serialized integrator may apply that change during parallel delivery; draft workers record the required entry without concurrently editing the shared file.

Scaffolding must refuse overwrites and never mark a feature accepted. A generated shell is explicitly incomplete until real behavior, examples and acceptance assertions exist. Do not create passing placeholder tests or conceal missing implementations with `pass`, permissive mocks or “not applicable”.

Parameterize common manifest/configuration, mount/unmount, failure cleanup, provider removal/replacement and physical-removal checks using the existing harnesses. Keep owner-specific behavioral tests, especially session cleanup, cancellation, persistence, numerical causality and fail-closed behavior. Test count is determined by obligations—not a universal cap.

Before greenfield implementation, make a bounded reuse decision: retain correct current V3 behavior, adapt an approved normalized V2 donor when genuinely applicable, or implement what is missing. V3 contracts remain authoritative. Raw V2 copying or a new broad legacy audit is not authorized, and missing donor evidence alone is not a blocker. [R6]

For numerical tests, specify small independent golden values and boundary/causality cases; do not calculate expected values by reusing the same algorithm under test. For UI, preserve interaction/lifecycle tests rather than maximizing brittle snapshots.

**Acceptance:** Generated structure conforms to existing contracts; rerunning cannot overwrite work; incomplete behavior cannot gain a completed status; injected lifecycle/resource defects fail the shared harness; feature-specific invariants remain covered. Expand to stateful/UI shapes only after the first shape proves useful.

**Implementation checkpoint (9 September 2026):** Compact Task packets now select exactly one of `REUSE_EXISTING_FIRST`, `SCAFFOLD_STATELESS_BACKEND`, `IMPLEMENT_MISSING`, or `NO_AUTOMATIC_SCAFFOLD`. Automatic scaffolding is restricted to a missing Standard backend owner with a missing dedicated contract target; existing V3 owners route to reuse, while Critical, UI, stateful/provider-marked, ambiguous, and existing-contract work cannot use this first shell. `scripts/scaffold_stateless_feature.py` previews or atomically creates the approved stateless structure, refuses every overwrite, emits only an explicit entry-point proposal unless serialized integrator authority is present, and generates `IN_PROGRESS`/`FAIL` evidence plus fail-closed feature and usage behavior. The structural shape references accepted `FEAT-PLUG-DECLARE_MANIFESTS` without copying its business defaults or logic. Shared stateless factory/mount/withdrawal conformance now covers its generic lifecycle while feature-specific protocol, configuration, security, retained-file, and package assertions remain owned by the feature. An injected cleanup leak fails the shared harness. The final DT-08 focused checkpoint passed **10 tests in 0.39 seconds (1.00 second wall clock)**. The final broader workflow regression passed **251 tests in 188.82 seconds**; that duration is recorded as qualification cost, not an inner-loop target.

## 7. Change set D — Increase delivery throughput

### DT-09 — Experiment with conservative batching without merging feature ownership

**Primary paths:** execution-policy sections of `docs/dev/Phased_Feature_Implementation_Plan.md`, `AGENTS.md`, `.agents/GOALS.md`, goal/integration controllers and tests. Preserve feature cards and requirements.

The initial DT-09 implementation batches only preparation, reusable context, integration validation and operator pushes for **two or three** routine/standard features with stable contracts and a coherent integration boundary. It does not batch their implementation authority or acceptance. Do not batch authorization, resource accounting, persistence recovery or other critical features merely because they are adjacent in the plan.

Each feature retains its own folder, identity, requirement mapping, Task branch, review, tests, acceptance record, exactly one implementation commit and its required merge record. Preparation, reusable task-packet inputs, broader integration validation and pushes may be grouped where the current protocol permits. Any final deterministic aggregate-evidence commit must be separately authorized bookkeeping and must not masquerade as a feature implementation. Record every constituent commit and the tested batch/integration identity.

Do not amend the current clean-accepted-`main`, one-child-Task, branch, review, implementation-commit or acceptance rules in the initial experiment. Required predecessors remain accepted and contract-stable. Select batch members whose shared preparation or validation work can be reused without consuming an unaccepted internal predecessor.

A later provisional multi-feature candidate mode may be considered only as a separate versioned protocol proposal after DT-09 measurement. That proposal must independently specify authorization, path ownership, predecessor semantics, failure isolation, per-feature commits, evidence and rollback. It is not implicitly authorized by this plan.

Each constituent feature is reviewed and accepted through the current Task protocol. The grouped integration candidate then qualifies the combined accepted set before push or the next declared integration boundary. Shared aggregate evidence remains single-writer and deterministic. Scope cannot grow merely to fill a batch. A failed grouped integration gate blocks the batch action and creates a bounded correction obligation; it does not erase truthful prior Task evidence or relabel an unaccepted feature as complete.

Keep all 205 feature identities and registered scope. Do not rewrite the master plan into 30 giant untraceable tickets. Annotate a strategy-ready scheduling priority within the existing dependency graph, without deleting prerequisites or claiming the remaining platform is complete. The aim is earlier useful strategy work while the full roadmap remains intact.

**Acceptance:** Two/three features share reusable preparation and one broader integration/push cycle while retaining separate Task branches, reviews, implementation commits and acceptance records; integration failure blocks the grouped action; required edges are preserved; shared files have one writer; already correct behavior is not rewritten merely to create another acceptance commit.

**Implementation checkpoint (9 September 2026):** `delivery_batches` now freezes
explicit two/three-member Routine/Standard groups from source-pinned Task
packets. Preparation rejects Critical or blocked packets, baseline drift,
duplicate identities, exclusive-path collisions, and an unaccepted predecessor
inside the same group. Each child still traverses the ordinary Task protocol and
records its task/merge commits. After the last member is independently accepted,
the Goal controller runs one exact full integration profile and emits a
`PUSH_READY` batch record; failure blocks the grouped action without undoing
accepted children, and no remote push is performed. Deterministic tests prove
these mechanics. The required live two/three-feature product pilot remains
pending and is not claimed by this checkpoint.

### DT-10 — Benchmark bounded parallelism and adopt the measured path

**Primary paths:** existing opt-in parallel/goal/integration-queue behavior, local run configuration, existing run summaries; no new orchestration engine.

Enable two genuinely independent lanes first, then evaluate the existing three-lane capability. Use separate branches/worktrees and task packets with complete write footprints. Reserve shared files for the integrator. Predecessor eligibility must include accepted evidence, not merely a folder's existence or a draft promise.

On integration, refresh against the current base, regenerate shared projections, inspect the resulting delta and qualify the exact combined candidate. Retain independent review of changed behavior. Do not grandfather stale approval solely because Git applied a patch cleanly.

Budget machine resources across **all** lanes, test workers and UI builds. Do not multiply three agents by unrestricted `pytest -n auto` and assume more processes imply more throughput. Keep small focused suites serial when worker startup costs more than it saves.

Profile representative suites with whole-command timing and pytest durations. Benchmark one, two and four workers only on parallel-safe selections. Use isolated temporary databases, ports and filesystem paths; keep unsafe tests serial until corrected. `worksteal` balances uneven durations; `xdist_group` placement requires the appropriate `loadgroup` scheduling mode and is not automatic isolation. [W2, W5]

After profiling and verifying resource isolation, evaluate domain-based CI shards behind the single required aggregate `acceptance` status from DT-03. The aggregate must fail when any required shard is missing, cancelled, skipped unexpectedly or failed. Retain a serial or broader fallback for tests whose cross-domain dependencies make safe sharding inconclusive.

Use the first ten **accepted** pilot features, spanning UI interaction, ordinary service behavior and a critical stateful/security/numerical case. Compare within risk/complexity classes, not by treating every feature as identical. Do not retest an already accepted critical implementation as a made-up “new feature” just to fill the sample.

Record these fields in existing runtime summaries:

```text
task_or_batch_id, feature_ids, risk_tier, baseline, candidate
planning_elapsed, execution_elapsed, review_elapsed, closeout_elapsed
command_wall_time, integration_wait, correction_count, correction_causes
acceptance_result, escaped_regression_or_reopen
provider_reported_usage_if_available
allowance_before, allowance_after, other_concurrent_usage_known
```

Use nonoverlapping stage durations for totals; nested subprocess timings are diagnostic breakdowns, not extra elapsed time to add twice. Allowance percentage points are not tokens or a per-task billing measure when other work shares the allowance.

**Initial operating targets, not guaranteed results**

| Measure | Target / adoption rule |
|---|---|
| Warm targeted feature feedback | p95 at or below 30 seconds for an ordinary unit/component selection, excluding dependency installation and full builds. Profile and classify slower selections rather than hiding them behind a universal target. |
| Warm ordinary pre-commit | p95 at or below 20 seconds. |
| Warm ordinary pre-push | p95 at or below 60 seconds; no hidden comprehensive suite. |
| Administrative failure causing full product replanning | Zero after known cases are repaired. |
| Identical validation rerun only because the role changed | Zero on the standard path when a valid runner receipt exists. |
| Routine/standard planning + review + close-out share | Aim below 25% of elapsed time; investigate the residual, do not compromise critical review to hit a ratio. |
| Accepted behavior per hour and allowance | Must improve for comparable scope; actual measured values replace claims. |
| Safety/quality | No bypass of required acceptance, lost requirement mappings or regression evidence. A small clean pilot is not proof of zero long-term defects. |

Measure model choices only after the process changes. Compare allowance per accepted change, first-pass correctness and correction loops at the same risk tier; no model or effort setting is prescribed from unsupported names/performance claims.

**Adoption:** Keep improvements that increase accepted throughput without weakening evidence. Disable a slower/flakier parallel configuration rather than discarding the product architecture. Do not build a dashboard to answer what a small run-summary report can show.

**Implementation checkpoint (9 September 2026):** Schema-v4 policy, Goal
generation, state, migration, status, worktree creation, leasing and serialized
integration now accept either two or three canonical lanes while retaining a
maximum of three. Configuration recommends two first; the tracked runtime
configuration remains disabled and unchanged. Accepted Task runs emit canonical
throughput summaries with nonoverlapping measured role/close-out durations,
command and wait fields, correction evidence, acceptance result, and nullable
usage/allowance observations. `scripts/benchmark_pytest_workers.py` benchmarks
only explicit parallel-safe selections at 1/2/4 workers with `worksteal` for
parallel cases. Adoption remains `INSUFFICIENT_EVIDENCE` until ten comparable
accepted results exist, and any escaped regression forces `KEEP_SEQUENTIAL`.
CI sharding remains deferred.

### DT-11 — Freeze and deliver the strategy-ready milestone

**Primary paths:** `docs/dev/Phased_Feature_Implementation_Plan.md`, `docs/dev/evidence/dependency-schedule.json`, applicable owning READMEs, Goal selection/runtime inputs and a bounded milestone evidence record. Preserve the complete 205-feature roadmap and all existing feature identities.

Define the first useful strategy-development outcome as this reproducible vertical slice:

```text
Load historical data
  → define a strategy
  → run a deterministic backtest with explicit execution assumptions
  → inspect trades and performance
  → save and reproduce the experiment
```

Use the following as a candidate capability checklist, not as a second feature registry or a predetermined implementation list:

- local historical-data ingestion and retained bar/feed access;
- only the indicators required by the selected first strategy, rather than a mandatory generic indicator catalogue;
- strategy definition covering entry, exit and risk rules;
- deterministic bar or tick backtesting with documented execution assumptions;
- an inspectable trade ledger, P&L, drawdown and core performance metrics;
- a minimal results/equity inspection UI; and
- saved experiment identity and reproducible replay.

The derived dependency closure and owning contracts determine the actual participating features and operations. Omit a checklist item only when the frozen milestone contract proves it unnecessary; do not add unrelated indicators or platform extensions merely because they appear in this illustrative list.

Derive the smallest valid dependency closure from the frozen dependency schedule and owning contracts. Classify every required feature as already accepted, remaining implementation, operation-gated qualification or externally blocked. Freeze an explicit Goal selection for only the remaining necessary entries; do not delete prerequisites, weaken capability edges, expand the selection silently or mark unrelated V3 features complete.

State the milestone's exact inputs, supported offline/provider assumptions, expected outputs, deterministic replay identity, UI or public usage path, failure behavior and acceptance commands. Separate the desired four-to-eight-hour timebox from the evidence: estimate only after the closure and prepared task packets reveal the actual remaining scope. If the closure cannot fit the timebox, report the smallest honest runnable subset and the missing obligations rather than redefining V3 completion.

**Acceptance:** One bounded workflow loads retained historical data, executes a saved strategy through a deterministic backtest, exposes inspectable trades and performance, and reproduces the same experiment under its documented identity and assumptions. Every participating requirement and feature remains traceable; all deferred V3 work remains visibly open; no mocked or component-only evidence is claimed as real-provider qualification.

**Rollback:** Remove only the milestone annotation/Goal selection when its dependency derivation is wrong. Do not revert accepted product features or rewrite the master feature registry.

**Implementation checkpoint (9 September 2026):** The frozen six seed Tasks now
derive through the canonical schedule to **58** Tasks: **13 accepted** and **45
remaining**. The generated evidence separately identifies operation-gated and
externally blocked members, pins source/schedule hashes, and states offline
inputs, outputs, replay identity, failure behavior, public/UI path, and exact
qualification commands. The generated 45-entry Goal is dormant pending the
post-DT-06 product pilot and completion or resolution of the existing active
Goal. No Task was activated, no open V3 entry was closed, and the desired
four-to-eight-hour timebox is explicitly not treated as feasibility evidence.

## 8. Testing cadence after remediation

| Boundary | Required work | Not the default |
|---|---|---|
| Editing | Behavior-specific tests, relevant consumers, small failure/golden/lifecycle cases | Full coverage, full UI build after each edit, unrelated workflow tests. |
| Pre-commit | Formatting, lint, hygiene and secret detection | Full pytest/mypy or full app build. |
| Pre-push | Lightweight submission/scope consistency checks | Automatic comprehensive coverage on each eligible path. |
| Candidate acceptance | One source-bound integration profile before Reviewer; independent review plus selected adversarial checks; unchanged receipt reused through commit authorization | Repeating an identical gate merely because another role starts. |
| Batch boundary | Each child accepted independently, then one combined full gate before the grouped push or next declared integration boundary | Treating one batch gate as shared implementation, review or acceptance authority. |
| Remote CI | Candidate-appropriate integration/full qualification under the stable `acceptance` status after an authorized push | Claiming local acceptance proves remote status or branch protection. |
| Full regression/phase/release | Full code suite and coverage plus applicable browser/cross-domain and required real-provider/performance/fault/removal qualification at their explicit gates | Claiming mocked component tests certify live/provider behavior. |

A later dedicated test session expands stress, robustness and system scenarios. It is not the first time core behavior receives assertions. Preserve mandated lifecycle/removal evidence through shared harnesses instead of deleting it. Faster execution and less repetitive test authoring are separate optimizations. Parallel pytest remains serial by default until an explicit parallel-safe selection is benchmarked at one, two and four workers; unmeasured `-n auto` is not part of the standard cadence.

**Implementation checkpoint (9 September 2026):** The cadence is now encoded in
`AGENTS.md` and the feature pipeline, while regression tests lock its executable
boundaries. Ordinary pytest has no implicit coverage; pre-commit contains only
hygiene/format/lint/secret checks; pre-push calls the candidate-aware `affected`
profile; the Controller runs one source-bound integration gate before Reviewer;
CI exposes stable `acceptance`; and deliberate full qualification retains Python
coverage, UI build/tests and workflow checks. DT-09 batch qualification remains
post-child-acceptance and pre-push. Browser, provider, performance, fault and
physical-removal claims remain separate explicit phase/operation evidence.

## 9. Concrete command reference

These commands match the checked-in interfaces at the 9 September 2026
implementation checkpoint. They are operating examples, not authorization for
execution, Git mutation, network access, credentials, live-provider activity or
destructive work. Substitute only exact revisions and paths resolved from the
active Task packet and repository state. A command that writes an ignored report
is still a local mutation; a command that prepares runtime input does not activate
or authorize a Task or Goal.

### Local preflight and authorized remote refresh

```powershell
git status --short --branch
git diff --name-only
git diff --cached --name-only
git rev-parse HEAD
git config --show-origin --get core.hooksPath
git config --show-origin --get core.autocrlf
git rev-list --left-right --count HEAD...origin/main
```

A missing Git configuration key normally reports no configured value; that alone is not a workflow failure. The divergence command uses the currently available remote-tracking ref and must report when its freshness is unknown.

When a current remote ref is required, only an authorized operator/controller outside an active Planner, Executor or Reviewer invocation may run:

```powershell
git fetch origin
```

`fetch` does not modify product files, but it performs network I/O and mutates remote-tracking refs. It is therefore not a reasoning-role read-only command or implicit permission for reset, rebase, merge, stash or push.

### Focused Python validation and deliberate profiling

```powershell
# Focused development: explicit scope and no coverage instrumentation.
uv run --locked pytest --no-cov <resolved-test-path> -q

# Deliberate slow-test profiling still requires an explicit bounded selection.
uv run --locked pytest --no-cov <resolved-test-path> --durations=30 --durations-min=0.1

# Benchmark only a selection already judged parallel-safe; writes an ignored report.
uv run --locked python scripts/benchmark_pytest_workers.py <resolved-test-path> --repeat 3 --report .dev/pytest-worker-benchmark.json

# Run only the measured bounded winner; keep shared-resource tests serial.
uv run --locked pytest --no-cov -n <measured-2-or-4> --dist=worksteal <resolved-test-path>

# Comprehensive coverage at its designated gate.
uv run --locked pytest --cov=app --cov-report=term-missing --cov-fail-under=80
```

Ordinary pytest no longer inherits coverage or HTML generation. The explicit
comprehensive command retains the project coverage floor without producing an
HTML report. Do not pass a focused subset to this global-coverage command and
interpret the result as whole-application qualification.

### Existing UI scripts

```powershell
Push-Location app/ui
# Install from the existing package lock when setup/lock state requires it.
npm ci
npm run test -- <resolved-test-path>
npm run typecheck
# Full UI validation/build only at the appropriate broader boundary.
npm run test
npm run build
# Local-ASGI browser journey only at an applicable browser/phase gate.
npm run e2e
Pop-Location
```

The current Playwright configuration uses the repository's local ASGI harness;
it is browser evidence, not external broker/provider qualification. In
automation, check and propagate every native process exit code because
PowerShell does not make a failed native command halt an entire script
automatically. A Python validator invoking npm must resolve the
platform-appropriate executable and use the UI working directory. Do not
reinstall npm dependencies after every source edit.

### Validation interface

```powershell
# Read-only route explanation for the outgoing local delta.
uv run --locked python scripts/ci_check.py --profile affected --base origin/main --head HEAD --explain

# Ordinary pre-push-equivalent affected validation.
uv run --locked python scripts/ci_check.py --profile affected --base origin/main --head HEAD

# Clean materialized candidate integration.
uv run --locked python scripts/ci_check.py --profile integration --base <accepted-main-commit> --head <candidate-commit>

# Controller-owned frozen dirty-worktree integration.
uv run --locked python scripts/ci_check.py --profile integration --base <accepted-main-commit> --head <source-head> --reviewed-worktree

# Deliberate full code qualification.
uv run --locked python scripts/ci_check.py --profile full

# Optional diagnostic report and complete ignored logs; not a reusable receipt.
uv run --locked python scripts/ci_check.py --profile affected --base origin/main --head HEAD --report .dev/validation-report.json --log-dir .dev/validation-logs
```

These profiles are implemented. Missing or unknown scope fails or widens
conservatively and never silently certifies an empty test selection. The
`integration` invocation for a frozen dirty worktree is Controller-owned and
adds `--reviewed-worktree`; manual editing uses explicit focused commands rather
than manufacturing reusable acceptance evidence. A `--report` file is a
diagnostic observation; only the Controller creates and verifies a source-bound
reusable validation receipt.

### Hook verification

```powershell
# Operates on the applicable staged files using the pre-commit boundary.
uv run --locked pre-commit run --hook-stage pre-commit

# Runs the configured candidate-aware affected pre-push boundary.
uv run --locked pre-commit run --hook-stage pre-push
```

Do not add `--no-verify` to the normal development reference. A bypass requires
an explicit exceptional decision and equivalent protection; it is not the
solution to slow validation.

### Task and Goal inspection or preparation

```powershell
# Read-only tracker and controller health/status inspection.
uv run --locked python .agents/make_task.py --list
uv run --locked python .agents/orchestrator.py doctor
uv run --locked python .agents/orchestrator.py goal-status

# Runtime-input generation: writes .agents/task.toml but does not activate it.
uv run --locked python .agents/make_task.py <task-id>

# Runtime-input generation: writes .agents/goal.toml but does not activate it.
uv run --locked python .agents/make_goal.py --entries <task-id-a> <task-id-b> --parallelism 1
uv run --locked python .agents/make_goal.py --entries <task-id-a> <task-id-b> --parallelism 2

# Conservative DT-09 preparation/integration grouping; each child remains independent.
uv run --locked python .agents/make_goal.py --entries <task-id-a> <task-id-b> --parallelism 1 --delivery-batch <task-id-a> <task-id-b>
```

Goal preparation with `--parallelism 3` is also supported, but two lanes are the
first measured trial. Generating Task/Goal input does not satisfy execute or
commit gates. Activation, resume, integration, cancellation and recovery use the
validated orchestrator state machine and their applicable owner authority; they
are intentionally not reduced to copy-paste shortcuts here.

### Deterministic remediation utilities

```powershell
# Safe evidence output discovery and current-projection drift check.
uv run --locked python scripts/project_feature_evidence.py --list-outputs
uv run --locked python scripts/project_feature_evidence.py --check-all

# Preview only; actual scaffold application requires packet and write authority.
uv run --locked python scripts/scaffold_stateless_feature.py --task-packet <task-packet.json> --preview

# Verify the frozen strategy-ready closure and generated Goal without activation.
uv run --locked python scripts/derive_strategy_ready_milestone.py --check

# Write a compact ignored throughput/adoption report from accepted run summaries.
uv run --locked python .agents/throughput.py --runs-dir .agents/runs --limit 10 --report .dev/throughput-report.json
```

Evidence/scaffold `--apply`, serialized registration, and generated Task/Goal
activation are mutating governed operations. Do not substitute their preview or
drift-check commands for reviewed requirement evidence.

### Explicit phase or operation qualification

```powershell
# Browser journey against the repository's bounded local ASGI harness.
Push-Location app/ui
npm run e2e
Pop-Location

# Physical provider-removal/reinstall qualification; run only at its governed gate.
uv run --locked python scripts/architecture/provider_deletion_matrix.py --all --reinstall --report .dev/provider-removability.json
```

These commands are intentionally outside ordinary editing and pre-push. External
provider qualification requires its own verified environment, credentials and
authority; neither the local Playwright harness nor the physical package-removal
matrix proves a live broker workflow.

**Implementation checkpoint (9 September 2026):** Every referenced CLI shape was
verified against its checked-in `--help` interface. The strategy-ready generated
closure and feature-documentation checks passed. No Task/Goal generation or
activation, evidence/scaffold application, hook, validation suite, browser,
provider, Git or network mutation was performed for this documentation update.
An additional read-only `project_feature_evidence.py --check-all` diagnostic
reported drift in the five live aggregate projections while Git reported no
content change for those files. This bounded task did not overwrite them without
the required reviewed projection request; the discrepancy remains visible for
separate diagnosis or the next authorized acceptance projection.

## 10. Exit criteria for the remediation

Implementation, effectiveness and optional adoption are different closure claims.
Passing workflow self-tests proves mechanism behavior; it does not prove that a
new product feature was delivered faster. The document uses these states:

| State | Meaning |
|---|---|
| `VERIFIED_IMPLEMENTATION` | Checked-in behavior is covered by deterministic regression or repository evidence. |
| `PENDING_PRODUCT_PILOT` | The mechanism exists, but a genuinely new accepted product feature has not yet supplied the required outcome evidence. |
| `PENDING_ADOPTION_SAMPLE` | The mechanism remains disabled or provisional until the required comparable accepted outcomes exist. |
| `PENDING_EXTERNAL_ADMINISTRATION` | Completion requires separately authorized remote configuration or another external-state change. |
| `EVIDENCE_DRIFT` | A deterministic check reports disagreement that must be diagnosed without silently overwriting evidence. |
| `DEFERRED_BY_OWNER` | An optional intervention was explicitly declined or postponed without being represented as adopted. |
| `COMPLETE` | Every mandatory local and measured-effectiveness criterion below is satisfied; external claims are made only when separately verified. |

### 10.1 Current exit matrix

| Criterion | Required evidence | Current state |
|---|---|---|
| Ordinary pytest has no implicit coverage or HTML generation. | Pytest configuration plus runner regression. | `VERIFIED_IMPLEMENTATION` |
| Pre-commit excludes full pytest, project-wide mypy and UI builds. | Hook configuration plus cadence regression. | `VERIFIED_IMPLEMENTATION` |
| Pre-push uses candidate-aware affected validation and widens unknown scope. | Hook, router and runner regressions. | `VERIFIED_IMPLEMENTATION` |
| One source-bound integration run can survive a role handoff without an identical rerun. | Receipt reuse, input-drift and forged-record regressions. | `VERIFIED_IMPLEMENTATION`; product pilot remains pending. |
| Known administrative corrections avoid unnecessary Planner reconstruction. | Classified bounded retry regressions plus measured product runs. | `PENDING_PRODUCT_PILOT` |
| A fully bound Routine/Standard packet can avoid fresh exploratory planning while Critical or ambiguous work retains it. | Packet/risk/stale-source regressions plus measured product runs. | `PENDING_PRODUCT_PILOT` |
| Failing, unreviewed, unauthorized, stale or unqualified candidates fail closed. | Controller, authority, receipt, projection and close-out regressions. | `VERIFIED_IMPLEMENTATION` |
| Shared bookkeeping is projected only from reviewed acceptance evidence and is idempotent. | Projection regressions and a clean live `--check-all`. | `EVIDENCE_DRIFT`: five live aggregate projections currently disagree with derived bytes. |
| Existing feature identities, requirements and open V3 scope remain truthful. | Plan, dependency schedule and evidence validators. | `VERIFIED_IMPLEMENTATION` |
| Three representative post-DT-06 features demonstrate the remediated path. | One new UI, one ordinary service and one Critical accepted run with complete timings/corrections. | `PENDING_PRODUCT_PILOT` — 0/3. |
| DT-10 produces an evidence-based lane decision. | Ten comparable accepted summaries spanning UI, ordinary service and Critical work, including sequential and parallel evidence. | `PENDING_ADOPTION_SAMPLE` — zero canonical summaries currently present. |
| Remote CI enforcement or branch protection is claimed only after inspection. | Current remote settings and required-status evidence. | `PENDING_EXTERNAL_ADMINISTRATION` |
| Strategy-ready delivery is scheduled from its frozen truthful closure. | Valid generated milestone plus satisfied activation prerequisites. | Defined and verified, but dormant. |

The current overall verdict is:

```text
IMPLEMENTATION DEPLOYED — EFFECTIVENESS NOT YET DEMONSTRATED
```

This is not `COMPLETE`, and it is not evidence of a universal five-to-fifteen
minute feature rate, an allowance reduction, or completion of V3 within eight
hours.

### 10.2 Mandatory completion gate

Mark the remediation `COMPLETE` only when all of the following are true:

1. The five-projection discrepancy is resolved by a reviewed projection or is
   proven and repaired as a validator defect; no evidence is overwritten merely
   to make the check green.
2. Three genuinely new representative product features are independently
   accepted through the remediated path: one UI interaction/presentation
   feature, one ordinary stateless service feature, and one Critical stateful,
   security, concurrency or numerical feature.
3. Those runs record nonoverlapping planning, execution, review and close-out
   durations, command time, integration wait, correction causes, acceptance
   outcome and available usage/allowance observations.
4. Administrative replanning is zero for the repaired mechanical cases, and no
   required test, coverage floor, review, requirement mapping, authorization or
   feature scope is lost.
5. Each throughput comparison uses reasonably similar historical scope and
   records limitations rather than converting an allowance percentage into a
   token count.
6. DT-10 is closed either by the required ten-result decision (`ADOPT_2`,
   `ADOPT_3`, or `KEEP_SEQUENTIAL`) or by an explicit owner decision to defer
   optional parallel adoption while parallelism remains disabled. An
   `INSUFFICIENT_EVIDENCE` result is not an adoption decision.
7. Any statement that remote CI or branch protection enforces acceptance is
   backed by a separately authorized inspection of the actual remote state.

Local remediation completion does not require changing remote administration,
but it must continue to label remote enforcement pending. Conversely, remote CI
success does not replace the local product pilot or retroactively grant local
Task acceptance.

### 10.3 Forecasting after measurement

Forecast remaining work only from accepted outcomes grouped into UI interaction,
ordinary service and Critical risk/complexity classes. Use observed distributions
rather than one headline average. Keep reasoning-stage elapsed time, command wall
time and integration wait nonoverlapping; account for dependency critical paths,
effective measured concurrency and serialized integration. Allowance percentages
remain observations when other concurrent usage is unknown.

Do not extrapolate from Task 1.16 alone, a theoretical three-worker maximum,
generated line counts, or a prototype video. If the sample does not support a
stable estimate, report the uncertainty and continue measuring instead of
inventing a completion date.

### 10.4 Ordered closure actions

1. Diagnose the five live-projection discrepancies without applying unreviewed
   evidence changes.
2. Run and accept the three representative post-DT-06 product features.
3. Record the continuation decision for evidence generation, scaffolding,
   batching and parallelism from those measured outcomes.
4. Accumulate the DT-10 ten-result sample only if parallel evaluation remains
   worthwhile; otherwise record `DEFERRED_BY_OWNER` and keep it disabled.
5. Activate the dormant strategy-ready Goal only after its documented pilot and
   active-Goal prerequisites are satisfied.
6. Inspect or change remote publication/branch protection only under separate
   owner authorization.

## 11. Implementation handoff

The remediation mechanisms are implemented. This section hands off the remaining
operational proof, adoption and closure work; it does not authorize the completed
DT work orders to be rerun.

### 11.1 Implemented baseline

| Scope | Accepted commit |
|---|---|
| DT-01 | `5faf73fe` |
| DT-02A and DT-02B | `6420d7e8` |
| DT-03 | `311e6dce` |
| DT-04, DT-05 and DT-06 | `82661187` |
| DT-07 and DT-08 | `a2575997` |
| DT-09, DT-10 and DT-11 | `d64ea9a3` |

These commits establish implementation evidence only. They do not satisfy the
post-DT-06 product pilot, the optional DT-10 adoption sample, remote
administration or the complete remediation exit gate by themselves.

### 11.2 Authority and sequencing

The handoffs below are bounded work specifications, not execute, commit, merge,
push, Goal-activation, remote-administration, credential, destructive-operation
or live-provider authorization. Each handoff must use the applicable repository
workflow, exact owner gates, current repository truth and a fresh source-bound
packet. Preserve unrelated user work and never manufacture acceptance, timing,
coverage, remote-enforcement or allowance evidence.

Run the mandatory work in this order:

1. Reconcile current evidence and Goal state.
2. Deliver and accept the three representative product-pilot features.
3. Evaluate the measured pilot and record the continuation decisions.
4. Close or explicitly defer the optional DT-10 parallel-adoption decision.
5. Activate the strategy-ready Goal only when its prerequisites are true.
6. Perform remote administration only under separate owner authority.
7. Apply the Section 10 completion gate.

### 11.3 Preliminary reconciliation handoff

> **Evidence and Goal reconciliation:** Diagnose the five aggregate evidence
> projections currently reported by `project_feature_evidence.py --check-all`
> without applying generated output first. Determine whether each difference is
> caused by stale accepted evidence, a projection defect, serialization or line
> endings, or genuine source drift. Separately reconcile the running Goal whose
> persisted handoff still selects Task 1.17 even though the implementation
> tracker marks Task 1.17 `PROVED_COMPLETE`. Do not overwrite evidence, edit Goal
> runtime state, skip a child or activate another Goal during diagnosis. Present
> exact findings and a path-bounded correction plan for independent approval and
> review. After an authorized correction, require an idempotent clean
> `--check-all`, consistent tracker/Goal state and preserved accepted history.

Evidence correction and Goal-state correction may share one investigation, but
they remain distinct mutations and must each have explicit path authority. A
clean generated diff is not proof that the underlying accepted feature evidence
is valid.

### 11.4 Three-feature product-pilot handoffs

Select genuinely new work after prerequisite and packet validation. Do not
retroactively count a remediation-framework change or an already accepted
feature as a pilot result.

> **UI pilot:** Deliver one bounded UI interaction or presentation feature
> through the remediated path. Generate a fresh packet, confirm Routine,
> Standard or Critical classification from actual scope, exercise the changed
> interaction and affected consumers, retain applicable accessibility and
> authorization behavior, independently review it and record complete
> nonoverlapping stage timings and correction causes.

> **Ordinary-service pilot:** Deliver one bounded ordinary stateless service
> feature through the remediated path. Use a source-bound packet and the
> scaffolder only if its eligibility checks pass. Prove its public happy path and
> critical unavailable or fail-closed behavior with focused tests, validate
> affected contracts and consumers, independently review it and record complete
> nonoverlapping stage timings and correction causes.

> **Critical pilot:** Deliver one stateful, security, authorization, concurrency
> or numerical feature through the Critical route. Retain substantive planning,
> adversarial independent review, failure-path testing and comprehensive
> integration acceptance. Task 1.18, `FEAT-ORCH-MANAGE_JOBS`, is a candidate
> because it owns persistent job identity, atomic acceptance, idempotency and
> recovery semantics; use it only if a fresh validated packet confirms its
> readiness and classification.

For every pilot, record planning, execution, review and close-out durations;
command wall time; integration wait; correction category; acceptance outcome;
and any available usage or allowance observation. Do not double-count
overlapping time or translate an allowance percentage into a token count.
Required tests, the coverage floor, independent review, requirement mapping,
authorization and complete feature scope remain intact.

### 11.5 Pilot evaluation and continuation handoff

> **Evaluate the post-DT-06 pilot:** Compare each accepted pilot with reasonably
> similar historical work in the same risk/complexity class. Report time spent
> on engineering reasoning, command execution, integration waiting and
> administrative correction separately. Confirm whether the repaired mechanical
> cases caused zero administrative replanning and whether any defect or required
> evidence escaped the faster path. Record explicit continuation, revision or
> suspension decisions for prepared packets, deterministic evidence projection,
> eligible stateless scaffolding and coherent delivery batching.

Three results are a checkpoint, not a statistically stable universal feature
rate. Preserve uncertainty and continue class-based measurement when the sample
does not support a forecast.

### 11.6 DT-10 parallel-adoption handoff

Parallel execution remains disabled until this handoff produces sufficient
accepted evidence or the owner explicitly defers it.

> **Evaluate bounded parallel adoption:** Accumulate ten canonical comparable
> accepted-run summaries spanning UI, ordinary-service and Critical work and
> including relevant sequential and bounded parallel observations. Benchmark
> accepted features per wall-clock hour, correction/replay rate, integration
> wait, collision/staleness rate and allowance observations. Produce exactly one
> supported decision: `ADOPT_2`, `ADOPT_3` or `KEEP_SEQUENTIAL`. If the owner
> declines the optional sample, record `DEFERRED_BY_OWNER` and keep parallelism
> disabled. `INSUFFICIENT_EVIDENCE` is a valid interim finding but is not an
> adoption decision.

The first parallel trial uses two lanes. Three lanes require additional measured
benefit and must retain disjoint leases, fresh review after refresh and serialized
acceptance.

### 11.7 Strategy-ready Goal handoff

> **Prepare the strategy-ready delivery Goal:** Verify the frozen milestone and
> generated Goal definition, complete the mandatory product pilot, and reconcile
> any existing active Goal before preparation or activation. Activate the Goal
> only through the deterministic Goal workflow and applicable owner authority.
> Preserve dependency order, independent child acceptance and every remaining V3
> feature outside the milestone as truthful deferred scope rather than marking it
> complete.

The generated strategy-ready artifact is a scheduling input, not proof of
implemented strategy capability and not permission to supersede an active Goal.

### 11.8 Remote-administration handoff

> **Verify remote enforcement:** Under separate owner authorization, refresh and
> inspect current remote state, CI status, branch protection and required checks.
> Repair or enable remote acceptance enforcement only through the repository
> administration surface and verify the result from the remote system. Do not
> infer protection from local tests, a checked-in CI file or a stale
> remote-tracking ref. Fetch, push and branch-protection changes remain separate
> operations with their own authority.

### 11.9 Final remediation closure handoff

> **Close the remediation:** Re-evaluate every item in the Section 10 exit matrix
> from current repository, accepted-run and authorized remote evidence. Mark the
> remediation `COMPLETE` only when every mandatory local and measured-
> effectiveness criterion is satisfied and every external claim is independently
> verified. Otherwise retain the precise pending, drift, deferred or external-
> administration state and name the next bounded action.

Closure updates documentation truth only after the underlying evidence exists;
editing the status label is never a substitute for that evidence.

## 12. Sources and audit boundaries

This section distinguishes historical diagnosis, accepted implementation,
working-tree validation and still-unproved outcomes. A source can support only
the class of claim assigned to it.

### 12.1 Evidence classes

| Class | Meaning and boundary |
|---|---|
| Supplied analysis | User-provided reports retained as diagnostic context; not independently reproduced unless separately stated. |
| Diagnostic baseline | Repository or remote state observed before remediation; not evidence of current behavior. |
| Accepted implementation | Behavior and regression evidence contained in an identified Git commit; not proof of later product throughput. |
| Working-tree validation | Commands executed against exact local bytes that are not yet represented by a final documentation commit. |
| Runtime observation | Local ignored controller or report state that can become stale and is not permanent product truth. |
| Remote observation | External state valid only for the inspected repository and time; it requires refresh before a current claim. |
| Operating hypothesis | A target or forecast that requires representative accepted product outcomes before adoption. |

### 12.2 Supplied analysis

**[S1]** `Pasted markdown(8).md`, supplied in this conversation, contains the
original performance complaint and three agent analyses. The reported Task 1.16
duration, allowance change, five iterations, defect findings and approximate
time allocation came from those reports. They were not independently
reconstructed here from a complete monotonic timing trace and are not canonical
throughput measurements.

### 12.3 Original diagnostic baseline

The following references describe the pre-remediation repository at commit
`a32a46ad5c3407bdb7b68bf8dc270d327b6e7625`, except R9. They remain historical
evidence for why the work was proposed and must not be read as descriptions of
the implemented DT-01 through DT-11 behavior.

Historical citation base:

```text
https://github.com/haruperi/HaruQuantAI/blob/a32a46ad5c3407bdb7b68bf8dc270d327b6e7625/
```

| Reference | Historical repository path / observation |
|---|---|
| R1 | `.pre-commit-config.yaml`: original pre-commit/pre-push stages, broad trigger regexes and secret baseline. |
| R2 | `pyproject.toml`: original implicit pytest coverage/HTML defaults, branch coverage and 80% floor, mypy scope/cache and installed development dependencies. |
| R3 | `scripts/ci_check.py`: original serial complete command list, unconditional workflow checks and nested uv invocation. |
| R4 | `.github/workflows/ci.yml`: original Windows runner, Python gates, separate provider-disable matrix and absence of npm checks. |
| R5 | `app/ui/package.json`: available typecheck, Vitest, build and Playwright scripts. |
| R6 | `AGENTS.md`, §§1–2.7 at the baseline: authority, architectural boundaries, donor policy, Task state machine, exact owner gates and role contracts. |
| R7 | `docs/dev/Phased_Feature_Implementation_Plan.md`, §§1–2.4 at the baseline: complete scope, sequencing, evidence, DOD-F and self-referential-hash avoidance. |
| R8 | `scripts/generate_phase0_evidence.py` at the baseline: existing deterministic evidence parsing and pinned historical references. |
| R9 | GitHub branch response for `main`, read 9 September 2026: the response reported `protected: false` and required-check enforcement off. |

The original inspection confirmed controller, Goal and integration infrastructure
but was not a complete product/runtime audit. The R9 remote observation is
historical: neither it nor a checked-in CI file establishes current remote
enforcement. A fresh remote claim requires separately authorized inspection.

### 12.4 Accepted remediation implementation

| Reference | Commit | Implemented scope and principal evidence |
|---|---|---|
| I1 | `5faf73fe` | DT-01: deterministic generated-output discovery, coordination-byte normalization, bounded Git-identity secret filtering and focused workflow/security regressions. |
| I2 | `6420d7e8` | DT-02A/DT-02B: fast ordinary pytest defaults, explicit validation profiles, candidate/dependency-aware routing and runner/router regressions. |
| I3 | `311e6dce` | DT-03: source-bound local integration acceptance, affected pre-push routing, UI CI qualification and removability gates. |
| I4 | `82661187` | DT-04/DT-05/DT-06: classified correction routing, risk-tiered task packets, reusable exact-input validation receipts and deterministic close-out. |
| I5 | `a2575997` | DT-07/DT-08: deterministic evidence projection, guarded stateless-feature scaffolding, shared conformance support and associated regressions. |
| I6 | `d64ea9a3` | DT-09/DT-10/DT-11: conservative delivery batches, bounded parallel-policy support, canonical throughput summaries and generated strategy-ready closure. |

These commits prove that the mechanisms and their deterministic regressions were
implemented. They do not prove a universal time reduction, a quota reduction,
parallel benefit, strategy readiness of unimplemented product behavior or
remediation effectiveness in new feature delivery.

### 12.5 Post-implementation working-tree validation

The documentation-completion working tree was based on
`d64ea9a3ac9e9054cdef04bf32ba5a70e2fd161a`. The following commands or gates were
executed during Sections 8–11 work:

| Reference | Validation result |
|---|---|
| V1 | Focused remediation regression selection: 42 tests passed. |
| V2 | `scripts/ci_check.py --profile full`: 2,408 Python tests with the project coverage floor, 837 UI tests plus production build, and 268 workflow tests plus workflow self-test passed. |
| V3 | `scripts/validate_feature_docs.py`: all 47 feature READMEs matched runtime truth. |
| V4 | `scripts/derive_strategy_ready_milestone.py --check`: generated strategy-ready closure check passed. |
| V5 | Section 9 command interfaces were checked against their implemented `--help` surfaces without activating a Task/Goal or applying evidence/scaffolding. |
| V6 | Section 11 implementation commit references resolved and its obsolete future-work instructions were absent. |

The complete validation emitted existing Python `ResourceWarning` and React
warning output. Those warnings were observed but were outside the approved
documentation/cadence scope and are not represented as fixed. V1–V6 are
working-tree/session evidence until a later commit records the changed document
bytes; this document deliberately does not attempt to predict its own commit
hash.

### 12.6 Outstanding time-bound observations

At the 9 September 2026 documentation checkpoint:

- `project_feature_evidence.py --check-all` reported byte drift in
  `contract-bindings.json`, `feature-baseline.json`, `path-bindings.json`,
  `requirement-status.json` and `usage-bindings.json`. The diagnostic did not
  apply generated replacements.
- The ignored Goal runtime reported `RUNNING` and retained a handoff to Task
  1.17 while the implementation tracker marked Task 1.17 `PROVED_COMPLETE`.
  This requires reconciliation, not manual state rewriting.
- The representative post-DT-06 product pilot remained 0/3.
- No canonical ten-result DT-10 adoption sample was present.
- Parallel execution remained disabled.
- Current remote CI and branch-protection enforcement remained unverified.

These are diagnostic observations, not durable feature status. Recheck their
exact source state before using them to authorize or close later work.

### 12.7 Generated, runtime and acceptance evidence boundaries

- Reviewed feature acceptance manifests and their source-bound evidence are the
  inputs to shared aggregate projections. A projection cannot override its
  authoritative inputs merely because generation is deterministic.
- Matching generated bytes prove reproducibility of the projection, not product
  correctness or satisfaction of an unverified requirement.
- `.agents/runs/`, `.agents/goals/`, task packets, validation receipts and
  ignored reports are runtime artifacts. Their validity depends on exact run,
  source, candidate, configuration and environment identity.
- Runtime observations must be reconciled before promotion into durable
  documentation. Copying ignored state into a tracked file is not reconciliation.
- A command result, report or receipt supplies evidence only for its declared
  inputs and never grants execute, commit, merge, push or acceptance authority.
- Historical accepted evidence is not rewritten to make a current projection
  green; repairs preserve provenance and receive their own review.

### 12.8 External tool documentation

These sources informed the implementation design. They explain upstream tool
semantics but are not HaruQuantAI acceptance evidence:

```text
[W1] pytest-cov configuration
https://pytest-cov.readthedocs.io/en/latest/config.html

[W2] pytest-xdist distribution modes
https://pytest-xdist.readthedocs.io/en/stable/distribution.html

[W3] GitHub required status checks and skip behavior
https://docs.github.com/en/pull-requests/how-tos/merge-and-close-pull-requests/troubleshooting-required-status-checks

[W4] uv locking and syncing
https://docs.astral.sh/uv/concepts/projects/sync/

[W5] pytest invocation and duration reporting
https://docs.pytest.org/en/stable/how-to/usage.html

[W6] pre-commit stages and filename handling
https://pre-commit.com/
```

### 12.9 Claims not established by this remediation

The evidence above does not establish:

- A universal five-to-fifteen-minute feature rate or an 80% allowance reduction.
- Completion of all V3 scope in four or eight hours.
- A conversion from displayed allowance percentage to model token usage.
- Production readiness of features still open in the implementation tracker.
- Live-trading safety, profitability, broker fills or provider qualification.
- Current remote branch protection or required-status enforcement.
- A throughput benefit from two or three parallel lanes.
- Strategy-ready product behavior solely because its dependency closure was
  generated.
- Complete remediation effectiveness before the Section 10 product-pilot and
  adoption decisions are satisfied.

### 12.10 Self-reference and future audit updates

This document does not embed the hash of a future commit containing its own
changed bytes. Git history or a later evidence record may identify that commit
after it exists. Future audit updates must retain historical observations as
historical, append or supersede them with dated source identities, record the
exact commands and limitations, and never rewrite an earlier hypothesis as
though it had already been measured.
