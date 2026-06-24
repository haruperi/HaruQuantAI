## Phase 0 Project Scaffold and CI Foundation

### Goal

Create the repository execution foundation before domain implementation begins, so every later phase uses the same project structure, dependency policy, quality gates, environment conventions, and release workflow.

Task inventory: calculated from the checkbox tasks in this section.

### Dependency Files and Functionality

Required functionality:

- Project scaffold and Python package baseline.
- Ruff, mypy, pytest, coverage, and pre-commit quality gates.
- Environment template and secure configuration conventions.
- CI workflow or equivalent local CI command runner.
- Migration, backup, restore, and release checklist ownership.

### Functionality to Implement

Tasks are grouped by domain functionality. Each task is actionable; related original requirements are preserved as sub-bullets where merged.

#### Project scaffold and package baseline

- [ ] Create the approved minimal repository scaffold before domain phase work begins, with Python project metadata in `pyproject.toml` under the approved Python version policy and package discovery configured so `app` imports reliably in tests, scripts, API runtime, and agent runtime.
  - Approved minimal repository scaffold
  - `pyproject.toml` Python version policy
  - Package discovery for `app` across tests/scripts/API/agent runtime
- [ ] Create `.gitignore` entries for virtual environments, caches, local data, secrets, logs, reports, and generated artifacts.
- [ ] Create `.env.example` with safe placeholder values only, and audit scaffold files to ensure no real credentials, broker tokens, API keys, private payloads, account numbers, or trading secrets are present.
  - `.env.example` placeholders only
  - No real secrets in scaffold files
- [ ] Create the lean documentation set: `PROJECT.md`, `ARCHITECTURE.md`, `MODULES.md`, `ROADMAP.md`, and `BUILDER.md`.
- [ ] Write the Builder approval workflow into `AGENTS.md` and `docs/BUILDER.md`, including an explicit statement that this implementation plan is not blanket approval for repository edits.
  - Builder approval workflow preserved in `AGENTS.md` / `docs/BUILDER.md`
  - Plan is not blanket approval for repository edits

#### Quality gates and CI

- [ ] Configure mypy strict as the canonical static typing gate.
- [ ] Configure pytest as the canonical unit and usage-test runner.
- [ ] Configure coverage to enforce at least 80% per affected package and project where applicable.
- [ ] Configure pre-commit to run formatting, linting, type, and test-adjacent safety checks appropriate for local development.
- [ ] Create a GitHub Actions workflow (or documented local equivalent) that runs the same quality gates and can run without optional broker SDKs, notification clients, LLM providers, or UI dependencies installed.
  - CI workflow or documented local equivalent
  - Gates run without optional dependencies installed
- [ ] Document how to run fast tests, full tests, usage examples, and CI checks locally.

#### Migrations, backups, releases, and deployment modes

- [ ] Define migration ownership and convention: which phase owns database migrations and schema versioning, the migration naming convention, and the rollback expectation for future database-backed phases.
  - Migration/schema-versioning ownership assigned before persistence code is implemented
  - Migration naming convention and rollback expectation
- [ ] Define local backup and restore expectations for data, audit, reports, optimization artifacts, and trade journals.
- [ ] Define deployment modes (local development, test, simulation, paper, shadow, live-read-only, micro-live, full-live) and require that production/live modes activate only via explicit configuration, never from safe defaults.
  - Deployment mode list
  - Live/production modes require explicit configuration, never default-activated
- [ ] Create a release checklist covering tests, docs, changelog, migration notes, rollback path, and operator risk review.
- [ ] Create a dependency policy documenting required, optional, broker-specific, UI-specific, and LLM-provider-specific dependencies, and document that optional-dependency imports remain safe while missing optional dependencies fail only when the dependent feature is used.
  - Dependency policy by category (required/optional/broker/UI/LLM)
  - Optional-dependency import-safety and lazy-failure behavior

#### Documentation and governance baseline

- [ ] Create a changelog discipline requiring every project-meaning change to be recorded.
- [ ] Document the phase execution order: the final phase dependency order, the sprint-pack execution rule, and that the Core Contracts phase is mandatory before cross-domain model duplication begins.
  - Final phase dependency order
  - Sprint-pack execution rule
  - Core Contracts phase mandatory before cross-domain model duplication
- [ ] Document the fail-closed principle for risk, live, trading, auth, event, and approval workflows.
- [ ] Document the service-ownership boundary: API routes, UI screens, and conversation flows must delegate to governed services and must not own domain decisions.
- [ ] Document the live-trading staged promotion path through read-only, paper, shadow, micro-live, and full-live modes. (Links to deployment-mode definition above.)
- [ ] Define and enforce the Sprint-Pack Execution Boundary as mandatory: only one approved sprint pack or explicitly approved phase slice may be implemented at a time, and the next sprint pack may not start until the current approved scope has at least 80 percent coverage for each affected file and package, unless an owner-approved documented exception exists.
  - One active approved sprint pack/phase slice at a time
  - 80% coverage gate per affected file/package before next sprint pack, unless documented exception
- [ ] Define the cross-phase readiness gate: Live, UI/API, Research, and Conversation phases may not implement governed mutation behavior until their upstream Data, Indicator, Strategy, Risk, Trading, Simulation, Analytics, and Optimization readiness gates are satisfied or explicitly deferred with owner approval.
- [ ] Define phase-advancement blockers: unresolved safety blockers, stale active documentation, missing changelog entries, skipped usage examples, failing import-safety checks, or unreviewed public contract changes each block phase advancement.
- [ ] Define checklist-completion evidence requirements: completion must cite evidence references (command summaries, coverage results, usage example status, docs updated, risk decisions, rollback path); unchecked boxes may not be marked complete from intent alone.
- [ ] Document that velocity pressure, checklist fatigue, or partial completion may not be used as rationale to bypass safety gates, coverage gates, approval gates, or live-trading promotion gates.

### Unit Tests Required

```text
tests/unit/scaffold/
tests/unit/scripts/
```

Test coverage:

- [ ] Write tests verifying project imports are side-effect free before optional dependencies are installed.
- [ ] Write tests verifying the local CI script exposes the approved quality-gate order.
- [ ] Write tests verifying `.env.example` contains placeholders only and no obvious secret values.
- [ ] Write tests verifying documentation files required by the lean documentation model exist.
- [ ] Write tests verifying release and backup check scripts fail clearly when required inputs are missing.

### Usage Examples Required

```text
tests/usage/00_project_scaffold.py
```

Usage examples must show:

- [ ] Build an example demonstrating running the local validation command in dry-run/report mode.
- [ ] Build an example demonstrating loading safe environment defaults without broker or network dependencies.
- [ ] Build an example demonstrating reading the release checklist and producing a bounded readiness summary.

### Quality and Documentation Standards

- [ ] Pass all CI quality gates (Ruff format, Ruff check, mypy --strict, pytest, and coverage at least 80%).
- [ ] Update module README and active documentation for any architecture or API changes.

### Acceptance Checklist

- Done criterion: All Phase 0 checkbox tasks are implemented or explicitly deferred with a documented reason.
- Done criterion: Repository scaffold, CI gates, docs baseline, environment template, and release checklist are ready before Phase 1 implementation.
- Done criterion: The project can be imported and tested without optional live-provider dependencies installed.
