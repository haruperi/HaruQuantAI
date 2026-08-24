# HaruQuantAI Orchestrator End-to-End Test Order

> **Status:** Temporary implementation tracker used only to validate the automated
> Planner/Executor/Reviewer orchestrator (`.agents/`). Not a product roadmap. Delete this file
> and the `D-TEST` domain after the workflow is proven.
> **Architecture baseline:** `docs/PROJECT.md`, `docs/ARCHITECTURE.md`, and owning package READMEs
> **Last updated:** 2026-08-24

## 1. How to use this file

This file mirrors the notation of `IMPLEMENTATION_ORDER.md` for a single disposable task. Entries follow
the same completion rules: mark a requirement complete only after appending executable evidence in the
form `— evidence: path/to/file:line`; mark the feature complete only after every applicable gate
(contracts, configuration, lifecycle, dependency, failure, documentation, and physical-removal) passes.

### Completion notation

```text
##### T.1 [ ] FEAT-TEST-GREETING

1. [ ] FR-TEST-GENERATE_GREETING
```

When completed:

```text
##### T.1 [x] FEAT-TEST-GREETING

1. [x] FR-TEST-GENERATE_GREETING — evidence: tests/services/test/greeting/test_greeting.py:12
```

## 2. Test sequence

### Increment T — Orchestrator workflow validation (temporary)

**Purpose:** Exercise the full automated three-role workflow (Planner dry run → owner approval →
Executor → Reviewer → close-out merge) on the smallest possible real feature slice, then prove the
feature is physically removable without harming the substrate.

**Exit gate:** The tracker entry is marked complete with evidence, the feature registers through the
standard composition entry point, its tests pass, and deleting the feature folder leaves the
architecture/composition suites green.

#### `D-TEST` — Test (temporary domain; physically removable)

##### T.1 [x] `FEAT-TEST-GREETING`

1. [x] `FR-TEST-GENERATE_GREETING` — evidence: tests/services/test/greeting/test_greeting.py:15

Minimal pure capability: generate a deterministic greeting for a validated caller name (trimmed,
non-empty, bounded length) through one registered feature — module folder, `manifest.py` with
`SPEC: FeatureSpec`, zero-argument factory registered under the `haruquantai.features` entry-point
group, feature-local README registry entry, a bounded deterministic secret-safe `if __name__ ==
"__main__":` usage harness, and feature tests. No persistence, no UI, no external I/O, no
interaction with real product domains beyond the documented registration surface.
