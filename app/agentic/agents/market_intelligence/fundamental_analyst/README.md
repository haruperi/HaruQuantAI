# Fundamental Analyst

> **Package:** `app/agentic/agents/market_intelligence/fundamental_analyst`
> **Feature:** `FEAT-AGT-09` Fundamental Research
> **Status:** `Completed`
> **Last updated:** `2026-07-30`

> This README documents one registered leaf agent package. It is **subordinate
> to the canonical Agentic Feature Registry** in `app/agentic/README.md`, which
> remains the sole authority for feature IDs, statuses, public APIs, contracts,
> and requirements. This file contains no Feature Registry section and defines
> no requirement of its own.

---

## 1. Purpose and Boundary

### Purpose

Say what point-in-time filings, transcripts, and macro releases actually
support, and say what would show the reading wrong.

### Owns

- The provider-neutral analyst definition and its one operation.
- The immutable base role instruction in `prompt.md`.
- `FundamentalEvidencePack` and the parallel key-set rule.
- The recommendation vocabulary a research role must not emit.

### Does not own

- Evidence. Research `FEAT-RES-13` assembles it from Data `FEAT-DATA-16`
  point-in-time documents; this package reads a projection.
- Applicability. Research decides whether a model applies to an asset class,
  and the analyst is told. See §3.
- Injection classification. `FEAT-AGT-06` decides what reads as an
  instruction; this package reuses that judgement.
- Any figure. Coverage, revisions, availability, and the canonical digest all
  arrive as evidence.

### Shared contracts

**Owned by this feature:** `FundamentalEvidencePack` `v1`.

**Consumed:** `AgentTask`/`AgentResult`/`AgentProvenance`/`BudgetUsage`
(`FEAT-AGT-01`), `RoleManifest`/`FirmMandate` (`-02`), `ModelProfile`/
`AdkRuntime` (`-03`), `AgentPolicy`/`ToolPolicy`/`call_governed_tool` (`-05`),
`classify_injection`/`store_memory` (`-06`), `reject_authorization_language`
(`-07`), and — through an injected port — Research's
`assess_intelligence_applicability` and `build_fundamental_source_evidence`.

---

## 2. Package Structure

```text
fundamental_analyst/
├── __init__.py     # Feature Registry public API only
├── agent.py        # Provider-neutral definition and the public use case
├── prompt.md       # Immutable base role instruction
├── schemas.py      # Feature-owned evidence pack
├── tools.py        # Governed Research evidence bindings
└── README.md       # This file
```

Exactly the canonical §4.9 file list.

**A recorded divergence.** The §4.9 dependency column lists the Research public
contracts as a local dependency of `agent.py` and `tools.py`. Nothing here
imports them. Building the evidence also requires a Data `ResearchSourceQuery`,
so a concrete binding would pull two receiver domains into an agent package. An
approved composition root binds the port instead, and a test asserts this
package names neither `app.services.research` nor `app.services.data`. The
chain stays Agentic → Research → Data.

---

## 3. Applicability is the receiver's answer

Research's issuer model covers equity, corporate bonds, and funds. **FX has no
issuer.** So a fundamental reading of EURUSD under `model="issuer"` is refused
`FUNDAMENTAL_MODEL_NOT_APPLICABLE` — and since this firm's mandate is an FX
mandate, that is the ordinary path rather than an edge case.

The applicability call happens **before** the evidence call, so a refused model
is never even queried for data. The integration test binds the port to
Research's real `assess_intelligence_applicability` and asserts the refusal is
genuine rather than mocked.

---

## 4. Behaviour

### Every claim carries a falsifier

`claims`, `assumptions`, `horizons`, and `falsifiers` are validated as parallel
key sets: identical keys, or the pack cannot be built. A claim nobody can say
how to falsify is not admissible, and this makes that a construction error
rather than a review finding. An orphaned falsifier is refused the same way.

### Lineage is copied, not described

`observed_from`, `available_by`, `source_kinds`, `coverage`, `evidence_refs`,
and `canonical_hash` all come from the projection. A model output claiming a
different availability instant or digest changes nothing — a test asserts it.

### Instructions never reach the model

Every projected reference passes `classify_injection` first. Flagged references
are excluded, counted in the trusted context, and recorded in the pack's
uncertainty statement. A projection consisting only of instructions refuses
`FUNDAMENTAL_COVERAGE_INSUFFICIENT` before any model call.

### The pack has no numeric field

Every value is bounded text. There is nothing here that could express a
recomputed upstream figure, which is the same discipline `FEAT-AGT-08`
established for the first leaf package.

### Refusal is a complete outcome

| Reason | Condition | Before the model? |
|---|---|---|
| `INTELLIGENCE_TOOL_DENIED` | An evidence tool is unregistered or denied | Yes |
| `FUNDAMENTAL_MODEL_NOT_APPLICABLE` | Research says the model does not apply | Yes |
| `FUNDAMENTAL_COVERAGE_INSUFFICIENT` | Projection incomplete, or every reference excluded | Yes |
| `FUNDAMENTAL_CLAIM_NOT_FALSIFIABLE` | Key sets diverge, or the text recommends | No |
| *model reasons* | The analyst itself declined | — |

---

## 5. Tests and Evidence

| Level | Location |
|---|---|
| Unit | `tests/agentic/unit/test_fundamental_analyst.py` |
| Usage | `tests/agentic/usage/09_fundamental.py` |
| Integration | `tests/agentic/integration/test_market_intelligence.py` |

```bash
uv run pytest tests/agentic/unit/test_fundamental_analyst.py -o addopts="" -q
```

```bash
uv run python tests/agentic/usage/09_fundamental.py
```

The integration test and the usage program both bind applicability to
Research's **real** function, so the FX/issuer refusal is demonstrated with
`FEAT-RES-13` as shipped rather than a stand-in.

### Known limits

- **No source has been fetched and no evidence assembled.** The projection
  arrives from a deterministic double; binding the port to
  `build_fundamental_source_evidence` and a Data query is a composition root's
  job, and no composition root exists.
- **No live provider call.** `FEAT-AGT-03`'s binding is structurally verified
  only.
- **Reading quality is not verified here.** Whether a claim is *good* is
  measured by `FEAT-AGT-17` evaluation against versioned sets. That mechanism
  exists, but no versioned set has been authored for this role and no grader
  calibrated, so this role has not in fact been evaluated.
- **`WF-AGT-PRI` remains `Missing`.** This role is one participant; the council
  needs the whole roster and the `FEAT-AGT-22` submission path.

---

## 6. Change Process

1. Update the canonical Agentic README first — it owns the registry row.
2. Update this file.
3. Change `prompt.md` and the manifest `base_prompt_hash` together.
4. **Never let the analyst decide applicability.** Asking Research is the point;
   a local rule would drift from the receiver's and eventually contradict it.
5. Never relax the parallel key-set rule. A claim without a falsifier is the
   failure mode this feature exists to prevent.
6. Never add a numeric field to the pack.
7. Update `schemas.py`, `tools.py`, tests, and the usage program.
8. Change status only after every gate passes.
