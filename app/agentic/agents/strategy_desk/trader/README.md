# Trader

> **Package:** `app/agentic/agents/strategy_desk/trader`
> **Feature:** `FEAT-AGT-20` Trade Proposal Handoff
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

Turn a supported strategy thesis into a proposal a deterministic system can
evaluate, hand it to the receiver's own intake, and record what the receiver
said.

### Owns

- The provider-neutral trader definition and proposal composition.
- The immutable base role instruction in `prompt.md`.
- `TradeProposal` and `TradeProposalReceipt`.
- The mapping onto Strategy's proposal-evaluation request.
- The broker-vocabulary prohibition list.

### Does not own

- Any decision. Strategy, Portfolio, Risk, and Trading each apply their own
  complete controls. See §5.
- Any order. No field here can hold a price, a size, a venue, or a route.
- Any evaluation. The receiver evaluates signals and builds intents; this
  package neither.
- Strategy registration, position sizing, live gating, or dispatch.

### Shared contracts

**Owned by this feature** — defined authoritatively here:

| Status | Contract | Version | Counterparty | Purpose |
|---|---|---|---|---|
| Completed | `TradeProposal` | `v1` | Agentic, UI/API | A non-executable view submitted for evaluation |
| Completed | `TradeProposalReceipt` | `v1` | Agentic, UI/API | What the receiver said, and no more |

**Consumed from other domains** — referenced only, never redefined:

| Contract | Version | Owner | Used for |
|---|---|---|---|
| `AgentTask` / `AgentResult` / `AgentProvenance` / `BudgetUsage` | `v1` | Agentic `FEAT-AGT-01` | Typed task input and result envelope |
| `RoleManifest` / `FirmMandate` | `v1` | Agentic `FEAT-AGT-02` | Role resolution and prompt-integrity verification |
| `ModelProfile` / `ModelInvocation` / `AdkRuntime` | `v1` | Agentic `FEAT-AGT-03` | Governed provider-neutral execution |
| `reject_authorization_language` | `v1` | Agentic `FEAT-AGT-07` | One definition of authorization language |
| `StrategyThesis` | `v1` | Agentic `FEAT-AGT-13` | The basis a proposal rests on, and its evidence |
| `create_strategy_proposal_evaluation_request` | `v1` | Strategy `FEAT-STR-11` | The receiver's own intake contract |

---

## 2. Package Structure

```text
trader/
├── __init__.py     # Feature Registry public API only
├── agent.py        # Provider-neutral definition and proposal composition
├── prompt.md       # Immutable base role instruction
├── schemas.py      # Feature-owned proposal and receipt contracts
├── handoff.py      # Mapping and submission to receiver-owned intake
└── README.md       # This file
```

Exactly the canonical §4.20 file list; no additions. The trader registers **no
tool**: it composes from a thesis it was handed and submits through the
receiver's own intake, so there is nothing for it to read through the governed
tool path.

### Public API

| Export | Kind | Purpose |
|---|---|---|
| `submit_trade_proposal` | function | Map one proposal onto receiver intake and record the receipt |
| `TradeProposal` / `TradeProposalReceipt` | classes | Typed contracts |
| `build_trade_proposal` / `build_trade_proposal_receipt` | functions | Validated constructors |

`propose_trade` in `agent.py` is the internal composition entry point. §4.20
assigns `agent.py` no additional public export, so it is not re-exported.

---

## 3. `WF-AGT-008` step 2 names operations that cannot take a proposal

The workflow says Strategy treats the proposal as untrusted input via
`strategy.validate_strategy_ref()` and `strategy.build_trade_intent()`. Neither
can: `build_trade_intent` requires a `StrategyDecision` and a
`StrategyExecutionContext`, which are deterministic evaluation state this
domain does not have and must not fabricate.

Strategy's `FEAT-STR-11` shipped the intake this handoff was meant for.
`StrategyProposalEvaluationRequest` carries `source_proposal_id`,
`source_task_id`, `source_content_hash`, thesis and invalidation evidence
references, horizon, expiry, and an evaluation scope — and **no price, no
quantity, no order type**. The receiver's own contract already refuses
broker-native fields.

---

## 4. Behaviour

### The proposal defines nothing executable

No price, quantity, lot size, notional, stop, target, order type, venue, or
account field exists on either contract. Three tests hold the line: field-set
disjointness against `FORBIDDEN_BROKER_FIELDS`, source-text absence in every
module except the one that owns the list, and the receiver contract's own lack
of anywhere to put one.

Execution vocabulary in prose is refused too. `FEAT-AGT-07`'s
`reject_authorization_language` covers authorization; this package adds the
level-and-size vocabulary a trader must never emit — `entry price`,
`stop loss`, `take profit`, `buy at`, `market order`, `lot size`.

### The model describes; the caller decides

Instrument, strategy identity, direction, horizon, and evaluation scope are
caller arguments. The model contributes the rationale, the invalidation, and
the uncertainty, and nothing else — a model output naming a different
instrument changes nothing. Evidence references come from the **thesis**, so a
proposal cannot cite something that was never gathered.

### Only a supported thesis may be proposed

`unsupported` and `insufficient_evidence` speak for themselves. `contested` is
excluded on purpose: a thesis whose evidence conflicts is one to resolve, not
to trade, and proposing on it would bury the conflict `FEAT-AGT-13` preserved.
Refused before any model call.

### The window is bounded by the receiver's own rule

The receiver caps horizon at thirty-one days and requires expiry to fall within
the declared horizon. Both are checked here, so a proposal this domain builds
cannot fail Strategy on a constraint that could have been applied first.

### The receiver derives the request identity

`create_strategy_proposal_evaluation_request` computes the
`evaluation_request_id` and `idempotency_key` from a content digest and
**refuses a caller that supplies either**. A proposal therefore cannot arrive
pre-stamped with an identity that might collide with, or impersonate, another —
which is what makes "no privileged route" structural rather than promised.

### A receipt says no more than the receiver said

Status comes from Strategy's own enumeration: `accepted_for_evaluation`,
`rejected`, `expired`, `no_signal`. There is no value meaning "filled", and a
status outside that set cannot be recorded.

When the receiver produced a canonical intent, the receipt records **that it
exists and its identity** — never its contents. An intent is Strategy's object;
copying its fields here is how a proposal starts looking like an order.

Three further claims are unrepresentable: an intent reported against a status
that cannot produce one, an intent claimed without its identity, and evaluated
signals reported for a rejected or expired proposal.

### Results must answer this proposal

A result naming a different proposal, or the same proposal at different
content, is refused. Otherwise a receipt could describe something other than
what was submitted.

### Refusal is a complete outcome

| Reason | Condition | Before the model? |
|---|---|---|
| `THESIS_NOT_PROPOSABLE` | The thesis is not `supported` | Yes |
| `THESIS_EVIDENCE_ABSENT` | The thesis carries no evidence | Yes |
| `HORIZON_OUT_OF_BOUNDS` | The horizon is non-positive or past the receiver's bound | Yes |
| `PROPOSAL_WINDOW_INVALID` | The validity window is empty or outlives the horizon | Yes |
| `PROPOSAL_NOT_SUBMITTABLE` | Approval, sizing, price, or venue language, or a stub statement | No |
| *model reasons* | The trader itself declined | — |

`submit_trade_proposal` raises rather than refuses: an expired proposal, an
incomplete receiver result, or a result bound to different content are all
programming or integration errors, not agent outcomes.

---

## 5. What stops here

`WF-AGT-008` steps 3 and 4 belong to Risk and Trading. Nothing in this package
names `app.services.risk`, `app.services.trading`, `app.services.brokers`,
`calculate_position_size`, `evaluate_live_gate`, or `dispatch_order_intent` —
a test asserts each. Exactly one receiver operation is imported, and a test
asserts the import list is exactly:

```python
from app.services.strategy import create_strategy_proposal_evaluation_request
```

It builds a request. It does not evaluate one.

---

## 6. Tests and Evidence

| Level | Location |
|---|---|
| Unit | `tests/agentic/unit/test_trader.py` |
| Usage | `tests/agentic/usage/20_trade_proposals.py` |
| Integration | `tests/agentic/integration/test_trade_proposal.py` |

```bash
uv run pytest tests/agentic/unit/test_trader.py -o addopts="" -q
```

```bash
uv run python tests/agentic/usage/20_trade_proposals.py
```

### Known limits

- **No proposal has been evaluated.** The intake is a deterministic double.
  `evaluate_strategy_proposal` needs a hash-bound `SignalEvaluator`, a strategy
  config, point-in-time indicators, and an execution context — a full Strategy
  composition a composition root owns. No signal has been evaluated here and no
  intent constructed.
- **No receipt is persisted.** §4.20's `FR-AGENTIC-060` side effect reads
  "Receipt persistence"; there is no store in the canonical file list and no
  table for receipts. `submit_trade_proposal` returns the receipt; persisting
  it belongs to `FEAT-AGT-21` operations or `FEAT-AGT-22`.
- **Proposal quality is not verified here.** Whether the view is *good* is
  measured by `FEAT-AGT-17` evaluation against versioned sets. That mechanism
  exists, but no versioned set has been authored for this role and no grader
  calibrated, so this role has not in fact been evaluated.
- **`WF-AGT-008` remains `Missing`.** This feature is steps 1 and 5; step 2's
  real operations are `proposal_intake`, and steps 3 and 4 are Risk's and
  Trading's.
- Google ADK binding is not implemented (`FEAT-AGT-03` is `Partial`).

---

## 7. Change Process

1. Update the canonical Agentic README first — it owns the registry row.
2. Update this file.
3. Change `prompt.md` and the manifest `base_prompt_hash` together; they are
   verified against each other at startup.
4. **Never add a field to `TradeProposal` that names a price, a size, a level,
   a venue, or a route.** The absence of one is the guarantee, and a "just
   informational" number is exactly what an execution path would later consume.
5. Never add a status to `TradeProposalReceipt` that Strategy does not define.
   The receipt mirrors the receiver; inventing a state is how Agentic would
   start reporting order truth.
6. Never widen the import list beyond the single request factory.
7. Update `schemas.py`, `handoff.py`, tests, and the usage program.
8. Change status only after every gate passes.
