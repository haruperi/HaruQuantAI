# Experiment Designer

> **Package:** `app/agentic/agents/experimentation/experiment_designer`
> **Feature:** `FEAT-AGT-14` Experiment and Simulation Coordination
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

Turn a strategy thesis into a pre-registered protocol that could refute it,
submit the receiver's own run request, and bind a verdict to exactly what that
run returned.

### Owns

- The provider-neutral Experiment Designer agent definition.
- The immutable base role instruction in `prompt.md`.
- The `ExperimentSpec` and `ExperimentVerdict` schemas.
- The experiment-ledger schema declarations and the persistence port.

### Does not own

- Execution. Simulation runs backtests; this role submits and reads.
- Any simulation request or result. Both belong to the receiver and are never
  constructed here.
- Any metric, fill, return, or performance value.
- Migration execution. Data owns the ledger, checksums, and write locks; this
  package declares statements only.
- Any approval, position size, or recommendation to trade.

### Shared contracts

**Owned by this feature** — defined authoritatively here:

| Status | Contract | Version | Counterparty | Purpose |
|---|---|---|---|---|
| Completed | `ExperimentSpec` | `v1` | Agentic, UI/API | Pre-registered protocol binding inputs, splits, embargo, costs, seed, baseline, metrics, stop rules, and the falsification outcome |
| Completed | `ExperimentVerdict` | `v1` | Agentic, UI/API | Run-bound reading distinguishing discovery, validation, holdout, and null-data evidence |

**Consumed from other domains** — referenced only, never redefined:

| Contract | Version | Owner | Used for |
|---|---|---|---|
| `AgentTask` / `AgentResult` / `AgentProvenance` / `BudgetUsage` | `v1` | Agentic `FEAT-AGT-01` | Typed task input and result envelope |
| `RoleManifest` / `FirmMandate` | `v1` | Agentic `FEAT-AGT-02` | Enabled role resolution and prompt-integrity verification |
| `ModelProfile` / `ModelInvocation` / `AdkRuntime` | `v1` | Agentic `FEAT-AGT-03` | Governed provider-neutral execution |
| `AgentPolicy` / `ToolPolicy` / `call_governed_tool` | `v1` | Agentic `FEAT-AGT-05` | Deny-by-default tool authorization |
| `Hypothesis` / `StrategyThesis` | `v1` | Agentic `FEAT-AGT-13` | The thesis under test and its rejection criteria |
| `simulation.backtest_request.v1` / `simulation.result.v1` | `v1` | Simulation | Receiver-owned request and result |
| Migration request and step builders | `v1` | Data | Ledger schema declaration |

---

## 2. Package Structure

```text
experiment_designer/
├── __init__.py      # Feature Registry public API only
├── agent.py         # Provider-neutral definition and both public use cases
├── prompt.md        # Immutable base role instruction
├── schemas.py       # Feature-owned typed protocol and verdict
├── tools.py         # Governed Simulation bindings and result-binding check
├── migrations.py    # Experiment-ledger schema declarations
├── repository.py    # Ledger port and deterministic in-memory double
└── README.md        # This file
```

No `evaluator.py` or sandbox file exists, because the canonical module
specification (§4.14) declares none.

### Public API

| Export | Kind | Purpose |
|---|---|---|
| `design_experiment` | function | Design and pre-register one protocol |
| `coordinate_simulation` | function | Execute one receiver-owned run and bind a verdict |
| `ExperimentSpec` | class | Pre-registered protocol |
| `ExperimentVerdict` | class | Run-bound verdict |
| `build_experiment_spec` / `build_experiment_verdict` | functions | Validated constructors |

`tools.py`, `migrations.py`, and `repository.py` are internal to the feature,
as the module specification requires. `SimulationPort` and
`AgenticExperimentStore` are the injection points a composition root binds.

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

### The protocol is pre-registered, and the digest proves it

`build_experiment_spec` derives `spec_hash` over the protocol as declared —
including the falsification outcome. Rewriting the criterion afterwards
produces a different digest, so a verdict carrying the original `spec_hash`
cannot have been matched against a criterion invented after the run.

Configuration comes from the caller: windows, baseline, cost model, seed, and
metrics are deterministic inputs. The model contributes the falsification
outcome, the stop rules, and the leakage controls — the design judgement, not
the configuration. A model that emits its own `seed` or `baseline_ref` is
ignored.

Split validity has one source of truth. `validate_split_windows` is called by
`ExperimentSpec` so an invalid protocol is unrepresentable, and by `agent.py`
first so an invalid one is refused before a model is paid to design for it.

**Falsifiability is not re-checked here.** `FEAT-AGT-13` makes a `Hypothesis`
without a rejection criterion unrepresentable, so a thesis that could not fail
cannot reach this feature. Adding a runtime guard would be dead code.

### Holdout is consumed, not borrowed

The ledger grants one holdout claim per protocol digest. `reserve_holdout`
succeeds once and refuses every later attempt, and the durable table makes
`spec_hash` its primary key, so a second look cannot be recorded across
processes either. `coordinate_simulation` checks before calling the receiver,
so the second look never executes — and the store refuses independently, so
bypassing the check changes nothing.

`ExperimentVerdict` closes the loop: a verdict citing holdout evidence without
recording `holdout_consumed` is rejected at construction.

### Coordination is not authorship

The caller supplies the receiver's request; it is passed through unchanged and
its hash recorded. On return, `verify_result_binding` checks that the result
carries complete lineage, reports a completed run, and agrees with the
submitted `config_hash`. A result that does not bind is refused as
`RESULT_NOT_FOR_REQUEST` — **before** the verdict model is invoked, so a
mismatched result is never handed to a model for reconciliation.

The package imports neither `SimulationBacktestRequestV1` nor
`SimulationResult`, and a test asserts that no module names them. There is no
site at which Agentic could author either contract.

### Every conclusion names its run

`ExperimentVerdict.conclusions` is keyed by the run identifier the **receiver**
returned, never by one the model supplied, and `evidence_classes` is validated
against the identical key set. A model that emits `run_id` in its output has no
effect on the keys.

### Refusal is a complete outcome

| Reason | Operation | Condition |
|---|---|---|
| `HYPOTHESES_ABSENT` | design | No hypothesis was named |
| `INPUTS_ABSENT` | design | No versioned input was named |
| `BASELINE_ABSENT` | design | No baseline to compare against |
| `SPLITS_INVALID` | design | Splits missing, out of order, overlapping, or inside the embargo |
| `PROTOCOL_NOT_REGISTERED` | coordinate | The protocol was not pre-registered before the run |
| `HOLDOUT_ALREADY_CONSUMED` | coordinate | This protocol's one holdout look is spent |
| `SIMULATION_TOOL_DENIED` | coordinate | The backtest tool is unregistered or authorization denied it |
| `RESULT_NOT_FOR_REQUEST` | coordinate | The returned result does not bind to the submitted request |
| *model reasons* | both | The designer itself declined |

Every design refusal and both pre-run coordination refusals occur before the
model is reached.

---

## 5. Persistence

`migrations.py` declares four tables — `agentic_experiment_specs`,
`agentic_experiment_runs`, `agentic_experiment_holdout_use`, and
`agentic_experiment_verdicts` — plus two indexes. It opens no connection and
executes nothing; a composition root passes the request to Data's
`run_domain_migrations`.

The holdout table's `spec_hash TEXT PRIMARY KEY` is the durable enforcement
point for scarcity. Every other guard in this feature is in-process; that
constraint is what survives a restart.

---

## 6. Tests and Evidence

| Level | Location |
|---|---|
| Unit | `tests/agentic/unit/test_experiment_designer.py` |
| Usage | `tests/agentic/usage/14_experiments.py` |
| Integration | `tests/agentic/integration/test_experiment_coordination.py` |

```bash
uv run pytest tests/agentic/unit/test_experiment_designer.py -o addopts="" -q
```

```bash
uv run python tests/agentic/usage/14_experiments.py
```

### Known limits

- The Simulation receiver arrives through `build_simulator_port`, which binds
  an injected facade. Wiring it to the real Simulation package root is a
  composition-root concern and is not exercised here; tests use deterministic
  doubles, and no backtest executes.
- Only the in-memory ledger exists. The durable store Data owns is declared but
  not implemented, so cross-process holdout scarcity is proven by the schema
  constraint rather than by an executed migration.
- `simulation.resolve_idempotent_run` is registered as an eligible tool and
  exposed on the port, but `agent.py` does not yet call it; idempotent
  re-attachment to a prior run is not implemented.
- `WF-AGT-003` remains `Missing`. This feature implements steps 3 through 5;
  steps 1 and 2 need `FEAT-AGT-09`, blocked on `FEAT-DATA-16`.
- Design *quality* is not verified here. Whether a protocol is well-posed is
  measured by `FEAT-AGT-17` evaluation against versioned sets. That mechanism
  now exists, but no versioned set has been authored for this role and no
  grader has been calibrated against it, so this role has not in fact been
  evaluated.

---

## 7. Change Process

1. Update the canonical Agentic README first — it owns the registry row.
2. Update this file.
3. Change `prompt.md` and the manifest `base_prompt_hash` together; they are
   verified against each other at startup.
4. Migrations are additive only. Never edit a released statement; add a new
   migration id.
5. Update `schemas.py`, `tools.py`, `repository.py`, tests, and the usage
   program.
6. Change status only after every gate passes.
