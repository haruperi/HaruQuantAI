# Google ADK and Model-Provider Architecture

> **Status:** Active supporting specification
>
> **Canonical requirements:** `FR-AGENTIC-007`–`009`

## Decision

Google Agent Development Kit 2.x is the selected Agentic runtime. Version 2.1.0 was
the current stable Python release verified on 2026-07-28. Its graph, dynamic, and
collaborative workflows, task API, human-input support, sessions, artifacts,
evaluation, and telemetry align with the target design. The project requires Python
3.14, which ADK 2.x supports through published constraints.

The dependency is not added during documentation work. Implementation re-verifies
and pins the stable compatible version and constraints in `pyproject.toml` and
`uv.lock`.

## Adapter boundary

- `AdkRuntime` owns ADK application, runner, workflow, agent/node, callback, session,
  and artifact mapping.
- `ModelGateway` owns provider-neutral invocation and response normalization.
- `ModelProfile` owns provider, exact model, region, credentials reference,
  capabilities, structured-output mode, limits, privacy/retention, and fallback.
- A leaf agent package's `agent.py` owns the provider-neutral feature definition and
  public use-case entry point. It depends on HaruQuantAI protocols, never ADK or
  provider SDKs.
- `prompt.md` remains a versioned HaruQuantAI artefact. ADK receives only the
  validated composed instruction through `AdkRuntime`.

## Agent construction and prompt integrity

The validated `RoleRegistry` resolves the owning agent package, `RoleManifest`,
`ModelProfile`, schemas, tools, evaluation state, and limits. The package
`agent.py` loads `prompt.md` as data, verifies its base hash, composes the bounded
manifest role instruction, and records the base-prompt, manifest, and composite
instruction hashes. Only then may it submit a provider-neutral definition to
`AdkRuntime`.

`AdkRuntime`, implemented only in `runtime/adk.py`, is the sole layer that
constructs ADK Agent, workflow, session, tool, callback, artifact, and evaluation
objects. It never receives an unverified prompt or grants tools beyond the
deterministic permission decision. Missing packages, prompt mutation, hash mismatch,
undeclared schemas/tools, disabled roles, or incompatible model profiles fail
closed before provider invocation.

## Provider changes

Changing one model-profile reference may select another supported model. Activation
still requires:

- Exact model identity; no floating aliases
- Structured schema and tool-call compatibility
- Context and output limits
- Safety/refusal and injection regression
- Data location, privacy, retention, and training-use review
- Latency, availability, quotas, and cost
- Shadow comparison and rollback

Silent substitution is prohibited in governed workflows. Safe fallback is normally
`refused`; an alternate model is used only when explicitly registered and evaluated
for the same capability.

## ADK upgrade policy

ADK public classes, events, sessions, workflow graphs, tools, CLI, and persisted
schemas are treated as a versioned external contract. Major upgrades require
migration and replay tests. Callbacks and standard extension points are used;
private methods and direct session-event mutation are prohibited.

## Verified upstream references

- [Google ADK 2.0 overview](https://adk.dev/2.0/)
- [Google ADK workflows](https://adk.dev/workflows/)
- [Google ADK model integrations](https://adk.dev/agents/models/)
- [Google ADK sessions and memory](https://adk.dev/sessions/)
- [Google ADK evaluation](https://adk.dev/evaluate/)
- [Google ADK callbacks](https://adk.dev/callbacks/)
- [Google ADK Python releases](https://github.com/google/adk-python/releases)
