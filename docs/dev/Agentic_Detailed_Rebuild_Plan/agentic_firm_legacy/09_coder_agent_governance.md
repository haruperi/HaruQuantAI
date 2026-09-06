# Code-Generating Agent Governance

> **Status:** Active supporting specification
>
> **Canonical requirements:** `FR-AGENTIC-046`–`054`

## Scope

The coder implements an authenticated, bounded specification. Open-ended discovery
by code generation is permitted only inside an approved experiment with a declared
lifetime search budget and null-data control.

## Sandbox

The sandbox is ephemeral, non-production, resource-limited, and separate from the
Agentic worker. It has:

- No broker, cloud, database, repository, signing, or production credentials
- Denied network egress unless one exact dependency mirror is approved
- Read-only approved inputs and write-only staging output
- Approved interpreter, dependency lock/constraints, and toolchain image
- CPU, memory, disk, process, wall-clock, and output limits
- Explicit process and file-handle teardown
- Captured dependency/SBOM, commands, exit status, bounded logs, and hashes

## Ordered gates

1. Specification and principal validation
2. Static formatting, linting, typing, secret, and dependency checks
3. Unit, property, mutation, and boundary tests
4. Timestamp causality and temporal non-interference
5. Deterministic frozen-reference replay
6. Leakage and holdout-consumption checks
7. Simulation with realistic costs and required risk profile
8. Walk-forward, stress, robustness, and simpler-baseline comparison
9. Independent critic review
10. Complete promotion packet
11. Authenticated human code review
12. Receiver-owned registration validation

No later gate compensates for an earlier failure.

## Search discipline

Every generated or repaired variant consumes the declared lifetime search budget.
All attempts, including failures, remain recorded. Holdouts are registered before
use and retired after use. Null or randomized data measures the system's false
discovery behaviour.

## No hot loading

Agentic never imports generated modules from staging. Only the owning receiver may
register an approved immutable artefact during an authorized release operation.
