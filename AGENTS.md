# HaruQuantAI Contributor Constitution

## 1. Authority and engineering principles

- **Repository truth, not chat memory.** Permanent truth lives in `AGENTS.md`,
  `docs/PROJECT.md`, `docs/ARCHITECTURE.md`, applicable package READMEs, and
  `.agents/logs/<timestamp>_<task>/`.
- **Scoped authority.** `AGENTS.md` owns workflow and verification;
  `docs/PROJECT.md` owns product scope; `docs/ARCHITECTURE.md` owns structural
  constraints; `docs/dev/feature_implementation_pipeline.md` and
  `docs/dev/domain_implementation_audit.md` own plugin build and audit standards.
- **Five Spatial Composability laws.** All future backend work must preserve:
  locality of behavior, orthogonality, explicit typed capability slots,
  hierarchical/algebraic composition, and schema-driven self-description.
- **One concrete plugin, one cohesive Python file.** Calculation, configuration,
  parameter schema, bounds, outputs, compatibility, lowering, and presentation
  metadata for one quantitative concept stay together. Shared universal
  metamodels may be imported; plugin-specific contracts may not be centralized.
- **No ambient coupling.** Components do not reach through registries, globals,
  private imports, or filesystem conventions at operation time. Collaboration is
  declared through typed capabilities and immutable documents.
- **Repository evidence over assertion.** Never invent behavior, tests, results,
  contracts, or completion status.
- **Surgical changes.** Implement the smallest complete approved change. Preserve
  unrelated user changes and report authority conflicts before editing.
- **Standard-library kernel.** `app/kernel/` uses only the Python standard
  library and contains no product, plugin, UI, persistence, or integration logic.
- **Honest UI.** `app/ui/` owns presentation and local view state. It must not
  duplicate backend algorithms, durable truth, authorization, or plugin schemas.

The repository is currently at a backend-reset baseline. No backend plugin,
host, registry, persistence, or gateway implementation may be added until an
approved architecture plan establishes its paths and public metamodel.

## 2. Plan -> Execute -> Walkthrough workflow

Every development task follows this sequence:

1. **Research and audit:** inspect active code, documentation, tests, references,
   dependencies, and working-tree state. Make no source edits.
2. **Implementation plan:** create or append
   `.agents/logs/<timestamp>_<task>/implementation-plan.md` using the canonical
   template and define exact `ALLOWED_WRITE_PATHS`.
3. **Owner approval gate:** stop until the owner explicitly responds
   `APPROVED: EXECUTE` or equivalently approves the documented plan.
4. **Surgical implementation:** edit only approved paths and record material
   deviations as a plan iteration before proceeding.
5. **Focused verification:** run change-scoped tests during development.
6. **Candidate qualification:** run `uv run python scripts/ci_check.py` after the
   candidate is complete, plus applicable UI commands.
7. **Walkthrough:** create `walkthrough.md` from the canonical template,
   including changes, exact commands/results, deviations, residual risks,
   `git status`, and a proposed commit message.
8. **Owner commit gate:** do not commit, merge, push, rebase, or rewrite history
   without explicit owner authorization after walkthrough review.

Approval applies only to the plan version presented. New destructive targets,
public contracts, dependencies, or architectural decisions require a recorded
iteration and renewed approval when they materially expand scope.

## 3. Plugin implementation standard

Once the replacement architecture is ratified, plugin work must follow
`docs/dev/feature_implementation_pipeline.md` and its companion audit. At
minimum, each plugin must provide:

- a stable namespaced ID and explicit compatibility version;
- immutable, typed inputs/outputs and capability requirements;
- an introspectable parameter schema with defaults, constraints, optimization
  bounds, units, and presentation hints;
- deterministic behavior with explicit missing-data, warm-up, error, and
  numerical policies;
- algebraic node/port declarations when composable in strategy trees;
- no import-time registration, I/O, tasks, threads, environment reads, or
  global mutation;
- discovery through the host catalog without editing a central plugin list;
- focused tests, removal/orthogonality tests, schema tests, and a deterministic
  offline usage example;
- truthful documentation with no metadata duplicated outside the plugin file.

Python `__init__.py` files are empty or docstring-only. Cross-plugin private
imports and sibling implementation imports are prohibited.

## 4. Coding and verification baseline

- Ruff formatting: four spaces, 88-character lines, Google-style docstrings.
- Mypy strict mode with all public signatures explicitly typed.
- No bare `except`, silent failures, application `print`, hidden logging setup,
  or secret-bearing diagnostics.
- Minimum 80% branch-aware pytest coverage across retained Python application
  source. Coverage is evidence, not semantic proof.
- Architecture checks must pass:
  `uv run python scripts/architecture_check.py`.
- Focused iteration uses explicit test paths and `--no-cov`; do not repeatedly
  run the complete suite while editing.
- UI changes require, as applicable:
  `npm --prefix app/ui run typecheck`, `npm --prefix app/ui run test`, and
  `npm --prefix app/ui run build`.
- Every backend plugin eventually requires a self-contained deterministic usage
  example in the location ratified by the replacement architecture.

## 5. Security, persistence, and external effects

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

## 6. Git authority

The owner retains exclusive authority over commits, branches, merges, rebases,
pushes, and history rewrites. The assistant may inspect Git, prepare diffs,
verify the candidate, and propose a commit message within the approved task.
