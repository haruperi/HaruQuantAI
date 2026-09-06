# Agentic Risk Boundary

> **Status:** Active supporting policy
>
> **Canonical requirements:** `FR-AGENTIC-013`–`015`, `055`–`060`

## Separation of responsibilities

The Agentic risk team is an advisory challenge function. It identifies missing
evidence, mandate conflicts, tail exposure, barrier risk, concentration, liquidity,
correlation, model, data, operational, counterparty, and execution risks.

The deterministic Risk domain alone returns authoritative risk decisions.

| Activity | Agentic | Deterministic owner |
|---|---|---|
| Identify and explain risk | Yes | Risk may also explain deterministic reasons |
| Request a risk evaluation | Yes | Risk validates the request |
| Recommend rejection or reduction | Advisory only | Risk decides |
| Calculate authoritative limits or size | No | Risk |
| Approve strategy, allocation, or trade | No | Risk/human policy |
| Activate or clear kill switch | No | Risk/Trading through authorized human paths |
| Submit broker order | No | Trading/Brokers |

## Proposal route

```text
Agentic evidence and deliberation
  → typed proposal
    → receiver validation
      → Strategy/Portfolio evaluation
        → deterministic Risk decision
          → authenticated Trading request
            → Trading readiness, idempotency, routing, reconciliation
              → Broker adapter
```

No Agentic service may skip a node or supply a precomputed “approved” value.

## Safe failure

- Risk evidence missing or stale: advice and proposal are refused.
- Risk domain unavailable: no consequential proposal progresses.
- Risk rejects: Agentic records the decision and may research alternatives; it may
  not repeatedly resubmit materially identical proposals.
- Kill switch active: Agentic may analyze the incident but cannot clear or route
  around it.
- Agent disagreement: preserve dissent; do not average incompatible risk limits.
