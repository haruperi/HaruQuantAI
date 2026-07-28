# Agent-Callable Tool Standard

> **Status:** Active supporting specification
>
> **Canonical requirements:** `FR-AGENTIC-013`–`015`, `061`–`063`

## Core rule

A tool is a narrow, typed adapter to one public deterministic operation. It contains
no LLM, hidden business policy, provider object, broad filesystem access, or
unregistered side effect.

## Tool declaration

Every tool declares:

- Stable name/version and owning Agentic feature
- Receiver domain, public operation, request/result schema
- Permission class and eligible role IDs
- Environment, asset, account, and data scope
- Side-effect class and idempotency semantics
- Required approval attestation
- Input/output size and content limits
- Timeout, retry, circuit, concurrency, and rate policy
- Token/tool/cost accounting
- Redaction and audit fields
- Failure mapping and cleanup behaviour

## Call lifecycle

1. Validate task, role, model, tool, schema, and trusted scope.
2. Authorize through the policy enforcement point.
3. Reserve budget and idempotency.
4. Record a redacted call-start audit event.
5. Invoke the receiver's public operation.
6. Validate and bound the result as untrusted input.
7. Record outcome, duration, cost, receiver reference, and safe failure.
8. Return a typed result; audit failure is a hard failure.

## Side effects

Read-only and deterministic computation tools may be granted explicitly. Staging
writes require an authenticated specification. Proposal submission is allowed only
through `FEAT-AGT-20`. Direct controlled mutations and critical tools are never
registered for agents.

`dry_run` never substitutes for permission, approval, or receiver validation.
