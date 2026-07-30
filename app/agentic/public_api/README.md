# Public API

> **Package:** `app/agentic/public_api`
> **Feature:** `FEAT-AGT-22` Public Agentic API and Operator Control
> **Status:** `Completed`
> **Last updated:** `2026-07-30`

> This README documents one registered root infrastructure package. It is
> **subordinate to the canonical Agentic Feature Registry** in
> `app/agentic/README.md`, which remains the sole authority for feature IDs,
> statuses, public APIs, contracts, and requirements. This file contains no
> Feature Registry section and defines no requirement of its own.

---

## 1. Read this first

This is the last of the twenty-two features, and landing it does **not** mean
the Agentic domain is finished. What exists is the machinery. What has not
happened:

- No live provider call. `FEAT-AGT-03`'s ADK binding is structurally verified
  and has never spoken to a model.
- No bound sandbox runtime. `FEAT-AGT-16` refuses an under-attested lease; it
  does not isolate anything.
- No durable store anywhere. Every store is the reference in-memory double.
- No role evaluated. `FEAT-AGT-17` is a mechanism with no versioned set behind
  it.
- No artefact promoted, no advisory reviewed, no proposal evaluated, no
  incident outside tests.
- `FEAT-AGT-09` and `FEAT-AGT-10` are not implemented at all.

The public API is a boundary over a firm that has never run for real.

---

## 2. Purpose and Boundary

### Purpose

Give an operator one authenticated, typed, bounded way to drive the firm, and
one way to stop it that does not hide what it did.

### Owns

- `AgenticDependencies` — the explicit composition record.
- The eight operator operations and their permission map.
- `OperatorOutcome` and the forbidden-payload rule.
- Disablement and its drain policy.

### Does not own

- Any behaviour. Every operation delegates to the feature that owns the thing
  it touches; this package adds a boundary, not a second implementation.
- Execution. It reserves runs and validates replays; it runs neither.
- Any deterministic safety control. See §6.

### Shared contracts

**Owned by this feature** — defined authoritatively here:

| Status | Contract | Version | Counterparty | Purpose |
|---|---|---|---|---|
| Completed | `AgenticDependencies` | `v1` | Composition root | Every port a public operation requires |
| Completed | `OperatorOutcome` | `v1` | UI/API | One typed bounded answer from the boundary |

**Consumed from other domains** — referenced only, never redefined: every
implemented Agentic feature, plus `utils.auth_context.v1` through the
structural `AuthenticatedPrincipal` Protocol.

---

## 3. Package Structure

```text
public_api/
├── __init__.py       # Feature Registry public API only
├── dependencies.py   # AgenticDependencies and the principal Protocol
├── service.py        # The operator operations and disablement
└── README.md         # This file
```

The canonical §4.22 file list plus `README.md`.

### Public API

| Export | Kind | Purpose |
|---|---|---|
| `submit_firm_request` | function | Submit one bounded governed request |
| `get_firm_run` | function | Inspect one run's durable state |
| `cancel_firm_run` | function | Cancel one non-terminal run |
| `approve_agentic_handoff` | function | Record a human approval of a staged artefact |
| `replay_firm_run` | function | Validate one isolated replay |
| `quarantine_firm_agent` | function | Classify, contain, and record one incident |
| `get_firm_audit` | function | Return one run's correlated redacted trace |
| `disable_agentic` | function | Stop new work and settle what is running |
| `build_agentic_dependencies` | function | Build the explicit composition record |
| `get_operator_operations` | function | List the registered operator operations |

`FR-AGENTIC-065` names seven operations; §4.22's key-exports column names
three of them. The column is a subset of the requirement, not a cap on it, so
all seven are here plus disablement for `FR-AGENTIC-066`.

---

## 4. Behaviour

### The dependency record is complete or it does not exist

Every port is a required field on a frozen slotted dataclass — no default, no
lazy lookup, no module-level singleton. `AgenticDependencies()` raises. A
caller cannot invoke an operator operation against a partially wired firm and
discover the gap at the point where it matters least.

### The payload is a string mapping, and that is the enforcement

`FR-AGENTIC-065` forbids exposing prompts, credentials, and provider
internals. An `OperatorOutcome` payload is `Mapping[str, str]`: there is no
nested object a `ModelProfile`, an `AgentProvenance`, or a prompt could travel
inside. `AgentProvenance` in particular carries `model_provider`,
`model_identifier`, and `base_prompt_hash`, so operator responses **project**
what an operator needs rather than returning it.

The forbidden-key rule closes the remaining route — naming the field. An
integration test renders every operator response and asserts no provider name,
no `vault://` reference, no prompt text, and no redacted credential appears
anywhere on the surface.

### Failures are mapped, never raised

Every operation returns a typed outcome. `refused` carries an enumerated
reason the caller can act on; `failed` carries a symbolic code from
`map_exception`. Nothing raw crosses the boundary — a provider or receiver
exception never reaches an operator as a traceback.

Ordinary conditions are refusals, not failures: an unknown run, an already
terminal run, a missing permission, a wrong environment, an unregistered
workflow, a transition the lifecycle machine forbids.

### Disablement stops work without hiding it

Enablement is checked **before** authentication for anything that creates or
changes work, because a disabled package should not be doing identity lookups
either. A principal holding nothing at all still gets `AGENTIC_DISABLED`.

`drain` lets non-terminal work finish; `cancel` stops it through the normal
orchestration path. Neither writes over the audit or operations stores, and a
test asserts the record count is identical before and after.

**Reads stay available while disabled.** Inspecting a run or a trace is how an
operator learns *why* the package was disabled; refusing that would make
disablement a way to hide.

Run identities are supplied rather than enumerated. `FEAT-AGT-04`'s store port
offers `load_run` and no listing, and widening a completed feature's port for
convenience would be the wrong trade.

---

## 5. What is deliberately not exported

`WF-AGT-005` names `agentic.open_sandbox()` and `agentic.stage_code_artifact()`
as planned root exports. Neither is exported, because no isolation runtime
exists to open and a function that could not do what its name promises would be
worse than the gap. `WF-AGT-005` stays `Missing`.

`FEAT-AGT-09` and `FEAT-AGT-10` are unimplemented, so no fundamental or
sentiment operation appears on the root either. A test asserts all four names
are absent.

Three earlier deferrals to this feature also remain open, and are recorded
rather than quietly closed:

| Deferred by | Still outstanding |
|---|---|
| `FEAT-AGT-16` | `open_sandbox` — needs a real isolation runtime |
| `FEAT-AGT-18` | The receiver handoff that would make `registered` reachable |
| `FEAT-AGT-19` | Submitting an advisory to Portfolio and Risk |

Each needs a receiver or runtime composition this package does not own.

---

## 6. Safety equivalence

`FR-AGENTIC-066` requires that disabling Agentic leaves deterministic safety
controls available. It does, for a structural reason: **Agentic never held
any.** The integration test asserts over every `.py` file in `app/agentic` that
the domain names no `apply_kill_switch_command`, no `check_risk_kill_switch`,
no `dispatch_order_intent`, no `evaluate_live_gate`, no
`review_allocation_proposal`, no `activate_allocation_budget`, no
`MetaTrader5`, and no `ALLOW_LIVE_MUTATIONS`.

Disabling a package that holds no safety authority cannot weaken safety. That
is the whole argument, and it is checked domain-wide rather than asserted.

---

## 7. Tests and Evidence

| Level | Location |
|---|---|
| Unit | `tests/agentic/unit/test_public_api.py` |
| Usage | `tests/agentic/usage/22_public_api.py` |
| Integration | `tests/agentic/integration/test_public_api_boundary.py` |

```bash
uv run pytest tests/agentic/unit/test_public_api.py -o addopts="" -q
```

```bash
uv run python tests/agentic/usage/22_public_api.py
```

The integration test drives the whole firm through the public API against the
real stores each owning feature ships — the run really transitions, the trace
is really redacted, the incident really contains, and the artefact really
advances through the lifecycle ledger.

### Known limits

- Everything in §1.
- No composition root binds this. `AgenticDependencies` is the shape one would
  fill; nothing fills it outside tests.
- `submit_firm_request` reserves a run. It does not execute one — that needs
  the orchestration executor and a bound runtime.

---

## 8. Change Process

1. Update the canonical Agentic README first — it owns the registry row.
2. Update this file.
3. **Never add a non-function to the package root.** The function-only rule is
   checked by test over the whole surface.
4. Never return a domain object from an operator operation. The payload is a
   string mapping so that a prompt or a credential has nowhere to travel;
   returning a contract object would reopen that route.
5. Never export a name for a capability that does not exist. §5 exists because
   that temptation is real.
6. Never let an exception cross the boundary. Map it.
7. Update `dependencies.py`, `service.py`, tests, and the usage program.
8. Change status only after every gate passes.
