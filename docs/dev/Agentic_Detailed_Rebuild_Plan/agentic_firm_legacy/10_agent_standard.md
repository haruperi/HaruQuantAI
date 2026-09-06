# Specialized Agent Standard

> **Status:** Active supporting specification
>
> **Canonical requirements:** `FR-AGENTIC-004`–`009`, `019`–`036`, `049`–`051`

## Role manifest

Every specialized role declares:

- Stable role ID, version, owning feature, department, and description
- Objective, expertise boundary, supported assets, and refusal conditions
- Input and output schema versions
- Pinned prompt hash and instruction hierarchy
- Approved model profile and permitted fallback
- Explicit tools and permission classes
- Data/source requirements and freshness
- Token, call, tool, cost, time, retry, and discussion budgets
- Evaluation set, thresholds, baseline, and ablation condition
- Memory read/write classes and retention
- Failure and incident behaviour

Startup validates the manifest against the firm mandate and registries.

## Package standard

Shared control-plane features remain in focused top-level packages under
`app/agentic/`. Every registered role-bearing feature resides in exactly one leaf
package under:

```text
app/agentic/agents/<department>/<agent_name>/
├── __init__.py
├── agent.py
├── prompt.md
├── schemas.py
└── README.md
```

`agents/` and department packages are namespaces only and contain no production
behaviour. The leaf package is the Feature Registry owning module. It adds
`tools.py`, `evaluator.py`, repositories, migrations, sandbox, store, or handoff
files only when the canonical module specification requires them.

File responsibilities are strict:

- `agent.py` defines the provider-neutral agent, loads and verifies `prompt.md`,
  binds the enabled manifest/model/schema/tool references, exposes the registered
  feature operation, and delegates execution to the injected `AdkRuntime`.
- `prompt.md` contains immutable base role instructions and no dynamic context,
  untrusted evidence, credentials, model selection, tool permission, or
  deterministic policy.
- `schemas.py` contains feature-owned typed inputs and outputs and performs no
  model call, orchestration, persistence, or owner-domain calculation.
- `README.md` follows `docs/templates/README.md` and remains subordinate to the
  canonical Agentic Feature Registry.
- A leaf `__init__.py` exposes only Feature Registry public API. Namespace
  `__init__.py` files expose no feature behaviour.

Direct Google ADK or provider imports, embedded prompt strings, and undeclared
feature behaviour are prohibited in a leaf agent package.

## Prompt standard

Prompts separate immutable system policy, role instruction, trusted structured
context, untrusted evidence, peer messages, and task input. Retrieved text is
delimited and cannot introduce instructions. Prompts require citations, uncertainty,
falsifiers, dissent, and refusal when evidence is insufficient.

The package-local `prompt.md` is the immutable base role instruction. Startup
verifies its content hash against the enabled manifest before agent construction.
When one feature capability supports multiple registered roles, the manifest may add
one bounded role instruction without duplicating implementation. Provenance records
the base-prompt hash, manifest hash, and resulting composite-instruction hash.
Unverified, missing, mutable-at-runtime, or incompatible prompt artefacts fail
closed.

## Output standard

All outputs use `AgentResult[T]`. A role emits one declared typed payload and:

- Distinguishes facts, calculations, inference, and recommendation
- References evidence IDs rather than copying unrestricted source payloads
- Records limitations and unresolved questions
- Contains no authorization language or execution-bound free text
- Is rejected after one bounded schema repair failure

## Adding or retiring roles

A new role requires an existing or newly approved feature, owning agent-package
mapping, manifest, prompt artefact, schema, tools, evaluation set, baseline, usage
evidence, and registry update. It remains disabled until all gates pass. A role is
retired when unsafe, redundant, uneconomic, or inferior to a simpler baseline; its
evidence remains auditable.
