# HaruQuantAI V3 — Phase 0 exit review and ratification

**Artifact:** Phase 0 exit review

**Status:** `RATIFIED_READY_FOR_PHASE_1`

**Date:** 2026-09-07

**Baseline HEAD:** `34edd2b3c8164b59ed9b2b2964c0d79f7c2d399a`

**Implementation state:** approved Quick-Fix working tree on `main`; no commit was
created or implied

## Verdict

All eight Phase 0 preparations are complete. The repository now has a
deterministic, schema-validated projection of the 205-feature plan, concrete
fixtures, measured performance evidence, authoritative domain bindings, and a
real local browser-readiness slice. Phase 0 consumed no feature-task slot and
does not claim that the remaining 203 feature tasks are implemented.

The ratification command is:

```powershell
uv run --frozen python scripts/validate_phase0.py
```

It must remain green before Phase 1 begins and throughout later tracker
progress. The baseline manifest and normalized Phase 0 source projections are
immutable snapshots verified against the recorded Git baseline. Current task
status, path, usage and requirement ledgers may advance only monotonically with
schema-valid acceptance evidence; they never rewrite the historical snapshot.
Phase 0 generation `--check` commands apply at ratification time, while the
validator owns the later snapshot-versus-progress distinction.

The baseline plan is pinned to Git blob
`a6a8754170c5ff1a0ba853f8b3d91f43a68aa2a3` at the recorded baseline HEAD.
Its exact stored bytes have SHA-256
`421120edda333378eed98f39e9e0a8c0870f50308cd5b96828175be33bbb328f`.
The earlier recorded value
`7fba3b8aa82ad94652c353ca997051067caa5fce650f39f389e9e9e705a5b5f6`
matched no LF or CRLF form of any committed plan and is retained only as
`legacy_unattested_plan_sha256`; it is not accepted as baseline authority.

For normal Task delivery, an already-existing accepted feature may retain its
40-hex commit. New evidence committed before close-out instead uses a stable
`task-closeout:<run-id>` reference because the final commit SHA cannot be
embedded in its own tree. The workflow-owned close-out receipt binds that
reference to the actual accepted commit after creation; the reference is never
represented as a Git SHA.

## Preparation gates

| Preparation | Evidence | Result |
| --- | --- | --- |
| 0.01 — source and scope | `baseline-manifest.json`, `specification-drift.md`, normalized source projection | COMPLETE |
| 0.02 — feature audit | `feature-baseline.json`, `requirement-status.json`, `path-bindings.json` | COMPLETE |
| 0.03 — domain bindings | 18 owning domain READMEs, `contract-bindings.json`, `schema-fixture-plan.json` | COMPLETE |
| 0.04 — schedule and gates | `dependency-schedule.json`, `operation-readiness.json`, `phase-ui-acceptance-matrix.json` | COMPLETE |
| 0.05 — numerical/external/security | deterministic fixture files, `fixture-manifest.json`, `numerical-security-policy.md`, `external-evidence-calendar.json` | COMPLETE |
| 0.06 — quality/performance | `quality-baseline.md`, `reference-hardware.json`, measured `performance-baseline.json` | COMPLETE |
| 0.07 — evidence and browser harness | `evidence-schema.json`, `usage-bindings.json`, real local ASGI/Playwright readiness test | COMPLETE |
| 0.08 — entry and execution source | this review and `docs/dev/Phased_Feature_Implementation_Plan.md` | COMPLETE |

## Verified invariants

- The plan contains exactly 205 unique feature/task pairs: 2 accepted and 203
  still open.
- The normalized inventory contains 575 FRs, 276 local NFRs, 476 required
  capability edges, and 233 operation-gated edges.
- Every required provider precedes its consumer, and every deferred operation
  has a provider, guard, test owner, and fail-closed readiness state.
- All 18 domain READMEs cover the exact feature set once and no longer retain
  unresolved Phase 0 contract-binding markers or stale source paths.
- Three non-ignored repository fixture files reproduce byte-for-byte and are
  hash-pinned.
- The browser slice uses the real local identity/API stack. It proves account
  registration, authenticated identity, blank-workspace creation, reload
  recovery, keyboard reachability, and bounded navigation time. Missing Phase 1
  providers remain explicit 503 unavailable responses.
- The phased plan is the default Task/Goal selection source; Phase 0 preparation
  headings are excluded from feature-task selection.

## Evidence limits retained

- Open external evidence blocks only the named production claim at its recorded
  due gate. No live provider, licence, broker fill, or donor parity is invented.
- The generated-tick fixture closes the offline fixture prerequisite, not future
  production-algorithm qualification.
- Existing React test and build warnings are recorded in `quality-baseline.md`;
  they are not hidden or converted into feature acceptance.
- A Quick-Fix has no independent Reviewer or automatic commit. This record
  ratifies the validated tree only; any later Git action requires separate owner
  direction.

## Phase 1 entry

Phase 1 may begin with Task 1.01 (`FEAT-UI-01`) through the configured atomic
Task/Goal workflow. Each feature still requires its own complete implementation,
usage evidence, independent review, accepted feature commit, and merge record.
