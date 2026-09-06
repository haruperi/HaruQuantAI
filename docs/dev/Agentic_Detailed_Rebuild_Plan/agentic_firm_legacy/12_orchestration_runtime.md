# Durable Orchestration Runtime

> **Status:** Active supporting specification
>
> **Canonical requirements:** `FR-AGENTIC-007`–`012`

## Runtime split

HaruQuantAI owns task contracts, graph definitions, state, checkpoints, policy,
idempotency, and failure semantics. `AdkRuntime` maps those portable definitions to
Google ADK 2.x Workflow, Agent, task, callback, session, artifact, evaluation, and
telemetry capabilities.

ADK types do not enter public contracts or persisted canonical records.

## Role-package resolution

Orchestration selects a stable role ID, never a filesystem path or arbitrary
callable. The validated `RoleRegistry` resolves that ID to its registered
`agents/<department>/<agent_name>/` owning package, model profile, schema versions,
tool policy, evaluation state, prompt hash, and limits. The leaf `agent.py` produces
a provider-neutral definition only after the package-local `prompt.md` and composite
instruction hashes pass validation.

Workflow code depends on the registry and Agentic contracts; it does not import
individual specialist packages or inspect prompt files directly. `AdkRuntime`
receives the validated definition and maps it to ADK runtime objects. Missing,
disabled, duplicated, hash-mismatched, or feature-incompatible role packages fail
closed before a model or tool call.

## Workflow graph

Graph construction is deterministic. Dynamic logic may select enabled nodes and
branches from registered capabilities, but it cannot invent roles, tools, limits,
or terminal states. Supported patterns include parallel independent analysis,
fan-in synthesis, deterministic routing, bounded loops, human-input waits, nested
workflows, and task delegation.

## Durable states

`submitted → running ↔ waiting_human → succeeded | refused | failed | cancelled | expired`

Every transition uses transactional persistence, expected-version checks, a write
lock, and an audit event. External calls use idempotency reservations so recovery
after an ambiguous outcome does not repeat side effects.

## Failure and recovery

- Transient provider/tool failures use declared bounded retries with jitter.
- Schema repair is limited to one attempt unless a feature specifies zero.
- Policy, evidence, injection, approval, and budget failures are not retried.
- Worker loss resumes from the last committed checkpoint.
- Cancellation propagates to pending nodes and safely drains non-cancellable calls.
- Expired tasks reject late results.
- Dead-letter/quarantine records preserve unresolved failures for operator action.

## Capacity

Per-workflow and global limits cover active runs, fan-out, provider concurrency,
tool concurrency, queues, context size, output size, tokens, cost, and wall time.
Overload rejects or queues by deterministic priority; the model cannot change it.
