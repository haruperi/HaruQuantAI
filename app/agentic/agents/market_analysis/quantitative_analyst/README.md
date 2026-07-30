# Quantitative Analyst

> **Package:** `app/agentic/agents/market_analysis/quantitative_analyst`
> **Feature:** `FEAT-AGT-12` Quantitative Research
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

Read versioned statistical evidence that Research and Analytics have already
produced, and state what it supports, how confident that reading can be, and
what would have to be true for it to be wrong.

### Owns

- The provider-neutral Quantitative Analyst agent definition.
- The immutable base role instruction in `prompt.md`.
- The `QuantitativeEvidencePack` output schema.
- The governed tool bindings to the Analytics metric catalog.

### Does not own

- Any statistic. Research and Analytics compute; this role interprets.
- Any estimator definition, formula, sample convention, or sample floor. Those
  are registered in the Analytics metric catalog and fetched, never authored.
- Any imputation, interpolation, or reconciliation of unusable evidence.
- Any approval, position size, or recommendation to trade.

### Shared contracts

**Owned by this feature** — defined authoritatively here:

| Status | Contract | Version | Counterparty | Purpose |
|---|---|---|---|---|
| Completed | `QuantitativeEvidencePack` | `v1` | Agentic, UI/API | Disclosed statistical reading binding sample, estimator, uncertainty, multiple-testing exposure, assumptions, and limitations |

**Consumed from other domains** — referenced only, never redefined:

| Contract | Version | Owner | Used for |
|---|---|---|---|
| `AgentTask` / `AgentResult` / `AgentProvenance` / `BudgetUsage` | `v1` | Agentic `FEAT-AGT-01` | Typed task input and result envelope |
| `RoleManifest` / `FirmMandate` | `v1` | Agentic `FEAT-AGT-02` | Enabled role resolution and prompt-integrity verification |
| `ModelProfile` / `ModelInvocation` / `AdkRuntime` | `v1` | Agentic `FEAT-AGT-03` | Governed provider-neutral execution |
| `AgentPolicy` / `ToolPolicy` / `call_governed_tool` | `v1` | Agentic `FEAT-AGT-05` | Deny-by-default tool authorization |
| Metric definition catalog and minimum-sample thresholds | `v1` | Analytics | Deterministic estimator grounding |

---

## 2. Package Structure

```text
quantitative_analyst/
├── __init__.py     # Feature Registry public API only
├── agent.py        # Provider-neutral definition and public use case
├── prompt.md       # Immutable base role instruction
├── schemas.py      # Feature-owned typed output
├── tools.py        # Governed Analytics catalog bindings
└── README.md       # This file
```

No `evaluator.py`, repository, migration, sandbox, or store file exists,
because the canonical module specification (§4.12) declares none.

### Public API

| Export | Kind | Purpose |
|---|---|---|
| `analyze_quantitative_evidence` | function | Analyse versioned Research and Analytics evidence |
| `QuantitativeEvidencePack` | class | Disclosed statistical reading |
| `build_quantitative_evidence_pack` | function | Validated constructor |

`tools.py` is internal to the feature, as the module specification requires.
Its `QuantitativeEvidencePort` Protocol is the injection point a composition
root binds to the real Analytics catalog.

---

## 3. Prompt Integrity

`prompt.md` is data, never code. `agent.py` loads it, normalizes line endings,
hashes it, and compares the digest against the enabled `RoleManifest` before
constructing anything. A mutated, missing, or empty prompt fails closed before
any model call. The shared implementation is
`app.agentic.governance.registry.verify_prompt_artifact`; the line-ending
convention is documented there and applies to every leaf agent package.

---

## 4. Behaviour

### The estimator is not the model's to choose

The model names a metric per finding; the Analytics catalog says what that
metric *is*. `agent.py` fetches each definition through a governed tool call,
then replaces the model's attribution with the registered formula before the
pack is built. A name the catalog does not recognize — including a formula the
model wrote out in place of a name — is refused as `ESTIMATOR_NOT_CATALOGUED`.

The sample floor works the same way: it is read from the catalog's
minimum-sample thresholds, not hard-coded here, so raising the floor in
Analytics changes what this role will interpret.

### Disclosure is structural

`QuantitativeEvidencePack` requires `sample_size`,
`multiple_testing_exposure`, `estimators`, `uncertainty`, `assumptions`, and
`limitations`. `estimators` and `uncertainty` are validated against the same
key set as `findings`, so a point estimate with no interval and a finding with
no estimator are both unrepresentable.

Sample size, multiple-testing exposure, dataset hash, configuration hash, and
split come from the caller and the deterministic evidence — never from model
output. A model that emits its own `sample_size` is ignored.

### Refusal is a complete outcome

`analyze_quantitative_evidence` returns `AgentResult[QuantitativeEvidencePack]`
with status `refused` and enumerated reasons when:

| Reason | Condition |
|---|---|
| `METRICS_NOT_REQUESTED` | No catalogued metric was named |
| `EVIDENCE_TOOL_DENIED` | A required catalog tool is unregistered or authorization denied it |
| `ESTIMATOR_NOT_CATALOGUED` | A metric, or a finding's attribution, has no registered definition |
| `EVIDENCE_ABSENT` | No versioned evidence was supplied |
| `NON_FINITE_INPUT` | A supplied statistic is `NaN` or infinite |
| `INSUFFICIENT_SAMPLE` | The sample is below the catalogued minimum for the estimator class |
| `EVIDENCE_NOT_ALIGNED` | Supplied evidence disagrees on dataset or configuration hash |
| `LEAKAGE_UNSAFE` | Reported leakage severity is `high` or `critical` |
| *model reasons* | The analyst itself declined |

The four `FR-AGENTIC-036` conditions — non-finite, under-sampled, non-aligned,
and leakage-unsafe — are all evaluated **before** the runtime is invoked. The
model is never shown data it would have to repair.

### No-imputation is structural

`QuantitativeEvidencePack` has **no numeric field**. Every value is bounded
text, so there is nowhere to place a statistic the evidence did not contain.

This is a structural bound, not a detection mechanism: a model can still write
a number inside a string. What the schema guarantees is that such a number is
visibly an assertion in a labelled text field, not a value the system presents
as measured.

---

## 5. Tests and Evidence

| Level | Location |
|---|---|
| Unit | `tests/agentic/unit/test_quantitative_analyst.py` |
| Usage | `tests/agentic/usage/12_quantitative.py` |
| Integration | `tests/agentic/integration/test_quantitative_evidence.py` |

```bash
uv run pytest tests/agentic/unit/test_quantitative_analyst.py -o addopts="" -q
```

```bash
uv run python tests/agentic/usage/12_quantitative.py
```

### Known limits

- The Analytics catalog arrives through `build_analytics_catalog_port`, which
  binds an injected facade. Wiring it to the real Analytics package root is a
  composition-root concern and is not exercised here; tests use deterministic
  doubles.
- Interpretation *quality* is not verified here. Grounding, disclosure
  calibration, and refusal correctness under adversarial evidence are measured
  by `FEAT-AGT-17` evaluation against versioned sets. That mechanism now
  exists, but no versioned set has been authored for this role and no grader
  has been calibrated against it, so this role has not in fact been evaluated.
- `analytics.validate_contract_version` is registered as an eligible tool but
  is not yet called by `agent.py`; evidence contract compatibility is checked
  by the caller.

---

## 6. Change Process

1. Update the canonical Agentic README first — it owns the registry row.
2. Update this file.
3. Change `prompt.md` and the manifest `base_prompt_hash` together; they are
   verified against each other at startup.
4. Update `schemas.py`, `tools.py`, tests, and the usage program.
5. Change status only after every gate passes.
