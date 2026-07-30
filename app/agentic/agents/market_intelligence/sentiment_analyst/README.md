# Sentiment Analyst

> **Package:** `app/agentic/agents/market_intelligence/sentiment_analyst`
> **Feature:** `FEAT-AGT-10` News and Sentiment Research
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

Report what the measured text evidence shows, and keep what it shows separate
from what it might mean.

### Owns

- The provider-neutral analyst definition and its one operation.
- The immutable base role instruction in `prompt.md`.
- `SentimentEvidencePack` and its five-way separation.
- The closed measurement-version check.

### Does not own

- Measurement. Research `FEAT-RES-13` computes polarity, coverage, trust,
  manipulation, and revision evidence from Data `FEAT-DATA-16` documents.
- Injection classification. `FEAT-AGT-06` decides what reads as an
  instruction. See §3.
- Deduplication or source selection. Both are upstream.

### Shared contracts

**Owned by this feature:** `SentimentEvidencePack` `v1`.

**Consumed:** the same control-plane contracts as every leaf role, plus —
through an injected port — Research's `assess_intelligence_applicability` and
`build_sentiment_source_evidence`.

---

## 2. Package Structure

```text
sentiment_analyst/
├── __init__.py     # Feature Registry public API only
├── agent.py        # Provider-neutral definition and the public use case
├── prompt.md       # Immutable base role instruction
├── schemas.py      # Feature-owned evidence pack
├── tools.py        # Governed, injection-filtered text-evidence bindings
└── README.md       # This file
```

Exactly the canonical §4.10 file list. The same dependency-column divergence
recorded in the fundamental analyst's README applies here: nothing imports
Research or Data, and a test asserts it.

---

## 3. Instruction stripping happens before the model, not after

`FR-AGENTIC-029` requires instruction stripping before sentiment reasoning.
Every projected reference passes `classify_injection` — `FEAT-AGT-06`'s
classifier, reused rather than restated — and anything flagged is:

1. excluded from what the model is shown,
2. counted in the trusted context as `excluded_references`,
3. recorded on the pack in `excluded_refs`, and
4. appended to the uncertainty statement.

The model never sees the flagged text. A projection consisting only of
instructions refuses `SENTIMENT_COVERAGE_INSUFFICIENT` before any model call.
This is the one place in the firm where hostile text is the expected input
rather than an edge case, and the filter running *first* is what makes the
rest of the reading trustworthy.

---

## 4. Behaviour

### Five fields, five different kinds of thing

| Field | Origin |
|---|---|
| `source_coverage` | Research, measured |
| `polarity` | Research, measured |
| `event_classification` | The model |
| `uncertainty` | The model |
| `unsupported_narrative` | The model, **labelled as not evidence** |

Keeping `unsupported_narrative` rather than forbidding it is deliberate: an
analyst that noticed something the lexicon cannot measure should say so, in the
field whose name says it is not a measurement. A test asserts a model output
attempting to rewrite `polarity` changes nothing.

### Governed metadata is carried, not described

`trust_evidence`, `manipulation_evidence`, `available_by`, `revisions`, and the
canonical digest come from the projection — exactly the `FR-AGENTIC-028` list,
because `SentimentSourceEvidence` already carries all of it.

### Disagreement is reported, not averaged

`disagreement` and `missing_measurements` survive into the pack. An analyst
that quietly averaged over disagreement would be hiding the most interesting
part of the evidence.

### The measurement version is closed

Research recognizes `lexicon-v1` and nothing else. The analyst checks that
**before any tool call**, so an unknown version costs no receiver round-trip.

### Refusal is a complete outcome

| Reason | Condition | Before the model? |
|---|---|---|
| `INTELLIGENCE_TOOL_DENIED` | An evidence tool is unregistered or denied | Yes |
| `MEASUREMENT_VERSION_UNKNOWN` | The version is not one Research recognizes | Yes |
| `SENTIMENT_MODEL_NOT_APPLICABLE` | Research says sentiment does not apply | Yes |
| `SENTIMENT_COVERAGE_INSUFFICIENT` | Projection incomplete, or every reference excluded | Yes |
| `SENTIMENT_OUTPUT_NOT_SEPARATED` | Recommendation language, or missing uncertainty | No |
| *model reasons* | The analyst itself declined | — |

---

## 5. Tests and Evidence

| Level | Location |
|---|---|
| Unit | `tests/agentic/unit/test_sentiment_analyst.py` |
| Usage | `tests/agentic/usage/10_sentiment.py` |
| Integration | `tests/agentic/integration/test_market_intelligence.py` |

```bash
uv run pytest tests/agentic/unit/test_sentiment_analyst.py -o addopts="" -q
```

```bash
uv run python tests/agentic/usage/10_sentiment.py
```

The integration test builds a **real** `SentimentSourceEvidence` and projects
it with Research's own `project_intelligence_evidence`, so the projection the
analyst reads is genuine.

### Known limits

- **No document has been fetched and no polarity measured.** The projection
  arrives from a deterministic double outside the integration test.
- **`classify_injection` is best-effort by its own admission.** It labels
  evidence so a caller can exclude it; it is not a security boundary. The
  boundary is that retrieved text occupies an evidence slot and never an
  instruction slot, which holds whether or not the classifier catches a
  particular string.
- **No live provider call.**
- **Reading quality is not verified here.** `FEAT-AGT-17` exists but no
  versioned set has been authored for this role and no grader calibrated.
- **`WF-AGT-PRI` remains `Missing`.**

---

## 6. Change Process

1. Update the canonical Agentic README first — it owns the registry row.
2. Update this file.
3. Change `prompt.md` and the manifest `base_prompt_hash` together.
4. **Never merge narrative into a measured field.** The separation is the
   feature; collapsing it would make an unsupported reading look measured.
5. Never filter instructions after the model call. Before is the point.
6. Never widen the measurement version without Research widening it first.
7. Update `schemas.py`, `tools.py`, tests, and the usage program.
8. Change status only after every gate passes.
