# ADR-0007: Cross-Domain Contract Ownership Rules

**Status:** Accepted
**Date:** 2026-07-12
**Deciders:** Haruperi (Owner)
**Source:** PROJECT.md OD-7

## Context

With eleven domains and ~19 cross-domain contracts, every contract needs exactly one schema owner, decided by rule rather than case by case. Ambiguity showed up concretely: who owns `StrategyRegistrationRequest` when Research produces the candidate but Strategy validates and registers it? Who owns `AuthContext`, produced by UI/API but consumed everywhere?

## Decision

Adopt three ownership rules: commands and requests are owned by the receiving domain; events and results are owned by the producing domain; shared context/envelope contracts are owned by the lowest common shared domain, normally Utils. A submitting domain may create an instance of a command without owning its schema. Additionally, advisory Research/Optimization outputs reach Strategy only through explicit UI/API-approved Strategy commands — never directly.

## Options Considered

### Option A: Producer always owns

**Pros:** One simple rule.
**Cons:** For commands it inverts authority — UI/API would define what a valid `StrategyRegistrationRequest` looks like, though Strategy must validate and enforce it. The validator must own the schema it validates.

### Option B: Central schema registry (one domain owns all contracts)

**Pros:** Single place to look.
**Cons:** Recreates a god-module; the owning domain becomes a change bottleneck coupled to every business concept, violating domain autonomy.

### Option C: Receiver-owns-commands / producer-owns-results / Utils-owns-envelopes (chosen)

**Pros:** Ownership follows enforcement authority; matches messaging-system convention (commands addressed to a handler, events published by an owner); envelope contracts (AuthContext, AuditEvent, StandardToolResponse) land in the one business-neutral domain everyone already depends on.
**Cons:** Three rules instead of one; each contract must be classified as command, result/event, or envelope.

## Trade-off Analysis

The classification cost is trivial (the Section 5 table records it) and buys unambiguous authority: whoever enforces a contract's validity owns its schema and its version. The advisory-path rule additionally guarantees no research or optimization output can mutate Strategy state without an explicit, authorized human-approved command through UI/API.

## Consequences

- Every row in the Section 5 contract table has a derivable owner; disputes resolve by classification, not negotiation.
- Versioning authority follows ownership (Section 5 versioning policy).
- Research and Optimization remain purely advisory by construction.

## Action Items

1. [ ] Classify any new contract (command / result / envelope) at introduction time in Section 5.
2. [ ] Add authorization tests for `StrategyRegistrationRequest` and `StrategyParameterUpdateRequest`.
