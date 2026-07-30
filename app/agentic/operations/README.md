# Operations

> **Package:** `app/agentic/operations`
> **Feature:** `FEAT-AGT-21` Observability, Incidents, and Operational Control
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

Show what a run did, stop what has gone wrong in a way that does not depend on
who noticed, and let a run be re-examined without letting it act again.

### Owns

- `AgenticTrace`, `IncidentRecord`, `ReplayRequest`, `ReplayOutcome`.
- The ten required span kinds and the nine incident kinds.
- The containment table mapping incident kind to required action.
- The append-only operations ledger port and its schema.

### Does not own

- Redaction. `FEAT-AGT-06` redacts at the memory boundary; this package
  inherits the result and defines no second redactor. See §3.
- Role state. `quarantine_agent` records the decision; the roster is re-issued
  by a governance manifest change. Same wall `FEAT-AGT-17` documented.
- Execution. `replay_run` validates a replay and runs nothing. See §5.
- Telemetry emission. It reads the audit store the firm already writes to.

### No role, no prompt, no model

This is a root infrastructure package. There is no `prompt.md`, no `agent.py`,
and no model invocation. Classifying an incident and containing it must be
deterministic; a model here would be a place to argue that an incident was not
one. A test asserts the package names none of the runtime symbols that would
make a model call possible.

### Shared contracts

**Owned by this feature** — defined authoritatively here:

| Status | Contract | Version | Counterparty | Purpose |
|---|---|---|---|---|
| Completed | `AgenticTrace` | `v1` | Agentic, UI/API | One correlated redacted view of a run |
| Completed | `IncidentRecord` | `v1` | Agentic, UI/API | A classified incident, its containment, and its preserved evidence |
| Completed | `ReplayRequest` | `v1` | Agentic, UI/API | A replay declared against immutable references |
| Completed | `ReplayOutcome` | `v1` | Agentic, UI/API | What a validated replay was permitted to do |

**Consumed from other domains** — referenced only, never redefined:

| Contract | Version | Owner | Used for |
|---|---|---|---|
| `WorkflowRun` / `cancel_task` / `is_terminal_state` | `v1` | Agentic `FEAT-AGT-04` | Containment through the normal cancellation path |
| `MemoryRecord` / `retrieve_memory` | `v1` | Agentic `FEAT-AGT-06` | Redacted audit evidence and its content digests |
| Data migration protocol | `v1` | Data | Declaring the ledger schema Data executes |

---

## 2. Package Structure

```text
operations/
├── __init__.py     # Feature Registry public API only
├── models.py       # Trace, incident, replay contracts and the containment table
├── migrations.py   # Operations-ledger schema executed by Data
├── repository.py   # Ledger port and its deterministic in-memory double
├── service.py      # get_run_trace, quarantine_agent, replay_run
└── README.md       # This file
```

The canonical §4.21 file list plus `README.md`, which every other package
carries.

### Public API

| Export | Kind | Purpose |
|---|---|---|
| `get_run_trace` | function | Assemble one correlated redacted trace |
| `quarantine_agent` | function | Classify, contain, and record one incident |
| `replay_run` | function | Validate one replay against immutable references |
| `get_run_incidents` / `get_quarantined_roles` / `verify_references` | functions | Read the ledger and check references |
| `AgenticTrace` / `IncidentRecord` / `ReplayRequest` / `ReplayOutcome` | classes | Typed contracts |
| `build_agentic_trace` / `build_incident_record` / `build_replay_request` | functions | Validated constructors |
| `REQUIRED_SPAN_KINDS` / `INCIDENT_KINDS` / `required_containment` | constants and function | The declared coverage and containment rules |
| `build_in_memory_operations_store` | function | Deterministic non-durable ledger |
| `get_operations_migration_statements` / `build_operations_migration_request` | functions | Declared schema, executed by Data |

---

## 3. Redaction is inherited, not redone

Every record a trace is assembled from was redacted by `store_memory` before it
was persisted, and carries the `redacted_paths` that were removed. The trace
carries the union of those paths, so an operator can see *that* redaction
happened without the trace ever having held the material.

A test asserts this package names `redact_mapping_value`, `redact_text_value`,
and `RedactionPolicy` nowhere. A second definition of what counts as a secret
is a second answer to the same question, and the two would eventually disagree.

---

## 4. Behaviour

### A trace covers every required span or does not exist

`REQUIRED_SPAN_KINDS` holds the ten things `FR-AGENTIC-061` names, validated by
**set equality**. `get_run_trace` refuses when any kind has no record, naming
the missing ones.

A record declares its span under the `span` content key. An unlabelled record
is counted — it happened — but covers nothing, and a record labelling a span
nobody agreed to does not widen the trace. Unlabelled telemetry is not
observability, and the refusal says so rather than assembling a partial view
that looks complete.

Cost is summed from `cost` spans. An unreadable cost is skipped with a warning
rather than silently read as zero; the span still counts as covered, because a
defective emitter is a different problem from an absent one.

### Containment is a property of the kind

| Incident kind | Action | Why |
|---|---|---|
| `injection`, `privilege`, `data_poisoning`, `sandbox` | `quarantine_and_cancel` | A hijacked or poisoned role must stop *and* not take the next task; cancelling the run alone leaves it eligible |
| `drift` | `quarantine` | Drift is a property of the role, not of one run, so the run may finish while the role stops taking new work |
| `cost`, `provider`, `runaway_loop`, `schema` | `cancel` | A bounded failure of one run; the role is not implicated |

The action is derived from the kind, never supplied by the caller, and
`IncidentRecord` rejects a record whose action disagrees with its kind. A
`quarantine` that names no role, and a `cancel` that names one, are both
unrepresentable — either would misreport what happened.

Cancellation goes through `orchestration.cancel_task`, the same path any
operator cancellation takes. A run that is already terminal is **not**
re-cancelled: the incident is recorded against its real state, because
rewriting a terminal outcome is not this feature's to do.

### Evidence is preserved, not discarded

`preserved_evidence_refs` is required and non-empty, and a checkpoint reference
is required. An incident that contained something and dropped what caused it
cannot be constructed. One classified incident per kind per correlated run: a
second report is refused rather than allowed to replace the first and its
evidence, in the in-memory double and by a `UNIQUE (run_id, correlation_id,
kind)` constraint in the durable table.

### Replay is isolated by the type

`environment` is `Literal["sandbox"]`, so a production replay is
unconstructable rather than merely refused. Every reference is a content
digest, and `replay_run` proves each one still matches what the store holds —
replaying against mutated evidence is not a replay. `ReplayOutcome` rejects any
non-zero `side_effects_attempted`, and defines no tool port, receiver, adapter,
or writer field.

---

## 5. What this feature decides and does not do

**It records a quarantine; it does not disable a role.** Governance exposes no
role-state mutation path — the same wall `FEAT-AGT-17` hit deciding
`disable`/`retire`. `get_quarantined_roles` tells a composition root which
roles an incident has implicated; acting on that is a governance manifest
re-issue.

**It validates a replay; it does not run one.** Re-executing a workflow needs
the orchestration executor and a bound runtime. `ReplayOutcome.executed` is
`False` because nothing here can make it anything else.

---

## 6. Tests and Evidence

| Level | Location |
|---|---|
| Unit | `tests/agentic/unit/test_operations.py` |
| Usage | `tests/agentic/usage/21_operations.py` |
| Integration | `tests/agentic/integration/test_incident_recovery.py` |

```bash
uv run pytest tests/agentic/unit/test_operations.py -o addopts="" -q
```

```bash
uv run python tests/agentic/usage/21_operations.py
```

The integration test uses the real `FEAT-AGT-04` and `FEAT-AGT-06` in-memory
stores rather than stand-ins written here, so the run really transitions, the
records are really redacted, and a terminal run really refuses to resume.

### Known limits

- **Completeness is enforced on assembly, not on emission.** A trace rejects
  incomplete coverage; nothing here can make a call site emit its span. Whether
  every emitter tags every span is a composition concern no test in this
  package settles, and a firm whose emitters stay silent gets no trace at all
  rather than a misleadingly complete one.
- **No durable store is bound.** `build_in_memory_operations_store` is a
  reference implementation; the uniqueness rules hold within one process until
  a composition root binds the Data-owned writer.
- **No incident has occurred.** This is the mechanism. Nothing has traversed it
  outside tests.
- **`WF-AGT-010` remains `Missing`.** Steps 1 through 4 land here; step 5 is
  validated rather than executed, and the workflow row also names
  `FR-AGENTIC-066`, which is `FEAT-AGT-22`'s.

---

## 7. Change Process

1. Update the canonical Agentic README first — it owns the registry row.
2. Update this file.
3. Never add a redactor. Redaction belongs to `FEAT-AGT-06`; a second one here
   would be a second answer to what counts as a secret.
4. Never let the containment table take a caller argument. The point is that
   the same incident contains the same way whoever reports it.
5. Never widen `ReplayEnvironment` beyond `sandbox`, and never let
   `side_effects_attempted` accept a non-zero value.
6. Adding a span or incident kind invalidates every existing trace or record by
   design — add the test that shows the old shape is now refused.
7. Update `models.py`, `service.py`, `repository.py`, `migrations.py`, tests,
   and the usage program.
8. Change status only after every gate passes.
