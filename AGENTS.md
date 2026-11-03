# Contributor Constitution

## Donor-first scope and responsibility

- SQX is the behavioral and responsibility baseline until parity is verified.
  Custom behavior requires a separate owner-approved proposal after parity.
- Before changing business logic, map the donor file/class/method or resource
  to one Python owner and its verification evidence. Mark partial or unknown
  evidence explicitly; filenames and file counts do not prove parity.
- Reuse the donor's ownership boundaries. Each behavior has one implementation;
  workspaces coordinate shared services rather than duplicate their logic.
- Every new function, module, or capability must serve a mapped requirement.
  Necessary Python or host differences need a short, explicit rationale in the
  responsibility map and implementation plan. Do not build speculative features,
  generic frameworks, or compatibility layers for anticipated future needs.
- Prefer consolidating duplicated code and keeping examples/configuration as
  resources. Report file/line changes, but do not force unrelated responsibilities
  into oversized files or count relocation alone as simplification.
- Record existing custom behavior as a divergence. Removing it or changing a
  public contract requires a concrete approved plan; cleanup is not implicit
  authorization to remove functionality.
- AlgoWizard ownership: `docs/dev/algo-wizard-donor-responsibility-map.md`.

## 1. Plan -> Execute -> Walkthrough workflow

Every development task follows this sequence:

1. **Research and audit:** inspect active code, documentation, tests, references,
   dependencies, and working-tree state. Make no source edits.
2. **Implementation plan:** Before touching code, write (in chat not file),
   implementation plan using the
   [implementation plan template](docs/templates/implementation-plan.md) .
3. **Owner approval gate:** stop until the owner explicitly responds exactly
   `APPROVED: EXECUTE` with nothing else. Any extra text means adjusting
   the plan or addressing that issue first.
4. **Surgical implementation:** edit only approved task and paths, record material
   deviations as a plan iteration before proceeding. Only one "APPROVED: EXECUTE"
   for what is listed in this task only do not treat historical approval as current.
   Any blockers during implementation will need its own "APPROVED: EXECUTE"
   after updating the implementation plan.
5. **Focused verification:** run change-scoped tests during development.
6. **Walkthrough:** After finishing coding/task, write (in chat not file)
   a summary using [walkthrough template](docs/templates/walkthrough.md), including changes, exact
   commands/results, deviations, residual risks, `git status`, and a proposed commit message.
7. **Owner commit gate:** do not commit, merge, push, rebase, or rewrite history
   without explicit owner authorization after walkthrough review.

Approval applies only to the plan version presented. New destructive targets,
public contracts, dependencies, or architectural decisions require a recorded
iteration and renewed approval when they materially expand scope.

## 2. Coding and verification baseline

- Ruff formatting: four spaces, 88-character lines, Google-style docstrings.
- Standardized top-of-file docstrings and non-silent requirement logging: every
  concrete Python module must have
  `Description:` (business logic and internal/external workflows), `Purpose:`
  (`FEAT-*`), `Key Capabilities:` (descriptive kebab-case `FR-*` labels, never
  numbered, with zero silent executions and explicit log verification), `Python API Usage:`, and `CLI Usage:`.
- Mypy strict mode with all public signatures explicitly typed.
- No bare `except`, silent failures, application `print`, hidden logging setup,
  or secret-bearing diagnostics.
- Minimum 80% branch-aware pytest coverage across retained Python application
  source. Coverage is evidence, not semantic proof.
- Focused iteration uses explicit test paths and `--no-cov`; do not repeatedly
  run the complete suite while editing.
- UI changes require, as applicable:
  `npm --prefix ui run typecheck`, `npm --prefix ui run test`, and
  `npm --prefix ui run build`.

## 3. Security, persistence, and external effects

- Never commit credentials, tokens, secrets, private endpoints, or sensitive
  configuration. Keep secret detection current.
- Fail closed when authority, compatibility, schema, credentials, or evidence is
  uncertain.
- Never delete, reset, truncate, migrate, or repurpose an active database without
  explicit owner authorization. Tests use isolated temporary stores.
- Persistence schemas, migrations, transactions, and retention belong to an
  explicitly ratified host capability; plugins never execute ad-hoc SQL.
- External integrations require typed capabilities, bounded timeouts, retry and
  rate policies, redaction, and explicit lifecycle ownership.
- Live trading and other irreversible external mutations are disabled by default
  and require distinct authorization beyond ordinary implementation work.

## 4. Git authority

The owner retains exclusive authority over commits, branches, merges, rebases,
pushes, and history rewrites. The assistant may inspect Git, prepare diffs,
verify the candidate, and propose a commit message within the approved task.
