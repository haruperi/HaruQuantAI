# ADR-0001: Defer the Conversation / AI-Interface Domain

**Status:** Accepted
**Date:** 2026-07-12
**Deciders:** Haruperi (Owner)
**Source:** PROJECT.md OD-1

## Context

Early system shaping raised the question of whether a conversational / AI-agent interface should be a first-class domain in the initial build. HaruQuantAI is a governed algorithmic trading platform where every execution path must be provable and fail-closed. An AI layer capable of drafting or planning broker-affecting actions introduces a large, hard-to-verify surface before the deterministic core even exists.

## Decision

Defer all AI-driven elements from the initial eleven-domain build. Conversation belongs to a future AI-Agentic domain, introduced only after the system operates fully without AI. Specifically deferred: the AI Agent actor, AI provider API integrations, external AI consumers of `StandardToolResponse`, and any AI-drafted broker-affecting actions.

## Options Considered

### Option A: Include an AI/Conversation domain from the start

| Dimension | Assessment |
|-----------|------------|
| Complexity | High — twelfth domain, external provider APIs, streaming, fallback degradation |
| Safety | High risk — AI-planned actions before governance is proven |
| Time to core value | Slower — delays the deterministic trading core |

**Pros:** Conversational UX from day one; contracts designed with AI consumers in mind.
**Cons:** Expands the verification surface massively; couples core contracts to a speculative consumer; violates the fail-closed-first build philosophy.

### Option B: Defer to a post-core AI-Agentic domain (chosen)

| Dimension | Assessment |
|-----------|------------|
| Complexity | Low now — eleven domains, no AI dependencies |
| Safety | Strong — no AI can touch broker paths until the governed core is verified |
| Time to core value | Faster |

**Pros:** Core system verifiable in isolation; AI added later against stable, versioned contracts.
**Cons:** Some contracts (e.g., `StandardToolResponse`) are designed for a consumer that does not yet exist; later AI integration may reveal contract gaps.

## Trade-off Analysis

The deciding factor is governance: the system's safety claims (independent Risk gate, fail-closed execution) must be established before any AI capability is layered on. The cost — possible contract rework when the AI domain arrives — is acceptable because contracts are versioned (Section 5 policy).

## Consequences

- The initial build has exactly eleven domains; no AI actor appears in Section 1.
- `StandardToolResponse` consumers are restricted to internal domains for now.
- The future AI-Agentic domain will enter as a new top-level consumer via UI/API-style delegation, requiring a new ADR.

## Action Items

1. [ ] Revisit after the system Definition of Done is met without AI.
2. [ ] Write a follow-up ADR defining the AI-Agentic domain boundary when introduced.
