# Lifecycle

> **Package:** `app/agentic/lifecycle`
> **Feature:** `FEAT-AGT-18` Artefact Promotion and Lifecycle
> **Status:** `Completed`
> **Last updated:** `2026-07-30`

> This README documents one registered root infrastructure package. It is
> **subordinate to the canonical Agentic Feature Registry** in
> `app/agentic/README.md`, which remains the sole authority for feature IDs,
> statuses, public APIs, contracts, and requirements. This file contains no
> Feature Registry section and defines no requirement of its own.

---

## 1. Purpose and Boundary

### Purpose

Decide whether a staged artefact has earned promotion, and record what happened
to it in a history that cannot be rewritten.

### Owns

- `PromotionEvidencePacket`, `LifecycleRecord`, `PromotionAssessment`.
- The five `FR-AGENTIC-053` gates and the order they run in.
- The artefact state machine and its predecessor table.
- The append-only transition ledger port and its schema.

### Does not own

- Any registration. Strategy alone registers a strategy version. See §5.
- Any evidence. The packet carries what `FEAT-AGT-14`, `-15`, `-16`, and `-17`
  produced; nothing here authors, recomputes, or re-derives it.
- Grading, backtesting, or search. No receiver is called from this package.
- Role state. `FEAT-AGT-17` decides whether a *role* continues; this feature
  decides about an *artefact*.

### No role, no prompt, no model

This is a root infrastructure package, not a registered agent. There is no
`prompt.md`, no `agent.py`, and no model invocation anywhere in it. Promotion is
a decision procedure over evidence others produced; adding a model would create
a place where one could argue its way past a gate. A test asserts the package
names none of the runtime symbols that would make a model call possible.

### Shared contracts

**Owned by this feature** — defined authoritatively here:

| Status | Contract | Version | Counterparty | Purpose |
|---|---|---|---|---|
| Completed | `PromotionEvidencePacket` | `v1` | Agentic, UI/API | The complete ordered evidence one promotion rests on |
| Completed | `LifecycleRecord` | `v1` | Agentic, UI/API | One append-only entry in an artefact's history |
| Completed | `PromotionAssessment` | `v1` | Agentic, UI/API | What the deterministic gates concluded |

**Consumed from other domains** — referenced only, never redefined:

| Contract | Version | Owner | Used for |
|---|---|---|---|
| `CodeArtifact` | `v1` | Agentic `FEAT-AGT-16` | The artefact being promoted, and its provenance |
| `ExperimentVerdict` | `v1` | Agentic `FEAT-AGT-14` | Out-of-sample evidence and holdout consumption |
| `SweepVerdict` | `v1` | Agentic `FEAT-AGT-15` | Cumulative search and holdout consumption |
| `CritiqueMemo` | `v1` | Agentic `FEAT-AGT-17` | Adversarial challenge and preserved blocking concerns |
| `utils.auth_context.v1` | `v1` | Utils | Human authentication of the approval |
| Data migration protocol | `v1` | Data | Declaring the ledger schema Data executes |

---

## 2. Package Structure

```text
lifecycle/
├── __init__.py      # Feature Registry public API only
├── models.py        # Packet, record, assessment, and the transition machine
├── service.py       # assess_promotion and transition_artifact
├── migrations.py    # Append-only ledger schema executed by Data
├── repository.py    # Ledger port and its deterministic in-memory double
└── README.md        # This file
```

**`migrations.py` and `repository.py` are additions to the canonical §4.18 file
list.** `FR-AGENTIC-054` requires transitions be append-only. An in-process
check vanishes on restart, so without a store that *rejects* a second write at
a position already recorded, "append-only" is a convention rather than a
property. The composite primary key `(artifact_hash, sequence)` is what makes
it survive a restart — the same argument that earned `FEAT-AGT-14` its holdout
table. The port follows the domain rule that no package outside Data implements
a database writer.

### Public API

| Export | Kind | Purpose |
|---|---|---|
| `assess_promotion` | function | Run the five gates over assembled evidence |
| `transition_artifact` | function | Append one governed transition |
| `get_artifact_state` / `get_artifact_history` / `can_transition` / `is_settled` | functions | Read the ledger |
| `PromotionEvidencePacket` / `LifecycleRecord` / `PromotionAssessment` | classes | Typed contracts |
| `build_promotion_evidence_packet` / `build_lifecycle_record` / `build_promotion_assessment` | functions | Validated constructors |
| `validate_transition` / `permitted_next_states` / `is_terminal_state` | functions | The transition machine |
| `build_in_memory_lifecycle_store` | function | Deterministic non-durable ledger |
| `get_lifecycle_migration_statements` / `build_lifecycle_migration_request` | functions | Declared schema, executed by Data |

---

## 3. Behaviour

### The packet is complete or it does not exist

Every evidence field on `PromotionEvidencePacket` is non-defaulted. A packet is
not a container that happens to hold what was available; it is the assertion
that the whole record exists, and the absence of any part makes the assertion
unconstructable. `packet_hash` covers the whole assembly, so evidence appended
after approval yields a different packet rather than a quietly extended one.

### Approval comes from a human, not a process

`approval_refusal` refuses a `SERVICE_ACCOUNT`, a principal without
`agentic:approve_promotion`, a principal issued for a different environment,
and an absent principal. The structural `ApprovingPrincipal` Protocol names only
the four fields approval reads, so a real `utils.auth_context.v1` satisfies it
without a deep import.

### Five gates, in the requirement's own order

| Gate | Termination reason | Read from |
|---|---|---|
| Leakage | `leakage_detected` | `ExperimentVerdict.evidence_classes` — no `validation` or `holdout` class means the result was measured on the data that selected it |
| Holdout reuse | `holdout_reused` | `holdout_consumed` on **both** the experiment and the sweep |
| Search budget | `search_budget_exhausted` | `SweepVerdict.lifetime_trials` against the packet's declared ceiling |
| Provenance | `provenance_incomplete` | The artefact's four provenance digests, and `promotion_status != "ready"` |
| Approval | `approval_absent` | The principal check above |

Every failed gate is reported; the first in requirement order becomes the
`termination_reason`. A gate failure is a **result, not an exception** — the
caller sees the whole picture rather than only the gate that ran first.

Blocking concerns from the critique survive a *passing* assessment. A promotion
that clears every gate while a critic's concern stands is a fact the record
should carry, not one it should drop.

### Transitions

```text
staged ──▶ evaluated ──▶ approved ──▶ registered ──▶ demoted
   │            │            │
   └────────────┴────────────┴──────▶ research_only
```

- **Append-only** — the ledger accepts position `n` once. The in-memory double
  refuses a rewrite; the durable table refuses it with a composite primary key.
- **Version-specific and never inherited** — records are keyed on
  `artifact_hash`, not `artifact_id`. Change one generated byte and the digest
  changes, so the altered artefact begins at `staged` with an empty history. It
  cannot inherit its predecessor's approval, because as far as the ledger is
  concerned it has no predecessor.
- **Non-skippable** — the current state is read from the ledger, never supplied
  by the caller, so holding a valid packet does not let anyone jump from
  `staged` to `approved`.
- **Automatically demotable** — `registered → demoted` needs no packet and no
  approval. Withdrawing an artefact should never be harder than promoting it.
- **Terminal** — nothing follows `research_only` or `demoted`. Re-assembling a
  passing packet does not reopen a terminated artefact.

---

## 4. Tests and Evidence

| Level | Location |
|---|---|
| Unit | `tests/agentic/unit/test_lifecycle.py` |
| Usage | `tests/agentic/usage/18_lifecycle.py` |
| Integration | `tests/agentic/integration/test_artifact_promotion.py` |

```bash
uv run pytest tests/agentic/unit/test_lifecycle.py -o addopts="" -q
```

```bash
uv run python tests/agentic/usage/18_lifecycle.py
```

Nothing is written to disk. The ledger is the in-memory double throughout, and
the migration module declares statements without opening a connection — a test
asserts it names no `connect`, `execute`, or `cursor`.

### Known limits

- **No artefact has been promoted.** This feature is the mechanism. Nothing has
  traversed it outside tests, and no receiver has registered anything.
- **`registered` is a state this feature cannot cause.** The state machine is
  complete rather than partial, but until `FEAT-AGT-22` supplies the handoff,
  nothing in production reaches that branch. It is exercised in tests only.
- **The leakage gate detects one form of leakage.** It establishes that the
  result was measured out of sample. It cannot see lookahead inside generated
  code — that is `FEAT-AGT-16`'s and the simulator's problem, and neither is
  reachable from here.
- **`lifetime_trial_ceiling` is caller-supplied.** No durable counter backs it;
  the gate compares the sweep's reported cumulative trials against a number the
  packet declares.
- **The durable store is not bound.** `build_in_memory_lifecycle_store` is a
  reference implementation. Until a composition root binds the Data-owned
  writer, append-only holds within one process only.
- **`WF-AGT-SEC` remains `Missing`.** This feature implements steps 5 and 6;
  steps 1–4 belong to `FEAT-AGT-16` and `-17`, and step 7 is the receiver's.

---

## 5. What this feature records and does not do

It records. It does not register.

`WF-AGT-SEC` step 7 reads *"the receiver domain alone registers the artefact —
`strategy.register_strategy_version()`"*. This package never calls it, never
constructs a `StrategyRegistrationRequest`, and never imports Strategy or the
simulator; tests assert all three. Recording `registered` means a receiver
registered the version, not that this feature caused it. Separating the record
from the act is what makes the record trustworthy.

---

## 6. Change Process

1. Update the canonical Agentic README first — it owns the registry row.
2. Update this file.
3. Never add a state without adding its row to `_PREDECESSORS`; a state absent
   from every predecessor set is unreachable, which is a silent failure.
4. Never key a record on `artifact_id`. Keying on the digest is the whole of
   non-inheritance, and changing it would let a modified artefact inherit an
   approval granted to a different one.
5. Never relax the append-only check to an upsert.
6. Update `models.py`, `service.py`, `repository.py`, `migrations.py`, tests,
   and the usage program.
7. Change status only after every gate passes.
