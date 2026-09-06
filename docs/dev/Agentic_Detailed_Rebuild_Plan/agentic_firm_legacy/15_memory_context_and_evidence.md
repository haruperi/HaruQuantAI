# Memory, Context, and Evidence Standard

> **Status:** Active supporting specification
>
> **Canonical requirements:** `FR-AGENTIC-016`–`018`

## Stores

1. Immutable evidence memory for source-backed facts and claims
2. Experiment memory for hypotheses, trials, outcomes, and holdout consumption
3. Operational audit memory for calls, policy, approvals, incidents, and costs
4. Bounded disposable working memory for one task

No free-form “institutional memory” is accepted as truth.

## Context assembly

`assemble_context` applies, in order:

1. Principal, mandate, task, asset, account, and environment scope
2. Contract/schema compatibility
3. Point-in-time availability and look-ahead prevention
4. Provenance, hash, source trust, licensing, and revision status
5. Freshness and event-window rules
6. Deduplication and conflicting-source marking
7. Injection/poisoning classification and instruction stripping
8. Relevance ranking and deterministic token budget
9. Clear separation of trusted instruction and untrusted evidence

## Memory writes

Writes carry author/model/tool, source evidence, workflow, role, confidence basis,
created/available times, TTL or retention class, sensitivity, injection status,
schema, and content hash. Corrections append; they do not overwrite history.

Working memory cannot be retrieved outside its task or after TTL. Evidence used for
a consequential proposal remains available for the audit retention period.

## Prohibited memory effects

Memory cannot grant permission, create approval, alter mandate or thresholds,
change a model profile, promote an artefact, or directly update live policy based on
P&L reflection.
