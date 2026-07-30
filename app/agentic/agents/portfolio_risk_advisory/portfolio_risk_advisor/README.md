# Portfolio and Risk Advisor

> **Package:** `app/agentic/agents/portfolio_risk_advisory/portfolio_risk_advisor`
> **Feature:** `FEAT-AGT-19` Portfolio and Risk Advisory
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

Describe how exposure is distributed and what could go wrong with it, and hand
that description to the domains that decide.

### Owns

- The provider-neutral advisor definition and its two operations.
- The immutable base role instruction in `prompt.md`.
- `AllocationProposal` and `RiskAdvisory`.
- The eight required risk kinds.
- The advisor-specific executable-language vocabulary. See §3.

### Does not own

- Any decision. Portfolio and Risk apply their complete normal controls to any
  request submitted to them, and may reject this advice in full. See §5.
- Any submission. Nothing here constructs or sends a receiver request; that is
  `FEAT-AGT-22`'s.
- Any number. Exposure, correlation, headroom, and mandate scope all arrive as
  evidence from their owning domains.
- Deliberation. `FEAT-AGT-07` runs the council; this package consumes its
  preserved dissent rather than re-implementing it.

### Shared contracts

**Owned by this feature** — defined authoritatively here:

| Status | Contract | Version | Counterparty | Purpose |
|---|---|---|---|---|
| Completed | `AllocationProposal` | `v1` | Agentic, UI/API | Non-binding relative-emphasis view carrying its own expiry |
| Completed | `RiskAdvisory` | `v1` | Agentic, UI/API | Independent critique across eight risk kinds |

**Consumed from other domains** — referenced only, never redefined:

| Contract | Version | Owner | Used for |
|---|---|---|---|
| `AgentTask` / `AgentResult` / `AgentProvenance` / `BudgetUsage` | `v1` | Agentic `FEAT-AGT-01` | Typed task input and result envelope |
| `RoleManifest` / `FirmMandate` | `v1` | Agentic `FEAT-AGT-02` | Role resolution and prompt-integrity verification |
| `ModelProfile` / `ModelInvocation` / `AdkRuntime` | `v1` | Agentic `FEAT-AGT-03` | Governed provider-neutral execution |
| `AgentPolicy` / `ToolPolicy` / `call_governed_tool` | `v1` | Agentic `FEAT-AGT-05` | Deny-by-default tool authorization |
| `AgenticMemoryStore` / `store_memory` | `v1` | Agentic `FEAT-AGT-06` | Governed audit of every evidence read |
| `DissentRecord` / `reject_authorization_language` | `v1` | Agentic `FEAT-AGT-07` | Preserved minority positions; one definition of authorization language |
| `build_portfolio_allocation_evidence` | `v1` | Analytics | Non-binding allocation evidence |
| `assess_common_mode_exposure` / `measure_cross_account_correlation` | `v1` | Portfolio | Shared-scenario and correlation observations |
| `get_account_state_snapshot` | `v1` | Data | Account-scope observations |
| `load_firm_mandate` | `v1` | Risk | Mandate identity and scope |

All five receiver operations are reached **through an injected port**, never by
import. Their real signatures want `Decimal` maps of loss-at-stop by account, a
connected broker adapter, and an analytics run config; Agentic constructing any
of those would be Agentic authoring receiver inputs.

---

## 2. Package Structure

```text
portfolio_risk_advisor/
├── __init__.py      # Feature Registry public API only
├── agent.py         # Provider-neutral definition and the two public use cases
├── prompt.md        # Immutable base role instruction
├── schemas.py       # Feature-owned proposal and advisory contracts
├── tools.py         # Governed Analytics/Portfolio/Risk/account bindings
└── README.md        # This file
```

Exactly the canonical §4.19 file list; no additions.

### Public API

| Export | Kind | Purpose |
|---|---|---|
| `advise_portfolio` | function | Produce one non-binding proposal from current evidence |
| `critique_risk` | function | Critique one proposal across all eight risk kinds |
| `AllocationProposal` / `RiskAdvisory` | classes | Typed contracts |
| `build_allocation_proposal` / `build_risk_advisory` | functions | Validated constructors |

---

## 3. Non-binding is three structural facts, not an adjective

**No executable quantity exists.** `relative_weights` are bounded strings keyed
by candidate. The model defines no lot size, notional, quantity, price, or order
field, so there is no value in a proposal that an execution path could consume
even if one were handed the object by mistake. A test asserts the field set is
disjoint from `FORBIDDEN_EXECUTABLE_FIELDS`.

**Authorization language is refused, from one definition.** `FEAT-AGT-07`'s
`reject_authorization_language` is reused rather than restated, so the domain
keeps a single account of what reads as an authorization.

On top of it, this package adds the **level-and-price vocabulary** specific to
an advisor: `entry price`, `stop loss`, `take profit`, `buy at`, `sell at`,
`deploy to live`, `units of`. Naming an entry price authorizes nothing in the
deliberation sense, but it produces something executable — which is precisely
what a non-binding proposal must not contain.

**Expiry is mandatory and strict.** `expires_at` must be strictly after
`issued_at`, so an already-expired proposal cannot be constructed. Critiquing an
expired proposal is refused before any model call, because advice about a
portfolio state that no longer holds is worse than no advice.

---

## 4. Behaviour

### Freshness comes from the receivers, not the model

Every read must carry an `observed_at` instant. Evidence without one is refused
`EVIDENCE_UNDATED`; evidence older than the caller's declared bound is refused
`EVIDENCE_STALE`. **An unreadable or naive instant counts as stale** — evidence
whose age cannot be established is not fresh evidence. All of this happens
before the provider is reached.

### Scope comes from Risk

`mandate_id`, `mandate_version`, `asset_class`, and `base_currency` are copied
from what `risk.load_firm_mandate` returned. The model is never asked and never
believed about the scope it is bounded by, so a proposal cannot quietly widen
its own asset class. An incomplete mandate refuses `MANDATE_SCOPE_UNAVAILABLE`
before any model call.

### Risk coverage is exact

All eight kinds — mandate, barrier, tail, concentration, liquidity,
correlation, operational, model — validated by **set equality**. An advisory
missing liquidity is unrepresentable, not thinner; a ninth kind is refused just
as firmly. Each assessment must clear 24 characters and must not read as
reassurance (`no concerns`, `looks good`, `lgtm`, `risk-free`).

### It emits no approval, by absence

`RiskAdvisory` has no verdict, no severity, no boolean. Its whole field set is
`advisory_id`, `task_id`, `proposal_id`, `proposal_hash`, `portfolio_id`,
`assessments`, `unresolved_risks`, `retained_dissent`, `evidence_refs`,
`issued_at`. There is nothing on it a caller could read as consent.

### Dissent comes from the record

`retained_dissent` is populated from a `DeliberationRecord`'s unresolved
positions, not from the model. A synthesis that quietly drops a minority
position misrepresents the discussion it came from.

### Refusal is a complete outcome

| Reason | Condition | Before the model? |
|---|---|---|
| `ADVISORY_TOOL_DENIED` | An evidence tool is unregistered or denied | Yes |
| `EVIDENCE_UNDATED` | A read returned no observation time | Yes |
| `EVIDENCE_STALE` | A read is older than the declared bound | Yes |
| `MANDATE_SCOPE_UNAVAILABLE` | The mandate omits identity or scope | Yes |
| `ADVICE_VALIDITY_INVALID` | The requested validity window is not positive | Yes |
| `PROPOSAL_EXPIRED` | The proposal under critique has expired | Yes |
| `PROPOSAL_NOT_ADVISORY` | Approval, sizing, or price language, or no candidate | No |
| `RISK_COVERAGE_INCOMPLETE` | A risk kind is missing, unknown, stub, or reassuring | No |
| *model reasons* | The advisor itself declined | — |

---

## 5. The receiver decides

Nothing in this package imports Portfolio, Risk, Analytics, or Data — a test
asserts it — and nothing constructs an `AllocationReviewRequest` or calls
`review_allocation_proposal`.

What the proposal carries is what a receiver rejects on: identity and digest,
mandate scope, evidence references, and observation times. Whether that is
enough is Risk's judgement, not this feature's.

The integration test and the usage program demonstrate this with **Risk's own
contract**: a projection missing evidence hashes, missing components, carrying
an incompatible runtime profile and execution route, or a rebalance with no
plan is rejected by `AllocationReviewRequest` itself. Those projections are
assembled in the tests, never in production.

---

## 6. Tests and Evidence

| Level | Location |
|---|---|
| Unit | `tests/agentic/unit/test_portfolio_risk_advisor.py` |
| Usage | `tests/agentic/usage/19_advisory.py` |
| Integration | `tests/agentic/integration/test_advisory_council.py` |

```bash
uv run pytest tests/agentic/unit/test_portfolio_risk_advisor.py -o addopts="" -q
```

```bash
uv run python tests/agentic/usage/19_advisory.py
```

### Known limits

- **No portfolio has been advised.** No evidence port is bound to a real
  receiver, no advice has reached Portfolio or Risk, and no receiver has
  reviewed anything.
- **One role, two operations.** The firm-organization table names a Portfolio
  Advisor, a Risk Critic, and a Compliance Critic; §4.19 registers one leaf
  package. `critique_risk` is therefore adversarial by construction rather than
  by separate agent. Independence across genuinely separate participants is
  `FEAT-AGT-07`'s, and this package consumes its record rather than replacing
  it.
- **Freshness rests on a caller-declared bound.** The port reports observed
  ages; nothing here independently establishes clock truth.
- **Advice quality is not verified here.** Whether the emphasis is *good* is
  measured by `FEAT-AGT-17` evaluation against versioned sets. That mechanism
  now exists, but no versioned set has been authored for this role and no
  grader has been calibrated against it, so this role has not in fact been
  evaluated.
- **`WF-AGT-TER` remains `Missing`.** This feature implements steps 1 and 4;
  steps 2 and 3 are `FEAT-AGT-07`, and step 5 needs the `FEAT-AGT-22`
  submission path.
- Google ADK binding is not implemented (`FEAT-AGT-03` is `Partial`).

---

## 7. Change Process

1. Update the canonical Agentic README first — it owns the registry row.
2. Update this file.
3. Change `prompt.md` and the manifest `base_prompt_hash` together; they are
   verified against each other at startup.
4. Never add a numeric or quantity field to `AllocationProposal`. The absence
   of one is the guarantee, and a "just informational" number is exactly the
   thing an execution path would later consume.
5. Never add a verdict, severity, or boolean to `RiskAdvisory`.
6. Never register a tool whose `side_effect_class` is not `read_only`.
7. Update `schemas.py`, `tools.py`, tests, and the usage program.
8. Change status only after every gate passes.
