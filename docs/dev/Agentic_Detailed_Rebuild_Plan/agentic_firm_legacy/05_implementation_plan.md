# Agentic Firm Documentation-First Implementation Plan

> **Status:** Active supporting plan
>
> **Canonical feature order:** `app/agentic/README.md`

## Governing rule

The complete end state is documented, reviewed, reconciled, and approved before the
first Agentic production module or test is created. A phased implementation order
does not permit partial architecture discovery during coding.

## Documentation completion gate

Before implementation:

1. All `FEAT-AGT-01`–`22` rows, public APIs, and `FR-AGENTIC-*` requirements are
   final.
2. All roles, workflows, contracts, stores, configuration, failure modes, security
   controls, deployment boundaries, and acceptance cases are final.
3. Every cross-domain producer, consumer, request owner, and authority boundary
   agrees across package READMEs, Project, and Architecture.
4. Google ADK and provider adapters are specified without leaking framework types.
5. Data readiness for each evidence-dependent agent is explicit.
6. The full implementation checklist has evidence targets and rollback steps.
7. No open owner decision remains.
8. All ten infrastructure feature folders and twelve role-bearing leaf agent
   packages match the canonical Feature Registry and dependency order.
9. Every role-bearing feature has final `agent.py`, `prompt.md`, schema, optional
   supporting-file, manifest, evaluation, test, usage, and README obligations.

## Future implementation sequence

After the documentation gate passes:

1. Canonical contracts and governance
2. ADK runtime, orchestration, permissions, and context/memory
3. Deliberation and operational controls
4. Simulation Interpreter and the four market-intelligence/market-analysis agent
   packages
5. Strategy Thesis Analyst, Experiment Designer, and Optimization Coordinator
   agent packages
6. Coder and Evaluation Manager agent packages, followed by lifecycle
7. Portfolio/Risk Advisor and Trader agent packages
8. Public API and system integration

Every feature receives its module, unit tests, exactly one numbered usage program,
integration evidence, and status update before the next dependent feature completes.
Targeted tests are used during development; a final domain and system gate follows.

For a role-bearing feature, its module is the exact registered
`agents/<department>/<agent_name>/` leaf package. The feature is incomplete until
`agent.py`, integrity-checked `prompt.md`, `schemas.py`, template-conformant
`README.md`, all specification-required optional files, registry/manifest parity,
tests, and usage evidence land together. Namespace packages contain no production
behaviour. Infrastructure features retain responsibility-based file names and do
not acquire artificial prompts or agent wrappers.

## Implementation-plan checklist format

Every future checklist item shall end with its expected evidence path and line
number. No item may be marked complete using a plan, prompt, mock screenshot, or
unexecuted test as evidence.
