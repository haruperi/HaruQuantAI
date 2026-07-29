# Simulation Interpreter

> **Package:** `app/agentic/agents/experimentation/simulation_interpreter`
> **Feature:** `FEAT-AGT-08` Analytics Interpretation
> **Status:** `Completed`
> **Last updated:** `2026-07-29`

> This README documents one registered leaf agent package. It is **subordinate
> to the canonical Agentic Feature Registry** in `app/agentic/README.md`, which
> remains the sole authority for feature IDs, statuses, public APIs, contracts,
> and requirements. This file contains no Feature Registry section and defines
> no requirement of its own.

---

## 1. Purpose and Boundary

### Purpose

Interpret one completed, versioned deterministic evidence artefact produced by
Analytics, Simulation, or Optimization, and state what it shows, what it does
not show, and what remains unanswered — without recomputing any part of it.

### Owns

- The provider-neutral Simulation Interpreter agent definition.
- The immutable base role instruction in `prompt.md`.
- The `RunInterpretation` output schema.

### Does not own

- Production of the evidence it reads. Analytics, Simulation, and Optimization
  own their own reports, results, and handoffs.
- Any metric, fill, return, or performance value. It quotes; it never derives.
- Any tool adapter. This feature registers no `tools.py`: it receives completed
  evidence from its caller and calls no receiver-domain operation.
- Any approval, position size, or recommendation to trade.

### Shared contracts

**Owned by this feature** — defined authoritatively here:

| Status | Contract | Version | Counterparty | Purpose |
|---|---|---|---|---|
| Completed | `RunInterpretation` | `v1` | Agentic, UI/API | Cited interpretation separating measured facts, deterministic derivations, model inferences, and recommendations |

**Consumed from other domains** — referenced only, never redefined:

| Contract | Version | Owner | Used for |
|---|---|---|---|
| `AgentTask` / `AgentResult` / `AgentProvenance` / `BudgetUsage` | `v1` | Agentic `FEAT-AGT-01` | Typed task input and result envelope |
| `RoleManifest` | `v1` | Agentic `FEAT-AGT-02` | Enabled role resolution and prompt-integrity verification |
| `ModelProfile` / `ModelInvocation` / `AdkRuntime` | `v1` | Agentic `FEAT-AGT-03` | Governed provider-neutral execution |

---

## 2. Package Structure

```text
simulation_interpreter/
├── __init__.py     # Feature Registry public API only
├── agent.py        # Provider-neutral definition and public use case
├── prompt.md       # Immutable base role instruction
├── schemas.py      # Feature-owned typed output
└── README.md       # This file
```

No `tools.py`, `evaluator.py`, repository, migration, sandbox, or store file
exists, because the canonical module specification (§4.8) declares none.

### Public API

| Export | Kind | Purpose |
|---|---|---|
| `interpret_analytics_evidence` | function | Interpret one completed evidence artefact |
| `RunInterpretation` | class | Cited interpretation output |
| `build_run_interpretation` | function | Validated constructor |

---

## 3. Prompt Integrity

`prompt.md` is data, never code. `agent.py` loads it, normalizes line endings,
hashes it, and compares the digest against the enabled `RoleManifest` before
constructing anything. A mutated, missing, or empty prompt fails closed before
any model call.

**Line-ending convention.** The digest is computed over text normalized to `\n`
with trailing whitespace stripped and a single terminating newline. Without
this, the same artefact would hash differently on Windows and Linux and the
integrity check would fail spuriously across platforms. Every leaf agent
package follows this convention; the shared implementation is
`app.agentic.governance.registry.verify_prompt_artifact`.

The manifest's `base_prompt_hash` must therefore be derived from the normalized
artefact text. `governance.build_role_manifest` derives the composite
instruction hash from that base hash, so editing the prompt without updating
the manifest is caught at registry validation.

---

## 4. Behaviour

### Refusal is a complete outcome

`interpret_analytics_evidence` returns `AgentResult[RunInterpretation]` with
status `refused` and enumerated reasons when:

| Reason | Condition |
|---|---|
| `EVIDENCE_ABSENT` | No artefact was supplied |
| `EVIDENCE_INCOMPLETE` | The artefact lacks `evidence_ref`, `schema_id`, or `contract_version` |
| `EVIDENCE_CONTRACT_INCOMPATIBLE` | The artefact declares a version this role cannot read |
| *model reasons* | The interpreter itself declined |

It never substitutes a plausible answer for a missing one.

### No-recomputation is structural

`RunInterpretation` has **no numeric field**. Every statement is bounded text
keyed by the source reference it came from, so there is nowhere to put a
recomputed metric and no way to state a fact without citing it.

This is a structural bound, not a detection mechanism: a model can still write
a number inside a string. What the schema guarantees is that such a number is
visibly an uncited assertion in a labelled field, not a value the system
presents as measured.

---

## 5. Tests and Evidence

| Level | Location |
|---|---|
| Unit | `tests/agentic/unit/test_simulation_interpreter.py` |
| Usage | `tests/agentic/usage/08_interpretation.py` |
| Integration | `tests/agentic/integration/test_interpretation.py` (`WF-AGT-002`) |

```bash
uv run pytest tests/agentic/unit/test_simulation_interpreter.py -o addopts="" -q
```

```bash
uv run python tests/agentic/usage/08_interpretation.py
```

### Known limits

- The agent-graph runtime is currently the deterministic in-repo double; the
  Google ADK binding is not implemented (`FEAT-AGT-03` is `Partial`).
- Interpretation *quality* is not verified here. Grounding, citation
  correctness, and refusal calibration are measured by `FEAT-AGT-17`
  evaluation against versioned sets, which is `Missing`.

---

## 6. Change Process

1. Update the canonical Agentic README first — it owns the registry row.
2. Update this file.
3. Change `prompt.md` and the manifest `base_prompt_hash` together; they are
   verified against each other at startup.
4. Update `schemas.py`, tests, and the usage program.
5. Change status only after every gate passes.
