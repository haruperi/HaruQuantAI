# Implementation Plan: [Goal / Task / Plugin]

> **Task ID:** `[TASK-XXX | PLUGIN-ID]`
> **Iteration:** `[1]`
> **Branch:** `[branch | main]`
> **Baseline Commit:** `[SHA]`

Follow-up work on the same task appends a labelled iteration to this file.

---

### User Review Required

> [!IMPORTANT]
> [Breaking changes, destructive actions, compatibility choices, or explicit
> owner decisions.]

### Open Questions

> [!NOTE]
> [Questions that materially affect scope, or `NONE`.]

---

## 1. Goal, Requirements & Usage Evidence

- **Problem and outcome:** [What changes and why.]
- **Ratified requirements:** [Exact IDs/laws/acceptance.]
- **Spatial invariants:** [How the five laws are preserved.]
- **Usage evidence:** [Deterministic primary-purpose scenario.]

## 2. Files Read (Audit Trail)

- [authority or source](C:/absolute/path) — [what was verified].

Include active implementation, universal APIs, consumers, tests, documentation,
working-tree state, and affected schemas. Do not plan from chat memory alone.

## 3. Proposed Changes & Implementation Order

Use explicit action tags:

- `[NEW]` [plugin.py](C:/absolute/path/app/plugins/kind/plugin.py) — complete
  cohesive behavior and self-description.
- `[MODIFY]` [consumer.py](C:/absolute/path) — only when a universal boundary,
  not plugin-specific wiring, genuinely changes.
- `[DELETE]` [obsolete.py](C:/absolute/path) — reason and replacement/recovery.

### Sequential Implementation Order

1. Universal contract/schema change, when explicitly approved.
2. One cohesive plugin or host owner.
3. Discovery/catalog/algebra integration through generic mechanisms.
4. Focused tests, usage scenario, and evidence.
5. Documentation reconciliation and qualification.

## 4. Dependencies and Contracts

- Capability slots and protocol/value types.
- Plugin/API and algebra/schema versions.
- Inputs, outputs, units, compatibility, and failure semantics.
- Persistence or external effects and their lifecycle owner.
- Consumer impact and why no plugin-specific duplication is introduced.

## 5. Blockers, Risks, and Trade-offs

- [Risk, observable consequence, and mitigation.]
- [Authority or compatibility conflict.]
- [Rollback trigger.]

## 6. Scope Boundaries (Inclusions & Exclusions)

- **In scope:** [Exact deliverables.]
- **Out of scope:** [Explicit non-goals and prohibited expansion.]

## 7. Verification Plan

### Focused tests

```powershell
uv run pytest --no-cov tests/plugins/[kind]/test_[plugin].py -v
```
### Usage evidence

```powershell
uv run python -m tests.examples.[approved_example]
```

### Architecture and qualification

```powershell
uv run python scripts/architecture_check.py
uv run python scripts/ci_check.py
```

Add UI typecheck/test/build when catalog, schema, algebra, transport, or rendering
changes. List every exact command planned.

### Manual verification

[Manual checks or `NONE`.]

## 8. Rollback & Contingency

[Targeted recovery steps, failure contingencies, and Git baseline.]

```text
ALLOWED_WRITE_PATHS:
- app/plugins/[kind]/[plugin].py
- tests/plugins/[kind]/test_[plugin].py
- tests/examples/[approved_example].py
- app/plugins/[kind]/README.md
- docs/dev/evidence/[approved_manifest].json
- .agents/logs/[task]/implementation-plan.md
- .agents/logs/[task]/walkthrough.md
END_ALLOWED_WRITE_PATHS:
```
